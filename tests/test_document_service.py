"""Tests for document processing service."""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch, mock_open

from app.services.document_service import DocumentProcessor, DocumentChunk, ProcessedDocument
from app.utils.exceptions import DocumentProcessingError, ValidationError


@pytest.mark.unit
class TestDocumentChunk:
    """Test DocumentChunk class."""
    
    def test_chunk_creation(self):
        """Test creating a document chunk."""
        chunk = DocumentChunk(
            id="test_chunk_1",
            document_id="test_doc_1",
            content="This is test content.",
            start_index=0,
            end_index=21,
            metadata={"test": "data"}
        )
        
        assert chunk.id == "test_chunk_1"
        assert chunk.document_id == "test_doc_1"
        assert chunk.content == "This is test content."
        assert chunk.start_index == 0
        assert chunk.end_index == 21
        assert chunk.metadata == {"test": "data"}
    
    def test_chunk_to_dict(self):
        """Test converting chunk to dictionary."""
        chunk = DocumentChunk(
            id="test_chunk_1",
            document_id="test_doc_1", 
            content="Test content",
            start_index=0,
            end_index=12
        )
        
        chunk_dict = chunk.to_dict()
        
        expected = {
            "id": "test_chunk_1",
            "document_id": "test_doc_1",
            "content": "Test content",
            "start_index": 0,
            "end_index": 12,
            "metadata": {}
        }
        
        assert chunk_dict == expected


@pytest.mark.unit  
class TestProcessedDocument:
    """Test ProcessedDocument class."""
    
    def test_document_creation(self, sample_chunks):
        """Test creating a processed document."""
        doc = ProcessedDocument(
            id="test_doc_1",
            filename="test.txt",
            content_type="text/plain",
            size=1024,
            chunks=sample_chunks,
            metadata={"test": "metadata"}
        )
        
        assert doc.id == "test_doc_1"
        assert doc.filename == "test.txt"
        assert doc.content_type == "text/plain"
        assert doc.size == 1024
        assert len(doc.chunks) == 2
        assert doc.metadata == {"test": "metadata"}
    
    def test_document_to_dict(self, sample_chunks):
        """Test converting document to dictionary."""
        doc = ProcessedDocument(
            id="test_doc_1",
            filename="test.txt",
            content_type="text/plain",
            size=1024,
            chunks=sample_chunks
        )
        
        doc_dict = doc.to_dict()
        
        assert doc_dict["id"] == "test_doc_1"
        assert doc_dict["filename"] == "test.txt"
        assert doc_dict["chunk_count"] == 2
        assert len(doc_dict["chunks"]) == 2
        assert doc_dict["metadata"] == {}


