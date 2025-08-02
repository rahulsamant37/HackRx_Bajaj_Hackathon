# Phase 1: Foundation & Configuration - Workflow Diagram

## Mermaid Diagram

```mermaid
graph TB
    A[Project Initialization] --> B[Environment Setup]
    B --> C[FastAPI Application Setup]
    C --> D[Configuration Management]
    D --> E[Logging System]
    E --> F[Exception Handling]
    F --> G[Middleware Implementation]
    G --> H[Health Check Endpoints]
    H --> I[Testing Infrastructure]

    %% Detailed Flow
    subgraph "Environment Setup"
        B1[Create Virtual Environment]
        B2[Install Dependencies]
        B3[Setup .env Configuration]
        B --> B1 --> B2 --> B3
    end

    subgraph "FastAPI Application"
        C1[Create FastAPI Instance]
        C2[Configure CORS Middleware]
        C3[Setup Lifespan Events]
        C4[Configure Documentation]
        C --> C1 --> C2 --> C3 --> C4
    end

    subgraph "Configuration System"
        D1[Pydantic Settings Model]
        D2[Environment Variable Loading]
        D3[Configuration Validation]
        D4[Settings Caching]
        D --> D1 --> D2 --> D3 --> D4
    end

    subgraph "Logging Implementation"
        E1[Structured Logging Setup]
        E2[Request ID Generation]
        E3[Performance Metrics]
        E4[Log Level Configuration]
        E --> E1 --> E2 --> E3 --> E4
    end

    subgraph "Exception System"
        F1[Base Exception Classes]
        F2[Domain-Specific Exceptions]
        F3[HTTP Status Mapping]
        F4[Error Context Capture]
        F --> F1 --> F2 --> F3 --> F4
    end

    subgraph "Middleware Stack"
        G1[Request Logging Middleware]
        G2[Error Handling Middleware]
        G3[Performance Monitoring]
        G4[Security Headers]
        G --> G1 --> G2 --> G3 --> G4
    end

    subgraph "Health Checks"
        H1[Basic Health Endpoint]
        H2[Detailed Health Check]
        H3[Kubernetes Probes]
        H4[Service Information]
        H --> H1 --> H2 --> H3 --> H4
    end

    subgraph "Testing Setup"
        I1[Pytest Configuration]
        I2[Test Fixtures]
        I3[Coverage Setup]
        I4[Test Environment]
        I --> I1 --> I2 --> I3 --> I4
    end

    %% Component Interactions
    D4 -.-> C1
    E4 -.-> G1
    F4 -.-> G2
    H4 -.-> D4

    %% Validation Flow
    J[Configuration Validation] --> K{Valid Config?}
    K -->|Yes| L[Application Start]
    K -->|No| M[Startup Error]
    
    D3 --> J
    L --> N[Ready for Phase 2]
    M --> O[Fix Configuration]
    O --> J

    %% Styling
    classDef setupPhase fill:#e1f5fe
    classDef configPhase fill:#f3e5f5
    classDef loggingPhase fill:#e8f5e8
    classDef errorPhase fill:#fff3e0
    classDef middlewarePhase fill:#fce4ec
    classDef healthPhase fill:#e0f2f1
    classDef testPhase fill:#f1f8e9

    class A,B,B1,B2,B3 setupPhase
    class C,C1,C2,C3,C4,D,D1,D2,D3,D4 configPhase
    class E,E1,E2,E3,E4 loggingPhase
    class F,F1,F2,F3,F4 errorPhase
    class G,G1,G2,G3,G4 middlewarePhase
    class H,H1,H2,H3,H4 healthPhase
    class I,I1,I2,I3,I4 testPhase
```

## Component Flow Details

### 1. Environment Setup Flow
```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Env as Environment
    participant Deps as Dependencies
    participant Config as Configuration

    Dev->>Env: Create virtual environment
    Env->>Dev: Environment ready
    Dev->>Deps: Install requirements.txt
    Deps->>Dev: Dependencies installed
    Dev->>Config: Copy .env.example to .env
    Config->>Dev: Configuration template ready
```

### 2. Configuration Loading Flow
```mermaid
sequenceDiagram
    participant App as Application
    participant Settings as Pydantic Settings
    participant EnvFile as .env File
    participant EnvVars as Environment Variables
    participant Validation as Validators

    App->>Settings: Initialize Settings
    Settings->>EnvFile: Load .env file
    Settings->>EnvVars: Load environment variables
    Settings->>Validation: Validate all settings
    Validation-->>Settings: Validation results
    Settings-->>App: Configured settings instance
```

