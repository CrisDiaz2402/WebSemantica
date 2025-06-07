#4. Event Extraction (Detectar eventos de compra, devoluciones, quejas)
#- Archivo: `Papelera\utils\event_extractor.py`
#- Llamado en: `Papelera\utils\main_processor.py` (dentro del método `process_single_review`).
#- ¿Qué Hace?: Define "disparadores" (triggers) de eventos (ej. "compré" para el evento 'compra', "devolví" para 'devolución'). 
#   ¬ El método `extract_events` escanea el texto en busca de estos disparadores y, si los encuentra, 
#     llama a `_create_event` para estructurar el evento, incluyendo el tipo, el disparador, el actor (usuario), 
#     el objeto (producto), el tiempo, la ubicación y el sentimiento asociado (determinado por `_extract_sentiment`).     
import spacy
import re
from typing import List, Dict, Tuple
from datetime import datetime

class EventExtractor:
    """Extractor of events from product reviews"""
    
    def __init__(self, model_name: str = "en_core_web_lg"):
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            import subprocess
            import sys
            subprocess.check_call([sys.executable, '-m', 'spacy', 'download', 'en_core_web_lg'])
            self.nlp = spacy.load("en_core_web_lg")
        
        # Define event types and their triggers (in English)
        self.event_triggers = {
            'purchase': ['bought', 'purchased', 'ordered', 'acquired', 'got'],
            'return': ['returned', 'sent back', 'exchanged', 'gave back'],
            'complaint': ['complain', 'complained', 'claim', 'protest', 'upset'],
            'recommendation': ['recommend', 'suggest', 'advise'],
            'failure': ['failed', 'broke', 'stopped working', 'does not work', 'defective'],
            'function': ['works well', 'works perfectly', 'operates correctly'],
            'delivery': ['arrived', 'received', 'delivered', 'came'],
            'rating': ['rate', 'score', 'value', 'give stars']
        }
        
        # Sentiment patterns in English
        self.sentiment_patterns = {
            'positive': ['excellent', 'good', 'great', 'perfect', 'amazing', 'recommended'],
            'negative': ['bad', 'terrible', 'horrible', 'defective', 'broken', 'disappointing'],
            'neutral': ['normal', 'average', 'acceptable', 'regular']
        }
    
    def extract_events(self, text: str, entities: Dict[str, any]) -> List[Dict[str, any]]:
        """Extracts events from text"""
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
        """Creates a structured event"""
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
        
        # Extract actor (person)
        persons = entities.get('Person', [])
        if persons:
            event['actor'] = persons[0]  # Take the first mentioned person
        
        # Extract object (product)
        products = entities.get('Product', []) + entities.get('products', [])
        if products:
            event['object'] = products[0]  # Take the first mentioned product
        
        # Extract time
        dates = entities.get('Date', [])
        if dates:
            event['time'] = dates[0]
        
        # Extract location
        locations = entities.get('Location', [])
        if locations:
            event['location'] = locations[0]
        
        return event
    
    def _extract_sentiment(self, text: str) -> str:
        """Extracts sentiment from text"""
        text_lower = text.lower()
        
        positive_count = sum(1 for word in self.sentiment_patterns['positive'] if word in text_lower)
        negative_count = sum(1 for word in self.sentiment_patterns['negative'] if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'