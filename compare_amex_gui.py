import streamlit as st
from difflib import HtmlDiff
import pandas as pd
import iso8583

import compare_amex_cli
from compare_amex_cli import (
    load_config,
    split_messages,
    parse_message,
    normalize,
    diff_fields,
    classify,
    render_report,
    IGNORED_FIELD_VALUES,
    IGNORED_SUBFIELDS,
    spec
)

# Page config
st.set_page_config(
    page_title="ISO 8583 Message Comparator",
    page_icon="🔍",
    layout="wide"
)

# Initialize session state
if 'comparison_done' not in st.session_state:
    st.session_state.comparison_done = False
if 'results' not in st.session_state:
    st.session_state.results = {}
if 'file1_content' not in st.session_state:
    st.session_state.file1_content = None
if 'file2_content' not in st.session_state:
    st.session_state.file2_content = None

def display_config_info():
    """Display current configuration in sidebar."""
    # Always read from the module so we see the values loaded by load_config,
    # not the stale local bindings captured at import time.
    ignored_fields = compare_amex_cli.IGNORED_FIELD_VALUES
    ignored_subfields = compare_amex_cli.IGNORED_SUBFIELDS

    with st.sidebar:
        st.header("⚙️ Configuration")
        
        with st.expander("Ignored Fields", expanded=False):
            if ignored_fields:
                st.write(", ".join(sorted(ignored_fields)))
            else:
                st.write("None")
        
        with st.expander("Ignored Subfields", expanded=False):
            if ignored_subfields:
                for field_num, subfields in sorted(ignored_subfields.items()):
                    st.write(f"**Field {field_num}:**")
                    for subfield in sorted(subfields):
                        st.write(f"  - {subfield}")
            else:
                st.write("None")

def compare_files(file1_content, file2_content, compare_request=True, compare_response=True):
    """Compare two ISO 8583 message files."""
    results = {}
    
    # Split into Request and Response sections
    req_a, resp_a = split_messages(file1_content)
    req_b, resp_b = split_messages(file2_content)
    
    # Compare Request messages
    if compare_request:
        parsed_req_a = normalize(parse_message(req_a))
        parsed_req_b = normalize(parse_message(req_b))
        
        diff_req = diff_fields(parsed_req_a, parsed_req_b)
        verdict_req = classify(diff_req)
        report_req = render_report(diff_req, verdict_req, "REQUEST")
        
        results['request'] = {
            'diff': diff_req,
            'verdict': verdict_req,
            'report': report_req,
            'fields_parsed_a': len(parsed_req_a),
            'fields_parsed_b': len(parsed_req_b),
            'raw_a': req_a,
            'raw_b': req_b
        }
    
    # Compare Response messages if they exist
    if compare_response and resp_a and resp_b:
        parsed_resp_a = normalize(parse_message(resp_a))
        parsed_resp_b = normalize(parse_message(resp_b))
        
        diff_resp = diff_fields(parsed_resp_a, parsed_resp_b)
        verdict_resp = classify(diff_resp)
        report_resp = render_report(diff_resp, verdict_resp, "RESPONSE")
        
        results['response'] = {
            'diff': diff_resp,
            'verdict': verdict_resp,
            'report': report_resp,
            'fields_parsed_a': len(parsed_resp_a),
            'fields_parsed_b': len(parsed_resp_b),
            'raw_a': resp_a,
            'raw_b': resp_b
        }
    
    return results

def display_verdict(verdict):
    """Display verdict with appropriate color coding."""
    if verdict == "NO DIFFERENCES FOUND":
        st.success(f"✅ {verdict}")
    elif verdict == "DIFFERENCES FOUND":
        st.error(f"❌ {verdict}")
    else:
        st.write(verdict)

