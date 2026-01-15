import re
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional

FIELD_CLASSES = {
    "FINANCIAL": {"004"},
    "SECURITY": {"052", "053", "055"},
    "OPERATIONAL": {"007", "011", "012", "033"},
}

IGNORED_FIELD_VALUES = {
    "011",  # STAN
    "012",  # Local Transaction Date/Time
}
IGNORED_SUBFIELDS = {
    "007": {"Time"},
}

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



FIELD_HEADER_RE = re.compile(r'\s*(\d{3})\s+(.+?)\s+=\s+"?(.*?)"?$')
SUBFIELD_RE = re.compile(r'\s+(\w+)\s*:\s*(.+)$')

def parse_message(text: str) -> Dict[str, ParsedField]:
    fields: Dict[str, ParsedField] = {}
    current: ParsedField | None = None

    for line in text.splitlines():
        header = FIELD_HEADER_RE.match(line)
        if header:
            number, name, value = header.groups()
            current = ParsedField(
                number=number,
                name=name.strip(),
                raw_value=value,
                subfields={}
            )
            fields[number] = current
            continue

        if current:
            sub = SUBFIELD_RE.match(line)
            if sub:
                key, value = sub.groups()
                current.subfields[key.strip()] = value.strip()

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
            if fa.raw_value != fb.raw_value or fa.subfields != fb.subfields:
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


def render_report(diff: DiffResult, verdict: str) -> str:
    out = []

    out.append("ISO 8583 Message Comparison Report")
    out.append("=" * 40)
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
            if f.before:
                out.append(f"  Before: {f.before.raw_value}")
            if f.after:
                out.append(f"  After : {f.after.raw_value}")
            out.append("")

    return "\n".join(out)



def main():
    text_a = open("IPH.txt").read()
    text_b = open("WLPFO.txt").read()

    parsed_a = normalize(parse_message(text_a))
    parsed_b = normalize(parse_message(text_b))

    diff = diff_fields(parsed_a, parsed_b)
    verdict = classify(diff)

    report = render_report(diff, verdict)
    print(report)





if __name__ == "__main__":
    main()
