"""
Filter management system using existing GenericFilter.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import from existing utils
import sys
sys.path.append(str(Path(__file__).parent.parent / "utils"))
from _query_dynamic import GenericFilter


class FilterManager:
    """
    Centralized filter management.
    Wraps the existing GenericFilter functionality.
    """
    
    def __init__(self, table_dfs: Dict[str, pd.DataFrame]):
        """
        Initialize FilterManager.
        
        Args:
            table_dfs: Dictionary of table_name -> DataFrame
        """
        self.table_dfs = table_dfs
        self.combined_df = self._create_combined_df()
        self.generic_filter = self._create_generic_filter()
    
    def _create_combined_df(self) -> pd.DataFrame:
        """Combine all DataFrames for filtering."""
        all_dfs = []
        for df in self.table_dfs.values():
            if df is not None and not df.empty:
                all_dfs.append(df)
        
        if all_dfs:
            return pd.concat(all_dfs, ignore_index=True)
        else:
            return pd.DataFrame()
    
    def _create_generic_filter(self) -> GenericFilter:
        """Create GenericFilter instance."""
        filterable_columns = [
            'scen', 'sector', 'subsector', 'service',
            'techgroup', 'comgroup', 'topic', 'attr', 'year'
        ]
        
        return GenericFilter(
            df=self.combined_df,
            filterable_columns=filterable_columns
        )
    
    def render_global_filters(self) -> Dict[str, List[Any]]:
        """
        Render global filters that apply to all modules.
        
        Returns:
            Dictionary of active filters
        """
        filters = {}
        
        if self.combined_df.empty:
            st.sidebar.warning("No data available for filtering.")
            return filters
        
        # Scenario filter (always shown)
        if 'scen' in self.combined_df.columns:
            scenarios = sorted(self.combined_df['scen'].unique())
            selected_scenarios = st.sidebar.multiselect(
                "Scenarios",
                options=scenarios,
                default=scenarios,
                key="global_filter_scen",
                help="Select scenarios to include in analysis"
            )
            filters['scen'] = selected_scenarios
            self.generic_filter.set_filter('scen', selected_scenarios)
        
        return filters
    
    def render_module_filters(
        self, 
        module_key: str, 
        config: Dict[str, Any]
    ) -> Dict[str, List[Any]]:
        """
        Render module-specific filters.
        
        Args:
            module_key: Unique module identifier
            config: Module filter configuration
            
        Returns:
            Dictionary of module-specific filters
        """
        filters = {}
        
        filterable_cols = config.get('filterable_columns', [])
        default_cols = config.get('default_columns', [])
        
        # Skip columns already in global filters
        global_filter_cols = ['scen']
        available_cols = [c for c in filterable_cols if c not in global_filter_cols]
        
        if not available_cols:
            return filters
        
        # Column selection
        selected_columns = st.multiselect(
            "Additional Filter Columns:",
            options=available_cols,
            default=[c for c in default_cols if c in available_cols],
            key=f"{module_key}_filter_columns"
        )
        
        # Create filters for selected columns
        for column in selected_columns:
            unique_values = self.generic_filter.get_unique_values(column)
            
            if not unique_values:
                continue
            
            selected_values = st.multiselect(
                f"Filter by {column}:",
                options=unique_values,
                default=unique_values,
                key=f"{module_key}_filter_{column}"
            )
            
            filters[column] = selected_values
            self.generic_filter.set_filter(column, selected_values)
        
        return filters
    
    def get_generic_filter(self) -> GenericFilter:
        """Get the underlying GenericFilter instance."""
        return self.generic_filter
    
    def apply_filters_to_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply current filters to a DataFrame.
        
        Args:
            df: DataFrame to filter
            
        Returns:
            Filtered DataFrame
        """
        return self.generic_filter.apply_filters(df)

    def get_active_unit_categories(
        self, 
        module_key: str, 
        table_dfs: Dict[str, pd.DataFrame]
    ) -> List[str]:
        """
        Get list of unit categories present in the active module's data.
        
        Args:
            module_key: Active module identifier
            table_dfs: All available tables
            
        Returns:
            List of category names found in the data
        """
        # Get unit converter from session
        converter = st.session_state.get('unit_converter')
        if not converter:
            return []
        
        # Get module's required tables from registry
        registry = st.session_state.get('module_registry')
        if not registry:
            return []
        
        try:
            module = registry.get_module(module_key)
            required_tables = module.get_required_tables()
        except KeyError:
            return []
        
        # If no required tables, use all tables
        if not required_tables:
            tables_to_check = list(table_dfs.keys())
        else:
            tables_to_check = required_tables
        
        # Extract unique categories from relevant tables
        categories = set()
        
        for table_name in tables_to_check:
            if table_name in table_dfs:
                df = table_dfs[table_name]
                if 'unit' in df.columns:
                    units = df['unit'].dropna().unique()
                    for unit in units:
                        category = converter.get_category(unit)
                        if category:
                            categories.add(category)
        
        return sorted(list(categories))

    def render_unit_configuration(
            self,
            active_categories: List[str],
            module_key: str,
            default_categories: List[str] = None
        ) -> Optional[Dict[str, Any]]:
            """
            Render unit configuration controls in sidebar.
            
            Args:
                active_categories: List of categories available in current module
                module_key: Use 'global' for shared settings across modules
                default_categories: Default categories to select
                
            Returns:
                Dict with 'selected_categories' and 'target_units' or None
            """
            if not active_categories:
                return None
            
            # Get unit converter
            converter = st.session_state.get('unit_converter')
            if not converter:
                return None
            
            # Get default target units from config
            default_target_units = converter.get_default_target_units()
            
            # Set defaults for categories
            if default_categories is None:
                default_categories = converter.default_selected_categories or ['energy', 'mass']
            
            # Filter defaults to only include available categories
            default_categories = [cat for cat in default_categories if cat in active_categories]
            
            # Use simple keys without module prefix for global settings
            cat_session_key = "global_unit_categories"
            
            # Initialize session state once
            if cat_session_key not in st.session_state:
                st.session_state[cat_session_key] = default_categories
                # Initialize target units too
                for cat in default_categories:
                    target_key = f"global_unit_target_{cat}"
                    if target_key not in st.session_state:
                        default_unit = default_target_units.get(cat)
                        if default_unit:
                            st.session_state[target_key] = default_unit
            
            # Category Filter (multiselect)
            st.sidebar.markdown("#### Unit Conversion")
            st.sidebar.caption("🌍 Global settings - apply to all modules")
            
            # Show info about defaults
            with st.sidebar.expander("ℹ️ Default Units", expanded=False):
                st.markdown("**Configured default target units:**")
                for cat, unit in default_target_units.items():
                    if cat in active_categories:
                        display_name = converter.get_unit_display_name(unit)
                        st.text(f"  • {cat}: {unit} ({display_name})")
            
            # Get current value from session state
            current_categories = st.session_state.get(cat_session_key, default_categories)
            
            # Ensure current categories are valid
            current_categories = [cat for cat in current_categories if cat in active_categories]
            if not current_categories:
                current_categories = default_categories
            
            selected_categories = st.sidebar.multiselect(
                "Active Categories",
                options=active_categories,
                default=current_categories,
                help="Select unit categories to include in analysis. Rows with other categories will be excluded."
            )
            
            # Update session state
            st.session_state[cat_session_key] = selected_categories
            
            if not selected_categories:
                st.sidebar.warning("⚠️ Select at least one category to view data")
                return None
            
            # Target Unit Selectors (one per selected category)
            target_units = {}
            
            st.sidebar.markdown("**Target Units:**")
            
            for category in selected_categories:
                # Get units for this category
                units = converter.get_units_by_category(category)
                
                if not units:
                    continue
                
                # Session key for this category's target
                target_key = f"global_unit_target_{category}"
                
                # Get or initialize default
                if target_key not in st.session_state:
                    default_unit = default_target_units.get(category, units[0])
                    st.session_state[target_key] = default_unit if default_unit in units else units[0]
                
                # Get current value
                current_unit = st.session_state[target_key]
                
                # Make sure it's still valid
                if current_unit not in units:
                    current_unit = units[0]
                    st.session_state[target_key] = current_unit
                
                # Find index
                try:
                    current_index = units.index(current_unit)
                except ValueError:
                    current_index = 0
                
                # Create format function for display
                def format_unit(unit, cat=category):
                    display_name = converter.get_unit_display_name(unit)
                    if unit == default_target_units.get(cat):
                        return f"{unit} - {display_name} ⭐"
                    return f"{unit} - {display_name}"
                
                # Render selectbox
                selected_unit = st.sidebar.selectbox(
                    f"{category.capitalize()}",
                    options=units,
                    index=current_index,
                    format_func=format_unit,
                    help=f"Convert all {category} units to this target unit"
                )
                
                # Update session state
                st.session_state[target_key] = selected_unit
                target_units[category] = selected_unit
            
            # Reset button
            if st.sidebar.button("🔄 Reset to Defaults", use_container_width=True):
                # Reset categories
                st.session_state[cat_session_key] = default_categories
                # Reset target units
                for cat in active_categories:
                    target_key = f"global_unit_target_{cat}"
                    default_unit = default_target_units.get(cat)
                    if default_unit:
                        st.session_state[target_key] = default_unit
                st.rerun()
            
            return {
                'selected_categories': selected_categories,
                'target_units': target_units
            }
        
        