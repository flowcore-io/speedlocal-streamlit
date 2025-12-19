# TIMES Data Explorer - Developer Guide

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![DuckDB](https://img.shields.io/badge/DuckDB-FFF000?style=flat&logo=duckdb&logoColor=black)](https://duckdb.org/)

Technical documentation for developers working on the TIMES Data Explorer application.

---

## 📐 Architecture Overview

![Architecture Diagram](architecture_simple.png)

The application follows a modular architecture with three main layers:

1. **Input Layer:** Database, CSV configs, YAML settings
2. **Processing Layer:** Data loading, filtering, unit conversion
3. **Visualization Layer:** Modular components for different analyses

See `architecture_detailed.png` for complete class and method diagrams.

---

## 📁 Repository Structure

```
times-data-explorer/
│
├── main.py                      # Application entry point
├── launch_app.bat              # Windows launcher script
├── launch_app_simple.bat       # Fast launcher (after setup)
├── requirements.txt            # Python dependencies
│
├── config/                     # Application configuration
│   ├── default_units.yaml     # Default target units per category
│   └── module_registry.py     # Module registration system
│
├── core/                       # Core management systems
│   ├── session_manager.py     # Streamlit session state wrapper
│   ├── data_loader.py         # Database loading orchestration
│   ├── filter_manager.py      # Filter UI and logic
│   └── unit_manager.py        # Unit conversion controls
│
├── components/                 # UI components
│   └── sidebar.py             # Database connection sidebar
│
├── modules/                    # Visualization modules
│   ├── base_module.py         # Abstract base class
│   ├── key_insights/          # Executive dashboard
│   ├── energy_emissions/      # Energy & emissions analysis
│   ├── energy_map/            # Regional flow maps
│   ├── subannual/             # subannual profiles
│   └── development/           # Debug & testing tools
│
├── utils/                      # Utility functions
│   ├── _connection_functions.py   # DuckDB connection
│   ├── _query_with_csv.py        # SQL query builder
│   ├── _query_dynamic.py         # Dynamic query helpers
│   ├── unit_converter.py         # Unit conversion logic
│   └── _plotting.py              # Plotly chart creation
│
└── inputs/                     # User data
    ├── mapping_db_views.csv   # Table definitions
    └── unit_conversions.csv   # Conversion rules
```

---

## 🏗️ Creating a New Module

### Step 1: Choose Your Base Class

**BaseModule** - For simple modules without standardized data flow:
```python
from modules.base_module import BaseModule

class MyModule(BaseModule):
    def __init__(self):
        super().__init__(
            name="My Module",
            description="What this module does",
            order=10,  # Display order
            enabled=True
        )
```

**BaseVisualizationModule** - For modules with standard data processing:
```python
from modules.base_module import BaseVisualizationModule

class MyVizModule(BaseVisualizationModule):
    # Inherits standard render() flow:
    # 1. Validate data
    # 2. Render unit controls
    # 3. Load & prepare data
    # 4. Apply filters
    # 5. Apply unit conversion
    # 6. Render visualization
```

### Step 2: Implement Required Methods

```python
def get_required_tables(self) -> list:
    """Return list of table names this module needs."""
    return ["energy", "emissions"]

def get_config(self) -> Dict[str, Any]:
    """Return module configuration."""
    return {
        "apply_global_filters": True,      # Use sidebar scenario filters?
        "apply_unit_conversion": True,     # Show unit controls?
        "show_module_filters": True,       # Show additional filters?
        "filterable_columns": ['sector', 'year'],  # Available filter columns
        "default_columns": ['sector']      # Pre-selected filters
    }

def render(self, table_dfs: Dict[str, pd.DataFrame], filters: Dict[str, Any]) -> None:
    """Main render method - create your UI here."""
    st.header("My Module")
    # Your visualization code here
```

### Step 3: Implement BaseVisualizationModule Methods (if using)

```python
def _load_and_prepare_data(self, table_dfs: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Load and prepare data for visualization.
    
    - Get required tables
    - Combine/transform data
    - Apply description mappings
    - Return single DataFrame
    """
    df = table_dfs.get("my_table")
    
    # Apply descriptions
    desc_mapping = self._get_desc_mapping()
    df = self._apply_descriptions(df, ['sector', 'com'], desc_mapping)
    
    return df

def _render_visualization(self, df: pd.DataFrame, filters: Dict[str, Any]) -> None:
    """
    Render the actual visualization.
    
    At this point:
    - Data is loaded
    - Filters are applied
    - Units are converted
    
    Just create your plots!
    """
    st.subheader("My Visualization")
    
    # Create plots using TimesReportPlotter
    from utils._plotting import TimesReportPlotter
    plotter = TimesReportPlotter(df)
    
    plot_spec = {
        'x_col': 'year',
        'y_col': 'value',
        'series': [{'group_col': 'sector', 'type': 'bar', 'stack': True}],
        'axes': {'primary': {'title': self._get_unit_label(df)}},
        'title': 'My Chart'
    }
    
    fig = plotter.create_figure(plot_spec)
    st.plotly_chart(fig, use_container_width=True)
```

### Step 4: Register Your Module

Edit `config/module_registry.py`:

```python
from modules.my_module.module import MyModule

class ModuleRegistry:
    def _register_default_modules(self) -> None:
        # ... existing modules ...
        
        # Add your module
        self.register_module("my_module", MyModule())
```

### Step 5: Test Your Module

1. You can check tables in Development module
2. Check filters and unit conversion
3. Check exclusion tracking for converted data (any loose units not defined yet and not converted)
4. Verify plots render correctly

---

## 🎨 Module Configuration Reference

### `get_config()` Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `apply_global_filters` | bool | True | Use global scenario filters from sidebar |
| `apply_unit_conversion` | bool | False | Show unit conversion controls in module |
| `show_module_filters` | bool | False | Show expandable filter section |
| `filterable_columns` | list | [] | Columns available for filtering |
| `default_columns` | list | [] | Pre-selected filter columns on load |

### Example Configurations

**Minimal Module (no filters, no conversion):**
```python
{
    "apply_global_filters": False,
    "apply_unit_conversion": False,
    "show_module_filters": False,
    "filterable_columns": [],
    "default_columns": []
}
```

**Example Analysis Module:**
```python
{
    "apply_global_filters": True,
    "apply_unit_conversion": True,
    "show_module_filters": True,
    "filterable_columns": ['sector', 'subsector', 'year'],
    "default_columns": ['sector']
}
```

---

## 🔌 Data Loading System

### Data Flow

```
mapping_db_views.csv → PandasDFCreator → DuckDB → DataFrames
                                              ↓
                                    DataLoaderManager
                                              ↓
                          SessionManager (st.session_state)
                                              ↓
                                          Modules
```

### mapping_db_views.csv Structure

| Column | Purpose | Example |
|--------|---------|---------|
| `table` | Output table name | `energy` |
| `label` | Column for labeling | `techgroup` |
| `sector` | Filter by sector | `TRA` or `TRA,IND` |
| `attr` | Filter by attribute | `f_in` |
| `aggregation` | Post-query grouping | `label, all_ts` |

**Filter Syntax:**
- **Exact match:** `TRA`
- **Multiple values:** `TRA,IND,AGR`
- **Wildcard:** `EXP*` (matches EXPELEDZ, EXPELCZ, etc.)
- **Regex:** `^EXP.*` (starts with EXP)
- **Negation:** `!DMZ` (exclude DMZ)

### Adding a New Table Definition

```csv
table,label,sector,topic,attr,aggregation
my_new_table,techgroup,TRA,energy,f_in,"label, year"
```

This creates a table called `my_new_table` with:
- Labels from `techgroup` column
- Filtered to transport sector
- Only energy topic
- Only `f_in` attribute
- Aggregated by label and year

Note: you can leave the aggregation column blank if you don't need automatic aggregation

---

## 🔄 Unit Conversion System

### Architecture

```
unit_conversions.csv → UnitConverter → UnitManager → Modules
                            ↓
                      ExclusionInfo (tracking)
```

### Adding New Unit Conversions

Edit `inputs/unit_conversions.csv`:

```csv
unit_long,from_unit,to_unit,factor,category
megawatt hour,MWh,GJ,3.6,energy
terawatt hour,TWh,GJ,3600000,energy
```
Note: this system is not scalable (adding new units) so this might be changed.

### Changing Default Units

Edit `config/default_units.yaml`:

```yaml
default_units:
  mass: "t"
  energy: "GJ"
  currency: "MKr25"
  new_category: "new_unit"
```

### Unit Conversion in Modules

The `BaseVisualizationModule` handles this automatically. For `BaseModule`:

```python
# In render() method
unit_config = self._render_unit_controls(table_dfs, filters)
if unit_config:
    filters['unit_config'] = unit_config

# Later, after filtering
df_converted = self._apply_unit_conversion(df, filters)
```

---

## 📊 Plotting System

### Using TimesReportPlotter

```python
from utils._plotting import TimesReportPlotter

plotter = TimesReportPlotter(df)
fig = plotter.create_figure(plot_spec)
st.plotly_chart(fig, use_container_width=True)
```

### Plot Specification Structure

```python
plot_spec = {
    'x_col': 'year',              # X-axis column
    'y_col': 'value',             # Y-axis column (or None for multi-column)
    'scenario_col': 'scen',       # Optional scenario grouping
    
    'series': [                   # List of series to plot
        {
            'group_col': 'sector',    # Column to group by
            'type': 'bar',            # 'bar', 'line', 'area'
            'stack': True,            # Stack bars?
            'y_axis': 'primary',      # 'primary' or 'secondary'
            'opacity': 0.85
        }
    ],
    
    'axes': {
        'primary': {
            'title': 'Energy [GJ]',
            'side': 'left',
            'showgrid': False
        },
        'secondary': {              # Optional
            'title': 'Price [Kr25]',
            'side': 'right',
            'overlaying': 'y',
            'showgrid': False
        }
    },
    
    'title': 'My Chart',
    'height': 600,
    'barmode': 'stack',          # 'stack', 'group', 'relative'
    'xaxis_type': 'linear'       # 'linear', 'category'
}
```

### Multi-Series Example

```python
plot_spec = {
    'x_col': 'all_ts',
    'y_col': None,  # Using explicit columns
    'series': [
        {
            'columns': ['Tech1', 'Tech2', 'Tech3'],  # Explicit columns
            'type': 'bar',
            'stack': True,
            'y_axis': 'primary'
        },
        {
            'columns': ['Price'],
            'type': 'line',
            'y_axis': 'secondary',
            'color': 'black',
            'dash': 'dash'
        }
    ],
    # ... rest of spec
}
```

---

## 🗺️ Map Rendering

### FlowMapRenderer

Located in `modules/energy_map/map_renderer.py`

**Configuration Files:**
- `map_settings.yaml` - Visual settings (zoom, colors, line width)
- `region_coordinates.yaml` - Pre-defined coordinates if it can't be geocoded

**Adding New Regions:**

```yaml
# region_coordinates.yaml
special_regions:
  MyRegion:
    lat: 55.123
    lon: 14.456
```

**Flow Data Requirements:**

DataFrame must have columns: `start`, `end`, `value`, `unit`

```python
flow_data = pd.DataFrame({
    'start': ['RegionA', 'RegionB'],
    'end': ['RegionB', 'RegionC'],
    'value': [100, 200],
    'unit': ['GJ', 'GJ']
})

folium_map = map_renderer.create_flow_map(flow_data)
```

---

## 🧪 Testing & Debugging

### Using the Development Module

1. **Filter Debug Tab:**
   - View active filters
   - See table row counts before/after filtering
   - Inspect data structure

2. **Description Tables Tab:**
   - Search description mappings
   - Verify label mappings are correct

3. **Data Inspector Tab:**
   - Examine column types and statistics
   - View sample data
   - Generate profile mapping templates

### Debug Output

```python
# In your module
st.write("DEBUG: DataFrame shape:", df.shape)
st.write("DEBUG: Columns:", df.columns.tolist())
st.write("DEBUG: Sample data:")
st.dataframe(df.head())

# Use expander for verbose output
with st.expander("🔍 Debug Info", expanded=False):
    st.json(filters)
    st.dataframe(df.describe())
```

### Common Debugging Patterns

**Check if data loaded:**
```python
if not self.validate_data(table_dfs):
    self.show_error("Required tables not available")
    return
```

**Track filtering steps:**
```python
st.write(f"Before filtering: {len(df)} rows")
df = self._apply_filters(df, filters)
st.write(f"After filtering: {len(df)} rows")
```

**Verify unit conversion:**
```python
df_converted, exclusion_info = converter.convert_and_filter(df, ...)
if exclusion_info.has_exclusions():
    st.warning(exclusion_info.get_summary())
```

---

## 🐛 Troubleshooting Guide

### Database Connection Issues

**Problem:** "Failed to connect to database"

**Solutions:**
1. Check Azure URL hasn't expired (check `se` parameter in URL)
2. Try local file instead: download database and use local path
3. Check internet connection
4. Verify DuckDB file isn't corrupted: `duckdb database.duckdb "SHOW TABLES;"`

### Empty DataFrames

**Problem:** Module shows "No data available"

**Debug Steps:**
1. Check `mapping_db_views.csv` filters aren't too restrictive
2. Use Development module → Data Inspector to see raw data
3. Verify table exists in database: `SHOW TABLES;`
4. Check aggregation specification isn't grouping everything away

### Unit Conversion Filtering Everything

**Problem:** All data disappears after enabling unit conversion

**Solutions:**
1. Check exclusion summary for details
2. Verify `unit` and `cur` columns exist in data
3. Add missing conversion rules to `unit_conversions.csv`
4. Check if units are spelled correctly (case-sensitive)

### Plotting Issues

**Problem:** "No data to plot" or blank charts

**Debug Steps:**
```python
# Check data before plotting
st.write("Data shape:", df.shape)
st.write("Unique x values:", df['year'].unique())
st.write("Unique groups:", df['sector'].unique())
st.write("Value range:", df['value'].min(), "-", df['value'].max())
```

### Performance Issues

**Problem:** App is slow or unresponsive

**Solutions:**
1. Reduce data size with stricter filters in `mapping_db_views.csv`
2. Use aggregation column to pre-aggregate data
3. Limit scenarios selected in global filters
4. Cache expensive operations:
   ```python
   @st.cache_data
   def expensive_operation(data):
       return result
   ```

### Session State Issues

**Problem:** Filters or settings not persisting

**Solutions:**
1. Use unique keys for widgets: `key=f"{module_name}_filter_year"`
2. Check session state keys: `SessionManager().get_all_keys()`
3. Clear session state if corrupted: Click "🔄 Reload Data" in sidebar

---

## 🔧 Advanced Customization

### Custom Description Mapping

Override label mapping in your module:

```python
def _load_and_prepare_data(self, table_dfs):
    df = table_dfs.get("my_table")
    
    # Custom mapping
    custom_mapping = {
        'TRA': 'Transportation Sector',
        'IND': 'Industrial Sector'
    }
    
    df['sector_desc'] = df['sector'].map(custom_mapping).fillna(df['sector'])
    
    return df
```

### Dynamic Configuration

Change module configuration based on data:

```python
def get_config(self):
    # Check if certain tables exist
    table_dfs = st.session_state.get('table_dfs', {})
    
    has_subannual = 'energy_subannual' in table_dfs
    
    return {
        "apply_global_filters": True,
        "apply_unit_conversion": has_subannual,  # Only if subannual data
        "filterable_columns": ['year', 'all_ts'] if has_subannual else ['year']
    }
```

### Custom Unit Categories

Add new categories to the system:

1. Add conversions to `unit_conversions.csv`:
```csv
unit_long,from_unit,to_unit,factor,category
person,person,kperson,0.001,population
thousand persons,kperson,person,1000,population
```

2. Add default to `default_units.yaml`:
```yaml
default_units:
  population: "kperson"
```

3. Use in your module - it will automatically appear in unit controls

---

## 📚 Code Style Guidelines

### Naming Conventions

- **Classes:** `PascalCase` (e.g., `EnergyEmissionsModule`)
- **Functions/Methods:** `snake_case` (e.g., `render_visualization`)
- **Private methods:** `_snake_case` (e.g., `_apply_filters`)
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `EXCLUDED_SECTORS`)

