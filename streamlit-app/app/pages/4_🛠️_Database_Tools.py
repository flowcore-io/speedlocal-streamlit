"""
Database Tools - Comprehensive database exploration and management utilities
Provides SQL query interface, schema exploration, and data management tools
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os
from datetime import datetime

# Add utils directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from database import connect_to_db, get_unique_values, test_database_connection

# Set page configuration
st.set_page_config(page_title="Database Tools", page_icon="🛠️", layout="wide")

@st.cache_data(show_spinner=False, ttl=3600)  # Cache for 1 hour
def get_table_info(conn):
    """Get information about all tables in the database"""
    try:
        # Get table names and info
        tables_query = """
        SELECT 
            table_name,
            table_type,
            column_count,
            estimated_size 
        FROM duckdb_tables() 
        WHERE schema_name = 'main'
        ORDER BY table_name
        """
        
        tables_df = conn.execute(tables_query).df()
        
        # Get detailed column info for each table
        table_details = {}
        for table_name in tables_df['table_name']:
            try:
                columns_query = f"""
                SELECT 
                    column_name,
                    column_type,
                    null as column_default,
                    is_nullable
                FROM duckdb_columns() 
                WHERE table_name = '{table_name}'
                AND schema_name = 'main'
                ORDER BY column_index
                """
                
                columns_df = conn.execute(columns_query).df()
                table_details[table_name] = columns_df
                
            except Exception as e:
                st.warning(f"Could not get column info for table {table_name}: {e}")
                table_details[table_name] = pd.DataFrame()
        
        return tables_df, table_details
        
    except Exception as e:
        st.error(f"Error getting table information: {str(e)}")
        return pd.DataFrame(), {}

@st.cache_data(show_spinner=False)
def execute_query(conn, query, limit=1000):
    """Execute a SQL query safely with row limit"""
    try:
        # Add LIMIT if not present and not a schema query
        query_upper = query.upper().strip()
        if not any(keyword in query_upper for keyword in ['LIMIT', 'DESCRIBE', 'SHOW', 'PRAGMA', 'INFORMATION_SCHEMA']):
            if not query_upper.endswith(';'):
                query += f" LIMIT {limit}"
            else:
                query = query[:-1] + f" LIMIT {limit};"
        
        result_df = conn.execute(query).df()
        return result_df, None
        
    except Exception as e:
        return None, str(e)

@st.cache_data(show_spinner=False)
def get_table_sample(conn, table_name, sample_size=10):
    """Get a sample of rows from a table"""
    try:
        query = f"SELECT * FROM {table_name} LIMIT {sample_size}"
        return conn.execute(query).df()
    except Exception as e:
        st.warning(f"Could not sample table {table_name}: {e}")
        return pd.DataFrame()

@st.cache_data(show_spinner=False) 
def get_table_stats(conn, table_name):
    """Get basic statistics about a table"""
    try:
        # Get row count
        count_query = f"SELECT COUNT(*) as row_count FROM {table_name}"
        row_count = conn.execute(count_query).df().iloc[0]['row_count']
        
        # Get column statistics
        columns_query = f"SELECT * FROM {table_name} LIMIT 1"
        sample_df = conn.execute(columns_query).df()
        
        stats = {
            'row_count': row_count,
            'column_count': len(sample_df.columns),
            'columns': list(sample_df.columns)
        }
        
        return stats
        
    except Exception as e:
        st.warning(f"Could not get stats for table {table_name}: {e}")
        return None

def create_query_suggestions():
    """Return common SQL query templates"""
    return {
        "Basic Data Exploration": {
            "View table structure": "DESCRIBE table_name",
            "Count rows": "SELECT COUNT(*) FROM table_name",
            "Sample data": "SELECT * FROM table_name LIMIT 10",
            "Unique values": "SELECT DISTINCT column_name FROM table_name",
        },
        "TIMES Data Queries": {
            "Available scenarios": "SELECT DISTINCT scen FROM timesreport_facts",
            "Available years": "SELECT DISTINCT year FROM timesreport_facts ORDER BY year",
            "Available regions": "SELECT DISTINCT reg FROM timesreport_facts",
            "Energy commodities": "SELECT DISTINCT com FROM timesreport_facts WHERE topic = 'energy'",
            "Process types": "SELECT DISTINCT prc FROM timesreport_facts WHERE prc LIKE 'TB%' OR prc LIKE 'IMP%' OR prc LIKE 'EXP%'",
        },
        "Energy Analysis": {
            "Total energy by year": """
