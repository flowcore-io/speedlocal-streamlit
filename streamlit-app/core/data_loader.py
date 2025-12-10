"""
Data loading manager using existing PandasDFCreator.
Wrapper around the existing data loading functionality.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Optional
from pathlib import Path

# Import from existing utils
import sys
sys.path.append(str(Path(__file__).parent.parent / "utils"))
from _query_with_csv import PandasDFCreator
from _connection_functions import connect_to_db
from _query_dynamic import DuckDBQueryHelper


class DataLoaderManager:
    """
    Centralized data loading manager.
    Wraps the existing PandasDFCreator functionality.
    """
    
    def __init__(self, db_source: str, mapping_csv: str, is_url: bool = False):
        """
        Initialize DataLoaderManager.
        
        Args:
            db_source: Database URL or local file path
            mapping_csv: Path to mapping CSV file
            is_url: Whether db_source is a URL
        """
        self.db_source = db_source
        self.mapping_csv = mapping_csv
        self.is_url = is_url
        self.table_dfs: Dict[str, pd.DataFrame] = {}
        self.creator: Optional[PandasDFCreator] = None
    
    def load_all_tables(self) -> Dict[str, pd.DataFrame]:
        """
        Load all tables using PandasDFCreator.
        
        Returns:
            Dictionary of table_name -> DataFrame
        """
        try:
            # Create PandasDFCreator instance
            self.creator = PandasDFCreator(
                db_source=self.db_source,
                mapping_csv=self.mapping_csv,
                is_url=self.is_url,
                use_cache=True
            )
            
            # Load all dataframes
            self.table_dfs = self.creator.run()
            
            # Validate
            if not self.table_dfs:
                st.error("No data was loaded from the database.")
                return {}
            
            # Log success
            loaded_tables = [name for name, df in self.table_dfs.items() if not df.empty]
            st.sidebar.success(f"✓ Loaded {len(loaded_tables)} tables successfully")
            
            return self.table_dfs
            
        except FileNotFoundError as e:
            st.error(f"File not found: {str(e)}")
            return {}
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            return {}
    
    def get_table(self, table_name: str) -> Optional[pd.DataFrame]:
        """
        Get a specific table DataFrame.
        
        Args:
            table_name: Name of the table
            
        Returns:
            DataFrame or None if not found
        """
        return self.table_dfs.get(table_name)
    
    def has_table(self, table_name: str) -> bool:
        """
        Check if a table exists and is not empty.
        
        Args:
            table_name: Name of the table
            
        Returns:
            True if table exists and has data
        """
        df = self.table_dfs.get(table_name)
        return df is not None and not df.empty
    
    def get_all_tables(self) -> Dict[str, pd.DataFrame]:
        """Get all loaded tables."""
        return self.table_dfs.copy()
    
    def get_loaded_table_names(self) -> list:
        """Get list of successfully loaded table names."""
        return [name for name, df in self.table_dfs.items() if not df.empty]

    def load_description_tables(self) -> pd.DataFrame:
        """
        Extract description tables from database and deduplicate.
        
        Returns:
            DataFrame with columns: set_name, element, description
        """
        try:
            # Connect to database
            conn = connect_to_db(
                source=self.creator.db_source,
                is_url=self.creator.is_url,
                use_cache=True
            )
            
            if conn is None:
                st.warning("Failed to connect to database for description tables.")
                return pd.DataFrame()
            
            # Extract description tables
            query_helper = DuckDBQueryHelper(conn)
            desc_data = query_helper.extract_desc_tables()
            
            # Close connection
            conn.close()
            
            if not desc_data:
                return pd.DataFrame()
            
            # Convert to DataFrame and deduplicate
            desc_df = pd.DataFrame(desc_data)
            desc_df = desc_df.drop_duplicates(subset=['set_name', 'element', 'description'])
            
            return desc_df
            
        except Exception as e:
            st.warning(f"Could not load description tables: {str(e)}")
            return pd.DataFrame()
    def load_unit_conversions(self, conversions_csv: str = "inputs/unit_conversions.csv") -> pd.DataFrame:
        """
        Load unit conversion table.
        
        Args:
            conversions_csv: Path to unit conversions CSV file
            
        Returns:
            DataFrame with conversion rules
        """
        try:
            from pathlib import Path
            csv_path = Path(conversions_csv)
            
            if not csv_path.exists():
                st.warning(f"Unit conversions file not found: {conversions_csv}")
                return pd.DataFrame()
            
            conversions_df = pd.read_csv(csv_path)
            
            # Validate required columns
            required_cols = ['unit_long', 'from_unit', 'to_unit', 'factor', 'category']
            missing_cols = [col for col in required_cols if col not in conversions_df.columns]
            
            if missing_cols:
                st.error(f"Unit conversions CSV missing columns: {missing_cols}")
                return pd.DataFrame()
            
            st.sidebar.success(f"✓ Loaded {len(conversions_df)} unit conversion rules")
            return conversions_df
            
        except Exception as e:
            st.warning(f"Could not load unit conversions: {str(e)}")
            return pd.DataFrame()
    def apply_label_descriptions(self, desc_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Apply descriptions to label columns in all loaded tables.
        
        Args:
            desc_df: Description DataFrame with columns [set_name, element, description]
            
        Returns:
            Updated table_dfs dictionary with label columns mapped to descriptions
        """
        if desc_df.empty:
            return self.table_dfs
        
        # Create a flat lookup: element -> description (across all desc tables)
        label_lookup = {}
        for _, row in desc_df.iterrows():
            element = str(row['element'])
            description = str(row['description'])
            # Store mapping (last one wins if duplicates exist)
            label_lookup[element] = description
        
        # Apply to each table that has a label column
        updated_tables = {}
        for table_name, df in self.table_dfs.items():
            if df.empty or 'label' not in df.columns:
                updated_tables[table_name] = df
                continue
            
            # Map label values to descriptions
            df_updated = df.copy()
            df_updated['label'] = df_updated['label'].map(label_lookup).fillna(df_updated['label'])
            updated_tables[table_name] = df_updated
        
        self.table_dfs = updated_tables
        return self.table_dfs
def create_description_mapping(desc_df: pd.DataFrame) -> Dict[str, Dict[str, str]]:
    """
    Create nested dictionary mapping from description DataFrame.
    
    Args:
        desc_df: DataFrame with columns [set_name, element, description]
    
    Returns:
        Nested dict like: {'sector': {'TRA': 'Transport', ...}, 'comgroup': {...}}
    """
    if desc_df.empty:
        return {}
    
    mapping = {}
    
    # Group by set_name (e.g., 'sector_desc', 'comgroup_desc')
    for set_name, group in desc_df.groupby('set_name'):
        # Remove '_desc' suffix to get column name
        # 'sector_desc' -> 'sector'
        column_name = set_name.replace('_desc', '')
        
        # Create mapping: element -> description
        mapping[column_name] = dict(zip(group['element'], group['description']))
    
    return mapping