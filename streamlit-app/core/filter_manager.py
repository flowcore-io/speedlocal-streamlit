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

    def render_module_unit_controls(
        self,
        module_key: str,
        available_categories: List[str]
    ) -> Dict[str, Any]:
        """
        Render unit conversion controls for a specific module.
        
        Args:
            module_key: Unique module identifier (e.g., "energy_emissions_v2")
            available_categories: List of categories relevant to this module
            
        Returns:
            Dict with 'selected_categories' and 'target_units'
        """
        converter = st.session_state.get('unit_converter')
        if not converter:
            st.warning("Unit converter not available")
            return {'target_units': {}, 'selected_categories': []}
        
        # Get defaults from config
        default_target_units = converter.get_default_target_units()
        
        # Session keys unique to this module
        cat_key = f"{module_key}_unit_categories"
        
        # 🆕 IMPORTANT: Initialize ALL session state keys BEFORE rendering widgets
        if cat_key not in st.session_state:
            st.session_state[cat_key] = available_categories
        
        # Initialize all target unit keys upfront
        for cat in available_categories:
            target_key = f"{module_key}_unit_target_{cat}"
            if target_key not in st.session_state:
                default_unit = default_target_units.get(cat)
                if default_unit:
                    st.session_state[target_key] = default_unit
        
        # Create compact layout with columns
        col1, col2, col3 = st.columns([3, 3, 1])
        
        with col1:
            st.markdown("**📊 Current Defaults:**")
            defaults_display = " | ".join([
                f"{cat}: **{default_target_units.get(cat, 'N/A')}**" 
                for cat in available_categories
            ])
            st.markdown(defaults_display)
        
        with col2:
            # Category selection
            selected_categories = st.multiselect(
                "Active Categories",
                options=available_categories,
                default=st.session_state[cat_key],
                key=f"{cat_key}_widget",
                help="Categories to include in analysis"
            )
            # Update session state after widget renders
            st.session_state[cat_key] = selected_categories
        
        with col3:
            # Reset button
            if st.button("🔄 Reset", key=f"{module_key}_reset", help="Reset to defaults"):
                st.session_state[cat_key] = available_categories
                for cat in available_categories:
                    target_key = f"{module_key}_unit_target_{cat}"
                    default_unit = default_target_units.get(cat)
                    if default_unit:
                        st.session_state[target_key] = default_unit
                st.rerun()
        
        if not selected_categories:
            st.warning("⚠️ Select at least one category to view data")
            return {'target_units': {}, 'selected_categories': []}
        
        # Target unit selectors in a row
        st.markdown("**🎯 Target Units:**")
        cols = st.columns(len(selected_categories))
        
        target_units = {}
        for idx, category in enumerate(selected_categories):
            with cols[idx]:
                units = converter.get_units_by_category(category)
                if not units:
                    continue
                
                target_key = f"{module_key}_unit_target_{category}"
                
                # Get current value from session state (already initialized above)
                current_unit = st.session_state.get(target_key)
                
                # Validate it's still in the list
                if current_unit not in units:
                    current_unit = units[0]
                    st.session_state[target_key] = current_unit
                
                current_index = units.index(current_unit)
                
                # Format function
                def format_unit(unit, cat=category):
                    display_name = converter.get_unit_display_name(unit)
                    if unit == default_target_units.get(cat):
                        return f"{unit} ({display_name}) ⭐"
                    return f"{unit} ({display_name})"
                
                selected_unit = st.selectbox(
                    f"{category.capitalize()}",
                    options=units,
                    index=current_index,
                    format_func=format_unit,
                    key=f"{target_key}_widget",
                    help=f"Convert all {category} units to this unit"
                )
                
                # Update session state after widget renders
                st.session_state[target_key] = selected_unit
                target_units[category] = selected_unit
        
        return {
            'selected_categories': selected_categories,
            'target_units': target_units
        }
        
        