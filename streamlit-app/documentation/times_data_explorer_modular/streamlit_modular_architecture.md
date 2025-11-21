# Streamlit App Modularization Plan for TIMES Data Explorer

## Executive Summary

This document provides a comprehensive plan to refactor your TIMES Data Explorer Streamlit app into a more modular, maintainable architecture aligned with your vision of having separate modules for Energy/Emissions, Land Use, Economics, and DAYNITE-level reporting.

---

## Current Architecture Analysis

### Strengths
1. **Good separation of concerns** with utility modules:
   - `_query_with_csv`: Data loading
   - `_plotting`: Visualization
   - `_query_dynamic`: Filtering logic
   - `_streamlit_ui`: UI components

2. **Session state management** for caching data
3. **Dynamic filtering system** using `GenericFilter`
4. **Consistent plotting patterns** with `TimesReportPlotter`

### Areas for Improvement
1. **Monolithic main function**: All visualization logic in one file
2. **Hard-coded visualization patterns**: Not easily extensible
3. **Tight coupling**: Filtering and plotting logic intertwined
4. **Limited reusability**: Tab-specific code can't be easily reused

---

## Proposed Modular Architecture

```
times_app/
├── main.py                          # Main entry point
├── config/
│   ├── __init__.py
│   ├── app_config.py               # Global configuration
│   └── module_registry.py          # Module registration system
├── core/
│   ├── __init__.py
│   ├── data_loader.py              # Centralized data loading
│   ├── filter_manager.py           # Centralized filtering
│   └── session_manager.py          # Session state management
├── modules/
│   ├── __init__.py
│   ├── base_module.py              # Abstract base class for modules
│   ├── key_insights/
│   │   ├── __init__.py
│   │   ├── module.py               # Key Insights module
│   │   ├── metrics.py              # KPI calculations
│   │   ├── comparisons.py          # Cross-scenario/regional comparisons
│   │   └── visualizations.py      # Dashboard components
│   ├── energy_emissions/
│   │   ├── __init__.py
│   │   ├── module.py               # Energy/Emissions module
│   │   ├── queries.py              # SQL queries
│   │   └── visualizations.py      # Module-specific plots
│   ├── land_use/
│   │   ├── __init__.py
│   │   ├── module.py
│   │   ├── queries.py
│   │   ├── visualizations.py
│   │   └── map_component.py       # Map visualization
│   ├── economics/
│   │   ├── __init__.py
│   │   ├── module.py
│   │   ├── queries.py
│   │   └── visualizations.py
│   └── daynite/
│       ├── __init__.py
│       ├── module.py
│       ├── queries.py
│       └── visualizations.py
├── components/
│   ├── __init__.py
│   ├── sidebar.py                  # Reusable sidebar components
│   ├── filters.py                  # Reusable filter components
│   └── plots.py                    # Reusable plot components
└── utils/
    ├── __init__.py
    ├── db_utils.py                 # Database utilities
    └── helpers.py                  # Helper functions
```

---

## Implementation Details

### 1. Module Base Class

Create an abstract base class that all modules inherit from:

```python
# modules/base_module.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import streamlit as st
import pandas as pd

class BaseModule(ABC):
    """Base class for all Streamlit app modules."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self._data_cache = {}
    
    @abstractmethod
    def get_required_tables(self) -> list[str]:
        """Return list of required database tables."""
        pass
    
    @abstractmethod
    def render(self, data: Dict[str, pd.DataFrame], filters: Dict[str, Any]) -> None:
        """Main render method for the module."""
        pass
    
    @abstractmethod
    def get_filter_config(self) -> Dict[str, Any]:
        """Return configuration for filters specific to this module."""
        pass
    
    def validate_data(self, data: Dict[str, pd.DataFrame]) -> bool:
        """Validate that required data is available."""
        required = self.get_required_tables()
        return all(table in data and not data[table].empty for table in required)
    
    def show_error(self, message: str):
        """Display error message."""
        st.error(f"[{self.name}] {message}")
    
    def show_warning(self, message: str):
        """Display warning message."""
        st.warning(f"[{self.name}] {message}")
    
    def show_info(self, message: str):
        """Display info message."""
        st.info(f"[{self.name}] {message}")
```

### 2. Energy/Emissions Module Example

```python
# modules/energy_emissions/module.py
from ..base_module import BaseModule
from .visualizations import EnergyVisualizer
from .queries import EnergyQueries
import streamlit as st
import pandas as pd
from typing import Dict, Any

class EnergyEmissionsModule(BaseModule):
    """Module for Energy and Emissions visualization."""
    
    EXCLUDED_SECTORS = ['AFO', 'DMZ', 'SYS', 'DHT', 'ELT', 'TRD', 'UPS', 'NA', 'FTS']
    
    def __init__(self):
        super().__init__(
            name="Energy & Emissions",
            description="Annual reporting with filtering options"
        )
        self.visualizer = EnergyVisualizer()
        self.queries = EnergyQueries()
    
    def get_required_tables(self) -> list[str]:
        return ["energy", "emissions"]
    
    def get_filter_config(self) -> Dict[str, Any]:
        return {
            "default_columns": ["scen", "sector", "year"],
            "exclude_sectors": self.EXCLUDED_SECTORS,
            "filterable_columns": [
                "scen", "sector", "subsector", "service",
                "techgroup", "comgroup", "year"
            ]
        }
    
    def render(self, data: Dict[str, pd.DataFrame], filters: Dict[str, Any]) -> None:
        """Render the Energy/Emissions module."""
        
        if not self.validate_data(data):
            self.show_error("Required data tables not available.")
            return
        
        # Create sub-tabs for Energy and Emissions
        energy_tab, emissions_tab = st.tabs(["Energy", "Emissions"])
        
        with energy_tab:
            self._render_energy_section(data["energy"], filters)
        
        with emissions_tab:
            self._render_emissions_section(data["emissions"], filters)
    
    def _render_energy_section(self, df_energy: pd.DataFrame, filters: Dict[str, Any]):
        """Render energy visualization section."""
        st.subheader("Energy Visualization")
        
        # Apply filters
        df_filtered = self._apply_filters(df_energy, filters)
        
        if df_filtered.empty:
            self.show_warning("No energy data available after applying filters.")
            return
        
        # Get available sectors
        sectors = self._get_available_sectors(df_filtered)
        
        # Aggregate plot
        self._render_aggregate_energy_plot(df_filtered, sectors)
        
        # Per-sector plots
        self._render_sector_energy_plots(df_filtered, sectors)
    
    def _render_emissions_section(self, df_emissions: pd.DataFrame, filters: Dict[str, Any]):
        """Render emissions visualization section."""
        st.subheader("Emissions Visualization")
        
        # Apply filters
        df_filtered = self._apply_filters(df_emissions, filters)
        
        if df_filtered.empty:
            self.show_warning("No emissions data available after applying filters.")
            return
        
        # Get available sectors
        sectors = self._get_available_sectors(df_filtered)
        
        # Aggregate plot
        self._render_aggregate_emissions_plot(df_filtered, sectors)
        
        # Per-sector plots
        self._render_sector_emissions_plots(df_filtered, sectors)
    
    def _apply_filters(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """Apply filters to dataframe."""
        df_filtered = df.copy()
        
        for col, values in filters.items():
            if col in df_filtered.columns and values:
                df_filtered = df_filtered[df_filtered[col].isin(values)]
        
        return df_filtered
    
    def _get_available_sectors(self, df: pd.DataFrame) -> list[str]:
        """Get list of available sectors, excluding predefined ones."""
        if 'sector' not in df.columns:
            return []
        
        sectors = sorted(df['sector'].unique())
        return [s for s in sectors if s not in self.EXCLUDED_SECTORS]
    
    def _render_aggregate_energy_plot(self, df: pd.DataFrame, sectors: list[str]):
        """Render aggregate energy plot."""
        st.markdown("### Aggregate Energy (All Sectors)")
        
        selected_sectors = st.multiselect(
            "Select sectors for aggregate plot",
            options=sectors,
            default=sectors,
            key=f"{self.name}_energy_agg_sectors"
        )
        
        if not selected_sectors:
            return
        
        df_agg = df[
            (df['sector'].isin(selected_sectors)) &
            (df['topic'] == 'energy') &
            (df['attr'] == 'f_in')
        ]
        
        if not df_agg.empty:
            fig = self.visualizer.create_stacked_bar(
                df_agg,
                x_col="year",
                y_col="value",
                group_col="comgroup",
                scenario_col="scen",
                title="Aggregate Energy Input"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_sector_energy_plots(self, df: pd.DataFrame, sectors: list[str]):
        """Render per-sector energy plots."""
        st.markdown("### Energy by Sector")
        
        for sector in sectors:
            with st.expander(f"**{sector}**", expanded=False):
                df_sector = df[
                    (df['sector'] == sector) &
                    (df['topic'] == 'energy') &
                    (df['attr'] == 'f_in')
                ]
                
                if not df_sector.empty:
                    fig = self.visualizer.create_stacked_bar(
                        df_sector,
                        x_col="year",
                        y_col="value",
                        group_col="comgroup",
                        scenario_col="scen",
                        title=f"Energy Input - {sector}"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"No data available for {sector}")
    
    def _render_aggregate_emissions_plot(self, df: pd.DataFrame, sectors: list[str]):
        """Render aggregate emissions plot."""
        st.markdown("### Aggregate Emissions (All Sectors)")
        
        selected_sectors = st.multiselect(
            "Select sectors for aggregate plot",
            options=sectors,
            default=sectors,
            key=f"{self.name}_emissions_agg_sectors"
        )
        
        if not selected_sectors:
            return
        
        df_agg = df[
            (df['sector'].isin(selected_sectors)) &
            (df['topic'] == 'emission')
        ].groupby(['year', 'sector', 'scen'], as_index=False)['value'].sum()
        
        if not df_agg.empty:
            fig = self.visualizer.create_line_plot(
                df_agg,
                x_col="year",
                y_col="value",
                line_group_col="sector",
                scenario_col="scen",
                title="Aggregate Emissions by Sector"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_sector_emissions_plots(self, df: pd.DataFrame, sectors: list[str]):
        """Render per-sector emissions plots."""
        st.markdown("### Emissions by Sector")
        
        for sector in sectors:
            with st.expander(f"**{sector}**", expanded=False):
                df_sector = df[
                    (df['sector'] == sector) &
                    (df['topic'] == 'emission')
                ].groupby(['year', 'comgroup', 'scen'], as_index=False)['value'].sum()
                
                if not df_sector.empty:
                    fig = self.visualizer.create_line_plot(
                        df_sector,
                        x_col="year",
                        y_col="value",
                        line_group_col="comgroup",
                        scenario_col="scen",
                        title=f"Emissions - {sector}"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"No emission data for {sector}")
```

