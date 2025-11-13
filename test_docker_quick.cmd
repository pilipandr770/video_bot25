@echo off
REM AI Video Generator Bot - Quick Docker Testing Script

echo ========================================
echo AI Video Bot - Docker Testing
echo ========================================
echo.

echo [1/8] Checking Docker...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo X Docker is not running
    exit /b 1
)
echo √ Docker is running
echo.

echo [2/8] Cleaning up existing containers...
docker-compose down -v >nul 2>&1
echo √ Cleanup complete
echo.

echo [3/8] Building Docker images...
docker-compose build
if %errorlevel% neq 0 (
    echo X Docker build failed
    exit /b 1
)
echo √ Docker images built
echo.

echo [4/8] Starting Redis...
docker-compose up -d redis
timeout /t 10 /nobreak >nul
echo √ Redis started
echo.

echo [5/8] Starting Web service...
docker-compose up -d web
timeout /t 15 /nobreak >nul
echo √ Web service started
echo.

echo [6/8] Starting Worker...
docker-compose up -d worker
timeout /t 5 /nobreak >nul
echo √ Worker started
echo.

echo [7/8] Testing health endpoint...
curl -s http://localhost:5000/health
echo.
echo.

echo [8/8] Testing Redis...
docker exec ai-video-bot-redis redis-cli ping
echo.

echo ========================================
echo Container Status
echo ========================================
docker-compose ps
echo.

echo ========================================
echo Testing Complete!
echo ========================================
echo.
echo Services running at:
echo   - Web:    http://localhost:5000
echo   - Redis:  localhost:6379
echo.
echo Useful commands:
echo   - View logs:     docker-compose logs -f
echo   - Stop services: docker-compose down
echo.
