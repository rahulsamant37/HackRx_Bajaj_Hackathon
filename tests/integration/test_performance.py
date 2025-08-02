"""Performance and load tests for the RAG system."""

import pytest
import time
import io
from unittest.mock import patch, AsyncMock, Mock


@pytest.mark.performance
@pytest.mark.slow
class TestAPIPerformance:
    """Performance tests for API endpoints."""
    
    def test_health_endpoint_performance(self, client, perf_helper):
        """Test health endpoint performance under load."""
        def make_health_request():
            return client.get("/health")
        
        stats = perf_helper.run_concurrent_requests(
            make_health_request,
            num_requests=100,
            max_workers=10
        )
        
        # Health endpoint should be very fast
        perf_helper.assert_performance_requirements(
            stats,
            max_avg_duration=0.05,  # 50ms average
            max_duration=0.2,       # 200ms max
            min_success_rate=1.0    # 100% success
        )
        
        # All requests should return 200
        for result, error in stats['results']:
            assert error is None
            assert result.status_code == 200
    
    @patch('app.api.endpoints.qa.get_rag_service')
    def test_qa_endpoint_performance(self, mock_get_rag, client, perf_helper):
        """Test Q&A endpoint performance."""
        # Mock RAG service for consistent performance
        mock_rag = AsyncMock()
        
        from app.services.rag_service import AnswerResponse
        mock_answer = AnswerResponse(
            answer="Performance test answer",
            question="Performance question",
            sources=[],
            answer_id="perf_test"
        )
        mock_rag.answer_question.return_value = mock_answer
        mock_get_rag.return_value = mock_rag
        
        def make_qa_request():
            return client.post("/qa/ask", json={
                "question": "Performance test question"
            })
        
        stats = perf_helper.run_concurrent_requests(
            make_qa_request,
            num_requests=50,
            max_workers=5
        )
        
        # Q&A should complete reasonably quickly
        perf_helper.assert_performance_requirements(
            stats,
            max_avg_duration=0.5,   # 500ms average
            max_duration=2.0,       # 2s max
            min_success_rate=0.95   # 95% success
        )
    
    @patch('app.api.endpoints.documents.get_document_processor')
    @patch('app.api.endpoints.documents.get_rag_service')
    def test_document_upload_performance(self, mock_doc_rag, mock_processor, client, perf_helper):
        """Test document upload endpoint performance."""
        # Mock services
        processor_mock = AsyncMock()
        rag_mock = AsyncMock()
        
        from app.services.document_service import ProcessedDocument, DocumentChunk
        mock_chunk = DocumentChunk("chunk1", "perf_doc", "Performance content", 0, 20)
        mock_doc = ProcessedDocument("perf_doc", "perf.txt", "text/plain", 20, [mock_chunk])
        
        processor_mock.process_file.return_value = mock_doc
        mock_processor.return_value = processor_mock
        
        rag_mock.add_document.return_value = "perf_doc"
        mock_doc_rag.return_value = rag_mock
        
        def make_upload_request():
            with patch('app.api.endpoints.documents.save_upload_file', return_value="/tmp/perf.txt"):
                file_content = io.BytesIO(b"Performance test content")
                return client.post(
                    "/documents/upload",
                    files={"file": ("perf.txt", file_content, "text/plain")}
                )
        
        stats = perf_helper.run_concurrent_requests(
            make_upload_request,
            num_requests=20,
            max_workers=3
        )
        
        # Upload should handle concurrent requests well
        perf_helper.assert_performance_requirements(
            stats,
            max_avg_duration=1.0,   # 1s average
            max_duration=3.0,       # 3s max
            min_success_rate=0.9    # 90% success
        )
    
    def test_document_list_performance_with_large_dataset(self, client, perf_helper):
        """Test document listing performance with large dataset."""
        # Create large mock processing status
        large_status = {
            f"doc_{i}": {
                "filename": f"test_{i}.txt",
                "status": "completed",
                "started_at": "2024-01-01T00:00:00",
                "chunk_count": 5
            }
            for i in range(1000)
        }
        
        def make_list_request():
            with patch('app.api.endpoints.documents.get_rag_service'), \
                 patch('app.api.endpoints.documents.processing_status', large_status):
                return client.get("/documents/?limit=50")
        
        stats = perf_helper.run_concurrent_requests(
            make_list_request,
            num_requests=20,
            max_workers=5
        )
        
        # List endpoint should handle large datasets efficiently
        perf_helper.assert_performance_requirements(
            stats,
            max_avg_duration=0.2,   # 200ms average
            max_duration=1.0,       # 1s max
            min_success_rate=1.0    # 100% success
        )


