"""User-facing HTTP endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.services import auth_service, user_service

router = APIRouter(prefix="/api/users", tags=["users"])


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=3, max_length=128)


@router.post("/register")
async def register_user(payload: Credentials):
    try:
        user = user_service.create_user(payload.username.strip(), payload.password.strip())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"id": user["id"], "username": user["username"], "role": user["role"]}


@router.post("/login")
async def login_user(payload: Credentials):
    user = user_service.validate_credentials(payload.username.strip(), payload.password.strip())
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = auth_service.session_manager.issue_token(user["id"], user["role"])
    return {"token": token, "username": user["username"], "role": user["role"]}
