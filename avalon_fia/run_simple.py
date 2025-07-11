#!/usr/bin/env python3
"""
Script para executar o dashboard simplificado (sem scipy)
"""

import os
import sys
import webbrowser
from pathlib import Path

# Adicionar trackfia ao path
sys.path.append(str(Path(__file__).parent))

def main():
    print("🚀 Iniciando Avalon FIA Dashboard (Versão Simplificada)")
    print("-" * 50)
    
    # Importar e executar a aplicação simplificada
    try:
        from trackfia.app_local_simple import app
        
        print("\n✅ Aplicação inicializada com sucesso!")
        print("📊 Abrindo navegador em http://localhost:5000")
        
        # Abrir navegador automaticamente
        webbrowser.open('http://localhost:5000')
        
        # Executar servidor
        app.run(debug=False, host='localhost', port=5000)
        
    except Exception as e:
        print(f"❌ Erro ao iniciar aplicação: {e}")
        import traceback
        traceback.print_exc()
        input("\nPressione Enter para sair...")

if __name__ == '__main__':
    main()