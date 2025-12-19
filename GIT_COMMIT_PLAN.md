# Git Commit Plan - Multi-Language TTS API

## Initial Repository Setup

```bash
# Initialize git repository
git init

# Add remote (replace with your actual repository URL)
git remote add origin https://github.com/yourusername/tts-api.git
```

---

## Commit Sequence (Execute in Order)

### Commit 1: Project Infrastructure & Configuration
**Purpose:** Base project setup, dependencies, and configuration files

```bash
git add pyproject.toml
git add requirements.txt
git add uv.lock
git add .env.example
git add .env.railway
git add .railway-env-template.txt
git add Dockerfile
git add railway.toml
git add Procfile
git add run.py
git add run_server.py

git commit -m "chore(infra): initialize project infrastructure

- Add Python dependencies (FastAPI, PyTorch, Transformers)
- Configure uv package manager
- Add Docker configuration for containerization
- Add Railway deployment configuration
- Add Procfile for platform deployment
- Configure environment variables template"
```

---

### Commit 2: Gitignore & Project Metadata
**Purpose:** Version control configuration

```bash
git add .gitignore

git commit -m "chore: add .gitignore for Python project

- Ignore Python cache files and bytecode
- Ignore virtual environments
- Ignore TTS cache and generated audio files
- Ignore IDE and OS specific files
- Ignore environment variables"
```

---

### Commit 3: Core API Configuration & Models
**Purpose:** Application configuration and data models

```bash
git add api/__init__.py
git add api/__main__.py
git add api/config.py
git add api/models.py

git commit -m "feat(core): add core API configuration and data models

- Implement Settings with Pydantic for configuration management
- Add multi-language support configuration (Oromo, Amharic)
- Define request/response models (TTSRequest, BatchTTSRequest)
- Add async job models (Job, JobStatus, AsyncTTSRequest)
- Configure CORS, webhook secrets, and server settings"
```

---

### Commit 4: TTS Model Manager & Utilities
**Purpose:** Multi-language TTS model management

```bash
git add api/model_manager.py
git add api/utils.py

git commit -m "feat(tts): implement multi-language TTS model manager

- Add MultiLanguageModelManager for handling multiple models
- Implement lazy loading for language models
- Add model caching and memory management
- Implement text chunking for long inputs
- Add retry logic for transient failures
- Support Oromo and Amharic languages with ISO code aliases"
```

---

### Commit 5: Async Job Management System
**Purpose:** Background job processing infrastructure

```bash
git add api/jobs.py
git add api/workers.py
git add api/storage.py

git commit -m "feat(jobs): implement async job processing system

Jobs Module:
- In-memory job storage with CRUD operations
- Job queue management (FIFO)
- Job status tracking (pending, processing, completed, failed, cancelled)
- Pagination support for job listing

Workers Module:
- Background worker with asyncio task
- Job processing with model loading
- Graceful shutdown handling
- Stuck job timeout detection (10 minutes)

Storage Module:
- Audio file storage management
- Automatic cleanup of old files (24-hour retention)
- Storage statistics tracking"
```

---

### Commit 6: Webhook Delivery System
**Purpose:** Secure webhook notifications

```bash
git add api/webhooks.py

git commit -m "feat(webhooks): add webhook delivery with HMAC signatures

- Implement HMAC-SHA256 signature generation
- Add signature verification for security
- Implement retry logic with exponential backoff (3 attempts)
- Track webhook delivery metrics
- Support webhook delivery status tracking
- Add timeout handling (10 seconds)"
```

---

### Commit 7: Middleware - Rate Limiting
**Purpose:** API rate limiting

```bash
git add api/middleware/__init__.py
git add api/middleware/rate_limit.py

git commit -m "feat(middleware): add rate limiting middleware

- Implement per-IP and per-API-key rate limiting
- Set limits: 60 requests/minute, 1000 requests/hour
- Add rate limit headers to responses
- Return 429 status with retry-after on limit exceeded
- Exclude health check endpoints from rate limiting"
```

---

### Commit 8: Middleware - API Key Authentication
**Purpose:** Optional API key authentication

```bash
git add api/middleware/api_key.py

git commit -m "feat(auth): add API key authentication middleware

- Implement APIKeyManager for key management
- Add key generation with secure random tokens
- Support key validation and revocation
- Add demo key for testing (demo_key_12345)
- Optional authentication (allows requests without keys)"
```

---

### Commit 9: Middleware - Prometheus Metrics
**Purpose:** Observability and monitoring

```bash
git add api/middleware/metrics.py

git commit -m "feat(metrics): add Prometheus metrics middleware

Request Metrics:
- Total requests by method, endpoint, status code
- Request duration histograms
- Active requests gauge
- Error count by type and endpoint

Job Metrics:
- Jobs created by language
- Job status distribution
- Job processing duration
- Queue length and pending jobs

Webhook Metrics:
- Delivery success/failure rates
- Retry attempts
- Delivery duration

Cache Metrics:
- Cache hits and misses by language"
```

---

