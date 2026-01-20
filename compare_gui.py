import streamlit as st
from pathlib import Path
import difflib
from difflib import HtmlDiff

from main import (
    load_config,
    split_messages,
    parse_message,
    normalize,
    diff_fields,
    classify,
    render_report,
    FIELD_CLASSES,
    IGNORED_FIELD_VALUES,
    IGNORED_SUBFIELDS
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
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        with st.expander("Field Classes", expanded=False):
            for category, fields in FIELD_CLASSES.items():
                st.write(f"**{category}:**")
                st.write(", ".join(sorted(fields)))
        
        with st.expander("Ignored Fields", expanded=False):
            if IGNORED_FIELD_VALUES:
                st.write(", ".join(sorted(IGNORED_FIELD_VALUES)))
            else:
                st.write("None")
        
        with st.expander("Ignored Subfields", expanded=False):
            if IGNORED_SUBFIELDS:
                for field_num, subfields in sorted(IGNORED_SUBFIELDS.items()):
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
    if verdict == "NO DIFFERENCES":
        st.success(f"✅ {verdict}")
    elif verdict == "OPERATIONAL DIFFERENCES ONLY":
        st.info(f"ℹ️ {verdict}")
    elif verdict == "FORMAT / ROUTING CHANGE ONLY":
        st.warning(f"⚠️ {verdict}")
    elif verdict == "POTENTIALLY IMPACTFUL":
        st.warning(f"⚠️ {verdict}")
    elif verdict == "FUNCTIONALLY DIFFERENT":
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

def display_field_changes(diff):
    """Display detailed field changes."""
    
    if diff.added:
        with st.expander(f"➕ Fields Added ({len(diff.added)})", expanded=True):
            for f in diff.added.values():
                st.write(f"**{f.number}** - {f.name}")
                if f.after and f.after.raw_value:
                    st.code(f.after.raw_value)
    
    if diff.removed:
        with st.expander(f"➖ Fields Removed ({len(diff.removed)})", expanded=True):
            for f in diff.removed.values():
                st.write(f"**{f.number}** - {f.name}")
                if f.before and f.before.raw_value:
                    st.code(f.before.raw_value)
    
    if diff.changed:
        with st.expander(f"🔄 Fields Changed ({len(diff.changed)})", expanded=True):
            for f in diff.changed.values():
                st.write(f"**{f.number}** - {f.name}")
                
                # Show subfield-level changes for fields with subfields
                if f.before and f.after and (f.before.subfields or f.after.subfields):
                    all_subfield_keys = set(f.before.subfields.keys()) | set(f.after.subfields.keys())
                    
                    for sk in sorted(all_subfield_keys):
                        before_val = f.before.subfields.get(sk, "<missing>")
                        after_val = f.after.subfields.get(sk, "<missing>")
                        if before_val != after_val:
                            col1, col2 = st.columns(2)
                            with col1:
                                st.text(f"{sk} - Before:")
                                st.code(before_val)
                            with col2:
                                st.text(f"{sk} - After:")
                                st.code(after_val)
                else:
                    # Show raw value changes for simple fields
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text("Before:")
                        st.code(f.before.raw_value if f.before else "<missing>")
                    with col2:
                        st.text("After:")
                        st.code(f.after.raw_value if f.after else "<missing>")
                
                st.divider()

def main():
    st.title("🔍 ISO 8583 Message Comparator")
    st.markdown("Compare two ISO 8583 message files and analyze their differences")
    
    # Load configuration
    config_path = st.sidebar.text_input("Config File", value="config.yaml")
    if st.sidebar.button("Reload Configuration"):
        with st.spinner("Loading configuration..."):
            load_config(config_path)
            st.sidebar.success("Configuration loaded successfully!")
    
    # Load config on first run
    if not FIELD_CLASSES:
        load_config(config_path)
    
    display_config_info()
    
    # Main content area
    st.header("Upload Files to Compare")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("File 1")
        file1 = st.file_uploader("Upload first ISO 8583 message file", type=['txt'], key="file1")
        
    with col2:
        st.subheader("File 2")
        file2 = st.file_uploader("Upload second ISO 8583 message file", type=['txt'], key="file2")
    
    # Comparison options
    st.subheader("Comparison Options")
    col1, col2 = st.columns(2)
    
    with col1:
        compare_request = st.checkbox("Compare Request Messages", value=True)
    with col2:
        compare_response = st.checkbox("Compare Response Messages", value=True)
    
    # Compare button
    if st.button("🔍 Compare Messages", type="primary", use_container_width=True):
        if file1 is None or file2 is None:
            st.error("Please upload both files before comparing")
        else:
            with st.spinner("Comparing messages..."):
                try:
                    # Read file contents
                    file1_content = file1.read().decode('utf-8')
                    file2_content = file2.read().decode('utf-8')
                    
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
                    st.session_state.file1_name = file1.name
                    st.session_state.file2_name = file2.name
                    
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
            ["Comparison Report", "Side-by-Side Diff"],
            horizontal=True,
            help="Comparison Report shows structured field differences. Side-by-Side Diff shows character-level differences in HTML format."
        )
        
        if view_mode == "Comparison Report":
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
                    st.text(results['request']['report'])
            
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
                    st.text(results['response']['report'])
            
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
                use_container_width=True
            )
        
        else:  # Side-by-Side Diff
            st.subheader("📊 Side-by-Side Comparison")
            
            # Let user choose what to compare
            diff_target = st.selectbox(
                "Select what to compare:",
                ["Full File", "Request Message Only", "Response Message Only"]
            )
            
            if diff_target == "Full File":
                display_side_by_side_diff(
                    st.session_state.file1_content,
                    st.session_state.file2_content,
                    st.session_state.file1_name,
                    st.session_state.file2_name
                )
            elif diff_target == "Request Message Only":
                if 'request' in st.session_state.results:
                    display_side_by_side_diff(
                        st.session_state.results['request']['raw_a'],
                        st.session_state.results['request']['raw_b'],
                        f"{st.session_state.file1_name} (Request)",
                        f"{st.session_state.file2_name} (Request)"
                    )
                else:
                    st.info("Request comparison not available")
            elif diff_target == "Response Message Only":
                if 'response' in st.session_state.results:
                    display_side_by_side_diff(
                        st.session_state.results['response']['raw_a'],
                        st.session_state.results['response']['raw_b'],
                        f"{st.session_state.file1_name} (Response)",
                        f"{st.session_state.file2_name} (Response)"
                    )
                else:
                    st.info("Response comparison not available")

if __name__ == "__main__":
    main()
