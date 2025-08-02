"""Tests for health check API endpoints."""

import pytest
from unittest.mock import patch, Mock


@pytest.mark.api
class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_basic_health_check(self, client):
        """Test basic health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
        assert "timestamp" in data
        assert "environment" in data
        
        # Check required fields
        assert data["service"] == "RAG Q&A Foundation"
        assert data["version"] == "1.0.0"
    
    def test_health_check_content_type(self, client):
        """Test health check response content type."""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
    
    @patch('app.api.endpoints.health.get_settings')
    def test_detailed_health_check_success(self, mock_get_settings, client):
        """Test detailed health check with all systems healthy."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.openai_api_key = "valid_api_key"
        mock_settings.vector_store_path = "/tmp/test_vector_store"
        mock_settings.log_file = "/tmp/test.log"
        mock_get_settings.return_value = mock_settings
        
        with patch('os.path.exists', return_value=True), \
             patch('os.access', return_value=True), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk, \
             patch('psutil.cpu_percent') as mock_cpu:
            
            # Mock system resources (healthy levels)
            mock_memory.return_value = Mock(percent=50.0)
            mock_disk.return_value = Mock(percent=60.0)
            mock_cpu.return_value = 30.0
            
            response = client.get("/health/detailed")
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert "checks" in data
            
            # Check individual health checks
            checks = data["checks"]
            assert "openai_config" in checks
            assert "vector_store" in checks
            assert "filesystem" in checks
            assert "system_resources" in checks
            
            # All should be healthy
            for check_name, check_data in checks.items():
                assert check_data["status"] in ["healthy", "warning"]
    
    @patch('app.api.endpoints.health.get_settings')
    def test_detailed_health_check_unhealthy(self, mock_get_settings, client):
        """Test detailed health check with some systems unhealthy."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.openai_api_key = "your_openai_api_key_here"  # Not configured
        mock_settings.vector_store_path = "/nonexistent/path"
        mock_settings.log_file = "/tmp/test.log"
        mock_get_settings.return_value = mock_settings
        
        with patch('os.path.exists', return_value=False), \
             patch('os.access', return_value=False):
            
            response = client.get("/health/detailed")
            
            assert response.status_code == 503
            
            data = response.json()
            assert data["status"] == "unhealthy"
            assert "checks" in data
            
            # Should have failing checks
            checks = data["checks"]
            assert checks["openai_config"]["status"] == "warning"
            assert checks["vector_store"]["status"] == "unhealthy"
    
    @patch('app.api.endpoints.health.get_settings')
    def test_detailed_health_check_warnings(self, mock_get_settings, client):
        """Test detailed health check with warnings."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.openai_api_key = "your_openai_api_key_here"  # Warning condition
        mock_settings.vector_store_path = "/tmp/test_vector_store"
        mock_settings.log_file = "/tmp/test.log"
        mock_get_settings.return_value = mock_settings
        
        with patch('os.path.exists', return_value=True), \
             patch('os.access', return_value=True), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk, \
             patch('psutil.cpu_percent') as mock_cpu:
            
            # Mock high resource usage (warning levels)
            mock_memory.return_value = Mock(percent=95.0)
            mock_disk.return_value = Mock(percent=95.0)
            mock_cpu.return_value = 95.0
            
            response = client.get("/health/detailed")
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "warning"
            
            # Check system resources show warning
            checks = data["checks"]
            assert checks["system_resources"]["status"] == "warning"
    
    def test_readiness_check_ready(self, client):
        """Test readiness check when service is ready.""" 
        with patch('app.api.endpoints.health.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.openai_api_key = "valid_api_key"
            mock_settings.vector_store_path = "/tmp/test_vector_store"
            mock_get_settings.return_value = mock_settings
            
            with patch('os.path.exists', return_value=True):
                response = client.get("/health/ready")
                
                assert response.status_code == 200
                
                data = response.json()
                assert data["status"] == "ready"
                assert "timestamp" in data
    
    def test_readiness_check_not_ready(self, client):
        """Test readiness check when service is not ready."""
        with patch('app.api.endpoints.health.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.openai_api_key = "your_openai_api_key_here"  # Not configured
            mock_settings.vector_store_path = "/tmp/test_vector_store"
            mock_get_settings.return_value = mock_settings
            
            response = client.get("/health/ready")
            
            assert response.status_code == 503
            
            data = response.json()
            assert data["status"] == "not_ready"
            assert "failed_checks" in data
            assert len(data["failed_checks"]) > 0
    
    def test_liveness_check(self, client):
        """Test liveness check endpoint."""
        with patch('psutil.Process') as mock_process:
            mock_process_instance = Mock()
            mock_process_instance.create_time.return_value = 1000.0
            mock_process.return_value = mock_process_instance
            
            response = client.get("/health/live")
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "alive"
            assert "timestamp" in data
            assert "uptime_seconds" in data
            assert data["uptime_seconds"] > 0
    
    def test_service_info(self, client):
        """Test service information endpoint."""
        response = client.get("/health/info")
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Check service info structure
        assert "service" in data
        assert "configuration" in data
        assert "api" in data
        assert "system" in data
        
        # Check service details
        service_info = data["service"]
        assert service_info["name"] == "RAG Q&A Foundation"
        assert service_info["version"] == "1.0.0"
        
        # Check configuration details
        config_info = data["configuration"]
        assert "embedding_model" in config_info
        assert "chat_model" in config_info
        assert "max_file_size_mb" in config_info
        assert "chunk_size" in config_info
        
        # Check API info
        api_info = data["api"]
        assert "docs_url" in api_info
        assert "redoc_url" in api_info
        
        # Check system info
        system_info = data["system"]
        assert "python_version" in system_info
        assert "platform" in system_info


@pytest.mark.api
class TestHealthEndpointErrors:
    """Test health endpoint error handling."""
    
    @patch('app.api.endpoints.health.get_settings')
    def test_detailed_health_check_exception(self, mock_get_settings, client):   
        """Test detailed health check with exception."""
        mock_get_settings.side_effect = Exception("Settings error")
        
        response = client.get("/health/detailed")
        
        # Should still return some response, not crash
        assert response.status_code in [500, 503]
    
    @patch('psutil.virtual_memory')
    def test_resource_check_exception(self, mock_memory, client):
        """Test resource checking with exception."""
        mock_memory.side_effect = Exception("Resource error")
        
        with patch('app.api.endpoints.health.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.openai_api_key = "valid_key"
            mock_settings.vector_store_path = "/tmp/test"
            mock_settings.log_file = "/tmp/test.log"
            mock_get_settings.return_value = mock_settings
            
            with patch('os.path.exists', return_value=True), \
                 patch('os.access', return_value=True):
                
                response = client.get("/health/detailed")
                
                assert response.status_code in [200, 503]
                
                if response.status_code == 200:
                    data = response.json()
                    # Should have warning status for system resources
                    checks = data.get("checks", {})
                    if "system_resources" in checks:
                        assert checks["system_resources"]["status"] == "warning"


@pytest.mark.integration
class TestHealthEndpointIntegration:
    """Integration tests for health endpoints."""
    
    def test_health_endpoint_sequence(self, client):
        """Test calling health endpoints in sequence."""
        # Test basic health first
        response1 = client.get("/health")
        assert response1.status_code == 200
        
        # Test service info
        response2 = client.get("/health/info")
        assert response2.status_code == 200
        
        # Test liveness
        response3 = client.get("/health/live")
        assert response3.status_code == 200
        
        # Test readiness
        response4 = client.get("/health/ready")
        assert response4.status_code in [200, 503]  # May fail without proper config
        
        # Test detailed (may fail without proper config)
        response5 = client.get("/health/detailed")
        assert response5.status_code in [200, 503]
        
        # All responses should be JSON
        for response in [response1, response2, response3, response4, response5]:
            assert "application/json" in response.headers.get("content-type", "")
    
    def test_health_endpoints_consistency(self, client):
        """Test that health endpoints return consistent information."""
        basic_response = client.get("/health")
        info_response = client.get("/health/info")
        
        assert basic_response.status_code == 200
        assert info_response.status_code == 200
        
        basic_data = basic_response.json()
        info_data = info_response.json()
        
        # Service name and version should be consistent
        assert basic_data["service"] == info_data["service"]["name"]
        assert basic_data["version"] == info_data["service"]["version"]
    
    def test_health_endpoint_headers(self, client):
        """Test health endpoint response headers."""
        response = client.get("/health")
        
        assert response.status_code == 200
        
        headers = response.headers
        assert "content-type" in headers
        assert "x-request-id" in headers  # Should be added by middleware
        
        # Security headers should be present (added by middleware)
        security_headers = [
            "x-content-type-options",
            "x-frame-options", 
            "x-xss-protection"
        ]
        
        for header in security_headers:
            assert header in headers


@pytest.mark.performance
class TestHealthEndpointPerformance:
    """Performance tests for health endpoints."""
    
    def test_basic_health_check_speed(self, client, performance_timer):
        """Test basic health check response time."""
        performance_timer.start()
        response = client.get("/health")
        performance_timer.stop()
        
        assert response.status_code == 200
        # Basic health check should be very fast (< 50ms)
        assert performance_timer.elapsed < 0.05
    
    def test_detailed_health_check_speed(self, client, performance_timer):
        """Test detailed health check response time."""
        performance_timer.start()
        response = client.get("/health/detailed")
        performance_timer.stop()
        
        # Detailed health check should still be reasonably fast (< 200ms)
        assert performance_timer.elapsed < 0.2
    
    def test_concurrent_health_checks(self, client):
        """Test concurrent health check requests."""
        import concurrent.futures
        import time
        
        def make_request():
            start_time = time.time()
            response = client.get("/health")
            end_time = time.time()
            return response.status_code, end_time - start_time
        
        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in futures]
        
        # All requests should succeed
        status_codes, durations = zip(*results)
        assert all(code == 200 for code in status_codes)
        
        # Average response time should be reasonable
        avg_duration = sum(durations) / len(durations)
        assert avg_duration < 0.1  # 100ms average