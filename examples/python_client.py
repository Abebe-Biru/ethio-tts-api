#!/usr/bin/env python3
"""
Comprehensive Python client example for Oromo TTS API
"""

import requests
import asyncio
import aiohttp
import aiofiles
import io
import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OromoTTSClient:
    """Synchronous client for Oromo TTS API"""
    
    def __init__(self, api_url: str = "http://localhost:8001", timeout: int = 30):
        self.api_url = api_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'OromoTTS-Python-Client/1.0'
        })
    
    def check_health(self) -> Dict:
        """Check API health status"""
        try:
            response = self.session.get(
                f"{self.api_url}/health", 
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Health check failed: {e}")
            raise
    
    def generate_speech(self, text: str, save_path: Optional[Union[str, Path]] = None) -> bytes:
        """
        Generate speech from text
        
        Args:
            text: Text to convert to speech
            save_path: Optional path to save the audio file
            
        Returns:
            Audio data as bytes
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            response = self.session.post(
                f"{self.api_url}/tts",
                json={"text": text},
                timeout=self.timeout
            )
            response.raise_for_status()
            
            audio_data = response.content
            
            if save_path:
                save_path = Path(save_path)
                save_path.parent.mkdir(parents=True, exist_ok=True)
                save_path.write_bytes(audio_data)
                logger.info(f"Audio saved to {save_path}")
            
            return audio_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"TTS generation failed: {e}")
            raise
    
    def batch_generate(self, texts: List[str]) -> Dict:
        """Generate speech for multiple texts"""
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        try:
            response = self.session.post(
                f"{self.api_url}/batch_tts",
                json={"texts": texts},
                timeout=self.timeout * 2  # Longer timeout for batch
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Batch TTS generation failed: {e}")
            raise
    
    def save_batch_results(self, batch_results: Dict, output_dir: Union[str, Path] = "batch_output"):
        """Save batch TTS results to files"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        saved_files = []
        for i, result in enumerate(batch_results.get("results", [])):
            # Decode base64 audio
            import base64
            audio_data = base64.b64decode(result["audio_b64"])
            
            # Save to file
            filename = f"audio_{result['hash'][:8]}.wav"
            filepath = output_dir / filename
            filepath.write_bytes(audio_data)
            saved_files.append(filepath)
            
            logger.info(f"Saved batch audio {i+1}: {filepath}")
        
        return saved_files
    
    def close(self):
        """Close the session"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

class AsyncOromoTTSClient:
    """Asynchronous client for Oromo TTS API"""
    
    def __init__(self, api_url: str = "http://localhost:8001", timeout: int = 30):
        self.api_url = api_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=self.timeout,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'OromoTTS-AsyncPython-Client/1.0'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def check_health(self) -> Dict:
        """Check API health status"""
        async with self.session.get(f"{self.api_url}/health") as response:
            response.raise_for_status()
            return await response.json()
    
    async def generate_speech(self, text: str, save_path: Optional[Union[str, Path]] = None) -> bytes:
        """Generate speech from text asynchronously"""
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        async with self.session.post(
            f"{self.api_url}/tts",
            json={"text": text}
        ) as response:
            response.raise_for_status()
            audio_data = await response.read()
            
            if save_path:
                save_path = Path(save_path)
                save_path.parent.mkdir(parents=True, exist_ok=True)
                async with aiofiles.open(save_path, 'wb') as f:
                    await f.write(audio_data)
                logger.info(f"Audio saved to {save_path}")
            
            return audio_data
    
    async def batch_generate(self, texts: List[str]) -> Dict:
        """Generate speech for multiple texts asynchronously"""
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        async with self.session.post(
            f"{self.api_url}/batch_tts",
            json={"texts": texts}
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    async def generate_multiple_concurrent(self, texts: List[str], output_dir: Union[str, Path] = "concurrent_output") -> List[Path]:
        """Generate multiple speeches concurrently"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        async def generate_single(i: int, text: str) -> Path:
            filename = f"audio_{i:03d}.wav"
            filepath = output_dir / filename
            await self.generate_speech(text, filepath)
            return filepath
        
        tasks = [generate_single(i, text) for i, text in enumerate(texts)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return successful results
        successful_results = [r for r in results if isinstance(r, Path)]
        logger.info(f"Generated {len(successful_results)}/{len(texts)} audio files")
        
        return successful_results

def play_audio_pygame(audio_data: bytes):
    """Play audio using pygame (requires: pip install pygame)"""
    try:
        import pygame
        pygame.mixer.init()
        
        # Load audio from bytes
        audio_buffer = io.BytesIO(audio_data)
        pygame.mixer.music.load(audio_buffer)
        pygame.mixer.music.play()
        
        # Wait for playback to finish
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)
            
        pygame.mixer.quit()
        
    except ImportError:
        logger.warning("pygame not installed. Install with: pip install pygame")
    except Exception as e:
        logger.error(f"Audio playback failed: {e}")

def play_audio_playsound(filepath: Union[str, Path]):
    """Play audio file using playsound (requires: pip install playsound)"""
    try:
        from playsound import playsound
        playsound(str(filepath))
    except ImportError:
        logger.warning("playsound not installed. Install with: pip install playsound")
    except Exception as e:
        logger.error(f"Audio playback failed: {e}")

# Example usage functions
def basic_example():
    """Basic synchronous usage example"""
    print("🧪 Basic TTS Example")
    
    with OromoTTSClient() as client:
        # Check health
        health = client.check_health()
        print(f"API Status: {health}")
        
        if not health.get("model_loaded"):
            print("❌ Model not loaded. Please wait for the API to initialize.")
            return
        
        # Generate speech
        text = "Akkam jirta? Maqaan koo Yaadannoo dha."
        print(f"Generating speech for: {text}")
        
        audio_data = client.generate_speech(text, "basic_example.wav")
        print(f"Generated {len(audio_data)} bytes of audio")
        
        # Try to play audio
        play_audio_pygame(audio_data)

def batch_example():
    """Batch processing example"""
    print("\n🧪 Batch TTS Example")
    
    with OromoTTSClient() as client:
        texts = [
            "Akkam jirta?",
            "Maqaan koo Yaadannoo dha.",
            "Ani Afaan Oromoo nan dubbadha.",
            "Baga nagaan dhuftan!",
            "Otuu nagaan jiraattan."
        ]
        
        print(f"Generating speech for {len(texts)} texts...")
        start_time = time.time()
        
        batch_results = client.batch_generate(texts)
        saved_files = client.save_batch_results(batch_results, "batch_example_output")
        
        end_time = time.time()
        print(f"Batch processing completed in {end_time - start_time:.2f} seconds")
        print(f"Saved {len(saved_files)} audio files")

async def async_example():
    """Asynchronous usage example"""
    print("\n🧪 Async TTS Example")
    
    async with AsyncOromoTTSClient() as client:
        # Check health
        health = await client.check_health()
        print(f"API Status: {health}")
        
        if not health.get("model_loaded"):
            print("❌ Model not loaded. Please wait for the API to initialize.")
            return
        
        # Generate multiple speeches concurrently
        texts = [
            "Akkam jirta?",
            "Nagaan jirta?",
            "Maqaan koo Yaadannoo dha.",
            "Ani barsiisaa dha."
        ]
        
        print(f"Generating {len(texts)} speeches concurrently...")
        start_time = time.time()
        
        saved_files = await client.generate_multiple_concurrent(texts, "async_example_output")
        
        end_time = time.time()
        print(f"Concurrent processing completed in {end_time - start_time:.2f} seconds")
        print(f"Generated {len(saved_files)} audio files")

def interactive_example():
    """Interactive CLI example"""
    print("\n🧪 Interactive TTS Example")
    print("Enter Oromo text (or 'quit' to exit):")
    
    with OromoTTSClient() as client:
        # Check health first
        try:
            health = client.check_health()
            if not health.get("model_loaded"):
                print("❌ Model not loaded. Please wait for the API to initialize.")
                return
        except Exception as e:
            print(f"❌ Cannot connect to API: {e}")
            return
        
        while True:
            try:
                text = input("\n📝 Enter text: ").strip()
                
                if text.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not text:
                    continue
                
                print("🔄 Generating speech...")
                audio_data = client.generate_speech(text)
                
                # Save with timestamp
                timestamp = int(time.time())
                filename = f"interactive_{timestamp}.wav"
                Path(filename).write_bytes(audio_data)
                
                print(f"✅ Audio saved as {filename}")
                
                # Try to play
                play_audio_pygame(audio_data)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    print("👋 Goodbye!")

if __name__ == "__main__":
    print("🎤 Oromo TTS Python Client Examples")
    print("=" * 50)
    
    # Run examples
    try:
        basic_example()
        batch_example()
        asyncio.run(async_example())
        
        # Ask if user wants interactive mode
        response = input("\n🤔 Run interactive mode? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            interactive_example()
            
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.exception("Unexpected error occurred")