"""
Base module class that all visualization modules inherit from.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import streamlit as st
import pandas as pd


class BaseModule(ABC):
    """Base class for all Streamlit app modules."""
    
    def __init__(self, name: str, description: str, order: int = 99, enabled: bool = True):
        """
        Initialize base module.
        
        Args:
            name: Display name of the module
            description: Short description of module functionality
            order: Display order (lower numbers appear first)
            enabled: Whether module is enabled
        """
        self.name = name
        self.description = description
        self.order = order
        self.enabled = enabled
        self._data_cache = {}
    
    @abstractmethod
    def get_required_tables(self) -> list:
        """Return list of required database tables."""
        pass
    
    @abstractmethod
    def render(
        self, 
        table_dfs: Dict[str, pd.DataFrame], 
        filters: Dict[str, Any]
    ) -> None:
        """
        Main render method for the module.
        
        Args:
            table_dfs: Dictionary of loaded DataFrames
            filters: Active filter settings
            data_loader: DataLoaderManager instance for additional queries
        """
        pass
    
    @abstractmethod
    def get_filter_config(self) -> Dict[str, Any]:
        """Return configuration for filters specific to this module."""
        pass
    
    def validate_data(self, table_dfs: Dict[str, pd.DataFrame]) -> bool:
        """Validate that required data is available."""
        required = self.get_required_tables()
        return all(
            table in table_dfs and not table_dfs[table].empty 
            for table in required
        )
    
    def _get_desc_mapping(self) -> Dict[str, Dict[str, str]]:
        """Get description mapping from session state."""
        return st.session_state.get('desc_mapping', {})

    def _get_desc_df(self) -> pd.DataFrame:
        """Get description DataFrame from session state."""
        return st.session_state.get('desc_df', pd.DataFrame())

    def _apply_filters(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """
        Apply filters to a DataFrame.
        
        Args:
            df: DataFrame to filter
            filters: Dictionary of column -> values to filter by
        
        Returns:
            Filtered DataFrame
        """
        df_filtered = df.copy()
        
        for col, values in filters.items():
            # Skip if column doesn't exist in this DataFrame
            if col not in df_filtered.columns:
                continue
            
            # Skip if no values selected (empty list)
            if not values:
                continue
            
            # Apply filter
            if isinstance(values, list):
                df_filtered = df_filtered[df_filtered[col].isin(values)]
            else:
                # Single value
                df_filtered = df_filtered[df_filtered[col] == values]
    
        return df_filtered

    def _apply_descriptions(
        self, 
        df: pd.DataFrame, 
        columns: list, 
        desc_mapping: Dict[str, Dict[str, str]]
    ) -> pd.DataFrame:
        """
        Add description columns to DataFrame.
        
        Args:
            df: DataFrame to add descriptions to
            columns: List of column names to map (e.g., ['sector', 'comgroup'])
            desc_mapping: Nested dict with mappings
        
        Returns:
            DataFrame with new columns: sector_desc, comgroup_desc, etc.
        """
        if not desc_mapping:
            return df
        
        df_with_desc = df.copy()
        
        for col in columns:
            if col in df_with_desc.columns and col in desc_mapping:
                # Create new column with descriptions
                # Falls back to original ID if description not found
                df_with_desc[f'{col}_desc'] = df_with_desc[col].map(
                    desc_mapping[col]
                ).fillna(df_with_desc[col])
        
        return df_with_desc 

    def show_error(self, message: str) -> None:
        """Display error message."""
        st.error(f"[{self.name}] {message}")
    
    def show_warning(self, message: str) -> None:
        """Display warning message."""
        st.warning(f"[{self.name}] {message}")
    
    def show_info(self, message: str) -> None:
        """Display info message."""
        st.info(f"[{self.name}] {message}")
    
    def show_success(self, message: str) -> None:
        """Display success message."""
        st.success(f"[{self.name}] {message}")
