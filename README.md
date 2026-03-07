# ISO 8583 Message Comparison Tool

A tool to compare ISO 8583 message files and identify differences at both field and subfield levels. Available as both a **Command-Line Interface (CLI)** and a **Web-Based GUI (Streamlit)**.

## Features

- **Two Interfaces**: Use either CLI for automation/scripts or Streamlit GUI for interactive analysis
- **Detailed Comparison**: Compares both Request and Response messages
- **Subfield-Level Analysis**: Shows differences within complex fields (e.g., Field 22, Field 55)
- **Configurable Ignoring**: Skip specific fields or subfields via YAML configuration
- **Flexible Output**: Print to console, save to file, or view in interactive web interface

## Installation

### Local Installation

Clone the GIT repo and (on Windows) start the amex.bat file.

- This will create a virtual environment, when not present
- Provides a default ignored_fields.yaml, when not present

## Configuration Files

The tool uses two configuration files:

- `ignored_fields.yaml` - Defines which fields/subfields to ignore during comparison
- `msg_specs.py` - Defines ISO 8583 message specifications (pre-configured, included in the project)

**First-time setup:** Copy the sample configuration to the project root before running:

```bash
cp samples/ignored_fields.yaml ignored_fields.yaml
```

**Windows:** `amex.bat` automatically copies `samples\ignored_fields.yaml` → `ignored_fields.yaml` on first run.

**Preserving customizations:** `ignored_fields.yaml` is ignored by Git, so your customizations won't be overwritten when you pull updates from the repository. The template in `samples/ignored_fields.yaml` is tracked by Git and serves as the reference configuration.

## Usage

### 🖥️ Streamlit GUI (Recommended)

Launch the interactive web interface:

```bash
uv run streamlit run compare_amex_gui.py
```

**Windows:**

```bat
:: One-click Windows launcher
amex.bat gui

:: Or run without arguments and choose option 1 from the interactive menu
amex.bat
```

Then open your browser to `http://localhost:8501` and:

1. Upload two ISO 8583 message files
2. Select which messages to compare (Request, Response, or both)
3. Click "Compare Messages"
4. Choose view mode:
   - **Comparison Report**: Structured analysis with field-level differences
   - **Side-by-Side Diff**: Visual HTML diff showing exact character changes
5. View interactive results with expandable sections
6. Download the full text report

**GUI Features:**

- 📤 Drag-and-drop file upload
- ⚙️ Configuration viewer in sidebar
- 📊 Visual metrics and summary statistics
- 🔍 Expandable field change details with side-by-side comparison
- 📥 Download button for full text report
- 🔄 Hot-reload configuration without restarting
- 📋 **Three View Modes:**
  - **Pandas DataFrame**: Color-coded table view with "show only differences" option for focused analysis
  - **Comparison Report**: Structured field-level differences and expandable sections
  - **Side-by-Side Diff**: Character-level HTML diff view showing exact changes in full file or specific messages

### 💻 Command-Line Interface

#### Basic Comparison

```bash
uv run compare_amex_cli.py file1.txt file2.txt -c ignored_fields.yaml
```

**Windows:**

```bat
:: One-click Windows launcher (two file arguments)
amex.bat cli file1.txt file2.txt

:: Or run without arguments and choose option 2 from the interactive menu
amex.bat
```

> **Note (Windows):** For advanced options (`--request-only`, `--response-only`, `-o`, `-c`, `--verbose`), invoke Python directly:
>
> ```bat
> python compare_amex_cli.py file1.txt file2.txt --request-only
> ```

#### Compare Only Request Messages

```bash
uv run compare_amex_cli.py file1.txt file2.txt --request-only -c ignored_fields.yaml
```

#### Compare Only Response Messages

```bash
uv run compare_amex_cli.py file1.txt file2.txt --response-only -c ignored_fields.yaml
```

#### Save Report to File

```bash
uv run compare_amex_cli.py file1.txt file2.txt -c ignored_fields.yaml -o report.txt
```

#### Use Custom Configuration

```bash
uv run compare_amex_cli.py file1.txt file2.txt -c custom_config.yaml
```

#### Verbose Output

```bash
uv run compare_amex_cli.py file1.txt file2.txt --verbose -c ignored_fields.yaml
```

