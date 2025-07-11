#!/usr/bin/env python3
"""
Atualizar dados da API e executar dashboard
"""

import os
import sys
import webbrowser
from pathlib import Path

# Adicionar trackfia ao path
sys.path.append(str(Path(__file__).parent))

def update_data_first():
    """Primeiro atualiza os dados da API"""
    print("Atualizando dados da API BTG...")
    
    try:
        from trackfia.api_btg_funds import fund_data_corrected
        
        # Forçar busca de dados novos
        df_xml, data_xml, header = fund_data_corrected('xml')
        
        print(f"Dados atualizados!")
        print(f"PL: R$ {header.get('patliq', 0):,.2f}")
        print(f"Total ativos: {len(df_xml) if df_xml is not None else 0}")
        
        return True
        
    except Exception as e:
        print(f"Erro ao atualizar dados: {e}")
        return False

def run_dashboard():
    """Executar o dashboard"""
    print("\nIniciando Dashboard...")
    
    try:
        from trackfia.app_complete import app
        
        print("Dashboard inicializado!")
        print("Acesse: http://localhost:5000")
        print("Ações agora devem aparecer!")
        
        # Abrir navegador
        webbrowser.open('http://localhost:5000')
        
        # Executar servidor
        app.run(debug=False, host='localhost', port=5000)
        
    except Exception as e:
        print(f"Erro no dashboard: {e}")
        print("\nVerifique se as dependências estão instaladas:")
        print("pip install flask pandas numpy requests matplotlib")

def main():
    print("Avalon FIA - Atualizar e Executar")
    print("=" * 50)
    
    # Primeiro atualizar dados
    if update_data_first():
        # Depois executar dashboard
        run_dashboard()
    else:
        print("Falha na atualização dos dados")

if __name__ == '__main__':
    main()