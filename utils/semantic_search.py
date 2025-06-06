#5. Modelo de Recuperación (Permitir recuperar reseñas similares por producto o experiencia)
#- Archivo: `utils\semantic_search.py`
#- Llamado en: `utils\main_processor.py` (dentro del método:
#   ¬ `get_semantic_search_results`, 
#   ¬ `search_by_product`, 
#   ¬ `search_by_sentiment`). 
#  Estas funciones son a su vez llamadas por `app.py` (en las rutas: 
#   ¬ `/search`, `/search/sentiment/<sentiment>`, 
#   ¬ `/search/product/<product>`) 
#  y por `Papelera\static\js\main.js` y `Papelera\templates\dashboard.html` (para las búsquedas avanzadas).
#- ¿Qué Hace?: Implementa un sistema de búsqueda semántica utilizando `TfidfVectorizer` de `scikit-learn` para 
#   convertir el texto de las reseñas y las consultas en vectores numéricos. Luego, utiliza la `cosine_similarity` 
#   (similitud coseno) para encontrar reseñas que son semánticamente similares a una consulta. Incluye métodos específicos 
#   para buscar por producto (`search_by_product`) y por sentimiento (`search_by_sentiment`).

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
import re

class SemanticSearch:
    """Sistema de búsqueda semántica para reseñas"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words=None,  # Manejaremos stop words manualmente
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.8
        )
        self.document_vectors = None
        self.documents = []
        self.metadata = []
        
        # Stop words en español
        self.spanish_stopwords = {
            'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le',
            'da', 'su', 'por', 'son', 'con', 'para', 'al', 'del', 'los', 'las', 'una', 'pero',
            'sus', 'me', 'hasta', 'hay', 'donde', 'han', 'quien', 'están', 'estado', 'desde',
            'todo', 'nos', 'durante', 'todos', 'uno', 'les', 'ni', 'contra', 'otros', 'ese',
            'eso', 'ante', 'ellos', 'e', 'esto', 'mí', 'antes', 'algunos', 'qué', 'unos',
            'yo', 'otro', 'otras', 'otra', 'él', 'tanto', 'esa', 'estos', 'mucho', 'quienes',
            'nada', 'muchos', 'cual', 'poco', 'ella', 'estar', 'estas', 'algunas', 'algo',
            'nosotros', 'mi', 'mis', 'tú', 'te', 'ti', 'tu', 'tus', 'ellas', 'nosotras'
        }
    
    def preprocess_text(self, text: str) -> str:
        """Preprocesa el texto para búsqueda"""
        # Convertir a minúsculas
        text = text.lower()
        
        # Eliminar caracteres especiales pero mantener espacios
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Normalizar espacios
        text = re.sub(r'\s+', ' ', text)
        
        # Eliminar stop words
        words = text.split()
        words = [word for word in words if word not in self.spanish_stopwords and len(word) > 2]
        
        return ' '.join(words)
    
    def index_documents(self, reviews: List[Dict[str, any]]):
        """Indexa los documentos para búsqueda"""
        self.documents = []
        self.metadata = []
        
        for review in reviews:
            # Combinar texto de la reseña con metadatos relevantes
            text_content = review.get('original_text', '')
            
            # Añadir información de entidades y eventos si está disponible
            if 'entities' in review:
                for entity_type, entities in review['entities'].items():
                    text_content += ' ' + ' '.join(entities)
            
            if 'products' in review:
                text_content += ' ' + ' '.join(review['products'])
            
            if 'brands' in review:
                text_content += ' ' + ' '.join(review['brands'])
            
            # Preprocesar texto
            processed_text = self.preprocess_text(text_content)
            self.documents.append(processed_text)
            self.metadata.append(review)
        
        # Crear vectores TF-IDF
        if self.documents:
            self.document_vectors = self.vectorizer.fit_transform(self.documents)
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, any]]:
        """Realiza búsqueda semántica"""
        if self.document_vectors is None:
            return []
        
        # Preprocesar consulta
        processed_query = self.preprocess_text(query)
        
        # Vectorizar consulta
        query_vector = self.vectorizer.transform([processed_query])
        
        # Calcular similitudes
        similarities = cosine_similarity(query_vector, self.document_vectors).flatten()
        
        # Obtener top-k resultados
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:  # Solo incluir resultados con similitud > 0
                result = self.metadata[idx].copy()
                result['similarity_score'] = float(similarities[idx])
                result['matched_text'] = self.documents[idx]
                results.append(result)
        
        return results
    
    def search_by_product(self, product_name: str, top_k: int = 5) -> List[Dict[str, any]]:
        """Busca reseñas de un producto específico"""
        query = f"producto {product_name} reseña opinión"
        return self.search(query, top_k)
    
    def search_by_sentiment(self, sentiment: str, top_k: int = 5) -> List[Dict[str, any]]:
        """Busca reseñas por sentimiento"""
        sentiment_queries = {
            'positivo': 'excelente bueno genial perfecto recomendado',
            'negativo': 'malo terrible horrible defectuoso decepcionante',
            'neutro': 'normal regular aceptable promedio'
        }
        
        query = sentiment_queries.get(sentiment.lower(), sentiment)
        return self.search(query, top_k)
    
    def get_search_statistics(self) -> Dict[str, any]:
        """Obtiene estadísticas del índice de búsqueda"""
        if self.document_vectors is None:
            return {'error': 'No hay documentos indexados'}
        
        return {
            'total_documents': len(self.documents),
            'vocabulary_size': len(self.vectorizer.vocabulary_) if hasattr(self.vectorizer, 'vocabulary_') else 0,
            'average_document_length': np.mean([len(doc.split()) for doc in self.documents]) if self.documents else 0
        }
