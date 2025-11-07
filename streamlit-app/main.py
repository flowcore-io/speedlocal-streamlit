"""
Main entry point for the modular TIMES Data Explorer application.
Refactored from times_app_test.py to support modular architecture.
"""

import streamlit as st
from pathlib import Path
import pandas as pd

from core.session_manager import SessionManager
from core.data_loader import DataLoaderManager
from core.filter_manager import FilterManager
from config.module_registry import ModuleRegistry
from components.sidebar import render_sidebar


def main():
    """Main Streamlit application entry point."""
    
    # Page configuration
    st.set_page_config(
        page_title="SpeedLocal: TIMES Data Explorer",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session manager
    session_mgr = SessionManager()
    
    # Initialize module registry
    if not session_mgr.has('module_registry'):
        session_mgr.set('module_registry', ModuleRegistry())
    
    module_registry = session_mgr.get('module_registry')
    
    # Title
    st.title("SpeedLocal: TIMES Data Explorer")
    
    # Render sidebar and get configuration
    sidebar_config = render_sidebar()
    
    if not sidebar_config.get('valid', False):
        st.warning("Please configure database connection in the sidebar.")
        st.stop()
    
    # Handle data reload
    if sidebar_config.get('reload_requested', False):
        session_mgr.clear_pattern('data')
        session_mgr.clear_pattern('filter')
        session_mgr.clear_pattern('loader')
        session_mgr.clear_pattern('desc')
        st.rerun()
    
    # Initialize data loader if not in session
    if not session_mgr.has('data_loader'):
        data_loader = DataLoaderManager(
            db_source=sidebar_config['db_source'],
            mapping_csv=sidebar_config['mapping_csv'],
            is_url=sidebar_config['is_url']
        )
        
        # Load data with progress feedback
        with st.spinner("Loading data from database..."):
            table_dfs = data_loader.load_all_tables()
        
        if not table_dfs:
            st.error("Failed to load data. Please check your database connection.")
            st.stop()
        
        # Load description tables
        with st.spinner("Loading description tables..."):
            from core.data_loader import create_description_mapping
            desc_df = data_loader.load_description_tables()
            desc_mapping = create_description_mapping(desc_df)
        
        # Store in session
        session_mgr.set('data_loader', data_loader)
        session_mgr.set('table_dfs', table_dfs)
        session_mgr.set('desc_df', desc_df)
        session_mgr.set('desc_mapping', desc_mapping)
    
    # Get data from session
    table_dfs = session_mgr.get('table_dfs', {})
    data_loader = session_mgr.get('data_loader')
    
    if not table_dfs:
        st.error("No data available. Please reload the application.")
        st.stop()
    
    # Initialize filter manager if not in session
    if not session_mgr.has('filter_manager'):
        filter_manager = FilterManager(table_dfs)
        session_mgr.set('filter_manager', filter_manager)
    
    filter_manager = session_mgr.get('filter_manager')
    
    # Render global filters in sidebar
    with st.sidebar:
        st.markdown("---")
        st.subheader("Global Filters")
        global_filters = filter_manager.render_global_filters()
    
    # Get enabled modules
    enabled_modules = module_registry.get_enabled_modules()
    
    if not enabled_modules:
        st.error("No modules are enabled. Please check your configuration.")
        st.stop()
    
    # Create tabs for each enabled module
    module_names = [module.name for module in enabled_modules.values()]
    tabs = st.tabs(module_names)
    
    # Render each module in its tab
    # Get description data from session
    desc_df = session_mgr.get('desc_df', pd.DataFrame())
    desc_mapping = session_mgr.get('desc_mapping', {})

    # Render each module in its tab
    for tab, (module_key, module) in zip(tabs, enabled_modules.items()):
        with tab:
            try:
                # Get module-specific filter config
                filter_config = module.get_filter_config()
                
                # Check if module wants global filters applied
                apply_global = filter_config.get('apply_global_filters', True)
                
                # Render module-specific filters (if any)
                module_filters = {}
                if filter_config.get('show_module_filters', False):
                    with st.expander("📊 Additional Filters", expanded=False):
                        module_filters = filter_manager.render_module_filters(
                            module_key,
                            filter_config
                        )
                
                # Decide which filters to pass
                if apply_global:
                    combined_filters = {**global_filters, **module_filters}
                else:
                    combined_filters = module_filters
                
                # Render the module (now with description data)
                module.render(table_dfs, combined_filters, data_loader)
                
            except Exception as e:
                st.error(f"Error rendering {module.name}: {str(e)}")
                
                # Debug mode: show full error
                if st.checkbox(f"Show error details for {module.name}", key=f"error_{module_key}"):
                    st.exception(e)


if __name__ == "__main__":
    main()
