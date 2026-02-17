# 🛠️ QuantOS Troubleshooting Guide

### 1. The "Black Screen" / Crash on Start
* **Issue:** The window opens and closes instantly.
* **Fix:** We have included a **Self-Healing** launcher. If it still fails, open the `scripts` folder and run `debug_start.bat`. This keeps the window open so you can read the error message.

### 2. "Port 5000 is in use"
* **Issue:** You have another app (like AirPlay or a local server) using the default port.
* **Fix:** **Fixed in v9.5!** The bot now automatically scans ports 5000 through 5010 until it finds an open door. Check the terminal to see which port it picked (e.g., `http://127.0.0.1:5001`).

### 3. Market Data Errors ("Auth Failed")
* **Issue:** The bot crashes when trying to get stock prices.
* **Fix:**
    * If you have **Alpaca Keys**, ensure they are correctly pasted in your `.env` file.
    * If you use **IBKR**, make sure **Trader Workstation (TWS)** is open and "Enable ActiveX and Socket Clients" is checked in TWS Settings.

### 4. "No module named..."
* **Issue:** Python didn't install the necessary libraries correctly.
* **Fix:** Double-click `scripts/clean_install.bat`. This will "nuke" the current environment and rebuild it fresh to ensure all dependencies are met.

---
*For further support, please check the logs in the `logs/` directory.*
