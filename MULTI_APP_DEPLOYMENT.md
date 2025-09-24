# Multi-App Streamlit Deployment Guide

This guide explains how to deploy the TIMES Energy Analytics platform as multiple separate Streamlit applications with path-based routing using Kubernetes and Helm.

## 🏗️ Architecture Overview

The platform consists of four standalone Streamlit applications:

- **TIMES Data Explorer** (`/times`) - Data exploration and filtering
- **Energy Flow Maps** (`/flowmaps`) - Geographic energy flow visualization  
- **Sankey Diagrams** (`/sankey`) - Energy flow pathway diagrams
- **Database Tools** (`/database`) - SQL query interface and database exploration

Each app runs as a separate deployment with its own resources, scaling independently while sharing a common ingress with path-based routing.

## 🔧 Container Configuration

### Docker Build
The existing Docker image supports multiple entry points:

```dockerfile
# The Dockerfile has been updated to support variable commands
ENTRYPOINT ["python", "-m", "streamlit", "run"]
CMD ["app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Entry Point Scripts
Each app has its own entry point script:
- `times_app.py` - TIMES Data Explorer
- `flow_maps_app.py` - Energy Flow Maps 
- `sankey_app.py` - Sankey Diagrams
- `database_app.py` - Database Tools

## 📦 Deployment Options

### Multi-App Deployment

Deploy all apps as separate services with path-based routing:

```bash
# Deploy with production configuration (multi-app architecture)
helm upgrade --install speedlocal-streamlit ./helm-chart \
  -f helm-chart/configuration/production.yaml \
  --namespace your-namespace
```

**Features:**
- ✅ Independent scaling per app
- ✅ Resource isolation
- ✅ Path-based routing (`/times`, `/flowmaps`, etc.)
- ✅ WebSocket support for each app
- ✅ Sticky sessions per path
- ✅ Lazy loading prevents import conflicts

**URLs:**
- `https://speedlocal-streamlit.customer.flowcore.io/times`
- `https://speedlocal-streamlit.customer.flowcore.io/flowmaps`
- `https://speedlocal-streamlit.customer.flowcore.io/sankey`
- `https://speedlocal-streamlit.customer.flowcore.io/database`


## ⚙️ Multi-App Configuration Details

### Service Configuration

Each app deployment is configured with:

```yaml
timesApp:
  enabled: true
  deployment:
    image: speedlocal/streamlit-app
    command: ["python", "-m", "streamlit", "run"]
    args: ["times_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
    replicas: 2
    resources:
      requests: 
        memory: "512Mi"
        cpu: "500m"
      limits:   
        memory: "2Gi"
        cpu: "2"
```

### Ingress Configuration

The custom ingress provides path-based routing with NGINX Inc controller:

```yaml
# Path rewriting to remove app prefixes
nginx.org/rewrites: |
  serviceName=times-app rewrite=/times/(.*) /$1;
  serviceName=flow-maps-app rewrite=/flowmaps/(.*) /$1;
  # ... other rewrites

# WebSocket support for all services
nginx.org/websocket-services: "times-app,flow-maps-app,sankey-app,database-app"

# Sticky sessions per path
nginx.org/sticky-cookie-services: |
  times-app route expires=1h path=/times
  flow-maps-app route expires=1h path=/flowmaps
  # ... other sessions
```

## 🚀 Deployment Steps

### 1. Build and Push Docker Image

```bash
# Build the image with multi-app support
cd streamlit-app
docker build -t speedlocal/streamlit-app:latest .

# Tag and push to ECR
docker tag speedlocal/streamlit-app:latest 305363105399.dkr.ecr.eu-west-1.amazonaws.com/speedlocal/streamlit-app:latest
docker push 305363105399.dkr.ecr.eu-west-1.amazonaws.com/speedlocal/streamlit-app:latest
```

### 2. Deploy with Helm

```bash
# Update Helm dependencies
cd helm-chart
helm dependency update

# Deploy production configuration (multi-app architecture)
helm upgrade --install speedlocal-streamlit . \
  -f configuration/production.yaml \
  --namespace speedlocal \
  --create-namespace
```

