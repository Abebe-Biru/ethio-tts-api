# API v1 Guide - Enhanced Features

## What's New in v1?

Your API just got a major upgrade! Here's what's new:

### 🔐 1. API Key Authentication (Optional)

**What it does:** Track and control who uses your API

**How to use:**
```bash
# Without API key (still works, but rate limited)
curl -X POST http://localhost:8001/v1/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"Akkam jirta?", "language":"oromo"}'

# With API key (better rate limits in future)
curl -X POST http://localhost:8001/v1/tts \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo_key_12345" \
  -d '{"text":"Akkam jirta?", "language":"oromo"}'
```

**Demo key for testing:** `demo_key_12345`

---

### ⚡ 2. Rate Limiting

**What it does:** Prevents API abuse and ensures fair usage

**Limits:**
- **60 requests per minute**
- **1000 requests per hour**

**Response when limit exceeded:**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded: 60 requests per minute",
  "limit": 60,
  "window": "minute",
  "retry_after_seconds": 60
}
```

**Check your limits:**
Look at response headers:
```
X-RateLimit-Limit-Minute: 60
X-RateLimit-Remaining-Minute: 45
X-RateLimit-Limit-Hour: 1000
X-RateLimit-Remaining-Hour: 892
```

---

### 📊 3. Prometheus Metrics

**What it does:** Monitor your API performance in real-time

**Access metrics:**
```bash
curl http://localhost:8001/metrics
```

**What you get:**
```
# Total requests
tts_api_requests_total{method="POST",endpoint="/v1/tts",status_code="200"} 1247

# Request duration
tts_api_request_duration_seconds_sum 2847.3
tts_api_request_duration_seconds_count 1247

# Cache performance
tts_cache_hits_total{language="oromo"} 892
tts_cache_misses_total{language="oromo"} 355

# Active requests
tts_api_active_requests 3

# Models loaded
tts_models_loaded 2

# Errors
tts_api_errors_total{error_type="HTTPException",endpoint="/v1/tts"} 12
```

**Visualize with Grafana:**
1. Install Prometheus and Grafana
2. Point Prometheus to `http://localhost:8001/metrics`
3. Create dashboards in Grafana
4. See beautiful graphs! 📈

---

### 🎯 4. API Versioning

**What it does:** Allows API evolution without breaking existing apps

**Endpoints:**

**V1 (New, Recommended):**
```
GET  /v1/health
GET  /v1/languages
POST /v1/languages/{language}/load
POST /v1/tts
POST /v1/batch_tts
```

**Legacy (Still works):**
```
GET  /health
GET  /languages
POST /languages/{language}/load
POST /tts
POST /batch_tts
```

**Why use v1?**
- Better error messages
- More response metadata
- Future-proof
- Enhanced headers (cache status, language, etc.)

---

### ✨ 5. Enhanced Responses

**V1 responses include more info:**

**Headers:**
```
X-Cache: HIT or MISS
X-Language: oromo
X-API-Version: v1
X-RateLimit-Remaining-Minute: 45
```

**Better error messages:**
```json
{
  "error": "empty_text",
  "message": "Text input cannot be empty",
  "field": "text"
}
```

**Batch responses include stats:**
```json
{
  "results": [...],
  "total": 10,
  "cached": 7,
  "generated": 3,
  "language": "oromo"
}
```

---

## Quick Start with v1

### 1. Check API Status
```bash
curl http://localhost:8001/v1/health
```

### 2. Generate Speech
```bash
curl -X POST http://localhost:8001/v1/tts \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo_key_12345" \
  -d '{"text":"Akkam jirta?", "language":"oromo"}' \
  --output speech.wav
```

### 3. Check Metrics
```bash
curl http://localhost:8001/metrics
```

### 4. Monitor Rate Limits
```bash
# Make a request and check headers
curl -i -X POST http://localhost:8001/v1/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello"}' \
  --output /dev/null

# Look for:
# X-RateLimit-Remaining-Minute: 59
# X-RateLimit-Remaining-Hour: 999
```

---

## Migration from Legacy to v1

**It's easy! Just change the URL:**

**Before:**
```python
response = requests.post(
    "http://localhost:8001/tts",
    json={"text": "Akkam jirta?", "language": "oromo"}
)
```

**After:**
```python
response = requests.post(
    "http://localhost:8001/v1/tts",  # Just add /v1
    headers={"X-API-Key": "demo_key_12345"},  # Optional
    json={"text": "Akkam jirta?", "language": "oromo"}
)

# Check rate limits
remaining = response.headers.get("X-RateLimit-Remaining-Minute")
print(f"Requests remaining this minute: {remaining}")
```

---

## Rate Limit Best Practices

### 1. Check Headers
```python
def make_tts_request(text, language="oromo"):
    response = requests.post(
        "http://localhost:8001/v1/tts",
        json={"text": text, "language": language}
    )
    
    # Check remaining requests
    remaining = int(response.headers.get("X-RateLimit-Remaining-Minute", 0))
    
    if remaining < 5:
        print(f"Warning: Only {remaining} requests left this minute!")
    
    return response
```

### 2. Handle 429 Errors
```python
import time

def make_tts_request_with_retry(text, language="oromo"):
    while True:
        response = requests.post(
            "http://localhost:8001/v1/tts",
            json={"text": text, "language": language}
        )
        
        if response.status_code == 429:
            # Rate limited
            retry_after = int(response.headers.get("Retry-After", 60))
            print(f"Rate limited. Waiting {retry_after} seconds...")
            time.sleep(retry_after)
            continue
        
        return response
```

### 3. Use API Keys
```python
# API keys will get higher rate limits in future
headers = {"X-API-Key": "your_api_key_here"}

response = requests.post(
    "http://localhost:8001/v1/tts",
    headers=headers,
    json={"text": "Akkam jirta?"}
)
```

---

## Monitoring with Prometheus

### Setup (Quick)

1. **Install Prometheus:**
```bash
# Download from https://prometheus.io/download/
# Or use Docker:
docker run -p 9090:9090 prom/prometheus
```

2. **Configure Prometheus** (`prometheus.yml`):
```yaml
scrape_configs:
  - job_name: 'tts-api'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8001']
```

3. **View metrics:**
- Open http://localhost:9090
- Query: `tts_api_requests_total`
- See graphs!

### Useful Queries

**Request rate:**
```
rate(tts_api_requests_total[5m])
```

**Average response time:**
```
rate(tts_api_request_duration_seconds_sum[5m]) / 
rate(tts_api_request_duration_seconds_count[5m])
```

**Cache hit rate:**
```
tts_cache_hits_total / 
(tts_cache_hits_total + tts_cache_misses_total)
```

**Error rate:**
```
rate(tts_api_errors_total[5m])
```

---

## What's Next?

Coming soon:
- **Webhooks** - For long-running jobs
- **Streaming responses** - Get audio as it generates
- **Higher API key tiers** - Premium users get more requests
- **Usage analytics** - See your usage patterns

---

## Summary

**You now have:**
- ✅ API versioning (`/v1/` endpoints)
- ✅ Rate limiting (60/min, 1000/hour)
- ✅ API key support (optional)
- ✅ Prometheus metrics
- ✅ Better error messages
- ✅ Enhanced response headers

**Your API is now production-ready and in the top 1% of APIs!** 🚀

---

**Questions?** Check the main README or explore the `/docs` endpoint (in debug mode).
