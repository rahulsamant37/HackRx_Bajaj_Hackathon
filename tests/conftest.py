"""Pytest configuration and shared fixtures."""

import os
import tempfile
import shutil
import asyncio
from typing import AsyncGenerator, Generator, Dict, Any
from unittest.mock import Mock, AsyncMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
import numpy as np

from app.main import create_app
from app.config import get_settings
from app.services.document_service import DocumentProcessor, ProcessedDocument, DocumentChunk
from app.services.rag_service import RAGService
from app.utils.logger import setup_logging


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings():
    """Test settings configuration."""
    # Set test environment variables
    os.environ.update({
        "ENVIRONMENT": "testing",
        "LOG_LEVEL": "WARNING",
        "GOOGLE_API_KEY": "test_key_not_real",
        "SECRET_KEY": "test_secret_key",
        "VECTOR_STORE_PATH": "./test_data/vector_store",
        "MAX_FILE_SIZE": "1048576",  # 1MB for testing
        "DEBUG": "False",
    })
    
    # Clear settings cache and get fresh settings
    get_settings.cache_clear()
    settings = get_settings()
    
    # Setup logging for tests
    setup_logging()
    
    return settings


@pytest.fixture(scope="session")
def temp_dir():
    """Create temporary directory for test files."""
    temp_path = tempfile.mkdtemp(prefix="rag_test_")
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(scope="session")
def test_app(test_settings):
    """Create test FastAPI application."""
    app = create_app()
    return app


@pytest.fixture
def client(test_app):
    """Create test client."""
    with TestClient(test_app) as client:
        yield client


@pytest.fixture
def mock_gemini_embeddings():
    """Mock Google Gemini embeddings for testing."""
    mock_embeddings = AsyncMock()
    
    # Mock embeddings response - Gemini embeddings are 768-dimensional
    # Return one embedding per input text
    def mock_embed_documents(texts):
        return [[0.1] * 768 for _ in texts]  # One embedding per text
    
    mock_embeddings.aembed_documents.side_effect = mock_embed_documents
    
    return mock_embeddings


@pytest.fixture 
def mock_gemini_chat():
    """Mock Google Gemini chat model for testing."""
    mock_chat = AsyncMock()
    
    # Mock chat completion response
    mock_response = Mock()
    mock_response.content = "This is a test answer."
    mock_response.usage_metadata = {
        "input_tokens": 50,
        "output_tokens": 20,
        "total_tokens": 70
    }
    mock_chat.ainvoke.return_value = mock_response
    
    return mock_chat


@pytest_asyncio.fixture(scope="function")
async def document_processor():
    """Create document processor instance."""
    return DocumentProcessor()


@pytest_asyncio.fixture(scope="function")
async def mock_rag_service(mock_gemini_embeddings, mock_gemini_chat):
    """Create RAG service with mocked Google Gemini components."""
    with patch('app.services.rag_service.GoogleGenerativeAIEmbeddings') as mock_embeddings_class, \
         patch('app.services.rag_service.ChatGoogleGenerativeAI') as mock_chat_class:
        
        mock_embeddings_class.return_value = mock_gemini_embeddings
        mock_chat_class.return_value = mock_gemini_chat
        
        rag_service = RAGService()
        yield rag_service


@pytest.fixture
def sample_text():
    """Sample text for testing."""
    return """
    This is a sample document for testing the RAG system.
    It contains multiple paragraphs with different information.
    
    The first paragraph talks about the importance of testing in software development.
    Testing ensures that our code works as expected and helps prevent bugs.
    
    The second paragraph discusses the benefits of automated testing.
    Automated tests can run quickly and provide immediate feedback to developers.
    
    Finally, this document concludes with some thoughts on best practices.
    Good tests should be fast, reliable, and easy to understand.
    """


@pytest.fixture
def sample_chunks():
    """Sample document chunks for testing."""
    return [
        DocumentChunk(
            id="chunk_1",
            document_id="test_doc_1",
            content="This is the first chunk of text for testing.",
            start_index=0,
            end_index=45,
            metadata={"chunk_index": 0}
        ),
        DocumentChunk(
            id="chunk_2", 
            document_id="test_doc_1",
            content="This is the second chunk with different content.",
            start_index=46,
            end_index=93,
            metadata={"chunk_index": 1}
        ),
    ]


@pytest.fixture
def sample_processed_document(sample_chunks):
    """Sample processed document for testing."""
    return ProcessedDocument(
        id="test_doc_1",
        filename="test_document.txt",
        content_type="text/plain",
        size=1024,
        chunks=sample_chunks,
        metadata={
            "upload_timestamp": "2024-01-01T00:00:00",
            "processing_time": 1.5,
        }
    )


