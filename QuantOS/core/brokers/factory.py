"""
QuantOS™ v8.7.0 - Broker Factory
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
import os
from config.settings_manager import settings_manager

def get_broker():
    # Priority: Settings Manager (UI controlled) -> Environment Variable -> Default
    broker_name = settings_manager.get("active_broker")
    if not broker_name:
        broker_name = os.getenv("ACTIVE_BROKER", "ibkr")
    
    broker_name = broker_name.lower()
    
    # Dynamic imports to prevent unnecessary library initialization
    if broker_name == "alpaca":
        from core.brokers.alpaca import AlpacaAdapter
        return AlpacaAdapter()
    elif broker_name == "robinhood":
        from core.brokers.robinhood import RobinhoodAdapter
        return RobinhoodAdapter()
    elif broker_name == "ibkr":
        from core.brokers.ibkr import IBKRAdapter
        return IBKRAdapter()
    elif broker_name == "schwab":
        from core.brokers.schwab import SchwabAdapter
        return SchwabAdapter()
    else:
        raise ValueError(f"Unknown broker: {broker_name}")
