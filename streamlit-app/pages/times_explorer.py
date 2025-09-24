"""
TIMES Data Explorer - Extracted functionality from original page
Uses lazy imports to avoid pybind11 conflicts
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

# Add utils directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app', 'utils'))
from database import connect_to_db, get_unique_values, get_sector_descriptions, test_database_connection

# Define sectors to exclude
EXCLUDED_SECTORS = ['DMZ', 'SYS', 'DHT', 'ELT', 'TRD']

def create_energy_plot(conn, sector, scenarios):
    """Create energy plot for specific sector with scenario comparison"""
    query = """
    SELECT 
        f.year,
        f.scen,
        f.comgroup,
        SUM(f.value) as value,
        f.unit,
        COALESCE(c.description, f.comgroup) as comgroup_desc
    FROM timesreport_facts f
    LEFT JOIN comgroup_desc c ON f.comgroup = c.id AND f.scen = c.scen
    WHERE f.topic = 'energy'
    AND f.attr = 'f_in'
    AND f.sector = ?
    AND f.scen IN ({})
    GROUP BY f.year, f.scen, f.comgroup, f.unit, c.description
    ORDER BY f.year, f.scen, c.description
    """.format(','.join(['?' for _ in scenarios]))
    
    try:
        # Execute query and get data
        df = conn.execute(query, [sector] + scenarios).df()
        
        if df.empty:
            st.write(f"No data available for sector {sector}")
            return

        # Create figure
        fig = go.Figure()
        
        # Get all unique years and commodity groups
        years = sorted(df['year'].unique())
        comgroups = sorted(df['comgroup_desc'].unique())
        
        # Create a consistent color map for commodity groups
        colors = px.colors.qualitative.Set3[:len(comgroups)]
        color_map = dict(zip(comgroups, colors))
        
        # Calculate bar width and positions
        scenario_width = 0.8 / len(scenarios)  # Width for each scenario's bar
        
        # Create bars for each year, scenario, and commodity group
        for year in years:
            year_data = df[df['year'] == year]
            
            for i, scen in enumerate(scenarios):
                scen_data = year_data[year_data['scen'] == scen]
                
                # Calculate x position for this scenario's bars
                x_pos = float(year) + (i - len(scenarios)/2 + 0.5) * scenario_width
                
                # Add bars for each commodity group
                for comgroup in comgroups:
                    value = scen_data[scen_data['comgroup_desc'] == comgroup]['value'].sum()
                    
                    fig.add_trace(go.Bar(
                        name=comgroup,
                        x=[x_pos],
                        y=[value],
                        width=scenario_width * 0.9,  # Slightly smaller than calculated width for spacing
                        marker_color=color_map[comgroup],
                        legendgroup=comgroup,
                        showlegend=year == years[0] and i == 0,  # Show legend only for first occurrence
                        hovertemplate=(
                            f"Year: {year}<br>" +
                            f"Scenario: {scen}<br>" +
                            f"Commodity: {comgroup}<br>" +
                            f"Value: %{{y:.2f}} {df.unit.iloc[0]}"
                        )
                    ))
        
        # Add scenario annotations above the plot
        for i, scen in enumerate(scenarios):
            fig.add_annotation(
                x=0.1 + i * 0.8/len(scenarios),
                y=1.05,
                text=scen,
                showarrow=False,
                xref="paper",
                yref="paper",
                font=dict(size=12)
            )
        
        # Update layout
        fig.update_layout(
            barmode='stack',
            title=f'Energy Input by Commodity Group and Scenario',
            xaxis_title="Year",
            yaxis_title=f"Energy Input ({df.unit.iloc[0]})",
            height=600,
            bargap=0,
            bargroupgap=0.1,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5,
                title=dict(text="Commodity Groups")
            ),
            margin=dict(t=80)  # Add more top margin for scenario labels
        )
        
        # Set x-axis ticks to show years clearly
        fig.update_xaxes(
            tickmode='array',
            ticktext=years,
            tickvals=years,
            tickangle=0
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creating plot: {str(e)}")

def create_emission_plot(conn, sector, scenarios):
    """Create emission plot for specific sector with scenario comparison"""
    query = """
    SELECT 
        f.year,
        f.scen,
        f.comgroup,
        SUM(f.value) as value,
        f.unit,
        COALESCE(c.description, f.comgroup) as comgroup_desc
    FROM timesreport_facts f
    LEFT JOIN comgroup_desc c ON f.comgroup = c.id AND f.scen = c.scen
    WHERE f.topic = 'emission'
    AND f.sector = ?
    AND f.scen IN ({})
    GROUP BY f.year, f.scen, f.comgroup, f.unit, c.description
    ORDER BY f.year, f.scen, c.description
    """.format(','.join(['?' for _ in scenarios]))
    
    try:
        # Execute query and get data
        df = conn.execute(query, [sector] + scenarios).df()
        
        if df.empty:
            st.write(f"No emission data available for sector {sector}")
            return

        # Create figure
        fig = go.Figure()
        
        # Get all unique years and commodity groups (emission types)
        years = sorted(df['year'].unique())
        comgroups = sorted(df['comgroup_desc'].unique())
        
        # Create a consistent color map for emission types
        colors = px.colors.qualitative.Set1[:len(comgroups)]
        color_map = dict(zip(comgroups, colors))
        
        # For emissions, we'll use a line chart with markers to better show trends over time
        for scen in scenarios:
            for comgroup in comgroups:
                scen_data = df[(df['scen'] == scen) & (df['comgroup_desc'] == comgroup)]
                
                if not scen_data.empty:
                    fig.add_trace(go.Scatter(
                        x=scen_data['year'],
                        y=scen_data['value'],
                        mode='lines+markers',
                        name=f"{comgroup} - {scen}",
                        line=dict(color=color_map[comgroup]),
                        marker=dict(size=8),
                        hovertemplate=(
                            "Year: %{x}<br>" +
                            f"Scenario: {scen}<br>" +
                            f"Emission Type: {comgroup}<br>" +
                            f"Value: %{{y:.2f}} {scen_data.unit.iloc[0]}"
                        )
                    ))
        
        # Update layout
        fig.update_layout(
            title=f'Emissions by Type and Scenario',
            xaxis_title="Year",
            yaxis_title=f"Emissions ({df.unit.iloc[0]})",
            height=600,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5
            )
        )
        
        # Set x-axis ticks to show years clearly
        fig.update_xaxes(
            tickmode='array',
            ticktext=years,
            tickvals=years,
            tickangle=0
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creating emission plot: {str(e)}")

def render_times_explorer():
    """Main render function for TIMES Data Explorer"""
    
    # Database connection section
    st.sidebar.header("🔗 Database Connection")
    
    # Connection type selection
    connection_type = st.sidebar.radio(
        "Connection Type:",
        ["Local File", "Azure URL"],
        help="Choose whether to connect to a local DuckDB file or download from Azure blob storage"
    )
    
    if connection_type == "Local File":
        db_path = st.sidebar.text_input("Enter path to DuckDB database:", "times_db.duckdb")
        is_url = False
    else:
        db_path = st.sidebar.text_input(
            "Enter Azure blob storage URL:", 
            placeholder="https://storage.blob.core.windows.net/container/database.duckdb?..."
        )
        is_url = True
        use_cache = st.sidebar.checkbox("Use local cache", value=True, help="Cache downloaded database locally")
    
    # Connect button
    if st.sidebar.button("Connect to Database"):
        if connection_type == "Azure URL":
            conn = connect_to_db(db_path, is_url=True, use_cache=use_cache)
        else:
            conn = connect_to_db(db_path, is_url=False)
        
        if conn is not None:
            # Test connection and show info
            test_database_connection(conn)
            st.session_state.db_connection = conn
        else:
            if 'db_connection' in st.session_state:
                del st.session_state.db_connection
    
    # Only show analysis options if connected
    if 'db_connection' in st.session_state:
        conn = st.session_state.db_connection
        
        try:
            # Get available scenarios
            all_scenarios = get_unique_values(conn, "scen")
            
            if not all_scenarios:
                st.error("No scenarios found in the database")
                return
            
            # Add scenario selection to sidebar
            selected_scenarios = st.sidebar.multiselect(
                "Select Scenarios to Compare:",
                options=all_scenarios,
                default=all_scenarios[:2] if len(all_scenarios) > 1 else all_scenarios,
                help="Choose one or more scenarios for comparison"
            )
            
            if not selected_scenarios:
                st.warning("Please select at least one scenario")
                return
            
            # Get sectors and their descriptions (excluding the specified sectors)
            sector_desc_dict = get_sector_descriptions(conn, EXCLUDED_SECTORS)
            
            if not sector_desc_dict:
                st.error("No sectors found in the database")
                return
            
            # Add topic selection tab
            topic_tabs = st.tabs(["⚡ Energy", "🌫️ Emissions"])
            
            # Energy visualization tab
            with topic_tabs[0]:
                st.header("⚡ Energy Analysis")
                st.markdown("**Energy input flows by commodity group and scenario comparison**")
                
                # Create tabs using sector descriptions
                sectors = list(sector_desc_dict.keys())
                sector_descs = [sector_desc_dict[sector] for sector in sectors]
                
                if len(sectors) > 0:
                    sector_tabs = st.tabs(sector_descs)
                    
                    # Create content for each sector tab
                    for tab, sector in zip(sector_tabs, sectors):
                        with tab:
                            st.subheader(f"{sector_desc_dict[sector]}")
                            create_energy_plot(conn, sector, selected_scenarios)
                else:
                    st.warning("No sectors available for energy analysis")
            
            # Emissions visualization tab
            with topic_tabs[1]:
                st.header("🌫️ Emissions Analysis")
                st.markdown("**Emission flows by type and scenario comparison**")
                
                # Create tabs using sector descriptions
                sectors = list(sector_desc_dict.keys())
                sector_descs = [sector_desc_dict[sector] for sector in sectors]
                
                if len(sectors) > 0:
                    sector_tabs = st.tabs(sector_descs)
                    
                    # Create content for each sector tab
                    for tab, sector in zip(sector_tabs, sectors):
                        with tab:
                            st.subheader(f"{sector_desc_dict[sector]}")
                            create_emission_plot(conn, sector, selected_scenarios)
                else:
                    st.warning("No sectors available for emissions analysis")
            
        except Exception as e:
            st.error(f"Error during analysis: {str(e)}")
    else:
        st.info("👆 Please connect to a database using the sidebar to start exploring TIMES data.")
        
        # Show feature overview
        st.markdown("""
        ## 🎯 Features
        
        ### 📊 **Energy Analysis**
        - Sector-based energy input visualization
        - Commodity group breakdown with stacked bar charts
        - Multi-scenario comparison capabilities
        - Interactive hover details and legends
        
        ### 🌫️ **Emissions Analysis**  
        - Emission tracking by sector and type
        - Time-series trend visualization with line charts
        - Scenario comparison for policy impact analysis
        - Detailed emission type categorization
        
        ### 🔗 **Database Connectivity**
        - **Local Files**: Connect to DuckDB files on your system
        - **Azure Integration**: Download and cache databases from Azure blob storage
        - **URL Validation**: Automatic Azure URL expiry checking
        - **Caching**: Smart local caching for improved performance
        
        ### 🎨 **Interactive Features**
        - Dynamic scenario selection and filtering
        - Color-coded commodity groups and emission types
        - Responsive chart layouts and annotations
        - Export-ready visualizations
        """)