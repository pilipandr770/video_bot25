# Docker Services Monitor
# Continuously monitors the health of all Docker services

param(
    [int]$IntervalSeconds = 30,
    [switch]$ShowLogs = $false
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Docker Services Monitor" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Monitoring interval: $IntervalSeconds seconds" -ForegroundColor Gray
Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Gray
Write-Host ""

function Get-ServiceStatus {
    param([string]$ContainerName)
    
    try {
        $status = docker inspect --format='{{.State.Status}}' $ContainerName 2>$null
        $health = docker inspect --format='{{.State.Health.Status}}' $ContainerName 2>$null
        
        if ($status -eq "running") {
            if ($health -and $health -ne "<no value>") {
                return @{
                    Status = $status
                    Health = $health
                    Icon = if ($health -eq "healthy") { "✓" } else { "⚠" }
                    Color = if ($health -eq "healthy") { "Green" } else { "Yellow" }
                }
            } else {
                return @{
                    Status = $status
                    Health = "N/A"
                    Icon = "✓"
                    Color = "Green"
                }
            }
        } else {
            return @{
                Status = $status
                Health = "N/A"
                Icon = "✗"
                Color = "Red"
            }
        }
    } catch {
        return @{
            Status = "unknown"
            Health = "N/A"
            Icon = "?"
            Color = "Gray"
        }
    }
}

function Test-Endpoint {
    param([string]$Url)
    
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
        return @{
            Success = $true
            StatusCode = $response.StatusCode
            Icon = "✓"
            Color = "Green"
        }
    } catch {
        return @{
            Success = $false
            StatusCode = "N/A"
            Icon = "✗"
            Color = "Red"
        }
    }
}

function Test-RedisConnection {
    try {
        $result = docker exec ai-video-bot-redis redis-cli ping 2>$null
        return @{
            Success = ($result -eq "PONG")
            Icon = if ($result -eq "PONG") { "✓" } else { "✗" }
            Color = if ($result -eq "PONG") { "Green" } else { "Red" }
        }
    } catch {
        return @{
            Success = $false
            Icon = "✗"
            Color = "Red"
        }
    }
}

$iteration = 0

while ($true) {
    $iteration++
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    Clear-Host
    
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Docker Services Monitor - Check #$iteration" -ForegroundColor Cyan
    Write-Host "Time: $timestamp" -ForegroundColor Gray
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Check container statuses
    Write-Host "Container Status:" -ForegroundColor Yellow
    Write-Host ""
    
    $redis = Get-ServiceStatus "ai-video-bot-redis"
    Write-Host "  $($redis.Icon) Redis:  " -NoNewline -ForegroundColor $redis.Color
    Write-Host "$($redis.Status) / $($redis.Health)" -ForegroundColor Gray
    
    $web = Get-ServiceStatus "ai-video-bot-web"
    Write-Host "  $($web.Icon) Web:    " -NoNewline -ForegroundColor $web.Color
    Write-Host "$($web.Status) / $($web.Health)" -ForegroundColor Gray
    
    $worker = Get-ServiceStatus "ai-video-bot-worker"
    Write-Host "  $($worker.Icon) Worker: " -NoNewline -ForegroundColor $worker.Color
    Write-Host "$($worker.Status) / $($worker.Health)" -ForegroundColor Gray
    
    Write-Host ""
    
    # Check connectivity
    Write-Host "Connectivity Tests:" -ForegroundColor Yellow
    Write-Host ""
    
    $redisConn = Test-RedisConnection
    Write-Host "  $($redisConn.Icon) Redis Connection:  " -NoNewline -ForegroundColor $redisConn.Color
    Write-Host $(if ($redisConn.Success) { "OK" } else { "FAILED" }) -ForegroundColor Gray
    
    $healthCheck = Test-Endpoint "http://localhost:5000/health"
    Write-Host "  $($healthCheck.Icon) Health Endpoint:   " -NoNewline -ForegroundColor $healthCheck.Color
    Write-Host $(if ($healthCheck.Success) { "OK (Status: $($healthCheck.StatusCode))" } else { "FAILED" }) -ForegroundColor Gray
    
    Write-Host ""
    
    # Overall status
    $allHealthy = $redis.Status -eq "running" -and 
                  $web.Status -eq "running" -and 
                  $worker.Status -eq "running" -and
                  $redisConn.Success -and
                  $healthCheck.Success
    
    if ($allHealthy) {
        Write-Host "Overall Status: " -NoNewline
        Write-Host "✓ ALL SYSTEMS OPERATIONAL" -ForegroundColor Green
    } else {
        Write-Host "Overall Status: " -NoNewline
        Write-Host "⚠ ISSUES DETECTED" -ForegroundColor Yellow
    }
    
    Write-Host ""
    
    # Show recent logs if requested
    if ($ShowLogs) {
        Write-Host "Recent Logs (last 5 lines):" -ForegroundColor Yellow
        Write-Host ""
        
        Write-Host "--- Web ---" -ForegroundColor Gray
        docker-compose logs --tail=5 web 2>$null | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
        
        Write-Host ""
        Write-Host "--- Worker ---" -ForegroundColor Gray
        docker-compose logs --tail=5 worker 2>$null | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
        
        Write-Host ""
    }
    
    Write-Host "Next check in $IntervalSeconds seconds... (Press Ctrl+C to stop)" -ForegroundColor Gray
    
    Start-Sleep -Seconds $IntervalSeconds
}
