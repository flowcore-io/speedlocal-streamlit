#!/usr/bin/env python3
"""
Energy Flow Maps - Standalone entry point
For running as individual containerized app
"""

import streamlit as st
from pages.energy_flow_maps import render_flow_maps

# Set page configuration
st.set_page_config(
    page_title="Energy Flow Maps",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # Header with navigation info
    st.markdown("""
    <div style="background: linear-gradient(90deg, #2ca02c 0%, #1f77b4 100%); padding: 10px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: white; text-align: center; margin: 0;">🌍 Energy Flow Maps</h2>
        <p style="color: white; text-align: center; margin: 5px 0 0 0; opacity: 0.9;">Part of Speed Local Analytics Hub</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Render the main functionality
    render_flow_maps()
    
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