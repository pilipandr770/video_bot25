# AI Video Generator Bot - Local Docker Testing Script (PowerShell)
# This script tests the complete Docker setup locally

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AI Video Bot - Local Docker Testing" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if Docker is running
function Test-DockerRunning {
    try {
        docker info | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Function to wait for service health
function Wait-ForHealthy {
    param(
        [string]$ServiceName,
        [int]$MaxAttempts = 30
    )
    
    Write-Host "Waiting for $ServiceName to be healthy..." -ForegroundColor Yellow
    
    for ($i = 1; $i -le $MaxAttempts; $i++) {
        $health = docker inspect --format='{{.State.Health.Status}}' $ServiceName 2>$null
        
        if ($health -eq "healthy") {
            Write-Host "✓ $ServiceName is healthy!" -ForegroundColor Green
            return $true
        }
        
        Write-Host "  Attempt $i/$MaxAttempts - Status: $health" -ForegroundColor Gray
        Start-Sleep -Seconds 2
    }
    
    Write-Host "✗ $ServiceName failed to become healthy" -ForegroundColor Red
    return $false
}

# Step 1: Check Docker
Write-Host "Step 1: Checking Docker..." -ForegroundColor Cyan
if (-not (Test-DockerRunning)) {
    Write-Host "✗ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}
Write-Host "✓ Docker is running" -ForegroundColor Green
Write-Host ""

# Step 2: Check .env file
Write-Host "Step 2: Checking .env file..." -ForegroundColor Cyan
if (-not (Test-Path ".env")) {
    Write-Host "✗ .env file not found. Please create it from .env.example" -ForegroundColor Red
    exit 1
}
Write-Host "✓ .env file exists" -ForegroundColor Green
Write-Host ""

# Step 3: Stop and remove existing containers
Write-Host "Step 3: Cleaning up existing containers..." -ForegroundColor Cyan
docker-compose down -v 2>$null
Write-Host "✓ Cleanup complete" -ForegroundColor Green
Write-Host ""

# Step 4: Build Docker image
Write-Host "Step 4: Building Docker image..." -ForegroundColor Cyan
docker-compose build
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Docker build failed" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Docker image built successfully" -ForegroundColor Green
Write-Host ""

# Step 5: Start Redis
Write-Host "Step 5: Starting Redis container..." -ForegroundColor Cyan
docker-compose up -d redis
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to start Redis" -ForegroundColor Red
    exit 1
}

if (-not (Wait-ForHealthy "ai-video-bot-redis")) {
    Write-Host "✗ Redis health check failed" -ForegroundColor Red
    docker-compose logs redis
    exit 1
}
Write-Host ""

# Step 6: Test Redis connection
Write-Host "Step 6: Testing Redis connection..." -ForegroundColor Cyan
$redisTest = docker exec ai-video-bot-redis redis-cli ping 2>$null
if ($redisTest -eq "PONG") {
    Write-Host "✓ Redis connection successful" -ForegroundColor Green
} else {
    Write-Host "✗ Redis connection failed" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 7: Start Flask web container
Write-Host "Step 7: Starting Flask web container..." -ForegroundColor Cyan
docker-compose up -d web
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to start web container" -ForegroundColor Red
    exit 1
}

if (-not (Wait-ForHealthy "ai-video-bot-web")) {
    Write-Host "✗ Web container health check failed" -ForegroundColor Red
    Write-Host "Showing web container logs:" -ForegroundColor Yellow
    docker-compose logs web
    exit 1
}
Write-Host ""

# Step 8: Test health check endpoint
Write-Host "Step 8: Testing health check endpoint..." -ForegroundColor Cyan
Start-Sleep -Seconds 3
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/health" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Health check endpoint responding" -ForegroundColor Green
        Write-Host "  Response: $($response.Content)" -ForegroundColor Gray
    } else {
        Write-Host "✗ Health check returned status: $($response.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Health check endpoint failed: $_" -ForegroundColor Red
    Write-Host "Showing web container logs:" -ForegroundColor Yellow
    docker-compose logs web
}
Write-Host ""

# Step 9: Start Celery worker
Write-Host "Step 9: Starting Celery worker container..." -ForegroundColor Cyan
docker-compose up -d worker
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to start worker container" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Celery worker started" -ForegroundColor Green
Start-Sleep -Seconds 5
Write-Host ""

# Step 10: Check all container statuses
Write-Host "Step 10: Checking all container statuses..." -ForegroundColor Cyan
Write-Host ""
docker-compose ps
Write-Host ""

# Step 11: Show logs from all containers
Write-Host "Step 11: Recent logs from all containers..." -ForegroundColor Cyan
Write-Host ""
Write-Host "--- Redis Logs ---" -ForegroundColor Yellow
docker-compose logs --tail=10 redis
Write-Host ""
Write-Host "--- Web Logs ---" -ForegroundColor Yellow
docker-compose logs --tail=20 web
Write-Host ""
Write-Host "--- Worker Logs ---" -ForegroundColor Yellow
docker-compose logs --tail=20 worker
Write-Host ""

# Step 12: Test basic functionality (if API keys are configured)
Write-Host "Step 12: Testing basic functionality..." -ForegroundColor Cyan
$envContent = Get-Content .env -Raw
if ($envContent -match "OPENAI_API_KEY=sk-" -and $envContent -match "TELEGRAM_BOT_TOKEN=\d+:") {
    Write-Host "✓ API keys appear to be configured" -ForegroundColor Green
    Write-Host "  You can now test the bot by sending messages to your Telegram bot" -ForegroundColor Gray
} else {
    Write-Host "⚠ API keys not fully configured in .env file" -ForegroundColor Yellow
    Write-Host "  Configure API keys to test full functionality" -ForegroundColor Gray
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Docker Testing Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "All containers are running!" -ForegroundColor Green
Write-Host ""
Write-Host "Services:" -ForegroundColor Cyan
Write-Host "  • Redis:        redis://localhost:6379" -ForegroundColor Gray
Write-Host "  • Web API:      http://localhost:5000" -ForegroundColor Gray
Write-Host "  • Health Check: http://localhost:5000/health" -ForegroundColor Gray
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Cyan
Write-Host "  • View logs:           docker-compose logs -f" -ForegroundColor Gray
Write-Host "  • View web logs:       docker-compose logs -f web" -ForegroundColor Gray
Write-Host "  • View worker logs:    docker-compose logs -f worker" -ForegroundColor Gray
Write-Host "  • Stop containers:     docker-compose down" -ForegroundColor Gray
Write-Host "  • Restart containers:  docker-compose restart" -ForegroundColor Gray
Write-Host ""
Write-Host "To test the bot:" -ForegroundColor Cyan
Write-Host "  1. Ensure API keys are configured in .env" -ForegroundColor Gray
Write-Host "  2. Set up ngrok or similar for webhook: ngrok http 5000" -ForegroundColor Gray
Write-Host "  3. Update TELEGRAM_WEBHOOK_URL in .env" -ForegroundColor Gray
Write-Host "  4. Run: python set_webhook.py" -ForegroundColor Gray
Write-Host "  5. Send a message to your Telegram bot" -ForegroundColor Gray
Write-Host ""
