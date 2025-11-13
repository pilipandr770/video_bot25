# Docker Local Testing Guide

This guide provides comprehensive instructions for testing the AI Video Generator Bot locally using Docker.

## Prerequisites

1. **Docker Desktop** installed and running
   - Download from: https://www.docker.com/products/docker-desktop
   - Ensure Docker daemon is running

2. **Environment Configuration**
   - Copy `.env.example` to `.env`
   - Fill in your API keys (see Configuration section below)

3. **System Requirements**
   - At least 4GB RAM available for Docker
   - 10GB free disk space
   - Windows 10/11 with WSL2 (for Windows users)

## Quick Start

### Option 1: PowerShell (Recommended for Windows)

```powershell
# Run the comprehensive test script
.\test_docker_local.ps1
```

### Option 2: CMD

```cmd
# Run the CMD test script
test_docker_local.cmd
```

### Option 3: Manual Docker Compose

```bash
# Build and start all services
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## Configuration

### Required Environment Variables

Edit your `.env` file with the following:

```env
# Telegram Bot (Required for full testing)
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather

# OpenAI (Required for AI features)
OPENAI_API_KEY=your_openai_api_key
OPENAI_SCRIPT_ASSISTANT_ID=asst_xxx
OPENAI_SEGMENT_ASSISTANT_ID=asst_xxx
OPENAI_ANIMATION_ASSISTANT_ID=asst_xxx

# Runway (Required for video generation)
RUNWAY_API_KEY=your_runway_api_key

# Redis (Auto-configured for Docker)
REDIS_URL=redis://redis:6379/0
```

### Optional Configuration

```env
# Logging
LOG_LEVEL=DEBUG  # Use DEBUG for local testing

# Application Settings
MAX_CONCURRENT_JOBS=5
FILE_CLEANUP_HOURS=1
TEMP_DIR=/app/temp
```

## Testing Steps

### 1. Build Docker Images

```powershell
docker-compose build
```

**Expected Output:**
- Successful build of Python 3.11 image
- Installation of all dependencies from requirements.txt
- FFmpeg installation via apt-get

**Troubleshooting:**
- If build fails, check your internet connection
- Ensure Docker has enough disk space
- Check `docker-compose.yml` syntax

### 2. Start Redis Container

```powershell
docker-compose up -d redis
```

**Verification:**
```powershell
# Check Redis is running
docker exec ai-video-bot-redis redis-cli ping
# Expected output: PONG

# Check Redis health
docker inspect --format='{{.State.Health.Status}}' ai-video-bot-redis
# Expected output: healthy
```

**Troubleshooting:**
- If Redis fails to start, check port 6379 is not in use
- View logs: `docker-compose logs redis`

### 3. Start Web Container

```powershell
docker-compose up -d web
```

**Verification:**
```powershell
# Check health endpoint
curl http://localhost:5000/health

# Expected response:
# {"status": "healthy", "redis": "connected", "timestamp": "..."}
```

**Troubleshooting:**
- If web fails to start, check logs: `docker-compose logs web`
- Common issues:
  - Port 5000 already in use
  - Missing environment variables
  - Redis connection failed

### 4. Start Worker Container

```powershell
docker-compose up -d worker
```

**Verification:**
```powershell
# Check worker logs for Celery startup
docker-compose logs worker

# Expected output should include:
# - celery@hostname ready
# - Connected to redis://redis:6379/0
```

**Troubleshooting:**
- Check worker logs: `docker-compose logs worker`
- Verify Redis connection
- Ensure all environment variables are set

### 5. Check All Container Statuses

```powershell
docker-compose ps
```

**Expected Output:**
```
NAME                    STATUS              PORTS
ai-video-bot-redis      Up (healthy)        0.0.0.0:6379->6379/tcp
ai-video-bot-web        Up (healthy)        0.0.0.0:5000->5000/tcp
ai-video-bot-worker     Up                  
```

### 6. Test Health Check Endpoint

```powershell
# PowerShell
Invoke-WebRequest -Uri "http://localhost:5000/health" -UseBasicParsing

# Or using curl
curl http://localhost:5000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "redis": "connected",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 7. Test Redis Connection

```powershell
# Test Redis from web container
docker exec ai-video-bot-web python -c "import redis; r = redis.from_url('redis://redis:6379/0'); print(r.ping())"

# Expected output: True
```

### 8. View Container Logs

```powershell
# All containers
docker-compose logs -f

# Specific container
docker-compose logs -f web
docker-compose logs -f worker
docker-compose logs -f redis

# Last 50 lines
docker-compose logs --tail=50 web
```

### 9. Test Basic Functionality

If you have API keys configured, you can test the bot:

#### Setup Webhook (for local testing with ngrok)

1. Install ngrok: https://ngrok.com/download
2. Start ngrok tunnel:
   ```bash
   ngrok http 5000
   ```
3. Update `.env` with ngrok URL:
   ```env
   TELEGRAM_WEBHOOK_URL=https://your-ngrok-id.ngrok.io
   ```
4. Restart web container:
   ```powershell
   docker-compose restart web
   ```
5. Set webhook:
   ```powershell
   python set_webhook.py
   ```

#### Test Bot

1. Open Telegram and find your bot
2. Send `/start` command
3. Send a text message with video description
4. Monitor logs:
   ```powershell
   docker-compose logs -f web worker
   ```

## Common Issues and Solutions

### Issue: Port Already in Use

