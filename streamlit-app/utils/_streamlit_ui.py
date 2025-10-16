# for streamlit components
import streamlit as st
import pandas as pd
from typing import Optional, List, Dict, Any

from ._query_with_csv import PandasDFCreator
from ._query_dynamic import DuckDBQueryHelper, GenericFilter


def get_unique_values(query_helper: DuckDBQueryHelper, column: str, table: str = "timesreport_facts"):
    """
    Streamlit wrapper for DuckDBQueryHelper.fetch_unique_values.
    Shows error in Streamlit if query fails.
    
    Args:
        query_helper: DuckDBQueryHelper instance
        column: Column name to get unique values from
        table: Table name (default: 'timesreport_facts')
        
    Returns:
        List of unique values
    """
    values = query_helper.fetch_unique_values(column, table)
    if not values:
        st.error(f"Error getting unique values for {column}")
    return values


class SidebarConfig:
    """
    Handles sidebar configuration for database connection and data loading.
    Returns configuration values needed to load data.
    """
    
    def __init__(self):
        self.db_source = None
        # self.mapping_csv = None
        self.is_url = None
        self.reload_requested = False
    
    def render(self) -> dict:
        """
        Render sidebar UI elements and return configuration dictionary.
        
        Returns:
            dict with keys: 'db_source', 'mapping_csv', 'is_url', 'reload_requested', 'valid'
        """
        # Sidebar: Connection Type Selection
        st.sidebar.header("Database Connection")
        connection_type = st.sidebar.radio(
            "Connection Type:",
            ["Azure URL", "Local File"],
            help="Choose whether to connect to a database via Azure URL or local file path"
        )

        # Get database source based on connection type
        if connection_type == "Azure URL":
            self.db_source = st.sidebar.text_input(
                "Database URL:",
                value="https://speedlocal.flowcore.app/api/duckdb/share/50614a06f4d629b27b7672c97d9f6774",
                help="Enter the Azure blob storage URL for the DuckDB database"
            )
            self.is_url = True
        else:
            self.db_source = st.sidebar.text_input(
                "Database File Path:",
                value="data/local_database.duckdb",
                help="Enter the local path to your DuckDB database file"
            )
            self.is_url = False

        # Mapping CSV input #<--- disabled for now but can explore if useful or not (ex. changing the filter for included data)
        # self.mapping_csv = st.sidebar.text_input(
        #     "Mapping CSV Path:",
        #     value="inputs/mapping_db_views.csv",
        #     help="Path to the mapping CSV file"
        # )

        # Add a button to load/reload data
        self.reload_requested = st.sidebar.button("Reload Data", type="primary")

        # Validate inputs
        valid = True
        if not self.db_source:
            st.warning("Please provide a database source.")
            valid = False
        
        # if not self.mapping_csv:
        #     st.warning("Please provide a mapping CSV path.")
        #     valid = False
        
        return {
            'db_source': self.db_source,
            # 'mapping_csv': self.mapping_csv,
            'is_url': self.is_url,
            'reload_requested': self.reload_requested,
            'valid': valid
        }

class FilterUI:
    """
    Streamlit UI component for GenericFilter.
    Provides interactive widgets for multi-column filtering.
    """
    
    def __init__(
        self, 
        generic_filter: GenericFilter,
        default_columns: Optional[List[str]] = None,
        section_title: str = "Data Filters"
    ):
        """
        Initialize FilterUI.
        
        Args:
            generic_filter: GenericFilter instance
            default_columns: Columns to show filters for by default
            section_title: Title for the filter section
        """
        self.generic_filter = generic_filter
        self.default_columns = default_columns or []
        self.section_title = section_title
    
    def render(self) -> Dict[str, List[Any]]:
        """
        Render the filter UI in Streamlit sidebar.
        
        Returns:
            Dictionary of active filters
        """
        st.sidebar.header(self.section_title)
        
        # Get available columns
        available_columns = self.generic_filter.get_available_columns()
        
        if not available_columns:
            st.sidebar.warning("No filterable columns available.")
            return {}
        
        # Column selection
        selected_columns = st.sidebar.multiselect(
            "Pick which attributes to filter:",
            options=available_columns,
            default=self.default_columns,
            help="Select columns to create filters for",
            key="filter_column_selector"
        )
        
        # Clear all filters button
        if st.sidebar.button("Clear All Filters", key="clear_filters_btn"):
            self.generic_filter.clear_filters()
            st.rerun()
        
        # Create filters for selected columns
        if selected_columns:
            st.sidebar.markdown("---")
            st.sidebar.subheader("Active Filters")
            
            for column in selected_columns:
                unique_values = self.generic_filter.get_unique_values(column)
                
                if not unique_values:
                    st.sidebar.warning(f"No values found for '{column}'")
                    continue
                
                # Get current filter values (if any)
                current_filter = self.generic_filter.get_active_filters().get(column, [])
                
                # Create multiselect for this column
                selected_values = st.sidebar.multiselect(
                    f"Filter by {column}:",
                    options=unique_values,
                    default=current_filter if current_filter else unique_values,
                    help=f"Select values to filter for {column}",
                    key=f"filter_{column}"
                )
                
                # Update filter
                self.generic_filter.set_filter(column, selected_values)
        
        # Display filter summary
        active_filters = self.generic_filter.get_active_filters()
        if active_filters:
            st.sidebar.markdown("---")
            st.sidebar.caption("**Filter Summary:**")
            st.sidebar.caption(self.generic_filter.get_filter_summary())
        
        return active_filters

