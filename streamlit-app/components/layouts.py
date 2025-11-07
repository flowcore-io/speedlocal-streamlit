"""
Reusable component for aggregate/disaggregate sector analysis layout.
Displays an aggregate plot (all sectors) and disaggregated plots (per sector).
"""

import streamlit as st
import pandas as pd
from typing import Dict, List
from pathlib import Path
import sys

# Import existing plotting functionality
sys.path.append(str(Path(__file__).parent.parent))
from _plotting import TimesReportPlotter


def render_agg_disagg_layout(
    df: pd.DataFrame,
    sectors: List[str],
    config: Dict[str, str],
    desc_mapping: Dict[str, Dict[str, str]],
    section_key: str
) -> None:
    """
    Render aggregate and disaggregate sector analysis.
    
    Args:
        df: DataFrame with data already filtered and descriptions applied
        sectors: List of sector IDs to display
        config: Configuration dict with keys:
            - plot_method: 'stacked_bar' or 'line_plot'
            - group_col_aggregate: Column name for aggregate plot grouping
            - group_col_disaggregate: Column name for disaggregate plot grouping
            - title: Title prefix for plots
        desc_mapping: Description mapping for display names (sector -> readable name)
        section_key: Unique key prefix for Streamlit widgets
    """
    
    if df.empty:
        st.warning(f"No data available for {config.get('title', 'analysis')}")
        return
    
    # --- AGGREGATE PLOT ---
    st.subheader(f"Aggregate {config['title']} (All Sectors)")
    
    selected_agg_sectors = st.multiselect(
        "Select sectors to include in aggregate plot",
        options=sectors,
        format_func=lambda x: f"{desc_mapping.get('sector', {}).get(x, x)} ({x})" if desc_mapping else x,
        default=sectors,
        key=f"{section_key}_agg_sectors"
    )
    
    if selected_agg_sectors:
        # Filter for selected sectors
        df_agg = df[df['sector'].isin(selected_agg_sectors)]
        
        if not df_agg.empty:
            plotter = TimesReportPlotter(df_agg)
            
            # Create plot based on method
            if config['plot_method'] == 'stacked_bar':
                fig = plotter.stacked_bar(
                    x_col="year",
                    y_col="value",
                    group_col=config['group_col_aggregate'],
                    scenario_col="scen",
                    filter_dict=None,
                    title=f"Aggregate {config['title']}"
                )
            elif config['plot_method'] == 'line_plot':
                fig = plotter.line_plot(
                    x_col="year",
                    y_col="value",
                    line_group_col=config['group_col_aggregate'],
                    scenario_col="scen",
                    filter_dict=None,
                    title=f"Aggregate {config['title']}"
                )
            else:
                st.error(f"Unknown plot method: {config['plot_method']}")
                return
            
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data available for selected sectors.")
    
    # --- DISAGGREGATED PLOTS PER SECTOR ---
    st.subheader(f"Disaggregated {config['title']} per Sector")
    
    for sector in sectors:
        # Get readable sector name for expander
        sector_display = desc_mapping.get('sector', {}).get(sector, sector) if desc_mapping else sector
        
        with st.expander(f"**{sector_display} ({sector})**", expanded=False):
            df_sector = df[df['sector'] == sector]
            
            if not df_sector.empty:
                plotter = TimesReportPlotter(df_sector)
                
                # Create plot based on method
                if config['plot_method'] == 'stacked_bar':
                    fig = plotter.stacked_bar(
                        x_col="year",
                        y_col="value",
                        group_col=config['group_col_disaggregate'],
                        scenario_col="scen",
                        filter_dict=None,
                        title=f"{config['title']} for {sector_display}"
                    )
                elif config['plot_method'] == 'line_plot':
                    fig = plotter.line_plot(
                        x_col="year",
                        y_col="value",
                        line_group_col=config['group_col_disaggregate'],
                        scenario_col="scen",
                        filter_dict=None,
                        title=f"{config['title']} for {sector_display}"
                    )
                else:
                    st.error(f"Unknown plot method: {config['plot_method']}")
                    continue
                
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"No data available for sector {sector}")