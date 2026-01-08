"""Business logic around user lifecycle."""
from __future__ import annotations

from typing import Dict, Optional

from backend.db import database


def _row_to_user(row) -> Dict[str, str]:
    return {
        "id": row.id,
        "username": row.username,
        "role": row.role,
        "created_at": row.created_at,
    }


def get_user_by_username(username: str) -> Optional[Dict[str, str]]:
    row = database.fetch_one("SELECT id, username, role, created_at, password FROM users WHERE username = ?", (username,))
    if not row:
        return None
    user = _row_to_user(row)
    user["password"] = row.password
    return user


def get_user_by_id(user_id: int) -> Optional[Dict[str, str]]:
    row = database.fetch_one("SELECT id, username, role, created_at FROM users WHERE id = ?", (user_id,))
    if not row:
        return None
    return _row_to_user(row)


def create_user(username: str, password: str, role: str = "user") -> Dict[str, str]:
    existing = database.fetch_one("SELECT id FROM users WHERE username = ?", (username,))
    if existing:
        raise ValueError("Username already exists")
    database.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
    created = get_user_by_username(username)
    if not created:
        raise RuntimeError("Failed to create user")
    return created


def validate_credentials(username: str, password: str) -> Optional[Dict[str, str]]:
    user = get_user_by_username(username)
    if not user:
        return None
    if user.get("password") != password:
        return None
    return user


def list_all_users() -> list[Dict[str, str]]:
    rows = database.fetch_all("SELECT id, username, role, created_at FROM users ORDER BY created_at DESC")
    return [_row_to_user(row) for row in rows]
