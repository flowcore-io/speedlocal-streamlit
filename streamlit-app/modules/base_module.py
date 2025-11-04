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
        filters: Dict[str, Any],
        data_loader: Any
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
