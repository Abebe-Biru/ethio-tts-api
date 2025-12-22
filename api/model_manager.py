"""
Multi-language TTS model manager for handling different language models
"""

import torch
from transformers import VitsModel, AutoTokenizer
from typing import Dict, Optional, Tuple, List
import structlog
from pyrsistent import pmap
from glom import glom

log = structlog.get_logger()

class MultiLanguageModelManager:
    """Manages multiple TTS models for different languages"""
    
    def __init__(self, supported_languages: Dict[str, str]):
        self.supported_languages = supported_languages
        self.models: Dict[str, VitsModel] = {}
        self.tokenizers: Dict[str, AutoTokenizer] = {}
        self.configs: Dict[str, dict] = {}
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
    async def load_model(self, language: str) -> Tuple[VitsModel, AutoTokenizer, dict]:
        """Load model for specific language"""
        # Normalize language code
        language = self._normalize_language(language)
        
        if language in self.models:
            log.info("model_already_loaded", language=language)
            return self.models[language], self.tokenizers[language], self.configs[language]
        
        if language not in self.supported_languages:
            raise ValueError(f"Unsupported language: {language}")
        
        model_name = self.supported_languages[language]
        
        try:
            log.info("loading_model", language=language, model_name=model_name)
            
            # Load model and tokenizer
            log.info("loading_model_weights", language=language, model_name=model_name)
            
            # UNLOAD OTHER MODELS FIRST to save RAM on free tiers
            # This implements strict "Single Model Mode"
            current_loaded = list(self.models.keys())
            for loaded_lang in current_loaded:
                if loaded_lang != language:
                    log.info("unloading_other_model_for_memory", target_language=language, unloading=loaded_lang)
                    self.unload_model(loaded_lang)

            model = VitsModel.from_pretrained(model_name)
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            # Apply Dynamic Quantization (Float32 -> Int8)
            # This reduces model size by ~4x (150MB -> 40MB) and speeds up CPU inference
            log.info("quantizing_model", language=language)
            model = torch.quantization.quantize_dynamic(
                model,
                {torch.nn.Linear},
                dtype=torch.qint8
            )
            
            # Set to evaluation mode and move to device
            model.eval()
            model.to(self.device)
            
            # Create immutable config
            config = pmap(model.config.to_dict())
            
            # Store in cache
            self.models[language] = model
            self.tokenizers[language] = tokenizer
            self.configs[language] = config
            
            # Log model info
            sampling_rate = glom(config, 'sampling_rate', default='unknown')
            log.info(
                "model_loaded_successfully", 
                language=language,
                model_name=model_name,
                device=str(self.device), 
                sampling_rate=sampling_rate,
                quantized=True
            )
            
            return model, tokenizer, config
            
        except Exception as e:
            log.error("model_load_failed", language=language, model_name=model_name, error=str(e))
            raise RuntimeError(f"Failed to load {language} model: {e}")
    
    def get_model(self, language: str) -> Tuple[Optional[VitsModel], Optional[AutoTokenizer], Optional[dict]]:
        """Get loaded model for language (returns None if not loaded)"""
        language = self._normalize_language(language)
        
        if language not in self.models:
            return None, None, None
            
        return self.models[language], self.tokenizers[language], self.configs[language]
    
    def is_model_loaded(self, language: str) -> bool:
        """Check if model is loaded for language"""
        language = self._normalize_language(language)
        return language in self.models
    
    def get_loaded_languages(self) -> List[str]:
        """Get list of currently loaded languages"""
        return list(self.models.keys())
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get supported languages and their model names"""
        return self.supported_languages.copy()
    
    def _normalize_language(self, language: str) -> str:
        """Normalize language code to standard form"""
        language = language.lower().strip()
        
        # Map ISO codes to full names
        language_map = {
            "om": "oromo",
            "am": "amharic"
        }
        
        return language_map.get(language, language)
    
    def unload_model(self, language: str):
        """Unload model to free memory"""
        language = self._normalize_language(language)
        
        if language in self.models:
            del self.models[language]
            del self.tokenizers[language] 
            del self.configs[language]
            
            # Force garbage collection
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            log.info("model_unloaded", language=language)
    
    def get_memory_usage(self) -> Dict[str, Dict[str, any]]:
        """Get memory usage information"""
        usage = {}
        
        for language in self.models:
            model = self.models[language]
            
            # Calculate model parameters
            total_params = sum(p.numel() for p in model.parameters())
            trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
            
            usage[language] = {
                "total_parameters": total_params,
                "trainable_parameters": trainable_params,
                "model_size_mb": total_params * 4 / (1024 * 1024),  # Assuming float32
                "device": str(next(model.parameters()).device)
            }
        
        return usage