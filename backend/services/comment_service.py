"""Comment-facing business logic."""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Set

from backend.db import database


def _row_to_comment(row, liked_ids: Set[int]) -> Dict[str, object]:
    return {
        "id": row.id,
        "post_id": row.post_id,
        "user_id": row.user_id,
        "username": row.username,
        "content": row.content,
        "created_at": row.created_at,
        "is_deleted": bool(row.is_deleted),
        "parent_comment_id": row.parent_comment_id,
        "like_count": int(row.like_count or 0),
        "liked_by_viewer": row.id in liked_ids,
        "replies": [],
    }


def _fetch_rows(post_id: Optional[str], include_deleted: bool) -> Sequence:
    sql = (
        "SELECT c.id, c.post_id, c.user_id, u.username, c.content, c.created_at, c.is_deleted, c.parent_comment_id, "
        "ISNULL(l.like_count, 0) AS like_count "
        "FROM comments c "
        "INNER JOIN users u ON u.id = c.user_id "
        "LEFT JOIN (SELECT comment_id, COUNT(*) AS like_count FROM comment_likes GROUP BY comment_id) l "
        "ON l.comment_id = c.id "
    )
    conditions = []
    params: List[object] = []
    if post_id:
        conditions.append("c.post_id = ?")
        params.append(post_id)
    if not include_deleted:
        conditions.append("c.is_deleted = 0")
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY c.created_at DESC"
    return database.fetch_all(sql, params)


def _fetch_liked_ids(comment_ids: List[int], viewer_id: Optional[int]) -> Set[int]:
    if not viewer_id or not comment_ids:
        return set()
    placeholders = ",".join(["?"] * len(comment_ids))
    sql = f"SELECT comment_id FROM comment_likes WHERE user_id = ? AND comment_id IN ({placeholders})"
    params = [viewer_id, *comment_ids]
    rows = database.fetch_all(sql, params)
    return {row.comment_id for row in rows}


def _build_tree(rows, liked_ids: Set[int]) -> List[Dict[str, object]]:
    comment_map: Dict[int, Dict[str, object]] = {}
    roots: List[Dict[str, object]] = []

    for row in rows:
        comment_map[row.id] = _row_to_comment(row, liked_ids)

    for comment in comment_map.values():
        parent_id = comment["parent_comment_id"]
        if parent_id and parent_id in comment_map:
            comment_map[parent_id]["replies"].append(comment)
        else:
            roots.append(comment)

    for comment in comment_map.values():
        comment["replies"].sort(key=lambda item: item["created_at"])

    roots.sort(key=lambda item: item["created_at"], reverse=True)
    return roots


def list_comments(post_id: str, include_deleted: bool = False, viewer_id: Optional[int] = None) -> List[Dict[str, object]]:
    rows = _fetch_rows(post_id, include_deleted)
    liked_ids = _fetch_liked_ids([row.id for row in rows], viewer_id)
    return _build_tree(rows, liked_ids)


def list_all_comments(include_deleted: bool = True) -> List[Dict[str, object]]:
    rows = _fetch_rows(post_id=None, include_deleted=include_deleted)
    return _build_tree(rows, liked_ids=set())


def add_comment(post_id: str, user_id: int, content: str, parent_comment_id: Optional[int] = None) -> Dict[str, object]:
    if parent_comment_id:
        parent = database.fetch_one("SELECT id, post_id, is_deleted FROM comments WHERE id = ?", (parent_comment_id,))
        if not parent or parent.is_deleted:
            raise ValueError("Parent comment unavailable")
        if parent.post_id != post_id:
            raise ValueError("Parent comment belongs to another post")

    database.execute(
        "INSERT INTO comments (post_id, user_id, content, parent_comment_id) VALUES (?, ?, ?, ?)",
        (post_id, user_id, content, parent_comment_id),
    )

    rows = database.fetch_all(
        "SELECT TOP 1 c.id, c.post_id, c.user_id, u.username, c.content, c.created_at, c.is_deleted, c.parent_comment_id, 0 AS like_count "
        "FROM comments c INNER JOIN users u ON u.id = c.user_id WHERE c.user_id = ? ORDER BY c.created_at DESC",
        (user_id,),
    )
    liked_ids: Set[int] = set()
    return _row_to_comment(rows[0], liked_ids) if rows else {}


def soft_delete_comment(comment_id: int) -> int:
    return database.execute("UPDATE comments SET is_deleted = 1 WHERE id = ?", (comment_id,))


def toggle_like(comment_id: int, user_id: int) -> Dict[str, object]:
    comment = database.fetch_one("SELECT id, is_deleted FROM comments WHERE id = ?", (comment_id,))
    if not comment or comment.is_deleted:
        raise ValueError("Comment not found")

    existing = database.fetch_one(
        "SELECT id FROM comment_likes WHERE comment_id = ? AND user_id = ?",
        (comment_id, user_id),
    )
    if existing:
        database.execute("DELETE FROM comment_likes WHERE id = ?", (existing.id,))
        liked = False
    else:
        database.execute("INSERT INTO comment_likes (comment_id, user_id) VALUES (?, ?)", (comment_id, user_id))
        liked = True

    total = database.fetch_one("SELECT COUNT(*) AS cnt FROM comment_likes WHERE comment_id = ?", (comment_id,)).cnt
    return {"liked": liked, "likes": int(total)}