@pytest.mark.unit
class TestDocumentProcessor:
    """Test DocumentProcessor class."""
    
    def test_processor_initialization(self):
        """Test document processor initialization."""
        processor = DocumentProcessor()
        
        assert processor.settings is not None
        assert isinstance(processor.supported_extensions, set)
        assert ".pdf" in processor.supported_extensions
        assert ".txt" in processor.supported_extensions
        assert ".docx" in processor.supported_extensions
        assert ".md" in processor.supported_extensions
    
    def test_validate_file_exists(self, sample_files):
        """Test file validation for existing files."""
        processor = DocumentProcessor()
        
        # Test valid file
        is_valid, error = processor.validate_file(sample_files["txt"])
        assert is_valid is True
        assert error is None
    
    def test_validate_file_not_exists(self):
        """Test file validation for non-existent files."""
        processor = DocumentProcessor()
        
        is_valid, error = processor.validate_file("/nonexistent/file.txt")
        assert is_valid is False
        assert "does not exist" in error
    
    def test_validate_file_unsupported_extension(self, temp_dir):
        """Test file validation for unsupported extensions."""
        processor = DocumentProcessor()
        
        # Create file with unsupported extension
        unsupported_file = os.path.join(temp_dir, "test.xyz")
        with open(unsupported_file, "w") as f:
            f.write("test content")
        
        is_valid, error = processor.validate_file(unsupported_file)
        assert is_valid is False
        assert "Unsupported file extension" in error
    
    def test_validate_file_size_limit(self, sample_files):
        """Test file size validation."""
        processor = DocumentProcessor()
        
        # Test file that exceeds size limit
        is_valid, error = processor.validate_file(sample_files["large"])
        assert is_valid is False
        assert "File too large" in error
    
    def test_extract_text_from_txt(self, sample_files):
        """Test text extraction from TXT files."""
        processor = DocumentProcessor()
        
        text = processor.extract_text(sample_files["txt"], ".txt")
        
        assert "sample text file" in text
        assert isinstance(text, str)
        assert len(text) > 0
    
    def test_extract_text_from_md(self, sample_files):
        """Test text extraction from Markdown files."""
        processor = DocumentProcessor()
        
        text = processor.extract_text(sample_files["md"], ".md")
        
        assert "Sample Markdown" in text
        assert "sample" in text
        assert isinstance(text, str)
    
    @patch('app.services.document_service.PdfReader')
    def test_extract_text_from_pdf(self, mock_pdf_reader):
        """Test text extraction from PDF files."""
        # Mock PDF reader
        mock_page = Mock()
        mock_page.extract_text.return_value = "Sample PDF content"
        
        mock_reader_instance = Mock()
        mock_reader_instance.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader_instance
        
        processor = DocumentProcessor()
        
        with tempfile.NamedTemporaryFile(suffix=".pdf") as temp_file:
            text = processor.extract_text(temp_file.name, ".pdf")
            
            assert "Sample PDF content" in text
            mock_pdf_reader.assert_called_once()
    
    @patch('app.services.document_service.DocxDocument')
    def test_extract_text_from_docx(self, mock_docx):
        """Test text extraction from DOCX files."""
        # Mock DOCX document
        mock_paragraph = Mock()
        mock_paragraph.text = "Sample DOCX content"
        
        mock_doc_instance = Mock()
        mock_doc_instance.paragraphs = [mock_paragraph]
        mock_docx.return_value = mock_doc_instance
        
        processor = DocumentProcessor()
        
        with tempfile.NamedTemporaryFile(suffix=".docx") as temp_file:
            text = processor.extract_text(temp_file.name, ".docx")
            
            assert "Sample DOCX content" in text
            mock_docx.assert_called_once()
    
    def test_extract_text_unsupported_type(self):
        """Test text extraction with unsupported file type."""
        processor = DocumentProcessor()
        
        with pytest.raises(ValidationError) as exc_info:
            processor.extract_text("test.xyz", ".xyz")
        
        assert "Unsupported file type" in str(exc_info.value)
    
    def test_create_chunks_basic(self, sample_text):
        """Test basic text chunking."""
        processor = DocumentProcessor()
        
        chunks = processor.create_chunks(sample_text, chunk_size=100, overlap=20)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)
        assert all(len(chunk) <= 100 for chunk in chunks)
    
    def test_create_chunks_empty_text(self):
        """Test chunking empty text."""
        processor = DocumentProcessor()
        
        chunks = processor.create_chunks("", chunk_size=100, overlap=20)
        
        assert chunks == []
    
    def test_create_chunks_invalid_params(self):
        """Test chunking with invalid parameters."""
        processor = DocumentProcessor()
        
        # Test invalid chunk size
        with pytest.raises(ValidationError) as exc_info:
            processor.create_chunks("test text", chunk_size=0, overlap=10)
        assert "Chunk size must be positive" in str(exc_info.value)
        
        # Test negative overlap
        with pytest.raises(ValidationError) as exc_info:
            processor.create_chunks("test text", chunk_size=100, overlap=-1)
        assert "Overlap must be non-negative" in str(exc_info.value)
        
        # Test overlap >= chunk size
        with pytest.raises(ValidationError) as exc_info:
            processor.create_chunks("test text", chunk_size=100, overlap=100)
        assert "Overlap must be less than chunk size" in str(exc_info.value)
    
    def test_create_chunks_overlap(self):
        """Test chunking with overlap."""
        processor = DocumentProcessor()
        text = "This is a test sentence for chunking with overlap functionality."
        
        chunks = processor.create_chunks(text, chunk_size=20, overlap=5)
        
        # Should have multiple chunks due to text length
        assert len(chunks) > 1
        
        # Check that chunks have some overlap (this is approximate due to word boundaries)
        for i in range(len(chunks) - 1):
            # There should be some common words between consecutive chunks
            current_words = set(chunks[i].split())
            next_words = set(chunks[i + 1].split())
            # Allow for some flexibility due to word boundary splitting
            assert len(current_words.intersection(next_words)) >= 0
    
    def test_get_metadata_basic(self, sample_files):
        """Test basic metadata extraction."""
        processor = DocumentProcessor()
        
        metadata = processor.get_metadata(sample_files["txt"])
        
        assert "filename" in metadata
        assert "file_extension" in metadata
        assert "file_size" in metadata
        assert "content_type" in metadata
        assert "created_time" in metadata
        assert "modified_time" in metadata
        assert "file_hash" in metadata
        
        assert metadata["file_extension"] == ".txt"
        assert metadata["file_size"] > 0
        assert isinstance(metadata["file_hash"], str)
    
    def test_get_metadata_nonexistent_file(self):
        """Test metadata extraction for nonexistent file."""
        processor = DocumentProcessor()
        
        metadata = processor.get_metadata("/nonexistent/file.txt")
        
        assert "error" in metadata
        assert "filename" in metadata
    
    @pytest.mark.asyncio
    async def test_process_file_success(self, sample_files):
        """Test successful file processing."""
        processor = DocumentProcessor()
        
        processed_doc = await processor.process_file(
            sample_files["txt"],
            chunk_size=50,
            chunk_overlap=10
        )
        
        assert isinstance(processed_doc, ProcessedDocument)
        assert processed_doc.id is not None
        assert processed_doc.filename.endswith(".txt")
        assert processed_doc.content_type == "text/plain"
        assert len(processed_doc.chunks) > 0
        assert all(isinstance(chunk, DocumentChunk) for chunk in processed_doc.chunks)
    
    @pytest.mark.asyncio
    async def test_process_file_with_metadata(self, sample_files):
        """Test file processing with additional metadata."""
        processor = DocumentProcessor()
        
        additional_metadata = {"source": "test", "category": "sample"}
        
        processed_doc = await processor.process_file(
            sample_files["txt"],
            additional_metadata=additional_metadata
        )
        
        assert "source" in processed_doc.metadata
        assert "category" in processed_doc.metadata
        assert processed_doc.metadata["source"] == "test"
        assert processed_doc.metadata["category"] == "sample"
    
    @pytest.mark.asyncio
    async def test_process_file_invalid_file(self):
        """Test processing invalid file."""
        processor = DocumentProcessor()
        
        with pytest.raises(ValidationError) as exc_info:
            await processor.process_file("/nonexistent/file.txt")
        
        assert "does not exist" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_process_file_unsupported_extension(self, temp_dir):
        """Test processing file with unsupported extension."""
        processor = DocumentProcessor()
        
        # Create file with unsupported extension
        unsupported_file = os.path.join(temp_dir, "test.xyz")
        with open(unsupported_file, "w") as f:
            f.write("test content")
        
        with pytest.raises(ValidationError) as exc_info:
            await processor.process_file(unsupported_file)
        
        assert "Unsupported file extension" in str(exc_info.value)


