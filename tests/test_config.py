"""Tests for configuration management."""

import os
import tempfile
import pytest
from pydantic import ValidationError

from app.config import Settings, get_settings


class TestSettings:
    """Test the Settings class."""
    
    def test_default_settings(self):
        """Test default settings values."""
        # Clear environment variables that might interfere
        env_vars = [
            "GOOGLE_API_KEY", "SECRET_KEY", "ENVIRONMENT", "DEBUG",
            "HOST", "PORT", "LOG_LEVEL"
        ]
        original_values = {}
        for var in env_vars:
            original_values[var] = os.environ.pop(var, None)
        
        try:
            # Create settings with minimal required values
            os.environ["GOOGLE_API_KEY"] = "test_key"
            os.environ["SECRET_KEY"] = "test_secret"
            
            settings = Settings()
            
            # Test default values
            assert settings.app_name == "RAG Q&A Foundation"
            assert settings.app_version == "1.0.0"
            assert settings.environment == "development"
            assert settings.debug is False
            assert settings.host == "0.0.0.0"
            assert settings.port == 8000
            assert settings.gemini_embedding_model == "models/embedding-001"
            assert settings.gemini_chat_model == "gemini-2.5-flash"
            assert settings.chunk_size == 1000
            assert settings.chunk_overlap == 200
            assert settings.log_level == "INFO"
            
        finally:
            # Restore original environment
            for var, value in original_values.items():
                if value is not None:
                    os.environ[var] = value
                else:
                    os.environ.pop(var, None)
    
    def test_required_fields(self):
        """Test that required fields raise validation errors."""
        # Clear required environment variables
        original_api_key = os.environ.pop("GOOGLE_API_KEY", None)
        original_secret_key = os.environ.pop("SECRET_KEY", None)
        
        try:
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            
            errors = exc_info.value.errors()
            error_fields = {error["loc"][0] for error in errors}
            assert "google_api_key" in error_fields
            assert "secret_key" in error_fields
            
        finally:
            # Restore environment
            if original_api_key:
                os.environ["GOOGLE_API_KEY"] = original_api_key
            if original_secret_key:
                os.environ["SECRET_KEY"] = original_secret_key
    
    def test_environment_validation(self):
        """Test environment setting validation."""
        os.environ["GOOGLE_API_KEY"] = "test_key"
        os.environ["SECRET_KEY"] = "test_secret"
        
        # Valid environments
        for env in ["development", "staging", "production"]:
            os.environ["ENVIRONMENT"] = env
            settings = Settings()
            assert settings.environment == env
        
        # Invalid environment
        os.environ["ENVIRONMENT"] = "invalid"
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        
        assert "Environment must be one of" in str(exc_info.value)
    
    def test_log_level_validation(self):
        """Test log level validation."""
        os.environ["GOOGLE_API_KEY"] = "test_key"
        os.environ["SECRET_KEY"] = "test_secret"
        
        # Valid log levels
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            os.environ["LOG_LEVEL"] = level
            settings = Settings()
            assert settings.log_level == level
        
        # Test case insensitive
        os.environ["LOG_LEVEL"] = "debug"
        settings = Settings()
        assert settings.log_level == "DEBUG"
        
        # Invalid log level
        os.environ["LOG_LEVEL"] = "INVALID"
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        
        assert "Log level must be one of" in str(exc_info.value)
    
    def test_log_format_validation(self):
        """Test log format validation."""
        os.environ["GOOGLE_API_KEY"] = "test_key"
        os.environ["SECRET_KEY"] = "test_secret"
        
        # Valid formats
        for fmt in ["json", "console"]:
            os.environ["LOG_FORMAT"] = fmt
            settings = Settings()
            assert settings.log_format == fmt
        
        # Invalid format
        os.environ["LOG_FORMAT"] = "invalid"
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        
        assert "Log format must be one of" in str(exc_info.value)
    
    def test_port_validation(self):
        """Test port validation."""
        os.environ["GOOGLE_API_KEY"] = "test_key"
        os.environ["SECRET_KEY"] = "test_secret"
        
        # Valid port
        os.environ["PORT"] = "8080"
        settings = Settings()
        assert settings.port == 8080
        
        # Invalid ports
        for invalid_port in ["0", "65536", "-1"]:
            os.environ["PORT"] = invalid_port
            with pytest.raises(ValidationError):
                Settings()
    
    def test_numeric_field_validation(self):
        """Test numeric field validations."""
        os.environ["GOOGLE_API_KEY"] = "test_key"
        os.environ["SECRET_KEY"] = "test_secret"
        
        # Test chunk size validation
        os.environ["CHUNK_SIZE"] = "0"
        with pytest.raises(ValidationError):
            Settings()
        
        os.environ["CHUNK_SIZE"] = "1000"
        settings = Settings()
        assert settings.chunk_size == 1000
        
        # Test chunk overlap validation
        os.environ["CHUNK_OVERLAP"] = "-1"
        with pytest.raises(ValidationError):
            Settings()
        
        # Test temperature validation
        os.environ["OPENAI_TEMPERATURE"] = "3.0"
        with pytest.raises(ValidationError):
            Settings()
        
        os.environ["OPENAI_TEMPERATURE"] = "0.7"
        settings = Settings()
        assert settings.openai_temperature == 0.7
    
    def test_directory_creation(self):
        """Test that required directories are created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            vector_path = os.path.join(temp_dir, "vector_store")
            log_path = os.path.join(temp_dir, "logs", "app.log")
            
            os.environ.update({
                "GOOGLE_API_KEY": "test_key",
                "SECRET_KEY": "test_secret",
                "VECTOR_STORE_PATH": vector_path,
                "LOG_FILE": log_path,
            })
            
            settings = Settings()
            
            # Check directories were created
            assert os.path.exists(vector_path)
            assert os.path.exists(os.path.dirname(log_path))
            assert settings.vector_store_path == vector_path
            assert settings.log_file == log_path
    
    def test_properties(self):
        """Test computed properties."""
        os.environ.update({
            "GOOGLE_API_KEY": "test_key",
            "SECRET_KEY": "test_secret",
        })
        
        # Test development environment
        os.environ["ENVIRONMENT"] = "development"
        settings = Settings()
        assert settings.is_development is True
        assert settings.is_production is False
        
        # Test production environment
        os.environ["ENVIRONMENT"] = "production"
        settings = Settings()
        assert settings.is_development is False
        assert settings.is_production is True
    
    def test_list_fields(self):
        """Test list field handling."""
        os.environ.update({
            "GOOGLE_API_KEY": "test_key",
            "SECRET_KEY": "test_secret",
        })
        
        settings = Settings()
        
        # Test default lists
        assert isinstance(settings.supported_extensions, list)
        assert ".pdf" in settings.supported_extensions
        assert ".txt" in settings.supported_extensions
        
        assert isinstance(settings.cors_origins, list)
        assert isinstance(settings.cors_methods, list)
        assert isinstance(settings.cors_headers, list)


class TestGetSettings:
    """Test the get_settings function."""
    
    def test_settings_caching(self):
        """Test that settings are cached."""
        os.environ.update({
            "GOOGLE_API_KEY": "test_key",
            "SECRET_KEY": "test_secret",
        })
        
        # Get settings twice
        settings1 = get_settings()
        settings2 = get_settings()
        
        # Should be the same instance due to caching
        assert settings1 is settings2
    
    def test_cache_clearing(self):
        """Test cache clearing functionality."""
        os.environ.update({
            "GOOGLE_API_KEY": "test_key_1",
            "SECRET_KEY": "test_secret",
        })
        
        settings1 = get_settings()
        assert settings1.google_api_key == "test_key_1"
        
        # Change environment and clear cache
        os.environ["GOOGLE_API_KEY"] = "test_key_2"
        get_settings.cache_clear()
        
        settings2 = get_settings()
        assert settings2.google_api_key == "test_key_2"
        assert settings1 is not settings2


class TestSettingsIntegration:
    """Integration tests for settings."""
    
    def test_settings_with_env_file(self):
        """Test settings loading from .env file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = os.path.join(temp_dir, ".env")
            
            # Create test .env file
            with open(env_file, "w") as f:
                f.write("GOOGLE_API_KEY=env_file_key\n")
                f.write("SECRET_KEY=env_file_secret\n")
                f.write("ENVIRONMENT=staging\n")
                f.write("DEBUG=true\n")
            
            # Change to temp directory and clear cache
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            get_settings.cache_clear()
            
            try:
                settings = Settings()
                assert settings.google_api_key == "env_file_key"
                assert settings.secret_key == "env_file_secret"
                assert settings.environment == "staging"
                assert settings.debug is True
                
            finally:
                os.chdir(original_cwd)
                get_settings.cache_clear()
    
    def test_environment_override_env_file(self):
        """Test that environment variables override .env file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = os.path.join(temp_dir, ".env")
            
            # Create test .env file
            with open(env_file, "w") as f:
                f.write("GOOGLE_API_KEY=env_file_key\n")
                f.write("SECRET_KEY=env_file_secret\n")
                f.write("ENVIRONMENT=development\n")
            
            # Set environment variable to override
            os.environ["ENVIRONMENT"] = "production"
            
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            get_settings.cache_clear()
            
            try:
                settings = Settings()
                # Environment variable should override .env file
                assert settings.environment == "production"
                # But .env file values should still be used for others
                assert settings.google_api_key == "env_file_key"
                
            finally:
                os.chdir(original_cwd)
                os.environ.pop("ENVIRONMENT", None)
                get_settings.cache_clear()


@pytest.mark.unit
class TestSettingsValidation:
    """Test advanced settings validation."""
    
    def test_chunk_overlap_validation(self):
        """Test chunk overlap vs chunk size validation."""
        os.environ.update({
            "GOOGLE_API_KEY": "test_key",
            "SECRET_KEY": "test_secret",
            "CHUNK_SIZE": "100",
            "CHUNK_OVERLAP": "150",  # Greater than chunk size
        })
        
        # This should pass pydantic validation but might be logically invalid
        # The validation is handled in the document processor
        settings = Settings()
        assert settings.chunk_size == 100
        assert settings.chunk_overlap == 150
    
    def test_file_size_limits(self):
        """Test file size limit validation."""
        os.environ.update({
            "GOOGLE_API_KEY": "test_key",
            "SECRET_KEY": "test_secret",
        })
        
        # Test valid file size
        os.environ["MAX_FILE_SIZE"] = "5242880"  # 5MB
        settings = Settings()
        assert settings.max_file_size == 5242880
        
        # Test invalid file size (negative)
        os.environ["MAX_FILE_SIZE"] = "-1"
        with pytest.raises(ValidationError):
            Settings()
    
    def test_rate_limiting_settings(self):
        """Test rate limiting configuration validation."""
        os.environ.update({
            "GOOGLE_API_KEY": "test_key",
            "SECRET_KEY": "test_secret",
        })
        
        # Test valid rate limiting
        os.environ["RATE_LIMIT_REQUESTS"] = "100"
        os.environ["RATE_LIMIT_WINDOW"] = "60"
        settings = Settings()
        assert settings.rate_limit_requests == 100
        assert settings.rate_limit_window == 60
        
        # Test invalid values
        os.environ["RATE_LIMIT_REQUESTS"] = "0"
        with pytest.raises(ValidationError):
            Settings()
            
        os.environ["RATE_LIMIT_REQUESTS"] = "100"
        os.environ["RATE_LIMIT_WINDOW"] = "0"
        with pytest.raises(ValidationError):
            Settings()