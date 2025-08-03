# RAG Q&A System Components

## 🎯 **Phase 1: Project Foundation (Day 1)**

### **PROMPT 1: Project Structure & Configuration**
```prompt
Create a complete FastAPI project structure for a production-ready RAG Q&A system called "rag-qa-foundation". 

Requirements:
- Python 3.11+ with proper package structure
- FastAPI with uvicorn server
- Environment configuration with pydantic-settings
- Logging configuration with structured logging
- Error handling middleware
- CORS middleware for frontend integration
- Health check endpoints

Project Structure:
```
rag-qa-foundation/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Configuration management
│   ├── middleware.py           # Custom middleware
│   ├── models/
│   │   ├── __init__.py
│   │   ├── requests.py         # Pydantic request models
│   │   └── responses.py        # Pydantic response models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── rag_service.py      # Core RAG logic
│   │   └── document_service.py # Document processing
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py             # Dependencies
│   │   └── endpoints/
│   │       ├── __init__.py
│   │       ├── health.py       # Health checks
│   │       ├── documents.py    # Document management
│   │       └── qa.py           # Q&A endpoints
│   └── utils/
│       ├── __init__.py
│       ├── logger.py           # Logging utilities
│       └── exceptions.py       # Custom exceptions
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

Include:
- Complete requirements.txt with all dependencies
- Configuration class with environment variables
- Structured logging setup
- Custom exception classes
- FastAPI app initialization with all middleware
- Type hints throughout
- Comprehensive docstrings

Make it production-ready with proper error handling and security considerations.
```

### **PROMPT 2: Core Configuration & Logging**
```prompt
Create a robust configuration and logging system for the RAG Q&A application.

Requirements:

1. **config.py** - Configuration management:
   - Use pydantic-settings for environment variables
   - GEMINI API configuration (key, organization, models)
   - Application settings (debug, host, port, environment)
   - Vector database settings (storage path, index parameters)
   - Rate limiting configuration
   - CORS settings
   - Validation for all required fields
   - Support for .env files and environment variables

2. **utils/logger.py** - Structured logging:
   - JSON structured logging for production
   - Console logging for development
   - Different log levels (DEBUG, INFO, WARNING, ERROR)
   - Request ID tracking
   - Performance metrics logging
   - Error context capture
   - Log rotation configuration

3. **utils/exceptions.py** - Custom exceptions:
   - RAGServiceError (base exception)
   - DocumentProcessingError
   - EmbeddingError
   - VectorStoreError
   - GEMINIAPIError
   - ValidationError
   - Include proper error codes and messages

4. **middleware.py** - Custom middleware:
   - Request logging middleware
   - Error handling middleware
   - Request ID generation
   - Performance monitoring
   - CORS handling

Include complete implementations with type hints, docstrings, and error handling. Make it production-ready with security best practices.
```

---

## 🎯 **Phase 2: Core RAG Implementation (Day 1-2)**

### **PROMPT 3: Document Processing Service**
```prompt
Create a comprehensive document processing service for the RAG system.

Requirements:

**services/document_service.py** - Document processing:
- Support for PDF, TXT, DOCX, and MD files
- Text extraction with proper encoding handling
- Text cleaning and preprocessing
- Chunk creation with overlapping windows
- Metadata extraction (filename, page numbers, timestamps)
- File validation and size limits
- Async processing support
- Error handling for corrupt files

Key Features:
- Class: DocumentProcessor
- Methods:
  - process_file(file_path: str) -> List[DocumentChunk]
  - extract_text(file_path: str, file_type: str) -> str
  - create_chunks(text: str, chunk_size: int, overlap: int) -> List[str]
  - validate_file(file_path: str) -> bool
  - get_metadata(file_path: str) -> Dict[str, Any]

- Use libraries: PyPDF2, python-docx, chardet
- Support for different chunk strategies
- Memory-efficient processing for large files
- Comprehensive error handling and logging
- Type hints and detailed docstrings
- Unit test examples

**models/requests.py** - Document-related models:
- DocumentUploadRequest
- ChunkingConfigRequest
- DocumentDeleteRequest

