"""
Main entry point for the modular TIMES Data Explorer application.
"""

import streamlit as st
from pathlib import Path
import pandas as pd

from core.session_manager import SessionManager
from core.data_loader import DataLoaderManager, create_all_description_mappings
from core.filter_manager import FilterManager
from core.unit_manager import UnitManager  
from config.module_registry import ModuleRegistry
from components.sidebar import render_sidebar
from utils.unit_converter import UnitConverter, ExclusionInfo


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
        session_mgr.clear_pattern('unit')  
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
            desc_df = data_loader.load_description_tables()
            all_mappings = create_all_description_mappings(desc_df)
            desc_mapping = all_mappings['nested']
        
            table_dfs = data_loader.apply_label_descriptions(desc_df)

        # Load unit conversions
        with st.spinner("Loading unit conversions..."):
            unit_conversions_df = data_loader.load_unit_conversions()
            
            # Create unit converter if conversions loaded successfully
            if not unit_conversions_df.empty:
                converter = UnitConverter(unit_conversions_df)
                session_mgr.set('unit_converter', converter)
            else:
                session_mgr.set('unit_converter', None)
        
        # Load timeslice metadata
        with st.spinner("Loading timeslice metadata..."):
            ts_metadata = data_loader.load_timeslice_metadata()
            session_mgr.set('ts_metadata', ts_metadata)

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
    
    # Initialize unit manager if not in session
    if not session_mgr.has('unit_manager'):
        unit_manager = UnitManager(table_dfs)
        session_mgr.set('unit_manager', unit_manager)
    
    unit_manager = session_mgr.get('unit_manager')
    
    # Get enabled modules
    enabled_modules = module_registry.get_enabled_modules()
    
    if not enabled_modules:
        st.error("No modules are enabled. Please check your configuration.")
        st.stop()
    
    # Create tabs for each enabled module
    module_names = [module.name for module in enabled_modules.values()]
    module_keys = list(enabled_modules.keys())

    # Initialize active module tracking BEFORE rendering anything
    if 'active_module_key' not in st.session_state:
        st.session_state.active_module_key = module_keys[0]

    # Render global filters in sidebar
    with st.sidebar:
        st.markdown("---")
        st.subheader("Global Filters")

        global_filters = filter_manager.render_global_filters()
        
        # Get active module's config
        active_module = module_registry.get_module(st.session_state.active_module_key)
        config = active_module.get_config()  

    # Initialize selected tab in session state
    if 'selected_tab_index' not in st.session_state:
        st.session_state.selected_tab_index = 0
    
    # Create tabs with unique keys
    tab_container = st.container()
    
    with tab_container:
        # Use radio buttons styled as tabs
        selected_tab_name = st.radio(
            "Select Module",
            options=module_names,
            index=st.session_state.selected_tab_index,
            horizontal=True,
            key="module_selector",
            label_visibility="collapsed"
        )
        
        # Update selected index
        st.session_state.selected_tab_index = module_names.index(selected_tab_name)
        
        # Get the selected module
        selected_module_key = module_keys[st.session_state.selected_tab_index]
        selected_module = enabled_modules[selected_module_key]
        
        st.session_state.active_module_key = selected_module_key
        
        st.divider()
        
        # Render only the selected module
        try:
            # Get module-specific config
            config = selected_module.get_config()  
            
            # Check if module wants global filters applied
            apply_global = config.get('apply_global_filters', True)
            
            # Render module-specific filters (if any)
            module_filters = {}
            if config.get('show_module_filters', False):
                with st.expander("📊 Additional Filters", expanded=False):
                    module_filters = filter_manager.render_module_filters(
                        selected_module_key,
                        config
                    )
            
            # Combine filters
            if apply_global:
                combined_filters = {**global_filters, **module_filters}
            else:
                combined_filters = module_filters
            
            # Module renders with the combined filters
            selected_module.render(table_dfs, combined_filters)
            
        except Exception as e:
            st.error(f"Error rendering {selected_module.name}: {str(e)}")
            
            # Debug mode: show full error
            if st.checkbox(f"Show error details for {selected_module.name}", key=f"error_{selected_module_key}"):
                st.exception(e)


if __name__ == "__main__":
    main()