class ST_PandasDFLoader:
    """
    Streamlit wrapper for PandasDFCreator.
    Loads DataFrames from DuckDB based on mapping CSV with Streamlit UI feedback.
    """
    def __init__(self, db_source: str, mapping_csv: str, is_url: bool = False):

        """
        Initialize the ST_PandasDFLoader.
        
        Args:
            db_source: Database URL or local file path
            mapping_csv: Path to mapping CSV file
            is_url: Whether db_source is a URL (True) or local file (False)
        """
        self.db_source = db_source
        self.mapping_csv = mapping_csv
        self.is_url = is_url
        self.table_dfs = {}
        self.available_tables = []
        self.loaded_tables = []
        self.missing_tables = []
    
    def load_dataframes(self) -> dict:
        """
        Load all DataFrames based on mapping CSV.
        Returns dictionary of table_name -> DataFrame.
        Displays Streamlit UI feedback during loading.
        """
        try:
            with st.spinner("Loading data from database..."):
                # Create PandasDFCreator instance
                creator = PandasDFCreator(
                    db_source=self.db_source, 
                    mapping_csv=self.mapping_csv, 
                    is_url=self.is_url
                )
                
                # Read mapping CSV to get available tables
                mapping_df = pd.read_csv(self.mapping_csv)
                self.available_tables = mapping_df['table'].unique().tolist()
                
                # st.sidebar.info(f"Tables in mapping CSV: {', '.join(self.available_tables)}")
                
                # Load all DataFrames
                dfs_dict = creator.run()
                
                # Validate that we got data
                if not dfs_dict:
                    st.error("No data was loaded from the database.")
                    return {}
                
                # Check which tables were successfully loaded
                self.loaded_tables = [
                    name for name, df in dfs_dict.items() 
                    if df is not None and not df.empty
                ]
                self.missing_tables = [
                    name for name in self.available_tables 
                    if name not in self.loaded_tables
                ]
                
                # Display loading status
                # if self.loaded_tables:
                #     st.sidebar.success(
                #         f"✓ Data loaded successfully! Loaded tables: {', '.join(self.loaded_tables)}"
                #     )
                
                # if self.missing_tables:
                #     st.sidebar.warning(
                #         f"⚠ Missing or empty tables: {', '.join(self.missing_tables)}"
                #     )
                
                # Store DataFrames by table name
                for table_name in self.available_tables:
                    df = dfs_dict.get(table_name)
                    if df is not None and not df.empty:
                        self.table_dfs[table_name] = df
                    else:
                        st.warning(f"Table '{table_name}' is empty or not found.")
                
                # Check if we have at least some data to work with
                if not self.table_dfs:
                    st.error("No valid data tables were loaded. Please check your mapping CSV and database.")
                    return {}
                
                return self.table_dfs
        
        except FileNotFoundError as e:
            st.error(f"File not found: {str(e)}")
            return {}
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            return {}
    
    def get_table(self, table_name: str) -> pd.DataFrame:
        """
        Get a specific table DataFrame.
        
        Args:
            table_name: Name of the table to retrieve
            
        Returns:
            DataFrame or None if not found
        """
        return self.table_dfs.get(table_name)
    
    def get_all_tables(self) -> dict:
        """
        Get all loaded tables.
        
        Returns:
            Dictionary of table_name -> DataFrame
        """
        return self.table_dfs
    
    def has_table(self, table_name: str) -> bool:
        """
        Check if a table was successfully loaded.
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            True if table exists and is not empty
        """
        return table_name in self.table_dfs