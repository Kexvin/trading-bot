"""
QuantOS™ v7.0.0 - Alpaca Adapter
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
import os
from core.broker_interface import BrokerInterface
from core.logger_config import get_logger

logger = get_logger("alpaca_adapter")

class AlpacaAdapter(BrokerInterface):
    def __init__(self):
        self.api_key = os.getenv("APCA_API_KEY_ID") or os.getenv("ALPACA_API_KEY")
        self.secret_key = os.getenv("APCA_API_SECRET_KEY") or os.getenv("ALPACA_SECRET_KEY")
        self.base_url = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")
        
        # Determine paper mode from new PAPER_MODE or old ENVIRONMENT
        paper_env = os.getenv("PAPER_MODE")
        if paper_env is not None:
            self.paper = paper_env.lower() == "true"
        else:
            self.paper = os.getenv("ENVIRONMENT", "PAPER").upper() == "PAPER"
            
        self.client = None
        self.data_client = None

    def authenticate(self):
        logger.info("🔐 Connecting to Alpaca...")
        try:
            self.client = TradingClient(self.api_key, self.secret_key, paper=self.paper)
            self.data_client = StockHistoricalDataClient(self.api_key, self.secret_key)
            logger.info(f"✅ Alpaca Authenticated (Paper: {self.paper}).")
            return True
        except Exception as e:
            logger.error(f"❌ Alpaca Connection Failed: {e}")
            return False

    def get_buying_power(self) -> float:
        try:
            account = self.client.get_account()
            return float(account.buying_power)
        except Exception as e:
            logger.error(f"Error fetching buying power: {e}")
            return 0.0

    def get_positions(self) -> list:
        try:
            alpaca_positions = self.client.get_all_positions()
            positions = []
            for p in alpaca_positions:
                positions.append({
                    "symbol": p.symbol,
                    "quantity": float(p.qty),
                    "market_value": float(p.market_value),
                    "average_buy_price": float(p.avg_entry_price)
                })
            return positions
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return []

    def get_latest_price(self, symbol: str) -> float:
        try:
            request_params = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            latest_quote = self.data_client.get_stock_latest_quote(request_params)
            return float(latest_quote[symbol].ask_price)
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return 0.0

    def submit_order(self, symbol: str, amount: float, side: str, order_type: str = "market", limit_price: float = None) -> dict:
        try:
            order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
            
            if order_type.lower() == "limit" and limit_price:
                # For limit orders, Alpaca requires quantity, not notional
                current_price = self.get_latest_price(symbol)
                qty = int(amount / limit_price) if limit_price > 0 else 0
                if qty <= 0:
                    return {"error": "Quantity 0"}
                
                order_data = LimitOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    limit_price=limit_price,
                    side=order_side,
                    time_in_force=TimeInForce.DAY
                )
            else:
                # Alpaca supports notional (dollar amount) for market orders
                order_data = MarketOrderRequest(
                    symbol=symbol,
                    notional=amount,
                    side=order_side,
                    time_in_force=TimeInForce.DAY
                )
            
            order = self.client.submit_order(order_data=order_data)
            logger.info(f"📝 Alpaca {side.upper()} {order_type.upper()} order for {symbol} (${amount}) submitted.")
            return dict(order)
        except Exception as e:
            logger.error(f"❌ Alpaca order failed: {e}")
            return {"error": str(e)}

    def cancel_all_orders(self):
        try:
            self.client.cancel_orders()
            logger.info("✅ All Alpaca orders cancelled.")
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")
