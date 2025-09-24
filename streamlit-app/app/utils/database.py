"""
Shared database utilities for Speed Local Streamlit applications
"""
import streamlit as st
import duckdb
import pandas as pd
import requests
import os
import tempfile
from pathlib import Path
import hashlib
import urllib.parse
from datetime import datetime
import traceback

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

def connect_to_db(source, is_url=False, use_cache=True, debug_mode=True):
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
        if debug_mode:
            st.code(traceback.format_exc())
        return None

def get_unique_values(conn, column, table="timesreport_facts", debug_mode=False):
    """Get unique values for a given column"""
    try:
        query = f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL ORDER BY {column}"
        result = conn.execute(query).fetchall()
        
        values = [x[0] for x in result]
        
        if debug_mode and len(values) > 0:
            st.write(f"Debug: Found {len(values)} unique values for {column}")
            st.write(f"Debug: Sample values: {values[:5] if len(values) > 5 else values}")
        
        return values
    except Exception as e:
        st.error(f"Error getting unique values for {column}: {str(e)}")
        if debug_mode:
            st.code(traceback.format_exc())
        return []

def get_sector_descriptions(conn, excluded_sectors=None):
    """Get sector IDs and their descriptions, excluding specified sectors"""
    if excluded_sectors is None:
        excluded_sectors = ['NA', 'DMZ', 'SYS', 'DHT', 'ELT', 'TRD']
    
    query = """
    SELECT DISTINCT 
        f.sector,
        COALESCE(s.description, f.sector) as sector_desc
    FROM timesreport_facts f
    LEFT JOIN sector_desc s ON f.sector = s.id AND f.scen = s.scen
    WHERE f.sector IS NOT NULL
    AND f.sector NOT IN ({})
    ORDER BY f.sector
    """.format(','.join([f"'{sector}'" for sector in excluded_sectors]))
    
    try:
        results = conn.execute(query).fetchall()
        return {sector: desc for sector, desc in results}
    except Exception as e:
        st.error(f"Error getting sector descriptions: {str(e)}")
        return {}

def test_database_connection(conn):
    """Test database connection and show basic info"""
    try:
        # Get table names
        tables = conn.execute("SHOW TABLES").fetchall()
        st.info(f"Database contains {len(tables)} tables")
        
        # Get basic stats from main table if it exists
        if any('timesreport_facts' in str(table) for table in tables):
            count = conn.execute("SELECT COUNT(*) FROM timesreport_facts").fetchall()[0][0]
            st.info(f"timesreport_facts table contains {count:,} records")
            
            # Show available scenarios
            scenarios = get_unique_values(conn, "scen", debug_mode=False)
            st.info(f"Available scenarios: {', '.join(scenarios[:5])}{'...' if len(scenarios) > 5 else ''}")
        
        return True
    except Exception as e:
        st.error(f"Error testing database: {str(e)}")
        return False