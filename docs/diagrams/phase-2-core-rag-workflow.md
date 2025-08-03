# Phase 2: Core RAG Implementation - Workflow Diagram

## Main RAG Workflow

```mermaid
graph TB
    A[Document Input] --> B[Document Processing Service]
    B --> C[Text Extraction]
    C --> D[Text Chunking]
    D --> E[Embedding Generation]
    E --> F[Vector Store Storage]
    
    G[User Query] --> H[Query Embedding]
    H --> I[Similarity Search]
    I --> J[Context Retrieval]
    J --> K[Answer Generation]
    K --> L[Response with Sources]

    %% Document Processing Pipeline
    subgraph "Document Processing Pipeline"
        B --> B1[File Validation]
        B1 --> B2[Format Detection]
        B2 --> B3[Security Check]
        
        C --> C1{File Type}
        C1 -->|PDF| C2[PyPDF2 Extraction]
        C1 -->|DOCX| C3[python-docx Extraction]
        C1 -->|TXT| C4[Text File Reading]
        C1 -->|MD| C5[Markdown Processing]
        
        C2 --> C6[Text Cleaning]
        C3 --> C6
        C4 --> C6
        C5 --> C6
        
        D --> D1[Chunk Size Configuration]
        D1 --> D2[Overlap Calculation]
        D2 --> D3[Boundary Detection]
        D3 --> D4[Metadata Attachment]
    end

    %% Embedding & Storage
    subgraph "Vector Processing"
        E --> E1[GEMINI API Call]
        E1 --> E2[text-embedding-ada-002]
        E2 --> E3[Vector Validation]
        
        F --> F1[FAISS Index Update]
        F1 --> F2[Metadata Storage]
        F2 --> F3[Index Persistence]
    end

    %% Query Processing
    subgraph "Query Processing"
        H --> H1[Query Preprocessing]
        H1 --> H2[GEMINI Embedding]
        
        I --> I1[FAISS Search]
        I1 --> I2[Similarity Scoring]
        I2 --> I3[Result Ranking]
        
        J --> J1[Context Assembly]
        J1 --> J2[Relevance Filtering]
        J2 --> J3[Context Optimization]
    end

    %% Answer Generation
    subgraph "Answer Generation"
        K --> K1[Prompt Construction]
        K1 --> K2[Context Injection]
        K2 --> K3[GEMINI Chat Completion]
        K3 --> K4[Response Processing]
        
        L --> L1[Source Citation]
        L1 --> L2[Confidence Scoring]
        L2 --> L3[Response Formatting]
    end

    %% Error Handling
    B1 --> M{Validation OK?}
    M -->|No| N[Document Error Response]
    M -->|Yes| B2
    
    E3 --> O{Embedding Valid?}
    O -->|No| P[Embedding Error]
    O -->|Yes| F
    
    K3 --> Q{Generation Success?}
    Q -->|No| R[Fallback Response]
    Q -->|Yes| K4

    %% Styling
    classDef docProcess fill:#e3f2fd
    classDef vectorProcess fill:#f1f8e9
    classDef queryProcess fill:#fff3e0
    classDef answerProcess fill:#fce4ec
    classDef errorProcess fill:#ffebee

    class B,B1,B2,B3,C,C1,C2,C3,C4,C5,C6,D,D1,D2,D3,D4 docProcess
    class E,E1,E2,E3,F,F1,F2,F3 vectorProcess
    class G,H,H1,H2,I,I1,I2,I3,J,J1,J2,J3 queryProcess
    class K,K1,K2,K3,K4,L,L1,L2,L3 answerProcess
    class M,N,O,P,Q,R errorProcess
```

## Document Processing Sequence

```mermaid
sequenceDiagram
    participant User as User
    participant DocService as Document Service
    participant FileValidator as File Validator
    participant TextExtractor as Text Extractor
    participant Chunker as Text Chunker
    participant GEMINI as GEMINI API
    participant FAISS as Vector Store

    User->>DocService: Upload Document
    DocService->>FileValidator: Validate File
    
    alt File Invalid
        FileValidator-->>DocService: Validation Error
        DocService-->>User: Error Response
    else File Valid
        FileValidator-->>DocService: Validation OK
        DocService->>TextExtractor: Extract Text
        TextExtractor-->>DocService: Raw Text
        
        DocService->>Chunker: Create Chunks
        Chunker-->>DocService: Text Chunks
        
        loop For Each Chunk
            DocService->>GEMINI: Generate Embedding
            GEMINI-->>DocService: Vector Embedding
        end
        
        DocService->>FAISS: Store Vectors
        FAISS-->>DocService: Storage Confirmation
        DocService-->>User: Processing Complete
    end
```

## RAG Query Processing Flow

