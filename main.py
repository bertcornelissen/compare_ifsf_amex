import re
import sys
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
try:
    import yaml
except ImportError:
    yaml = None

# Global configuration - will be loaded from config file
FIELD_CLASSES = {}
IGNORED_FIELD_VALUES = set()
IGNORED_SUBFIELDS = {}


def load_config(config_path: str = "config.yaml") -> bool:
    """Load configuration from YAML file."""
    global FIELD_CLASSES, IGNORED_FIELD_VALUES, IGNORED_SUBFIELDS
    
    if not yaml:
        print("Warning: PyYAML not installed. Using default configuration.", file=sys.stderr)
        print("Install with: pip install pyyaml", file=sys.stderr)
        # Set defaults
        FIELD_CLASSES = {
            "FINANCIAL": {"004"},
            "SECURITY": {"052", "053", "055"},
            "OPERATIONAL": {"007", "011", "012", "033"},
        }
        IGNORED_FIELD_VALUES = {"011"}
        IGNORED_SUBFIELDS = {
            "007": {"Time"},
            "012": {"Day", "Time"},
            "022": {"8-Cardmember Authentication Method", "9-Cardmember Authentication Entity", 
                    "10-Card Data Output Capability", "11-Terminal Output Capability"},
            "043": {"2-Postal Code"}
        }
        return False
    
    config_file = Path(config_path)
    if not config_file.exists():
        print(f"Warning: Config file '{config_path}' not found. Using default configuration.", file=sys.stderr)
        return False
    
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Load field classes
        if 'field_classes' in config:
            FIELD_CLASSES = {
                category: set(fields) 
                for category, fields in config['field_classes'].items()
            }
        
        # Load ignored fields
        if 'ignored_fields' in config:
            IGNORED_FIELD_VALUES = set(config['ignored_fields'])
        
        # Load ignored subfields
        if 'ignored_subfields' in config:
            IGNORED_SUBFIELDS = {
                field_num: set(subfields)
                for field_num, subfields in config['ignored_subfields'].items()
            }
        
        return True
    except Exception as e:
        print(f"Error loading config file: {e}", file=sys.stderr)
        return False

@dataclass
class ParsedField:
    number: str
    name: str
    raw_value: Optional[str]
    subfields: Dict[str, str]

@dataclass
class FieldDiff:
    number: str
    name: str
    before: ParsedField | None
    after: ParsedField | None
    ignored_subfields: Set[str] = field(default_factory=set)

@dataclass
class DiffResult:
    added: Dict[str, FieldDiff]
    removed: Dict[str, FieldDiff]
    changed: Dict[str, FieldDiff]


def effective_subfields(field: ParsedField) -> Dict[str, str]:
    """
    Return subfields that participate in comparison.
    Suppressed subfields are already normalized to <IGNORED>,
    so simple dict comparison is sufficient.
    """
    return field.subfields


def fields_differ(fa: ParsedField, fb: ParsedField) -> bool:
    """
    Decide semantic difference between two fields.
    """

    # If both fields have subfields, compare subfields ONLY
    if fa.subfields or fb.subfields:
        return effective_subfields(fa) != effective_subfields(fb)

    # Otherwise compare raw value
    return fa.raw_value != fb.raw_value


def split_messages(text: str) -> tuple[str, str]:
    """
    Split file content into Request and Response sections.
    Returns (request_section, response_section).
    """
    lines = text.splitlines()
    request_start = None
    response_start = None
    
    for i, line in enumerate(lines):
        if line.startswith("Request: message type"):
            request_start = i
        elif line.startswith("Response: message type"):
            response_start = i
            break
    
    if request_start is not None and response_start is not None:
        request_text = "\n".join(lines[request_start:response_start])
        response_text = "\n".join(lines[response_start:])
        return request_text, response_text
    
    # If no split found, return entire text as request
    return text, ""


