"""Bootstrap script that creates the SQL Server schema used by the comment service."""
from __future__ import annotations

import sys

import pyodbc

from backend.config import APP_SETTINGS, DATABASE_CONFIG


def _build_conn_str(database: str) -> str:
    server = DATABASE_CONFIG["server"]
    port = DATABASE_CONFIG.get("port")
    if port:
        server = f"{server},{port}"

    parts = [
        f"DRIVER={DATABASE_CONFIG['driver']}",
        f"SERVER={server}",
        f"DATABASE={database}",
        f"UID={DATABASE_CONFIG['username']}",
        f"PWD={DATABASE_CONFIG['password']}",
        f"Encrypt={DATABASE_CONFIG.get('encrypt', 'no')}",
        f"TrustServerCertificate={DATABASE_CONFIG.get('trust_server_certificate', 'yes')}",
    ]
    return ";".join(parts)


def ensure_database():
    target_db = DATABASE_CONFIG["database"]
    conn = pyodbc.connect(_build_conn_str("master"))
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute(f"IF NOT EXISTS(SELECT * FROM sys.databases WHERE name = '{target_db}') BEGIN CREATE DATABASE [{target_db}] END")
    cursor.close()
    conn.close()


def ensure_tables():
    conn = pyodbc.connect(_build_conn_str(DATABASE_CONFIG["database"]))
    cursor = conn.cursor()
    cursor.execute(
        """
        IF OBJECT_ID('users', 'U') IS NULL
        CREATE TABLE users (
            id INT IDENTITY(1,1) PRIMARY KEY,
            username NVARCHAR(100) NOT NULL UNIQUE,
            password NVARCHAR(255) NOT NULL,
            role NVARCHAR(20) NOT NULL DEFAULT 'user',
            created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
        )
        """
    )
    cursor.execute(
        """
        IF OBJECT_ID('comments', 'U') IS NULL
        CREATE TABLE comments (
            id INT IDENTITY(1,1) PRIMARY KEY,
            post_id NVARCHAR(255) NOT NULL,
            user_id INT NOT NULL FOREIGN KEY REFERENCES users(id),
            content NVARCHAR(MAX) NOT NULL,
            created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
            is_deleted BIT NOT NULL DEFAULT 0,
            parent_comment_id INT NULL FOREIGN KEY REFERENCES comments(id)
        )
        """
    )
    cursor.execute(
        """
        IF COL_LENGTH('comments', 'parent_comment_id') IS NULL
        ALTER TABLE comments ADD parent_comment_id INT NULL FOREIGN KEY REFERENCES comments(id)
        """
    )
    cursor.execute(
        """
        IF OBJECT_ID('comment_likes', 'U') IS NULL
        CREATE TABLE comment_likes (
            id INT IDENTITY(1,1) PRIMARY KEY,
            comment_id INT NOT NULL FOREIGN KEY REFERENCES comments(id) ON DELETE CASCADE,
            user_id INT NOT NULL FOREIGN KEY REFERENCES users(id) ON DELETE CASCADE,
            created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
            CONSTRAINT UQ_comment_likes UNIQUE (comment_id, user_id)
        )
        """
    )
    conn.commit()
    cursor.close()
    conn.close()


def seed_admin():
    conn = pyodbc.connect(_build_conn_str(DATABASE_CONFIG["database"]))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    existing_admins = cursor.fetchone()[0]
    if not existing_admins:
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, 'admin')",
            (APP_SETTINGS["default_admin_username"], APP_SETTINGS["default_admin_password"]),
        )
        conn.commit()
        print(f"Created default admin '{APP_SETTINGS['default_admin_username']}'")
    cursor.close()
    conn.close()


def main():
    try:
        ensure_database()
        ensure_tables()
        seed_admin()
    except pyodbc.Error as exc:
        print(f"Failed to initialize database: {exc}")
        sys.exit(1)
    print("Database ready.")


if __name__ == "__main__":
    main()
