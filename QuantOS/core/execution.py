"""
QuantOS™ v7.0.0 - Execution Engine
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
from core.logger_config import get_logger
from core.money_manager import money_manager
from core.tax_engine import tax_engine
from core import ledger
from core import notifier
import os
import asyncio

logger = get_logger("execution")

class ExecutionEngine:
    def __init__(self, broker):
        self.broker = broker
        self.webhook = os.getenv("DISCORD_WEBHOOK_URL")

    async def execute_smart_order(self, symbol, side, amount, settings):
        """
        Calculates a 'Marketable Limit Order' price to balance fill rate vs slippage.
        """
        max_slippage_pct = settings.get("max_slippage_pct", 0.5) / 100.0
        timeout = settings.get("execution_timeout", 30)
        
        try:
            current_price = self.broker.get_latest_price(symbol)
            if current_price <= 0:
                return {"error": f"Invalid price for {symbol}"}, 0

            if side.lower() == "buy":
                limit_price = round(current_price * (1 + max_slippage_pct), 3)
            else:
                limit_price = round(current_price * (1 - max_slippage_pct), 3)

            logger.info(f"⚡ Smart Limit ({side.upper()}): Current ${current_price:.2f} -> Limit ${limit_price:.2f}")
            
            # Place the limit order
            res = self.broker.submit_order(symbol, amount, side, order_type="limit", limit_price=limit_price)
            
            # Note: A true 'Chase' loop or timeout would require order tracking IDs 
            # which varies by broker. For v6.3, we'll stick to the Marketable Limit protection.
            return res, current_price
        except Exception as e:
            logger.error(f"Smart order failed: {e}")
            return {"error": str(e)}, 0

    async def execute_buy(self, symbol, score, indicators, settings):
        """
        The Gatekeeper: Strict threshold check before buying.
        """
        min_threshold = settings.get("min_confidence_threshold", 75)
        
        if score < min_threshold:
            logger.info(f"⏭️ Skipping {symbol}: Score {score} is below threshold {min_threshold}.")
            return False

        # --- CFO CHECK: Wash Sale Guard ---
        if settings.get("wash_sale_guard_enabled"):
            if tax_engine.is_wash_sale_risk(symbol):
                logger.warning(f"🚫 Skipping {symbol} buy: Wash Sale Risk (Sold for loss <30 days ago).")
                return False

        logger.info(f"🚀 GATEKEEPER APPROVED: {symbol} with score {score}!")

        # 1. Calculate Position Size
        try:
            buying_power = self.broker.get_buying_power()
            
            if buying_power <= 0:
                logger.error("❌ Cannot calculate position size: Buying power is 0.")
                return False

            buy_amount = money_manager.calculate_position_size(buying_power, score)
            
            if buy_amount <= 0:
                logger.info(f"💰 Money Manager suggested $0 for {symbol}. Skipping.")
                return False

            # 2. Execution
            is_paper = settings.get("environment").upper() == "PAPER"
            
            if is_paper:
                current_price = self.broker.get_latest_price(symbol)
                logger.info(f"📝 PAPER BUY: {symbol} (${buy_amount:.2f} Simulated)")
                ledger.record_trade("BUY", symbol, current_price, buy_amount/current_price, f"Score: {score}", tax_impact=0.0)
                return True
            else:
                res, current_price = await self.execute_smart_order(symbol, "buy", buy_amount, settings)
                if "error" not in res:
                    qty = buy_amount / current_price 
                    ledger.record_trade("BUY", symbol, current_price, qty, f"Score: {score}", tax_impact=0.0)
                    notifier.send_alert(f"🚨 **BUY:** {symbol} @ ${current_price:.2f} (Smart Limit)", self.webhook)
                    return True
                else:
                    logger.error(f"❌ Execution failed for {symbol}: {res['error']}")
                    return False

        except Exception as e:
            logger.error(f"❌ Execution failed for {symbol}: {e}")
            return False

    async def execute_sell(self, symbol, current_price, quantity, reason, settings):
        """
        Handles selling and recording with tax impact estimation.
        """
        try:
            # Calculate PnL for tax estimation
            avg_buy_price = ledger.get_average_buy_price(symbol)
            gross_pnl = (current_price - avg_buy_price) * quantity if avg_buy_price else 0.0
            est_tax = tax_engine.estimate_tax_bill(gross_pnl)

            is_paper = settings.get("environment").upper() == "PAPER"
            if is_paper:
                logger.info(f"📝 PAPER SELL: {symbol} (Simulated) - {reason}")
                ledger.record_trade("SELL", symbol, current_price, quantity, f"{reason} (PAPER)", tax_impact=est_tax)
            else:
                sell_amount = quantity * current_price
                res, _ = await self.execute_smart_order(symbol, "sell", sell_amount, settings)
                if "error" not in res:
                    ledger.record_trade("SELL", symbol, current_price, quantity, reason, tax_impact=est_tax)
                    notifier.send_alert(f"📉 **SELL:** {symbol} - {reason} (Est Tax: ${est_tax:.2f})", self.webhook)
                else:
                    logger.error(f"❌ Sell execution failed for {symbol}: {res['error']}")
                    return False
            return True
        except Exception as e:
            logger.error(f"❌ Sell failed for {symbol}: {e}")
            return False
