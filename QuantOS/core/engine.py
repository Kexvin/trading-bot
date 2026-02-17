"""
QuantOS™ v9.4.0 - Trading Engine Core
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
import asyncio
import os
import sys
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Core Imports
from core import brain
from core import ledger
from core import tickers
from core.execution import ExecutionEngine
from core.logger_config import get_logger
from core.risk_manager import RiskManager
from core.brokers.factory import get_broker
from core.data.streamer import MarketStream
from core.collector import DataCollector
from strategies.analysis import calculate_confidence_score
from config.settings_manager import settings_manager

logger = get_logger("engine")

class TradingEngine:
    def __init__(self):
        self.version = "9.4.0"
        self.collector = None
        self.broker = None
        self.is_running = False

    def initialize(self):
        """Pre-flight checks and initialization."""
        self.collector = DataCollector()
        load_dotenv()
        self.broker = get_broker()
        if not self.broker.authenticate():
            raise ConnectionError(f"Failed to authenticate with {os.getenv('ACTIVE_BROKER')}")
        ledger.init_ledger()
        logger.info(f"🚀 Trading Engine v{self.version} Initialized")

    def is_market_open(self):
        """Checks if the US Equity market is currently open."""
        try:
            # Simple check via broker or current time
            now = datetime.now()
            # Market hours: 9:30 AM - 4:00 PM EST
            # This is a simplified check; brokers like Alpaca have better API for this
            if hasattr(self.broker, "is_market_open"):
                return self.broker.is_market_open()
            
            # Fallback to local time check (assumes local is EST for this snippet)
            is_weekday = now.weekday() < 5
            is_hours = (9, 30) <= (now.hour, now.minute) < (16, 0)
            return is_weekday and is_hours
        except:
            return False

    async def trade_loop(self):
        """The main trading loop logic."""
        risk_manager = RiskManager(self.broker)
        execution_engine = ExecutionEngine(self.broker)
        watchlist = tickers.WATCHLIST

        while self.is_running:
            if settings_manager.get("bot_paused"):
                await asyncio.sleep(60)
                continue

            logger.info(f"🔎 Scanning {len(watchlist)} assets...")
            for stock in watchlist:
                try:
                    current_price = self.broker.get_latest_price(stock)
                    if current_price <= 0: continue

                    # Analysis (Simplified for brevity in this refactor)
                    import robin_stocks.robinhood as rh
                    history = rh.stocks.get_stock_historicals(stock, interval='day', span='year')
                    if not history: continue
                    
                    df = pd.DataFrame(history)
                    df['Close'] = pd.to_numeric(df['close_price'], errors='coerce')
                    rsi_rt = brain.realtime_brain.calculate_rsi(stock)
                    score, indicators = calculate_confidence_score(stock, df, rsi_rt, is_simulation=False)

                    # Execution
                    if not ledger.has_position(stock):
                        await execution_engine.execute_buy(stock, score, indicators, settings_manager.settings)
                    else:
                        # Trailing Stop Logic here...
                        pass

                    await asyncio.sleep(0.1)
                except Exception as e:
                    logger.warning(f"⚠️ Error scanning {stock}: {e}")

            await asyncio.sleep(60)

    async def start_async(self):
        self.is_running = True
        self.initialize()
        
        # Start market streamer and trade loop
        market_stream = MarketStream(tickers.WATCHLIST[:200], self.on_market_update, broker=self.broker)
        await asyncio.gather(self.trade_loop(), market_stream.start())

    def run(self):
        """Synchronous wrapper for threading."""
        asyncio.run(self.start_async())

    async def on_market_update(self, symbol, data_type, data):
        if data_type == "trade":
            price = data.get("price")
            if price:
                brain.realtime_brain.update_price(symbol, price)
