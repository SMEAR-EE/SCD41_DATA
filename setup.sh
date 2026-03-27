#!/bin/bash
# setup.sh — Create venv and install dependencies (local use only)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

MIN_DISK_MB=500
MIN_RAM_GB=8
REC_RAM_GB=16
VENV_DIR="venv"
CONFIG_FILE="config/sensors.yaml"
REQ_FILE="requirements.txt"
REQ_DEV_FILE="requirements_dev.txt"
DEV_MODE=false

# Parse flags
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --dev) DEV_MODE=true ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
    shift
done

# --- Checks ---

# Python 3.10+
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found. Install Python 3.10+" >&2
    exit 1
fi
PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    echo "Error: Python 3.10+ required (found $PY_VER)" >&2
    exit 1
fi
echo "Python $PY_VER"

# Disk space
available_mb=$(df -m "$SCRIPT_DIR" 2>/dev/null | awk 'NR==2 {print $4}')
if [ -n "$available_mb" ] && [ "$available_mb" -lt "$MIN_DISK_MB" ]; then
    echo "Error: ${available_mb} MB available, need at least ${MIN_DISK_MB} MB" >&2
    exit 1
fi

# RAM (warning only)
ram_gb=""
if [ -f /proc/meminfo ]; then
    ram_kb=$(awk '/^MemTotal/ {print $2}' /proc/meminfo)
    ram_gb=$((ram_kb / 1048576))
elif command -v sysctl &> /dev/null; then
    ram_bytes=$(sysctl -n hw.memsize 2>/dev/null || true)
    if [ -n "$ram_bytes" ]; then
        ram_gb=$((ram_bytes / 1073741824))
    fi
fi
if [ -n "$ram_gb" ]; then
    if [ "$ram_gb" -lt "$MIN_RAM_GB" ]; then
        echo "Warning: ${ram_gb} GB RAM detected (min ${MIN_RAM_GB} GB, recommend ${REC_RAM_GB} GB)" >&2
        echo "  The pipeline loads large DataFrames; low memory may cause slow processing." >&2
    fi
fi

# Project structure
if [ ! -d "src" ]; then
    echo "Error: src/ not found — run from project root" >&2
    exit 1
fi
if [ ! -f "$REQ_FILE" ]; then
    echo "Error: $REQ_FILE not found" >&2
    exit 1
fi

# --- venv ---

if [ -d "$VENV_DIR" ]; then
    echo "venv/ exists, skipping creation"
else
    python3 -m venv "$VENV_DIR"
    echo "Created venv/"
fi

source "$VENV_DIR/bin/activate"
pip install --quiet --upgrade pip

# --- Install deps ---

if [ "$DEV_MODE" = true ] && [ -f "$REQ_DEV_FILE" ]; then
    pip install --quiet -r "$REQ_FILE" -r "$REQ_DEV_FILE"
    echo "Installed dependencies ($REQ_FILE + $REQ_DEV_FILE)"
else
    pip install --quiet -r "$REQ_FILE"
    echo "Installed dependencies ($REQ_FILE)"
fi

# --- Config check ---

if [ -f "$CONFIG_FILE" ]; then
    unpopulated=$(grep -E 'input_dir:\s*(#|$)' "$CONFIG_FILE" 2>/dev/null || true)
    if [ -n "$unpopulated" ]; then
        echo "" >&2
        echo "Warning: $CONFIG_FILE has unpopulated input_dir paths:" >&2
        echo "$unpopulated" >&2
        echo "  Edit $CONFIG_FILE before running the pipeline." >&2
    fi
else
    echo "Warning: $CONFIG_FILE not found — copy from template and configure before running" >&2
fi

# --- Done ---

echo ""
echo "Setup complete. Next:"
echo "  source $VENV_DIR/bin/activate"
echo "  jupyter notebook process_data.ipynb   # interactive"
echo "  python -m src.pipeline                # CLI"