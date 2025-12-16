"""
Development module for debugging.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional
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
            "show_module_filters": True,
            "filterable_columns": ['scen', 'year', 'all_ts', 'prc'],
            "default_columns": []
        }
    
    def render(
        self,
        table_dfs: Dict[str, pd.DataFrame],
        filters: Dict[str, Any]
    ) -> None:
        """Render Development dashboard."""
        
        st.header("🔧 Development & Debug")
        
        # Get description data from session
        desc_df = self._get_desc_df()
        
        # Create tabs
        debug_tab, desc_tab, data_tab = st.tabs([
            "🔍 Filter Debug", 
            "📋 Description Tables", 
            "📊 Data Inspector"
            # "🧪 Plot Tester"
        ])
        
        with debug_tab:
            self._render_filter_debug(table_dfs, filters)
        
        with desc_tab:
            self._render_description_tables(desc_df)

        with data_tab:
            self._render_data_inspector(table_dfs, filters)
        
        # with plot_test_tab: 
        #     self._render_plot_tester(table_dfs)
    
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
            st.divider()
            st.subheader("Generate Unique Mapping Template")
            
            st.info(
                "This tool generates a unique combination of data identifiers "
                "originally for subannual graphs, but not being used currently. "
                "The original idea was that the type of graph would be different " \
                "depending on plot_group column if it's production, consumption, or storage."
            )
            
            # Check if this looks like a time series table
            has_timeseries = 'all_ts' in df_filtered.columns
            
            if has_timeseries:
                self._render_profile_mapping_generator(df_filtered, selected_table)
            else:
                st.warning(f"Table '{selected_table}' doesn't have 'all_ts' column. Select a time series table.")
                
    def _render_profile_mapping_generator(
        self,
        df: pd.DataFrame,
        table_name: str
    ) -> None:
        """
        Generate profile_mapping.csv template from time series data.
        
        Uses existing 'label' column from data and applies description mapping.
        """
        st.write("**Configuration:**")
        
        # Check if label column exists
        if 'label' not in df.columns:
            st.error("This table doesn't have a 'label' column. Cannot generate profile mapping.")
            return
        
        # Define columns to exclude from grouping
        default_exclude = ['scen', 'value', 'file_id', 'year', 'all_ts', 'unit', 'cur']
        
        # Let user choose which columns to include
        available_cols = [col for col in df.columns if col not in default_exclude]
        
        col1, col2 = st.columns(2)
        
        with col1:
            grouping_cols = st.multiselect(
                "Columns to include in mapping:",
                options=available_cols,
                default=available_cols,
                key="profile_mapping_cols",
                help="Select which columns to include in the profile mapping"
            )
        
        with col2:
            # Default plot group
            default_plot_group = st.text_input(
                "Default plot group:",
                value="production",
                key="profile_mapping_plot_group",
                help="Default plot group for all series (can be edited in CSV)"
            )
        
        if not grouping_cols:
            st.warning("Select at least one column")
            return
        
        # Generate unique combinations
        try:
            # Get unique combinations
            unique_combinations = df[grouping_cols].drop_duplicates().reset_index(drop=True)

            # ALWAYS initialize label_with_desc (fallback to original)
            unique_combinations['label_with_desc'] = unique_combinations['label']

            # Apply description mapping to the 'label' column
            desc_mapping = self._get_desc_mapping()

            if desc_mapping and 'label' in unique_combinations.columns:
                # Get label source from mapping_db_views.csv
                label_source = self._detect_label_source_from_mapping(table_name)
                
                if label_source:
                    st.info(f"📋 Label source: **{label_source}**")
                    
                    if label_source in desc_mapping:
                        # Apply the description mapping
                        unique_combinations['label_with_desc'] = unique_combinations['label'].map(
                            desc_mapping[label_source]
                        ).fillna(unique_combinations['label'])  # ← This overwrites the fallback
                        
                        st.success(f"✅ Applied {len(unique_combinations)} {label_source} descriptions")
                        
                    else:
                        st.warning(f"⚠️ No description mapping available for '{label_source}'")
                else:
                    st.error(f"❌ Could not determine label source from mapping_db_views.csv for table '{table_name}'")
            else:
                st.warning("No description mapping available")

            # Prepare final mapping dataframe
            n_rows = len(unique_combinations)

            mapping_df = pd.DataFrame({
                'table': [table_name] * n_rows,
                'label': unique_combinations['label_with_desc'].tolist(),  # ← Make sure this is here
                'plot_group': [default_plot_group] * n_rows,
                'color': [''] * n_rows
            })

            # Add ALL the original columns as-is (except 'label' which we already added with descriptions)
            for col in grouping_cols:
                if col != 'label':  # ← SKIP 'label' - we already added it with descriptions
                    mapping_df[col] = unique_combinations[col].tolist()
            
            # Show preview
            st.write(f"**Generated {len(mapping_df)} unique series:**")
            st.dataframe(mapping_df, use_container_width=True)
            
            # Show statistics
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Unique Series", len(mapping_df))
            with col_b:
                if 'label' in grouping_cols:
                    st.metric("Unique Labels", unique_combinations['label'].nunique())
            
            # Download button
            csv_data = mapping_df.to_csv(index=False)
            
            st.download_button(
                label="📥 Download as profile_mapping.csv",
                data=csv_data,
                file_name=f"profile_mapping_{table_name}.csv",
                mime="text/csv",
                help="Download this CSV and place it in your module's config folder"
            )
            
        except Exception as e:
            st.error(f"Error generating mapping: {str(e)}")
            st.exception(e)
    
    def _detect_label_source_from_mapping(self, table_name: str) -> Optional[str]:
        """
        Determine what column the 'label' comes from by reading mapping_db_views.csv
        
        Returns the column name (e.g., 'subsector', 'techgroup') or None
        """
        try:
            # Try to find the mapping CSV
            mapping_csv_path = Path("inputs/mapping_db_views.csv")
            
            if not mapping_csv_path.exists():
                return None
            
            # Read the mapping CSV
            mapping_df = pd.read_csv(mapping_csv_path)
            
            # Find rows for this table
            table_rows = mapping_df[mapping_df['table'] == table_name]
            
            if table_rows.empty:
                return None
            
            # Get the label column specification
            label_spec = table_rows['label'].dropna().unique()
            
            if len(label_spec) > 0:
                label_source = str(label_spec[0]).strip().lower()
                
                # Common label sources
                valid_sources = [
                    'subsector', 'sector', 'techgroup', 'comgroup', 
                    'prc', 'com', 'service', 'topic', 'attr'
                ]
                
                if label_source in valid_sources:
                    return label_source
            
            return None
            
        except Exception as e:
            st.error(f"Error reading mapping CSV: {e}")
            return None
    