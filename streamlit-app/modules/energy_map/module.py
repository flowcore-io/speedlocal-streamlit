"""
Energy Flow Map module for visualizing regional energy flows.
"""

import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from typing import Dict, Any
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from modules.base_module import BaseModule
from modules.energy_map.map_renderer import FlowMapRenderer


class EnergyMapModule(BaseModule):
    """Energy flow map visualization module."""
    
    def __init__(self):
        super().__init__(
            name="Energy Flow Map",
            description="Visualize regional energy flows on interactive map",
            order=2,  # After Energy & Emissions
            enabled=True
        )
        
        # Initialize map renderer
        config_dir = Path(__file__).parent / "config"
        self.map_renderer = FlowMapRenderer(config_dir)
    
    def get_required_tables(self) -> list:
        return ["map"]
    
    def get_filter_config(self) -> Dict[str, Any]:
        return {
            "apply_global_filters": True,  # Get scenario from sidebar
            "apply_unit_conversion": False,  # Maps don't need unit conversion
            "show_module_filters": True,
            "filterable_columns": ['year', 'com'],
            "default_columns": []
        }
    
    def render(
        self,
        table_dfs: Dict[str, pd.DataFrame],
        filters: Dict[str, Any]
    ) -> None:
        """Main render method for energy flow map."""
        
        if not self.validate_data(table_dfs):
            self.show_error("Map data table not available.")
            return
        
        # Get raw data
        df_raw = table_dfs.get("map")
        
        if df_raw is None or df_raw.empty:
            self.show_error("No map data available.")
            return
        
        # Transform and prepare data
        df_transformed = self._transform_data(df_raw)
        
        if df_transformed.empty:
            self.show_warning("No flow data available after transformation.")
            return
        
        # Apply global filters (scenario)
        df_filtered = self._apply_filters(df_transformed, filters)
        
        if df_filtered.empty:
            self.show_warning("No data available after applying scenario filters.")
            return
        
        # Render map controls and visualization
        self._render_map_interface(df_filtered)
    
    def _transform_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform raw map data into flow format.
        
        Args:
            df: Raw DataFrame from mapping_db_views.csv
            
        Returns:
            DataFrame with columns: scen, year, com, start, end, value
        """
        dfs_to_concat = []
        
        # 1. TB (Transmission Backbone) flows
        tb = df[
            (df['attr'] == 'f_out') & 
            (df['prc'].str.startswith('TB', na=False))
        ].copy()
        
        if not tb.empty:
            # Transform region names - use apply for safer handling
            tb['start'] = tb['regfrom'].apply(
                lambda x: x.split('_', 1)[1] if '_' in str(x) else x
            )
            tb['end'] = tb['regto'].apply(
                lambda x: x.split('_', 1)[1] if '_' in str(x) else x
            )
            dfs_to_concat.append(tb)
        
        # 2. IMP (Import) flows
        imp = df[
            (df['prc'].str.startswith('IMP', na=False)) & 
            (df['topic'] == 'energy') & 
            (df['attr'] == 'f_out')
        ].copy()
        
        if not imp.empty:
            imp['start'] = imp['regfrom'].replace('IMPEXP', 'Global Market')
            imp['end'] = imp['regto'].apply(
                lambda x: x.split('_', 1)[1] if '_' in str(x) else x
            )
            dfs_to_concat.append(imp)
        
        # 3. EXP (Export) flows
        exp = df[
            (df['prc'].str.startswith('EXP', na=False)) & 
            (df['attr'] == 'f_in')
        ].copy()
        
        if not exp.empty:
            exp['start'] = exp['regfrom'].apply(
                lambda x: x.split('_', 1)[1] if '_' in str(x) else x
            )
            exp['end'] = exp['regto'].replace('IMPEXP', 'Global Market')
            dfs_to_concat.append(exp)
        
        if not dfs_to_concat:
            return pd.DataFrame()
        
        # Combine all flows
        df_combined = pd.concat(dfs_to_concat, ignore_index=True)
        
        # Replace DKB with BORNHOLM
        df_combined['start'] = df_combined['start'].replace('DKB', 'BORNHOLM')
        df_combined['end'] = df_combined['end'].replace('DKB', 'BORNHOLM')
        
        # Group by essential columns and aggregate
        df_aggregated = df_combined.groupby(
            ['scen', 'year', 'com', 'start', 'end'],
            as_index=False
        )['value'].sum()
        
        return df_aggregated
    
    def _render_map_interface(self, df: pd.DataFrame) -> None:
        """
        Render map interface with filters and visualization.
        
        Args:
            df: Transformed and filtered DataFrame
        """
        st.header("🗺️ Energy Flow Map")
        
        # Get available filter options
        available_scenarios = sorted(df['scen'].unique())
        available_years = sorted(df['year'].unique())
        available_fuels = sorted(df['com'].unique())
        
        # Create filter controls in columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_scenario = st.selectbox(
                "Scenario",
                options=available_scenarios,
                key="map_scenario_select"
            )
        
        with col2:
            selected_year = st.selectbox(
                "Year",
                options=available_years,
                key="map_year_select"
            )
        
        with col3:
            selected_fuel = st.selectbox(
                "Fuel/Commodity",
                options=available_fuels,
                key="map_fuel_select"
            )
        
        # Filter data based on selections
        df_map = df[
            (df['scen'] == selected_scenario) &
            (df['year'] == selected_year) &
            (df['com'] == selected_fuel)
        ]
        
        if df_map.empty:
            self.show_warning(
                f"No flow data available for {selected_scenario}, "
                f"{selected_year}, {selected_fuel}"
            )
            return
        
        # Show data summary
        st.metric(
            label="Total Flow Volume",
            value=f"{df_map['value'].sum():.1f} PJ",
            help="Sum of all flows for selected filters"
        )
        
        # Create and render map
        st.subheader(f"Flow Map: {selected_scenario} — {selected_year} — {selected_fuel}")
        
        with st.spinner("Generating map..."):
            try:
                folium_map = self.map_renderer.create_flow_map(df_map)
                map_html = folium_map._repr_html_()
                components.html(map_html, height=800, scrolling=True)
            except Exception as e:
                self.show_error(f"Error creating map: {str(e)}")
                st.exception(e)