from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config import settings

app = FastAPI(title=settings.app_name)
app.include_router(router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", response_class=HTMLResponse)
def home():
    with open("app/templates/index.html", "r", encoding="utf-8") as file:
        return file.read()


@app.get("/health")
def health():
    return {"status": "ok"}
