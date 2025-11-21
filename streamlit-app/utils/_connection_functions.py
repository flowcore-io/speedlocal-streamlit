import os
import urllib
import hashlib
import tempfile
from pathlib import Path
from datetime import datetime
import requests
import duckdb

def connect_to_db(source, is_url=False, use_cache=True, message_callback=None, progress_callback=None):
    """
    Connect to a DuckDB database (local file or URL).
    Returns a read-only connection or None on failure.
    """
    try:
        if is_url:
            db_path = download_database(
                source,
                use_cache=use_cache,
                progress_callback=progress_callback,
                message_callback=message_callback
            )
            if not db_path:
                return None
        else:
            db_path = source
            if not os.path.exists(db_path):
                if message_callback:
                    message_callback("error", f"Local database file not found: {db_path}")
                return None

        conn = duckdb.connect(db_path, read_only=True)
        if message_callback:
            message_callback("success", "Successfully connected to database!")
        return conn

    except Exception as e:
        if message_callback:
            message_callback("error", f"Error connecting to database: {str(e)}")
        return None

# def msg(level, text):
#     print(f"[{level.upper()}] {text}")

# def progress(progress, text):
#     print(f"Progress: {progress*100:.1f}% - {text}")

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


def download_database(url, use_cache=True, progress_callback=None, message_callback=None):
    """
    Download DuckDB database from URL and cache it.
    Returns the path to the downloaded file.

    Args:
        url (str): Azure blob URL or other HTTP(s) link.
        use_cache (bool): If True, reuse cached copy if available.
        progress_callback (func): Optional function(progress: float, msg: str)
        message_callback (func): Optional function(level: str, msg: str)
                                 where level ∈ {"info","error","success"}
    """
    try:
        # Check if Azure URL has expired
        is_expired, expiry_time = check_azure_url_expiry(url)
        if is_expired:
            if message_callback:
                message_callback("error", f"Azure blob storage URL has expired (expired on: {expiry_time})")
            return None
        elif expiry_time and message_callback:
            message_callback("info", f"Azure URL expires on: {expiry_time}")

        # Create cache directory
        parsed_url = urllib.parse.urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        url_hash = hashlib.md5(base_url.encode()).hexdigest()[:8]

        cache_dir = Path(tempfile.gettempdir()) / "duckdb_cache"
        cache_dir.mkdir(exist_ok=True)
        cache_file = cache_dir / f"cached_db_{url_hash}.duckdb"

        # Check cache validity
        if use_cache and cache_file.exists():
            cache_age = datetime.now().timestamp() - cache_file.stat().st_mtime
            if cache_age < 24 * 3600:  # 24 hours
                if message_callback:
                    message_callback("info", f"Using cached database (cached {cache_age/3600:.1f} hours ago)")
                return str(cache_file)
            else:
                if message_callback:
                    message_callback("info", "Cache expired, downloading fresh copy...")

        # Download
        if message_callback:
            message_callback("info", "Downloading database from Azure blob storage...")

        session = requests.Session()
        session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
        response = session.get(url, stream=True, timeout=300)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        block_size = 8192

        with open(cache_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0 and progress_callback:
                        progress = downloaded / total_size
                        progress_callback(progress, f"{downloaded/1024/1024:.1f} MB / {total_size/1024/1024:.1f} MB")

        if message_callback:
            message_callback("success", f"Database downloaded successfully! (Size: {downloaded/1024/1024:.1f} MB)")

        return str(cache_file)

    except requests.exceptions.Timeout:
        if message_callback:
            message_callback("error", "Download timed out. Please try again.")
        return None
    except requests.exceptions.RequestException as e:
        msg = str(e)
        if "403" in msg:
            err = "Access denied. URL may have expired or insufficient permissions."
        elif "404" in msg:
            err = "Database not found at the provided URL."
        else:
            err = f"Error downloading database: {msg}"
        if message_callback:
            message_callback("error", err)
        return None
    except Exception as e:
        if message_callback:
            message_callback("error", f"Unexpected error: {str(e)}")
        return None


# --- Usage ---
if __name__ == "__main__":
    url = "https://speedlocal.flowcore.app/api/duckdb/share/de0274a3e2da3eed3f920dab28c81bf8"

    conn = connect_to_db(
        url,
        is_url=True,
        message_callback=msg,
        progress_callback=progress
    )

    if conn:
        print("\nTables:")
        print(conn.sql("SHOW TABLES").df())
        # Assuming 'conn' is your DuckDB connection
        tables_df = conn.sql("SHOW TABLES").df()  # get list of tables
        table_names = tables_df['name'].tolist()  # extract table names

        # Dictionary to store DataFrames
        dfs = {}

        for table in table_names:
            dfs[table] = conn.sql(f"SELECT * FROM {table}").df()
            print(f"Loaded table '{table}' into dataframe with shape {dfs[table].shape}")