@pytest.mark.performance
class TestServicePerformance:
    """Performance tests for core services."""
    
    @pytest.mark.asyncio 
    async def test_document_processing_performance(self, mock_data, perf_helper):
        """Test document processing performance."""
        from app.services.document_service import DocumentProcessor
        
        processor = DocumentProcessor()
        
        # Create test content of various sizes
        test_contents = [
            mock_data.generate_document_content("technology", 500),   # Small
            mock_data.generate_document_content("science", 2000),     # Medium
            mock_data.generate_document_content("business", 5000),    # Large
        ]
        
        processing_times = []
        
        for content in test_contents:
            # Create temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            try:
                start_time = time.time()
                processed_doc = await processor.process_file(temp_path)
                processing_time = time.time() - start_time
                
                processing_times.append(processing_time)
                
                # Verify processing completed successfully
                assert processed_doc is not None
                assert len(processed_doc.chunks) > 0
                
                # Processing should scale reasonably with content size
                assert processing_time < 2.0  # Max 2 seconds
                
            finally:
                import os
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
        
        # Processing time should increase with content size but remain reasonable
        assert all(t < 2.0 for t in processing_times)
        print(f"Processing times: {processing_times}")
    
    @pytest.mark.asyncio
    async def test_embedding_batch_performance(self, mock_rag_service, perf_helper):
        """Test embedding creation performance with different batch sizes."""
        batch_sizes = [1, 10, 50, 100]
        performance_results = {}
        
        for batch_size in batch_sizes:
            texts = [f"Test text number {i}" for i in range(batch_size)]
            
            start_time = time.time()
            embeddings = await mock_rag_service._create_embeddings(texts)
            processing_time = time.time() - start_time
            
            performance_results[batch_size] = {
                'time': processing_time,
                'per_text': processing_time / batch_size if batch_size > 0 else 0,
                'embeddings_shape': embeddings.shape
            }
            
            # Verify embeddings were created
            assert embeddings.shape[0] == batch_size
            assert embeddings.shape[1] == 1536  # Standard dimension
        
        # Larger batches should be more efficient per text
        assert performance_results[100]['per_text'] <= performance_results[1]['per_text']
        
        print("Embedding performance results:", performance_results)
    
    @pytest.mark.asyncio
    async def test_vector_search_performance(self, populated_rag_service, perf_helper):
        """Test vector search performance with different parameters."""
        search_params = [
            {"k": 5, "query": "short query"},
            {"k": 10, "query": "medium length query with more words"},
            {"k": 20, "query": "this is a longer query that contains more words and should test the performance of the search system"},
        ]
        
        search_times = []
        
        for params in search_params:
            start_time = time.time()
            results = await populated_rag_service.search_similar(
                params["query"], 
                k=params["k"]
            )
            search_time = time.time() - start_time
            
            search_times.append(search_time)
            
            # Verify search completed successfully
            assert isinstance(results, list)
            assert len(results) <= params["k"]
            
            # Search should be fast
            assert search_time < 0.5  # Max 500ms
        
        # All searches should complete quickly
        avg_search_time = sum(search_times) / len(search_times)
        assert avg_search_time < 0.2  # Average under 200ms
        
        print(f"Search times: {search_times}")


