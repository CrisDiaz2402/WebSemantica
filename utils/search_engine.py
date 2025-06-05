import os
import string
from collections import defaultdict
from nltk.corpus import stopwords
import nltk

nltk.download('stopwords')

class SearchEngine:
    def __init__(self, documents_dir):
        self.documents_dir = documents_dir           # "/ruta/al/proyecto/documents"
        self.document_ids = {}                       # Diccionario vacío {}
        self.inverted_index = defaultdict(list)      # Diccionario con listas por defecto
        self.initialize_engine()                     # ¡LLAMADA INICIAL!
    
    def map_function(self, text):
        text = text.lower()
        tokens = text.split()
        tokens = [token.strip(string.punctuation) for token in tokens]
        stop_words = set(stopwords.words('spanish'))
        tokens = [token for token in tokens if token not in stop_words and token]
        return tokens
    
    def reduce_function(self, tokens, doc_id):
        doc_inverted_index = defaultdict(list)
        for token in tokens:
            doc_inverted_index[token].append(doc_id)
        return doc_inverted_index
    
    def initialize_engine(self):
        # Asignar IDs a los documentos
        for i, filename in enumerate(os.listdir(self.documents_dir), 1):
            self.document_ids[i] = filename
        
        # Construir índice invertido
        for doc_id, filename in self.document_ids.items():
            with open(os.path.join(self.documents_dir, filename), 'r', encoding='utf-8') as f:
                text = f.read()
            tokens = self.map_function(text)
            doc_index = self.reduce_function(tokens, doc_id)
            
            for token, doc_ids in doc_index.items():
                self.inverted_index[token].extend(doc_ids)
        
        # Eliminar duplicados
        for token in self.inverted_index:
            self.inverted_index[token] = list(set(self.inverted_index[token]))
    
    def search(self, query):
        query_terms = self.map_function(query.lower())
        
        # Obtener documentos relevantes
        doc_sets = []
        for term in query_terms:
            if term in self.inverted_index:
                doc_sets.append(set(self.inverted_index[term]))
        
        # Intersección (AND)
        relevant_docs = set.intersection(*doc_sets) if doc_sets else set()
        
        # Calcular ranking
        rankings = {}
        for doc_id in relevant_docs:
            filename = self.document_ids[doc_id]
            with open(os.path.join(self.documents_dir, filename), 'r', encoding='utf-8') as f:
                doc_text = f.read().lower()
            doc_terms = self.map_function(doc_text)
            score = sum(1 for term in query_terms if term in doc_terms)
            rankings[doc_id] = {
                'filename': filename,
                'content': doc_text,
                'score': score
            }
        
        # Ordenar resultados
        sorted_results = sorted(rankings.items(), key=lambda x: x[1]['score'], reverse=True)
        return sorted_results