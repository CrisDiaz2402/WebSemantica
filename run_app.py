#!/usr/bin/env python3
"""
Script para ejecutar la aplicación Flask del Extractor Semántico
"""

import os
import sys
from app import app

def main():
    """Función principal para ejecutar la aplicación"""
    
    print("=" * 60)
    print("EXTRACTOR SEMÁNTICO DE OPINIONES DE PRODUCTOS")
    print("Sistema Web con Flask")
    print("=" * 60)
    
    # Verificar que las dependencias estén instaladas
    try:
        import pandas
        import spacy
        import sklearn
        print("✅ Dependencias verificadas")
    except ImportError as e:
        print(f"❌ Falta dependencia: {e}")
        print("Ejecuta: python install_dependencies.py")
        return
    
    # Crear directorios necesarios
    directories = ['uploads', 'exports', 'visualizations', 'static/images']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("📁 Directorios creados")
    print("🚀 Iniciando servidor Flask...")
    print("📱 Accede a: http://localhost:5000")
    print("⏹️  Presiona Ctrl+C para detener")
    
    # Ejecutar la aplicación
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        threaded=True
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Servidor detenido por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
