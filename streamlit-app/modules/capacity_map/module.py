"""
Capacity Map module for visualizing process capacities on a geographic map.
"""

import streamlit as st
from streamlit_folium import st_folium

import pandas as pd
import geopandas as gpd
from pathlib import Path
from typing import Optional, Dict, List, Any

from modules.base_module import BaseVisualizationModule
from utils.map_system.base_map import BaseMapRenderer
from utils.map_system.layers import CapacityLayer


class CapacityMapModule(BaseVisualizationModule):
    """Capacity Map visualization module"""
    
    def __init__(self):
        """Initialize the Capacity Map module."""
        super().__init__(
            name="Capacity Map",
            description="Visualize process capacities on an interactive geographic map",
            order=4,
            enabled=True
        )
        
        # Paths
        self.config_path = Path(__file__).parent / "config"
        base_config_path = Path(__file__).parent.parent.parent / "utils" / "map_system" / "config.yaml"
        module_config_path = self.config_path / "map_settings.yaml"
        
        # Load config with override
        self.map_config = BaseMapRenderer.load_config_with_override(
            base_config_path=base_config_path,
            module_config_path=module_config_path
        )
    
    def get_required_tables(self) -> list:
        """Get list of required database tables/views."""
        return ["capacity_map"]
    
    def get_config(self) -> Dict[str, Any]:
        """Get module configuration."""
        return {
            "apply_global_filters": True,
            "apply_unit_conversion": True,
            "show_module_filters": False,
            "filterable_columns": ['year', 'prc', 'reg'],
            "default_columns": []
        }

    
    def _load_prc_coordinates_from_csv(self, table_dfs: Dict[str, pd.DataFrame]) -> dict:
        csv_path = self.config_path / "prc_coordinates.csv"
        
        # Use base loader with Danish CSV format
        prc_coords = BaseMapRenderer.load_coordinates_from_csv(
            csv_path=csv_path,
            key_column='PRC',
            sep=';',          # Semicolon separator
            decimal='.',      # dot decimal
            show_stats=True
        )
        
        if not prc_coords:
            return {}
        
        # Enrich with database metadata (method unchanged)
        prc_coords = self._enrich_with_database_metadata(prc_coords, table_dfs)
        
        return prc_coords
            

    def _enrich_with_database_metadata(
            self, 
            prc_coords_dict: dict,
            table_dfs: Dict[str, pd.DataFrame]
        ) -> dict:
        """
        Enrich coordinate dictionary with metadata from database.
        
        Args:
            prc_coords_dict: Dictionary with PRC -> {lat, lon, ...}
            
        Returns:
            Enhanced dictionary with type, region, display_name added
        """
        
        if 'capacity_map' not in table_dfs:
            st.warning("capacity_map table not available for metadata enrichment")
            for prc in prc_coords_dict:
                prc_coords_dict[prc].update({
                    'type': 'default',
                    'region': 'Unknown',
                    'display_name': prc
                })
            return prc_coords_dict
        
        df = table_dfs['capacity_map']
        
        # Create lookup for each PRC
        for prc in list(prc_coords_dict.keys()):
            prc_data = df[df['prc'] == prc]
            
            if not prc_data.empty:
                row = prc_data.iloc[0]
                
                # Extract metadata
                techgroup = row.get('techgroup', 'default')
                regfrom = row.get('regfrom', 'Unknown')
                
                # Get display name from label
                if 'label' in row and pd.notna(row['label']):
                    label_text = str(row['label'])
                    words = label_text.split()
                    display_name = ' '.join(words[:2]) if len(words) >= 2 else label_text
                else:
                    display_name = prc
                
                # Update dictionary
                prc_coords_dict[prc].update({
                    'type': techgroup if pd.notna(techgroup) else 'default',
                    'region': regfrom if pd.notna(regfrom) else 'Unknown',
                    'display_name': display_name
                })
            else:
                prc_coords_dict[prc].update({
                    'type': 'default',
                    'region': 'Unknown',
                    'display_name': prc
                })
        
        return prc_coords_dict
    def _load_and_prepare_data(self, table_dfs: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Load and prepare capacity data.
        
        This runs BEFORE filtering and unit conversion.
        
        Args:
            table_dfs: All available tables
            
        Returns:
            Raw capacity DataFrame with descriptions applied
        """
        # Get capacity data
        df = table_dfs.get("capacity_map", pd.DataFrame())
        
        if df.empty:
            return df
        
        # Apply description mappings
        desc_mapping = self._get_desc_mapping()
        if desc_mapping:
            df = self._apply_descriptions(
                df,
                ['sector', 'prc', 'comgroup', 'techgroup'],
                desc_mapping
            )
        
        # Load coordinates (needed for filtering and rendering later)
        if not hasattr(self, 'prc_coords'):
            self.prc_coords = self._load_prc_coordinates_from_csv(table_dfs)
        
        return df
    # def render(
    #     self,
    #     table_dfs: Dict[str, pd.DataFrame],
    #     filters: Dict[str, Any]
    # ) -> None:
    #     """
    #     Main render method - entry point for the module
        
    #     Args:
    #         table_dfs: Dictionary of dataframes loaded from mapping_db_views.csv
    #         filters: Dictionary with filter selections (scenario, etc.)
    #     """
    #     self.prc_coords = self._load_prc_coordinates_from_csv(table_dfs)
    #     # self.map_builder.prc_coordinates = self.prc_coords 

    #     st.title("Capacity Map")
    #     st.markdown("""
    #     Visualize process capacities on an interactive geographic map. 
    #     Each marker represents a facility with technical capacity (tcap) data.
    #     """)
        
    #     # Validate data availability
    #     if not self.validate_data(table_dfs):
    #         self.show_error("Capacity map data table not available.")
    #         with st.expander("Setup Instructions"):
    #             st.markdown("""
    #             Add this line to `inputs/mapping_db_views.csv`:
    #             ```
    #             capacity_map,prc,,,,,,,,capacity,tcap,,,,,,,,,,
    #             ```
    #             Then restart the application.
    #             """)
    #         return
        
    #     # Get raw data from table_dfs
    #     df_raw = table_dfs.get("capacity_map")
        
    #     if df_raw is None or df_raw.empty:
    #         self.show_warning("No capacity data available.")
    #         return
        
    #     # Apply global filters (scenario)
    #     df_filtered = self._apply_filters(df_raw, filters)
        
    #     if df_filtered.empty:
    #         self.show_warning("No data available after applying filters.")
    #         return
        
    #     # Render page filters and get selections
    #     filter_selections = self._render_page_filters(df_filtered)
        
    #     if filter_selections is None:
    #         st.info("Configure filters in the sidebar to display the map")
    #         return
        
    #     # Apply module-specific filters
    #     capacity_data = self._apply_module_filters(df_filtered, filter_selections)
        
    #     # Check for data after filtering
    #     if capacity_data.empty:
    #         self.show_warning("No capacity data matches the selected filters.")
    #         return
        
    #     # Check for unmapped processes
    #     # unmapped = self.map_builder.get_unmapped_processes(capacity_data)
    #     # if unmapped:
    #     #     with st.expander(f"{len(unmapped)} processes without coordinate mappings", expanded=False):
    #     #         st.warning(
    #     #             f"The following {len(unmapped)} processes have capacity data but no coordinates defined:\n\n"
    #     #             f"{', '.join(unmapped)}"
    #     #         )
        
    #     # Display map and summary
    #     self._render_map_and_summary(capacity_data, filter_selections)
    def _render_visualization(self, df: pd.DataFrame, filters: Dict[str, Any]) -> None:
        """
        Render the capacity map visualization.
        
        Data is already:
        - Filtered by global filters (scenario)
        - Unit-converted
        
        Args:
            df: Filtered and converted capacity DataFrame
            filters: Active filters (for reference)
        """
        st.header("Capacity Map")
        
        # Render filter controls and get selections
        filter_selections = self._render_page_filters(df)
        
        if not filter_selections:
            return
        
        # Apply module-specific filters (year, process, region, type)
        capacity_data = self._apply_module_filters(df, filter_selections)
        
        if capacity_data.empty:
            st.warning("No capacity data available for selected filters")
            return
        
        # Render map and summary
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
        
        # Create filter columns
        col1, col2, col3 = st.columns(3)

        with col1:
            # Scenario filter - USE df_raw here
            available_scenarios = sorted(df_raw['scen'].unique())  # ✅ Changed to df_raw
            selected_scenario = st.selectbox(
                "Scenario",
                options=available_scenarios,
                index=0,
                key="capacity_map_scenario"
            )
        
        with col2:
            # Year filter - USE df_raw here
            available_years = sorted(df_raw['year'].unique())  # ✅ Changed to df_raw
            selected_year = st.selectbox(
                "Year",
                options=available_years,
                index=0,
                key="capacity_map_year"
            )
        
        # NOW create df_filtered after getting the selections
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
            
            # Create map renderer
            map_renderer = BaseMapRenderer(self.map_config)

            # Create capacity layer
            capacity_layer = CapacityLayer(
                name="Facilities",
                config=self.map_config.get('capacity_layer', {}),
                prc_coords=self.prc_coords,
                capacity_data=capacity_data,
                year=filter_selections['year']
            )

            # Add layer and render
            map_renderer.add_layer(capacity_layer)
            base_map = map_renderer.create_base_map()
            final_map = map_renderer.render(base_map)

            # Display map
            st_folium(
                final_map,
                width=None,
                height=600,
                returned_objects=[]
            )
        
        with col2:
            self._render_summary_statistics(capacity_data, filter_selections)
    
    def _render_summary_statistics(self, capacity_data: pd.DataFrame, filter_selections: dict):
        """Render summary statistics panel."""
        st.subheader("Summary")
        
        # Get unit label from converted data
        unit_label = self._get_unit_label(capacity_data)  # ← Use helper instead of hardcoded "MW"
        
        # Total capacity
        total_capacity = capacity_data['value'].sum()
        num_facilities = len(capacity_data)
        
        # Display metrics
        st.metric("Total Capacity", f"{total_capacity:.2f} {unit_label}")  # ← Use dynamic unit
        st.metric("Facilities", num_facilities)
        
        # ... rest stays the same, also update other hardcoded "MW" references ...
        
        st.divider()
        
        # Capacity by facility type
        st.markdown("**By Facility Type:**")
        type_summary = []
        for prc in capacity_data['prc'].unique():
            if prc in self.prc_coords:
                facility_type = self.prc_coords[prc].get('type', 'unknown')
                capacity = capacity_data[capacity_data['prc'] == prc]['value'].sum()
                type_summary.append({'Type': facility_type, 'Capacity': capacity})
        
        if type_summary:
            type_df = pd.DataFrame(type_summary)
            type_grouped = type_df.groupby('Type')['Capacity'].sum().sort_values(ascending=False)
            
            # Get description mapping
            desc_mapping = self._get_desc_mapping()
            
            for ftype, cap in type_grouped.items():
                # Use description if available, otherwise use formatted type name
                if desc_mapping and 'techgroup' in desc_mapping:
                    display_name = desc_mapping['techgroup'].get(ftype, ftype.replace('_', ' ').title())
                else:
                    display_name = ftype.replace('_', ' ').title()
                
                st.text(f"{display_name}: {cap:.2f} {unit_label}")            
        
        st.divider()
        
        # Capacity by region
        st.markdown("**By Region:**")
        if 'regfrom' in capacity_data.columns:
            region_summary = capacity_data.groupby('regfrom')['value'].sum().sort_values(ascending=False)
            for region, cap in region_summary.items():
                st.text(f"{region}: {cap:.2f} {unit_label}")
        
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