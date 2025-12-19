# Webhooks Guide - Async TTS API

Complete guide for using async TTS jobs with webhook notifications.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Webhook Security](#webhook-security)
- [Job Lifecycle](#job-lifecycle)
- [Error Handling](#error-handling)
- [Monitoring](#monitoring)
- [Examples](#examples)
- [Best Practices](#best-practices)

---

## Overview

The async TTS API allows you to submit long-running text-to-speech jobs and receive results via webhook notifications. This is ideal for:

- **Long texts** - Process large documents without timeout issues
- **Batch processing** - Submit multiple jobs and get notified when each completes
- **Background processing** - Don't block your application waiting for TTS generation
- **Reliable delivery** - Automatic retries ensure you receive notifications

### How It Works

```
1. You submit a job → API returns job_id immediately
2. Job processes in background → Your app continues working
3. Job completes → API sends webhook to your URL
4. You download the audio → Use the provided download link
```

---

## Quick Start

### 1. Create an Async Job

```bash
curl -X POST http://localhost:8001/v1/tts/async \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Akkam jirta? Maqaan koo Kiro jedhama.",
    "language": "oromo",
    "webhook_url": "https://your-app.com/webhook"
  }'
```

**Response:**
```json
{
  "job_id": "job_abc123def456",
  "status": "pending",
  "message": "Job created and queued for processing",
  "created_at": "2024-12-18T10:00:00Z"
}
```

### 2. Receive Webhook Notification

When the job completes, you'll receive a POST request at your webhook URL:

```json
{
  "job_id": "job_abc123def456",
  "status": "completed",
  "created_at": "2024-12-18T10:00:00Z",
  "completed_at": "2024-12-18T10:01:30Z",
  "audio_url": "/v1/download/job_abc123def456",
  "error_message": null,
  "language": "oromo",
  "text_length": 42
}
```

### 3. Download the Audio

```bash
curl -O http://localhost:8001/v1/download/job_abc123def456
```

---

## API Endpoints

### Create Async Job

**POST** `/v1/tts/async`

Create a new async TTS job.

**Request Body:**
```json
{
  "text": "Text to convert to speech",
  "language": "oromo",  // or "amharic", "om", "am"
  "webhook_url": "https://your-app.com/webhook"
}
```

**Response:** `202 Accepted`
```json
{
  "job_id": "job_abc123",
  "status": "pending",
  "message": "Job created and queued for processing",
  "created_at": "2024-12-18T10:00:00Z"
}
```

**Limits:**
- Text: 1-50,000 characters
- Max pending jobs: 100
- Rate limit: 10 jobs/minute

---

### Get Job Status

**GET** `/v1/jobs/{job_id}`

Check the status of a job.

**Response:** `200 OK`
```json
{
  "job_id": "job_abc123",
  "status": "completed",  // pending, processing, completed, failed, cancelled
  "created_at": "2024-12-18T10:00:00Z",
  "started_at": "2024-12-18T10:00:05Z",
  "completed_at": "2024-12-18T10:01:30Z",
  "audio_url": "/v1/download/job_abc123",
  "error_message": null
}
```

---

### List All Jobs

**GET** `/v1/jobs?page=1&page_size=20`

List all jobs with pagination.

**Query Parameters:**
- `page` - Page number (default: 1)
- `page_size` - Jobs per page (default: 20, max: 100)

**Response:** `200 OK`
```json
{
  "jobs": [...],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

---

### Cancel Job

**DELETE** `/v1/jobs/{job_id}`

Cancel a pending job.

**Response:** `200 OK`
```json
{
  "message": "Job cancelled successfully",
  "job_id": "job_abc123",
  "status": "cancelled",
  "cancelled_at": "2024-12-18T10:00:30Z"
}
```

**Note:** Only pending jobs can be cancelled. Processing/completed jobs return `409 Conflict`.

---

### Download Audio

**GET** `/v1/download/{job_id}`

Download the generated audio file.

**Response:** `200 OK`
- Content-Type: `audio/wav`
- Audio file in WAV format

**Note:** Audio files are automatically deleted after 24 hours.

---

## Webhook Security

All webhooks include HMAC-SHA256 signatures for verification.

### Webhook Headers

```
X-Webhook-Signature: sha256=abc123...
X-Webhook-Timestamp: 1702814400
X-Webhook-ID: job_abc123
X-Webhook-Attempt: 1
```

### Verifying Signatures (Python)

```python
import hmac
import hashlib
import json

def verify_webhook(payload_json, signature, timestamp, secret):
    """Verify webhook signature"""
    # Reconstruct the message
    message = f"{timestamp}.{payload_json}"
    
    # Generate expected signature
    expected = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures (timing-safe)
    return hmac.compare_digest(signature, f"sha256={expected}")

# Usage in Flask
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    signature = request.headers.get('X-Webhook-Signature')
    timestamp = request.headers.get('X-Webhook-Timestamp')
    payload_json = request.data.decode('utf-8')
    
    if not verify_webhook(payload_json, signature, timestamp, YOUR_SECRET):
        return 'Invalid signature', 401
    
    # Process webhook
    data = json.loads(payload_json)
    print(f"Job {data['job_id']} completed!")
    
    return 'OK', 200
```

### Verifying Signatures (Node.js)

```javascript
const crypto = require('crypto');

function verifyWebhook(payloadJson, signature, timestamp, secret) {
    // Reconstruct the message
    const message = `${timestamp}.${payloadJson}`;
    
    // Generate expected signature
    const expected = crypto
        .createHmac('sha256', secret)
        .update(message)
        .digest('hex');
    
    // Compare signatures (timing-safe)
    return crypto.timingSafeEqual(
        Buffer.from(signature),
        Buffer.from(`sha256=${expected}`)
    );
}

// Usage in Express
app.post('/webhook', (req, res) => {
    const signature = req.headers['x-webhook-signature'];
    const timestamp = req.headers['x-webhook-timestamp'];
    const payloadJson = JSON.stringify(req.body);
    
    if (!verifyWebhook(payloadJson, signature, timestamp, YOUR_SECRET)) {
        return res.status(401).send('Invalid signature');
    }
    
    // Process webhook
    console.log(`Job ${req.body.job_id} completed!`);
    
    res.send('OK');
});
```

### Getting Your Secret

The webhook secret is configured in your `.env` file:

```bash
WEBHOOK_SECRET=your-secret-key-here
```

**Important:** Keep this secret secure! Anyone with this secret can forge webhooks.

---

## Job Lifecycle

### Status Flow

```
pending → processing → completed
                    ↘ failed
                    ↘ cancelled
```

### Status Descriptions

| Status | Description | Can Cancel? |
|--------|-------------|-------------|
| `pending` | Job is queued, waiting to be processed | ✅ Yes |
| `processing` | Job is currently being processed | ❌ No |
| `completed` | Job completed successfully, audio available | ❌ No |
| `failed` | Job failed with error | ❌ No |
| `cancelled` | Job was cancelled by user | ❌ No |

### Typical Timeline

- **Job Creation:** < 500ms
- **Queue Wait:** 0-5 seconds (depends on queue length)
- **Processing:** 30-120 seconds (first time, model loading)
- **Processing:** 5-30 seconds (subsequent jobs, model cached)
- **Webhook Delivery:** < 10 seconds after completion

---

## Error Handling

### Common Errors

#### 400 Bad Request
```json
{
  "detail": {
    "error": "empty_text",
    "message": "Text input cannot be empty",
    "field": "text"
  }
}
```

**Causes:**
- Empty text
- Invalid language
- Invalid webhook URL format

---

#### 404 Not Found
```json
{
  "detail": {
    "error": "job_not_found",
    "message": "Job 'job_abc123' not found",
    "job_id": "job_abc123"
  }
}
```

**Causes:**
- Job ID doesn't exist
- Job was deleted

---

#### 409 Conflict
```json
{
  "detail": {
    "error": "cannot_cancel",
    "message": "Job cannot be cancelled. Current status: processing",
    "job_id": "job_abc123",
    "status": "processing",
    "reason": "Only pending jobs can be cancelled"
  }
}
```

**Causes:**
- Trying to cancel a non-pending job

---

#### 410 Gone
```json
{
  "detail": {
    "error": "audio_expired",
    "message": "Audio file has expired or been deleted",
    "job_id": "job_abc123",
    "note": "Audio files are automatically deleted after 24 hours"
  }
}
```

**Causes:**
- Audio file older than 24 hours
- Audio file was manually deleted

---

#### 429 Too Many Requests
```json
{
  "detail": {
    "error": "queue_full",
    "message": "Too many pending jobs. Please try again later.",
    "pending_jobs": 100,
    "max_pending": 100
  }
}
```

**Causes:**
- More than 100 pending jobs
- Rate limit exceeded (10 jobs/minute)

---

### Webhook Retry Logic

If webhook delivery fails, the API automatically retries:

- **Attempt 1:** Immediate
- **Attempt 2:** After 2 seconds
- **Attempt 3:** After 4 seconds
- **Attempt 4:** After 8 seconds (final)

**Success Codes:** 200, 201, 202, 204

**Failure:** After 3 retries, webhook is marked as failed (but job data is still available).

---

## Monitoring

### Prometheus Metrics

The API exposes Prometheus metrics at `/metrics`:

```bash
curl http://localhost:8001/metrics
```

### Key Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `tts_job_created_total` | Counter | Total jobs created by language |
| `tts_job_status_total` | Counter | Jobs by final status |
| `tts_job_processing_duration_seconds` | Histogram | Job processing time |
| `tts_job_queue_length` | Gauge | Current queue size |
| `tts_job_pending_total` | Gauge | Current pending jobs |
| `tts_webhook_delivery_total` | Counter | Webhook deliveries (success/failure) |
| `tts_webhook_retry_total` | Counter | Webhook retry attempts |
| `tts_webhook_delivery_duration_seconds` | Histogram | Webhook delivery time |

### Example Queries (PromQL)

```promql
# Average job processing time by language
rate(tts_job_processing_duration_seconds_sum[5m]) 
/ rate(tts_job_processing_duration_seconds_count[5m])

# Webhook success rate
rate(tts_webhook_delivery_total{status="success"}[5m]) 
/ rate(tts_webhook_delivery_total[5m])

# Current queue backlog
tts_job_queue_length
```

---

## Examples

### Complete Python Example

```python
import requests
import time
from flask import Flask, request

app = Flask(__name__)
API_URL = "http://localhost:8001"

# 1. Create async job
def create_job(text, language="oromo"):
    response = requests.post(
        f"{API_URL}/v1/tts/async",
        json={
            "text": text,
            "language": language,
            "webhook_url": "https://your-app.com/webhook"
        }
    )
    return response.json()

# 2. Webhook endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    
    if data['status'] == 'completed':
        # Download audio
        audio_url = f"{API_URL}{data['audio_url']}"
        audio_response = requests.get(audio_url)
        
        # Save audio
        with open(f"{data['job_id']}.wav", 'wb') as f:
            f.write(audio_response.content)
        
        print(f"✓ Audio saved: {data['job_id']}.wav")
    
    elif data['status'] == 'failed':
        print(f"✗ Job failed: {data['error_message']}")
    
    return 'OK', 200

# 3. Usage
if __name__ == '__main__':
    # Create job
    job = create_job("Akkam jirta?", "oromo")
    print(f"Job created: {job['job_id']}")
    
    # Start webhook server
    app.run(port=5000)
```

### Complete Node.js Example

```javascript
const express = require('express');
const axios = require('axios');
const fs = require('fs');

const app = express();
app.use(express.json());

const API_URL = 'http://localhost:8001';

// 1. Create async job
async function createJob(text, language = 'oromo') {
    const response = await axios.post(`${API_URL}/v1/tts/async`, {
        text,
        language,
        webhook_url: 'https://your-app.com/webhook'
    });
    return response.data;
}

// 2. Webhook endpoint
app.post('/webhook', async (req, res) => {
    const data = req.body;
    
    if (data.status === 'completed') {
        // Download audio
        const audioUrl = `${API_URL}${data.audio_url}`;
        const audioResponse = await axios.get(audioUrl, {
            responseType: 'arraybuffer'
        });
        
        // Save audio
        fs.writeFileSync(`${data.job_id}.wav`, audioResponse.data);
        console.log(`✓ Audio saved: ${data.job_id}.wav`);
    }
    
    else if (data.status === 'failed') {
        console.log(`✗ Job failed: ${data.error_message}`);
    }
    
    res.send('OK');
});

// 3. Usage
(async () => {
    // Create job
    const job = await createJob('Akkam jirta?', 'oromo');
    console.log(`Job created: ${job.job_id}`);
    
    // Start webhook server
    app.listen(5000, () => {
        console.log('Webhook server running on port 5000');
    });
})();
```

---

## Best Practices

### 1. Webhook Endpoint Design

✅ **DO:**
- Return 200-204 status codes quickly (< 5 seconds)
- Process webhooks asynchronously (queue for background processing)
- Verify webhook signatures
- Log all webhook deliveries
- Handle duplicate deliveries (idempotency)

❌ **DON'T:**
- Perform long-running operations in webhook handler
- Return error codes for temporary issues (we'll retry)
- Expose webhook endpoints without authentication
- Ignore signature verification

### 2. Error Handling

```python
# Good: Retry with exponential backoff
def check_job_status(job_id, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{API_URL}/v1/jobs/{job_id}")
            return response.json()
        except requests.RequestException:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise
```

### 3. Audio File Management

```python
# Download and save audio immediately
def download_audio(job_id):
    response = requests.get(f"{API_URL}/v1/download/{job_id}")
    
    if response.status_code == 200:
        # Save to permanent storage
        with open(f"audio/{job_id}.wav", 'wb') as f:
            f.write(response.content)
        return True
    
    elif response.status_code == 410:
        print("Audio expired (>24 hours old)")
        return False
```

### 4. Monitoring

```python
# Track job metrics
import time

start_time = time.time()
job = create_job(text, language)

# Poll until complete
while True:
    status = check_job_status(job['job_id'])
    
    if status['status'] in ['completed', 'failed']:
        duration = time.time() - start_time
        print(f"Job completed in {duration:.2f}s")
        break
    
    time.sleep(2)
```

### 5. Rate Limiting

```python
# Respect rate limits
import time
from collections import deque

class RateLimiter:
    def __init__(self, max_per_minute=10):
        self.max_per_minute = max_per_minute
        self.requests = deque()
    
    def wait_if_needed(self):
        now = time.time()
        
        # Remove old requests
        while self.requests and self.requests[0] < now - 60:
            self.requests.popleft()
        
        # Wait if at limit
        if len(self.requests) >= self.max_per_minute:
            sleep_time = 60 - (now - self.requests[0])
            time.sleep(sleep_time)
        
        self.requests.append(time.time())

# Usage
limiter = RateLimiter(max_per_minute=10)

for text in texts:
    limiter.wait_if_needed()
    create_job(text)
```

---

## Support

For issues or questions:
- Check the [API documentation](API_V1_GUIDE.md)
- Review [examples](examples/)
- Check server logs for errors
- Monitor `/metrics` endpoint

---

**Built with ❤️ for async TTS processing**
