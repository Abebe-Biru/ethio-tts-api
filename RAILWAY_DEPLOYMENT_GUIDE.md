# 🚀 Railway Deployment Guide - Multi-Language TTS API

**Deploy your TTS API to production in 5 minutes!**

---

## Why Railway?

✅ **Fastest deployment** - From code to production in 5 minutes  
✅ **Free tier** - $5 credit/month (enough for testing)  
✅ **ML-friendly** - Handles PyTorch models (up to 8GB RAM)  
✅ **Auto-deploy** - Push to GitHub, auto-deploys  
✅ **Built-in monitoring** - Logs, metrics, and health checks  
✅ **Automatic HTTPS** - SSL certificates managed for you  
✅ **No credit card required** - Start for free  

---

## Prerequisites

- [ ] GitHub account
- [ ] Railway account (sign up at [railway.app](https://railway.app))
- [ ] Your code pushed to GitHub
- [ ] 5 minutes of your time ⏱️

---

## 🎯 Quick Deploy (5 Minutes)

### Step 1: Prepare Your Repository (2 minutes)

```bash
# 1. Make sure you have the required files
ls -la

# You should see:
# ✓ pyproject.toml or requirements.txt
# ✓ railway.toml
# ✓ Procfile
# ✓ .gitignore

# 2. Ensure .gitignore is set up correctly
cat .gitignore

# Should include:
# .env
# __pycache__/
# *.pyc
# .venv/
# tts_cache/
# async_audio/
# *.wav

# 3. Commit and push to GitHub
git add .
git commit -m "feat: prepare for Railway deployment"
git push origin main
```

---

### Step 2: Deploy to Railway (2 minutes)

#### Option A: Deploy via Railway Dashboard (Recommended)

1. **Go to Railway**: https://railway.app

2. **Sign in with GitHub**
   - Click "Login with GitHub"
   - Authorize Railway

3. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your TTS API repository
   - Click "Deploy Now"

4. **Wait for Build** (1-2 minutes)
   - Railway auto-detects Python
   - Installs dependencies
   - Builds your app

#### Option B: Deploy via Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Or with Homebrew (Mac)
brew install railway

# Login
railway login

# Initialize project
railway init

# Deploy
railway up
```

---

### Step 3: Configure Environment Variables (1 minute)

1. **Go to your project** in Railway dashboard

2. **Click "Variables" tab**

3. **Add these variables:**

```bash
# Required
WEBHOOK_SECRET=<generate-strong-secret>
DEBUG=false
HOST=0.0.0.0
PORT=8001

# Optional (recommended)
CORS_ORIGINS=*
CACHE_DIR=tts_cache
```

**Generate a strong webhook secret:**
```bash
# On Mac/Linux
openssl rand -base64 32

# Or Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Example output: 
# xK9mP2nQ5rT8wV1yZ4aB7cD0eF3gH6jL9mN2pQ5sT8v
```

4. **Click "Deploy"** to restart with new variables

---

### Step 4: Get Your URL & Test (30 seconds)

1. **Generate Domain**
   - Click "Settings" tab
   - Scroll to "Domains"
   - Click "Generate Domain"
   - Your URL: `https://your-app-name.up.railway.app`

2. **Test Health Endpoint**
```bash
# Set your Railway URL
export API_URL="https://your-app-name.up.railway.app"

# Test health
curl $API_URL/v1/health

# Expected response:
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "model_loaded": false,
#   "supported_languages": ["oromo", "amharic", "om", "am"]
# }
```

3. **Test TTS Generation**
```bash
# Generate Oromo speech
curl -X POST $API_URL/v1/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"Akkam jirta?", "language":"oromo"}' \
  --output test.wav

# Check file
ls -lh test.wav
# Should be ~100KB-500KB

# Play it (Mac)
afplay test.wav

# Play it (Linux)
aplay test.wav
```

---

## 🎉 You're Live!

Your API is now deployed and accessible at:
```
https://your-app-name.up.railway.app
```

**Next steps:**
- [Test async jobs](#test-async-jobs)
- [Monitor your app](#monitoring)
- [Set up custom domain](#custom-domain-optional)
- [Scale your app](#scaling)

---

## 🧪 Test Async Jobs

### 1. Create an Async Job

```bash
# You'll need a webhook URL to receive notifications
# Use webhook.site for testing: https://webhook.site

# Get your unique webhook URL from webhook.site
export WEBHOOK_URL="https://webhook.site/your-unique-id"

# Create async job
curl -X POST $API_URL/v1/tts/async \
  -H "Content-Type: application/json" \
  -d "{
    \"text\": \"Akkam jirta? Maqaan koo Kiro jedhama. Ani gargaaraa AI.\",
    \"language\": \"oromo\",
    \"webhook_url\": \"$WEBHOOK_URL\"
  }"

# Response:
# {
#   "job_id": "job_abc123def456",
#   "status": "pending",
#   "message": "Job created and queued for processing",
#   "created_at": "2024-12-19T10:00:00Z"
# }
```

### 2. Check Job Status

```bash
# Save job_id from previous response
export JOB_ID="job_abc123def456"

# Check status
curl $API_URL/v1/jobs/$JOB_ID

# Response:
# {
#   "job_id": "job_abc123def456",
#   "status": "completed",  # or "pending", "processing"
#   "audio_url": "/v1/download/job_abc123def456",
#   ...
# }
```

### 3. Download Audio

```bash
# Download the generated audio
curl -O $API_URL/v1/download/$JOB_ID

# File will be saved as: job_abc123def456.wav
```

### 4. Check Webhook Notification

Go to your webhook.site URL and you should see:

```json
{
  "job_id": "job_abc123def456",
  "status": "completed",
  "created_at": "2024-12-19T10:00:00Z",
  "completed_at": "2024-12-19T10:01:30Z",
  "audio_url": "/v1/download/job_abc123def456",
  "language": "oromo",
  "text_length": 58
}
```

---

## 📊 Monitoring

### View Logs

**Railway Dashboard:**
1. Go to your project
2. Click "Deployments" tab
3. Click on latest deployment
4. View real-time logs

**Railway CLI:**
```bash
railway logs
```

### Check Metrics

```bash
# Prometheus metrics
curl $API_URL/metrics

# Key metrics to watch:
# - tts_api_requests_total
# - tts_job_queue_length
# - tts_webhook_delivery_total
```

### Health Checks

Railway automatically monitors your `/v1/health` endpoint.

**Configure in railway.toml:**
```toml
[deploy]
healthcheckPath = "/v1/health"
healthcheckTimeout = 100
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

---

## 🔧 Configuration

### Railway.toml Explained

```toml
[build]
builder = "NIXPACKS"  # Railway's auto-builder

[deploy]
startCommand = "python -m api"  # How to start your app
healthcheckPath = "/v1/health"  # Health check endpoint
healthcheckTimeout = 100        # Timeout in seconds
restartPolicyType = "ON_FAILURE"  # Restart on crash
restartPolicyMaxRetries = 3     # Max restart attempts
```

### Procfile Explained

```
web: python -m api
```

This tells Railway how to start your web service.

### Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `WEBHOOK_SECRET` | ✅ Yes | - | Secret for webhook HMAC signatures |
| `DEBUG` | No | `false` | Enable debug mode (shows /docs) |
| `HOST` | No | `0.0.0.0` | Server host |
| `PORT` | No | `8001` | Server port (Railway sets this) |
| `CORS_ORIGINS` | No | `*` | Allowed CORS origins |
| `CACHE_DIR` | No | `tts_cache` | Cache directory path |

---

## 🚀 Scaling

### Vertical Scaling (More Resources)

**When to scale:**
- CPU usage > 80%
- Memory usage > 80%
- Queue length consistently > 20

**How to scale:**
1. Go to "Settings" tab
2. Scroll to "Resources"
3. Increase RAM/CPU
4. Click "Update"

**Pricing:**
- **Hobby**: $5/month (512MB RAM, 0.5 vCPU)
- **Pro**: $20/month (8GB RAM, 8 vCPU)

### Horizontal Scaling (Multiple Instances)

**Requirements:**
1. Switch to PostgreSQL for job storage
2. Use Redis for queue management
3. Use S3/R2 for audio storage

**Not needed until:**
- > 1000 requests/minute
- > 100 concurrent jobs

---

## 🌐 Custom Domain (Optional)

### Add Your Domain

1. **Go to Settings** → Domains
2. **Click "Custom Domain"**
3. **Enter your domain**: `api.yourdomain.com`
4. **Add DNS records** (Railway provides instructions)

**DNS Configuration:**
```
Type: CNAME
Name: api
Value: your-app-name.up.railway.app
```

5. **Wait for SSL** (automatic, 1-5 minutes)

---

## 🐛 Troubleshooting

### Issue: Build Failed

**Symptoms:**
```
Error: Could not find a version that satisfies the requirement torch
```

**Solution:**
```bash
# Make sure requirements.txt or pyproject.toml is correct
# Railway uses Python 3.12 by default

# Add runtime.txt to specify Python version
echo "python-3.12" > runtime.txt
git add runtime.txt
git commit -m "fix: specify Python version"
git push
```

---

### Issue: App Crashes on Startup

**Symptoms:**
```
Application failed to respond
```

**Solution 1: Check Logs**
```bash
railway logs

# Look for errors like:
# - Import errors
# - Missing dependencies
# - Port binding issues
```

**Solution 2: Verify Start Command**
```bash
# In railway.toml, ensure:
startCommand = "python -m api"

# Or in Procfile:
web: python -m api
```

**Solution 3: Check Port**
```python
# In api/main.py or api/__main__.py
# Railway sets PORT environment variable
import os
port = int(os.getenv("PORT", 8001))
```

---

### Issue: Models Not Loading

**Symptoms:**
```
First request takes 2+ minutes
Model download timeout
```

**Solution: Preload Models**

Add to `api/main.py` startup event:
```python
@app.on_event("startup")
async def startup_event():
    # ... existing code ...
    
    # Preload models
    log.info("preloading_models")
    await model_manager.load_model("oromo")
    await model_manager.load_model("amharic")
    log.info("models_preloaded")
```

---

### Issue: Out of Memory

**Symptoms:**
```
Killed
Exit code: 137
```

**Solution:**
1. **Upgrade plan** (Hobby → Pro)
2. **Reduce concurrent jobs**
3. **Implement model unloading**

```python
# In api/model_manager.py
# Unload unused models after 1 hour
async def cleanup_unused_models():
    for language in list(self.models.keys()):
        if not recently_used(language):
            self.unload_model(language)
```

---

### Issue: Webhook Delivery Fails

**Symptoms:**
```
Webhook delivery failed after 3 retries
```

**Solution:**
1. **Check webhook URL** is accessible
2. **Verify webhook endpoint** returns 200-204
3. **Check webhook logs** for errors
4. **Test webhook locally** first

```bash
# Test webhook endpoint
curl -X POST https://your-webhook-url.com/webhook \
  -H "Content-Type: application/json" \
  -d '{"job_id":"test","status":"completed"}'

# Should return 200 OK
```

---

### Issue: Rate Limit Errors

**Symptoms:**
```
429 Too Many Requests
```

**Solution:**

Increase limits in `api/middleware/rate_limit.py`:
```python
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=120,  # Increased from 60
    requests_per_hour=2000    # Increased from 1000
)
```

---

### Issue: Audio Files Fill Disk

**Symptoms:**
```
No space left on device
```

**Solution:**

Reduce retention time in `api/storage.py`:
```python
# Change from 24 hours to 6 hours
await storage.cleanup_old_files(max_age_hours=6)
```

Or use Railway's persistent storage:
```bash
# In Railway dashboard
# Settings → Volumes → Add Volume
# Mount path: /app/async_audio
```

---

## 💰 Cost Estimates

### Free Tier
- **$5 credit/month**
- **500 execution hours**
- **Good for:** Testing, low traffic

### Hobby Plan ($5/month)
- **512MB RAM, 0.5 vCPU**
- **Good for:** < 100 jobs/day
- **Handles:** ~10 concurrent requests

### Pro Plan ($20/month)
- **8GB RAM, 8 vCPU**
- **Good for:** < 1000 jobs/day
- **Handles:** ~100 concurrent requests

### Enterprise (Custom)
- **Custom resources**
- **Good for:** > 1000 jobs/day
- **Contact Railway for pricing**

---

## 🔒 Security Best Practices

### 1. Secure Webhook Secret

```bash
# Generate strong secret (32+ characters)
openssl rand -base64 32

# Add to Railway environment variables
# Never commit to git!
```

### 2. Restrict CORS Origins

```bash
# In Railway variables
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Not recommended for production:
# CORS_ORIGINS=*
```

### 3. Enable API Key Authentication

```python
# In api/middleware/api_key.py
# Generate API keys for users
# Track usage per key
```

### 4. Use HTTPS Only

```python
# Railway provides HTTPS automatically
# Redirect HTTP to HTTPS (optional)
```

---

## 📈 Performance Optimization

### 1. Enable Caching

```bash
# Already enabled by default
# Cache directory: tts_cache/
```

### 2. Preload Models

```python
# In api/main.py startup event
await model_manager.load_model("oromo")
await model_manager.load_model("amharic")
```

### 3. Use Persistent Storage

```bash
# Railway Dashboard → Settings → Volumes
# Add volume for tts_cache to persist across deploys
```

### 4. Monitor Performance

```bash
# Check metrics regularly
curl $API_URL/metrics | grep tts_job_processing_duration

# Set up alerts for:
# - High error rate (> 5%)
# - Long queue (> 50 jobs)
# - Slow processing (> 60s)
```

---

## 🔄 CI/CD Setup

### Automatic Deployments

Railway automatically deploys when you push to GitHub!

```bash
# Make changes
git add .
git commit -m "feat: add new feature"
git push origin main

# Railway automatically:
# 1. Detects push
# 2. Builds new image
# 3. Runs tests (if configured)
# 4. Deploys to production
# 5. Runs health checks
```

### Deploy Specific Branch

```bash
# Railway Dashboard → Settings → Deploy
# Change "Production Branch" to your branch name
```

### Manual Deploy

```bash
# Railway CLI
railway up

# Or trigger from dashboard
# Deployments → Deploy Latest
```

---

## 📚 Additional Resources

### Railway Documentation
- **Main Docs**: https://docs.railway.app
- **Python Guide**: https://docs.railway.app/guides/python
- **Environment Variables**: https://docs.railway.app/develop/variables

### Your API Documentation
- **API Guide**: See `API_V1_GUIDE.md`
- **Webhooks Guide**: See `WEBHOOKS_GUIDE.md`
- **Full Deployment**: See `DEPLOYMENT.md`

### Support
- **Railway Discord**: https://discord.gg/railway
- **Railway Status**: https://status.railway.app

---

## ✅ Deployment Checklist

Before going live:

**Code:**
- [ ] All tests passing
- [ ] No secrets in code
- [ ] .gitignore configured
- [ ] Code pushed to GitHub

**Railway:**
- [ ] Project created
- [ ] Environment variables set
- [ ] WEBHOOK_SECRET generated
- [ ] Domain configured (optional)

**Testing:**
- [ ] Health check works
- [ ] TTS generation works
- [ ] Async jobs work
- [ ] Webhooks deliver
- [ ] Metrics accessible

**Monitoring:**
- [ ] Logs reviewed
- [ ] Metrics checked
- [ ] Health checks passing
- [ ] Error rate < 1%

**Security:**
- [ ] CORS configured
- [ ] Webhook secret secure
- [ ] API keys enabled (optional)
- [ ] HTTPS working

---

## 🎯 Quick Commands Reference

```bash
# Deploy
railway up

# View logs
railway logs

# Open dashboard
railway open

# Run command
railway run python test_complete_api.py

# Add environment variable
railway variables set WEBHOOK_SECRET=your-secret

# Check status
railway status

# Link to project
railway link
```

---

## 🚀 You're Ready!

Your Multi-Language TTS API is now live on Railway!

**Your API URL:**
```
https://your-app-name.up.railway.app
```

**Test it:**
```bash
curl https://your-app-name.up.railway.app/v1/health
```

**Share it:**
```
API Documentation: https://your-app-name.up.railway.app/docs
Metrics: https://your-app-name.up.railway.app/metrics
```

---

**Need help?** Check the troubleshooting section or Railway Discord!

**Built with ❤️ for easy deployment**