### 3. Land Use Module Example

```python
# modules/land_use/module.py
from ..base_module import BaseModule
from .visualizations import LandUseVisualizer
from .map_component import LandUseMap
import streamlit as st
import pandas as pd
from typing import Dict, Any

class LandUseModule(BaseModule):
    """Module for Land Use visualization with map integration."""
    
    def __init__(self):
        super().__init__(
            name="Land Use",
            description="Spatial visualization of land use in KHA units"
        )
        self.visualizer = LandUseVisualizer()
        self.map_component = LandUseMap()
    
    def get_required_tables(self) -> list[str]:
        return ["land_use"]  # Assuming you have or will have this table
    
    def get_filter_config(self) -> Dict[str, Any]:
        return {
            "default_columns": ["scen", "region", "year"],
            "filterable_columns": [
                "scen", "region", "sector", "subsector",
                "comgroup", "techgroup", "year"
            ]
        }
    
    def render(self, data: Dict[str, pd.DataFrame], filters: Dict[str, Any]) -> None:
        """Render the Land Use module."""
        
        if not self.validate_data(data):
            self.show_warning("Land use data not yet available in database.")
            self.show_info("This module will be available once land use data is added.")
            return
        
        st.subheader("Land Use Visualization")
        
        # Create two columns: map and charts
        col_map, col_charts = st.columns([1.5, 1])
        
        with col_map:
            self._render_map_section(data["land_use"], filters)
        
        with col_charts:
            self._render_charts_section(data["land_use"], filters)
    
    def _render_map_section(self, df: pd.DataFrame, filters: Dict[str, Any]):
        """Render map visualization."""
        st.markdown("#### Regional Map")
        
        df_filtered = self._apply_filters(df, filters)
        
        if df_filtered.empty:
            self.show_warning("No land use data after filtering.")
            return
        
        # Create interactive map
        map_fig = self.map_component.create_map(df_filtered)
        st.plotly_chart(map_fig, use_container_width=True)
    
    def _render_charts_section(self, df: pd.DataFrame, filters: Dict[str, Any]):
        """Render charts for land use."""
        st.markdown("#### Land Use Statistics")
        
        df_filtered = self._apply_filters(df, filters)
        
        if df_filtered.empty:
            return
        
        # Time series chart
        fig_timeseries = self.visualizer.create_timeseries(df_filtered)
        st.plotly_chart(fig_timeseries, use_container_width=True)
        
        # Breakdown by category
        fig_breakdown = self.visualizer.create_breakdown(df_filtered)
        st.plotly_chart(fig_breakdown, use_container_width=True)
    
    def _apply_filters(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """Apply filters to dataframe."""
        df_filtered = df.copy()
        
        for col, values in filters.items():
            if col in df_filtered.columns and values:
                df_filtered = df_filtered[df_filtered[col].isin(values)]
        
        return df_filtered
```

### 4. Key Insights Module

