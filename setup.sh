#!/bin/bash
# SCD41 Validation Study - Setup Script
# Sets up Python environment and directory structure

set -e  # Exit on error

echo "================================================"
echo "SCD41 Validation Study - Environment Setup"
echo "================================================"

# 1. Check Python version
echo ""
echo "[1/5] Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found. Please install Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
echo "✓ Found Python $PYTHON_VERSION"

# 2. Create virtual environment
echo ""
echo "[2/5] Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  venv/ already exists, skipping creation"
else
    python3 -m venv venv
    echo "✓ Created venv/"
fi

# 3. Activate and install dependencies
echo ""
echo "[3/5] Installing dependencies..."
source venv/bin/activate

# Upgrade pip first
pip install --quiet --upgrade pip

# Install core dependencies
pip install --quiet \
    pandas \
    numpy \
    pyarrow \
    pyyaml \
    jupyter \
    matplotlib \
    seaborn

echo "✓ Installed Python packages"

# 4. Create output directories
echo ""
echo "[4/5] Creating output directories..."
mkdir -p output/individual
mkdir -p output/merged
mkdir -p output/merged/parquet
mkdir -p output/parquet
mkdir -p output/logs
mkdir -p output/plots

echo "✓ Created output structure:"
echo "   output/individual/    - Individual sensor CSVs"
echo "   output/merged/        - Merged datasets (CSV)"
echo "   output/merged/parquet/- Merged datasets (Parquet)"
echo "   output/parquet/       - Individual sensor Parquet"
echo "   output/logs/          - Processing logs"
echo "   output/plots/         - Visualization outputs"

# 5. Verify src/ exists
echo ""
echo "[5/5] Verifying project structure..."
if [ ! -d "src" ]; then
    echo "❌ Error: src/ directory not found"
    echo "   Please ensure you're running this from the project root"
    exit 1
fi

if [ ! -f "sensors.yaml" ]; then
    echo "⚠️  Warning: sensors.yaml not found"
    echo "   You'll need to configure sensor paths before processing"
fi

echo "✓ Project structure verified"

# Done!
echo ""
echo "================================================"
echo "✓ Setup complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Activate environment:  source venv/bin/activate"
echo "2. Configure sensors:     edit sensors.yaml"
echo "3. Start Jupyter:         jupyter notebook"
echo "4. Or run processing:     python -m src.pipeline"
echo ""
echo "Deactivate with: deactivate"