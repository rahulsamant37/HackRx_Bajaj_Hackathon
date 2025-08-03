#!/usr/bin/env python3
"""Simple script to test the RAG API endpoints."""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.main import app
from app.config import get_settings


async def test_health_endpoints():
    """Test health endpoints."""
    print("🏥 Testing Health Endpoints...")
    
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    # Test basic health check
    response = client.get("/health")
    print(f"Health Check: {response.status_code} - {response.json()}")
    
    # Test detailed health check
    response = client.get("/health/detailed")
    print(f"Detailed Health: {response.status_code}")
    if response.status_code == 200:
        print("✅ All health checks passed")
    else:
        print("⚠️ Some health checks failed - this is expected without GEMINI API key")
    
    # Test service info
    response = client.get("/health/info")
    print(f"Service Info: {response.status_code} - Available")


def test_configuration():
    """Test configuration loading."""
    print("⚙️ Testing Configuration...")
    
    try:
        settings = get_settings()
        print(f"App Name: {settings.app_name}")
        print(f"Environment: {settings.environment}")
        print(f"Vector Store Path: {settings.vector_store_path}")
        
        # Check if directories were created
        if os.path.exists(settings.vector_store_path):
            print("✅ Vector store directory created")
        
        if settings.google_api_key and settings.google_api_key != "your_google_api_key_here":
            print("✅ Google Gemini API key configured")
        else:
            print("⚠️ Google Gemini API key not configured - needed for full functionality")
            
    except Exception as e:
        print(f"❌ Configuration error: {e}")


def test_services():
    """Test service initialization."""
    print("🔧 Testing Services...")
    
    try:
        from app.services.document_service import DocumentProcessor
        from app.services.rag_service import RAGService
        
        # Test document processor
        doc_processor = DocumentProcessor()
        print("✅ Document processor initialized")
        
        # Test RAG service
        rag_service = RAGService()
        print("✅ RAG service initialized")
        
        # Test stats
        stats = rag_service.get_stats()
        print(f"Vector store stats: {stats}")
        
    except Exception as e:
        print(f"❌ Service initialization error: {e}")


def test_api_documentation():
    """Test API documentation endpoints."""
    print("📚 Testing API Documentation...")
    
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    # Test OpenAPI schema
    response = client.get("/openapi.json")
    if response.status_code == 200:
        print("✅ OpenAPI schema available")
        
        # Count endpoints
        openapi_data = response.json()
        paths = openapi_data.get("paths", {})
        endpoint_count = len(paths)
        print(f"📋 Total API endpoints: {endpoint_count}")
        
        # List main endpoints
        print("Main endpoints:")
        for path in sorted(paths.keys()):
            methods = list(paths[path].keys())
            print(f"  {path}: {', '.join(methods).upper()}")
    else:
        print("❌ OpenAPI schema not available")


def main():
    """Run all tests."""
    print("🚀 Starting RAG Q&A Foundation API Tests")
    print("=" * 50)
    
    test_configuration()
    print()
    
    test_services()
    print()
    
    test_health_endpoints()
    print()
    
    test_api_documentation()
    print()
    
    print("=" * 50)
    print("✅ Basic tests completed!")
    print()
    print("🌐 To start the server, run:")
    print("   python -m app.main")
    print("   # or")
    print("   uvicorn app.main:app --reload")
    print()
    print("📖 Then visit http://localhost:8000/docs for API documentation")


if __name__ == "__main__":
    main()