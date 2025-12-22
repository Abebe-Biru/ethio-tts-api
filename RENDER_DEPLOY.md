# Deploy to Render - Complete Guide

## Quick Deploy (5 Minutes)

### Step 1: Push to GitHub

```bash
git add render.yaml build.sh
git commit -m "Add Render deployment configuration"
git push origin main
```

### Step 2: Create Render Account

1. Go to https://render.com
2. Sign up with GitHub

### Step 3: Deploy

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Render will auto-detect `render.yaml`
4. Click **"Apply"**

**That's it!** Render will automatically:
- Install Python 3.10
- Run `build.sh` to install dependencies
- Start your API with `python -m api`
- Assign a public URL

---

## Configuration Details

### `render.yaml`

Render uses this file for infrastructure as code:

```yaml
services:
  - type: web
    name: oromo-tts-api
    runtime: python
    plan: free
    buildCommand: "./build.sh"
    startCommand: "python -m api"
    healthCheckPath: /v1/health
```

### `build.sh`

Custom build script that:
1. Installs CPU-only PyTorch (~200MB vs 6GB CUDA)
2. Installs transformers without deps
3. Installs all other dependencies

**Why CPU-only?** Render free tier has limited disk space, and you don't have GPU access anyway.

---

## Environment Variables

Render auto-configures these from `render.yaml`:

| Variable | Value | Description |
|----------|-------|-------------|
| `PYTHON_VERSION` | 3.10.15 | Python version |
| `DEBUG` | false | Production mode |
| `HOST` | 0.0.0.0 | Bind to all interfaces |
| `PORT` | 10000 | Render's default port |
| `CORS_ORIGINS` | * | Allow all origins |
| `WEBHOOK_SECRET` | auto-generated | Secure webhook signing |

---

## Your API URL

After deployment, your API will be at:

```
https://oromo-tts-api.onrender.com
```

### Test Endpoints

```bash
# Health check
curl https://oromo-tts-api.onrender.com/v1/health

# API docs
https://oromo-tts-api.onrender.com/docs

# Metrics
curl https://oromo-tts-api.onrender.com/metrics
```

---

## Free Tier Limits

| Resource | Limit |
|----------|-------|
| **RAM** | 512MB |
| **Disk** | 1GB |
| **Hours** | 750/month |
| **Bandwidth** | 100GB/month |
| **Sleep** | After 15 min inactivity |

**Note:** Free tier services sleep after 15 minutes of inactivity. First request after sleep takes ~30 seconds to wake up.

---

## Cold Start Behavior

### First Request After Sleep
- **Wake up time:** ~30 seconds
- **Model download:** 1-2 minutes (first time only)
- **Total:** ~2-3 minutes first request

### Subsequent Requests
- **TTS generation:** 5-15 seconds
- **Job creation:** <500ms

---

## Monitoring

### Render Dashboard
- Real-time logs
- CPU/Memory metrics
- Deploy history
- Health check status

### Your API Metrics
```bash
curl https://oromo-tts-api.onrender.com/metrics
```

Key metrics:
- `tts_job_created_total`
- `tts_job_queue_length`
- `tts_webhook_delivery_total`

---

## Troubleshooting

### Build Fails

**Check build logs** in Render dashboard for errors.

Common issues:
- Missing system dependencies
- Out of disk space
- Python version mismatch

**Solution:** Review `build.sh` and ensure all dependencies are listed.

### Out of Memory

**Symptom:** Service crashes, "Killed" in logs

**Solution:** 
- Upgrade to Starter plan ($7/month, 512MB → 2GB RAM)
- Or optimize model loading

### Models Not Loading

**Symptom:** Timeout on first request

**Solution:** This is normal! Models download on first request (~2 minutes). Subsequent requests are fast.

---

## Upgrade Options

### Starter Plan ($7/month)
- 2GB RAM
- No sleep
- Custom domains
- Better performance

### Pro Plan ($25/month)
- 4GB RAM
- Priority support
- Advanced metrics

---

## Custom Domain

1. Go to Render dashboard → Settings
2. Add custom domain
3. Update DNS records
4. Enable HTTPS (automatic)

---

## Auto-Deploy

Render automatically deploys when you push to `main` branch:

```bash
git push origin main
# Render detects push and redeploys
```

Disable in Render dashboard if needed.

---

## Summary

✅ **Infrastructure as Code** - `render.yaml`  
✅ **CPU-only PyTorch** - Saves disk space  
✅ **Auto-deploy** - Push to deploy  
✅ **Free tier** - 750 hours/month  
✅ **HTTPS** - Automatic SSL  
✅ **Health checks** - Auto-restart on failure  

**Deploy time:** ~5 minutes  
**Build time:** ~3-5 minutes  
**Your URL:** `https://oromo-tts-api.onrender.com`
