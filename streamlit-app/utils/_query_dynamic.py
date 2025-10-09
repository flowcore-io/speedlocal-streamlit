# utils/_query_dynamic.py

import pandas as pd
import duckdb

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