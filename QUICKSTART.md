# Quick Start Guide

## Installation

### Local Installation

```bash
cd /path/to/compare_ifsf_amex
```

### Shared Directory Installation

For multi-user environments, install to a shared location:

```bash
# Install to shared directory
cd /opt/compare_ifsf_amex  # or any shared location

# Add to PATH or create symlinks
export PATH="/opt/compare_ifsf_amex:$PATH"

# Now anyone can run from anywhere:
compare_amex_cli.sh file1.txt file2.txt
compare_amex_gui.sh
```

## Configuration Files

**First-time setup:** When you first run the tool, if `config.yaml` and `msg_specs.py` don't exist, they will be automatically created from the templates in `samples/`:

- `samples/default_config.yaml` → `config.yaml`
- `samples/default_msg_specs.py` → `msg_specs.py`

These files are ignored by Git, so your customizations won't be lost when pulling updates.

## Basic Usage

### 🖥️ GUI (Recommended)

**Windows:**

```bat
# One-click launcher
amex.bat gui

# Or interactive menu (run without arguments and choose option 1)
amex.bat
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
# Using wrapper script (recommended, works from anywhere)
./compare_amex_cli.sh samples/IPH.txt samples/WLPFO.txt

# Or directly with uv (must be in project directory)
uv run compare_amex_cli.py samples/IPH.txt samples/WLPFO.txt
```

**Windows:**

```bat
# One-click launcher
amex.bat cli samples\IPH.txt samples\WLPFO.txt

# Or interactive menu (run without arguments and choose option 2)
amex.bat
```

> **Note (Windows):** `amex.bat cli` accepts two file arguments. For advanced options (`--request-only`, `-o`, `-c`, etc.), invoke Python directly:
>
> ```bat
> python compare_amex_cli.py samples\IPH.txt samples\WLPFO.txt --request-only
> ```

### Compare only Request messages

```bash
./compare_amex_cli.sh samples/IPH.txt samples/WLPFO.txt --request-only
```

### Save report to file

```bash
./compare_amex_cli.sh samples/IPH.txt samples/WLPFO.txt -o report.txt
```

### Get help

```bash
./compare_amex_cli.sh --help
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
./compare_amex_cli.sh samples/IPH.txt samples/WLPFO.txt --request-only
```

```bat
:: Windows — basic two-file comparison (no extra options via amex.bat)
amex.bat cli samples\IPH.txt samples\WLPFO.txt
```

**Example 2: Custom config**

```bash
./compare_amex_cli.sh file1.txt file2.txt -c production.yaml
```

```bat
:: Windows — use Python directly for extra options
python compare_amex_cli.py file1.txt file2.txt -c production.yaml
```

**Example 3: Verbose output to file**

```bash
./compare_amex_cli.sh msg1.txt msg2.txt --verbose -o detailed_report.txt
```

```bat
:: Windows — use Python directly for extra options
python compare_amex_cli.py msg1.txt msg2.txt --verbose -o detailed_report.txt
```

## Files

- `compare_amex_gui.py` - Streamlit GUI (recommended for interactive use)
- `compare_amex_cli.py` - CLI comparison tool (for automation/scripts)
- `compare_amex_gui.sh` - Wrapper script for GUI (works from anywhere)
- `compare_amex_cli.sh` - Wrapper script for CLI (works from anywhere)
- `amex.bat` - Windows one-click launcher (`amex.bat gui`, `amex.bat cli file1 file2`, or `amex.bat` for interactive menu)
- `config.yaml` - User configuration (auto-created from samples/, customize this!)
- `msg_specs.py` - Message specifications (auto-created from samples/)
- `samples/` - Default templates for configuration and message specs
  - `default_config.yaml` - Default configuration template
  - `default_msg_specs.py` - Default message specification template
  - `IPH.txt`, `WLPFO.txt` - Sample message files
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
./compare_amex_cli.sh file1.txt file2.txt --request-only   # Only Request
./compare_amex_cli.sh file1.txt file2.txt --response-only  # Only Response
```
