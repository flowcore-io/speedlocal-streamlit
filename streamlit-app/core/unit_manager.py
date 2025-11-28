"""
Unit conversion controls management.
Handles detection and rendering of unit conversion UI controls.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple

from utils.unit_converter import ExclusionInfo

class UnitManager:
    """
    Centralized unit conversion controls management.
    Handles category detection and UI rendering for unit conversion.
    """
    
    def __init__(self, table_dfs: Dict[str, pd.DataFrame]):
        """
        Initialize UnitManager.
        
        Args:
            table_dfs: Dictionary of table_name -> DataFrame
        """
        self.table_dfs = table_dfs
    
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
                
                # Check both 'unit' and 'cur' columns
                for col in ['unit', 'cur']:
                    if col in df.columns:
                        units = df[col].dropna().unique()
                        for unit in units:
                            # Filter out 'NA' string and empty values
                            if unit and str(unit).upper() != 'NA':
                                category = converter.get_category(unit)
                                if category:
                                    categories.add(category)
        
        return sorted(list(categories))
    
    def render_unit_controls_if_enabled(
        self,
        module,
        table_dfs: Dict[str, pd.DataFrame],
        expanded: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Render unit conversion controls for a module (if enabled).
        
        This is the main entry point for modules. It:
        1. Checks if module has unit conversion enabled
        2. Detects available categories from data
        3. Renders expander with controls
        4. Returns unit configuration
        
        Args:
            module: Module instance (BaseModule subclass)
            table_dfs: All available data tables
            expanded: Whether expander should be open by default
            
        Returns:
            Dict with 'selected_categories' and 'target_units' or None
        """
        # Check if module wants unit conversion
        config = module.get_config()
        st.write("DEBUG: config =", config) 

        if not config.get('apply_unit_conversion', False):
            return None
        
        # Get module key
        module_key = module.name.replace(" ", "_").lower()
        # st.write("DEBUG (UnitManager): module_key =", module_key)
        
        # Detect available categories from data
        available_categories = self.get_active_unit_categories(module_key, table_dfs)
        # st.write("DEBUG (UnitManager): available_categories =", available_categories)

        if not available_categories:
            st.warning("No unit categories detected in data")
            return None
        
        # Get converter to show defaults info
        converter = st.session_state.get('unit_converter')
        if not converter:
            st.warning("Unit converter not available for unit conversion")
            return None
        
        default_target_units = converter.get_default_target_units()
        
        # Render in expander
        with st.expander("⚙️ Unit Conversion Settings", expanded=expanded):
            # Show available categories info
            st.caption(f"📊 Detected categories in data: {', '.join(available_categories)}")
            
            # Show defaults
            if default_target_units:
                defaults_text = " | ".join([
                    f"{cat}: **{default_target_units.get(cat, 'N/A')}**" 
                    for cat in available_categories
                ])
                st.markdown(f"**Default units:** {defaults_text}")
            
            st.divider()
            
            # Render controls
            unit_config = self.render_module_unit_controls(
                module_key=module_key,
                available_categories=available_categories
            )
            
            return unit_config
    
    def render_module_unit_controls(
        self,
        module_key: str,
        available_categories: List[str]
    ) -> Dict[str, Any]:
        """
        Render unit conversion controls for a specific module.
        
        Args:
            module_key: Unique module identifier (e.g., "energy_&_emissions_v2")
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
        
        # Initialize with ALL available categories by default
        if cat_key not in st.session_state:
            st.session_state[cat_key] = available_categories
        
        # Initialize all target unit keys upfront with defaults
        for cat in available_categories:
            target_key = f"{module_key}_unit_target_{cat}"
            if target_key not in st.session_state:
                default_unit = default_target_units.get(cat)
                if default_unit:
                    st.session_state[target_key] = default_unit
        
        # Create compact layout with columns
        col1, col2 = st.columns([3, 1])
        
        with col1:
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
        
        with col2:
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

    def apply_unit_conversion(
        self,
        df: pd.DataFrame,
        unit_config: Dict[str, Any],
        section_title: str = "Data"
    ) -> Tuple[pd.DataFrame, ExclusionInfo]:
        """
        Apply unit conversion to a DataFrame.
        
        Args:
            df: DataFrame to convert
            unit_config: Dict with 'target_units' and 'selected_categories'
            section_title: Title for warning messages (e.g., "Energy Input")
            
        Returns:
            Tuple of (converted_df, exclusion_info)
        """
        if df.empty:
            return df, ExclusionInfo(0, 0, set(), set(), set(), set())
        
        # Get converter from session
        converter = st.session_state.get('unit_converter')
        if not converter:
            st.warning(f"⚠️ Unit converter not available. Using raw data for {section_title}.")
            return df, ExclusionInfo(0, 0, set(), set(), set(), set())
        
        # Apply conversion
        df_converted, exclusion_info = converter.convert_and_filter(
            df,
            target_units=unit_config.get('target_units'),
            selected_categories=unit_config.get('selected_categories'),
            unit_col='unit',
            currency_col='cur',
            value_col='value'
        )
        
        # Show warning if rows were excluded
        if exclusion_info.has_exclusions():
            with st.expander(
                f"⚠️ {section_title}: {exclusion_info.excluded_rows} of "
                f"{exclusion_info.total_rows} rows excluded during unit conversion",
                expanded=False
            ):
                st.text(exclusion_info.get_summary())
                
                # Show which units are being used
                if unit_config.get('target_units'):
                    st.markdown("**Target units:**")
                    for category, unit in unit_config['target_units'].items():
                        if category in unit_config.get('selected_categories', []):
                            st.text(f"  • {category}: {unit}")
        
        return df_converted, exclusion_info


    def show_conversion_summary(self) -> None:
        """Show overall conversion summary with default units."""
        converter = st.session_state.get('unit_converter')
        if not converter:
            return
        
        default_units = converter.get_default_target_units()
        if default_units:
            with st.expander("ℹ️ Default Units", expanded=False):
                # st.markdown("**Default target units:**")
                for category, unit in default_units.items():
                    st.text(f"  • {category}: {unit}")
                st.info(
                    "These are the default units from your configuration. "
                    "You can override them using the controls above."
                )


    def get_unit_config_from_filters(
        self,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract unit configuration from filters or use defaults.
        
        Args:
            filters: Current filter settings
            
        Returns:
            Dict with 'target_units' and 'selected_categories'
        """
        # Check if there's a unit config in filters
        if 'unit_config' in filters and filters['unit_config']:
            return filters['unit_config']
        
        # Fallback to defaults
        converter = st.session_state.get('unit_converter')
        if not converter:
            return {'target_units': {}, 'selected_categories': []}
        
        return {
            'target_units': converter.get_default_target_units(),
            'selected_categories': converter.get_all_categories()
        }