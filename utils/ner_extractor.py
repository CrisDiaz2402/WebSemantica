#2. NER (Identificar marcas, productos, ubicaciones, fechas.)
#- Archivo: `utils\ner_extractor.py`
#- Llamado en: `utils\main_processor.py` (dentro del método `process_single_review`).
#- ¿Qué Hace?: Utiliza la biblioteca `spaCy` para el Reconocimiento de Entidades Nombradas (NER). 
#  Carga un modelo de lenguaje (ej. `es_core_news_sm`) y proporciona métodos como:  
#    ¬ `extract_entities`: para identificar entidades generales, 
#    ¬ `extract_entities_by_type`: para agruparlas por categoría (Persona, Organización, Ubicación, Fecha, etc.), 
#    ¬ `extract_product_mentions` para identificar productos específicos y 
#    ¬ `extract_brands`: para reconocer marcas. 
#  El método `analyze_review` consolida todos estos resultados para una reseña.
  
import spacy
import pandas as pd
from typing import List, Dict, Tuple
from collections import defaultdict

class NERExtractor:
    """Named Entity Extractor using spaCy"""

    def __init__(self, model_name: str = "en_core_web_lg"):
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            print(f"Model {model_name} not found. Trying Spanish model...")
            try:
                self.nlp = spacy.load("es_core_news_lg")
            except OSError:
                print("No spaCy model found. Installing basic English model...")
                import subprocess
                import sys
                subprocess.check_call([sys.executable, '-m', 'spacy', 'download', 'en_core_web_lg'])
                self.nlp = spacy.load("en_core_web_lg")

        # Mapping spaCy labels to custom categories
        self.entity_mapping = {
            'PERSON': 'Person',
            'PER': 'Person',
            'ORG': 'Organization',
            'GPE': 'Location',
            'LOC': 'Location',
            'DATE': 'Date',
            'TIME': 'Time',
            'MONEY': 'Money',
            'QUANTITY': 'Quantity',
            'PRODUCT': 'Product',
            'MISC': 'Miscellaneous'
        }

    def extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract named entities from the text"""
        doc = self.nlp(text)
        entities = []

        for ent in doc.ents:
            entity_type = self.entity_mapping.get(ent.label_, ent.label_)
            entities.append({
                'text': ent.text,
                'label': entity_type,
                'start': ent.start_char,
                'end': ent.end_char,
                'confidence': 1.0  # spaCy does not provide confidence directly
            })

        return entities

    def extract_entities_by_type(self, text: str) -> Dict[str, List[str]]:
        """Extract entities grouped by type"""
        entities = self.extract_entities(text)
        grouped = defaultdict(list)

        for entity in entities:
            grouped[entity['label']].append(entity['text'])

        # Remove duplicates while preserving order
        for label in grouped:
            grouped[label] = list(dict.fromkeys(grouped[label]))

        return dict(grouped)

    def extract_product_mentions(self, text: str) -> List[str]:
        """Extract specific product mentions using patterns"""
        doc = self.nlp(text)
        products = []

        # Look for product patterns
        product_patterns = [
            r'\b[A-Z][a-z]+\s+[A-Z0-9]+\b',  # iPhone 14, Galaxy S23
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z0-9]+\b',  # Samsung Galaxy S23
        ]

        import re
        for pattern in product_patterns:
            matches = re.findall(pattern, text)
            products.extend(matches)

        # Also look for entities labeled as PRODUCT
        for ent in doc.ents:
            if ent.label_ in ['PRODUCT', 'MISC'] and len(ent.text.split()) <= 3:
                products.append(ent.text)

        return list(set(products))  # Remove duplicates

    def extract_brands(self, text: str) -> List[str]:
        """Extract brands mentioned in the text"""
        # List of known brands (can be expanded)
        known_brands = [
            'Apple', 'Samsung', 'Google', 'Microsoft', 'Sony', 'LG', 'Huawei',
            'Xiaomi', 'OnePlus', 'Nokia', 'Motorola', 'HP', 'Dell', 'Lenovo',
            'Asus', 'Acer', 'Nike', 'Adidas', 'Zara', 'H&M', 'Amazon', 'Netflix'
        ]

        brands_found = []
        text_lower = text.lower()

        for brand in known_brands:
            if brand.lower() in text_lower:
                brands_found.append(brand)

        # Also look for organizations that could be brands
        entities = self.extract_entities_by_type(text)
        if 'Organization' in entities:
            brands_found.extend(entities['Organization'])

        return list(set(brands_found))

    def analyze_review(self, review_text: str) -> Dict[str, any]:
        """Complete analysis of a review"""
        return {
            'entities': self.extract_entities_by_type(review_text),
            'products': self.extract_product_mentions(review_text),
            'brands': self.extract_brands(review_text),
            'all_entities': self.extract_entities(review_text)
        }