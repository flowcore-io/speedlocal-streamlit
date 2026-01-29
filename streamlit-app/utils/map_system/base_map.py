"""
Base map rendering system for all map visualizations.
"""

import folium
import yaml
import pandas as pd
import geopandas as gpd
import streamlit as st
from pathlib import Path
from typing import Dict, List, Any, Optional


class BaseMapRenderer:
    """
    Base class for creating Folium maps with configurable layers.
    
    Usage:
        renderer = BaseMapRenderer(config)
        renderer.add_layer(CapacityLayer(...))
        renderer.add_layer(FlowLayer(...))
        
        base_map = renderer.create_base_map()
        final_map = renderer.render(base_map)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize map renderer with configuration.
        
        Args:
            config: Configuration dictionary from YAML
        """
        self.config = config
        self.layers: List['MapLayer'] = []
    
    def create_base_map(self) -> folium.Map:
        """
        Create base Folium map with default view settings.
        
        Returns:
            Folium Map object
        """
        view_config = self.config.get('default_view', {})
        
        return folium.Map(
            location=[
                view_config.get('center_lat', 59.5),
                view_config.get('center_lon', 13.0)
            ],
            zoom_start=view_config.get('zoom_start', 5),
            tiles=view_config.get('tiles', 'OpenStreetMap')
        )
    
    def add_layer(self, layer: 'MapLayer') -> None:
        """
        Add a visualization layer to the map.
        
        Args:
            layer: MapLayer instance (CapacityLayer, FlowLayer, etc.)
        """
        self.layers.append(layer)
    
    def render(self, map_obj: folium.Map) -> folium.Map:
        """
        Render all layers onto the map.
        
        Args:
            map_obj: Base Folium map object
            
        Returns:
            Map with all layers rendered
        """
        # Render each layer
        for layer in self.layers:
            map_obj = layer.render(map_obj)
        
        # Add layer control if configured
        layers_config = self.config.get('layers', {})
        if layers_config.get('show_control', True):
            folium.LayerControl(
                collapsed=layers_config.get('collapsed', True),
                position=layers_config.get('position', 'topright')
            ).add_to(map_obj)
        
        return map_obj
    
    @staticmethod
    def load_config(config_path: Path) -> Dict[str, Any]:
        """
        Load YAML configuration file.
        
        Args:
            config_path: Path to YAML config file
            
        Returns:
            Configuration dictionary
        """
        try:
            with open(config_path) as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return {}
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}

    @staticmethod
    def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge override config into base config (deep merge).
        
        Override values replace base values at all nesting levels.
        
        Args:
            base_config: Base configuration dictionary
            override_config: Override configuration dictionary
            
        Returns:
            Merged configuration dictionary
        
        Example:
            base = {'default_view': {'center_lat': 59.5, 'zoom_start': 5}}
            override = {'default_view': {'center_lat': 55.0}}
            result = {'default_view': {'center_lat': 55.0, 'zoom_start': 5}}
        """
        import copy
        merged = copy.deepcopy(base_config)
        
        def deep_merge(base: dict, override: dict) -> dict:
            """Recursively merge override into base."""
            for key, value in override.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    # Recursively merge nested dicts
                    base[key] = deep_merge(base[key], value)
                else:
                    # Override value
                    base[key] = value
            return base
        
        return deep_merge(merged, override_config)

    @staticmethod
    def load_config_with_override(
        base_config_path: Path,
        module_config_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Load configuration with optional module-specific override.
        
        Args:
            base_config_path: Path to base config (utils/map_system/config.yaml)
            module_config_path: Optional path to module config (modules/.../map_settings.yaml)
            
        Returns:
            Merged configuration dictionary
        """
        # Load base config
        base_config = BaseMapRenderer.load_config(base_config_path)
        
        # If no override, return base
        if module_config_path is None or not module_config_path.exists():
            return base_config
        
        # Load and merge override
        module_config = BaseMapRenderer.load_config(module_config_path)
        return BaseMapRenderer.merge_configs(base_config, module_config)

    @staticmethod
    def load_coordinates_from_csv(
        csv_path: Path,
        key_column: str = 'REGION',
        sep: str = ',',
        decimal: str = '.',
        show_stats: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """
        Load coordinates from CSV with full EPSG and geometry support.
        
        Supports both point coordinates (X, Y) and WKT geometries (polygons, multipolygons).
        Handles coordinate reference system conversion to EPSG:4326 (WGS84 lat/lon).
        
        Args:
            csv_path: Path to CSV file
            key_column: Column name for unique identifiers (e.g., 'REGION' or 'PRC')
            sep: CSV separator (default ',', use ';' for European format)
            decimal: Decimal separator (default '.', use ',' for European format)
            show_stats: Display loading statistics in Streamlit sidebar
        
        Returns:
            Dictionary mapping key -> coordinate data:
            {
                'HASLE': {
                    'lat': 55.183333,      # Latitude in WGS84
                    'lon': 14.705,         # Longitude in WGS84
                    'geometry': <Point>,   # Shapely geometry object
                    'geometry_type': 'point',  # 'point', 'polygon', or 'other'
                    'epsg': 4326          # Original EPSG code
                }
            }
        
        CSV Format:
            Required columns: {key_column}, X, Y, WKT, EPSG
            - X, Y: Point coordinates in the EPSG system specified
            - WKT: Well-Known Text geometry (POINT, POLYGON, MULTIPOLYGON, etc.)
            - EPSG: Coordinate reference system code
            
        Logic:
            - If X, Y provided (non-zero): Uses those as coordinates
            - If X, Y blank/zero but WKT provided: Extracts from WKT geometry
            - Converts all coordinates to EPSG:4326 (WGS84 lat/lon)
            - For polygons: Uses centroid as lat/lon for marker placement
        
        Error Handling:
            - Missing CSV file: Returns empty dict with warning
            - Missing required columns: Returns empty dict with error
            - WKT parse failure: Skips row with warning
            - Missing coordinates: Skips row with warning
        """
        # Check if file exists
        if not csv_path.exists():
            if show_stats:
                st.sidebar.error(f"Coordinate CSV not found: {csv_path}")
            return {}
        
        try:
            # Load CSV with specified format
            df = pd.read_csv(csv_path, sep=sep, decimal=decimal)
            
            # Validate required columns
            required_cols = [key_column, 'X', 'Y', 'WKT', 'EPSG']
            if not all(col in df.columns for col in required_cols):
                if show_stats:
                    st.sidebar.error(f"CSV missing required columns: {required_cols}")
                return {}
            
            # Initialize dictionary
            coords_dict = {}
            unmapped_count = 0
            
            # Group by EPSG for batch processing
            for epsg, group in df.groupby('EPSG'):
                # Separate points and polygons
                # Check if WKT contains actual geometry keywords (not just "0")
                has_wkt = (
                    group['WKT'].notna() & 
                    (group['WKT'].astype(str).str.contains('POLYGON|POINT|LINESTRING', case=False, na=False))
                )
                has_xy = (group['X'] != 0) | (group['Y'] != 0)

                # Process WKT geometries (polygons/multipolygons/points)
                wkt_group = group[has_wkt].copy()
                if not wkt_group.empty:
                    try:
                        # Clean WKT strings: remove "0 " prefix if present
                        # (e.g., "0 MULTIPOLYGON" -> "MULTIPOLYGON")
                        wkt_group['WKT_CLEAN'] = (
                            wkt_group['WKT']
                            .astype(str)
                            .str.strip()
                            .str.replace(r'^0\s+', '', regex=True)
                        )
                        
                        # Create GeoDataFrame from WKT
                        gdf_wkt = gpd.GeoDataFrame(
                            wkt_group,
                            geometry=gpd.GeoSeries.from_wkt(wkt_group['WKT_CLEAN']),
                            crs=f"EPSG:{epsg}"
                        )
                        
                        # Convert to WGS84 (EPSG:4326) if needed
                        if gdf_wkt.crs.to_epsg() != 4326:
                            gdf_wkt = gdf_wkt.to_crs(epsg=4326)
                        
                        # Get centroid for display location (important for polygons)
                        gdf_wkt['centroid'] = gdf_wkt.geometry.centroid
                        gdf_wkt['lat'] = gdf_wkt['centroid'].y
                        gdf_wkt['lon'] = gdf_wkt['centroid'].x
                        
                        # Store WKT geometries
                        for _, row in gdf_wkt.iterrows():
                            # Detect geometry type
                            geom = row['geometry']
                            if geom.geom_type in ['Polygon', 'MultiPolygon']:
                                geom_type = 'polygon'
                            elif geom.geom_type in ['Point', 'MultiPoint']:
                                geom_type = 'point'
                            else:
                                geom_type = 'other'  # LineString, etc.
                            
                            coords_dict[row[key_column]] = {
                                'lat': row['lat'],
                                'lon': row['lon'],
                                'geometry_type': geom_type,
                                'geometry': geom,
                                'epsg': epsg
                            }
                    
                    except Exception as e:
                        if show_stats:
                            st.sidebar.warning(f"Error processing WKT for EPSG {epsg}: {e}")
                
                # Process point geometries from X, Y coordinates
                point_group = group[~has_wkt & has_xy].copy()
                if not point_group.empty:
                    try:
                        # Create GeoDataFrame from X, Y
                        gdf_points = gpd.GeoDataFrame(
                            point_group,
                            geometry=gpd.points_from_xy(point_group['X'], point_group['Y']),
                            crs=f"EPSG:{epsg}"
                        )
                        
                        # Convert to WGS84 (EPSG:4326) if needed
                        if gdf_points.crs.to_epsg() != 4326:
                            gdf_points = gdf_points.to_crs(epsg=4326)
                        
                        # Extract lat/lon from converted geometry
                        gdf_points['lat'] = gdf_points.geometry.y
                        gdf_points['lon'] = gdf_points.geometry.x
                        
                        # Store point geometries
                        for _, row in gdf_points.iterrows():
                            coords_dict[row[key_column]] = {
                                'lat': row['lat'],
                                'lon': row['lon'],
                                'geometry_type': 'point',
                                'geometry': row['geometry'],
                                'epsg': epsg
                            }
                    
                    except Exception as e:
                        if show_stats:
                            st.sidebar.warning(f"Error processing points for EPSG {epsg}: {e}")
                
                # Count unmapped (no WKT and X=0, Y=0)
                unmapped_count += len(group[~has_wkt & ~has_xy])
            
            # Display statistics
            if show_stats:
                if unmapped_count > 0:
                    st.sidebar.info(f"ℹ️ {unmapped_count} entries skipped (no coordinates)")
                
                # Count by geometry type
                point_count = sum(
                    1 for v in coords_dict.values() 
                    if v.get('geometry_type') == 'point'
                )
                polygon_count = sum(
                    1 for v in coords_dict.values() 
                    if v.get('geometry_type') == 'polygon'
                )
                
                st.sidebar.success(f"✓ Loaded {point_count} points, {polygon_count} polygons")
            
            return coords_dict
            
        except Exception as e:
            if show_stats:
                st.sidebar.error(f"Error loading coordinates from CSV: {e}")
            return {}