# Quick Start Guide

## Installation

```bash
cd /home/bert/PythonProjects/compare_ifsf_amex
uv sync
```

## Basic Usage

### Compare two files (shows Request and Response)

```bash
./compare.sh IPH.txt WLPFO.txt
```

or

```bash
uv run python main.py IPH.txt WLPFO.txt
```

### Compare only Request messages

```bash
./compare.sh IPH.txt WLPFO.txt --request-only
```

### Save report to file

```bash
./compare.sh IPH.txt WLPFO.txt -o report.txt
```

### Get help

```bash
./compare.sh --help
```

## Configuration

Edit `config.yaml` to customize which fields and subfields are ignored:

```yaml
# Completely ignore these fields
ignored_fields:
  - "011" # STAN

# Ignore specific subfields
ignored_subfields:
  "022":
    - "8-Cardmember Authentication Method"
    - "10-Card Data Output Capability"
```

See [CONFIG_GUIDE.md](CONFIG_GUIDE.md) for detailed configuration options.

## Examples

**Example 1: Quick comparison**

```bash
./compare.sh IPH.txt WLPFO.txt --request-only
```

**Example 2: Custom config**

```bash
./compare.sh file1.txt file2.txt -c production.yaml
```

**Example 3: Verbose output to file**

```bash
./compare.sh msg1.txt msg2.txt --verbose -o detailed_report.txt
```

## Files

- `main.py` - Main comparison tool
- `config.yaml` - Default configuration (customize this!)
- `compare.sh` - Convenience wrapper script
- `README.md` - Full documentation
- `CONFIG_GUIDE.md` - Configuration reference

## Common Tasks

### See all Field 022 differences

Temporarily edit `config.yaml` and remove or comment out the Field 022 ignored subfields:

```yaml
ignored_subfields:
  "022": [] # Empty list = compare all subfields
```

### Ignore all timestamps

```yaml
ignored_fields:
  - "007" # Transmission Date/Time
  - "012" # Local Transaction Date/Time
```

### Compare only specific message type

```bash
./compare.sh file1.txt file2.txt --request-only   # Only Request
./compare.sh file1.txt file2.txt --response-only  # Only Response
```