def display_side_by_side_diff(text1, text2, title1="File 1", title2="File 2"):
    """Display side-by-side diff using difflib.HtmlDiff."""
    
    # Split texts into lines
    lines1 = text1.splitlines()
    lines2 = text2.splitlines()

    # Generate HTML diff
    html_diff = HtmlDiff(wrapcolumn=100).make_file(
        lines1,
        lines2,
        title1,
        title2
    )

    # Add custom CSS to improve color scheme
    dark_css = """
    <style>
    body {
        background-color: #1e1e1e;
        color: #d4d4d4;
        display: flex; /* Use flexbox for centering */
        justify-content: center; /* Center horizontally */
        align-items: center; /* Center vertically */
        height: 100vh; /* Full viewport height */
        margin: 0; /* Remove default margin */
    }

    table.diff {
        font-size: 13px;
        font-family: Consolas, Monaco, 'Courier New', monospace;
        line-height: 1.4;
        border-collapse: collapse;
        margin-left: 0px; /* Shift the table to the left */
        width: 95%; /* Use most of the available width */
    }

    /* Table headers */
    .diff_header {
        background-color: #252526;
        color: #cccccc;
    }

    /* Line numbers */
    .diff_header a {
        color: #6a9955;
        text-decoration: none;
    }

    /* Added / removed lines */
    .diff_add {
        background-color: #144212; /* Dark green for added lines */
        color: #ffffff; /* White text for contrast */
    }

    .diff_sub {
        background-color: #8B0000; /* Dark red for removed lines */
        color: #ffffff; /* White text for contrast */
    }

    /* Changed text */
    .diff_chg {
        background-color: #1E90FF; /* Dodger blue for changed lines */
        color: #ffffff; /* White text for contrast */
    }

    /* Table borders */
    table.diff td {
        border: 1px solid #333333;
    }
    </style>
    """

    # Inject custom CSS into the HTML
    htmlx = html_diff.replace("</head>", dark_css + "</head>")

    # Display in streamlit using st.html
    st.html(htmlx)

