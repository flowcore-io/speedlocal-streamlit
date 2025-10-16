import streamlit as st
from pathlib import Path
import pandas as pd
from utils._query_with_csv import PandasDFCreator
from utils._plotting import TimesReportPlotter
from utils._query_dynamic import GenericFilter
from utils._streamlit_ui import SidebarConfig, ST_PandasDFLoader, FilterUI


EXCLUDED_SECTORS = ['AFO','DMZ','SYS','DHT','ELT','TRD','UPS','NA','FTS']

def main(mapping_csv: str):
    """Main Streamlit UI using preloaded Pandas DataFrames for plotting."""
    
    st.set_page_config(page_title="SpeedLocal: TIMES Data Explorer", layout="wide")
    st.title("SpeedLocal: TIMES Data Explorer (beta version) !")

     # Render sidebar configuration
    sidebar = SidebarConfig()
    config = sidebar.render()
    
    # Exit if configuration is invalid
    if not config['valid']:
        return
    
    # Handle data loading with reload logic
    if config['reload_requested']:
        # Clear all session state when reloading
        for key in ['table_dfs', 'loader', 'generic_filter', 'filter_ui']:
            if key in st.session_state:
                del st.session_state[key]
    
    # Load data if not already in session state
    if 'table_dfs' not in st.session_state:
        loader = ST_PandasDFLoader(
            db_source=config['db_source'],
            mapping_csv=mapping_csv, 
            is_url=config['is_url']
        )
        st.session_state['table_dfs'] = loader.load_dataframes()
        st.session_state['loader'] = loader
    
    # Get data from session state
    table_dfs = st.session_state.get('table_dfs', {})
    loader = st.session_state.get('loader')
    
    # Exit if no data was loaded
    if not table_dfs:
        return
    
    # Get specific tables
    df_energy = loader.get_table("energy") if loader else table_dfs.get("energy")
    df_emissions = loader.get_table("emissions") if loader else table_dfs.get("emissions")

    # Combine all DataFrames for filtering (or use a specific one)
    # Using energy table as the base for filters, but you can combine multiple tables
    first_table_df = None
    if table_dfs:
        first_table_name = list(table_dfs.keys())[0]
        first_table_df = table_dfs[first_table_name]
    
    if first_table_df is None or first_table_df.empty:
        st.error("No data available for filtering.")
        return
    
    # Define filterable columns (customize based on your needs)
    filterable_columns = ['scen', 'sector', 'subsector', 'comgroup', 'topic', 'attr', 'year']
    
    # Initialize GenericFilter if not in session state
    if 'generic_filter' not in st.session_state:
        st.session_state['generic_filter'] = GenericFilter(
            df=first_table_df,
            filterable_columns=filterable_columns
        )
    
    generic_filter = st.session_state['generic_filter']
    
    # Initialize FilterUI if not in session state
    if 'filter_ui' not in st.session_state:
        st.session_state['filter_ui'] = FilterUI(
            generic_filter=generic_filter,
            default_columns=['scen'],  # Default to showing scenario filter
            section_title="Data Filters"
        )
    
    filter_ui = st.session_state['filter_ui']
    
    # Render filter UI and get active filters
    active_filters = filter_ui.render()
    
    # Apply filters to get sectors list (excluding certain sectors)
    if first_table_df is not None and not first_table_df.empty:
        # Apply filters to the dataframe
        filtered_df = generic_filter.apply_filters(first_table_df)
        
        if 'sector' in filtered_df.columns:
            sectors = sorted(filtered_df['sector'].unique())
            sectors = [s for s in sectors if s not in EXCLUDED_SECTORS]
        else:
            sectors = []
            st.sidebar.warning("'sector' column not found in data.")
    else:
        sectors = []
        st.sidebar.warning("No data available for filters.")

    # Tabs for topics
    topic_tabs = st.tabs(["Energy", "Emissions", "Development"])

    # ---------------------- ENERGY TAB ----------------------
    with topic_tabs[0]:
        st.header("Energy Visualization")

        # --- Top-level aggregate plot ---
        st.subheader("Aggregate Energy Plot (All Sectors)")
        selected_agg_sectors = st.multiselect(
            "Select sectors to include in aggregate plot",
            options=sectors,
            default=sectors
        )

        energy_plotter = TimesReportPlotter(df_energy)
        fig_energy_agg = energy_plotter.stacked_bar(
            x_col="year",
            y_col="value",
            group_col="comgroup",
            scenario_col="scen",
            filter_dict={"sector": selected_agg_sectors, "topic": "energy", "attr": "f_in"},
            title="Aggregate Energy Input"
        )
        if fig_energy_agg:
            st.plotly_chart(fig_energy_agg, use_container_width=True)
        else:
            st.warning("No data for selected sectors in aggregate plot.")

        # --- Bottom-level disaggregated plots per sector ---
        st.subheader("Disaggregated Energy Plots per Sector")
        for sector in sectors:
            st.markdown(f"**{sector}**")
            fig_energy_sector = energy_plotter.stacked_bar(
                x_col="year",
                y_col="value",
                group_col="comgroup",
                scenario_col="scen",
                filter_dict={"sector": sector, "topic": "energy", "attr": "f_in"},
                title=f"Energy Input for {sector}"
            )
            if fig_energy_sector:
                st.plotly_chart(fig_energy_sector, use_container_width=True)
            else:
                st.warning(f"No energy data for sector {sector}.")

    # ---------------------- EMISSIONS TAB ----------------------
    with topic_tabs[1]:
        st.header("Emissions Visualization")

        # --- Top-level aggregate plot ---
        st.subheader("Aggregate Emissions Plot (All Sectors)")
        selected_agg_sectors = st.multiselect(
            "Select sectors to include in aggregate plot",
            options=sectors,
            default=sectors,
            key="emission_agg"
        )

        if selected_agg_sectors:
            # Aggregate values per sector and scenario
            df_em_agg = df_emissions[
                (df_emissions['sector'].isin(selected_agg_sectors)) &
                (df_emissions['topic'] == "emission")
            ].groupby(['year', 'sector', 'scen'], as_index=False)['value'].sum()

            # Create a dummy 'sector' as line_group_col
            emission_plotter = TimesReportPlotter(df_em_agg)
            fig_emission_agg = emission_plotter.line_plot(
                x_col="year",
                y_col="value",
                line_group_col="sector",  # one line per sector
                scenario_col="scen",
                filter_dict=None,  # already filtered/aggregated
                title="Aggregate Emissions by Sector"
            )
            if fig_emission_agg:
                st.plotly_chart(fig_emission_agg, use_container_width=True)
            else:
                st.warning("No data for selected sectors in aggregate plot.")

        # --- Bottom-level disaggregated plots per sector ---
        st.subheader("Disaggregated Emission Plots per Sector")
        for sector in sectors:
            st.markdown(f"**{sector}**")
            # Aggregate per comgroup per scenario for this sector
            df_sector = df_emissions[
                (df_emissions['sector'] == sector) &
                (df_emissions['topic'] == "emission")
            ].groupby(['year', 'comgroup', 'scen'], as_index=False)['value'].sum()

            if not df_sector.empty:
                emission_plotter = TimesReportPlotter(df_sector)
                fig_emission_sector = emission_plotter.line_plot(
                    x_col="year",
                    y_col="value",
                    line_group_col="comgroup",
                    scenario_col="scen",
                    filter_dict=None,
                    title=f"Emissions for {sector}"
                )
                st.plotly_chart(fig_emission_sector, use_container_width=True)
            else:
                st.warning(f"No emission data for sector {sector}.")

    # ---------------------- DEVELOPMENT TAB ----------------------
    with topic_tabs[2]:
        st.header("Development")
        st.info("This section is for testing new features.")
        try:
            st.image("images/speed-local.jpg", caption="Speed Local", use_container_width=True)
        except FileNotFoundError:
            st.error("Image not found: images/speed-local.jpg")
        try:
            st.image("images/map.png")
        except FileNotFoundError:
            st.error("Image not found: images/map.png")

if __name__ == "__main__":
    main(
        mapping_csv="inputs/mapping_db_views.csv"
    )