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

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
import re
import math
from collections import Counter, defaultdict

class BM25:
    """
    Implementación de BM25 (Best Matching 25) para ranking de documentos
    """
    
    def __init__(self, k1: float = 1.2, b: float = 0.75):
        """
        Inicializa BM25 con parámetros estándar
        
        Args:
            k1: Controla la saturación de frecuencia de términos (típicamente 1.2-2.0)
            b: Controla la normalización por longitud del documento (típicamente 0.75)
        """
        self.k1 = k1
        self.b = b
        self.corpus = []
        self.doc_freqs = []
        self.idf = {}
        self.doc_len = []
        self.avgdl = 0
        self.N = 0
        
    def fit(self, corpus: List[List[str]]):
        """
        Entrena el modelo BM25 con el corpus de documentos
        
        Args:
            corpus: Lista de documentos, donde cada documento es una lista de tokens
        """
        self.corpus = corpus
        self.N = len(corpus)
        
        # Calcular longitudes de documentos
        self.doc_len = [len(doc) for doc in corpus]
        self.avgdl = sum(self.doc_len) / self.N if self.N > 0 else 0
        
        # Calcular frecuencias de documentos
        df = defaultdict(int)
        for doc in corpus:
            unique_tokens = set(doc)
            for token in unique_tokens:
                df[token] += 1
        
        # Calcular IDF para cada término
        self.idf = {}
        for token, freq in df.items():
            # Fórmula BM25 IDF: log((N - df + 0.5) / (df + 0.5))
            self.idf[token] = math.log((self.N - freq + 0.5) / (freq + 0.5))
        
        # Calcular frecuencias de términos por documento
        self.doc_freqs = []
        for doc in corpus:
            freq_dict = Counter(doc)
            self.doc_freqs.append(freq_dict)
    
    def get_scores(self, query: List[str]) -> np.ndarray:
        """
        Calcula scores BM25 para una consulta contra todos los documentos
        
        Args:
            query: Lista de tokens de la consulta
            
        Returns:
            Array numpy con scores BM25 para cada documento
        """
        scores = np.zeros(self.N)
        
        for i, doc_freq in enumerate(self.doc_freqs):
            score = 0
            doc_len = self.doc_len[i]
            
            for token in query:
                if token in doc_freq:
                    # Frecuencia del término en el documento
                    tf = doc_freq[token]
                    
                    # IDF del término
                    idf = self.idf.get(token, 0)
                    
                    # Fórmula BM25
                    numerator = tf * (self.k1 + 1)
                    denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl))
                    
                    score += idf * (numerator / denominator)
            
            scores[i] = score
        
        return scores
    
    def get_top_n(self, query: List[str], n: int = 5) -> List[Tuple[int, float]]:
        """
        Obtiene los top-n documentos más relevantes para una consulta
        
        Args:
            query: Lista de tokens de la consulta
            n: Número de documentos a retornar
            
        Returns:
            Lista de tuplas (índice_documento, score) ordenadas por score descendente
        """
        scores = self.get_scores(query)
        top_indices = np.argsort(scores)[::-1][:n]
        
        return [(int(idx), float(scores[idx])) for idx in top_indices if scores[idx] > 0]


