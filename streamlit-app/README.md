# Speed Local Analytics Hub

A comprehensive scientific data visualization and analysis platform for Nordic green transition research, built with individual Streamlit applications to avoid dependency conflicts.

## 🚀 Quick Start

### Launch the Main Hub

```bash
cd /Users/julius/git/flowcore/speedlocal-streamlit/streamlit-app
python -m streamlit run landing_page.py --server.port 8501
```

Visit: **http://localhost:8501**

### Launch Individual Tools

Each analysis tool runs as a separate Streamlit app to avoid pybind11 conflicts:

#### 📊 TIMES Data Explorer
```bash
python -m streamlit run apps/times_explorer.py --server.port 8502
```
Visit: **http://localhost:8502**

#### 🌍 Energy Flow Maps
```bash
python -m streamlit run apps/energy_flow_maps.py --server.port 8504
```
Visit: **http://localhost:8504**

#### 📈 Sankey Diagrams
```bash
python -m streamlit run apps/sankey_diagrams.py --server.port 8503
```
Visit: **http://localhost:8503**

#### 🛠️ Database Tools
```bash
python -m streamlit run apps/database_tools.py --server.port 8505
```
Visit: **http://localhost:8505**

## 🏗️ Architecture

### New Structure (Separate Apps)
```
streamlit-app/
├── landing_page.py          # Main navigation hub
├── apps/                    # Individual Streamlit apps
│   ├── times_explorer.py
│   ├── energy_flow_maps.py
│   ├── sankey_diagrams.py
│   └── database_tools.py
└── app/                     # Original structure (legacy)
    ├── main.py
    ├── pages/
    └── utils/
```

### Benefits

✅ **Conflict-Free**: Each app runs in isolation, avoiding pybind11 type registration conflicts  
✅ **Independent**: Run only the tools you need  
✅ **Resource Efficient**: Lower memory usage per app  
✅ **Stable**: No crashes from conflicting C++ extensions  
✅ **Scalable**: Easy to add new tools without affecting existing ones  

## 🛡️ Problem Solved

The original multipage Streamlit app suffered from **pybind11 type registration conflicts** when multiple pages imported different C++ extension packages (folium, geopy, streamlit-folium, duckdb) simultaneously on macOS ARM64 with Python 3.13.

### The Issue
```python
# This caused crashes when multiple pages were loaded:
import folium
import streamlit_folium  
import geopy
import duckdb
# RuntimeError: pybind11::detail::type_info already registered
```

### The Solution
Each app now imports dependencies only when needed and runs in complete isolation:

```python
# Energy Flow Maps app only loads its dependencies
def create_flow_map():
    import folium  # Lazy import
    from folium.plugins import AntPath
    # ... rest of function
    
def display_map():
    from streamlit_folium import st_folium  # Lazy import when displaying
    # ... rest of function
```

## 🎯 Features

### 📊 TIMES Data Explorer
- Advanced sector-based energy and emission analysis
- Multi-scenario comparison capabilities
- Interactive charts with filtering
- Azure blob storage integration

### 🌍 Energy Flow Maps  
- Interactive geospatial energy flow visualization
- Animated flow pathways with direction indicators
- Real-time geocoding of region names
- Bidirectional flow detection

### 📈 Sankey Diagrams
- Interactive Plotly-based energy flow diagrams
- Node categorization with color coding
- Flow aggregation and threshold filtering
- Export-ready visualizations

### 🛠️ Database Tools
- Comprehensive schema exploration
- SQL query interface with templates
- Automated data analysis
- Quick chart generator

## 🔧 Technical Details

### Dependencies
- **Core**: streamlit, pandas, numpy, plotly
- **Database**: duckdb (with lazy import fixes)
- **Geospatial**: folium, streamlit-folium, geopy (with lazy imports)
- **Visualization**: plotly.express, plotly.graph_objects

### Lazy Import Strategy
Critical packages are imported only when their functions are called:

```python
# ❌ Global import (causes conflicts)
import folium
from streamlit_folium import st_folium

# ✅ Lazy import (conflict-free)
def create_map():
    import folium  # Import only when needed
    # ... use folium

def display_map():
    from streamlit_folium import st_folium  # Import only when displaying
    # ... use st_folium
```

## 🐛 Troubleshooting

### App Won't Start
```bash
# Install/upgrade Streamlit
python -m pip install --upgrade streamlit

# Check Python version (3.8+ required)
python --version
```

### Port Already in Use
```bash
# Use different port
python -m streamlit run landing_page.py --server.port 8502

# Or find and kill existing process
lsof -i :8501
kill -9 <PID>
```

### Missing Dependencies
```bash
# Install common dependencies
python -m pip install streamlit pandas numpy plotly duckdb folium streamlit-folium geopy
```

## 📚 Usage Guide

1. **Start with the Landing Page**: Launch `landing_page.py` for navigation
2. **Click Tool Blocks**: Each tool shows terminal commands to launch
3. **Run Commands**: Copy/paste the provided terminal commands
4. **Access Tools**: Visit the localhost URLs for each tool
5. **Multiple Tools**: Run several tools simultaneously on different ports

## 🔄 Migration from Original

The original `app/main.py` with multipage structure is preserved but deprecated. The new separate app structure is recommended for stability.

### Original (Deprecated)
```bash
python -m streamlit run app/main.py  # May crash due to conflicts
```

### New (Recommended)  
```bash
python -m streamlit run landing_page.py  # Stable navigation hub
```

## 🏠 Development

To add a new analysis tool:

1. Create `apps/new_tool.py` following the existing pattern
2. Add navigation back to hub: `"🏠 Back to Analytics Hub"` button
3. Update `landing_page.py` with new navigation block
4. Use lazy imports for problematic dependencies
5. Include comprehensive feature documentation

## 🌱 About Speed Local

Speed Local is a platform for scientists to share and analyze GAMS reports and scientific datasets for Nordic green transition research, powered by Flowcore Infrastructure.