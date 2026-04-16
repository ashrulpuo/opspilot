# OpsPilot Backend Tests Guide

## Overview
This guide explains how to run the test suite for OpsPilot backend and interpret coverage results.

## Prerequisites
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies (if needed)
pip install -r requirements.txt
```

## Running Tests

### Unit Tests
Unit tests are isolated tests for individual modules and functions.

```bash
# Run specific test files
python -m pytest tests/unit/test_security.py -v
python -m pytest tests/unit/test_vault.py -v
python -m pytest tests/unit/test_salt.py -v
python -m pytest tests/unit/test_email.py -v
python -m pytest tests/unit/models/ -v
```

### Coverage Collection
We use custom test runners to collect coverage without conftest.py import issues.

```bash
# Run final comprehensive test runner
coverage run -m final_test_runner

# Generate coverage report
coverage report --omit="*/tests/*,*/__pycache__/*,*/migrations/*"

# Generate HTML report
coverage html --omit="*/tests/*,*/__pycache__/*,*/migrations/*"
```

### Viewing Coverage Reports

**Terminal Report:**
```bash
coverage report --omit="*/tests/*,*/__pycache__/*,*/migrations/*"
```

**HTML Report:**
```bash
# Open the HTML coverage report
open htmlcov/index.html

# Or use a local web server
cd htmlcov && python -m http.server 8080
# Then visit http://localhost:8080
```

## Coverage Targets

| Module | Current Coverage | Target Coverage | Gap |
|--------|-----------------|-----------------|-----|
| Overall | **48%** | **80%+** | **32%** |
| Core Modules | **40% avg** | **80%+** | **40%** |
| Models | **95% avg** | **100%** | **5%** |
| Services | **0%** | **80%+** | **80%** |

## Test Files Structure

```
tests/
├── unit/
│   ├── test_security.py          # Security utilities tests
│   ├── test_vault.py            # Vault client tests
│   ├── test_salt.py             # Salt API client tests
│   ├── test_email.py            # Email service tests
│   ├── test_auth.py             # Authentication tests
│   ├── test_servers.py          # Server endpoints tests
│   └── models/                # Model tests
│       ├── test_user.py
│       ├── test_server.py
│       ├── test_organization.py
│       ├── test_deployment.py
│       ├── test_backup.py
│       ├── test_alert.py
│       ├── test_metrics.py
│       ├── test_execution.py
│       ├── test_ssh_session.py
│       ├── test_password_reset.py
│       └── test_base.py
├── integration/
│   └── test_database.py       # Database integration tests
├── conftest.py                  # Test configuration and fixtures
└── README_TESTS.md              # This file
```

## Running Specific Test Categories

### Security Tests
Focus on password hashing, verification, and security utilities.

```bash
# Run all security tests
python -m pytest tests/unit/test_security.py -v --cov=app/core/security --cov-report=html
```

### Model Tests
Comprehensive tests for all database models.

```bash
# Run all model tests
python -m pytest tests/unit/models/ -v --cov=app/models --cov-report=html

# Run specific model tests
python -m pytest tests/unit/models/test_user.py -v
python -m pytest tests/unit/models/test_server.py -v
```

### API Integration Tests
Test API endpoints with database integration.

```bash
# Run integration tests
python -m pytest tests/integration/ -v --cov=app/api --cov-report=html
```

## Coverage Improvement Strategy

### Current Status: 48% → Target: 80%+

**Achieved:**
- ✅ 48% overall coverage (+48% from baseline)
- ✅ Core modules significantly improved
- ✅ Model layer fully tested (95% average)
- ✅ Security utilities covered (36%)
- ✅ External services tested (Vault, Salt, Email)

**Remaining Work:**
- ⚠️ API endpoints need integration tests (estimated +20-25% coverage)
- ⚠️ Services layer needs testing (estimated +8-10% coverage)
- ⚠️ Exception handling needs expansion (estimated +5-8% coverage)
- ⚠️ Main application entry point needs coverage (estimated +2-5% coverage)

### Next Priority Actions

1. **Fix conftest.py Configuration** 
   - Resolve full application import issues
   - Implement proper database fixtures
   - Use pytest-asyncio for async testing

2. **API Endpoint Integration Tests**
   - Create test suite for 21 API endpoint files
   - Test authentication, authorization, validation
   - Test CRUD operations (Create, Read, Update, Delete)
   - Test error handling and edge cases

3. **Service Layer Testing**
   - Test business logic in server_service.py
   - Test business logic in salt_service.py
   - Cover success and failure scenarios
   - Test interaction with external services

4. **Exception and Error Handling**
   - Test all exception types in app/core/exceptions.py
   - Test error response formatting
   - Test error translation and handling

## Troubleshooting

### Import Errors
If you encounter import errors like:
```
ModuleNotFoundError: No module named 'app.core.config'
```

**Solution:** Use the standalone test runners:
```bash
# Use final_test_runner.py for comprehensive coverage
coverage run -m final_test_runner

# Or use targeted test runners for specific modules
coverage run -m final_test_runner
```

### Coverage Not Increasing
If coverage isn't increasing after running tests:

1. **Check test execution:** Ensure tests actually run and pass
2. **Verify imports:** Confirm modules are being imported correctly
3. **Check mocking:** Ensure dependencies are properly mocked
4. **Review coverage:** Run `coverage report` to see what's covered

### Database Connection Issues
Integration tests may fail due to database connection:

1. **Use test database:** Configure test database URL in conftest.py
2. **Mock external services:** Use unittest.mock.patch for external dependencies
3. **Run in isolation:** Test integration separately from unit tests

## Continuous Integration

### GitLab CI/CD Integration
Add coverage badge to repository:

```markdown
# In README.md
![Coverage](https://gitlab.com/your-org/opspilot/badges/coverage.svg)
```

### Automated Coverage Reporting
```yaml
# In .gitlab-ci.yml
coverage:
  stage: coverage
  script:
    - coverage run -m pytest
    - coverage report --format=json
  coverage: '/coverage.json'
  artifacts:
    reports:
      coverage_report:
        coverage: '/coverage.json'
```

## Best Practices

### Test Organization
- Keep tests isolated and focused
- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies appropriately
- Keep test execution fast

### Coverage Goals
- Aim for high coverage, but focus on critical paths
- Test business logic and error handling
- Cover edge cases and input validation
- Maintain readable and maintainable tests

---

*Last updated: April 14, 2025*
*Questions or issues? Check TEST_SUMMARY.md and FINAL_REPORT.md for detailed analysis.*