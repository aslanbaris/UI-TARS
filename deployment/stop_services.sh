#!/bin/bash

# UI-TARS Service Stopper

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping UI-TARS services...${NC}"

# Kill by PID files
if [ -f logs/model-service.pid ]; then
    kill $(cat logs/model-service.pid) 2>/dev/null || true
    rm logs/model-service.pid
    echo -e "${GREEN}✓ Mock Model Service stopped${NC}"
fi

if [ -f logs/parser-service.pid ]; then
    kill $(cat logs/parser-service.pid) 2>/dev/null || true
    rm logs/parser-service.pid
    echo -e "${GREEN}✓ Parser Service stopped${NC}"
fi

if [ -f logs/api-gateway.pid ]; then
    kill $(cat logs/api-gateway.pid) 2>/dev/null || true
    rm logs/api-gateway.pid
    echo -e "${GREEN}✓ API Gateway stopped${NC}"
fi

# Fallback: kill by process name
pkill -f "mock_model_service.py" 2>/dev/null || true
pkill -f "parser_service.py" 2>/dev/null || true
pkill -f "api_gateway.py" 2>/dev/null || true

echo -e "\n${GREEN}All services stopped${NC}"
