from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD
import pandas as pd
from typing import List, Dict, Tuple

class KnowledgeRepresentation:
    """Representación del conocimiento usando RDF"""
    
    def __init__(self):
        self.graph = Graph()
        
        # Definir namespaces
        self.REVIEW = Namespace("http://example.org/review/")
        self.PRODUCT = Namespace("http://example.org/product/")
        self.USER = Namespace("http://example.org/user/")
        self.EVENT = Namespace("http://example.org/event/")
        
        # Bind namespaces
        self.graph.bind("review", self.REVIEW)
        self.graph.bind("product", self.PRODUCT)
        self.graph.bind("user", self.USER)
        self.graph.bind("event", self.EVENT)
        self.graph.bind("rdfs", RDFS)
    
    def add_triple(self, subject: str, predicate: str, obj: str, obj_type: str = "literal"):
        """Añade una tripleta al grafo RDF"""
        # Crear URIs
        subj_uri = self._create_uri(subject, "user")
        pred_uri = self._create_predicate_uri(predicate)
        
        if obj_type == "literal":
            obj_node = Literal(obj)
        else:
            obj_node = self._create_uri(obj, obj_type)
        
        self.graph.add((subj_uri, pred_uri, obj_node))
    
    def _create_uri(self, name: str, type_prefix: str) -> URIRef:
        """Crea una URI basada en el nombre y tipo"""
        clean_name = name.replace(" ", "_").replace("-", "_")
        
        if type_prefix == "user":
            return self.USER[clean_name]
        elif type_prefix == "product":
            return self.PRODUCT[clean_name]
        elif type_prefix == "event":
            return self.EVENT[clean_name]
        else:
            return self.REVIEW[clean_name]
    
    def _create_predicate_uri(self, predicate: str) -> URIRef:
        """Crea una URI para el predicado"""
        clean_predicate = predicate.replace(" ", "_").replace("-", "_")
        return self.REVIEW[clean_predicate]
    
    def add_event_to_graph(self, event: Dict[str, any], review_id: str):
        """Añade un evento al grafo RDF"""
        event_id = f"event_{review_id}_{event['type']}"
        event_uri = self._create_uri(event_id, "event")
        
        # Añadir tipo de evento
        self.graph.add((event_uri, RDF.type, self.EVENT[event['type'].capitalize()]))
        
        # Añadir propiedades del evento
        if event.get('actor'):
            actor_uri = self._create_uri(event['actor'], "user")
            self.graph.add((event_uri, self.EVENT.hasActor, actor_uri))
        
        if event.get('object'):
            object_uri = self._create_uri(event['object'], "product")
            self.graph.add((event_uri, self.EVENT.hasObject, object_uri))
        
        if event.get('sentiment'):
            self.graph.add((event_uri, self.EVENT.hasSentiment, Literal(event['sentiment'])))
        
        # Añadir trigger
        self.graph.add((event_uri, self.EVENT.hasTrigger, Literal(event['trigger'])))
    
    def create_product_sentiment_graph(self, reviews_data: List[Dict[str, any]]):
        """Crea un grafo de productos y sentimientos"""
        for review in reviews_data:
            review_id = review.get('id', 'unknown')
            
            # Añadir eventos
            if 'events' in review:
                for event in review['events']:
                    self.add_event_to_graph(event, review_id)
    
    def query_products_by_sentiment(self, sentiment: str) -> List[str]:
        """Consulta productos por sentimiento"""
        query = f"""
        SELECT ?product WHERE {{
            ?event event:hasSentiment "{sentiment}" .
            ?event event:hasObject ?product .
        }}
        """
        
        try:
            results = self.graph.query(query)
            products = [str(row[0]).split('/')[-1] for row in results]
            return products
        except:
            return []
    
    def export_to_turtle(self, filename: str):
        """Exporta el grafo a formato Turtle"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(self.graph.serialize(format='turtle'))
    
    def get_graph_stats(self) -> Dict[str, int]:
        """Obtiene estadísticas del grafo"""
        return {
            'total_triples': len(self.graph),
            'unique_subjects': len(set(s for s, p, o in self.graph)),
            'unique_predicates': len(set(p for s, p, o in self.graph)),
            'unique_objects': len(set(o for s, p, o in self.graph))
        }
