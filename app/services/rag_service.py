"""Core RAG service with Google Gemini embeddings and FAISS vector store."""

import os
# import json
import uuid
# import asyncio
import pickle
from typing import List, Dict, Any, Optional
# from datetime import datetime
import time

import numpy as np
import faiss
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.schema import HumanMessage, SystemMessage

from app.config import get_settings
from app.services.document_service import ProcessedDocument
from app.utils.exceptions import (
    # RAGServiceError, 
    EmbeddingError, 
    VectorStoreError, 
    GeminiAPIError,
    ValidationError
)
from app.utils.logger import get_logger, log_execution_time, LoggerMixin


class SearchResult:
    """Represents a search result from the vector store."""
    
    def __init__(
        self,
        document_id: str,
        chunk_id: str,
        content: str,
        score: float,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize search result.
        
        Args:
            document_id: Source document ID
            chunk_id: Source chunk ID
            content: Matching content
            score: Similarity score
            metadata: Additional metadata
        """
        self.document_id = document_id
        self.chunk_id = chunk_id
        self.content = content
        self.score = score
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "content": self.content,
            "score": self.score,
            "metadata": self.metadata,
        }


class AnswerResponse:
    """Represents an answer response from the RAG system."""
    
    def __init__(
        self,
        answer: str,
        question: str,
        sources: List[SearchResult],
        answer_id: str,
        confidence: Optional[float] = None,
        processing_time: float = 0.0,
        token_usage: Optional[Dict[str, int]] = None,
    ):
        """Initialize answer response.
        
        Args:
            answer: Generated answer
            question: Original question
            sources: Source documents used
            answer_id: Unique answer identifier
            confidence: Answer confidence score
            processing_time: Processing time in seconds
            token_usage: Token usage statistics
        """
        self.answer = answer
        self.question = question
        self.sources = sources
        self.answer_id = answer_id
        self.confidence = confidence
        self.processing_time = processing_time
        self.token_usage = token_usage or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "answer": self.answer,
            "question": self.question,
            "sources": [source.to_dict() for source in self.sources],
            "answer_id": self.answer_id,
            "confidence": self.confidence,
            "processing_time": self.processing_time,
            "token_usage": self.token_usage,
        }


class RAGService(LoggerMixin):
    """Core RAG service handling embeddings, vector storage, and Q&A."""
    
    def __init__(self):
        """Initialize RAG service."""
        self.settings = get_settings()
        
        # Initialize LangChain Google Gemini components
        self.embeddings = GoogleGenerativeAIEmbeddings(
            google_api_key=self.settings.google_api_key,
            model=self.settings.gemini_embedding_model,
        )
        
        self.llm = ChatGoogleGenerativeAI(
            google_api_key=self.settings.google_api_key,
            model=self.settings.gemini_chat_model,
            temperature=self.settings.gemini_temperature,
            max_tokens=self.settings.gemini_max_tokens,
        )
        
        # Initialize vector store
        self.index = None
        self.chunk_metadata = {}  # Maps chunk index to metadata
        self.document_chunks = {}  # Maps document_id to list of chunk indices
        self._initialized = False
        
        # Ensure vector store directory exists
        os.makedirs(self.settings.vector_store_path, exist_ok=True)
    
    async def _ensure_initialized(self) -> None:
        """Ensure the RAG service is initialized."""
        if not self._initialized:
            await self._load_index()
            self._initialized = True
    
    async def _load_index(self) -> None:
        """Load existing FAISS index and metadata."""
        try:
            index_path = os.path.join(self.settings.vector_store_path, "faiss.index")
            metadata_path = os.path.join(self.settings.vector_store_path, "metadata.pkl")
            
            if os.path.exists(index_path) and os.path.exists(metadata_path):
                # Load FAISS index
                self.index = faiss.read_index(index_path)
                
                # Load metadata
                with open(metadata_path, 'rb') as f:
                    data = pickle.load(f)
                    self.chunk_metadata = data.get('chunk_metadata', {})
                    self.document_chunks = data.get('document_chunks', {})
                
                self.logger.info(
                    "vector_store_loaded",
                    index_size=self.index.ntotal if self.index else 0,
                    chunk_count=len(self.chunk_metadata),
                    document_count=len(self.document_chunks)
                )
            else:
                # Initialize new index
                self.index = faiss.IndexFlatL2(self.settings.vector_dimension)
                self.logger.info("new_vector_store_initialized")
                
        except Exception as e:
            self.logger.error("vector_store_load_error", error=str(e))
            # Initialize new index on error
            self.index = faiss.IndexFlatL2(self.settings.vector_dimension)
    
    async def _save_index(self) -> None:
        """Save FAISS index and metadata to disk."""
        try:
            index_path = os.path.join(self.settings.vector_store_path, "faiss.index")
            metadata_path = os.path.join(self.settings.vector_store_path, "metadata.pkl")
            
            # Save FAISS index
            if self.index:
                faiss.write_index(self.index, index_path)
            
            # Save metadata
            metadata = {
                'chunk_metadata': self.chunk_metadata,
                'document_chunks': self.document_chunks,
                'last_updated': time.time(),
            }
            
            with open(metadata_path, 'wb') as f:
                pickle.dump(metadata, f)
            
            self.logger.info("vector_store_saved")
            
        except Exception as e:
            self.logger.error("vector_store_save_error", error=str(e))
            raise VectorStoreError(f"Failed to save vector store: {str(e)}", operation="save")
    
    @log_execution_time("create_embeddings")
    async def _create_embeddings(self, texts: List[str]) -> np.ndarray:
        """Create embeddings for texts using LangChain Google Gemini embeddings.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Numpy array of embeddings
            
        Raises:
            EmbeddingError: If embedding creation fails
        """
        if not texts:
            return np.empty((0, self.settings.vector_dimension))
        
        try:
            # Truncate texts if too long (Gemini limit is ~30,000 tokens)
            truncated_texts = [text[:25000] for text in texts]
            
            # Use LangChain's async embedding method
            embeddings = await self.embeddings.aembed_documents(truncated_texts)
            
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            self.logger.info(
                "embeddings_created_with_langchain",
                text_count=len(texts),
                embedding_dimension=embeddings_array.shape[1]
            )
            
            return embeddings_array
            
        except Exception as e:
            self.logger.error("embedding_creation_error", error=str(e), text_count=len(texts))
            
            if "rate limit" in str(e).lower():
                raise EmbeddingError(
                    "Google Gemini API rate limit exceeded",
                    details={"retry_after": 60}
                )
            elif "context length" in str(e).lower():
                raise EmbeddingError(
                    "Text too long for embedding model",
                    text_length=max(len(text) for text in texts) if texts else 0
                )
            else:
                raise EmbeddingError(f"Failed to create embeddings: {str(e)}")
    
    @log_execution_time("add_document")
    async def add_document(
        self,
        processed_doc: ProcessedDocument,
        batch_size: int = 50
    ) -> str:
        """Add document chunks to vector store.
        
        Args:
            processed_doc: Processed document with chunks
            batch_size: Batch size for processing embeddings
            
        Returns:
            Document ID
            
        Raises:
            VectorStoreError: If document addition fails
        """
        await self._ensure_initialized()
        
        try:
            if not processed_doc.chunks:
                raise VectorStoreError(
                    "Document has no chunks to add",
                    operation="add_document",
                    details={"document_id": processed_doc.id}
                )
            
            self.logger.info(
                "adding_document_to_vector_store",
                document_id=processed_doc.id,
                chunk_count=len(processed_doc.chunks)
            )
            
            # Extract texts from chunks
            chunk_texts = [chunk.content for chunk in processed_doc.chunks]
            
            # Create embeddings in batches
            all_embeddings = []
            chunk_indices = []
            
            for i in range(0, len(chunk_texts), batch_size):
                batch_texts = chunk_texts[i:i + batch_size]
                batch_embeddings = await self._create_embeddings(batch_texts)
                all_embeddings.append(batch_embeddings)
                
                # Track chunk indices for this document
                start_idx = self.index.ntotal + len(chunk_indices)
                chunk_indices.extend(range(start_idx, start_idx + len(batch_texts)))
            
            # Combine all embeddings
            if all_embeddings:
                embeddings = np.vstack(all_embeddings)
            else:
                embeddings = np.empty((0, self.settings.vector_dimension))
            
            # Add to FAISS index
            self.index.add(embeddings)
            
            # Store metadata
            for i, (chunk, chunk_idx) in enumerate(zip(processed_doc.chunks, chunk_indices)):
                self.chunk_metadata[chunk_idx] = {
                    'chunk_id': chunk.id,
                    'document_id': processed_doc.id,
                    'content': chunk.content,
                    'start_index': chunk.start_index,
                    'end_index': chunk.end_index,
                    'metadata': chunk.metadata,
                    'added_timestamp': time.time(),
                }
            
            # Track document chunks
            self.document_chunks[processed_doc.id] = chunk_indices
            
            # Save to disk
            await self._save_index()
            
            self.logger.info(
                "document_added_successfully",
                document_id=processed_doc.id,
                chunk_count=len(processed_doc.chunks),
                total_chunks_in_store=self.index.ntotal
            )
            
            return processed_doc.id
            
        except Exception as e:
            self.logger.error(
                "document_addition_error",
                document_id=processed_doc.id,
                error=str(e)
            )
            
            if isinstance(e, (EmbeddingError, VectorStoreError)):
                raise
            
            raise VectorStoreError(
                f"Failed to add document to vector store: {str(e)}",
                operation="add_document"
            )
    
    @log_execution_time("search_similar")
    async def search_similar(
        self,
        query: str,
        k: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[SearchResult]:
        """Search for similar chunks in vector store.
        
        Args:
            query: Search query
            k: Number of results to return
            score_threshold: Minimum similarity score
            
        Returns:
            List of search results
            
        Raises:
            VectorStoreError: If search fails
            ValidationError: If parameters are invalid
        """
        await self._ensure_initialized()
        
        try:
            if not query.strip():
                raise ValidationError("Query cannot be empty", field="query", value=query)
            
            if k <= 0:
                raise ValidationError("k must be positive", field="k", value=k)
            
            if self.index.ntotal == 0:
                self.logger.warning("search_on_empty_index")
                return []
            
            # Create query embedding using LangChain
            query_embedding = await self.embeddings.aembed_query(query)
            if not query_embedding:
                return []
            
            query_vector = np.array([query_embedding], dtype=np.float32)
            
            # Search in FAISS index
            search_k = min(k, self.index.ntotal)
            distances, indices = self.index.search(query_vector, search_k)
            
            # Convert to search results
            results = []
            score_threshold = score_threshold or self.settings.similarity_threshold
            
            for distance, idx in zip(distances[0], indices[0]):
                if idx == -1:  # FAISS returns -1 for empty results
                    continue
                
                # Convert distance to similarity score (FAISS uses L2 distance)
                similarity_score = 1.0 / (1.0 + distance)
                
                if similarity_score < score_threshold:
                    continue
                
                # Get chunk metadata
                chunk_meta = self.chunk_metadata.get(idx, {})
                if not chunk_meta:
                    self.logger.warning("missing_chunk_metadata", index=idx)
                    continue
                
                result = SearchResult(
                    document_id=chunk_meta.get('document_id', ''),
                    chunk_id=chunk_meta.get('chunk_id', ''),
                    content=chunk_meta.get('content', ''),
                    score=similarity_score,
                    metadata=chunk_meta.get('metadata', {})
                )
                results.append(result)
            
            # Sort by score (highest first)
            results.sort(key=lambda x: x.score, reverse=True)
            
            self.logger.info(
                "similarity_search_completed",
                query_length=len(query),
                results_found=len(results),
                search_k=search_k
            )
            
            return results
            
        except Exception as e:
            self.logger.error("similarity_search_error", query=query[:100], error=str(e))
            
            if isinstance(e, (EmbeddingError, ValidationError)):
                raise
            
            raise VectorStoreError(
                f"Failed to search vector store: {str(e)}",
                operation="search"
            )
    
    @log_execution_time("answer_question")
    async def answer_question(
        self,
        question: str,
        context_limit: int = 4000,
        max_results: int = 5,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AnswerResponse:
        """Answer question using RAG approach.
        
        Args:
            question: Question to answer
            context_limit: Maximum context length in characters
            max_results: Maximum number of context documents
            temperature: Response creativity
            max_tokens: Maximum response tokens
            
        Returns:
            Answer response with sources
            
        Raises:
            GeminiAPIError: If Google Gemini API fails
            ValidationError: If parameters are invalid
        """
        await self._ensure_initialized()
        
        start_time = time.time()
        answer_id = str(uuid.uuid4())
        
        try:
            if not question.strip():
                raise ValidationError("Question cannot be empty", field="question", value=question)
            
            # Search for relevant context
            search_results = await self.search_similar(question, k=max_results)
            
            # Build context from search results
            context_parts = []
            total_length = 0
            used_sources = []
            
            for result in search_results:
                content_length = len(result.content)
                if total_length + content_length > context_limit:
                    # Try to fit partial content
                    remaining_space = context_limit - total_length
                    if remaining_space > 100:  # Only if we have reasonable space
                        partial_content = result.content[:remaining_space].rsplit(' ', 1)[0]
                        context_parts.append(f"Source: {partial_content}...")
                    break
                
                context_parts.append(f"Source: {result.content}")
                used_sources.append(result)
                total_length += content_length
            
            context = "\\n\\n".join(context_parts)
            
            # Create prompt
            prompt = self._create_qa_prompt(question, context)
            
            # Create messages for LangChain
            system_message = SystemMessage(
                content="You are a helpful assistant that answers questions based on the provided context. "
                       "If the context doesn't contain enough information to answer the question, "
                       "say so clearly. Always base your answer on the provided sources."
            )
            human_message = HumanMessage(content=prompt)
            
            # Get response from LangChain ChatGoogleGenerativeAI
            # Update temperature and max_tokens if provided
            if temperature is not None:
                self.llm.temperature = temperature
            if max_tokens is not None:
                self.llm.max_tokens = max_tokens
            
            response = await self.llm.ainvoke([system_message, human_message])
            
            answer = response.content
            processing_time = time.time() - start_time
            
            # Extract token usage from LangChain response
            token_usage = {}
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                token_usage = {
                    "prompt_tokens": response.usage_metadata.get("input_tokens", 0),
                    "completion_tokens": response.usage_metadata.get("output_tokens", 0),
                    "total_tokens": response.usage_metadata.get("total_tokens", 0),
                }
            elif hasattr(response, 'response_metadata') and response.response_metadata:
                # Fallback for different LangChain versions
                usage = response.response_metadata.get('token_usage', {})
                token_usage = {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                }
            
            # Calculate confidence based on source relevance
            confidence = self._calculate_confidence(used_sources) if used_sources else 0.0
            
            answer_response = AnswerResponse(
                answer=answer,
                question=question,
                sources=used_sources,
                answer_id=answer_id,
                confidence=confidence,
                processing_time=processing_time,
                token_usage=token_usage
            )
            
            self.logger.info(
                "question_answered",
                answer_id=answer_id,
                question_length=len(question),
                answer_length=len(answer),
                source_count=len(used_sources),
                processing_time=processing_time,
                confidence=confidence
            )
            
            return answer_response
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(
                "question_answering_error",
                answer_id=answer_id,
                question=question[:100],
                error=str(e),
                processing_time=processing_time
            )
            
            if isinstance(e, (ValidationError, VectorStoreError, EmbeddingError)):
                raise
            
            if "rate limit" in str(e).lower():
                raise GeminiAPIError(
                    "Google Gemini API rate limit exceeded",
                    api_endpoint="generateContent",
                    details={"retry_after": 60}
                )
            
            raise GeminiAPIError(
                f"Failed to generate answer: {str(e)}",
                api_endpoint="generateContent"
            )
    
    def _create_qa_prompt(self, question: str, context: str) -> str:
        """Create prompt for Q&A.
        
        Args:
            question: User question
            context: Retrieved context
            
        Returns:
            Formatted prompt
        """
        if not context.strip():
            return f"Question: {question}\\n\\nNo relevant context found. Please answer based on general knowledge or indicate if you cannot answer."
        
        return f"""Context information:
{context}

Question: {question}

Please answer the question based on the context provided above. If the context doesn't contain enough information to fully answer the question, please state that clearly and provide what information you can from the context."""
    
    def _calculate_confidence(self, sources: List[SearchResult]) -> float:
        """Calculate confidence score based on source relevance.
        
        Args:
            sources: List of search results used
            
        Returns:
            Confidence score between 0 and 1
        """
        if not sources:
            return 0.0
        
        # Simple confidence calculation based on top score and source count
        top_score = sources[0].score
        source_count_factor = min(len(sources) / 3.0, 1.0)  # More sources = higher confidence, up to 3
        
        # Combine top score with source count factor
        confidence = (top_score * 0.7) + (source_count_factor * 0.3)
        
        return min(confidence, 1.0)
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete document from vector store.
        
        Args:
            document_id: ID of document to delete
            
        Returns:
            True if deleted successfully
            
        Raises:
            VectorStoreError: If deletion fails
        """
        try:
            if document_id not in self.document_chunks:
                self.logger.warning("document_not_found_for_deletion", document_id=document_id)
                return False
            
            # Get chunk indices for this document
            chunk_indices = self.document_chunks[document_id]
            
            # Remove from metadata
            for idx in chunk_indices:
                self.chunk_metadata.pop(idx, None)
            
            # Remove from document tracking
            del self.document_chunks[document_id]
            
            # Note: FAISS doesn't support individual deletion efficiently
            # For production, consider using a different vector store or rebuilding index
            self.logger.warning(
                "document_deletion_metadata_only",
                document_id=document_id,
                note="FAISS vectors remain in index - consider rebuilding for complete removal"
            )
            
            # Save updated metadata
            await self._save_index()
            
            self.logger.info("document_deleted", document_id=document_id, chunk_count=len(chunk_indices))
            return True
            
        except Exception as e:
            self.logger.error("document_deletion_error", document_id=document_id, error=str(e))
            raise VectorStoreError(
                f"Failed to delete document: {str(e)}",
                operation="delete_document"
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get RAG system statistics.
        
        Returns:
            System statistics
        """
        try:
            return {
                "total_documents": len(self.document_chunks),
                "total_chunks": len(self.chunk_metadata),
                "vector_store_size": self.index.ntotal if self.index else 0,
                "vector_dimension": self.settings.vector_dimension,
                "last_updated": time.time(),
            }
        except Exception as e:
            self.logger.error("stats_retrieval_error", error=str(e))
            return {
                "error": str(e),
                "total_documents": 0,
                "total_chunks": 0,
                "vector_store_size": 0,
            }