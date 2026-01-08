"""Reusable FastAPI dependencies."""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, Header, HTTPException, status

from backend.services import auth_service, user_service


async def get_bearer_token(authorization: str = Header(...)) -> str:
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token")
    return authorization.split(" ", 1)[1].strip()


async def get_current_user(token: str = Depends(get_bearer_token)) -> dict:
    try:
        session = auth_service.require_session(token)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user = user_service.get_user_by_id(session["user_id"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    user["role"] = session["role"]
    user["token"] = token
    return user


async def get_current_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return user


async def get_optional_user(authorization: Optional[str] = Header(default=None)) -> Optional[dict]:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    try:
        session = auth_service.require_session(token)
    except PermissionError:
        return None
    user = user_service.get_user_by_id(session["user_id"])
    if not user:
        return None
    user["role"] = session["role"]
    user["token"] = token
    return user