```python
# modules/key_insights/module.py
from ..base_module import BaseModule
from .metrics import MetricsCalculator
from .comparisons import ComparisonEngine
from .visualizations import InsightsVisualizer
import streamlit as st
import pandas as pd
from typing import Dict, Any, List

class KeyInsightsModule(BaseModule):
    """
    Module for Key Modelling Insights - Executive dashboard for stakeholders.
    
    This module provides:
    - High-level KPIs and metrics
    - Scenario comparisons
    - Regional comparisons (e.g., Trøndelag, Vara, Bornholm)
    - Executive summaries
    - Key findings and recommendations
    """
    
    def __init__(self):
        super().__init__(
            name="Key Insights",
            description="Executive dashboard with key findings and comparisons"
        )
        self.metrics_calc = MetricsCalculator()
        self.comparison_engine = ComparisonEngine()
        self.visualizer = InsightsVisualizer()
    
    def get_required_tables(self) -> list[str]:
        return ["energy", "emissions", "capacity", "costs"]
    
    def get_filter_config(self) -> Dict[str, Any]:
        return {
            "default_columns": ["scen"],
            "filterable_columns": ["scen", "year", "region"],
            "comparison_mode": True  # Enable comparison features
        }
    
    def render(self, data: Dict[str, pd.DataFrame], filters: Dict[str, Any]) -> None:
        """Render the Key Insights dashboard."""
        
        if not self.validate_data(data):
            self.show_warning("Required data for insights not fully available.")
            # Continue with partial rendering
        
        # Create main sections
        self._render_executive_summary(data, filters)
        
        st.markdown("---")
        
        # Create columns for layout
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_kpi_dashboard(data, filters)
        
        with col2:
            self._render_scenario_comparison(data, filters)
        
        st.markdown("---")
        
        # Regional comparison section (if applicable)
        if self._has_regional_data(data):
            self._render_regional_comparison(data, filters)
            st.markdown("---")
        
        # Detailed findings
        self._render_key_findings(data, filters)
    
    def _render_executive_summary(self, data: Dict[str, pd.DataFrame], filters: Dict[str, Any]):
        """Render executive summary with key takeaways."""
        st.header("📊 Executive Summary")
        
        # Generate summary metrics
        summary = self.metrics_calc.calculate_summary_metrics(data, filters)
        
        # Display in metric cards
        cols = st.columns(4)
        
        metrics_config = [
            {
                "label": "Total Energy Demand",
                "key": "total_energy",
                "unit": "PJ",
                "icon": "⚡"
            },
            {
                "label": "CO₂ Emissions",
                "key": "total_emissions",
                "unit": "Mt CO₂",
                "icon": "🌍"
            },
            {
                "label": "Renewable Share",
                "key": "renewable_share",
                "unit": "%",
                "icon": "🌱"
            },
            {
                "label": "System Cost",
                "key": "total_cost",
                "unit": "M€",
                "icon": "💰"
            }
        ]
        
        for col, metric_cfg in zip(cols, metrics_config):
            with col:
                value = summary.get(metric_cfg["key"], 0)
                delta = summary.get(f"{metric_cfg['key']}_change", None)
                
                st.metric(
                    label=f"{metric_cfg['icon']} {metric_cfg['label']}",
                    value=f"{value:,.1f} {metric_cfg['unit']}",
                    delta=f"{delta:+.1f}%" if delta is not None else None,
                    delta_color="inverse" if metric_cfg['key'] == 'total_emissions' else "normal"
                )
        
        # Key highlights
        st.markdown("### 🎯 Key Highlights")
        highlights = self._generate_highlights(data, filters, summary)
        for highlight in highlights:
            st.info(highlight)
    
    def _render_kpi_dashboard(self, data: Dict[str, pd.DataFrame], filters: Dict[str, Any]):
        """Render KPI dashboard with key performance indicators."""
        st.subheader("📈 Key Performance Indicators")
        
        # Calculate KPIs
        kpis = self.metrics_calc.calculate_kpis(data, filters)
        
        # Energy intensity
        st.markdown("**Energy Intensity**")
        fig_intensity = self.visualizer.create_kpi_gauge(
            value=kpis.get('energy_intensity', 0),
            title="Energy per GDP",
            unit="MJ/€",
            range_max=kpis.get('energy_intensity_max', 100)
        )
        st.plotly_chart(fig_intensity, use_container_width=True)
        
        # Emissions intensity
        st.markdown("**Emissions Intensity**")
        fig_emissions_intensity = self.visualizer.create_kpi_gauge(
            value=kpis.get('emissions_intensity', 0),
            title="CO₂ per Energy",
            unit="kg CO₂/GJ",
            range_max=kpis.get('emissions_intensity_max', 100)
        )
        st.plotly_chart(fig_emissions_intensity, use_container_width=True)
        
        # Cost effectiveness
        st.markdown("**Cost Effectiveness**")
        fig_cost = self.visualizer.create_kpi_gauge(
            value=kpis.get('cost_per_emission_reduction', 0),
            title="€ per ton CO₂ reduced",
            unit="€/t CO₂",
            range_max=kpis.get('cost_per_emission_max', 200)
        )
        st.plotly_chart(fig_cost, use_container_width=True)
    
    def _render_scenario_comparison(self, data: Dict[str, pd.DataFrame], filters: Dict[str, Any]):
        """Render scenario comparison section."""
        st.subheader("🔀 Scenario Comparison")
        
        scenarios = filters.get('scen', [])
        
        if len(scenarios) < 2:
            st.info("Select at least 2 scenarios in filters to enable comparison.")
            return
        
        # Comparison selector
        comparison_type = st.selectbox(
            "Comparison Type",
            options=[
                "Energy Mix",
                "Emissions Trajectory",
                "Technology Capacity",
                "Cost Breakdown"
            ],
            key="insights_comparison_type"
        )
        
        # Generate comparison based on type
        if comparison_type == "Energy Mix":
            fig = self.comparison_engine.compare_energy_mix(data, scenarios, filters)
            st.plotly_chart(fig, use_container_width=True)
            
            # Add insights
            insights = self.comparison_engine.analyze_energy_mix_differences(data, scenarios, filters)
            with st.expander("💡 Analysis"):
                for insight in insights:
                    st.markdown(f"- {insight}")
        
        elif comparison_type == "Emissions Trajectory":
            fig = self.comparison_engine.compare_emissions_trajectory(data, scenarios, filters)
            st.plotly_chart(fig, use_container_width=True)
            
            # Calculate emissions reduction
            reductions = self.comparison_engine.calculate_emissions_reductions(data, scenarios, filters)
            
            st.markdown("**Emissions Reduction vs Baseline**")
            for scenario, reduction in reductions.items():
                if scenario != scenarios[0]:  # Skip baseline
                    st.metric(
                        label=scenario,
                        value=f"{reduction['absolute']:.1f} Mt CO₂",
                        delta=f"{reduction['percentage']:.1f}%",
                        delta_color="inverse"
                    )
        
        elif comparison_type == "Technology Capacity":
            fig = self.comparison_engine.compare_technology_capacity(data, scenarios, filters)
            st.plotly_chart(fig, use_container_width=True)
            
        elif comparison_type == "Cost Breakdown":
            fig = self.comparison_engine.compare_costs(data, scenarios, filters)
            st.plotly_chart(fig, use_container_width=True)
            
            # Cost difference table
            cost_diff = self.comparison_engine.calculate_cost_differences(data, scenarios, filters)
            st.dataframe(cost_diff, use_container_width=True)
    
    def _render_regional_comparison(self, data: Dict[str, pd.DataFrame], filters: Dict[str, Any]):
        """Render regional comparison (e.g., Trøndelag, Vara, Bornholm)."""
        st.subheader("🗺️ Regional Comparison")
        
        st.markdown("""
        Compare results across different regions in the SpeedLocal project:
        - **Trøndelag** (Norway)
        - **Vara** (Sweden)  
        - **Bornholm** (Denmark)
        """)
        
        # Get available regions from data
        regions = self._get_available_regions(data)
        
        if len(regions) < 2:
            st.info("Regional comparison requires data from multiple regions.")
            return
        
        # Region selector
        selected_regions = st.multiselect(
            "Select regions to compare",
            options=regions,
            default=regions[:3] if len(regions) >= 3 else regions,
            key="insights_region_selector"
        )
        
        if len(selected_regions) < 2:
            st.warning("Please select at least 2 regions.")
            return
        
        # Comparison metric selector
        metric = st.selectbox(
            "Comparison Metric",
            options=[
                "Energy Demand per Capita",
                "Renewable Energy Share",
                "Emissions per Capita",
                "Energy System Cost"
            ],
            key="insights_regional_metric"
        )
        
        # Create regional comparison
        fig = self.comparison_engine.compare_regions(
            data, 
            selected_regions, 
            metric, 
            filters
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Regional insights table
        regional_summary = self.comparison_engine.create_regional_summary(
            data,
            selected_regions,
            filters
        )
        
        st.markdown("**Regional Summary Statistics**")
        st.dataframe(regional_summary, use_container_width=True)
    
    def _render_key_findings(self, data: Dict[str, pd.DataFrame], filters: Dict[str, Any]):
        """Render key findings and recommendations."""
        st.subheader("🔍 Key Findings & Recommendations")
        
        # Generate findings based on analysis
        findings = self._analyze_and_generate_findings(data, filters)
        
        # Create tabs for different finding categories
        finding_tabs = st.tabs([
            "🌍 Decarbonization",
            "⚡ Energy System", 
            "💰 Economics",
            "📊 Technology"
        ])
        
        with finding_tabs[0]:
            st.markdown("### Decarbonization Pathways")
            for finding in findings.get('decarbonization', []):
                self._render_finding_card(finding)
        
        with finding_tabs[1]:
            st.markdown("### Energy System Insights")
            for finding in findings.get('energy_system', []):
                self._render_finding_card(finding)
        
        with finding_tabs[2]:
            st.markdown("### Economic Analysis")
            for finding in findings.get('economics', []):
                self._render_finding_card(finding)
        
        with finding_tabs[3]:
            st.markdown("### Technology Deployment")
            for finding in findings.get('technology', []):
                self._render_finding_card(finding)
    
    def _render_finding_card(self, finding: Dict[str, Any]):
        """Render a single finding card."""
        with st.container():
            col1, col2 = st.columns([0.1, 0.9])
            
            with col1:
                # Icon based on finding type
                icon = finding.get('icon', '📌')
                st.markdown(f"## {icon}")
            
            with col2:
                st.markdown(f"**{finding.get('title', 'Finding')}**")
                st.markdown(finding.get('description', ''))
                
                if 'data' in finding:
                    # Show supporting data/chart
                    st.plotly_chart(finding['data'], use_container_width=True)
                
                if 'recommendation' in finding:
                    st.info(f"💡 **Recommendation:** {finding['recommendation']}")
            
            st.markdown("---")
    
    def _generate_highlights(
        self, 
        data: Dict[str, pd.DataFrame], 
        filters: Dict[str, Any],
        summary: Dict[str, Any]
    ) -> List[str]:
        """Generate key highlights for executive summary."""
        highlights = []
        
        # Renewable energy highlight
        renewable_share = summary.get('renewable_share', 0)
        if renewable_share > 50:
            highlights.append(
                f"✅ **High renewable integration:** {renewable_share:.0f}% of energy from renewable sources"
            )
        elif renewable_share > 30:
            highlights.append(
                f"📈 **Growing renewables:** {renewable_share:.0f}% renewable energy share achieved"
            )
        
        # Emissions reduction highlight
        emissions_change = summary.get('total_emissions_change', 0)
        if emissions_change < -30:
            highlights.append(
                f"🌍 **Significant decarbonization:** {abs(emissions_change):.0f}% reduction in CO₂ emissions"
            )
        elif emissions_change < -10:
            highlights.append(
                f"🌱 **Emissions reduction:** {abs(emissions_change):.0f}% decrease in CO₂ emissions"
            )
        
        # Cost efficiency highlight
        cost_effectiveness = summary.get('cost_per_emission_reduction', 0)
        if 0 < cost_effectiveness < 100:
            highlights.append(
                f"💰 **Cost-effective decarbonization:** €{cost_effectiveness:.0f} per ton CO₂ reduced"
            )
        
        # Energy efficiency highlight
        energy_change = summary.get('total_energy_change', 0)
        if energy_change < -10:
            highlights.append(
                f"⚡ **Improved energy efficiency:** {abs(energy_change):.0f}% reduction in energy demand"
            )
        
        return highlights
    
    def _analyze_and_generate_findings(
        self,
        data: Dict[str, pd.DataFrame],
        filters: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Analyze data and generate findings."""
        findings = {
            'decarbonization': [],
            'energy_system': [],
            'economics': [],
            'technology': []
        }
        
        # Decarbonization findings
        emissions_analysis = self.metrics_calc.analyze_emissions_trajectory(data, filters)
        if emissions_analysis.get('net_zero_year'):
            findings['decarbonization'].append({
                'icon': '🎯',
                'title': 'Net-Zero Trajectory',
                'description': f"Modelling shows potential to reach net-zero emissions by {emissions_analysis['net_zero_year']}.",
                'recommendation': "Accelerate deployment of key technologies to meet this target."
            })
        
        # Energy system findings
        energy_mix = self.metrics_calc.analyze_energy_mix(data, filters)
        if energy_mix.get('diversification_index', 0) > 0.7:
            findings['energy_system'].append({
                'icon': '⚡',
                'title': 'Diverse Energy Portfolio',
                'description': "Energy system shows high diversification across multiple sources.",
                'recommendation': "Maintain diversity to ensure energy security and resilience."
            })
        
        # Economics findings
        cost_analysis = self.metrics_calc.analyze_costs(data, filters)
        if cost_analysis.get('investment_required'):
            findings['economics'].append({
                'icon': '💰',
                'title': 'Investment Requirements',
                'description': f"Total investment of €{cost_analysis['investment_required']:.0f}M required for transition.",
                'recommendation': "Develop financing mechanisms to mobilize necessary capital."
            })
        
        # Technology findings
        tech_analysis = self.metrics_calc.analyze_technology_deployment(data, filters)
        key_tech = tech_analysis.get('key_technologies', [])
        if key_tech:
            findings['technology'].append({
                'icon': '🔧',
                'title': 'Critical Technologies',
                'description': f"Key technologies for transition: {', '.join(key_tech[:3])}",
                'recommendation': "Prioritize R&D and deployment support for these technologies."
            })
        
        return findings
    
    def _has_regional_data(self, data: Dict[str, pd.DataFrame]) -> bool:
        """Check if regional data is available."""
        for df in data.values():
            if 'region' in df.columns and df['region'].nunique() > 1:
                return True
        return False
    
    def _get_available_regions(self, data: Dict[str, pd.DataFrame]) -> List[str]:
        """Get list of available regions."""
        regions = set()
        for df in data.values():
            if 'region' in df.columns:
                regions.update(df['region'].unique())
        return sorted(list(regions))


# modules/key_insights/metrics.py
import pandas as pd
import numpy as np
from typing import Dict, Any, List

class MetricsCalculator:
    """Calculate key metrics and KPIs from TIMES data."""
    
    def calculate_summary_metrics(
        self,
        data: Dict[str, pd.DataFrame],
        filters: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate high-level summary metrics."""
        metrics = {}
        
        # Total energy demand
        if 'energy' in data:
            df_energy = self._apply_filters(data['energy'], filters)
            metrics['total_energy'] = df_energy['value'].sum() / 1000  # Convert to PJ
            
            # Calculate change vs baseline if multiple scenarios
            scenarios = filters.get('scen', [])
            if len(scenarios) >= 2:
                baseline = df_energy[df_energy['scen'] == scenarios[0]]['value'].sum()
                current = df_energy[df_energy['scen'] == scenarios[-1]]['value'].sum()
                metrics['total_energy_change'] = ((current - baseline) / baseline) * 100
        
        # Total emissions
        if 'emissions' in data:
            df_emissions = self._apply_filters(data['emissions'], filters)
            metrics['total_emissions'] = df_emissions['value'].sum()
            
            scenarios = filters.get('scen', [])
            if len(scenarios) >= 2:
                baseline = df_emissions[df_emissions['scen'] == scenarios[0]]['value'].sum()
                current = df_emissions[df_emissions['scen'] == scenarios[-1]]['value'].sum()
                metrics['total_emissions_change'] = ((current - baseline) / baseline) * 100
        
        # Renewable share
        if 'energy' in data:
            df_energy = self._apply_filters(data['energy'], filters)
            renewable_commodities = ['WIND', 'SOLAR', 'HYDRO', 'BIOMASS', 'GEOTHERMAL']
            
            total = df_energy['value'].sum()
            renewable = df_energy[
                df_energy['comgroup'].str.contains('|'.join(renewable_commodities), case=False, na=False)
            ]['value'].sum()
            
            metrics['renewable_share'] = (renewable / total * 100) if total > 0 else 0
        
        # System cost
        if 'costs' in data:
            df_costs = self._apply_filters(data['costs'], filters)
            metrics['total_cost'] = df_costs['value'].sum()
        
        # Cost per emission reduction
        if 'total_cost' in metrics and 'total_emissions_change' in metrics:
            if metrics['total_emissions_change'] < 0:
                emissions_reduced = abs(metrics.get('total_emissions', 0) * metrics['total_emissions_change'] / 100)
                if emissions_reduced > 0:
                    metrics['cost_per_emission_reduction'] = metrics['total_cost'] / emissions_reduced
        
        return metrics
    
    def calculate_kpis(
        self,
        data: Dict[str, pd.DataFrame],
        filters: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate detailed KPIs."""
        kpis = {}
        
        # Energy intensity (requires GDP data or can use proxy)
        if 'energy' in data:
            df_energy = self._apply_filters(data['energy'], filters)
            total_energy = df_energy['value'].sum()
            # Placeholder - replace with actual GDP data
            assumed_gdp = 10000  # Million euros
            kpis['energy_intensity'] = total_energy / assumed_gdp
            kpis['energy_intensity_max'] = 100
        
        # Emissions intensity
        if 'energy' in data and 'emissions' in data:
            df_energy = self._apply_filters(data['energy'], filters)
            df_emissions = self._apply_filters(data['emissions'], filters)
            
            total_energy = df_energy['value'].sum()
            total_emissions = df_emissions['value'].sum()
            
            if total_energy > 0:
                kpis['emissions_intensity'] = (total_emissions * 1000) / total_energy  # kg CO2/GJ
                kpis['emissions_intensity_max'] = 100
        
        # Cost effectiveness
        summary = self.calculate_summary_metrics(data, filters)
        kpis['cost_per_emission_reduction'] = summary.get('cost_per_emission_reduction', 0)
        kpis['cost_per_emission_max'] = 200
        
        return kpis
    
    def analyze_emissions_trajectory(
        self,
        data: Dict[str, pd.DataFrame],
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze emissions trajectory and estimate net-zero year."""
        analysis = {}
        
        if 'emissions' not in data:
            return analysis
        
        df = self._apply_filters(data['emissions'], filters)
        
        # Group by year and calculate total
        yearly = df.groupby('year')['value'].sum().sort_index()
        
        # Check if approaching zero
        if len(yearly) >= 2:
            trend = np.polyfit(yearly.index, yearly.values, 1)
            
            # Extrapolate to find net-zero year
            if trend[0] < 0:  # Negative slope (decreasing)
                net_zero_year = -trend[1] / trend[0]
                if 2020 <= net_zero_year <= 2100:
                    analysis['net_zero_year'] = int(net_zero_year)
        
        return analysis
    
    def analyze_energy_mix(
        self,
        data: Dict[str, pd.DataFrame],
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze energy mix diversification."""
        analysis = {}
        
        if 'energy' not in data:
            return analysis
        
        df = self._apply_filters(data['energy'], filters)
        
        # Calculate shares by commodity group
        total = df['value'].sum()
        shares = df.groupby('comgroup')['value'].sum() / total
        
        # Calculate diversity index (Shannon entropy)
        diversity = -np.sum(shares * np.log(shares + 1e-10))
        max_diversity = np.log(len(shares))
        
        analysis['diversification_index'] = diversity / max_diversity if max_diversity > 0 else 0
        analysis['dominant_source'] = shares.idxmax()
        analysis['dominant_share'] = shares.max()
        
        return analysis
    
    def analyze_costs(
        self,
        data: Dict[str, pd.DataFrame],
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze cost structure."""
        analysis = {}
        
        if 'costs' not in data:
            return analysis
        
        df = self._apply_filters(data['costs'], filters)
        
        analysis['investment_required'] = df[df['cost_type'] == 'investment']['value'].sum()
        analysis['operational_cost'] = df[df['cost_type'] == 'operational']['value'].sum()
        
        return analysis
    
    def analyze_technology_deployment(
        self,
        data: Dict[str, pd.DataFrame],
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze key technology deployment."""
        analysis = {}
        
        if 'capacity' not in data:
            return analysis
        
        df = self._apply_filters(data['capacity'], filters)
        
        # Identify technologies with highest growth
        tech_growth = df.groupby('techgroup')['value'].sum().sort_values(ascending=False)
        
        analysis['key_technologies'] = tech_growth.head(5).index.tolist()
        analysis['total_capacity'] = tech_growth.sum()
        
        return analysis
    
    def _apply_filters(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """Apply filters to dataframe."""
        df_filtered = df.copy()
        
        for col, values in filters.items():
            if col in df_filtered.columns and values:
                df_filtered = df_filtered[df_filtered[col].isin(values)]
        
        return df_filtered


# modules/key_insights/comparisons.py
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Any, List

class ComparisonEngine:
    """Engine for comparing scenarios and regions."""
    
    def compare_energy_mix(
        self,
        data: Dict[str, pd.DataFrame],
        scenarios: List[str],
        filters: Dict[str, Any]
    ) -> go.Figure:
        """Create energy mix comparison chart."""
        if 'energy' not in data:
            return go.Figure()
        
        df = data['energy']
        
        # Apply filters
        for col, values in filters.items():
            if col != 'scen' and col in df.columns and values:
                df = df[df[col].isin(values)]
        
        # Filter for scenarios
        df = df[df['scen'].isin(scenarios)]
        
        # Aggregate by scenario and commodity group
        df_agg = df.groupby(['scen', 'comgroup'], as_index=False)['value'].sum()
        
        # Create stacked bar chart
        fig = go.Figure()
        
        commodities = df_agg['comgroup'].unique()
        colors = self._get_color_palette(len(commodities))
        
        for i, commodity in enumerate(commodities):
            df_commodity = df_agg[df_agg['comgroup'] == commodity]
            
            fig.add_trace(go.Bar(
                name=commodity,
                x=df_commodity['scen'],
                y=df_commodity['value'],
                marker_color=colors[i]
            ))
        
        fig.update_layout(
            barmode='stack',
            title="Energy Mix Comparison Across Scenarios",
            xaxis_title="Scenario",
            yaxis_title="Energy (GJ)",
            height=400
        )
        
        return fig
    
    def compare_emissions_trajectory(
        self,
        data: Dict[str, pd.DataFrame],
        scenarios: List[str],
        filters: Dict[str, Any]
    ) -> go.Figure:
        """Create emissions trajectory comparison."""
        if 'emissions' not in data:
            return go.Figure()
        
        df = data['emissions']
        
        # Apply filters
        for col, values in filters.items():
            if col not in ['scen', 'year'] and col in df.columns and values:
                df = df[df[col].isin(values)]
        
        # Filter for scenarios
        df = df[df['scen'].isin(scenarios)]
        
        # Aggregate by scenario and year
        df_agg = df.groupby(['scen', 'year'], as_index=False)['value'].sum()
        
        # Create line chart
        fig = go.Figure()
        
        for scenario in scenarios:
            df_scen = df_agg[df_agg['scen'] == scenario]
            
            fig.add_trace(go.Scatter(
                name=scenario,
                x=df_scen['year'],
                y=df_scen['value'],
                mode='lines+markers',
                line=dict(width=3)
            ))
        
        fig.update_layout(
            title="Emissions Trajectory Comparison",
            xaxis_title="Year",
            yaxis_title="CO₂ Emissions (Mt)",
            height=400
        )
        
        return fig
    
    def calculate_emissions_reductions(
        self,
        data: Dict[str, pd.DataFrame],
        scenarios: List[str],
        filters: Dict[str, Any]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate emissions reductions compared to baseline."""
        if 'emissions' not in data or len(scenarios) < 2:
            return {}
        
        df = data['emissions']
        
        # Apply filters
        for col, values in filters.items():
            if col != 'scen' and col in df.columns and values:
                df = df[df[col].isin(values)]
        
        # Calculate total emissions per scenario
        emissions_by_scenario = df[df['scen'].isin(scenarios)].groupby('scen')['value'].sum()
        
        baseline = emissions_by_scenario.iloc[0]
        
        reductions = {}
        for scenario in scenarios[1:]:
            if scenario in emissions_by_scenario.index:
                current = emissions_by_scenario[scenario]
                absolute_reduction = baseline - current
                percentage_reduction = (absolute_reduction / baseline * 100) if baseline > 0 else 0
                
                reductions[scenario] = {
                    'absolute': absolute_reduction,
                    'percentage': percentage_reduction
                }
        
        return reductions
    
    def compare_technology_capacity(
        self,
        data: Dict[str, pd.DataFrame],
        scenarios: List[str],
        filters: Dict[str, Any]
    ) -> go.Figure:
        """Compare technology capacity across scenarios."""
        if 'capacity' not in data:
            return go.Figure()
        
        df = data['capacity']
        
        # Apply filters
        for col, values in filters.items():
            if col != 'scen' and col in df.columns and values:
                df = df[df[col].isin(values)]
        
        # Filter for scenarios
        df = df[df['scen'].isin(scenarios)]
        
        # Aggregate by scenario and technology
        df_agg = df.groupby(['scen', 'techgroup'], as_index=False)['value'].sum()
        
        # Get top technologies
        top_techs = df_agg.groupby('techgroup')['value'].sum().nlargest(10).index
        df_agg = df_agg[df_agg['techgroup'].isin(top_techs)]
        
        # Create grouped bar chart
        fig = go.Figure()
        
        for scenario in scenarios:
            df_scen = df_agg[df_agg['scen'] == scenario]
            
            fig.add_trace(go.Bar(
                name=scenario,
                x=df_scen['techgroup'],
                y=df_scen['value']
            ))
        
        fig.update_layout(
            barmode='group',
            title="Technology Capacity Comparison",
            xaxis_title="Technology",
            yaxis_title="Capacity (MW)",
            height=400
        )
        
        return fig
    
    def compare_costs(
        self,
        data: Dict[str, pd.DataFrame],
        scenarios: List[str],
        filters: Dict[str, Any]
    ) -> go.Figure:
        """Compare costs across scenarios."""
        if 'costs' not in data:
            return go.Figure()
        
        df = data['costs']
        
        # Apply filters
        for col, values in filters.items():
            if col != 'scen' and col in df.columns and values:
                df = df[df[col].isin(values)]
        
        # Filter for scenarios
        df = df[df['scen'].isin(scenarios)]
        
        # Create stacked bar by cost type
        df_agg = df.groupby(['scen', 'cost_type'], as_index=False)['value'].sum()
        
        fig = go.Figure()
        
        cost_types = df_agg['cost_type'].unique()
        
        for cost_type in cost_types:
            df_type = df_agg[df_agg['cost_type'] == cost_type]
            
            fig.add_trace(go.Bar(
                name=cost_type,
                x=df_type['scen'],
                y=df_type['value']
            ))
        
        fig.update_layout(
            barmode='stack',
            title="Cost Comparison Across Scenarios",
            xaxis_title="Scenario",
            yaxis_title="Cost (M€)",
            height=400
        )
        
        return fig
    
    def calculate_cost_differences(
        self,
        data: Dict[str, pd.DataFrame],
        scenarios: List[str],
        filters: Dict[str, Any]
    ) -> pd.DataFrame:
        """Calculate cost differences between scenarios."""
        if 'costs' not in data or len(scenarios) < 2:
            return pd.DataFrame()
        
        df = data['costs']
        
        # Apply filters
        for col, values in filters.items():
            if col != 'scen' and col in df.columns and values:
                df = df[df[col].isin(values)]
        
        # Calculate total costs per scenario
        costs_by_scenario = df[df['scen'].isin(scenarios)].groupby('scen')['value'].sum()
        
        # Create difference table
        baseline = costs_by_scenario.iloc[0]
        
        diff_data = []
        for scenario in scenarios:
            if scenario in costs_by_scenario.index:
                current = costs_by_scenario[scenario]
                diff = current - baseline
                diff_pct = (diff / baseline * 100) if baseline > 0 else 0
                
                diff_data.append({
                    'Scenario': scenario,
                    'Total Cost (M€)': f"{current:.1f}",
                    'Difference vs Baseline (M€)': f"{diff:+.1f}",
                    'Difference (%)': f"{diff_pct:+.1f}%"
                })
        
        return pd.DataFrame(diff_data)
    
    def compare_regions(
        self,
        data: Dict[str, pd.DataFrame],
        regions: List[str],
        metric: str,
        filters: Dict[str, Any]
    ) -> go.Figure:
        """Compare regions on selected metric."""
        # Implementation depends on metric selected
        fig = go.Figure()
        
        # Placeholder implementation
        fig.add_trace(go.Bar(
            x=regions,
            y=[100, 150, 120],  # Placeholder data
            name=metric
        ))
        
        fig.update_layout(
            title=f"Regional Comparison: {metric}",
            xaxis_title="Region",
            yaxis_title=metric,
            height=400
        )
        
        return fig
    
    def create_regional_summary(
        self,
        data: Dict[str, pd.DataFrame],
        regions: List[str],
        filters: Dict[str, Any]
    ) -> pd.DataFrame:
        """Create summary table for regional comparison."""
        # Placeholder implementation
        summary_data = []
        
        for region in regions:
            summary_data.append({
                'Region': region,
                'Population': 'N/A',
                'Total Energy (PJ)': 'N/A',
                'CO₂ Emissions (Mt)': 'N/A',
                'Renewable Share (%)': 'N/A'
            })
        
        return pd.DataFrame(summary_data)
    
    def analyze_energy_mix_differences(
        self,
        data: Dict[str, pd.DataFrame],
        scenarios: List[str],
        filters: Dict[str, Any]
    ) -> List[str]:
        """Analyze and describe energy mix differences."""
        insights = []
        
        if 'energy' not in data:
            return insights
        
        df = data['energy']
        
        # Apply filters
        for col, values in filters.items():
            if col != 'scen' and col in df.columns and values:
                df = df[df[col].isin(values)]
        
        df = df[df['scen'].isin(scenarios)]
        
        # Calculate shares
        for scenario in scenarios[1:]:
            df_base = df[df['scen'] == scenarios[0]]
            df_scen = df[df['scen'] == scenario]
            
            base_renewable = df_base[df_base['comgroup'].str.contains('WIND|SOLAR|HYDRO', na=False)]['value'].sum()
            scen_renewable = df_scen[df_scen['comgroup'].str.contains('WIND|SOLAR|HYDRO', na=False)]['value'].sum()
            
            base_total = df_base['value'].sum()
            scen_total = df_scen['value'].sum()
            
            if base_total > 0 and scen_total > 0:
                base_share = base_renewable / base_total * 100
                scen_share = scen_renewable / scen_total * 100
                
                diff = scen_share - base_share
                
                insights.append(
                    f"**{scenario}** increases renewable share by {diff:+.1f}% compared to baseline"
                )
        
        return insights
    
    def _get_color_palette(self, n: int) -> List[str]:
        """Get a color palette with n colors."""
        import plotly.express as px
        return px.colors.qualitative.Set3[:n]


# modules/key_insights/visualizations.py
import plotly.graph_objects as go
from typing import Any

class InsightsVisualizer:
    """Visualization components for Key Insights module."""
    
    def create_kpi_gauge(
        self,
        value: float,
        title: str,
        unit: str,
        range_max: float,
        threshold_good: float = None,
        threshold_warning: float = None
    ) -> go.Figure:
        """Create a gauge chart for KPI visualization."""
        
        # Determine color based on thresholds
        if threshold_good and threshold_warning:
            if value <= threshold_good:
                color = "green"
            elif value <= threshold_warning:
                color = "yellow"
            else:
                color = "red"
        else:
            color = "blue"
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=value,
            title={'text': title},
            number={'suffix': f" {unit}"},
            gauge={
                'axis': {'range': [0, range_max]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, range_max * 0.33], 'color': "lightgray"},
                    {'range': [range_max * 0.33, range_max * 0.66], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': range_max * 0.9
                }
            }
        ))
        
        fig.update_layout(height=250)
        
        return fig
    
    def create_stacked_bar(self, df, **kwargs):
        """Create stacked bar chart - placeholder."""
        # Reuse from TimesReportPlotter
        pass
    
    def create_line_plot(self, df, **kwargs):
        """Create line plot - placeholder."""
        # Reuse from TimesReportPlotter
        pass
```

