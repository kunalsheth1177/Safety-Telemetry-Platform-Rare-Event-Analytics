#!/bin/bash
# Comprehensive Audit Script for Safety Telemetry Platform
# GENERATED FOR AUDIT PURPOSES

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "Safety Telemetry Platform - Audit Runner"
echo "=========================================="
echo ""

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "[1/4] Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
echo "[2/4] Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "[3/4] Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run audit
echo "[4/4] Running comprehensive audit..."
python audit_report/audit_runner.py

echo ""
echo "=========================================="
echo "Audit complete! Check audit_report/ for results"
echo "=========================================="
