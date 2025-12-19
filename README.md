# Multi-Language TTS API

A FastAPI-based text-to-speech service supporting **Oromo** and **Amharic** languages using Meta's MMS-TTS models.

## Features

### Core Features
- **Multi-language support**: Oromo and Amharic TTS generation
- **Dynamic model loading**: Load language models on-demand
- **Language-specific caching**: Optimized caching per language
- **Batch processing**: Generate multiple speeches efficiently
- **Structured logging**: JSON-formatted logs with language context
- **Health monitoring**: Track loaded models and language status
- **CORS support**: Web-friendly API
- **Interactive web demo**: Try both languages in your browser

### Enterprise Features (v2.0+)
- **🔄 Async Jobs with Webhooks**: Submit long-running jobs and get notified when complete
- **🔐 API Key Authentication**: Optional authentication for tracking and rate limiting
- **⚡ Rate Limiting**: 60 requests/min, 1000/hour with automatic throttling
- **📊 Prometheus Metrics**: Comprehensive monitoring and observability
- **🎯 Job Management**: Create, track, cancel, and download async TTS jobs
- **🔒 Webhook Security**: HMAC-SHA256 signatures for webhook verification
- **📦 Audio Storage**: Automatic file management with 24-hour retention
- **♻️ Retry Logic**: Automatic webhook delivery retries with exponential backoff

## Quick Start

```bash
# Install dependencies
uv sync

# Test that everything is working
uv run python test_startup.py

# Start development server (with auto-reload)
uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Start production server
uv run uvicorn api.main:app --host 0.0.0.0 --port 8000

# Alternative: Run as Python module
uv run python -m api
```

The API will be available at:
- **API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs (debug mode only)

## API Endpoints

### Synchronous TTS (v1)
- `GET /v1/health` - Check API status and loaded models
- `GET /v1/languages` - List available and loaded languages
- `POST /v1/languages/{language}/load` - Preload a language model
- `POST /v1/tts` - Generate speech synchronously (< 10s)
- `POST /v1/batch_tts` - Generate multiple speeches in batch

### Asynchronous TTS with Webhooks (v1)
- `POST /v1/tts/async` - Create async job (returns immediately)
- `GET /v1/jobs/{job_id}` - Get job status
- `GET /v1/jobs` - List all jobs with pagination
- `DELETE /v1/jobs/{job_id}` - Cancel a pending job
- `GET /v1/download/{job_id}` - Download generated audio

### Monitoring
- `GET /` - API information and feature list
- `GET /metrics` - Prometheus metrics endpoint

**📖 Documentation:**
- [WEBHOOKS_GUIDE.md](WEBHOOKS_GUIDE.md) - Complete async jobs & webhooks guide
- [API_V1_GUIDE.md](API_V1_GUIDE.md) - Full API reference
- [QUICK_START_V1.md](QUICK_START_V1.md) - Quick start guide

## Supported Languages

| Language | Code | ISO Code | Model |
|----------|------|----------|-------|
| Oromo | `oromo` | `om` | `facebook/mms-tts-orm` |
| Amharic | `amharic` | `am` | `facebook/mms-tts-amh` |

See [MULTILANG_GUIDE.md](MULTILANG_GUIDE.md) for detailed multi-language documentation.

## Environment Variables

Create a `.env` file in the project root:

```bash
# Server Configuration
HOST=0.0.0.0
PORT=8001
DEBUG=false

# CORS Configuration
CORS_ORIGINS=*

# Webhook Configuration
WEBHOOK_SECRET=your-webhook-secret-key-change-in-production

# Cache Configuration
CACHE_DIR=tts_cache
```

See `.env.example` for all available options.

## Docker Support

```bash
# Build image
docker build -t oromo-tts-api .

# Run container
docker run -p 8000:8000 oromo-tts-api
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all dependencies are installed with `uv sync`
2. **Model Loading**: The first startup may take time to download the MMS-TTS model
3. **Memory Issues**: The PyTorch model requires significant RAM (2GB+)
4. **Port Conflicts**: Change the port if 8000 is already in use: `--port 8001`

### Testing

```bash
# Test synchronous TTS
curl -X POST http://localhost:8001/v1/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"Akkam jirta?", "language":"oromo"}' \
  --output oromo.wav

# Test async TTS with webhooks
curl -X POST http://localhost:8001/v1/tts/async \
  -H "Content-Type: application/json" \
  -d '{
    "text":"Akkam jirta? Maqaan koo Kiro jedhama.",
    "language":"oromo",
    "webhook_url":"https://your-app.com/webhook"
  }'

# Check job status
curl http://localhost:8001/v1/jobs/{job_id}

# Download audio
curl -O http://localhost:8001/v1/download/{job_id}

# Run comprehensive tests
uv run python test_phase4_worker.py      # Test async jobs
uv run python test_phase6_webhooks.py    # Test webhook security
uv run python test_phase7_cancellation.py # Test job cancellation
uv run python test_phase8_metrics.py     # Test metrics
```

### Web Demo

Open `examples/multilang_web_demo.html` in your browser for an interactive demo with both languages.