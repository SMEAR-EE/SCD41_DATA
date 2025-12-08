#!/bin/bash
# Quick activation script
# Usage:
#   source activate.sh

if [ -d "venv" ]; then
    # shellcheck disable=SC1091
    source venv/bin/activate
    echo "✓ Virtual environment activated"
    echo ""
    echo "Quick commands:"
    echo "  jupyter notebook           - Start Jupyter"
    echo "  python                     - Python shell"
    echo "  deactivate                 - Exit venv"
    echo ""
else
    echo "ERROR: Virtual environment not found!"
    echo "Run ./setup.sh first"
    # If sourced, 'return' is nicer than 'exit'
    return 1 2>/dev/null || exit 1
fi
