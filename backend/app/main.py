"""Titik masuk backend SIS. Jalankan: uvicorn app.main:app --reload --port 8000"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from .api import admin_routes, auth_routes, chat_routes, data_routes
from .config import settings
from .db import engine

PREFIX = "/api/v1"

app = FastAPI(title="School Intelligence System - SMKN 4 Bandung", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_routes.router, prefix=PREFIX)
app.include_router(data_routes.router, prefix=PREFIX)
app.include_router(chat_routes.router, prefix=PREFIX)
app.include_router(admin_routes.router, prefix=PREFIX)


@app.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, dict) else {"code": "ERROR", "message": str(exc.detail), "details": None}
    return JSONResponse({"error": detail}, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError):
    return JSONResponse(
        {"error": {"code": "VALIDATION_ERROR", "message": "Input tidak valid.", "details": exc.errors()}}, status_code=422
    )


@app.exception_handler(Exception)
async def unexpected_error(_: Request, exc: Exception):
    # detail tidak dibocorkan ke klien; lihat log server
    import logging

    logging.getLogger("uvicorn.error").exception("Kesalahan tak terduga", exc_info=exc)
    return JSONResponse({"error": {"code": "INTERNAL", "message": "Terjadi kesalahan di server.", "details": None}}, status_code=500)


@app.get(f"{PREFIX}/health", tags=["sistem"])
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        database = "ok"
    except Exception:  # noqa: BLE001 - status saja, tanpa membocorkan detail
        database = "error"
    return {"status": "ok" if database == "ok" else "degraded", "database": database, "rag": "pencarian leksikal (profil_sekolah.json)", "gemini": "aktif" if settings.gemini_api_key else "tidak aktif (mode aturan)"}
