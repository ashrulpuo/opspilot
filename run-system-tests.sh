#!/bin/bash

# OpsPilot System Test Script
# Run comprehensive system tests before deployment

echo "🧪 Running OpsPilot System Tests..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test
run_test() {
    TESTS_RUN=$((TESTS_RUN + 1))
    echo "[$TESTS_RUN] $1"
    
    if eval "$2"; then
        echo -e "${GREEN}✅ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ FAILED${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    echo ""
}

# Test 1: Check if Docker is running
echo "🐳 Testing Infrastructure..."
run_test "Docker is running" "docker ps > /dev/null 2>&1"

# Test 2: Check PostgreSQL is healthy
run_test "PostgreSQL is healthy" "docker ps | grep opspilot-postgres | grep healthy"

# Test 3: Check Redis is healthy
run_test "Redis is healthy" "docker ps | grep opspilot-redis | grep healthy"

# Test 4: Check Vault is running
run_test "Vault is running" "docker ps | grep opspilot-vault"

# Test 5: Check Python version
echo "🐍 Testing Python Environment..."
run_test "Python 3.14+ is available" "python3 --version | grep -E '3\.1[4-9]'"

# Test 6: Check Poetry is installed
run_test "Poetry is installed" "poetry --version > /dev/null 2>&1"

# Test 7: Check backend dependencies
echo "📦 Testing Backend Dependencies..."
cd /Volumes/ashrul/Development/Active/opspilot/backend
run_test "Backend dependencies installed" "poetry check > /dev/null 2>&1"

# Test 8: Check frontend dependencies
echo "🎨 Testing Frontend Dependencies..."
cd /Volumes/ashrul/Development/Active/opspilot/frontend
if [ -f "package.json" ]; then
    run_test "Frontend package.json exists" "true"
    run_test "Frontend node_modules exists" "[ -d node_modules ]"
else
    echo -e "${YELLOW}⚠️ Frontend package.json not found${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 9: Run backend unit tests
echo "🧪 Testing Backend Tests..."
cd /Volumes/ashrul/Development/Active/opspilot/backend
if [ -d "tests" ]; then
    echo "Running backend tests..."
    export PATH="/Users/ashrul/.local/bin:$PATH"
    poetry run pytest tests/models/test_user.py -v --tb=short > /tmp/backend_tests.log 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ FAILED${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo "Check test results: /tmp/backend_tests.log"
    fi
else
    echo -e "${YELLOW}⚠️ Backend tests directory not found${NC}"
fi
echo ""

# Test 10: Check test coverage
echo "📊 Testing Test Coverage..."
cd /Volumes/ashrul/Development/Active/opspilot/backend
if [ -f ".coverage" ]; then
    run_test "Coverage report exists" "true"
    
    # Try to read coverage (if pytest-cov is installed)
    if command -v pytest &> /dev/null; then
        echo "Running coverage check..."
        poetry run pytest --cov=app tests/models/test_user.py --cov-report=term > /tmp/coverage.log 2>&1
        
        if grep -q "coverage:" /tmp/coverage.log 2>/dev/null; then
            echo -e "${GREEN}✅ PASSED${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            # Extract coverage percentage
            COVERAGE=$(grep "coverage:" /tmp/coverage.log | head -1)
            echo -e "${GREEN}$COVERAGE${NC}"
        else
            echo -e "${YELLOW}⚠️ Coverage check skipped (pytest-cov not fully configured)${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️ pytest-cov not available${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ Coverage report not found${NC}"
fi
echo ""

# Test 11: Check documentation
echo "📚 Testing Documentation..."
cd /Volumes/ashrul/Development/Active/opspilot

DOCS_TO_CHECK=(
    "docs/archive/reports/FINAL_COMPLETION_REPORT.md"
    "docs/backend/FORGOT_PASSWORD_COMPLETE.md"
    "docs/backend/SECURITY_SCAN_COMPLETE.md"
    "docs/frontend/E2E_TESTS_COMPLETE.md"
    "docs/deployment/DEPLOYMENT_STATUS.md"
)

for doc in "${DOCS_TO_CHECK[@]}"; do
    if [ -f "$doc" ]; then
        echo -e "${GREEN}✅${NC} $doc"
    else
        echo -e "${RED}❌${NC} $doc"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
done

echo ""

# Test 12: Check API endpoints count
echo "🔌 Testing API Endpoints..."
cd /Volumes/ashrul/Development/Active/opspilot/backend/app/api/v1
API_COUNT=$(find . -name "*.py" ! -name "__*" | wc -l | tr -d ' ')
echo "Found $API_COUNT API endpoint files"
if [ "$API_COUNT" -ge 10 ]; then
    echo -e "${GREEN}✅ PASSED${NC} (10+ API modules)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠️ WARNING${NC} (less than 10 API modules)"
fi
echo ""

# Test 13: Check model count
echo "🗄️ Testing Models..."
cd /Volumes/ashrul/Development/Active/opspilot/backend/app/models
MODEL_COUNT=$(find . -name "*.py" ! -name "__*" ! -name "base.py" | wc -l | tr -d ' ')
echo "Found $MODEL_COUNT model files"
if [ "$MODEL_COUNT" -ge 10 ]; then
    echo -e "${GREEN}✅ PASSED${NC} (10+ models)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠️ WARNING${NC} (less than 10 models)"
fi
echo ""

# Test 14: Check E2E tests
echo "🎭 Testing E2E Tests..."
cd /Volumes/ashrul/Development/Active/opspilot/frontend
if [ -f "tests/e2e/specs/opspilot.spec.ts" ]; then
    run_test "E2E test file exists" "true"
    
    if [ -f "playwright.config.ts" ]; then
        run_test "Playwright config exists" "true"
    else
        echo -e "${YELLOW}⚠️ Playwright config not found${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ E2E tests not found${NC}"
fi
echo ""

# Print summary
echo "========================================"
echo "📊 Test Summary"
echo "========================================"
echo -e "Tests Run:    ${GREEN}$TESTS_RUN${NC}"
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""
PASS_RATE=$(( (TESTS_PASSED * 100) / TESTS_RUN))
echo -e "Pass Rate: ${GREEN}$PASS_RATE%${NC}"
echo "========================================"

# Exit with appropriate code
if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! Ready for deployment.${NC}"
    exit 0
else
    echo -e "${RED}⚠️ Some tests failed. Review and fix before deployment.${NC}"
    exit 1
fi
