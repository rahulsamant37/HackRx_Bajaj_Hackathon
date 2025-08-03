# Phase 4: Testing Framework - Workflow Diagram

## Complete Testing Architecture

```mermaid
graph TB
    A[Testing Framework] --> B[Test Categories]
    B --> C[Unit Tests]
    B --> D[Integration Tests]
    B --> E[Performance Tests]
    B --> F[API Tests]
    
    subgraph "Unit Testing Flow"
        C --> C1[Configuration Tests]
        C --> C2[Service Tests]
        C --> C3[Utility Tests]
        C --> C4[Model Tests]
        
        C1 --> C1A[Settings Validation]
        C1A --> C1B[Environment Loading]
        C1B --> C1C[Config Errors]
        
        C2 --> C2A[Document Service]
        C2A --> C2B[RAG Service]
        C2B --> C2C[Vector Operations]
        
        C3 --> C3A[Logger Functions]
        C3A --> C3B[Exception Handling]
        C3B --> C3C[Helper Functions]
        
        C4 --> C4A[Request Models]
        C4A --> C4B[Response Models]
        C4B --> C4C[Validation Rules]
    end
    
    subgraph "Integration Testing Flow"
        D --> D1[End-to-End Workflows]
        D --> D2[Service Integration]
        D --> D3[Database Operations]
        D --> D4[External API Integration]
        
        D1 --> D1A[Upload → Process → Query]
        D1A --> D1B[Multi-Document Scenarios]
        D1B --> D1C[Error Recovery]
        
        D2 --> D2A[Service Communication]
        D2A --> D2B[Dependency Injection]
        D2B --> D2C[Cross-Service Validation]
        
        D3 --> D3A[Vector Store Operations]
        D3A --> D3B[Metadata Management]
        D3B --> D3C[Persistence Testing]
        
        D4 --> D4A[GEMINI API Integration]
        D4A --> D4B[Rate Limiting]
        D4B --> D4C[Error Handling]
    end
    
    subgraph "Performance Testing Flow"
        E --> E1[Load Testing]
        E --> E2[Stress Testing]
        E --> E3[Benchmark Testing]
        E --> E4[Resource Monitoring]
        
        E1 --> E1A[Concurrent Users]
        E1A --> E1B[Request Throughput]
        E1B --> E1C[Response Times]
        
        E2 --> E2A[Resource Limits]
        E2A --> E2B[Breaking Points]
        E2B --> E2C[Recovery Testing]
        
        E3 --> E3A[Processing Speed]
        E3A --> E3B[Memory Usage]
        E3B --> E3C[Regression Detection]
        
        E4 --> E4A[CPU Monitoring]
        E4A --> E4B[Memory Tracking]
        E4B --> E4C[I/O Performance]
    end
    
    subgraph "API Testing Flow"
        F --> F1[Endpoint Testing]
        F --> F2[Authentication Testing]
        F --> F3[Error Response Testing]
        F --> F4[OpenAPI Compliance]
        
        F1 --> F1A[Request Validation]
        F1A --> F1B[Response Format]
        F1B --> F1C[Status Codes]
        
        F2 --> F2A[Authentication Methods]
        F2A --> F2B[Authorization Levels]
        F2B --> F2C[Security Headers]
        
        F3 --> F3A[Error Scenarios]
        F3A --> F3B[Error Messages]
        F3B --> F3C[Error Codes]
        
        F4 --> F4A[Schema Validation]
        F4A --> F4B[Documentation Sync]
        F4B --> F4C[Example Validation]
    end

    %% Test Execution Flow
    G[Test Execution] --> H[Test Discovery]
    H --> I[Test Selection]
    I --> J[Test Running]
    J --> K[Result Collection]
    K --> L[Report Generation]
    
    %% Quality Gates
    L --> M{Coverage > 80%?}
    M -->|No| N[Coverage Failure]
    M -->|Yes| O{Performance OK?}
    O -->|No| P[Performance Failure]
    O -->|Yes| Q{All Tests Pass?}
    Q -->|No| R[Test Failures]
    Q -->|Yes| S[✅ Tests Passed]

    %% Styling
    classDef unitTest fill:#e3f2fd
    classDef integrationTest fill:#f1f8e9
    classDef performanceTest fill:#fff3e0
    classDef apiTest fill:#fce4ec
    classDef execution fill:#e0f2f1
    classDef quality fill:#ffebee

    class C,C1,C2,C3,C4,C1A,C1B,C1C,C2A,C2B,C2C,C3A,C3B,C3C,C4A,C4B,C4C unitTest
    class D,D1,D2,D3,D4,D1A,D1B,D1C,D2A,D2B,D2C,D3A,D3B,D3C,D4A,D4B,D4C integrationTest
    class E,E1,E2,E3,E4,E1A,E1B,E1C,E2A,E2B,E2C,E3A,E3B,E3C,E4A,E4B,E4C performanceTest
    class F,F1,F2,F3,F4,F1A,F1B,F1C,F2A,F2B,F2C,F3A,F3B,F3C,F4A,F4B,F4C apiTest
    class G,H,I,J,K,L execution
    class M,N,O,P,Q,R,S quality
```

