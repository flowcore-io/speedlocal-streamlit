"""
Development module for debugging.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from base_module import BaseModule


class DevelopmentModule(BaseModule):
    """Development tab for testing."""
    
    def __init__(self):
        super().__init__(
            name="Development",
            description="Debug information and data exploration tools",
            order=999,  # always last tab
            enabled=True
        )
    
    def get_required_tables(self) -> list:
        return []  # Works with whatever is available
    
    def get_config(self) -> Dict[str, Any]:
        """Return module configuration."""
        return {
            "apply_global_filters": True,
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
        """Render Development dashboard."""
        
        st.header("🔧 Development & Debug")
        st.info("This section is for development and debugging purposes.")
        
        # Get description data from session
        desc_df = self._get_desc_df()
        
        # Create tabs
        debug_tab, desc_tab, data_tab = st.tabs([
            "🔍 Filter Debug", 
            "📋 Description Tables", 
            "📊 Data Inspector"
        ])
        
        with debug_tab:
            self._render_filter_debug(table_dfs, filters)
        
        with desc_tab:
            self._render_description_tables(desc_df)

        with data_tab:
            self._render_data_inspector(table_dfs, filters)
    
    def _render_filter_debug(self, table_dfs: Dict[str, pd.DataFrame], filters: Dict[str, Any]) -> None:
        """Render filter debugging information."""
        st.subheader("Active Filters")
        
        if filters:
            st.json(filters)
        else:
            st.info("No filters currently active")
        
        st.subheader("Available Tables")
        st.write(f"Total tables: {len(table_dfs)}")
        
        for table_name, df in table_dfs.items():
            # Apply filters to show filtered row count
            df_filtered = self._apply_filters(df, filters)
            
            with st.expander(f"📊 {table_name} ({len(df_filtered):,} / {len(df):,} rows after filtering)"):
                st.write(f"**Columns:** {', '.join(df.columns.tolist())}")
                st.write(f"**Shape (unfiltered):** {df.shape}")
                st.write(f"**Shape (filtered):** {df_filtered.shape}")
                st.dataframe(df_filtered.head(10))
    
    def _render_description_tables(self, desc_df: pd.DataFrame) -> None:
        """Render description tables."""
        st.subheader("Description Mappings")
        
        if desc_df.empty:
            st.warning("No description data available")
            return
        
        # Search functionality
        search = st.text_input("🔍 Search descriptions", "")
        
        if search:
            mask = desc_df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)
            filtered_df = desc_df[mask]
            st.write(f"Found {len(filtered_df)} matches")
            st.dataframe(filtered_df, use_container_width=True)
        else:
            st.dataframe(desc_df, use_container_width=True)
        
        # Summary stats
        st.subheader("Summary")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Descriptions", len(desc_df))
        with col2:
            if 'set_name' in desc_df.columns:
                st.metric("Unique Sets", desc_df['set_name'].nunique())
    
    def _render_data_inspector(self, table_dfs: Dict[str, pd.DataFrame], filters: Dict[str, Any]) -> None:
        """Render data inspector."""
        st.subheader("Data Inspector")
        
        if not table_dfs:
            st.warning("No data tables available")
            return
        
        # Table selector
        selected_table = st.selectbox(
            "Select table to inspect:",
            options=list(table_dfs.keys())
        )
        
        if selected_table:
            df = table_dfs[selected_table]
            
            df_filtered = self._apply_filters(df, filters)
            
            # Show filtering info
            if len(df_filtered) < len(df):
                st.info(f"Filtered from {len(df):,} rows to {len(df_filtered):,} rows")
            
            # Show basic info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Rows (filtered)", len(df_filtered))
            with col2:
                st.metric("Columns", len(df_filtered.columns))
            with col3:
                st.metric("Memory", f"{df_filtered.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
            
            # Column information
            st.subheader("Column Information")
            col_info = pd.DataFrame({
                'Column': df_filtered.columns,
                'Type': df_filtered.dtypes.astype(str),
                'Non-Null': df_filtered.count(),
                'Unique': [df_filtered[col].nunique() for col in df_filtered.columns]
            })
            st.dataframe(col_info, use_container_width=True)
            
            # Sample data
            st.subheader("Sample Data")
            n_rows = st.slider("Number of rows to display", 5, 100, 10)
            st.dataframe(df_filtered.head(n_rows), use_container_width=True)