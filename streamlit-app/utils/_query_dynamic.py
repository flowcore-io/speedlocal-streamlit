# utils/_query_dynamic.py

import pandas as pd
import duckdb
from typing import Dict, List, Optional, Any

class DuckDBQueryHelper:
    """Reusable class for querying DuckDB database."""

    def __init__(self, conn: duckdb.DuckDBPyConnection):
        """
        Initialize with an active DuckDB connection.
        
        Args:
            conn: DuckDB connection object
        """
        if conn is None:
            raise ValueError("A valid DuckDB connection is required.")
        self.conn = conn

    def fetch_unique_values(self, column: str, table: str = "timesreport_facts") -> list:
        """
        Get unique values for a given column.

        Args:
            column (str): Column name
            table (str): Table name (default: 'timesreport_facts')

        Returns:
            List of unique values
        """
        try:
            query = f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL ORDER BY {column}"
            result = self.conn.execute(query).fetchall()
            return [x[0] for x in result]
        except Exception as e:
            print(f"Error fetching unique values for {column}: {e}")
            return []

    def extract_desc_tables(self) -> list:
        """
        Extract all tables ending with '_desc' and return a list of dictionaries
        with keys 'set_name', 'element', 'description'.
        """
        desc_data = []

        try:
            # Get all table names
            tables_df = self.conn.sql("SHOW TABLES").df()
            table_names = tables_df['name'].tolist()

            # Filter tables ending with '_desc'
            desc_tables = [name for name in table_names if name.lower().endswith('_desc')]

            for table_name in desc_tables:
                try:
                    df = self.conn.sql(f"SELECT * FROM {table_name}").df()
                    records_added = 0

                    # Use 'id' as element and 'description' as description
                    if 'id' in df.columns and 'description' in df.columns:
                        for _, row in df.iterrows():
                            desc_data.append({
                                'set_name': table_name,
                                'element': str(row['id']),
                                'description': str(row['description'])
                            })
                            records_added += 1

                    print(f"Extracted {records_added} records from table '{table_name}'")

                except Exception as e:
                    print(f"Error processing table '{table_name}': {e}")
                    continue

        except Exception as e:
            print(f"Error querying DuckDB: {e}")

        return desc_data
    
    def run_query(self, query: str) -> pd.DataFrame:
        """Execute an arbitrary SQL query and return a DataFrame."""
        try:
            return self.conn.sql(query).df()
        except Exception as e:
            print(f"Error executing query: {e}")
            return pd.DataFrame()
        
    def fetch_filtered_data(self, table: str, filters: dict) -> pd.DataFrame:
        """
        Fetch filtered data dynamically using WHERE conditions.

        Args:
            table (str): Table name
            filters (dict): {column: value} pairs for filtering

        Returns:
            pd.DataFrame: Filtered data
        """
        try:
            conditions = []
            for col, val in filters.items():
                if isinstance(val, list):
                    vals = ', '.join(f"'{v}'" for v in val)
                    conditions.append(f"{col} IN ({vals})")
                else:
                    conditions.append(f"{col} = '{val}'")
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            query = f"SELECT * FROM {table} WHERE {where_clause}"
            return self.conn.sql(query).df()

        except Exception as e:
            print(f"Error fetching filtered data: {e}")
            return pd.DataFrame()
    
    def list_tables(self) -> list:
        """Return a list of available tables in the database."""
        try:
            return self.conn.sql("SHOW TABLES").df()["name"].tolist()
        except Exception as e:
            print(f"Error listing tables: {e}")
            return []

class GenericFilter:
    """
    Generic filter class for creating flexible multi-column filters.
    Works with DataFrames to provide filtering capabilities.
    """
    
    def __init__(self, df: pd.DataFrame, filterable_columns: Optional[List[str]] = None):
        """
        Initialize GenericFilter with a DataFrame.
        
        Args:
            df: DataFrame to filter
            filterable_columns: List of column names that can be filtered.
                              If None, all columns are filterable.
        """
        self.df = df
        self.filterable_columns = filterable_columns or list(df.columns)
        self.active_filters: Dict[str, List[Any]] = {}
    
    def get_available_columns(self) -> List[str]:
        """Get list of columns available for filtering."""
        return [col for col in self.filterable_columns if col in self.df.columns]
    
    def get_unique_values(self, column: str) -> List[Any]:
        """
        Get unique values for a specific column.
        
        Args:
            column: Column name
            
        Returns:
            Sorted list of unique values
        """
        if column not in self.df.columns:
            return []
        
        unique_vals = self.df[column].dropna().unique()
        try:
            return sorted(unique_vals)
        except TypeError:
            # If values aren't sortable, return as list
            return list(unique_vals)
    
    def set_filter(self, column: str, values: List[Any]) -> None:
        """
        Set filter for a specific column.
        
        Args:
            column: Column name to filter
            values: List of values to filter by
        """
        if values:  # Only set if values list is not empty
            self.active_filters[column] = values
        elif column in self.active_filters:
            # Remove filter if values list is empty
            del self.active_filters[column]
    
    def remove_filter(self, column: str) -> None:
        """Remove filter for a specific column."""
        if column in self.active_filters:
            del self.active_filters[column]
    
    def clear_filters(self) -> None:
        """Clear all active filters."""
        self.active_filters = {}
    
    def get_active_filters(self) -> Dict[str, List[Any]]:
        """Get dictionary of currently active filters."""
        return self.active_filters.copy()
    
    def apply_filters(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Apply all active filters to DataFrame.
        
        Args:
            df: DataFrame to filter. If None, uses self.df
            
        Returns:
            Filtered DataFrame
        """
        df_to_filter = df if df is not None else self.df
        
        if not self.active_filters:
            return df_to_filter.copy()
        
        filtered_df = df_to_filter.copy()
        
        for column, values in self.active_filters.items():
            if column in filtered_df.columns and values:
                filtered_df = filtered_df[filtered_df[column].isin(values)]
        
        return filtered_df
    
    def get_filter_summary(self) -> str:
        """
        Get a human-readable summary of active filters.
        
        Returns:
            String description of active filters
        """
        if not self.active_filters:
            return "No active filters"
        
        summary_parts = []
        for column, values in self.active_filters.items():
            value_str = ", ".join(str(v) for v in values[:3])
            if len(values) > 3:
                value_str += f" (+ {len(values) - 3} more)"
            summary_parts.append(f"{column}: {value_str}")
        
        return " | ".join(summary_parts)