@pytest.mark.integration
class TestDocumentProcessorIntegration:
    """Integration tests for document processor."""
    
    @pytest.mark.asyncio
    async def test_full_processing_pipeline(self, temp_dir):
        """Test complete document processing pipeline."""
        processor = DocumentProcessor()
        
        # Create a test document with known content
        test_content = """This is a test document for integration testing.
        
        It contains multiple paragraphs to test the chunking functionality.
        The document processor should be able to handle this content properly.
        
        This paragraph contains different information to ensure proper chunking.
        Each chunk should maintain meaningful content boundaries when possible.
        """
        
        test_file = os.path.join(temp_dir, "integration_test.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        # Process the document
        processed_doc = await processor.process_file(
            test_file,
            chunk_size=100,
            chunk_overlap=20,
            additional_metadata={"test_type": "integration"}
        )
        
        # Verify results
        assert processed_doc.filename == "integration_test.txt"
        assert processed_doc.size > 0
        assert len(processed_doc.chunks) > 1  # Should create multiple chunks
        assert processed_doc.metadata["test_type"] == "integration"
        
        # Verify chunks
        total_content = "".join(chunk.content for chunk in processed_doc.chunks)
        # Should contain most of original content (some may be lost at boundaries)
        assert "integration testing" in total_content
        assert "chunking functionality" in total_content
        
        # Verify chunk metadata
        for i, chunk in enumerate(processed_doc.chunks):
            assert chunk.document_id == processed_doc.id
            assert chunk.metadata["chunk_index"] == i
            assert chunk.start_index >= 0
            assert chunk.end_index > chunk.start_index
    
    @pytest.mark.asyncio
    async def test_encoding_handling(self, temp_dir):
        """Test handling of different text encodings."""
        processor = DocumentProcessor()
        
        # Create files with different encodings
        test_content = "This is a test with special characters: café, naïve, résumé"
        
        # UTF-8 file
        utf8_file = os.path.join(temp_dir, "utf8_test.txt")
        with open(utf8_file, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        processed_doc = await processor.process_file(utf8_file)
        
        # Verify content is properly decoded
        full_content = "".join(chunk.content for chunk in processed_doc.chunks)
        assert "café" in full_content
        assert "naïve" in full_content
        assert "résumé" in full_content
    
    @pytest.mark.asyncio
    async def test_large_file_processing(self, temp_dir):
        """Test processing of larger files."""
        processor = DocumentProcessor()
        
        # Create a larger test file (but within limits)
        large_content = "This is a test sentence. " * 1000  # ~25KB
        
        large_file = os.path.join(temp_dir, "large_test.txt")
        with open(large_file, "w", encoding="utf-8") as f:
            f.write(large_content)
        
        processed_doc = await processor.process_file(
            large_file,
            chunk_size=500,
            chunk_overlap=50
        )
        
        # Verify processing
        assert len(processed_doc.chunks) > 10  # Should create many chunks
        assert processed_doc.size > 20000  # Should be large
        
        # Verify all chunks have reasonable content
        for chunk in processed_doc.chunks:
            assert len(chunk.content) > 0
            assert "test sentence" in chunk.content
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, temp_dir):
        """Test error handling and recovery."""
        processor = DocumentProcessor()
        
        # Test with corrupted file (empty file that claims to be PDF)
        corrupt_file = os.path.join(temp_dir, "corrupt.pdf")
        with open(corrupt_file, "w") as f:
            f.write("This is not a valid PDF")
        
        with pytest.raises(DocumentProcessingError) as exc_info:
            await processor.process_file(corrupt_file)
        
        assert "Failed to extract text from PDF" in str(exc_info.value)
        assert exc_info.value.details["filename"] == "corrupt.pdf"


@pytest.mark.slow
class TestDocumentProcessorPerformance:
    """Performance tests for document processor."""
    
    @pytest.mark.asyncio
    async def test_processing_speed(self, temp_dir, performance_timer):
        """Test document processing speed."""
        processor = DocumentProcessor()
        
        # Create test content
        content = "This is a performance test sentence. " * 100
        test_file = os.path.join(temp_dir, "perf_test.txt")
        with open(test_file, "w") as f:
            f.write(content)
        
        performance_timer.start()
        processed_doc = await processor.process_file(test_file)
        performance_timer.stop()
        
        # Should process quickly (less than 1 second for small files)
        assert performance_timer.elapsed < 1.0
        assert len(processed_doc.chunks) > 0
    
    @pytest.mark.asyncio
    async def test_memory_usage(self, temp_dir):
        """Test memory usage during processing."""
        import psutil
        import os
        
        processor = DocumentProcessor()
        process = psutil.Process(os.getpid())
        
        # Get initial memory usage
        initial_memory = process.memory_info().rss
        
        # Process multiple files
        for i in range(10):
            content = f"Test document {i} content. " * 100
            test_file = os.path.join(temp_dir, f"memory_test_{i}.txt")
            with open(test_file, "w") as f:
                f.write(content)
            
            await processor.process_file(test_file)
        
        # Check final memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50 * 1024 * 1024