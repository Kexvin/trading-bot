"""
QuantOS™ v9.8.0 - Golden Master Server
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
import os
import sys
from fastapi import APIRouter, Request, Body, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

# Router for all UI and API logic
router = APIRouter()

# Routes
@router.get("/health")
async def health_check():
    return {"status": "online", "version": "9.8.0"}

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return request.app.state.templates.TemplateResponse("index.html", {"request": request, "page": "dashboard"})

@router.get("/welcome", response_class=HTMLResponse)
async def welcome_page(request: Request):
    return request.app.state.templates.TemplateResponse("welcome.html", {"request": request})

@router.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    return request.app.state.templates.TemplateResponse("analytics.html", {"request": request, "page": "analytics"})

@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    return request.app.state.templates.TemplateResponse("settings.html", {"request": request, "page": "settings"})

@router.get("/backtester", response_class=HTMLResponse)
async def backtester_page(request: Request):
    return request.app.state.templates.TemplateResponse("backtester.html", {"request": request, "page": "backtester"})

@router.get("/api/settings")
async def get_settings():
    from config.settings_manager import settings_manager
    return settings_manager.settings

@router.post("/api/toggle-pause")
async def toggle_pause():
    from config.settings_manager import settings_manager
    current = settings_manager.get("bot_paused")
    settings_manager.save_settings({"bot_paused": not current})
    return {"paused": not current}

@router.get("/api/dashboard")
async def get_dashboard():
    from strategies import analytics
    from config.settings_manager import settings_manager
    stats = analytics.get_performance_stats()
    return {
        "equity": stats.get("total_equity", 0.0),
        "today_pnl": stats.get("total_profit", 0.0),
        "win_rate": stats.get("win_rate", 0),
        "portfolio": [],
        "logs": [],
        "bot_paused": settings_manager.get("bot_paused")
    }
