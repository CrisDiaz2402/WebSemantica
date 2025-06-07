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
    """Semantic search system for reviews"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words=None,  # We'll handle stop words manually
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.8
        )
        self.document_vectors = None
        self.documents = []
        self.metadata = []
        
        # English stop words
        self.english_stopwords = {
            'the', 'and', 'is', 'in', 'to', 'of', 'a', 'for', 'it', 'on', 'with', 'as', 'this', 'that',
            'at', 'by', 'an', 'be', 'are', 'from', 'was', 'or', 'but', 'not', 'have', 'has', 'had',
            'they', 'you', 'we', 'he', 'she', 'his', 'her', 'their', 'them', 'our', 'us', 'were',
            'can', 'will', 'would', 'should', 'could', 'may', 'might', 'do', 'does', 'did', 'so',
            'if', 'about', 'which', 'who', 'whom', 'what', 'when', 'where', 'why', 'how', 'all',
            'any', 'some', 'no', 'more', 'most', 'other', 'such', 'only', 'own', 'same', 'than',
            'too', 'very', 'just', 'also', 'into', 'over', 'after', 'before', 'between', 'because',
            'while', 'during', 'each', 'few', 'many', 'both', 'every', 'either', 'neither'
        }
    
    def preprocess_text(self, text: str) -> str:
        """Preprocesses text for search"""
        # Lowercase
        text = text.lower()
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Normalize spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove stop words
        words = text.split()
        words = [word for word in words if word not in self.english_stopwords and len(word) > 2]
        
        return ' '.join(words)
    
    def index_documents(self, reviews: List[Dict[str, any]]):
        """Indexes documents for search"""
        self.documents = []
        self.metadata = []
        
        for review in reviews:
            # Combine review text with relevant metadata
            text_content = review.get('original_text', '')
            
            # Add entity and event info if available
            if 'entities' in review:
                for entity_type, entities in review['entities'].items():
                    text_content += ' ' + ' '.join(entities)
            
            if 'products' in review:
                text_content += ' ' + ' '.join(review['products'])
            
            if 'brands' in review:
                text_content += ' ' + ' '.join(review['brands'])
            
            # Preprocess text
            processed_text = self.preprocess_text(text_content)
            self.documents.append(processed_text)
            self.metadata.append(review)
        
        # Create TF-IDF vectors
        if self.documents:
            self.document_vectors = self.vectorizer.fit_transform(self.documents)
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, any]]:
        """Performs semantic search"""
        if self.document_vectors is None:
            return []
        
        # Preprocess query
        processed_query = self.preprocess_text(query)
        
        # Vectorize query
        query_vector = self.vectorizer.transform([processed_query])
        
        # Compute similarities
        similarities = cosine_similarity(query_vector, self.document_vectors).flatten()
        
        # Get top-k results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:  # Only include results with similarity > 0
                result = self.metadata[idx].copy()
                result['similarity_score'] = float(similarities[idx])
                result['matched_text'] = self.documents[idx]
                results.append(result)
        
        return results
    
    def search_by_product(self, product_name: str, top_k: int = 5) -> List[Dict[str, any]]:
        """Searches reviews for a specific product"""
        query = f"product {product_name} review opinion"
        return self.search(query, top_k)
    
    def search_by_sentiment(self, sentiment: str, top_k: int = 5) -> List[Dict[str, any]]:
        """Searches reviews by sentiment"""
        sentiment_queries = {
            'positive': 'excellent good great perfect recommended',
            'negative': 'bad terrible horrible defective disappointing',
            'neutral': 'average normal acceptable regular'
        }
        
        query = sentiment_queries.get(sentiment.lower(), sentiment)
        return self.search(query, top_k)
    
    def get_search_statistics(self) -> Dict[str, any]:
        """Gets search index statistics"""
        if self.document_vectors is None:
            return {'error': 'No documents indexed'}
        
        return {
            'total_documents': len(self.documents),
            'vocabulary_size': len(self.vectorizer.vocabulary_) if hasattr(self.vectorizer, 'vocabulary_') else 0,
            'average_document_length': np.mean([len(doc.split()) for doc in self.documents]) if self.documents else 0
        }