"""FastAPI entrypoint for the Hexo comment system."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from backend.api import admin_api, comment_api, user_api

APP_ROOT = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=str(APP_ROOT / "templates"))

app = FastAPI(title="Hexo Comment Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(user_api.router)
app.include_router(comment_api.router)
app.include_router(admin_api.router)

app.mount("/static", StaticFiles(directory=str(APP_ROOT / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return "<h3>Hexo Comment API is running.</h3>"

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})


@app.get("/health")
async def healthcheck():
    return {"status": "ok"}
