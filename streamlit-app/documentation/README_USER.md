# TIMES Data Explorer - User Guide

An interactive web application for exploring and visualizing TIMES energy model results stored in DuckDB databases.

---

## 🚀 Quick Launch

Assuming you are in `streamlit-app/`

### Option 1: One-Click Launch

**First Time Setup:**
```batch
# Double-click this file:
launch_app.bat
```
This will automatically:
- ✅ Create a virtual environment
- ✅ Install all dependencies
- ✅ Launch the app in your browser

**Subsequent Launches:**
```batch
# Use the faster simple launcher:
launch_app_simple.bat
```

### Option 2: Manual Launch (For Python Users)

**Setup (first time only):**
```bash
# Install dependencies
pip install -r requirements.txt
```

**Launch:**
```bash
# Run Streamlit
streamlit run main.py
```

The app will automatically open in your browser at `http://localhost:8501`

---

#### 📋 Prerequisites

- Python 3.8 or higher
- Internet connection (for connecting to database from Azure URL)
- Modern web browser (Chrome, Firefox, Edge, Safari)

---

## ⚙️ Configuration

### Required Input Files

Check these files in the `inputs/` folder:

| File | Purpose |
|------|---------|
| `mapping_db_views.csv` | Defines how database tables are queried and labeled |
| `unit_conversions.csv` | Defines unit conversion rules (e.g., kt → t, PJ → GJ) |

### Configuration Files


| File | Purpose |
|------|---------|
| `config/default_units.yaml` | Default target units for each category (mass, energy, currency) |
| `config/module_registry.py` | Where the existing modules are registered and set to active or inactive |
| `modules/subannual/config/profile_config.yaml` | Subannual module visualization settings |
| `modules/energy_map/config/map_settings.yaml` | Map module display settings (zoom, colors, line styles) |
| `modules/energy_map/config/region_coordinates.yaml` | Geographic coordinates for regional mapping |

---

### Database Connection

Configure in the **sidebar** when you launch the app:

1. **Connection Type:**
   - **Azure URL** (default): Connect to cloud-hosted database
   - **Local File**: Use a database file on your computer

2. **Database Source:**
   - Azure URL: `https://speedlocal.flowcore.app/api/duckdb/share/...`
   - Local path: `inputs/your_database.duckdb`

3. **Mapping CSV Path:**
   - Default: `inputs/mapping_db_views.csv`

---

## 📊 Modules Overview

### 1. Key Insights
**Purpose:** Executive dashboard with high-level project information

---

### 2. Energy & Emissions
**Purpose:** Annual energy and emissions reporting

**Features:**
- **Energy Input Analysis:**
  - Aggregate view across all sectors
  - Disaggregated view per sector
  - Stacked bar charts by fuel type (comgroup)
  
- **Emissions Analysis:**
  - Aggregate emissions by sector
  - Disaggregated emissions by commodity
  - Line charts showing trends

---

### 3. Energy Flow Map
**Purpose:** Visualize regional energy flows on interactive maps

**Features:**
- Interactive Folium maps
- Bidirectional flow visualization
- Animated flow paths (AntPath)
- Regional markers with NUTS coding
- Flow aggregation by fuel type

---

### 4. Subannual Profile
**Purpose:** analysis with subannual temporal resolution

**Features:**
- Stacked bar charts by specified group (techgroup, prc, com, comgroup, etc)
- timeslice group selector (ex. filter by weeks)
- Production visualization (price, consumption, and storage coming soon)

---

### 5. 🔧 Development
**Purpose:** Debugging and testing tools for developers, Troubleshoot data issues and explore database structure

**Features:**
- Filter debugging information
- Description table viewer
- Data inspector with column analysis
- Profile mapping generator (for configuration)

---

## 🔄 Unit Conversion

The app supports automatic unit conversion for multiple categories:

| Category | Example Units | Default |
|----------|---------------|---------|
| **Energy** | PJ, GJ, TJ, MWh | GJ |
| **Mass** | kt, t, Mt | t |
| **Currency** | MKr25, Kr25 | MKr25 |
| **Length** | km, m | km |
| **Area** | KHA, ha | KHA |
| **Volume** | MM3, m³ | MM3 |

**Note:** Rows with unknown or unconvertible units are filtered out. Check the exclusion summary to see what was removed.

---

## 🐛 Troubleshooting

### App won't start
**Problem:** "streamlit is not recognized as a command"
**Solution:** 
- Delete the `venv` folder
- Run `launch_app.bat` again
- Or manually: `pip install -r requirements.txt`

### No data appears
**Problem:** Database connection failed or tables are empty
**Solution:**
- Check the Azure URL hasn't expired
- Verify `mapping_db_views.csv` exists in `inputs/`
- Click "🔄 Reload Data" in the sidebar

### Unit conversion issues
**Problem:** All data disappears after enabling unit conversion
**Solution:**
- Check if your data has the correct `unit` and `cur` columns
- Review the exclusion summary to see what was filtered out
- Verify `unit_conversions.csv` has the necessary conversion rules

### Map not displaying
**Problem:** Map is blank or regions not found
**Solution:**
- Check `region_coordinates.yaml` has coordinates for your regions, maybe some regions are not automatically read and have to be hardcoded
- Verify the needed table exists in your database

---

## 📚 Additional Resources

- **Architecture Diagrams:** See `documentation/architecture_simple.png` and `architecture_detailed.png`
- **Developer Documentation:** See `README_DEVELOPER.md`
- **TIMES Model Documentation:** [IEA-ETSAP](https://iea-etsap.org/index.php/etsap-tools/model-generators/times)
- **TIMES Report Documentation:** [TIMESreport Documentation](https://github.com/Energy-Modelling-Lab/DemoS_012_timesreport/blob/master/README.md)
---

## 🎯 Quick Tips

💡 **Tip 1:** Always check unit conversion exclusions to understand what data is being filtered

💡 **Tip 2:** The Development module is useful for understanding data structure of queried tables through `mapping_db_views.csv`

💡 **Tip 3:** Azure URLs expire - download the database locally if you need offline access