## Test Execution Pipeline

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant pytest as Pytest
    participant Fixtures as Test Fixtures
    participant Mocks as Mock Services
    participant Coverage as Coverage Tool
    participant Report as Report Generator

    Dev->>pytest: Run tests
    pytest->>Fixtures: Load test fixtures
    Fixtures-->>pytest: Test data ready
    
    pytest->>Mocks: Setup mocks
    Mocks-->>pytest: Mock services ready
    
    loop For Each Test
        pytest->>pytest: Execute test
        pytest->>Coverage: Track coverage
        pytest->>pytest: Collect results
    end
    
    pytest->>Coverage: Generate coverage report
    Coverage-->>pytest: Coverage data
    
    pytest->>Report: Generate test report
    Report-->>pytest: Test results
    
    pytest-->>Dev: Test execution complete
```

## Test Fixture Architecture

```mermaid
graph TB
    A[Test Fixtures] --> B[Application Fixtures]
    A --> C[Data Fixtures]
    A --> D[Mock Fixtures]
    A --> E[Database Fixtures]
    
    subgraph "Application Fixtures"
        B --> B1[FastAPI Test Client]
        B --> B2[Test Settings]
        B --> B3[Service Instances]
        
        B1 --> B1A[HTTP Client Setup]
        B1A --> B1B[Authentication Setup]
        B1B --> B1C[Base URL Configuration]
        
        B2 --> B2A[Test Environment Config]
        B2A --> B2B[Mock API Keys]
        B2B --> B2C[Test Database Paths]
        
        B3 --> B3A[RAG Service Instance]
        B3A --> B3B[Document Service Instance]
        B3B --> B3C[Vector Store Instance]
    end
    
    subgraph "Data Fixtures"
        C --> C1[Sample Documents]
        C --> C2[Test Queries]
        C --> C3[Expected Responses]
        
        C1 --> C1A[PDF Documents]
        C1A --> C1B[Text Documents]
        C1B --> C1C[DOCX Documents]
        C1C --> C1D[Markdown Documents]
        
        C2 --> C2A[Simple Questions]
        C2A --> C2B[Complex Questions]
        C2B --> C2C[Edge Case Queries]
        
        C3 --> C3A[Known Answers]
        C3A --> C3B[Error Responses]
        C3B --> C3C[Validation Results]
    end
    
    subgraph "Mock Fixtures"
        D --> D1[GEMINI Mock]
        D --> D2[External Service Mocks]
        D --> D3[File System Mocks]
        
        D1 --> D1A[Embedding Responses]
        D1A --> D1B[Chat Completions]
        D1B --> D1C[Error Scenarios]
        
        D2 --> D2A[HTTP Service Mocks]
        D2A --> D2B[Database Mocks]
        D2B --> D2C[Cache Mocks]
        
        D3 --> D3A[Temporary Files]
        D3A --> D3B[Upload Simulation]
        D3B --> D3C[File Cleanup]
    end
    
    subgraph "Database Fixtures"
        E --> E1[Test Vector Store]
        E --> E2[Sample Data Population]
        E --> E3[Cleanup Procedures]
        
        E1 --> E1A[Temporary Index]
        E1A --> E1B[Test Metadata]
        E1B --> E1C[Isolation Setup]
        
        E2 --> E2A[Pre-loaded Documents]
        E2A --> E2B[Known Embeddings]
        E2B --> E2C[Test Scenarios]
        
        E3 --> E3A[Post-Test Cleanup]
        E3A --> E3B[Resource Release]
        E3B --> E3C[State Reset]
    end
