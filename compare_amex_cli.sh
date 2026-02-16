#!/usr/bin/env bash
# Convenience script for Unix running ISO 8583 message comparison CLI
# Usage: ./compare_amex_cli.sh file1.txt file2.txt [options]


cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source .venv/bin/activat

python3 compare_amex_cli.py "$@"
