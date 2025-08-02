"""End-to-end integration tests for the RAG Q&A system."""

import pytest
import io
import time
from unittest.mock import patch, AsyncMock, Mock


@pytest.mark.integration
class TestEndToEndRAGWorkflow:
    """Test complete RAG workflow from document upload to question answering."""
    
    @patch('app.api.endpoints.documents.get_document_processor')
    @patch('app.api.endpoints.documents.get_rag_service')
    @patch('app.api.endpoints.qa.get_rag_service')
    def test_complete_rag_workflow(self, mock_qa_rag, mock_doc_rag, mock_processor, client):
        """Test complete workflow: upload document -> process -> ask question -> get answer."""
        # Setup mocks
        processor_mock = AsyncMock()
        rag_mock = AsyncMock()
        
        # Mock document processing
        from app.services.document_service import ProcessedDocument, DocumentChunk
        mock_chunks = [
            DocumentChunk("chunk1", "doc1", "This is about artificial intelligence and machine learning.", 0, 50),
            DocumentChunk("chunk2", "doc1", "Machine learning is a subset of AI that focuses on algorithms.", 51, 100)
        ]
        mock_processed_doc = ProcessedDocument(
            id="doc1",
            filename="ai_guide.txt",
            content_type="text/plain",
            size=100,
            chunks=mock_chunks
        )
        processor_mock.process_file.return_value = mock_processed_doc
        mock_processor.return_value = processor_mock
        
        # Mock RAG service for document upload
        rag_mock.add_document.return_value = "doc1"
        rag_mock.get_stats.return_value = {"total_documents": 1}
        mock_doc_rag.return_value = rag_mock
        
        # Mock RAG service for Q&A
        from app.services.rag_service import AnswerResponse, SearchResult
        mock_sources = [
            SearchResult("doc1", "chunk1", "This is about artificial intelligence and machine learning.", 0.95),
            SearchResult("doc1", "chunk2", "Machine learning is a subset of AI that focuses on algorithms.", 0.87)
        ]
        mock_answer = AnswerResponse(
            answer="Artificial Intelligence (AI) is a broad field that includes machine learning, which focuses on algorithms that can learn from data.",
            question="What is artificial intelligence?",
            sources=mock_sources,
            answer_id="answer123",
            confidence=0.92,
            processing_time=1.2
        )
        rag_mock.answer_question.return_value = mock_answer
        mock_qa_rag.return_value = rag_mock
        
        # Step 1: Upload document
        test_file = io.BytesIO(b"This is about artificial intelligence and machine learning. Machine learning is a subset of AI that focuses on algorithms.")
        
        with patch('app.api.endpoints.documents.save_upload_file', return_value="/tmp/ai_guide.txt"):
            upload_response = client.post(
                "/documents/upload",
                files={"file": ("ai_guide.txt", test_file, "text/plain")}
            )
        
        assert upload_response.status_code == 201
        upload_data = upload_response.json()
        document_id = upload_data["document_id"]
        
        # Verify upload response
        assert upload_data["success"] is True
        assert upload_data["filename"] == "ai_guide.txt"
        assert upload_data["status"] == "processing"
        
        # Step 2: Check processing status (simulate completion)
        mock_processing_status = {
            document_id: {
                "filename": "ai_guide.txt",
                "status": "completed",
                "progress": 1.0,
                "steps_completed": 3,
                "total_steps": 3,
                "chunk_count": 2,
                "started_at": "2024-01-01T00:00:00"
            }
        }
        
        with patch('app.api.endpoints.documents.processing_status', mock_processing_status):
            status_response = client.get(f"/documents/{document_id}/status")
        
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["status"] == "completed"
        assert status_data["progress"] == 1.0
        
        # Step 3: List documents to verify upload
        with patch('app.api.endpoints.documents.processing_status', mock_processing_status):
            list_response = client.get("/documents/")
        
        assert list_response.status_code == 200
        list_data = list_response.json()
        assert list_data["total_count"] == 1
        assert len(list_data["documents"]) == 1
        assert list_data["documents"][0]["filename"] == "ai_guide.txt"
        
        # Step 4: Ask question about the document
        question_request = {
            "question": "What is artificial intelligence?",
            "max_results": 5,
            "include_sources": True
        }
        
        qa_response = client.post("/qa/ask", json=question_request)
        
        assert qa_response.status_code == 200
        qa_data = qa_response.json()
        
        # Verify Q&A response
        assert qa_data["success"] is True
        assert "artificial intelligence" in qa_data["answer"].lower()
        assert qa_data["question"] == "What is artificial intelligence?"
        assert len(qa_data["sources"]) == 2
        assert qa_data["confidence"] == 0.92
        assert qa_data["processing_time"] == 1.2
        
        # Verify sources contain relevant content
        sources = qa_data["sources"]
        assert any("artificial intelligence" in source["content"].lower() for source in sources)
        assert any("machine learning" in source["content"].lower() for source in sources)
        
        # Step 5: Test chat interface with follow-up question
        chat_request = {
            "message": "Can you explain machine learning in more detail?",
            "max_results": 3
        }
        
        # Mock follow-up answer
        followup_answer = AnswerResponse(
            answer="Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from and make predictions or decisions based on data.",
            question="Can you explain machine learning in more detail?",
            sources=mock_sources[:1],  # Use first source
            answer_id="answer456",
            confidence=0.88
        )
        rag_mock.answer_question.return_value = followup_answer
        
        with patch('app.api.endpoints.qa.chat_sessions', {}):
            chat_response = client.post("/qa/chat", json=chat_request)
        
        assert chat_response.status_code == 200
        chat_data = chat_response.json()
        
        assert chat_data["success"] is True
        assert "machine learning" in chat_data["response"].lower()
        assert "session_id" in chat_data
        assert chat_data["conversation_length"] == 2  # User message + response
        
        # Step 6: Submit feedback on the answer
        feedback_request = {
            "answer_id": qa_data["answer_id"],
            "rating": 5,
            "comment": "Very helpful and accurate answer!"
        }
        
        with patch('app.api.endpoints.qa.answer_feedback', {}):
            feedback_response = client.post("/qa/feedback", json=feedback_request)
        
        assert feedback_response.status_code == 200
        feedback_data = feedback_response.json()
        
        assert feedback_data["success"] is True
        assert feedback_data["answer_id"] == qa_data["answer_id"]
        assert feedback_data["rating"] == 5
        
        # Verify all services were called appropriately
        processor_mock.process_file.assert_called_once()
        rag_mock.add_document.assert_called_once()
        assert rag_mock.answer_question.call_count == 2  # Q&A + Chat
    
    @patch('app.api.endpoints.documents.get_document_processor')
    @patch('app.api.endpoints.documents.get_rag_service')
    @patch('app.api.endpoints.qa.get_rag_service')
    def test_multiple_documents_workflow(self, mock_qa_rag, mock_doc_rag, mock_processor, client):
        """Test workflow with multiple documents."""
        # Setup mocks for multiple documents
        processor_mock = AsyncMock()
        rag_mock = AsyncMock()
        
        from app.services.document_service import ProcessedDocument, DocumentChunk
        
        # Mock first document
        doc1_chunks = [
            DocumentChunk("chunk1", "doc1", "Python is a programming language.", 0, 30)
        ]
        doc1 = ProcessedDocument("doc1", "python.txt", "text/plain", 30, doc1_chunks)
        
        # Mock second document
        doc2_chunks = [
            DocumentChunk("chunk2", "doc2", "JavaScript is used for web development.", 0, 40)
        ]
        doc2 = ProcessedDocument("doc2", "javascript.txt", "text/plain", 40, doc2_chunks)
        
        # Configure processor to return different docs
        processor_mock.process_file.side_effect = [doc1, doc2]
        mock_processor.return_value = processor_mock
        
        # Configure RAG service
        rag_mock.add_document.side_effect = ["doc1", "doc2"]
        rag_mock.get_stats.return_value = {"total_documents": 2}
        mock_doc_rag.return_value = rag_mock
        
        # Upload first document
        with patch('app.api.endpoints.documents.save_upload_file', return_value="/tmp/python.txt"):
            file1 = io.BytesIO(b"Python is a programming language.")
            upload1_response = client.post(
                "/documents/upload",
                files={"file": ("python.txt", file1, "text/plain")}
            )
        
        assert upload1_response.status_code == 201
        doc1_id = upload1_response.json()["document_id"]
        
        # Upload second document
        with patch('app.api.endpoints.documents.save_upload_file', return_value="/tmp/javascript.txt"):
            file2 = io.BytesIO(b"JavaScript is used for web development.")
            upload2_response = client.post(
                "/documents/upload", 
                files={"file": ("javascript.txt", file2, "text/plain")}
            )
        
        assert upload2_response.status_code == 201
        doc2_id = upload2_response.json()["document_id"]
        
        # Verify both documents were processed
        assert processor_mock.process_file.call_count == 2
        assert rag_mock.add_document.call_count == 2
        
        # Mock processing status for both documents
        mock_processing_status = {
            doc1_id: {
                "filename": "python.txt",
                "status": "completed",
                "chunk_count": 1
            },
            doc2_id: {
                "filename": "javascript.txt", 
                "status": "completed",
                "chunk_count": 1
            }
        }
        
        # List documents to verify both exist
        with patch('app.api.endpoints.documents.processing_status', mock_processing_status):
            list_response = client.get("/documents/")
        
        assert list_response.status_code == 200
        list_data = list_response.json()
        assert list_data["total_count"] == 2
        
        filenames = [doc["filename"] for doc in list_data["documents"]]
        assert "python.txt" in filenames
        assert "javascript.txt" in filenames
        
        # Ask question that could relate to both documents
        from app.services.rag_service import AnswerResponse, SearchResult
        mock_sources = [
            SearchResult("doc1", "chunk1", "Python is a programming language.", 0.75),
            SearchResult("doc2", "chunk2", "JavaScript is used for web development.", 0.70)
        ]
        mock_answer = AnswerResponse(
            answer="Both Python and JavaScript are programming languages, but they serve different purposes.",
            question="What are programming languages?",
            sources=mock_sources,
            answer_id="multi_doc_answer"
        )
        rag_mock.answer_question.return_value = mock_answer
        mock_qa_rag.return_value = rag_mock
        
        qa_response = client.post("/qa/ask", json={
            "question": "What are programming languages?",
            "max_results": 10
        })
        
        assert qa_response.status_code == 200
        qa_data = qa_response.json()
        
        # Should get sources from both documents
        assert len(qa_data["sources"]) == 2
        source_docs = [source["document_id"] for source in qa_data["sources"]]
        assert "doc1" in source_docs
        assert "doc2" in source_docs
    
    def test_error_handling_workflow(self, client):
        """Test error handling in various workflow scenarios."""
        # Test 1: Upload invalid file type
        invalid_file = io.BytesIO(b"Invalid content")
        upload_response = client.post(
            "/documents/upload",
            files={"file": ("invalid.xyz", invalid_file, "application/octet-stream")}
        )
        assert upload_response.status_code == 400
        assert "Unsupported file type" in upload_response.json()["detail"]
        
        # Test 2: Ask question without any documents
        with patch('app.api.endpoints.qa.get_rag_service') as mock_get_rag:
            mock_rag = AsyncMock()
            mock_rag.answer_question.side_effect = Exception("No documents available")
            mock_get_rag.return_value = mock_rag
            
            qa_response = client.post("/qa/ask", json={
                "question": "What is this about?"
            })
            assert qa_response.status_code == 500
        
        # Test 3: Get status for non-existent document
        status_response = client.get("/documents/nonexistent_doc/status")
        assert status_response.status_code == 404
        
        # Test 4: Delete non-existent document
        delete_response = client.delete("/documents/nonexistent_doc")
        assert delete_response.status_code == 404
        
        # Test 5: Get history for non-existent chat session
        history_response = client.get("/qa/history/nonexistent_session")
        assert history_response.status_code == 404
    
    @patch('app.api.endpoints.documents.get_document_processor')
    @patch('app.api.endpoints.documents.get_rag_service')
    def test_document_deletion_workflow(self, mock_doc_rag, mock_processor, client):
        """Test complete document deletion workflow."""
        # Setup mocks
        processor_mock = AsyncMock()
        rag_mock = AsyncMock()
        
        from app.services.document_service import ProcessedDocument, DocumentChunk
        mock_chunk = DocumentChunk("chunk1", "doc_to_delete", "Content to be deleted", 0, 20)
        mock_doc = ProcessedDocument("doc_to_delete", "delete_me.txt", "text/plain", 20, [mock_chunk])
        
        processor_mock.process_file.return_value = mock_doc
        mock_processor.return_value = processor_mock
        
        rag_mock.add_document.return_value = "doc_to_delete"
        rag_mock.delete_document.return_value = True
        rag_mock.get_stats.return_value = {"total_documents": 1}
        mock_doc_rag.return_value = rag_mock
        
        # Step 1: Upload document
        with patch('app.api.endpoints.documents.save_upload_file', return_value="/tmp/delete_me.txt"):
            test_file = io.BytesIO(b"Content to be deleted")
            upload_response = client.post(
                "/documents/upload",
                files={"file": ("delete_me.txt", test_file, "text/plain")}
            )
        
        assert upload_response.status_code == 201
        document_id = upload_response.json()["document_id"]
        
        # Step 2: Verify document exists
        mock_processing_status = {
            document_id: {
                "filename": "delete_me.txt",
                "status": "completed",
                "chunk_count": 1
            }
        }
        
        with patch('app.api.endpoints.documents.processing_status', mock_processing_status):
            detail_response = client.get(f"/documents/{document_id}")
            assert detail_response.status_code == 200
        
        # Step 3: Delete document
        with patch('app.api.endpoints.documents.processing_status', mock_processing_status):
            delete_response = client.delete(f"/documents/{document_id}")
        
        assert delete_response.status_code == 200
        delete_data = delete_response.json()
        assert delete_data["success"] is True
        assert delete_data["document_id"] == document_id
        assert delete_data["chunks_deleted"] == 1
        
        # Verify RAG service delete was called
        rag_mock.delete_document.assert_called_once_with(document_id)
        
        # Step 4: Verify document no longer exists
        with patch('app.api.endpoints.documents.processing_status', {}):
            detail_response = client.get(f"/documents/{document_id}")
            assert detail_response.status_code == 404


