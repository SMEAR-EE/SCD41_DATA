#!/bin/bash

# Safe, idempotent setup script for the SMEAR Estonia CO2 project.
# This script NEVER overwrites files silently and NEVER performs destructive actions.

set -euo pipefail

echo "================================================"
echo "  SMEAR Estonia CO2 Processing - Setup"
echo "================================================"

# -------------------------------
# Utility: fail with message
# -------------------------------
fail() {
    echo "❌ ERROR: $1"
    exit 1
}

# -------------------------------
# Check python3 exists
# -------------------------------
if ! command -v python3 >/dev/null 2>&1; then
    fail "Python3 is not installed or not in PATH."
fi

python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Found Python $python_version"

# -------------------------------
# Check requirements.txt exists
# -------------------------------
if [[ ! -f "requirements.txt" ]]; then
    fail "requirements.txt not found in current directory."
fi

# -------------------------------
# Create virtual environment (safe)
# -------------------------------
if [[ -d "venv" ]]; then
    echo "✓ Virtual environment already exists at ./venv"
else
    echo "Creating virtual environment..."
    python3 -m venv venv || fail "Unable to create virtual environment."
fi

# -------------------------------
# Activate environment
# -------------------------------
if [[ -f "venv/bin/activate" ]]; then
    echo "Activating virtual environment..."
    # shellcheck disable=SC1091
    source venv/bin/activate
else
    fail "venv/bin/activate not found — venv creation failed."
fi

# -------------------------------
# Upgrade pip safely
# -------------------------------
echo ""
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel || fail "pip upgrade failed."

# -------------------------------
# Install dependencies safely
# -------------------------------
echo ""
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt || fail "Dependency installation failed."

# -------------------------------
# Create directory structure safely
# -------------------------------
echo ""
echo "Creating directory structure..."

safe_mkdir() {
    if [[ ! -d "$1" ]]; then
        mkdir -p "$1"
        echo "  ✓ Created $1"
    else
        echo "  ✓ Exists: $1"
    fi
}

safe_mkdir "output/individual"
safe_mkdir "output/parquet"
safe_mkdir "output/logs"
safe_mkdir "output/plots"
safe_mkdir "config"

# -------------------------------
# Create default sensors.yaml if missing
# -------------------------------

if [[ ! -f "config/sensors.yaml" ]]; then
    echo "Creating config/sensors.yaml from template..."
    cp config/sensors.example.yaml config/sensors.yaml
    echo "✓ Edit config/sensors.yaml to match your raw data paths."
fi


echo ""
echo "================================================"
echo "  ✓ Setup Complete! (No destructive operations performed)"
echo "================================================"
echo ""
echo "Next steps:"
echo "  1. Activate the environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Edit config/sensors.yaml with your dataset paths"
echo ""
echo "  3. Run the notebook:"
echo "     jupyter notebook notebooks/process_data.ipynb"
echo ""
echo "  Or run directly:"
echo "     python -c 'from src.pipeline import run_pipeline; run_pipeline()'"
echo ""

exit 0
