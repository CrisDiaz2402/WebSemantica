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
    """Extractor de entidades nombradas usando spaCy"""
    
    def __init__(self, model_name: str = "es_core_news_sm"):
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            print(f"Modelo {model_name} no encontrado. Usando modelo en inglés...")
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                print("No se encontró ningún modelo de spaCy. Instalando modelo básico...")
                import subprocess
                import sys
                subprocess.check_call([sys.executable, '-m', 'spacy', 'download', 'en_core_web_sm'])
                self.nlp = spacy.load("en_core_web_sm")
        
        # Mapeo de etiquetas de spaCy a categorías personalizadas
        self.entity_mapping = {
            'PERSON': 'Persona',
            'PER': 'Persona',
            'ORG': 'Organización',
            'GPE': 'Ubicación',
            'LOC': 'Ubicación',
            'DATE': 'Fecha',
            'TIME': 'Tiempo',
            'MONEY': 'Dinero',
            'QUANTITY': 'Cantidad',
            'PRODUCT': 'Producto',
            'MISC': 'Misceláneo'
        }
    
    def extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extrae entidades nombradas del texto"""
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            entity_type = self.entity_mapping.get(ent.label_, ent.label_)
            entities.append({
                'text': ent.text,
                'label': entity_type,
                'start': ent.start_char,
                'end': ent.end_char,
                'confidence': 1.0  # spaCy no proporciona confianza directamente
            })
        
        return entities
    
    def extract_entities_by_type(self, text: str) -> Dict[str, List[str]]:
        """Extrae entidades agrupadas por tipo"""
        entities = self.extract_entities(text)
        grouped = defaultdict(list)
        
        for entity in entities:
            grouped[entity['label']].append(entity['text'])
        
        # Eliminar duplicados manteniendo el orden
        for label in grouped:
            grouped[label] = list(dict.fromkeys(grouped[label]))
        
        return dict(grouped)
    
    def extract_product_mentions(self, text: str) -> List[str]:
        """Extrae menciones específicas de productos usando patrones"""
        doc = self.nlp(text)
        products = []
        
        # Buscar patrones de productos
        product_patterns = [
            r'\b[A-Z][a-z]+\s+[A-Z0-9]+\b',  # iPhone 14, Galaxy S23
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z0-9]+\b',  # Samsung Galaxy S23
        ]
        
        import re
        for pattern in product_patterns:
            matches = re.findall(pattern, text)
            products.extend(matches)
        
        # También buscar entidades marcadas como PRODUCT
        for ent in doc.ents:
            if ent.label_ in ['PRODUCT', 'MISC'] and len(ent.text.split()) <= 3:
                products.append(ent.text)
        
        return list(set(products))  # Eliminar duplicados
    
    def extract_brands(self, text: str) -> List[str]:
        """Extrae marcas mencionadas en el texto"""
        # Lista de marcas conocidas (se puede expandir)
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
        
        # También buscar organizaciones que podrían ser marcas
        entities = self.extract_entities_by_type(text)
        if 'Organización' in entities:
            brands_found.extend(entities['Organización'])
        
        return list(set(brands_found))
    
    def analyze_review(self, review_text: str) -> Dict[str, any]:
        """Análisis completo de una reseña"""
        return {
            'entities': self.extract_entities_by_type(review_text),
            'products': self.extract_product_mentions(review_text),
            'brands': self.extract_brands(review_text),
            'all_entities': self.extract_entities(review_text)
        }
