# Phase 3: API Endpoints Implementation - Workflow Diagram

## Complete API Architecture

```mermaid
graph TB
    A[HTTP Request] --> B[FastAPI Router]
    B --> C{Endpoint Type}
    
    C -->|Documents| D[Document Management API]
    C -->|Q&A| E[Question-Answer API]
    C -->|Health| F[Health Check API]
    
    subgraph "Document Management Flow"
        D --> D1[Document Upload]
        D --> D2[Document Listing]
        D --> D3[Document Retrieval]
        D --> D4[Document Deletion]
        D --> D5[Document Reprocessing]
        
        D1 --> D1A[File Validation]
        D1A --> D1B[Background Processing]
        D1B --> D1C[Status Updates]
        
        D2 --> D2A[Pagination Logic]
        D2A --> D2B[Filtering]
        D2B --> D2C[Sorting]
        
        D3 --> D3A[Document Lookup]
        D3A --> D3B[Chunk Retrieval]
        D3B --> D3C[Metadata Assembly]
        
        D4 --> D4A[Document Validation]
        D4A --> D4B[Vector Cleanup]
        D4B --> D4C[Confirmation]
        
        D5 --> D5A[Reprocess Request]
        D5A --> D5B[Background Task]
        D5B --> D5C[Status Tracking]
    end
    
    subgraph "Q&A Flow"
        E --> E1[Simple Q&A]
        E --> E2[Streaming Q&A]
        E --> E3[Conversational Chat]
        E --> E4[Session Management]
        E --> E5[Feedback Collection]
        
        E1 --> E1A[Question Processing]
        E1A --> E1B[Context Retrieval]
        E1B --> E1C[Answer Generation]
        E1C --> E1D[Response Assembly]
        
        E2 --> E2A[Stream Setup]
        E2A --> E2B[Progressive Generation]
        E2B --> E2C[Real-time Updates]
        E2C --> E2D[Stream Completion]
        
        E3 --> E3A[Session Lookup]
        E3A --> E3B[Context Building]
        E3B --> E3C[Conversation Update]
        E3C --> E3D[Response with Memory]
        
        E4 --> E4A[Session Creation]
        E4A --> E4B[History Retrieval]
        E4B --> E4C[Session Cleanup]
        
        E5 --> E5A[Feedback Validation]
        E5A --> E5B[Storage]
        E5B --> E5C[Analytics Update]
    end
    
    subgraph "Health Check Flow"
        F --> F1[Basic Health]
        F --> F2[Detailed Health]
        F --> F3[Readiness Probe]
        F --> F4[Liveness Probe]
        F --> F5[Service Info]
        
        F1 --> F1A[Quick Status]
        F2 --> F2A[Dependency Checks]
        F2A --> F2B[Resource Monitoring]
        F2B --> F2C[Performance Metrics]
        
        F3 --> F3A[Service Readiness]
        F4 --> F4A[Application Liveness]
        F5 --> F5A[Version Info]
        F5A --> F5B[Configuration Info]
    end
    
    %% Response Processing
    D1D[Document Response] --> G[Response Middleware]
    E1D --> G
    E2D --> G
    E3D --> G
    F1A --> G
    F2C --> G
    
    G --> H[Error Handling]
    H --> I[Logging]
    I --> J[HTTP Response]

    %% Styling
    classDef docAPI fill:#e3f2fd
    classDef qaAPI fill:#f1f8e9
    classDef healthAPI fill:#fff3e0
    classDef middleware fill:#fce4ec
    classDef response fill:#e0f2f1

    class D,D1,D2,D3,D4,D5,D1A,D1B,D1C,D2A,D2B,D2C,D3A,D3B,D3C,D4A,D4B,D4C,D5A,D5B,D5C docAPI
    class E,E1,E2,E3,E4,E5,E1A,E1B,E1C,E1D,E2A,E2B,E2C,E2D,E3A,E3B,E3C,E3D,E4A,E4B,E4C,E5A,E5B,E5C qaAPI
    class F,F1,F2,F3,F4,F5,F1A,F2A,F2B,F2C,F3A,F4A,F5A,F5B healthAPI
    class G,H,I middleware
    class J response
```

## Document Upload API Flow