def parse_message(text: str) -> dict[str, ParsedField]:
    fields: dict[str, ParsedField] = {}
    current: Optional[ParsedField] = None

    FIELD_HEADER_RE = re.compile(r'\s*(\d{3})\s+(.+?)\s+=\s+[\'"]?(.*?)[\'"]?$')
    # Match both with and without leading spaces for numbered subfields
    # Handles formats like "Subfield 1 - Name" and "Subfield 1-Name"
    SUBFIELD_RE = re.compile(r'^\s*Subfield\s+(\d+)\s*-\s*(.+?)\s*=\s*(.+?)$')
    # For Field 55 and similar complex fields with named attributes (must have at least 6 spaces)
    NAMED_ATTRIBUTE_RE = re.compile(r'^\s{6,}([A-Za-z][\w\s\(\)/]+?)\s*=\s*(.+?)$')

    for line in text.splitlines():
        header = FIELD_HEADER_RE.match(line)
        if header:
            number, name, value = header.groups()
            current = ParsedField(
                number=number,
                name=name.strip(),
                raw_value=value.strip(),
                subfields={}
            )
            fields[number] = current
            continue

        if current:
            # Parse numbered Subfield lines (highest priority - check first)
            sub_match = SUBFIELD_RE.match(line)
            if sub_match:
                sub_no, sub_name, value = sub_match.groups()
                # Clean up value - remove quotes and parenthetical content at end
                value = value.split('(')[0].strip()
                value = value.strip('"\'')
                current.subfields[f"{sub_no}-{sub_name.strip()}"] = value
                continue
            
            # Parse named attribute lines (for Field 55 and similar)
            # Only if not already matched as a subfield
            attr_match = NAMED_ATTRIBUTE_RE.match(line)
            if attr_match:
                attr_name, value = attr_match.groups()
                # Skip deeply nested byte-level details
                if ', Bit' not in line and 'bit ' not in line:
                    # Clean up value
                    value = value.split('(')[0].strip()
                    value = value.strip('"\'')
                    # Don't overwrite numbered subfields with named attributes
                    if not any(k.startswith(f"{num}-") for num in range(1, 100) for k in [attr_name]):
                        current.subfields[attr_name.strip()] = value

    return fields


def normalize(fields: dict[str, ParsedField]) -> dict[str, ParsedField]:
    out = {}

    for num, field in fields.items():
        
        # Suppress entire field value?
        if num in IGNORED_FIELD_VALUES:
            out[num] = ParsedField(
                number=field.number,
                name=field.name,
                raw_value="<IGNORED>",
                subfields={}  # or keep structure if you prefer
            )
            continue

        # Otherwise suppress selected subfields
        ignored_subs = IGNORED_SUBFIELDS.get(num, set())
        new_subfields = {
            k: ("<IGNORED>" if k in ignored_subs else v)
            for k, v in field.subfields.items()
        }

        out[num] = ParsedField(
            number=field.number,
            name=field.name,
            raw_value=field.raw_value,
            subfields=new_subfields
        )

    return out



def diff_fields(
    a: Dict[str, ParsedField],
    b: Dict[str, ParsedField],
) -> DiffResult:

    added = {}
    removed = {}
    changed = {}

    all_fields = set(a) | set(b)

    for f in sorted(all_fields):
        fa = a.get(f)
        fb = b.get(f)

        if fa and not fb:
            removed[f] = FieldDiff(f, fa.name, fa, None)

        elif fb and not fa:
            added[f] = FieldDiff(f, fb.name, None, fb)

        else:
            if fields_differ(fa, fb):
                changed[f] = FieldDiff(f, fa.name, fa, fb)


    return DiffResult(added, removed, changed)


def classify(diff: DiffResult) -> str:
    changed_fields = set(diff.changed) | set(diff.added) | set(diff.removed)

    if changed_fields & FIELD_CLASSES["FINANCIAL"]:
        return "FUNCTIONALLY DIFFERENT"

    if changed_fields & FIELD_CLASSES["SECURITY"]:
        return "POTENTIALLY IMPACTFUL"

    if diff.added or diff.removed:
        return "FORMAT / ROUTING CHANGE ONLY"

    if diff.changed:
        return "OPERATIONAL DIFFERENCES ONLY"

    return "NO DIFFERENCES"


def render_report(diff: DiffResult, verdict: str, message_type: str = "") -> str:
    out = []

    out.append(f"ISO 8583 Message Comparison Report - {message_type}")
    out.append("=" * 50)
    out.append("")
    out.append(f"VERDICT: {verdict}")
    out.append("")

    out.append("Summary")
    out.append("-------")
    out.append(f"Fields added   : {len(diff.added)}")
    out.append(f"Fields removed : {len(diff.removed)}")
    out.append(f"Fields changed : {len(diff.changed)}")
    out.append("")

    if diff.added:
        out.append("Fields Added")
        out.append("------------")
        for f in diff.added.values():
            out.append(f"+ {f.number} {f.name}")
        out.append("")

    if diff.removed:
        out.append("Fields Removed")
        out.append("--------------")
        for f in diff.removed.values():
            out.append(f"- {f.number} {f.name}")
        out.append("")

    if diff.changed:
        out.append("Fields Changed")
        out.append("--------------")
        for f in diff.changed.values():
            out.append(f"! {f.number} {f.name}")
            
            # Show subfield-level changes for fields with subfields
            if f.before and f.after and (f.before.subfields or f.after.subfields):
                all_subfield_keys = set(f.before.subfields.keys()) | set(f.after.subfields.keys())
                for sk in sorted(all_subfield_keys):
                    before_val = f.before.subfields.get(sk, "<missing>")
                    after_val = f.after.subfields.get(sk, "<missing>")
                    if before_val != after_val:
                        out.append(f"    {sk}:")
                        out.append(f"      Before: {before_val}")
                        out.append(f"      After : {after_val}")
            else:
                # Show raw value changes for simple fields
                if f.before:
                    out.append(f"  Before: {f.before.raw_value}")
                if f.after:
                    out.append(f"  After : {f.after.raw_value}")
            out.append("")

    return "\n".join(out)



