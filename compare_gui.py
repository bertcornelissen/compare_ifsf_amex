import streamlit as st
from pathlib import Path
import tempfile
import yaml
from main import (
    split_messages,
    parse_message,
    diff_fields,
    ParsedField
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
if 'config' not in st.session_state:
    st.session_state.config = None

def load_session_config(config_path: str = "config.yaml") -> dict:
    """Load configuration into session-specific dict (thread-safe for multiple users)."""
    config = {
        'field_classes': {},
        'ignored_fields': set(),
        'ignored_subfields': {}
    }
    
    try:
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, 'r') as f:
                yaml_config = yaml.safe_load(f)
            
            # Load field classes
            if 'field_classes' in yaml_config:
                config['field_classes'] = {
                    category: set(fields) 
                    for category, fields in yaml_config['field_classes'].items()
                }
            
            # Load ignored fields
            if 'ignored_fields' in yaml_config:
                config['ignored_fields'] = set(yaml_config['ignored_fields'])
            
            # Load ignored subfields
            if 'ignored_subfields' in yaml_config:
                config['ignored_subfields'] = {
                    field_num: set(subfields)
                    for field_num, subfields in yaml_config['ignored_subfields'].items()
                }
            
            return config
    except Exception as e:
        st.error(f"Error loading config: {e}")
    
    # Default configuration
    config['field_classes'] = {
        "FINANCIAL": {"004"},
        "SECURITY": {"052", "053", "055"},
        "OPERATIONAL": {"007", "011", "012", "033"},
    }
    config['ignored_fields'] = {"011"}
    config['ignored_subfields'] = {
        "007": {"Time"},
        "012": {"Day", "Time"},
        "022": {"8-Cardmember Authentication Method", "9-Cardmember Authentication Entity", 
                "10-Card Data Output Capability", "11-Terminal Output Capability"},
        "043": {"2-Postal Code"}
    }
    return config

def normalize_with_config(fields: dict, config: dict) -> dict:
    """Normalize fields using session-specific config."""
    out = {}
    ignored_fields = config['ignored_fields']
    ignored_subfields = config['ignored_subfields']

    for num, field in fields.items():
        # Suppress entire field value?
        if num in ignored_fields:
            out[num] = ParsedField(
                number=field.number,
                name=field.name,
                raw_value="<IGNORED>",
                subfields={}
            )
            continue

        # Otherwise suppress selected subfields
        ignored_subs = ignored_subfields.get(num, set())
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

def classify_with_config(diff, config: dict) -> str:
    """Classify differences using session-specific config."""
    field_classes = config['field_classes']
    changed_fields = set(diff.changed) | set(diff.added) | set(diff.removed)

    if changed_fields & field_classes.get("FINANCIAL", set()):
        return "FUNCTIONALLY DIFFERENT"

    if changed_fields & field_classes.get("SECURITY", set()):
        return "POTENTIALLY IMPACTFUL"

    if diff.added or diff.removed:
        return "FORMAT / ROUTING CHANGE ONLY"

    if diff.changed:
        return "OPERATIONAL DIFFERENCES ONLY"

    return "NO DIFFERENCES"

def render_report_local(diff, verdict: str, message_type: str = "") -> str:
    """Render report (copied from main.py to avoid global state issues)."""
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
                if f.before:
                    out.append(f"  Before: {f.before.raw_value}")
                if f.after:
                    out.append(f"  After : {f.after.raw_value}")
            out.append("")

    return "\n".join(out)

def display_config_info(config):
    """Display current configuration in sidebar."""
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        with st.expander("Field Classes", expanded=False):
            for category, fields in config['field_classes'].items():
                st.write(f"**{category}:**")
                st.write(", ".join(sorted(fields)))
        
        with st.expander("Ignored Fields", expanded=False):
            if config['ignored_fields']:
                st.write(", ".join(sorted(config['ignored_fields'])))
            else:
                st.write("None")
        
        with st.expander("Ignored Subfields", expanded=False):
            if config['ignored_subfields']:
                for field_num, subfields in sorted(config['ignored_subfields'].items()):
                    st.write(f"**Field {field_num}:**")
                    for subfield in sorted(subfields):
                        st.write(f"  - {subfield}")
            else:
                st.write("None")

def compare_files(file1_content, file2_content, config, compare_request=True, compare_response=True):
    """Compare two ISO 8583 message files using session-specific config."""
    results = {}
    
    # Split into Request and Response sections
    req_a, resp_a = split_messages(file1_content)
    req_b, resp_b = split_messages(file2_content)
    
    # Compare Request messages
    if compare_request:
        parsed_req_a = normalize_with_config(parse_message(req_a), config)
        parsed_req_b = normalize_with_config(parse_message(req_b), config)
        
        diff_req = diff_fields(parsed_req_a, parsed_req_b)
        verdict_req = classify_with_config(diff_req, config)
        report_req = render_report_local(diff_req, verdict_req, "REQUEST")
        
        results['request'] = {
            'diff': diff_req,
            'verdict': verdict_req,
            'report': report_req,
            'fields_parsed_a': len(parsed_req_a),
            'fields_parsed_b': len(parsed_req_b)
        }
    
    # Compare Response messages if they exist
    if compare_response and resp_a and resp_b:
        parsed_resp_a = normalize_with_config(parse_message(resp_a), config)
        parsed_resp_b = normalize_with_config(parse_message(resp_b), config)
        
        diff_resp = diff_fields(parsed_resp_a, parsed_resp_b)
        verdict_resp = classify_with_config(diff_resp, config)
        report_resp = render_report_local(diff_resp, verdict_resp, "RESPONSE")
        
        results['response'] = {
            'diff': diff_resp,
            'verdict': verdict_resp,
            'report': report_resp,
            'fields_parsed_a': len(parsed_resp_a),
            'fields_parsed_b': len(parsed_resp_b)
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
    
    # Load configuration into session state (isolated per user)
    config_path = st.sidebar.text_input("Config File", value="config.yaml")
    if st.sidebar.button("Reload Configuration") or st.session_state.config is None:
        with st.spinner("Loading configuration..."):
            st.session_state.config = load_session_config(config_path)
            st.sidebar.success("Configuration loaded successfully!")
    
    display_config_info(st.session_state.config)
    
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
                    
                    # Perform comparison with session-specific config
                    results = compare_files(
                        file1_content, 
                        file2_content, 
                        st.session_state.config,
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

if __name__ == "__main__":
    main()
