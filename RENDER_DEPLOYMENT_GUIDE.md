# Render.com Deployment Guide

This guide provides step-by-step instructions for deploying the AI Video Generator Bot to Render.com.

## Prerequisites

Before starting the deployment, ensure you have:

1. ✅ A GitHub account with this repository pushed
2. ✅ A Render.com account (sign up at https://render.com)
3. ✅ All required API keys:
   - Telegram Bot Token (from @BotFather)
   - OpenAI API Key
   - Three OpenAI Assistant IDs (Script, Segment, Animation)
   - Runway API Key

## Step 1: Create Render.com Account and Connect GitHub

1. Go to https://render.com and sign up or log in
2. Click on "New +" button in the top right
3. Select "Blueprint" from the dropdown
4. Click "Connect GitHub" if not already connected
5. Authorize Render to access your GitHub repositories
6. Select this repository from the list

## Step 2: Deploy from Blueprint (render.yaml)

Render will automatically detect the `render.yaml` file and create all three services:

1. **ai-video-bot-web** (Flask web application)
2. **ai-video-bot-worker** (Celery worker)
3. **ai-video-redis** (Redis instance)

### Configure Environment Variables

For each service (web and worker), you need to set the following environment variables:

#### Web Service Environment Variables

Navigate to the web service settings and add:

```bash
# Telegram Configuration
TELEGRAM_BOT_TOKEN=<your_telegram_bot_token>
TELEGRAM_WEBHOOK_URL=https://ai-video-bot-web.onrender.com

# OpenAI Configuration
OPENAI_API_KEY=<your_openai_api_key>
OPENAI_SCRIPT_ASSISTANT_ID=<your_script_assistant_id>
OPENAI_SEGMENT_ASSISTANT_ID=<your_segment_assistant_id>
OPENAI_ANIMATION_ASSISTANT_ID=<your_animation_assistant_id>

# Runway Configuration
RUNWAY_API_KEY=<your_runway_api_key>

# Redis URL (auto-configured by Render)
REDIS_URL=<auto-filled-by-render>

# Application Settings (already set in render.yaml)
TEMP_DIR=/app/temp
MAX_CONCURRENT_JOBS=5
FILE_CLEANUP_HOURS=1
FFMPEG_PATH=ffmpeg
FFPROBE_PATH=ffprobe
LOG_LEVEL=INFO
```

#### Worker Service Environment Variables

Navigate to the worker service settings and add:

```bash
# OpenAI Configuration
OPENAI_API_KEY=<your_openai_api_key>
OPENAI_SCRIPT_ASSISTANT_ID=<your_script_assistant_id>
OPENAI_SEGMENT_ASSISTANT_ID=<your_segment_assistant_id>
OPENAI_ANIMATION_ASSISTANT_ID=<your_animation_assistant_id>

# Runway Configuration
RUNWAY_API_KEY=<your_runway_api_key>

# Redis URL (auto-configured by Render)
REDIS_URL=<auto-filled-by-render>

# Application Settings (already set in render.yaml)
TEMP_DIR=/app/temp
MAX_CONCURRENT_JOBS=5
FILE_CLEANUP_HOURS=1
FFMPEG_PATH=ffmpeg
FFPROBE_PATH=ffprobe
LOG_LEVEL=INFO
```

**Important Notes:**
- Mark all API keys as "Secret" in Render dashboard
- The `REDIS_URL` will be automatically populated by Render from the redis service
- Replace `<your_*>` placeholders with your actual values
- The `TELEGRAM_WEBHOOK_URL` should match your actual Render web service URL

## Step 3: Configure Disk Storage

Disk storage is already configured in `render.yaml`:

- **Web Service**: 10 GB mounted at `/app/temp`
- **Worker Service**: 20 GB mounted at `/app/temp`

Verify in the Render dashboard:
1. Go to each service settings
2. Navigate to "Disks" section
3. Confirm the disk is mounted at `/app/temp`

## Step 4: Deploy Services

1. Click "Apply" or "Create Blueprint" to start deployment
2. Render will:
   - Build Docker images for web and worker services
   - Start the Redis instance
   - Deploy all services

### Monitor Deployment

Watch the deployment logs for each service:

1. **Redis Service**: Should start immediately (no build required)
2. **Web Service**: 
   - Build time: ~5-10 minutes
   - Look for: "Starting gunicorn" in logs
3. **Worker Service**:
   - Build time: ~5-10 minutes
   - Look for: "celery@worker ready" in logs

## Step 5: Verify Health Check

Once the web service is deployed:

1. Get your web service URL from Render dashboard (e.g., `https://ai-video-bot-web.onrender.com`)
2. Test the health check endpoint:

```bash
curl https://ai-video-bot-web.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "ai-video-generator-bot"
}
```

## Step 6: Set Telegram Webhook

### Option A: Automatic (Recommended)

The application will automatically set the webhook on startup if `TELEGRAM_WEBHOOK_URL` is configured.

Check the web service logs for:
```
telegram_webhook_configured webhook_url=https://ai-video-bot-web.onrender.com/webhook
```

### Option B: Manual Setup

If automatic setup fails, use the provided script:

```bash
# Update set_webhook.py with your values
python set_webhook.py
```

Or use curl:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://ai-video-bot-web.onrender.com/webhook",
    "allowed_updates": ["message", "callback_query"]
  }'
