"""
Sidebar configuration component.
Adapted from existing SidebarConfig in _streamlit_ui.py
"""

import streamlit as st


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
            value="https://speedlocal.flowcore.app/api/duckdb/share/cdec00e6d060fb1cfd56c4e9e046289f",
            help="Enter the Azure blob storage URL for the DuckDB database"
        )
        is_url = True
    else:
        db_source = st.sidebar.text_input(
            "Database File Path:",
            value="inputs/speedlocal_times_db_bornholm_v3.duckdb",
            help="Enter the local path to your DuckDB database file"
        )
        is_url = False

    # Mapping CSV input
    mapping_csv = st.sidebar.text_input(
        "Mapping CSV Path:",
        value="inputs/mapping_db_views.csv",
        help="Path to the mapping CSV file that defines data views"
    )

    # Add a button to load/reload data
    reload_requested = st.sidebar.button("🔄 Reload Data", type="primary")

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
