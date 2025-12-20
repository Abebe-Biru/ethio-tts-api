# 🚀 Deploy to Railway NOW - Quick Steps

## Your Repository
**GitHub URL:** https://github.com/Abebe-Biru/ethio-tts-api

---

## Step 1: Go to Railway (2 minutes)

1. **Open Railway**: https://railway.app
2. **Click "Login"** → Sign in with GitHub
3. **Authorize Railway** to access your GitHub repos

---

## Step 2: Create New Project (1 minute)

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Search for: **"ethio-tts-api"**
4. Click on your repository
5. Click **"Deploy Now"**

Railway will automatically:
- ✅ Detect it's a Python project
- ✅ Read `railway.toml` for configuration
- ✅ Install dependencies from `pyproject.toml`
- ✅ Start your app with the command in `Procfile`

**Wait 2-3 minutes for the build to complete...**

---

## Step 3: Configure Environment Variables (1 minute)

Once deployed, click on your project, then:

1. Click **"Variables"** tab
2. Click **"+ New Variable"**
3. Add these variables:

```bash
WEBHOOK_SECRET=<paste-secret-below>
DEBUG=false
HOST=0.0.0.0
PORT=8001
CORS_ORIGINS=*
```

### Generate Webhook Secret:

Run this command in your terminal:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output and paste it as `WEBHOOK_SECRET` value.

4. Click **"Deploy"** to restart with new variables

---

## Step 4: Get Your URL (30 seconds)

1. Click **"Settings"** tab
2. Scroll to **"Domains"** section
3. Click **"Generate Domain"**
4. Copy your URL: `https://your-app-name.up.railway.app`

---

## Step 5: Test Your API (1 minute)

### Test Health Endpoint:
```bash
curl https://your-app-name.up.railway.app/v1/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "model_loaded": false,
  "supported_languages": ["oromo", "amharic", "om", "am"]
}
```

### Test TTS Generation:
```bash
curl -X POST https://your-app-name.up.railway.app/v1/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"Akkam jirta?", "language":"oromo"}' \
  --output test.wav
```

**Check the file:**
```bash
ls -lh test.wav
```

---

## 🎉 You're Live!

Your API is now deployed at:
```
https://your-app-name.up.railway.app
```

### View Logs:
1. Go to Railway dashboard
2. Click **"Deployments"** tab
3. Click on latest deployment
4. View real-time logs

### Monitor Metrics:
```bash
curl https://your-app-name.up.railway.app/metrics
```

---

## Troubleshooting

### If build fails:
1. Check logs in Railway dashboard
2. Verify `pyproject.toml` has all dependencies
3. Check that `railway.toml` is correct

### If app crashes:
1. Check logs for errors
2. Verify environment variables are set
3. Check that `PORT` is not hardcoded

### If models don't load:
- First request may take 1-2 minutes (downloading models)
- Be patient!
- Check logs for "model_loaded_successfully"

---

## Next Steps

- ✅ Test async jobs with webhooks
- ✅ Set up custom domain (optional)
- ✅ Monitor logs and metrics
- ✅ Share your API URL!

---

**Need help?** Check `RAILWAY_DEPLOYMENT_GUIDE.md` for detailed troubleshooting.
