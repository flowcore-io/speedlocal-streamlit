"""
Data transformation utilities for time profile visualization.
Handles aggregation, scaling, and wide-format conversion.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import re


class TimeProfileTransformer:
    """Transform time series data for profile visualization."""
    
    def __init__(self, config: Dict):
        """
        Initialize transformer with configuration.
        
        Args:
            config: Dictionary from profile_config.yaml
        """
        self.config = config
    
    def aggregate_regions(
        self,
        df: pd.DataFrame,
        selected_regions: Optional[List[str]] = None,
        region_col: str = 'regfrom'
    ) -> pd.DataFrame:
        """
        Aggregate data by regions.
        
        Args:
            df: DataFrame with regional data
            selected_regions: List of regions to include (None = all regions)
            region_col: Name of region column
            
        Returns:
            Aggregated DataFrame with regfrom='ALL' if aggregated
        """
        if df.empty:
            return df
        
        df_work = df.copy()
        
        # Filter by selected regions if specified
        if selected_regions and region_col in df_work.columns:
            df_work = df_work[df_work[region_col].isin(selected_regions)]
        
        if df_work.empty:
            return df_work
        
        # Group columns (exclude region columns and value)
        group_cols = [col for col in df_work.columns 
                     if col not in [region_col, 'regto', 'value', 'Value']]
        
        # Determine value column
        value_col = 'value' if 'value' in df_work.columns else 'Value'
        
        # Aggregate
        df_agg = df_work.groupby(group_cols, as_index=False)[value_col].sum()
        
        # Mark as aggregated
        if region_col in df_agg.columns:
            df_agg[region_col] = 'ALL'
        if 'regto' in df_agg.columns:
            df_agg['regto'] = 'ALL'
        
        return df_agg
    
    def transform_to_wide(
        self,
        df: pd.DataFrame,
        timeseries_col: str = 'all_ts',
        label_col: str = 'label',
        value_col: str = 'value',
        index_cols: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Transform to wide format: timeseries as rows, labels as columns.
        
        Args:
            df: Long-format DataFrame
            timeseries_col: Column with time indices
            label_col: Column with series labels (becomes column headers)
            value_col: Column with values
            index_cols: Additional columns to include in index (e.g., ['scen', 'year'])
            
        Returns:
            Wide-format DataFrame
        """
        if df.empty:
            return pd.DataFrame()
        
        # Default index columns
        if index_cols is None:
            index_cols = ['scen', 'year']
        
        # Filter to only columns we need
        pivot_cols = [timeseries_col] + index_cols + [label_col, value_col]
        pivot_cols = [c for c in pivot_cols if c in df.columns]
        
        df_pivot = df[pivot_cols].copy()
        
        # Create pivot table
        try:
            wide_df = df_pivot.pivot_table(
                index=[timeseries_col] + [c for c in index_cols if c in df_pivot.columns],
                columns=label_col,
                values=value_col,
                aggfunc='sum'
            ).reset_index()
            
            return wide_df
        except Exception as e:
            print(f"Error pivoting data: {e}")
            return pd.DataFrame()
    
    def get_plot_categories(
        self,
        wide_df: pd.DataFrame,
        mapping_df: pd.DataFrame,
        timeseries_col: str = 'all_ts'
    ) -> Dict[str, List[str]]:
        """
        Map column names to plot categories based on mapping.
        
        Args:
            wide_df: Wide-format DataFrame
            mapping_df: DataFrame from profile_mapping.csv
            timeseries_col: Name of timeseries column (to exclude from categories)
            
        Returns:
            Dictionary: {plot_group: [column_names]}
        """
        categories = {}
        
        # Get all data columns (exclude timeseries and index columns)
        exclude_cols = [timeseries_col, 'scen', 'year']
        data_cols = [col for col in wide_df.columns if col not in exclude_cols]
        
        # Map each column to its plot group
        for col in data_cols:
            # Find matching row in mapping
            match = mapping_df[mapping_df['label'] == col]
            
            if not match.empty:
                plot_group = match.iloc[0]['plot_group']
                
                if plot_group not in categories:
                    categories[plot_group] = []
                
                categories[plot_group].append(col)
        
        return categories
    
    def get_unit_info(
        self,
        df: pd.DataFrame,
        plot_categories: Dict[str, List[str]],
        label_col: str = 'label'
    ) -> Dict[str, str]:
        """
        Extract unit information for each plot group.
        
        Args:
            df: Original long-format DataFrame (with unit/cur columns)
            plot_categories: Dictionary mapping plot_group to column names
            label_col: Column name containing labels
            
        Returns:
            Dictionary: {plot_group: unit_string}
        """
        unit_info = {}
        
        for plot_group, labels in plot_categories.items():
            units = set()
            currencies = set()
            
            for label in labels:
                # Find rows matching this label
                label_data = df[df[label_col] == label]
                
                if not label_data.empty:
                    # Check unit column
                    if 'unit' in label_data.columns:
                        label_units = label_data['unit'].dropna().unique()
                        units.update([u for u in label_units if str(u).upper() != 'NA'])
                    
                    # Check currency column
                    if 'cur' in label_data.columns:
                        label_curs = label_data['cur'].dropna().unique()
                        currencies.update([c for c in label_curs if str(c).upper() != 'NA'])
            
            # Combine units and currencies
            all_units = list(units) + list(currencies)
            
            if all_units:
                unit_info[plot_group] = ', '.join(sorted(all_units))
            else:
                unit_info[plot_group] = 'units'
        
        return unit_info
