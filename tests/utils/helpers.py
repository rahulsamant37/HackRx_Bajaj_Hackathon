"""Test utility functions and helpers."""

import tempfile
import os
import time
import json
from typing import Dict, Any, List, Optional
from contextlib import contextmanager

import pytest


class TestFileManager:
    """Manager for creating and cleaning up test files."""
    
    def __init__(self):
        self.temp_files = []
        self.temp_dirs = []
    
    def create_text_file(self, content: str, filename: str = "test.txt") -> str:
        """Create a temporary text file with given content."""
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix=f"_{filename}",
            delete=False,
            encoding='utf-8'
        )
        temp_file.write(content)
        temp_file.close()
        
        self.temp_files.append(temp_file.name)
        return temp_file.name
    
    def create_binary_file(self, content: bytes, filename: str = "test.bin") -> str:
        """Create a temporary binary file with given content."""
        temp_file = tempfile.NamedTemporaryFile(
            mode='wb',
            suffix=f"_{filename}",
            delete=False
        )
        temp_file.write(content)
        temp_file.close()
        
        self.temp_files.append(temp_file.name)
        return temp_file.name
    
    def create_large_file(self, size_mb: int, filename: str = "large.txt") -> str:
        """Create a large temporary file of specified size."""
        content = "x" * (1024 * 1024 * size_mb)
        return self.create_text_file(content, filename)
    
    def create_temp_dir(self) -> str:
        """Create a temporary directory."""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def cleanup(self):
        """Clean up all created temporary files and directories."""
        import shutil
        
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except Exception:
                pass
        
        for dir_path in self.temp_dirs:
            try:
                if os.path.exists(dir_path):
                    shutil.rmtree(dir_path)
            except Exception:
                pass
        
        self.temp_files.clear()
        self.temp_dirs.clear()


class APITestHelper:
    """Helper class for API testing."""
    
    @staticmethod
    def assert_successful_response(response, expected_status: int = 200):
        """Assert that API response is successful."""
        assert response.status_code == expected_status
        assert "application/json" in response.headers.get("content-type", "")
        
        data = response.json()
        if "success" in data:
            assert data["success"] is True
        
        return data
    
    @staticmethod
    def assert_error_response(response, expected_status: int = 400):
        """Assert that API response contains error."""
        assert response.status_code == expected_status
        assert "application/json" in response.headers.get("content-type", "")
        
        data = response.json()
        assert "detail" in data or ("success" in data and data["success"] is False)
        
        return data
    
    @staticmethod
    def assert_validation_error(response):
        """Assert that response is a validation error."""
        return APITestHelper.assert_error_response(response, 422)
    
    @staticmethod
    def extract_document_id(upload_response) -> str:
        """Extract document ID from upload response."""
        data = APITestHelper.assert_successful_response(upload_response, 201)
        assert "document_id" in data
        return data["document_id"]
    
    @staticmethod
    def wait_for_processing(client, document_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Wait for document processing to complete."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = client.get(f"/documents/{document_id}/status")
            if response.status_code != 200:
                break
            
            data = response.json()
            status = data.get("status", "unknown")
            
            if status in ["completed", "failed"]:
                return data
            
            time.sleep(0.5)
        
        raise TimeoutError(f"Document processing did not complete within {timeout} seconds")


class PerformanceTestHelper:
    """Helper for performance testing."""
    
    @staticmethod
    @contextmanager
    def measure_time():
        """Context manager to measure execution time."""
        start_time = time.time()
        yield lambda: time.time() - start_time
    
    @staticmethod
    def run_concurrent_requests(func, num_requests: int = 10, max_workers: int = 5):
        """Run multiple requests concurrently and return results."""
        import concurrent.futures
        
        results = []
        durations = []
        
        def timed_request():
            start_time = time.time()
            try:
                result = func()
                duration = time.time() - start_time
                return result, duration, None
            except Exception as e:
                duration = time.time() - start_time
                return None, duration, e
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(timed_request) for _ in range(num_requests)]
            
            for future in concurrent.futures.as_completed(futures):
                result, duration, error = future.result()
                results.append((result, error))
                durations.append(duration)
        
        return {
            'results': results,
            'durations': durations,
            'avg_duration': sum(durations) / len(durations),
            'max_duration': max(durations),
            'min_duration': min(durations),
            'success_count': sum(1 for result, error in results if error is None),
            'error_count': sum(1 for result, error in results if error is not None)
        }
    
    @staticmethod
    def assert_performance_requirements(
        stats: Dict[str, Any],
        max_avg_duration: float = 1.0,
        max_duration: float = 5.0,
        min_success_rate: float = 0.95
    ):
        """Assert that performance meets requirements."""
        success_rate = stats['success_count'] / (stats['success_count'] + stats['error_count'])
        
        assert stats['avg_duration'] <= max_avg_duration, \
            f"Average duration {stats['avg_duration']:.3f}s exceeds limit {max_avg_duration}s"
        
        assert stats['max_duration'] <= max_duration, \
            f"Max duration {stats['max_duration']:.3f}s exceeds limit {max_duration}s"
        
        assert success_rate >= min_success_rate, \
            f"Success rate {success_rate:.2%} below minimum {min_success_rate:.2%}"


