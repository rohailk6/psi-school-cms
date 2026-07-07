from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """
    Fields required to create a new user.

    The role is passed as a string (e.g. "teacher") and the service
    layer will look up the corresponding Role row and create the
    UserRoleAssignment. This keeps the API simple while the DB
    stays normalized.
    """
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: str
    # e.g. "teacher", "student", "admin"
    # service layer validates this is a real role name


class UserUpdate(BaseModel):
    """All fields are optional — send only what you want to change."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """
    Full user record returned by the API.
    Never exposes password_hash or deleted_at.
    """
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    is_active: bool
    roles: List[str]
    # derived from user_roles junction — the service layer populates this
    last_login_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
