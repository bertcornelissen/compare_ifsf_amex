import streamlit as st
import difflib
import html

st.title("File Comparison")

col1, col2 = st.columns(2)

file_a = col1.file_uploader("Upload File A", type=None)
file_b = col2.file_uploader("Upload File B", type=None)

if file_a and file_b:
    text_a = file_a.read().decode("utf-8").splitlines()
    text_b = file_b.read().decode("utf-8").splitlines()

    from difflib import HtmlDiff

    diff_html = HtmlDiff(wrapcolumn=100).make_file(
        text_a,
        text_b,
        file_a.name,
        file_b.name
    )

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
        margin-left: -475px; /* Shift the table to the left */
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
    htmlx = diff_html.replace("</head>", dark_css + "</head>")

    # with st.expander("Show full diff", expanded=True):
    st.html(htmlx)
