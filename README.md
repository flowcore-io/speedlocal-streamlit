# Speed Local Streamlit Analytics

🚀 **A comprehensive multi-page Streamlit application for analyzing TIMES energy system data with advanced visualization capabilities including geospatial mapping, Sankey diagrams, and interactive database tools.**

This repository contains a sophisticated analytics dashboard for visualizing and analyzing energy system data from the Speed Local project, which focuses on Nordic green transition research through trans-Nordic collaboration.

## 🌟 Features

### 📊 TIMES Data Explorer
- **Interactive scenario analysis** with sector-based energy and emissions visualization
- **Dynamic filtering** by scenario, year, and sector
- **Comparative analysis** between different energy scenarios
- **Stacked bar charts** for energy inputs by sector
- **Line charts** for emissions trends over time

### 🌍 Energy Flow Maps  
- **Interactive geospatial visualization** of energy flows between regions
- **Folium-based maps** with zoom, pan, and interactive features
- **Automated geocoding** for region coordinates
- **Flow magnitude visualization** with proportional line thickness
- **Color-coded flows**: Blue (exports), Red (imports), Green (bidirectional)
- **Animated pathways** showing energy flow directions

### 📊 Sankey Diagrams
- **Comprehensive energy flow analysis** with Plotly Sankey charts
- **Multi-type flow visualization**: Production, Consumption, Transmission, Import/Export
- **Node categorization** with color-coding for technologies, demands, and regions
- **Interactive filtering** with flow threshold controls
- **Statistical analysis** with flow breakdowns and top flows ranking

### 🛠️ Database Tools
- **Schema Explorer**: Browse database structure with table and column information
- **SQL Query Interface**: Execute custom queries with safety controls and templates
- **Automated Data Analysis**: Quick metrics and statistical summaries
- **Quick Chart Generator**: Build custom visualizations from SQL results
- **Data Export**: Download query results and analysis data

## 📁 Repository Structure

```
speedlocal-streamlit/
├── streamlit-app/                        # Streamlit application code
│   ├── app/
│   │   ├── main.py                       # Main dashboard and landing page
│   │   ├── pages/
│   │   │   ├── 1_📊_TIMES_Data_Explorer.py   # Advanced TIMES data analysis
│   │   │   ├── 2_🌍_Energy_Flow_Maps.py      # Geospatial energy flow visualization  
│   │   │   ├── 3_📊_Sankey_Diagrams.py       # Energy flow Sankey charts
│   │   │   └── 4_🛠️_Database_Tools.py        # Database management utilities
│   │   └── utils/
│   │       ├── database.py               # Database connection and utilities
│   │       └── geo_settings.py           # Geographic constants and settings
│   ├── assets/                           # Static assets
│   ├── tests/                            # Application tests
│   ├── requirements.txt                  # Python dependencies
│   └── Dockerfile                        # Container image definition
├── helm-chart/                           # Kubernetes deployment manifests
│   ├── values.yaml                       # Base Helm values
│   └── configuration/                    # Environment-specific configs (ArgoCD compatible)
│       └── production.yaml
└── README.md                             # This file
```

## 🎯 Project Overview

The Speed Local project provides a platform where scientists can:
- Upload GAMS reports and scientific datasets
- Process data into reusable flat structures
- Create shareable DuckDB files by combining datasets
- Collaborate on Nordic green transition research

This multi-page Streamlit application provides comprehensive visualization and analysis capabilities for TIMES energy system data, including:
- **Advanced data exploration** with interactive filtering and comparative analysis
- **Geospatial visualization** of energy flows between regions
- **Sankey diagrams** for comprehensive energy flow analysis
- **Database management tools** for direct data access and custom queries

## 🚀 Quick Start

### Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/flowcore-io/speedlocal-streamlit.git
   cd speedlocal-streamlit
   ```

2. **Set up Python environment**:
   ```bash
   cd streamlit-app
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   streamlit run app/main.py
   ```

4. **Open in browser**:
   Navigate to `http://localhost:8501`

### Docker Development

1. **Build the Docker image**:
   ```bash
   cd streamlit-app
   docker build -t speedlocal-streamlit .
   ```

2. **Run the container**:
   ```bash
   docker run -p 8501:8501 speedlocal-streamlit
   ```

## 🚢 Deployment

This application is designed to deploy on Flowcore's Kubernetes infrastructure using the `flowcore-microservices` Helm chart.

### Building and Pushing to ECR

