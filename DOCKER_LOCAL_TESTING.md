# Docker Local Testing Guide

This guide explains how to test the AI Video Generator Bot locally using Docker.

## Prerequisites

1. **Docker Desktop** installed and running
   - Windows: [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
   - Mac: [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
   - Linux: [Docker Engine](https://docs.docker.com/engine/install/)

2. **Docker Compose** (included with Docker Desktop)

3. **Environment Variables** configured in `.env` file
   - Copy `.env.example` to `.env`
   - Fill in your API keys (see below)

## Quick Start

### Windows (PowerShell)

```powershell
.\test_docker_local.ps1
```

### Linux/Mac (Bash)

```bash
chmod +x test_docker_local.sh
./test_docker_local.sh
```

## What the Test Script Does

The test script performs the following steps:

1. ✅ **Checks Docker** - Verifies Docker is running
2. ✅ **Cleans up** - Removes existing containers and volumes
3. ✅ **Builds images** - Builds the application Docker image
4. ✅ **Starts Redis** - Launches Redis container and waits for health check
5. ✅ **Starts Web** - Launches Flask web application and waits for health check
6. ✅ **Starts Worker** - Launches Celery worker container
7. ✅ **Tests Health** - Verifies the `/health` endpoint responds
8. ✅ **Tests Redis** - Verifies Redis connection works
9. ✅ **Shows Logs** - Displays recent logs from all containers
10. ✅ **Checks Config** - Verifies API keys are configured

## Manual Testing Steps

If you prefer to test manually, follow these steps:

### 1. Start All Services

```bash
docker-compose up -d
```

### 2. Check Container Status

```bash
docker-compose ps
```

Expected output:
```
NAME                    STATUS              PORTS
ai-video-bot-redis      Up (healthy)        0.0.0.0:6379->6379/tcp
ai-video-bot-web        Up (healthy)        0.0.0.0:5000->5000/tcp
ai-video-bot-worker     Up                  
```

### 3. Test Health Endpoint

```bash
curl http://localhost:5000/health
```

Expected response:
```json
{"status": "healthy", "redis": "connected", "timestamp": "2024-..."}
```

### 4. Test Redis Connection

```bash
docker exec ai-video-bot-redis redis-cli ping
```

Expected response:
```
PONG
```

### 5. View Logs

View all logs:
```bash
docker-compose logs -f
```

View specific service logs:
```bash
docker-compose logs -f web
docker-compose logs -f worker
docker-compose logs -f redis
```

### 6. Access Container Shell

```bash
# Web container
docker exec -it ai-video-bot-web bash

# Worker container
docker exec -it ai-video-bot-worker bash

# Redis container
docker exec -it ai-video-bot-redis sh
```

## Testing with API Keys

To test full functionality, you need to configure API keys in `.env`:

### Required API Keys

1. **Telegram Bot Token**
   - Get from [@BotFather](https://t.me/BotFather)
   - Format: `TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

2. **OpenAI API Key**
   - Get from [OpenAI Platform](https://platform.openai.com/api-keys)
   - Format: `OPENAI_API_KEY=sk-proj-...`

3. **OpenAI Assistant IDs** (3 assistants)
   - Create at [OpenAI Assistants](https://platform.openai.com/assistants)
   - See `ASSISTANT_SETUP_GUIDE.md` for instructions
   - Format: `OPENAI_SCRIPT_ASSISTANT_ID=asst_...`

4. **Runway API Key**
   - Get from [Runway](https://runwayml.com)
   - Format: `RUNWAY_API_KEY=key_...`

### Testing Without API Keys

You can still test the infrastructure without API keys:

- ✅ Container startup and health checks
- ✅ Redis connectivity
- ✅ Web server responds
- ✅ Celery worker starts
- ❌ Cannot test video generation pipeline
- ❌ Cannot test Telegram bot integration

## Common Issues and Solutions

### Issue: Docker is not running

**Error:**
```
Cannot connect to the Docker daemon
```

**Solution:**
- Start Docker Desktop
- Wait for Docker to fully initialize
- Run the test script again

### Issue: Port already in use

**Error:**
```
Bind for 0.0.0.0:5000 failed: port is already allocated
```

**Solution:**
```bash
# Stop existing containers
docker-compose down

# Or change ports in docker-compose.yml
```

### Issue: Health check fails

**Error:**
```
✗ Web service health check failed
```

**Solution:**
```bash
# Check logs for errors
docker-compose logs web

# Common causes:
# - Missing dependencies
# - Configuration errors
# - Port conflicts
```

### Issue: Redis connection fails

**Error:**
```
✗ Redis connection failed
```

**Solution:**
```bash
# Check Redis logs
docker-compose logs redis

# Restart Redis
docker-compose restart redis

# Verify Redis is healthy
docker inspect ai-video-bot-redis | grep Health
```

### Issue: Worker not processing tasks

**Solution:**
```bash
# Check worker logs
docker-compose logs worker

# Verify Redis connection
docker exec ai-video-bot-worker python -c "import redis; r=redis.from_url('redis://redis:6379/0'); print(r.ping())"

# Restart worker
docker-compose restart worker
```

## Architecture Overview

```
┌─────────────────────────────────────────┐
│         Docker Compose Network          │
│                                         │
│  ┌──────────────┐                      │
│  │    Redis     │                      │
│  │   (Port 6379)│◄─────────┐          │
│  └──────────────┘          │          │
│                            │          │
│  ┌──────────────┐          │          │
│  │  Flask Web   │          │          │
│  │  (Port 5000) │──────────┤          │
│  └──────────────┘          │          │
│                            │          │
│  ┌──────────────┐          │          │
│  │Celery Worker │──────────┘          │
│  └──────────────┘                     │
│                                         │
└─────────────────────────────────────────┘
```

## Service Details

### Redis Service
- **Image:** redis:7-alpine
- **Port:** 6379
- **Purpose:** Message broker for Celery, approval state storage
- **Health Check:** `redis-cli ping`

### Web Service
- **Build:** Custom Dockerfile
- **Port:** 5000
- **Purpose:** Flask application, Telegram webhook endpoint
- **Health Check:** `curl http://localhost:5000/health`
- **Dependencies:** Redis

### Worker Service
- **Build:** Custom Dockerfile (same as web)
- **Command:** `celery -A app.tasks worker`
- **Purpose:** Asynchronous video generation tasks
- **Dependencies:** Redis

## Useful Commands

### Container Management

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart a service
docker-compose restart web

# Rebuild and restart
docker-compose up -d --build

# Remove all containers and volumes
docker-compose down -v
```

### Monitoring

```bash
# View container status
docker-compose ps

# View resource usage
docker stats

# Follow logs in real-time
docker-compose logs -f

# View last 50 lines of logs
docker-compose logs --tail=50
```

### Debugging

```bash
# Execute command in container
docker exec ai-video-bot-web python --version

# Access Python shell
docker exec -it ai-video-bot-web python

# Check environment variables
docker exec ai-video-bot-web env

# Test Redis from web container
docker exec ai-video-bot-web python -c "import redis; r=redis.from_url('redis://redis:6379/0'); print(r.ping())"

# Test FFmpeg
docker exec ai-video-bot-web ffmpeg -version
```

### Cleanup

```bash
# Remove stopped containers
docker-compose rm

# Remove unused images
docker image prune

# Remove all unused resources
docker system prune -a

# Remove volumes
docker volume prune
```

## Next Steps

After successful local testing:

1. ✅ Verify all containers are healthy
2. ✅ Test health endpoint responds
3. ✅ Verify Redis connectivity
4. ✅ Check logs for errors
5. 📝 Configure API keys for full testing
6. 🚀 Deploy to Render.com (see `RENDER_DEPLOYMENT.md`)

## Troubleshooting Checklist

- [ ] Docker Desktop is running
- [ ] No port conflicts (5000, 6379)
- [ ] `.env` file exists and is configured
- [ ] All containers show "Up" status
- [ ] Health checks pass (web and redis)
- [ ] No errors in logs
- [ ] Redis responds to PING
- [ ] Health endpoint returns 200 OK

## Support

If you encounter issues:

1. Check the logs: `docker-compose logs`
2. Verify configuration: Check `.env` file
3. Review this guide for common issues
4. Check Docker Desktop status
5. Restart Docker Desktop if needed

## Performance Notes

### Resource Usage

- **Redis:** ~10-20 MB RAM
- **Web:** ~100-200 MB RAM
- **Worker:** ~100-200 MB RAM
- **Total:** ~300-500 MB RAM

### Disk Space

- **Images:** ~500 MB
- **Temp files:** Varies (cleaned up automatically)
- **Logs:** Grows over time (rotate regularly)

### Optimization Tips

1. Limit worker concurrency: `--concurrency=2`
2. Set Redis max memory: `--maxmemory 256mb`
3. Clean up old containers: `docker system prune`
4. Monitor disk usage: `docker system df`

## Security Notes

- Never commit `.env` file to version control
- Keep API keys secure
- Use environment variables for sensitive data
- Regularly update Docker images
- Monitor container logs for suspicious activity

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Redis Documentation](https://redis.io/documentation)
