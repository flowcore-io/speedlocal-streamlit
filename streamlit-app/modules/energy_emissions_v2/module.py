"""
Energy and Emissions visualization module - Version 2 with Unit Conversion.
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

from modules.base_module import BaseModule
from components.layouts import agg_disagg_layout
from utils.unit_converter import UnitConverter, ExclusionInfo


class EnergyEmissionsModuleV2(BaseModule):
    """
    Energy and Emissions visualization module with unit conversion.
    
    Features:
    - Auto-detects unit categories from data
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
        },
        'emissions': {
            'df_key': 'emissions',
            'additional_filter': {},
            'plot_method': 'line_plot',
            'group_col_aggregate': 'sector_desc',
            'group_col_disaggregate': 'com_desc',
            'title': 'Emissions',
        }
    }
    
    def __init__(self):
        super().__init__(
            name="Energy & Emissions",
            description="Annual reporting with unit conversion support",
            order=1,
            enabled=True
        )
        self._exclusion_info = {}  # Track exclusions per section
    
    def get_required_tables(self) -> list:
        return ["energy", "emissions"]
    
    def get_config(self) -> Dict[str, Any]:
        """Return module configuration."""
        return {
            "apply_global_filters": True,
            "apply_unit_conversion": True,
            "show_module_filters": False,
            "filterable_columns": ['subsector', 'comgroup', 'year'],
            "default_columns": []
        }
    
    def render(
        self,
        table_dfs: Dict[str, pd.DataFrame],
        filters: Dict[str, Any]
    ) -> None:
        """Main render method with unit conversion."""
        
        if not self.validate_data(table_dfs):
            self.show_error("Required data tables (energy/emissions) not available.")
            return
        
        # Get unit manager from session
        unit_mgr = st.session_state.get('unit_manager')

        # Render unit controls (manager checks if enabled via get_config)
        unit_config = None
        if unit_mgr:
            unit_config = unit_mgr.render_unit_controls_if_enabled(
                module=self,
                table_dfs=table_dfs,
                expanded=False
            )
        
        # Add to filters if available
        if unit_config:
            filters['unit_config'] = unit_config
        
        st.divider()
        
        # Show overall conversion summary
        if unit_config:
            unit_mgr.show_conversion_summary()
        
        # Create sub-tabs for Energy and Emissions
        energy_tab, emissions_tab = st.tabs(["⚡ Energy", "🌍 Emissions"])
        
        with energy_tab:
            self._render_section('energy', table_dfs, filters)
        
        with emissions_tab:
            self._render_section('emissions', table_dfs, filters)
    
    def _render_section(
        self,
        section_key: str,
        table_dfs: Dict[str, pd.DataFrame],
        filters: Dict[str, Any]
    ) -> None:
        """Render a single section (energy or emissions) with unit conversion."""       
       
        config = self.SECTION_CONFIGS[section_key]
        unique_section_key = f"{section_key}"
        df = table_dfs.get(config['df_key'])
        
        if df is None or df.empty:
            self.show_error(f"{config['title']} data not available.")
            return
        
        # Apply user filters
        df_filtered = self._apply_filters(df, filters)
        
        if df_filtered.empty:
            self.show_warning(f"No {config['title']} data available after applying filters.")
            return
        
        # Apply unit conversion using UnitManager
        unit_mgr = st.session_state.get('unit_manager')
        if unit_mgr and 'unit_config' in filters:
            unit_config = unit_mgr.get_unit_config_from_filters(filters)
            df_converted, _ = unit_mgr.apply_unit_conversion(
                df_filtered,
                unit_config,
                section_title=config['title']
            )
        else:
            df_converted = df_filtered
        
        if df_converted.empty:
            self.show_warning(f"No {config['title']} data remaining after unit conversion.")
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
            section_key=unique_section_key
        )
    
    def _get_available_sectors(self, df: pd.DataFrame) -> List[str]:
        """Get list of available sectors, excluding predefined ones."""
        if 'sector' not in df.columns:
            return []
        
        sectors = sorted(df['sector'].unique())
        return [s for s in sectors if s not in self.EXCLUDED_SECTORS]