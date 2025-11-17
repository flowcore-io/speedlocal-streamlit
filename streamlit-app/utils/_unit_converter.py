"""
Unit conversion utilities for TIMES data.
"""

import pandas as pd
from typing import Dict, List, Tuple, Optional


class UnitConverter:
    """Handles unit conversions based on conversion table."""
    
    def __init__(self, conversions_df: pd.DataFrame):
        """
        Initialize UnitConverter with conversion rules.
        
        Args:
            conversions_df: DataFrame from unit_conversions.csv with columns:
                           unit_long, from_unit, to_unit, factor, category
        """
        self.conversions_df = conversions_df
        
        # Create category lookup: unit → category
        self.unit_to_category = dict(zip(
            conversions_df['from_unit'],
            conversions_df['category']
        ))
    
    def get_conversion_factor(self, from_unit: str, to_unit: str) -> Optional[float]:
        """
        Look up conversion factor between two units.
        
        Args:
            from_unit: Source unit (e.g., 'kt')
            to_unit: Target unit (e.g., 't')
            
        Returns:
            Conversion factor or None if not found
        """
        match = self.conversions_df[
            (self.conversions_df['from_unit'] == from_unit) &
            (self.conversions_df['to_unit'] == to_unit)
        ]
        
        if not match.empty:
            return match.iloc[0]['factor']
        
        return None
    
    def get_category(self, unit: str) -> Optional[str]:
        """
        Get category for a given unit.
        
        Args:
            unit: Unit code (e.g., 't', 'kt')
            
        Returns:
            Category string or None if not found
        """
        return self.unit_to_category.get(unit)
    
    def get_units_by_category(self, category: str) -> List[str]:
        """
        Get all units belonging to a category.
        
        Args:
            category: Category name (e.g., 'mass', 'energy')
            
        Returns:
            List of unit codes
        """
        units = self.conversions_df[
            self.conversions_df['category'] == category
        ]['to_unit'].unique().tolist()
        
        return units
    
    def get_unit_display_name(self, unit: str) -> str:
        """
        Get display name for a unit.
        
        Args:
            unit: Unit code (e.g., 't')
            
        Returns:
            Display name (e.g., 'ton') or unit code if not found
        """
        match = self.conversions_df[self.conversions_df['to_unit'] == unit]
        
        if not match.empty:
            return match.iloc[0]['unit_long']
        
        return unit
    
    def filter_by_categories(
        self,
        df: pd.DataFrame,
        selected_categories: List[str],
        unit_col: str = 'unit'
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Filter dataframe to only include rows with units in selected categories.
        
        Args:
            df: DataFrame to filter
            selected_categories: List of category names to keep
            unit_col: Name of column containing units
            
        Returns:
            Tuple of:
                - Filtered DataFrame
                - List of unknown units that were filtered out
        """
        if df.empty or unit_col not in df.columns:
            return df, []
        
        # Find units not in our conversion table
        unknown_units = []
        valid_units = []
        
        for unit in df[unit_col].dropna().unique():
            if unit in self.unit_to_category:
                category = self.unit_to_category[unit]
                if category in selected_categories:
                    valid_units.append(unit)
            else:
                unknown_units.append(unit)
        
        # Filter to valid units only
        if valid_units:
            df_filtered = df[df[unit_col].isin(valid_units)].copy()
        else:
            df_filtered = pd.DataFrame()
        
        return df_filtered, unknown_units
    
    def convert_dataframe(
        self,
        df: pd.DataFrame,
        target_units: Dict[str, str],
        unit_col: str = 'unit',
        value_col: str = 'value'
    ) -> pd.DataFrame:
        """
        Convert values in dataframe based on target units for each category.
        
        Args:
            df: DataFrame to convert
            target_units: Dict mapping category → target unit (e.g., {'mass': 't'})
            unit_col: Name of column containing units
            value_col: Name of column containing values to convert
            
        Returns:
            DataFrame with converted values and updated units
        """
        if df.empty or unit_col not in df.columns or value_col not in df.columns:
            return df
        
        df_converted = df.copy()
        
        for idx, row in df_converted.iterrows():
            current_unit = row[unit_col]
            
            if pd.isna(current_unit):
                continue
            
            # Get category for this unit
            category = self.unit_to_category.get(current_unit)
            
            if category and category in target_units:
                target_unit = target_units[category]
                
                # Skip if already in target unit
                if current_unit == target_unit:
                    continue
                
                # Get conversion factor
                factor = self.get_conversion_factor(current_unit, target_unit)
                
                if factor is not None:
                    # Convert value
                    df_converted.at[idx, value_col] = row[value_col] * factor
                    # Update unit
                    df_converted.at[idx, unit_col] = target_unit
        
        return df_converted