import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd
import json
from typing import Dict, List, Any
import numpy as np
from collections import Counter
import os

class OpinionVisualizer:
    """Clase para visualizar los resultados del análisis semántico"""
    
    def __init__(self):
        plt.style.use('default')
        self.colors = {
            'positive': '#2E8B57',  # Verde
            'negative': '#DC143C',  # Rojo
            'neutral': '#4682B4'     # Azul
        }
    
    def load_processed_data(self, json_file: str) -> List[Dict[str, Any]]:
        """Carga los datos procesados desde JSON"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error cargando datos: {e}")
            return []
    
    def create_sentiment_chart(self, processed_reviews: List[Dict[str, Any]]) -> str:
        """Crea gráfico de distribución de sentimientos"""
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        for review in processed_reviews:
            for event in review.get('events', []):
                sentiment = event.get('sentiment', 'neutral')
                sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        # Crear gráfico
        fig, ax = plt.subplots(figsize=(10, 6))
        sentiments = list(sentiment_counts.keys())
        counts = list(sentiment_counts.values())
        colors = [self.colors[s] for s in sentiments]
        
        bars = ax.bar(sentiments, counts, color=colors)
        ax.set_title('Distribución de Sentimientos en Reseñas', fontsize=16)
        ax.set_xlabel('Sentimiento', fontsize=12)
        ax.set_ylabel('Número de Eventos', fontsize=12)
        
        # Añadir valores en las barras
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{count}', ha='center', va='bottom')
        
        plt.tight_layout()
        
        # Guardar gráfico
        output_path = 'static/images/sentiment_distribution.png'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def create_products_chart(self, processed_reviews: List[Dict[str, Any]]) -> str:
        """Crea gráfico de productos más mencionados"""
        all_products = []
        for review in processed_reviews:
            all_products.extend(review.get('products', []))
        
        product_counts = Counter(all_products)
        top_products = dict(product_counts.most_common(10))
        
        if not top_products:
            return None
        
        # Crear gráfico horizontal
        fig, ax = plt.subplots(figsize=(12, 8))
        products = list(top_products.keys())
        counts = list(top_products.values())
        
        bars = ax.barh(products, counts, color='skyblue')
        ax.set_title('Productos Más Mencionados', fontsize=16)
        ax.set_xlabel('Número de Menciones', fontsize=12)
        ax.set_ylabel('Productos', fontsize=12)
        
        # Añadir valores en las barras
        for bar, count in zip(bars, counts):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2.,
                   f'{count}', ha='left', va='center')
        
        plt.tight_layout()
        
        # Guardar gráfico
        output_path = 'static/images/product_mentions.png'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def save_all_visualizations(self, processed_reviews: List[Dict[str, Any]], output_dir: str = 'visualizations'):
        """Guarda todas las visualizaciones"""
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs('static/images', exist_ok=True)
        
        print("Generando visualizaciones...")
        
        # Crear gráficos
        sentiment_path = self.create_sentiment_chart(processed_reviews)
        products_path = self.create_products_chart(processed_reviews)
        
        print(f"Visualizaciones guardadas:")
        if sentiment_path:
            print(f"- {sentiment_path}")
        if products_path:
            print(f"- {products_path}")
