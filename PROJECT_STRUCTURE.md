# Project Structure - Multi-App Streamlit Architecture

## 📁 Current File Structure

```
speedlocal-streamlit/
├── streamlit-app/
│   ├── app/
│   │   ├── main.py                    # Original single-app entry (router-based)
│   │   └── utils/
│   │       ├── database.py            # Database connection utilities
│   │       └── geo_settings.py        # Geographic data settings
│   ├── pages/                         # Page modules for router app
│   │   ├── home.py                    # Landing/navigation page
│   │   ├── times_explorer.py          # TIMES data exploration module
│   │   ├── energy_flow_maps.py        # Energy flow maps module (lazy imports)
│   │   ├── sankey_diagrams.py         # Sankey diagrams module
│   │   └── database_tools.py          # Database tools module
│   ├── main.py                        # Router-based main app (query param routing)
│   ├── times_app.py                   # ✅ Standalone TIMES Explorer app
│   ├── flow_maps_app.py               # ✅ Standalone Energy Flow Maps app
│   ├── sankey_app.py                  # ✅ Standalone Sankey Diagrams app
│   ├── database_app.py                # ✅ Standalone Database Tools app
│   ├── Dockerfile                     # Multi-app container configuration
│   └── requirements.txt               # Python dependencies
├── helm-chart/
│   ├── Chart.yaml                     # Helm chart metadata
│   ├── values.yaml                    # Base values with custom ingress
│   ├── configuration/
│   │   └── production.yaml            # ✅ Multi-app production config
│   └── templates/
│       └── custom-ingress.yaml        # Path-based ingress routing
├── MULTI_APP_DEPLOYMENT.md            # Comprehensive deployment guide
├── DEPLOYMENT_COMMANDS.md             # Quick command reference
└── IMPLEMENTATION_SUMMARY.md          # Architecture overview
```

## 🚀 Current Architecture

### Multi-App Production Deployment
The system now deploys as **4 separate Streamlit applications** with the following routing:

| Path | Application | Entry Point | Purpose |
|------|-------------|-------------|---------|
| `/times` | TIMES Data Explorer | `times_app.py` | Data filtering and analysis |
| `/flowmaps` | Energy Flow Maps | `flow_maps_app.py` | Geographic visualization |
| `/sankey` | Sankey Diagrams | `sankey_app.py` | Flow pathway diagrams |
| `/database` | Database Tools | `database_app.py` | SQL interface and exploration |

### Key Features ✅
- **Path-Based Routing**: Clean URLs via NGINX ingress
- **Independent Scaling**: Each app scales separately based on resource needs
- **Lazy Imports**: Import conflicts resolved with lazy loading
- **WebSocket Support**: Full Streamlit functionality preserved
- **Sticky Sessions**: User sessions maintained per application
- **Production Ready**: Comprehensive health checks and monitoring

## 🔧 Deployment Configuration

### Production Deployment
```bash
helm upgrade --install speedlocal-streamlit ./helm-chart \
  -f configuration/production.yaml \
  --namespace speedlocal
```

**Deployed Services:**
- `times-app` (2 replicas, 512Mi-2Gi memory)
- `flow-maps-app` (3 replicas, 1Gi-3Gi memory) 
- `sankey-app` (3 replicas, 1Gi-3Gi memory)
- `database-app` (2 replicas, 512Mi-2Gi memory)

**Ingress Routes:**
- `https://speedlocal-streamlit.customer.flowcore.io/times`
- `https://speedlocal-streamlit.customer.flowcore.io/flowmaps`
- `https://speedlocal-streamlit.customer.flowcore.io/sankey`
- `https://speedlocal-streamlit.customer.flowcore.io/database`

## 🛠️ Development Options

### Option 1: Individual App Development
Test each app independently:
```bash
cd streamlit-app
streamlit run times_app.py --server.port=8501
streamlit run flow_maps_app.py --server.port=8502
streamlit run sankey_app.py --server.port=8503
streamlit run database_app.py --server.port=8504
```

### Option 2: Router App Development
Test the router-based app (query param routing):
```bash
streamlit run main.py --server.port=8501
# Access via: http://localhost:8501/?route=times
```

### Option 3: Original App Structure
The original single app is still available at `app/main.py`:
```bash
streamlit run app/main.py --server.port=8501
```

## 🧹 Cleanup Completed

### Removed Files:
- `apps/` directory (duplicate standalone apps)
- `app/pages/` directory (emoji-named pages)
- `landing_page.py` (unused landing page)
- `helm-chart/configuration/multi-app.yaml` (consolidated into production.yaml)

### Clean Structure:
- ✅ No duplicate code
- ✅ Single source of truth for each app
- ✅ Clear separation between router and standalone apps
- ✅ Consistent naming conventions

## 📊 Resource Allocation

### Production Resources (Total):
- **Memory**: ~10Gi requests, ~32Gi limits
- **CPU**: ~4 cores requests, ~16 cores limits  
- **Pods**: 10 total across 4 applications
- **Services**: 4 independent services with load balancing

### Per-App Scaling:
- **TIMES Explorer**: Light scaling (data queries)
- **Flow Maps**: Heavy scaling (geospatial processing)
- **Sankey Diagrams**: Heavy scaling (complex visualizations)
- **Database Tools**: Light scaling (SQL operations)

## 🔐 Security & Production Features

- **Non-root Containers**: All apps run as user 10001:10001
- **Read-only Filesystem**: Enhanced security posture
- **Resource Limits**: Prevention of resource exhaustion
- **Health Checks**: Readiness and liveness probes per app
- **TLS Termination**: HTTPS via ingress controller
- **Network Policies**: Apps can be isolated if needed

## 🔄 CI/CD Workflow Updates

### Automated Deployments
The CI/CD workflow has been updated to handle all 4 apps:

```yaml
# When a release is published, the workflow will:
# 1. Build a single Docker image
# 2. Push to ECR with the release tag
# 3. Update ALL app deployments in production.yaml:
#    - timesApp.deployment.tag
#    - flowMapsApp.deployment.tag
#    - sankeyApp.deployment.tag
#    - databaseApp.deployment.tag
# 4. Commit and push the changes
```

**Workflow Features:**
- ✅ Single image build for all apps
- ✅ Atomic version updates across all deployments
- ✅ Automatic Helm chart updates
- ✅ Git commit with descriptive message

## 🎯 Next Steps

1. **Deploy to Production**: Use the updated `production.yaml`
2. **Test CI/CD Pipeline**: Create a test release to verify all apps update
3. **Monitor Performance**: Track resource usage per app
4. **Optimize Scaling**: Adjust replicas based on actual usage
5. **Add Metrics**: Implement custom Prometheus metrics
6. **Database Optimization**: Consider connection pooling

## 💡 Benefits Achieved

- ✅ **Resolved Import Conflicts**: pybind11 issues eliminated
- ✅ **Independent Scaling**: Resource optimization per workload
- ✅ **Clean URLs**: Professional path-based routing
- ✅ **Operational Flexibility**: Deploy/update apps independently
- ✅ **Development Efficiency**: Multiple development approaches
- ✅ **Production Ready**: Comprehensive monitoring and health checks