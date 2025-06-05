from flask import Flask, render_template, request, jsonify
from utils.search_engine import SearchEngine
import os

app = Flask(__name__)

# Configuración
DOCUMENTS_DIR = os.path.join(os.path.dirname(__file__), 'documents')

# Inicializar motor de búsqueda
search_engine = SearchEngine(DOCUMENTS_DIR)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query', '')
    results = search_engine.search(query)
    
    formatted_results = []
    for doc_id, doc_data in results:
        formatted_results.append({
            'id': doc_id,
            'filename': doc_data['filename'],
            'content': doc_data['content'],
            'score': doc_data['score']
        })
    
    return jsonify({'results': formatted_results})

if __name__ == '__main__':
    app.run(debug=True)