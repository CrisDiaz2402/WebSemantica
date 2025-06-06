from flask import Flask, render_template, request, jsonify, send_file
from utils.main_processor import OpinionExtractor
from utils.visualization import OpinionVisualizer
import os
import json
from datetime import datetime
import pandas as pd

app = Flask(__name__)

# Configuración
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATA_FOLDER'] = 'data'  # Nueva carpeta para CSVs
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Crear directorios necesarios
os.makedirs('uploads', exist_ok=True)
os.makedirs('data', exist_ok=True)  # Crear carpeta data
os.makedirs('visualizations', exist_ok=True)
os.makedirs('exports', exist_ok=True)

# Inicializar el extractor semántico
extractor = OpinionExtractor()
visualizer = OpinionVisualizer()

@app.route('/')
def home():
    """Página principal del sistema"""
    return render_template('index.html')

@app.route('/api/check-data-file')
def check_data_file():
    """Verifica si existe el archivo data.csv y obtiene información básica"""
    try:
        data_file_path = os.path.join('documents', 'data.csv')
        
        if os.path.exists(data_file_path):
            # Leer información básica del archivo
            df = pd.read_csv(data_file_path)
            
            return jsonify({
                'exists': True,
                'path': data_file_path,
                'rows': len(df),
                'columns': list(df.columns),
                'size': os.path.getsize(data_file_path)
            })
        else:
            return jsonify({
                'exists': False,
                'path': data_file_path
            })
    except Exception as e:
        return jsonify({
            'exists': False,
            'error': str(e)
        }), 500

@app.route('/process-fixed-data')
def process_fixed_data():
    """Procesa el archivo fijo documents/data.csv"""
    try:
        data_file_path = os.path.join('documents', 'data.csv')
        
        if not os.path.exists(data_file_path):
            return jsonify({'error': 'Archivo documents/data.csv no encontrado'}), 404
        
        # Obtener columna de texto
        text_column = request.args.get('text_column', 'review_text')
        
        # Procesar el archivo
        results = extractor.process_csv(data_file_path, text_column)
        
        if results:
            return jsonify({
                'success': True,
                'message': f'Procesadas {len(results)} reseñas desde documents/data.csv',
                'total_reviews': len(results),
                'text_column': text_column
            })
        else:
            return jsonify({'error': 'Error procesando el archivo'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/api/csv-files')
def list_csv_files():
    """Lista archivos CSV disponibles en la carpeta data"""
    try:
        data_folder = app.config['DATA_FOLDER']
        csv_files = []
        
        if os.path.exists(data_folder):
            for filename in os.listdir(data_folder):
                if filename.endswith('.csv'):
                    filepath = os.path.join(data_folder, filename)
                    file_size = os.path.getsize(filepath)
                    file_modified = datetime.fromtimestamp(os.path.getmtime(filepath))
                    
                    csv_files.append({
                        'filename': filename,
                        'size': file_size,
                        'modified': file_modified.isoformat(),
                        'path': filepath
                    })
        
        return jsonify({
            'files': csv_files,
            'total': len(csv_files)
        })
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/process-csv/<filename>')
def process_csv_from_data(filename):
    """Procesa un archivo CSV específico de la carpeta data"""
    try:
        data_folder = app.config['DATA_FOLDER']
        filepath = os.path.join(data_folder, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'Archivo no encontrado'}), 404
        
        if not filename.endswith('.csv'):
            return jsonify({'error': 'El archivo debe ser CSV'}), 400
        
        # Procesar el archivo
        text_column = request.args.get('text_column', 'review_text')
        results = extractor.process_csv(filepath, text_column)
        
        if results:
            return jsonify({
                'success': True,
                'message': f'Procesadas {len(results)} reseñas desde {filename}',
                'total_reviews': len(results),
                'filename': filename
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

@app.route('/generate_sample')
def generate_sample():
    """Genera datos de ejemplo para probar el sistema"""
    try:
        from utils.main_processor import create_sample_csv
        csv_file = create_sample_csv()  # Ahora guarda en documents/data.csv
        
        # Procesar automáticamente
        results = extractor.process_csv(csv_file, 'review_text')
        
        return jsonify({
            'success': True,
            'message': f'Generados y procesados datos de ejemplo: {len(results)} reseñas',
            'file': csv_file
        })
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
