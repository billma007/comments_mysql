"""Administrator-only operations."""
from __future__ import annotations

from typing import Dict, List

from backend.services import comment_service, user_service


def ensure_admin(role: str) -> None:
    if role != "admin":
        raise PermissionError("Administrator role required")


def delete_comment(comment_id: int) -> None:
    updated = comment_service.soft_delete_comment(comment_id)
    if not updated:
        raise ValueError("Comment not found")


def create_admin(username: str, password: str) -> Dict[str, str]:
    return user_service.create_user(username, password, role="admin")


def moderation_feed(include_deleted: bool = True) -> List[Dict[str, str]]:
    return comment_service.list_all_comments(include_deleted=include_deleted)
