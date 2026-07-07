from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import BaseModel


# ─────────────────────────────────────────────────────────────────────────────
# RBAC (Role-Based Access Control) — how permissions work in this system
#
# Flow:  User → user_roles → Role → role_permissions → Permission
#
# Why not just a role column on User?
#   • A user can hold multiple roles (e.g. an admin who also teaches)
#   • Permissions are checked by code string ("marks:write") embedded in the
#     JWT, so every request is validated without hitting the database
#   • Role assignments are audited: who gave whom which role, and when
# ─────────────────────────────────────────────────────────────────────────────


class Role(BaseModel):
    """
    A named bundle of permissions.
    Seeded roles: super_admin, admin, teacher, student.

    is_system=True means seed.py created this role — the API
    will refuse to delete it to prevent locking yourself out.
    """
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    # e.g. "teacher" — the machine-readable identifier used in code
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # e.g. "Class Teacher" — shown in the UI
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Many-to-many: a role has many permissions
    permissions: Mapped[List["Permission"]] = relationship(
        secondary="role_permissions",
        back_populates="roles",
        lazy="selectin",
        # selectin = load permissions in a second SELECT whenever Role is loaded
        # avoids N+1 queries when iterating over a role's permissions
    )
    user_assignments: Mapped[List["UserRoleAssignment"]] = relationship(
        back_populates="role",
    )


class Permission(BaseModel):
    """
    A single granular action the system can authorize.

    Format:  resource:action   →   e.g. "marks:write", "students:read"

    Stored in the DB so they're auditable. At login they're collected
    from the user's roles and embedded in the JWT — meaning every
    subsequent request can check permissions from the token alone,
    with zero database lookups.
    """
    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    # e.g. "marks:write" — this is what gets checked in require_permission()
    resource: Mapped[str] = mapped_column(String(50), nullable=False)
    # e.g. "marks"
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    # e.g. "write"
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("resource", "action", name="uq_permission_resource_action"),
    )

    roles: Mapped[List["Role"]] = relationship(
        secondary="role_permissions",
        back_populates="permissions",
    )


class RolePermission(Base):
    """
    Junction table: which permissions belong to which role.

    Uses Base directly (not BaseModel) because:
    • No need for its own UUID — the PK is (role_id, permission_id) combined
    • No updated_at — once a permission is in a role, it either stays or leaves
    It's a pure link record with no extra metadata.
    """
    __tablename__ = "role_permissions"

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    )


class UserRoleAssignment(Base):
    """
    Junction table: which roles have been assigned to which user.

    Unlike RolePermission, this records WHO assigned the role and WHEN.
    That audit trail matters — you want to know if an admin accidentally
    gave someone super_admin rights.

    assigned_by is nullable because the first super_admin is assigned
    by the seed script (no human user exists yet to be the assigner).
    """
    __tablename__ = "user_roles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    assigned_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    role: Mapped["Role"] = relationship(back_populates="user_assignments")


class RefreshToken(Base):
    """
    Stores a SHA-256 hash of the refresh token in the database.

    Why hash instead of storing the raw token?
    Same reason we hash passwords: if the DB is compromised, the
    attacker gets useless hashes — they can't derive the original token.

    Why store in DB at all?
    So we can revoke tokens server-side on logout. Without this,
    a stolen refresh token would remain valid until its 7-day expiry.
    Setting revoked_at immediately kills the token.
    """
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
        # null = still valid; set to NOW() on logout
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class User(BaseModel):
    """
    The central identity record for every person in the system.
    Admins, teachers, and students all have a User row.

    What lives HERE:   auth credentials, personal info, account state
    What lives elsewhere:
      • Roles           → user_roles junction (supports multiple roles)
      • Teacher details → teacher_profiles table
      • Student details → student_profiles table

    Soft delete: NEVER hard-delete a User. Set deleted_at instead.
    Why? Because marks, enrollments, and assignments all reference
    users.id — deleting a row would either break FK constraints or
    cascade-wipe historical data you need to keep.
    """
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
        # soft delete: set this to NOW() instead of deleting the row
    )

    # Role assignments — loaded automatically (selectin) because they're
    # needed on almost every request that touches a User.
    role_assignments: Mapped[List["UserRoleAssignment"]] = relationship(
        "UserRoleAssignment",
        foreign_keys="[UserRoleAssignment.user_id]",
        lazy="selectin",
    )
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        "RefreshToken",
        foreign_keys="[RefreshToken.user_id]",
    )
    # Profile links — one or none depending on their role(s)
    student: Mapped[Optional["Student"]] = relationship(
        back_populates="user", uselist=False
    )
    teacher: Mapped[Optional["Teacher"]] = relationship(
        back_populates="user", uselist=False
    )

    @property
    def roles(self) -> list[str]:
        """Derived from role_assignments (loaded via lazy='selectin')."""
        return [a.role.name for a in self.role_assignments]

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
