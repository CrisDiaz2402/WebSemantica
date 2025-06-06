#3. Relationship Extraction (Determinar relaciones como (usuario, compró, producto))
#- Archivo: `Papelera\utils\relationship_extractor.py`
#- Llamado en: `Papelera\utils\main_processor.py` (dentro del método `process_single_review`).
#- ¿Qué Hace?: Utiliza `spaCy` para el análisis de dependencias sintácticas. 
#   ¬ El método `extract_subject_verb_object` identifica relaciones básicas Sujeto-Verbo-Objeto. 
#   ¬ El método `extract_purchase_relations` busca patrones específicos de compra (ej. verbos como "compré") 
#     y los relaciona con entidades de Persona y Producto previamente identificadas. 
#   ¬ El método `extract_all_relations` combina todas las relaciones encontradas.
import spacy
from typing import List, Dict, Tuple
import re

class RelationshipExtractor:
    """Extractor de relaciones entre entidades"""
    
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
        
        # Patrones de relaciones comunes
        self.relation_patterns = {
            'compra': ['compré', 'compró', 'adquirí', 'pedí', 'ordené'],
            'recomendación': ['recomiendo', 'recomendó', 'sugiero', 'aconsejo'],
            'fabricación': ['fabricado por', 'hecho por', 'de la marca', 'marca'],
            'ubicación': ['en', 'desde', 'ubicado en', 'de'],
            'tiempo': ['el', 'en', 'durante', 'hace'],
            'calificación': ['califico', 'puntúo', 'valoro', 'doy'],
            'problema': ['falló', 'roto', 'defectuoso', 'problema', 'error'],
            'funcionamiento': ['funciona', 'trabaja', 'opera', 'sirve']
        }
    
    def extract_subject_verb_object(self, text: str) -> List[Tuple[str, str, str]]:
        """Extrae relaciones sujeto-verbo-objeto básicas"""
        doc = self.nlp(text)
        relations = []
        
        for sent in doc.sents:
            # Buscar el verbo principal
            root_verb = None
            for token in sent:
                if token.dep_ == "ROOT" and token.pos_ == "VERB":
                    root_verb = token
                    break
            
            if root_verb:
                # Buscar sujeto
                subject = None
                for child in root_verb.children:
                    if child.dep_ in ["nsubj", "nsubjpass"]:
                        subject = self._get_full_phrase(child)
                        break
                
                # Buscar objeto
                obj = None
                for child in root_verb.children:
                    if child.dep_ in ["dobj", "pobj", "attr"]:
                        obj = self._get_full_phrase(child)
                        break
                
                if subject and obj:
                    relations.append((subject, root_verb.lemma_, obj))
        
        return relations
    
    def _get_full_phrase(self, token) -> str:
        """Obtiene la frase completa incluyendo modificadores"""
        phrase_tokens = [token]
        
        # Agregar modificadores a la izquierda
        for child in token.children:
            if child.dep_ in ["det", "amod", "compound", "nmod"]:
                phrase_tokens.append(child)
        
        # Ordenar por posición en el texto
        phrase_tokens.sort(key=lambda x: x.i)
        return " ".join([t.text for t in phrase_tokens])
    
    def extract_purchase_relations(self, text: str, entities: Dict[str, List[str]]) -> List[Dict[str, str]]:
        """Extrae relaciones específicas de compra"""
        relations = []
        text_lower = text.lower()
        
        # Buscar patrones de compra
        purchase_verbs = self.relation_patterns['compra']
        
        for verb in purchase_verbs:
            if verb in text_lower:
                # Intentar encontrar quién compró qué
                persons = entities.get('Persona', [])
                products = entities.get('Producto', []) + entities.get('products', [])
                
                for person in persons:
                    for product in products:
                        if person.lower() in text_lower and product.lower() in text_lower:
                            relations.append({
                                'subject': person,
                                'predicate': 'compró',
                                'object': product,
                                'confidence': 0.8
                            })
        
        return relations
    
    def extract_all_relations(self, text: str, entities: Dict[str, any]) -> List[Dict[str, str]]:
        """Extrae todas las relaciones posibles del texto"""
        all_relations = []
        
        # Relaciones básicas sujeto-verbo-objeto
        svo_relations = self.extract_subject_verb_object(text)
        for subj, verb, obj in svo_relations:
            all_relations.append({
                'subject': subj,
                'predicate': verb,
                'object': obj,
                'confidence': 0.5,
                'type': 'svo'
            })
        
        # Relaciones específicas
        all_relations.extend(self.extract_purchase_relations(text, entities))
        
        return all_relations
