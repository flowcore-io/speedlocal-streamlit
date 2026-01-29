"""
Map layer classes for different visualization types.
"""

from abc import ABC, abstractmethod
import folium
import pandas as pd
from typing import Dict, Any
from folium.plugins import AntPath
from collections import defaultdict
from geopy.geocoders import Nominatim
import time


class MapLayer(ABC):
    """
    Abstract base class for map layers.
    
    Each layer type (capacity, flow, etc.) inherits from this.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize map layer.
        
        Args:
            name: Display name for this layer
            config: Configuration dictionary for this layer
        """
        self.name = name
        self.config = config
    
    @abstractmethod
    def render(self, map_obj: folium.Map) -> folium.Map:
        """
        Render this layer onto the map.
        
        Args:
            map_obj: Folium Map object
            
        Returns:
            Map with layer added
        """
        pass

class CapacityLayer(MapLayer):
    """
    Map layer for capacity markers and polygons.
    
    Shows facilities with capacity data as markers,
    and area-based facilities as polygons.
    """
    
    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
        prc_coords: Dict[str, Any],
        capacity_data: pd.DataFrame,
        year: int
    ):
        """
        Initialize capacity layer.
        
        Args:
            name: Display name for this layer
            config: Configuration for capacity layer
            prc_coords: Dictionary of process coordinates
            capacity_data: DataFrame with capacity data
            year: Year being displayed
        """
        super().__init__(name, config)
        self.prc_coords = prc_coords
        self.capacity_data = capacity_data
        self.year = year
    
    def render(self, map_obj: folium.Map) -> folium.Map:
        """Render capacity markers and polygons onto map."""
        
        if self.capacity_data.empty:
            return map_obj
        
        # Create feature groups for different facility types
        feature_groups = {}
        marker_styles = self.config.get('marker_styles', {})
        
        for _, row in self.capacity_data.iterrows():
            prc = row['prc']
            
            # Skip if no coordinates defined
            if prc not in self.prc_coords:
                continue
            
            coord_info = self.prc_coords[prc]
            lat = coord_info.get('lat')
            lon = coord_info.get('lon')
            facility_type = coord_info.get('type', 'default')
            display_name = coord_info.get('display_name', prc)
            region = coord_info.get('region', row.get('regfrom', 'Unknown'))
            
            # Skip if coordinates missing
            if lat is None or lon is None:
                continue
            
            # Get marker style
            style = marker_styles.get(facility_type, marker_styles.get('default', {}))
            
            # Create feature group if needed
            if facility_type not in feature_groups:
                group_name = style.get('description', facility_type.replace('_', ' ').title())
                feature_groups[facility_type] = folium.FeatureGroup(name=f"Capacity: {group_name}")
            
            # Add marker
            self._add_marker(
                feature_groups[facility_type],
                coord_info,
                row,
                style,
                display_name,
                region
            )
            
            # Add polygon if exists
            if coord_info.get('geometry_type') == 'polygon':
                self._add_polygon(
                    feature_groups[facility_type],
                    coord_info,
                    style,
                    display_name
                )
        
        # Add all feature groups to map
        for group in feature_groups.values():
            group.add_to(map_obj)
        
        return map_obj
    
    def _add_marker(self, group, coord_info, data_row, style, display_name, region):
        """Add a capacity marker."""
        popup_html = self._create_popup_html(
            display_name=display_name,
            prc=data_row['prc'],
            capacity=data_row['value'],
            unit=data_row.get('unit', 'MW'),
            year=self.year,
            region=region,
            lat=coord_info['lat'],
            lon=coord_info['lon']
        )
        
        marker = folium.Marker(
            location=[coord_info['lat'], coord_info['lon']],
            popup=folium.Popup(
                popup_html,
                max_width=self.config.get('popup', {}).get('max_width', 400)
            ),
            tooltip=f"{display_name}: {data_row['value']:.2f} {data_row.get('unit', 'MW')}",
            icon=folium.Icon(
                color=style.get('color', 'gray'),
                icon=style.get('icon', 'circle'),
                prefix=style.get('prefix', 'fa')
            )
        )
        
        marker.add_to(group)
    
    def _add_polygon(self, group, coord_info, style, display_name):
        """Add a polygon shape."""
        if 'geometry' not in coord_info:
            return
        
        polygon_geojson = coord_info['geometry'].__geo_interface__
        polygon_config = self.config.get('polygon_style', {})
        
        folium.GeoJson(
            polygon_geojson,
            style_function=lambda x: {
                'fillColor': style.get('color', 'gray'),
                'color': style.get('color', 'gray'),
                'weight': polygon_config.get('weight', 2),
                'fillOpacity': polygon_config.get('fillOpacity', 0.3)
            },
            tooltip=f"{display_name} (area)"
        ).add_to(group)
    
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
        """Create HTML for marker popup."""
        popup_config = self.config.get('popup', {})
        
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


