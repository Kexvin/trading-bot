"""
QuantOS™ v7.0.0 - Robinhood Adapter
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
import robin_stocks.robinhood as rh
import os
from core.broker_interface import BrokerInterface
from core.logger_config import get_logger

logger = get_logger("robinhood_adapter")

class RobinhoodAdapter(BrokerInterface):
    def __init__(self):
        self.Username = os.getenv("ROBINHOOD_UserNAME") or os.getenv("RH_UserNAME")
        self.password = os.getenv("ROBINHOOD_PASSWORD") or os.getenv("RH_PASSWORD")
        self.totp = os.getenv("ROBINHOOD_TOTP") or os.getenv("RH_TOTP_SECRET")

    def authenticate(self):
        logger.info("🔐 Connecting to Robinhood...")
        try:
            rh.login(Username=self.Username, password=self.password, store_session=True, mfa_code=self.totp)
            logger.info("✅ Robinhood Authenticated.")
            return True
        except Exception as e:
            logger.error(f"❌ Robinhood Login Failed: {e}")
            return False

    def get_buying_power(self) -> float:
        try:
            profile = rh.profiles.load_account_profile()
            return float(profile.get('portfolio_cash', 0))
        except Exception as e:
            logger.error(f"Error fetching buying power: {e}")
            return 0.0

    def get_positions(self) -> list:
        try:
            holdings = rh.build_holdings()
            positions = []
            for ticker, data in holdings.items():
                positions.append({
                    "symbol": ticker,
                    "quantity": float(data.get('quantity', 0)),
                    "market_value": float(data.get('equity', 0)),
                    "average_buy_price": float(data.get('average_buy_price', 0))
                })
            return positions
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return []

    def get_latest_price(self, symbol: str) -> float:
        try:
            quote = rh.stocks.get_latest_price(symbol)
            if quote and quote[0]:
                return float(quote[0])
            return 0.0
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return 0.0

    def submit_order(self, symbol: str, amount: float, side: str, order_type: str = "market", limit_price: float = None) -> dict:
        """
        Robinhood supports fractional orders by price for market orders.
        For limit orders, we convert to quantity.
        """
        try:
            if order_type.lower() == "limit" and limit_price:
                qty = int(amount / limit_price) if limit_price > 0 else 0
                if qty <= 0:
                    return {"error": "Quantity 0"}
                
                if side.lower() == "buy":
                    res = rh.orders.order_buy_limit(symbol, qty, limit_price)
                else:
                    res = rh.orders.order_sell_limit(symbol, qty, limit_price)
            else:
                if side.lower() == "buy":
                    res = rh.orders.order_buy_fractional_by_price(symbol, amount)
                else:
                    res = rh.orders.order_sell_fractional_by_price(symbol, amount)
            
            logger.info(f"📝 Robinhood {side.upper()} {order_type.upper()} order for {symbol} (${amount}) submitted.")
            return res
        except Exception as e:
            logger.error(f"❌ Robinhood order failed: {e}")
            return {"error": str(e)}

    def cancel_all_orders(self):
        try:
            rh.orders.cancel_all_stock_orders()
            logger.info("✅ All Robinhood stock orders cancelled.")
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")
