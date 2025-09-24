"""
Sankey Diagrams - Full functionality from original page
Interactive energy flow visualization with Plotly Sankey charts
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import sys
import os

# Add utils directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app', 'utils'))
from database import connect_to_db, get_unique_values, test_database_connection

@st.cache_data(show_spinner=False)
def load_sankey_data(conn, scenario, year, region=None):
    """Load comprehensive energy flow data for Sankey diagram"""
    try:
        # Base query to get all energy flows
        region_filter = f"AND (f.reg = '{region}' OR f.regfrom = '{region}' OR f.regto = '{region}')" if region else ""
        
        query = f"""
        WITH all_flows AS (
            -- Production flows (f_out from production processes)
            SELECT 
                f.prc as source_node,
                f.com as target_node,
                f.reg as region,
                SUM(f.value) as value,
                'production' as flow_type,
                f.scen,
                f.year
            FROM timesreport_facts f
            WHERE f.attr = 'f_out'
            AND f.topic = 'energy'
            AND f.scen = ?
            AND f.year = ?
            AND f.value > 0
            AND NOT f.prc LIKE 'TB%'  -- Exclude transmission
            AND NOT f.prc LIKE 'IMP%' -- Exclude imports  
            AND NOT f.prc LIKE 'EXP%' -- Exclude exports
            {region_filter}
            GROUP BY f.prc, f.com, f.reg, f.scen, f.year
            
            UNION ALL
            
            -- Consumption flows (f_in to consumption processes) 
            SELECT 
                f.com as source_node,
                f.prc as target_node,
                f.reg as region,
                SUM(f.value) as value,
                'consumption' as flow_type,
                f.scen,
                f.year
            FROM timesreport_facts f
            WHERE f.attr = 'f_in'
            AND f.topic = 'energy'
            AND f.scen = ?
            AND f.year = ?
            AND f.value > 0
            AND NOT f.prc LIKE 'TB%'  -- Exclude transmission
            AND NOT f.prc LIKE 'IMP%' -- Exclude imports
            AND NOT f.prc LIKE 'EXP%' -- Exclude exports
            {region_filter}
            GROUP BY f.com, f.prc, f.reg, f.scen, f.year
            
            UNION ALL
            
            -- Import flows 
            SELECT 
                'External' as source_node,
                f.com as target_node,
                f.regto as region,
                SUM(f.value) as value,
                'import' as flow_type,
                f.scen,
                f.year
            FROM timesreport_facts f
            WHERE f.prc LIKE 'IMP%'
            AND f.attr = 'f_out'
            AND f.topic = 'energy'
            AND f.scen = ?
            AND f.year = ?
            AND f.value > 0
            {region_filter.replace('f.reg', 'f.regto') if region_filter else ''}
            GROUP BY f.com, f.regto, f.scen, f.year
            
            UNION ALL
            
            -- Export flows
            SELECT 
                f.com as source_node,
                'External' as target_node,
                f.regfrom as region,
                SUM(f.value) as value,
                'export' as flow_type,
                f.scen,
                f.year
            FROM timesreport_facts f
            WHERE f.prc LIKE 'EXP%'
            AND f.attr = 'f_in'
            AND f.topic = 'energy'
            AND f.scen = ?
            AND f.year = ?
            AND f.value > 0
            {region_filter.replace('f.reg', 'f.regfrom') if region_filter else ''}
            GROUP BY f.com, f.regfrom, f.scen, f.year
            
            UNION ALL
            
            -- Transmission flows (between regions)
            SELECT 
                f.regfrom as source_node,
                f.regto as target_node,
                f.regfrom as region,
                SUM(f.value) as value,
                'transmission' as flow_type,
                f.scen,
                f.year
            FROM timesreport_facts f
            WHERE f.prc LIKE 'TB%'
            AND f.attr = 'f_out'
            AND f.scen = ?
            AND f.year = ?
            AND f.value > 0
            {region_filter.replace('f.reg', 'f.regfrom') if region_filter else ''}
            GROUP BY f.regfrom, f.regto, f.scen, f.year
        )
        SELECT * FROM all_flows WHERE value > 0
        """
        
        # Execute query with appropriate number of parameters
        params = [scenario, year] * 5  # 5 subqueries, each needs scenario and year
        df = conn.execute(query, params).df()
        
        if not df.empty:
            # Clean up node names
            df['source_clean'] = df['source_node'].str.replace('_', ' ').str.title()
            df['target_clean'] = df['target_node'].str.replace('_', ' ').str.title()
            df['region_clean'] = df['region'].str.replace('DKB', 'Bornholm')
            
            # Add node prefixes for better categorization
            df.loc[df['flow_type'] == 'production', 'source_clean'] = '[TECH] ' + df.loc[df['flow_type'] == 'production', 'source_clean']
            df.loc[df['flow_type'] == 'consumption', 'target_clean'] = '[DEMAND] ' + df.loc[df['flow_type'] == 'consumption', 'target_clean']
            df.loc[df['flow_type'] == 'transmission', 'source_clean'] = '[REGION] ' + df.loc[df['flow_type'] == 'transmission', 'source_clean']
            df.loc[df['flow_type'] == 'transmission', 'target_clean'] = '[REGION] ' + df.loc[df['flow_type'] == 'transmission', 'target_clean']
            
        return df
    
    except Exception as e:
        st.error(f"Error loading Sankey data: {str(e)}")
        return pd.DataFrame()

@st.cache_data(show_spinner=False) 
def prepare_sankey_traces(df, min_flow_threshold=0.1):
    """Prepare Sankey diagram traces from flow data"""
    if df.empty:
        return None
    
    # Filter out very small flows
    df_filtered = df[df['value'] >= min_flow_threshold].copy()
    
    if df_filtered.empty:
        return None
    
    # Create unique node list
    sources = df_filtered['source_clean'].unique()
    targets = df_filtered['target_clean'].unique()
    all_nodes = pd.Series(np.concatenate([sources, targets])).unique()
    
    # Create node mapping
    node_dict = {node: i for i, node in enumerate(all_nodes)}
    
    # Map source and target to indices
    df_filtered['source_idx'] = df_filtered['source_clean'].map(node_dict)
    df_filtered['target_idx'] = df_filtered['target_clean'].map(node_dict)
    
    # Aggregate flows by source-target pairs
    flow_summary = df_filtered.groupby(['source_idx', 'target_idx', 'source_clean', 'target_clean'])['value'].sum().reset_index()
    
    # Create color mapping based on flow type
    colors = []
    for node in all_nodes:
        if node.startswith('[TECH]'):
            colors.append('rgba(31, 119, 180, 0.8)')  # Blue for technology
        elif node.startswith('[DEMAND]'):
            colors.append('rgba(255, 127, 14, 0.8)')  # Orange for demand
        elif node.startswith('[REGION]'):
            colors.append('rgba(44, 160, 44, 0.8)')   # Green for regions
        elif node == 'External':
            colors.append('rgba(214, 39, 40, 0.8)')   # Red for external
        else:
            colors.append('rgba(148, 103, 189, 0.8)') # Purple for commodities
    
    return {
        'source': flow_summary['source_idx'].tolist(),
        'target': flow_summary['target_idx'].tolist(), 
        'value': flow_summary['value'].tolist(),
        'labels': all_nodes.tolist(),
        'colors': colors,
        'flow_summary': flow_summary
    }

def create_sankey_diagram(sankey_data):
    """Create interactive Sankey diagram using Plotly"""
    if not sankey_data:
        return None
    
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=sankey_data['labels'],
            color=sankey_data['colors']
        ),
        link=dict(
            source=sankey_data['source'],
            target=sankey_data['target'],
            value=sankey_data['value'],
            color=['rgba(100, 100, 100, 0.3)'] * len(sankey_data['source'])
        )
    )])
    
    fig.update_layout(
        title_text="Energy Flow Sankey Diagram",
        font_size=12,
        height=600,
        margin=dict(t=50, l=0, r=0, b=0)
    )
    
    return fig

@st.cache_data(show_spinner=False)
def create_flow_type_breakdown(df):
    """Create breakdown charts by flow type"""
    if df.empty:
        return None
    
    # Aggregate by flow type
    flow_type_summary = df.groupby('flow_type')['value'].sum().reset_index()
    
    # Create pie chart
    fig = px.pie(
        flow_type_summary, 
        values='value', 
        names='flow_type',
        title="Energy Flow Breakdown by Type",
        color_discrete_map={
            'production': '#1f77b4',
            'consumption': '#ff7f0e', 
            'transmission': '#2ca02c',
            'import': '#d62728',
            'export': '#9467bd'
        }
    )
    
    fig.update_layout(height=400)
    return fig

@st.cache_data(show_spinner=False)
def create_top_flows_chart(df, n_flows=10):
    """Create chart showing top N energy flows"""
    if df.empty:
        return None
    
    # Get top flows
    top_flows = df.nlargest(n_flows, 'value').copy()
    top_flows['flow_label'] = top_flows['source_clean'] + ' → ' + top_flows['target_clean']
    
    # Create horizontal bar chart
    fig = px.bar(
        top_flows,
        x='value',
        y='flow_label',
        color='flow_type',
        title=f"Top {n_flows} Energy Flows",
        labels={'value': 'Energy Flow', 'flow_label': 'Flow Path'},
        color_discrete_map={
            'production': '#1f77b4',
            'consumption': '#ff7f0e',
            'transmission': '#2ca02c', 
            'import': '#d62728',
            'export': '#9467bd'
        }
    )
    
    fig.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
    return fig

def render_sankey_diagrams():
    """Main render function for Sankey Diagrams"""
    
    # Database connection section
    st.sidebar.header("🔗 Database Connection")
    
    # Connection type selection
    connection_type = st.sidebar.radio(
        "Connection Type:",
        ["Local File", "Azure URL"],
        help="Choose whether to connect to a local DuckDB file or download from Azure blob storage"
    )
    
    if connection_type == "Local File":
        db_path = st.sidebar.text_input("Enter path to DuckDB database:", "speedlocal_times_db_bornholm.duckdb")
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
            test_database_connection(conn)
            st.session_state.db_connection = conn
        else:
            if 'db_connection' in st.session_state:
                del st.session_state.db_connection
    
    # Only show analysis options if connected
    if 'db_connection' in st.session_state:
        conn = st.session_state.db_connection
        
        try:
            # Get available data for filters
            scenarios = get_unique_values(conn, "scen")
            years = get_unique_values(conn, "year")
            regions = get_unique_values(conn, "reg")
            
            # Convert years to integers and sort
            try:
                years = sorted([int(y) for y in years if str(y).isdigit()])
            except:
                years = [2020, 2030, 2040, 2050]  # Default years
            
            if not scenarios:
                scenarios = ["DEFAULT"]
            if not regions:
                regions = ["BORNHOLM"]
                
            # Sidebar filters
            st.sidebar.header("🎛️ Sankey Controls")
            
            scenario = st.sidebar.selectbox("Scenario", scenarios)
            year = st.sidebar.selectbox("Year", years)
            
            # Region filter (optional)
            use_region_filter = st.sidebar.checkbox("Filter by region", value=False)
            region = None
            if use_region_filter:
                region = st.sidebar.selectbox("Region", regions)
            
            # Flow threshold
            min_flow = st.sidebar.number_input(
                "Minimum flow threshold", 
                min_value=0.0, 
                max_value=100.0, 
                value=1.0,
                step=0.1,
                help="Hide flows below this threshold to simplify the diagram"
            )
            
            # Load and process data
            if st.sidebar.button("Generate Sankey Diagram") or 'sankey_data' not in st.session_state:
                with st.spinner("Loading energy flow data..."):
                    flow_data = load_sankey_data(conn, scenario, year, region)
                    
                    if not flow_data.empty:
                        sankey_traces = prepare_sankey_traces(flow_data, min_flow)
                        st.session_state.sankey_data = sankey_traces
                        st.session_state.flow_data = flow_data
                        st.session_state.current_filters = (scenario, year, region)
                    else:
                        st.warning("No data found for the selected filters")
                        if 'sankey_data' in st.session_state:
                            del st.session_state.sankey_data
            
            # Display current filters
            if 'current_filters' in st.session_state:
                scen, yr, reg = st.session_state.current_filters
                region_text = f", Region: {reg}" if reg else ""
                st.info(f"📊 **Current View**: {scen} scenario, Year {yr}{region_text}")
            
            # Create and display Sankey diagram
            if 'sankey_data' in st.session_state and st.session_state.sankey_data:
                
                # Main Sankey diagram
                sankey_fig = create_sankey_diagram(st.session_state.sankey_data)
                if sankey_fig:
                    st.plotly_chart(sankey_fig, use_container_width=True)
                
                # Additional analysis charts
                if 'flow_data' in st.session_state and not st.session_state.flow_data.empty:
                    df = st.session_state.flow_data
                    
                    # Flow statistics
                    st.subheader("📈 Flow Analysis")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Total Flows", len(df))
                    col2.metric("Unique Nodes", len(st.session_state.sankey_data['labels']))
                    col3.metric("Total Energy", f"{df['value'].sum():.1f}")
                    col4.metric("Max Flow", f"{df['value'].max():.1f}")
                    
                    # Side-by-side charts
                    chart_col1, chart_col2 = st.columns(2)
                    
                    with chart_col1:
                        # Flow type breakdown
                        flow_breakdown_fig = create_flow_type_breakdown(df)
                        if flow_breakdown_fig:
                            st.plotly_chart(flow_breakdown_fig, use_container_width=True)
                    
                    with chart_col2:
                        # Top flows chart
                        top_flows_fig = create_top_flows_chart(df)
                        if top_flows_fig:
                            st.plotly_chart(top_flows_fig, use_container_width=True)
                    
                    # Detailed data tables
                    with st.expander("📊 View Detailed Flow Data"):
                        # Flow summary
                        st.subheader("Flow Summary")
                        flow_summary = st.session_state.sankey_data['flow_summary']
                        st.dataframe(flow_summary.sort_values('value', ascending=False))
                        
                        # Raw data
                        st.subheader("Raw Flow Data")
                        display_df = df[['source_clean', 'target_clean', 'value', 'flow_type', 'region_clean']].copy()
                        display_df.columns = ['Source', 'Target', 'Value', 'Flow Type', 'Region']
                        st.dataframe(display_df.sort_values('Value', ascending=False))
                
            elif 'sankey_data' in st.session_state:
                st.warning("⚠️ No flow data found for the selected filters. Try adjusting the minimum flow threshold or different scenario/year combinations.")
            
        except Exception as e:
            st.error(f"Error generating Sankey diagram: {str(e)}")
    
    else:
        st.info("👆 Please connect to a database using the sidebar to start exploring Sankey diagrams.")
        
        # Show feature overview
        st.markdown("""
        ## 🎯 Features
        
        ### 📊 **Interactive Sankey Diagrams**
        - **Plotly-based**: Full interactivity with zoom, pan, and hover details
        - **Node categorization**: Color-coded nodes for technologies, demands, regions
        - **Flow aggregation**: Intelligent combining of similar energy flows
        - **Threshold filtering**: Hide small flows to focus on major pathways
        
        ### ⚡ **Energy Flow Types**
        - **🏭 Production Flows**: From technologies to energy commodities
        - **🏠 Consumption Flows**: From commodities to demand sectors
        - **🔄 Transmission Flows**: Inter-regional energy transfers
        - **📥 Import Flows**: External energy sources
        - **📤 Export Flows**: Energy sent to external markets
        
        ### 📈 **Analysis Features**
        - **Flow breakdown**: Pie chart showing energy flow proportions by type
        - **Top flows ranking**: Bar chart of largest energy pathways
        - **Statistical metrics**: Total flows, nodes, energy volumes
        - **Regional filtering**: Focus analysis on specific regions
        - **Data export**: Access to raw flow data and summaries
        
        ### 🎨 **Visual Design**
        - **Color coding**: Technologies (blue), Demands (orange), Regions (green), External (red)
        - **Proportional widths**: Flow thickness represents energy magnitude  
        - **Clean labeling**: Automatic node name formatting and categorization
        - **Interactive legends**: Click to highlight/hide specific flow types
        
        ### 🔧 **Customization Options**
        - **Flow threshold**: Adjust minimum flow visibility
        - **Region filtering**: Analyze specific geographic areas
        - **Scenario comparison**: Switch between different energy scenarios
        - **Temporal analysis**: View flows across different years
        
        ### 💡 **Use Cases**
        - **Energy system analysis**: Understand energy transformation pathways
        - **Bottleneck identification**: Find capacity constraints in energy flows
        - **Scenario comparison**: Compare energy flows between scenarios
        - **Policy impact**: Assess effects of energy policy changes
        - **Investment planning**: Identify critical energy infrastructure needs
        """)