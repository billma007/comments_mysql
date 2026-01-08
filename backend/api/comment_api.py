"""Comment CRUD endpoints for Hexo front-end."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, Field

from backend.api import dependencies
from backend.services import comment_service

router = APIRouter(prefix="/api/comments", tags=["comments"])


class CommentCreate(BaseModel):
    post_id: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1, max_length=2000)
    parent_comment_id: int | None = Field(default=None, ge=1)


@router.get("")
async def list_post_comments(
    post_id: str = Query(..., min_length=1, max_length=255),
    viewer=Depends(dependencies.get_optional_user),
):
    viewer_id = viewer["id"] if viewer else None
    comments = comment_service.list_comments(post_id, viewer_id=viewer_id)
    return {"items": comments}


@router.post("")
async def submit_comment(payload: CommentCreate, user=Depends(dependencies.get_current_user)):
    if not payload.content.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty comments are not allowed")
    try:
        comment = comment_service.add_comment(
            payload.post_id.strip(),
            user["id"],
            payload.content.strip(),
            payload.parent_comment_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return comment


@router.post("/{comment_id}/like")
async def toggle_like(
    comment_id: int = Path(..., ge=1),
    user=Depends(dependencies.get_current_user),
):
    try:
        result = comment_service.toggle_like(comment_id, user["id"])
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"comment_id": comment_id, **result}
