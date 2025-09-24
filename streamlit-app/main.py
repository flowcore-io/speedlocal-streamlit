"""
Speed Local Analytics Hub - URL Router Based Main Application
Handles URL routing to different analysis tools while avoiding pybind11 conflicts
"""

import streamlit as st
import sys
import os

# Add current directory and utils to path
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'app', 'utils'))

st.set_page_config(
    page_title="Speed Local Analytics Hub",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def get_route_from_url():
    """Extract route from URL parameters"""
    try:
        # Get URL params from Streamlit
        query_params = st.query_params
        
        # Check for route parameter
        if "route" in query_params:
            return query_params["route"]
        elif "page" in query_params:
            return query_params["page"]
        else:
            return "home"
    except:
        return "home"

def render_navigation():
    """Render navigation bar"""
    st.markdown("""
    <div style="background: linear-gradient(90deg, #1f77b4 0%, #ff7f0e 100%); padding: 10px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: white; text-align: center; margin: 0;">🚀 Speed Local Analytics Hub</h2>
        <p style="color: white; text-align: center; margin: 5px 0 0 0; opacity: 0.9;">Nordic Green Transition Research Platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation buttons
    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns(5)
    
    with nav_col1:
        if st.button("🏠 Home", use_container_width=True, type="secondary"):
            st.query_params.clear()
            st.rerun()
    
    with nav_col2:
        if st.button("📊 TIMES Explorer", use_container_width=True):
            st.query_params.route = "times"
            st.rerun()
    
    with nav_col3:
        if st.button("🌍 Flow Maps", use_container_width=True):
            st.query_params.route = "flow-maps"
            st.rerun()
    
    with nav_col4:
        if st.button("📈 Sankey Diagrams", use_container_width=True):
            st.query_params.route = "sankey"
            st.rerun()
    
    with nav_col5:
        if st.button("🛠️ Database Tools", use_container_width=True):
            st.query_params.route = "database"
            st.rerun()

def render_home():
    """Render the home page"""
    from pages.home import render_home_page
    render_home_page()

def render_times_explorer():
    """Render TIMES Data Explorer with lazy imports"""
    st.header("📊 TIMES Data Explorer")
    st.markdown("**Advanced sector-based energy and emission analysis with scenario comparison capabilities**")
    
    # Import the TIMES explorer functionality
    from pages.times_explorer import render_times_explorer
    render_times_explorer()

def render_flow_maps():
    """Render Energy Flow Maps with lazy imports"""
    st.header("🌍 Energy Flow Maps")
    st.markdown("**Interactive geospatial visualization of energy flows between regions**")
    
    # Import the flow maps functionality  
    from pages.energy_flow_maps import render_flow_maps
    render_flow_maps()

def render_sankey_diagrams():
    """Render Sankey Diagrams with lazy imports"""
    st.header("📈 Sankey Diagrams")
    st.markdown("**Interactive energy flow visualization with comprehensive flow analysis**")
    
    # Import the sankey functionality
    from pages.sankey_diagrams import render_sankey_diagrams
    render_sankey_diagrams()

def render_database_tools():
    """Render Database Tools with lazy imports"""
    st.header("🛠️ Database Tools")
    st.markdown("**Comprehensive database exploration, querying, and management utilities**")
    
    # Import the database tools functionality
    from pages.database_tools import render_database_tools
    render_database_tools()

def main():
    """Main application router"""
    
    # Render navigation
    render_navigation()
    
    # Get current route
    current_route = get_route_from_url()
    
    # Route to appropriate page
    if current_route == "home":
        render_home()
    elif current_route == "times":
        render_times_explorer()
    elif current_route == "flow-maps":
        render_flow_maps()
    elif current_route == "sankey":
        render_sankey_diagrams()
    elif current_route == "database":
        render_database_tools()
    else:
        # Unknown route - redirect to home
        st.error(f"Unknown route: {current_route}")
        render_home()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #888; padding: 20px;'>
        <p>🌱 <strong>Speed Local Project</strong> - Accelerating Nordic green transition through trans-Nordic collaboration</p>
        <p>Built with Streamlit • Powered by Flowcore Infrastructure</p>
        <p><strong>URL Routes:</strong> /?route=times | /?route=flow-maps | /?route=sankey | /?route=database</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()