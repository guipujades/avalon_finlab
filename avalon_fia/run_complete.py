#!/usr/bin/env python3
"""
Script para executar o dashboard completo e elegante do Avalon FIA
"""

import os
import sys
import webbrowser
from pathlib import Path

# Adicionar trackfia ao path
sys.path.append(str(Path(__file__).parent))

def main():
    print("🚀 Iniciando Avalon FIA Analytics Dashboard")
    print("💎 Versão Completa com Interface Elegante")
    print("-" * 50)
    
    try:
        from trackfia.app_complete import app
        
        print("\n✅ Sistema inicializado com sucesso!")
        print("📊 Abrindo dashboard em http://localhost:5000")
        print("\n📌 Funcionalidades disponíveis:")
        print("   • Análise completa do portfolio")
        print("   • Métricas de risco (VaR, Sharpe)")
        print("   • Gráficos interativos")
        print("   • Dados de mercado em tempo real")
        print("   • Análise de concentração")
        print("   • Exportação de dados")
        
        # Abrir navegador automaticamente
        webbrowser.open('http://localhost:5000')
        
        # Executar servidor
        app.run(debug=False, host='localhost', port=5000)
        
    except Exception as e:
        print(f"\n❌ Erro ao iniciar aplicação: {e}")
        print("\nPossíveis soluções:")
        print("1. Instalar dependências faltantes:")
        print("   pip install flask pandas numpy requests matplotlib")
        print("2. Verificar se o MetaTrader 5 está configurado")
        print("3. Confirmar credenciais da API BTG")
        
        import traceback
        print("\nDetalhes do erro:")
        traceback.print_exc()
        
        input("\nPressione Enter para sair...")

if __name__ == '__main__':
    main()