# Create a new conda environment named 'times_viz' 
# - By running each of the commands lines 1)-4) below individually in a terminal
# 1) conda create -n times_viz python=3.10
# Activate the environment
# 2) conda activate times_viz
# Install required packages
# 3) conda install -c conda-forge streamlit duckdb pandas plotly requests
# Verify installations
# 4) python -c "import streamlit as st; import duckdb; import pandas as pd; import plotly.express as px; import requests; print('All packages imported successfully!')"

# Use the following code in terminal where the times_viz.py is located:
# streamlit run times_viz_energy_emissions_url_azure.py

import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit.runtime.scriptrunner.script_runner as script_runner
import requests
import os
import tempfile
from pathlib import Path
import hashlib
import urllib.parse
from datetime import datetime

script_runner.SCRIPT_RUN_CONTEXT_ATTR_NAME = "STREAMLIT_SCRIPT_RUN_CONTEXT"

# Set page configuration
st.set_page_config(page_title="SpeedLocal: TIMES Data Explorer", layout="wide")

# Title
st.title("SpeedLocal: TIMES Data Explorer!")

# Define sectors to exclude
EXCLUDED_SECTORS = [ 'DMZ', 'SYS', 'DHT','ELT','TRD']

def check_azure_url_expiry(url):
    """
    Check if Azure blob storage URL has expired based on 'se' parameter
    """
    try:
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        if 'se' in query_params:
            # Parse the expiry time
            expiry_str = query_params['se'][0]
            # Azure uses URL-encoded datetime format
            expiry_str = urllib.parse.unquote(expiry_str)
            expiry_time = datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
            current_time = datetime.now(expiry_time.tzinfo)
            
            if current_time > expiry_time:
                return True, expiry_time
            else:
                return False, expiry_time
        
        return False, None
    except Exception:
        return False, None

@st.cache_resource(show_spinner=False, ttl=3600)  # Cache for 1 hour
def download_database(url, use_cache=True):
    """
    Download DuckDB database from URL and cache it.
    Returns the path to the downloaded file.
    """
    try:
        # Check if Azure URL has expired
        is_expired, expiry_time = check_azure_url_expiry(url)
        if is_expired:
            st.error(f"Azure blob storage URL has expired (expired on: {expiry_time})")
            return None
        elif expiry_time:
            st.info(f"Azure URL expires on: {expiry_time}")
        
        # Create a hash of the URL for cache naming (excluding query parameters for Azure URLs)
        parsed_url = urllib.parse.urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        url_hash = hashlib.md5(base_url.encode()).hexdigest()[:8]
        
        # Define cache directory and file
        cache_dir = Path(tempfile.gettempdir()) / "streamlit_duckdb_cache"
        cache_dir.mkdir(exist_ok=True)
        cache_file = cache_dir / f"cached_db_{url_hash}.duckdb"
        
        # Check if cached file exists and use_cache is True
        if use_cache and cache_file.exists():
            # Check cache file age (for Azure URLs, refresh every 24 hours)
            cache_age = datetime.now().timestamp() - cache_file.stat().st_mtime
            max_cache_age = 24 * 3600  # 24 hours
            
            if cache_age < max_cache_age:
                st.info(f"Using cached database (cached {cache_age/3600:.1f} hours ago)")
                return str(cache_file)
            else:
                st.info("Cache expired, downloading fresh copy...")
        
        # Download the file
        with st.spinner(f"Downloading database from Azure blob storage... This may take a moment."):
            # Use a session with retries for better reliability
            session = requests.Session()
            session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
            
            response = session.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            # Get file size if available
            total_size = int(response.headers.get('content-length', 0))
            
            # Write to cache file with progress
            with open(cache_file, 'wb') as f:
                downloaded = 0
                block_size = 8192
                
                if total_size > 0:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = downloaded / total_size
                            progress_bar.progress(progress)
                            status_text.text(f"Downloaded {downloaded/1024/1024:.1f} MB / {total_size/1024/1024:.1f} MB")
                
                if total_size > 0:
                    progress_bar.empty()
                    status_text.empty()
            
            st.success(f"Database downloaded successfully! (Size: {downloaded/1024/1024:.1f} MB)")
            return str(cache_file)
            
    except requests.exceptions.Timeout:
        st.error("Download timed out. The database file might be very large. Please try again.")
        return None
    except requests.exceptions.RequestException as e:
        if "403" in str(e):
            st.error("Access denied. The Azure blob storage URL may have expired or insufficient permissions.")
        elif "404" in str(e):
            st.error("Database not found at the provided URL.")
        else:
            st.error(f"Error downloading database: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Unexpected error during download: {str(e)}")
        return None

