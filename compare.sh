#!/usr/bin/env bash
# Convenience script for running ISO 8583 message comparison
# Usage: ./compare.sh file1.txt file2.txt [options]

uv run python main.py "$@"
