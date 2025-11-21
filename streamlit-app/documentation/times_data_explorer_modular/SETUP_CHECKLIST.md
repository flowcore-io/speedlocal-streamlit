# Setup Checklist for Modular TIMES Data Explorer

## ✅ Pre-Setup Checklist

Before you begin, ensure you have:

- [ ] Your existing `utils/` directory with:
  - [ ] `_connection_functions.py`
  - [ ] `_plotting.py`
  - [ ] `_query_dynamic.py`
  - [ ] `_query_with_csv.py`
  - [ ] `_streamlit_ui.py`
  - [ ] `settings.py`

- [ ] Your `inputs/mapping_db_views.csv` file
- [ ] Database connection (Azure URL or local DuckDB file)
- [ ] Python 3.8+ installed
- [ ] Required packages: `streamlit`, `pandas`, `plotly`, `duckdb`

## 📦 Step 1: Extract the Package

```bash
# Extract the tarball
tar -xzf times_refactored_complete.tar.gz

# Navigate to the directory
cd refactored_app
```

## 📁 Step 2: Copy Your Files

```bash
# Copy your existing utils directory
cp -r /path/to/your/existing/utils ./utils

# Copy your mapping CSV
mkdir -p inputs
cp /path/to/your/mapping_db_views.csv ./inputs/

# (Optional) Copy images for Key Insights module
mkdir -p images
cp /path/to/your/speed-local.jpg ./images/
cp /path/to/your/map.png ./images/
```

## 🔍 Step 3: Verify File Structure

```bash
# Check that everything is in place
ls -la

# Should see:
# main.py
# config/
# core/
# modules/
# components/
# utils/           ← Your copied files
# inputs/          ← Your mapping CSV
# images/          ← (Optional) Your images
```

## 🐍 Step 4: Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install streamlit pandas plotly duckdb

# Or if you have a requirements.txt:
pip install -r requirements.txt
```

## 🚀 Step 5: Run the Application

```bash
# Start Streamlit
streamlit run main.py

# The app should open in your browser at http://localhost:8501
```

## ✅ Step 6: Verify Functionality

### 6.1 Database Connection
- [ ] Open the application in your browser
- [ ] Check sidebar shows "Database Connection"
- [ ] Enter your database URL or file path
- [ ] Click "🔄 Reload Data"
- [ ] Verify "✓ Loaded X tables successfully" message

### 6.2 Global Filters
- [ ] Check sidebar shows "Global Filters"
- [ ] Verify "Scenarios" filter appears
- [ ] Select/deselect scenarios
- [ ] Verify changes are reflected in visualizations

### 6.3 Key Insights Tab
- [ ] First tab should be "Key Insights"
- [ ] Check "Key Modelling Insights" header appears
- [ ] Expand "🔍 Filter Debug Information"
- [ ] Verify active filters are shown
- [ ] Check placeholder metrics appear
- [ ] Verify project images display (if added)

### 6.4 Energy & Emissions Tab
- [ ] Second tab should be "Energy & Emissions"
- [ ] Check sub-tabs "⚡ Energy" and "🌍 Emissions" appear

#### Energy Sub-tab
- [ ] "Aggregate Energy Plot (All Sectors)" appears
- [ ] Sector multiselect works
- [ ] Stacked bar chart displays
- [ ] "Disaggregated Energy Plots per Sector" appears
- [ ] Sector expanders work
- [ ] Per-sector plots display correctly

#### Emissions Sub-tab
- [ ] "Aggregate Emissions Plot (All Sectors)" appears
- [ ] Sector multiselect works
- [ ] Line chart displays
- [ ] "Disaggregated Emission Plots per Sector" appears
- [ ] Sector expanders work
- [ ] Per-sector plots display correctly

## 🐛 Troubleshooting

### Problem: Import Errors

**Symptom:** `ModuleNotFoundError: No module named 'utils'`

**Solution:**
```bash
# Verify utils directory exists
ls -la utils/

# Check Python path
python -c "import sys; print(sys.path)"
```

### Problem: Database Connection Fails

**Symptom:** "Error connecting to database"

**Solutions:**
1. Check database URL/path is correct
2. If using Azure URL, verify it hasn't expired
3. Check network connectivity
4. Try local file path instead

### Problem: No Data Loads

**Symptom:** "No data was loaded from the database"

**Solutions:**
1. Verify `mapping_db_views.csv` path is correct
2. Check mapping CSV has correct format
3. Verify database contains expected tables
4. Check Streamlit logs for detailed error messages

### Problem: Plots Don't Display

**Symptom:** Charts are missing or show "No data"

**Solutions:**
1. Check filters - may have filtered out all data
2. Reset filters by clicking "Clear All Filters"
3. Verify data table exists and has data
4. Check Streamlit console for errors

### Problem: Module Not Appearing

**Symptom:** Key Insights or Energy/Emissions tab missing

**Solutions:**
1. Check `config/module_registry.py`
2. Verify module is registered in `_register_default_modules()`
3. Verify module `enabled = True`
4. Restart Streamlit

## 📝 Post-Setup Tasks

### Immediate
- [ ] Test with different scenarios
- [ ] Verify all existing functionality works
- [ ] Check performance with your full dataset
- [ ] Bookmark the application URL

### Optional Enhancements
- [ ] Customize Key Insights with actual KPIs
- [ ] Add your organization's logo
- [ ] Modify color schemes in plotting functions
- [ ] Add custom metrics or calculations

### Future Development
- [ ] Plan Land Use module implementation
- [ ] Plan Economics module implementation
- [ ] Plan DAYNITE module implementation
- [ ] Consider adding configuration files

## 📚 Reference Documentation

Quick links to documentation:

1. **README.md** - Quick start and overview
2. **MIGRATION_GUIDE.md** - Detailed implementation guide
3. **IMPLEMENTATION_SUMMARY.md** - High-level summary
4. **streamlit_modular_architecture.md** - Full architecture design

## 🎉 Success!

If all checklist items are complete, congratulations! Your modular TIMES Data Explorer is now running.

## 📧 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review the documentation files
3. Check Streamlit logs in the console
4. Verify all files are in correct locations

---

**Last Updated:** November 2025  
**Version:** 1.0
