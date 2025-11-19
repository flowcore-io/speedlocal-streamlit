"""
Unit conversion utilities for TIMES data.
Handles both unit and currency conversions with separate columns.
"""

import pandas as pd
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass


@dataclass
class ExclusionInfo:
    """Information about rows excluded during conversion."""
    total_rows: int
    excluded_rows: int
    unknown_units: Set[str]
    unknown_currencies: Set[str]
    unconvertible_units: Set[str]
    unconvertible_currencies: Set[str]
    
    def has_exclusions(self) -> bool:
        """Check if any rows were excluded."""
        return self.excluded_rows > 0
    
    def get_summary(self) -> str:
        """Get human-readable summary of exclusions."""
        if not self.has_exclusions():
            return "No rows excluded"
        
        lines = [f"Excluded {self.excluded_rows} of {self.total_rows} rows:"]
        
        if self.unknown_units:
            lines.append(f"  - Unknown units: {', '.join(sorted(self.unknown_units))}")
        if self.unknown_currencies:
            lines.append(f"  - Unknown currencies: {', '.join(sorted(self.unknown_currencies))}")
        if self.unconvertible_units:
            lines.append(f"  - Unconvertible units: {', '.join(sorted(self.unconvertible_units))}")
        if self.unconvertible_currencies:
            lines.append(f"  - Unconvertible currencies: {', '.join(sorted(self.unconvertible_currencies))}")
        
        return "\n".join(lines)


