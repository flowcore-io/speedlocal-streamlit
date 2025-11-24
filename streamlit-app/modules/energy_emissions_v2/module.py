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
        # st.write("**DEBUG _get_unit_config:**")
        # st.write(f"  - 'unit_config' in filters: {'unit_config' in filters}")
        # if 'unit_config' in filters:
        #     st.write(f"  - filters['unit_config']: {filters['unit_config']}")
        
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
        
        # # 🔍 DEBUG OUTPUT
        # st.write(f"### 🔍 DEBUG: {config['title']}")
        # st.write(f"**1. Target units from config:**", unit_config.get('target_units'))
        # st.write(f"**2. Units in your data (first 10):**", df[config.get('unit_col', 'unit')].dropna().unique()[:10].tolist())
        # st.write(f"**3. Sample values BEFORE conversion:**")
        
        # unit_col = config.get('unit_col', 'unit')
        # currency_col = config.get('currency_col', 'cur')
        # value_col = config.get('value_col', 'value')

        # for idx, row in df.head(3).iterrows():
        #     value = row[value_col]
        #     unit = row.get(unit_col, '')
        #     currency = row.get(currency_col, '')
            
        #     # Build display string
        #     parts = [f"  Row {idx}: {value}"]
        #     if pd.notna(unit) and unit != '' and unit != 'NA':
        #         parts.append(unit)
        #     if pd.notna(currency) and currency != '' and currency != 'NA':
        #         parts.append(f"[{currency}]")
            
        #     st.write(" ".join(parts))

        # Apply conversion and filtering
        df_converted, exclusion_info = converter.convert_and_filter(
            df,
            target_units=unit_config.get('target_units'),
            selected_categories=unit_config.get('selected_categories'),
            unit_col=config.get('unit_col', 'unit'),
            currency_col=config.get('currency_col', 'cur'),
            value_col=config.get('value_col', 'value')
        )
        
        # # 🔍 DEBUG OUTPUT
        # st.write(f"**4. Units AFTER conversion:**", df_converted[config.get('unit_col', 'unit')].dropna().unique()[:10].tolist())
        # st.write(f"**5. Sample values AFTER conversion:**")
        # for idx, row in df_converted.head(3).iterrows():
        #     value = row[value_col]
        #     unit = row.get(unit_col, '')
        #     currency = row.get(currency_col, '')
            
        #     # Build display string
        #     parts = [f"  Row {idx}: {value}"]
        #     if pd.notna(unit) and unit != '' and unit != 'NA':
        #         parts.append(unit)
        #     if pd.notna(currency) and currency != '' and currency != 'NA':
        #         parts.append(f"[{currency}]")
            
        #     st.write(" ".join(parts))

        # st.write(f"**6. Rows: {len(df)} to {len(df_converted)}**")
        # st.write("---")
        
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
        Delegates to FilterManager for actual rendering.
        
        Returns:
            Dict with 'selected_categories' and 'target_units'
        """
        # Get filter manager from session
        filter_manager = st.session_state.get('filter_manager')
        if not filter_manager:
            st.warning("Filter manager not available")
            return {'target_units': {}, 'selected_categories': []}
        
        # Get module-specific categories (energy and mass for this module)
        available_categories = ['energy', 'mass']
        
        # Use unique module key
        module_key = self.name.replace(" ", "_").lower()
        
        # Delegate to FilterManager
        return filter_manager.render_module_unit_controls(
            module_key=module_key,
            available_categories=available_categories
        )