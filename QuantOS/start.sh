#!/bin/bash

# ==========================================
#        QUANTOS AUTO-BOOTSTRAPPER (v8.9.1)
# Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
# ==========================================

# 1. Handle Git Bash/Cygwin hangs
PYTHON_CMD="python"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    echo "🪟 Windows Unix-Emulator detected. Enabling winpty support..."
    PYTHON_CMD="winpty python.exe"
fi

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "🚀 QuantOS Bootstrapper Initialized..."

# 0. Aggressive Cloud Sync
if [ -d ".git" ]; then
    echo "☁️  Forcing cloud synchronization..."
    git fetch --all --quiet
    # Overwrite local changes to ensure 100% parity with master
    git reset --hard origin/main --quiet
    echo "✅ Code synchronized with master repository."
fi

# 1. Setup Virtual Env
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv || python -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ CRITICAL: Failed to create virtual environment."
        exit 1
    fi
fi

# 2. Activate (Cross-platform activation)
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    echo "❌ ERROR: Activation script not found."
    exit 1
fi

# 3. Auto-Install Dependencies
echo "🔎 Checking dependencies..."
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet

# 4. Pre-flight Validation
export PYTHONPATH=$PYTHONPATH:.
python scripts/validate_env.py
if [ $? -ne 0 ]; then
    echo "❌ CRITICAL: Environment validation failed."
    exit 1
fi

# 5. Launch the Main Brain
echo "🧠 Starting Bot Engine..."
# We use the determined PYTHON_CMD to handle Git Bash properly
$PYTHON_CMD main.py
