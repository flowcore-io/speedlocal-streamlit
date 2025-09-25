# Project Structure - Single-App Streamlit Architecture

## 📁 Current File Structure

```
speedlocal-streamlit/
├── streamlit-app/
│   ├── Dockerfile                     # Container configuration for single app
│   ├── README.md                      # App-specific documentation
│   ├── requirements.txt               # Python dependencies
│   ├── times_app.py                   # Main Streamlit entry point (TIMES Explorer)
│   ├── utils/
│   │   └── settings.py                # Geographic defaults and cached config values
│   └── images/
│       ├── speed-local.jpg            # Branding asset
│       └── map.png                    # Energy system reference map
├── helm-chart/
│   ├── Chart.yaml                     # Helm chart metadata
│   ├── values.yaml                    # Default single-app values (multi-app stubs disabled)
│   ├── configuration/
│   │   └── production.yaml            # Legacy multi-app overrides (pending cleanup)
│   └── templates/
│       └── custom-ingress.yaml        # Path-based ingress (unused for single-app)
├── scripts/
│   └── build-and-deploy.sh            # Helper for local ECR builds & pushes
├── docker-compose.yml                 # Local container orchestration (single service)
├── README.md                          # Repository overview
├── CHANGELOG.md                       # Release notes
└── TIMES_APP_MIGRATION.md             # Migration record for TIMES Explorer
```

## 🚀 Application Overview

- **Primary App**: `streamlit-app/times_app.py`
- **Runtime Command**: `python -m streamlit run times_app.py`
- **Core Capabilities**:
  - Azure Blob Storage downloader with smart caching & expiry detection
  - Local DuckDB support for offline analysis
  - Energy & emissions dashboards with Plotly visualisations
  - Scenario comparison controls in Streamlit sidebar
- **Supporting Assets**:
  - `utils/settings.py` supplies geographic defaults and cached selectors
  - `images/` directory hosts branding and map visuals referenced in the UI
  - `requirements.txt` pins Streamlit, DuckDB, pandas, Plotly, requests, etc.
  - `Dockerfile` builds a hardened image (non-root, health check) for deployment

## 🔧 Deployment Configuration

### Helm Deployment (Current Target)

- Enable only the `timesApp` deployment in `helm-chart/values.yaml` or environment-specific overrides
- Update the image tag under `flowcore-microservices.deployments.timesApp.deployment.tag`
- Ensure ingress remains disabled unless a dedicated hostname is configured
- Apply with:
  ```bash
  helm upgrade --install speedlocal-streamlit ./helm-chart --namespace speedlocal
  ```
- Legacy multi-app keys (`flowMapsApp`, `sankeyApp`, `databaseApp`) remain in `values.yaml` and `configuration/production.yaml` for historical reference but should stay disabled.

### Resource Recommendations

- Replicas: 2 (scales horizontally via Helm values)
- CPU: requests `500m`, limits `2`
- Memory: requests `512Mi`, limits `2Gi`
- Port: 8501
- Liveness/Readiness: `/_stcore/health`

## 🛠️ Development Workflows

- **Local (Streamlit CLI)**
  ```bash
  cd streamlit-app
  pip install -r requirements.txt
  streamlit run times_app.py --server.port=8501
  ```
- **Docker**
  ```bash
  cd streamlit-app
  docker build -t times-explorer .
  docker run -p 8501:8501 times-explorer
  ```
- **Docker Compose (repo root)**
  ```bash
  docker compose up --build
  ```
- **Manual Build & Push**
  ```bash
  ./scripts/build-and-deploy.sh
  ```

## 🧹 Cleanup & Legacy Artifacts

- Removed router-based modules and duplicate standalone apps (`flow_maps_app.py`, `sankey_app.py`, `database_app.py`, legacy `app/` tree)
- Consolidated documentation into this file, `README.md`, and `TIMES_APP_MIGRATION.md`
- Retained `configuration/production.yaml` to preserve historical multi-app settings pending formal retirement

## 🔐 Security & Observability

- Containers run as non-root user `10001` with optional read-only filesystem
- Health checks are wired to Streamlit's `/_stcore/health` endpoint
- TLS terminates at ingress; enable `customIngress` only when dedicated hostname is available
- Caching is handled within Streamlit; no persistent volumes required
- Secrets management via `flowcore-secret-requester` remains disabled by default

## 🔄 CI/CD Workflow Summary

- GitHub Actions workflow (`.github/workflows/streamlit-cicd.yml`) builds the image from `streamlit-app` and pushes to Amazon ECR (`speedlocal/streamlit-app`)
- Step to update multi-app tags in `configuration/production.yaml` remains for backwards compatibility but is considered legacy behaviour
- Commits are pushed automatically when Helm values change after a release

## 🎯 Next Steps

1. Confirm `timesApp` is the only enabled deployment across environments
2. Deprecate or remove unused multi-app configuration once no longer required
3. Monitor production metrics and adjust resource requests as usage grows
4. Add observability hooks (logging/metrics) as needed for long-term operations
5. Document any environment-specific secrets or overrides in `README.md`

## 💡 Benefits of the Single-App Focus

- ✅ Simplified deployment pipeline with one image and one Helm release path
- ✅ Reduced maintenance burden by eliminating duplicate code paths
- ✅ Clear documentation for developers and operators
- ✅ Smaller attack surface and easier security hardening
- ✅ Streamlined troubleshooting with a single source of truth