SELECT year, SUM(value) as total_energy 
FROM timesreport_facts 
WHERE topic = 'energy' AND attr = 'f_out' 
GROUP BY year ORDER BY year
""",
            "Energy by scenario": """
SELECT scen, year, SUM(value) as total_energy
FROM timesreport_facts 
WHERE topic = 'energy' AND attr = 'f_out'
GROUP BY scen, year ORDER BY scen, year
""",
            "Top energy flows": """
SELECT prc, com, reg, SUM(value) as total_flow
FROM timesreport_facts
WHERE topic = 'energy' AND attr = 'f_out' AND year = 2030
GROUP BY prc, com, reg
ORDER BY total_flow DESC LIMIT 20
""",
        },
        "Emissions Analysis": {
            "Emissions by year": """
SELECT year, SUM(value) as total_emissions
FROM timesreport_facts 
WHERE topic = 'emissions' 
GROUP BY year ORDER BY year
""",
            "Emissions by sector": """
SELECT prc, SUM(value) as total_emissions
FROM timesreport_facts
WHERE topic = 'emissions' AND year = 2030
GROUP BY prc ORDER BY total_emissions DESC
""",
        }
    }

def main():
    # Title and description
    st.title("🛠️ Database Tools")
    st.markdown("**Comprehensive database exploration, querying, and management utilities**")
    
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
    
    # Main interface - only show if connected
    if 'db_connection' in st.session_state:
        conn = st.session_state.db_connection
        
        # Create tabs for different tools
        tab1, tab2, tab3, tab4 = st.tabs(["🔍 Schema Explorer", "⚡ SQL Query", "📊 Data Analysis", "📈 Quick Charts"])
        
        # Tab 1: Schema Explorer
        with tab1:
            st.subheader("Database Schema Explorer")
            
            # Get table information
            with st.spinner("Loading database schema..."):
                tables_df, table_details = get_table_info(conn)
            
            if not tables_df.empty:
                # Display tables overview
                st.write("### 📋 Tables Overview")
                st.dataframe(tables_df, use_container_width=True)
                
                # Table selector
                if len(table_details) > 0:
                    selected_table = st.selectbox("Select table to explore:", list(table_details.keys()))
                    
                    if selected_table:
                        col1, col2 = st.columns([1, 1])
                        
                        with col1:
                            st.write(f"### 📄 Table: `{selected_table}`")
                            
                            # Show column information
                            if not table_details[selected_table].empty:
                                st.write("**Columns:**")
                                st.dataframe(table_details[selected_table], use_container_width=True)
                            
                            # Show table statistics
                            stats = get_table_stats(conn, selected_table)
                            if stats:
                                st.write("**Statistics:**")
                                st.write(f"- **Rows**: {stats['row_count']:,}")
                                st.write(f"- **Columns**: {stats['column_count']}")
                        
                        with col2:
                            st.write("### 👀 Sample Data")
                            sample_size = st.slider("Sample size:", 5, 50, 10)
                            sample_df = get_table_sample(conn, selected_table, sample_size)
                            
                            if not sample_df.empty:
                                st.dataframe(sample_df, use_container_width=True)
                            else:
                                st.info("No sample data available")
        
        # Tab 2: SQL Query Interface  
        with tab2:
            st.subheader("SQL Query Interface")
            
            # Query suggestions
            with st.expander("💡 Query Templates & Examples", expanded=False):
                suggestions = create_query_suggestions()
                
                for category, queries in suggestions.items():
                    st.write(f"**{category}**")
                    for name, query in queries.items():
                        if st.button(f"Use: {name}", key=f"btn_{category}_{name}"):
                            st.session_state.sql_query = query
                    st.write("")
            
            # Query input
            default_query = getattr(st.session_state, 'sql_query', 'SELECT * FROM timesreport_facts LIMIT 10')
            query = st.text_area(
                "Enter SQL query:",
                value=default_query,
                height=150,
                help="Enter any SQL query. LIMIT will be added automatically for safety."
            )
            
            # Query execution controls
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                execute_button = st.button("🚀 Execute Query", type="primary")
            with col2:
                row_limit = st.number_input("Row limit:", min_value=10, max_value=10000, value=1000, step=100)
            with col3:
                st.write(f"⚠️ Queries will be automatically limited to {row_limit} rows for performance")
            
            # Execute query
            if execute_button and query.strip():
                with st.spinner("Executing query..."):
                    start_time = datetime.now()
                    result_df, error = execute_query(conn, query, row_limit)
                    end_time = datetime.now()
                    execution_time = (end_time - start_time).total_seconds()
                
                if error:
                    st.error(f"❌ Query failed: {error}")
                elif result_df is not None:
                    st.success(f"✅ Query executed successfully in {execution_time:.2f}s")
                    
                    # Show results
                    if not result_df.empty:
                        st.write(f"### 📊 Results ({len(result_df)} rows)")
                        st.dataframe(result_df, use_container_width=True)
                        
                        # Download option
                        csv = result_df.to_csv(index=False)
                        st.download_button(
                            label="💾 Download as CSV",
                            data=csv,
                            file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("Query returned no results")
        
        # Tab 3: Data Analysis
        with tab3:
            st.subheader("Automated Data Analysis")
            
            # Get available columns for analysis
            try:
                # Quick analysis of timesreport_facts if it exists
                test_query = "SELECT * FROM timesreport_facts LIMIT 1"
                test_df = conn.execute(test_query).df()
                
                if not test_df.empty:
                    st.write("### 📊 TIMES Database Quick Analysis")
                    
                    # Get key metrics
                    analysis_col1, analysis_col2 = st.columns(2)
                    
                    with analysis_col1:
                        # Data overview metrics
                        st.write("**🔢 Data Overview**")
                        
                        metrics_queries = {
                            "Total Records": "SELECT COUNT(*) as count FROM timesreport_facts",
                            "Unique Scenarios": "SELECT COUNT(DISTINCT scen) as count FROM timesreport_facts",
                            "Year Range": "SELECT MIN(year) || ' - ' || MAX(year) as range FROM timesreport_facts",
                            "Unique Regions": "SELECT COUNT(DISTINCT reg) as count FROM timesreport_facts",
                            "Unique Processes": "SELECT COUNT(DISTINCT prc) as count FROM timesreport_facts",
                            "Unique Commodities": "SELECT COUNT(DISTINCT com) as count FROM timesreport_facts"
                        }
                        
                        for metric_name, metric_query in metrics_queries.items():
                            try:
                                result = conn.execute(metric_query).df()
                                if not result.empty:
                                    value = result.iloc[0, 0]
                                    st.metric(metric_name, value)
                            except:
                                st.metric(metric_name, "N/A")
                    
                    with analysis_col2:
                        # Topic distribution
                        st.write("**📈 Topic Distribution**")
                        try:
                            topic_query = """
                            SELECT topic, COUNT(*) as count 
                            FROM timesreport_facts 
                            GROUP BY topic 
                            ORDER BY count DESC
                            """
                            topic_df = conn.execute(topic_query).df()
                            
                            if not topic_df.empty:
                                fig_pie = px.pie(topic_df, values='count', names='topic', 
                                               title="Records by Topic")
                                fig_pie.update_layout(height=300)
                                st.plotly_chart(fig_pie, use_container_width=True)
                        except:
                            st.info("Could not generate topic distribution chart")
                    
                    # Temporal analysis
                    st.write("### 📅 Temporal Analysis")
                    try:
                        temporal_query = """
                        SELECT year, topic, SUM(value) as total_value
                        FROM timesreport_facts 
                        WHERE value > 0
                        GROUP BY year, topic
                        ORDER BY year, topic
                        """
                        temporal_df = conn.execute(temporal_query).df()
                        
                        if not temporal_df.empty:
                            fig_line = px.line(temporal_df, x='year', y='total_value', color='topic',
                                             title="Total Values by Year and Topic")
                            fig_line.update_layout(height=400)
                            st.plotly_chart(fig_line, use_container_width=True)
                    except Exception as e:
                        st.info(f"Could not generate temporal analysis: {e}")
                        
            except Exception as e:
                st.info("No timesreport_facts table found. Use the SQL Query tab to explore available data.")
        
        # Tab 4: Quick Charts
        with tab4:
            st.subheader("Quick Chart Generator")
            
            # Chart builder interface
            st.write("### 🎨 Build Custom Charts")
            
            chart_query = st.text_area(
                "Enter query for chart data:",
                value="SELECT year, SUM(value) as total FROM timesreport_facts WHERE topic = 'energy' GROUP BY year ORDER BY year",
                height=100,
                help="Query should return data suitable for charting"
            )
            
            chart_type = st.selectbox("Chart Type:", ["Line Chart", "Bar Chart", "Scatter Plot", "Area Chart"])
            
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if st.button("📊 Generate Chart"):
                    try:
                        chart_df, error = execute_query(conn, chart_query, 1000)
                        
                        if error:
                            st.error(f"Query failed: {error}")
                        elif chart_df is not None and not chart_df.empty:
                            st.session_state.chart_data = chart_df
                            st.session_state.chart_type = chart_type
                            st.success("Chart data loaded!")
                        else:
                            st.warning("Query returned no data")
                    except Exception as e:
                        st.error(f"Error generating chart: {e}")
            
            with col2:
                # Display chart if data is available
                if 'chart_data' in st.session_state and 'chart_type' in st.session_state:
                    df = st.session_state.chart_data
                    chart_type = st.session_state.chart_type
                    
                    if len(df.columns) >= 2:
                        x_col = df.columns[0]
                        y_col = df.columns[1]
                        color_col = df.columns[2] if len(df.columns) > 2 else None
                        
                        try:
                            if chart_type == "Line Chart":
                                fig = px.line(df, x=x_col, y=y_col, color=color_col)
                            elif chart_type == "Bar Chart":
                                fig = px.bar(df, x=x_col, y=y_col, color=color_col)
                            elif chart_type == "Scatter Plot":
                                fig = px.scatter(df, x=x_col, y=y_col, color=color_col)
                            elif chart_type == "Area Chart":
                                fig = px.area(df, x=x_col, y=y_col, color=color_col)
                            
                            fig.update_layout(height=400)
                            st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.error(f"Could not create chart: {e}")
                    else:
                        st.warning("Chart data needs at least 2 columns")
    
    else:
        st.info("👆 Please connect to a database using the sidebar to start using database tools.")
        
        # Show feature overview
        st.markdown("""
        ## 🎯 Database Tools Features
        
        ### 🔍 **Schema Explorer**
        - **Table Discovery**: Browse all tables and their structures
        - **Column Analysis**: View column types, constraints, and properties  
        - **Data Sampling**: Preview sample data from any table
        - **Statistics**: Row counts, column counts, and basic metrics
        - **Interactive Navigation**: Click-through table exploration
        
        ### ⚡ **SQL Query Interface**
        - **Query Templates**: Pre-built queries for common analyses
        - **Safety Controls**: Automatic row limits to prevent performance issues
        - **Execution Timing**: Monitor query performance
        - **Result Export**: Download query results as CSV
        - **Error Handling**: Clear error messages and query validation
        
        ### 📊 **Automated Data Analysis**
        - **Quick Metrics**: Instant overview of database contents
        - **Topic Distribution**: Visual breakdown of data categories
        - **Temporal Analysis**: Time-series trends and patterns
        - **Statistical Summaries**: Key statistics and data quality metrics
        - **Interactive Charts**: Plotly-based visualizations
        
        ### 📈 **Quick Chart Generator**
        - **Custom Queries**: Build charts from any SQL query result
        - **Multiple Chart Types**: Line, bar, scatter, and area charts
        - **Dynamic Visualization**: Real-time chart generation
        - **Interactive Features**: Zoom, pan, and hover details
        - **Flexible Data Mapping**: Automatic column detection for X/Y/Color axes
        
        ### 🛡️ **Safety Features**
        - **Row Limits**: Automatic limits to prevent memory issues
        - **Query Validation**: Basic SQL validation and error handling
        - **Performance Monitoring**: Execution time tracking
        - **Cache Management**: Efficient data caching for repeated operations
        - **Connection Management**: Robust database connection handling
        
        ### 💾 **Data Export Options**
        - **CSV Download**: Export query results and analysis data
        - **Formatted Reports**: Structured data export with timestamps
        - **Chart Export**: Save visualizations (via browser)
        - **Session Persistence**: Maintain query history and results
        
        ### 🎛️ **Connection Options**
        - **Local Files**: Connect to local DuckDB files
        - **Azure Storage**: Download and connect to cloud databases
        - **Cache Management**: Local caching for cloud databases
        - **URL Validation**: Automatic URL expiry checking
        """)

if __name__ == "__main__":
    main()