"""
QuantOS™ v9.5.0 - Self-Healing Launcher
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
import os
import sys
import socket
import threading
import time
import webbrowser
import requests
import uvicorn
from interface import create_app
from core.engine import TradingEngine
from core.logger_config import get_logger

logger = get_logger("launcher")

# --- CONFIGURATION ---
START_PORT = 5000
MAX_PORT_RETRIES = 10
CHECK_INTERVAL = 0.5  # Seconds between health checks
MAX_WAIT_TIME = 10    # Max seconds to wait for server

def find_available_port(start_port, max_retries):
    """Scans for a free port starting from start_port."""
    for port in range(start_port, start_port + max_retries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # connect_ex returns 0 if the port is busy/open
            if sock.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return None

def wait_for_server(port):
    """Pings the server until it responds or times out."""
    url = f"http://127.0.0.1:{port}/"
    start_time = time.time()
    
    print(f"🏥 Performing health checks on port {port}...", end="", flush=True)
    
    while time.time() - start_time < MAX_WAIT_TIME:
        try:
            # We check if the server is up and returning something
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                print(" ✅ ONLINE")
                return True
        except (requests.ConnectionError, requests.Timeout):
            pass
        time.sleep(CHECK_INTERVAL)
        print(".", end="", flush=True)
    
    print(" ❌ TIMEOUT")
    return False

def launch_browser_safely(port):
    """Waits for server health check, then opens browser."""
    if wait_for_server(port):
        print(f"🚀 Launching Dashboard: http://127.0.0.1:{port}")
        webbrowser.open(f"http://127.0.0.1:{port}")
    else:
        print("\n⚠️  WARNING: Browser launch skipped (Server not responding).")
        print(f"   Please manually visit: http://127.0.0.1:{port}")

def start_engine_background():
    """Starts the trading bot without blocking the UI."""
    try:
        logger.info("📡 Initializing Trading Engine thread...")
        bot = TradingEngine()
        if bot.is_market_open():
            bot.run()
        else:
            print("🌙 Market Closed. Bot is in 'Sleep Mode' (Monitoring Only).")
            logger.info("Market Closed. Monitoring only.")
    except Exception as e:
        logger.error(f"⚠️  Engine Error: {e}")
        print(f"\n⚠️  TRADING ENGINE ERROR: {e}")

# --- MAIN ENTRY POINT ---
if __name__ == "__main__":
    # 1. Dynamic Port Selection
    port = find_available_port(START_PORT, MAX_PORT_RETRIES)
    if not port:
        print(f"❌ CRITICAL: No available ports found ({START_PORT}-{START_PORT+MAX_PORT_RETRIES} are all busy).")
        sys.exit(1)

    print(f"✅ Selected Port: {port}")

    # 2. Initialize App (FastAPI)
    app = create_app()

    # 3. Start Trading Engine (Background Thread)
    engine_thread = threading.Thread(target=start_engine_background, daemon=True)
    engine_thread.start()

    # 4. Start Browser Launcher (Background Thread)
    launcher_thread = threading.Thread(target=launch_browser_safely, args=(port,), daemon=True)
    launcher_thread.start()

    # 5. Start Web Server (Blocking)
    print("⚡ Starting QuantOS Web Server...")
    try:
        # Note: FastAPI uses uvicorn.run instead of app.run
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="error")
    except Exception as e:
        print(f"❌ Server Crash: {e}")
        logger.error(f"Server crashed: {e}")
