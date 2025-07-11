#!/usr/bin/env python3
"""
Script para executar o dashboard local do Avalon FIA
"""

import os
import sys
import webbrowser
from pathlib import Path

# Adicionar trackfia ao path
sys.path.append(str(Path(__file__).parent / 'trackfia'))

def main():
    print("🚀 Iniciando Avalon FIA Dashboard Local")
    print("-" * 50)
    
    # Importar e executar a aplicação
    try:
        from trackfia.app_local import app
        
        # Abrir navegador automaticamente
        webbrowser.open('http://localhost:5000')
        
        # Executar servidor
        app.run(debug=False, host='localhost', port=5000)
        
    except Exception as e:
        print(f"❌ Erro ao iniciar aplicação: {e}")
        print("\nVerifique se:")
        print("1. As dependências estão instaladas (Flask, pandas, numpy, etc.)")
        print("2. O MetaTrader 5 está instalado e configurado")
        print("3. As credenciais da API BTG estão corretas")
        input("\nPressione Enter para sair...")

if __name__ == '__main__':
    main()