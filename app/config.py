"""Configuration management using pydantic-settings."""

import os
from functools import lru_cache
from typing import List

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application Settings
    app_name: str = Field(default="RAG Q&A Foundation", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    app_description: str = Field(
        default="Production-ready RAG Q&A system with FastAPI",
        description="Application description"
    )
    environment: str = Field(default="development", description="Environment (development, staging, production)")
    debug: bool = Field(default=False, description="Debug mode")
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port", ge=1, le=65535)
    
    # Google Gemini Configuration
    google_api_key: str = Field(..., description="Google API key for Gemini")
    gemini_embedding_model: str = Field(
        default="models/embedding-001",
        description="Google Gemini embedding model"
    )
    gemini_chat_model: str = Field(default="gemini-2.5-flash", description="Google Gemini chat model")
    gemini_max_tokens: int = Field(default=1000, description="Max tokens for Gemini responses", ge=1)
    gemini_temperature: float = Field(
        default=0.7,
        description="Temperature for Gemini responses",
        ge=0.0,
        le=2.0
    )
    
    # Vector Database Settings
    vector_store_path: str = Field(default="./data/vector_store", description="Vector store path")
    vector_index_type: str = Field(default="IndexFlatL2", description="FAISS index type")
    vector_dimension: int = Field(default=768, description="Vector dimension for Gemini embeddings", ge=1)
    similarity_threshold: float = Field(
        default=0.8,
        description="Similarity threshold for search",
        ge=0.0,
        le=1.0
    )
    
    # Document Processing
    max_file_size: int = Field(
        default=10485760,  # 10MB
        description="Maximum file size in bytes",
        ge=1
    )
    chunk_size: int = Field(default=1000, description="Text chunk size", ge=1)
    chunk_overlap: int = Field(default=200, description="Text chunk overlap", ge=0)
    supported_extensions: List[str] = Field(
        default=[".pdf", ".txt", ".docx", ".md"],
        description="Supported file extensions"
    )
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=100, description="Rate limit requests per window", ge=1)
    rate_limit_window: int = Field(default=60, description="Rate limit window in seconds", ge=1)
    
    # CORS Settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8501"],
        description="CORS allowed origins"
    )
    cors_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE"],
        description="CORS allowed methods"
    )
    cors_headers: List[str] = Field(default=["*"], description="CORS allowed headers")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or console)")
    log_file: str = Field(default="./logs/app.log", description="Log file path")
    
    # Security
    secret_key: str = Field(..., description="Secret key for JWT")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration in minutes",
        ge=1
    )
    
    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment setting."""
        allowed_environments = ["development", "staging", "production"]
        if v not in allowed_environments:
            raise ValueError(f"Environment must be one of {allowed_environments}")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of {allowed_levels}")
        return v.upper()
    
    @validator("log_format")
    def validate_log_format(cls, v):
        """Validate log format."""
        allowed_formats = ["json", "console"]
        if v not in allowed_formats:
            raise ValueError(f"Log format must be one of {allowed_formats}")
        return v
    
    @validator("vector_store_path")
    def validate_vector_store_path(cls, v):
        """Ensure vector store directory exists."""
        os.makedirs(v, exist_ok=True)
        return v
    
    @validator("log_file")
    def validate_log_file(cls, v):
        """Ensure log directory exists."""
        log_dir = os.path.dirname(v)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()