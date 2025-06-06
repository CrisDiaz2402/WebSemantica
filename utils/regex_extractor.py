import re
import pandas as pd
from typing import List, Dict, Tuple

class RegexExtractor:
    """Extractor de patrones usando expresiones regulares"""
    
    def __init__(self):
        # Patrones de expresiones regulares
        self.patterns = {
            'precio': r'\$?\d+[.,]?\d*\s*(?:euros?|€|dollars?|\$|pesos?|soles?)',
            'fecha': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
            'modelo': r'\b[A-Z]\w*\s*\d+[A-Z]*\b|\b\w+\s*[Mm]odel\s*\w+\b',
            'calificacion': r'\b[1-5]\s*(?:estrellas?|stars?)\b|\b\d+/\d+\b|\b\d+\.\d+/\d+\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'telefono': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b|\b$$\d{3}$$\s*\d{3}[-.]?\d{4}\b'
        }
    
    def extract_prices(self, text: str) -> List[str]:
        """Extrae menciones de precios del texto"""
        return re.findall(self.patterns['precio'], text, re.IGNORECASE)
    
    def extract_dates(self, text: str) -> List[str]:
        """Extrae fechas del texto"""
        return re.findall(self.patterns['fecha'], text)
    
    def extract_models(self, text: str) -> List[str]:
        """Extrae modelos de productos del texto"""
        return re.findall(self.patterns['modelo'], text)
    
    def extract_ratings(self, text: str) -> List[str]:
        """Extrae calificaciones del texto"""
        return re.findall(self.patterns['calificacion'], text, re.IGNORECASE)
    
    def extract_all_patterns(self, text: str) -> Dict[str, List[str]]:
        """Extrae todos los patrones del texto"""
        return {
            'precios': self.extract_prices(text),
            'fechas': self.extract_dates(text),
            'modelos': self.extract_models(text),
            'calificaciones': self.extract_ratings(text)
        }
    
    def clean_text(self, text: str) -> str:
        """Limpia el texto eliminando caracteres especiales"""
        # Eliminar URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*$$$$,]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Eliminar menciones y hashtags
        text = re.sub(r'@\w+|#\w+', '', text)
        
        # Normalizar espacios
        text = re.sub(r'\s+', ' ', text)
        
        # Eliminar caracteres especiales pero mantener puntuación básica
        text = re.sub(r'[^\w\s.,!?;:()\-]', '', text)
        
        return text.strip()