```mermaid
sequenceDiagram
    participant User as User
    participant RAGService as RAG Service
    participant GEMINI as GEMINI API
    participant FAISS as Vector Store
    participant ContextAssembler as Context Assembler

    User->>RAGService: Ask Question
    RAGService->>GEMINI: Generate Query Embedding
    GEMINI-->>RAGService: Query Vector
    
    RAGService->>FAISS: Search Similar Vectors
    FAISS-->>RAGService: Similar Chunks
    
    RAGService->>ContextAssembler: Assemble Context
    ContextAssembler-->>RAGService: Formatted Context
    
    RAGService->>GEMINI: Generate Answer
    Note over GEMINI: GPT-3.5-turbo with context
    GEMINI-->>RAGService: Generated Answer
    
    RAGService-->>User: Answer + Sources
```

## Vector Store Architecture

```mermaid
graph TB
    A[Document Chunks] --> B[Embedding Generation]
    B --> C[FAISS Index]
    
    subgraph "FAISS Vector Store"
        C --> D[IndexFlatL2]
        D --> E[Vector Arrays]
        E --> F[Similarity Search]
        
        G[Metadata Store] --> H[Document IDs]
        H --> I[Chunk IDs]
        I --> J[Source Information]
        
        K[Persistence Layer] --> L[Index Files]
        L --> M[Metadata Files]
        M --> N[Configuration Files]
    end
    
    subgraph "Search Operations"
        F --> O[Query Vector Input]
        O --> P[Similarity Calculation]
        P --> Q[Top-K Results]
        Q --> R[Score Filtering]
        R --> S[Result Ranking]
    end
    
    subgraph "Storage Operations"
        E --> T[Add Vectors]
        T --> U[Update Index]
        U --> V[Save to Disk]
        
        J --> W[Store Metadata]
        W --> X[Update Mappings]
        X --> Y[Persist Metadata]
    end

    %% Cross-references
    S -.-> H
    S -.-> I
    V -.-> L
    Y -.-> M
```

## GEMINI Integration Flow

```mermaid
graph LR
    subgraph "Embedding Pipeline"
        A[Text Chunks] --> B[GEMINI Client]
        B --> C[text-embedding-ada-002]
        C --> D[1536-dim Vectors]
        D --> E[Validation]
        E --> F[Storage]
    end
    
    subgraph "Chat Completion Pipeline"  
        G[Question + Context] --> H[Prompt Engineering]
        H --> I[GEMINI Client]
        I --> J[gpt-3.5-turbo]
        J --> K[Generated Answer]
        K --> L[Response Processing]
    end
    
    subgraph "Error Handling"
        M[API Rate Limits] --> N[Exponential Backoff]
        N --> O[Retry Logic]
        O --> P[Circuit Breaker]
        
        Q[API Errors] --> R[Error Classification]
        R --> S[Fallback Strategy]
        S --> T[User Notification]
    end
    
    %% Connections
    E --> M
    I --> Q
    F --> G
```

## Memory Management & Performance

```mermaid
graph TB
    A[Large Document Input] --> B{Size Check}
    B -->|Small| C[Direct Processing]
    B -->|Large| D[Streaming Processing]
    
    C --> E[Memory Buffer]
    D --> F[Chunk-by-Chunk Processing]
    
    F --> G[Process Chunk]
    G --> H[Generate Embedding]
    H --> I[Store Immediately]
    I --> J{More Chunks?}
    J -->|Yes| G
    J -->|No| K[Complete]
    
    E --> L[Full Document Processing]
    L --> M[Batch Embedding]
    M --> N[Bulk Storage]
    
    subgraph "Resource Management"
        O[Memory Monitor] --> P{Memory Usage}
        P -->|High| Q[Trigger Cleanup]
        P -->|Normal| R[Continue Processing]
        
        Q --> S[Clear Buffers]
        S --> T[Garbage Collection]
        T --> R
    end
    
    subgraph "Performance Optimization"
        U[Embedding Cache] --> V[Check Cache]
        V -->|Hit| W[Return Cached]
        V -->|Miss| X[Generate New]
        X --> Y[Update Cache]
        
        Z[Connection Pool] --> AA[Reuse Connections]
        AA --> BB[Reduce Latency]
    end
    
    %% Monitoring
    H -.-> O
    M -.-> O
    H -.-> U
    I -.-> Z
```

## Error Handling & Recovery

```mermaid
graph TB
    A[Operation Start] --> B{Operation Type}
    
    B -->|Document Processing| C[Document Error Handler]
    B -->|Embedding Generation| D[Embedding Error Handler]
    B -->|Vector Storage| E[Storage Error Handler]
    B -->|Query Processing| F[Query Error Handler]
    
    C --> C1{Error Type}
    C1 -->|File Corrupt| C2[File Error Response]
    C1 -->|Size Limit| C3[Size Error Response]
    C1 -->|Unsupported Format| C4[Format Error Response]
    
    D --> D1{Error Type}
    D1 -->|Rate Limit| D2[Exponential Backoff]
    D1 -->|API Error| D3[Retry with Fallback]
    D1 -->|Network Error| D4[Connection Retry]
    
    E --> E1{Error Type}
    E1 -->|Disk Full| E2[Storage Alert]
    E1 -->|Index Corrupt| E3[Index Rebuild]
    E1 -->|Permission Error| E4[Access Error]
    
    F --> F1{Error Type}
    F1 -->|No Results| F2[Empty Result Response]
    F1 -->|Generation Failed| F3[Fallback Answer]
    F1 -->|Context Too Large| F4[Context Truncation]
    
    %% Recovery Actions
    D2 --> G[Wait & Retry]
    D3 --> H[Use Cached Results]
    D4 --> I[Connection Recovery]
    E3 --> J[Rebuild from Backup]
    F3 --> K[Generic Response]
    F4 --> L[Smart Truncation]
    
    %% Logging
    C2 --> M[Log Error]
    C3 --> M
    C4 --> M
    D2 --> M
    E2 --> M
    F2 --> M
    
    M --> N[Error Analytics]
    N --> O[Monitoring Dashboard]
```