### Commit 10: API v1 Routes
**Purpose:** Versioned API endpoints

```bash
git add api/v1/__init__.py
git add api/v1/routes.py

git commit -m "feat(routes): add v1 API endpoints

Synchronous Endpoints:
- GET /v1/health - Enhanced health check with model status
- GET /v1/languages - List supported and loaded languages
- POST /v1/languages/{language}/load - Preload language model
- POST /v1/tts - Generate speech with caching
- POST /v1/batch_tts - Batch speech generation

Async Job Endpoints:
- POST /v1/tts/async - Create async TTS job
- GET /v1/jobs/{job_id} - Get job status
- GET /v1/jobs - List jobs with pagination
- DELETE /v1/jobs/{job_id} - Cancel pending job
- GET /v1/download/{job_id} - Download generated audio

Features:
- API key support via X-API-Key header
- Enhanced error messages with structured responses
- Cache status headers (HIT/MISS)
- Language and API version headers"
```

---

### Commit 11: Main Application
**Purpose:** FastAPI application setup

```bash
git add api/main.py

git commit -m "feat(api): implement main FastAPI application

- Initialize FastAPI with v1 API structure
- Configure structured logging with structlog (JSON format)
- Add CORS middleware with configurable origins
- Integrate rate limiting middleware
- Integrate metrics middleware
- Setup model manager with lazy loading
- Initialize audio storage system
- Start background worker on startup
- Add root endpoint with API information
- Add /metrics endpoint for Prometheus
- Configure health checks and graceful shutdown"
```

---

### Commit 12: Legacy Backup
**Purpose:** Preserve old implementation

```bash
git add api/main_legacy_backup.py

git commit -m "chore: preserve legacy main.py as backup

- Keep old implementation for reference
- Will be removed after v1 is stable"
```

---

### Commit 13: Test Files - Phase Tests
**Purpose:** Comprehensive test suite

```bash
git add test_phase1_models.py
git add test_phase2_async_endpoint.py
git add test_phases_3_to_5.py
git add test_phase4_worker.py
git add test_phase6_webhooks.py
git add test_phase7_cancellation.py
git add test_phase8_metrics.py

git commit -m "test: add phased test suite for all features

Phase 1: Model loading and language support
Phase 2: Async endpoint creation
Phase 3-5: Rate limiting, API keys, and metrics
Phase 4: Background worker processing
Phase 6: Webhook delivery and signatures
Phase 7: Job cancellation
Phase 8: Prometheus metrics validation"
```

---

### Commit 14: Test Files - Integration Tests
**Purpose:** End-to-end testing

```bash
git add test_complete_api.py
git add test_complete_webhooks.py
git add test_v1_features.py
git add test_improved_metrics.py
git add test_quick.py

git commit -m "test: add integration and feature tests

- Complete API workflow tests
- Complete webhook integration tests
- V1 feature validation tests
- Improved metrics testing
- Quick smoke tests"
```

---

### Commit 15: Test Audio Files
**Purpose:** Test fixtures

```bash
git add test_amharic.wav
git add test_oromo.wav
git add test_verify.wav
git add test_complete_amharic_job_*.wav
git add test_complete_oromo_job_*.wav
git add test_worker_job_*.wav

git commit -m "test: add test audio fixtures

- Sample Oromo and Amharic audio files
- Generated test outputs for verification"
```

---

### Commit 16: Generated Audio Files (Optional - Usually Ignored)
**Purpose:** Example outputs (consider adding to .gitignore instead)

```bash
# Note: These should typically be in .gitignore
# Only commit if you want to preserve examples

git add async_audio/*.wav

git commit -m "chore: add example generated audio files

- Example async job outputs
- For demonstration purposes only
- Consider adding to .gitignore for production"
```

---

### Commit 17: Documentation - Main Guides
**Purpose:** User documentation

```bash
git add README.md
git add START_HERE.md
git add QUICK_START_V1.md

git commit -m "docs: add main project documentation

README.md:
- Project overview and features
- Quick start guide
- API endpoints reference
- Supported languages table
- Environment variables
- Docker support

START_HERE.md:
- 3-step quick start
- Web demo instructions
- Common tasks guide
- Troubleshooting section
- Learning path

QUICK_START_V1.md:
- V1 API quick start guide"
```

---

### Commit 18: Documentation - API Guides
**Purpose:** API reference documentation

```bash
git add API_V1_GUIDE.md
git add WEBHOOKS_GUIDE.md
git add MULTILANG_GUIDE.md

git commit -m "docs: add comprehensive API guides

API_V1_GUIDE.md:
- V1 features overview (auth, rate limiting, metrics)
- Migration guide from legacy to v1
- Rate limit best practices
- Prometheus monitoring setup

WEBHOOKS_GUIDE.md:
- Complete async jobs and webhooks guide
- Webhook security and signature verification
- Job lifecycle documentation
- Error handling guide
- Code examples (Python, Node.js)

MULTILANG_GUIDE.md:
- Multi-language support documentation
- Language-specific examples"
```