### 4. Module Registry

```python
# config/module_registry.py
from typing import Dict, Type
from modules.base_module import BaseModule
from modules.key_insights.module import KeyInsightsModule
from modules.energy_emissions.module import EnergyEmissionsModule
from modules.land_use.module import LandUseModule
# from modules.economics.module import EconomicsModule
# from modules.daynite.module import DayNiteModule

class ModuleRegistry:
    """Central registry for all app modules."""
    
    def __init__(self):
        self._modules: Dict[str, BaseModule] = {}
        self._register_default_modules()
    
    def _register_default_modules(self):
        """Register all default modules."""
        self.register_module("key_insights", KeyInsightsModule())
        self.register_module("energy_emissions", EnergyEmissionsModule())
        self.register_module("land_use", LandUseModule())
        # self.register_module("economics", EconomicsModule())
        # self.register_module("daynite", DayNiteModule())
    
    def register_module(self, key: str, module: BaseModule):
        """Register a new module."""
        self._modules[key] = module
    
    def get_module(self, key: str) -> BaseModule:
        """Get a registered module."""
        if key not in self._modules:
            raise KeyError(f"Module '{key}' not found in registry.")
        return self._modules[key]
    
    def get_all_modules(self) -> Dict[str, BaseModule]:
        """Get all registered modules."""
        return self._modules.copy()
    
    def get_module_names(self) -> list[str]:
        """Get list of module names for display."""
        return [module.name for module in self._modules.values()]
```

