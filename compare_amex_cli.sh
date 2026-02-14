#!/usr/bin/env bash
# Convenience script for running ISO 8583 message comparison CLI
# Usage: ./compare_amex_cli.sh file1.txt file2.txt [options]


cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "$(pwd)"

# Detect the operating system and activate the virtual environment
if [[ "$(lsb_release -is 2>/dev/null)" == "Ubuntu" ]]; then
    source .venv/bin/activate
elif [[ "$(uname)" == "Linux" ]]; then
    source .venv/bin/activate
elif [[ "$(uname)" == "Darwin" ]]; then
    source .venv/bin/activate
elif [[ "$(uname)" == "CYGWIN"* || "$(uname)" == "MINGW"* || "$(uname)" == "MSYS"* ]]; then
    .venv\Scripts\activate
else
    echo "Unsupported OS. Exiting."
    exit 1
fi

python3 compare_amex_cli.py "$@"
