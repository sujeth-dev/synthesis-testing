#!/bin/bash
set -e

echo ""
echo "============================================================"
echo "  ADAPTIVE LEARNING SYSTEM LAB v1.0"
echo "  BKT + SM-2 + Decision Engine + Interactive Dashboard"
echo "============================================================"
echo ""

# Check Python
echo "[1/6] Checking Python..."
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "[ERROR] Python not found. Install Python 3.8+ first."
    exit 1
fi
echo "[OK] $($PYTHON --version)"

# Virtual env
echo ""
echo "[2/6] Setting up virtual environment..."
if [ ! -d "venv" ]; then
    $PYTHON -m venv venv
    echo "[OK] Created"
else
    echo "[OK] Exists"
fi

# Activate
echo ""
echo "[3/6] Activating..."
source venv/bin/activate
echo "[OK] Activated"

# Install
echo ""
echo "[4/6] Installing dependencies..."
pip install -r requirements.txt -q
echo "[OK] Done"

# Datasets
echo ""
echo "[5/6] Pre-generating datasets..."
mkdir -p data
python -c "import sys; sys.path.insert(0,'backend'); from datasets import preload_all; preload_all()"
echo "[OK] Datasets ready"

# Launch
echo ""
echo "[6/6] Starting server..."
echo "  Dashboard: http://localhost:5000"
echo ""

# Open browser
if command -v open &>/dev/null; then
    (sleep 3 && open http://localhost:5000) &
elif command -v xdg-open &>/dev/null; then
    (sleep 3 && xdg-open http://localhost:5000) &
fi

python backend/server.py
