#!/bin/bash
# Quick activation helper
# Usage: source activate.sh

if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated"
    echo "  Python: $(python --version)"
    echo "  Location: $(which python)"
    echo ""
    echo "Deactivate with: deactivate"
else
    echo "❌ venv/ not found. Run ./setup.sh first"
    return 1 2>/dev/null || exit 1
fi