#!/bin/bash
# AI Video Generator Bot - Local Docker Testing Script
# This script tests the complete Docker setup locally

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================"
echo -e "AI Video Bot - Local Docker Testing"
echo -e "========================================${NC}"
echo ""

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}✗ Docker is not running. Please start Docker.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker is running${NC}"
}

# Function to wait for service health
wait_for_health() {
    local service_name=$1
    local max_attempts=30
    local sleep_seconds=2
    
    echo -e "${YELLOW}Waiting for $service_name to be healthy...${NC}"
    
    for ((i=1; i<=max_attempts; i++)); do
        health=$(docker inspect --format='{{.State.Health.Status}}' "$service_name" 2>/dev/null || echo "unknown")
        
        if [ "$health" = "healthy" ]; then
            echo -e "${GREEN}✓ $service_name is healthy!${NC}"
            return 0
        fi
        
        echo -e "${CYAN}  Attempt $i/$max_attempts - Status: $health${NC}"
        sleep $sleep_seconds
    done
    
    echo -e "${RED}✗ $service_name failed to become healthy${NC}"
    return 1
}

# Check if Docker is running
echo -e "${CYAN}[1/8] Checking Docker...${NC}"
check_docker
echo ""

# Stop and remove existing containers
echo -e "${CYAN}[2/8] Cleaning up existing containers...${NC}"
docker-compose down -v 2>/dev/null || true
echo -e "${GREEN}✓ Cleanup complete${NC}"
echo ""

# Build Docker images
echo -e "${CYAN}[3/8] Building Docker images...${NC}"
docker-compose build
echo -e "${GREEN}✓ Docker images built successfully${NC}"
echo ""

# Start Redis container
echo -e "${CYAN}[4/8] Starting Redis container...${NC}"
docker-compose up -d redis

if ! wait_for_health "ai-video-bot-redis"; then
    echo -e "${RED}✗ Redis health check failed${NC}"
    docker-compose logs redis
    exit 1
fi
echo ""

# Start Flask web container
echo -e "${CYAN}[5/8] Starting Flask web container...${NC}"
docker-compose up -d web

if ! wait_for_health "ai-video-bot-web"; then
    echo -e "${RED}✗ Web service health check failed${NC}"
    docker-compose logs web
    exit 1
fi
echo ""

# Start Celery worker container
echo -e "${CYAN}[6/8] Starting Celery worker container...${NC}"
docker-compose up -d worker

# Wait a bit for worker to initialize
echo -e "${YELLOW}Waiting for worker to initialize...${NC}"
sleep 5
echo -e "${GREEN}✓ Worker started${NC}"
echo ""

# Check health endpoint
echo -e "${CYAN}[7/8] Testing health check endpoint...${NC}"
if response=$(curl -s -w "\n%{http_code}" http://localhost:5000/health 2>/dev/null); then
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$status_code" = "200" ]; then
        echo -e "${GREEN}✓ Health check passed: $body${NC}"
    else
        echo -e "${RED}✗ Health check returned status: $status_code${NC}"
    fi
else
    echo -e "${RED}✗ Health check failed${NC}"
fi
echo ""

# Test Redis connection
echo -e "${CYAN}[8/8] Testing Redis connection...${NC}"
if redis_test=$(docker exec ai-video-bot-redis redis-cli ping 2>/dev/null); then
    if [ "$redis_test" = "PONG" ]; then
        echo -e "${GREEN}✓ Redis connection successful${NC}"
    else
        echo -e "${RED}✗ Redis connection failed${NC}"
    fi
else
    echo -e "${RED}✗ Redis connection failed${NC}"
fi
echo ""

# Display container status
echo -e "${CYAN}========================================"
echo -e "Container Status"
echo -e "========================================${NC}"
docker-compose ps
echo ""

# Display logs summary
echo -e "${CYAN}========================================"
echo -e "Recent Logs"
echo -e "========================================${NC}"
echo ""
echo -e "${YELLOW}--- Redis Logs (last 10 lines) ---${NC}"
docker-compose logs --tail=10 redis
echo ""
echo -e "${YELLOW}--- Web Logs (last 15 lines) ---${NC}"
docker-compose logs --tail=15 web
echo ""
echo -e "${YELLOW}--- Worker Logs (last 15 lines) ---${NC}"
docker-compose logs --tail=15 worker
echo ""

# Summary
echo -e "${CYAN}========================================"
echo -e "Testing Summary"
echo -e "========================================${NC}"
echo ""
echo -e "${GREEN}All containers are running!${NC}"
echo ""
echo -e "${CYAN}Services:${NC}"
echo "  - Redis:  http://localhost:6379"
echo "  - Web:    http://localhost:5000"
echo "  - Worker: Running in background"
echo ""
echo -e "${CYAN}Useful commands:${NC}"
echo "  - View logs:        docker-compose logs -f [service]"
echo "  - Stop services:    docker-compose down"
echo "  - Restart service:  docker-compose restart [service]"
echo "  - Shell access:     docker exec -it ai-video-bot-web bash"
echo ""

# Check if API keys are configured
echo -e "${CYAN}========================================"
echo -e "API Configuration Check"
echo -e "========================================${NC}"
echo ""

if [ -f .env ]; then
    has_openai=$(grep -q "OPENAI_API_KEY=sk-" .env && echo "yes" || echo "no")
    has_runway=$(grep -q "RUNWAY_API_KEY=key_" .env && echo "yes" || echo "no")
    has_telegram=$(grep -q "TELEGRAM_BOT_TOKEN=[0-9]" .env && echo "yes" || echo "no")
    
    if [ "$has_openai" = "yes" ]; then
        echo -e "${GREEN}✓ OpenAI API key configured${NC}"
    else
        echo -e "${YELLOW}⚠ OpenAI API key not configured${NC}"
    fi
    
    if [ "$has_runway" = "yes" ]; then
        echo -e "${GREEN}✓ Runway API key configured${NC}"
    else
        echo -e "${YELLOW}⚠ Runway API key not configured${NC}"
    fi
    
    if [ "$has_telegram" = "yes" ]; then
        echo -e "${GREEN}✓ Telegram bot token configured${NC}"
    else
        echo -e "${YELLOW}⚠ Telegram bot token not configured${NC}"
    fi
    
    echo ""
    if [ "$has_openai" != "yes" ] || [ "$has_runway" != "yes" ] || [ "$has_telegram" != "yes" ]; then
        echo -e "${YELLOW}Note: Some API keys are not configured."
        echo "      Full functionality testing requires all API keys."
        echo "      Update .env file with your API keys to test end-to-end.${NC}"
    else
        echo -e "${GREEN}All API keys are configured! You can test full functionality.${NC}"
    fi
else
    echo -e "${YELLOW}⚠ .env file not found${NC}"
fi

echo ""
echo -e "${CYAN}========================================"
echo -e "${GREEN}Docker testing complete!${NC}"
echo -e "${CYAN}========================================${NC}"
