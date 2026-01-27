# Quick Start Guide

## Installation

```bash
cd /home/bert/PythonProjects/compare_ifsf_amex
uv sync
```

## Basic Usage

### 🖥️ GUI (Recommended)

Launch the interactive web interface:

```bash
uv run streamlit run compare_gui.py
```

Open `http://localhost:8501` in your browser. The GUI provides:

- Drag-and-drop file upload
- Three view modes:
  - **Pandas DataFrame**: Color-coded table view with "show only differences" option
  - **Comparison Report**: Structured field-level differences
  - **Side-by-Side Diff**: Character-level HTML diff
- Interactive expandable sections
- Downloadable reports
- Configuration viewer in sidebar

### 💻 CLI - Compare two files (shows Request and Response)

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
  - "11" # STAN
  - "41" # Card Acceptor Terminal ID
  - "43" # Card Acceptor Name/Location

# Ignore specific subfields
ignored_subfields:
  "55":
    - "Transaction Date"
    - "Unpredictable Number"
    - "Application Cryptogram"
  "12":
    - "Day"
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

- `compare_gui.py` - Streamlit GUI (recommended for interactive use)
- `main.py` - CLI comparison tool (for automation/scripts)
- `config.yaml` - Default configuration (customize this!)
- `compare.sh` - Convenience wrapper script for CLI
- `README.md` - Full documentation
- `CONFIG_GUIDE.md` - Configuration reference

## Common Tasks

### See all Field 55 differences

Temporarily edit `config.yaml` and remove or comment out the Field 55 ignored subfields:

```yaml
ignored_subfields:
  "55": [] # Empty list = compare all subfields
```

### Ignore all timestamps

```yaml
ignored_fields:
  - "07" # Transmission Date/Time
  - "12" # Local Transaction Date/Time
```

### Compare only specific message type

```bash
./compare.sh file1.txt file2.txt --request-only   # Only Request
./compare.sh file1.txt file2.txt --response-only  # Only Response
```
