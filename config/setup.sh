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
safe_mkdir "notebooks"

# -------------------------------
# Create default sensors.yaml if missing
# -------------------------------
if [[ ! -f "config/sensors.yaml" ]]; then
    echo "Creating config/sensors.yaml..."
    read -p "Enter path to your raw SCD41 data: " scd41
    read -p "Enter path to your LGR reference data: " lgr

    cat <<EOF > config/sensors.yaml
sensors:
  - name: CO2_SCT1_2M
    sensor_type: scd41
    sensor_id: null
    input_dir: "$scd41"
    altitude_m: 2
    expected_interval: 60
    co2_range: [0, 5000]
    temp_range: [-40, 70]
    humidity_range: [0, 100]

  - name: LGR_30M
    sensor_type: lgr_csv
    sensor_id: null
    input_dir: "$lgr"
    altitude_m: 30
    expected_interval: 1
    co2_range: [0, 20000]
EOF

    echo "✓ config/sensors.yaml created."
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
