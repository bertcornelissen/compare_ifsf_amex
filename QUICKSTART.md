# Quick Start Guide

## Installation

### Local Installation

Clone the GIT repo and (on Windows) start the amex.bat file.

- This will create a virtual environment, when not present
- Provides a default ignored_fields.yaml, when not present

## Configuration Files

**First-time setup:** Copy the sample configuration to the project root before running:

```bash
cp samples/ignored_fields.yaml ignored_fields.yaml
```

**Windows:** `amex.bat` automatically copies `samples\ignored_fields.yaml` → `ignored_fields.yaml` on first run.

`ignored_fields.yaml` is ignored by Git, so your customizations won't be lost when pulling updates.

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
uv run compare_amex_cli.py samples/IPH.txt samples/WLPFO.txt -c ignored_fields.yaml
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
uv run compare_amex_cli.py samples/IPH.txt samples/WLPFO.txt --request-only -c ignored_fields.yaml
```

### Save report to file

```bash
uv run compare_amex_cli.py samples/IPH.txt samples/WLPFO.txt -c ignored_fields.yaml -o report.txt
```

### Get help

```bash
uv run compare_amex_cli.py --help
```

## Configuration

Edit `ignored_fields.yaml` to customize which fields and subfields are ignored:

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
uv run compare_amex_cli.py samples/IPH.txt samples/WLPFO.txt --request-only -c ignored_fields.yaml
```

```bat
:: Windows — basic two-file comparison (no extra options via amex.bat)
amex.bat cli samples\IPH.txt samples\WLPFO.txt
```

**Example 2: Custom config**

```bash
uv run compare_amex_cli.py file1.txt file2.txt -c production.yaml
```

```bat
:: Windows — use Python directly for extra options
python compare_amex_cli.py file1.txt file2.txt -c production.yaml
```

**Example 3: Verbose output to file**

```bash
uv run compare_amex_cli.py msg1.txt msg2.txt --verbose -c ignored_fields.yaml -o detailed_report.txt
```

```bat
:: Windows — use Python directly for extra options
python compare_amex_cli.py msg1.txt msg2.txt --verbose -c ignored_fields.yaml -o detailed_report.txt
```

## Files

- `compare_amex_gui.py` - Streamlit GUI (recommended for interactive use)
- `compare_amex_cli.py` - CLI comparison tool (for automation/scripts)
- `amex.bat` - Windows one-click launcher (`amex.bat gui`, `amex.bat cli file1 file2`, or `amex.bat` for interactive menu)
- `ignored_fields.yaml` - User configuration (copy from `samples/ignored_fields.yaml`, customize this!)
- `msg_specs.py` - Message specifications (pre-configured, included in project)
- `samples/` - Sample files and configuration template
  - `ignored_fields.yaml` - Default configuration template
  - `IPH.txt`, `WLPFO.txt` - Sample message files
- `README.md` - Full documentation
- `CONFIG_GUIDE.md` - Configuration reference

## Common Tasks

### See all Field 55 differences

Temporarily edit `ignored_fields.yaml` and remove or comment out the Field 55 ignored subfields:

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
uv run compare_amex_cli.py file1.txt file2.txt --request-only -c ignored_fields.yaml   # Only Request
uv run compare_amex_cli.py file1.txt file2.txt --response-only -c ignored_fields.yaml  # Only Response
```
