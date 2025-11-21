"""
Folium map renderer for energy flow visualization.
"""

import folium
from folium.plugins import AntPath
from folium import Popup, IFrame
import pandas as pd
import yaml
import streamlit as st
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from geopy.geocoders import Nominatim
import time


class FlowMapRenderer:
    """Handles creation of Folium flow maps."""
    
    def __init__(self, config_dir: Path):
        """
        Initialize map renderer with configuration.
        
        Args:
            config_dir: Path to config directory with YAML files
        """
        self.config_dir = config_dir
        self.map_settings = self._load_map_settings()
        self.region_coords = self._load_region_coordinates()
        self.geocoder = Nominatim(user_agent="speedlocal_energy_map")
        self._geocode_cache = {}  # Session-level cache
    
    def _load_map_settings(self) -> dict:
        """Load map settings from YAML."""
        settings_path = self.config_dir / "map_settings.yaml"
        if not settings_path.exists():
            st.warning(f"Map settings not found at {settings_path}, using defaults")
            return self._get_default_settings()
        
        with open(settings_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _load_region_coordinates(self) -> dict:
        """Load region coordinates from YAML."""
        coords_path = self.config_dir / "region_coordinates.yaml"
        if not coords_path.exists():
            st.warning(f"Region coordinates not found at {coords_path}")
            return {'special_regions': {}}
        
        with open(coords_path, 'r') as f:
            data = yaml.safe_load(f)
            return data.get('special_regions', {})
    
    def _get_default_settings(self) -> dict:
        """Return default map settings."""
        return {
            'map_defaults': {
                'zoom_start': 8,
                'center_lat': 55.12,
                'center_lon': 14.92,
                'tiles': 'CartoDB positron'
            },
            'line_styles': {
                'max_width': 15,
                'min_width': 2,
                'pulse_color': '#0000FF',
                'base_color': '#b2b2b2',
                'delay': 1000,
                'dash_array': [1, 90]
            },
            'marker_styles': {
                'width': 10,
                'height': 10,
                'fill': 'black',
                'opacity': 0.5
            }
        }
    
    def get_region_location(self, region_name: str) -> Optional[Tuple[float, float]]:
        """
        Get coordinates for a region.
        
        Args:
            region_name: Name of the region
            
        Returns:
            Tuple of (lat, lon) or None if not found
        """
        # Check predefined coordinates
        if region_name in self.region_coords:
            coords = self.region_coords[region_name]
            return (coords['lat'], coords['lon'])
        
        # Check cache
        if region_name in self._geocode_cache:
            return self._geocode_cache[region_name]
        
        # Geocode dynamically
        try:
            st.info(f"🌐 Geocoding region: {region_name} (not in region_coordinates.yaml)")
            location = self.geocoder.geocode(region_name)
            if location:
                coords = (location.latitude, location.longitude)
                self._geocode_cache[region_name] = coords
                time.sleep(1)  # Respect rate limits
                return coords
            else:
                st.warning(f"⚠️ Could not geocode region: {region_name}")
                return None
        except Exception as e:
            st.error(f"❌ Error geocoding {region_name}: {e}")
            return None
    
    def create_flow_map(self, flow_data: pd.DataFrame) -> folium.Map:
        """
        Create Folium map with flow visualization.
        
        Args:
            flow_data: DataFrame with columns ['start', 'end', 'value']
            
        Returns:
            Folium Map object
        """
        # Get map settings
        defaults = self.map_settings['map_defaults']
        line_styles = self.map_settings['line_styles']
        marker_styles = self.map_settings['marker_styles']
        
        # Create base map
        m = folium.Map(
            location=[defaults['center_lat'], defaults['center_lon']],
            zoom_start=defaults['zoom_start'],
            tiles=defaults['tiles']
        )
        
        # Get unique regions
        regions = pd.unique(flow_data[['start', 'end']].values.ravel())
        
        # Build region location dict
        region_locations = {}
        for region in regions:
            coords = self.get_region_location(region)
            if coords:
                region_locations[region] = coords
        
        # Add markers for regions
        for region, coords in region_locations.items():
            folium.Marker(
                location=coords,
                popup=region,
                icon=folium.DivIcon(
                    html=f"""<div><svg>
                        <rect x='0' y='0' 
                              width='{marker_styles['width']}' 
                              height='{marker_styles['height']}' 
                              fill='{marker_styles['fill']}' 
                              opacity='{marker_styles['opacity']}'/>
                    </svg></div>"""
                )
            ).add_to(m)
        
        # Build bidirectional flow lookup
        flow_lookup = defaultdict(lambda: {'AtoB': 0, 'BtoA': 0})
        
        for _, row in flow_data.iterrows():
            a = row['start']
            b = row['end']
            key = tuple(sorted([a, b]))
            
            if a < b:
                flow_lookup[key]['A'] = a
                flow_lookup[key]['B'] = b
                flow_lookup[key]['AtoB'] += row['value']
            else:
                flow_lookup[key]['A'] = b
                flow_lookup[key]['B'] = a
                flow_lookup[key]['BtoA'] += row['value']
        
        # Calculate line widths
        max_value = flow_data['value'].max()
        min_value = flow_data['value'].min()
        
        if max_value == min_value:
            # All values are the same
            width_scale = lambda val: line_styles['max_width']
        else:
            # Linear scaling
            width_scale = lambda val: (
                (line_styles['max_width'] - line_styles['min_width']) * 
                (val / max_value) + line_styles['min_width']
            )
        
        # Add flow lines
        for key, val in flow_lookup.items():
            a, b = val['A'], val['B']
            a_to_b = val['AtoB']
            b_to_a = val['BtoA']
            
            # Get coordinates
            if a not in region_locations or b not in region_locations:
                continue
            
            start_coords = region_locations[a]
            end_coords = region_locations[b]
            
            # Create popup
            popup_html = f"""
                <div style='font-size:14px; line-height:1.6; width:150px;'>
                    <strong>{a} → {b}</strong>: {round(a_to_b, 1)} PJ<br>
                    <strong>{b} → {a}</strong>: {round(b_to_a, 1)} PJ
                </div>
            """
            
            # A → B flow
            if a_to_b > 0:
                AntPath(
                    locations=[start_coords, end_coords],
                    weight=width_scale(a_to_b),
                    pulse_color=line_styles['pulse_color'],
                    color=line_styles['base_color'],
                    delay=line_styles['delay'],
                    dash_array=line_styles['dash_array'],
                    popup=popup_html
                ).add_to(m)
            
            # B → A flow
            if b_to_a > 0:
                AntPath(
                    locations=[end_coords, start_coords],
                    weight=width_scale(b_to_a),
                    pulse_color=line_styles['pulse_color'],
                    color=line_styles['base_color'],
                    delay=line_styles['delay'],
                    dash_array=line_styles['dash_array'],
                    popup=popup_html
                ).add_to(m)
        
        return m