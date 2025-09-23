import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Speed Local Analytics",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Header
st.title("🚀 Speed Local Analytics Dashboard")
st.markdown("**Scientific data visualization and analysis for Nordic green transition research**")

# Sidebar
with st.sidebar:
    st.header("Navigation")
    st.markdown("---")
    st.info("📊 **Speed Local Project**\n\nA platform for scientists to share and analyze GAMS reports and scientific datasets for Nordic green transition research.")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📈 Dashboard Overview")
    
    # Sample metrics
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
    with metric_col1:
        st.metric(
            label="Datasets Available",
            value="24",
            delta="3"
        )
    
    with metric_col2:
        st.metric(
            label="DuckDB Files",
            value="12",
            delta="2"
        )
    
    with metric_col3:
        st.metric(
            label="GAMS Reports",
            value="15",
            delta="1"
        )
    
    with metric_col4:
        st.metric(
            label="Active Users",
            value="8",
            delta="1"
        )
    
    st.markdown("---")
    
    # Sample chart placeholder
    st.subheader("📊 Dataset Usage Over Time")
    
    # Generate sample data
    sample_data = pd.DataFrame({
        'Date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
        'GAMS Uploads': [2, 1, 3, 2, 4, 1, 2, 3, 1, 4, 2, 3, 1, 2, 3, 4, 1, 2, 3, 2, 1, 4, 3, 2, 1, 3, 2, 4, 1, 2],
        'DuckDB Downloads': [5, 3, 7, 4, 8, 2, 5, 6, 3, 9, 4, 7, 2, 5, 6, 8, 3, 5, 7, 4, 2, 9, 6, 5, 3, 7, 4, 8, 2, 5]
    })
    
    st.line_chart(
        sample_data.set_index('Date'),
        height=400
    )

with col2:
    st.header("🔗 Quick Actions")
    
    # Action buttons
    if st.button("📤 Upload Dataset", use_container_width=True):
        st.info("This would redirect to the Speed Local Admin upload interface")
    
    if st.button("🔍 Browse Datasets", use_container_width=True):
        st.info("This would show available datasets for analysis")
    
    if st.button("🗄️ Create DuckDB", use_container_width=True):
        st.info("This would allow combining datasets into DuckDB files")
    
    st.markdown("---")
    
    st.header("📋 Recent Activity")
    
    # Sample activity feed
    activities = [
        {"time": "2 hours ago", "action": "New GAMS file uploaded", "user": "Dr. Sarah"},
        {"time": "5 hours ago", "action": "DuckDB file created", "user": "Erik"},
        {"time": "1 day ago", "action": "Dataset shared publicly", "user": "Dr. Sarah"},
        {"time": "2 days ago", "action": "New user joined", "user": "Anna"},
        {"time": "3 days ago", "action": "GAMS report processed", "user": "Erik"},
    ]
    
    for activity in activities:
        with st.container():
            st.text(f"⏱️ {activity['time']}")
            st.text(f"👤 {activity['user']}: {activity['action']}")
            st.markdown("---")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #888; padding: 20px;'>
        <p>🌱 <strong>Speed Local Project</strong> - Accelerating Nordic green transition through trans-Nordic collaboration</p>
        <p>Built with Streamlit • Powered by Flowcore Infrastructure</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Health check endpoint (Streamlit exposes /_stcore/health automatically)