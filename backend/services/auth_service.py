"""In-memory session / token registry."""
from __future__ import annotations

import secrets
import threading
import time
from typing import Dict, Optional

from backend.config import APP_SETTINGS


class SessionManager:
    def __init__(self, ttl_seconds: int) -> None:
        self._ttl = ttl_seconds
        self._sessions: Dict[str, Dict[str, int]] = {}
        self._lock = threading.Lock()

    def issue_token(self, user_id: int, role: str) -> str:
        token = secrets.token_hex(32)
        expires_at = int(time.time()) + self._ttl
        with self._lock:
            self._sessions[token] = {"user_id": user_id, "role": role, "expires_at": expires_at}
        return token

    def get_session(self, token: str) -> Optional[Dict[str, int]]:
        now = int(time.time())
        with self._lock:
            session = self._sessions.get(token)
            if not session:
                return None
            if session["expires_at"] < now:
                self._sessions.pop(token, None)
                return None
            return session

    def revoke(self, token: str) -> None:
        with self._lock:
            self._sessions.pop(token, None)


session_manager = SessionManager(APP_SETTINGS["token_ttl_seconds"])


def require_session(token: str) -> Dict[str, int]:
    session = session_manager.get_session(token)
    if not session:
        raise PermissionError("Invalid or expired token")
    return session


def require_admin_session(token: str) -> Dict[str, int]:
    session = require_session(token)
    if session.get("role") != "admin":
        raise PermissionError("Administrator privileges required")
    return session
