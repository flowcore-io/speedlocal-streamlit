#!/usr/bin/env python3
"""
Database Tools - Standalone Streamlit App
Entry point for running the Database Tools functionality as a separate app.
"""

import streamlit as st
import sys
import os

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(__file__))

# Import the page module
from pages.database_tools import render_database_tools

def main():
    """Main application entry point"""
    
    # Configure the Streamlit page
    st.set_page_config(
        page_title="Database Tools - TIMES Energy Analytics",
        page_icon="🗄️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
        .main > div {
            padding-top: 2rem;
        }
        .stSelectbox > div > div > select {
            background-color: white;
        }
        .metric-container {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 0.5rem 0;
        }
        .sql-query-area {
            font-family: 'Courier New', monospace;
        }
        div[data-testid="stExpander"] {
            border: 1px solid #e0e0e0;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        .plotly-chart {
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Main header
    st.title("🗄️ Database Tools")
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 1.5rem; border-radius: 1rem; margin-bottom: 2rem;">
        <h2 style="color: white; margin: 0; text-align: center;">
            Comprehensive Database Exploration & Analysis
        </h2>
        <p style="color: #f0f0f0; margin: 0.5rem 0 0 0; text-align: center; font-size: 1.1rem;">
            Connect to DuckDB databases • Execute SQL queries • Visualize data • Generate reports
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick stats/info section
    info_col1, info_col2, info_col3, info_col4 = st.columns(4)
    
    with info_col1:
        st.markdown("""
        <div class="metric-container">
            <h4>🔍 Schema Explorer</h4>
            <p>Browse tables, columns, and data structure</p>
        </div>
        """, unsafe_allow_html=True)
    
    with info_col2:
        st.markdown("""
        <div class="metric-container">
            <h4>⚡ SQL Interface</h4>
            <p>Execute queries with templates and safety</p>
        </div>
        """, unsafe_allow_html=True)
    
    with info_col3:
        st.markdown("""
        <div class="metric-container">
            <h4>📊 Auto Analysis</h4>
            <p>Instant insights and data summaries</p>
        </div>
        """, unsafe_allow_html=True)
    
    with info_col4:
        st.markdown("""
        <div class="metric-container">
            <h4>📈 Quick Charts</h4>
            <p>Generate visualizations from any query</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Render the main database tools interface
    render_database_tools()
    
    # Footer with navigation info
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p><strong>Database Tools</strong> | Part of TIMES Energy Analytics Platform</p>
        <p>🏠 <a href="/">Return to Home</a> | 📊 <a href="/times">TIMES Explorer</a> | 
           🗺️ <a href="/flowmaps">Flow Maps</a> | 🌊 <a href="/sankey">Sankey Diagrams</a></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()