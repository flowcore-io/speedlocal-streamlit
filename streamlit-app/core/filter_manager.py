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
            module_key: Active module identifier (for unique keys)
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
        
        # Set defaults
        if default_categories is None:
            default_categories = ['energy', 'mass']
        
        # Filter defaults to only include available categories
        default_categories = [cat for cat in default_categories if cat in active_categories]
        
        # Session key for category selection
        session_key_cat = f"unit_categories_{module_key}"
        
        # Initialize with defaults if first time
        if session_key_cat not in st.session_state:
            st.session_state[session_key_cat] = default_categories
        
        # Category Filter (multiselect)
        st.sidebar.markdown("#### Unit Configuration")
        
        selected_categories = st.sidebar.multiselect(
            "Unit Categories",
            options=active_categories,
            key=session_key_cat,
            help="Select unit categories to include in analysis"
        )
        
        if not selected_categories:
            st.sidebar.info("Select at least one category to enable unit conversion")
            return None
        
        # Target Unit Selectors (one per selected category)
        target_units = {}
        
        for category in selected_categories:
            # Get units for this category
            units = converter.get_units_by_category(category)
            
            if not units:
                continue
            
            # Session key for this category's target
            target_key = f"unit_target_{module_key}_{category}"
            
            # Initialize default (first unit) if not set
            if target_key not in st.session_state:
                st.session_state[target_key] = units[0]
            
            # Create format function for display
            def format_unit(unit):
                return converter.get_unit_display_name(unit)
            
            selected_unit = st.sidebar.selectbox(
                f"Target Unit ({category})",
                options=units,
                format_func=format_unit,
                key=target_key,
                help=f"Convert all {category} units to this unit"
            )
            
            target_units[category] = selected_unit
        
        return {
            'selected_categories': selected_categories,
            'target_units': target_units
        }