class UnitConverter:
    """Handles unit and currency conversions based on conversion table."""
    
    def __init__(self, conversions_df: pd.DataFrame, config_path: Optional[str] = None):
        """
        Initialize UnitConverter with conversion rules.
        
        Args:
            conversions_df: DataFrame from unit_conversions.csv with columns:
                           unit_long, from_unit, to_unit, factor, category
            config_path: Path to default_units.yaml config file
        """
        self.conversions_df = conversions_df
        
        # Create category lookup: unit → category
        self.unit_to_category = dict(zip(
            conversions_df['from_unit'],
            conversions_df['category']
        ))
        
        # Load default units from config
        self.default_units = self._load_default_units(config_path)
        self.default_selected_categories = self._load_default_categories(config_path)
    
    def _load_default_units(self, config_path: Optional[str] = None) -> Dict[str, str]:
        """Load default units from YAML config file."""
        if config_path is None:
            # Default to config/default_units.yaml relative to project root
            config_path = Path(__file__).parent.parent / "config" / "default_units.yaml"
        else:
            config_path = Path(config_path)
        
        if not config_path.exists():
            print(f"Warning: Config file not found at {config_path}")
            return {}
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('default_units', {})
        except Exception as e:
            print(f"Warning: Could not load config from {config_path}: {e}")
            return {}
    
    def _load_default_categories(self, config_path: Optional[str] = None) -> List[str]:
        """Load default selected categories from YAML config file."""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "default_units.yaml"
        else:
            config_path = Path(config_path)
        
        if not config_path.exists():
            return []
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('default_selected_categories', [])
        except Exception as e:
            return []
    
    def get_default_unit(self, category: str) -> Optional[str]:
        """Get default target unit for a category."""
        return self.default_units.get(category)
    
    def get_default_target_units(self) -> Dict[str, str]:
        """Get all default target units."""
        return self.default_units.copy()
    
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
    
    def get_all_categories(self) -> List[str]:
        """Get all available categories from conversion table."""
        return sorted(self.conversions_df['category'].unique().tolist())
    
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
    
    def is_unit_known(self, unit: str) -> bool:
        """Check if a unit exists in the conversion table."""
        if pd.isna(unit):
            return False
        return unit in self.unit_to_category
    
    def can_convert(self, from_unit: str, to_unit: str) -> bool:
        """Check if conversion is possible between two units."""
        if pd.isna(from_unit) or pd.isna(to_unit):
            return False
        if from_unit == to_unit:
            return True
        return self.get_conversion_factor(from_unit, to_unit) is not None
    
    def convert_and_filter(
        self,
        df: pd.DataFrame,
        target_units: Optional[Dict[str, str]] = None,
        selected_categories: Optional[List[str]] = None,
        unit_col: str = 'unit',
        currency_col: str = 'cur',
        value_col: str = 'value'
    ) -> Tuple[pd.DataFrame, ExclusionInfo]:
        """
        Convert units/currencies and filter out rows that cannot be converted.
        
        This method handles three cases:
        1. Physical flows/capacity: unit != NA, currency == NA (convert unit only)
        2. Financial flows: unit == NA, currency != NA (convert currency only)
        3. Prices: unit != NA, currency != NA (convert both with special methodology)
        
        Args:
            df: DataFrame to convert
            target_units: Dict mapping category → target unit (uses defaults if None)
            selected_categories: List of categories to include (uses all if None)
            unit_col: Name of column containing units
            currency_col: Name of column containing currencies
            value_col: Name of column containing values to convert
            
        Returns:
            Tuple of:
                - Converted and filtered DataFrame
                - ExclusionInfo object with details about excluded rows
        """
        if df.empty:
            return df, ExclusionInfo(0, 0, set(), set(), set(), set())
        
        # Use defaults if not provided
        if target_units is None:
            target_units = self.get_default_target_units()
        
        if selected_categories is None:
            selected_categories = self.get_all_categories()
        
        # Track exclusions
        total_rows = len(df)
        unknown_units = set()
        unknown_currencies = set()
        unconvertible_units = set()
        unconvertible_currencies = set()
        
        # Create mask for rows to keep
        keep_mask = pd.Series([True] * len(df), index=df.index)
        
        df_result = df.copy()
        
        # Check if columns exist
        has_unit_col = unit_col in df.columns
        has_currency_col = currency_col in df.columns
        has_value_col = value_col in df.columns
        
        if not has_value_col:
            return df, ExclusionInfo(total_rows, 0, set(), set(), set(), set())
        
        # Process each row
        for idx, row in df_result.iterrows():
            unit = row.get(unit_col) if has_unit_col else None
            currency = row.get(currency_col) if has_currency_col else None
            value = row[value_col]
            
            row_valid = True
            conversion_factor = 1.0  # Track total conversion factor
            
            # Check if unit and currency are actual values (not NA, None, empty string, or 'NA' string)
            has_unit = has_unit_col and not pd.isna(unit) and unit != '' and unit != 'NA'
            has_currency = has_currency_col and not pd.isna(currency) and currency != '' and currency != 'NA'
            
            # Case 1: Physical flows/capacity (unit present, no currency)
            # Case 3: Prices (both unit and currency present)
            if has_unit:
                # Check if unit is known
                if not self.is_unit_known(unit):
                    unknown_units.add(unit)
                    row_valid = False
                else:
                    category = self.get_category(unit)
                    
                    # Check if category is selected
                    if category not in selected_categories:
                        row_valid = False
                    else:
                        # Try to convert
                        target_unit = target_units.get(category)
                        
                        if target_unit and unit != target_unit:
                            if not self.can_convert(unit, target_unit):
                                unconvertible_units.add(f"{unit}→{target_unit}")
                                row_valid = False
                            else:
                                # Get conversion factor
                                factor = self.get_conversion_factor(unit, target_unit)
                                conversion_factor *= factor
                                df_result.at[idx, unit_col] = target_unit
            
            # Case 2: Financial flows (currency present, no unit)
            # Case 3: Prices (both unit and currency present)
            if has_currency and row_valid:  # Only check if row is still valid
                # Check if currency is known
                if not self.is_unit_known(currency):
                    unknown_currencies.add(currency)
                    row_valid = False
                else:
                    category = self.get_category(currency)
                    
                    # Check if category is selected
                    if category not in selected_categories:
                        row_valid = False
                    else:
                        # Try to convert
                        target_currency = target_units.get(category)
                        
                        if target_currency and currency != target_currency:
                            if not self.can_convert(currency, target_currency):
                                unconvertible_currencies.add(f"{currency}→{target_currency}")
                                row_valid = False
                            else:
                                # Get conversion factor
                                factor = self.get_conversion_factor(currency, target_currency)
                                conversion_factor *= factor
                                df_result.at[idx, currency_col] = target_currency
            
            # Apply the total conversion factor to the value
            if row_valid and conversion_factor != 1.0:
                df_result.at[idx, value_col] = value * conversion_factor
            
            keep_mask[idx] = row_valid
        
        # Filter dataframe
        df_filtered = df_result[keep_mask].copy()
        
        excluded_rows = total_rows - len(df_filtered)
        
        exclusion_info = ExclusionInfo(
            total_rows=total_rows,
            excluded_rows=excluded_rows,
            unknown_units=unknown_units,
            unknown_currencies=unknown_currencies,
            unconvertible_units=unconvertible_units,
            unconvertible_currencies=unconvertible_currencies)
        
        return df_filtered, exclusion_info

    # Keep legacy methods for backwards compatibility
    def filter_by_categories(
        self,
        df: pd.DataFrame,
        selected_categories: List[str],
        unit_col: str = 'unit'
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Legacy method: Filter dataframe to only include rows with units in selected categories.
        
        Note: Consider using convert_and_filter() for new code.
        """
        if df.empty or unit_col not in df.columns:
            return df, []
        
        unknown_units = []
        valid_units = []
        
        for unit in df[unit_col].dropna().unique():
            if unit in self.unit_to_category:
                category = self.unit_to_category[unit]
                if category in selected_categories:
                    valid_units.append(unit)
            else:
                unknown_units.append(unit)
        
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
        Legacy method: Convert values in dataframe based on target units.
        
        Note: Consider using convert_and_filter() for new code.
        """
        if df.empty or unit_col not in df.columns or value_col not in df.columns:
            return df
        
        df_converted = df.copy()
        
        for idx, row in df_converted.iterrows():
            current_unit = row[unit_col]
            
            if pd.isna(current_unit):
                continue
            
            category = self.unit_to_category.get(current_unit)
            
            if category and category in target_units:
                target_unit = target_units[category]
                
                if current_unit == target_unit:
                    continue
                
                factor = self.get_conversion_factor(current_unit, target_unit)
                
                if factor is not None:
                    df_converted.at[idx, value_col] = row[value_col] * factor
                    df_converted.at[idx, unit_col] = target_unit
        
        return df_converted