### 3. Verify Deployment

```bash
# Check deployment status
kubectl get deployments -n speedlocal
kubectl get services -n speedlocal  
kubectl get ingress -n speedlocal

# Check pods
kubectl get pods -n speedlocal -l component=ui

# Check logs for each app
kubectl logs -l app.kubernetes.io/name=times-app -n speedlocal
kubectl logs -l app.kubernetes.io/name=flow-maps-app -n speedlocal
```

## 📊 Resource Requirements

### Per-App Resources

| App | Memory Request | Memory Limit | CPU Request | CPU Limit | Notes |
|-----|----------------|--------------|-------------|-----------|-------|
| TIMES Explorer | 512Mi | 2Gi | 500m | 2 | Data-intensive queries |
| Flow Maps | 1Gi | 3Gi | 500m | 2 | Geospatial processing |
| Sankey Diagrams | 1Gi | 3Gi | 500m | 2 | Complex visualizations |
| Database Tools | 512Mi | 2Gi | 500m | 2 | SQL processing |

### Total Cluster Resources (2 replicas each)

- **Memory**: ~6Gi requests, ~20Gi limits
- **CPU**: ~4 cores requests, ~16 cores limits
- **Pods**: 8 total (2 per app)

## 🔍 Monitoring and Troubleshooting

### Health Checks

All apps use Streamlit's built-in health endpoint:
- **Readiness**: `/_stcore/health` (30s initial delay)
- **Liveness**: `/_stcore/health` (60s initial delay)

### Common Issues

1. **Import Conflicts**: Resolved by lazy imports in each page module
2. **Memory Issues**: Adjust resources based on usage patterns
3. **WebSocket Issues**: Ensure sticky sessions and proper annotations
4. **Path Routing**: Check ingress rewrite rules

### Debugging Commands

```bash
# Check ingress configuration
kubectl describe ingress speedlocal-streamlit-multi-app -n speedlocal

# View NGINX config (if accessible)
kubectl exec -it <nginx-controller-pod> -- cat /etc/nginx/conf.d/default.conf

# Port forward for direct access
kubectl port-forward svc/times-app 8501:8501 -n speedlocal
```

## 🔄 Rolling Updates

Update individual apps without affecting others:

```bash
# Update specific app image
helm upgrade speedlocal-streamlit . \
  -f configuration/production.yaml \
  --set flowcore-microservices.deployments.timesApp.deployment.tag=v1.2.3 \
  --namespace speedlocal
```

## 📈 Scaling

Scale individual apps based on usage:

```bash
# Scale Flow Maps app for high geographic processing demand  
helm upgrade speedlocal-streamlit . \
  -f configuration/multi-app.yaml \
  --set flowcore-microservices.deployments.flowMapsApp.deployment.replicas=4 \
  --namespace speedlocal
```

## 🔐 Security Considerations

- All apps run as non-root user (10001:10001)
- Read-only root filesystem enabled
- Network policies can isolate apps
- RBAC controls deployment permissions
- TLS termination at ingress level

## 🎯 Benefits of Multi-App Architecture

### ✅ Advantages
- **Independent Scaling**: Scale each app based on usage
- **Resource Isolation**: Memory/CPU issues in one app don't affect others
- **Deployment Flexibility**: Update/rollback individual apps
- **Clear Separation**: Each app has distinct responsibilities
- **Better Caching**: App-specific caching strategies
- **Import Safety**: Lazy imports prevent C++ extension conflicts

### ⚠️ Considerations  
- **Increased Complexity**: More services to manage
- **Resource Overhead**: Each app has baseline resource usage
- **Session Management**: Users need separate sessions per app
- **Shared State**: No shared state between apps (by design)

## 📚 Related Documentation

- [Main README](README.md) - Project overview and development setup
- [Docker Configuration](streamlit-app/Dockerfile) - Container build details
- [Helm Chart Values](helm-chart/values.yaml) - Full configuration options
- [Production Config](helm-chart/configuration/production.yaml) - Single-app deployment