# RAG QA Foundation - Docker Deployment Guide

This repository contains optimized Dockerfiles for deploying the RAG QA Foundation application, with special focus on Vercel deployment with size constraints.

## Dockerfile Options

### 1. `Dockerfile` - Standard Production Build
- Based on Python 3.12 slim
- Multi-stage build for optimization
- Includes health checks and security best practices
- Target size: ~300-400MB

### 2. `Dockerfile.vercel` - Vercel Optimized
- Uses distroless base image for minimal size
- Optimized for Vercel's container deployment
- Target size: ~200-250MB

### 3. `Dockerfile.alpine` - Ultra Minimal
- Alpine Linux base for smallest possible size
- Target size: ~150-200MB
- Best for size-constrained deployments

## Vercel Deployment

### Prerequisites
1. Install Vercel CLI: `npm i -g vercel`
2. Login to Vercel: `vercel login`

### Deployment Steps

```bash
# 1. Build and test locally (optional)
docker build -f Dockerfile.vercel -t rag-qa-app .
docker run -p 8000:8000 rag-qa-app

# 2. Deploy to Vercel
vercel --docker

# Or use specific Dockerfile
vercel --docker --build-arg DOCKERFILE=Dockerfile.alpine
```

### Environment Variables
Set these in your Vercel dashboard:

```
GOOGLE_API_KEY=your_gemini_api_key
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

## Size Optimization Techniques Used

1. **Multi-stage builds** - Separate build and runtime environments
2. **uv package manager** - Faster and more efficient than pip
3. **Minimal base images** - Alpine Linux and distroless images
4. **Dependency optimization** - Only production dependencies
5. **Layer caching** - Optimized layer ordering
6. **Dockerignore** - Exclude unnecessary files

## Build Commands

```bash
# Standard build
docker build -t rag-qa-app .

# Vercel optimized build
docker build -f Dockerfile.vercel -t rag-qa-app-vercel .

# Alpine minimal build
docker build -f Dockerfile.alpine -t rag-qa-app-alpine .

# Check image size
docker images | grep rag-qa-app
```

## Performance Tips

1. **External Vector Store**: For production, consider moving vector store to external storage (S3, etc.)
2. **Model Caching**: Cache Google Gemini responses when appropriate
3. **Memory Limits**: Set appropriate memory limits for containers
4. **Workers**: Use single worker for Vercel (memory constraints)

## Troubleshooting

### Image Too Large
- Use `Dockerfile.alpine` for smallest size
- Remove unnecessary data files
- Consider external storage for large assets

### Deployment Fails
- Check environment variables are set
- Verify port configuration (Vercel assigns ports dynamically)
- Check logs: `vercel logs`

### Performance Issues
- Monitor memory usage
- Consider upgrading Vercel plan for more resources
- Optimize vector store size
