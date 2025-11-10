"""
Reusable layout components for data visualization.
Contains common layout patterns used across multiple modules.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List
from pathlib import Path
import sys

# Import existing plotting functionality
sys.path.append(str(Path(__file__).parent.parent))
from _plotting import TimesReportPlotter


def agg_disagg_layout(
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
        
        # Aggregate data by year, scenario, and grouping column
        df_agg = df_agg.groupby(
            ['year', 'scen', config['group_col_aggregate']], 
            as_index=False
        )['value'].sum()

        if not df_agg.empty:
            plotter = TimesReportPlotter(df_agg)
            
            # Replace the if/elif block with single plot call
            fig = plotter.plot(
                method=config['plot_method'],
                x_col="year",
                y_col="value",
                group_col=config['group_col_aggregate'],
                scenario_col="scen",
                filter_dict=None,
                title=f"Aggregate {config['title']}",
                height=600
            )
            
            if fig:
                st.plotly_chart(fig, use_container_width=True, key=f"{section_key}_agg_chart")
        else:
            st.warning("No data available for selected sectors.")
    
    # --- DISAGGREGATED PLOTS PER SECTOR ---
    st.subheader(f"Disaggregated {config['title']} per Sector")
    
    for sector in sectors:
        sector_display = desc_mapping.get('sector', {}).get(sector, sector) if desc_mapping else sector
        
        with st.expander(f"**{sector_display} ({sector})**", expanded=False):
            df_sector = df[df['sector'] == sector]
            
            # Aggregate data by year, scenario, and grouping column
            df_sector = df_sector.groupby(
                ['year', 'scen', config['group_col_disaggregate']], 
                as_index=False
            )['value'].sum()
            
            if not df_sector.empty:
                plotter = TimesReportPlotter(df_sector)
                
                # Replace the if/elif block with single plot call
                fig = plotter.plot(
                    method=config['plot_method'],
                    x_col="year",
                    y_col="value",
                    group_col=config['group_col_disaggregate'],
                    scenario_col="scen",
                    filter_dict=None,
                    title=f"{config['title']} for {sector_display}",
                    height=600
                )
                
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key=f"{section_key}_disagg_{sector}")
            else:
                st.info(f"No data available for sector {sector}")