#1. Expresiones regulares (Encontrar menciones de precios, fechas, modelos.)
#- Archivo: `utils\regex_extractor.py`
#- Llamado en: `utils\main_processor.py` (dentro del método `process_single_review`).
#- ¿Qué Hace?: Define patrones de expresiones regulares (`self.patterns`) para identificar y extraer: 
#    ¬ precios (`extract_prices`), 
#    ¬ fechas (`extract_dates`), 
#    ¬ modelos (`extract_models`),
#    ¬ calificaciones (`extract_ratings`) 
#  del texto de las reseñas. También incluye una función `clean_text` para preprocesar el texto eliminando 
#  URLs, menciones, hashtags y normalizando espacios.

import re
import pandas as pd
from typing import List, Dict, Tuple

class RegexExtractor:
    """Pattern extractor using regular expressions for English data"""
    
    def __init__(self):
        # Regular expression patterns for English
        self.patterns = {
            'price': r'\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|usd|\$|pounds?|£|euros?|€)?',
            'date': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
            'model': r'\b([A-Z]{2,}\d+[A-Z0-9]*)\b|\b\w+\s*[Mm]odel\s*\w+\b',
            'rating': r'\b[1-5]\s*(?:stars?)\b|\b\d+/\d+\b|\b\d+\.\d+/\d+\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b(?:\+1\s*)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
        }
    
    def extract_prices(self, text: str) -> List[str]:
        """Extracts price mentions from text"""
        return re.findall(self.patterns['price'], text, re.IGNORECASE)
    
    def extract_dates(self, text: str) -> List[str]:
        """Extracts dates from text"""
        return re.findall(self.patterns['date'], text)
    
    def extract_models(self, text: str) -> List[str]:
        """Extracts product models from text"""
        return re.findall(self.patterns['model'], text)
    
    def extract_ratings(self, text: str) -> List[str]:
        """Extracts ratings from text"""
        return re.findall(self.patterns['rating'], text, re.IGNORECASE)
    
    def extract_all_patterns(self, text: str) -> Dict[str, List[str]]:
        """Extracts all patterns from text"""
        return {
            'prices': self.extract_prices(text),
            'dates': self.extract_dates(text),
            'models': self.extract_models(text),
            'ratings': self.extract_ratings(text)
        }
    
    def clean_text(self, text: str) -> str:
        """Cleans text by removing special characters"""
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*$$$$,]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove mentions and hashtags
        text = re.sub(r'@\w+|#\w+', '', text)
        
        # Normalize spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-]', '', text)
        
        return text.strip()
