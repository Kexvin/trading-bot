import os
import yfinance as yf
import pandas as pd
from core.tickers import WATCHLIST

def harvest_watchlist(limit=None):
    # Dynamically use the watchlist from tickers.py
    watchlist = WATCHLIST
    
    # Ensure SPY is included for benchmarking
    if "SPY" not in watchlist:
        watchlist.append("SPY")
    
    if limit:
        watchlist = watchlist[:limit]
    
    if not os.path.exists("data"):
        os.makedirs("data")
        print("📂 Created /data directory.")

    print(f"📥 Starting Global Harvest for {len(watchlist)} tickers...")
    
    for symbol in watchlist:
        try:
            print(f"📡 Downloading {symbol}...")
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="15y")
            
            if df.empty:
                print(f"⚠️ No data found for {symbol}")
                continue
                
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
            df.columns = [col.lower() for col in df.columns]
            
            file_path = f"data/{symbol.lower()}_history.csv"
            df.to_csv(file_path)
            print(f"✅ Saved {symbol}")
        except Exception as e:
            print(f"❌ Failed to harvest {symbol}: {e}")

if __name__ == "__main__":
    import sys
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except:
            pass
    harvest_watchlist(limit=limit)
