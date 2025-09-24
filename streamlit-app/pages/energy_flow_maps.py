"""
Energy Flow Maps - Full functionality with lazy imports to avoid pybind11 conflicts
Displays energy flows between regions using Folium maps with flow magnitude visualization
"""

import streamlit as st
import pandas as pd
import numpy as np
from collections import defaultdict
import time
import sys
import os

# Add utils directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app', 'utils'))
from database import connect_to_db, get_unique_values, test_database_connection
from geo_settings import SPECIAL_REGIONS, MAP_CENTER, DEFAULT_ZOOM, MAP_TILE, MAX_LINE_WIDTH, MIN_LINE_WIDTH

# Initialize geocoder with lazy import
@st.cache_resource
def get_geolocator():
    from geopy.geocoders import Nominatim
    return Nominatim(user_agent="speedlocal_energy_maps")

@st.cache_data(show_spinner=False)
def load_energy_flow_data(conn, scenario, year, fuel):
    """Load and process energy flow data from database"""
    try:
        # Query to get energy flows (TB links, imports, exports)
        query = """
        WITH energy_flows AS (
            -- Get transmission flows (TB links) - only cross-regional flows
            SELECT 
                f.regfrom,
                f.regto,
                f.com as fuel,
                f.scen,
                f.year,
                SUM(f.value) as value,
                'transmission' as flow_type
            FROM timesreport_facts f
            WHERE f.prc LIKE 'TB%'
            AND f.attr = 'f_out'
            AND f.scen = ?
            AND f.year = ?
            AND f.com = ?
            AND f.value > 0
            AND f.regfrom IS NOT NULL 
            AND f.regto IS NOT NULL
            AND f.regfrom != f.regto
            GROUP BY f.regfrom, f.regto, f.com, f.scen, f.year
            
            UNION ALL
            
            -- Get import flows
            SELECT 
                f.regfrom,
                f.regto,
                f.com as fuel,
                f.scen,
                f.year,
                SUM(f.value) as value,
                'import' as flow_type
            FROM timesreport_facts f
            WHERE f.prc LIKE 'IMP%'
            AND f.topic = 'energy'
            AND f.attr = 'f_out'
            AND f.scen = ?
            AND f.year = ?
            AND f.com = ?
            AND f.value > 0
            AND f.regfrom IS NOT NULL 
            AND f.regto IS NOT NULL
            GROUP BY f.regfrom, f.regto, f.com, f.scen, f.year
            
            UNION ALL
            
            -- Get export flows
            SELECT 
                f.regto as regfrom,
                f.regfrom as regto,
                f.com as fuel,
                f.scen,
                f.year,
                SUM(f.value) as value,
                'export' as flow_type
            FROM timesreport_facts f
            WHERE f.prc LIKE 'EXP%'
            AND f.topic = 'energy'
            AND f.attr = 'f_in'
            AND f.scen = ?
            AND f.year = ?
            AND f.com = ?
            AND f.value > 0
            AND f.regfrom IS NOT NULL 
            AND f.regto IS NOT NULL
            GROUP BY f.regto, f.regfrom, f.com, f.scen, f.year
        )
        SELECT * FROM energy_flows WHERE value > 0
        """
        
        df = conn.execute(query, [scenario, year, fuel, scenario, year, fuel, scenario, year, fuel]).df()
        
        if not df.empty:
            # Clean up region names
            df['start'] = df['regfrom'].str.replace('DKB', 'BORNHOLM').str.replace('IMPEXP', 'Global Market')
            df['end'] = df['regto'].str.replace('DKB', 'BORNHOLM').str.replace('IMPEXP', 'Global Market')
            
            # Remove underscore prefixes if present
            df['start'] = df['start'].str.split('_', n=1).str[-1]
            df['end'] = df['end'].str.split('_', n=1).str[-1]
            
        return df
    
    except Exception as e:
        st.error(f"Error loading energy flow data: {str(e)}")
        return pd.DataFrame()

@st.cache_data(show_spinner=False)
def build_region_coordinates(regions):
    """Build coordinate dictionary for regions with geocoding"""
    geolocator = get_geolocator()
    coordinates = {}
    
    # Use special regions first
    for region in regions:
        if region in SPECIAL_REGIONS:
            lat, lon = SPECIAL_REGIONS[region]
            coordinates[region] = [lat, lon]
        else:
            # Try geocoding
            try:
                location = geolocator.geocode(f"{region}, Denmark")
                if location:
                    coordinates[region] = [location.latitude, location.longitude]
                else:
                    # Fallback to Bornholm area for unknown regions
                    coordinates[region] = [55.1, 14.9]
                time.sleep(0.5)  # Respect rate limits
            except Exception as e:
                st.warning(f"Could not geocode {region}: {e}")
                coordinates[region] = [55.1, 14.9]
    
    return coordinates

