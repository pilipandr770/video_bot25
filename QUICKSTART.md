# Quick Start Guide

Get the AI Video Generator Bot running locally in Docker in 5 minutes!

## Prerequisites

- Docker Desktop installed and running
- Git (to clone the repo)
- API keys ready (Telegram, OpenAI, Runway)

## Step 1: Download FFmpeg (Required!)

**On Linux/macOS:**
```bash
cd bin/ffmpeg
bash download_ffmpeg.sh
cd ../..
```

**On Windows:**
1. Download from: https://www.gyan.dev/ffmpeg/builds/
2. Extract `ffmpeg.exe` and `ffprobe.exe`
3. Copy both files to `bin/ffmpeg/` directory

## Step 2: Configure Environment

1. Open `.env` file in the project root
2. Fill in your API keys:

```bash
# Get from @BotFather on Telegram
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Get from https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-...

# Create at https://platform.openai.com/assistants
OPENAI_ASSISTANT_ID=asst_...

# Get from https://runwayml.com
RUNWAY_API_KEY=...
```

## Step 3: Start Docker Services

```bash
# Build and start all services
docker-compose up -d

# Wait 30 seconds for services to start
# Then check status
docker-compose ps
```

You should see:
- ✅ ai-video-bot-redis (healthy)
- ✅ ai-video-bot-web (healthy)  
- ✅ ai-video-bot-worker (running)

## Step 4: Verify Setup

```bash
# Run the test script
bash test_docker_setup.sh

# Or manually test health endpoint
curl http://localhost:5000/health
```

Expected response:
```json
{"status":"healthy","service":"ai-video-generator-bot"}
```

## Step 5: Test with Telegram (Optional)

To test with real Telegram messages:

1. **Install ngrok**: https://ngrok.com/download

2. **Start ngrok tunnel:**
   ```bash
   ngrok http 5000
   ```

3. **Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)

4. **Update .env:**
   ```bash
   TELEGRAM_WEBHOOK_URL=https://abc123.ngrok.io
   ```

5. **Restart web service:**
   ```bash
   docker-compose restart web
   ```

6. **Set Telegram webhook:**
   ```bash
   curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://abc123.ngrok.io/webhook"}'
   ```

7. **Send a message to your bot!**

## Monitor Logs

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f web
docker-compose logs -f worker
```

## Common Issues

### "FFmpeg not found"
- Download FFmpeg binaries first (Step 1)
- Rebuild: `docker-compose build --no-cache`

### "Port 5000 already in use"
- Stop other services using port 5000
- Or change port in `docker-compose.yml`

### "Redis connection failed"
- Check Redis is running: `docker-compose ps redis`
- Restart: `docker-compose restart redis`

### "Environment variable not set"
- Check `.env` file has all required keys
- Restart services: `docker-compose restart`

## Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove data
docker-compose down -v
```

## Next Steps

After successful local testing:
1. ✅ Commit code to GitHub (`.env` is gitignored)
2. 🚀 Deploy to Render.com
3. 🎬 Start generating videos!

## Need Help?

- Check logs: `docker-compose logs -f`
- Read full guide: `DOCKER_SETUP.md`
- Review README: `README.md`
