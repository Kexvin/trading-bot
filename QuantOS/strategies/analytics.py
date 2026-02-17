import pandas as pd
import numpy as np
import os
from config.settings_manager import settings_manager

# FORCE CORRECT FOLDER
os.chdir(os.path.dirname(os.path.abspath(__file__)))

LEDGER_FILE = "survivor_ledger.csv"

def get_performance_stats():
    """
    Reads the ledger, calculates detailed metrics including Sharpe and Tax Efficiency.
    """
    if not os.path.exists(LEDGER_FILE):
        return {"win_rate": 0, "status": "No Data"}

    try:
        df = pd.read_csv(LEDGER_FILE)
    except Exception:
        return {"win_rate": 0, "status": "Empty Ledger"}

    if df.empty:
        return {"win_rate": 0, "status": "Empty Ledger"}

    # Track completed trades (FIFO matching)
    completed_profits = []
    daily_pnl = {}
    total_tax_impact = 0.0
    positions = {} # ticker: [[qty, price], ...]

    for _, row in df.iterrows():
        ticker = row['Ticker']
        action = row['Action']
        price = float(row['Price'])
        qty = float(row['Quantity'])
        date_str = str(row['Date']).split(' ')[0]
        tax_impact = float(row.get('Est_Tax_Impact', 0.0))
        total_tax_impact += tax_impact

        if ticker not in positions:
            positions[ticker] = []

        if action == 'BUY':
            positions[ticker].append([qty, price])
        elif action == 'SELL':
            shares_to_sell = qty
            trade_profit = 0
            while shares_to_sell > 0 and positions[ticker]:
                buy_qty, buy_price = positions[ticker][0]
                
                if buy_qty <= shares_to_sell:
                    trade_profit += buy_qty * (price - buy_price)
                    shares_to_sell -= buy_qty
                    positions[ticker].pop(0)
                else:
                    trade_profit += shares_to_sell * (price - buy_price)
                    positions[ticker][0][0] -= shares_to_sell
                    shares_to_sell = 0
            
            completed_profits.append(trade_profit)
            daily_pnl[date_str] = daily_pnl.get(date_str, 0.0) + trade_profit

    if not completed_profits:
        return {
            "win_rate": 0, 
            "total_profit": 0, 
            "status": "No Closed Trades"
        }

    wins = [p for p in completed_profits if p > 0]
    losses = [p for p in completed_profits if p < 0]
    
    win_rate = (len(wins) / len(completed_profits)) * 100
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else gross_profit
    
    total_profit = sum(completed_profits)
    net_profit = total_profit - total_tax_impact
    tax_efficiency = (net_profit / total_profit * 100) if total_profit > 0 else 0
    
    # Sharpe Ratio (Simplified Daily)
    if len(daily_pnl) > 1:
        returns = pd.Series(list(daily_pnl.values()))
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
    else:
        sharpe = 0.0

    return {
        "win_rate": win_rate,
        "total_profit": total_profit,
        "net_profit": net_profit,
        "tax_efficiency": tax_efficiency,
        "profit_factor": profit_factor,
        "sharpe_ratio": sharpe,
        "total_trades": len(completed_profits),
        "daily_pnl": daily_pnl,
        "status": "Active"
    }

def get_coaching_advice(stats):
    """
    Returns a 'Mode' for the Brain based on performance.
    """
    if stats['status'] != "Active":
        return "NORMAL", "Not enough data yet. Stick to the plan."
        
    wr = stats['win_rate']
    
    if wr < 40:
        return "DEFENSIVE", "⚠️ We are losing too much. Tightening RSI to < 25."
    elif wr > 70:
        return "AGGRESSIVE", "🔥 We are on fire! Loosening RSI to < 35."
    else:
        return "NORMAL", "✅ Steady performance. Keeping RSI at 30."

if __name__ == "__main__":
    stats = get_performance_stats()
    mode, advice = get_coaching_advice(stats)
    print(f"📊 Win Rate: {stats['win_rate']:.1f}%")
    print(f"💰 Total Profit: ${stats['total_profit']:.2f}")
    print(f"🧠 Coach Says: {advice}")