**models/responses.py** - Document-related responses:
- DocumentResponse
- ChunkResponse
- ProcessingStatusResponse
- DocumentListResponse

Make it production-ready with proper validation, error handling, and performance considerations.
```

### **PROMPT 4: Core RAG Service**
```prompt
Create the main RAG service that handles embeddings, vector storage, and question answering.

Requirements:

**services/rag_service.py** - Core RAG implementation:

Main Class: RAGService
- Initialize GEMINI client and FAISS vector store
- Handle document embedding and storage
- Implement similarity search with configurable parameters
- Generate answers using GPT-3.5-turbo with context
- Support for conversation memory
- Async operations for better performance

Key Methods:
1. add_document(chunks: List[str], metadata: List[Dict]) -> str
   - Create embeddings for text chunks
   - Store in FAISS with metadata
   - Return document ID

2. search_similar(query: str, k: int = 5) -> List[SearchResult]
   - Create query embedding
   - Search FAISS index
   - Return ranked results with scores and metadata

3. answer_question(question: str, context_limit: int = 4000) -> AnswerResponse
   - Search for relevant context
   - Build prompt with context
   - Call GEMINI API for answer generation
   - Include source citations

4. delete_document(doc_id: str) -> bool
   - Remove document from vector store
   - Update FAISS index

5. get_stats() -> Dict[str, Any]
   - Return system statistics
   - Document count, index size, etc.

Technical Requirements:
- Use GEMINI text-embedding-ada-002 for embeddings
- FAISS IndexFlatL2 for vector storage
- Implement proper error handling for API failures
- Add retry logic with exponential backoff
- Include prompt engineering for better answers
- Support for different similarity metrics
- Memory management for large document collections
- Comprehensive logging and metrics

**models/responses.py** additions:
- SearchResult model
- AnswerResponse model with sources
- RAGStats model

Include complete implementation with error handling, logging, type hints, and docstrings. Make it thread-safe and production-ready.
```

---

## 🎯 **Phase 3: API Endpoints (Day 2-3)**

### **PROMPT 5: Document Management API**
```prompt
Create comprehensive document management API endpoints.

Requirements:

**api/endpoints/documents.py** - Document management:

Endpoints to implement:
1. POST /documents/upload
   - Accept multipart file upload
   - Validate file type and size
   - Process document asynchronously
   - Return upload status and document ID
   - Support batch uploads

2. GET /documents
   - List all uploaded documents
   - Support pagination and filtering
   - Include metadata and processing status
   - Search documents by name/content

3. GET /documents/{document_id}
   - Get specific document details
   - Include chunks and metadata
   - Return processing status

4. DELETE /documents/{document_id}
   - Remove document from system
   - Clean up vector store entries
   - Return deletion confirmation

5. POST /documents/{document_id}/reprocess
   - Reprocess document with new settings
   - Update vector store
   - Return processing status

**api/deps.py** - Dependencies:
- get_rag_service() dependency
- get_document_processor() dependency
- File validation dependencies
- Rate limiting dependencies

Technical Requirements:
- Async endpoint implementations
- Proper HTTP status codes
- Comprehensive error responses
- Request/response validation with Pydantic
- File upload handling with size limits
- Background task processing
- OpenAPI documentation with examples
- Security headers and validation

**models/requests.py** additions:
- DocumentUploadRequest
- DocumentSearchRequest
- ReprocessingRequest

**models/responses.py** additions:
- DocumentUploadResponse
- DocumentDetailResponse
- DocumentListResponse
- DeletionResponse

Include proper error handling, validation, logging, and OpenAPI documentation. Make it production-ready with security considerations.
```

### **PROMPT 6: Question-Answering API**
```prompt
Create sophisticated question-answering API endpoints with streaming support.

Requirements:

**api/endpoints/qa.py** - Q&A endpoints:

Main Endpoints:
1. POST /qa/ask
   - Accept question and optional parameters
   - Search relevant documents
   - Generate answer with sources
   - Support streaming responses
   - Include confidence scores

2. POST /qa/ask/stream
   - Streaming response for real-time answers
   - Server-sent events (SSE) implementation
   - Progressive answer building
   - Real-time status updates

