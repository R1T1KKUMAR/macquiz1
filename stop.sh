#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "Stopping MacQuiz servers..."

# Find and kill processes on port 8000 (backend)
BACKEND_PID=$(lsof -ti:8000)
if [ ! -z "$BACKEND_PID" ]; then
    kill -9 $BACKEND_PID
    echo -e "${GREEN}✓ Backend server stopped${NC}"
else
    echo "Backend server not running"
fi

# Find and kill processes on port 5173 (frontend)
FRONTEND_PID=$(lsof -ti:5173)
if [ ! -z "$FRONTEND_PID" ]; then
    kill -9 $FRONTEND_PID
    echo -e "${GREEN}✓ Frontend server stopped${NC}"
else
    echo "Frontend server not running"
fi

echo "Done!"
