import streamlit as st
from pathlib import Path
from utils._query_with_csv import PandasDFCreator
from utils._plotting import TimesReportPlotter

EXCLUDED_SECTORS = ['AFO','DMZ','SYS','DHT','ELT','TRD','UPS','NA','FTS']

def main(db_source: str, mapping_csv: str, is_url: bool = True):
    """Main Streamlit UI using preloaded Pandas DataFrames for plotting."""
    
    st.set_page_config(page_title="SpeedLocal: TIMES Data Explorer", layout="wide")
    st.title("SpeedLocal: TIMES Data Explorer (beta version) !")

    # Load DataFrames
    creator = PandasDFCreator(db_source=db_source, mapping_csv=mapping_csv, is_url=is_url)
    dfs_dict = creator.run()

    df_energy = dfs_dict.get("energy")
    df_emissions = dfs_dict.get("emissions")

    if df_energy is None or df_energy.empty:
        st.error("Energy DataFrame is empty. Cannot display plots.")
        return
    if df_emissions is None or df_emissions.empty:
        st.error("Emissions DataFrame is empty. Cannot display plots.")
        return

    # Sidebar filters
    sectors = sorted(df_energy['sector'].unique())
    sectors = [s for s in sectors if s not in EXCLUDED_SECTORS]
    # selected_sector = st.sidebar.selectbox("Select sector", sectors)

    scenarios = sorted(df_energy['scen'].unique())
    selected_scenarios = st.sidebar.multiselect("Select energy scenarios", scenarios, default=scenarios[:2])

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
        db_source="https://speedlocal.flowcore.app/api/duckdb/share/fa45bb6b7d2a92f71d53968d181f6c7b",  # Replace with actual URL or local path
        mapping_csv="inputs/mapping_db_views.csv",  # Replace with actual path to mapping CSV
        is_url=True
    )