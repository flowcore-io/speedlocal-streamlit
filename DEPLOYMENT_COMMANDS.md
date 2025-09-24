# Quick Deployment Commands

## 🚀 Multi-App Deployment

### Deploy All Apps with Path Routing
```bash
cd helm-chart
helm dependency update
helm upgrade --install speedlocal-streamlit . \
  -f configuration/production.yaml \
  --namespace speedlocal \
  --create-namespace
```

### Verify Deployment
```bash
kubectl get all -n speedlocal
kubectl get ingress -n speedlocal
```

### Test Each App
```bash
# TIMES Data Explorer
curl -s https://speedlocal-streamlit.customer.flowcore.io/times/_stcore/health

# Energy Flow Maps  
curl -s https://speedlocal-streamlit.customer.flowcore.io/flowmaps/_stcore/health

# Sankey Diagrams
curl -s https://speedlocal-streamlit.customer.flowcore.io/sankey/_stcore/health

# Database Tools
curl -s https://speedlocal-streamlit.customer.flowcore.io/database/_stcore/health
```


## 🏗️ Docker Build & Push

```bash
cd streamlit-app

# Build image
docker build -t speedlocal/streamlit-app:latest .

# Tag for ECR
docker tag speedlocal/streamlit-app:latest \
  305363105399.dkr.ecr.eu-west-1.amazonaws.com/speedlocal/streamlit-app:latest

# Push to ECR (requires AWS CLI configured)
docker push 305363105399.dkr.ecr.eu-west-1.amazonaws.com/speedlocal/streamlit-app:latest
```

## 🔧 Local Testing

### Test Individual Apps Locally
```bash
cd streamlit-app

# TIMES Data Explorer
streamlit run times_app.py --server.port=8501

# Energy Flow Maps
streamlit run flow_maps_app.py --server.port=8502

# Sankey Diagrams  
streamlit run sankey_app.py --server.port=8503

# Database Tools
streamlit run database_app.py --server.port=8504
```

### Test with Docker
```bash
# TIMES Explorer
docker run -p 8501:8501 speedlocal/streamlit-app:latest times_app.py

# Flow Maps
docker run -p 8502:8501 speedlocal/streamlit-app:latest flow_maps_app.py

# Sankey
docker run -p 8503:8501 speedlocal/streamlit-app:latest sankey_app.py

# Database
docker run -p 8504:8501 speedlocal/streamlit-app:latest database_app.py
```

## 📊 Monitoring Commands

### Check Pod Status
```bash
kubectl get pods -n speedlocal -l component=ui
kubectl describe pods -n speedlocal -l app.kubernetes.io/name=times-app
```

### View Logs
```bash
kubectl logs -l app.kubernetes.io/name=times-app -n speedlocal --tail=100
kubectl logs -l app.kubernetes.io/name=flow-maps-app -n speedlocal --tail=100
kubectl logs -l app.kubernetes.io/name=sankey-app -n speedlocal --tail=100
kubectl logs -l app.kubernetes.io/name=database-app -n speedlocal --tail=100
```

### Port Forward for Debug
```bash
kubectl port-forward svc/times-app 8501:8501 -n speedlocal
kubectl port-forward svc/flow-maps-app 8502:8501 -n speedlocal
kubectl port-forward svc/sankey-app 8503:8501 -n speedlocal
kubectl port-forward svc/database-app 8504:8501 -n speedlocal
```

## ⚙️ Configuration Updates

### Scale Individual Apps
```bash
# Scale Flow Maps (resource intensive)
helm upgrade speedlocal-streamlit ./helm-chart \
  -f configuration/production.yaml \
  --set flowcore-microservices.deployments.flowMapsApp.deployment.replicas=4 \
  --namespace speedlocal

# Scale TIMES Explorer for high query load
helm upgrade speedlocal-streamlit ./helm-chart \
  -f configuration/production.yaml \
  --set flowcore-microservices.deployments.timesApp.deployment.replicas=3 \
  --namespace speedlocal
```

### Update Image Tag
```bash
helm upgrade speedlocal-streamlit ./helm-chart \
  -f configuration/production.yaml \
  --set flowcore-microservices.deployments.timesApp.deployment.tag=v1.2.3 \
  --namespace speedlocal
```

### Resource Adjustment
```bash
# Increase memory for Flow Maps
helm upgrade speedlocal-streamlit ./helm-chart \
  -f configuration/production.yaml \
  --set flowcore-microservices.deployments.flowMapsApp.deployment.resources.limits.memory=4Gi \
  --namespace speedlocal
```

## 🧹 Cleanup Commands

### Delete Multi-App Deployment
```bash
helm uninstall speedlocal-streamlit --namespace speedlocal
kubectl delete namespace speedlocal
```

### Delete Individual Resources
```bash
kubectl delete deployment times-app -n speedlocal
kubectl delete service times-app -n speedlocal
kubectl delete ingress speedlocal-streamlit-multi-app -n speedlocal
```

## 🔍 Troubleshooting

### Check Ingress Configuration
```bash
kubectl describe ingress speedlocal-streamlit-multi-app -n speedlocal
kubectl get ingress -n speedlocal -o yaml
```

### Restart Specific App
```bash
kubectl rollout restart deployment/times-app -n speedlocal
kubectl rollout restart deployment/flow-maps-app -n speedlocal
```

### Check Events
```bash
kubectl get events -n speedlocal --sort-by=.metadata.creationTimestamp
```