```mermaid
sequenceDiagram
    participant Client as Client
    participant API as Document API
    participant Validator as File Validator
    participant BGTask as Background Task
    participant DocService as Document Service
    participant Storage as Vector Store
    participant Status as Status Tracker

    Client->>API: POST /documents/upload
    Note over Client,API: Multipart file upload
    
    API->>Validator: Validate files
    alt Invalid Files
        Validator-->>API: Validation errors
        API-->>Client: 400 Bad Request
    else Valid Files
        Validator-->>API: Files validated
        API->>BGTask: Queue processing
        BGTask-->>API: Task ID
        API-->>Client: 202 Accepted + Task ID
        
        par Background Processing
            BGTask->>DocService: Process documents
            DocService->>Storage: Store embeddings
            Storage-->>DocService: Storage complete
            DocService-->>BGTask: Processing complete
            BGTask->>Status: Update status
        and Status Polling
            loop Status Check
                Client->>API: GET /documents/status/{task_id}
                API->>Status: Check status
                Status-->>API: Current status
                API-->>Client: Status response
            end
        end
    end
```

## Streaming Q&A Implementation

```mermaid
sequenceDiagram
    participant Client as Client
    participant API as Q&A API
    participant RAG as RAG Service
    participant OpenAI as OpenAI API
    participant Stream as SSE Handler

    Client->>API: POST /qa/ask/stream
    Note over Client,API: Question with streaming flag
    
    API->>Stream: Initialize SSE connection
    Stream-->>Client: Connection established
    
    API->>RAG: Process question
    RAG->>OpenAI: Stream chat completion
    
    loop Streaming Response
        OpenAI-->>RAG: Partial response chunk
        RAG-->>API: Processed chunk
        API->>Stream: Send SSE event
        Stream-->>Client: data: {"chunk": "text"}
    end
    
    OpenAI-->>RAG: Stream complete
    RAG-->>API: Final response with sources
    API->>Stream: Send completion event
    Stream-->>Client: data: {"complete": true, "sources": [...]}
    Stream->>Client: Close connection
```

## Session Management Architecture

```mermaid
graph TB
    A[Chat Request] --> B{Session ID Provided?}
    
    B -->|No| C[Create New Session]
    B -->|Yes| D[Load Existing Session]
    
    C --> E[Generate Session ID]
    E --> F[Initialize Context]
    F --> G[Store Session]
    
    D --> H{Session Exists?}
    H -->|No| I[Session Not Found Error]
    H -->|Yes| J[Load Session Context]
    
    G --> K[Process Message]
    J --> K
    
    K --> L[Retrieve Relevant Context]
    L --> M[Build Conversation History]
    M --> N[Generate Response]
    N --> O[Update Session]
    O --> P[Return Response]
    
    subgraph "Session Storage"
        Q[Session Store] --> R[Session Metadata]
        R --> S[Message History]
        S --> T[Context Window]
        T --> U[User Preferences]
    end
    
    subgraph "Session Cleanup"
        V[Cleanup Scheduler] --> W{Session Age}
        W -->|Old| X[Archive Session]
        W -->|Active| Y[Keep Session]
        X --> Z[Free Resources]
    end
    
    O -.-> Q
    G -.-> Q
    V -.-> Q
```

## Request Validation Pipeline

```mermaid
graph LR
    A[Incoming Request] --> B[Pydantic Validation]
    B --> C{Valid?}
    
    C -->|No| D[Validation Error]
    D --> E[400 Bad Request]
    
    C -->|Yes| F[Business Logic Validation]
    F --> G{Business Rules OK?}
    
    G -->|No| H[Business Error]
    H --> I[422 Unprocessable Entity]
    
    G -->|Yes| J[Security Validation]
    J --> K{Security Check OK?}
    
    K -->|No| L[Security Error]
    L --> M[403 Forbidden]
    
    K -->|Yes| N[Rate Limit Check]
    N --> O{Under Limit?}
    
    O -->|No| P[Rate Limit Error]
    P --> Q[429 Too Many Requests]
    
    O -->|Yes| R[Process Request]
    R --> S[Success Response]
    
    subgraph "Validation Types"
        T[Schema Validation] --> B
        U[File Type Check] --> F
        V[Size Limits] --> F
        W[Input Sanitization] --> J
        X[Request Origin] --> J
        Y[User Quotas] --> N
        Z[Endpoint Limits] --> N
    end
```

## Error Handling & Response Flow

