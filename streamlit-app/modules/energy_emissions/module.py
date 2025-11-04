"""
Energy and Emissions visualization module.
Refactored from the original times_app_test.py Energy and Emissions tabs.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any
from pathlib import Path
import sys

# Import base module
sys.path.append(str(Path(__file__).parent.parent))
from base_module import BaseModule

# Import existing plotting functionality
sys.path.append(str(Path(__file__).parent.parent.parent / "utils"))
from _plotting import TimesReportPlotter


class EnergyEmissionsModule(BaseModule):
    """Energy and Emissions visualization module."""
    
    # Sectors to exclude (from original EXCLUDED_SECTORS)
    EXCLUDED_SECTORS = ['AFO', 'DMZ', 'SYS', 'DHT', 'ELT', 'TRD', 'UPS', 'NA', 'FTS']
    
    def __init__(self):
        super().__init__(
            name="Energy & Emissions",
            description="Annual reporting with sector-level analysis",
            order=1,
            enabled=True
        )
    
    def get_required_tables(self) -> list:
        return ["energy", "emissions"]
    
    def get_filter_config(self) -> Dict[str, Any]:
        return {
            "show_module_filters": False,
            "filterable_columns": ['sector', 'subsector', 'comgroup', 'year'],
            "default_columns": []
        }
    
    def render(
        self,
        table_dfs: Dict[str, pd.DataFrame],
        filters: Dict[str, Any],
        data_loader: Any
    ) -> None:
        """Main render method."""
        
        if not self.validate_data(table_dfs):
            self.show_error("Required data tables (energy/emissions) not available.")
            return
        
        # Get filter manager
        sys.path.append(str(Path(__file__).parent.parent.parent / "core"))
        from filter_manager import FilterManager
        
        filter_manager = FilterManager(table_dfs)
        generic_filter = filter_manager.get_generic_filter()
        
        # Get available sectors
        combined_df = pd.concat([df for df in table_dfs.values() if not df.empty], ignore_index=True)
        filtered_df = generic_filter.apply_filters(combined_df)
        sectors = self._get_available_sectors(filtered_df)
        
        # Create sub-tabs
        energy_tab, emissions_tab = st.tabs(["⚡ Energy", "🌍 Emissions"])
        
        with energy_tab:
            self._render_energy_section(table_dfs.get("energy"), generic_filter, sectors)
        
        with emissions_tab:
            self._render_emissions_section(table_dfs.get("emissions"), generic_filter, sectors)
    
    def _get_available_sectors(self, df: pd.DataFrame) -> list:
        if 'sector' not in df.columns:
            return []
        sectors = sorted(df['sector'].unique())
        return [s for s in sectors if s not in self.EXCLUDED_SECTORS]
    
    def _render_energy_section(self, df_energy, generic_filter, sectors):
        st.header("Energy Visualization")
        
        if df_energy is None or df_energy.empty:
            self.show_error("Energy data not available.")
            return
        
        df_energy_filtered = generic_filter.apply_filters(df_energy)
        
        if df_energy_filtered.empty:
            self.show_warning("No energy data available after applying filters.")
            return
        
        # Aggregate plot
        st.subheader("Aggregate Energy Plot (All Sectors)")
        selected_agg_sectors = st.multiselect(
            "Select sectors to include in aggregate plot",
            options=sectors,
            default=sectors,
            key="energy_agg_sectors"
        )
        
        if selected_agg_sectors:
            df_energy_agg = df_energy_filtered[
                (df_energy_filtered['sector'].isin(selected_agg_sectors)) &
                (df_energy_filtered['topic'] == 'energy') &
                (df_energy_filtered['attr'] == 'f_in')
            ]
            
            if not df_energy_agg.empty:
                energy_plotter = TimesReportPlotter(df_energy_agg)
                fig_energy_agg = energy_plotter.stacked_bar(
                    x_col="year",
                    y_col="value",
                    group_col="comgroup",
                    scenario_col="scen",
                    filter_dict=None,
                    title="Aggregate Energy Input"
                )
                if fig_energy_agg:
                    st.plotly_chart(fig_energy_agg, use_container_width=True)
        
        # Disaggregated plots
        st.subheader("Disaggregated Energy Plots per Sector")
        for sector in sectors:
            with st.expander(f"**{sector}**", expanded=False):
                df_sector = df_energy_filtered[
                    (df_energy_filtered['sector'] == sector) &
                    (df_energy_filtered['topic'] == 'energy') &
                    (df_energy_filtered['attr'] == 'f_in')
                ]
                
                if not df_sector.empty:
                    energy_plotter = TimesReportPlotter(df_sector)
                    fig = energy_plotter.stacked_bar(
                        x_col="year",
                        y_col="value",
                        group_col="comgroup",
                        scenario_col="scen",
                        filter_dict=None,
                        title=f"Energy Input for {sector}"
                    )
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"No data available for sector {sector}")
    
    def _render_emissions_section(self, df_emissions, generic_filter, sectors):
        st.header("Emissions Visualization")
        
        if df_emissions is None or df_emissions.empty:
            self.show_error("Emissions data not available.")
            return
        
        df_emissions_filtered = generic_filter.apply_filters(df_emissions)
        
        if df_emissions_filtered.empty:
            self.show_warning("No emissions data available after applying filters.")
            return
        
        # Aggregate plot
        st.subheader("Aggregate Emissions Plot (All Sectors)")
        selected_agg_sectors = st.multiselect(
            "Select sectors to include in aggregate plot",
            options=sectors,
            default=sectors,
            key="emission_agg_sectors"
        )
        
        if selected_agg_sectors:
            df_em_agg = df_emissions_filtered[
                (df_emissions_filtered['sector'].isin(selected_agg_sectors)) &
                (df_emissions_filtered['topic'] == "emission")
            ].groupby(['year', 'sector', 'scen'], as_index=False)['value'].sum()
            
            if not df_em_agg.empty:
                emission_plotter = TimesReportPlotter(df_em_agg)
                fig = emission_plotter.line_plot(
                    x_col="year",
                    y_col="value",
                    line_group_col="sector",
                    scenario_col="scen",
                    filter_dict=None,
                    title="Aggregate Emissions by Sector"
                )
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
        
        # Disaggregated plots
        st.subheader("Disaggregated Emission Plots per Sector")
        for sector in sectors:
            with st.expander(f"**{sector}**", expanded=False):
                df_sector = df_emissions_filtered[
                    (df_emissions_filtered['sector'] == sector) &
                    (df_emissions_filtered['topic'] == "emission")
                ].groupby(['year', 'comgroup', 'scen'], as_index=False)['value'].sum()
                
                if not df_sector.empty:
                    emission_plotter = TimesReportPlotter(df_sector)
                    fig = emission_plotter.line_plot(
                        x_col="year",
                        y_col="value",
                        line_group_col="comgroup",
                        scenario_col="scen",
                        filter_dict=None,
                        title=f"Emissions for {sector}"
                    )
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"No emission data for sector {sector}")
