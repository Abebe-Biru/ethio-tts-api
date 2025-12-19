# Multi-Language TTS Guide

Complete guide for using the multi-language Text-to-Speech API supporting Oromo and Amharic languages.

## 🌍 Overview

The Multi-Language TTS API now supports multiple languages with dynamic model loading and language-specific caching. This allows you to generate speech in different languages without restarting the service.

### Supported Languages

| Language | Code | ISO Code | Model |
|----------|------|----------|-------|
| Oromo | `oromo` | `om` | `facebook/mms-tts-orm` |
| Amharic | `amharic` | `am` | `facebook/mms-tts-amh` |

## 🚀 Quick Start

### 1. Start the Server

```bash
# Install dependencies
uv sync

# Start the server
uv run python start_server.py
```

The API will be available at `http://localhost:8001`

### 2. Test Multi-Language Support

```bash
# Run the multi-language test suite
uv run python test_multilang.py
```

### 3. Try the Web Demo

Open `examples/multilang_web_demo.html` in your browser for an interactive demo.

## 📋 API Endpoints

### Health Check with Language Status

```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "cache_size": 15,
  "supported_languages": ["oromo", "amharic"],
  "loaded_languages": ["oromo"],
  "default_language": "oromo"
}
```

### Get Language Information

```bash
GET /languages
```

**Response:**
```json
{
  "supported_languages": {
    "oromo": {
      "model_name": "facebook/mms-tts-orm",
      "loaded": true,
      "is_default": true
    },
    "amharic": {
      "model_name": "facebook/mms-tts-amh",
      "loaded": false,
      "is_default": false
    }
  },
  "default_language": "oromo",
  "loaded_count": 1,
  "total_count": 2
}
```

### Load Language Model

```bash
POST /languages/{language}/load
```

**Example:**
```bash
curl -X POST http://localhost:8001/languages/amharic/load
```

**Response:**
```json
{
  "message": "Model for 'amharic' loaded successfully"
}
```

### Generate Speech (Single)

```bash
POST /tts
```

**Request Body:**
```json
{
  "text": "Akkam jirta? Maqaan koo Yaadannoo dha.",
  "language": "oromo"
}
```

**Notes:**
- `language` parameter is optional (defaults to `oromo`)
- Supports both full names (`oromo`, `amharic`) and ISO codes (`om`, `am`)
- Returns WAV audio file

**Examples:**

```bash
# Oromo (default)
curl -X POST http://localhost:8001/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"Akkam jirta?"}' \
  --output oromo_speech.wav

# Oromo (explicit)
curl -X POST http://localhost:8001/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"Akkam jirta?", "language":"oromo"}' \
  --output oromo_speech.wav

# Amharic
curl -X POST http://localhost:8001/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"ሰላም! እንዴት ነህ?", "language":"amharic"}' \
  --output amharic_speech.wav

# Using ISO codes
curl -X POST http://localhost:8001/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"Baga nagaan dhuftan!", "language":"om"}' \
  --output oromo_speech.wav
```

### Generate Speech (Batch)

```bash
POST /batch_tts
```

**Request Body:**
```json
{
  "texts": [
    "Akkam jirta?",
    "Maqaan koo Yaadannoo dha.",
    "Ani Afaan Oromoo nan dubbadha."
  ],
  "language": "oromo"
}
```

**Response:**
```json
{
  "results": [
    {
      "hash": "abc123...",
      "audio_b64": "UklGRiQAAABXQVZFZm10..."
    },
    {
      "hash": "def456...",
      "audio_b64": "UklGRiQAAABXQVZFZm10..."
    }
  ]
}
```

## 💻 Client Examples

### Python Client

