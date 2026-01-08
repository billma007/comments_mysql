"""Application-wide configuration helpers."""
from __future__ import annotations

import os

DATABASE_CONFIG = {
    "driver": os.getenv("SQLSERVER_DRIVER", "{ODBC Driver 17 for SQL Server}"),
    "server": os.getenv("SQLSERVER_SERVER", "localhost"),
    "port": os.getenv("SQLSERVER_PORT", "1433"),
    "database": os.getenv("SQLSERVER_DATABASE", "HexoComments"),
    "username": os.getenv("SQLSERVER_USERNAME", "sa"),
    "password": os.getenv("SQLSERVER_PASSWORD", "787805ma"),
    "encrypt": os.getenv("SQLSERVER_ENCRYPT", "no"),
    "trust_server_certificate": os.getenv("SQLSERVER_TRUST_CERT", "yes"),
}

APP_SETTINGS = {
    "token_ttl_seconds": int(os.getenv("APP_TOKEN_TTL", "86400")),
    "default_admin_username": os.getenv("DEFAULT_ADMIN_USERNAME", "admin"),
    "default_admin_password": os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123"),
    "hexo_api_base": os.getenv("HEX0_API_BASE", "http://localhost:8000"),
}
