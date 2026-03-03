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
            name="Subannual Profile",
            description="subannual visualization",
            order=4,
            enabled=True
        )
        self._exclusion_info = {}  # Track exclusions per section
        # Load configuration
        self.config_dir = Path(__file__).parent / "config"
        self.profile_config = self._load_profile_config()

    def get_required_tables(self) -> list:
#        return ["energy_subannual", "elc_price"]
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
        
        return df_combined
    
    def _get_available_timeslice_groups(self) -> Dict[str, List[str]]:
        config = self._load_profile_config()
        parts_map = config.get('timeslice_groups', {})
        
        ts_metadata = st.session_state.get('ts_metadata', pd.DataFrame())
        
        if ts_metadata.empty or 'all_ts' not in ts_metadata.columns:
            return {key: [] for key in parts_map}

        series = ts_metadata['all_ts'].dropna().astype(str)
        results = {}

        for key, prefix in parts_map.items():
            # extract() grabs the digits, then we prepend the prefix back
            extracted = series.str.extract(rf'{prefix}(\d+)', expand=False).dropna().unique()
            
            # Sort by converting to int, then return the formatted string
            # We use a list comprehension to put the prefix back on
            sorted_values = sorted(extracted, key=int)
            results[key] = [f"{prefix}{v}" for v in sorted_values]

        return results

    def _render_visualization(self, df: pd.DataFrame, filters: Dict) -> None:
        """Render interface with dynamic timeslice groups."""
        st.header("Subannual Profile")

        # Global Filter Controls (Row 1)
        g_col1, g_col2, g_col3 = st.columns(3)
        
        with g_col1:
            scenarios = sorted(df['scen'].unique())
            selected_scenario = st.selectbox("Scenario", scenarios, key="tp_scenario")
        
        with g_col2:
            years = sorted(df['year'].unique())
            selected_year = st.selectbox("Year", years, index=len(years)-1, key="tp_year")
        
        with g_col3:
            regions = sorted(df['regfrom'].unique()) if 'regfrom' in df.columns else []
            if not regions:
                self.show_warning("No regions found in data")
                return
            selected_region = st.selectbox("Region", regions, index=0, key="tp_region")

        # Dynamic Timeslice Controls (Row 2)
        st.markdown("---")
        ts_groups = self._get_available_timeslice_groups()
        ts_cols = st.columns(len(ts_groups))
        
        # Store selections in a dict to use for filtering
        selections = {}
        
        for i, (group_label, options) in enumerate(ts_groups.items()):
            with ts_cols[i]:
                selections[group_label] = st.multiselect(
                    label=group_label.capitalize(),
                    options=options,
                    default=[],
                    key=f"tp_{group_label}"
                )

        # 3. Apply Global Filters
        df_plot = df[
            (df['scen'] == selected_scenario) &
            (df['year'] == selected_year) &
            (df['regfrom'] == selected_region)
        ]
        
        if df_plot.empty:
            self.show_warning("No data for selected filters.")
            return

        # Apply Generic Timeslice Filtering
        # This logic filters the dataframe for every group where a selection was made
        for group_label, selected_values in selections.items():
            if selected_values:
                # Matches any of the selected codes (e.g., 'S001|S002') within the string
                pattern = '|'.join(selected_values)
                df_plot = df_plot[df_plot['all_ts'].str.contains(pattern, na=False)]
                
                if df_plot.empty:
                    self.show_warning(f"No data for selected {group_label}.")
                    return

        # Transform and Render
        df_wide = self._transform_to_wide(df_plot)
        
        if df_wide.empty:
            self.show_warning("No data after transformation.")
            return
        
        # Debug info
        # with st.expander("🔍 Debug Info", expanded=False):
        #     st.write("**DataFrame shape:**", df_wide.shape)
        #     st.write("**Columns:**", df_wide.columns.tolist())
            
        #     data_cols = [col for col in df_wide.columns if col not in ['all_ts', 'scen', 'year']]
        #     st.write("**Data columns:**", data_cols)
        #     st.write("**Number of series:**", len(data_cols))

        # Get all data columns (technology names)
        data_cols = [col for col in df_wide.columns if col not in ['all_ts', 'scen', 'year']]

        if not data_cols:
            self.show_warning("No data series to plot")
            return
        
        try:
            # Get unit label
            unit_label = self._get_unit_label(df_plot)
            
            # Build plot specification from profile_config.yaml
            plot_spec = self._build_plot_spec_from_config(
                data_cols=data_cols,
                unit_label=unit_label,
                title=f"Subannual Profile: {selected_scenario} — {selected_year} — {selected_region}"
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