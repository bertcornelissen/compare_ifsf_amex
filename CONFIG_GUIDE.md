# Configuration Guide for ISO 8583 Message Comparison

This guide explains how to customize the comparison behavior using the `config.yaml` file.

## Quick Start

The tool looks for `config.yaml` in the current directory by default.

**In the Streamlit GUI:** Enter the config file path in the sidebar.

**In the CLI:** Use the `-c` option:

```bash
uv run python main.py file1.txt file2.txt -c my_config.yaml
```

## Configuration Structure

```yaml
field_classes:
  CATEGORY_NAME:
    - "field_number"

ignored_fields:
  - "field_number"

ignored_subfields:
  "field_number":
    - "subfield_identifier"
```

## Field Classes

Field classes categorize fields for impact assessment. This affects the VERDICT output.

**Supported categories:**

- `FINANCIAL`: Changes that affect transaction amounts or financial processing
- `SECURITY`: Changes that affect security-related fields (e.g., PIN, cryptograms)
- `OPERATIONAL`: Changes that affect routing or operational behavior

**Example:**

```yaml
field_classes:
  FINANCIAL:
    - "04" # Amount, Transaction
  SECURITY:
    - "52" # PIN Data
    - "53" # Security Related Control Information
    - "55" # Integrated Circuit Card System Related Data
  OPERATIONAL:
    - "07" # Date And Time, Transmission
    - "11" # Systems Trace Audit Number
    - "12" # Date And Time, Local Transaction
    - "33" # Forwarding Institution Identification Code
```

**Impact on Verdict:**

- Changes to FINANCIAL fields → "FUNCTIONALLY DIFFERENT"
- Changes to SECURITY fields → "POTENTIALLY IMPACTFUL"
- Only FORMAT changes (add/remove fields) → "FORMAT / ROUTING CHANGE ONLY"
- Only OPERATIONAL changes → "OPERATIONAL DIFFERENCES ONLY"
- No changes → "NO DIFFERENCES"

## Ignored Fields

List field numbers that should be completely ignored. The entire field value will be replaced with `<IGNORED>` before comparison.

**Use cases:**

- Fields that change with every transaction (e.g., STAN, timestamps)
- Fields that are transaction-specific but not relevant to comparison

**Example:**

```yaml
ignored_fields:
  - "11" # STAN - Systems Trace Audit Number (changes per transaction)
  - "41" # Card Acceptor Terminal ID
  - "43" # Card Acceptor Name/Location
  - "p" # Primary Bitmap
  - "33" # Forwarding Institution Identification Code
```

**Effect:** These fields will never show as different, regardless of their values.

## Ignored Subfields

For fields with multiple subfields, you can ignore specific subfields while comparing others.

**Use cases:**

- Time components that vary but dates should match
- Terminal capabilities that vary by hardware but not relevant to message logic
- Formatting differences in composite fields

**Format:** Field number as string, subfield identifiers as list

**Subfield identifier format:**

- For numbered subfields: `"N-Name"` where N is the subfield number
- For named attributes: `"Attribute Name"`

**Example:**

```yaml
ignored_subfields:
  "55":
    - "Transaction Date"
    - "Unpredictable Number"
    - "Application Cryptogram"

  "12":
    - "Day"
```

**Effect:** Only the specified subfields are ignored; all other subfields in the field are still compared.

## Finding Subfield Identifiers

To find the correct subfield identifiers for the `ignored_subfields` configuration:

1. Run a comparison **without** ignoring any subfields:

   ```bash
   uv run python main.py file1.txt file2.txt > full_report.txt
   ```

2. Look at the changed fields in the output to see the exact subfield names:

   ```
   ! 022 Point Of Service Data Code
       2-Cardholder Authentication Capability:
         Before: 0
         After : 1
       8-Cardmember Authentication Method:
         Before: 5
         After : 1
   ```

3. Copy the exact subfield identifier (e.g., `"2-Cardholder Authentication Capability"`) to your config.

## Common Configurations

### Minimal (compare everything)

```yaml
field_classes:
  FINANCIAL: ["004"]
  SECURITY: ["052", "055"]
  OPERATIONAL: ["011"]

ignored_fields: []
ignored_subfields: {}
```

### Standard (ignore transaction-specific fields)

```yaml
field_classes:
  FINANCIAL: ["04"]
  SECURITY: ["52", "53", "55"]
  OPERATIONAL: ["07", "11", "12", "33"]

ignored_fields:
  - "11" # STAN
  - "41" # Card Acceptor Terminal ID
  - "43" # Card Acceptor Name/Location
  - "p" # Primary Bitmap
  - "33"

ignored_subfields:
  "55":
    - "Transaction Date"
    - "Unpredictable Number"
    - "Application Cryptogram"
  "12":
    - "Day"
```

### Strict (ignore all timestamps and counters)

```yaml
field_classes:
  FINANCIAL: ["04"]
  SECURITY: ["52", "53", "55"]
  OPERATIONAL: ["07", "11", "12", "33"]

ignored_fields:
  - "07" # Transmission Date/Time
  - "011" # STAN
  - "012" # Local Transaction Date/Time

ignored_subfields:
  "055":
    - "Application Transaction Counter"
    - "Unpredictable Number"
    - "3-Unpredictable Number"
    - "4-Application Transaction Counter (AT"
```

## Tips

1. **Start minimal**: Begin with few ignored fields and add more as you identify irrelevant differences
2. **Document reasons**: Add comments explaining why each field/subfield is ignored
3. **Version control**: Keep your config files in version control with your test cases
4. **Environment-specific**: Use different configs for different environments (dev, test, prod)
5. **Test configs**: Run comparisons with and without ignoring to verify your config is correct

## Troubleshooting

**Config file not found:**

```
Warning: Config file 'config.yaml' not found. Using default configuration.
```

Solution: Create a `config.yaml` file or specify the correct path with `-c`

**Field still showing as different:**

- Check the exact field number (must be 3 digits with leading zeros)
- For subfields, check the exact identifier including dashes and capitalization
- Run with `--verbose` to see parsing details

**Subfield not being ignored:**

- Verify the subfield identifier matches exactly (copy from a comparison report)
- Check YAML syntax (proper indentation, quotes around numbers)
- Ensure the field number is a string: `"022"` not `022`
