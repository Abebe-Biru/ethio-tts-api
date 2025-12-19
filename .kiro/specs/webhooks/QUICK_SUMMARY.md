# Webhooks Feature - Quick Summary

## 🎯 What We're Building

**Async TTS with Webhooks** - Users submit long TTS jobs, get immediate response, and receive results via webhook callback.

---

## 📋 10 Requirements (User Stories)

1. **Async Job Creation** - Submit jobs without waiting
2. **Job Status Tracking** - Check job progress
3. **Background Processing** - Process jobs asynchronously
4. **Webhook Delivery** - Notify users when done
5. **Webhook Security** - Verify webhook authenticity
6. **Audio Storage** - Store and serve audio files
7. **Job Cancellation** - Cancel pending jobs
8. **Error Handling** - Clear error messages
9. **Rate Limiting** - Prevent abuse
10. **Monitoring** - Track performance metrics

---

## 🏗️ Architecture (Simple View)

```
User → POST /v1/tts/async → Get job_id immediately
                ↓
        Background Worker processes job
                ↓
        POST to user's webhook_url with result
```

---

## 📁 Files We'll Create/Modify

**New Files:**
- `api/jobs.py` - Job management
- `api/workers.py` - Background worker
- `api/webhooks.py` - Webhook sending
- `api/storage.py` - File storage

**Modified Files:**
- `api/models.py` - Add Job models
- `api/v1/routes.py` - Add async endpoints
- `api/middleware/metrics.py` - Add webhook metrics

---

## 🚀 10 Implementation Phases

| Phase | What | Time |
|-------|------|------|
| 1 | Data Models & Storage | 30 min |
| 2 | Async Job Creation | 20 min |
| 3 | Job Status Endpoints | 15 min |
| 4 | Background Worker | 45 min |
| 5 | Audio File Storage | 20 min |
| 6 | Webhook Delivery | 30 min |
| 7 | Webhook Security | 25 min |
| 8 | Job Cancellation | 15 min |
| 9 | Metrics & Monitoring | 20 min |
| 10 | Testing & Docs | 30 min |

**Total: ~4 hours**

---

## 🎯 Key Endpoints

### New Endpoints:
```
POST   /v1/tts/async          - Create async job
GET    /v1/jobs/{job_id}      - Get job status
GET    /v1/jobs               - List all jobs
DELETE /v1/jobs/{job_id}      - Cancel job
GET    /v1/download/{job_id}  - Download audio
```

---

## 💡 How It Works (Example)

### 1. User Creates Job:
```bash
POST /v1/tts/async
{
  "text": "Very long text...",
  "language": "oromo",
  "webhook_url": "https://myapp.com/callback"
}

Response (immediate):
{
  "job_id": "job_abc123",
  "status": "pending",
  "message": "Job queued"
}
```

### 2. User Checks Status (Optional):
```bash
GET /v1/jobs/job_abc123

Response:
{
  "job_id": "job_abc123",
  "status": "processing",
  "created_at": "2024-12-17T10:00:00Z"
}
```

### 3. Webhook Delivered (Automatic):
```bash
POST https://myapp.com/callback
{
  "job_id": "job_abc123",
  "status": "completed",
  "audio_url": "https://api.com/download/job_abc123",
  "completed_at": "2024-12-17T10:02:30Z"
}
```

### 4. User Downloads Audio:
```bash
GET /v1/download/job_abc123
→ Returns audio file
```

---

## 🔐 Security (Webhook Signatures)

Every webhook includes:
```
X-Webhook-Signature: sha256=abc123...
X-Webhook-Timestamp: 1702814400
```

User verifies:
```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature == f"sha256={expected}"
```

---

## 📊 What Gets Tracked (Metrics)

- `webhook_delivery_total` - Success/failure count
- `webhook_retry_total` - Retry attempts
- `job_processing_duration_seconds` - How long jobs take
- `job_queue_length` - Current queue size
- `job_status_total` - Jobs by status

---

## ✅ Success Criteria

We're done when:
- ✅ Jobs create in < 500ms
- ✅ Webhooks deliver in < 10s
- ✅ 99% delivery success rate
- ✅ All tests pass
- ✅ Documentation complete

---

## 🎯 MVP Decisions

| Feature | MVP Choice | Future |
|---------|------------|--------|
| Storage | In-memory dict | Redis/PostgreSQL |
| Queue | asyncio.Queue | Redis Queue |
| Worker | Single async task | Multiple workers |
| Files | Local filesystem | S3/Cloud |
| Retries | 3 attempts | Configurable |

---

## 📚 Documentation We'll Create

1. **WEBHOOKS_GUIDE.md** - User guide with examples
2. **test_webhooks.py** - Comprehensive tests
3. **API docs** - Updated OpenAPI/Swagger

---

## 🚀 Ready to Build?

**Phase 1 starts with:**
- Creating Job data models
- Setting up in-memory storage
- Basic CRUD operations

**Estimated time:** 30 minutes

**Want to proceed?** 😄
