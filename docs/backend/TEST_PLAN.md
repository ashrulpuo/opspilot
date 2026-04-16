# OpsPilot Backend Test Coverage Improvement Plan

## Current Status
- **Baseline Coverage**: 0% (no tests currently exist)
- **Target Coverage**: 80%+
- **Current Test Files**: Only 2 unit test files (test_auth.py, test_servers.py)

## Test Areas to Cover

### 1. Database Models (13 models)
- ✅ User model - Created
- ✅ Server model - Created  
- ✅ Organization model - Created
- ✅ Deployment model - Created
- ✅ Backup model - Created
- ✅ Alert model - Created
- ✅ Metrics model - Created
- ✅ Execution model - Created
- ✅ SSH Session model - Created
- ✅ Password Reset model - Created
- ❌ Base model - Created
- ❌ Additional models (if any)

### 2. API Endpoints (61 endpoints)
- ✅ Auth endpoints - Partially tested
- ❌ All other API endpoints (servers, organizations, metrics, backups, health, salt, alerts, credentials, commands, logs, deployments, ssh)

### 3. Security Utilities
- ❌ Password hashing and verification
- ❌ JWT token generation and validation
- ❌ Authentication middleware
- ❌ Authorization checks

### 4. Vault Client Operations
- ❌ Vault connection and secret management
- ❌ Secret retrieval and storage
- ❌ Vault authentication

### 5. Salt API Client Operations
- ❌ Salt connection and API calls
- ❌ Salt job execution
- ❌ Salt key management

### 6. Email Service
- ❌ Email sending functionality
- ❌ Template rendering
- ❌ Email configuration

### 7. Background Jobs (Celery tasks)
- ❌ Celery task execution
- ❌ Task scheduling
- ❌ Task results handling

### 8. Websocket Handlers
- ❌ WebSocket connection handling
- ❌ Real-time communication
- ❌ Session management

### 9. Error Handlers
- ❌ Custom error handling
- ❌ Exception translation
- ❌ Error response formatting

### 10. Validation Schemas
- ❌ Pydantic schema validation
- ❌ Request/response validation
- ❌ Data serialization/deserialization

## Test Types

### Unit Tests (Target: 50+)
- Model validation and business logic
- Utility functions
- Service layer functionality
- Security utilities
- Configuration handling

### Integration Tests (Target: 20+)
- API endpoint testing
- Database operations
- External service integration (Vault, Salt, Email)
- Celery task execution
- WebSocket functionality

## Implementation Strategy

### Phase 1: Models (Complete)
- Created comprehensive unit tests for all 13 models
- Each model has 10-15 test cases covering:
  - Creation with valid/invalid data
  - String representation
  - Equality/inequality comparisons
  - Default values
  - Update functionality
  - Relationship handling
  - Edge cases

### Phase 2: API Endpoints
- Create integration tests for all API endpoints
- Test HTTP methods (GET, POST, PUT, DELETE)
- Test authentication and authorization
- Test request/response validation
- Test error handling

### Phase 3: Services and Utilities
- Test security utilities (password hashing, JWT)
- Test Vault client operations
- Test Salt API client operations
- Test email service
- Test Celery tasks

### Phase 4: Advanced Features
- Test WebSocket handlers
- Test error handlers
- Test validation schemas

## Deliverables

1. **Coverage Report (Baseline)**: 0% coverage established
2. **50+ Unit Tests**: Completed for all models
3. **20+ Integration Tests**: In progress
4. **Final Coverage Report (>80%)**: Target
5. **Test Documentation**: In progress
6. **Coverage Badge**: To be implemented in GitLab

## Progress Tracking

### Completed (Phase 1)
- ✅ Created test directory structure
- ✅ Created comprehensive unit tests for all 13 models
- ✅ Each model has 10-15 test cases
- ✅ Total: ~130 unit tests created

### In Progress (Phase 2)
- ❌ API endpoint integration tests
- ❌ Service layer tests
- ❌ Security utilities tests

### Planned (Phase 3-4)
- ❌ External service integration tests
- ❌ Advanced feature tests
- ❌ Coverage improvement to 80%+