def create_flow_map(flow_data):
    """Create Folium map with energy flows - LAZY IMPORTS"""
    # CRITICAL: Import folium and related packages only when this function is called
    import folium
    from folium.plugins import AntPath
    
    if flow_data.empty:
        st.warning("No flow data available for the selected criteria")
        return None
    
    # Get unique regions
    all_regions = pd.concat([flow_data['start'], flow_data['end']]).unique()
    
    # Get coordinates for regions
    with st.spinner("Geocoding regions..."):
        region_coords = build_region_coordinates(all_regions)
    
    # Create base map
    m = folium.Map(location=MAP_CENTER, zoom_start=DEFAULT_ZOOM, tiles=MAP_TILE)
    
    # Add region markers
    for region, coords in region_coords.items():
        folium.Marker(
            location=coords,
            popup=f"<b>{region}</b>",
            tooltip=region,
            icon=folium.DivIcon(
                html=f"""<div style="font-size: 10px; font-weight: bold; 
                         background: rgba(255,255,255,0.7); 
                         border: 1px solid black; 
                         border-radius: 3px; 
                         padding: 2px;">{region}</div>""",
                icon_size=(len(region)*6, 20),
                icon_anchor=(len(region)*3, 10)
            )
        ).add_to(m)
    
    # Normalize flow values for line thickness
    max_flow = flow_data['value'].max()
    min_flow = flow_data['value'].min()
    
    if max_flow > min_flow:
        flow_data['line_width'] = (
            (flow_data['value'] - min_flow) / (max_flow - min_flow) * 
            (MAX_LINE_WIDTH - MIN_LINE_WIDTH) + MIN_LINE_WIDTH
        )
    else:
        flow_data['line_width'] = MAX_LINE_WIDTH
    
    # Process flows and handle bidirectional flows
    flow_lookup = defaultdict(lambda: {'AtoB': 0, 'BtoA': 0})
    
    for _, row in flow_data.iterrows():
        start, end = row['start'], row['end']
        value = row['value']
        
        # Create consistent key for both directions
        key = tuple(sorted([start, end]))
        
        if start < end:  # A to B
            flow_lookup[key]['AtoB'] += value
        else:  # B to A
            flow_lookup[key]['BtoA'] += value
    
    # Add flow lines to map
    for (region_a, region_b), flows in flow_lookup.items():
        if region_a not in region_coords or region_b not in region_coords:
            continue
            
        coord_a = region_coords[region_a]
        coord_b = region_coords[region_b]
        
        # Calculate net flow and direction
        net_flow = flows['AtoB'] - flows['BtoA']
        total_flow = flows['AtoB'] + flows['BtoA']
        
        if total_flow == 0:
            continue
        
        # Determine direction and flow magnitude
        if abs(net_flow) > total_flow * 0.1:  # Significant directional flow
            if net_flow > 0:
                # A to B flow
                start_coord, end_coord = coord_a, coord_b
                arrow_color = 'blue'
                direction_text = f"{region_a} → {region_b}"
            else:
                # B to A flow
                start_coord, end_coord = coord_b, coord_a
                arrow_color = 'red'
                direction_text = f"{region_b} → {region_a}"
            
            # Calculate line width based on total flow magnitude
            if max_flow > min_flow:
                line_width = ((abs(net_flow) - min_flow) / (max_flow - min_flow) * 
                             (MAX_LINE_WIDTH - MIN_LINE_WIDTH) + MIN_LINE_WIDTH)
            else:
                line_width = MAX_LINE_WIDTH
            
            # Add animated flow line
            AntPath(
                locations=[start_coord, end_coord],
                color=arrow_color,
                weight=max(2, line_width),
                opacity=0.7,
                dash_array=[10, 20],
                delay=1000,
                popup=folium.Popup(
                    f"""<b>{direction_text}</b><br>
                    Flow: {abs(net_flow):.2f}<br>
                    Type: {'Net Export' if net_flow > 0 else 'Net Import'}""",
                    max_width=200
                )
            ).add_to(m)
        
        else:  # Bidirectional flow
            # Add simple line for balanced flows
            folium.PolyLine(
                locations=[coord_a, coord_b],
                color='green',
                weight=3,
                opacity=0.5,
                popup=folium.Popup(
                    f"""<b>{region_a} ↔ {region_b}</b><br>
                    Bidirectional Flow<br>
                    A→B: {flows['AtoB']:.2f}<br>
                    B→A: {flows['BtoA']:.2f}""",
                    max_width=200
                )
            ).add_to(m)
    
    # Add legend
    legend_html = """
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 200px; height: 120px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <h4>Energy Flow Legend</h4>
    <p><span style="color:blue;">━━━━</span> Net Export Flow</p>
    <p><span style="color:red;">━━━━</span> Net Import Flow</p>
    <p><span style="color:green;">━━━━</span> Bidirectional Flow</p>
    <p><i>Line thickness = Flow magnitude</i></p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

def render_flow_maps():
    """Main render function for Energy Flow Maps"""
    
    # Database connection section
    st.sidebar.header("🔗 Database Connection")
    
    # Connection type selection
    connection_type = st.sidebar.radio(
        "Connection Type:",
        ["Local File", "Azure URL"],
        help="Choose whether to connect to a local DuckDB file or download from Azure blob storage"
    )
    
    if connection_type == "Local File":
        db_path = st.sidebar.text_input("Enter path to DuckDB database:", "speedlocal_times_db_bornholm.duckdb")
        is_url = False
    else:
        db_path = st.sidebar.text_input(
            "Enter Azure blob storage URL:", 
            placeholder="https://storage.blob.core.windows.net/container/database.duckdb?..."
        )
        is_url = True
        use_cache = st.sidebar.checkbox("Use local cache", value=True, help="Cache downloaded database locally")
    
    # Connect button
    if st.sidebar.button("Connect to Database"):
        if connection_type == "Azure URL":
            conn = connect_to_db(db_path, is_url=True, use_cache=use_cache)
        else:
            conn = connect_to_db(db_path, is_url=False)
        
        if conn is not None:
            test_database_connection(conn)
            st.session_state.db_connection = conn
        else:
            if 'db_connection' in st.session_state:
                del st.session_state.db_connection
    
    # Only show map options if connected
    if 'db_connection' in st.session_state:
        conn = st.session_state.db_connection
        
        try:
            # Get available data for filters
            scenarios = get_unique_values(conn, "scen")
            years = get_unique_values(conn, "year")
            fuels = get_unique_values(conn, "com")
            
            # Convert years to integers and sort
            try:
                years = sorted([int(y) for y in years if str(y).isdigit()])
            except:
                years = [2020, 2030, 2040, 2050]  # Default years
            
            if not scenarios:
                scenarios = ["DEFAULT"]
            if not fuels:
                fuels = ["ELC", "NGS", "COL"]  # Default fuels
                
            # Sidebar filters
            st.sidebar.header("🎛️ Flow Map Controls")
            
            scenario = st.sidebar.selectbox("Scenario", scenarios)
            year = st.sidebar.selectbox("Year", years)
            fuel = st.sidebar.selectbox("Fuel Type", fuels)
            
            # Load and display data
            if st.sidebar.button("Generate Flow Map") or 'flow_data' not in st.session_state:
                with st.spinner("Loading energy flow data..."):
                    flow_data = load_energy_flow_data(conn, scenario, year, fuel)
                    st.session_state.flow_data = flow_data
                    st.session_state.current_filters = (scenario, year, fuel)
            
            # Display current filters
            if 'current_filters' in st.session_state:
                scen, yr, fl = st.session_state.current_filters
                st.info(f"📊 **Current View**: {scen} scenario, Year {yr}, Fuel: {fl}")
            
            # Create and display map
            if 'flow_data' in st.session_state and not st.session_state.flow_data.empty:
                flow_map = create_flow_map(st.session_state.flow_data)
                
                if flow_map:
                    # CRITICAL: Lazy import for streamlit_folium only when displaying
                    from streamlit_folium import st_folium
                    
                    # Display the map
                    map_data = st_folium(flow_map, width=1200, height=600)
                    
                    # Show flow statistics
                    st.subheader("📈 Flow Statistics")
                    df = st.session_state.flow_data
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Total Flows", len(df))
                    col2.metric("Unique Regions", len(pd.concat([df['start'], df['end']]).unique()))
                    col3.metric("Total Energy", f"{df['value'].sum():.1f}")
                    col4.metric("Max Flow", f"{df['value'].max():.1f}")
                    
                    # Show detailed flow data
                    with st.expander("📊 View Flow Data"):
                        st.dataframe(df.sort_values('value', ascending=False))
                
            elif 'flow_data' in st.session_state:
                st.warning("⚠️ No energy flow data found for the selected filters. Try different scenario/year/fuel combinations.")
            
        except Exception as e:
            st.error(f"Error loading map data: {str(e)}")
    
    else:
        st.info("👆 Please connect to a database using the sidebar to start exploring energy flow maps.")
        
        # Show feature overview
        st.markdown("""
        ## 🎯 Features
        
        ### 🗺️ **Interactive Mapping**
        - Folium-based interactive maps with zoom and pan capabilities
        - Regional markers with geographic coordinates
        - Dynamic flow visualization with animated arrows
        
        ### ⚡ **Energy Flow Analysis**
        - **Transmission Flows**: Inter-regional energy transmission
        - **Import/Export Flows**: International energy trade
        - **Bidirectional Flow Detection**: Balanced trade relationships
        - **Flow Magnitude Visualization**: Line thickness represents energy volume
        
        ### 🎨 **Visual Features**
        - **Color-coded flows**: Blue (exports), Red (imports), Green (bidirectional)
        - **Animated pathways**: Moving dashes show flow direction
        - **Interactive popups**: Click flows for detailed information
        - **Geographic accuracy**: Automatic geocoding of region names
        
        ### 🛠️ **Technical Capabilities**
        - **Real-time geocoding**: Uses Nominatim for region coordinates
        - **Smart caching**: Efficient data loading and coordinate caching  
        - **Flow aggregation**: Handles complex bidirectional energy flows
        - **Responsive design**: Scales to different screen sizes
        
        ### 🎛️ **Filter Options**
        - **Scenario selection**: Compare different energy scenarios
        - **Year selection**: Temporal analysis across time periods
        - **Fuel type filtering**: Focus on specific energy commodities
        - **Dynamic updates**: Real-time map regeneration
        """)