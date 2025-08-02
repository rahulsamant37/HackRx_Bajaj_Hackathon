"""Tests for RAG service."""

import pytest
import numpy as np
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from app.services.rag_service import RAGService, SearchResult, AnswerResponse
from app.utils.exceptions import EmbeddingError, VectorStoreError, GeminiAPIError, ValidationError


@pytest.mark.unit
class TestSearchResult:
    """Test SearchResult class."""
    
    def test_search_result_creation(self):
        """Test creating a search result."""
        result = SearchResult(
            document_id="doc_1",
            chunk_id="chunk_1",
            content="Test content",
            score=0.85,
            metadata={"test": "data"}
        )
        
        assert result.document_id == "doc_1"
        assert result.chunk_id == "chunk_1"
        assert result.content == "Test content"
        assert result.score == 0.85
        assert result.metadata == {"test": "data"}
    
    def test_search_result_to_dict(self):
        """Test converting search result to dictionary."""
        result = SearchResult(
            document_id="doc_1",
            chunk_id="chunk_1",
            content="Test content",
            score=0.85
        )
        
        result_dict = result.to_dict()
        
        expected = {
            "document_id": "doc_1",
            "chunk_id": "chunk_1",
            "content": "Test content",
            "score": 0.85,
            "metadata": {}
        }
        
        assert result_dict == expected


@pytest.mark.unit
class TestAnswerResponse:
    """Test AnswerResponse class."""
    
    def test_answer_response_creation(self):
        """Test creating an answer response."""
        sources = [SearchResult("doc_1", "chunk_1", "Test content", 0.85)]
        
        response = AnswerResponse(
            answer="This is the answer.",
            question="What is the test?",
            sources=sources,
            answer_id="answer_123",
            confidence=0.9,
            processing_time=1.5,
            token_usage={"total": 100}
        )
        
        assert response.answer == "This is the answer."
        assert response.question == "What is the test?"
        assert len(response.sources) == 1
        assert response.answer_id == "answer_123"
        assert response.confidence == 0.9
        assert response.processing_time == 1.5
        assert response.token_usage == {"total": 100}
    
    def test_answer_response_to_dict(self):
        """Test converting answer response to dictionary."""
        sources = [SearchResult("doc_1", "chunk_1", "Test content", 0.85)]
        
        response = AnswerResponse(
            answer="Test answer",
            question="Test question",
            sources=sources,
            answer_id="answer_123"
        )
        
        response_dict = response.to_dict()
        
        assert response_dict["answer"] == "Test answer"
        assert response_dict["question"] == "Test question"
        assert len(response_dict["sources"]) == 1
        assert response_dict["answer_id"] == "answer_123"


