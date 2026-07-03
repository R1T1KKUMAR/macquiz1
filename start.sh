#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

clear
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}     MacQuiz - Complete Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    echo "Please install Python 3.8 or higher"
    exit 1
fi
echo -e "${GREEN}✓ Python $(python3 --version) found${NC}"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    echo "Please install Node.js 16 or higher"
    exit 1
fi
echo -e "${GREEN}✓ Node.js $(node --version) found${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down servers...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}✓ Servers stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# ========================================
# Backend Setup
# ========================================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Setting up Backend${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${GREEN}Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Install dependencies
echo -e "${GREEN}Installing backend dependencies...${NC}"
pip install -r requirements.txt > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Backend dependencies installed${NC}"
else
    echo -e "${RED}❌ Failed to install backend dependencies${NC}"
    exit 1
fi

# Start backend server in background
echo -e "${GREEN}Starting backend server...${NC}"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend server started (PID: $BACKEND_PID)${NC}"
echo -e "${BLUE}   URL: http://localhost:8000${NC}"
echo -e "${BLUE}   Docs: http://localhost:8000/docs${NC}"
echo ""

cd ..

# ========================================
# Frontend Setup
# ========================================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Setting up Frontend${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${GREEN}Installing frontend dependencies...${NC}"
    npm install > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
    else
        echo -e "${RED}❌ Failed to install frontend dependencies${NC}"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
else
    echo -e "${GREEN}✓ Frontend dependencies already installed${NC}"
fi

# Start frontend server in background
echo -e "${GREEN}Starting frontend server...${NC}"
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}✓ Frontend server started (PID: $FRONTEND_PID)${NC}"
echo -e "${BLUE}   URL: http://localhost:5173${NC}"
echo ""

cd ..

# ========================================
# Summary
# ========================================
sleep 3  # Wait for servers to fully start

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  🎉 MacQuiz is Running!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Frontend:${NC}    http://localhost:5173"
echo -e "${GREEN}Backend API:${NC} http://localhost:8000"
echo -e "${GREEN}API Docs:${NC}    http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}Default Login Credentials:${NC}"
echo -e "  Email:    admin@macquiz.com"
echo -e "  Password: admin123"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo -e "  Backend:  backend.log"
echo -e "  Frontend: frontend.log"
echo ""
echo -e "${RED}Press Ctrl+C to stop all servers${NC}"
echo ""

# Wait for user interrupt
wait