3. POST /qa/chat
   - Conversational Q&A with memory
   - Maintain conversation context
   - Support follow-up questions
   - Session management

4. GET /qa/history/{session_id}
   - Retrieve conversation history
   - Support pagination
   - Include metadata and timestamps

5. POST /qa/feedback
   - Accept user feedback on answers
   - Store ratings and comments
   - Support answer improvement

Advanced Features:
- Support for different answer styles (detailed, brief, technical)
- Multilingual question support
- Query expansion and refinement
- Answer caching for common questions
- Real-time response streaming
- Conversation context management
- Source attribution and citations
- Confidence scoring

Technical Implementation:
- Async/await for all operations
- SSE streaming for real-time responses
- Redis for session storage
- Rate limiting per user/session
- Input sanitization and validation
- Comprehensive error handling
- Performance monitoring
- Request/response logging

**models/requests.py** additions:
- QuestionRequest
- ChatRequest
- FeedbackRequest
- HistoryRequest

**models/responses.py** additions:
- AnswerResponse with sources and confidence
- ChatResponse
- StreamingResponse
- HistoryResponse
- FeedbackResponse

Include streaming implementation, session management, error handling, and comprehensive OpenAPI documentation. Make it production-ready with performance optimization.
```

### **PROMPT 7: Health Check & Monitoring API**
```prompt
Create comprehensive health check and monitoring endpoints for the RAG system.

Requirements:

**api/endpoints/health.py** - Health and monitoring:

Health Check Endpoints:
1. GET /health
   - Basic health check
   - Return service status and version
   - Quick response for load balancers

2. GET /health/detailed
   - Comprehensive health check
   - Test all external dependencies
   - GEMINI API connectivity
   - Vector store status
   - File system access
   - Memory and disk usage

3. GET /health/ready
   - Readiness probe for Kubernetes
   - Check if service can handle requests
   - Validate all dependencies are ready

4. GET /health/live
   - Liveness probe for Kubernetes
   - Check if service is alive
   - Minimal health validation

Monitoring Endpoints:
5. GET /metrics
   - Prometheus-compatible metrics
   - Request counters and latencies
   - Error rates and success rates
   - Resource usage metrics
   - Custom RAG metrics (documents, queries, etc.)

6. GET /stats
   - System statistics
   - Document count and sizes
   - Query performance metrics
   - Cache hit rates
   - User activity statistics

7. GET /info
   - Service information
   - Version, build info
   - Configuration (non-sensitive)
   - API documentation links

Implementation Requirements:
- Async implementations for all endpoints
- Dependency health checking
- Metric collection and aggregation
- Proper HTTP status codes
- Detailed error responses
- Performance monitoring
- Resource usage tracking
- OpenAPI documentation

**utils/metrics.py** - Metrics collection:
- Prometheus metric definitions
- Custom metric collectors
- Performance tracking decorators
- Error rate tracking
- Request duration tracking

**models/responses.py** additions:
- HealthResponse
- DetailedHealthResponse
- MetricsResponse
- StatsResponse
- InfoResponse

Include comprehensive monitoring, proper health checks, metrics collection, and Kubernetes-ready probes. Make it production-ready with observability best practices.
```

---

## 🎯 **Phase 4: Testing Framework (Day 3-4)**

### **PROMPT 8: Comprehensive Testing Suite**
```prompt
Create a comprehensive testing framework for the RAG Q&A system.

Requirements:

