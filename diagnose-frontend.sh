#!/bin/bash

# OpsPilot Frontend Diagnostic Script
# Check frontend status and provide solutions

echo "🔍 OpsPilot Frontend Diagnostics..."
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check 1: Check which port frontend is running on
echo "🔌 Checking Vite Processes..."
VITE_PIDS=$(ps aux | grep -E "vite.*opspilot" | grep -v grep | grep -v defunct | awk '{print $2}')
echo "Found Vite processes: $VITE_PIDS"

# Check 2: Check which ports are listening
echo ""
echo "🔌 Checking Listening Ports..."
PORTS=$(netstat -an 2>/dev/null | grep LISTEN | grep -E ":(8848|8090|5173|8000)" | awk '{print $4}' | sort -u)
echo "Frontend candidate ports: $PORTS"

# Check 3: Check frontend logs for errors
echo ""
echo "📋 Checking Frontend Logs..."
LOG_FILE="/tmp/frontend_final.log"
if [ -f "$LOG_FILE" ]; then
    echo "Log file: $LOG_FILE"
    echo "Last 20 lines:"
    tail -n 20 "$LOG_FILE"
else
    echo -e "${YELLOW}⚠️ Log file not found${NC}"
fi

# Check 4: Check for duplicate exports
echo ""
echo "🔍 Checking for Duplicate Exports..."
DUPLICATE_EXPORTS=$(grep -r "export.*CommandsAPI" /Volumes/ashrul/Development/Active/opspilot/frontend/src/api/opspilot/*.ts | wc -l | awk '{print $1}')
if [ "$DUPLICATE_EXPORTS" -gt 2 ]; then
    echo -e "${RED}❌ Found $DUPLICATE_EXPORTS exports of CommandsAPI${NC}"
    echo "Expected: Only 1 export"
else
    echo -e "${GREEN}✅ No duplicate exports found${NC}"
fi

# Check 5: Check import paths
echo ""
echo "🔍 Checking Import Paths..."
IMPORT_ERRORS=$(grep -r "from '../client'" /Volumes/ashrul/Development/Active/opspilot/frontend/src/api/opspilot/*.ts 2>/dev/null | wc -l | awk '{print $1}')
if [ "$IMPORT_ERRORS" -gt 0 ]; then
    echo -e "${RED}❌ Found $IMPORT_ERRORS incorrect import paths${NC}"
    echo "Expected: from '../opspilot/client'"
    echo "Run: cd frontend/src/api/opspilot && for file in *.ts; do sed -i '' \"s|from '../client'|from '../opspilot/client'|g\" \"$file\"; done"
else
    echo -e "${GREEN}✅ All imports are correct${NC}"
fi

# Summary
echo ""
echo "========================================"
echo "📊 Diagnostic Summary"
echo "========================================"

if [ -z "$VITE_PIDS" ]; then
    echo -e "${RED}❌ Frontend dev server is NOT running${NC}"
    echo "To start:"
    echo "  cd /Volumes/ashrul/Development/Active/opspilot/frontend"
    echo "  pnpm dev"
else
    echo -e "${GREEN}✅ Frontend dev server IS running${NC}"
    echo "PID(s): $VITE_PIDS"
    echo ""
    echo "Try these URLs in your browser:"
    for port in $PORTS; do
        echo "  - http://localhost:$port"
    done
fi

echo "========================================"