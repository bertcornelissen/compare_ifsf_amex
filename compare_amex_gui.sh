#!/usr/bin/env bash
# Convenience script for Unix running ISO 8583 message comparison GUI
# Usage: ./compare_amex_gui.sh 

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source .venv/bin/activate

streamlit run compare_amex_gui.py "$@"