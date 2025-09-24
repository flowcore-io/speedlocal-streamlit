# CI/CD Workflow Validation Guide

## 🔧 Updated Workflow Overview

The CI/CD workflow has been updated to handle the multi-app architecture. When a release is published or manually triggered, it will:

1. **Build single Docker image** for all apps
2. **Push to ECR** with the release tag  
3. **Update ALL 4 app deployments** in `production.yaml`
4. **Commit and push** the changes automatically

## 📋 What Gets Updated

### Before (Single App):
```yaml
flowcore-microservices:
  deployments:
    speedlocalStreamlit:
      deployment:
        tag: "v0.2.3"  # Only this was updated
```

### After (Multi-App):
```yaml
flowcore-microservices:
  deployments:
    timesApp:
      deployment:
        tag: "v0.2.4"  # ✅ Updated
    flowMapsApp:
      deployment:
        tag: "v0.2.4"  # ✅ Updated  
    sankeyApp:
      deployment:
        tag: "v0.2.4"  # ✅ Updated
    databaseApp:
      deployment:
        tag: "v0.2.4"  # ✅ Updated
```

## 🧪 Testing the Workflow

### Option 1: Manual Workflow Dispatch
Test without creating an actual release:

1. Go to **Actions** tab in GitHub
2. Select **"Streamlit Build & Deploy (on Release)"**
3. Click **"Run workflow"**
4. Enter a test tag like `v0.2.4-test`
5. Monitor the workflow execution

### Option 2: Test Release
Create a test release to validate:

```bash
# Create and push a test tag
git tag v0.2.4-test
git push origin v0.2.4-test

# Create release from the tag in GitHub UI
# The workflow should automatically trigger
```

## ✅ Validation Checklist

After running the workflow, verify:

- [ ] **Docker Image**: Check ECR for new image with correct tag
- [ ] **Helm Values**: Verify all 4 apps have updated tags in `production.yaml`
- [ ] **Git Commit**: Check for automatic commit with message "fix(helm): 🚀 Update all app tags to vX.X.X"
- [ ] **Deployment**: If auto-deployed, check all pods are updated

### Expected Workflow Output:
```
✅ Build image 
✅ Push image to ECR
✅ Updated TIMES Explorer app to tag v0.2.4
✅ Updated Energy Flow Maps app to tag v0.2.4  
✅ Updated Sankey Diagrams app to tag v0.2.4
✅ Updated Database Tools app to tag v0.2.4
✅ Committed and pushed production.yaml with tag v0.2.4
```

## 🔍 Troubleshooting

### Common Issues:

1. **yq Command Fails**
   - Check the YAML path syntax in the workflow
   - Verify the deployment keys match production.yaml

2. **Git Push Fails**  
   - Ensure `FLOWCORE_MACHINE_GITHUB_TOKEN` has write permissions
   - Check if branch protection rules allow automated commits

3. **ECR Push Fails**
   - Verify AWS IAM role permissions
   - Check if ECR repository exists

### Manual Validation Commands:

```bash
# Test yq commands locally
yq '.flowcore-microservices.deployments.timesApp.deployment.tag = "v0.2.4"' helm-chart/configuration/production.yaml

# Check current tags in production.yaml
yq '.flowcore-microservices.deployments.*.deployment.tag' helm-chart/configuration/production.yaml

# Verify all apps have same tag after update
yq '.flowcore-microservices.deployments | to_entries | .[] | .key + ": " + .value.deployment.tag' helm-chart/configuration/production.yaml
```

## 📊 Expected Results

After a successful workflow run:

```bash
# All apps should have the same tag version
$ yq '.flowcore-microservices.deployments.*.deployment.tag' helm-chart/configuration/production.yaml
"v0.2.4"
"v0.2.4" 
"v0.2.4"
"v0.2.4"
```

## 🚨 Rollback Procedure

If something goes wrong:

```bash
# Revert the automated commit
git revert HEAD

# Or manually fix the production.yaml
yq -i '.flowcore-microservices.deployments.timesApp.deployment.tag = "v0.2.3"' helm-chart/configuration/production.yaml
yq -i '.flowcore-microservices.deployments.flowMapsApp.deployment.tag = "v0.2.3"' helm-chart/configuration/production.yaml
yq -i '.flowcore-microservices.deployments.sankeyApp.deployment.tag = "v0.2.3"' helm-chart/configuration/production.yaml
yq -i '.flowcore-microservices.deployments.databaseApp.deployment.tag = "v0.2.3"' helm-chart/configuration/production.yaml

# Commit and push the fix
git add helm-chart/configuration/production.yaml
git commit -m "fix(helm): Rollback to v0.2.3"
git push origin main
```

## 💡 Benefits of Updated Workflow

- ✅ **Atomic Updates**: All apps get updated together
- ✅ **Single Image**: One build serves all applications
- ✅ **Consistent Versions**: No version drift between apps
- ✅ **Automated**: No manual intervention required
- ✅ **Traceable**: Clear git history of version changes
- ✅ **Rollback Ready**: Easy to revert if needed