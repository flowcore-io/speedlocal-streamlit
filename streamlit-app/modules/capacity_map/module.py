"""
Capacity Map module for visualizing process capacities on a geographic map.
"""

import streamlit as st
from streamlit_folium import st_folium
import yaml
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List, Any

from modules.base_module import BaseModule
from .map_builder import MapBuilder


class CapacityMapModule(BaseModule):
    """Capacity Map visualization module"""
    
    def __init__(self):
        """Initialize the Capacity Map module."""
        super().__init__(
            name="Capacity Map",
            description="Visualize process capacities on an interactive geographic map",
            order=4,
            enabled=True
        )
        
        # Load configurations
        self.config_path = Path(__file__).parent / "config"
        self.prc_coords = self._load_yaml_config("prc_coordinates.yaml")
        self.map_settings = self._load_yaml_config("map_settings.yaml")
        
        # Initialize map builder
        self.map_builder = MapBuilder(self.map_settings, self.prc_coords)
    
    def get_required_tables(self) -> list:
        """Get list of required database tables/views."""
        return ["capacity_map"]
    
    def get_config(self) -> Dict[str, Any]:
        """Get module configuration."""
        return {
            "apply_global_filters": True,
            "apply_unit_conversion": False,
            "show_module_filters": False,
            "filterable_columns": ['year', 'prc', 'reg'],
            "default_columns": []
        }
    
    def _load_yaml_config(self, filename: str) -> dict:
        """Load YAML configuration file"""
        try:
            with open(self.config_path / filename) as f:
                return yaml.safe_load(f)
        except Exception as e:
            st.error(f"Error loading {filename}: {e}")
            return {}
    
    def render(
        self,
        table_dfs: Dict[str, pd.DataFrame],
        filters: Dict[str, Any]
    ) -> None:
        """
        Main render method - entry point for the module
        
        Args:
            table_dfs: Dictionary of dataframes loaded from mapping_db_views.csv
            filters: Dictionary with filter selections (scenario, etc.)
        """
        st.title("Capacity Map")
        st.markdown("""
        Visualize process capacities on an interactive geographic map. 
        Each marker represents a facility with technical capacity (tcap) data.
        """)
        
        # Validate data availability
        if not self.validate_data(table_dfs):
            self.show_error("Capacity map data table not available.")
            with st.expander("Setup Instructions"):
                st.markdown("""
                Add this line to `inputs/mapping_db_views.csv`:
                ```
                capacity_map,prc,,,,,,,,capacity,tcap,,,,,,,,,,
                ```
                Then restart the application.
                """)
            return
        
        # Get raw data from table_dfs
        df_raw = table_dfs.get("capacity_map")
        
        if df_raw is None or df_raw.empty:
            self.show_warning("No capacity data available.")
            return
        
        # Apply global filters (scenario)
        df_filtered = self._apply_filters(df_raw, filters)
        
        if df_filtered.empty:
            self.show_warning("No data available after applying filters.")
            return
        
        # Render page filters and get selections
        filter_selections = self._render_page_filters(df_filtered)
        
        if filter_selections is None:
            st.info("Configure filters in the sidebar to display the map")
            return
        
        # Apply module-specific filters
        capacity_data = self._apply_module_filters(df_filtered, filter_selections)
        
        # Check for data after filtering
        if capacity_data.empty:
            self.show_warning("No capacity data matches the selected filters.")
            return
        
        # Check for unmapped processes
        unmapped = self.map_builder.get_unmapped_processes(capacity_data)
        if unmapped:
            with st.expander(f"{len(unmapped)} processes without coordinate mappings", expanded=False):
                st.warning(
                    f"The following {len(unmapped)} processes have capacity data but no coordinates defined:\n\n"
                    f"{', '.join(unmapped)}"
                )
        
        # Display map and summary
        self._render_map_and_summary(capacity_data, filter_selections)
    
    def _apply_filters(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """Apply global filters (scenario)."""
        df_filtered = df.copy()
        
        # Apply scenario filter if available
        if 'scenario' in filters and filters['scenario']:
            if 'scen' in df_filtered.columns:
                df_filtered = df_filtered[df_filtered['scen'] == filters['scenario']]
        
        return df_filtered
    
    def _render_page_filters(self, df_raw: pd.DataFrame) -> Optional[dict]:
        """
        Render page filter controls (not sidebar)
        
        Args:
            df_raw: Raw dataframe from table_dfs
            
        Returns:
            Dictionary with filter selections or None if invalid
        """
        st.subheader("Filter Settings")
        
        # Get available scenarios
        available_scenarios = sorted(df_raw['scen'].unique()) if 'scen' in df_raw.columns else []
        if not available_scenarios:
            st.error("No scenarios available")
            return None
        
        # Get available years
        available_years = sorted(df_raw['year'].unique()) if 'year' in df_raw.columns else []
        if not available_years:
            st.error("No years available")
            return None
        
        # Create filter controls in columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_scenario = st.selectbox(
                "Scenario",
                options=available_scenarios,
                key="capacity_map_scenario"
            )
        
        with col2:
            selected_year = st.selectbox(
                "Year",
                options=available_years,
                index= 0,
                key="capacity_map_year"
            )
        
        # Filter data by scenario and year for subsequent filters
        df_filtered = df_raw[
            (df_raw['scen'] == selected_scenario) &
            (df_raw['year'] == selected_year)
        ]
        
        # Get processes that have coordinates defined
        all_processes = df_filtered['prc'].unique() if 'prc' in df_filtered.columns else []
        mapped_processes = [p for p in all_processes if p in self.prc_coords]
        
        if not mapped_processes:
            st.warning("No processes with coordinate mappings found")
            return None
        
        # Get facility types from mapped processes
        available_types = list(set(
            self.prc_coords[p].get('type', 'unknown') 
            for p in mapped_processes
        ))
        
        with col3:
            # Facility type filter
            selected_types = st.multiselect(
                "Facility Types",
                options=sorted(available_types),
                default=sorted(available_types),
                key="capacity_map_types"
            )
        
        # Filter processes by selected types
        filtered_processes = [
            p for p in mapped_processes 
            if self.prc_coords[p].get('type', 'unknown') in selected_types
        ]
        
        # Get regions from filtered processes
        available_regions = list(set(
            self.prc_coords[p].get('region', 'unknown') 
            for p in filtered_processes
        ))
        
        # Region filter (full width below)
        selected_regions = st.multiselect(
            "Regions",
            options=sorted(available_regions),
            default=sorted(available_regions),
            key="capacity_map_regions"
        )
        
        # Final process list after region filter
        final_processes = [
            p for p in filtered_processes
            if self.prc_coords[p].get('region', 'unknown') in selected_regions
        ]
        
        if not final_processes:
            st.warning("No processes match the selected filters")
            return None
        
        st.info(f"🔍 {len(final_processes)} facilities will be displayed")
        
        st.divider()
        
        return {
            'scenario': selected_scenario,
            'year': selected_year,
            'processes': final_processes,
            'regions': selected_regions,
            'types': selected_types
        }
    
    def _apply_module_filters(self, df_raw: pd.DataFrame, filter_selections: dict) -> pd.DataFrame:
        """
        Apply module-specific filters
        
        Args:
            df_raw: Raw dataframe
            filter_selections: Dictionary with filter selections
            
        Returns:
            Filtered dataframe
        """
        df = df_raw.copy()
        
        # Filter by scenario
        if 'scen' in df.columns and 'scenario' in filter_selections:
            df = df[df['scen'] == filter_selections['scenario']]

        # Filter by year
        if 'year' in df.columns:
            df = df[df['year'] == filter_selections['year']]
        
        # Filter by processes (only those with coordinates)
        if 'prc' in df.columns and filter_selections['processes']:
            df = df[df['prc'].isin(filter_selections['processes'])]
        
        return df
    
    def _render_map_and_summary(self, capacity_data: pd.DataFrame, filter_selections: dict):
        """
        Render the map and summary statistics
        
        Args:
            capacity_data: Filtered capacity dataframe
            filter_selections: Dictionary with filter selections
        """
        # Create two columns - map on left, stats on right
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader(f"Capacity Map - {filter_selections['year']}")
            
            # Build map
            map_obj = self.map_builder.create_base_map()
            map_obj = self.map_builder.add_capacity_markers(
                map_obj, 
                capacity_data, 
                filter_selections['year']
            )
            
            # Display map
            st_folium(
                map_obj, 
                width=None,  # Use full column width
                height=600,
                returned_objects=[]
            )
        
        with col2:
            self._render_summary_statistics(capacity_data, filter_selections)
    
    def _render_summary_statistics(self, capacity_data: pd.DataFrame, filter_selections: dict):
        """
        Render summary statistics panel
        
        Args:
            capacity_data: Filtered capacity dataframe
            filter_selections: Dictionary with filter selections
        """
        st.subheader("Summary")
        
        # Total capacity
        total_capacity = capacity_data['value'].sum()
        avg_capacity = capacity_data['value'].mean()
        num_facilities = len(capacity_data)
        
        # Display metrics
        st.metric("Total Capacity", f"{total_capacity:.2f} MW")
        st.metric("Facilities", num_facilities)
        st.metric("Avg Capacity", f"{avg_capacity:.2f} MW")
        
        st.divider()
        
        # Capacity by facility type
        st.markdown("**By Facility Type:**")
        type_summary = []
        for prc in capacity_data['prc'].unique():
            if prc in self.prc_coords:
                facility_type = self.prc_coords[prc].get('type', 'unknown')
                capacity = capacity_data[capacity_data['prc'] == prc]['value'].sum()
                type_summary.append({'Type': facility_type, 'Capacity (MW)': capacity})
        
        if type_summary:
            type_df = pd.DataFrame(type_summary)
            type_grouped = type_df.groupby('Type')['Capacity (MW)'].sum().sort_values(ascending=False)
            for ftype, cap in type_grouped.items():
                st.text(f"{ftype.replace('_', ' ').title()}: {cap:.2f} MW")
        
        st.divider()
        
        # Capacity by region
        st.markdown("**By Region:**")
        if 'reg' in capacity_data.columns:
            region_summary = capacity_data.groupby('reg')['value'].sum().sort_values(ascending=False)
            for region, cap in region_summary.items():
                st.text(f"{region}: {cap:.2f} MW")
        
        # Download button
        st.divider()
        
        # Get scenario from data
        scenario = capacity_data['scen'].iloc[0] if 'scen' in capacity_data.columns else "data"
        
        csv = capacity_data.to_csv(index=False)
        st.download_button(
            label="Download Data",
            data=csv,
            file_name=f"capacity_map_{scenario}_{filter_selections['year']}.csv",
            mime="text/csv"
        )