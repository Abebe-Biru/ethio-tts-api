# Webhooks Implementation Plan

## Overview

This document outlines the step-by-step implementation plan for adding webhook support to the TTS API.

## Architecture Overview

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ POST /v1/tts/async
       ↓
┌─────────────────────────────────┐
│      FastAPI Server             │
│  ┌──────────────────────────┐  │
│  │ Create Job               │  │
│  │ Store in DB              │  │
│  │ Add to Queue             │  │
│  │ Return job_id            │  │
│  └──────────────────────────┘  │
└─────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────┐
│   Background Worker             │
│  ┌──────────────────────────┐  │
│  │ Get job from queue       │  │
│  │ Generate TTS             │  │
│  │ Save audio file          │  │
│  │ Update job status        │  │
│  │ Send webhook             │  │
│  └──────────────────────────┘  │
└─────────────────────────────────┘
       │
       ↓
┌─────────────┐
│ User's      │
│ Webhook URL │
└─────────────┘
```

## File Structure

```
api/
├── jobs.py              # Job management (CRUD operations)
├── workers.py           # Background worker
├── webhooks.py          # Webhook sending logic
├── storage.py           # Audio file storage
├── models.py            # Add AsyncTTSRequest, Job models
└── v1/
    └── routes.py        # Add async endpoints
```

## Implementation Phases

### Phase 1: Data Models & Storage (Foundation)
**Time: 30 minutes**

Files to create/modify:
- `api/models.py` - Add AsyncTTSRequest, Job models
- `api/jobs.py` - Job storage and retrieval

What we'll build:
- Job data model with all fields
- In-memory job storage (dict-based for MVP)
- CRUD operations for jobs
- Job ID generation (UUID)

### Phase 2: Async Job Creation (API Endpoint)
**Time: 20 minutes**

Files to modify:
- `api/v1/routes.py` - Add POST /v1/tts/async endpoint

What we'll build:
- Async job creation endpoint
- Input validation (webhook_url format)
- Job queueing
- Immediate response with job_id

### Phase 3: Job Status Endpoints
**Time: 15 minutes**

Files to modify:
- `api/v1/routes.py` - Add GET /v1/jobs/{job_id} and GET /v1/jobs

What we'll build:
- Get single job status
- List all jobs (with pagination)
- Job not found handling

### Phase 4: Background Worker
**Time: 45 minutes**

Files to create:
- `api/workers.py` - Background job processor

What we'll build:
- Async worker that processes queue
- TTS generation integration
- Job status updates
- Error handling and retry logic
- Worker lifecycle management

### Phase 5: Audio File Storage
**Time: 20 minutes**

Files to create:
- `api/storage.py` - File storage management

What we'll build:
- Save audio files with job_id
- Generate download URLs
- File cleanup (24-hour expiration)
- Download endpoint

### Phase 6: Webhook Delivery
**Time: 30 minutes**

Files to create:
- `api/webhooks.py` - Webhook sending logic

What we'll build:
- HTTP POST to webhook_url
- Retry logic (3 attempts, exponential backoff)
- Success/failure tracking
- Timeout handling

### Phase 7: Webhook Security (Signatures)
**Time: 25 minutes**

Files to modify:
- `api/webhooks.py` - Add signature generation
- `api/config.py` - Add webhook secret

What we'll build:
- HMAC-SHA256 signature generation
- X-Webhook-Signature header
- Timestamp inclusion
- Verification example documentation

### Phase 8: Job Cancellation
**Time: 15 minutes**

Files to modify:
- `api/v1/routes.py` - Add DELETE /v1/jobs/{job_id}

What we'll build:
- Cancel pending jobs
- Prevent cancellation of processing jobs
- Webhook notification for cancelled jobs

### Phase 9: Metrics & Monitoring
**Time: 20 minutes**

Files to modify:
- `api/middleware/metrics.py` - Add webhook metrics

What we'll build:
- Webhook success/failure counters
- Job processing duration histogram
- Queue length gauge
- Retry count tracking

### Phase 10: Testing & Documentation
**Time: 30 minutes**

Files to create:
- `test_webhooks.py` - Comprehensive tests
- `WEBHOOKS_GUIDE.md` - User documentation

What we'll build:
- Test async job creation
- Test webhook delivery
- Test signature verification
- Test error scenarios
- User guide with examples

## Total Estimated Time: 4 hours

## Implementation Order

We'll implement in this order to ensure each piece builds on the previous:

1. ✅ **Phase 1: Data Models** - Foundation
2. ✅ **Phase 2: Job Creation** - Users can submit jobs
3. ✅ **Phase 3: Job Status** - Users can check status
4. ✅ **Phase 4: Background Worker** - Jobs get processed
5. ✅ **Phase 5: Storage** - Audio files are saved
6. ✅ **Phase 6: Webhooks** - Users get notified
7. ✅ **Phase 7: Security** - Webhooks are secure
8. ✅ **Phase 8: Cancellation** - Users can cancel
9. ✅ **Phase 9: Metrics** - We can monitor
10. ✅ **Phase 10: Testing** - Everything works

## Key Design Decisions

### 1. Storage: In-Memory vs Database
**Decision:** Start with in-memory (dict), easy to migrate to Redis/PostgreSQL later
**Rationale:** Faster MVP, simpler setup, good for learning

### 2. Queue: asyncio.Queue vs Redis
**Decision:** Use asyncio.Queue for MVP
**Rationale:** No external dependencies, sufficient for single-server deployment

### 3. Worker: Separate Process vs Same Process
**Decision:** Same process, separate async task
**Rationale:** Simpler deployment, easier debugging, good for MVP

### 4. File Storage: Local vs Cloud
**Decision:** Local filesystem for MVP
**Rationale:** No cloud setup needed, easy to test, can migrate to S3 later

### 5. Webhook Retries: Immediate vs Delayed
**Decision:** Exponential backoff (2s, 4s, 8s)
**Rationale:** Industry standard, gives temporary issues time to resolve

## Migration Path (Future)

When scaling beyond MVP:
1. **Storage:** dict → Redis → PostgreSQL
2. **Queue:** asyncio.Queue → Redis Queue → RabbitMQ
3. **Worker:** Single worker → Multiple workers → Celery
4. **Files:** Local → S3/Cloud Storage
5. **Webhooks:** Sync → Async with dedicated service

## Success Metrics

We'll know it's working when:
- ✅ Jobs are created in < 500ms
- ✅ Webhooks deliver in < 10s after completion
- ✅ 99% webhook delivery success rate
- ✅ Background worker processes 10+ jobs/min
- ✅ All tests pass
- ✅ Documentation is clear and complete

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Worker crashes | Auto-restart, job status timeout detection |
| Webhook endpoint down | Retry logic, failure tracking |
| Queue overflow | Rate limiting, max queue size |
| File storage full | Automatic cleanup, size limits |
| Memory leaks | Periodic worker restart, monitoring |

## Next Steps

1. Review this plan with you
2. Get approval to proceed
3. Start with Phase 1 (Data Models)
4. Implement phase by phase
5. Test after each phase
6. Deploy and celebrate! 🎉

---

**Ready to start implementing?** Let me know and we'll begin with Phase 1!