```

## Mock Strategy Implementation

```mermaid
graph TB
    A[Mock Strategy] --> B[GEMINI API Mocking]
    A --> C[File System Mocking]
    A --> D[Database Mocking]
    A --> E[Network Mocking]
    
    subgraph "GEMINI API Mocking"
        B --> B1[Embedding API Mock]
        B --> B2[Chat Completion Mock]
        B --> B3[Error Simulation]
        
        B1 --> B1A[Deterministic Embeddings]
        B1A --> B1B[Consistent Vectors]
        B1B --> B1C[Performance Simulation]
        
        B2 --> B2A[Pre-defined Answers]
        B2A --> B2B[Streaming Simulation]
        B2B --> B2C[Token Usage Tracking]
        
        B3 --> B3A[Rate Limit Errors]
        B3A --> B3B[API Failures]
        B3B --> B3C[Network Timeouts]
    end
    
    subgraph "File System Mocking"
        C --> C1[File Upload Simulation]
        C --> C2[Storage Operations]
        C --> C3[File Access Control]
        
        C1 --> C1A[Multipart Upload Mock]
        C1A --> C1B[File Validation Mock]
        C1B --> C1C[Size Limit Testing]
        
        C2 --> C2A[Read Operations]
        C2A --> C2B[Write Operations]  
        C2B --> C2C[Delete Operations]
        
        C3 --> C3A[Permission Testing]
        C3A --> C3B[Access Errors]
        C3B --> C3C[Security Validation]
    end
    
    subgraph "Database Mocking"
        D --> D1[Vector Store Mock]
        D --> D2[Metadata Store Mock]
        D --> D3[Transaction Mock]
        
        D1 --> D1A[Search Operations]
        D1A --> D1B[Index Operations]
        D1B --> D1C[Performance Simulation]
        
        D2 --> D2A[CRUD Operations]
        D2A --> D2B[Query Simulation]
        D2B --> D2C[Consistency Testing]
        
        D3 --> D3A[Commit/Rollback]
        D3A --> D3B[Isolation Testing]
        D3B --> D3C[Concurrency Control]
    end
    
    subgraph "Network Mocking"
        E --> E1[HTTP Request Mock]
        E --> E2[Response Simulation]
        E --> E3[Network Errors]
        
        E1 --> E1A[Request Validation]
        E1A --> E1B[Header Checking]
        E1B --> E1C[Body Verification]
        
        E2 --> E2A[Status Code Control]
        E2A --> E2B[Response Body Mock]
        E2B --> E2C[Timing Simulation]
        
        E3 --> E3A[Connection Errors]
        E3A --> E3B[Timeout Errors]
        E3B --> E3C[DNS Errors]
    end
