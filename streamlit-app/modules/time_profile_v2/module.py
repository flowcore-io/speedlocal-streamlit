"""
Time Profile Module for hourly/sub-annual time series visualization.
"""

import streamlit as st
import pandas as pd
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from modules.base_module import BaseVisualizationModule
from utils._plotting import TimesReportPlotter


class TimeProfileModuleV2(BaseVisualizationModule):
    def __init__(self):
        super().__init__(
            name="Time Profile V2",
            description="subannual visualization",
            order=4,
            enabled=True
        )
        self._exclusion_info = {}  # Track exclusions per section
        # Load configuration
        self.config_dir = Path(__file__).parent / "config"
        self.profile_config = self._load_profile_config()
        self.profile_mapping = self._load_profile_mapping()

    def get_required_tables(self) -> list:
        return ["energy_subannual"]
    
    def get_config(self) -> Dict[str, Any]:
        """Return module configuration."""
        return {
            "apply_global_filters": True,
            "apply_unit_conversion": True,
            "show_module_filters": True,
            "filterable_columns": ['regfrom'],
            "default_columns": ['regfrom']
        }
    
    def _load_and_prepare_data(self, table_dfs: Dict) -> pd.DataFrame:
        """Combine required tables and prepare."""
        # Combine tables
        dfs = []
        for table_name in self.get_required_tables():
            if table_name in table_dfs:
                df = table_dfs[table_name].copy()
                # Filter out ANNUAL
                if 'all_ts' in df.columns:
                    df = df[df['all_ts'] != 'ANNUAL']
                dfs.append(df)
        
        df_combined = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
        
        # Apply descriptions
        df_combined = self._apply_descriptions(df_combined, ['label'])
        
        return df_combined
    
    def _render_visualization(self, df: pd.DataFrame, filters: Dict) -> None:
        """Render time profile interface."""
        st.header("⏱️ Time Series Profile")
        
        # Filter controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            scenarios = sorted(df['scen'].unique())
            selected_scenario = st.selectbox("Scenario", scenarios)
        
        with col2:
            years = sorted(df['year'].unique())
            selected_year = st.selectbox("Year", years, index=len(years)-1)
        
        with col3:
            aggregate = st.checkbox("Aggregate all regions", value=True)
        
        # Filter data
        df_plot = df[
            (df['scen'] == selected_scenario) &
            (df['year'] == selected_year)
        ]
        
        if df_plot.empty:
            self.show_warning("No data for selected filters.")
            return
        
        # Aggregate regions if needed
        if aggregate and 'regfrom' in df_plot.columns:
            df_plot = self._aggregate_regions(df_plot)
        
        # Transform to wide format
        df_wide = self._transform_to_wide(df_plot)
        
        if df_wide.empty:
            self.show_warning("No data after transformation.")
            return
        
        # Build plot spec from config
        plot_spec = self._build_plot_spec(df_wide)
        
        # Create plot
        st.subheader(f"Profile: {selected_scenario} — {selected_year}")
        plotter = TimesReportPlotter(df_wide)
        fig = plotter.create_figure(plot_spec)
        st.plotly_chart(fig, use_container_width=True)
    
    def _aggregate_regions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate by regions (replaces transformer method)."""
        group_cols = [col for col in df.columns 
                     if col not in ['regfrom', 'regto', 'value']]
        return df.groupby(group_cols, as_index=False)['value'].sum()
    
    def _transform_to_wide(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform to wide format (replaces transformer method)."""
        try:
            return df.pivot_table(
                index=['all_ts', 'scen', 'year'],
                columns='label',
                values='value',
                aggfunc='sum'
            ).reset_index()
        except Exception as e:
            st.error(f"Error transforming data: {e}")
            return pd.DataFrame()
    
    def _build_plot_spec(self, df_wide: pd.DataFrame) -> Dict:
        """Build plot spec from config and data."""
        # Map columns to plot groups using profile_mapping
        plot_groups = self._map_columns_to_groups(df_wide)
        
        # Build series from config
        series = []
        for group_name, columns in plot_groups.items():
            group_config = self.profile_config['plot_groups'][group_name]
            series.append({
                'columns': columns,
                'type': group_config['plot_type'],
                'y_axis': group_config.get('y_axis', 'primary'),
                'stack': group_config.get('stack', False),
                'opacity': group_config.get('opacity', 0.85),
            })
        
        return {
            'x_col': 'all_ts',
            'series': series,
            'axes': self._build_axes_config(),
            'title': f"Time Profile: {df_wide['scen'].iloc[0]} ({df_wide['year'].iloc[0]})",
            'height': 600
        }
    
    def _map_columns_to_groups(self, df_wide: pd.DataFrame) -> Dict[str, List[str]]:
        """Map columns to plot groups using profile_mapping."""
        categories = {}
        data_cols = [col for col in df_wide.columns 
                    if col not in ['all_ts', 'scen', 'year']]
        
        for col in data_cols:
            match = self.profile_mapping[self.profile_mapping['label'] == col]
            if not match.empty:
                plot_group = match.iloc[0]['plot_group']
                if plot_group not in categories:
                    categories[plot_group] = []
                categories[plot_group].append(col)
        
        return categories
    
    def _build_axes_config(self) -> Dict:
        """Build axes config from profile_config.yaml."""
        return {
            'primary': self.profile_config['y_axes']['primary'],
            'secondary': self.profile_config['y_axes'].get('secondary')
        }