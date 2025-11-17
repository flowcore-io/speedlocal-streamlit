"""
Key Insights module for stakeholder-facing dashboard.
Refactored from the Development tab in original times_app_test.py.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from base_module import BaseModule

# Import DuckDBQueryHelper for extract_desc_tables
sys.path.append(str(Path(__file__).parent.parent.parent / "utils"))
from _query_dynamic import DuckDBQueryHelper


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
    
    def get_filter_config(self) -> Dict[str, Any]:
        return {
            "apply_global_filters": True,
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
        
        """Render Development dashboard."""
        
        st.header("🔧 Development & Debug")
        st.info("This section is for development and debugging purposes.")
        
        # Get description data from session
        desc_df = self._get_desc_df()
        
        # Create two main sections
        debug_tab, desc_tab, data_tab = st.tabs(["🔍 Filter Debug", "📋 Description Tables", "📊 Data Inspector"])
        
        with debug_tab:
            self._render_filter_debug(table_dfs, filters)
        
        with desc_tab:
            self._render_description_tables(desc_df)

        with data_tab:
            self._render_data_inspector(table_dfs)
    
    def _render_filter_debug(
        self, 
        table_dfs: Dict[str, pd.DataFrame],
        filters: Dict[str, Any]
    ) -> None:
        """Render filter debug information."""
        
        st.subheader("Filter Debug Information")
        
        # Get filter config
        filter_config = self.get_filter_config()
        apply_global = filter_config.get('apply_global_filters', True)
        
        # Show filter status
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Global Filters Applied", value="Yes" if apply_global else "No")
        with col2:
            st.metric(label="Active Filter Count", value=len(filters))
        
        # Show active filters
        st.markdown("#### Active Filters")
        if filters:
            filter_df = pd.DataFrame([
                {"Column": col, "Selected Values": ", ".join(map(str, vals[:3])) + (f" (+{len(vals)-3} more)" if len(vals) > 3 else "")}
                for col, vals in filters.items()
            ])
            st.dataframe(filter_df, use_container_width=True, hide_index=True)
        else:
            st.info("No filters currently applied")
        
        # Show row counts
        st.markdown("#### Data Row Counts")
        
        combined_df = pd.concat([df for df in table_dfs.values() if not df.empty], ignore_index=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Total Rows (All Data)", value=f"{len(combined_df):,}")
        
        with col2:
            if filters:
                filtered_df = self._apply_filters(combined_df, filters)
                st.metric(
                    label="Filtered Rows", 
                    value=f"{len(filtered_df):,}",
                    delta=f"{len(filtered_df) - len(combined_df):,}"
                )
            else:
                st.metric(label="Filtered Rows", value=f"{len(combined_df):,}")
        
        with col3:
            if filters and len(combined_df) > 0:
                pct = (len(filtered_df) / len(combined_df)) * 100
                st.metric(label="% of Total Data", value=f"{pct:.1f}%")
            else:
                st.metric(label="% of Total Data", value="100%")
        
        # Show available tables
        st.markdown("#### Available Tables")
        table_info = []
        for table_name, df in table_dfs.items():
            table_info.append({
                "Table Name": table_name,
                "Rows": f"{len(df):,}",
                "Columns": len(df.columns),
                "Memory (MB)": f"{df.memory_usage(deep=True).sum() / 1024**2:.2f}"
            })
        
        if table_info:
            st.dataframe(pd.DataFrame(table_info), use_container_width=True, hide_index=True)
        
        # Detailed filter impact per table
        with st.expander("📊 Filter Impact by Table"):
            for table_name, df in table_dfs.items():
                if filters:
                    filtered_table = self._apply_filters(df, filters)
                    reduction = len(df) - len(filtered_table)
                    pct_reduction = (reduction / len(df) * 100) if len(df) > 0 else 0
                    
                    st.markdown(f"**{table_name}**: {len(df):,} → {len(filtered_table):,} rows "
                              f"({pct_reduction:.1f}% reduction)")
                else:
                    st.markdown(f"**{table_name}**: {len(df):,} rows (no filters)")
    
    def _render_description_tables(
        self,
        desc_df: pd.DataFrame
    ) -> None:
        """Render description tables from session data."""
        
        st.subheader("Description Tables")
        st.markdown("Tables ending with `_desc` contain human-readable descriptions for IDs used in the data.")
        
        if desc_df is None or desc_df.empty:
            st.warning("No description tables available.")
            st.info("Description tables are loaded at startup from the database.")
            return
        
        # Show summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Total Descriptions", value=f"{len(desc_df):,}")
        with col2:
            st.metric(label="Unique Sets", value=desc_df['set_name'].nunique())
        with col3:
            st.metric(label="Unique Elements", value=desc_df['element'].nunique())
        
        st.markdown("---")
        
        # Search/filter functionality
        st.markdown("#### Search & Filter")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Filter by set_name
            all_sets = ["All"] + sorted(desc_df['set_name'].unique().tolist())
            selected_set = st.selectbox(
                "Filter by Set Name",
                options=all_sets,
                key="dev_desc_set_filter"
            )
        
        with col2:
            # Search by element or description
            search_term = st.text_input(
                "Search Element or Description",
                placeholder="Type to search...",
                key="dev_desc_search"
            )
        
        # Apply filters
        filtered_desc = desc_df.copy()
        
        if selected_set != "All":
            filtered_desc = filtered_desc[filtered_desc['set_name'] == selected_set]
        
        if search_term:
            mask = (
                filtered_desc['element'].str.contains(search_term, case=False, na=False) |
                filtered_desc['description'].str.contains(search_term, case=False, na=False)
            )
            filtered_desc = filtered_desc[mask]
        
        # Show filtered count
        st.info(f"Showing {len(filtered_desc):,} of {len(desc_df):,} descriptions")
        
        # Display table
        st.markdown("#### Description Data")
        st.dataframe(
            filtered_desc,
            use_container_width=True,
            hide_index=True,
            column_config={
                "set_name": st.column_config.TextColumn("Set Name", width="medium"),
                "element": st.column_config.TextColumn("Element", width="medium"),
                "description": st.column_config.TextColumn("Description", width="large")
            }
        )
        
        # Download option
        st.markdown("---")
        csv = filtered_desc.to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv,
            file_name="description_tables.csv",
            mime="text/csv"
        )   
    def _render_data_inspector(
        self,
        table_dfs: Dict[str, pd.DataFrame]
    ) -> None:
        """Render data inspector to view loaded dataframes."""
        
        st.subheader("📊 Data Inspector")
        st.markdown("Inspect dataframes loaded by `PandasDFCreator` from `mapping_db_views.csv`")
        
        if not table_dfs:
            st.warning("No dataframes available. Please reload data.")
            return
        
        # Show summary metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Total Tables", value=len(table_dfs))
        with col2:
            total_rows = sum(len(df) for df in table_dfs.values())
            st.metric(label="Total Rows (All Tables)", value=f"{total_rows:,}")
        
        st.markdown("---")
        
        # Dropdown to select table
        table_names = list(table_dfs.keys())
        selected_table = st.selectbox(
            "Select Table to Inspect",
            options=table_names,
            key="dev_data_inspector_table"
        )
        
        if selected_table:
            df = table_dfs[selected_table]
            
            # Show table info
            st.markdown(f"### Table: `{selected_table}`")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(label="Rows", value=f"{len(df):,}")
            with col2:
                st.metric(label="Columns", value=len(df.columns))
            with col3:
                memory_mb = df.memory_usage(deep=True).sum() / 1024**2
                st.metric(label="Memory (MB)", value=f"{memory_mb:.2f}")
            with col4:
                # Count unique values in key columns if they exist
                if 'sector' in df.columns:
                    unique_sectors = df['sector'].nunique()
                    st.metric(label="Unique Sectors", value=unique_sectors)
            
            # Show column info
            with st.expander("📋 Column Information", expanded=False):
                col_info = []
                for col in df.columns:
                    col_info.append({
                        "Column": col,
                        "Type": str(df[col].dtype),
                        "Non-Null": f"{df[col].notna().sum():,}",
                        "Null": f"{df[col].isna().sum():,}",
                        "Unique": f"{df[col].nunique():,}"
                    })
                st.dataframe(
                    pd.DataFrame(col_info),
                    use_container_width=True,
                    hide_index=True
                )
            
            # Search/filter functionality
            st.markdown("#### Filter Data")
            
            # Let user filter by any column
            filter_col = st.selectbox(
                "Filter by column (optional)",
                options=["None"] + list(df.columns),
                key="dev_inspector_filter_col"
            )
            
            filtered_df = df.copy()
            
            if filter_col != "None":
                unique_values = df[filter_col].dropna().unique()
                if len(unique_values) <= 50:  # Only show multiselect if reasonable number
                    selected_values = st.multiselect(
                        f"Select values for {filter_col}",
                        options=sorted(unique_values.tolist()),
                        key="dev_inspector_filter_values"
                    )
                    if selected_values:
                        filtered_df = filtered_df[filtered_df[filter_col].isin(selected_values)]
                else:
                    st.info(f"Column has {len(unique_values)} unique values. Use search below instead.")
            
            # Show row count after filtering
            st.info(f"Showing {len(filtered_df):,} of {len(df):,} rows")
            
            # Display dataframe
            st.markdown("#### Data Preview")
            st.dataframe(
                filtered_df,
                use_container_width=True,
                height=400
            )
            
            # Download option
            st.markdown("---")
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label=f"📥 Download {selected_table} as CSV",
                data=csv,
                file_name=f"{selected_table}_data.csv",
                mime="text/csv",
                key="dev_inspector_download"
            )