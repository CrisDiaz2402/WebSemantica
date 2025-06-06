import spacy
import re
from typing import List, Dict, Tuple
from datetime import datetime

class EventExtractor:
    """Extractor de eventos de reseñas de productos"""
    
    def __init__(self, model_name: str = "es_core_news_sm"):
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                import subprocess
                import sys
                subprocess.check_call([sys.executable, '-m', 'spacy', 'download', 'en_core_web_sm'])
                self.nlp = spacy.load("en_core_web_sm")
        
        # Definir tipos de eventos y sus triggers
        self.event_triggers = {
            'compra': ['compré', 'compró', 'adquirí', 'pedí', 'ordené', 'conseguí'],
            'devolución': ['devolví', 'regresé', 'retorné', 'cambié'],
            'queja': ['me quejo', 'reclamo', 'protesto', 'molesto'],
            'recomendación': ['recomiendo', 'sugiero', 'aconsejo'],
            'fallo': ['falló', 'rompió', 'dejó de funcionar', 'no funciona', 'defectuoso'],
            'funcionamiento': ['funciona bien', 'trabaja perfectamente', 'opera correctamente'],
            'entrega': ['llegó', 'recibí', 'entregaron', 'arribó'],
            'calificación': ['califico', 'puntúo', 'valoro', 'doy estrellas']
        }
        
        # Patrones de sentimientos
        self.sentiment_patterns = {
            'positivo': ['excelente', 'bueno', 'genial', 'perfecto', 'increíble', 'recomendado'],
            'negativo': ['malo', 'terrible', 'horrible', 'defectuoso', 'roto', 'decepcionante'],
            'neutro': ['normal', 'regular', 'aceptable', 'promedio']
        }
    
    def extract_events(self, text: str, entities: Dict[str, any]) -> List[Dict[str, any]]:
        """Extrae eventos del texto"""
        events = []
        text_lower = text.lower()
        
        for event_type, triggers in self.event_triggers.items():
            for trigger in triggers:
                if trigger in text_lower:
                    event = self._create_event(text, trigger, event_type, entities)
                    if event:
                        events.append(event)
        
        return events
    
    def _create_event(self, text: str, trigger: str, event_type: str, entities: Dict[str, any]) -> Dict[str, any]:
        """Crea un evento estructurado"""
        event = {
            'type': event_type,
            'trigger': trigger,
            'actor': None,
            'object': None,
            'time': None,
            'location': None,
            'sentiment': self._extract_sentiment(text),
            'confidence': 0.7
        }
        
        # Extraer actor (persona)
        persons = entities.get('Persona', [])
        if persons:
            event['actor'] = persons[0]  # Tomar la primera persona mencionada
        
        # Extraer objeto (producto)
        products = entities.get('products', []) + entities.get('Producto', [])
        if products:
            event['object'] = products[0]  # Tomar el primer producto mencionado
        
        # Extraer tiempo
        dates = entities.get('Fecha', [])
        if dates:
            event['time'] = dates[0]
        
        # Extraer ubicación
        locations = entities.get('Ubicación', [])
        if locations:
            event['location'] = locations[0]
        
        return event
    
    def _extract_sentiment(self, text: str) -> str:
        """Extrae el sentimiento del texto"""
        text_lower = text.lower()
        
        positive_count = sum(1 for word in self.sentiment_patterns['positivo'] if word in text_lower)
        negative_count = sum(1 for word in self.sentiment_patterns['negativo'] if word in text_lower)
        
        if positive_count > negative_count:
            return 'positivo'
        elif negative_count > positive_count:
            return 'negativo'
        else:
            return 'neutro'
