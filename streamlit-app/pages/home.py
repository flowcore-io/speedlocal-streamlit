"""
Home page for Speed Local Analytics Hub
"""

import streamlit as st
import pandas as pd

def render_home_page():
    """Render the main home page content"""
    
    # Welcome section
    st.markdown("""
    ## Welcome to Speed Local Analytics Hub 🚀
    
    Your comprehensive platform for Nordic green transition research data analysis and visualization.
    """)
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📁 Available Tools",
            value="4",
            delta="Active"
        )
    
    with col2:
        st.metric(
            label="🗄️ Data Sources",
            value="Multiple",
            delta="DuckDB + Azure"
        )
    
    with col3:
        st.metric(
            label="📈 Analysis Types",
            value="Energy + Emissions",
            delta="TIMES Models"
        )
    
    with col4:
        st.metric(
            label="🌍 Geographic Scope",
            value="Nordic Region",
            delta="Focus: Bornholm"
        )
    
    st.markdown("---")
    
    # Tools overview
    st.markdown("## 🧭 Available Analysis Tools")
    
    tool_col1, tool_col2 = st.columns(2)
    
    with tool_col1:
        with st.container():
            st.markdown("""
            ### 📊 [TIMES Data Explorer](?route=times)
            Advanced sector-based energy and emission analysis with interactive charts and multi-scenario comparison capabilities.
            
            **Features:**
            - Energy input visualization by commodity groups
            - Emissions tracking by sector and type
            - Scenario comparison analysis
            - Azure blob storage integration
            """)
        
        with st.container():
            st.markdown("""
            ### 📈 [Sankey Diagrams](?route=sankey)
            Interactive energy flow visualization showing transformations and distributions across the energy system.
            
            **Features:**
            - Production and consumption flows
            - Import/export analysis
            - Node categorization with color coding
            - Flow aggregation and filtering
            """)
    
    with tool_col2:
        with st.container():
            st.markdown("""
            ### 🌍 [Energy Flow Maps](?route=flow-maps)
            Interactive geospatial visualization of energy flows between regions with real-time mapping.
            
            **Features:**
            - Animated flow pathways
            - Bidirectional flow detection
            - Geographic coordinate mapping
            - Regional energy trade analysis
            """)
        
        with st.container():
            st.markdown("""
            ### 🛠️ [Database Tools](?route=database)
            Comprehensive database exploration and management utilities for direct data access.
            
            **Features:**
            - Schema exploration
            - SQL query interface
            - Automated data analysis
            - Quick chart generation
            """)
    
    st.markdown("---")
    
    # Quick access buttons
    st.markdown("## ⚡ Quick Access")
    
    btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
    
    with btn_col1:
        if st.button("🚀 Launch TIMES Explorer", use_container_width=True, type="primary"):
            st.query_params.route = "times"
            st.rerun()
    
    with btn_col2:
        if st.button("🗺️ Open Flow Maps", use_container_width=True, type="primary"):
            st.query_params.route = "flow-maps"
            st.rerun()
    
    with btn_col3:
        if st.button("📊 View Sankey", use_container_width=True, type="primary"):
            st.query_params.route = "sankey"
            st.rerun()
    
    with btn_col4:
        if st.button("⚙️ Database Tools", use_container_width=True, type="primary"):
            st.query_params.route = "database"
            st.rerun()
    
    st.markdown("---")
    
    # Sample activity chart
    st.markdown("## 📈 Platform Activity")
    
    # Generate sample data
    sample_data = pd.DataFrame({
        'Date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
        'GAMS Uploads': [2, 1, 3, 2, 4, 1, 2, 3, 1, 4, 2, 3, 1, 2, 3, 4, 1, 2, 3, 2, 1, 4, 3, 2, 1, 3, 2, 4, 1, 2],
        'DuckDB Queries': [5, 3, 7, 4, 8, 2, 5, 6, 3, 9, 4, 7, 2, 5, 6, 8, 3, 5, 7, 4, 2, 9, 6, 5, 3, 7, 4, 8, 2, 5]
    })
    
    st.line_chart(
        sample_data.set_index('Date'),
        height=300
    )
    
    # Recent activity
    activity_col1, activity_col2 = st.columns([2, 1])
    
    with activity_col1:
        st.markdown("### 📋 Getting Started")
        st.markdown("""
        1. **Choose a tool** from the navigation above or quick access buttons
        2. **Connect to your data** using local DuckDB files or Azure storage URLs  
        3. **Explore and analyze** your TIMES model results interactively
        4. **Switch between tools** using the navigation bar or URL routes
        
        **Direct URL Access:**
        - Energy Analysis: `/?route=times`
        - Geographic Flows: `/?route=flow-maps`  
        - Flow Diagrams: `/?route=sankey`
        - Database Access: `/?route=database`
        """)
    
    with activity_col2:
        st.markdown("### 📊 Platform Info")
        st.info("""
        **🔧 Technical Stack**
        - Streamlit Web Framework
        - DuckDB for fast analytics
        - Plotly for interactive charts
        - Folium for mapping
        - Azure blob storage support
        
        **🌐 URL Routing**
        Each tool accessible via clean URLs for easy bookmarking and sharing.
        """)
        
    st.markdown("---")
    
    st.markdown("""
    ### 🎯 About Speed Local
    
    Speed Local is a platform designed for scientists and researchers working on Nordic green transition initiatives. 
    The platform enables sharing and collaborative analysis of GAMS reports and scientific datasets, 
    with a particular focus on energy system modeling and emissions analysis.
    
    **Key Capabilities:**
    - **TIMES Model Analysis**: Comprehensive analysis of energy system optimization results
    - **Multi-Scenario Comparison**: Compare different energy transition pathways
    - **Geospatial Visualization**: Understand regional energy flows and trade patterns
    - **Interactive Exploration**: Dynamic filtering and drill-down capabilities
    - **Collaborative Research**: Share insights and findings with the research community
    """)