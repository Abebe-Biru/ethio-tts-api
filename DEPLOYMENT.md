# Deployment Guide - Multi-Language TTS API

Complete guide for deploying your async TTS API to production.

## Table of Contents

- [Quick Start (Railway)](#quick-start-railway)
- [Alternative Platforms](#alternative-platforms)
- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [Monitoring & Alerts](#monitoring--alerts)
- [Scaling](#scaling)
- [Troubleshooting](#troubleshooting)

---

## Quick Start (Railway)

### Why Railway?
- ✅ **Easiest deployment** - 5 minutes from code to production
- ✅ **Free tier** - $5 credit/month (500 hours)
- ✅ **ML-friendly** - Handles PyTorch models (up to 8GB RAM)
- ✅ **Auto-deploy** - Push to GitHub, auto-deploys
- ✅ **Built-in database** - PostgreSQL included
- ✅ **Automatic HTTPS** - SSL certificates managed for you

### Step 1: Prepare Your Code

```bash
# 1. Make sure .gitignore is set up
cat > .gitignore << EOF
# Environment
.env
.env.local

# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/

# TTS Cache & Audio
tts_cache/
async_audio/
*.wav

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
EOF

# 2. Commit your code
git add .
git commit -m "Prepare for deployment"

# 3. Push to GitHub
git push origin main
```

### Step 2: Deploy to Railway

1. **Sign up**: Go to [railway.app](https://railway.app) and sign up with GitHub

2. **Create New Project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your TTS API repository
   - Railway will auto-detect it's a Python project

3. **Configure Environment Variables**:
   Click "Variables" tab and add:
   ```
   WEBHOOK_SECRET=<generate-strong-secret-here>
   DEBUG=false
   HOST=0.0.0.0
   PORT=8001
   CORS_ORIGINS=*
   ```

4. **Deploy**:
   - Railway automatically builds and deploys
   - Wait 2-5 minutes for first deployment
   - Models will download on first request (~1-2 minutes)

5. **Get Your URL**:
   - Click "Settings" → "Generate Domain"
   - Your API will be at: `https://your-app.up.railway.app`

### Step 3: Test Your Deployment

```bash
# Set your Railway URL
export API_URL="https://your-app.up.railway.app"

# Test health endpoint
curl $API_URL/v1/health

# Create async job
curl -X POST $API_URL/v1/tts/async \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Akkam jirta?",
    "language": "oromo",
    "webhook_url": "https://webhook.site/your-unique-id"
  }'

# Check metrics
curl $API_URL/metrics
```

### Step 4: Set Up Monitoring

1. **Railway Dashboard**:
   - View logs in real-time
   - Monitor CPU/Memory usage
   - Track deployments

2. **Health Checks**:
   Railway automatically monitors your `/v1/health` endpoint

3. **Alerts** (Optional):
   - Go to Settings → Notifications
   - Add email/Slack for downtime alerts

---

## Alternative Platforms

### Render.com

**Best for:** Free tier with auto-sleep

```yaml
# render.yaml
services:
  - type: web
    name: tts-api
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "uvicorn api.main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: WEBHOOK_SECRET
        generateValue: true
      - key: DEBUG
        value: false
```

**Deploy:**
1. Push to GitHub
2. Connect Render to your repo
3. Create "New Web Service"
4. Select your repo
5. Deploy!

**Cost:** Free (sleeps after 15min), $7/month for always-on

---

### DigitalOcean App Platform

**Best for:** Reliable and affordable

```yaml
# .do/app.yaml
name: tts-api
services:
  - name: api
    github:
      repo: your-username/tts-api
      branch: main
    build_command: pip install -r requirements.txt
    run_command: uvicorn api.main:app --host 0.0.0.0 --port 8080
    envs:
      - key: WEBHOOK_SECRET
        value: ${WEBHOOK_SECRET}
      - key: DEBUG
        value: "false"
    instance_size_slug: basic-xs
    instance_count: 1
```

**Deploy:**
1. Push to GitHub
2. Go to DigitalOcean → Apps
3. Create App → GitHub
4. Select repo
5. Configure environment variables
6. Deploy!

**Cost:** $5/month (basic), $12/month (professional)

---

### AWS (Advanced)

**Best for:** Production scale, full control

#### Option 1: ECS Fargate (Recommended)

```dockerfile
# Already have Dockerfile!
# Just push to ECR and deploy to ECS
```

**Steps:**
1. Build and push Docker image to ECR
2. Create ECS cluster
3. Create task definition
4. Create service with load balancer
5. Configure auto-scaling

**Cost:** ~$20-50/month (depends on usage)

#### Option 2: EC2 (Manual)

```bash
# On EC2 instance
sudo apt update
sudo apt install python3-pip
git clone your-repo
cd tts-api
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8001
```

**Cost:** $5-10/month (t3.small)

---

### Fly.io

**Best for:** Global deployment, edge computing

```toml
# fly.toml
app = "tts-api"

[build]
  builder = "paketobuildpacks/builder:base"

[[services]]
  http_checks = []
  internal_port = 8001
  processes = ["app"]
  protocol = "tcp"

  [[services.ports]]
    force_https = true
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443
```

**Deploy:**
```bash
fly launch
fly deploy
```

**Cost:** Free tier (3 VMs), then ~$10/month

---

## Pre-Deployment Checklist

### Security

- [ ] Generate strong `WEBHOOK_SECRET` (32+ characters)
- [ ] Set `DEBUG=false` in production
- [ ] Review CORS settings (`CORS_ORIGINS`)
- [ ] Add API key authentication (optional)
- [ ] Enable HTTPS (automatic on most platforms)

### Performance

- [ ] Test with production-like data
- [ ] Monitor memory usage (models need 2-4GB)
- [ ] Set up caching strategy
- [ ] Configure rate limits appropriately

### Monitoring

- [ ] Set up health check endpoint monitoring
- [ ] Configure log aggregation
- [ ] Set up error alerts
- [ ] Monitor Prometheus metrics

### Backup

- [ ] Plan for job data persistence (if needed)
- [ ] Set up audio file backup (if needed)
- [ ] Document recovery procedures

---

## Environment Variables

### Required

```bash
# Webhook Security (REQUIRED)
WEBHOOK_SECRET=your-super-secret-key-min-32-chars

# Server Configuration
HOST=0.0.0.0
PORT=8001
DEBUG=false

# CORS (adjust for your domain)
CORS_ORIGINS=https://your-frontend.com,https://your-app.com
```

### Optional

```bash
# Cache Configuration
CACHE_DIR=tts_cache

# Model Configuration (defaults work fine)
# No need to change unless you want different models
```

### Generating Secrets

```bash
# Generate strong webhook secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Or use openssl
openssl rand -base64 32
```

---

## Database Setup

### Current: In-Memory Storage
Your API currently uses in-memory storage (dict-based). This works great for:
- ✅ Development
- ✅ Small-scale production
- ✅ Single-server deployments

**Limitations:**
- ❌ Jobs lost on restart
- ❌ Can't scale horizontally (multiple servers)

### Future: PostgreSQL (Recommended for Production)

When you need persistence, upgrade to PostgreSQL:

```python
# api/jobs.py (future upgrade)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Instead of dict
# _jobs: Dict[str, Job] = {}

# Use database
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
```

**Railway includes PostgreSQL for free!**

---

## Monitoring & Alerts

### Built-in Monitoring

Your API already has:
- ✅ `/v1/health` - Health check endpoint
- ✅ `/metrics` - Prometheus metrics
- ✅ Structured logging (JSON format)

### Set Up Prometheus + Grafana (Optional)

```yaml
# docker-compose.yml (for self-hosted monitoring)
version: '3'
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'tts-api'
    static_configs:
      - targets: ['your-api-url:8001']
```

### Key Metrics to Monitor

```promql
# Request rate
rate(tts_api_requests_total[5m])

# Error rate
rate(tts_api_errors_total[5m]) / rate(tts_api_requests_total[5m])

# Job processing time
histogram_quantile(0.95, rate(tts_job_processing_duration_seconds_bucket[5m]))

# Queue length
tts_job_queue_length

# Webhook success rate
rate(tts_webhook_delivery_total{status="success"}[5m]) / rate(tts_webhook_delivery_total[5m])
```

### Alerts (Example)

```yaml
# alerts.yml
groups:
  - name: tts_api
    rules:
      - alert: HighErrorRate
        expr: rate(tts_api_errors_total[5m]) > 0.05
        annotations:
          summary: "High error rate detected"

      - alert: LongQueueLength
        expr: tts_job_queue_length > 50
        annotations:
          summary: "Job queue is backing up"

      - alert: WebhookFailures
        expr: rate(tts_webhook_delivery_total{status="failure"}[5m]) > 0.1
        annotations:
          summary: "Webhook delivery failures"
```

---

## Scaling

### Vertical Scaling (Increase Resources)

**When to scale up:**
- CPU usage > 80%
- Memory usage > 80%
- Queue length consistently > 20

**Railway:**
- Go to Settings → Resources
- Increase RAM/CPU
- Redeploy

**Cost:** ~$5-20/month per tier

---

### Horizontal Scaling (Multiple Servers)

**Requirements:**
1. Switch to PostgreSQL for job storage
2. Use Redis for queue management
3. Use S3/R2 for audio file storage

**Architecture:**
```
Load Balancer
    ↓
[API Server 1] [API Server 2] [API Server 3]
    ↓              ↓              ↓
PostgreSQL    Redis Queue    S3 Storage
```

**When you need this:**
- > 1000 requests/minute
- > 100 concurrent jobs
- Need 99.99% uptime

---

## Troubleshooting

### Issue: Models Not Loading

**Symptoms:**
- First request takes 2+ minutes
- "Model not loaded" errors

**Solution:**
```bash
# Preload models on startup
# Add to api/main.py startup event:
await model_manager.load_model("oromo")
await model_manager.load_model("amharic")
```

---

### Issue: Out of Memory

**Symptoms:**
- Server crashes
- "Killed" in logs

**Solution:**
1. Increase RAM (Railway: 2GB → 4GB)
2. Reduce concurrent jobs
3. Implement model unloading for unused languages

---

### Issue: Slow Webhook Delivery

**Symptoms:**
- Webhooks take > 30 seconds
- Timeout errors

**Solution:**
1. Check webhook endpoint response time
2. Increase timeout in `api/webhooks.py`
3. Implement async webhook queue

---

### Issue: Audio Files Filling Disk

**Symptoms:**
- Disk space warnings
- "No space left" errors

**Solution:**
```bash
# Reduce retention time (default: 24 hours)
# In api/storage.py, change cleanup_old_files:
await storage.cleanup_old_files(max_age_hours=6)  # 6 hours instead of 24
```

Or use cloud storage (S3/R2).

---

### Issue: Rate Limit Errors

**Symptoms:**
- 429 Too Many Requests
- Queue full errors

**Solution:**
1. Increase rate limits in `api/middleware/rate_limit.py`
2. Add more workers
3. Scale horizontally

---

## Production Best Practices

### 1. Use Environment Variables

```bash
# Never commit secrets!
# Use .env file locally
# Use platform's environment variables in production
```

### 2. Enable Logging

```python
# Already configured with structlog!
# Logs are in JSON format for easy parsing
```

### 3. Set Up Health Checks

```bash
# Your /v1/health endpoint is perfect
# Configure platform to check it every 30 seconds
```

### 4. Implement Graceful Shutdown

```python
# Already handled by FastAPI!
# Workers stop gracefully on shutdown
```

### 5. Use CDN for Audio Files

```bash
# For high traffic, use Cloudflare R2 (free 10GB)
# Or AWS S3 with CloudFront
```

### 6. Monitor Everything

```bash
# Check metrics daily
curl https://your-api.com/metrics | grep tts_job

# Set up alerts for:
# - Error rate > 5%
# - Queue length > 50
# - Webhook failures > 10%
```

---

## Cost Estimates

### Small Scale (< 1000 jobs/day)
- **Railway Free Tier**: $0/month (500 hours)
- **Railway Hobby**: $5/month
- **Render Free**: $0/month (with sleep)

### Medium Scale (1000-10000 jobs/day)
- **Railway Pro**: $20/month
- **DigitalOcean**: $12/month
- **Render Standard**: $25/month

### Large Scale (> 10000 jobs/day)
- **AWS ECS**: $50-200/month
- **Multiple servers**: $100-500/month
- **With CDN**: +$10-50/month

---

## Next Steps

1. **Deploy to Railway** (5 minutes)
2. **Test with real traffic** (1 day)
3. **Monitor metrics** (ongoing)
4. **Optimize based on usage** (as needed)
5. **Scale when needed** (when you hit limits)

---

## Support & Resources

- **Railway Docs**: https://docs.railway.app
- **FastAPI Deployment**: https://fastapi.tiangolo.com/deployment/
- **Your API Docs**: See WEBHOOKS_GUIDE.md

---

**🚀 Ready to deploy? Start with Railway and scale as you grow!**

**Questions?** Check the troubleshooting section or review your metrics at `/metrics`.

---

**Built with ❤️ for production deployment**