### 5. Refactored Main Application

```python
# main.py
import streamlit as st
from pathlib import Path
import pandas as pd
from typing import Dict, Any

from core.data_loader import DataLoader
from core.filter_manager import FilterManager
from core.session_manager import SessionManager
from config.module_registry import ModuleRegistry
from components.sidebar import render_sidebar

def main():
    """Main Streamlit application entry point."""
    
    # Page configuration
    st.set_page_config(
        page_title="SpeedLocal: TIMES Data Explorer",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session manager
    session_mgr = SessionManager()
    
    # Initialize module registry
    if "module_registry" not in st.session_state:
        st.session_state.module_registry = ModuleRegistry()
    
    module_registry = st.session_state.module_registry
    
    # Title
    st.title("SpeedLocal: TIMES Data Explorer")
    
    # Render sidebar and get configuration
    config = render_sidebar()
    
    if not config.get('valid', False):
        st.stop()
    
    # Handle data loading
    if config.get('reload_requested', False):
        session_mgr.clear_all()
    
    # Load data if not in session
    if not session_mgr.has('data_loader'):
        data_loader = DataLoader(
            db_source=config['db_source'],
            mapping_csv=config.get('mapping_csv', 'inputs/mapping_db_views.csv'),
            is_url=config.get('is_url', False)
        )
        
        # Load all required tables from all modules
        required_tables = set()
        for module in module_registry.get_all_modules().values():
            required_tables.update(module.get_required_tables())
        
        data = data_loader.load_tables(list(required_tables))
        
        session_mgr.set('data_loader', data_loader)
        session_mgr.set('data', data)
    
    # Get data from session
    data = session_mgr.get('data', {})
    
    if not data:
        st.error("No data loaded. Please check your database connection.")
        st.stop()
    
    # Initialize filter manager
    if not session_mgr.has('filter_manager'):
        filter_manager = FilterManager(data)
        session_mgr.set('filter_manager', filter_manager)
    
    filter_manager = session_mgr.get('filter_manager')
    
    # Render global filters in sidebar
    with st.sidebar:
        st.markdown("---")
        st.subheader("Global Filters")
        global_filters = filter_manager.render_global_filters()
    
    # Create tabs for each module
    module_names = module_registry.get_module_names()
    tabs = st.tabs(module_names)
    
    # Render each module in its tab
    for tab, (module_key, module) in zip(tabs, module_registry.get_all_modules().items()):
        with tab:
            try:
                # Get module-specific filter config
                filter_config = module.get_filter_config()
                
                # Render module-specific filters
                with st.expander("📊 Module Filters", expanded=False):
                    module_filters = filter_manager.render_module_filters(
                        module_key,
                        filter_config
                    )
                
                # Combine global and module filters
                combined_filters = {**global_filters, **module_filters}
                
                # Render the module
                module.render(data, combined_filters)
                
            except Exception as e:
                st.error(f"Error rendering {module.name}: {str(e)}")
                if st.checkbox(f"Show error details for {module.name}", key=f"error_{module_key}"):
                    st.exception(e)

if __name__ == "__main__":
    main()
```

