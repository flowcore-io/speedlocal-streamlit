import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Optional, Dict, List, Union

class TimesReportPlotter:
    """
    Generic plotting class using pre-loaded DataFrames, but dynamically
    validates filters/grouping columns using DuckDBQueryHelper.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        query_helper: Optional["DuckDBQueryHelper"] = None
    ):
        """
        Args:
            df: DataFrame from PandasDFCreator
            query_helper: DuckDBQueryHelper instance (optional) to dynamically validate filters
        """
        if df.empty:
            raise ValueError("DataFrame is empty.")
        self.df = df.copy()
        self.query_helper = query_helper
        self.color_maps = {}

    def _get_color_map(self, group_col: str) -> Dict[str, str]:
        groups = sorted(self.df[group_col].unique())
        if group_col not in self.color_maps:
            colors = px.colors.qualitative.Set3[:len(groups)]
            self.color_maps[group_col] = dict(zip(groups, colors))
        return self.color_maps[group_col]

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
            yaxis_title=y_col,
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
            yaxis_title=y_col,
            height=height
        )
        return fig
