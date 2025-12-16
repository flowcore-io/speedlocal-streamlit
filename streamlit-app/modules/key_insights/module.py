"""
Key Insights module for stakeholder-facing dashboard.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from base_module import BaseModule


class KeyInsightsModule(BaseModule):
    """Key Insights module - Executive dashboard."""
    
    def __init__(self):
        super().__init__(
            name="Key Insights",
            description="Executive dashboard with key findings",
            order=0,  # First tab
            enabled=True
        )
    
    def get_required_tables(self) -> list:
        return []  # Works with whatever is available
    
    def get_config(self) -> Dict[str, Any]:
        """Return module configuration."""
        return {
            "apply_global_filters": False,
            "apply_unit_conversion": False,
            "show_module_filters": False,
            "filterable_columns": ['scen', 'year'],
            "default_columns": []
        }
    
    def render(
        self,
        table_dfs: Dict[str, pd.DataFrame],
        filters: Dict[str, Any]
    ) -> None:
        """Render Key Insights dashboard."""
        
        st.header("Key Modelling Insights")
        st.info("This section provides high-level insights for stakeholders.")
        
        # Placeholder metrics
        st.markdown("---")
        st.subheader("📊 Key Performance Indicators")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="⚡ Total Energy",
                value="TBD",
                help="Total energy demand across scenarios"
            )
        
        with col2:
            st.metric(
                label="🌍 CO₂ Emissions",
                value="TBD",
                help="Total emissions"
            )
        
        with col3:
            st.metric(
                label="🌱 Renewable Share",
                value="TBD",
                help="Percentage renewable energy"
            )
        
        with col4:
            st.metric(
                label="💰 System Cost",
                value="TBD",
                help="Total system cost"
            )
        
        # Project information
        st.markdown("---")
        st.subheader("🗺️ SpeedLocal Project")
        st.markdown("""
        The SpeedLocal project focuses on energy system modeling across three regions:
        - **Trøndelag** (Norway)
        - **Vara** (Sweden)
        - **Bornholm** (Denmark)
        """)
        
        # Display images
        try:
            st.image("images/speed-local.jpg", caption="Speed Local", use_container_width=True)
        except FileNotFoundError:
            st.info("💡 Add `images/speed-local.jpg` to display project logo")
        
        try:
            col_a, col_b = st.columns(2)
            with col_a:
                st.image("images/map.png", caption="Project Regions")
        except FileNotFoundError:
            st.info("💡 Add `images/map.png` to display project map")
        
