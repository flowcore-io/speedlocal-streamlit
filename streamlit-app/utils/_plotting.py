import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Optional, Dict, List, Union, Any

from utils.unit_converter import extract_unit_label

class TimesReportPlotter:
    """
    Generic plotting class using pre-loaded DataFrames.
    
    New unified interface via create_figure() method with configuration-driven plotting.
    Legacy methods (stacked_bar, line_plot, stacked_timeseries) maintained for compatibility.
    """

    def __init__(
        self,
        df: pd.DataFrame
    ):
        """
        Args:
            df: DataFrame from PandasDFCreator
        """
        if df.empty:
            raise ValueError("DataFrame is empty.")
        self.df = df.copy()
        self.color_maps = {}

    def _get_color_map(self, group_col: str) -> Dict[str, str]:
        groups = sorted(self.df[group_col].unique())
        if group_col not in self.color_maps:
            colors = px.colors.qualitative.Set3[:len(groups)]
            self.color_maps[group_col] = dict(zip(groups, colors))
        return self.color_maps[group_col]

    
    def create_figure(
        self,
        plot_spec: Dict[str, Any],
        filters: Optional[Dict[str, Union[str, List[str]]]] = None
    ) -> Optional[go.Figure]:
        """
        Create any type of plot from a specification dictionary.
        
        Args:
            plot_spec: Plot specification with structure:
                {
                    'x_col': str,                    # X-axis column name
                    'y_col': str,                    # Y-axis column name (or None for multi-column)
                    'series': [                      # List of series to plot
                        {
                            'group_col': str,        # Column to group by (optional)
                            'columns': List[str],    # Explicit columns to plot (optional)
                            'type': str,             # 'bar', 'line', 'area'
                            'stack': bool,           # Stack bars (for type='bar')
                            'y_axis': str,           # 'primary' or 'secondary'
                            'opacity': float,        # Trace opacity
                            'dash': str,             # Line dash style (for type='line')
                            'fill': str,             # Fill style (for type='area')
                            'color': str,            # Explicit color (optional)
                        }
                    ],
                    'scenario_col': str,             # Column for scenario grouping (optional)
                    'scenario_layout': str,          # 'grouped', 'overlay' (optional)
                    'axes': {                        # Axis configuration
                        'primary': {
                            'title': str,
                            'side': str,
                            'showgrid': bool
                        },
                        'secondary': {              # Optional secondary axis
                            'title': str,
                            'side': str,
                            'overlaying': bool,
                            'showgrid': bool,
                            'align_zero': bool
                        }
                    },
                    'title': str,                    # Plot title
                    'height': int,                   # Plot height in pixels
                    'barmode': str,                  # 'stack', 'group', 'relative'
                }
            filters: Optional filters to apply to data
            
        Returns:
            Plotly Figure object or None if data is empty
        """
        # Apply filters
        df = self._filter_df_internal(filters)
        if df.empty:
            return None
        
        # Extract spec components
        x_col = plot_spec.get('x_col')
        y_col = plot_spec.get('y_col', 'value')
        series_specs = plot_spec.get('series', [])
        scenario_col = plot_spec.get('scenario_col')
        axes_config = plot_spec.get('axes', {})
        title = plot_spec.get('title', 'Plot')
        height = plot_spec.get('height', 600)
        barmode = plot_spec.get('barmode', 'stack')
        
        if not series_specs:
            return None
        
        # Create figure
        fig = go.Figure()
        
        # Build traces for each series
        for series_spec in series_specs:
            self._add_series_traces(
                fig=fig,
                df=df,
                series_spec=series_spec,
                x_col=x_col,
                y_col=y_col,
                scenario_col=scenario_col
            )
        
        # Configure layout
        self._configure_layout(
            fig=fig,
            axes_config=axes_config,
            x_col=x_col,
            title=title,
            height=height,
            barmode=barmode,
            df = df
        )
        
        return fig
    
    def _filter_df_internal(self, filters: Optional[Dict] = None) -> pd.DataFrame:
        """Apply filters to dataframe."""
        df = self.df.copy()
        
        if not filters:
            return df
        
        for col, val in filters.items():
            if col not in df.columns:
                continue
            
            if isinstance(val, list):
                df = df[df[col].isin(val)]
            else:
                df = df[df[col] == val]
        
        return df
    
    def _add_series_traces(
        self,
        fig: go.Figure,
        df: pd.DataFrame,
        series_spec: Dict,
        x_col: str,
        y_col: Optional[str],
        scenario_col: Optional[str]
    ) -> None:
        """Add traces for a single series specification."""
        
        series_type = series_spec.get('type', 'bar')
        group_col = series_spec.get('group_col')
        columns = series_spec.get('columns')  # Explicit columns (for time series)
        y_axis = 'y2' if series_spec.get('y_axis') == 'secondary' else 'y'
        
        # Determine what to plot
        if columns:
            # Explicit columns specified (e.g., time series with multiple commodities)
            self._add_column_traces(
                fig=fig,
                df=df,
                columns=columns,
                x_col=x_col,
                series_spec=series_spec,
                y_axis=y_axis
            )
        elif group_col:
            # Group by column (e.g., group by comgroup, techgroup)
            self._add_grouped_traces(
                fig=fig,
                df=df,
                group_col=group_col,
                x_col=x_col,
                y_col=y_col,
                scenario_col=scenario_col,
                series_spec=series_spec,
                y_axis=y_axis
            )
        else:
            # Single series, no grouping
            self._add_single_trace(
                fig=fig,
                df=df,
                x_col=x_col,
                y_col=y_col,
                series_spec=series_spec,
                y_axis=y_axis
            )
    
    def _add_column_traces(
        self,
        fig: go.Figure,
        df: pd.DataFrame,
        columns: List[str],
        x_col: str,
        series_spec: Dict,
        y_axis: str
    ) -> None:
        """Add traces for explicitly specified columns (time series mode)."""
        
        series_type = series_spec.get('type', 'bar')
        opacity = series_spec.get('opacity', 0.85)
        color = series_spec.get('color')
        
        # For area plots, sum all columns
        if series_type == 'area':
            y_values = df[columns].sum(axis=1)
            
            fig.add_trace(go.Scatter(
                name=series_spec.get('name', 'Area'),
                x=df[x_col],
                y=y_values,
                mode='lines',
                fill=series_spec.get('fill', 'tozeroy'),
                line=dict(width=series_spec.get('line_width', 0)),
                fillcolor=series_spec.get('fillcolor', 'rgba(128,128,128,0.2)'),
                opacity=opacity,
                yaxis=y_axis,
                showlegend=True
            ))
        else:
            # For bar/line, plot each column
            for col in columns:
                if col not in df.columns:
                    continue
                
                if series_type == 'bar':
                    fig.add_trace(go.Bar(
                        name=col,
                        x=df[x_col],
                        y=df[col],
                        marker_color=color,
                        opacity=opacity,
                        yaxis=y_axis,
                        marker_line_width=0
                    ))
                
                elif series_type == 'line':
                    line_config = {'width': series_spec.get('width', 1)}
                    if series_spec.get('dash'):
                        line_config['dash'] = series_spec['dash']
                    if color:
                        line_config['color'] = color
                    
                    fig.add_trace(go.Scatter(
                        name=col,
                        x=df[x_col],
                        y=df[col],
                        mode='lines',
                        line=line_config,
                        yaxis=y_axis
                    ))
    
    def _add_grouped_traces(
        self,
        fig: go.Figure,
        df: pd.DataFrame,
        group_col: str,
        x_col: str,
        y_col: str,
        scenario_col: Optional[str],
        series_spec: Dict,
        y_axis: str
    ) -> None:
        """Add traces grouped by a column (with optional scenario separation)."""
        
        series_type = series_spec.get('type', 'bar')
        opacity = series_spec.get('opacity', 0.85)
        
        # Get color map for this group column
        color_map = self._get_color_map(group_col)
        groups = sorted(df[group_col].unique())
        
        # Handle scenarios
        scenarios = sorted(df[scenario_col].unique()) if scenario_col and scenario_col in df.columns else [None]
        
        if series_type == 'bar' and scenario_col and len(scenarios) > 1:
            # Grouped bars by scenario
            self._add_grouped_bar_traces(
                fig=fig,
                df=df,
                groups=groups,
                group_col=group_col,
                x_col=x_col,
                y_col=y_col,
                scenario_col=scenario_col,
                scenarios=scenarios,
                color_map=color_map,
                y_axis=y_axis,
                opacity=opacity
            )
        else:
            # Simple grouped traces
            for scen in scenarios:
                scen_data = df[df[scenario_col] == scen] if scenario_col else df
                
                for grp in groups:
                    grp_data = scen_data[scen_data[group_col] == grp]
                    
                    if grp_data.empty:
                        continue
                    
                    name = f"{grp} - {scen}" if scen else grp
                    
                    if series_type == 'bar':
                        fig.add_trace(go.Bar(
                            name=name,
                            x=grp_data[x_col],
                            y=grp_data[y_col],
                            marker_color=color_map.get(grp),
                            opacity=opacity,
                            yaxis=y_axis,
                            marker_line_width=0,
                            legendgroup=grp,
                            showlegend=(scen == scenarios[0]) if scenario_col else True
                        ))
                    
                    elif series_type == 'line':
                        fig.add_trace(go.Scatter(
                            name=name,
                            x=grp_data[x_col],
                            y=grp_data[y_col],
                            mode='lines+markers',
                            line=dict(color=color_map.get(grp)),
                            marker=dict(size=6),
                            yaxis=y_axis
                        ))
    
    def _add_grouped_bar_traces(
        self,
        fig: go.Figure,
        df: pd.DataFrame,
        groups: List,
        group_col: str,
        x_col: str,
        y_col: str,
        scenario_col: str,
        scenarios: List,
        color_map: Dict,
        y_axis: str,
        opacity: float
    ) -> None:
        """Add grouped bar traces with scenario separation."""
        
        x_values = sorted(df[x_col].unique())
        scenario_width = 0.8 / len(scenarios)
        
        for x in x_values:
            x_data = df[df[x_col] == x]
            
            for i, scen in enumerate(scenarios):
                scen_data = x_data[x_data[scenario_col] == scen]
                x_pos = float(x) + (i - len(scenarios)/2 + 0.5) * scenario_width
                
                for grp in groups:
                    value = scen_data[scen_data[group_col] == grp][y_col].sum()
                    
                    fig.add_trace(go.Bar(
                        x=[x_pos],
                        y=[value],
                        name=grp,
                        width=scenario_width * 0.9,
                        marker_color=color_map.get(grp),
                        opacity=opacity,
                        yaxis=y_axis,
                        legendgroup=grp,
                        showlegend=(x == x_values[0] and i == 0)
                    ))
    
    def _add_single_trace(
        self,
        fig: go.Figure,
        df: pd.DataFrame,
        x_col: str,
        y_col: str,
        series_spec: Dict,
        y_axis: str
    ) -> None:
        """Add a single trace (no grouping)."""
        
        series_type = series_spec.get('type', 'line')
        opacity = series_spec.get('opacity', 0.85)
        color = series_spec.get('color')
        name = series_spec.get('name', 'Series')
        
        if series_type == 'bar':
            fig.add_trace(go.Bar(
                name=name,
                x=df[x_col],
                y=df[y_col],
                marker_color=color,
                opacity=opacity,
                yaxis=y_axis
            ))
        
        elif series_type == 'line':
            line_config = {'width': series_spec.get('width', 2)}
            if series_spec.get('dash'):
                line_config['dash'] = series_spec['dash']
            if color:
                line_config['color'] = color
            
            fig.add_trace(go.Scatter(
                name=name,
                x=df[x_col],
                y=df[y_col],
                mode='lines+markers',
                line=line_config,
                yaxis=y_axis
            ))
    
    def _configure_layout(
        self,
        fig: go.Figure,
        axes_config: Dict,
        x_col: str,
        title: str,
        height: int,
        barmode: str,
        df: pd.DataFrame = None
    ) -> None:
        """Configure figure layout including axes."""
        
        # Get primary axis config
        primary_config = axes_config.get('primary', {})
        primary_title = primary_config.get('title', 'Value')
        
        # Auto-detect unit if not specified
        if primary_title == 'Value' or not primary_title:
            primary_title = self._get_unit_label_from_df()
        
        layout_config = {
            'barmode': barmode,
            'title': title,
            'height': height,
            'xaxis': {
                'title': x_col,
                'tickfont': dict(size=10),
                'type': 'linear'
            },
            'yaxis': {
                'title': primary_title,
                'side': primary_config.get('side', 'left'),
                'showgrid': primary_config.get('showgrid', False),
                'tickfont': dict(size=11)
            },
            'legend': dict(
                orientation="h",
                yanchor="top",
                y=-0.15,
                xanchor="center",
                x=0.5,
                font=dict(size=11)
            ),
            'margin': dict(t=90, b=120, l=60, r=60)
        }
        # Set explicit tick values if we have numeric data
        if df is not None and x_col in df.columns:
            x_values = sorted(df[x_col].unique())
            if len(x_values) > 0 and isinstance(x_values[0], (int, float)):
                layout_config['xaxis']['tickmode'] = 'array'
                layout_config['xaxis']['tickvals'] = x_values
                layout_config['xaxis']['ticktext'] = [str(int(x)) for x in x_values]
                       
        # Add secondary axis if configured
        secondary_config = axes_config.get('secondary')
        if secondary_config:
            secondary_title = secondary_config.get('title', 'Secondary Value')
            
            layout_config['yaxis2'] = {
                'title': secondary_title,
                'overlaying': 'y',
                'side': secondary_config.get('side', 'right'),
                'showgrid': secondary_config.get('showgrid', False),
                'tickfont': dict(size=11),
                'showticklabels': True
            }
        
        fig.update_layout(**layout_config)
    
    def _get_unit_label_from_df(self) -> str:
        """
        Extract unit label from dataframe.
        Wrapper around utility function.
        """
        return extract_unit_label(self.df)
    
    