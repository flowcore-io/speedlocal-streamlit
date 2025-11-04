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