def display_diff_summary(diff):
    """Display a summary of differences in columns."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Fields Added", len(diff.added))
    with col2:
        st.metric("Fields Removed", len(diff.removed))
    with col3:
        st.metric("Fields Changed", len(diff.changed))

def parse_sub_field(data, spec):
    """Parse subfields from field data."""
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

def parse_all_subfields(doc_dec):
    """Parse all subfields in a decoded message."""
    for k, v in doc_dec.items():
        ss = spec[k].get("sub_field_specs")
        if ss is not None:
            parsed = parse_sub_field(v, ss)
            doc_dec[k] = parsed
    return doc_dec

def create_pandas_comparison(raw_msg1, raw_msg2, show_only_differences=False):
    """Create a pandas DataFrame comparison with highlighted differences."""
    try:
        # Decode both messages
        msg_bytes1 = bytes.fromhex(raw_msg1.replace("\n", "").strip())
        msg_bytes2 = bytes.fromhex(raw_msg2.replace("\n", "").strip())
        
        doc_dec1, _ = iso8583.decode(msg_bytes1, spec)
        doc_dec2, _ = iso8583.decode(msg_bytes2, spec)
        
        # Parse subfields for both
        doc_dec1 = parse_all_subfields(doc_dec1)
        doc_dec2 = parse_all_subfields(doc_dec2)
        
        # Normalize to DataFrames
        df1 = pd.json_normalize(doc_dec1)
        df2 = pd.json_normalize(doc_dec2)
        
        # Sort columns
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
        
        # Build comparison DataFrame
        rows = []
        for col in all_cols:
            # Check if this field/subfield should be ignored
            should_ignore = False
            
            # Extract field number (without subfield) for checking
            field_num = col.split('.')[0] if '.' in col else col
            
            # Check for ignored fields (entire field)
            # Need to normalize field numbers: try both with and without leading zeros
            if field_num in IGNORED_FIELD_VALUES:
                should_ignore = True
            # Try alternative formats: "12" vs "012", "4" vs "04"
            elif field_num.isdigit():
                # Try with leading zero
                field_with_zero = field_num.zfill(3)  # "12" -> "012", "4" -> "004"
                field_without_leading = field_num.lstrip('0') or '0'  # "012" -> "12", "04" -> "4"
                if field_with_zero in IGNORED_FIELD_VALUES or field_without_leading in IGNORED_FIELD_VALUES:
                    should_ignore = True
            
            # Check for ignored subfields
            if '.' in col:
                main_field, sub_field = col.split('.', 1)
                # Try with and without leading zeros for field number
                ignored_subs = IGNORED_SUBFIELDS.get(main_field, set())
                if not ignored_subs:
                    # Try with leading zero removed/added
                    alt_field = main_field.lstrip('0') if main_field.startswith('0') else f"0{main_field}"
                    ignored_subs = IGNORED_SUBFIELDS.get(alt_field, set())
                
                # Check if subfield name matches any ignored subfield
                sub_specs = spec.get(main_field, {}).get('sub_field_specs', {})
                sub_desc = sub_specs.get(sub_field, {}).get('desc', sub_field)
                if sub_field in ignored_subs or sub_desc in ignored_subs:
                    should_ignore = True
            
            val1 = str(df1.iloc[0][col])
            val2 = str(df2.iloc[0][col])
            
            # Skip ignored fields/subfields only if present in both files
            if should_ignore and val1 != '_______' and val2 != '_______':
                continue
            
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
        
        if show_only_differences:
            cmp_df = cmp_df[(cmp_df['value1'] != cmp_df['value2']) | (cmp_df['value1'] == '_______') | (cmp_df['value2'] == '_______')]
        
        # Apply styling
        def highlight_info(row):
            val1 = row['value1']
            val2 = row['value2']
            green_soft = 'background-color: rgba(46,204,113,0.72)'
            red_soft = 'background-color: rgba(231,76,60,0.72)'
            orange_soft = 'background-color: rgba(243,156,18,0.72)'
            
            if val1 == '_______' and val2 != '_______':
                return ['', '', '', green_soft]
            elif val1 != '_______' and val2 == '_______':
                return ['', '', red_soft, '']
            elif val1 != val2:
                return ['', '', orange_soft, orange_soft]
            else:
                return [''] * 4
        
        styled_cmp_df = cmp_df.style.apply(highlight_info, axis=1).hide(axis=0)
        return styled_cmp_df
    
    except Exception as e:
        st.error(f"Error creating table comparison: {str(e)}")
        st.write("Debugging Information:")
        st.write(f"Raw Message 1: {raw_msg1}")
        st.write(f"Raw Message 2: {raw_msg2}")
        st.write("Decoded Message 1:")
        try:
            st.write(iso8583.decode(bytes.fromhex(raw_msg1.replace("\n", "").strip()), spec))
        except Exception as decode_error:
            st.write(f"Error decoding Message 1: {decode_error}")
        st.write("Decoded Message 2:")
        try:
            st.write(iso8583.decode(bytes.fromhex(raw_msg2.replace("\n", "").strip()), spec))
        except Exception as decode_error:
            st.write(f"Error decoding Message 2: {decode_error}")
        return None
    
def display_field_changes(diff):
    """Display detailed field changes in a compact format."""

    if diff.added:
        with st.expander(f"➕ Fields Added ({len(diff.added)})", expanded=True):
            # Create a table for compact display of added fields
            added_data = []
            for f in diff.added.values():
                added_data.append({
                    "Field": f.number,
                    "Description": f.name,
                    "Value": f.after.raw_value if f.after and f.after.raw_value else "<missing>"
                })

            # Convert to DataFrame for better display
            if added_data:
                df_added = pd.DataFrame(added_data)
                st.dataframe(df_added, width='stretch')

    if diff.removed:
        with st.expander(f"➖ Fields Removed ({len(diff.removed)})", expanded=True):
            # Create a table for compact display of removed fields
            removed_data = []
            for f in diff.removed.values():
                removed_data.append({
                    "Field": f.number,
                    "Description": f.name,
                    "Value": f.before.raw_value if f.before and f.before.raw_value else "<missing>"
                })

            # Convert to DataFrame for better display
            if removed_data:
                df_removed = pd.DataFrame(removed_data)
                st.dataframe(df_removed, width='stretch')

    if diff.changed:
        with st.expander(f"🔄 Fields Changed ({len(diff.changed)})", expanded=True):
            # Create a table for compact display
            changed_data = []
            for f in diff.changed.values():
                if f.before and f.after and (f.before.subfields or f.after.subfields):
                    # Subfield-level changes
                    all_subfield_keys = set(f.before.subfields.keys()) | set(f.after.subfields.keys())
                    for sk in sorted(all_subfield_keys):
                        before_val = f.before.subfields.get(sk, "<missing>")
                        after_val = f.after.subfields.get(sk, "<missing>")
                        if before_val != after_val:
                            changed_data.append({
                                "Field": f"{f.number}.{sk}",
                                "Description": f"{f.name} - Subfield {sk}",
                                "Before": before_val,
                                "After": after_val
                            })
                else:
                    # Simple field changes
                    changed_data.append({
                        "Field": f.number,
                        "Description": f.name,
                        "Before": f.before.raw_value if f.before else "<missing>",
                        "After": f.after.raw_value if f.after else "<missing>"
                    })

            # Convert to DataFrame for better display
            if changed_data:
                df_changed = pd.DataFrame(changed_data)
                st.dataframe(df_changed, width='stretch')

def render_report(diff, verdict, message_type):
    """Render a full text report including added fields content."""
    report = []
    report.append(f"=== {message_type} MESSAGE COMPARISON ===")
    report.append(f"Verdict: {verdict}")

    if diff.added:
        report.append("\nFields Added:")
        for f in diff.added.values():
            value = f.after.raw_value if f.after and f.after.raw_value else "<missing>"
            report.append(f"{f.number:<30} ({f.name:<50}): {value:20}")

    if diff.removed:
        report.append("\nFields Removed:")
        for f in diff.removed.values():
            value = f.before.raw_value if f.before and f.before.raw_value else "<missing>"
            report.append(f"{f.number:<30} ({f.name:<50}): {value:20}")

    if diff.changed:
        report.append("\nFields Changed:")
        for f in diff.changed.values():
            before = f.before.raw_value if f.before else "<missing>"
            after = f.after.raw_value if f.after else "<missing>"
            report.append(f"{f.number:<30} ({f.name:<50}): Before: {before:20}, After: {after:20}")

    return "\n".join(report)

def main():
    st.title("🔍 AMEX ISO 8583 Message Comparator")
    st.markdown("Compare two ISO 8583 message files and analyze their differences")
    
    # Load configuration
    config_path = st.sidebar.text_input("Config File", value="ignored_fields.yaml")
    if st.sidebar.button("Reload Configuration"):
        with st.spinner("Loading configuration..."):
            load_config(config_path)
            st.sidebar.success("Configuration loaded successfully!")
    
    # Load config on first run or when the config path changes
    if 'config_loaded' not in st.session_state or st.session_state.get('last_config_path') != config_path:
        load_config(config_path)
        st.session_state.config_loaded = True
        st.session_state.last_config_path = config_path
    
    display_config_info()
    
    # Main content area
    st.header("Upload Files to Compare")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("File 1")
        tab_upload1, tab_paste1 = st.tabs(["📂 Upload File", "📋 Paste Content"])
        with tab_upload1:
            file1 = st.file_uploader("Upload first ISO 8583 message file", type=['txt'], key="file1")
        with tab_paste1:
            pasted1 = st.text_area("Paste file 1 content here", height=200, key="paste1")

    with col2:
        st.subheader("File 2")
        tab_upload2, tab_paste2 = st.tabs(["📂 Upload File", "📋 Paste Content"])
        with tab_upload2:
            file2 = st.file_uploader("Upload second ISO 8583 message file", type=['txt'], key="file2")
        with tab_paste2:
            pasted2 = st.text_area("Paste file 2 content here", height=200, key="paste2")
    
    # Comparison options
    st.subheader("Comparison Options")
    col1, col2 = st.columns(2)
    
    with col1:
        compare_request = st.checkbox("Compare Request Messages", value=True)
    with col2:
        compare_response = st.checkbox("Compare Response Messages", value=True)
    
    # Compare button
    if st.button("🔍 Compare Messages", type="primary", width='stretch'):
        # Resolve content from upload or paste for each file
        file1_content = None
        file1_name = None
        file2_content = None
        file2_name = None

        if file1 is not None:
            file1_content = file1.read().decode('utf-8')
            file1_name = file1.name
        elif pasted1 and pasted1.strip():
            file1_content = pasted1
            file1_name = "pasted_file_1.txt"

        if file2 is not None:
            file2_content = file2.read().decode('utf-8')
            file2_name = file2.name
        elif pasted2 and pasted2.strip():
            file2_content = pasted2
            file2_name = "pasted_file_2.txt"

        if file1_content is None or file2_content is None:
            st.error("Please upload or paste content for both files before comparing")
        else:
            with st.spinner("Comparing messages..."):
                try:
                    # Store file contents for diff view
                    st.session_state.file1_content = file1_content
                    st.session_state.file2_content = file2_content
                    
                    # Perform comparison
                    results = compare_files(
                        file1_content, 
                        file2_content, 
                        compare_request, 
                        compare_response
                    )
                    
                    # Store results in session state
                    st.session_state.results = results
                    st.session_state.comparison_done = True
                    st.session_state.file1_name = file1_name
                    st.session_state.file2_name = file2_name
                    
                    st.success("Comparison completed!")
                    
                except Exception as e:
                    st.error(f"Error during comparison: {str(e)}")
                    st.exception(e)
    
    # Display results if comparison has been done
    if st.session_state.comparison_done and st.session_state.results:
        st.divider()
        st.header("📊 Comparison Results")
        
        # View mode selector - Make it prominent
        st.subheader("Choose View Mode")
        view_mode = st.radio(
            "How would you like to view the comparison?",
            ["Table View", "Comparison Report", "Side-by-Side Diff"],
            horizontal=True,
            help="Table View shows a color-coded table. Comparison Report shows structured field differences. Side-by-Side Diff shows character-level differences in HTML format."
        )
        
        if view_mode == "Table View":
            # Custom CSS for pandas table styling
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
            
            # Option to show only differences
            show_only_differences = st.checkbox("Show only differences", value=False)

            if 'request' in st.session_state.results:
                st.markdown("### 📤 Request Message Comparison")
                styled_df = create_pandas_comparison(
                    st.session_state.results['request']['raw_a'],
                    st.session_state.results['request']['raw_b'],
                    show_only_differences
                )
                if styled_df is not None:
                    st.markdown(styled_df.to_html(), unsafe_allow_html=True)
                else:
                    st.error("Failed to create a styled DataFrame for the Request Message comparison.")

            if 'response' in st.session_state.results:
                st.divider()
                st.markdown("### 📥 Response Message Comparison")
                styled_df = create_pandas_comparison(
                    st.session_state.results['response']['raw_a'],
                    st.session_state.results['response']['raw_b'],
                    show_only_differences
                )
                if styled_df is not None:
                    st.markdown(styled_df.to_html(), unsafe_allow_html=True)
                else:
                    st.error("Failed to create a styled DataFrame for the Response Message comparison.")
        
        elif view_mode == "Comparison Report":
            # File names
            st.write(f"**File 1:** {st.session_state.file1_name}")
            st.write(f"**File 2:** {st.session_state.file2_name}")
            
            results = st.session_state.results
            
            # Request comparison results
            if 'request' in results:
                st.subheader("📤 REQUEST Message Comparison")
                
                display_verdict(results['request']['verdict'])
                
                st.write(f"Fields parsed from File 1: {results['request']['fields_parsed_a']}")
                st.write(f"Fields parsed from File 2: {results['request']['fields_parsed_b']}")
                
                display_diff_summary(results['request']['diff'])
                display_field_changes(results['request']['diff'])
                
                # Show full text report
                with st.expander("📄 View Full Text Report", expanded=False):
                    st.code(results['request']['report'])
            
            # Response comparison results
            if 'response' in results:
                st.divider()
                st.subheader("📥 RESPONSE Message Comparison")
                
                display_verdict(results['response']['verdict'])
                
                st.write(f"Fields parsed from File 1: {results['response']['fields_parsed_a']}")
                st.write(f"Fields parsed from File 2: {results['response']['fields_parsed_b']}")
                
                display_diff_summary(results['response']['diff'])
                display_field_changes(results['response']['diff'])
                
                # Show full text report
                with st.expander("📄 View Full Text Report", expanded=False):
                    st.code(results['response']['report'])
            
            # Download button for combined report
            st.divider()
            combined_report = []
            if 'request' in results:
                combined_report.append("=" * 70)
                combined_report.append("COMPARING REQUEST MESSAGES")
                combined_report.append("=" * 70)
                combined_report.append(results['request']['report'])
            
            if 'response' in results:
                combined_report.append("\n" + "=" * 70)
                combined_report.append("COMPARING RESPONSE MESSAGES")
                combined_report.append("=" * 70)
                combined_report.append(results['response']['report'])
            
            report_text = "\n".join(combined_report)
            
            st.download_button(
                label="📥 Download Full Report",
                data=report_text,
                file_name="comparison_report.txt",
                mime="text/plain",
                width='stretch'
            )
        
        else:  # Side-by-Side Diff
            st.subheader("📊 Side-by-Side Comparison")

            if 'request' in st.session_state.results:
                st.markdown("### 📤 Request Message")
                display_side_by_side_diff(
                    st.session_state.results['request']['raw_a'],
                    st.session_state.results['request']['raw_b'],
                    f"{st.session_state.file1_name} (Request)",
                    f"{st.session_state.file2_name} (Request)"
                )

            if 'response' in st.session_state.results:
                st.divider()
                st.markdown("### 📥 Response Message")
                display_side_by_side_diff(
                    st.session_state.results['response']['raw_a'],
                    st.session_state.results['response']['raw_b'],
                    f"{st.session_state.file1_name} (Response)",
                    f"{st.session_state.file2_name} (Response)"
                )

if __name__ == "__main__":
    main()