class SemanticSearch:
    """Sistema de búsqueda semántica usando BM25"""
    
    def __init__(self, k1: float = 1.2, b: float = 0.75):
        """
        Inicializa el sistema de búsqueda con BM25
        
        Args:
            k1: Parámetro de saturación de BM25
            b: Parámetro de normalización por longitud de BM25
        """
        self.bm25 = BM25(k1=k1, b=b)
        self.documents = []
        self.metadata = []
        self.tokenized_docs = []
        
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
    
    def preprocess_text(self, text: str) -> List[str]:
        """
        Preprocesa texto y retorna lista de tokens
        
        Args:
            text: Texto a procesar
            
        Returns:
            Lista de tokens limpios
        """
        # Lowercase
        text = text.lower()
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Normalize spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Tokenize and remove stop words
        words = text.split()
        words = [word for word in words if word not in self.english_stopwords and len(word) > 2]
        
        return words
    
    def index_documents(self, reviews: List[Dict[str, any]]):
        """
        Indexa documentos para búsqueda usando BM25
        
        Args:
            reviews: Lista de reseñas procesadas
        """
        self.documents = []
        self.metadata = []
        self.tokenized_docs = []
        
        print(f"[BM25] Indexando {len(reviews)} documentos...")
        
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
            
            # Tokenize text
            tokens = self.preprocess_text(text_content)
            
            self.documents.append(text_content)
            self.tokenized_docs.append(tokens)
            self.metadata.append(review)
        
        # Entrenar modelo BM25
        if self.tokenized_docs:
            print("[BM25] Entrenando modelo BM25...")
            self.bm25.fit(self.tokenized_docs)
            print(f"[BM25] Modelo entrenado con {len(self.tokenized_docs)} documentos")
            print(f"[BM25] Vocabulario: {len(self.bm25.idf)} términos únicos")
            print(f"[BM25] Longitud promedio de documento: {self.bm25.avgdl:.2f} tokens")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, any]]:
        """
        Realiza búsqueda semántica usando BM25
        
        Args:
            query: Consulta de búsqueda
            top_k: Número de resultados a retornar
            
        Returns:
            Lista de documentos relevantes con scores BM25
        """
        if not self.tokenized_docs:
            print("[BM25] No hay documentos indexados")
            return []
        
        # Tokenizar consulta
        query_tokens = self.preprocess_text(query)
        
        if not query_tokens:
            print("[BM25] Consulta vacía después del preprocesamiento")
            return []
        
        print(f"[BM25] Buscando: {query}")
        print(f"[BM25] Tokens de consulta: {query_tokens}")
        
        # Obtener top-k resultados usando BM25
        top_results = self.bm25.get_top_n(query_tokens, top_k)
        
        results = []
        for idx, score in top_results:
            if score > 0:  # Solo incluir resultados con score positivo
                result = self.metadata[idx].copy()
                result['similarity_score'] = score
                result['bm25_score'] = score  # Score específico de BM25
                result['matched_text'] = ' '.join(self.tokenized_docs[idx][:100])  # Primeros 100 tokens
                result['query_tokens'] = query_tokens
                results.append(result)
        
        print(f"[BM25] Encontrados {len(results)} resultados relevantes")
        for i, result in enumerate(results[:3]):  # Mostrar top 3
            print(f"[BM25] #{i+1}: Score={result['bm25_score']:.4f}, ID={result.get('id', 'unknown')}")
        
        return results
    
    def search_by_product(self, product_name: str, top_k: int = 5) -> List[Dict[str, any]]:
        """
        Busca reseñas para un producto específico
        
        Args:
            product_name: Nombre del producto
            top_k: Número de resultados
            
        Returns:
            Lista de reseñas relevantes
        """
        # Expandir consulta con términos relacionados con productos
        query = f"product {product_name} review opinion experience quality"
        return self.search(query, top_k)
    
    def search_by_sentiment(self, sentiment: str, top_k: int = 5) -> List[Dict[str, any]]:
        """
        Busca reseñas por sentimiento usando BM25
        
        Args:
            sentiment: Sentimiento a buscar (positive, negative, neutral)
            top_k: Número de resultados
            
        Returns:
            Lista de reseñas con el sentimiento especificado
        """
        # Mapeo de sentimientos a términos de consulta expandidos
        sentiment_queries = {
            'positive': 'excellent good great perfect amazing wonderful fantastic outstanding recommended love best quality satisfied happy pleased',
            'negative': 'bad terrible horrible awful disappointing defective broken poor worst hate disappointed unsatisfied problem issue',
            'neutral': 'average normal acceptable regular okay standard typical moderate fair decent'
        }
        
        query = sentiment_queries.get(sentiment.lower(), sentiment)
        return self.search(query, top_k)
    
    def get_search_statistics(self) -> Dict[str, any]:
        """
        Obtiene estadísticas del índice de búsqueda BM25
        
        Returns:
            Diccionario con estadísticas del sistema
        """
        if not self.tokenized_docs:
            return {'error': 'No documents indexed'}
        
        # Calcular estadísticas adicionales
        vocab_size = len(self.bm25.idf)
        total_tokens = sum(len(doc) for doc in self.tokenized_docs)
        unique_tokens_per_doc = [len(set(doc)) for doc in self.tokenized_docs]
        
        return {
            'algorithm': 'BM25',
            'total_documents': len(self.tokenized_docs),
            'vocabulary_size': vocab_size,
            'total_tokens': total_tokens,
            'average_document_length': self.bm25.avgdl,
            'average_unique_tokens_per_doc': np.mean(unique_tokens_per_doc) if unique_tokens_per_doc else 0,
            'bm25_parameters': {
                'k1': self.bm25.k1,
                'b': self.bm25.b
            },
            'corpus_statistics': {
                'min_doc_length': min(self.bm25.doc_len) if self.bm25.doc_len else 0,
                'max_doc_length': max(self.bm25.doc_len) if self.bm25.doc_len else 0,
                'median_doc_length': np.median(self.bm25.doc_len) if self.bm25.doc_len else 0
            }
        }
    
    def tune_parameters(self, queries: List[str], relevance_judgments: List[List[int]], 
                       k1_range: Tuple[float, float] = (0.5, 3.0), 
                       b_range: Tuple[float, float] = (0.0, 1.0)) -> Dict[str, float]:
        """
        Optimiza parámetros BM25 usando consultas de prueba
        
        Args:
            queries: Lista de consultas de prueba
            relevance_judgments: Lista de listas con índices de documentos relevantes para cada consulta
            k1_range: Rango de valores para k1
            b_range: Rango de valores para b
            
        Returns:
            Mejores parámetros encontrados
        """
        best_score = 0
        best_params = {'k1': self.bm25.k1, 'b': self.bm25.b}
        
        # Grid search simple
        k1_values = np.arange(k1_range[0], k1_range[1], 0.2)
        b_values = np.arange(b_range[0], b_range[1], 0.1)
        
        for k1 in k1_values:
            for b in b_values:
                # Crear nuevo modelo BM25 con parámetros de prueba
                test_bm25 = BM25(k1=k1, b=b)
                test_bm25.fit(self.tokenized_docs)
                
                total_score = 0
                for query, relevant_docs in zip(queries, relevance_judgments):
                    query_tokens = self.preprocess_text(query)
                    top_results = test_bm25.get_top_n(query_tokens, len(relevant_docs))
                    
                    # Calcular precisión simple
                    retrieved_docs = [idx for idx, _ in top_results]
                    precision = len(set(retrieved_docs) & set(relevant_docs)) / len(retrieved_docs) if retrieved_docs else 0
                    total_score += precision
                
                avg_score = total_score / len(queries) if queries else 0
                
                if avg_score > best_score:
                    best_score = avg_score
                    best_params = {'k1': k1, 'b': b}
        
        # Actualizar modelo con mejores parámetros
        self.bm25 = BM25(k1=best_params['k1'], b=best_params['b'])
        self.bm25.fit(self.tokenized_docs)
        
        print(f"[BM25] Mejores parámetros encontrados: k1={best_params['k1']:.2f}, b={best_params['b']:.2f}")
        print(f"[BM25] Score promedio: {best_score:.4f}")
        
        return best_params