def connect_to_db(source, is_url=False, use_cache=True):
    """
    Create a connection to the DuckDB database.
    Can handle both local file paths and URLs.
    """
    try:
        if is_url:
            # Download the database from URL
            db_path = download_database(source, use_cache=use_cache)
            if db_path is None:
                return None
        else:
            # Use local file path
            db_path = source
            if not os.path.exists(db_path):
                st.error(f"Local database file not found: {db_path}")
                return None
        
        # Connect to the database
        conn = duckdb.connect(str(db_path), read_only=True)
        st.success("Successfully connected to database!")
        return conn
    except Exception as e:
        st.error(f"Error connecting to database: {str(e)}")
        return None

def get_unique_values(conn, column, table="timesreport_facts"):
    """Get unique values for a given column"""
    try:
        query = f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL ORDER BY {column}"
        result = conn.execute(query).fetchall()
        return [x[0] for x in result]
    except Exception as e:
        st.error(f"Error getting unique values for {column}: {str(e)}")
        return []

def get_sector_descriptions(conn):
    """Get sector IDs and their descriptions, excluding specified sectors"""
    query = """
    SELECT DISTINCT 
        f.sector,
        COALESCE(s.description, f.sector) as sector_desc
    FROM timesreport_facts f
    LEFT JOIN sector_desc s ON f.sector = s.id AND f.scen = s.scen
    WHERE f.sector IS NOT NULL
    AND f.sector NOT IN ({})
    ORDER BY f.sector
    """.format(','.join(["'" + sector + "'" for sector in EXCLUDED_SECTORS]))
    
    try:
        results = conn.execute(query).fetchall()
        return {sector: desc for sector, desc in results}
    except Exception as e:
        st.error(f"Error getting sector descriptions: {str(e)}")
        return {}