---

### Commit 19: Documentation - Deployment
**Purpose:** Deployment and operations guides

```bash
git add DEPLOYMENT.md
git add RAILWAY_DEPLOY.md
git add RAILWAY_TROUBLESHOOTING.md
git add READY_FOR_RAILWAY.md

git commit -m "docs: add deployment documentation

DEPLOYMENT.md:
- Complete deployment guide
- Railway quick start (5 minutes)
- Alternative platforms (Render, DigitalOcean, AWS, Fly.io)
- Pre-deployment checklist
- Environment variables reference
- Monitoring and alerts setup
- Scaling strategies
- Troubleshooting guide
- Cost estimates

RAILWAY_DEPLOY.md:
- Railway-specific deployment guide

RAILWAY_TROUBLESHOOTING.md:
- Railway troubleshooting tips

READY_FOR_RAILWAY.md:
- Railway deployment readiness checklist"
```

---

### Commit 20: Documentation - Project Summaries
**Purpose:** Project status and change documentation

```bash
git add CLEANUP_SUMMARY.md
git add UPGRADE_SUMMARY.md
git add METRICS_IMPROVEMENTS.md
git add TEST_RESULTS.md

git commit -m "docs: add project summaries and change logs

- Cleanup summary of refactoring work
- Upgrade summary for v1 migration
- Metrics improvements documentation
- Test results and coverage"
```

---

### Commit 21: Examples Directory
**Purpose:** Code examples for users

```bash
git add examples/

git commit -m "examples: add client examples and demos

- Multi-language web demo (HTML/JS)
- Python client examples
- Node.js client examples
- Integration examples"
```

---

### Commit 22: Cache Directories (Structure Only)
**Purpose:** Preserve directory structure

```bash
# Create .gitkeep files to preserve empty directories
echo "*" > tts_cache/.gitignore
echo "!.gitignore" >> tts_cache/.gitignore

echo "*" > async_audio/.gitignore
echo "!.gitignore" >> async_audio/.gitignore

git add tts_cache/.gitignore
git add async_audio/.gitignore

git commit -m "chore: add cache directory structure

- Add tts_cache for model caching
- Add async_audio for job outputs
- Configure to ignore contents but preserve structure"
```

---

### Commit 23: IDE Configuration (Optional)
**Purpose:** Share IDE settings

```bash
git add .vscode/
git add .kiro/

git commit -m "chore: add IDE configuration

- VSCode settings for Python development
- Kiro AI assistant configuration"
```

---

## Final Steps

```bash
# Review all commits
git log --oneline

# Create initial tag
git tag -a v2.0.0 -m "Release v2.0.0 - Multi-language TTS API with async jobs"

# Push to remote
git push -u origin main
git push --tags
```

---

## Alternative: Squashed History Approach

If you prefer a cleaner history with fewer commits:

```bash
# Commit 1: Core Infrastructure
git add pyproject.toml requirements.txt uv.lock Dockerfile railway.toml Procfile .gitignore
git commit -m "chore: initialize project infrastructure and configuration"

# Commit 2: Core Application
git add api/__init__.py api/__main__.py api/config.py api/models.py api/main.py
git commit -m "feat(core): implement core API with FastAPI and Pydantic models"

# Commit 3: TTS Engine
git add api/model_manager.py api/utils.py
git commit -m "feat(tts): implement multi-language TTS model manager"

# Commit 4: Async Jobs System
git add api/jobs.py api/workers.py api/storage.py api/webhooks.py
git commit -m "feat(jobs): implement async job processing with webhooks"

# Commit 5: Middleware
git add api/middleware/
git commit -m "feat(middleware): add authentication, rate limiting, and metrics"

# Commit 6: API Routes
git add api/v1/
git commit -m "feat(routes): add v1 API endpoints"

# Commit 7: Tests
git add test_*.py *.wav
git commit -m "test: add comprehensive test suite"

# Commit 8: Documentation
git add *.md
git commit -m "docs: add complete documentation"

# Commit 9: Examples
git add examples/
git commit -m "examples: add client examples and demos"
```

---

## Notes

1. **Audio Files**: Consider adding `*.wav` to `.gitignore` instead of committing them
2. **Cache Directories**: The `tts_cache/` and `async_audio/` should be in `.gitignore`
3. **Environment Files**: Never commit `.env` with secrets, only `.env.example`
4. **Legacy Files**: Remove `api/main_legacy_backup.py` after confirming v1 works
5. **Test Outputs**: Add test output files to `.gitignore`

---

## Recommended .gitignore Additions

```bash
# Add these to .gitignore
echo "" >> .gitignore
echo "# Test outputs" >> .gitignore
echo "test_*.wav" >> .gitignore
echo "async_audio/*.wav" >> .gitignore
echo "" >> .gitignore
echo "# Cache" >> .gitignore
echo "tts_cache/" >> .gitignore
echo "api/tts_cache/" >> .gitignore

git add .gitignore
git commit -m "chore: update .gitignore to exclude generated files"
```
