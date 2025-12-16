"""
Module for sub-annual time data visualization.
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


class SubAnnualModule(BaseVisualizationModule):
    def __init__(self):
        super().__init__(
            name="Sub-Annual Profile",
            description="subannual visualization",
            order=4,
            enabled=True
        )
        self._exclusion_info = {}  # Track exclusions per section
        # Load configuration
        self.config_dir = Path(__file__).parent / "config"
        self.profile_config = self._load_profile_config()

    def get_required_tables(self) -> list:
        return ["energy_subannual"]
    
    def get_config(self) -> Dict[str, Any]:
        """Return module configuration."""
        return {
            "apply_global_filters": True,
            "apply_unit_conversion": True,
            "show_module_filters": True,
            "filterable_columns": ['techgroup', 'prc'],
            "default_columns": ['techgroup']
        }
    
    def _load_profile_config(self) -> Dict:
        """Load profile_config.yaml."""
        config_path = self.config_dir / "profile_config.yaml"
        
        if not config_path.exists():
            st.warning(f"Config file not found: {config_path}")
            return {}
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    
    def _load_and_prepare_data(self, table_dfs: Dict) -> pd.DataFrame:
        """Combine required tables and prepare."""
        dfs = []
        for table_name in self.get_required_tables():
            if table_name in table_dfs:
                df = table_dfs[table_name].copy()
                # Filter out ANNUAL
                if 'all_ts' in df.columns:
                    df = df[df['all_ts'] != 'ANNUAL']
                dfs.append(df)
        
        df_combined = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
        
        # Labels are already mapped to descriptions by DataLoaderManager
        return df_combined
    
    def _get_available_weeks(self) -> List[str]:
        """
        Get list of available weeks from timeslice metadata.
        
        Returns:
            List of week codes (e.g., ['W03', 'W09', 'W16', 'W42'])
        """
        # Get timeslice metadata from session
        ts_metadata = st.session_state.get('ts_metadata', pd.DataFrame())
        
        if ts_metadata.empty or 'all_ts' not in ts_metadata.columns:
            # Fallback to hardcoded list if metadata not available
            return ['W03', 'W09', 'W16', 'W42']
        
        # Extract unique week prefixes (first 3 characters)
        weeks = ts_metadata['all_ts'].str[:3].unique()
        
        # Filter to only week codes (start with 'W')
        weeks = [w for w in weeks if str(w).startswith('W')]
        
        # Sort naturally (W03, W09, W16, W42)
        weeks = sorted(weeks, key=lambda x: int(x[1:]) if len(x) > 1 and x[1:].isdigit() else 0)
        
        return weeks

    def _render_visualization(self, df: pd.DataFrame, filters: Dict) -> None:
        """Render interface."""
        st.header("Subannual Profile")
        
        # Filter controls
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            scenarios = sorted(df['scen'].unique())
            selected_scenario = st.selectbox("Scenario", scenarios, key="tp_scenario")
        
        with col2:
            years = sorted(df['year'].unique())
            selected_year = st.selectbox("Year", years, index=len(years)-1, key="tp_year")
        
        with col3:
            regions = sorted(df['regfrom'].unique()) if 'regfrom' in df.columns else []
            if not regions:
                self.show_warning("No regions found in data")
                return
            
            selected_region = st.selectbox(
                "Region", 
                regions, 
                index=0,
                key="tp_region"
            )
        
        with col4:
            # Get available weeks from metadata (dynamically loaded)
            available_weeks = self._get_available_weeks()
            
            selected_weeks = st.multiselect(
                "Weeks",
                options=available_weeks,
                default=[],
                key="tp_weeks",
                help="Select specific weeks to display (leave empty to show all weeks)"
            )

        # Filter data by scenario/year/region
        df_plot = df[
            (df['scen'] == selected_scenario) &
            (df['year'] == selected_year) &
            (df['regfrom'] == selected_region)
        ]
        
        if df_plot.empty:
            self.show_warning("No data for selected filters.")
            return
        
        # Filter to selected weeks (ONLY if weeks are selected)
        if selected_weeks:  # ← CHANGED: Only filter if user selected specific weeks
            week_pattern = '|'.join([f'^{w}' for w in selected_weeks])
            df_plot = df_plot[df_plot['all_ts'].str.match(week_pattern)]
            
            if df_plot.empty:
                self.show_warning("No data for selected week(s).")
                return
        
        # Transform to wide format
        df_wide = self._transform_to_wide(df_plot)
        
        if df_wide.empty:
            self.show_warning("No data after transformation.")
            return
        
        # Debug info
        with st.expander("🔍 Debug Info", expanded=False):
            st.write("**DataFrame shape:**", df_wide.shape)
            st.write("**Columns:**", df_wide.columns.tolist())
            
            data_cols = [col for col in df_wide.columns if col not in ['all_ts', 'scen', 'year']]
            st.write("**Data columns:**", data_cols)
            st.write("**Number of series:**", len(data_cols))

        # Get all data columns (technology names)
        data_cols = [col for col in df_wide.columns if col not in ['all_ts', 'scen', 'year']]

        if not data_cols:
            self.show_warning("No data series to plot")
            return

        # Create plot
        # st.subheader(f"Profile: {selected_scenario} — {selected_year} — {selected_region}")

        try:
            # Get unit label
            unit_label = self._get_unit_label(df_plot)
            
            # Build plot specification from profile_config.yaml
            plot_spec = self._build_plot_spec_from_config(
                data_cols=data_cols,
                unit_label=unit_label,
                title=f"Time Profile: {selected_scenario} — {selected_year} — {selected_region}"
            )

            plotter = TimesReportPlotter(df_wide)
            fig = plotter.create_figure(plot_spec)
            
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                self.show_error("Failed to create plot")

        except Exception as e:
            self.show_error(f"Error creating plot: {str(e)}")
            st.exception(e)
    
    def _aggregate_regions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate by regions (replaces transformer method)."""
        group_cols = [col for col in df.columns 
                     if col not in ['regfrom', 'regto', 'value']]
        return df.groupby(group_cols, as_index=False)['value'].sum()
    
    def _transform_to_wide(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform to wide format using just the label column."""
        try:
            if 'label' not in df.columns:
                st.error("No 'label' column found in data")
                return pd.DataFrame()
            
            # Use label directly as column name (no combining with other fields)
            df_wide = df.pivot_table(
                index=['all_ts', 'scen', 'year'],
                columns='label',  # Just use label as-is
                values='value',
                aggfunc='sum'
            ).reset_index()
            
            return df_wide
        
        except Exception as e:
            st.error(f"Error transforming data: {e}")
            st.exception(e)
            return pd.DataFrame()
    
    def _build_axes_config(self) -> Dict:
        """Build axes config from profile_config.yaml."""
        return {
            'primary': self.profile_config['y_axes']['primary'],
            'secondary': self.profile_config['y_axes'].get('secondary')
        }

    def _build_plot_spec_from_config(
        self, 
        data_cols: List[str], 
        unit_label: str,
        title: str
    ) -> Dict[str, Any]:
        """
        Build plot specification from profile_config.yaml.
        
        Args:
            data_cols: List of column names to plot (technology names)
            unit_label: Unit label for y-axis
            title: Plot title
        
        Returns:
            Plot specification dict for create_figure()
        """
        # Get config sections
        plot_groups = self.profile_config.get('plot_groups', {})
        y_axes = self.profile_config.get('y_axes', {})
        
        # Get production plot config (assuming all data_cols are production)
        production_config = plot_groups.get('production', {}) #SHOULD CHANGE THIS SYSTEM IN THE FUTURE
        
        # Build series specification
        series_spec = {
            'columns': data_cols,
            'type': production_config.get('plot_type', 'bar'),
            'stack': production_config.get('stack', True),
            'y_axis': production_config.get('y_axis', 'primary'),
            'opacity': production_config.get('opacity', 0.85)
        }
        
        # Build axes configuration
        primary_axis = y_axes.get('primary', {})
        axes_config = {
            'primary': {
                'title': f"{primary_axis.get('title', 'Value')} [{unit_label}]",
                'side': primary_axis.get('side', 'left'),
                'showgrid': primary_axis.get('showgrid', False)
            }
        }
        
        # Add secondary axis if configured
        if 'secondary' in y_axes:
            secondary_axis = y_axes['secondary']
            axes_config['secondary'] = {
                'title': secondary_axis.get('title', 'Secondary Value'),
                'side': secondary_axis.get('side', 'right'),
                'overlaying': 'y',
                'showgrid': secondary_axis.get('showgrid', False)
            }
        
        # Build complete plot specification
        plot_spec = {
            'x_col': 'all_ts',
            'y_col': None,  # Using explicit columns
            'series': [series_spec],
            'axes': axes_config,
            'title': title,
            'height': 600,
            'barmode': 'stack' if series_spec['stack'] else 'group',
            'xaxis_type': 'category'
        }
        
        return plot_spec