```

### Verify Webhook

Check webhook status:

```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

Expected response should show:
- `url`: Your webhook URL
- `has_custom_certificate`: false
- `pending_update_count`: 0
- `last_error_date`: (should be empty)

## Step 7: Test the Bot

1. Open Telegram and find your bot
2. Send `/start` command
3. Send a test message: "Create an ad for a new smartphone"
4. Monitor the logs in Render dashboard:
   - Web service: Should show incoming webhook requests
   - Worker service: Should show video generation progress
   - Redis: Should show connection logs

## Troubleshooting

### Build Failures

**Issue**: Docker build fails
- Check Dockerfile syntax
- Verify all dependencies in requirements.txt
- Check Render build logs for specific errors

**Issue**: FFmpeg not found
- The Dockerfile installs FFmpeg via apt-get
- Verify the installation step completed successfully

### Runtime Errors

**Issue**: Redis connection failed
- Verify REDIS_URL is correctly set
- Check Redis service is running
- Ensure services are in the same region

**Issue**: Webhook not receiving updates
- Verify TELEGRAM_WEBHOOK_URL is correct
- Check webhook is set correctly with getWebhookInfo
- Ensure web service is publicly accessible
- Check Telegram webhook logs for errors

**Issue**: Celery worker not processing tasks
- Verify worker service is running
- Check REDIS_URL is correctly configured
- Monitor worker logs for errors
- Ensure all API keys are set

### Performance Issues

**Issue**: Slow video generation
- Consider upgrading to higher Render plans
- Increase worker concurrency (currently set to 2)
- Monitor disk usage and increase if needed

**Issue**: Out of disk space
- Check disk usage in Render dashboard
- Increase disk size if needed (web: 10GB, worker: 20GB)
- Verify FILE_CLEANUP_HOURS is working (set to 1 hour)

## Monitoring and Maintenance

### Logs

Access logs for each service in Render dashboard:
- Web service: HTTP requests, webhook events
- Worker service: Video generation progress, errors
- Redis: Connection logs

### Metrics

Monitor in Render dashboard:
- CPU usage
- Memory usage
- Disk usage
- Request count
- Response times

### Scaling

To handle more load:

1. **Vertical Scaling**: Upgrade service plans
   - Starter → Standard → Pro
   
2. **Horizontal Scaling**: Add more workers
   - Duplicate worker service in render.yaml
   - Increase worker concurrency

3. **Optimize**:
   - Adjust MAX_CONCURRENT_JOBS
   - Tune Celery worker settings
   - Implement caching for repeated requests

## Cost Estimation

Based on Render.com pricing (as of 2024):

- **Web Service (Starter)**: $7/month
- **Worker Service (Starter)**: $7/month
- **Redis (Starter)**: $7/month
- **Disk Storage**: 
  - Web (10GB): ~$1/month
  - Worker (20GB): ~$2/month

**Total**: ~$24/month for basic setup

## Security Best Practices

1. ✅ All API keys stored as secrets in Render
2. ✅ Webhook endpoint uses HTTPS
3. ✅ Rate limiting enabled (5 req/min, 20 req/hour)
4. ✅ Automatic file cleanup after 1 hour
5. ✅ No sensitive data in logs
6. ✅ Environment variables not committed to Git

## Next Steps

After successful deployment:

1. ✅ Test all bot features thoroughly
2. ✅ Monitor logs for errors
3. ✅ Set up alerts in Render dashboard
4. ✅ Document any custom configurations
5. ✅ Plan for scaling based on usage

## Support

- Render Documentation: https://render.com/docs
- Telegram Bot API: https://core.telegram.org/bots/api
- OpenAI API: https://platform.openai.com/docs
- Runway API: https://docs.runwayml.com

---

**Deployment Checklist**

- [ ] GitHub repository connected to Render
- [ ] Blueprint deployed from render.yaml
- [ ] All environment variables configured
- [ ] Disk storage verified
- [ ] All services deployed successfully
- [ ] Health check endpoint responding
- [ ] Telegram webhook configured
- [ ] Bot tested with sample message
- [ ] Logs monitored for errors
- [ ] Performance metrics reviewed