### 3. Middleware Stack Setup
```mermaid
graph LR
    A[Incoming Request] --> B[CORS Middleware]
    B --> C[Request Logging Middleware]
    C --> D[Error Handling Middleware]
    D --> E[FastAPI Application]
    E --> F[Health Check Endpoint]
    F --> G[Response]
    G --> H[Performance Logging]
    H --> I[Outgoing Response]

    %% Error Flow
    D --> J[Exception Caught]
    J --> K[Error Logging]
    K --> L[Error Response]
    L --> I
```

### 4. Health Check Architecture
```mermaid
graph TB
    A[Health Check Request] --> B{Endpoint Type}
    
    B -->|/health| C[Basic Health Check]
    B -->|/health/detailed| D[Detailed Health Check]
    B -->|/health/ready| E[Readiness Probe]
    B -->|/health/live| F[Liveness Probe]
    B -->|/health/info| G[Service Information]

    C --> H[Return Status: OK]
    
    D --> I[Check Dependencies]
    I --> J[Check Resources]
    J --> K[Return Detailed Status]

    E --> L[Check Readiness]
    L --> M{All Systems Ready?}
    M -->|Yes| N[200 OK]
    M -->|No| O[503 Service Unavailable]

    F --> P[Check Liveness]
    P --> Q{Application Alive?}
    Q -->|Yes| R[200 OK]
    Q -->|No| S[503 Service Unavailable]

    G --> T[Return Service Info]
```

## Key Files Created in Phase 1

```mermaid
graph LR
    A[Phase 1 Files] --> B[app/main.py]
    A --> C[app/config.py]
    A --> D[app/middleware.py]
    A --> E[app/utils/logger.py]
    A --> F[app/utils/exceptions.py]
    A --> G[app/api/endpoints/health.py]
    A --> H[requirements.txt]
    A --> I[.env.example]
    A --> J[pytest.ini]

    B --> B1[FastAPI App Creation]
    B --> B2[Middleware Registration]
    B --> B3[Lifespan Management]

    C --> C1[Pydantic Settings]
    C --> C2[Environment Loading]
    C --> C3[Validation Rules]

    D --> D1[Request Logging]
    D --> D2[Error Handling]
    D --> D3[Performance Monitoring]

    E --> E1[Structured Logging]
    E --> E2[Request Tracing]
    E --> E3[Performance Metrics]

    F --> F1[Exception Hierarchy]
    F --> F2[Error Codes]
    F --> F3[Context Capture]

    G --> G1[Health Endpoints]
    G --> G2[Dependency Checks]
    G --> G3[System Metrics]
```

## Success Criteria Checklist

```mermaid
graph TB
    A[Phase 1 Complete] --> B{FastAPI Running?}
    B -->|Yes| C{Configuration Valid?}
    B -->|No| Z[Fix FastAPI Setup]
    
    C -->|Yes| D{Logging Working?}
    C -->|No| Y[Fix Configuration]
    
    D -->|Yes| E{Health Checks Pass?}
    D -->|No| X[Fix Logging]
    
    E -->|Yes| F{Tests Passing?}
    E -->|No| W[Fix Health Checks]
    
    F -->|Yes| G[✅ Ready for Phase 2]
    F -->|No| V[Fix Tests]

    Z --> B
    Y --> C  
    X --> D
    W --> E
    V --> F
```

## Excalidraw Conversion Notes

When converting to Excalidraw:

1. **Use consistent shapes**: Rectangles for processes, diamonds for decisions, circles for start/end
2. **Color coding**: Use the suggested color scheme from the classDef
3. **Group related components**: Use grouping boxes for subgraphs
4. **Add icons**: Consider adding small icons for different component types
5. **Flow direction**: Maintain top-to-bottom or left-to-right flow
6. **Connection styles**: Use different arrow styles for different relationship types (solid for flow, dashed for dependencies)

## Component Legend

- 🔧 **Setup Phase**: Environment and project initialization
- ⚙️ **Configuration**: Settings and environment management  
- 📝 **Logging**: Structured logging and monitoring
- ❌ **Error Handling**: Exception management and error responses
- 🔄 **Middleware**: Request/response processing pipeline
- 💚 **Health Checks**: System monitoring and status endpoints
- 🧪 **Testing**: Test infrastructure and quality assurance