```python
import requests

class MultiLangTTSClient:
    def __init__(self, api_url="http://localhost:8001"):
        self.api_url = api_url
    
    def generate_speech(self, text, language="oromo", save_path=None):
        """Generate speech in specified language"""
        response = requests.post(
            f"{self.api_url}/tts",
            json={"text": text, "language": language}
        )
        response.raise_for_status()
        
        audio_data = response.content
        
        if save_path:
            with open(save_path, "wb") as f:
                f.write(audio_data)
        
        return audio_data
    
    def load_language(self, language):
        """Pre-load a language model"""
        response = requests.post(f"{self.api_url}/languages/{language}/load")
        return response.json()
    
    def get_languages(self):
        """Get supported languages and their status"""
        response = requests.get(f"{self.api_url}/languages")
        return response.json()

# Usage
client = MultiLangTTSClient()

# Check available languages
languages = client.get_languages()
print(f"Supported: {languages['supported_languages']}")

# Load Amharic model
client.load_language("amharic")

# Generate Oromo speech
client.generate_speech(
    "Akkam jirta? Maqaan koo Yaadannoo dha.",
    language="oromo",
    save_path="oromo_greeting.wav"
)

# Generate Amharic speech
client.generate_speech(
    "ሰላም! እንዴት ነህ? ስሜ ያዳንኖ ነው።",
    language="amharic",
    save_path="amharic_greeting.wav"
)
```

### JavaScript Client

```javascript
class MultiLangTTSClient {
    constructor(apiUrl = 'http://localhost:8001') {
        this.apiUrl = apiUrl;
    }
    
    async generateSpeech(text, language = 'oromo') {
        const response = await fetch(`${this.apiUrl}/tts`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, language })
        });
        
        if (!response.ok) {
            throw new Error('TTS generation failed');
        }
        
        const audioBlob = await response.blob();
        return URL.createObjectURL(audioBlob);
    }
    
    async loadLanguage(language) {
        const response = await fetch(`${this.apiUrl}/languages/${language}/load`, {
            method: 'POST'
        });
        return response.json();
    }
    
    async getLanguages() {
        const response = await fetch(`${this.apiUrl}/languages`);
        return response.json();
    }
}

// Usage
const client = new MultiLangTTSClient();

// Check available languages
const languages = await client.getLanguages();
console.log('Supported:', languages.supported_languages);

// Load Amharic model
await client.loadLanguage('amharic');

// Generate Oromo speech
const oromoAudioUrl = await client.generateSpeech(
    'Akkam jirta? Maqaan koo Yaadannoo dha.',
    'oromo'
);
const oromoAudio = new Audio(oromoAudioUrl);
oromoAudio.play();

// Generate Amharic speech
const amharicAudioUrl = await client.generateSpeech(
    'ሰላም! እንዴት ነህ? ስሜ ያዳንኖ ነው።',
    'amharic'
);
const amharicAudio = new Audio(amharicAudioUrl);
amharicAudio.play();
```

## 🏗️ Architecture

### Model Management

The `MultiLanguageModelManager` class handles:
- Dynamic model loading/unloading
- Language normalization (ISO codes → full names)
- Memory management
- Model caching

### Caching Strategy

- **Language-specific caching**: Each language has separate cache entries
- **Cache key format**: `waveform_{language}_{text_hash}`
- **Persistent storage**: DiskCache with SQLite backend
- **Automatic cache hits**: Same text in same language reuses cached audio

### Memory Optimization

- Models are loaded on-demand
- Only requested language models are kept in memory
- GPU memory is automatically managed
- Models can be unloaded to free resources

## 🔧 Configuration

### Environment Variables

```bash
# .env file
DEBUG=false
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
DEFAULT_LANGUAGE=oromo
CACHE_DIR=tts_cache
```

### Programmatic Configuration

```python
# api/config.py
class Settings(BaseSettings):
    supported_languages: Dict[str, str] = {
        "oromo": "facebook/mms-tts-orm",
        "amharic": "facebook/mms-tts-amh",
        # Add more languages here
    }
    
    default_language: str = "oromo"
```

## 📊 Performance

### Model Loading Times

| Language | First Load | Subsequent Requests |
|----------|-----------|---------------------|
| Oromo | 30-60s | <500ms |
| Amharic | 30-60s | <500ms |

### Memory Usage

| Configuration | Memory Usage |
|--------------|--------------|
| 1 model loaded | 2-3 GB |
| 2 models loaded | 4-6 GB |

### Optimization Tips