@pytest.mark.performance
class TestMemoryPerformance:
    """Memory usage and efficiency tests."""
    
    def test_memory_usage_during_operations(self, client):
        """Test memory usage during various operations."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Mock services to control memory usage
        with patch('app.api.endpoints.qa.get_rag_service') as mock_get_rag:
            mock_rag = AsyncMock()
            
            from app.services.rag_service import AnswerResponse
            mock_answer = AnswerResponse(
                answer="Memory test answer",
                question="Memory test",
                sources=[],
                answer_id="memory_test"
            )
            mock_rag.answer_question.return_value = mock_answer
            mock_get_rag.return_value = mock_rag
            
            # Perform many operations
            for i in range(100):
                # Q&A requests
                response = client.post("/qa/ask", json={
                    "question": f"Memory test question {i}"
                })
                assert response.status_code == 200
                
                # Health checks
                health_response = client.get("/health")
                assert health_response.status_code == 200
                
                # Check memory every 20 operations
                if i % 20 == 0:
                    current_memory = process.memory_info().rss
                    memory_increase = current_memory - initial_memory
                    
                    # Memory increase should be reasonable (< 50MB per 20 operations)
                    assert memory_increase < 50 * 1024 * 1024
        
        # Final memory check
        final_memory = process.memory_info().rss
        total_increase = final_memory - initial_memory
        
        # Total memory increase should be reasonable (< 100MB for 100 operations)
        assert total_increase < 100 * 1024 * 1024
        
        print(f"Memory usage: Initial: {initial_memory / 1024 / 1024:.1f}MB, "
              f"Final: {final_memory / 1024 / 1024:.1f}MB, "
              f"Increase: {total_increase / 1024 / 1024:.1f}MB")
    
    def test_memory_cleanup_after_errors(self, client):
        """Test that memory is properly cleaned up after errors."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Generate errors and measure memory
        for i in range(50):
            # Invalid requests that should cause errors
            invalid_response = client.post("/qa/ask", json={})
            assert invalid_response.status_code == 422
            
            # Non-existent endpoints
            not_found_response = client.get(f"/nonexistent/{i}")
            assert not_found_response.status_code == 404
            
            # Check memory every 10 errors
            if i % 10 == 0:
                current_memory = process.memory_info().rss
                memory_increase = current_memory - initial_memory
                
                # Memory shouldn't increase significantly due to errors
                assert memory_increase < 20 * 1024 * 1024  # < 20MB
        
        final_memory = process.memory_info().rss
        total_increase = final_memory - initial_memory
        
        # Total memory increase should be minimal for error cases
        assert total_increase < 30 * 1024 * 1024  # < 30MB
    
    @pytest.mark.asyncio
    async def test_large_document_memory_efficiency(self, file_manager, mock_data):
        """Test memory efficiency when processing large documents."""
        import psutil
        import os
        
        from app.services.document_service import DocumentProcessor
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        processor = DocumentProcessor()
        
        # Create progressively larger documents
        document_sizes = [1000, 5000, 10000, 20000]  # characters
        
        for size in document_sizes:
            content = mock_data.generate_document_content("technology", size)
            temp_file = file_manager.create_text_file(content, f"large_{size}.txt")
            
            pre_processing_memory = process.memory_info().rss
            
            # Process the document
            processed_doc = await processor.process_file(temp_file)
            
            post_processing_memory = process.memory_info().rss
            processing_memory_increase = post_processing_memory - pre_processing_memory
            
            # Verify processing completed
            assert processed_doc is not None
            assert len(processed_doc.chunks) > 0
            
            # Memory increase should be proportional but not excessive
            # Should be less than 10x the document size
            max_expected_increase = size * 10
            assert processing_memory_increase < max_expected_increase
            
            print(f"Document size: {size}, Memory increase: {processing_memory_increase / 1024:.1f}KB")
        
        final_memory = process.memory_info().rss
        total_increase = final_memory - initial_memory
        
        # Total increase should be reasonable
        assert total_increase < 100 * 1024 * 1024  # < 100MB total