```

## Performance Testing Architecture

```mermaid
graph TB
    A[Performance Testing] --> B[Load Testing]
    A --> C[Stress Testing]
    A --> D[Volume Testing]
    A --> E[Endurance Testing]
    
    subgraph "Load Testing Setup"
        B --> B1[User Simulation]
        B --> B2[Request Patterns]
        B --> B3[Ramp-up Strategy]
        
        B1 --> B1A[Concurrent Users: 1-50]
        B1A --> B1B[User Behavior Modeling]
        B1B --> B1C[Session Management]
        
        B2 --> B2A[Document Upload Load]
        B2A --> B2B[Q&A Query Load]
        B2B --> B2C[Mixed Workload]
        
        B3 --> B3A[Gradual Increase]
        B3A --> B3B[Spike Testing]
        B3B --> B3C[Sustained Load]
    end
    
    subgraph "Stress Testing Setup"
        C --> C1[Resource Limits]
        C --> C2[Breaking Points]
        C --> C3[Recovery Testing]
        
        C1 --> C1A[Memory Exhaustion]
        C1A --> C1B[CPU Saturation]
        C1B --> C1C[Disk Space Limits]
        
        C2 --> C2A[Maximum Throughput]
        C2A --> C2B[Error Thresholds]
        C2B --> C2C[System Limits]
        
        C3 --> C3A[Graceful Degradation]
        C3A --> C3B[Service Recovery]
        C3B --> C3C[Data Consistency]
    end
    
    subgraph "Volume Testing Setup"
        D --> D1[Large Document Sets]
        D --> D2[High Query Volume]
        D --> D3[Data Scaling]
        
        D1 --> D1A[1000+ Documents]
        D1A --> D1B[Large File Sizes]
        D1B --> D1C[Processing Time]
        
        D2 --> D2A[10000+ Queries]
        D2A --> D2B[Complex Questions]
        D2B --> D2C[Response Quality]
        
        D3 --> D3A[Vector Store Scaling]
        D3A --> D3B[Memory Usage]
        D3B --> D3C[Search Performance]
    end
    
    subgraph "Endurance Testing Setup"
        E --> E1[Long Duration]
        E --> E2[Memory Leaks]
        E --> E3[Resource Cleanup]
        
        E1 --> E1A[24+ Hour Runs]
        E1A --> E1B[Sustained Load]
        E1B --> E1C[Performance Drift]
        
        E2 --> E2A[Memory Monitoring]
        E2A --> E2B[Leak Detection]
        E2B --> E2C[Resource Growth]
        
        E3 --> E3A[File Cleanup]
        E3A --> E3B[Connection Cleanup]
        E3B --> E3C[Cache Management]
    end
```

## Continuous Integration Test Flow

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Git as Git Repository
    participant CI as CI Pipeline
    participant Tests as Test Suite
    participant Coverage as Coverage Check
    participant Quality as Quality Gates
    participant Deploy as Deployment

    Dev->>Git: Push code changes
    Git->>CI: Trigger pipeline
    
    CI->>CI: Setup environment
    CI->>CI: Install dependencies
    
    CI->>Tests: Run unit tests
    Tests-->>CI: Test results
    
    alt Unit Tests Pass
        CI->>Tests: Run integration tests
        Tests-->>CI: Test results
        
        alt Integration Tests Pass
            CI->>Tests: Run performance tests
            Tests-->>CI: Performance results
            
            CI->>Coverage: Check coverage
            Coverage-->>CI: Coverage report
            
            alt Coverage > 80%
                CI->>Quality: Quality gates check
                Quality-->>CI: Quality results
                
                alt Quality Gates Pass
                    CI->>Deploy: Deploy to staging
                    Deploy-->>CI: Deployment success
                else Quality Gates Fail
                    CI-->>Dev: Quality failure notification
                end
            else Coverage Too Low
                CI-->>Dev: Coverage failure notification
            end
        else Integration Tests Fail
            CI-->>Dev: Integration test failure
        end
    else Unit Tests Fail
        CI-->>Dev: Unit test failure notification
    end
```

## Test Data Management

