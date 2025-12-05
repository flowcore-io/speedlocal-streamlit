"""
Time Profile Module for hourly/sub-annual time series visualization.
"""

import streamlit as st
import pandas as pd
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from modules.base_module import BaseModule
from modules.time_profile.transformer import TimeProfileTransformer
from utils._plotting import TimesReportPlotter


class TimeProfileModule(BaseModule):
    """Time series profile visualization module."""
    
    def __init__(self):
        super().__init__(
            name="Time Profile",
            description="Hourly/sub-annual time series visualization",
            order=3,
            enabled=True
        )
        
        # Load configuration
        self.config_dir = Path(__file__).parent / "config"
        self.profile_config = self._load_profile_config()
        self.profile_mapping = self._load_profile_mapping()
        
        # Initialize transformer
        self.transformer = TimeProfileTransformer(self.profile_config)
    
    def _load_profile_config(self) -> Dict:
        """Load profile_config.yaml."""
        config_path = self.config_dir / "profile_config.yaml"
        
        if not config_path.exists():
            st.warning(f"Config file not found: {config_path}")
            return {}
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _load_profile_mapping(self) -> pd.DataFrame:
        """Load profile_mapping.csv."""
        mapping_path = self.config_dir / "profile_mapping.csv"
        
        if not mapping_path.exists():
            st.warning(f"Mapping file not found: {mapping_path}")
            return pd.DataFrame()
        
        return pd.read_csv(mapping_path)
    
    def get_required_tables(self) -> list:
        """Return list of required tables from mapping."""
        if self.profile_mapping.empty:
            return []
        
        return self.profile_mapping['table'].unique().tolist()
    
    def get_config(self) -> Dict[str, Any]:
        """Return module configuration."""
        return {
            "apply_global_filters": True,
            "apply_unit_conversion": True,
            "show_module_filters": True,
            "filterable_columns": ['regfrom'],
            "default_columns": []
        }
    
    def render(
        self,
        table_dfs: Dict[str, pd.DataFrame],
        filters: Dict[str, Any]
    ) -> None:
        """Main render method."""
        
        st.header("⏱️ Time Series Profile")
        
        # Validate data
        if not self.validate_data(table_dfs):
            self.show_error("Required data tables not available.")
            return
        
        if self.profile_mapping.empty:
            self.show_error("Profile mapping not configured.")
            return
        
        # Get unit manager from session
        unit_mgr = st.session_state.get('unit_manager')
        
        # Render unit controls
        unit_config = None
        if unit_mgr:
            unit_config = unit_mgr.render_unit_controls_if_enabled(
                module=self,
                table_dfs=table_dfs,
                expanded=False
            )
        
        # Add to filters
        if unit_config:
            filters['unit_config'] = unit_config
        
        st.divider()
        
        # Show conversion summary
        if unit_config and unit_mgr:
            unit_mgr.show_conversion_summary()
        
        # Combine all required tables
        df_combined = self._combine_tables(table_dfs)
        
        if df_combined.empty:
            self.show_warning("No data available from required tables.")
            return
        
        # Apply global filters
        df_filtered = self._apply_filters(df_combined, filters)
        
        if df_filtered.empty:
            self.show_warning("No data after applying filters.")
            return
        
        # Apply unit conversion
        df_converted = self._apply_unit_conversion_if_enabled(df_filtered, filters)
        
        if df_converted.empty:
            self.show_warning("No data after unit conversion.")
            return
        
        # Render time profile interface
        self._render_time_profile_interface(df_converted, filters)
    
    def _combine_tables(self, table_dfs: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Combine required tables into single DataFrame."""
        dfs_to_combine = []
        
        for table_name in self.get_required_tables():
            if table_name in table_dfs:
                df = table_dfs[table_name].copy()
                
                # Filter out ANNUAL timesteps
                if 'all_ts' in df.columns:
                    df = df[df['all_ts'] != 'ANNUAL']
                
                # Apply description mapping to label column
                # The label column can contain any type of ID (techgroup, comgroup, sector, etc.)
                # We need to detect what type it is and apply the appropriate description mapping
                desc_mapping = self._get_desc_mapping()
                
                if desc_mapping and 'label' in df.columns:
                    # Get unique label values to determine what they represent
                    sample_labels = df['label'].dropna().unique()[:10]
                    
                    # Try to find which description set matches
                    # Check common columns: techgroup, comgroup, sector, subsector, prc, com
                    possible_desc_types = ['techgroup', 'comgroup', 'sector', 'subsector', 
                                        'service', 'prc', 'com', 'topic', 'attr']
                    
                    for desc_type in possible_desc_types:
                        if desc_type in desc_mapping:
                            desc_dict = desc_mapping[desc_type]
                            
                            # Check if any sample labels exist in this description dict
                            matches = sum(1 for label in sample_labels if label in desc_dict)
                            
                            # If we find matches, apply this mapping
                            if matches > 0:
                                df['label'] = df['label'].map(desc_dict).fillna(df['label'])
                                break
                
                dfs_to_combine.append(df)
        
        if not dfs_to_combine:
            return pd.DataFrame()
        
        return pd.concat(dfs_to_combine, ignore_index=True)
    
    def _apply_unit_conversion_if_enabled(
        self,
        df: pd.DataFrame,
        filters: Dict[str, Any]
    ) -> pd.DataFrame:
        """Apply unit conversion if enabled."""
        unit_mgr = st.session_state.get('unit_manager')
        
        if unit_mgr and 'unit_config' in filters:
            unit_config = unit_mgr.get_unit_config_from_filters(filters)
            df_converted, _ = unit_mgr.apply_unit_conversion(
                df,
                unit_config,
                section_title="Time Profile"
            )
            return df_converted
        
        return df
    
    def _render_time_profile_interface(
        self,
        df: pd.DataFrame,
        filters: Dict[str, Any]
    ) -> None:
        """Render time profile visualization interface."""
        self._show_available_labels(df)
        
        # Create filter controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Scenario filter (from global filters)
            scenarios = sorted(df['scen'].unique())
            selected_scenario = st.selectbox(
                "Scenario",
                options=scenarios,
                key="timeprofile_scenario"
            )
        
        with col2:
            # Year filter
            years = sorted(df['year'].unique())
            selected_year = st.selectbox(
                "Year",
                options=years,
                index=len(years)-1 if years else 0,  # Default to last year
                key="timeprofile_year"
            )
        
        with col3:
            # Region filter (if available)
            if 'regfrom' in df.columns:
                regions = sorted(df['regfrom'].unique())
                
                # Option to aggregate or show specific regions
                aggregate_regions = st.checkbox(
                    "Aggregate all regions",
                    value=True,
                    key="timeprofile_aggregate"
                )
                
                if not aggregate_regions:
                    selected_regions = st.multiselect(
                        "Select regions",
                        options=regions,
                        default=regions,
                        key="timeprofile_regions"
                    )
                else:
                    selected_regions = None
            else:
                selected_regions = None
                aggregate_regions = True
        
        # Filter data by selections
        df_plot = df[
            (df['scen'] == selected_scenario) &
            (df['year'] == selected_year)
        ].copy()
        
        if df_plot.empty:
            self.show_warning("No data for selected filters.")
            return
        
        # Aggregate regions if needed
        if aggregate_regions or selected_regions:
            df_plot = self.transformer.aggregate_regions(
                df_plot,
                selected_regions=selected_regions,
                region_col='regfrom'
            )
        
        if df_plot.empty:
            self.show_warning("No data after region aggregation.")
            return

        # Transform to wide format
        df_wide = self.transformer.transform_to_wide(
            df_plot,
            timeseries_col='all_ts',
            label_col='label',
            value_col='value',
            index_cols=['scen', 'year']
        )
        
        if df_wide.empty:
            self.show_warning("Failed to transform data to wide format.")
            return
        
        # Get plot categories
        plot_categories = self.transformer.get_plot_categories(
            df_wide,
            self.profile_mapping,
            timeseries_col='all_ts'
        )
        
        if not plot_categories:
            self.show_warning("No plot categories matched from mapping.")
            return
        
        # Get unit information
        unit_info = self.transformer.get_unit_info(
            df_plot,
            plot_categories,
            label_col='label'
        )
        
        # Show data summary
        st.metric(
            "Time Steps",
            len(df_wide),
            help="Number of hourly/sub-annual time steps"
        )
        
        # Create plot
        st.subheader(f"Profile: {selected_scenario} — {selected_year}")
        
        with st.spinner("Generating time series plot..."):
            try:
                plotter = TimesReportPlotter(df_wide)
                
                fig = plotter.stacked_timeseries(
                    time_col='all_ts',
                    categories=plot_categories,
                    config=self.profile_config,
                    unit_info=unit_info,
                    title=f"Time Profile: {selected_scenario} ({selected_year})"
                )
                
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    self.show_error("Failed to create plot.")
                    
            except Exception as e:
                self.show_error(f"Error creating plot: {str(e)}")
                st.exception(e)
    
    def _show_available_labels(self, df: pd.DataFrame) -> None:
        """Debug helper: Show available labels after description mapping."""
        if 'label' in df.columns:
            labels = sorted(df['label'].unique())
            
            with st.expander("🔍 Available Labels (for profile_mapping.csv)", expanded=False):
                st.write("Copy these into `profile_mapping.csv`:")
                st.code("\n".join([f"energy_subannual,{label},production," for label in labels]))