@pytest.mark.performance
class TestConcurrencyPerformance:
    """Test performance under concurrent load."""
    
    @patch('app.api.endpoints.qa.get_rag_service')
    def test_concurrent_qa_requests(self, mock_get_rag, client, perf_helper):
        """Test handling of concurrent Q&A requests."""
        mock_rag = AsyncMock()
        
        from app.services.rag_service import AnswerResponse
        mock_answer = AnswerResponse(
            answer="Concurrent test answer",
            question="Concurrent test",
            sources=[],
            answer_id="concurrent_test"
        )
        mock_rag.answer_question.return_value = mock_answer
        mock_get_rag.return_value = mock_rag
        
        def make_request():
            return client.post("/qa/ask", json={
                "question": "Concurrent test question"
            })
        
        # Test with increasing concurrency levels
        concurrency_levels = [5, 10, 20]
        
        for concurrency in concurrency_levels:
            stats = perf_helper.run_concurrent_requests(
                make_request,
                num_requests=concurrency * 2,
                max_workers=concurrency
            )
            
            # Should handle concurrency well
            assert stats['success_count'] >= stats['error_count']
            assert stats['avg_duration'] < 1.0  # Average under 1s
            
            print(f"Concurrency {concurrency}: "
                  f"Success rate: {stats['success_count'] / (stats['success_count'] + stats['error_count']):.2%}, "
                  f"Avg time: {stats['avg_duration']:.3f}s")
    
    def test_mixed_workload_performance(self, client, perf_helper):
        """Test performance with mixed workload (different endpoint types)."""
        import random
        
        def make_random_request():
            request_type = random.choice(['health', 'list_docs', 'qa'])
            
            if request_type == 'health':
                return client.get("/health")
            elif request_type == 'list_docs':
                with patch('app.api.endpoints.documents.processing_status', {}), \
                     patch('app.api.endpoints.documents.get_rag_service'):
                    return client.get("/documents/")
            else:  # qa
                with patch('app.api.endpoints.qa.get_rag_service') as mock_get_rag:
                    mock_rag = AsyncMock()
                    
                    from app.services.rag_service import AnswerResponse
                    mock_answer = AnswerResponse(
                        answer="Mixed workload answer",
                        question="Mixed workload test",
                        sources=[],
                        answer_id="mixed_test"
                    )
                    mock_rag.answer_question.return_value = mock_answer
                    mock_get_rag.return_value = mock_rag
                    
                    return client.post("/qa/ask", json={
                        "question": "Mixed workload test"
                    })
        
        stats = perf_helper.run_concurrent_requests(
            make_random_request,
            num_requests=50,
            max_workers=10
        )
        
        # Mixed workload should still perform well
        perf_helper.assert_performance_requirements(
            stats,
            max_avg_duration=0.5,   # 500ms average
            max_duration=2.0,       # 2s max
            min_success_rate=0.9    # 90% success
        )
        
        print(f"Mixed workload results: {stats['success_count']} success, "
              f"{stats['error_count']} errors, "
              f"avg time: {stats['avg_duration']:.3f}s")


@pytest.mark.performance
class TestScalabilityLimits:
    """Test system behavior at scale limits."""
    
    def test_large_query_handling(self, client):
        """Test handling of very large queries."""
        with patch('app.api.endpoints.qa.get_rag_service') as mock_get_rag:
            mock_rag = AsyncMock()
            
            from app.services.rag_service import AnswerResponse
            mock_answer = AnswerResponse(
                answer="Large query answer",
                question="Large query test",
                sources=[],
                answer_id="large_query_test"
            )
            mock_rag.answer_question.return_value = mock_answer
            mock_get_rag.return_value = mock_rag
            
            # Test with increasingly large queries
            query_sizes = [100, 500, 1000, 2000]  # characters
            
            for size in query_sizes:
                large_query = "x" * size
                
                start_time = time.time()
                response = client.post("/qa/ask", json={
                    "question": large_query
                })
                processing_time = time.time() - start_time
                
                if size <= 1000:  # Should handle up to 1000 chars
                    assert response.status_code == 200
                    assert processing_time < 2.0  # Should complete in reasonable time
                else:  # Very large queries might be rejected
                    assert response.status_code in [200, 422]  # Success or validation error
                
                print(f"Query size: {size}, Status: {response.status_code}, Time: {processing_time:.3f}s")
    
    def test_many_small_requests_vs_few_large_requests(self, client, perf_helper):
        """Compare performance of many small vs few large requests."""
        with patch('app.api.endpoints.qa.get_rag_service') as mock_get_rag:
            mock_rag = AsyncMock()
            
            from app.services.rag_service import AnswerResponse
            mock_answer = AnswerResponse(
                answer="Batch test answer",
                question="Batch test",
                sources=[],
                answer_id="batch_test"
            )
            mock_rag.answer_question.return_value = mock_answer
            mock_get_rag.return_value = mock_rag
            
            # Test many small requests
            def make_small_request():
                return client.post("/qa/ask", json={
                    "question": "Small"
                })
            
            small_stats = perf_helper.run_concurrent_requests(
                make_small_request,
                num_requests=100,
                max_workers=10
            )
            
            # Test fewer large requests
            def make_large_request():
                large_question = "This is a much larger question that contains more content and should test the system's ability to handle larger payloads efficiently."
                return client.post("/qa/ask", json={
                    "question": large_question
                })
            
            large_stats = perf_helper.run_concurrent_requests(
                make_large_request,
                num_requests=25,
                max_workers=5
            )
            
            # Both should complete successfully
            assert small_stats['success_count'] > 90  # At least 90% success
            assert large_stats['success_count'] > 20   # At least 80% success
            
            print(f"Small requests: {small_stats['success_count']}/100 success, "
                  f"avg time: {small_stats['avg_duration']:.3f}s")
            print(f"Large requests: {large_stats['success_count']}/25 success, "
                  f"avg time: {large_stats['avg_duration']:.3f}s")