```mermaid
graph TB
    A[Test Data Management] --> B[Test Data Creation]
    A --> C[Test Data Storage]
    A --> D[Test Data Cleanup]
    A --> E[Test Data Versioning]
    
    subgraph "Test Data Creation"
        B --> B1[Sample Document Generation]
        B --> B2[Mock Response Creation]
        B --> B3[Edge Case Data]
        
        B1 --> B1A[PDF Generator]
        B1A --> B1B[Text Generator]
        B1B --> B1C[DOCX Creator]
        B1C --> B1D[Markdown Builder]
        
        B2 --> B2A[API Response Templates]
        B2A --> B2B[Error Response Templates]
        B2B --> B2C[Streaming Data]
        
        B3 --> B3A[Large Files]
        B3A --> B3B[Corrupted Data]
        B3B --> B3C[Empty Files]
        B3C --> B3D[Unicode Edge Cases]
    end
    
    subgraph "Test Data Storage"
        C --> C1[File System Storage]
        C --> C2[Database Storage]
        C --> C3[Memory Cache]
        
        C1 --> C1A[fixtures/ Directory]
        C1A --> C1B[Organized by Type]
        C1B --> C1C[Version Control]
        
        C2 --> C2A[Test Database]
        C2A --> C2B[Seed Data Scripts]
        C2B --> C2C[Data Isolation]
        
        C3 --> C3A[Fixture Caching]
        C3A --> C3B[Performance Optimization]
        C3B --> C3C[Memory Management]
    end
    
    subgraph "Test Data Cleanup"
        D --> D1[Automatic Cleanup]
        D --> D2[Manual Cleanup]
        D --> D3[Cleanup Verification]
        
        D1 --> D1A[Post-Test Hooks]
        D1A --> D1B[Temporary File Removal]
        D1B --> D1C[Database Cleanup]
        
        D2 --> D2A[Cleanup Commands]
        D2A --> D2B[Force Cleanup]
        D2B --> D2C[Selective Cleanup]
        
        D3 --> D3A[Resource Verification]
        D3A --> D3B[Memory Check]
        D3B --> D3C[File System Check]
    end
    
    subgraph "Test Data Versioning"
        E --> E1[Data Schema Versions]
        E --> E2[Backward Compatibility]
        E --> E3[Migration Testing]
        
        E1 --> E1A[Version Tracking]
        E1A --> E1B[Schema Evolution]
        E1B --> E1C[Breaking Changes]
        
        E2 --> E2A[Legacy Support]
        E2A --> E2B[Compatibility Matrix]
        E2B --> E2C[Deprecation Paths]
        
        E3 --> E3A[Migration Scripts]
        E3A --> E3B[Data Validation]
        E3B --> E3C[Rollback Testing]
    end
```

## Test Reporting & Analytics

```mermaid
graph LR
    A[Test Execution] --> B[Result Collection]
    B --> C[Report Generation]
    C --> D[Analytics Dashboard]
    
    subgraph "Result Collection"
        B --> B1[Test Outcomes]
        B --> B2[Coverage Data]
        B --> B3[Performance Metrics]
        B --> B4[Error Information]
        
        B1 --> B1A[Pass/Fail Status]
        B1A --> B1B[Execution Time]
        B1B --> B1C[Test Categories]
        
        B2 --> B2A[Line Coverage]
        B2A --> B2B[Branch Coverage]
        B2B --> B2C[Function Coverage]
        
        B3 --> B3A[Response Times]
        B3A --> B3B[Memory Usage]
        B3B --> B3C[CPU Usage]
        
        B4 --> B4A[Exception Details]
        B4A --> B4B[Stack Traces]
        B4B --> B4C[Error Categories]
    end
    
    subgraph "Report Generation"
        C --> C1[HTML Reports]
        C --> C2[XML Reports]
        C --> C3[JSON Reports]
        C --> C4[PDF Reports]
        
        C1 --> C1A[Interactive Coverage]
        C1A --> C1B[Test Results View]
        C1B --> C1C[Performance Charts]
        
        C2 --> C2A[CI Integration]
        C2A --> C2B[JUnit Format]
        C2B --> C2C[Tool Compatibility]
        
        C3 --> C3A[API Integration]
        C3A --> C3B[Data Processing]
        C3B --> C3C[Custom Analytics]
        
        C4 --> C4A[Executive Summary]
        C4A --> C4B[Detailed Analysis]
        C4B --> C4C[Recommendations]
    end
    
    subgraph "Analytics Dashboard"
        D --> D1[Trend Analysis]
        D --> D2[Quality Metrics]
        D --> D3[Performance Tracking]
        D --> D4[Alert System]
        
        D1 --> D1A[Test Pass Rate Trends]
        D1A --> D1B[Coverage Trends]
        D1B --> D1C[Performance Trends]
        
        D2 --> D2A[Code Quality Score]
        D2A --> D2B[Test Reliability]
        D2B --> D2C[Bug Detection Rate]
        
        D3 --> D3A[Response Time Tracking]
        D3A --> D3B[Resource Usage Trends]
        D3B --> D3C[Scalability Metrics]
        
        D4 --> D4A[Failure Alerts]
        D4A --> D4B[Performance Degradation]
        D4B --> D4C[Coverage Drops]
    end
```