## Configuration

The tool uses an `ignored_fields.yaml` file to control which fields and subfields are ignored during comparison. This is useful for excluding fields that naturally vary between transactions (like timestamps or transaction IDs).

**Note:** If `ignored_fields.yaml` doesn't exist, copy it from `samples/ignored_fields.yaml`. Your customized `ignored_fields.yaml` is ignored by Git, so your changes won't be lost when pulling updates.

### Configuration File Format

```yaml
# Fields to completely ignore (entire field value)
ignored_fields:
  - "11" # STAN - Systems Trace Audit Number (changes per transaction)
  - "41" # Card Acceptor Terminal ID
  - "43" # Card Acceptor Name/Location
  - "p" # Primary Bitmap
  - "33"

# Subfields to ignore within specific fields
ignored_subfields:
  "55":
    - "Transaction Date"
    - "Unpredictable Number"
    - "Application Cryptogram"

  "12":
    - "Day"
```

### Configuration Options

#### ignored_fields

List of field numbers to completely ignore. The entire field value will be marked as `<IGNORED>` during comparison.

#### ignored_subfields

Map of field numbers to lists of subfield identifiers that should be ignored. Useful for fields with multiple subfields where only some are relevant for comparison.

## Output

The tool generates a detailed comparison report showing:

1. **Summary**: Count of added, removed, and changed fields
2. **Fields Added**: Fields present in file2 but not in file1
3. **Fields Removed**: Fields present in file1 but not in file2
4. **Fields Changed**: Detailed subfield-level differences

### Example Output

```
ISO 8583 Message Comparison Report - REQUEST
==================================================

Summary
-------
Fields added   : 4
Fields removed : 0
Fields changed : 8

Fields Changed
--------------
! 022 Point Of Service Data Code
    2-Cardholder Authentication Capability:
      Before: 0
      After : 1

! 055 Integrated Circuit Card System Related Data
    1-Application Cryptogram:
      Before: 7B 37 68 BF C2 CC F0 82
      After : E5 E9 B1 92 4B 0B 49 26
```

## CLI Options

```
usage: compare_amex_cli.py [-h] [-c CONFIG] [-o OUTPUT] [--request-only]
                           [--response-only] [--verbose] file1 file2

positional arguments:
  file1                First ISO 8583 message file to compare
  file2                Second ISO 8583 message file to compare

options:
  -h, --help           show this help message and exit
  -c, --config CONFIG  Configuration file path (default: config.yaml)
  -o, --output OUTPUT  Output file for comparison report
  --request-only       Compare only Request messages
  --response-only      Compare only Response messages
  --verbose            Show detailed parsing information
```

## Examples

### GUI Usage

```bash
uv run streamlit run compare_amex_gui.py

# Then open http://localhost:8501 in your browser
```

**Windows:**

```bat
amex.bat gui
```

### CLI Usage

Compare two message files with default configuration:

```bash
uv run compare_amex_cli.py samples/IPH.txt samples/WLPFO.txt -c ignored_fields.yaml
```

**Windows:**

```bat
amex.bat cli samples\IPH.txt samples\WLPFO.txt
```

Compare only request messages and save to file:

```bash
uv run compare_amex_cli.py samples/IPH.txt samples/WLPFO.txt --request-only -o diff_report.txt -c ignored_fields.yaml
```

```bat
:: Windows — use Python directly for extra options
python compare_amex_cli.py samples\IPH.txt samples\WLPFO.txt --request-only -o diff_report.txt -c ignored_fields.yaml
```

Use a custom configuration file:

```bash
uv run compare_amex_cli.py msg1.txt msg2.txt -c production_config.yaml
```

```bat
:: Windows — use Python directly for extra options
python compare_amex_cli.py msg1.txt msg2.txt -c production_config.yaml
```

## Exit Codes

- `0`: Successful comparison
- `1`: Error (file not found, parse error, etc.)

## Field Support

The tool supports all ISO 8583 fields including:

- Simple fields with single values
- Complex fields with multiple subfields (e.g., Field 22, Field 43)
- EMV/chip card data fields (e.g., Field 55)

Subfields are automatically parsed and compared individually, allowing for precise identification of differences within complex fields.