```mermaid
graph TB
    A[Request Processing] --> B{Error Occurred?}
    
    B -->|No| C[Success Response]
    B -->|Yes| D[Error Classification]
    
    D --> E{Error Type}
    
    E -->|Validation| F[400 Bad Request]
    E -->|Authentication| G[401 Unauthorized]  
    E -->|Authorization| H[403 Forbidden]
    E -->|Not Found| I[404 Not Found]
    E -->|Conflict| J[409 Conflict]
    E -->|Payload Too Large| K[413 Payload Too Large]
    E -->|Unprocessable| L[422 Unprocessable Entity]
    E -->|Rate Limit| M[429 Too Many Requests]
    E -->|Internal| N[500 Internal Server Error]
    E -->|Service Unavailable| O[503 Service Unavailable]
    
    F --> P[Error Response Assembly]
    G --> P
    H --> P  
    I --> P
    J --> P
    K --> P
    L --> P
    M --> P
    N --> P
    O --> P
    
    P --> Q[Error Logging]
    Q --> R[Sanitize Error Details]
    R --> S[Add Request ID]
    S --> T[Format Error Response]
    
    C --> U[Success Logging]
    T --> V[HTTP Response]
    U --> V
    
    subgraph "Error Response Format"
        W[Error Object] --> X[Error Code]
        W --> Y[Message]
        W --> Z[Details]
        W --> AA[Request ID]
        W --> BB[Timestamp]
    end
    
    T -.-> W
```

## API Dependency Injection

```mermaid
graph TB
    A[FastAPI Dependency System] --> B[Service Dependencies]
    A --> C[Validation Dependencies]
    A --> D[Security Dependencies]
    A --> E[Configuration Dependencies]
    
    subgraph "Service Dependencies"
        B --> B1[get_rag_service]
        B --> B2[get_document_processor]
        B --> B3[get_session_manager]
        
        B1 --> B1A[RAG Service Instance]
        B2 --> B2A[Document Service Instance]
        B3 --> B3A[Session Manager Instance]
    end
    
    subgraph "Validation Dependencies"
        C --> C1[validate_file_upload]
        C --> C2[validate_question_request]
        C --> C3[validate_session_data]
        
        C1 --> C1A[File Validation Logic]
        C2 --> C2A[Question Validation Logic]
        C3 --> C3A[Session Validation Logic]
    end
    
    subgraph "Security Dependencies"
        D --> D1[rate_limit_check]
        D --> D2[security_headers]
        D --> D3[input_sanitizer]
        
        D1 --> D1A[Rate Limiting Logic]
        D2 --> D2A[Security Header Logic]
        D3 --> D3A[Input Sanitization Logic]
    end
    
    subgraph "Configuration Dependencies"
        E --> E1[get_settings]
        E --> E2[get_openai_client]
        E --> E3[get_vector_store]
        
        E1 --> E1A[Settings Instance]
        E2 --> E2A[OpenAI Client Instance]
        E3 --> E3A[Vector Store Instance]
    end
    
    %% Dependency Relationships
    B1A -.-> E2A
    B1A -.-> E3A
    B2A -.-> E1A
    B3A -.-> E1A
```

## Background Task Processing

```mermaid
graph TB
    A[API Request] --> B[Create Background Task]
    B --> C[Task Queue]
    C --> D[Task Worker]
    
    subgraph "Task Processing"
        D --> E[Task Execution]
        E --> F{Task Type}
        
        F -->|Document Processing| G[Process Document]
        F -->|Reprocessing| H[Reprocess Document]
        F -->|Cleanup| I[Cleanup Resources]
        
        G --> J[Update Progress]
        H --> J
        I --> J
        
        J --> K[Task Status Store]
        K --> L{Task Complete?}
        
        L -->|No| M[Continue Processing]
        L -->|Yes| N[Mark Complete]
        
        M --> E
        N --> O[Notify Completion]
    end
    
    subgraph "Status Tracking"
        P[Status API] --> Q[Check Task Status]
        Q --> K
        K --> R[Return Status]
        R --> S[Client Response]
    end
    
    subgraph "Error Handling"
        E --> T{Error Occurred?}
        T -->|Yes| U[Log Error]
        U --> V[Update Status to Failed]
        V --> W[Error Response]
        T -->|No| J
    end
    
    O -.-> P
    B -.-> K
```

## API Performance Monitoring

```mermaid
graph LR
    A[API Request] --> B[Performance Middleware]
    B --> C[Request Timing Start]
    C --> D[Process Request]
    D --> E[Request Timing End]
    E --> F[Calculate Metrics]
    
    F --> G[Response Time]
    F --> H[Resource Usage]
    F --> I[Status Code]
    F --> J[Error Rate]
    
    G --> K[Metrics Store]
    H --> K
    I --> K
    J --> K
    
    K --> L[Monitoring Dashboard]
    L --> M[Alerts]
    
    subgraph "Metrics Collection"
        N[Request Counter] --> K
        O[Response Time Histogram] --> K
        P[Error Rate Counter] --> K
        Q[Active Connections Gauge] --> K
        R[Queue Length Gauge] --> K
    end
    
    subgraph "Alerting Rules"
        M --> S[High Error Rate]
        M --> T[Slow Response Time]
        M --> U[High Memory Usage]
        M --> V[Queue Overflow]
    end
    
    B -.-> N
    E -.-> O
    T -.-> P
```

