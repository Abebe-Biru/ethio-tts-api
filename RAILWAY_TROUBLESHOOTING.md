# Railway Deployment - Complete Troubleshooting Guide

## ✅ FIXED: Import Error

**Error:** `ERROR: Error loading ASGI app. Could not import module "main".`

**Solution:** ✅ FIXED in `railway.toml` and `Procfile`
- Changed from: `uvicorn api.main:app`
- Changed to: `python -m uvicorn api.main:app`

**Action:** Push the updated files and Railway will auto-redeploy!

```bash
git add railway.toml Procfile
git commit -m "Fix: Update start command for Railway"
git push origin main
```

---

## 🚀 Quick Fixes for Common Railway Errors

### Error: "Could not import module"
**Fix:** Use `python -m uvicorn` instead of just `uvicorn`
✅ Already fixed in your files!

### Error: "Port already in use"
**Fix:** Railway sets `$PORT` automatically - don't hardcode port 8001
✅ Already using `$PORT` in your files!

### Error: "Module not found"
**Fix:** Make sure `api/__init__.py` exists
✅ Already exists in your project!

### Error: "No module named 'torch'"
**Fix:** Railway needs to install dependencies
✅ Your `pyproject.toml` has all dependencies!

### Error: "Out of memory"
**Fix:** Upgrade Railway plan to 1GB+ RAM
- Free tier: 512MB (might be tight)
- Hobby: 1GB (recommended)
- Pro: 8GB (for heavy usage)

---

## 📋 Deployment Checklist

### Before Pushing:
- [x] `railway.toml` - Fixed start command ✅
- [x] `Procfile` - Fixed start command ✅
- [x] `pyproject.toml` - All dependencies listed ✅
- [x] `api/__init__.py` - Exists ✅
- [x] `.gitignore` - Excludes unnecessary files ✅

### After Pushing:
- [ ] Railway auto-deploys (watch logs)
- [ ] Build completes (2-5 minutes)
- [ ] Server starts successfully
- [ ] Health check passes
- [ ] Test endpoints work

---

## 🔍 How to Check Railway Logs

1. Go to Railway dashboard
2. Click on your project
3. Click "Deployments" tab
4. Click latest deployment
5. Watch logs in real-time

**Look for:**
- ✅ "Application startup complete"
- ✅ "Uvicorn running on http://0.0.0.0:$PORT"
- ❌ Any ERROR messages

---

## 🧪 Test Your Deployment

Once deployed, run these tests:

```bash
# Set your Railway URL
export API_URL="https://your-app.up.railway.app"

# 1. Health check
curl $API_URL/v1/health

# Expected: {"status":"healthy","api_version":"v1",...}

# 2. Create async job
curl -X POST $API_URL/v1/tts/async \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Akkam jirta?",
    "language": "oromo",
    "webhook_url": "https://webhook.site/unique-id"
  }'

# Expected: {"job_id":"job_...","status":"pending",...}

# 3. Check metrics
curl $API_URL/metrics

# Expected: Prometheus metrics output
```

---

## 🐛 If Deployment Still Fails

### Step 1: Check Build Logs
Look for:
- Python version issues
- Missing dependencies
- Import errors

### Step 2: Check Runtime Logs
Look for:
- Port binding errors
- Module import errors
- Memory issues

### Step 3: Verify Environment Variables
Make sure these are set in Railway:
```
WEBHOOK_SECRET=<your-secret>
DEBUG=false
HOST=0.0.0.0
CORS_ORIGINS=*
```

### Step 4: Test Locally First
```bash
# Test the exact command Railway uses
python -m uvicorn api.main:app --host 0.0.0.0 --port 8001

# If this works locally, it should work on Railway
```

---

## 💡 Pro Tips

### Tip 1: Watch Logs During Deployment
```bash
# Railway CLI (optional)
railway logs
```

### Tip 2: First Request Takes Time
- Models download on first request (1-2 minutes)
- This is NORMAL - don't panic!
- Subsequent requests are fast

### Tip 3: Increase Timeout
If you get timeouts:
1. Go to Railway Settings
2. Increase "Health Check Timeout" to 300 seconds
3. Redeploy

### Tip 4: Monitor Memory
- Check Railway metrics tab
- If memory > 80%, upgrade plan
- PyTorch models need 2-4GB RAM

---

## ✅ Success Indicators

You'll know it's working when:
1. ✅ Build completes without errors
2. ✅ "Application startup complete" in logs
3. ✅ Health check returns 200 OK
4. ✅ Can create async jobs
5. ✅ Metrics endpoint accessible

---

## 🎯 Next Steps After Successful Deployment

1. **Test Everything**
   - Run all endpoints
   - Create test jobs
   - Verify webhooks work

2. **Monitor Performance**
   - Check Railway metrics
   - Monitor `/metrics` endpoint
   - Watch for errors

3. **Update Documentation**
   - Add Railway URL to README
   - Share with users

4. **Set Up Alerts**
   - Configure Railway notifications
   - Monitor health checks

---

## 📞 Still Having Issues?

1. **Check Railway Status**: https://status.railway.app
2. **Railway Docs**: https://docs.railway.app
3. **Your Logs**: Railway dashboard → Deployments → Logs
4. **Test Locally**: Make sure it works on your machine first

---

## 🚀 You're Almost There!

The fix is applied. Just push and Railway will redeploy:

```bash
git add .
git commit -m "Fix Railway deployment"
git push origin main
```

Watch the logs and you'll see it work! 🎉

---

**Built with ❤️ and debugged for Railway** 🚂
