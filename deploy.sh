#!/bin/bash

# RAG QA Foundation - Multi-Platform Deployment Script

set -e

echo "🚀 RAG QA Foundation - Deployment Script"
echo "========================================="

# Deployment platform selection
echo "Select deployment platform:"
echo "1. Railway (Recommended for Docker - No size limits)"
echo "2. Google Cloud Run (Enterprise-grade)"
echo "3. Render (Simple Docker deployment)"
echo "4. Local Docker build only"
echo "5. Vercel Serverless (Limited - requires external vector store)"

read -p "Enter choice (1-5): " platform_choice

case $platform_choice in
    1)
        PLATFORM="railway"
        echo "🚂 Deploying to Railway"
        ;;
    2)
        PLATFORM="gcp"
        echo "☁️ Deploying to Google Cloud Run"
        ;;
    3)
        PLATFORM="render"
        echo "🎨 Setting up for Render deployment"
        ;;
    4)
        PLATFORM="local"
        echo "🏠 Building locally only"
        ;;
    5)
        PLATFORM="vercel"
        echo "⚡ Deploying to Vercel (Serverless)"
        ;;
    *)
        echo "❌ Invalid choice. Using Railway (recommended)"
        PLATFORM="railway"
        ;;
esac

# Dockerfile selection for Docker-based platforms
if [[ $PLATFORM != "vercel" ]]; then
    echo ""
    echo "Select Dockerfile for deployment:"
    echo "1. Dockerfile.vercel (Optimized - ~200-250MB)"
    echo "2. Dockerfile.alpine (Ultra minimal - ~150-200MB)"
    echo "3. Dockerfile (Standard production - ~300-400MB)"

    read -p "Enter choice (1-3): " choice

    case $choice in
        1)
            DOCKERFILE="Dockerfile.vercel"
            echo "📦 Using Vercel-optimized Dockerfile"
            ;;
        2)
            DOCKERFILE="Dockerfile.alpine"
            echo "📦 Using Alpine-based minimal Dockerfile"
            ;;
        3)
            DOCKERFILE="Dockerfile"
            echo "📦 Using standard production Dockerfile"
            ;;
        *)
            echo "❌ Invalid choice. Using default (Dockerfile.vercel)"
            DOCKERFILE="Dockerfile.vercel"
            ;;
    esac
fi

# Check if docker is running (for Docker-based deployments)
if [[ $PLATFORM != "vercel" ]] && ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Platform-specific deployment logic
case $PLATFORM in
    "railway")
        # Check if Railway CLI is installed
        if ! command -v railway &> /dev/null; then
            echo "❌ Railway CLI not found. Installing..."
            npm install -g @railway/cli
        fi
        
        # Check if logged in to Railway
        if ! railway whoami &> /dev/null; then
            echo "🔑 Please login to Railway..."
            railway login
        fi
        
        # Build locally first to check size
        echo "🔨 Building Docker image locally to check size..."
        docker build -f $DOCKERFILE -t rag-qa-test .
        
        # Check image size
        SIZE=$(docker images rag-qa-test --format "table {{.Size}}" | tail -n +2)
        echo "📏 Image size: $SIZE"
        
        # Clean up test image
        docker rmi rag-qa-test
        
        # Deploy to Railway
        echo "🚀 Deploying to Railway..."
        railway up
        ;;
        
    "gcp")
        # Check if gcloud is installed
        if ! command -v gcloud &> /dev/null; then
            echo "❌ Google Cloud CLI not found. Please install it first."
            echo "Visit: https://cloud.google.com/sdk/docs/install"
            exit 1
        fi
        
        read -p "Enter your GCP Project ID: " PROJECT_ID
        if [ -z "$PROJECT_ID" ]; then
            echo "❌ Project ID is required"
            exit 1
        fi
        
        echo "🔨 Building and deploying to Google Cloud Run..."
        gcloud builds submit --tag gcr.io/$PROJECT_ID/rag-qa-app --project=$PROJECT_ID
        gcloud run deploy rag-qa-app --image gcr.io/$PROJECT_ID/rag-qa-app --platform managed --project=$PROJECT_ID
        ;;
        
    "render")
        echo "🎨 For Render deployment:"
        echo "1. Connect your GitHub repository to Render"
        echo "2. Create a new Web Service"
        echo "3. Select 'Docker' as the environment"
        echo "4. Use Dockerfile: $DOCKERFILE"
        echo "5. Set the port to 8000"
        echo ""
        echo "Visit: https://dashboard.render.com/"
        ;;
        
    "local")
        echo "🔨 Building Docker image locally..."
        docker build -f $DOCKERFILE -t rag-qa-app .
        
        # Check image size
        SIZE=$(docker images rag-qa-app --format "table {{.Size}}" | tail -n +2)
        echo "📏 Image size: $SIZE"
        
        echo "🏃 To run locally:"
        echo "docker run -p 8000:8000 rag-qa-app"
        ;;
        
    "vercel")
        # Check if vercel CLI is installed
        if ! command -v vercel &> /dev/null; then
            echo "❌ Vercel CLI not found. Installing..."
            npm install -g vercel
        fi
        
        # Check if logged in to Vercel
        if ! vercel whoami &> /dev/null; then
            echo "� Please login to Vercel..."
            vercel login
        fi
        
        echo "⚠️  WARNING: Vercel serverless has limitations:"
        echo "   - Function size must be < 50MB"
        echo "   - No persistent storage"
        echo "   - Vector store must be external (S3, etc.)"
        echo ""
        read -p "Continue with Vercel serverless deployment? (y/N): " continue_vercel
        if [[ $continue_vercel != "y" && $continue_vercel != "Y" ]]; then
            echo "❌ Deployment cancelled. Consider using Railway instead."
            exit 1
        fi
        
        echo "🚀 Deploying to Vercel..."
        vercel
        ;;
esac

echo "✅ Deployment process complete!"

case $PLATFORM in
    "railway")
        echo "🌐 Check your Railway dashboard for the deployment URL"
        ;;
    "gcp")
        echo "🌐 Check Google Cloud Console for your Cloud Run service URL"
        ;;
    "render")
        echo "🌐 Complete the setup in Render dashboard"
        ;;
    "local")
        echo "🏠 Image built successfully. Run with: docker run -p 8000:8000 rag-qa-app"
        ;;
    "vercel")
        echo "🌐 Check your Vercel dashboard for the deployment URL"
        ;;
esac
