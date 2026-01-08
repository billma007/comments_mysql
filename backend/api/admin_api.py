"""Admin-only HTTP endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.api import dependencies
from backend.services import admin_service

router = APIRouter(prefix="/api/admin", tags=["admin"])


class AdminCreatePayload(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=3, max_length=128)


class DeleteCommentPayload(BaseModel):
    comment_id: int


@router.post("/create")
async def create_admin_user(payload: AdminCreatePayload, admin=Depends(dependencies.get_current_admin)):
    try:
        new_admin = admin_service.create_admin(payload.username.strip(), payload.password.strip())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"id": new_admin["id"], "username": new_admin["username"], "role": new_admin["role"]}


@router.post("/delete_comment")
async def delete_comment(payload: DeleteCommentPayload, admin=Depends(dependencies.get_current_admin)):
    try:
        admin_service.delete_comment(payload.comment_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"status": "deleted", "comment_id": payload.comment_id}


@router.get("/comments")
async def moderation_comments(include_deleted: bool = True, admin=Depends(dependencies.get_current_admin)):
    comments = admin_service.moderation_feed(include_deleted=include_deleted)
    return {"items": comments}
