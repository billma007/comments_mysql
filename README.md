# Hexo Comment Stack

Python + SQL Server backend for handling blog comments while keeping Hexo static.

**Warning : This project is for course design purposes only and does not include encryption or security features.  Please DO NOT deploy this code directly on the internet.**

Project details: https://billma.top/2026/01/08/comments-hexo/

## 1. Prerequisites

- Python 3.10+
- SQL Server (Developer / Express)
- ODBC Driver 18 for SQL Server (or adjust driver in `backend/config.py`)

## 2. Configure Environment

Set these env vars (PowerShell example):

```powershell
$env:SQLSERVER_SERVER = "localhost"
$env:SQLSERVER_USERNAME = "sa"
$env:SQLSERVER_PASSWORD = "YourStrong!Passw0rd"
$env:SQLSERVER_DATABASE = "HexoComments"
$env:DEFAULT_ADMIN_USERNAME = "admin"
$env:DEFAULT_ADMIN_PASSWORD = "admin123"
```

## 3. Install Dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## 4. Initialize SQL Server

```powershell
python init_db.py
```

Database script creates tables and seeds an admin (credentials from env or defaults).

## 5. Run FastAPI

```powershell
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

- `http://localhost:8000/static/comments.js` → embeddable Hexo script
- `http://localhost:8000/admin` → admin console

## 6. Embed in Hexo

1. Copy `backend/static/comments.js` to `themes/<theme>/source/js/` or load directly from the running server.
2. In the Hexo post layout add:

```html
<div id="hexo-comments-root" data-post-id="{{ page.permalink }}"></div>
<script>
  window.HEX0_COMMENTS_CONFIG = {
    apiBase: 'https://your-domain.com',
    postId: '{{ page.permalink }}'
  };
</script>
<script src="https://your-domain.com/static/comments.js" defer></script>
```

## 7. API Overview

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/api/users/register` | POST | Register normal user |
| `/api/users/login` | POST | Login, receive token |
| `/api/comments` | GET | Public comments for a post |
| `/api/comments` | POST | Add comment (needs token) |
| `/api/admin/comments` | GET | Admin moderation feed |
| `/api/admin/delete_comment` | POST | Soft delete |
| `/api/admin/create` | POST | Create new admin |

Tokens are simple in-memory sessions (resets on server restart). Keep FastAPI process running to preserve sessions.

## 8. Next Steps

- Add HTTPS / reverse proxy before going live
- Consider hashing passwords before production use
- Add pagination and rate limiting as your blog grows