## Configuration & Settings Flow

```mermaid
graph LR
    A[Application Start] --> B[Load Configuration]
    B --> C{Config Valid?}
    C -->|No| D[Configuration Error]
    C -->|Yes| E[Initialize Services]
    
    E --> F[RAG Service Init]
    F --> G[Document Service Init]
    
    subgraph "RAG Service Configuration"
        F --> F1[GEMINI Client Setup]
        F1 --> F2[API Key Validation]
        F2 --> F3[Model Configuration]
        F3 --> F4[Vector Store Setup]
        F4 --> F5[FAISS Index Loading]
    end
    
    subgraph "Document Service Configuration"
        G --> G1[File Size Limits]
        G1 --> G2[Supported Formats]
        G2 --> G3[Chunk Configuration]
        G3 --> G4[Processing Options]
    end
    
    subgraph "Runtime Configuration"
        H[Configuration Updates] --> I[Reload Settings]
        I --> J[Update Services]
        J --> K[Validate Changes]
        K --> L[Apply Changes]
    end
    
    F5 --> M[Service Ready]
    G4 --> M
    M --> N[Phase 2 Complete]
```

## Key Components Created

```mermaid
mindmap
  root((Phase 2 Components))
    Document Service
      DocumentProcessor
      ProcessedDocument  
      DocumentChunk
      File Validators
      Text Extractors
      Chunking Logic
    RAG Service
      RAGService
      SearchResult
      ConversationSession
      Embedding Manager
      Context Assembler
    GEMINI Integration
      Async Client
      Embedding API
      Chat Completion API
      Rate Limiting
      Error Handling
    Vector Store
      FAISS Index
      Metadata Storage
      Persistence Layer
      Search Operations
    Pydantic Models
      Request Models
      Response Models
      Validation Rules
      Type Safety
```

## Success Criteria Validation

```mermaid
graph TB
    A[Phase 2 Testing] --> B{Document Processing?}
    B -->|✅| C{Embedding Generation?}
    B -->|❌| B1[Fix Document Processing]
    
    C -->|✅| D{Vector Storage?}
    C -->|❌| C1[Fix Embedding Service]
    
    D -->|✅| E{Similarity Search?}
    D -->|❌| D1[Fix Vector Store]
    
    E -->|✅| F{Answer Generation?}
    E -->|❌| E1[Fix Search Logic]
    
    F -->|✅| G{Performance OK?}
    F -->|❌| F1[Fix Answer Generation]
    
    G -->|✅| H[✅ Ready for Phase 3]
    G -->|❌| G1[Optimize Performance]
    
    %% Feedback loops
    B1 --> B
    C1 --> C
    D1 --> D
    E1 --> E
    F1 --> F
    G1 --> G
```

## Performance Metrics Dashboard

```mermaid
graph LR
    A[Performance Monitoring] --> B[Document Processing]
    A --> C[Embedding Generation]
    A --> D[Search Performance]
    A --> E[Answer Generation]
    
    B --> B1[Processing Speed: docs/min]
    B --> B2[Memory Usage: MB]
    B --> B3[Success Rate: %]
    
    C --> C1[Embedding Speed: chunks/sec]
    C --> C2[API Latency: ms]
    C --> C3[Cost Tracking: $]
    
    D --> D1[Search Latency: ms]
    D --> D2[Result Quality: score]
    D --> D3[Index Size: vectors]
    
    E --> E1[Response Time: sec]
    E --> E2[Answer Quality: score]
    E --> E3[Source Relevance: %]
```

## Excalidraw Conversion Notes

For Excalidraw conversion:

1. **Process Boxes**: Use rounded rectangles for services/processes
2. **Decision Diamonds**: Use diamond shapes for conditional logic
3. **Data Stores**: Use cylinder shapes for databases/storage
4. **APIs**: Use cloud shapes for external services
5. **Flow Types**: 
   - Solid arrows for data flow
   - Dashed arrows for dependencies
   - Thick arrows for main workflow
6. **Color Coding**:
   - Blue: Document processing
   - Green: Vector operations  
   - Orange: Query processing
   - Pink: Answer generation
   - Red: Error handling
7. **Grouping**: Use background rectangles for logical groupings
8. **Icons**: Add small icons for different component types (document, database, API, etc.)