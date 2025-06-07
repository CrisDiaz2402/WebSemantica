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
    """Extractor of relations between entities"""

    def __init__(self, model_name: str = "en_core_web_lg"):
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            import subprocess
            import sys
            subprocess.check_call([sys.executable, '-m', 'spacy', 'download', 'en_core_web_lg'])
            self.nlp = spacy.load("en_core_web_lg")

        # Common relation patterns in English
        self.relation_patterns = {
            'purchase': ['bought', 'purchased', 'ordered', 'acquired'],
            'recommendation': ['recommend', 'suggest', 'advise'],
            'manufacture': ['manufactured by', 'made by', 'from brand', 'brand'],
            'location': ['in', 'from', 'located in', 'of'],
            'time': ['on', 'in', 'during', 'ago'],
            'rating': ['rate', 'score', 'value', 'give'],
            'problem': ['failed', 'broken', 'defective', 'problem', 'error'],
            'function': ['works', 'operates', 'serves', 'functions']
        }

    def extract_subject_verb_object(self, text: str) -> List[Tuple[str, str, str]]:
        """Extracts basic subject-verb-object relations"""
        doc = self.nlp(text)
        relations = []

        for sent in doc.sents:
            # Find the main verb
            root_verb = None
            for token in sent:
                if token.dep_ == "ROOT" and token.pos_ == "VERB":
                    root_verb = token
                    break

            if root_verb:
                # Find subject
                subject = None
                for child in root_verb.children:
                    if child.dep_ in ["nsubj", "nsubjpass"]:
                        subject = self._get_full_phrase(child)
                        break

                # Find object
                obj = None
                for child in root_verb.children:
                    if child.dep_ in ["dobj", "pobj", "attr"]:
                        obj = self._get_full_phrase(child)
                        break

                if subject and obj:
                    relations.append((subject, root_verb.lemma_, obj))

        return relations

    def _get_full_phrase(self, token) -> str:
        """Gets the full phrase including modifiers"""
        phrase_tokens = [token]

        # Add left modifiers
        for child in token.children:
            if child.dep_ in ["det", "amod", "compound", "nmod"]:
                phrase_tokens.append(child)

        # Sort by position in text
        phrase_tokens.sort(key=lambda x: x.i)
        return " ".join([t.text for t in phrase_tokens])

    def extract_purchase_relations(self, text: str, entities: Dict[str, List[str]]) -> List[Dict[str, str]]:
        """Extracts specific purchase relations"""
        relations = []
        text_lower = text.lower()

        # Look for purchase patterns
        purchase_verbs = self.relation_patterns['purchase']

        for verb in purchase_verbs:
            if verb in text_lower:
                # Try to find who bought what
                persons = entities.get('Person', [])  # English entity label
                products = entities.get('Product', []) + entities.get('products', [])

                for person in persons:
                    for product in products:
                        if person.lower() in text_lower and product.lower() in text_lower:
                            relations.append({
                                'subject': person,
                                'predicate': 'bought',
                                'object': product,
                                'confidence': 0.8
                            })

        return relations

    def extract_all_relations(self, text: str, entities: Dict[str, any]) -> List[Dict[str, str]]:
        """Extracts all possible relations from the text"""
        all_relations = []

        # Basic subject-verb-object relations
        svo_relations = self.extract_subject_verb_object(text)
        for subj, verb, obj in svo_relations:
            all_relations.append({
                'subject': subj,
                'predicate': verb,
                'object': obj,
                'confidence': 0.5,
                'type': 'svo'
            })

        # Specific relations
        all_relations.extend(self.extract_purchase_relations(text, entities))

        return all_relations