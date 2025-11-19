"""
Energy and Emissions visualization module - Version 2 with Unit Conversion.
This version applies unit conversion at data loading time.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now import from base modules and components
from modules.base_module import BaseModule
from components.layouts import agg_disagg_layout
from utils import UnitConverter, ExclusionInfo


class EnergyEmissionsModuleV2(BaseModule):
    """
    Energy and Emissions visualization module with unit conversion.
    
    Key enhancements in V2:
    - Applies unit conversion at data loading time
    - Filters out rows with unknown/unconvertible units
    - Shows warnings about excluded data
    - Uses default units from config/default_units.yaml
    """
    
    # Sectors to exclude
    EXCLUDED_SECTORS = ['DMZ', 'DHT', 'ELT', 'TRD', 'UPS', 'NA', 'FTS', 'SYS']
    
    # Configuration for each section
    SECTION_CONFIGS = {
        'energy': {
            'df_key': 'energy',
            'additional_filter': {'attr': 'f_in'},
            'plot_method': 'stacked_bar',
            'group_col_aggregate': 'comgroup_desc',
            'group_col_disaggregate': 'comgroup_desc',
            'title': 'Energy Input',
            'value_col': 'value',  # Column to convert
            'unit_col': 'unit',  # Unit column
            'currency_col': 'cur'  # Currency column (if exists)
        },
        'emissions': {
            'df_key': 'emissions',
            'additional_filter': {},
            'plot_method': 'line_plot',
            'group_col_aggregate': 'sector_desc',
            'group_col_disaggregate': 'com_desc',
            'title': 'Emissions',
            'value_col': 'value',
            'unit_col': 'unit',
            'currency_col': 'cur'
        }
    }
    
    def __init__(self):
        super().__init__(
            name="Energy & Emissions V2",  # Different name to distinguish from V1
            description="Annual reporting with unit conversion support",
            order=1,
            enabled=True
        )
        self._exclusion_info = {}  # Track exclusions per section
    
    def get_required_tables(self) -> list:
        return ["energy", "emissions"]
    
    def get_filter_config(self) -> Dict[str, Any]:
        return {
            "apply_global_filters": True,
            "show_module_filters": False,
            #"apply_unit_conversion": True,  # Legacy (should be removed unit conversion is now a core feature.)
            "default_unit_categories": ['energy', 'mass'],  # Categories to show in sidebar
            "filterable_columns": ['sector', 'subsector', 'comgroup', 'year'],
            "default_columns": []
        }
    
    def render(
        self,
        table_dfs: Dict[str, pd.DataFrame],
        filters: Dict[str, Any]
    ) -> None:
        """Main render method with unit conversion."""  # ← Better description
        
        if not self.validate_data(table_dfs):
            self.show_error("Required data tables (energy/emissions) not available.")
            return
        
           # 🆕 ADD MODULE-LEVEL UNIT CONTROLS
        st.subheader("⚙️ Unit Conversion Settings")
    
        # Render unit controls and get config
        unit_config = self._render_unit_controls()
    
        # Add to filters
        filters['unit_config'] = unit_config
    
        st.divider()
        
        # Show overall unit conversion summary at the top
        self._show_conversion_summary()
        
        # Create sub-tabs for Energy and Emissions
        energy_tab, emissions_tab = st.tabs(["⚡ Energy", "🌍 Emissions"])
        
        with energy_tab:
            self._render_section('energy', table_dfs, filters)
        
        with emissions_tab:
            self._render_section('emissions', table_dfs, filters)
    
    def _get_unit_converter(self) -> Optional[UnitConverter]:
        """Get UnitConverter from session state."""
        return st.session_state.get('unit_converter')
    
    def _get_unit_config(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get unit configuration from filters or use defaults.
        
        Args:
            filters: Current filter settings
            
        Returns:
            Dict with 'target_units' and 'selected_categories'
        """
        # 🔍 DEBUG
        st.write("**DEBUG _get_unit_config:**")
        st.write(f"  - 'unit_config' in filters: {'unit_config' in filters}")
        if 'unit_config' in filters:
            st.write(f"  - filters['unit_config']: {filters['unit_config']}")
        
        # First, check if there's a global unit config in filters
        if 'unit_config' in filters and filters['unit_config']:
            return filters['unit_config']
        
        # Fallback to defaults
        converter = self._get_unit_converter()
        if not converter:
            return {'target_units': {}, 'selected_categories': []}
        
        return {
            'target_units': converter.get_default_target_units(),
            'selected_categories': converter.get_all_categories()
        }
    
    def _apply_unit_conversion(
        self,
        df: pd.DataFrame,
        filters: Dict[str, Any],
        section_key: str,
        config: Dict[str, Any]
    ) -> pd.DataFrame:
        """Apply unit conversion to a DataFrame."""
        
        if df.empty:
            return df
        
        # Get converter
        converter = self._get_unit_converter()
        if not converter:
            st.warning(f"⚠️ Unit converter not available. Using raw data for {config['title']}.")
            return df
        
        # Get unit configuration
        unit_config = self._get_unit_config(filters)
        
        # 🔍 DEBUG OUTPUT
        st.write(f"### 🔍 DEBUG: {config['title']}")
        st.write(f"**1. Target units from config:**", unit_config.get('target_units'))
        st.write(f"**2. Units in your data (first 10):**", df[config.get('unit_col', 'unit')].dropna().unique()[:10].tolist())
        st.write(f"**3. Sample values BEFORE conversion:**", df[config.get('value_col', 'value')].head(3).tolist())
        
        # Apply conversion and filtering
        df_converted, exclusion_info = converter.convert_and_filter(
            df,
            target_units=unit_config.get('target_units'),
            selected_categories=unit_config.get('selected_categories'),
            unit_col=config.get('unit_col', 'unit'),
            currency_col=config.get('currency_col', 'cur'),
            value_col=config.get('value_col', 'value')
        )
        
        # 🔍 DEBUG OUTPUT
        st.write(f"**4. Units AFTER conversion:**", df_converted[config.get('unit_col', 'unit')].dropna().unique()[:10].tolist())
        st.write(f"**5. Sample values AFTER conversion:**", df_converted[config.get('value_col', 'value')].head(3).tolist())
        st.write(f"**6. Rows: {len(df)} → {len(df_converted)}**")
        st.write("---")
        
        # Store exclusion info for this section
        self._exclusion_info[section_key] = exclusion_info
        
        # Show warning if rows were excluded
        if exclusion_info.has_exclusions():
            with st.expander(
                f"⚠️ {config['title']}: {exclusion_info.excluded_rows} of "
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
        
        return df_converted
    
    def _show_conversion_summary(self) -> None:
        """Show overall conversion summary at the top."""
        converter = self._get_unit_converter()
        if not converter:
            return
        
        default_units = converter.get_default_target_units()
        if default_units:
            with st.expander("ℹ️ Unit Conversion Settings", expanded=False):
                st.markdown("**Default target units:**")
                for category, unit in default_units.items():
                    st.text(f"  • {category}: {unit}")
                st.info(
                    "These are the default units from your configuration. "
                    "You can override them using the controls above."
                )
    
    def _render_section(
        self,
        section_key: str,
        table_dfs: Dict[str, pd.DataFrame],
        filters: Dict[str, Any]
    ) -> None:
        """Render a single section (energy or emissions) with unit conversion."""       
       
        # Get config for this section
        config = self.SECTION_CONFIGS[section_key]

        # ✅ ADD THIS LINE HERE:
        unique_section_key = f"v2_{section_key}"
        
        # Get the dataframe
        df = table_dfs.get(config['df_key'])

        # 🔍 ADD THIS DEBUG LINE:
        # st.write(f"DEBUG: Available columns in {config['df_key']}:", df.columns.tolist())
        
        if df is None or df.empty:
            self.show_error(f"{config['title']} data not available.")
            return
        
        # Apply user filters (scenario, year, etc.)
        df_filtered = self._apply_filters(df, filters)
        
        if df_filtered.empty:
            self.show_warning(f"No {config['title']} data available after applying filters.")
            return
        
        # **APPLY UNIT CONVERSION - This is the key new step!**
        df_converted = self._apply_unit_conversion(
            df_filtered,
            filters,
            section_key,
            config
        )
        
        if df_converted.empty:
            self.show_warning(
                f"No {config['title']} data remaining after unit conversion. "
                f"Try adjusting unit conversion settings in the sidebar."
            )
            return
        
        # Apply additional filters (e.g., attr == 'f_in' for energy)
        for col, val in config['additional_filter'].items():
            if col in df_converted.columns:
                df_converted = df_converted[df_converted[col] == val]
        
        if df_converted.empty:
            self.show_warning(f"No {config['title']} data after applying additional filters.")
            return
        
        # Apply descriptions to get readable names
        desc_mapping = self._get_desc_mapping()
        if desc_mapping:
            df_converted = self._apply_descriptions(
                df_converted,
                ['sector', 'comgroup', 'techgroup', 'com'],
                desc_mapping
            )
        
        # Get available sectors (excluding predefined ones)
        sectors = self._get_available_sectors(df_converted)
        
        if not sectors:
            self.show_warning(f"No sectors available for {config['title']} visualization.")
            return
        
        # Show data summary
        st.metric(
            label=f"{config['title']} Data Points",
            value=f"{len(df_converted):,}",
            help="Number of rows after filtering and unit conversion"
        )
        
        # Render using reusable layout
        st.header(f"{config['title']} Visualization")
        
        agg_disagg_layout(
            df=df_converted,
            sectors=sectors,
            config=config,
            desc_mapping=desc_mapping,
            section_key=unique_section_key  # Changed from section_key
        )
    
    def _get_available_sectors(self, df: pd.DataFrame) -> List[str]:
        """Get list of available sectors, excluding predefined ones."""
        if 'sector' not in df.columns:
            return []
        
        sectors = sorted(df['sector'].unique())
        return [s for s in sectors if s not in self.EXCLUDED_SECTORS]

    def _render_unit_controls(self) -> Dict[str, Any]:
        """
        Render unit conversion controls within the module.
        Uses global defaults but stores per-module.
        
        Returns:
            Dict with 'selected_categories' and 'target_units'
        """
        converter = self._get_unit_converter()
        if not converter:
            st.warning("Unit converter not available")
            return {'target_units': {}, 'selected_categories': []}
        
        # Get defaults from config
        default_target_units = converter.get_default_target_units()
        available_categories = ['energy', 'mass']  # Module-specific categories
        
        # Session keys unique to this module
        module_key = self.name.replace(" ", "_").lower()
        cat_key = f"{module_key}_unit_categories"
        
        # 🆕 IMPORTANT: Initialize ALL session state keys BEFORE rendering widgets
        # This prevents the "first change rerun" issue
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