# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Start with auto-reload for development
uvicorn app.main:app --reload --log-level debug

# Or run directly with Python
python -m app.main

# Production mode (without docs/debug)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Run all tests with coverage
pytest

# Run specific test types
pytest -m unit                    # Unit tests only
pytest -m integration             # Integration tests only
pytest -m "not slow"              # Skip slow tests
pytest -m requires_openai         # Tests requiring OpenAI API

# Run specific test files
pytest tests/test_rag_service.py
pytest tests/integration/test_end_to_end.py

# Run with verbose output
pytest -v --tb=long
```

### Code Quality
```bash
# Format code
black .
isort .

# Lint code
flake8 .
mypy .

# All quality checks
black . && isort . && flake8 . && mypy .
```

## Project Architecture

### Core Components

**FastAPI Application (`app/main.py`)**
- Entry point with lifespan management
- CORS and custom middleware configuration
- Conditional docs/debug based on environment

**Configuration (`app/config.py`)**
- Pydantic-based settings with validation
- Environment variable support via .env files
- Comprehensive validation for all settings

**Services Layer**
- `rag_service.py`: Core RAG implementation with OpenAI + FAISS
- `document_service.py`: Document processing (PDF, TXT, DOCX, MD)

**API Endpoints (`app/api/endpoints/`)**
- `health.py`: Health checks and service info
- `documents.py`: Document upload and management
- `qa.py`: Q&A endpoints with streaming support

### Key Design Patterns

**Dependency Injection**
- Settings accessed via `get_settings()` cached function
- Services follow singleton pattern with proper lifecycle management

**Error Handling**
- Custom exceptions in `app/utils/exceptions.py`
- Structured error responses with proper HTTP status codes
- Global error handling middleware

**Logging**
- Structured JSON logging via structlog
- Request tracing with correlation IDs
- Performance monitoring with execution timing

**Vector Store Architecture**
- FAISS-based similarity search with configurable index types
- Persistent storage with metadata tracking
- Chunked document processing with overlap

### Configuration Management

**Environment Files**
- `.env`: Local development settings
- `.env.example`: Template with all available options

**Key Settings**
- OpenAI API configuration (models, tokens, temperature)
- Vector store settings (path, index type, similarity threshold)
- Document processing (chunk size, overlap, file size limits)
- Rate limiting and CORS configuration

### Testing Strategy

**Test Structure**
- Unit tests for individual components
- Integration tests for full workflows
- Performance tests for vector operations
- API endpoint tests with mock data

**Test Configuration**
- Coverage reporting with 80% minimum threshold
- Async test support enabled
- Mock OpenAI responses for consistent testing
- Separate test vector store path

### Document Processing Pipeline

1. **Upload & Validation**: File type and size validation
2. **Text Extraction**: Format-specific parsing (PDF, DOCX, etc.)
3. **Chunking**: Intelligent text splitting with overlap
4. **Embedding**: OpenAI text-embedding-ada-002
5. **Indexing**: FAISS vector store with metadata
6. **Storage**: Persistent storage with document tracking

### RAG Query Pipeline

1. **Query Embedding**: Convert question to vector
2. **Similarity Search**: FAISS search with configurable threshold
3. **Context Assembly**: Retrieve and rank relevant chunks
4. **Answer Generation**: OpenAI chat completion with context
5. **Response Streaming**: Optional SSE streaming support

## Development Guidelines

### Adding New Endpoints
1. Define Pydantic models in `app/models/`
2. Implement business logic in `app/services/`
3. Create endpoint in appropriate `app/api/endpoints/` file
4. Add comprehensive tests in `tests/`
5. Update API documentation if needed

### Vector Store Operations
- Vector store automatically creates directories via config validation
- Index type configurable via `VECTOR_INDEX_TYPE` (default: IndexFlatL2)
- Similarity threshold configurable for search quality vs recall

### Environment Setup
1. Copy `.env.example` to `.env`
2. Set `OPENAI_API_KEY` (required)
3. Configure other settings as needed
4. Vector store path will be created automatically

### Security Considerations
- OpenAI API key must be set in environment variables
- JWT configuration for future authentication features
- Rate limiting configured per endpoint
- CORS properly configured for development/production