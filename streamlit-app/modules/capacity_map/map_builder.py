"""
Map Building Utilities
Handles creation of Folium maps with capacity markers
"""

import folium
from folium import plugins
import pandas as pd
from typing import Dict, Any, Optional


class MapBuilder:
    """Builds interactive Folium maps with capacity data"""
    
    def __init__(self, map_settings: Dict[str, Any], prc_coordinates: Dict[str, Any]):
        """
        Initialize map builder with configuration
        
        Args:
            map_settings: Map settings from config
            prc_coordinates: Process coordinates from config
        """
        self.map_settings = map_settings
        self.prc_coordinates = prc_coordinates
    
    def create_base_map(self) -> folium.Map:
        """
        Create base Folium map with default view settings
        
        Returns:
            Folium Map object
        """
        default_view = self.map_settings.get('default_view', {})
        
        m = folium.Map(
            location=[
                default_view.get('center_lat', 59.5),
                default_view.get('center_lon', 13.0)
            ],
            zoom_start=default_view.get('zoom_start', 5),
            tiles=default_view.get('tiles', 'OpenStreetMap')
        )
        
        return m
    
    def add_capacity_markers(
        self,
        map_obj: folium.Map,
        capacity_data: pd.DataFrame,
        year: int
    ) -> folium.Map:
        """
        Add capacity markers to the map
        
        Args:
            map_obj: Folium Map object
            capacity_data: DataFrame with capacity data
            year: Year being displayed
            
        Returns:
            Updated Folium Map object
        """
        if capacity_data.empty:
            return map_obj
        
        # Create feature groups for different facility types
        feature_groups = {}
        marker_styles = self.map_settings.get('marker_styles', {})
        
        for _, row in capacity_data.iterrows():
            prc = row['prc']
            
            # Skip if no coordinates defined for this process
            if prc not in self.prc_coordinates:
                continue
            
            coord_info = self.prc_coordinates[prc]
            lat = coord_info.get('lat')
            lon = coord_info.get('lon')
            facility_type = coord_info.get('type', 'default')
            display_name = coord_info.get('display_name', prc)
            region = coord_info.get('region', row.get('reg', 'Unknown'))
            
            # Skip if coordinates are missing
            if lat is None or lon is None:
                continue
            
            # Get marker style for this facility type
            style = marker_styles.get(facility_type, marker_styles.get('default', {}))
            
            # Create feature group if it doesn't exist
            if facility_type not in feature_groups:
                group_name = style.get('description', facility_type.replace('_', ' ').title())
                feature_groups[facility_type] = folium.FeatureGroup(name=group_name)
            
            # Create popup content
            popup_html = self._create_popup_html(
                display_name=display_name,
                prc=prc,
                capacity=row['value'],
                unit=row.get('unit', 'MW'),
                year=year,
                region=region,
                lat=lat,
                lon=lon
            )
            
            # Create marker
            marker = folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=self.map_settings.get('popup', {}).get('max_width', 400)),
                tooltip=f"{display_name}: {row['value']:.2f} {row.get('unit', 'MW')}",
                icon=folium.Icon(
                    color=style.get('color', 'gray'),
                    icon=style.get('icon', 'circle'),
                    prefix=style.get('prefix', 'fa')
                )
            )
            
            # Add marker to appropriate feature group
            marker.add_to(feature_groups[facility_type])
        
        # Add all feature groups to map
        for group in feature_groups.values():
            group.add_to(map_obj)
        
        # Add layer control if configured
        if self.map_settings.get('layers', {}).get('show_control', True):
            folium.LayerControl(
                collapsed=self.map_settings.get('layers', {}).get('collapsed', True),
                position=self.map_settings.get('layers', {}).get('position', 'topright')
            ).add_to(map_obj)
        
        return map_obj
    
    def _create_popup_html(
        self,
        display_name: str,
        prc: str,
        capacity: float,
        unit: str,
        year: int,
        region: str,
        lat: float,
        lon: float
    ) -> str:
        """
        Create HTML content for marker popup
        
        Args:
            display_name: Facility display name
            prc: Process ID
            capacity: Capacity value
            unit: Unit of measurement
            year: Year
            region: Region code
            lat: Latitude
            lon: Longitude
            
        Returns:
            HTML string for popup
        """
        popup_config = self.map_settings.get('popup', {})
        
        html = f"""
        <div style="font-family: Arial, sans-serif; min-width: 200px;">
            <h4 style="margin: 0 0 10px 0; color: #2c3e50;">{display_name}</h4>
            <hr style="margin: 5px 0;">
        """
        
        if popup_config.get('show_process_name', True):
            html += f"<p style='margin: 5px 0;'><b>Process:</b> {prc}</p>"
        
        if popup_config.get('show_capacity', True):
            html += f"<p style='margin: 5px 0;'><b>Capacity:</b> {capacity:.2f} {unit}</p>"
        
        if popup_config.get('show_year', True):
            html += f"<p style='margin: 5px 0;'><b>Year:</b> {year}</p>"
        
        if popup_config.get('show_region', True):
            html += f"<p style='margin: 5px 0;'><b>Region:</b> {region}</p>"
        
        if popup_config.get('show_coordinates', True):
            html += f"<p style='margin: 5px 0;'><b>Location:</b> {lat:.4f}°N, {lon:.4f}°E</p>"
        
        html += "</div>"
        
        return html
    
    def get_unmapped_processes(self, capacity_data: pd.DataFrame) -> list:
        """
        Get list of processes that don't have coordinate mappings
        
        Args:
            capacity_data: DataFrame with capacity data
            
        Returns:
            List of unmapped process IDs
        """
        all_processes = capacity_data['prc'].unique().tolist()
        unmapped = [prc for prc in all_processes if prc not in self.prc_coordinates]
        return unmapped