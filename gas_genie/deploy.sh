#!/bin/bash
set -e

# Variables
PROJECT_ID="your-project-id"  # Replace with your GCP project ID
SERVICE_NAME="gas-genie"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME:latest"

# Build with platform specification
docker buildx build --platform linux/amd64 -t $IMAGE_NAME .

# Push to Container Registry
gcloud auth configure-docker -q
docker push $IMAGE_NAME

# Deploy to Cloud Run with proper configuration
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars "FIREWORKS_API_KEY=your-fireworks-api-key,ETHERSCAN_API_KEY=your-etherscan-api-key" \
  --memory 1Gi \
  --cpu 1 