### Documentation

Use docstrings for all public methods:

```python
def render_visualization(self, df: pd.DataFrame, filters: Dict[str, Any]) -> None:
    """
    Render the energy analysis visualization.
    
    Args:
        df: Prepared and filtered DataFrame with energy data
        filters: Active filter settings from FilterManager
        
    Returns:
        None - renders directly to Streamlit
        
    Notes:
        Expects df to have columns: year, sector, value, unit
    """
```

### Error Handling

Use the base class helper methods:

```python
if df.empty:
    self.show_warning("No data available for selected filters")
    return

try:
    fig = plotter.create_figure(plot_spec)
except Exception as e:
    self.show_error(f"Error creating plot: {str(e)}")
    st.exception(e)  # Show full traceback in debug mode

---

## 🔄 Version Control Best Practices

### What to Commit

✅ **DO commit:**
- All `.py` source files
- Configuration `.yaml` files (without sensitive data)
- Template `.csv` files (empty structure)
- `requirements.txt`
- Documentation files
- Launch scripts

❌ **DON'T commit:**
- `venv/` folder
- `__pycache__/` folders
- `.duckdb` database files
- User data in `inputs/` folder
- Streamlit cache (`.streamlit/cache/`)

---

Last updated: December 2024 (Merry Christmas :D )
