# AVIF Converter Kubernetes Deployment

## Overview
This service provides HEIC/JPEG to AVIF conversion with full and thumbnail variants.

## Deployment

### Prerequisites
- Kubernetes cluster with `webapps` namespace
- GitHub Container Registry access

### Automatic Deployment
The service automatically deploys to Kubernetes on every push to `main` branch via GitHub Actions.

### Manual Deployment
```bash
# Apply the deployment
kubectl apply -f k8s/deployment.yaml -n webapps

# Check deployment status
kubectl get pods -n webapps -l app=avif-converter
kubectl logs -f deployment/avif-converter -n webapps
```

### Service Configuration
- **Internal Service**: `avif-converter.webapps.svc.cluster.local:3002`
- **Health Check**: `/health`
- **Endpoints**: `/convert` (HEIC), `/convert-jpeg` (JPEG)

### Resource Requirements
- **Memory**: 256Mi request, 1Gi limit
- **CPU**: 200m request, 2000m limit
- **Replicas**: 2 (for load distribution)

### Environment Variables
- `MAX_FILE_SIZE`: Maximum file size in bytes (default: 50MB)
- `QUALITY`: AVIF quality setting (default: 80)

## Testing
```bash
# Port forward for local testing
kubectl port-forward svc/avif-converter 8000:3002 -n webapps

# Test health endpoint
curl http://localhost:8000/health

# Test conversion (replace with actual image file)
curl -X POST -F "file=@test.heic" http://localhost:8000/convert
```
