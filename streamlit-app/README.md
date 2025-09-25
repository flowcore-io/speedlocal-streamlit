# TIMES Data Explorer - Streamlit App

A Streamlit application for exploring TIMES energy model data with interactive visualizations for energy flows and emissions analysis.

## Features

- 🔗 **Flexible Database Connection**: Connect to local DuckDB files or Azure blob storage
- 💾 **Smart Caching**: Automatic caching of downloaded databases for faster access
- ⏰ **URL Expiry Detection**: Automatic detection of Azure URL expiration
- 📊 **Multi-scenario Comparison**: Compare different scenarios side by side
- 🎯 **Interactive Visualizations**: Energy and emission data with detailed hover information
- 🏭 **Sector Analysis**: Separate analysis for different energy sectors
- 🌱 **Emissions Tracking**: Comprehensive emissions visualization and trends

## Project Structure

```
streamlit-app/
├── times_app.py           # Main Streamlit application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── utils/
│   └── settings.py       # Geographic and settings data
├── images/
│   ├── speed-local.jpg   # Application branding
│   └── map.png          # Energy system map
└── README.md            # This documentation
```

## Quick Start

### Local Development

1. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:

   ```bash
   streamlit run times_app.py
   ```

3. **Access the App**:
   Open your browser to `http://localhost:8501`

### Docker Deployment

1. **Build the Image**:

   ```bash
   docker build -t times-explorer .
   ```

2. **Run the Container**:

   ```bash
   docker run -p 8501:8501 times-explorer
   ```

## Usage Guide

### Database Connection

The application supports two connection methods:

#### 1. Azure URL (Default)

- Pre-configured with default Azure blob storage URL
- Automatic expiry detection and warnings
- Smart caching (refreshes every 24 hours)
- Download progress indicator

#### 2. Local File

- Connect to local DuckDB files
- Useful for development and testing
- Default path: `./duckDB/speedlocal_times_db.duckdb`

### Navigation

The application provides three main tabs:

#### Energy Visualization

- **Sector-based Analysis**: View energy data by sector (excluding DMZ, SYS, DHT, ELT, TRD)
- **Commodity Groups**: Analyze different energy commodities
- **Scenario Comparison**: Compare multiple scenarios side-by-side
- **Interactive Charts**: Stacked bar charts with detailed hover information

#### Emissions Visualization  

- **Emission Types**: Track different emission categories
- **Trend Analysis**: Line charts showing emission trends over time
- **Multi-scenario Views**: Compare emission scenarios
- **Time Series**: Detailed temporal analysis

#### Development

- **System Images**: View energy system maps and branding
- **Testing Area**: Placeholder for new features

### Key Controls

- **Scenario Selection**: Multi-select dropdown in sidebar to choose scenarios
- **Database Info**: Expandable section showing database statistics
- **Cache Management**: Clear cache button for fresh downloads
- **Connection Status**: Real-time connection status indicators

## Database Schema

The application expects a DuckDB database with the following key tables:

- `timesreport_facts`: Main facts table with energy and emission data
- `sector_desc`: Sector descriptions and metadata
- `comgroup_desc`: Commodity group descriptions

### Expected Columns in `timesreport_facts`

- `year`: Year of the data
- `scen`: Scenario identifier
- `topic`: Data topic ('energy' or 'emission')
- `attr`: Attribute type ('f_in', 'f_out', etc.)
- `sector`: Sector identifier
- `comgroup`: Commodity group
- `value`: Numeric value
- `unit`: Unit of measurement

## Configuration

### Environment Variables

- `STREAMLIT_SERVER_PORT`: Server port (default: 8501)
- `STREAMLIT_SERVER_ADDRESS`: Server address (default: 0.0.0.0)

### Cache Settings

- **Location**: System temp directory / streamlit_duckdb_cache
- **Refresh**: Every 24 hours for Azure URLs
- **Manual**: Clear cache button in sidebar

## Dependencies

- **streamlit**: Web application framework
- **duckdb**: Database engine
- **pandas**: Data manipulation
- **plotly**: Interactive visualizations
- **requests**: HTTP client for Azure downloads

## Development

### Adding New Features

1. **New Visualizations**: Add functions following the pattern of `create_energy_plot()` and `create_emission_plot()`
2. **Database Queries**: Use parameterized queries for security
3. **Error Handling**: Wrap database operations in try-catch blocks
4. **Caching**: Use `@st.cache_data` for expensive operations

### Testing

```bash
# Syntax check
python -m py_compile times_app.py

# Run with test data
streamlit run times_app.py
```

## Performance Notes

- Database downloads are cached locally for 24 hours
- Large datasets may take time to load initially
- Interactive plots use Plotly for optimal performance
- Connection pooling is handled automatically by DuckDB

## Troubleshooting

### Common Issues

1. **Azure URL Expired**: Check the URL expiry date in the sidebar
2. **Database Not Found**: Verify the file path or URL
3. **No Data**: Check scenario and sector selections
4. **Slow Loading**: Clear cache to force fresh download

### Error Messages

- `Error connecting to database`: Check connection settings
- `No scenarios found`: Verify database schema
- `Access denied`: Azure URL may have expired or insufficient permissions
- `Download timed out`: Database file may be very large

## License

This project is part of the SpeedLocal platform by FlowCore.

## Support

For issues and questions, please contact the FlowCore development team.