### 6. Core Components

```python
# core/data_loader.py
import pandas as pd
from typing import Dict, List, Optional
import streamlit as st

class DataLoader:
    """Centralized data loading from DuckDB or CSV."""
    
    def __init__(self, db_source: str, mapping_csv: str, is_url: bool = False):
        self.db_source = db_source
        self.mapping_csv = mapping_csv
        self.is_url = is_url
        self._connection = None
    
    def load_tables(self, table_names: List[str]) -> Dict[str, pd.DataFrame]:
        """Load specified tables from database."""
        data = {}
        
        with st.spinner("Loading data from database..."):
            for table_name in table_names:
                try:
                    df = self._load_table(table_name)
                    if df is not None and not df.empty:
                        data[table_name] = df
                        st.success(f"✓ Loaded {table_name}: {len(df)} rows")
                    else:
                        st.warning(f"⚠ Table {table_name} is empty or not found")
                except Exception as e:
                    st.error(f"✗ Error loading {table_name}: {str(e)}")
        
        return data
    
    def _load_table(self, table_name: str) -> Optional[pd.DataFrame]:
        """Load a single table."""
        # Implementation depends on your current utils
        # This is a placeholder
        pass
    
    def get_connection(self):
        """Get database connection."""
        if self._connection is None:
            # Create connection
            pass
        return self._connection
    
    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None


# core/filter_manager.py
import streamlit as st
import pandas as pd
from typing import Dict, List, Any

class FilterManager:
    """Centralized filter management."""
    
    def __init__(self, data: Dict[str, pd.DataFrame]):
        self.data = data
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize filter state."""
        if 'global_filters' not in st.session_state:
            st.session_state.global_filters = {}
        if 'module_filters' not in st.session_state:
            st.session_state.module_filters = {}
    
    def render_global_filters(self) -> Dict[str, List[Any]]:
        """Render global filters that apply to all modules."""
        filters = {}
        
        # Combine all dataframes to get unique values
        all_df = pd.concat([df for df in self.data.values() if not df.empty], ignore_index=True)
        
        # Scenario filter
        if 'scen' in all_df.columns:
            scenarios = sorted(all_df['scen'].unique())
            selected_scenarios = st.multiselect(
                "Scenarios",
                options=scenarios,
                default=scenarios,
                key="global_filter_scen"
            )
            filters['scen'] = selected_scenarios
        
        # Year filter
        if 'year' in all_df.columns:
            years = sorted(all_df['year'].unique())
            selected_years = st.multiselect(
                "Years",
                options=years,
                default=years,
                key="global_filter_year"
            )
            filters['year'] = selected_years
        
        return filters
    
    def render_module_filters(self, module_key: str, config: Dict[str, Any]) -> Dict[str, List[Any]]:
        """Render module-specific filters."""
        filters = {}
        
        filterable_cols = config.get('filterable_columns', [])
        
        for col in filterable_cols:
            # Skip if already in global filters
            if col in st.session_state.get('global_filters', {}):
                continue
            
            # Get unique values from relevant tables
            values = self._get_unique_values(col)
            
            if values:
                selected = st.multiselect(
                    col.capitalize(),
                    options=values,
                    default=values,
                    key=f"{module_key}_filter_{col}"
                )
                filters[col] = selected
        
        return filters
    
    def _get_unique_values(self, column: str) -> List[Any]:
        """Get unique values for a column across all data."""
        all_values = set()
        
        for df in self.data.values():
            if column in df.columns:
                all_values.update(df[column].dropna().unique())
        
        return sorted(list(all_values))


# core/session_manager.py
import streamlit as st
from typing import Any, Dict

class SessionManager:
    """Manage Streamlit session state."""
    
    def set(self, key: str, value: Any):
        """Set a session state value."""
        st.session_state[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a session state value."""
        return st.session_state.get(key, default)
    
    def has(self, key: str) -> bool:
        """Check if key exists in session state."""
        return key in st.session_state
    
    def delete(self, key: str):
        """Delete a key from session state."""
        if key in st.session_state:
            del st.session_state[key]
    
    def clear_all(self):
        """Clear all session state."""
        for key in list(st.session_state.keys()):
            del st.session_state[key]
    
    def clear_pattern(self, pattern: str):
        """Clear keys matching a pattern."""
        keys_to_delete = [key for key in st.session_state.keys() if pattern in key]
        for key in keys_to_delete:
            del st.session_state[key]
```

