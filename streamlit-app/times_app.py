#!/usr/bin/env python3
"""
TIMES Data Explorer - Standalone entry point
For running as individual containerized app
"""

import streamlit as st
from pages.times_explorer import render_times_explorer

# Set page configuration
st.set_page_config(
    page_title="TIMES Data Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # Header with navigation info
    st.markdown("""
    <div style="background: linear-gradient(90deg, #1f77b4 0%, #ff7f0e 100%); padding: 10px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: white; text-align: center; margin: 0;">📊 TIMES Data Explorer</h2>
        <p style="color: white; text-align: center; margin: 5px 0 0 0; opacity: 0.9;">Part of Speed Local Analytics Hub</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Render the main functionality
    render_times_explorer()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #888; padding: 10px;'>
        <p>🌱 <strong>Speed Local Project</strong> - Nordic Green Transition Research Platform</p>
        <p>Visit the <strong><a href="/" target="_blank">Analytics Hub</a></strong> for other tools</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()