@pytest.fixture
def sample_pdf_content():
    """Sample PDF content as bytes."""
    # This is a minimal PDF header - in real tests you'd use a proper PDF
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"


@pytest.fixture
def sample_files(temp_dir):
    """Create sample files for testing."""
    files = {}
    
    # Create sample text file
    txt_path = os.path.join(temp_dir, "sample.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("This is a sample text file for testing the document processor.")
    files["txt"] = txt_path
    
    # Create sample markdown file
    md_path = os.path.join(temp_dir, "sample.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Sample Markdown\n\nThis is a **sample** markdown file for testing.")
    files["md"] = md_path
    
    # Create sample large file (for size limit testing)
    large_path = os.path.join(temp_dir, "large.txt")
    with open(large_path, "w", encoding="utf-8") as f:
        f.write("x" * 2048000)  # 2MB file
    files["large"] = large_path
    
    return files


@pytest.fixture
def mock_faiss_index():
    """Mock FAISS index for testing."""
    mock_index = Mock()
    mock_index.ntotal = 0
    mock_index.add = Mock()
    mock_index.search = Mock(return_value=(
        np.array([[0.5, 0.7, 0.9]]),  # distances
        np.array([[0, 1, 2]])          # indices
    ))
    return mock_index


@pytest_asyncio.fixture(scope="function")
async def populated_rag_service(mock_rag_service, sample_processed_document):
    """RAG service with some test data."""
    with patch('faiss.IndexFlatL2') as mock_faiss:
        mock_index = Mock()
        mock_index.ntotal = 2
        mock_index.add = Mock()
        mock_index.search = Mock(return_value=(
            np.array([[0.3, 0.6]]),  # distances
            np.array([[0, 1]])        # indices
        ))
        mock_faiss.return_value = mock_index
        
        # Add test document
        await mock_rag_service.add_document(sample_processed_document)
        
        yield mock_rag_service


@pytest.fixture
def auth_headers():
    """Sample authentication headers."""
    return {"Authorization": "Bearer test_token"}


@pytest.fixture
def upload_file_data():
    """Sample file upload data."""
    return {
        "file": ("test.txt", "This is test content", "text/plain")
    }


class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_document_chunk(
        chunk_id: str = "test_chunk",
        document_id: str = "test_doc",
        content: str = "Test content",
        start_index: int = 0,
        end_index: int = 12,
        metadata: Dict[str, Any] = None
    ) -> DocumentChunk:
        """Create a test document chunk."""
        return DocumentChunk(
            id=chunk_id,
            document_id=document_id,
            content=content,
            start_index=start_index,
            end_index=end_index,
            metadata=metadata or {}
        )
    
    @staticmethod
    def create_processed_document(
        doc_id: str = "test_doc",
        filename: str = "test.txt",
        chunks: list = None,
        metadata: Dict[str, Any] = None
    ) -> ProcessedDocument:
        """Create a test processed document."""
        if chunks is None:
            chunks = [TestDataFactory.create_document_chunk()]
        
        return ProcessedDocument(
            id=doc_id,
            filename=filename,
            content_type="text/plain",
            size=len(chunks[0].content) if chunks else 0,
            chunks=chunks,
            metadata=metadata or {}
        )


@pytest.fixture
def test_data_factory():
    """Test data factory instance."""
    return TestDataFactory


# Performance testing fixtures
@pytest.fixture
def performance_timer():
    """Timer for performance testing."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


# Async testing utilities
@pytest_asyncio.fixture(scope="function")
async def async_mock():
    """Create async mock utility."""
    def create_async_mock(return_value=None, side_effect=None):
        mock = AsyncMock()
        if return_value is not None:
            mock.return_value = return_value
        if side_effect is not None:
            mock.side_effect = side_effect
        return mock
    
    return create_async_mock


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Cleanup test data after each test."""
    yield
    
    # Clean up any test files or data
    test_dirs = ["./test_data", "./logs/test", "./htmlcov"]
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir, ignore_errors=True)


# Error simulation fixtures
@pytest.fixture
def error_scenarios():
    """Common error scenarios for testing."""
    return {
        "GEMINI_rate_limit": Exception("Rate limit exceeded"),
        "GEMINI_invalid_key": Exception("Invalid API key"),
        "file_not_found": FileNotFoundError("File not found"),
        "permission_denied": PermissionError("Permission denied"),
        "vector_store_error": Exception("Vector store operation failed"),
        "embedding_error": Exception("Failed to create embeddings"),
    }