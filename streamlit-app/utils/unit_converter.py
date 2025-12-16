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
        VECTORIZED VERSION
        """
        if df.empty:
            return df, ExclusionInfo(0, 0, set(), set(), set(), set())
        
        # Use defaults if not provided
        if target_units is None:
            target_units = self.get_default_target_units()
        
        if selected_categories is None:
            selected_categories = self.get_all_categories()
        
        total_rows = len(df)
        df_result = df.copy()
        
        # Track exclusions
        unknown_units = set()
        unknown_currencies = set()
        unconvertible_units = set()
        unconvertible_currencies = set()
        
        # Create validity mask (starts as all True)
        valid_mask = pd.Series([True] * len(df_result), index=df_result.index)
        
        # Build conversion lookup tables
        unit_factors, unit_targets, cur_factors, cur_targets = self._build_conversion_maps(
            df_result, target_units, selected_categories, unit_col, currency_col
        )
        
        # Check if columns exist
        has_unit_col = unit_col in df_result.columns
        has_currency_col = currency_col in df_result.columns
        has_value_col = value_col in df_result.columns
        
        if not has_value_col:
            return df, ExclusionInfo(total_rows, 0, set(), set(), set(), set())
        
        # === VECTORIZED UNIT CONVERSION ===
        if has_unit_col:
            # Identify rows with unit values (not NA)
            has_unit = df_result[unit_col].notna() & (df_result[unit_col] != '') & (df_result[unit_col] != 'NA')
            
            # Check which units are known and convertible
            is_known = df_result[unit_col].isin(self.unit_to_category.keys())
            is_in_map = df_result[unit_col].isin(unit_factors.keys())
            
            # Track unknown units
            unknown_unit_mask = has_unit & ~is_known
            if unknown_unit_mask.any():
                unknown_units = set(df_result.loc[unknown_unit_mask, unit_col].unique())
            
            # Track unconvertible units (known but not in conversion map)
            unconvertible_unit_mask = has_unit & is_known & ~is_in_map
            if unconvertible_unit_mask.any():
                unconvertible_units = set(
                    df_result.loc[unconvertible_unit_mask, unit_col].apply(
                        lambda u: f"{u}→{target_units.get(self.get_category(u), 'unknown')}"
                    ).unique()
                )
            
            # Update validity mask
            # Rows are valid if: (no unit) OR (unit is convertible)
            valid_mask = valid_mask & ((~has_unit) | is_in_map)
            
            # Apply conversions vectorized
            conversion_factors = df_result.loc[is_in_map, unit_col].map(unit_factors)
            df_result.loc[is_in_map, value_col] = df_result.loc[is_in_map, value_col] * conversion_factors
            df_result.loc[is_in_map, unit_col] = df_result.loc[is_in_map, unit_col].map(unit_targets)
        
        # === VECTORIZED CURRENCY CONVERSION ===
        if has_currency_col:
            # Identify rows with currency values (not NA)
            has_currency = df_result[currency_col].notna() & (df_result[currency_col] != '') & (df_result[currency_col] != 'NA')
            
            # Check which currencies are known and convertible
            is_known = df_result[currency_col].map(lambda x: self.is_unit_known(x) if pd.notna(x) else False)
            is_in_map = df_result[currency_col].isin(cur_factors.keys())
            
            # Track unknown currencies
            unknown_cur_mask = has_currency & ~is_known
            if unknown_cur_mask.any():
                unknown_currencies = set(df_result.loc[unknown_cur_mask, currency_col].unique())
            
            # Track unconvertible currencies
            unconvertible_cur_mask = has_currency & is_known & ~is_in_map
            if unconvertible_cur_mask.any():
                unconvertible_currencies = set(
                    df_result.loc[unconvertible_cur_mask, currency_col].apply(
                        lambda c: f"{c}→{target_units.get(self.get_category(c), 'unknown')}"
                    ).unique()
                )
            
            # Update validity mask (only if row is still valid from unit check)
            valid_mask &= ~has_currency | is_in_map
            
            # Apply conversions vectorized
            conversion_factors = df_result.loc[is_in_map, unit_col].map(unit_factors)
            df_result.loc[is_in_map, value_col] = df_result.loc[is_in_map, value_col] * conversion_factors
            df_result.loc[is_in_map, unit_col] = df_result.loc[is_in_map, unit_col].map(unit_targets)
        
        # Filter to valid rows only
        df_filtered = df_result[valid_mask].copy()
        
        excluded_rows = total_rows - len(df_filtered)
        
        exclusion_info = ExclusionInfo(
            total_rows=total_rows,
            excluded_rows=excluded_rows,
            unknown_units=unknown_units,
            unknown_currencies=unknown_currencies,
            unconvertible_units=unconvertible_units,
            unconvertible_currencies=unconvertible_currencies
        )
        
        return df_filtered, exclusion_info

    def _build_conversion_maps(
        self,
        df: pd.DataFrame,
        target_units: Dict[str, str],
        selected_categories: List[str],
        unit_col: str = 'unit',
        currency_col: str = 'cur'
    ) -> Tuple[Dict, Dict, Dict, Dict]:
        """
        Build lookup dictionaries for vectorized conversion.
        
        Returns:
            Tuple of (unit_factors, unit_targets, cur_factors, cur_targets)
            Each is a dict mapping from_value -> factor or target
        """
        unit_factors = {}
        unit_targets = {}
        cur_factors = {}
        cur_targets = {}
        
        # Get unique values from dataframe
        if unit_col in df.columns:
            unique_units = df[unit_col].dropna().unique()
            
            for unit in unique_units:
                if not self.is_unit_known(unit):
                    continue  # Will be filtered out
                
                category = self.get_category(unit)
                if category not in selected_categories:
                    continue  # Will be filtered out
                
                target = target_units.get(category)
                if not target:
                    continue
                
                if unit == target:
                    unit_factors[unit] = 1.0
                    unit_targets[unit] = target
                else:
                    factor = self.get_conversion_factor(unit, target)
                    if factor is not None:
                        unit_factors[unit] = factor
                        unit_targets[unit] = target
        
        # Same for currency column
        if currency_col in df.columns:
            unique_currencies = df[currency_col].dropna().unique()
            
            for cur in unique_currencies:
                if not self.is_unit_known(cur):
                    continue
                
                category = self.get_category(cur)
                if category not in selected_categories:
                    continue
                
                target = target_units.get(category)
                if not target:
                    continue
                
                if cur == target:
                    cur_factors[cur] = 1.0
                    cur_targets[cur] = target
                else:
                    factor = self.get_conversion_factor(cur, target)
                    if factor is not None:
                        cur_factors[cur] = factor
                        cur_targets[cur] = target
        
        return unit_factors, unit_targets, cur_factors, cur_targets


## Additional unit-realted helper functions
def extract_unit_label(df: pd.DataFrame, unit_col: str = 'unit', currency_col: str = 'cur') -> str:
    """
    Extract unit label from dataframe for axis labels.
    Checks both unit and currency columns.
    
    Args:
        df: DataFrame with unit/cur columns
        unit_col: Name of unit column (default: 'unit')
        currency_col: Name of currency column (default: 'cur')
        
    Returns:
        String representing units (e.g., 't', 'GJ', 'MKr25')
        Returns 'value' if no units found
    """
    if df.empty:
        return 'value'
    
    units = []
    
    # Check unit column
    if unit_col in df.columns:
        df_units = df[unit_col].dropna().unique()
        units.extend([u for u in df_units if str(u).upper() != 'NA'])
    
    # Check currency column
    if currency_col in df.columns:
        df_curs = df[currency_col].dropna().unique()
        units.extend([c for c in df_curs if str(c).upper() != 'NA'])
    
    if not units:
        return 'value'
    elif len(units) == 1:
        return str(units[0])
    else:
        return ', '.join(sorted(set(str(u) for u in units)))