class FlowLayer(MapLayer):
    """
    Map layer for energy flow visualization.
    
    Shows bidirectional flows between regions using animated lines.
    """
    
    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
        flow_data: pd.DataFrame,
        region_coords: Dict[str, tuple]
    ):
        """
        Initialize flow layer.
        
        Args:
            name: Display name for this layer
            config: Configuration for flow layer
            flow_data: DataFrame with columns ['start', 'end', 'value', 'unit']
            region_coords: Dictionary mapping region_name -> (lat, lon)
        """
        super().__init__(name, config)
        self.flow_data = flow_data
        self.region_coords = region_coords
        self.geocoder = Nominatim(
            user_agent="speedlocal_energy_map",
            timeout = 10
            )
        self._geocode_cache = {}
        self.geocoding_messages = []
    
    def render(self, map_obj: folium.Map) -> folium.Map:
        """Render flow lines and region markers onto map."""
        
        if self.flow_data.empty:
            return map_obj
        
        # Get unique regions from flow data
        regions = pd.unique(self.flow_data[['start', 'end']].values.ravel())
        
        # Build complete region location dict
        region_locations = self._build_region_locations(regions)
        
        # Create feature groups for layer control
        regions_group = folium.FeatureGroup(name="Region Markers")
        labels_group = folium.FeatureGroup(name="Region Labels")
        flows_group = folium.FeatureGroup(name="Energy Flows")
        
        # Add region markers
        self._add_region_markers(regions_group, region_locations)
        
        # Add region labels (if enabled)
        label_config = self.config.get('region_labels', {})
        if label_config.get('enabled', True):
            self._add_region_labels(labels_group, region_locations, label_config)
        
        # Add flow lines
        self._add_flow_lines(flows_group, region_locations)
        
        # Add groups to map
        regions_group.add_to(map_obj)
        if label_config.get('enabled', True):
            labels_group.add_to(map_obj)
        flows_group.add_to(map_obj)
        
        return map_obj
    
    def _build_region_locations(self, regions: list) -> Dict[str, tuple]:
        """
        Build dictionary of region locations.
        Uses predefined coords first, geocodes if needed.
        
        Args:
            regions: List of region names
            
        Returns:
            Dictionary mapping region_name -> (lat, lon)
        """
        region_locations = {}
        
        for region in regions:
            # Check predefined coordinates
            if region in self.region_coords:
                region_locations[region] = self.region_coords[region]
            else:
                # Geocode dynamically
                coords = self._geocode_region(region)
                if coords:
                    region_locations[region] = coords
        
        return region_locations
    
    def _geocode_region(self, region_name: str) -> tuple:
        """
        Geocode a region name to coordinates.
        
        Args:
            region_name: Name of region
            
        Returns:
            Tuple of (lat, lon) or None if not found
        """
        # Check cache
        if region_name in self._geocode_cache:
            return self._geocode_cache[region_name]
        
        # Geocode
        try:
            # Store message instead of displaying immediately
            self.geocoding_messages.append(
                f"🌍 Geocoding region: {region_name} (not in region_coordinates)"
            )
            
            location = self.geocoder.geocode(region_name)
            if location:
                coords = (location.latitude, location.longitude)
                self._geocode_cache[region_name] = coords
                time.sleep(1)
                return coords
            else:
                self.geocoding_messages.append(
                    f"⚠️ Could not geocode region: {region_name}"
                )
                return None
        except Exception as e:
            self.geocoding_messages.append(
                f"❌ Error geocoding {region_name}: {e}"
            )
            return None
    
    def _add_region_markers(self, group, region_locations: Dict[str, tuple]):
        """Add markers for each region to feature group."""
        marker_styles = self.config.get('marker_styles', {})
        
        for region, coords in region_locations.items():
            folium.Marker(
                location=coords,
                popup=region,
                icon=folium.DivIcon(
                    html=f"""<div><svg>
                        <rect x='0' y='0' 
                            width='{marker_styles.get('width', 10)}' 
                            height='{marker_styles.get('height', 10)}' 
                            fill='{marker_styles.get('fill', 'black')}' 
                            opacity='{marker_styles.get('opacity', 0.5)}'/>
                    </svg></div>"""
                )
            ).add_to(group)
    def _add_region_labels(
        self, 
        group, 
        region_locations: Dict[str, tuple],
        label_config: Dict[str, Any]
    ):
        """Add text labels for each region to feature group."""
        font_size = label_config.get('font_size', '12px')
        font_weight = label_config.get('font_weight', 'bold')
        color = label_config.get('color', '#333')
        offset_y = label_config.get('offset_y', -25)
        
        for region, coords in region_locations.items():
            folium.Marker(
                location=coords,
                icon=folium.DivIcon(
                    html=f"""
                    <div style="
                        font-size: {font_size};
                        font-weight: {font_weight};
                        color: {color};
                        text-align: center;
                        white-space: nowrap;
                        margin-top: {offset_y}px;
                        text-shadow: 1px 1px 2px white, -1px -1px 2px white;
                    ">
                        {region}
                    </div>
                    """
                )
            ).add_to(group)

    def _add_flow_lines(self, group, region_locations: Dict[str, tuple]):
        """Add animated flow lines between regions."""
        line_styles = self.config.get('line_styles', {})
        
        # Get unit for display
        unit = self.flow_data['unit'].iloc[0] if 'unit' in self.flow_data.columns and not self.flow_data.empty else "PJ"
        
        # Build bidirectional flow lookup
        flow_lookup = defaultdict(lambda: {'AtoB': 0, 'BtoA': 0})
        
        for _, row in self.flow_data.iterrows():
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
        max_value = self.flow_data['value'].max()
        min_value = self.flow_data['value'].min()
        
        if max_value == min_value:
            width_scale = lambda val: line_styles.get('max_width', 15)
        else:
            width_scale = lambda val: (
                (line_styles.get('max_width', 15) - line_styles.get('min_width', 2)) * 
                (val / max_value) + line_styles.get('min_width', 2)
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
                    <strong>{a} → {b}</strong>: {round(a_to_b, 1)} {unit}<br>
                    <strong>{b} → {a}</strong>: {round(b_to_a, 1)} {unit}
                </div>
            """
            
            # A → B flow
            if a_to_b > 0:
                AntPath(
                    locations=[start_coords, end_coords],
                    weight=width_scale(a_to_b),
                    pulse_color=line_styles.get('pulse_color', '#0000FF'),
                    color=line_styles.get('base_color', '#b2b2b2'),
                    delay=line_styles.get('delay', 1000),
                    dash_array=line_styles.get('dash_array', [1, 90]),
                    popup=popup_html
                ).add_to(group)
            
            # B → A flow
            if b_to_a > 0:
                AntPath(
                    locations=[end_coords, start_coords],
                    weight=width_scale(b_to_a),
                    pulse_color=line_styles.get('pulse_color', '#0000FF'),
                    color=line_styles.get('base_color', '#b2b2b2'),
                    delay=line_styles.get('delay', 1000),
                    dash_array=line_styles.get('dash_array', [1, 90]),
                    popup=popup_html
                ).add_to(group)