```bash
# Set your AWS configuration
AWS_ACCOUNT_ID=305363105399
AWS_REGION=eu-west-1
ECR_REGISTRY=${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
IMAGE_REPO=speedlocal/streamlit-app
IMAGE_TAG=v1.0.0

# Login to ECR
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}

# Create repository if it doesn't exist
aws ecr describe-repositories --repository-names ${IMAGE_REPO} || aws ecr create-repository --repository-name ${IMAGE_REPO}

# Build and push
cd streamlit-app
docker build -t ${ECR_REGISTRY}/${IMAGE_REPO}:${IMAGE_TAG} .
docker push ${ECR_REGISTRY}/${IMAGE_REPO}:${IMAGE_TAG}
```

### Kubernetes Deployment

The Helm configuration in `helm-chart/` is designed to be used with the `public-customer-sites-manifests` repository for ArgoCD deployment:

1. Copy the Helm values to the appropriate environment configuration
2. Update the image tag and hostname as needed
3. Commit and push to trigger ArgoCD deployment

### Environment URLs

- **Development**: `https://speedlocal-streamlit-dev.flowcore.app`
- **Production**: `https://speedlocal-streamlit.flowcore.app`

## 🛠 Technical Details

### Features

- **Multi-page Application**: Four specialized analysis pages for different use cases
- **Advanced Data Visualization**: Interactive charts, maps, and Sankey diagrams
- **Database Management**: Complete database exploration and query capabilities
- **Geospatial Analysis**: Interactive maps with energy flow visualization
- **Export Capabilities**: Download data and visualizations for further analysis
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Analysis**: Dynamic filtering and comparative scenario analysis

### Technology Stack

- **Frontend**: Streamlit 1.32+
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly, Folium for interactive charts and maps
- **Database**: DuckDB for efficient analytical queries
- **Geospatial**: GeoPy for geocoding and coordinate management
- **Container**: Python 3.11 slim Docker image
- **Deployment**: Kubernetes with NGINX Ingress
- **Infrastructure**: Flowcore Kubernetes platform

## 💾 Database Connection

The application supports two database connection methods:

### Local DuckDB Files
- Place your `.duckdb` file in an accessible location
- Use the "Local File" connection option
- Enter the full path to your database file

### Azure Blob Storage
- Generate a SAS URL for your DuckDB file in Azure Storage
- Use the "Azure URL" connection option
- Enable local caching for improved performance
- URLs are automatically validated for expiry

## 📋 Data Requirements

The application expects a DuckDB database with a `timesreport_facts` table containing:

### Required Columns:
- `scen`: Scenario identifier
- `year`: Year of the data point
- `reg`: Region identifier  
- `prc`: Process/technology identifier
- `com`: Commodity/fuel type
- `attr`: Attribute type (f_in, f_out, etc.)
- `topic`: Data topic (energy, emissions, etc.)
- `value`: Numerical value
- `regfrom`, `regto`: For transmission flows

### Data Types Supported:
- **Energy flows**: Production, consumption, imports, exports, transmission
- **Emissions data**: By sector and technology
- **Regional data**: Multi-region energy systems
- **Temporal data**: Multi-year scenario analysis

## 🎛️ Usage Guide

### 1. Connect to Database
- Use the sidebar connection panel on any page
- Select connection type (Local File or Azure URL)
- Test connection to verify data access

### 2. TIMES Data Explorer
- Select scenario, year, and sector filters
- Generate energy input visualizations by sector
- Compare emissions trends across scenarios
- Export data for further analysis

### 3. Energy Flow Maps  
- Configure scenario, year, and fuel filters
- Generate interactive maps showing regional energy flows
- Explore flow statistics and regional connections
- Use geographic markers and flow animations

### 4. Sankey Diagrams
- Set scenario, year, and optional region filters
- Adjust flow threshold to focus on major pathways
- Analyze flow types and energy transformation chains
- Export flow summaries and detailed data

### 5. Database Tools
- **Schema Explorer**: Navigate database structure
- **SQL Query**: Execute custom analysis queries
- **Data Analysis**: Get automated insights
- **Quick Charts**: Build custom visualizations

### Health Checks

Streamlit automatically exposes a health check endpoint at `/_stcore/health` which is used by Kubernetes probes.

## 🔗 Integration

This dashboard integrates with:
- **Speed Local Admin** (`speedlocal.flowcore.app`) - Main data management platform
- **Flowcore Platform** - Event-driven data processing
- **Azure Blob Storage** - File storage and retrieval
- **DuckDB Files** - Public dataset access

## 🌱 About Speed Local

Speed Local is part of the broader initiative to accelerate Nordic green transition through trans-Nordic collaboration. The project enables scientists to:

- Share high-quality scientific datasets
- Collaborate on research across Nordic countries
- Provide transparent access to green transition data
- Support evidence-based policy making

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

For support and questions, please contact the Flowcore team.
Speed Local Streamlit dashboard for scientific data visualization and analysis
