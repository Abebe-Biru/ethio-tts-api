# Railway Deployment Checklist

## ✅ Pre-Deployment (Complete!)

Your API is now ready for Railway deployment! Here's what we prepared:

### Files Created/Updated:
- ✅ `railway.toml` - Railway configuration
- ✅ `Procfile` - Start command for Railway
- ✅ `requirements.txt` - Python dependencies (backup)
- ✅ `.env.railway` - Environment variables template
- ✅ `.gitignore` - Updated to exclude test files and audio
- ✅ `pyproject.toml` - Already configured with all dependencies

---

## 🚀 Deployment Steps

### Step 1: Generate Webhook Secret

```bash
# Run this command to generate a strong secret:
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Copy the output - you'll need it for Railway
```

### Step 2: Push to GitHub

```bash
# Make sure everything is committed
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### Step 3: Deploy to Railway

1. **Go to Railway**: https://railway.app
2. **Sign up/Login** with GitHub
3. **New Project** → "Deploy from GitHub repo"
4. **Select your repository**
5. **Wait for auto-detection** (Railway will detect Python)

### Step 4: Configure Environment Variables

In Railway dashboard, go to **Variables** tab and add:

```
WEBHOOK_SECRET=<paste-your-generated-secret>
DEBUG=false
HOST=0.0.0.0
CORS_ORIGINS=*
```

**Note:** Railway automatically sets `PORT` - don't add it manually!

### Step 5: Deploy!

- Railway will automatically build and deploy
- First deployment takes 3-5 minutes
- Watch the logs in the "Deployments" tab

### Step 6: Get Your URL

1. Go to **Settings** tab
2. Click **Generate Domain**
3. Your API will be at: `https://your-app.up.railway.app`

### Step 7: Test Your Deployment

```bash
# Set your Railway URL
export API_URL="https://your-app.up.railway.app"

# Test health
curl $API_URL/v1/health

# Test async job
curl -X POST $API_URL/v1/tts/async \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Akkam jirta?",
    "language": "oromo",
    "webhook_url": "https://webhook.site/your-unique-id"
  }'
```

---

## 📊 What Railway Will Do

1. **Detect Python** - Automatically recognizes your project
2. **Install Dependencies** - Runs `pip install` from pyproject.toml
3. **Start Server** - Runs command from `Procfile`
4. **Assign URL** - Gives you a public HTTPS URL
5. **Monitor Health** - Checks `/v1/health` endpoint
6. **Auto-restart** - Restarts if server crashes

---

## 💰 Cost Estimate

### Free Tier
- **$5 credit/month** (500 hours)
- Perfect for testing and small projects
- Includes:
  - 512MB RAM
  - 1 vCPU
  - Automatic HTTPS
  - Custom domain support

### When You Need More
- **Hobby Plan**: $5/month
  - 1GB RAM
  - 2 vCPU
  - Always-on
  
- **Pro Plan**: $20/month
  - 8GB RAM
  - 8 vCPU
  - Priority support

**Your API will likely run fine on the free tier for testing!**

---

## 🔍 Monitoring Your Deployment

### Railway Dashboard
- **Logs**: Real-time logs in "Deployments" tab
- **Metrics**: CPU/Memory usage in "Metrics" tab
- **Health**: Automatic health checks

### Your API Metrics
```bash
# Check Prometheus metrics
curl https://your-app.up.railway.app/metrics

# Key metrics to watch:
# - tts_job_created_total
# - tts_job_queue_length
# - tts_webhook_delivery_total
```

---

## 🐛 Troubleshooting

### Issue: Build Failed

**Check:**
- All dependencies in `pyproject.toml`
- No syntax errors in code
- Railway logs for specific error

**Solution:**
```bash
# Test locally first
uv run python -m api
```

---

### Issue: Server Won't Start

**Check:**
- Environment variables are set
- `PORT` is not manually set (Railway sets it)
- Health check endpoint is working

**Solution:**
```bash
# Check Railway logs
# Look for startup errors
```

---

### Issue: Models Not Loading

**Symptoms:**
- First request takes 2+ minutes
- Timeout errors

**Solution:**
This is normal! Models download on first request.
- Oromo model: ~1-2 minutes first time
- Amharic model: ~1-2 minutes first time
- Subsequent requests: Fast (models cached)

**Optional:** Increase timeout in Railway settings to 300 seconds

---

### Issue: Out of Memory

**Symptoms:**
- Server crashes
- "Killed" in logs

**Solution:**
1. Upgrade to Hobby plan (1GB RAM)
2. Or Pro plan (8GB RAM) for heavy usage

---

## 🎯 Next Steps After Deployment

1. **Test thoroughly** - Run all your test scripts
2. **Monitor metrics** - Check `/metrics` daily
3. **Set up alerts** - Configure Railway notifications
4. **Update documentation** - Add your Railway URL to docs
5. **Share with users** - Your API is live!

---

## 📚 Additional Resources

- **Railway Docs**: https://docs.railway.app
- **Your API Docs**: 
  - WEBHOOKS_GUIDE.md
  - DEPLOYMENT.md
  - README.md

---

## ✅ Deployment Checklist

Before deploying, verify:

- [ ] Code pushed to GitHub
- [ ] Webhook secret generated
- [ ] Environment variables ready
- [ ] `.gitignore` excludes test files
- [ ] All tests passing locally
- [ ] Documentation updated

After deploying, verify:

- [ ] Health endpoint responds
- [ ] Can create async jobs
- [ ] Webhooks deliver successfully
- [ ] Metrics endpoint accessible
- [ ] Audio downloads work
- [ ] No errors in Railway logs

---

**🎉 You're ready to deploy! Follow the steps above and you'll be live in 5 minutes!**

**Questions?** Check DEPLOYMENT.md for more detailed information.
