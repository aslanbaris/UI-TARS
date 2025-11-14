#!/bin/bash

# UI-TARS Service Starter (Without Docker)
# Starts all services locally for testing

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         UI-TARS Service Starter                       ║${NC}"
echo -e "${BLUE}║         Starting services without Docker              ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════╝${NC}\n"

# Check Python packages
echo -e "${YELLOW}Checking Python packages...${NC}"
python3 -c "import fastapi, uvicorn, pydantic, httpx" 2>/dev/null || {
    echo -e "${RED}✗ Missing packages. Installing...${NC}"
    pip install -q fastapi uvicorn[standard] pydantic httpx ui-tars redis
}
echo -e "${GREEN}✓ All packages available${NC}\n"

# Create log directory
mkdir -p logs

# Kill existing services
echo -e "${YELLOW}Stopping existing services...${NC}"
pkill -f "mock_model_service.py" 2>/dev/null || true
pkill -f "parser_service.py" 2>/dev/null || true
pkill -f "api_gateway.py" 2>/dev/null || true
sleep 2
echo -e "${GREEN}✓ Existing services stopped${NC}\n"

# Start Mock Model Service
echo -e "${BLUE}Starting Mock Model Service (port 8081)...${NC}"
cd model-service
nohup python3 mock_model_service.py > ../logs/model-service.log 2>&1 &
MODEL_PID=$!
echo $MODEL_PID > ../logs/model-service.pid
cd ..
sleep 2

# Check if model service started
if curl -s http://localhost:8081/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Mock Model Service started (PID: $MODEL_PID)${NC}"
else
    echo -e "${RED}✗ Failed to start Mock Model Service${NC}"
    exit 1
fi

# Start Parser Service
echo -e "${BLUE}Starting Parser Service (port 8082)...${NC}"
cd parser-service
nohup python3 parser_service.py > ../logs/parser-service.log 2>&1 &
PARSER_PID=$!
echo $PARSER_PID > ../logs/parser-service.pid
cd ..
sleep 2

# Check if parser service started
if curl -s http://localhost:8082/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Parser Service started (PID: $PARSER_PID)${NC}"
else
    echo -e "${RED}✗ Failed to start Parser Service${NC}"
    exit 1
fi

# Start API Gateway
echo -e "${BLUE}Starting API Gateway (port 8080)...${NC}"
export MODEL_SERVICE_URL=http://localhost:8081
export PARSER_SERVICE_URL=http://localhost:8082
export REDIS_URL=redis://localhost:6379
export DATABASE_URL=postgresql://uitars:test@localhost:5432/uitars

cd api-gateway
nohup python3 -c "
import uvicorn
from api_gateway import app
uvicorn.run(app, host='0.0.0.0', port=8080, log_level='info')
" > ../logs/api-gateway.log 2>&1 &
GATEWAY_PID=$!
echo $GATEWAY_PID > ../logs/api-gateway.pid
cd ..
sleep 3

# Check if API gateway started
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API Gateway started (PID: $GATEWAY_PID)${NC}"
else
    echo -e "${YELLOW}⚠  API Gateway may have issues (Redis/Postgres not running)${NC}"
fi

# Summary
echo -e "\n${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║             Services Started Successfully             ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}\n"

echo -e "${BLUE}Service URLs:${NC}"
echo -e "  • Mock Model:  ${GREEN}http://localhost:8081/health${NC}"
echo -e "  • Parser:      ${GREEN}http://localhost:8082/health${NC}"
echo -e "  • API Gateway: ${GREEN}http://localhost:8080/health${NC}"

echo -e "\n${BLUE}Logs:${NC}"
echo -e "  • tail -f logs/model-service.log"
echo -e "  • tail -f logs/parser-service.log"
echo -e "  • tail -f logs/api-gateway.log"

echo -e "\n${BLUE}To stop services:${NC}"
echo -e "  • ./stop_services.sh"
echo -e "  • Or: pkill -f 'mock_model_service.py|parser_service.py|api_gateway.py'"

echo -e "\n${YELLOW}Test the services:${NC}"
echo -e "  curl http://localhost:8080/health | jq"

echo ""