## Quality Gates Implementation

```mermaid
graph TB
    A[Quality Gates] --> B[Coverage Gates]
    A --> C[Performance Gates] 
    A --> D[Security Gates]
    A --> E[Reliability Gates]
    
    subgraph "Coverage Gates"
        B --> B1{Line Coverage ≥ 80%?}
        B --> B2{Branch Coverage ≥ 70%?}
        B --> B3{Function Coverage ≥ 90%?}
        
        B1 -->|No| B4[Coverage Failure]
        B2 -->|No| B4
        B3 -->|No| B4
        B1 -->|Yes| B5[Coverage Pass]
        B2 -->|Yes| B5
        B3 -->|Yes| B5
    end
    
    subgraph "Performance Gates"
        C --> C1{Response Time < 3s?}
        C --> C2{Memory Usage < 500MB?}
        C --> C3{Error Rate < 1%?}
        
        C1 -->|No| C4[Performance Failure]
        C2 -->|No| C4
        C3 -->|No| C4
        C1 -->|Yes| C5[Performance Pass]
        C2 -->|Yes| C5
        C3 -->|Yes| C5
    end
    
    subgraph "Security Gates"
        D --> D1{Vulnerability Scan Pass?}
        D --> D2{Dependency Check Pass?}
        D --> D3{SAST Analysis Pass?}
        
        D1 -->|No| D4[Security Failure]
        D2 -->|No| D4
        D3 -->|No| D4
        D1 -->|Yes| D5[Security Pass]
        D2 -->|Yes| D5
        D3 -->|Yes| D5
    end
    
    subgraph "Reliability Gates"
        E --> E1{Test Pass Rate ≥ 95%?}
        E --> E2{Flaky Test Rate < 5%?}
        E --> E3{Build Success Rate ≥ 90%?}
        
        E1 -->|No| E4[Reliability Failure]
        E2 -->|No| E4
        E3 -->|No| E4
        E1 -->|Yes| E5[Reliability Pass]
        E2 -->|Yes| E5
        E3 -->|Yes| E5
    end
    
    %% Final Decision
    B5 --> F{All Gates Pass?}
    C5 --> F
    D5 --> F
    E5 --> F
    
    B4 --> G[Deployment Blocked]
    C4 --> G
    D4 --> G
    E4 --> G
    
    F -->|Yes| H[✅ Deployment Approved]
    F -->|No| G
```

## Excalidraw Conversion Guidelines

For Excalidraw conversion:

1. **Shapes & Icons**:
   - Rectangle: Test categories and processes
   - Circle: Start/end points
   - Diamond: Decision points and quality gates
   - Hexagon: Mock services and external dependencies
   - Cloud: CI/CD pipeline components

2. **Color Scheme**:
   - Blue (#e3f2fd): Unit tests
   - Green (#f1f8e9): Integration tests
   - Orange (#fff3e0): Performance tests
   - Pink (#fce4ec): API tests
   - Teal (#e0f2f1): Test execution flow
   - Red (#ffebee): Quality gates and failures

3. **Flow Indicators**:
   - Solid arrows: Sequential test flow
   - Dashed arrows: Dependencies and relationships
   - Thick arrows: Main execution path
   - Dotted arrows: Async operations and callbacks

4. **Grouping Elements**:
   - Background rectangles: Test categories
   - Swim lanes: Different test phases
   - Containers: Related test components
   - Frames: Quality assurance processes

5. **Status Indicators**:
   - Green check marks: Passed tests/gates
   - Red X marks: Failed tests/gates
   - Yellow warning signs: Performance issues
   - Progress bars: Coverage and metrics