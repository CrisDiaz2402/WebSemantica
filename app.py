from flask import Flask, render_template, request, jsonify, send_file
from utils.main_processor import OpinionExtractor
from utils.visualization import OpinionVisualizer # Asumo que esta clase existe y es necesaria
import os
import json
from datetime import datetime
import pandas as pd

app = Flask(__name__)

# Configuración
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Crear directorios necesarios
os.makedirs('uploads', exist_ok=True)
os.makedirs('documents', exist_ok=True) # Asegurarse de que la carpeta documents exista
os.makedirs('visualizations', exist_ok=True)
os.makedirs('exports', exist_ok=True)

# Inicializar el extractor semántico
extractor = OpinionExtractor()
visualizer = OpinionVisualizer() # Asumo que OpinionVisualizer se inicializa aquí

@app.route('/')
def home():
    """Página principal del sistema"""
    return render_template('index.html')

@app.route('/api/check-data-file')
def check_data_file():
    """Verifica si existe el archivo test.csv y obtiene información básica"""
    print("[INFO] Iniciando verificación del archivo test.csv")
    
    try:
        data_file_path = os.path.join('documents', 'test.csv')
        print(f"[DEBUG] Ruta construida para el archivo: {data_file_path}")
        
        if os.path.exists(data_file_path):
            print("[INFO] El archivo existe.")
            
            # Leer información básica del archivo
            df = pd.read_csv(data_file_path)
            print(f"[INFO] Archivo leído correctamente. Filas: {len(df)}, Columnas: {df.columns.tolist()}")
            
            file_size = os.path.getsize(data_file_path)
            print(f"[INFO] Tamaño del archivo: {file_size} bytes")
            
            result = {
                'exists': True,
                'path': data_file_path,
                'rows': len(df),
                'columns': list(df.columns),
                'size': file_size
            }
            print(f"[RESULT] Resultado JSON a retornar: {result}")
            return jsonify(result)
        else:
            print("[WARNING] El archivo no existe.")
            result = {
                'exists': False,
                'path': data_file_path
            }
            print(f"[RESULT] Resultado JSON a retornar: {result}")
            return jsonify(result)
    except Exception as e:
        print(f"[ERROR] Ocurrió una excepción: {str(e)}")
        return jsonify({
            'exists': False,
            'error': str(e)
        }), 500

@app.route('/process-fixed-data')
def process_fixed_data():
    """Procesa el archivo fijo documents/test.csv"""
    try:
        data_file_path = os.path.join('documents', 'test.csv')
        
        if not os.path.exists(data_file_path):
            return jsonify({'error': 'Archivo documents/test.csv no encontrado'}), 404
        
        # Obtener columna de texto
        text_column = request.args.get('text_column', 'review_text')
        
        # Procesar el archivo
        results = extractor.process_csv(data_file_path, text_column)
        
        if results:
            return jsonify({
                'success': True,
                'message': f'Procesadas {len(results)} reseñas desde documents/test.csv',
                'total_reviews': len(results),
                'text_column': text_column
            })
        else:
            return jsonify({'error': 'Error procesando el archivo'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/search', methods=['POST'])
def semantic_search():
    """Búsqueda semántica en las reseñas"""
    try:
        query = request.form.get('query', '').strip()
        top_k = int(request.form.get('top_k', 5))
        
        if not query:
            return jsonify({'error': 'Consulta vacía'}), 400
        
        results = extractor.get_semantic_search_results(query, top_k)
        
        formatted_results = []
        for result in results:
            formatted_results.append({
                'id': result.get('id', 'unknown'),
                'text': result.get('original_text', '')[:200] + '...',
                'score': round(result.get('similarity_score', 0), 3),
                'products': result.get('products', []),
                'brands': result.get('brands', []),
                'sentiment': result.get('events', [{}])[0].get('sentiment', 'neutro') if result.get('events') else 'neutro'
            })
        
        return jsonify({
            'results': formatted_results,
            'total': len(formatted_results),
            'query': query
        })
        
    except Exception as e:
        return jsonify({'error': f'Error en búsqueda: {str(e)}'}), 500

@app.route('/search/sentiment/<sentiment>')
def search_by_sentiment(sentiment):
    """Búsqueda por sentimiento específico"""
    try:
        top_k = int(request.args.get('top_k', 5))
        results = extractor.search_engine.search_by_sentiment(sentiment, top_k)
        
        formatted_results = []
        for result in results:
            formatted_results.append({
                'id': result.get('id', 'unknown'),
                'text': result.get('original_text', '')[:200] + '...',
                'score': round(result.get('similarity_score', 0), 3),
                'products': result.get('products', []),
                'brands': result.get('brands', [])
            })
        
        return jsonify({
            'results': formatted_results,
            'sentiment': sentiment,
            'total': len(formatted_results)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/search/product/<product>')
def search_by_product(product):
    """Búsqueda por producto específico"""
    try:
        top_k = int(request.args.get('top_k', 5))
        results = extractor.search_engine.search_by_product(product, top_k)
        
        formatted_results = []
        for result in results:
            formatted_results.append({
                'id': result.get('id', 'unknown'),
                'text': result.get('original_text', '')[:200] + '...',
                'score': round(result.get('similarity_score', 0), 3),
                'sentiment': result.get('events', [{}])[0].get('sentiment', 'neutro') if result.get('events') else 'neutro'
            })
        
        return jsonify({
            'results': formatted_results,
            'product': product,
            'total': len(formatted_results)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/analytics')
def analytics():
    """Página de análisis y estadísticas"""
    try:
        if not extractor.processed_reviews:
            return render_template('analytics.html', error="No hay datos procesados")
        
        report = extractor.generate_report()
        return render_template('analytics.html', report=report)
        
    except Exception as e:
        return render_template('analytics.html', error=f"Error: {str(e)}")

@app.route('/visualizations')
def visualizations():
    """Página de visualizaciones"""
    return render_template('visualizations.html')

@app.route('/api/report')
def get_report():
    """API para obtener reporte completo"""
    try:
        report = extractor.generate_report()
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/api/events/<event_type>')
def get_events_by_type(event_type):
    """API para obtener eventos por tipo"""
    try:
        events = extractor.get_events_by_type(event_type)
        return jsonify({
            'events': events,
            'type': event_type,
            'total': len(events)
        })
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/api/products/sentiment/<sentiment>')
def get_products_by_sentiment(sentiment):
    """API para obtener productos por sentimiento"""
    try:
        products = extractor.get_products_by_sentiment(sentiment)
        return jsonify({
            'products': products,
            'sentiment': sentiment,
            'total': len(products)
        })
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/export/json')
def export_json():
    """Exporta resultados en formato JSON"""
    try:
        filename = f"exports/processed_reviews_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        extractor.export_results(filename)
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/export/rdf')
def export_rdf():
    """Exporta grafo de conocimiento en formato RDF"""
    try:
        filename = f"exports/knowledge_graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ttl"
        extractor.export_knowledge_graph(filename)
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/dashboard')
def dashboard():
    """Dashboard principal con visualizaciones"""
    try:
        if not extractor.processed_reviews:
            return render_template('dashboard.html', error="No hay datos procesados")
        
        # Generar visualizaciones
        visualizer.save_all_visualizations(extractor.processed_reviews)
        
        return render_template('dashboard.html', success=True)
    except Exception as e:
        return render_template('dashboard.html', error=f"Error: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
