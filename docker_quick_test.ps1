# Quick Docker Test - Minimal validation
# Use this for quick checks after making changes

Write-Host "Quick Docker Test" -ForegroundColor Cyan
Write-Host "=================" -ForegroundColor Cyan
Write-Host ""

# Check if containers are running
Write-Host "Checking container status..." -ForegroundColor Yellow
$containers = docker-compose ps --services --filter "status=running" 2>$null

if ($containers -match "redis" -and $containers -match "web" -and $containers -match "worker") {
    Write-Host "✓ All containers running" -ForegroundColor Green
} else {
    Write-Host "✗ Some containers are not running" -ForegroundColor Red
    docker-compose ps
    exit 1
}

# Quick health checks
Write-Host ""
Write-Host "Running health checks..." -ForegroundColor Yellow

# Redis
$redisTest = docker exec ai-video-bot-redis redis-cli ping 2>$null
if ($redisTest -eq "PONG") {
    Write-Host "✓ Redis: OK" -ForegroundColor Green
} else {
    Write-Host "✗ Redis: FAILED" -ForegroundColor Red
}

# Web
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/health" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Web: OK" -ForegroundColor Green
    } else {
        Write-Host "✗ Web: FAILED (Status: $($response.StatusCode))" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Web: FAILED (Not responding)" -ForegroundColor Red
}

# Worker (check if process is running)
$workerCheck = docker exec ai-video-bot-worker ps aux 2>$null | Select-String "celery"
if ($workerCheck) {
    Write-Host "✓ Worker: OK" -ForegroundColor Green
} else {
    Write-Host "✗ Worker: FAILED" -ForegroundColor Red
}

Write-Host ""
Write-Host "Quick test complete!" -ForegroundColor Cyan