def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Compare ISO 8583 message files and report differences.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s file1.txt file2.txt
  %(prog)s file1.txt file2.txt -c custom_config.yaml
  %(prog)s file1.txt file2.txt -o report.txt
  %(prog)s file1.txt file2.txt --request-only
        """
    )
    
    parser.add_argument(
        'file1',
        help='First ISO 8583 message file to compare'
    )
    parser.add_argument(
        'file2',
        help='Second ISO 8583 message file to compare'
    )
    parser.add_argument(
        '-c', '--config',
        default='config.yaml',
        help='Configuration file path (default: config.yaml)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output file for comparison report (default: print to stdout)'
    )
    parser.add_argument(
        '--request-only',
        action='store_true',
        help='Compare only Request messages, skip Response messages'
    )
    parser.add_argument(
        '--response-only',
        action='store_true',
        help='Compare only Response messages, skip Request messages'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed parsing information'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    load_config(args.config)
    
    # Check if input files exist
    file1_path = Path(args.file1)
    file2_path = Path(args.file2)
    
    if not file1_path.exists():
        print(f"Error: File '{args.file1}' not found.", file=sys.stderr)
        sys.exit(1)
    
    if not file2_path.exists():
        print(f"Error: File '{args.file2}' not found.", file=sys.stderr)
        sys.exit(1)
    
    # Read input files
    try:
        text_a = file1_path.read_text()
        text_b = file2_path.read_text()
    except Exception as e:
        print(f"Error reading files: {e}", file=sys.stderr)
        sys.exit(1)

    # Split into Request and Response sections
    req_a, resp_a = split_messages(text_a)
    req_b, resp_b = split_messages(text_b)
    
    # Prepare output
    output_lines = []
    
    # Compare Request messages
    if not args.response_only:
        output_lines.append("=" * 70)
        output_lines.append("COMPARING REQUEST MESSAGES")
        output_lines.append("=" * 70)
        
        parsed_req_a = normalize(parse_message(req_a))
        parsed_req_b = normalize(parse_message(req_b))
        
        if args.verbose:
            output_lines.append(f"\nFile 1: {args.file1}")
            output_lines.append(f"  Parsed {len(parsed_req_a)} fields")
            output_lines.append(f"File 2: {args.file2}")
            output_lines.append(f"  Parsed {len(parsed_req_b)} fields")
            output_lines.append("")

        diff_req = diff_fields(parsed_req_a, parsed_req_b)
        verdict_req = classify(diff_req)
        report_req = render_report(diff_req, verdict_req, "REQUEST")
        output_lines.append(report_req)

    # Compare Response messages if they exist
    if not args.request_only and resp_a and resp_b:
        output_lines.append("\n" + "=" * 70)
        output_lines.append("COMPARING RESPONSE MESSAGES")
        output_lines.append("=" * 70)
        
        parsed_resp_a = normalize(parse_message(resp_a))
        parsed_resp_b = normalize(parse_message(resp_b))

        if args.verbose:
            output_lines.append(f"\nFile 1: {args.file1}")
            output_lines.append(f"  Parsed {len(parsed_resp_a)} fields")
            output_lines.append(f"File 2: {args.file2}")
            output_lines.append(f"  Parsed {len(parsed_resp_b)} fields")
            output_lines.append("")

        diff_resp = diff_fields(parsed_resp_a, parsed_resp_b)
        verdict_resp = classify(diff_resp)
        report_resp = render_report(diff_resp, verdict_resp, "RESPONSE")
        output_lines.append(report_resp)
    
    # Output results
    output_text = "\n".join(output_lines)
    
    if args.output:
        try:
            Path(args.output).write_text(output_text)
            print(f"Comparison report written to: {args.output}")
        except Exception as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(output_text)





if __name__ == "__main__":
    main()
