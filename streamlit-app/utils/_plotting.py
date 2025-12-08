import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Optional, Dict, List, Union, Any

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
        Checks both 'unit' and 'cur' columns.
        """
        units = []
        
        if 'unit' in self.df.columns:
            df_units = self.df['unit'].dropna().unique()
            units.extend([u for u in df_units if str(u).upper() != 'NA'])
        
        if 'cur' in self.df.columns:
            df_curs = self.df['cur'].dropna().unique()
            units.extend([c for c in df_curs if str(c).upper() != 'NA'])
        
        if not units:
            return 'value'
        elif len(units) == 1:
            return str(units[0])
        else:
            return ', '.join(sorted(set(str(u) for u in units)))
    
    # ==================== LEGACY METHODS (for backward compatibility) ====================

    def _filter_df(self, filter_dict: Optional[Dict[str, Union[str, List[str]]]] = None) -> pd.DataFrame:
        """
        Filter the DataFrame using provided dictionary. If query_helper is provided,
        only keep values that exist in the DB.
        """
        df = self.df.copy()
        if filter_dict and self.query_helper:
            for col, val in filter_dict.items():
                # Get allowed values from DB
                allowed_values = self.query_helper.fetch_unique_values(col)
                if isinstance(val, list):
                    val_filtered = [v for v in val if v in allowed_values]
                    df = df[df[col].isin(val_filtered)]
                else:
                    df = df[df[col] == val] if val in allowed_values else df.iloc[0:0]
        elif filter_dict:
            for col, val in filter_dict.items():
                if isinstance(val, list):
                    df = df[df[col].isin(val)]
                else:
                    df = df[df[col] == val]
        return df

    def plot(self, method: str, **kwargs) -> Optional[go.Figure]:
        """
        Dynamically call plotting method by name.
        
        Args:
            method: Name of the plotting method ('stacked_bar', 'line_plot', etc.)
            **kwargs: All arguments to pass to the plotting method
            
        Returns:
            Plotly figure or None
            
        Raises:
            ValueError: If method name is not recognized
        """
        if not hasattr(self, method):
            available = [m for m in dir(self) if not m.startswith('_') and callable(getattr(self, m))]
            raise ValueError(
                f"Unknown plot method: '{method}'. "
                f"Available methods: {', '.join(available)}"
            )
        
        plot_func = getattr(self, method)
        return plot_func(**kwargs)

    def stacked_bar(
        self,
        x_col: str,
        y_col: str,
        group_col: str,
        scenario_col: Optional[str] = None,
        filter_dict: Optional[Dict[str, Union[str, List[str]]]] = None,
        title: str = "Stacked Bar Chart",
        height: int = 600
    ) -> Optional[go.Figure]:

        df = self._filter_df(filter_dict)
        if df.empty:
            return None

        # Detect units from data (may be multiple after conversion)
        if 'unit' in df.columns:
            units = df['unit'].dropna().unique()
            if len(units) == 1:
                unit_label = units[0]
            elif len(units) > 1:
                unit_label = ", ".join(sorted(units))
            else:
                unit_label = y_col
        else:
            unit_label = y_col

        groups = sorted(df[group_col].unique())
        color_map = self._get_color_map(group_col)
        x_values = sorted(df[x_col].unique())
        scenarios = sorted(df[scenario_col].unique()) if scenario_col else [None]
        scenario_width = 0.8 / len(scenarios)

        fig = go.Figure()
        for x in x_values:
            x_data = df[df[x_col] == x]
            for i, scen in enumerate(scenarios):
                scen_data = x_data[x_data[scenario_col] == scen] if scenario_col else x_data
                x_pos = float(x) + (i - len(scenarios)/2 + 0.5) * scenario_width
                for grp in groups:
                    value = scen_data[scen_data[group_col] == grp][y_col].sum()
                    fig.add_trace(go.Bar(
                        x=[x_pos],
                        y=[value],
                        name=grp,
                        width=scenario_width * 0.9,
                        marker_color=color_map.get(grp),
                        legendgroup=grp,
                        showlegend=x==x_values[0] and i==0
                    ))

        fig.update_layout(
            barmode='stack',
            title=title,
            xaxis_title=x_col,
            yaxis_title=unit_label,  # ← Updated to show unit(s)
            height=height,
            bargap=0,
            bargroupgap=0.1
        )
        fig.update_xaxes(tickmode='array', tickvals=x_values, ticktext=x_values)
        return fig


    def line_plot(
        self,
        x_col: str,
        y_col: str,
        group_col: str,
        scenario_col: Optional[str] = None,
        filter_dict: Optional[Dict[str, Union[str, List[str]]]] = None,
        title: str = "Line Chart",
        height: int = 600
    ) -> Optional[go.Figure]:

        df = self._filter_df(filter_dict)
        if df.empty:
            return None

        # Detect units from data (may be multiple after conversion)
        if 'unit' in df.columns:
            units = df['unit'].dropna().unique()
            if len(units) == 1:
                unit_label = units[0]
            elif len(units) > 1:
                unit_label = ", ".join(sorted(units))
            else:
                unit_label = y_col
        else:
            unit_label = y_col

        color_map = self._get_color_map(group_col)
        scenarios = sorted(df[scenario_col].unique()) if scenario_col else [None]

        fig = go.Figure()
        for scen in scenarios:
            for grp in sorted(df[group_col].unique()):
                scen_data = df[(df[scenario_col]==scen) & (df[group_col]==grp)] if scenario_col else df[df[group_col]==grp]
                if not scen_data.empty:
                    fig.add_trace(go.Scatter(
                        x=scen_data[x_col],
                        y=scen_data[y_col],
                        mode='lines+markers',
                        name=f"{grp} - {scen}" if scen else grp,
                        line=dict(color=color_map.get(grp)),
                        marker=dict(size=6),
                        showlegend=True
                    ))

        fig.update_layout(
            title=title,
            xaxis_title=x_col,
            yaxis_title=unit_label,  # ← Updated to show unit(s)
            height=height
        )
        return fig
    def stacked_timeseries(
        self,
        time_col: str,
        categories: Dict[str, List[str]],
        config: Dict,
        unit_info: Dict[str, str],
        title: str = "Time Series Profile",
        height: int = 600
    ) -> Optional[go.Figure]:
        """
        Create stacked timeseries plot with multiple plot types.
        
        Args:
            time_col: Column containing time indices (e.g., 'all_ts')
            categories: Dict mapping plot_group -> list of column names
                       e.g., {'production': ['Solar', 'Wind'], 'price': ['Price']}
            config: Configuration dict from profile_config.yaml
            unit_info: Dict mapping plot_group -> unit string for axis labels
            title: Plot title
            height: Plot height in pixels
            
        Returns:
            Plotly figure or None
        """
        if self.df.empty:
            return None
        
        # Get plot group configs
        plot_groups_config = config.get('plot_groups', {})
        y_axes_config = config.get('y_axes', {})
        
        # Determine which groups go on which axis
        primary_groups = []
        secondary_groups = []
        
        for group_name in categories.keys():
            group_config = plot_groups_config.get(group_name, {})
            y_axis = group_config.get('y_axis', 'primary')
            
            if y_axis == 'secondary':
                secondary_groups.append(group_name)
            else:
                primary_groups.append(group_name)
        
        # Calculate y-axis ranges with zero alignment
        primary_range = self._calculate_axis_range(categories, primary_groups)
        secondary_range = self._calculate_axis_range(categories, secondary_groups)
        
        # Align zero points if configured
        if y_axes_config.get('secondary', {}).get('align_zero', False):
            primary_range, secondary_range = self._align_zero_axes(
                primary_range, secondary_range
            )
        
        # Create figure
        fig = go.Figure()
        
        # Track which series have been added for legend management
        legend_added = set()
        
        # Add traces for each category
        for group_name, columns in categories.items():
            group_config = plot_groups_config.get(group_name, {})
            plot_type = group_config.get('plot_type', 'bar')
            y_axis = 'y2' if group_config.get('y_axis') == 'secondary' else 'y'
            
            for col in columns:
                if col not in self.df.columns:
                    continue
                
                # Get color (from config or auto-generate)
                color = group_config.get('color', None)
                
                # Add trace based on plot type
                if plot_type == 'bar':
                    fig.add_trace(go.Bar(
                        name=col,
                        x=self.df[time_col],
                        y=self.df[col],
                        marker_line_width=0,
                        opacity=group_config.get('opacity', 0.85),
                        marker_color=color,
                        yaxis=y_axis,
                        showlegend=col not in legend_added
                    ))
                    legend_added.add(col)
                    
                elif plot_type == 'area':
                    # Sum all columns in this group for area fill
                    if group_name not in legend_added:
                        y_values = self.df[columns].sum(axis=1)
                        
                        fig.add_trace(go.Scatter(
                            name=f"{group_name.replace('_', ' ').title()}",
                            x=self.df[time_col],
                            y=y_values,
                            mode='lines',
                            fill=group_config.get('fill', 'tozeroy'),
                            line=dict(width=group_config.get('line_width', 0)),
                            fillcolor=group_config.get('fillcolor', 'rgba(128,128,128,0.2)'),
                            opacity=group_config.get('opacity', 1.0),
                            yaxis=y_axis,
                            showlegend=True
                        ))
                        legend_added.add(group_name)
                    
                elif plot_type == 'line':
                    line_config = {
                        'width': group_config.get('width', 1)
                    }
                    
                    if group_config.get('dash'):
                        line_config['dash'] = group_config['dash']
                    if color:
                        line_config['color'] = color
                    
                    fig.add_trace(go.Scatter(
                        name=col,
                        x=self.df[time_col],
                        y=self.df[col],
                        mode='lines',
                        line=line_config,
                        yaxis=y_axis,
                        showlegend=col not in legend_added
                    ))
                    legend_added.add(col)
        
        # Build axis titles with units
        primary_title = y_axes_config.get('primary', {}).get('title', 'Value')
        secondary_title = y_axes_config.get('secondary', {}).get('title', 'Secondary Value')
        
        # Append units to titles
        primary_units = [unit_info.get(g, '') for g in primary_groups if g in unit_info]
        secondary_units = [unit_info.get(g, '') for g in secondary_groups if g in unit_info]
        
        if primary_units:
            primary_title += f" [{', '.join(filter(None, primary_units))}]"
        if secondary_units:
            secondary_title += f" [{', '.join(filter(None, secondary_units))}]"
        
        # Update layout
        fig.update_layout(
            barmode='relative',  # Allows positive and negative stacking
            width=1400,
            height=height,
            title=title,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.15,
                xanchor="center",
                x=0.5,
                font=dict(size=11)
            ),
            xaxis=dict(
                title='Time',
                tickfont=dict(size=10)
            ),
            yaxis=dict(
                title=primary_title,
                side=y_axes_config.get('primary', {}).get('side', 'left'),
                showgrid=y_axes_config.get('primary', {}).get('showgrid', False),
                tickfont=dict(size=11),
                range=primary_range
            ),
            margin=dict(t=90, b=120, l=60, r=60)
        )
        
        # Add secondary y-axis if needed
        if secondary_groups:
            fig.update_layout(
                yaxis2=dict(
                    title=secondary_title,
                    overlaying='y',
                    side=y_axes_config.get('secondary', {}).get('side', 'right'),
                    showgrid=y_axes_config.get('secondary', {}).get('showgrid', False),
                    tickfont=dict(size=11),
                    showticklabels=True,
                    range=secondary_range
                )
            )
        
        return fig
    
    def _calculate_axis_range(
        self,
        categories: Dict[str, List[str]],
        groups: List[str]
    ) -> List[float]:
        """Calculate appropriate axis range for given groups."""
        if not groups:
            return [0, 1]
        
        # Get all columns for these groups
        cols = []
        for group in groups:
            if group in categories:
                cols.extend(categories[group])
        
        if not cols:
            return [0, 1]
        
        # Filter to existing columns
        cols = [c for c in cols if c in self.df.columns]
        
        if not cols:
            return [0, 1]
        
        # Calculate min and max
        values = self.df[cols].values.flatten()
        values = values[~pd.isna(values)]
        
        if len(values) == 0:
            return [0, 1]
        
        min_val = values.min()
        max_val = values.max()
        
        # Add buffer
        buffer = 0.05 * (max_val - min_val) if max_val != min_val else 0.1
        
        return [min_val - buffer, max_val + buffer]
    
    def _align_zero_axes(
        self,
        primary_range: List[float],
        secondary_range: List[float]
    ) -> tuple:
        """Align zero points between primary and secondary y-axes."""
        primary_min, primary_max = primary_range
        sec_min, sec_max = secondary_range
        
        # Avoid zero-divide
        if primary_min == 0 or primary_max == 0:
            return primary_range, secondary_range
        
        # Compute positive:negative ratio for primary
        ratio = abs(primary_max) / abs(primary_min) if abs(primary_min) > 0 else 1
        
        # For secondary axis, expand min/max so the ratio matches
        sec_max_abs = max(abs(sec_max), abs(sec_min))
        sec_min_aligned = -sec_max_abs / ratio if ratio != 0 else sec_min
        sec_max_aligned = sec_max_abs
        
        return primary_range, [sec_min_aligned, sec_max_aligned]