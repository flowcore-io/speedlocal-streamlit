"""
Energy and Emissions visualization module.
Refactored to use reusable agg_disagg_layout component.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now import from base modules and components
from modules.base_module import BaseModule
from components.layouts import agg_disagg_layout


class EnergyEmissionsModule(BaseModule):
    """Energy and Emissions visualization module."""
    
    # Sectors to exclude
    EXCLUDED_SECTORS = ['DMZ', 'SYS', 'DHT', 'ELT', 'TRD', 'UPS', 'NA', 'FTS']
    
    # Configuration for each section
    SECTION_CONFIGS = {
        'energy': {
            'df_key': 'energy',
            'additional_filter': {'attr': 'f_in'},
            'plot_method': 'stacked_bar',
            'group_col_aggregate': 'comgroup_desc',
            'group_col_disaggregate': 'comgroup_desc',
            'title': 'Energy Input'
        },
        'emissions': {
            'df_key': 'emissions',
            'additional_filter': {},
            'plot_method': 'line_plot',
            'group_col_aggregate': 'sector_desc',
            'group_col_disaggregate': 'comgroup_desc',
            'title': 'Emissions'
        }
    }
    
    def __init__(self):
        super().__init__(
            name="Energy & Emissions",
            description="Annual reporting with sector-level analysis",
            order=1,
            enabled=True
        )
    
    def get_required_tables(self) -> list:
        return ["energy", "emissions"]
    
    def get_filter_config(self) -> Dict[str, Any]:
        return {
            "apply_global_filters": True,
            "show_module_filters": False,
            "filterable_columns": ['sector', 'subsector', 'comgroup', 'year'],
            "default_columns": []
        }
    
    def render(
        self,
        table_dfs: Dict[str, pd.DataFrame],
        filters: Dict[str, Any]
    ) -> None:
        """Main render method."""
        
        if not self.validate_data(table_dfs):
            self.show_error("Required data tables (energy/emissions) not available.")
            return
        
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
        """Render a single section (energy or emissions)."""
        
        # Get config for this section
        config = self.SECTION_CONFIGS[section_key]
        
        # Get the dataframe
        df = table_dfs.get(config['df_key'])
        
        if df is None or df.empty:
            self.show_error(f"{config['title']} data not available.")
            return
        
        # Apply user filters (scenario, year, etc.)
        df_filtered = self._apply_filters(df, filters)
        
        if df_filtered.empty:
            self.show_warning(f"No {config['title']} data available after applying filters.")
            return
        
        # Apply additional filters (e.g., attr == 'f_in' for energy)
        for col, val in config['additional_filter'].items():
            if col in df_filtered.columns:
                df_filtered = df_filtered[df_filtered[col] == val]
        
        if df_filtered.empty:
            self.show_warning(f"No {config['title']} data after applying additional filters.")
            return
        
        # Apply descriptions to get readable names
        desc_mapping = self._get_desc_mapping()
        if desc_mapping:
            df_filtered = self._apply_descriptions(
                df_filtered,
                ['sector', 'comgroup', 'techgroup'],
                desc_mapping
            )
        
        # Get available sectors (excluding predefined ones)
        sectors = self._get_available_sectors(df_filtered)
        
        if not sectors:
            self.show_warning(f"No sectors available for {config['title']} visualization.")
            return
        
        # Render using reusable layout
        st.header(f"{config['title']} Visualization")
        
        agg_disagg_layout(
            df=df_filtered,
            sectors=sectors,
            config=config,
            desc_mapping=desc_mapping,
            section_key=section_key
        )
    
    def _get_available_sectors(self, df: pd.DataFrame) -> List[str]:
        """Get list of available sectors, excluding predefined ones."""
        if 'sector' not in df.columns:
            return []
        
        sectors = sorted(df['sector'].unique())
        return [s for s in sectors if s not in self.EXCLUDED_SECTORS]