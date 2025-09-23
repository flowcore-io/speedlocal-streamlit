# Speed Local Streamlit Dashboard

🚀 **Scientific data visualization and analysis dashboard for the Speed Local project**

This repository contains a Streamlit dashboard for visualizing and analyzing scientific datasets from the Speed Local project, which focuses on Nordic green transition research through trans-Nordic collaboration.

## 📁 Repository Structure

```
speedlocal-streamlit/
├── streamlit-app/          # Streamlit application code
│   ├── app/
│   │   ├── main.py         # Main dashboard application
│   │   └── pages/          # Additional pages (future)
│   ├── assets/             # Static assets
│   ├── tests/              # Application tests
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile          # Container image definition
├── helm-chart/             # Kubernetes deployment manifests
│   ├── values.yaml         # Base Helm values
│   └── environments/       # Environment-specific configs
│       ├── development.yaml
│       └── production.yaml
└── README.md               # This file
```

## 🎯 Project Overview

The Speed Local project provides a platform where scientists can:
- Upload GAMS reports and scientific datasets
- Process data into reusable flat structures
- Create shareable DuckDB files by combining datasets
- Collaborate on Nordic green transition research

This Streamlit dashboard provides visualization and analysis capabilities for the data managed through the Speed Local Admin platform.

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

- **Dashboard Overview**: Key metrics and usage statistics
- **Data Visualization**: Charts and graphs for dataset analysis
- **Quick Actions**: Integration points with Speed Local Admin
- **Activity Feed**: Recent activity and updates
- **Responsive Design**: Works on desktop and mobile devices

### Technology Stack

- **Frontend**: Streamlit 1.32+
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly (ready for integration)
- **Container**: Python 3.11 slim Docker image
- **Deployment**: Kubernetes with NGINX Ingress
- **Infrastructure**: Flowcore Kubernetes platform

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
