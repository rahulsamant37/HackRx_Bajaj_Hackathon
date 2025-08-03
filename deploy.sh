#!/bin/bash

# RAG QA Foundation - Vercel Deployment Script

set -e

echo "🚀 RAG QA Foundation - Vercel Deployment"
echo "========================================"

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Check if logged in to Vercel
if ! vercel whoami &> /dev/null; then
    echo "🔑 Please login to Vercel..."
    vercel login
fi

# Build options
echo "Select Dockerfile for deployment:"
echo "1. Dockerfile.vercel (Recommended for Vercel - ~200-250MB)"
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

# Check if docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build locally first to check size
echo "🔨 Building Docker image locally to check size..."
docker build -f $DOCKERFILE -t rag-qa-test .

# Check image size
SIZE=$(docker images rag-qa-test --format "table {{.Size}}" | tail -n +2)
echo "📏 Image size: $SIZE"

# Warning if size might be too large
if [[ $SIZE == *"GB"* ]] || [[ $SIZE =~ ^[3-9][0-9][0-9] ]]; then
    echo "⚠️  Warning: Image size might exceed Vercel limits (250MB)"
    read -p "Continue anyway? (y/N): " continue_deploy
    if [[ $continue_deploy != "y" && $continue_deploy != "Y" ]]; then
        echo "❌ Deployment cancelled"
        exit 1
    fi
fi

# Clean up test image
docker rmi rag-qa-test

# Deploy to Vercel
echo "🚀 Deploying to Vercel..."
if [ "$DOCKERFILE" != "Dockerfile" ]; then
    # Copy the selected Dockerfile to Dockerfile for Vercel
    cp $DOCKERFILE Dockerfile.deploy
    vercel --docker
    rm Dockerfile.deploy
else
    vercel --docker
fi

echo "✅ Deployment complete!"
echo "🌐 Check your Vercel dashboard for the deployment URL"
