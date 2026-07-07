"""
Seed script — run once (or re-run safely) to populate:
  1. Roles
  2. Permissions
  3. Role → Permission assignments
  4. Default super admin user

Usage:
    cd backend
    python -m app.db.seed

Or with custom admin credentials:
    SEED_ADMIN_EMAIL=admin@school.com SEED_ADMIN_PASSWORD=secret python -m app.db.seed

IDEMPOTENT: safe to run multiple times. Uses "get or create" for every row
so re-running never duplicates data.
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# ── Permission catalogue ───────────────────────────────────────────────────────
#
# Format: (resource, action)
# Code is derived as f"{resource}:{action}" — e.g. "students:write"
#
# Why separate resource + action columns instead of just storing the code?
# So you can query "all permissions for resource=students" easily,
# and the UI can group them by resource in a permission manager screen.

ALL_PERMISSIONS: list[tuple[str, str, str]] = [
    # (resource, action, human-readable description)
    ("users",               "read",   "View user accounts"),
    ("users",               "write",  "Create and update user accounts"),
    ("users",               "delete", "Deactivate or soft-delete user accounts"),

    ("students",            "read",   "View student profiles"),
    ("students",            "write",  "Create and update student profiles"),
    ("students",            "delete", "Soft-delete student profiles"),

    ("teachers",            "read",   "View teacher profiles"),
    ("teachers",            "write",  "Create and update teacher profiles"),
    ("teachers",            "delete", "Soft-delete teacher profiles"),

    ("classes",             "read",   "View classes and sections"),
    ("classes",             "write",  "Create and update classes and sections"),
    ("classes",             "delete", "Delete classes and sections"),

    ("subjects",            "read",   "View subjects"),
    ("subjects",            "write",  "Create and update subjects; assign to classes"),
    ("subjects",            "delete", "Remove subjects from classes"),

    ("academic_years",      "read",   "View academic years"),
    ("academic_years",      "write",  "Create and update academic years"),
    ("academic_years",      "delete", "Delete academic years"),

    ("enrollments",         "read",   "View student enrollments"),
    ("enrollments",         "write",  "Enroll and transfer students"),

    ("teacher_assignments", "read",   "View teacher class/subject assignments"),
    ("teacher_assignments", "write",  "Assign teachers to classes and subjects"),
    ("teacher_assignments", "delete", "Remove teacher assignments"),

    ("exams",               "read",   "View exams and exam schedules"),
    ("exams",               "write",  "Create and manage exams; change exam status"),
    ("exams",               "delete", "Delete draft exams"),

    ("marks",               "read",   "View student marks"),
    ("marks",               "write",  "Enter and update student marks"),
]

# ── Role → Permission matrix ───────────────────────────────────────────────────
#
# Each role gets a set of permission codes (resource:action).
# "ALL" is a shorthand meaning every permission in ALL_PERMISSIONS.
# Roles with fewer permissions get an explicit list.

_ALL_CODES = {f"{r}:{a}" for r, a, _ in ALL_PERMISSIONS}

ROLE_DEFINITIONS: list[dict] = [
    {
        "name": "super_admin",
        "display_name": "Super Administrator",
        "description": "Full system access including user and role management.",
        "is_system": True,
        "permissions": _ALL_CODES,
    },
    {
        "name": "admin",
        "display_name": "Administrator",
        "description": "Manages academic data: students, teachers, classes, exams, marks.",
        "is_system": True,
        "permissions": _ALL_CODES - {"users:delete"},
        # Admins can manage users but cannot delete/deactivate accounts —
        # that privilege is reserved for super_admin to prevent lockouts.
    },
    {
        "name": "teacher",
        "display_name": "Teacher",
        "description": "Views class/student data and enters marks for assigned subjects.",
        "is_system": True,
        "permissions": {
            "students:read",
            "classes:read",
            "subjects:read",
            "academic_years:read",
            "enrollments:read",
            "teacher_assignments:read",
            "exams:read",
            "marks:read",
            "marks:write",   # ← the key teacher permission
        },
    },
    {
        "name": "student",
        "display_name": "Student",
        "description": "Views their own exam schedules and marks.",
        "is_system": True,
        "permissions": {
            "exams:read",
            "marks:read",    # service layer filters to own marks only
        },
    },
]

# ── Super admin defaults (override via env) ────────────────────────────────────

DEFAULT_ADMIN_EMAIL    = os.getenv("SEED_ADMIN_EMAIL",    "admin@psi.edu.pk")
DEFAULT_ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "Admin@1234!")
DEFAULT_ADMIN_FNAME    = os.getenv("SEED_ADMIN_FIRST_NAME", "System")
DEFAULT_ADMIN_LNAME    = os.getenv("SEED_ADMIN_LAST_NAME",  "Admin")


# ── Seeding logic ──────────────────────────────────────────────────────────────

async def seed(db: AsyncSession) -> None:
    from app.models.user import (
        User, Role, Permission, RolePermission, UserRoleAssignment, RefreshToken
    )
    from app.core.security import hash_password

    print("Seeding permissions...")
    permission_map: dict[str, Permission] = {}

    for resource, action, description in ALL_PERMISSIONS:
        code = f"{resource}:{action}"
        existing = (await db.execute(
            select(Permission).where(Permission.code == code)
        )).scalar_one_or_none()

        if existing:
            permission_map[code] = existing
        else:
            perm = Permission(
                code=code,
                resource=resource,
                action=action,
                description=description,
            )
            db.add(perm)
            await db.flush()
            permission_map[code] = perm
            print(f"  + permission: {code}")

    print(f"\nSeeding {len(ROLE_DEFINITIONS)} roles...")

    for role_def in ROLE_DEFINITIONS:
        role = (await db.execute(
            select(Role).where(Role.name == role_def["name"])
        )).scalar_one_or_none()

        if not role:
            role = Role(
                name=role_def["name"],
                display_name=role_def["display_name"],
                description=role_def["description"],
                is_system=role_def["is_system"],
            )
            db.add(role)
            await db.flush()
            print(f"  + role: {role_def['name']}")
        else:
            print(f"  ~ role already exists: {role_def['name']}")

        # Assign permissions to the role (idempotent)
        for code in role_def["permissions"]:
            perm = permission_map.get(code)
            if not perm:
                print(f"  ! WARNING: permission '{code}' not found — skipping")
                continue

            existing_rp = (await db.execute(
                select(RolePermission).where(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == perm.id,
                )
            )).scalar_one_or_none()

            if not existing_rp:
                db.add(RolePermission(role_id=role.id, permission_id=perm.id))

    await db.flush()

    # ── Super admin user ───────────────────────────────────────────────────────

    print(f"\nSeeding super admin ({DEFAULT_ADMIN_EMAIL})...")

    existing_user = (await db.execute(
        select(User).where(User.email == DEFAULT_ADMIN_EMAIL)
    )).scalar_one_or_none()

    if existing_user:
        print("  ~ super admin already exists — skipping")
    else:
        admin_user = User(
            email=DEFAULT_ADMIN_EMAIL,
            password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
            first_name=DEFAULT_ADMIN_FNAME,
            last_name=DEFAULT_ADMIN_LNAME,
            is_active=True,
        )
        db.add(admin_user)
        await db.flush()

        # Assign the super_admin role
        super_admin_role = (await db.execute(
            select(Role).where(Role.name == "super_admin")
        )).scalar_one()

        db.add(UserRoleAssignment(
            user_id=admin_user.id,
            role_id=super_admin_role.id,
        ))

        print(f"  + created super admin: {DEFAULT_ADMIN_EMAIL}")
        print(f"  + password: {DEFAULT_ADMIN_PASSWORD}")
        print("  ! IMPORTANT: change the password after first login")

    await db.commit()
    print("\nSeed complete.")


# ── Entry point ────────────────────────────────────────────────────────────────

async def main() -> None:
    # Import here so the script can be run directly without the full app context
    from app.db.session import AsyncSessionLocal
    # Importing all models ensures SQLAlchemy's mapper is fully configured
    import app.models  # noqa: F401

    async with AsyncSessionLocal() as db:
        try:
            await seed(db)
        except Exception as exc:
            await db.rollback()
            print(f"\nSeed FAILED: {exc}", file=sys.stderr)
            raise


if __name__ == "__main__":
    asyncio.run(main())