@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceIntegration:
    """Integration tests focusing on performance."""
    
    def test_system_performance_under_load(self, client, performance_timer):
        """Test system performance with multiple concurrent operations."""
        import concurrent.futures
        
        # Mock services for performance testing
        with patch('app.api.endpoints.documents.get_document_processor') as mock_processor, \
             patch('app.api.endpoints.documents.get_rag_service') as mock_doc_rag, \
             patch('app.api.endpoints.qa.get_rag_service') as mock_qa_rag:
            
            # Setup lightweight mocks
            processor_mock = AsyncMock()
            rag_mock = AsyncMock()
            
            from app.services.document_service import ProcessedDocument, DocumentChunk
            mock_chunk = DocumentChunk("chunk1", "perf_doc", "Performance test content", 0, 25)
            mock_doc = ProcessedDocument("perf_doc", "perf.txt", "text/plain", 25, [mock_chunk])
            
            processor_mock.process_file.return_value = mock_doc
            mock_processor.return_value = processor_mock
            
            rag_mock.add_document.return_value = "perf_doc"
            rag_mock.get_stats.return_value = {"total_documents": 1}
            mock_doc_rag.return_value = rag_mock
            
            from app.services.rag_service import AnswerResponse
            mock_answer = AnswerResponse(
                answer="Performance test answer",
                question="Performance question",
                sources=[],
                answer_id="perf_answer"
            )
            rag_mock.answer_question.return_value = mock_answer
            mock_qa_rag.return_value = rag_mock
            
            def upload_document():
                with patch('app.api.endpoints.documents.save_upload_file', return_value="/tmp/perf.txt"):
                    file_content = io.BytesIO(b"Performance test content")
                    response = client.post(
                        "/documents/upload",
                        files={"file": ("perf.txt", file_content, "text/plain")}
                    )
                    return response.status_code
            
            def ask_question():
                response = client.post("/qa/ask", json={
                    "question": "Performance question"
                })
                return response.status_code
            
            def check_health():
                response = client.get("/health")
                return response.status_code
            
            # Test concurrent operations
            performance_timer.start()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                # Submit mixed workload
                upload_futures = [executor.submit(upload_document) for _ in range(3)]
                qa_futures = [executor.submit(ask_question) for _ in range(5)]
                health_futures = [executor.submit(check_health) for _ in range(2)]
                
                # Wait for all to complete
                all_futures = upload_futures + qa_futures + health_futures
                results = [future.result() for future in all_futures]
            
            performance_timer.stop()
            
            # All operations should succeed
            assert all(status == 200 or status == 201 for status in results)
            
            # Total time should be reasonable (< 2 seconds for mocked operations)
            assert performance_timer.elapsed < 2.0
    
    def test_memory_usage_stability(self, client):
        """Test memory usage stability over multiple operations."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Mock services to avoid actual processing
        with patch('app.api.endpoints.qa.get_rag_service') as mock_get_rag:
            mock_rag = AsyncMock()
            
            from app.services.rag_service import AnswerResponse
            mock_answer = AnswerResponse(
                answer="Memory test answer",
                question="Memory test question",
                sources=[],
                answer_id="memory_test"
            )
            mock_rag.answer_question.return_value = mock_answer
            mock_get_rag.return_value = mock_rag
            
            # Perform many operations
            for i in range(50):
                # Ask questions
                response = client.post("/qa/ask", json={
                    "question": f"Memory test question {i}"
                })
                assert response.status_code == 200
                
                # Check health
                health_response = client.get("/health")
                assert health_response.status_code == 200
                
                # Occasional list operation
                if i % 10 == 0:
                    with patch('app.api.endpoints.documents.processing_status', {}):
                        list_response = client.get("/documents/")
                        assert list_response.status_code == 200
            
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be reasonable (< 20MB for 50 operations)
            assert memory_increase < 20 * 1024 * 1024
    
    def test_response_time_consistency(self, client):
        """Test that response times remain consistent across multiple requests."""
        response_times = []
        
        with patch('app.api.endpoints.qa.get_rag_service') as mock_get_rag:
            mock_rag = AsyncMock()
            
            from app.services.rag_service import AnswerResponse
            mock_answer = AnswerResponse(
                answer="Consistency test answer",
                question="Consistency test",
                sources=[],
                answer_id="consistency_test"
            )
            mock_rag.answer_question.return_value = mock_answer
            mock_get_rag.return_value = mock_rag
            
            # Make multiple requests and measure response times
            for i in range(20):
                start_time = time.time()
                
                response = client.post("/qa/ask", json={
                    "question": "Consistency test"
                })
                
                end_time = time.time()
                response_time = end_time - start_time
                response_times.append(response_time)
                
                assert response.status_code == 200
            
            # Calculate statistics
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            
            # Response times should be consistent
            assert avg_time < 0.1  # Average < 100ms
            assert max_time < 0.2  # Max < 200ms
            assert max_time - min_time < 0.15  # Variation < 150ms


@pytest.mark.integration
class TestSystemResilience:
    """Test system resilience and error recovery."""
    
    def test_graceful_service_degradation(self, client):
        """Test system behavior when individual services fail."""
        # Test 1: Document service failure
        with patch('app.api.endpoints.documents.get_document_processor') as mock_processor:
            mock_processor.side_effect = Exception("Document service unavailable")
            
            file_content = io.BytesIO(b"Test content")
            response = client.post(
                "/documents/upload",
                files={"file": ("test.txt", file_content, "text/plain")}
            )
            
            # Should handle error gracefully
            assert response.status_code in [500, 503]
            assert "application/json" in response.headers.get("content-type", "")
        
        # Test 2: RAG service failure during Q&A
        with patch('app.api.endpoints.qa.get_rag_service') as mock_get_rag:
            mock_rag = AsyncMock()
            mock_rag.answer_question.side_effect = Exception("RAG service unavailable")
            mock_get_rag.return_value = mock_rag
            
            response = client.post("/qa/ask", json={
                "question": "This will fail"
            })
            
            # Should handle error gracefully
            assert response.status_code == 500
            assert "application/json" in response.headers.get("content-type", "")
        
        # Test 3: Health checks should still work
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_invalid_input_handling(self, client):
        """Test handling of various invalid inputs."""
        # Test invalid JSON
        response = client.post(
            "/qa/ask",
            data="invalid json",
            headers={"content-type": "application/json"}
        )
        assert response.status_code == 422
        
        # Test missing required fields
        response = client.post("/qa/ask", json={})
        assert response.status_code == 422
        
        # Test invalid parameter values
        response = client.post("/qa/ask", json={
            "question": "test",
            "max_results": -1
        })
        assert response.status_code == 422
        
        # Test extremely long input
        long_question = "x" * 10000
        response = client.post("/qa/ask", json={
            "question": long_question
        })
        assert response.status_code == 422
    
    def test_rate_limiting_behavior(self, client):
        """Test rate limiting functionality."""
        # Note: This test may need to be adjusted based on actual rate limiting configuration
        with patch('app.api.endpoints.qa.get_rag_service') as mock_get_rag:
            mock_rag = AsyncMock()
            
            from app.services.rag_service import AnswerResponse
            mock_answer = AnswerResponse(
                answer="Rate limit test",
                question="Test question",
                sources=[],
                answer_id="rate_test"
            )
            mock_rag.answer_question.return_value = mock_answer
            mock_get_rag.return_value = mock_rag
            
            # Make many rapid requests (may trigger rate limiting)
            responses = []
            for i in range(35):  # More than typical rate limit
                response = client.post("/qa/ask", json={
                    "question": f"Rate limit test {i}"
                })
                responses.append(response.status_code)
            
            # Should eventually hit rate limit (429) or all succeed (200)
            success_count = responses.count(200)
            rate_limit_count = responses.count(429)
            
            assert success_count + rate_limit_count == len(responses)
            
            # If rate limiting is active, should see some 429s
            if rate_limit_count > 0:
                assert rate_limit_count < len(responses)  # Not all should be rate limited