"""
Base module class that all visualization modules inherit from.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import streamlit as st
import pandas as pd

from utils.unit_converter import extract_unit_label

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
        """
        pass
    
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """
        Return configuration for this module.
        
        Configuration includes:
        - apply_global_filters: Whether to apply global scenario filters
        - apply_unit_conversion: Whether to show unit conversion controls
        - show_module_filters: Whether to show additional filter options
        - filterable_columns: List of columns that can be filtered
        - default_columns: List of columns to filter by default
        
        Returns:
            Dictionary of configuration settings
        """
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
    
    def _apply_unit_conversion(
        self,
        df: pd.DataFrame,
        filters: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        Apply unit conversion if enabled in module config.
        Standardizes the pattern used across all modules.
        
        Args:
            df: DataFrame to convert
            filters: Filters containing unit_config
            
        Returns:
            Converted DataFrame or original if conversion not enabled/available
        """
        if df.empty:
            return df
        
        # Check if module wants unit conversion
        config = self.get_config()
        if not config.get('apply_unit_conversion', False):
            return df
        
        # Get unit manager from session
        unit_mgr = st.session_state.get('unit_manager')
        
        if not unit_mgr or 'unit_config' not in filters:
            return df
        
        # Apply conversion
        unit_config = unit_mgr.get_unit_config_from_filters(filters)
        df_converted, _ = unit_mgr.apply_unit_conversion(
            df,
            unit_config,
            section_title=self.name
        )
        
        return df_converted
    
    def _get_unit_label(self, df: pd.DataFrame) -> str:
        """
        Extract unit label from dataframe for axis labels.
        Wrapper around utility function.
        """
        return extract_unit_label(df)
    
    def _render_unit_controls(
        self,
        table_dfs: Dict[str, pd.DataFrame],
        filters: Dict[str, Any],
        expanded: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Render unit conversion controls if enabled in module config.
        
        Args:
            table_dfs: All available tables
            filters: Current filters (currently unused, reserved for state restoration)
            expanded: Whether expander should be open by default
        
        Returns:
            Unit config dict or None if not applicable
        """
        # Check if module wants unit conversion
        config = self.get_config()
        if not config.get('apply_unit_conversion', False):
            return None
        
        # Get unit manager from session
        unit_mgr = st.session_state.get('unit_manager')
        
        if not unit_mgr:
            return None
        
        # Render controls
        unit_config = unit_mgr.render_unit_controls_if_enabled(
            module=self,
            table_dfs=table_dfs,
            expanded=expanded
        )
        
        return unit_config

class BaseVisualizationModule(BaseModule):
    """
    Standard pattern for visualization modules.
    
    Provides a consistent render flow:
    1. Validate data
    2. Render unit controls
    3. Load and prepare data
    4. Apply filters
    5. Apply unit conversion
    6. Render visualization
    
    Subclasses must implement:
    - _load_and_prepare_data()
    - _render_visualization()
    """
    
    def render(
        self,
        table_dfs: Dict[str, pd.DataFrame],
        filters: Dict[str, Any]
    ) -> None:
        """
        Standard render flow for visualization modules.
        
        Args:
            table_dfs: Dictionary of loaded DataFrames
            filters: Active filter settings
        """
        # 1. Validate data
        if not self.validate_data(table_dfs):
            self.show_error("Required data tables not available.")
            return
        
        # 2. Render unit controls (if enabled in config)
        unit_config = self._render_unit_controls(table_dfs, filters, expanded=False)
        if unit_config:
            filters['unit_config'] = unit_config
        
        st.divider()
        
        # 3. Show conversion summary (if unit conversion is enabled)
        # if unit_config:
        #     unit_mgr = st.session_state.get('unit_manager')
        #     if unit_mgr:
        #         unit_mgr.show_conversion_summary()
        
        # 4. Load and prepare data (module-specific)
        df = self._load_and_prepare_data(table_dfs)
        
        if df is None or df.empty:
            self.show_warning("No data available after loading.")
            return
        
        # 5. Apply filters
        df = self._apply_filters(df, filters)
        
        if df.empty:
            self.show_warning("No data available after applying filters.")
            return
        
        # 6. Apply unit conversion (if enabled)
        df = self._apply_unit_conversion(df, filters)
        
        if df.empty:
            self.show_warning("No data remaining after unit conversion.")
            return
        
        # 7. Render visualization (module-specific)
        self._render_visualization(df, filters)
    
    @abstractmethod
    def _load_and_prepare_data(
        self,
        table_dfs: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Load and prepare data for visualization.
        
        This is where modules should:
        - Get their required tables
        - Combine multiple tables if needed
        - Apply initial filtering (like attr='f_in')
        - Apply description mappings
        
        Args:
            table_dfs: Dictionary of available tables
            
        Returns:
            Prepared DataFrame ready for filtering and visualization
        """
        pass
    
    @abstractmethod
    def _render_visualization(
        self,
        df: pd.DataFrame,
        filters: Dict[str, Any]
    ) -> None:
        """
        Render the actual visualization.
        
        This is where modules should:
        - Create plots
        - Render interactive controls
        - Display results
        
        Args:
            df: Filtered and converted DataFrame
            filters: Active filters (for reference)
        """
        pass