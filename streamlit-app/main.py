"""
Main entry point for the modular TIMES Data Explorer application.
Refactored from times_app_test.py to support modular architecture.
"""

import streamlit as st
from pathlib import Path
import pandas as pd

from core.session_manager import SessionManager
from core.data_loader import DataLoaderManager,create_description_mapping
from core.filter_manager import FilterManager
from config.module_registry import ModuleRegistry
from components.sidebar import render_sidebar
from utils._unit_converter import UnitConverter



def main():
    """Main Streamlit application entry point."""
    
    # Debug: Check if main is called multiple times
    if 'main_call_count' not in st.session_state:
        st.session_state.main_call_count = 0
    st.session_state.main_call_count += 1
    print(f"DEBUG: main() called {st.session_state.main_call_count} times")

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
            desc_df = data_loader.load_description_tables()
            desc_mapping = create_description_mapping(desc_df)
        
        # Load unit conversions
        with st.spinner("Loading unit conversions..."):
            unit_conversions_df = data_loader.load_unit_conversions()
            
            # Create unit converter if conversions loaded successfully
            if not unit_conversions_df.empty:
                converter = UnitConverter(unit_conversions_df)
                session_mgr.set('unit_converter', converter)
            else:
                session_mgr.set('unit_converter', None)

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
        
        # Unit configuration (dynamic based on active module)
        active_module = module_registry.get_module(st.session_state.active_module_key)
        filter_config = active_module.get_filter_config()
        
        print(f"DEBUG: Active module = {st.session_state.active_module_key}")
        print(f"DEBUG: apply_unit_conversion = {filter_config.get('apply_unit_conversion', False)}")


        if filter_config.get('apply_unit_conversion', False):
            # Get active categories from current module's data
            active_categories = filter_manager.get_active_unit_categories(
                st.session_state.active_module_key,
                table_dfs
            )
            
            print(f"DEBUG: active_categories = {active_categories}")

            # Get module's default categories (if specified)
            default_categories = filter_config.get('default_unit_categories', ['energy', 'mass'])
            
            print(f"DEBUG: default_categories = {default_categories}")

            # Render unit configuration
            unit_config = filter_manager.render_unit_configuration(
                active_categories,
                st.session_state.active_module_key,
                default_categories
            )
            print(f"DEBUG: unit_config = {unit_config}")

            if unit_config:
                global_filters['unit_config'] = unit_config

    # Create tabs
    tabs = st.tabs(module_names)

    print(f"DEBUG: About to iterate tabs")
    for tab, (module_key, module) in zip(tabs, enabled_modules.items()):
        print(f"DEBUG: Checking tab for module_key = {module_key}")
        with tab:
            print(f"DEBUG: Inside 'with tab' for module_key = {module_key}")
            st.session_state.active_module_key = module_key
            
    # Render each module in its tab
    for tab, (module_key, module) in zip(tabs, enabled_modules.items()):
        with tab:
            # This tab's content only executes when it's active

            st.session_state.active_module_key = module_key

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
                
                # Apply unit conversion if module opts in
                if filter_config.get('apply_unit_conversion', False) and 'unit_config' in combined_filters:
                    unit_config = combined_filters['unit_config']
                    converter = session_mgr.get('unit_converter')
                    
                    if converter:
                        converted_dfs = {}
                        all_unknown_units = []
                        
                        for table_name, df in table_dfs.items():
                            if table_name in module.get_required_tables():
                                # Filter by categories
                                df_filtered, unknown_units = converter.filter_by_categories(
                                    df, 
                                    unit_config['selected_categories']
                                )
                                all_unknown_units.extend(unknown_units)
                                
                                # Convert units
                                df_converted = converter.convert_dataframe(
                                    df_filtered,
                                    unit_config['target_units']
                                )
                                converted_dfs[table_name] = df_converted
                            else:
                                converted_dfs[table_name] = df
                        
                        # Show warning if unknown units found
                        if all_unknown_units:
                            unique_unknown = list(set(all_unknown_units))
                            st.warning(
                                f"⚠️ Unknown units filtered out: {', '.join(unique_unknown)}. "
                                f"These units are not in unit_conversions.csv and have been excluded."
                            )
                        
                        # Pass converted data to module
                        module.render(converted_dfs, combined_filters)
                    else:
                        st.error("Unit converter not available. Please check unit_conversions.csv")
                        module.render(table_dfs, combined_filters)
                else:
                    # No unit conversion - pass original data
                    module.render(table_dfs, combined_filters)
            except Exception as e:
                st.error(f"Error rendering {module.name}: {str(e)}")
                
                # Debug mode: show full error
                if st.checkbox(f"Show error details for {module.name}", key=f"error_{module_key}"):
                    st.exception(e)


if __name__ == "__main__":
    main()
