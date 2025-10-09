# for streamlit components
import streamlit as st
import pandas as pd

from ._query_functions import *

# --- Streamlit wrapper (optional) ---
def get_unique_values(conn, column, table="timesreport_facts"):
    """
    Streamlit-friendly wrapper for fetch_unique_values.
    Shows error in Streamlit if query fails.
    """
    import streamlit as st
    values = fetch_unique_values(conn, column, table)
    if not values:
        st.error(f"Error getting unique values for {column}")
    return values