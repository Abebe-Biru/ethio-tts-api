# 🚀 START HERE - Multi-Language TTS API

Welcome! This guide will help you get started with the Multi-Language TTS API in just a few minutes.

---

## ⚡ Quick Start (3 Steps)

### 1️⃣ Start the Server
```bash
uv run python start_server.py
```

### 2️⃣ Test It Works
```bash
uv run python test_multilang.py
```

### 3️⃣ Try the Demo
```bash
uv run python quick_start.py
```

**That's it!** You're ready to use the API. 🎉

---

## 🌐 Try the Web Demo

Open in your browser:
```bash
open examples/multilang_web_demo.html
```

Or just double-click the file!

---

## 📖 What Can I Do?

### Generate Oromo Speech
```bash
curl -X POST http://localhost:8001/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"Akkam jirta?"}' \
  --output oromo.wav
```

### Generate Amharic Speech
```bash
curl -X POST http://localhost:8001/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"ሰላም!", "language":"amharic"}' \
  --output amharic.wav
```

### Check Available Languages
```bash
curl http://localhost:8001/languages
```

---

## 📚 Documentation Guide

**New to the project?** Start here:
1. 📖 [README.md](README.md) - Project overview
2. 🚀 [MULTILANG_GUIDE.md](MULTILANG_GUIDE.md) - Complete usage guide
3. 🎮 Try `quick_start.py` - Interactive demo

**Upgrading from v1.x?**
1. 🔄 [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - Step-by-step upgrade
2. 📋 [CHANGELOG.md](CHANGELOG.md) - What's new

**Want to understand the system?**
1. 🏗️ [ARCHITECTURE.md](ARCHITECTURE.md) - System design
2. 📊 [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Technical details

**Ready to deploy?**
1. 🚀 [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide
2. ✅ [COMPLETION_REPORT.md](COMPLETION_REPORT.md) - Production readiness

---

## 🎯 Common Tasks

### I want to...

#### ...generate speech in Python
```python
import requests

response = requests.post(
    "http://localhost:8001/tts",
    json={"text": "Akkam jirta?", "language": "oromo"}
)

with open("speech.wav", "wb") as f:
    f.write(response.content)
```

#### ...generate speech in JavaScript
```javascript
const response = await fetch('http://localhost:8001/tts', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text: 'Akkam jirta?', language: 'oromo'})
});

const audioBlob = await response.blob();
const audioUrl = URL.createObjectURL(audioBlob);
const audio = new Audio(audioUrl);
audio.play();
```

#### ...check if the API is running
```bash
curl http://localhost:8001/health
```

#### ...see all available endpoints
```bash
curl http://localhost:8001/
```

#### ...load a new language model
```bash
curl -X POST http://localhost:8001/languages/amharic/load
```

---

## 🆘 Troubleshooting

### Server won't start
```bash
# Check if dependencies are installed
uv sync

# Try starting again
uv run python start_server.py
```

### Can't connect to API
```bash
# Check if server is running
curl http://localhost:8001/health

# Check the port (default is 8001)
# If using different port, update your requests
```

### Model loading takes too long
- First load takes 30-60 seconds (downloading model)
- Subsequent requests are fast (<5 seconds)
- Be patient on first request!

### Out of memory
- Each model needs 2-3 GB RAM
- Loading both languages needs 4-6 GB
- Close other applications or use one language at a time

---

## 📞 Need Help?

### Documentation
- 📖 [MULTILANG_GUIDE.md](MULTILANG_GUIDE.md) - Comprehensive guide
- 🔄 [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - Upgrade help
- 🏗️ [ARCHITECTURE.md](ARCHITECTURE.md) - System design

### Examples
- 🎮 `quick_start.py` - Interactive demo
- 🌐 `examples/multilang_web_demo.html` - Web interface
- 🐍 `examples/python_client.py` - Python examples
- 🟢 `examples/nodejs_client.js` - Node.js examples

### Testing
- 🧪 `test_multilang.py` - Run all tests
- 🔍 `test_startup.py` - Check startup
- 🎯 `test_tts.py` - Test endpoints

---

## 🎓 Learning Path

### Beginner (5 minutes)
1. ✅ Run `quick_start.py`
2. ✅ Open web demo
3. ✅ Generate your first speech

### Intermediate (30 minutes)
1. ✅ Read [MULTILANG_GUIDE.md](MULTILANG_GUIDE.md)
2. ✅ Try Python/JavaScript examples
3. ✅ Explore API endpoints

### Advanced (1-2 hours)
1. ✅ Study [ARCHITECTURE.md](ARCHITECTURE.md)
2. ✅ Review source code
3. ✅ Customize for your needs

---

## 🌟 Features

### Supported Languages
| Language | Code | Example |
|----------|------|---------|
| Oromo | `oromo`, `om` | "Akkam jirta?" |
| Amharic | `amharic`, `am` | "ሰላም!" |

### Key Features
- ✅ Multi-language support
- ✅ Dynamic model loading
- ✅ Audio caching
- ✅ Batch processing
- ✅ Web interface
- ✅ REST API
- ✅ Docker support

---

## 🚀 Next Steps

### For Users
1. Try the web demo
2. Generate some speech
3. Integrate into your app

### For Developers
1. Read the architecture guide
2. Review the code
3. Extend with new languages

### For DevOps
1. Review deployment guide
2. Set up monitoring
3. Deploy to production

---

## 📋 Quick Reference

### API Endpoints
```
GET  /health                    - Health check
GET  /languages                 - List languages
POST /languages/{lang}/load     - Load model
POST /tts                       - Generate speech
POST /batch_tts                 - Batch generation
GET  /docs                      - API docs (DEBUG mode)
```

### Environment Variables
```bash
DEBUG=false                     # Enable debug mode
CORS_ORIGINS=*                  # CORS origins
DEFAULT_LANGUAGE=oromo          # Default language
CACHE_DIR=tts_cache            # Cache directory
```

### Commands
```bash
# Start server
uv run python start_server.py

# Run tests
uv run python test_multilang.py

# Quick demo
uv run python quick_start.py

# Docker
docker build -t tts-api .
docker run -p 8001:8001 tts-api
```

---

## ✅ Checklist

Before you start:
- [ ] Dependencies installed (`uv sync`)
- [ ] Server running (`start_server.py`)
- [ ] Health check passes (`curl /health`)

First steps:
- [ ] Run quick start demo
- [ ] Try web interface
- [ ] Generate test audio
- [ ] Read MULTILANG_GUIDE.md

Ready for production:
- [ ] Tests passing
- [ ] Documentation reviewed
- [ ] Deployment configured
- [ ] Monitoring set up

---

## 🎉 You're Ready!

Everything you need is here. Pick your path:

- 🎮 **Just want to try it?** → Run `quick_start.py`
- 🌐 **Prefer web interface?** → Open `multilang_web_demo.html`
- 📖 **Want to learn more?** → Read `MULTILANG_GUIDE.md`
- 🚀 **Ready to deploy?** → Check `DEPLOYMENT.md`

**Happy TTS generation!** 🎤

---

**Version**: 2.0.0  
**Status**: Production Ready ✅  
**Last Updated**: December 13, 2024