def create_energy_plot(conn, sector, scenarios):
    """Create energy plot for specific sector with scenario comparison"""
    query = """
    SELECT 
        f.year,
        f.scen,
        f.comgroup,
        SUM(f.value) as value,
        f.unit,
        COALESCE(c.description, f.comgroup) as comgroup_desc
    FROM timesreport_facts f
    LEFT JOIN comgroup_desc c ON f.comgroup = c.id AND f.scen = c.scen
    WHERE f.topic = 'energy'
    AND f.attr = 'f_in'
    AND f.sector = ?
    AND f.scen IN ({})
    GROUP BY f.year, f.scen, f.comgroup, f.unit, c.description
    ORDER BY f.year, f.scen, c.description
    """.format(','.join(['?' for _ in scenarios]))
    
    try:
        # Execute query and get data
        df = conn.execute(query, [sector] + scenarios).df()
        
        if df.empty:
            st.write(f"No data available for sector {sector}")
            return

        # Create figure
        fig = go.Figure()
        
        # Get all unique years and commodity groups
        years = sorted(df['year'].unique())
        comgroups = sorted(df['comgroup_desc'].unique())
        
        # Create a consistent color map for commodity groups
        colors = px.colors.qualitative.Set3[:len(comgroups)]
        color_map = dict(zip(comgroups, colors))
        
        # Calculate bar width and positions
        scenario_width = 0.8 / len(scenarios)  # Width for each scenario's bar
        
        # Create bars for each year, scenario, and commodity group
        for year in years:
            year_data = df[df['year'] == year]
            
            for i, scen in enumerate(scenarios):
                scen_data = year_data[year_data['scen'] == scen]
                
                # Calculate x position for this scenario's bars
                x_pos = float(year) + (i - len(scenarios)/2 + 0.5) * scenario_width
                
                # Add bars for each commodity group
                for comgroup in comgroups:
                    value = scen_data[scen_data['comgroup_desc'] == comgroup]['value'].sum()
                    
                    fig.add_trace(go.Bar(
                        name=comgroup,
                        x=[x_pos],
                        y=[value],
                        width=scenario_width * 0.9,  # Slightly smaller than calculated width for spacing
                        marker_color=color_map[comgroup],
                        legendgroup=comgroup,
                        showlegend=year == years[0] and i == 0,  # Show legend only for first occurrence
                        hovertemplate=(
                            f"Year: {year}<br>" +
                            f"Scenario: {scen}<br>" +
                            f"Commodity: {comgroup}<br>" +
                            f"Value: %{{y:.2f}} {df.unit.iloc[0]}"
                        )
                    ))
        
        # Add scenario annotations above the plot
        for i, scen in enumerate(scenarios):
            fig.add_annotation(
                x=0.1 + i * 0.8/len(scenarios),
                y=1.05,
                text=scen,
                showarrow=False,
                xref="paper",
                yref="paper",
                font=dict(size=12)
            )
        
        # Update layout
        fig.update_layout(
            barmode='stack',
            title=f'Energy Input by Commodity Group and Scenario',
            xaxis_title="Year",
            yaxis_title=f"Energy Input ({df.unit.iloc[0]})",
            height=600,
            bargap=0,
            bargroupgap=0.1,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5,
                title=dict(text="Commodity Groups")
            ),
            margin=dict(t=80)  # Add more top margin for scenario labels
        )
        
        # Set x-axis ticks to show years clearly
        fig.update_xaxes(
            tickmode='array',
            ticktext=years,
            tickvals=years,
            tickangle=0
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creating plot: {str(e)}")

def create_emission_plot(conn, sector, scenarios):
    """Create emission plot for specific sector with scenario comparison"""
    query = """
    SELECT 
        f.year,
        f.scen,
        f.comgroup,
        SUM(f.value) as value,
        f.unit,
        COALESCE(c.description, f.comgroup) as comgroup_desc
    FROM timesreport_facts f
    LEFT JOIN comgroup_desc c ON f.comgroup = c.id AND f.scen = c.scen
    WHERE f.topic = 'emission'
    AND f.sector = ?
    AND f.scen IN ({})
    GROUP BY f.year, f.scen, f.comgroup, f.unit, c.description
    ORDER BY f.year, f.scen, c.description
    """.format(','.join(['?' for _ in scenarios]))
    
    try:
        # Execute query and get data
        df = conn.execute(query, [sector] + scenarios).df()
        
        if df.empty:
            st.write(f"No emission data available for sector {sector}")
            return

        # Create figure
        fig = go.Figure()
        
        # Get all unique years and commodity groups (emission types)
        years = sorted(df['year'].unique())
        comgroups = sorted(df['comgroup_desc'].unique())
        
        # Create a consistent color map for emission types
        colors = px.colors.qualitative.Set1[:len(comgroups)]
        color_map = dict(zip(comgroups, colors))
        
        # For emissions, we'll use a line chart with markers to better show trends over time
        for scen in scenarios:
            for comgroup in comgroups:
                scen_data = df[(df['scen'] == scen) & (df['comgroup_desc'] == comgroup)]
                
                if not scen_data.empty:
                    fig.add_trace(go.Scatter(
                        x=scen_data['year'],
                        y=scen_data['value'],
                        mode='lines+markers',
                        name=f"{comgroup} - {scen}",
                        line=dict(color=color_map[comgroup]),
                        marker=dict(size=8),
                        hovertemplate=(
                            "Year: %{x}<br>" +
                            f"Scenario: {scen}<br>" +
                            f"Emission Type: {comgroup}<br>" +
                            f"Value: %{{y:.2f}} {scen_data.unit.iloc[0]}"
                        )
                    ))
        
        # Update layout
        fig.update_layout(
            title=f'Emissions by Type and Scenario',
            xaxis_title="Year",
            yaxis_title=f"Emissions ({df.unit.iloc[0]})",
            height=600,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5
            )
        )
        
        # Set x-axis ticks to show years clearly
        fig.update_xaxes(
            tickmode='array',
            ticktext=years,
            tickvals=years,
            tickangle=0
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creating emission plot: {str(e)}")

def main():
    # Add sidebar for database connection
    st.sidebar.header("Database Connection")
    
    # Radio button to choose between URL and local file
    connection_type = st.sidebar.radio(
        "Connection Type:",
        ["Azure URL", "Local File"],
        help="Choose whether to connect to a database via Azure URL or local file path"
    )
    
    if connection_type == "Azure URL":
        # Default Azure URL - your provided URL
        default_url = "https://speedlocal.flowcore.app/api/duckdb/share/f5cab424b9d0aba6bc6dedf0424c8422"
        
        db_source = st.sidebar.text_area(
            "Enter Azure Blob Storage URL:",
            value=default_url,
            height=100,
            help="Enter the full Azure blob storage URL with SAS token"
        )
        
        # Check URL expiry and show warning if needed
        if db_source:
            is_expired, expiry_time = check_azure_url_expiry(db_source)
            if is_expired:
                st.sidebar.error(f"⚠️ URL has expired (expired: {expiry_time})")
            elif expiry_time:
                days_until_expiry = (expiry_time - datetime.now(expiry_time.tzinfo)).days
                if days_until_expiry < 7:
                    st.sidebar.warning(f"⚠️ URL expires in {days_until_expiry} days ({expiry_time})")
                else:
                    st.sidebar.info(f"✅ URL expires: {expiry_time}")
        
        # Add cache option
        use_cache = st.sidebar.checkbox(
            "Use cached database if available",
            value=True,
            help="If checked, will use a previously downloaded version of the database if available (refreshes every 24 hours)"
        )
        
        # Add button to clear cache
        if st.sidebar.button("Clear Cache"):
            try:
                cache_dir = Path(tempfile.gettempdir()) / "streamlit_duckdb_cache"
                if cache_dir.exists():
                    import shutil
                    shutil.rmtree(cache_dir)
                    st.sidebar.success("Cache cleared successfully!")
                    # Clear the cache decorator as well
                    download_database.clear()
            except Exception as e:
                st.sidebar.error(f"Error clearing cache: {str(e)}")
        
        is_url = True
    else:
        db_source = st.sidebar.text_input(
            "Enter path to DuckDB database:",
            value="./duckDB/speedlocal_times_db.duckdb",
            help="Enter the local file path to the DuckDB database"
        )
        use_cache = True  # Not used for local files
        is_url = False
    
    # Connection button
    connect_button = st.sidebar.button("Connect to Database")
    
    # Auto-connect for Azure URL if it's the default and not expired
    auto_connect = False
    if connection_type == "Azure URL" and db_source:
        is_expired, _ = check_azure_url_expiry(db_source)
        if not is_expired and 'connected' not in st.session_state:
            auto_connect = True
    
    if connect_button or auto_connect:
        conn = connect_to_db(db_source, is_url=is_url, use_cache=use_cache)
        
        if conn is not None:
            try:
                # Store connection in session state
                st.session_state['conn'] = conn
                st.session_state['connected'] = True
                
                # Get available scenarios
                all_scenarios = get_unique_values(conn, "scen")
                
                if not all_scenarios:
                    st.error("No scenarios found in the database")
                    return
                
                # Store scenarios in session state
                st.session_state['scenarios'] = all_scenarios
                
                # Show database info
                with st.sidebar.expander("Database Info"):
                    try:
                        # Get basic database statistics
                        stats_query = """
                        SELECT 
                            COUNT(DISTINCT scen) as scenarios,
                            COUNT(DISTINCT year) as years,
                            COUNT(DISTINCT sector) as sectors,
                            COUNT(*) as total_records
                        FROM timesreport_facts
                        """
                        stats = conn.execute(stats_query).fetchone()
                        st.write(f"📊 Scenarios: {stats[0]}")
                        st.write(f"📅 Years: {stats[1]}")
                        st.write(f"🏭 Sectors: {stats[2]}")
                        st.write(f"📝 Records: {stats[3]:,}")
                    except:
                        st.write("Database connected successfully")
                
            except Exception as e:
                st.error(f"Error reading initial data: {str(e)}")
    
    # Check if we have an active connection
    if 'connected' in st.session_state and st.session_state['connected']:
        conn = st.session_state['conn']
        all_scenarios = st.session_state['scenarios']
        
        # Add scenario selection to sidebar
        selected_scenarios = st.sidebar.multiselect(
            "Select Scenarios to Compare:",
            options=all_scenarios,
            default=all_scenarios[:2] if len(all_scenarios) > 1 else all_scenarios
        )
        
        if not selected_scenarios:
            st.warning("Please select at least one scenario")
            return
        
        try:
            # Get sectors and their descriptions (excluding the specified sectors)
            sector_desc_dict = get_sector_descriptions(conn)
            
            if not sector_desc_dict:
                st.error("No sectors found in the database")
                return
            
            # Add topic selection tab
            topic_tabs = st.tabs(["Energy", "Emissions", "Development"])
            
            # Energy visualization tab
            with topic_tabs[0]:
                st.header("Energy Visualization")
                
                # Create tabs using sector descriptions
                sectors = list(sector_desc_dict.keys())
                sector_descs = [sector_desc_dict[sector] for sector in sectors]
                sector_tabs = st.tabs(sector_descs)
                
                # Create content for each sector tab
                for tab, sector in zip(sector_tabs, sectors):
                    with tab:
                        st.subheader(f"{sector_desc_dict[sector]}")
                        create_energy_plot(conn, sector, selected_scenarios)
            
            # Emissions visualization tab
            with topic_tabs[1]:
                st.header("Emissions Visualization")
                
                # Create tabs using sector descriptions
                sectors = list(sector_desc_dict.keys())
                sector_descs = [sector_desc_dict[sector] for sector in sectors]
                sector_tabs = st.tabs(sector_descs)
                
                # Create content for each sector tab
                for tab, sector in zip(sector_tabs, sectors):
                    with tab:
                        st.subheader(f"{sector_desc_dict[sector]}")
                        create_emission_plot(conn, sector, selected_scenarios)
            # Development tab placeholder
            with topic_tabs[2]:
                st.header("Development")
                st.info("This section is for testing new features.")
                # Display .jpg
                try:
                    st.image("images/speed-local.jpg", caption="Speed Local", use_container_width=True)
                except FileNotFoundError:
                    st.error("Image not found: images/speed-local.jpg")
                except Exception as e:
                    st.error(f"Error loading image: {str(e)}")

                # Display .png
                try:
                    st.image("images/map.png")
                except FileNotFoundError:
                    st.error("Image not found: images/map.png")
                except Exception as e:
                    st.error(f"Error loading image: {str(e)}")
                
                

        except Exception as e:
            st.error(f"Error reading data: {str(e)}")
    else:
        st.info("👈 Please connect to a database using the sidebar options.")
        
        # Show some helpful information
        st.markdown("""
        ### Getting Started
        
        1. **Azure URL**: Use the pre-filled Azure blob storage URL (default option)
        2. **Local File**: If you have a local DuckDB file, select this option
        
        ### Features
        - **Caching**: Downloaded databases are cached locally for faster access
        - **URL Expiry Check**: Automatic detection of Azure URL expiration
        - **Multi-scenario Comparison**: Compare different scenarios side by side
        - **Interactive Visualizations**: Energy and emission data with detailed hover information
        """)

if __name__ == "__main__":
    main()