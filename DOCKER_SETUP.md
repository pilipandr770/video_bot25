# Docker Setup Guide for Local Testing

This guide will help you set up and test the AI Video Generator Bot locally using Docker.

## Prerequisites

- Docker Desktop installed ([Download here](https://www.docker.com/products/docker-desktop))
- Docker Compose (included with Docker Desktop)
- Git (for cloning the repository)
- API keys for Telegram, OpenAI, and Runway

## Step 1: Download FFmpeg Binaries

Before building the Docker image, you need to download FFmpeg binaries:

```bash
# Navigate to the FFmpeg directory
cd bin/ffmpeg

# Run the download script (Linux/macOS)
bash download_ffmpeg.sh

# Or download manually
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar -xf ffmpeg-release-amd64-static.tar.xz
cp ffmpeg-*-amd64-static/ffmpeg .
cp ffmpeg-*-amd64-static/ffprobe .
chmod +x ffmpeg ffprobe
rm -rf ffmpeg-*-amd64-static*

# Return to project root
cd ../..
```

**For Windows users:**
- Download FFmpeg from https://www.gyan.dev/ffmpeg/builds/
- Extract and copy `ffmpeg.exe` and `ffprobe.exe` to `bin/ffmpeg/`

## Step 2: Configure Environment Variables

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and fill in your API keys:
```bash
# Required API keys
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
OPENAI_API_KEY=your_openai_api_key
OPENAI_ASSISTANT_ID=your_assistant_id
RUNWAY_API_KEY=your_runway_api_key

# For local testing, keep these as is
TELEGRAM_WEBHOOK_URL=http://localhost:5000
REDIS_URL=redis://redis:6379/0
LOG_LEVEL=DEBUG
```

### Getting API Keys

**Telegram Bot Token:**
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow instructions
3. Copy the token provided

**OpenAI API Key:**
1. Go to https://platform.openai.com/api-keys
2. Create a new secret key
3. Copy the key (starts with `sk-`)

**OpenAI Assistant ID:**
1. Go to https://platform.openai.com/assistants
2. Create a new assistant with instructions like:
   ```
   You are a professional video script writer. Generate engaging 4-minute video scripts
   for advertising based on user descriptions. Structure the script into clear segments
   that can be visualized. Focus on storytelling and visual descriptions.
   ```
3. Copy the Assistant ID (starts with `asst_`)

**Runway API Key:**
1. Sign up at https://runwayml.com
2. Navigate to API settings
3. Generate an API key

## Step 3: Build Docker Images

Build the Docker images for the application:

```bash
# Build all services
docker-compose build

# Or build with no cache (if you made changes)
docker-compose build --no-cache
```

This will:
- Create a Python 3.11 environment
- Install all dependencies from requirements.txt
- Copy application code and FFmpeg binaries
- Set up the temp directory

## Step 4: Start Services

Start all services (Redis, Web, Worker):

```bash
# Start in detached mode
docker-compose up -d

# Or start with logs visible
docker-compose up
```

This will start:
- **Redis**: Message broker and approval system storage
- **Web**: Flask application with webhook endpoint
- **Worker**: Celery worker for video generation tasks

## Step 5: Verify Services

Check that all services are running:

```bash
# Check service status
docker-compose ps

# Expected output:
# NAME                    STATUS              PORTS
# ai-video-bot-redis      Up (healthy)        0.0.0.0:6379->6379/tcp
# ai-video-bot-web        Up (healthy)        0.0.0.0:5000->5000/tcp
# ai-video-bot-worker     Up                  

# Check health endpoint
curl http://localhost:5000/health

# Expected response:
# {"status":"healthy","service":"ai-video-generator-bot"}
```

## Step 6: View Logs

Monitor logs from all services:

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f web
docker-compose logs -f worker
docker-compose logs -f redis

# View last 100 lines
docker-compose logs --tail=100 -f
```

## Step 7: Test with ngrok (Optional)

To test with real Telegram messages, you need a public URL. Use ngrok:

1. Install ngrok: https://ngrok.com/download

2. Start ngrok tunnel:
```bash
ngrok http 5000
```

3. Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

4. Update `.env`:
```bash
TELEGRAM_WEBHOOK_URL=https://abc123.ngrok.io
```

5. Restart web service:
```bash
docker-compose restart web
```

6. Set Telegram webhook:
```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://abc123.ngrok.io/webhook"}'
```

7. Send a message to your bot in Telegram!

## Step 8: Testing the Application

### Basic Health Check
```bash
# Test health endpoint
curl http://localhost:5000/health

# Test root endpoint
curl http://localhost:5000/
```

### Test Redis Connection
```bash
# Connect to Redis container
docker exec -it ai-video-bot-redis redis-cli

# Test Redis
127.0.0.1:6379> PING
PONG
127.0.0.1:6379> exit
```

### Test Celery Worker
```bash
# Check worker logs
docker-compose logs worker

# Should see:
# [tasks]
#   . app.tasks.generate_video
# celery@<hostname> ready.
```

### Test with Telegram Bot
1. Open Telegram and find your bot
2. Send `/start` - should receive welcome message
3. Send a text description of a video
4. Monitor logs: `docker-compose logs -f`

## Common Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart a specific service
docker-compose restart web

# View logs
docker-compose logs -f

# Rebuild after code changes
docker-compose build
docker-compose up -d

# Clean up everything (including volumes)
docker-compose down -v

# Execute command in container
docker exec -it ai-video-bot-web bash

# Check resource usage
docker stats
```

## Troubleshooting

### Services won't start
```bash
# Check logs for errors
docker-compose logs

# Rebuild images
docker-compose build --no-cache
docker-compose up -d
```

### Redis connection errors
```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
docker exec -it ai-video-bot-redis redis-cli ping
```

### FFmpeg not found
```bash
# Check FFmpeg binaries exist
ls -la bin/ffmpeg/

# Should see:
# ffmpeg
# ffprobe

# Check permissions
chmod +x bin/ffmpeg/ffmpeg bin/ffmpeg/ffprobe
```

### Port already in use
```bash
# Find process using port 5000
lsof -i :5000  # macOS/Linux
netstat -ano | findstr :5000  # Windows

# Kill the process or change port in docker-compose.yml
```

### Out of disk space
```bash
# Clean up Docker
docker system prune -a

# Remove old images
docker image prune -a

# Remove volumes
docker volume prune
```

### Worker not processing tasks
```bash
# Check worker logs
docker-compose logs worker

# Restart worker
docker-compose restart worker

# Check Redis connection
docker exec -it ai-video-bot-worker python -c "from redis import Redis; r = Redis.from_url('redis://redis:6379/0'); print(r.ping())"
```

## Development Workflow

1. Make code changes in your editor
2. Rebuild the affected service:
   ```bash
   docker-compose build web  # or worker
   ```
3. Restart the service:
   ```bash
   docker-compose up -d
   ```
4. Check logs:
   ```bash
   docker-compose logs -f web
   ```

## Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clears Redis data)
docker-compose down -v

# Stop but keep containers
docker-compose stop
```

## Next Steps

After successful local testing:
1. Commit your changes (but NOT the .env file!)
2. Push to GitHub
3. Follow the Render.com deployment guide
4. Configure environment variables in Render dashboard
5. Deploy and test in production

## Notes

- The `.env` file is gitignored - never commit API keys!
- Temporary files are stored in `./temp` directory
- FFmpeg binaries must be downloaded before building
- For production, use Render.com or similar platform
- Monitor resource usage with `docker stats`
- Redis data is ephemeral in this setup (lost on restart)

## Support

If you encounter issues:
1. Check logs: `docker-compose logs -f`
2. Verify environment variables in `.env`
3. Ensure FFmpeg binaries are present
4. Check Docker Desktop is running
5. Review error messages in logs
