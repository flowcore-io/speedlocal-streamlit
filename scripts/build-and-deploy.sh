#!/bin/bash

# Build and Deploy Script for Speed Local Streamlit
# This script builds the Docker image and pushes it to ECR

set -e

# Configuration
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-"305363105399"}
AWS_REGION=${AWS_REGION:-"eu-west-1"}
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
IMAGE_REPO=${IMAGE_REPO:-"speedlocal/streamlit-app"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Building and deploying Speed Local Streamlit${NC}"
echo -e "${YELLOW}Configuration:${NC}"
echo -e "  ECR Registry: ${ECR_REGISTRY}"
echo -e "  Image Repo: ${IMAGE_REPO}"
echo -e "  Image Tag: ${IMAGE_TAG}"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Login to ECR
echo -e "${YELLOW}🔑 Logging in to ECR...${NC}"
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}

# Create ECR repository if it doesn't exist
echo -e "${YELLOW}📦 Ensuring ECR repository exists...${NC}"
aws ecr describe-repositories --repository-names ${IMAGE_REPO} 2>/dev/null || {
    echo -e "${YELLOW}Creating ECR repository: ${IMAGE_REPO}${NC}"
    aws ecr create-repository --repository-name ${IMAGE_REPO}
}

# Build Docker image
echo -e "${YELLOW}🔨 Building Docker image...${NC}"
cd streamlit-app
docker build -t ${ECR_REGISTRY}/${IMAGE_REPO}:${IMAGE_TAG} .

# Push to ECR
echo -e "${YELLOW}⬆️  Pushing image to ECR...${NC}"
docker push ${ECR_REGISTRY}/${IMAGE_REPO}:${IMAGE_TAG}

echo -e "${GREEN}✅ Build and deployment completed successfully!${NC}"
echo -e "${GREEN}Image: ${ECR_REGISTRY}/${IMAGE_REPO}:${IMAGE_TAG}${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Update the image tag in helm-chart/environments/<environment>.yaml"
echo -e "2. Commit and push changes to trigger ArgoCD deployment"
echo -e "3. Monitor deployment status in ArgoCD dashboard"