@pytest.mark.unit
class TestRAGService:
    """Test RAGService class."""
    
    @patch('app.services.rag_service.ChatGoogleGenerativeAI')
    @patch('app.services.rag_service.GoogleGenerativeAIEmbeddings')
    @patch('faiss.IndexFlatL2')
    def test_rag_service_initialization(self, mock_faiss, mock_embeddings, mock_chat, test_settings):
        """Test RAG service initialization."""
        mock_index = Mock()
        mock_index.ntotal = 0
        mock_faiss.return_value = mock_index
        
        rag_service = RAGService()
        
        assert rag_service.settings is not None
        assert rag_service.embeddings is not None
        assert rag_service.llm is not None
        mock_embeddings.assert_called_once()
        mock_chat.assert_called_once()
        mock_faiss.assert_called_once_with(768)  # Gemini vector dimension
    
    @pytest.mark.asyncio
    async def test_create_embeddings_success(self, mock_rag_service):
        """Test successful embedding creation."""
        texts = ["Test text 1", "Test text 2"]
        
        embeddings = await mock_rag_service._create_embeddings(texts)
        
        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape == (2, 768)  # 2 texts, 768 dimensions for Gemini
        mock_rag_service.embeddings.aembed_documents.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_embeddings_empty_list(self, mock_rag_service):
        """Test embedding creation with empty list."""
        embeddings = await mock_rag_service._create_embeddings([])
        
        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape == (0, 768)
        # Should not call Gemini API for empty list
        mock_rag_service.embeddings.aembed_documents.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_create_embeddings_api_error(self, mock_rag_service):
        """Test embedding creation with API error."""
        mock_rag_service.embeddings.aembed_documents.side_effect = Exception("API Error")
        
        with pytest.raises(EmbeddingError) as exc_info:
            await mock_rag_service._create_embeddings(["Test text"])
        
        assert "Failed to create embeddings" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_embeddings_rate_limit(self, mock_rag_service):
        """Test embedding creation with rate limit error."""
        mock_rag_service.embeddings.aembed_documents.side_effect = Exception("rate limit exceeded")
        
        with pytest.raises(EmbeddingError) as exc_info:
            await mock_rag_service._create_embeddings(["Test text"])
        
        assert "Google Gemini API rate limit exceeded" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_add_document_success(self, mock_rag_service, sample_processed_document):
        """Test successful document addition."""
        # Mock FAISS index
        mock_rag_service.index = Mock()
        mock_rag_service.index.ntotal = 0
        mock_rag_service.index.add = Mock()
        
        # Mock save index
        mock_rag_service._save_index = AsyncMock()
        
        doc_id = await mock_rag_service.add_document(sample_processed_document)
        
        assert doc_id == sample_processed_document.id
        mock_rag_service.index.add.assert_called_once()
        mock_rag_service._save_index.assert_called_once()
        
        # Check metadata was stored
        assert sample_processed_document.id in mock_rag_service.document_chunks
    
    @pytest.mark.asyncio
    async def test_add_document_no_chunks(self, mock_rag_service, sample_processed_document):
        """Test adding document with no chunks."""
        sample_processed_document.chunks = []
        
        with pytest.raises(VectorStoreError) as exc_info:
            await mock_rag_service.add_document(sample_processed_document)
        
        assert "no chunks to add" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_add_document_embedding_error(self, mock_rag_service, sample_processed_document):
        """Test document addition with embedding error."""
        mock_rag_service._create_embeddings = AsyncMock(side_effect=EmbeddingError("Embedding failed"))
        
        with pytest.raises(EmbeddingError):
            await mock_rag_service.add_document(sample_processed_document)
    
    @pytest.mark.asyncio
    async def test_search_similar_success(self, populated_rag_service):
        """Test successful similarity search."""
        query = "test query"
        
        results = await populated_rag_service.search_similar(query, k=2)
        
        assert isinstance(results, list)
        assert len(results) <= 2
        
        # Check result structure
        for result in results:
            assert isinstance(result, SearchResult)
            assert hasattr(result, 'document_id')
            assert hasattr(result, 'chunk_id')
            assert hasattr(result, 'content')
            assert hasattr(result, 'score')
    
    @pytest.mark.asyncio
    async def test_search_similar_empty_query(self, mock_rag_service):
        """Test search with empty query."""
        with pytest.raises(ValidationError) as exc_info:
            await mock_rag_service.search_similar("", k=5)
        
        assert "Query cannot be empty" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_search_similar_invalid_k(self, mock_rag_service):
        """Test search with invalid k value."""
        with pytest.raises(ValidationError) as exc_info:
            await mock_rag_service.search_similar("test", k=0)
        
        assert "k must be positive" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_search_similar_empty_index(self, mock_rag_service):
        """Test search on empty index."""
        mock_rag_service.index.ntotal = 0
        
        results = await mock_rag_service.search_similar("test query")
        
        assert results == []
    
    @pytest.mark.asyncio
    async def test_answer_question_success(self, populated_rag_service):
        """Test successful question answering."""
        question = "What is this about?"
        
        answer = await populated_rag_service.answer_question(question)
        
        assert isinstance(answer, AnswerResponse)
        assert answer.answer == "This is a test answer."
        assert answer.question == question
        assert len(answer.sources) >= 0
        assert answer.answer_id is not None
        assert answer.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_answer_question_empty_question(self, mock_rag_service):
        """Test answering empty question."""
        with pytest.raises(ValidationError) as exc_info:
            await mock_rag_service.answer_question("")
        
        assert "Question cannot be empty" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_answer_question_no_context(self, mock_rag_service):
        """Test answering question with no relevant context."""
        # Mock empty search results
        mock_rag_service.search_similar = AsyncMock(return_value=[])
        
        answer = await mock_rag_service.answer_question("What is this about?")
        
        assert isinstance(answer, AnswerResponse)
        assert answer.answer == "This is a test answer."
        assert len(answer.sources) == 0
    
    @pytest.mark.asyncio
    async def test_answer_question_gemini_error(self, mock_rag_service):
        """Test question answering with Gemini API error."""
        mock_rag_service.llm.ainvoke.side_effect = Exception("API Error")
        mock_rag_service.search_similar = AsyncMock(return_value=[])
        
        with pytest.raises(GeminiAPIError) as exc_info:
            await mock_rag_service.answer_question("Test question")
        
        assert "Failed to generate answer" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_delete_document_success(self, populated_rag_service):
        """Test successful document deletion."""
        # Add document first
        populated_rag_service.document_chunks["test_doc"] = [0, 1, 2]
        populated_rag_service.chunk_metadata = {
            0: {"document_id": "test_doc"},
            1: {"document_id": "test_doc"},
            2: {"document_id": "test_doc"}
        }
        populated_rag_service._save_index = AsyncMock()
        
        result = await populated_rag_service.delete_document("test_doc")
        
        assert result is True
        assert "test_doc" not in populated_rag_service.document_chunks
        assert 0 not in populated_rag_service.chunk_metadata
        populated_rag_service._save_index.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_document_not_found(self, mock_rag_service):
        """Test deleting non-existent document."""
        result = await mock_rag_service.delete_document("nonexistent_doc")
        
        assert result is False
    
    def test_get_stats(self, mock_rag_service):
        """Test getting system statistics."""
        mock_rag_service.index.ntotal = 10
        mock_rag_service.document_chunks = {"doc1": [0, 1], "doc2": [2, 3, 4]}
        mock_rag_service.chunk_metadata = {0: {}, 1: {}, 2: {}, 3: {}, 4: {}}
        
        stats = mock_rag_service.get_stats()
        
        assert stats["total_documents"] == 2
        assert stats["total_chunks"] == 5
        assert stats["vector_store_size"] == 10
        assert stats["vector_dimension"] == 1536
        assert "last_updated" in stats
    
    def test_get_stats_error(self, mock_rag_service):
        """Test getting stats with error."""
        mock_rag_service.document_chunks = None  # Cause error
        
        stats = mock_rag_service.get_stats()
        
        assert "error" in stats
        assert stats["total_documents"] == 0
    
    def test_create_qa_prompt(self, mock_rag_service):
        """Test QA prompt creation."""
        question = "What is the capital of France?"
        context = "France is a country in Europe. Paris is the capital city of France."
        
        prompt = mock_rag_service._create_qa_prompt(question, context)
        
        assert question in prompt
        assert context in prompt
        assert "Context information:" in prompt
    
    def test_create_qa_prompt_no_context(self, mock_rag_service):
        """Test QA prompt creation with no context."""
        question = "What is the capital of France?"
        context = ""
        
        prompt = mock_rag_service._create_qa_prompt(question, context)
        
        assert question in prompt
        assert "No relevant context found" in prompt
    
    def test_calculate_confidence(self, mock_rag_service):
        """Test confidence calculation."""
        sources = [
            SearchResult("doc1", "chunk1", "content1", 0.9),
            SearchResult("doc1", "chunk2", "content2", 0.8),
            SearchResult("doc1", "chunk3", "content3", 0.7),
        ]
        
        confidence = mock_rag_service._calculate_confidence(sources)
        
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0  # Should be positive with good sources
    
    def test_calculate_confidence_no_sources(self, mock_rag_service):
        """Test confidence calculation with no sources."""
        confidence = mock_rag_service._calculate_confidence([])
        
        assert confidence == 0.0


