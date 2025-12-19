# Oromo TTS API Examples

This directory contains comprehensive examples showing how to integrate the Oromo TTS API into various applications and platforms.

## 📁 Files Overview

### 🌐 Web Integration
- **`web_integration.html`** - Complete web application example with interactive UI
  - Real-time TTS generation
  - Audio playback controls
  - Caching system
  - Example Oromo texts
  - Error handling

### 🐍 Python Clients
- **`python_client.py`** - Comprehensive Python client with sync/async support
  - Synchronous and asynchronous clients
  - Batch processing
  - Audio playback integration
  - Interactive CLI mode
  - Performance testing

### 🟢 Node.js Client
- **`nodejs_client.js`** - Full-featured Node.js client
  - Promise-based API
  - Concurrent processing
  - Cross-platform audio playback
  - Performance benchmarking
  - Interactive mode

## 🚀 Quick Start

### Web Example
```bash
# Open the HTML file in your browser
open web_integration.html
# or
python -m http.server 8080
# Then visit: http://localhost:8080/web_integration.html
```

### Python Example
```bash
# Install dependencies
pip install requests aiohttp aiofiles pygame

# Run the example
python python_client.py
```

### Node.js Example
```bash
# Install dependencies
npm install axios fs-extra node-wav speaker

# Run the example
node nodejs_client.js
```

## 🎯 Example Features

### Basic Usage
- Health checking
- Single text-to-speech generation
- Audio file saving
- Error handling

### Advanced Features
- **Batch Processing**: Generate multiple speeches efficiently
- **Concurrent Processing**: Parallel generation for better performance
- **Caching**: Client-side caching to avoid duplicate requests
- **Audio Playback**: Cross-platform audio playback integration
- **Interactive Mode**: CLI interfaces for testing

### Performance Optimization
- Connection pooling
- Request batching
- Concurrent processing
- Caching strategies
- Error recovery

## 📊 Performance Comparison

The examples include performance testing to compare different approaches:

| Method | Speed | Use Case |
|--------|-------|----------|
| Sequential | Baseline | Simple, single requests |
| Concurrent | 2-4x faster | Multiple independent texts |
| Batch | 3-5x faster | Many texts, server-side optimization |

## 🔧 Configuration

### API Endpoint
All examples default to `http://localhost:8001` but can be configured:

```javascript
// JavaScript
const client = new OromoTTSClient('http://your-api-server:8001');
```

```python
# Python
client = OromoTTSClient('http://your-api-server:8001')
```

```javascript
// Node.js
const client = new OromoTTSClient('http://your-api-server:8001');
```

### Environment Variables
You can also use environment variables:

```bash
export OROMO_TTS_API_URL=http://your-api-server:8001
export OROMO_TTS_TIMEOUT=30000
```

## 🎵 Audio Playback

### Web Browsers
- Uses HTML5 Audio API
- Automatic playback (if allowed by browser)
- Download functionality

### Python
- **pygame**: Cross-platform audio playback
- **playsound**: Simple audio file playback
- **pydub**: Advanced audio processing

### Node.js
- **node-wav + speaker**: Direct audio buffer playback
- **System commands**: Platform-specific audio players
  - macOS: `afplay`
  - Linux: `aplay`
  - Windows: PowerShell Media.SoundPlayer

## 🛠️ Customization

### Adding New Languages
```python
# Extend the client for multiple languages
class MultiLanguageTTSClient(OromoTTSClient):
    def __init__(self, language='oromo'):
        if language == 'oromo':
            super().__init__('http://localhost:8001')
        elif language == 'amharic':
            super().__init__('http://localhost:8002')
        # Add more languages...
```

### Custom Audio Processing
```javascript
// Add audio effects or processing
class EnhancedTTSClient extends OromoTTSClient {
    async generateSpeechWithEffects(text, effects = {}) {
        const audioBuffer = await this.generateSpeech(text);
        
        if (effects.speed) {
            // Apply speed modification
            return this.changeSpeed(audioBuffer, effects.speed);
        }
        
        return audioBuffer;
    }
}
```

### Integration with UI Frameworks

#### React
```jsx
import { useState, useEffect } from 'react';

function OromoTTSComponent() {
    const [client] = useState(() => new OromoTTSClient());
    const [isLoading, setIsLoading] = useState(false);
    
    const handleSpeak = async (text) => {
        setIsLoading(true);
        try {
            const audioUrl = await client.generateSpeech(text);
            const audio = new Audio(audioUrl);
            await audio.play();
        } finally {
            setIsLoading(false);
        }
    };
    
    return (
        <div>
            <button onClick={() => handleSpeak("Akkam jirta?")} disabled={isLoading}>
                {isLoading ? 'Generating...' : 'Speak Oromo'}
            </button>
        </div>
    );
}
```

#### Vue.js
```vue
<template>
  <div>
    <button @click="speak" :disabled="loading">
      {{ loading ? 'Generating...' : 'Speak Oromo' }}
    </button>
  </div>
</template>

<script>
export default {
  data() {
    return {
      client: new OromoTTSClient(),
      loading: false
    };
  },
  methods: {
    async speak() {
      this.loading = true;
      try {
        const audioUrl = await this.client.generateSpeech("Akkam jirta?");
        const audio = new Audio(audioUrl);
        await audio.play();
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>
```

## 🐛 Troubleshooting

### Common Issues

1. **Connection Refused**
   ```bash
   # Check if API server is running
   curl http://localhost:8001/health
   ```

2. **Model Not Loaded**
   ```python
   # Wait for model to load
   import time
   while not client.check_health()['model_loaded']:
       print("Waiting for model to load...")
       time.sleep(5)
   ```

3. **Audio Playback Issues**
   ```bash
   # Install audio dependencies
   pip install pygame playsound
   npm install node-wav speaker
   ```

4. **CORS Issues (Web)**
   ```javascript
   // Make sure API server has CORS enabled
   // Check browser console for CORS errors
   ```

### Debug Mode
Enable debug logging in examples:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

```javascript
// Add debug flag to client
const client = new OromoTTSClient('http://localhost:8001', { debug: true });
```

## 📚 Additional Resources

- **API Documentation**: http://localhost:8001/docs
- **OpenAPI Schema**: http://localhost:8001/openapi.json
- **Health Check**: http://localhost:8001/health
- **Main Documentation**: ../README.md
- **Usage Examples**: ../USAGE_EXAMPLES.md

## 🤝 Contributing

To add new examples:

1. Create a new file in this directory
2. Follow the existing naming convention
3. Include comprehensive error handling
4. Add documentation and comments
5. Test with the API server
6. Update this README

## 📄 License

These examples are provided under the same license as the main project.