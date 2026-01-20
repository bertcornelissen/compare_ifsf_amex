# ISO 8583 Message Comparison Tool

A tool to compare ISO 8583 message files and identify differences at both field and subfield levels. Available as both a **Command-Line Interface (CLI)** and a **Web-Based GUI (Streamlit)**.

## Features

- **Two Interfaces**: Use either CLI for automation/scripts or Streamlit GUI for interactive analysis
- **Detailed Comparison**: Compares both Request and Response messages
- **Subfield-Level Analysis**: Shows differences within complex fields (e.g., Field 22, Field 55)
- **Configurable Ignoring**: Skip specific fields or subfields via YAML configuration
- **Impact Classification**: Categorizes changes as FINANCIAL, SECURITY, OPERATIONAL, or FORMAT changes
- **Flexible Output**: Print to console, save to file, or view in interactive web interface

## Installation

```bash
uv sync
```

Or with pip:

```bash
pip install pyyaml streamlit
```

## Usage

### 🖥️ Streamlit GUI (Recommended)

Launch the interactive web interface:

```bash
uv run streamlit run compare_gui.py
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
- 📊 Visual metrics and color-coded verdicts
- 🔍 Expandable field change details with side-by-side comparison
- 📥 Download button for full text report
- 🔄 Hot-reload configuration without restarting
- 📋 **Two View Modes:**
  - **Comparison Report**: Structured field-level differences with impact analysis
  - **Side-by-Side Diff**: Character-level HTML diff view showing exact changes

### 💻 Command-Line Interface

#### Basic Comparison

```bash
uv run python main.py file1.txt file2.txt
```

#### Compare Only Request Messages

```bash
uv run python main.py file1.txt file2.txt --request-only
```

#### Compare Only Response Messages

```bash
uv run python main.py file1.txt file2.txt --response-only
```

#### Save Report to File

```bash
uv run python main.py file1.txt file2.txt -o report.txt
```

#### Use Custom Configuration

```bash
uv run python main.py file1.txt file2.txt -c custom_config.yaml
```

#### Verbose Output

```bash
uv run python main.py file1.txt file2.txt --verbose
```

## Configuration

The tool uses a `config.yaml` file to control which fields and subfields are ignored during comparison. This is useful for excluding fields that naturally vary between transactions (like timestamps or transaction IDs).

### Configuration File Format

```yaml
# Field classification for impact assessment
field_classes:
  FINANCIAL:
    - "004" # Amount, Transaction
  SECURITY:
    - "052" # PIN Data
    - "053" # Security Related Control Information
    - "055" # Integrated Circuit Card System Related Data
  OPERATIONAL:
    - "007" # Date And Time, Transmission
    - "011" # Systems Trace Audit Number
    - "012" # Date And Time, Local Transaction

# Fields to completely ignore (entire field value)
ignored_fields:
  - "011" # STAN - changes per transaction

# Subfields to ignore within specific fields
ignored_subfields:
  "007":
    - "Time" # Ignore time component, compare only date

  "022":
    - "8-Cardmember Authentication Method"
    - "9-Cardmember Authentication Entity"
    - "10-Card Data Output Capability"
    - "11-Terminal Output Capability"
```

### Configuration Options

#### field_classes

Groups fields into categories for impact assessment:

- **FINANCIAL**: Changes that affect transaction amounts or financial processing
- **SECURITY**: Changes that affect security-related fields
- **OPERATIONAL**: Changes that affect routing or operational behavior

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

VERDICT: POTENTIALLY IMPACTFUL

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
usage: main.py [-h] [-c CONFIG] [-o OUTPUT] [--request-only]
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
# Launch the Streamlit GUI
uv run streamlit run compare_gui.py

# Then open http://localhost:8501 in your browser
```

### CLI Usage

Compare two message files with default configuration:

```bash
uv run python main.py IPH.txt WLPFO.txt
```

Compare only request messages and save to file:

```bash
uv run python main.py IPH.txt WLPFO.txt --request-only -o diff_report.txt
```

Use a custom configuration file:

```bash
uv run python main.py msg1.txt msg2.txt -c production_config.yaml
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
