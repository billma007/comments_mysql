"""Thin database helper layer that owns every direct SQL Server interaction."""
from __future__ import annotations

import contextlib
from typing import Any, Iterable, Optional, Sequence

import pyodbc

from backend.config import DATABASE_CONFIG


def _build_connection_string(database_override: Optional[str] = None) -> str:
    """构建 SQL Server 连接字符串，可选地覆盖数据库名。"""
    server = DATABASE_CONFIG["server"]
    port = DATABASE_CONFIG.get("port")
    if port:
        server = f"{server},{port}"

    database = database_override or DATABASE_CONFIG["database"]
    encrypt = DATABASE_CONFIG.get("encrypt", "no").lower()
    trust_cert = DATABASE_CONFIG.get("trust_server_certificate", "yes").lower()

    parts = [
        f"DRIVER={DATABASE_CONFIG['driver']}",
        f"SERVER={server}",
        f"DATABASE={database}",
        f"UID={DATABASE_CONFIG['username']}",
        f"PWD={DATABASE_CONFIG['password']}",
        f"Encrypt={encrypt}",
        f"TrustServerCertificate={trust_cert}",
    ]
    return ";".join(parts)


@contextlib.contextmanager
def get_connection(database_override: Optional[str] = None):
    """获取 pyodbc 连接，自动处理提交 / 回滚 / 关闭。"""
    connection = pyodbc.connect(_build_connection_string(database_override))
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def execute(query: str, params: Optional[Sequence[Any]] = None) -> int:
    """执行 INSERT/UPDATE/DELETE，返回受影响行数。"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params or [])
        affected = cursor.rowcount
        cursor.close()
        return affected


def fetch_one(query: str, params: Optional[Sequence[Any]] = None) -> Optional[pyodbc.Row]:
    """执行查询并返回一行记录；若无结果则返回 None。"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params or [])
        row = cursor.fetchone()
        cursor.close()
        return row


def fetch_all(query: str, params: Optional[Sequence[Any]] = None) -> Iterable[pyodbc.Row]:
    """执行查询并返回所有记录列表。"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params or [])
        rows = cursor.fetchall()
        cursor.close()
        return rows


def execute_with_identity(query: str, params: Optional[Sequence[Any]] = None) -> int:
    """执行插入语句并返回 SCOPE_IDENTITY()，用于获得自增主键。"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params or [])
        cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
        new_id = cursor.fetchone()[0]
        cursor.close()
        return new_id
