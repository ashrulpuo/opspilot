# Testing Guide

This document describes the testing setup for the SaltStack Data Collection feature.

## Backend Testing

### Test Structure

```
backend/tests/
├── conftest.py                 # Pytest configuration and fixtures
├── test_api/                   # API endpoint tests
│   └── test_salt_endpoints.py  # Salt API integration tests
├── test_models/                # Model unit tests
│   └── test_salt_models.py     # Salt model tests
└── test_services/              # Service unit tests
    ├── test_salt_api_client.py   # Salt API client tests
    └── test_sse_service.py      # SSE service tests
```

### Running Backend Tests

```bash
# Run all tests
cd backend
pytest

# Run specific test file
pytest tests/test_models/test_salt_models.py

# Run with coverage
pytest --cov=backend/app --cov-report=html

# Run async tests only
pytest -m asyncio

# Run integration tests only
pytest -m integration
```

### Test Coverage

- **Models:** 100% coverage target
- **Services:** 80% coverage target
- **API Endpoints:** 80% coverage target

### Test Fixtures

- `db_session`: Async database session (in-memory SQLite)
- `client`: Async HTTP client with database override
- `sample_metrics`: Sample metrics data
- `sample_beacon_data`: Sample beacon data
- `sample_service_data`: Sample service data
- `sample_process_data`: Sample process data
- `sample_package_data`: Sample package data
- `sample_log_data`: Sample log data

---

## Frontend Testing

### Test Structure

```
frontend/
├── vitest.config.ts            # Vitest configuration
├── tests/
│   ├── setup.ts                # Test setup and mocks
│   └── composables/
│       └── __tests__/
│           └── useSaltStream.spec.ts  # SSE composable tests
```

### Running Frontend Tests

```bash
# Run all tests
cd frontend
npm run test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch

# Run specific test file
npm run test -- src/composables/__tests__/useSaltStream.spec.ts
```

### Test Coverage

- **Composables:** 80% coverage target
- **Components:** 70% coverage target

### Test Mocks

- `window.matchMedia`: Mocked for responsive components
- `IntersectionObserver`: Mocked for lazy loading
- `ResizeObserver`: Mocked for resize handling
- `localStorage`: Mocked for browser storage
- `useSaltStore`: Mocked Pinia store

---

## E2E Testing (Future)

### Tools

- **Playwright** or **Cypress**
- Test critical user flows

### Test Scenarios

- Server registration
- Metrics streaming
- Service management
- Process monitoring
- Package updates
- Log filtering
- Alert acknowledgment

### Running E2E Tests

```bash
# Playwright
cd frontend
npx playwright test

# Cypress
cd frontend
npm run test:e2e
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      - name: Run tests
        run: |
          cd backend
          pytest --cov=backend/app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd frontend
          npm install
      - name: Run tests
        run: |
          cd frontend
          npm run test:coverage
```

---

## Testing Best Practices

1. **Arrange, Act, Assert** - Structure tests clearly
2. **Isolate tests** - Each test should be independent
3. **Use fixtures** - Reuse common test data
4. **Mock external dependencies** - Redis, Salt API, etc.
5. **Test edge cases** - Invalid data, errors, timeouts
6. **Keep tests fast** - Use in-memory databases
7. **Use descriptive names** - Test names should explain what they test

---

## Troubleshooting

### Backend Tests Fail

```bash
# Clean test database
rm -f test.db

# Reset dependencies
pip install -r requirements.txt --force-reinstall
```

### Frontend Tests Fail

```bash
# Clear cache
rm -rf node_modules/.vite

# Reinstall dependencies
rm -rf node_modules
npm install
```

### Slow Tests

```bash
# Run only specific tests
pytest tests/test_models/test_salt_models.py::TestSaltMinion

# Skip slow tests
pytest -m "not slow"
```
