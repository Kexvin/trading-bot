"""
QuantOS™ v9.8.0 - Golden Master Server
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
import os
import sys
import traceback
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


@router.get("/api/run_simulation")
async def run_simulation(
    asset: str = "SPY",
    strategy_template: str = "TREND",
    start_year: int | None = None,
    end_year: int | None = None,
    initial_capital: float = 100000.0,
):
    """Runs the Strategy Lab historical simulation and returns year-by-year results."""
    try:
        from strategies.backtester import BacktestEngine

        allowed_templates = {"TREND", "MEAN_REV", "ML_BOOST"}
        normalized_template = (strategy_template or "TREND").upper().strip()
        if normalized_template not in allowed_templates:
            return JSONResponse(
                status_code=400,
                content={"message": f"Unknown strategy_template '{strategy_template}'", "traceback": None},
            )

        engine = BacktestEngine(initial_capital=initial_capital, symbol=asset, strategy_template=normalized_template)

        if start_year is None or end_year is None:
            history_path = os.path.join(engine.data_dir, f"{engine.symbol.lower()}_history.csv")
            if not os.path.exists(history_path):
                return JSONResponse(
                    status_code=500,
                    content={
                        "message": f"CRITICAL: No historical data file found for {engine.symbol}.",
                        "traceback": None,
                    },
                )

            import pandas as pd

            df = pd.read_csv(history_path, usecols=["Date"])
            if df.empty:
                return JSONResponse(
                    status_code=500,
                    content={
                        "message": f"CRITICAL: {engine.symbol} history file is empty.",
                        "traceback": None,
                    },
                )

            dates = pd.to_datetime(df["Date"], errors="coerce", utc=True)
            years = dates.dt.year.dropna().astype(int)
            if years.empty:
                return JSONResponse(
                    status_code=500,
                    content={
                        "message": f"CRITICAL: {engine.symbol} history file has no valid dates.",
                        "traceback": None,
                    },
                )

            min_year = int(years.min())
            max_year = int(years.max())
            start_year = min_year if start_year is None else start_year
            end_year = max_year if end_year is None else end_year

        if start_year > end_year:
            return JSONResponse(
                status_code=400,
                content={"message": "start_year must be <= end_year", "traceback": None},
            )

        return engine.simulate_performance(start_year=start_year, end_year=end_year)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "message": str(e),
                "traceback": traceback.format_exc(),
            },
        )


@router.get("/api/backtest_assets")
async def backtest_assets():
    """Lists available historical datasets based on *_history.csv files in the data directory."""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    assets: list[str] = []
    try:
        for name in os.listdir(data_dir):
            if not name.endswith("_history.csv"):
                continue
            ticker = name[:-len("_history.csv")].strip()
            if not ticker:
                continue
            assets.append(ticker.upper())
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e), "assets": []})

    assets = sorted(set(assets))
    return {"assets": assets}