---

## Migration Strategy

### Phase 1: Foundation (Week 1-2)
1. Create new directory structure
2. Implement base module class
3. Implement core components (DataLoader, FilterManager, SessionManager)
4. Set up module registry

### Phase 2: Module Migration (Week 3-4)
1. Migrate Energy/Emissions to new module structure
2. Test thoroughly
3. Migrate remaining sections one by one
4. Keep old code as fallback

### Phase 3: New Modules (Week 5-6)
1. Implement Land Use module with map component
2. Implement Economics module
3. Implement DAYNITE module
4. Add module-specific queries and visualizations

### Phase 4: Enhancement (Week 7-8)
1. Add module configuration files
2. Implement module enable/disable functionality
3. Add module-level caching
4. Optimize performance
5. Add comprehensive testing

---

## Key Benefits of This Architecture

### 1. **Modularity**
- Each module is self-contained
- Easy to add/remove/modify modules
- Clear separation of concerns

### 2. **Reusability**
- Common components shared across modules
- Base class provides consistent interface
- Filter and visualization logic centralized

### 3. **Maintainability**
- Easier to understand and debug
- Changes to one module don't affect others
- Clear code organization

### 4. **Scalability**
- Easy to add new modules
- Can disable modules that aren't needed
- Performance can be optimized per module