class MockDataGenerator:
    """Generator for mock test data."""
    
    @staticmethod
    def generate_document_content(topic: str, length: int = 500) -> str:
        """Generate realistic document content."""
        templates = {
            "technology": [
                "Artificial intelligence and machine learning are transforming industries.",
                "Cloud computing provides scalable infrastructure for modern applications.",
                "Cybersecurity is crucial for protecting digital assets and privacy.",
                "Software development methodologies continue to evolve rapidly."
            ],
            "science": [
                "Scientific research advances our understanding of the natural world.",
                "Climate change presents significant challenges for global ecosystems.",
                "Medical breakthroughs improve healthcare outcomes worldwide.",
                "Space exploration expands human knowledge of the universe."
            ],
            "business": [
                "Digital transformation is reshaping traditional business models.",
                "Customer experience is becoming a key competitive differentiator.",
                "Supply chain optimization reduces costs and improves efficiency.",
                "Data-driven decision making enhances business performance."
            ]
        }
        
        sentences = templates.get(topic, templates["technology"])
        
        content = []
        current_length = 0
        
        while current_length < length:
            for sentence in sentences:
                if current_length >= length:
                    break
                content.append(sentence)
                current_length += len(sentence) + 1
        
        return " ".join(content)[:length]
    
    @staticmethod
    def generate_questions_for_topic(topic: str) -> List[str]:
        """Generate relevant questions for a topic."""
        questions = {
            "technology": [
                "What is artificial intelligence?",
                "How does machine learning work?",
                "What are the benefits of cloud computing?",
                "Why is cybersecurity important?"
            ],
            "science": [
                "What is climate change?",
                "How does scientific research work?",
                "What are recent medical breakthroughs?",
                "Why do we explore space?"
            ],
            "business": [
                "What is digital transformation?",
                "How to improve customer experience?",
                "What is supply chain optimization?",
                "Why is data-driven decision making important?"
            ]
        }
        
        return questions.get(topic, questions["technology"])
    
    @staticmethod
    def generate_chat_conversation(length: int = 5) -> List[Dict[str, str]]:
        """Generate a realistic chat conversation."""
        conversation_templates = [
            ("user", "Hello, can you help me understand this document?"),
            ("assistant", "Of course! I'd be happy to help you understand the document. What specific aspect would you like me to explain?"),
            ("user", "What are the main topics covered?"),
            ("assistant", "Based on the document, the main topics include technology trends, implementation strategies, and best practices."),
            ("user", "Can you elaborate on the implementation strategies?"),
            ("assistant", "The document outlines several key implementation strategies including phased rollouts, stakeholder engagement, and risk mitigation approaches."),
            ("user", "What about best practices?"),
            ("assistant", "The best practices mentioned focus on continuous monitoring, regular reviews, and maintaining clear documentation throughout the process."),
            ("user", "Thank you, that's very helpful!"),
            ("assistant", "You're welcome! Feel free to ask if you have any other questions about the document.")
        ]
        
        return [
            {"role": role, "content": content}
            for role, content in conversation_templates[:length]
        ]


class TestDataValidator:
    """Validator for test data and responses."""
    
    @staticmethod
    def validate_document_response(data: Dict[str, Any], required_fields: Optional[List[str]] = None):
        """Validate document response structure."""
        default_fields = ["id", "filename", "size", "content_type", "upload_timestamp", "processing_status"]
        fields_to_check = required_fields or default_fields
        
        for field in fields_to_check:
            assert field in data, f"Missing required field: {field}"
        
        # Validate specific field types
        if "size" in data:
            assert isinstance(data["size"], int) and data["size"] >= 0
        
        if "processing_status" in data:
            valid_statuses = ["pending", "processing", "completed", "failed"]
            assert data["processing_status"] in valid_statuses
    
    @staticmethod
    def validate_answer_response(data: Dict[str, Any]):
        """Validate Q&A answer response structure."""
        required_fields = ["answer", "question", "sources", "answer_id"]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Validate answer content
        assert isinstance(data["answer"], str) and len(data["answer"]) > 0
        assert isinstance(data["question"], str) and len(data["question"]) > 0
        assert isinstance(data["sources"], list)
        
        # Validate sources structure
        for source in data["sources"]:
            source_fields = ["document_id", "chunk_id", "content", "score"]
            for field in source_fields:
                assert field in source, f"Missing source field: {field}"
            
            assert 0.0 <= source["score"] <= 1.0, "Score should be between 0 and 1"
    
    @staticmethod
    def validate_chat_response(data: Dict[str, Any]):
        """Validate chat response structure."""
        required_fields = ["response", "session_id", "message_id", "conversation_length"]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        assert isinstance(data["response"], str) and len(data["response"]) > 0
        assert isinstance(data["conversation_length"], int) and data["conversation_length"] > 0


# Pytest fixtures using the helper classes
@pytest.fixture
def file_manager():
    """Provide a test file manager."""
    manager = TestFileManager()
    yield manager
    manager.cleanup()


@pytest.fixture
def api_helper():
    """Provide API test helper."""
    return APITestHelper()


@pytest.fixture
def perf_helper():
    """Provide performance test helper."""
    return PerformanceTestHelper()


@pytest.fixture
def mock_data():
    """Provide mock data generator."""
    return MockDataGenerator()


@pytest.fixture
def data_validator():
    """Provide test data validator."""
    return TestDataValidator()


# Custom pytest markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests that test individual components"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests that test component interactions"
    )
    config.addinivalue_line(
        "markers", "api: API endpoint tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests"
    )
    config.addinivalue_line(
        "markers", "performance: Performance and load tests"
    )
    config.addinivalue_line(
        "markers", "requires_gemini: Tests that require Google Gemini API key"
    )
    config.addinivalue_line(
        "markers", "requires_files: Tests that require test files"
    )