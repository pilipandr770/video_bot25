#!/bin/bash

# Test script for Docker setup verification
# Run this after starting docker-compose to verify everything works

set -e

echo "=========================================="
echo "AI Video Generator Bot - Docker Test"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check if services are running
echo "Test 1: Checking if services are running..."
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✓ Services are running${NC}"
else
    echo -e "${RED}✗ Services are not running${NC}"
    echo "Run: docker-compose up -d"
    exit 1
fi
echo ""

# Test 2: Check Redis health
echo "Test 2: Checking Redis connection..."
if docker exec ai-video-bot-redis redis-cli ping | grep -q "PONG"; then
    echo -e "${GREEN}✓ Redis is healthy${NC}"
else
    echo -e "${RED}✗ Redis is not responding${NC}"
    exit 1
fi
echo ""

# Test 3: Check web service health endpoint
echo "Test 3: Checking web service health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:5000/health)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Web service is healthy${NC}"
    echo "Response: $HEALTH_RESPONSE"
else
    echo -e "${RED}✗ Web service health check failed${NC}"
    echo "Response: $HEALTH_RESPONSE"
    exit 1
fi
echo ""

# Test 4: Check root endpoint
echo "Test 4: Checking root endpoint..."
ROOT_RESPONSE=$(curl -s http://localhost:5000/)
if echo "$ROOT_RESPONSE" | grep -q "AI Video Generator Bot"; then
    echo -e "${GREEN}✓ Root endpoint is working${NC}"
else
    echo -e "${RED}✗ Root endpoint failed${NC}"
    exit 1
fi
echo ""

# Test 5: Check Celery worker
echo "Test 5: Checking Celery worker..."
WORKER_LOGS=$(docker-compose logs worker | tail -20)
if echo "$WORKER_LOGS" | grep -q "celery@.*ready"; then
    echo -e "${GREEN}✓ Celery worker is ready${NC}"
else
    echo -e "${YELLOW}⚠ Celery worker may not be ready yet${NC}"
    echo "Check logs: docker-compose logs worker"
fi
echo ""

# Test 6: Check FFmpeg in web container
echo "Test 6: Checking FFmpeg availability..."
if docker exec ai-video-bot-web test -f /app/bin/ffmpeg/ffmpeg; then
    FFMPEG_VERSION=$(docker exec ai-video-bot-web /app/bin/ffmpeg/ffmpeg -version | head -n 1)
    echo -e "${GREEN}✓ FFmpeg is available${NC}"
    echo "Version: $FFMPEG_VERSION"
else
    echo -e "${RED}✗ FFmpeg not found in container${NC}"
    echo "Make sure to download FFmpeg binaries before building:"
    echo "cd bin/ffmpeg && bash download_ffmpeg.sh"
    exit 1
fi
echo ""

# Test 7: Check environment variables
echo "Test 7: Checking critical environment variables..."
ENV_CHECK=$(docker exec ai-video-bot-web python -c "
from app.config import Config
import sys

missing = []
if not Config.TELEGRAM_BOT_TOKEN:
    missing.append('TELEGRAM_BOT_TOKEN')
if not Config.OPENAI_API_KEY:
    missing.append('OPENAI_API_KEY')
if not Config.OPENAI_ASSISTANT_ID:
    missing.append('OPENAI_ASSISTANT_ID')
if not Config.RUNWAY_API_KEY:
    missing.append('RUNWAY_API_KEY')

if missing:
    print('MISSING:' + ','.join(missing))
    sys.exit(1)
else:
    print('OK')
    sys.exit(0)
" 2>&1)

if echo "$ENV_CHECK" | grep -q "OK"; then
    echo -e "${GREEN}✓ All required environment variables are set${NC}"
elif echo "$ENV_CHECK" | grep -q "MISSING:"; then
    MISSING_VARS=$(echo "$ENV_CHECK" | grep "MISSING:" | cut -d: -f2)
    echo -e "${YELLOW}⚠ Missing environment variables: $MISSING_VARS${NC}"
    echo "Update your .env file with these values"
else
    echo -e "${YELLOW}⚠ Could not verify environment variables${NC}"
    echo "Error: $ENV_CHECK"
fi
echo ""

# Test 8: Check temp directory
echo "Test 8: Checking temp directory..."
if docker exec ai-video-bot-web test -d /app/temp; then
    echo -e "${GREEN}✓ Temp directory exists${NC}"
else
    echo -e "${RED}✗ Temp directory not found${NC}"
    exit 1
fi
echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "${GREEN}✓ Docker setup is working correctly!${NC}"
echo ""
echo "Next steps:"
echo "1. Ensure all API keys are set in .env file"
echo "2. For Telegram testing, set up ngrok:"
echo "   ngrok http 5000"
echo "3. Update TELEGRAM_WEBHOOK_URL in .env with ngrok URL"
echo "4. Restart web service: docker-compose restart web"
echo "5. Set webhook: curl -X POST \"https://api.telegram.org/bot<TOKEN>/setWebhook\" -d '{\"url\":\"<NGROK_URL>/webhook\"}'"
echo "6. Send a message to your bot!"
echo ""
echo "Monitor logs: docker-compose logs -f"
echo "=========================================="
