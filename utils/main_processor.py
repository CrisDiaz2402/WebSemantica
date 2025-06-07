import pandas as pd
from typing import Dict, List, Any
import json
from datetime import datetime
import os

# Asumo que estas clases existen en el mismo directorio utils
# y que sus implementaciones son correctas.
from .regex_extractor import RegexExtractor
from .ner_extractor import NERExtractor
from .relationship_extractor import RelationshipExtractor
from .event_extractor import EventExtractor
from .knowledge_representation import KnowledgeRepresentation
from .semantic_search import SemanticSearch

class OpinionExtractor:
    """Clase principal que integra todos los componentes del extractor semántico"""
    
    def __init__(self):
        self.regex_extractor = RegexExtractor()
        self.ner_extractor = NERExtractor()
        self.relationship_extractor = RelationshipExtractor()
        self.event_extractor = EventExtractor()
        self.knowledge_rep = KnowledgeRepresentation()
        self.search_engine = SemanticSearch()
        
        self.processed_reviews = []
    
    def process_csv(self, csv_file_path: str, text_column: str = 'review_text') -> List[Dict[str, Any]]:
        """Procesa un archivo CSV de reseñas"""
        print(f"Cargando datos desde {csv_file_path}...")
        
        try:
            df = pd.read_csv(csv_file_path)
            print(f"Cargadas {len(df)} reseñas")
        except Exception as e:
            print(f"Error cargando CSV: {e}")
            return []
        
        if text_column not in df.columns:
            print(f"Columna '{text_column}' no encontrada. Columnas disponibles: {list(df.columns)}")
            return []
        
        processed_reviews = []
        
        for idx, row in df.iterrows():
            review_text = str(row[text_column])
            review_id = f"review_{idx}"
            
            print(f"Procesando reseña {idx + 1}/{len(df)}...")
            
            # Procesar la reseña
            processed_review = self.process_single_review(review_text, review_id, dict(row))
            processed_reviews.append(processed_review)
        
        self.processed_reviews = processed_reviews
        
        # Crear representación del conocimiento
        print("Creando grafo de conocimiento...")
        self.knowledge_rep.create_product_sentiment_graph(processed_reviews)
        
        # Indexar para búsqueda
        print("Indexando para búsqueda semántica...")
        self.search_engine.index_documents(processed_reviews)
        
        print("Procesamiento completado!")
        return processed_reviews
    
    def process_single_review(self, text: str, review_id: str, metadata: Dict = None) -> Dict[str, Any]:
        """Procesa una sola reseña aplicando todas las técnicas"""
        
        # 1. Limpieza y extracción con regex
        clean_text = self.regex_extractor.clean_text(text)
        regex_patterns = self.regex_extractor.extract_all_patterns(text)
        
        # 2. Reconocimiento de entidades nombradas (NER)
        ner_analysis = self.ner_extractor.analyze_review(text)
        
        # 3. Extracción de relaciones
        relations = self.relationship_extractor.extract_all_relations(text, ner_analysis)
        
        # 4. Extracción de eventos
        events = self.event_extractor.extract_events(text, ner_analysis)
        
        # Compilar resultado
        processed_review = {
            'id': review_id,
            'original_text': text,
            'clean_text': clean_text,
            'regex_patterns': regex_patterns,
            'entities': ner_analysis['entities'],
            'products': ner_analysis['products'],
            'brands': ner_analysis['brands'],
            'relations': relations,
            'events': events,
            'metadata': metadata or {},
            'processed_at': datetime.now().isoformat()
        }
        
        return processed_review
    
    def get_semantic_search_results(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Realiza búsqueda semántica"""
        return self.search_engine.search(query, top_k)
    
    def get_products_by_sentiment(self, sentiment: str) -> List[str]:
        """Obtiene productos por sentimiento usando el grafo RDF"""
        return self.knowledge_rep.query_products_by_sentiment(sentiment)
    
    def get_events_by_type(self, event_type: str) -> List[Dict[str, str]]:
        """Obtiene eventos por tipo"""
        events = []
        for review in self.processed_reviews:
            for event in review.get('events', []):
                if event.get('type') == event_type:
                    events.append({
                        'event': f"{event_type}_{review['id']}",
                        'actor': event.get('actor'),
                        'object': event.get('object'),
                        'sentiment': event.get('sentiment')
                    })
        return events
    
    def export_results(self, output_file: str = 'processed_reviews.json'):
        """Exporta los resultados procesados"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.processed_reviews, f, ensure_ascii=False, indent=2)
        print(f"Resultados exportados a {output_file}")
    
    def export_knowledge_graph(self, output_file: str = 'knowledge_graph.ttl'):
        """Exporta el grafo de conocimiento a formato Turtle"""
        self.knowledge_rep.export_to_turtle(output_file)
        print(f"Grafo de conocimiento exportado a {output_file}")
    
    def generate_report(self) -> Dict[str, Any]:
        """Genera un reporte completo del análisis"""
        if not self.processed_reviews:
            return {'error': 'No hay reseñas procesadas'}
        
        # Estadísticas generales
        total_reviews = len(self.processed_reviews)
        
        # Contar entidades
        all_products = []
        all_brands = []
        all_events = []
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        for review in self.processed_reviews:
            all_products.extend(review.get('products', []))
            all_brands.extend(review.get('brands', []))
            all_events.extend(review.get('events', []))
            
            # Contar sentimientos de eventos
            for event in review.get('events', []):
                sentiment = event.get('sentiment', 'neutral')
                sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        # Productos y marcas más mencionados
        from collections import Counter
        product_counts = Counter(all_products)
        brand_counts = Counter(all_brands)
        
        # Tipos de eventos más comunes
        event_types = [event.get('type', 'unknown') for event in all_events]
        event_type_counts = Counter(event_types)
        
        # Estadísticas del grafo
        graph_stats = self.knowledge_rep.get_graph_stats()
        
        # Estadísticas de búsqueda
        search_stats = self.search_engine.get_search_statistics()
        
        report = {
            'resumen_general': {
                'total_reseñas': total_reviews,
                'productos_únicos': len(set(all_products)),
                'marcas_únicas': len(set(all_brands)),
                'eventos_totales': len(all_events)
            },
            'productos_más_mencionados': dict(product_counts.most_common(10)),
            'marcas_más_mencionadas': dict(brand_counts.most_common(10)),
            'distribución_sentimientos': sentiment_counts,
            'tipos_eventos_más_comunes': dict(event_type_counts.most_common(10)),
            'estadísticas_grafo': graph_stats,
            'estadísticas_búsqueda': search_stats,
            'generado_en': datetime.now().isoformat()
        }
        
        return report
    
    def save_report(self, filename: str = 'analysis_report.json'):
        """Guarda el reporte de análisis"""
        report = self.generate_report()
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"Reporte guardado en {filename}")

# La función create_sample_csv ha sido eliminada de este archivo.
