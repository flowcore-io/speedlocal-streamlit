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
