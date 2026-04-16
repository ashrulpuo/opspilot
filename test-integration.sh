#!/bin/bash

# OpsPilot Integration Test Script
# Test frontend-backend integration

echo "🧪 Running OpsPilot Integration Tests..."
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

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

# Test 1: Backend Health
echo "🔌 Testing Backend..."
run_test "Backend health endpoint" "curl -s http://localhost:8000/api/v1/health"

# Test 2: Frontend Running
echo "🎨 Testing Frontend..."
run_test "Frontend is running" "curl -s http://localhost:8848 > /dev/null 2>&1"

# Test 3: API Documentation
echo "📚 Testing API Documentation..."
run_test "API docs accessible" "curl -s http://localhost:8000/docs > /dev/null 2>&1"

# Test 4: OpenAPI Schema
echo "🔧 Testing OpenAPI Schema..."
run_test "OpenAPI JSON accessible" "curl -s http://localhost:8000/openapi.json > /dev/null 2>&1"

# Test 5: Backend API v1
echo "🔌 Testing Backend API v1..."
run_test "API v1 endpoint" "curl -s http://localhost:8000/api/v1/ > /dev/null 2>&1"

# Summary
echo "========================================"
echo "📊 Integration Test Summary"
echo "========================================"
echo -e "Tests Run:    ${GREEN}$TESTS_RUN${NC}"
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

PASS_RATE=$(( (TESTS_PASSED * 100) / TESTS_RUN))
echo -e "Pass Rate: ${GREEN}$PASS_RATE%${NC}"
echo "========================================"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All integration tests passed!${NC}"
    exit 0
else
    echo -e "${RED}⚠️ Some integration tests failed.${NC}"
    exit 1
fi
