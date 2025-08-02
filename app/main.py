"""FastAPI application entry point for RAG Q&A Foundation."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.middleware import RequestLoggingMiddleware, ErrorHandlingMiddleware
from app.api.endpoints import health
from app.utils.logger import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    setup_logging()
    yield
    # Shutdown
    pass


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )
    
    # Add custom middleware
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Include routers
    app.include_router(health.router, prefix="/health", tags=["health"])
    
    # Import and include other routers
    from app.api.endpoints import documents, qa
    app.include_router(documents.router, prefix="/documents", tags=["documents"])
    app.include_router(qa.router, prefix="/qa", tags=["questions-answers"])
    
    return app


# Create application instance
app = create_app()


@app.get("/")
async def root():
    """Root endpoint with basic application information."""
    settings = get_settings()
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "description": settings.app_description,
        "docs_url": "/docs" if settings.environment != "production" else None,
    }


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_config=None,  # Use our custom logging
    )