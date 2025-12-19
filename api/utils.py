"""
Utility functions for TTS generation
"""
import torch
import io
import hashlib
import base64
import soundfile as sf
from boltons.iterutils import chunked
from glom import glom
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog

log = structlog.get_logger()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_waveform(inputs, model_instance):
    """Generate waveform with retry logic for transient failures."""
    with torch.no_grad():
        return model_instance(**inputs).waveform


async def get_model_for_language(language: str, model_manager, settings):
    """Get or load model for specified language"""
    # Check if model is already loaded
    model_instance, tokenizer_instance, config = model_manager.get_model(language)
    
    if model_instance is None:
        # Load model if not already loaded
        log.info("loading_model_for_request", language=language)
        model_instance, tokenizer_instance, config = await model_manager.load_model(language)
    
    return model_instance, tokenizer_instance, config


def sync_generate(text, language, model_manager):
    """Synchronous generation logic for offloading to thread."""
    # Get model for language (this will be called from thread, so we need the sync version)
    model_instance, tokenizer_instance, config = model_manager.get_model(language)
    
    if model_instance is None:
        raise RuntimeError(f"Model for language '{language}' is not loaded")
    
    # Use boltons for chunking if text is long
    words = text.split()
    if len(words) > 200:
        chunks = list(chunked(words, 200))
        processed_text = ' '.join([' '.join(chunk) for chunk in chunks])
        log.debug("text_chunked", original_len=len(words), chunks=len(chunks), language=language)
    else:
        processed_text = text
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    inputs = tokenizer_instance(processed_text, return_tensors="pt").to(device)
    output = generate_waveform(inputs, model_instance)
    waveform = output.squeeze().cpu().float().numpy()
    
    # Get sampling rate from config
    sampling_rate = glom(config, 'sampling_rate', default=16000)
    
    buffer = io.BytesIO()
    sf.write(buffer, waveform, sampling_rate, format="WAV")
    buffer.seek(0)
    return buffer


def process_single_text(text, language, model_manager, cache):
    """Wrapper for thread_map in batch processing."""
    buffer = sync_generate(text, language, model_manager)
    # Include language in cache key for language-specific caching
    text_hash = hashlib.md5(f"{language}:{text}".encode()).hexdigest()
    cache_key = f"waveform_{language}_{text_hash}"
    waveform_bytes = buffer.getvalue()
    cache[cache_key] = waveform_bytes
    return {"hash": text_hash, "audio_b64": base64.b64encode(waveform_bytes).decode('utf-8')}
