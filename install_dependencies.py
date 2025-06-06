import subprocess
import sys

def install_requirements():
    """Instala las dependencias necesarias para el proyecto"""
    requirements = [
        'pandas==2.0.3',
        'spacy==3.7.2', 
        'rdflib==7.0.0',
        'networkx==3.1',
        'matplotlib==3.7.2',
        'scikit-learn==1.3.0',
        'nltk==3.8.1',
        'textblob==0.17.1',
        'wordcloud==1.9.2',
        'plotly==5.17.0'
    ]
    
    for requirement in requirements:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', requirement])
            print(f"✓ Instalado: {requirement}")
        except subprocess.CalledProcessError:
            print(f"✗ Error instalando: {requirement}")
    
    # Descargar modelo de spaCy en español
    try:
        subprocess.check_call([sys.executable, '-m', 'spacy', 'download', 'es_core_news_sm'])
        print("✓ Modelo de spaCy en español descargado")
    except subprocess.CalledProcessError:
        print("✗ Error descargando modelo de spaCy")

if __name__ == "__main__":
    install_requirements()