### 5. **Testability**
- Each module can be tested independently
- Mock data can be injected easily
- Unit tests for each component

---

## Additional Recommendations

### 1. Configuration Files
Use YAML or JSON for module configuration:

```yaml
# config/modules.yaml
modules:
  key_insights:
    enabled: true
    order: 0  # First tab - stakeholder dashboard
    required_tables: ["energy", "emissions", "capacity", "costs"]
    default_filters:
      - scen
      - year
    features:
      - scenario_comparison
      - regional_comparison
      - kpi_dashboard
      - executive_summary
    
  energy_emissions:
    enabled: true
    order: 1
    required_tables: ["energy", "emissions"]
    default_filters:
      - scen
      - sector
      - year
    excluded_sectors:
      - AFO
      - DMZ
      - SYS
  
  land_use:
    enabled: false  # Enable when data available
    order: 2
    required_tables: ["land_use"]
    default_filters:
      - scen
      - region
      - year
```

### 2. Query Builder Pattern
Create a query builder for complex DuckDB queries:

```python
# modules/energy_emissions/queries.py
from typing import Dict, Any, List

class EnergyQueries:
    """Query builder for energy/emissions data."""
    
    @staticmethod
    def get_energy_by_sector(
        scenarios: List[str],
        years: List[int],
        sectors: List[str] = None
    ) -> str:
        """Build query for energy by sector."""
        query = """
        SELECT 
            f.scen,
            f.sector,
            s.description as sector_desc,
            f.year,
            f.comgroup,
            c.description as comgroup_desc,
            SUM(f.value) as value,
            f.unit
        FROM timesreport_facts f
        LEFT JOIN sector_desc s ON f.sector = s.id AND f.scen = s.scen
        LEFT JOIN comgroup_desc c ON f.comgroup = c.id AND f.scen = c.scen
        WHERE f.topic = 'energy'
        AND f.attr = 'f_in'
        AND f.scen IN ({scenarios})
        AND f.year IN ({years})
        """
        
        if sectors:
            query += f" AND f.sector IN ({','.join(['?' for _ in sectors])})"
        
        query += " GROUP BY f.scen, f.sector, s.description, f.year, f.comgroup, c.description, f.unit"
        
        return query
```

### 3. Visualization Library
Create a visualization library specific to your needs:

```python
# components/plots.py
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

class TimesPlotBuilder:
    """Builder for TIMES-specific plots."""
    
    @staticmethod
    def stacked_bar_by_scenario(
        df: pd.DataFrame,
        x_col: str,
        y_col: str,
        stack_col: str,
        scenario_col: str,
        title: str = None
    ) -> go.Figure:
        """Create stacked bar chart with scenario comparison."""
        # Implementation
        pass
    
    @staticmethod
    def line_with_confidence(
        df: pd.DataFrame,
        x_col: str,
        y_col: str,
        scenario_col: str,
        confidence_level: float = 0.95,
        title: str = None
    ) -> go.Figure:
        """Create line plot with confidence intervals."""
        # Implementation
        pass
```

### 4. Error Handling
Implement robust error handling:

```python
# utils/error_handler.py
import streamlit as st
import logging
from functools import wraps

def handle_errors(func):
    """Decorator for error handling."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            st.error(f"An error occurred: {str(e)}")
            if st.session_state.get('debug_mode', False):
                st.exception(e)
            return None
    return wrapper
```

---

## Conclusion

This modular architecture provides:
- **Clear separation** between modules
- **Easy extensibility** for new features
- **Improved maintainability** through organized code
- **Better testability** with isolated components
- **Scalable structure** for future growth

The migration can be done incrementally, allowing you to maintain the current functionality while transitioning to the new structure.

Would you like me to provide more detail on any specific aspect or help implement a particular module?
