"""Health check endpoints for monitoring and diagnostics."""

import os
import sys
import time
from typing import Dict, List, Any

from fastapi import APIRouter, HTTPException
import psutil

from app.config import get_settings
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/", summary="Basic health check")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint for load balancers.
    
    Returns:
        Basic health status and service information
    """
    settings = get_settings()
    
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": time.time(),
        "environment": settings.environment,
    }


@router.get("/detailed", summary="Detailed health check")
async def detailed_health_check() -> Dict[str, Any]:
    """Comprehensive health check with dependency validation.
    
    Returns:
        Detailed health status including dependencies
    
    Raises:
        HTTPException: If critical dependencies are unavailable
    """
    settings = get_settings()
    logger.info("performing_detailed_health_check")
    
    health_data = {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": time.time(),
        "environment": settings.environment,
        "checks": {},
    }
    
    # Check Google Gemini API key configuration
    try:
        api_key_configured = bool(settings.google_api_key and settings.google_api_key != "your_google_api_key_here")
        health_data["checks"]["gemini_config"] = {
            "status": "healthy" if api_key_configured else "warning",
            "message": "Google Gemini API key configured" if api_key_configured else "Google Gemini API key not configured",
        }
    except Exception as e:
        health_data["checks"]["gemini_config"] = {
            "status": "unhealthy",
            "message": f"Google Gemini configuration error: {str(e)}",
        }
    
    # Check vector store directory
    try:
        vector_store_accessible = os.path.exists(settings.vector_store_path) and os.access(settings.vector_store_path, os.W_OK)
        health_data["checks"]["vector_store"] = {
            "status": "healthy" if vector_store_accessible else "unhealthy",
            "message": "Vector store accessible" if vector_store_accessible else "Vector store not accessible",
            "path": settings.vector_store_path,
        }
    except Exception as e:
        health_data["checks"]["vector_store"] = {
            "status": "unhealthy",
            "message": f"Vector store check error: {str(e)}",
        }
    
    # Check file system access
    try:
        log_dir = os.path.dirname(settings.log_file)
        filesystem_writable = os.access(log_dir, os.W_OK) if log_dir else True
        health_data["checks"]["filesystem"] = {
            "status": "healthy" if filesystem_writable else "unhealthy",
            "message": "File system writable" if filesystem_writable else "File system not writable",
        }
    except Exception as e:
        health_data["checks"]["filesystem"] = {
            "status": "unhealthy",
            "message": f"File system check error: {str(e)}",
        }
    
    # Check system resources
    try:
        memory_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent
        cpu_usage = psutil.cpu_percent(interval=1)
        
        health_data["checks"]["system_resources"] = {
            "status": "healthy" if all([memory_usage < 90, disk_usage < 90, cpu_usage < 90]) else "warning",
            "memory_usage_percent": memory_usage,
            "disk_usage_percent": disk_usage,
            "cpu_usage_percent": cpu_usage,
        }
    except Exception as e:
        health_data["checks"]["system_resources"] = {
            "status": "warning",
            "message": f"Resource check error: {str(e)}",
        }
    
    # Determine overall status
    unhealthy_checks = [check for check in health_data["checks"].values() if check["status"] == "unhealthy"]
    if unhealthy_checks:
        health_data["status"] = "unhealthy"
        logger.warning("detailed_health_check_failed", unhealthy_checks=len(unhealthy_checks))
        raise HTTPException(status_code=503, detail=health_data)
    
    warning_checks = [check for check in health_data["checks"].values() if check["status"] == "warning"]
    if warning_checks:
        health_data["status"] = "warning"
        logger.warning("detailed_health_check_warnings", warning_checks=len(warning_checks))
    
    logger.info("detailed_health_check_completed", status=health_data["status"])
    return health_data


@router.get("/ready", summary="Readiness probe")
async def readiness_check() -> Dict[str, Any]:
    """Kubernetes readiness probe to check if service can handle requests.
    
    Returns:
        Readiness status
    
    Raises:
        HTTPException: If service is not ready
    """
    settings = get_settings()
    
    # Check critical dependencies
    ready = True
    checks = []
    
    # Check Google Gemini configuration
    if not settings.google_api_key or settings.google_api_key == "your_google_api_key_here":
        ready = False
        checks.append("Google Gemini API key not configured")
    
    # Check vector store directory
    if not os.path.exists(settings.vector_store_path):
        ready = False
        checks.append("Vector store directory not accessible")
    
    if not ready:
        logger.warning("readiness_check_failed", failed_checks=checks)
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "message": "Service not ready to handle requests",
                "failed_checks": checks,
            }
        )
    
    return {
        "status": "ready",
        "message": "Service ready to handle requests",
        "timestamp": time.time(),
    }


@router.get("/live", summary="Liveness probe")
async def liveness_check() -> Dict[str, Any]:
    """Kubernetes liveness probe to check if service is alive.
    
    Returns:
        Liveness status
    """
    return {
        "status": "alive",
        "timestamp": time.time(),
        "uptime_seconds": time.time() - psutil.Process().create_time(),
    }


@router.get("/info", summary="Service information")
async def service_info() -> Dict[str, Any]:
    """Get service information and configuration.
    
    Returns:
        Service information (non-sensitive)
    """
    settings = get_settings()
    
    return {
        "service": {
            "name": settings.app_name,
            "version": settings.app_version,
            "description": settings.app_description,
            "environment": settings.environment,
        },
        "configuration": {
            "embedding_model": settings.gemini_embedding_model,
            "chat_model": settings.gemini_chat_model,
            "max_file_size_mb": settings.max_file_size / (1024 * 1024),
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap,
            "supported_extensions": settings.supported_extensions,
            "vector_dimension": settings.vector_dimension,
        },
        "api": {
            "docs_url": "/docs" if not settings.is_production else None,
            "redoc_url": "/redoc" if not settings.is_production else None,
        },
        "system": {
            "python_version": sys.version,
            "platform": sys.platform,
        },
    }