# 🚀 Quick Start - Your Upgraded API

## Step 1: Install Dependencies

```bash
uv sync
```

This installs the new `prometheus-client` package.

---

## Step 2: Start the Server

```bash
uv run uvicorn api.main:app --host 0.0.0.0 --port 8001
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

---

## Step 3: Test It Works

Open a new terminal and run:

```bash
# Test health
curl http://localhost:8001/v1/health

# Test TTS
curl -X POST http://localhost:8001/v1/tts \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo_key_12345" \
  -d '{"text":"Akkam jirta?", "language":"oromo"}' \
  --output test.wav

# Check metrics
curl http://localhost:8001/metrics
```

---

## Step 4: Run the Test Suite

```bash
uv run python test_v1_features.py
```

This will test all the new features!

---

## What's New?

1. **Rate Limiting** - 60 requests/min, 1000/hour
2. **API Keys** - Use `X-API-Key: demo_key_12345`
3. **Metrics** - Visit `/metrics` for Prometheus data
4. **Versioning** - Use `/v1/` endpoints
5. **Better Errors** - Helpful, structured error messages

---

## Quick Examples

### Python
```python
import requests

# With API key
response = requests.post(
    "http://localhost:8001/v1/tts",
    headers={"X-API-Key": "demo_key_12345"},
    json={"text": "Akkam jirta?", "language": "oromo"}
)

# Check rate limits
remaining = response.headers.get("X-RateLimit-Remaining-Minute")
print(f"Requests remaining: {remaining}")

# Save audio
with open("speech.wav", "wb") as f:
    f.write(response.content)
```

### JavaScript
```javascript
const response = await fetch('http://localhost:8001/v1/tts', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-API-Key': 'demo_key_12345'
    },
    body: JSON.stringify({
        text: 'Akkam jirta?',
        language: 'oromo'
    })
});

// Check rate limits
const remaining = response.headers.get('X-RateLimit-Remaining-Minute');
console.log(`Requests remaining: ${remaining}`);

// Play audio
const audioBlob = await response.blob();
const audioUrl = URL.createObjectURL(audioBlob);
const audio = new Audio(audioUrl);
audio.play();
```

### cURL
```bash
# Basic request
curl -X POST http://localhost:8001/v1/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello", "language":"oromo"}' \
  --output speech.wav

# With API key and verbose output
curl -v -X POST http://localhost:8001/v1/tts \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo_key_12345" \
  -d '{"text":"Akkam jirta?", "language":"oromo"}' \
  --output speech.wav
```

---

## Monitoring

### View Metrics
```bash
curl http://localhost:8001/metrics
```

### Set Up Grafana (Optional)

1. Install Prometheus:
```bash
docker run -d -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

2. Create `prometheus.yml`:
```yaml
scrape_configs:
  - job_name: 'tts-api'
    scrape_interval: 15s
    static_configs:
      - targets: ['host.docker.internal:8001']
```

3. Install Grafana:
```bash
docker run -d -p 3000:3000 grafana/grafana
```

4. Open http://localhost:3000 and add Prometheus as data source

---

## Troubleshooting

### "Module not found" error
```bash
uv sync
```

### "Port already in use"
```bash
# Change port
uv run uvicorn api.main:app --host 0.0.0.0 --port 8002
```

### Rate limit hit
Wait 60 seconds or use a different API key

---

## Next Steps

1. ✅ Read [UPGRADE_SUMMARY.md](UPGRADE_SUMMARY.md) for full details
2. ✅ Read [API_V1_GUIDE.md](API_V1_GUIDE.md) for usage examples
3. ✅ Set up monitoring with Prometheus/Grafana
4. ✅ Deploy to production!

---

**You're all set!** 🎉

Your API is now production-ready with enterprise features!