**tests/** structure:
```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures
├── test_config.py           # Configuration tests
├── test_document_service.py # Document processing tests
├── test_rag_service.py      # RAG service tests
├── test_api_documents.py    # Document API tests
├── test_api_qa.py          # Q&A API tests
├── test_api_health.py      # Health check tests
├── integration/
│   ├── test_end_to_end.py  # Full workflow tests
│   └── test_performance.py # Performance tests
├── fixtures/
│   ├── sample_documents/   # Test documents
│   └── test_data.py       # Test data
└── utils/
    ├── helpers.py         # Test utilities
    └── mocks.py          # Mock objects
```

**conftest.py** - Pytest configuration:
- FastAPI test client setup
- Mock GEMINI client
- Temporary file system setup
- Database fixtures
- Authentication fixtures
- Performance test decorators

**test_rag_service.py** - Core service tests:
- Test document embedding and storage
- Test similarity search functionality
- Test question answering with mocks
- Test error handling scenarios
- Test memory management
- Performance benchmarks

**test_api_qa.py** - Q&A API tests:
- Test question answering endpoints
- Test streaming responses
- Test conversation management
- Test error responses
- Test rate limiting
- Test input validation

**test_document_service.py** - Document processing tests:
- Test file processing for different formats
- Test chunking strategies
- Test metadata extraction
- Test error handling for corrupt files
- Test large file processing
- Memory usage tests

**integration/test_end_to_end.py** - Full workflow tests:
- Upload document → Ask question → Get answer
- Multiple document scenarios
- Complex query scenarios
- Performance under load
- Error recovery tests

Testing Features:
- Pytest with async support
- Mock external APIs (GEMINI)
- Temporary file handling
- Database state management
- Performance benchmarking
- Coverage reporting
- Parameterized tests
- Fixture factories

**pytest.ini** configuration:
- Test discovery settings
- Coverage configuration
- Async test support
- Marker definitions
- Output formatting

Include comprehensive test coverage (>90%), proper mocking, performance tests, and CI/CD integration. Make it production-ready with automated testing.
```

### **PROMPT 9: Performance & Load Testing**
```prompt
Create performance and load testing framework for the RAG system.

Requirements:

**tests/performance/** - Performance testing:

1. **test_performance.py** - Core performance tests:
   - Document processing speed benchmarks
   - Embedding generation performance
   - Vector search latency tests
   - Question answering response times
   - Memory usage profiling
   - Concurrent request handling

2. **load_testing.py** - Load testing with Locust:
   - Simulate realistic user behavior
   - Document upload load tests
   - Q&A query load tests
   - Concurrent user scenarios
   - Stress testing limits
   - Performance degradation analysis

3. **benchmark_rag.py** - RAG-specific benchmarks:
   - Accuracy benchmarks with test datasets
   - Response quality evaluation
   - Source attribution accuracy
   - Different chunk size performance
   - Embedding model comparisons

**utils/performance.py** - Performance utilities:
- Timing decorators
- Memory profiling utilities
- Performance metric collection
- Benchmark data generation
- Results analysis and reporting

Load Testing Scenarios:
- Gradual user ramp-up (1-100 users)
- Document upload stress test
- Concurrent Q&A queries
- Mixed workload simulation
- Peak traffic simulation
- Long-running stability test

Performance Metrics:
- Response time percentiles (p50, p95, p99)
- Throughput (requests/second)
- Error rates under load
- Memory usage patterns
- CPU utilization
- Document processing speed
- Vector search performance

**locustfile.py** - Locust configuration:
- User behavior simulation
- Realistic data patterns
- Progressive load increase
- Custom metrics collection
- Detailed reporting

Benchmarking Framework:
- Automated performance regression detection
- Performance comparison across versions
- Resource usage monitoring
- Scalability analysis
- Bottleneck identification

Include comprehensive performance monitoring, load testing scenarios, and automated benchmarking. Make it production-ready with CI/CD integration.
```

---

## 🎯 **Phase 5: DevOps & Deployment (Day 4-5)**

### **PROMPT 10: Docker Configuration**
```prompt
Create comprehensive Docker configuration for the RAG Q&A system.

Requirements:

**Dockerfile** - Multi-stage production build:
- Python 3.11 slim base image
- Security-hardened container
- Multi-stage build for optimization
- Non-root user setup
- Proper layer caching
- Health check configuration
- Environment variable support
- Volume mounts for data persistence

**docker-compose.yml** - Development environment:
- FastAPI application service
- Redis for caching and sessions
- Volume mounts for development
- Environment variable configuration
- Network configuration
- Port mapping
- Health checks
- Restart policies

**docker-compose.prod.yml** - Production environment:
- Optimized for production
- Reverse proxy configuration
- SSL/TLS termination
- Log aggregation
- Monitoring integration
- Backup volumes
- Security configurations

Docker Configuration Features:
- Multi-architecture support (AMD64, ARM64)
- Security scanning integration
- Build optimization for faster deployments
- Proper secret management
- Resource limits and reservations
- Log rotation configuration
- Health check endpoints
- Graceful shutdown handling

**docker/** directory structure:
```
docker/
├── Dockerfile.prod        # Production optimized
├── Dockerfile.dev         # Development with debug
├── nginx.conf            # Reverse proxy config
├── entrypoint.sh         # Container startup script
└── health-check.sh       # Health check script
```

**entrypoint.sh** - Container startup:
- Environment validation
- Database migration/setup
- Service initialization
- Health check implementation
- Graceful shutdown handling

Security Features:
- Non-root user execution
- Minimal attack surface
- Secret management
- File permission hardening
- Network security
- Container scanning integration

Include production-ready Docker configuration with security, performance, and monitoring considerations.
```

### **PROMPT 11: GitHub Actions CI/CD Pipeline**
```prompt
Create a comprehensive GitHub Actions CI/CD pipeline for the RAG system.

Requirements:

**.github/workflows/** structure:
```
.github/
├── workflows/
│   ├── ci.yml              # Continuous Integration
│   ├── cd.yml              # Continuous Deployment
│   ├── security.yml        # Security scanning
│   ├── performance.yml     # Performance testing
│   └── release.yml         # Release automation
├── dependabot.yml          # Dependency updates
└── PULL_REQUEST_TEMPLATE.md
```

**ci.yml** - Continuous Integration:
Triggers: Push, Pull Request
Jobs:
1. **Code Quality**:
   - Python linting (black, flake8, isort)
   - Type checking (mypy)
   - Security scanning (bandit)
   - Dependency vulnerability check

2. **Testing**:
   - Unit tests with pytest
   - Integration tests
   - Coverage reporting (codecov)
   - Test result artifacts

3. **Build**:
   - Docker image build
   - Multi-architecture builds
   - Image vulnerability scanning
   - Build artifacts

**cd.yml** - Continuous Deployment:
Triggers: Successful CI on main branch
Jobs:
1. **Deploy to Staging**:
   - Deploy to staging environment
   - Run smoke tests
   - Performance validation

2. **Deploy to Production**:
   - Manual approval required
   - Blue-green deployment
   - Health checks
   - Rollback capability

**security.yml** - Security Pipeline:
- CodeQL analysis
- Dependency vulnerability scanning
- Container image security scanning
- SAST (Static Application Security Testing)
- Secret scanning
- License compliance check

**performance.yml** - Performance Testing:
- Automated performance benchmarks
- Load testing with Locust
- Performance regression detection
- Resource usage monitoring
- Performance report generation

Pipeline Features:
- Matrix builds (Python versions, OS)
- Caching for faster builds
- Parallel job execution
- Artifact management
- Notification integration (Slack, email)
- Environment promotion workflow
- Automatic rollback on failures

**Secrets Management**:
- GEMINI API keys
- Docker Hub credentials
- Cloud provider credentials
- Database connection strings
- Encryption keys

**Environment Configuration**:
- Development environment variables
- Staging configuration
- Production secrets
- Feature flag management

Include comprehensive CI/CD with security, testing, deployment, and monitoring. Make it production-ready with proper approval workflows and rollback capabilities.
```

---

## 🎯 **Phase 6: Frontend & Documentation (Day 5-6)**

### **PROMPT 12: Streamlit Frontend Interface**
```prompt
Create a professional Streamlit web interface for testing and demonstrating the RAG Q&A system.

Requirements:

**streamlit_app.py** - Main Streamlit application:

Interface Sections:
1. **Document Management Page**:
   - File upload widget (drag & drop)
   - Support multiple file types (PDF, TXT, DOCX)
   - Upload progress indicators
   - Document list with metadata
   - Document deletion functionality
   - Batch upload support

2. **Q&A Interface Page**:
   - Question input with auto-complete
   - Real-time answer streaming
   - Source document highlighting
   - Confidence score display
   - Answer history
   - Export conversation functionality

3. **Analytics Dashboard**:
   - System statistics visualization
   - Document processing metrics
   - Query performance charts
   - User activity analytics
   - Error rate monitoring

4. **Configuration Page**:
   - RAG parameter tuning
   - Model selection interface
   - Chunk size configuration
   - Search parameter adjustment
   - API endpoint configuration

Advanced Features:
- Session state management
- Real-time status updates
- Progress bars for long operations
- Error handling with user-friendly messages
- Responsive design for mobile devices
- Dark/light theme support
- Export functionality (PDF, JSON)
- Keyboard shortcuts

**pages/** structure:
```
pages/
├── 01_📄_Documents.py      # Document management
├── 02_❓_Ask_Questions.py   # Q&A interface
├── 03_📊_Analytics.py      # Analytics dashboard
├── 04_⚙️_Settings.py       # Configuration
└── 05_📖_API_Docs.py       # API documentation
```

**utils/streamlit_utils.py** - Utility functions:
- API client wrapper
- File handling utilities
- Chart generation functions
- Session state management
- Error handling decorators

UI/UX Features:
- Professional styling with custom CSS
- Loading animations and spinners
- Toast notifications for user feedback
- Sidebar navigation with icons
- Responsive layout design
- Data visualization with Plotly
- Interactive charts and graphs
- File preview capabilities

**config/streamlit_config.toml** - Streamlit configuration:
- Theme customization
- Server configuration
- Performance optimization
- Security settings

Testing Integration:
- Mock API responses for development
- Error scenario simulation
- Performance testing interface
- User acceptance testing support

Include professional UI/UX, comprehensive functionality, and production-ready deployment configuration.
```

### **PROMPT 13: Comprehensive Documentation**
```prompt
Create comprehensive documentation for the RAG Q&A system.

Requirements:

**README.md** - Main project documentation:
- Project overview and features
- Quick start guide
- Installation instructions
- Usage examples with code
- API documentation links
- Deployment instructions
- Contributing guidelines
- License and acknowledgments

**docs/** structure:
```
docs/
├── index.md                # Documentation home
├── getting-started.md      # Quick start guide
├── installation.md         # Detailed installation
├── api-reference.md        # API documentation
├── architecture.md         # System architecture
├── deployment.md           # Deployment guide
├── configuration.md        # Configuration options
├── performance.md          # Performance tuning
├── troubleshooting.md      # Common issues
├── contributing.md         # Development guide
├── examples/
│   ├── basic-usage.md     # Basic examples
│   ├── advanced-usage.md  # Advanced examples
│   └── api-examples.md    # API usage examples
└── assets/
    ├── architecture.png   # Architecture diagrams
    └── screenshots/       # UI screenshots
```

**getting-started.md** - Quick start:
- Prerequisites and requirements
- Step-by-step setup instructions
- First document upload
- First question example
- Common next steps

**api-reference.md** - API documentation:
- Complete endpoint documentation
- Request/response examples
- Authentication requirements
- Error codes and handling
- Rate limiting information
- SDK examples

**architecture.md** - Technical documentation:
- System architecture overview
- Component interaction diagrams
- Data flow explanations
- Technology stack details
- Scalability considerations
- Security architecture

**deployment.md** - Deployment guide:
- Docker deployment instructions
- Kubernetes deployment manifests
- Cloud platform guides (AWS, GCP, Azure)
- Environment configuration
- Monitoring setup
- Backup and recovery

**performance.md** - Performance guide:
- Performance tuning recommendations
- Scaling strategies
- Monitoring and metrics
- Troubleshooting slow performance
- Resource optimization
- Load testing guidelines

**troubleshooting.md** - Support documentation:
- Common error messages and solutions
- Debugging techniques
- Log analysis guide
- Performance issues
- Configuration problems
- Support contact information

Documentation Features:
- Interactive code examples
- Copy-paste ready commands
- Screenshots and diagrams
- Version-specific information
- Search functionality
- Cross-references and links
- Mobile-friendly formatting

**mkdocs.yml** - Documentation site configuration:
- Site navigation structure
- Theme configuration
- Plugin configuration
- Search integration
- Analytics setup

Include comprehensive, user-friendly documentation with examples, diagrams, and troubleshooting guides. Make it production-ready for end users and developers.
```

---

## 🎯 **Bonus: Advanced Features (Day 6-7)**

### **PROMPT 14: Advanced Configuration & Monitoring**
```prompt
Create advanced configuration management and monitoring systems for the RAG application.

Requirements:

**config/advanced_config.py** - Advanced configuration:
- Multi-environment configuration (dev, staging, prod)
- Feature flag management
- Dynamic configuration reloading
- Configuration validation and schemas
- Secrets management integration
- Performance tuning parameters
- A/B testing configuration

**monitoring/** - Monitoring system:
```
monitoring/
├── prometheus.yml          # Prometheus config
├── grafana/
│   ├── dashboards/        # Grafana dashboards
│   └── provisioning/      # Dashboard provisioning
├── alerts/
│   ├── rules.yml         # Alerting rules
│   └── notifications.yml # Alert destinations
└── logs/
    ├── logstash.conf     # Log processing
    └── elasticsearch.yml # Search config
```

**utils/metrics.py** - Advanced metrics:
- Custom Prometheus metrics
- Business metrics tracking
- Performance profiling
- User behavior analytics
- Error tracking and categorization
- Resource usage monitoring

Monitoring Features:
- Real-time dashboards
- Alert management
- Log aggregation and search
- Performance profiling
- User activity tracking
- Error rate monitoring
- Capacity planning metrics

**utils/feature_flags.py** - Feature flag system:
- Dynamic feature toggling
- A/B testing framework
- User-based feature rollouts
- Performance impact measurement
- Configuration-driven features

Include production-ready monitoring, alerting, and configuration management systems.
```

### **PROMPT 15: Security & Compliance**
```prompt
Create comprehensive security and compliance features for the RAG system.

Requirements:

**security/** - Security implementation:
```
security/
├── auth.py               # Authentication system
├── rbac.py              # Role-based access control
├── encryption.py        # Data encryption utilities
├── audit.py             # Audit logging
├── compliance.py        # Compliance checking
└── scanner.py           # Security scanning
```

**auth.py** - Authentication system:
- JWT token management
- OAuth2 integration
- API key authentication
- Rate limiting per user
- Session management
- Multi-factor authentication support

**rbac.py** - Role-based access:
- User role definitions
- Permission management
- Resource-based access control
- Admin interface for user management
- Audit trail for access changes

**encryption.py** - Data protection:
- Encryption at rest for documents
- Encryption in transit
- Key management
- PII detection and masking
- Secure deletion

**audit.py** - Audit logging:
- Complete audit trail
- User activity logging
- Data access tracking
- Compliance reporting
- Log integrity verification

**compliance.py** - Compliance features:
- GDPR compliance tools
- Data retention policies
- Right to be forgotten implementation
- Data export functionality
- Privacy policy enforcement

Security Features:
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF protection
- Security headers implementation
- Vulnerability scanning integration
- Penetration testing support

Include enterprise-grade security with compliance, audit, and access control features.
```

---

## 🚀 **Usage Strategy for Maximum Efficiency**

### **Development Sequence:**
1. **Day 1**: Prompts 1-4 (Foundation + Core RAG)
2. **Day 2**: Prompts 5-7 (API Endpoints)
3. **Day 3**: Prompts 8-9 (Testing Framework)
4. **Day 4**: Prompts 10-11 (DevOps)
5. **Day 5**: Prompts 12-13 (Frontend + Docs)
6. **Day 6-7**: Prompts 14-15 (Advanced Features)

### **Pro Tips for Using These Prompts:**
1. **Copy-paste exactly** - These are optimized for Claude Code
2. **Review and iterate** - Show Claude the generated code for improvements
3. **Ask for explanations** - Request architectural decisions explanations
4. **Request optimizations** - Ask for performance and security improvements
5. **Test incrementally** - Build and test each component before moving on

### **Quality Assurance:**
- Always request **type hints and docstrings**
- Ask for **error handling** in every component
- Request **production-ready** implementations
- Include **logging and monitoring** in all prompts
- Ensure **security considerations** are addressed

**You now have a complete roadmap to build a production-grade RAG system with Claude Code! 🚀**