**Error:** `Bind for 0.0.0.0:5000 failed: port is already allocated`

**Solution:**
```powershell
# Find process using port 5000
netstat -ano | findstr :5000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or change port in docker-compose.yml
ports:
  - "5001:5000"  # Use port 5001 instead
```

### Issue: Redis Connection Failed

**Error:** `redis.exceptions.ConnectionError: Error connecting to Redis`

**Solution:**
```powershell
# Check Redis is running
docker-compose ps redis

# Restart Redis
docker-compose restart redis

# Check Redis logs
docker-compose logs redis
```

### Issue: Worker Not Processing Tasks

**Symptoms:** Tasks stuck in pending state

**Solution:**
```powershell
# Check worker logs
docker-compose logs worker

# Restart worker
docker-compose restart worker

# Verify Redis connection from worker
docker exec ai-video-bot-worker python -c "import redis; r = redis.from_url('redis://redis:6379/0'); print(r.ping())"
```

### Issue: Health Check Failing

**Error:** Web container shows unhealthy status

**Solution:**
```powershell
# Check web logs
docker-compose logs web

# Test health endpoint manually
curl http://localhost:5000/health

# Restart web container
docker-compose restart web
```

### Issue: FFmpeg Not Found

**Error:** `FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'`

**Solution:**
- FFmpeg is installed via apt-get in Dockerfile
- Verify installation:
  ```powershell
  docker exec ai-video-bot-web which ffmpeg
  docker exec ai-video-bot-web ffmpeg -version
  ```

## Useful Commands

### Container Management

```powershell
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart web

# Rebuild and restart
docker-compose up -d --build

# Remove all containers and volumes
docker-compose down -v
```

### Logs and Debugging

```powershell
# Follow logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Logs since timestamp
docker-compose logs --since 2024-01-15T10:00:00

# Export logs to file
docker-compose logs > docker-logs.txt
```

### Container Inspection

```powershell
# Execute command in container
docker exec -it ai-video-bot-web bash

# Check container stats
docker stats

# Inspect container
docker inspect ai-video-bot-web

# Check container health
docker inspect --format='{{.State.Health.Status}}' ai-video-bot-web
```

### Cleanup

```powershell
# Remove stopped containers
docker-compose rm

# Remove unused images
docker image prune

# Remove all unused resources
docker system prune -a

# Remove volumes
docker volume prune
```

## Performance Testing

### Test Redis Performance

```powershell
docker exec ai-video-bot-redis redis-benchmark -q -n 1000
```

### Test Web Performance

```powershell
# Using Apache Bench (if installed)
ab -n 100 -c 10 http://localhost:5000/health

# Using PowerShell
1..100 | ForEach-Object {
    Measure-Command { Invoke-WebRequest -Uri "http://localhost:5000/health" -UseBasicParsing }
} | Measure-Object -Property TotalMilliseconds -Average
```

### Monitor Resource Usage

```powershell
# Real-time stats
docker stats

# Container resource limits
docker inspect ai-video-bot-web | Select-String -Pattern "Memory|Cpu"
```

## Integration Testing

### Test Celery Task Queue

```powershell
# Enter web container
docker exec -it ai-video-bot-web python

# In Python shell:
from app.tasks import celery_app
from app.tasks.video_generation import generate_video_task

# Send test task
result = generate_video_task.delay(
    job_id="test-123",
    user_id=12345,
    chat_id=12345,
    prompt="Test video about technology"
)

# Check task status
print(result.status)
```

### Test OpenAI Integration

```powershell
docker exec -it ai-video-bot-web python -c "
from app.services.openai_service import OpenAIService
import os

service = OpenAIService(
    api_key=os.getenv('OPENAI_API_KEY'),
    script_assistant_id=os.getenv('OPENAI_SCRIPT_ASSISTANT_ID'),
    segment_assistant_id=os.getenv('OPENAI_SEGMENT_ASSISTANT_ID'),
    animation_assistant_id=os.getenv('OPENAI_ANIMATION_ASSISTANT_ID')
)

# Test script generation
script = service.generate_script('Create a 50-second ad about smartphones')
print('Script generated:', len(script), 'characters')
"
```

## Continuous Testing

### Watch Mode

```powershell
# Watch logs continuously
docker-compose logs -f

# Watch specific service
docker-compose logs -f web

# Watch with grep filter
docker-compose logs -f | Select-String "ERROR"
```

### Automated Health Checks

Create a scheduled task to run health checks:

```powershell
# health_check_loop.ps1
while ($true) {
    Write-Host "$(Get-Date) - Running health check..."
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000/health" -UseBasicParsing -TimeoutSec 5
        Write-Host "✓ Health check passed" -ForegroundColor Green
    } catch {
        Write-Host "✗ Health check failed" -ForegroundColor Red
        docker-compose logs --tail=20 web
    }
    
    Start-Sleep -Seconds 30
}
```

## Next Steps

After successful local testing:

1. **Configure API Keys**: Add real API keys to `.env`
2. **Test Full Pipeline**: Send test messages through Telegram bot
3. **Monitor Performance**: Check resource usage and response times
4. **Deploy to Render**: Use `render.yaml` for production deployment
5. **Set Up Monitoring**: Configure logging and alerting

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Redis Documentation](https://redis.io/documentation)
- [Project README](./README.md)
- [Deployment Guide](./DEPLOYMENT_CHECKLIST.md)
