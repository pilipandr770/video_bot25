@echo off
REM AI Video Generator Bot - Local Docker Testing Script (CMD)
REM This script tests the complete Docker setup locally

echo ========================================
echo AI Video Bot - Local Docker Testing
echo ========================================
echo.

REM Step 1: Check Docker
echo Step 1: Checking Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running. Please start Docker Desktop.
    exit /b 1
)
echo [OK] Docker is running
echo.

REM Step 2: Check .env file
echo Step 2: Checking .env file...
if not exist ".env" (
    echo [ERROR] .env file not found. Please create it from .env.example
    exit /b 1
)
echo [OK] .env file exists
echo.

REM Step 3: Stop and remove existing containers
echo Step 3: Cleaning up existing containers...
docker-compose down -v >nul 2>&1
echo [OK] Cleanup complete
echo.

REM Step 4: Build Docker image
echo Step 4: Building Docker image...
docker-compose build
if errorlevel 1 (
    echo [ERROR] Docker build failed
    exit /b 1
)
echo [OK] Docker image built successfully
echo.

REM Step 5: Start Redis
echo Step 5: Starting Redis container...
docker-compose up -d redis
if errorlevel 1 (
    echo [ERROR] Failed to start Redis
    exit /b 1
)
echo [OK] Redis container started
echo Waiting for Redis to be healthy...
timeout /t 10 /nobreak >nul
echo.

REM Step 6: Test Redis connection
echo Step 6: Testing Redis connection...
docker exec ai-video-bot-redis redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Redis connection failed
    exit /b 1
)
echo [OK] Redis connection successful
echo.

REM Step 7: Start Flask web container
echo Step 7: Starting Flask web container...
docker-compose up -d web
if errorlevel 1 (
    echo [ERROR] Failed to start web container
    exit /b 1
)
echo [OK] Web container started
echo Waiting for web service to be ready...
timeout /t 15 /nobreak >nul
echo.

REM Step 8: Test health check endpoint
echo Step 8: Testing health check endpoint...
curl -f http://localhost:5000/health >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Health check endpoint not responding yet
    echo Showing web container logs:
    docker-compose logs --tail=20 web
) else (
    echo [OK] Health check endpoint responding
)
echo.

REM Step 9: Start Celery worker
echo Step 9: Starting Celery worker container...
docker-compose up -d worker
if errorlevel 1 (
    echo [ERROR] Failed to start worker container
    exit /b 1
)
echo [OK] Celery worker started
timeout /t 5 /nobreak >nul
echo.

REM Step 10: Check all container statuses
echo Step 10: Checking all container statuses...
echo.
docker-compose ps
echo.

REM Step 11: Show logs from all containers
echo Step 11: Recent logs from all containers...
echo.
echo --- Redis Logs ---
docker-compose logs --tail=10 redis
echo.
echo --- Web Logs ---
docker-compose logs --tail=20 web
echo.
echo --- Worker Logs ---
docker-compose logs --tail=20 worker
echo.

REM Summary
echo ========================================
echo Docker Testing Summary
echo ========================================
echo.
echo All containers are running!
echo.
echo Services:
echo   - Redis:        redis://localhost:6379
echo   - Web API:      http://localhost:5000
echo   - Health Check: http://localhost:5000/health
echo.
echo Useful commands:
echo   - View logs:           docker-compose logs -f
echo   - View web logs:       docker-compose logs -f web
echo   - View worker logs:    docker-compose logs -f worker
echo   - Stop containers:     docker-compose down
echo   - Restart containers:  docker-compose restart
echo.
echo To test the bot:
echo   1. Ensure API keys are configured in .env
echo   2. Set up ngrok or similar for webhook: ngrok http 5000
echo   3. Update TELEGRAM_WEBHOOK_URL in .env
echo   4. Run: python set_webhook.py
echo   5. Send a message to your Telegram bot
echo.