@pytest.mark.integration
class TestRAGServiceIntegration:
    """Integration tests for RAG service."""
    
    @pytest.mark.asyncio
    async def test_full_rag_pipeline(self, mock_rag_service, sample_processed_document):
        """Test complete RAG pipeline from document to answer."""
        # Setup mocks for full pipeline
        mock_rag_service.index = Mock()
        mock_rag_service.index.ntotal = 0
        mock_rag_service.index.add = Mock()
        mock_rag_service.index.search = Mock(return_value=(
            np.array([[0.5]]),  # distances
            np.array([[0]])     # indices
        ))
        mock_rag_service._save_index = AsyncMock()
        mock_rag_service._load_index = AsyncMock()
        
        # Add document
        doc_id = await mock_rag_service.add_document(sample_processed_document)
        assert doc_id == sample_processed_document.id
        
        # Search for similar content
        results = await mock_rag_service.search_similar("test query")
        assert isinstance(results, list)
        
        # Answer question
        answer = await mock_rag_service.answer_question("What is this about?")
        assert isinstance(answer, AnswerResponse)
        assert answer.answer is not None
    
    @pytest.mark.asyncio
    async def test_multiple_documents_search(self, mock_rag_service, test_data_factory):
        """Test searching across multiple documents."""
        # Create multiple test documents
        doc1 = test_data_factory.create_processed_document(
            "doc1", "test1.txt",
            [test_data_factory.create_document_chunk("chunk1", "doc1", "Python programming")]
        )
        doc2 = test_data_factory.create_processed_document(
            "doc2", "test2.txt", 
            [test_data_factory.create_document_chunk("chunk2", "doc2", "Machine learning")]
        )
        
        # Setup mocks
        mock_rag_service.index = Mock()
        mock_rag_service.index.ntotal = 0
        mock_rag_service.index.add = Mock()
        mock_rag_service._save_index = AsyncMock()
        
        # Add documents
        await mock_rag_service.add_document(doc1)
        await mock_rag_service.add_document(doc2)
        
        # Verify both documents are tracked
        assert "doc1" in mock_rag_service.document_chunks
        assert "doc2" in mock_rag_service.document_chunks
        
        # Verify stats
        stats = mock_rag_service.get_stats()
        assert stats["total_documents"] == 2
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, mock_rag_service, sample_processed_document):
        """Test error handling and recovery."""
        # Simulate embedding error
        mock_rag_service._create_embeddings = AsyncMock(side_effect=EmbeddingError("Test error"))
        
        with pytest.raises(EmbeddingError):
            await mock_rag_service.add_document(sample_processed_document)
        
        # Service should still be functional after error
        stats = mock_rag_service.get_stats()
        assert "total_documents" in stats
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, mock_rag_service, test_data_factory):
        """Test concurrent RAG operations."""
        import asyncio
        
        # Setup mocks
        mock_rag_service.index = Mock()
        mock_rag_service.index.ntotal = 0
        mock_rag_service.index.add = Mock()
        mock_rag_service._save_index = AsyncMock()
        
        # Create multiple documents
        docs = [
            test_data_factory.create_processed_document(f"doc{i}", f"test{i}.txt")
            for i in range(5)
        ]
        
        # Add documents concurrently
        tasks = [mock_rag_service.add_document(doc) for doc in docs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All operations should succeed
        assert all(not isinstance(result, Exception) for result in results)
        assert len(mock_rag_service.document_chunks) == 5


@pytest.mark.slow
class TestRAGServicePerformance:
    """Performance tests for RAG service."""
    
    @pytest.mark.asyncio
    async def test_search_performance(self, populated_rag_service, performance_timer):
        """Test search performance."""
        query = "test query for performance"
        
        performance_timer.start()
        results = await populated_rag_service.search_similar(query, k=10)
        performance_timer.stop()
        
        # Search should be fast (< 100ms for small index)
        assert performance_timer.elapsed < 0.1
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_answer_generation_performance(self, populated_rag_service, performance_timer):
        """Test answer generation performance."""
        question = "What is this document about?"
        
        performance_timer.start()
        answer = await populated_rag_service.answer_question(question)
        performance_timer.stop()
        
        # Answer generation should complete in reasonable time
        assert performance_timer.elapsed < 5.0  # 5 seconds max
        assert isinstance(answer, AnswerResponse)
    
    @pytest.mark.asyncio
    async def test_batch_embedding_performance(self, mock_rag_service, performance_timer):
        """Test batch embedding creation performance."""
        # Create many texts
        texts = [f"Test text number {i}" for i in range(100)]
        
        performance_timer.start()
        embeddings = await mock_rag_service._create_embeddings(texts)
        performance_timer.stop()
        
        # Should handle batch efficiently
        assert performance_timer.elapsed < 2.0  # 2 seconds for mock
        assert embeddings.shape[0] == 100


@pytest.mark.requires_gemini
class TestRAGServiceWithRealAPI:
    """Tests that require real Google Gemini API (marked for optional execution)."""
    
    @pytest.mark.asyncio
    async def test_real_embedding_creation(self):
        """Test embedding creation with real API (if API key available)."""
        try:
            rag_service = RAGService()
            texts = ["This is a test sentence."]
            
            embeddings = await rag_service._create_embeddings(texts)
            
            assert embeddings.shape == (1, 768)  # Gemini embeddings are 768-dimensional
            assert embeddings.dtype == np.float32
            
        except Exception as e:
            if "API key" in str(e) or "rate limit" in str(e):
                pytest.skip("Real Google Gemini API not available or rate limited")
            else:
                raise
    
    @pytest.mark.asyncio
    async def test_real_qa_generation(self):
        """Test Q&A generation with real API (if API key available)."""
        try:
            rag_service = RAGService()
            
            answer = await rag_service.answer_question(
                "What is 2+2?",
                context_limit=1000,
                max_results=1,
                temperature=0.0
            )
            
            assert isinstance(answer, AnswerResponse)
            assert answer.answer is not None
            assert len(answer.answer) > 0
            
        except Exception as e:
            if "API key" in str(e) or "rate limit" in str(e):
                pytest.skip("Real Google Gemini API not available or rate limited")
            else:
                raise