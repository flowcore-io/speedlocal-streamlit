"""
Sidebar configuration component.
Adapted from existing SidebarConfig in _streamlit_ui.py
Enhanced with native OS file picker for DuckDB selection.
"""

import streamlit as st
from pathlib import Path
import tkinter as tk
from tkinter import filedialog


def open_file_picker(file_types: str = "DuckDB Files") -> str:
    """
    Open native file picker dialog to select a file.
    
    Args:
        file_types: Description for the file type filter
        
    Returns:
        Selected file path as string, or empty string if cancelled
    """
    try:
        # Create a hidden root window
        root = tk.Tk()
        root.withdraw()  # Hide the window
        root.attributes('-topmost', True)  # Bring dialog to front
        
        # Open file dialog filtered to .duckdb files
        file_path = filedialog.askopenfilename(
            title="Select DuckDB Database File",
            filetypes=[
                ("DuckDB Files", "*.duckdb"),
                ("All Files", "*.*")
            ],
            initialdir=str(Path.cwd())
        )
        
        root.destroy()
        return file_path
    except Exception as e:
        st.error(f"Error opening file picker: {e}")
        return ""


def render_sidebar() -> dict:
    """
    Render sidebar UI elements and return configuration dictionary.
    
    Returns:
        Dictionary with keys: 'db_source', 'mapping_csv', 'is_url', 'reload_requested', 'valid'
    """
    st.sidebar.header("Database Connection")
    
    # Connection Type Selection
    connection_type = st.sidebar.radio(
        "Connection Type:",
        ["Azure URL", "Local File"],
        help="Choose whether to connect to a database via Azure URL or local file path"
    )

    # Get database source based on connection type
    if connection_type == "Azure URL":
        db_source = st.sidebar.text_input(
            "Database URL:",
            value="https://speedlocal.flowcore.app/api/duckdb/share/97799049f12652bf8bca8be8c6f2836f",
            help="Enter the Azure blob storage URL for the DuckDB database"
        )
        is_url = True
    else:
        # Local File - with native file picker
        st.sidebar.subheader("Local Database File")
        
        # Initialize session state for selected file
        if 'selected_duckdb_path' not in st.session_state:
            st.session_state.selected_duckdb_path = ""
        
        # File picker button
        st.sidebar.write("Choose a DuckDB file:")
        if st.sidebar.button("📂 Browse", type="secondary", use_container_width=True):
            selected = open_file_picker()
            if selected:
                st.session_state.selected_duckdb_path = selected
                st.rerun()
        
        # Display selected file
        if st.session_state.selected_duckdb_path:
            st.sidebar.success(f"✅ Selected: `{Path(st.session_state.selected_duckdb_path).name}`")
            db_source = st.session_state.selected_duckdb_path
            
            # Option to clear selection
            if st.sidebar.button("🗑️ Clear Selection", use_container_width=True):
                st.session_state.selected_duckdb_path = ""
                st.rerun()
        else:
            st.sidebar.info("ℹ️ Click 'Browse' to select a DuckDB file")
            db_source = ""
        
        # Fallback: manual path entry
        st.sidebar.write("Or enter path manually:")
        manual_path = st.sidebar.text_input(
            "Database File Path:",
            value="",
            placeholder="e.g., C:/databases/speedlocal.duckdb",
            help="Enter the full or relative path to your DuckDB database file"
        )
        
        # Use manual path if provided and no file selected via browser
        if manual_path and not db_source:
            db_source = manual_path
        
        is_url = False

    # Mapping CSV input
    st.sidebar.subheader("Mapping Configuration")
    mapping_csv = st.sidebar.text_input(
        "Mapping CSV Path:",
        value="inputs/mapping_db_views.csv",
        help="Path to the mapping CSV file that defines data views"
    )

    # Add a button to load/reload data
    st.sidebar.divider()
    reload_requested = st.sidebar.button("🔄 Reload Data", type="primary", use_container_width=True)

    # Validate inputs
    valid = True
    if not db_source:
        st.sidebar.warning("Please provide a database source.")
        valid = False
    
    if not mapping_csv:
        st.sidebar.warning("Please provide a mapping CSV path.")
        valid = False
    
    return {
        'db_source': db_source,
        'mapping_csv': mapping_csv,
        'is_url': is_url,
        'reload_requested': reload_requested,
        'valid': valid
    }