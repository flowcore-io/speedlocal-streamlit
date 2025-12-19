"""
Energy and Emissions visualization module
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

from modules.base_module import BaseVisualizationModule

class EnergyEmissionsModule(BaseVisualizationModule):
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
    PLOT_SPECS = {
        'energy': {
            'table': 'energy',
            'additional_filter': {
                'attr': 'f_in'
                },
            'aggregate': {
                'series': [{
                    'group_col': 'comgroup_desc', 
                    'type': 'bar', 
                    'stack': True
                    }],
                'title': 'Aggregate Energy Input (All Sectors)'
            },
            'disaggregate': {
                'series': [{
                    'group_col': 'comgroup_desc', 
                    'type': 'bar', 
                    'stack': True
                    }],
                'title_template': 'Energy Input for {sector}'
            }
        },
        'emissions': {
            'table': 'emissions',
            'additional_filter': {},
            'aggregate': {
                'series': [{
                    'group_col': 'sector_desc', 
                    'type': 'line'
                    }],
                'title': 'Aggregate Emissions (All Sectors)'
            },
            'disaggregate': {
                'series': [{
                    'group_col': 'com_desc',
                    'type': 'line'
                    }],
                'title_template': 'Emissions for {sector}'
            }
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
            "show_module_filters": True,
            "filterable_columns": ['subsector', 'comgroup', 'year'],
            "default_columns": []
        }
    
    def _load_and_prepare_data(
        self,
        table_dfs: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Load and prepare energy and emissions data.
        
        Combines both tables and tags them for later separation.
        """
        dfs_to_combine = []
        
        for section_key in ['energy', 'emissions']:
            spec = self.PLOT_SPECS[section_key]
            table_name = spec['table']
            
            if table_name in table_dfs and not table_dfs[table_name].empty:
                df = table_dfs[table_name].copy()
                
                # Apply additional filters (e.g., attr='f_in' for energy)
                for col, val in spec['additional_filter'].items():
                    if col in df.columns:
                        df = df[df[col] == val]
                
                # Tag with section for later separation
                df['_section'] = section_key
                
                dfs_to_combine.append(df)
        
        if not dfs_to_combine:
            return pd.DataFrame()
        
        combined_df = pd.concat(dfs_to_combine, ignore_index=True)
        
        # Apply descriptions
        desc_mapping = self._get_desc_mapping()
        if desc_mapping:
            combined_df = self._apply_descriptions(
                combined_df,
                ['sector', 'comgroup', 'techgroup', 'com'],
                desc_mapping
            )
        
        return combined_df
    
    def _render_visualization(
        self,
        df: pd.DataFrame,
        filters: Dict[str, Any]
    ) -> None:
        """
        Render energy and emissions tabs.
        
        Data is already loaded, filtered, and unit-converted by base class.
        """
        # Create tabs
        energy_tab, emissions_tab = st.tabs(["⚡ Energy", "🌍 Emissions"])
        
        with energy_tab:
            df_energy = df[df['_section'] == 'energy']
            self._render_section('energy', df_energy)
        
        with emissions_tab:
            df_emissions = df[df['_section'] == 'emissions']
            self._render_section('emissions', df_emissions)
    
    def _render_section(
        self,
        section_key: str,
        df: pd.DataFrame
    ) -> None:
        """Render one section (energy or emissions)."""
        if df.empty:
            self.show_warning(f"No data available for {section_key}")
            return
        
        spec = self.PLOT_SPECS[section_key]
        
        # Get available sectors (excluding predefined ones)
        sectors = self._get_available_sectors(df)
        
        if not sectors:
            self.show_warning(f"No sectors available for {section_key}")
            return
        
        # Get unit label for axis
        unit_label = self._get_unit_label(df)
        
        # Show data summary
        st.metric(
            label=f"{spec['aggregate']['title']} - Data Points",
            value=f"{len(df):,}",
            help="Number of rows"
        )
        
        # === AGGREGATE PLOT ===
        
        # Get description mapping and create formatted sector options
        desc_mapping = self._get_desc_mapping()
        
        # Pre-format the sector options as a dict
        sector_options_formatted = {}
        for sector in sectors:
            if desc_mapping and 'sector' in desc_mapping:
                desc = desc_mapping['sector'].get(sector, sector)
                sector_options_formatted[sector] = f"{desc} ({sector})"
            else:
                sector_options_formatted[sector] = sector
        
        # Sector selection - use format_func with the pre-built dict
        selected_sectors = st.multiselect(
            "Select sectors to include:",
            options=sectors,
            default=sectors,
            key=f"{section_key}_agg_sectors",
            format_func=lambda x: sector_options_formatted.get(x, x)
        )
        
        if selected_sectors:
            df_agg = df[df['sector'].isin(selected_sectors)]
            
            # Aggregate by grouping column
            group_col = spec['aggregate']['series'][0]['group_col']
            df_agg = df_agg.groupby(
                ['year', 'scen', group_col],
                as_index=False
            )['value'].sum()
            
            if not df_agg.empty:
                # Build plot spec
                plot_spec = {
                    'x_col': 'year',
                    'y_col': 'value',
                    'scenario_col': 'scen',
                    'series': spec['aggregate']['series'],
                    'axes': {'primary': {'title': unit_label}},
                    'title': spec['aggregate']['title'],
                    'height': 600,
                    'barmode': 'stack'
                }
                from utils._plotting import TimesReportPlotter
                plotter = TimesReportPlotter(df_agg)
                fig = plotter.create_figure(plot_spec)
                
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No data for selected sectors")
    
        # === DISAGGREGATE PLOTS PER SECTOR ===
        st.subheader(f"Disaggregated per Sector")
        
        for sector in sectors:
            # Get sector display name from pre-built dict
            sector_display = sector_options_formatted.get(sector, sector)
            
            with st.expander(f"**{sector_display}**", expanded=False):
                df_sector = df[df['sector'] == sector]
                
                # Aggregate by grouping column
                group_col = spec['disaggregate']['series'][0]['group_col']
                df_sector = df_sector.groupby(
                    ['year', 'scen', group_col],
                    as_index=False
                )['value'].sum()
                
                if not df_sector.empty:
                    # Build plot spec
                    plot_spec = {
                        'x_col': 'year',
                        'y_col': 'value',
                        'scenario_col': 'scen',
                        'series': spec['disaggregate']['series'],
                        'axes': {'primary': {'title': unit_label}},
                        'title': spec['disaggregate']['title_template'].format(sector=sector_display),
                        'height': 600,
                        'barmode': 'stack'
                    }
                    
                    # Create plot
                    from utils._plotting import TimesReportPlotter
                    plotter = TimesReportPlotter(df_sector)
                    fig = plotter.create_figure(plot_spec)
                    
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"No data for {sector_display}")

    def _get_available_sectors(self, df: pd.DataFrame) -> List[str]:
        """Get list of available sectors, excluding predefined ones."""
        if 'sector' not in df.columns:
            return []
        
        sectors = sorted(df['sector'].unique())
        return [s for s in sectors if s not in self.EXCLUDED_SECTORS]