from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ── Password hashing ──────────────────────────────────────────────────────────
# bcrypt is the industry standard for hashing passwords
# Every password gets a random "salt" added before hashing
# so two users with the same password have different hashes
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    Takes a plain password like "mypassword123"
    Returns a hash like "$2b$12$randomstuff..."
    This hash is what gets stored in the database.
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Takes the plain password the user typed at login
    and the hash stored in the database.
    Returns True if they match, False if not.
    We never decrypt the hash — bcrypt rehashes and compares.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT Tokens ────────────────────────────────────────────────────────────────
# JWT = JSON Web Token
# It's a string that looks like: xxxxx.yyyyy.zzzzz
# It contains user info (id, role) and is signed with your SECRET_KEY
# Anyone can READ the token but cannot FAKE one without the secret key

def create_access_token(data: dict) -> str:
    """
    Creates a short-lived access token (15 minutes).
    This is what the frontend sends with every API request.
    
    data should contain: {"sub": str(user_id), "role": user.role}
    sub = subject = who this token belongs to
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """
    Creates a long-lived refresh token (7 days).
    When the access token expires, the frontend sends this
    to get a new access token without logging in again.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """
    Decodes and verifies a JWT token.
    Returns the payload dict if valid, None if expired or tampered.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def hash_token(raw_token: str) -> str:
    """
    Returns a SHA-256 hex digest of a token string.

    Used to store refresh tokens in the database without keeping
    the raw value. If the DB leaks, an attacker gets hashes they
    can't reverse into usable tokens.

    SHA-256 (not bcrypt) is appropriate here because:
    • Refresh tokens are already long random strings (high entropy)
    • We need fast lookup by hash on every refresh request
    • bcrypt's slowness is only needed when hashing low-entropy passwords
    """
    return hashlib.sha256(raw_token.encode()).hexdigest()