## OpenAPI Documentation Generation

```mermaid
graph TB
    A[FastAPI Application] --> B[Route Discovery]
    B --> C[Pydantic Model Analysis]
    C --> D[OpenAPI Schema Generation]
    
    subgraph "Schema Components"
        D --> E[Paths]
        E --> F[Request Models]
        F --> G[Response Models]
        G --> H[Error Models]
        H --> I[Security Schemas]
    end
    
    subgraph "Documentation Endpoints"
        I --> J[/docs - Swagger UI]
        I --> K[/redoc - ReDoc]
        I --> L[/openapi.json - Schema]
    end
    
    subgraph "Enhancement Features"
        M[Custom Descriptions] --> D
        N[Example Requests] --> F
        O[Example Responses] --> G
        P[Error Examples] --> H
        Q[Authentication Examples] --> I
    end
    
    subgraph "Interactive Features"
        J --> R[Try It Out]
        J --> S[Authentication Testing]
        J --> T[Response Validation]
        
        K --> U[Better Typography]
        K --> V[Code Examples]
        K --> W[Navigation]
    end
```

## Endpoint Testing Strategy

```mermaid
graph TB
    A[API Testing] --> B[Unit Tests]
    A --> C[Integration Tests]
    A --> D[Load Tests]
    A --> E[Security Tests]
    
    subgraph "Unit Tests"
        B --> B1[Endpoint Logic]
        B --> B2[Request Validation]
        B --> B3[Response Formatting]
        B --> B4[Error Handling]
    end
    
    subgraph "Integration Tests"
        C --> C1[End-to-End Workflows]
        C --> C2[Service Integration]
        C --> C3[Database Operations]
        C --> C4[External API Calls]
    end
    
    subgraph "Load Tests"
        D --> D1[Concurrent Requests]
        D --> D2[High Throughput]
        D --> D3[Memory Usage]
        D --> D4[Response Times]
    end
    
    subgraph "Security Tests"
        E --> E1[Input Validation]
        E --> E2[Authentication]
        E --> E3[Authorization]
        E --> E4[Rate Limiting]
    end
    
    subgraph "Test Tools"
        F[pytest] --> B
        G[httpx] --> C
        H[locust] --> D
        I[security scanners] --> E
    end
```

## Success Criteria Validation

```mermaid
graph TB
    A[Phase 3 Testing] --> B{Document API Working?}
    B -->|✅| C{Q&A API Working?}
    B -->|❌| B1[Fix Document Endpoints]
    
    C -->|✅| D{Health Checks OK?}
    C -->|❌| C1[Fix Q&A Endpoints]
    
    D -->|✅| E{Streaming Works?}
    D -->|❌| D1[Fix Health Endpoints]
    
    E -->|✅| F{Error Handling OK?}
    E -->|❌| E1[Fix Streaming]
    
    F -->|✅| G{Performance OK?}
    F -->|❌| F1[Fix Error Handling]
    
    G -->|✅| H{Documentation Complete?}
    G -->|❌| G1[Optimize Performance]
    
    H -->|✅| I[✅ Ready for Phase 4]
    H -->|❌| H1[Complete Documentation]
    
    %% Feedback loops
    B1 --> B
    C1 --> C
    D1 --> D
    E1 --> E
    F1 --> F
    G1 --> G
    H1 --> H
```

## Excalidraw Conversion Guidelines

For converting to Excalidraw:

1. **Shapes**:
   - Rectangles: API endpoints and processes
   - Rounded rectangles: Services and handlers
   - Diamonds: Decision points
   - Cylinders: Data stores
   - Clouds: External services

2. **Colors**:
   - Blue (#e3f2fd): Document management
   - Green (#f1f8e9): Q&A functionality  
   - Orange (#fff3e0): Health checks
   - Pink (#fce4ec): Middleware/processing
   - Teal (#e0f2f1): Responses

3. **Flow Types**:
   - Solid thick arrows: Main request flow
   - Solid thin arrows: Data flow
   - Dashed arrows: Dependencies
   - Dotted arrows: Async/background processes

4. **Grouping**:
   - Background rectangles for API groups
   - Swim lanes for different service layers
   - Containers for related components

5. **Labels**:
   - HTTP methods and status codes
   - Service names and versions
   - Performance metrics
   - Error types and codes