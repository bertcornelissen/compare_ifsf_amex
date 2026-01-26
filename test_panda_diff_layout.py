from typing import Optional
import iso8583
import pandas as pd
from msg_specs import spec, field_55_spec
import streamlit as st

st.set_page_config(layout="wide")

def parse_sub_field(data, spec):
    # Accept str or bytes
    if isinstance(data, str):
        data = data.encode("ascii")

    offset = 0
    length_data = len(data)
    result = {}

    for field_nr, field in spec.items():
        if offset >= length_data:
            break  # no more data available

        len_type = field["len_type"]
        max_len = field["max_len"]
        data_enc = field.get("data_enc", "ascii")

        # --- fixed-length field ---
        if len_type == 0:
            field_len = max_len

        # --- variable-length field ---
        else:
            # read length indicator
            if offset + len_type > length_data:
                break

            len_bytes = data[offset:offset + len_type]
            field_len = int(len_bytes.decode("ascii"), 16) * 2
            offset += len_type

        # read field data
        if offset + field_len > length_data:
            break

        raw_value = data[offset:offset + field_len]
        offset += field_len

        result[field_nr] = raw_value.decode(data_enc)

    return result


text = """
F1F1F0F0703025C128E08200F1F5F3F7F4F2F4F5F0F0F1F7F4F1F0F0F7F0F0F4F0F0F0F0F0F0F0F0F0F0F0F3F0F0F0F4F0F2F9F9F8F2F5F1F2F0F3F1F1F2F8F3F3F5F2F8F5F0F0F1F0F1F5F5F5F0F0F0F1F0F0F1F9F0F0F5F5F4F1F0F9F6F7F3F8F0F5F0F0F1F3F7F3F7F4F2F4F5F0F0F1F7F4F1F0F0F7C4F2F5F1F2F2F0F1F1F5F0F4F1F2F3F4F5F0F0F0F0F0F5F3F3F7F1F0F0F0F0F0F3F6C3F1F1D2C1F1F1F1F4F6F0F1F3F5F5F0F6F84040404040F5F4D2C1D2C2D2C340E7C2D6D2E240404040404040404040E0E0E4A399858388A3404040404040E0F9F9F9F9C1E940404040F5F2F8D5D3C4F9F7F8F0F5F7C1C7D5E200017B3768BFC2CCF0820706020103A00000020749F107950000008000251203000000000012210978052818000000000000000080
"""
text2 = """
F1F1F0F0723425E1A8E08200F1F5F3F7F4F2F4F5F0F0F1F7F4F1F0F0F7F0F0F4F0F0F0F0F0F0F0F0F0F0F0F3F0F0F0F1F2F0F2F1F2F4F9F2F0F0F0F0F0F4F1F2F5F1F2F0F2F1F3F4F9F2F0F2F5F1F2F5F2F8F5F1F0F1F0F1F5F1F1F3F2F0F1F0F0F1F9F0F0F5F3F9F9F6F0F9F6F7F3F8F0F5F0F0F1F0F9F6F7F3F0F0F1F1F8F0F3F7F3F7F4F2F4F5F0F0F1F7F4F1F0F0F7C4F2F5F1F2F2F0F1F1F5F0F4F1F2F3F4F5F0F0F0F0F0F2F2F5404040404040404040C3F1F0C1C1F1F0F1F0F1F4F8F2F3F2F6F5F54040404040F6F3C5D8E4C5D5E240E6D6D9D3C4D3C9D5C5E0C18599A340A5819540D585A2A2A3998181A340F4F5E0D9D6E3E3C5D9C4C1D4E0F3F0F1F2C3C140404040E0F5F2F8F9F7F8F0F5F7C1C7D5E20001E5E9B1924B0B49260706020103A00000398F896D07F80000008000251202000000000012210978052818000000000000000080
"""


# Decode both messages
msg_bytes1 = bytes.fromhex(text)
msg_bytes2 = bytes.fromhex(text2)

doc_dec1, _ = iso8583.decode(msg_bytes1, spec)
doc_dec2, _ = iso8583.decode(msg_bytes2, spec)

# Parse subfields for both decoded messages
def parse_all_subfields(doc_dec):
    for k, v in doc_dec.items():
        ss = spec[k].get("sub_field_specs")
        if ss is not None:
            parsed = parse_sub_field(v, ss)
            doc_dec[k] = parsed
    return doc_dec

doc_dec1 = parse_all_subfields(doc_dec1)
doc_dec2 = parse_all_subfields(doc_dec2)




# Normalize both dicts to DataFrames
df1 = pd.json_normalize(doc_dec1)
df2 = pd.json_normalize(doc_dec2)

# Get all columns from both
def safe_sort_key(col):
    parts = col.split('.')
    key = []
    for p in parts:
        if p.isdigit():
            key.append((0, int(p)))
        else:
            key.append((1, p))
    return tuple(key)

all_cols_set = set(df1.columns) | set(df2.columns)
cols_rest = [c for c in all_cols_set if c not in ('t', 'p')]
all_cols = []
if 't' in all_cols_set:
    all_cols.append('t')
if 'p' in all_cols_set:
    all_cols.append('p')
all_cols += sorted(cols_rest, key=safe_sort_key)
df1 = df1.reindex(columns=all_cols, fill_value='_______')
df2 = df2.reindex(columns=all_cols, fill_value='_______')

# Compare and build comparison DataFrame
rows = []


for col in all_cols:
    val1 = str(df1.iloc[0][col])
    val2 = str(df2.iloc[0][col])
    if '.' in col:
        main_field, sub_field = col.split('.', 1)
        main_desc = spec.get(main_field, {}).get('desc', main_field)
        sub_specs = spec.get(main_field, {}).get('sub_field_specs', {})
        sub_desc = sub_specs.get(sub_field, {}).get('desc', sub_field)
        field_name = main_desc + "." + sub_desc
    else:
        field_name = spec.get(col, {}).get('desc', col)
    rows.append({'field': col, 'field_name': field_name, 'value1': val1, 'value2': val2})

cmp_df = pd.DataFrame(rows)

# Style the DataFrame to color different rows red


def highlight_info(row):
    # field, field_name, value1, value2
    val1 = row['value1']
    val2 = row['value2']
    # Slightly more prominent, still soft colors
    green_soft = 'background-color: rgba(46,204,113,0.72)'
    red_soft = 'background-color: rgba(231,76,60,0.72)'
    orange_soft = 'background-color: rgba(243,156,18,0.72)'

    if val1 == '_______' and val2 != '_______':
        # Added in 2 -> highlight value2
        return ['', '', '', green_soft]
    elif val1 != '_______' and val2 == '_______':
        # Missing in 2 -> highlight value1
        return ['', '', red_soft, '']
    elif val1 != val2:
        # Values differ -> highlight both values
        return ['', '', orange_soft, orange_soft]
    else:
        return [''] * 4

styled_cmp_df = cmp_df.style.apply(highlight_info, axis=1).hide(axis=0)


# Inject custom CSS to shift content left and style table
st.markdown("""
    <style>
    section.main > div {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    table {
        width: 100% !important;
        table-layout: auto !important;
    }
    th.col0, td.col0 { width: 50px !important; } /* field */
    th.col1, td.col1 { width: 200px !important; white-space: nowrap !important; } /* field_name */
    th.col2, td.col2 { width: 150px !important; } /* value1 */
    th.col3, td.col3 { width: 150px !important; } /* value2 */
    </style>
""", unsafe_allow_html=True)

st.markdown("### Comparison of Decoded Messages")
st.markdown(styled_cmp_df.to_html(), unsafe_allow_html=True)