1. **Pre-load models**: Load all needed models at startup
2. **Use caching**: Leverage the built-in cache for repeated texts
3. **Batch processing**: Use `/batch_tts` for multiple texts
4. **GPU acceleration**: Use CUDA-enabled GPU for faster generation

## 🐛 Troubleshooting

### Model Not Loading

**Problem**: Model fails to load or takes too long

**Solutions**:
```bash
# Check available memory
free -h

# Check GPU availability
nvidia-smi

# Increase timeout in code
# api/main.py - increase wait time in startup_event
```

### Language Not Supported

**Problem**: Error "Unsupported language"

**Solutions**:
- Check supported languages: `GET /languages`
- Use correct language codes: `oromo`, `amharic`, `om`, `am`
- Add new language in `api/config.py`

### Cache Issues

**Problem**: Cache growing too large

**Solutions**:
```bash
# Clear cache directory
rm -rf tts_cache/*

# Or use API endpoint
curl -X POST http://localhost:8001/cache/clear
```

### Memory Issues

**Problem**: Out of memory errors

**Solutions**:
- Load only needed languages
- Reduce batch size
- Use CPU instead of GPU for smaller models
- Increase system swap space

## 🚀 Advanced Usage

### Adding New Languages

1. Find the MMS-TTS model on Hugging Face
2. Add to `api/config.py`:

```python
supported_languages: Dict[str, str] = {
    "oromo": "facebook/mms-tts-orm",
    "amharic": "facebook/mms-tts-amh",
    "somali": "facebook/mms-tts-som",  # New language
}
```

3. Restart the server
4. Load the new model: `POST /languages/somali/load`

### Custom Model Configuration

```python
# api/model_manager.py
class MultiLanguageModelManager:
    def __init__(self, supported_languages: Dict[str, str], device="auto"):
        self.device = self._get_device(device)
        # ... rest of initialization
    
    def _get_device(self, device):
        if device == "auto":
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
        return torch.device(device)
```

### Monitoring Model Usage

```python
# Get memory usage
response = requests.get("http://localhost:8001/models/memory")
print(response.json())

# Example output:
# {
#   "oromo": {
#     "total_parameters": 123456789,
#     "model_size_mb": 470.5,
#     "device": "cuda:0"
#   },
#   "amharic": {
#     "total_parameters": 123456789,
#     "model_size_mb": 470.5,
#     "device": "cuda:0"
#   }
# }
```

## 📚 Example Texts

### Oromo Examples

```
Akkam jirta? Nagaan jirta?
(How are you? Are you well?)

Maqaan koo Yaadannoo dha. Ani barsiisaa dha.
(My name is Yaadannoo. I am a teacher.)

Baga nagaan dhuftan! Otuu nagaan jiraattan.
(Welcome! May you live in peace.)

Afaan Oromoo dubbachuu nan danda'a.
(I can speak Oromo.)

Galatoomaa! Haa tanu.
(Thank you! Let's go.)
```

### Amharic Examples

```
ሰላም! እንዴት ነህ?
(Hello! How are you?)

ስሜ ያዳንኖ ነው። መምህር ነኝ።
(My name is Yaadannoo. I am a teacher.)

እንኳን ደህና መጣህ!
(Welcome!)

አማርኛ መናገር እችላለሁ።
(I can speak Amharic.)

አመሰግናለሁ! እንሂድ።
(Thank you! Let's go.)
```

## 🎯 Best Practices

1. **Pre-load models**: Load all needed models at startup for faster response
2. **Use language codes consistently**: Stick to either full names or ISO codes
3. **Implement caching**: Use client-side caching for frequently used phrases
4. **Monitor memory**: Keep track of memory usage when loading multiple models
5. **Handle errors gracefully**: Implement retry logic for model loading failures
6. **Test thoroughly**: Use the test suite to verify multi-language functionality

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the API documentation: `http://localhost:8001/docs`
3. Run the test suite: `python test_multilang.py`
4. Check logs for detailed error messages

---

**Version**: 2.0.0  
**Last Updated**: December 2024  
**Languages Supported**: Oromo, Amharic
