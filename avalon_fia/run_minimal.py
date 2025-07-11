#!/usr/bin/env python3
"""
Script para executar o dashboard minimal (sem dependências externas)
"""

import os
import sys
import webbrowser
import subprocess
from pathlib import Path

def check_data_availability():
    """Verifica se os dados estão disponíveis"""
    print("🔍 Verificando disponibilidade dos dados...")
    
    from datetime import datetime
    import pickle as pkl
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    pickle_dir = Path('/mnt/c/Users/guilh/Documents/GitHub/database/dados_api')
    
    header_path = pickle_dir / f'header_{current_date}.pkl'
    data_xml_path = pickle_dir / f'data_xml_{current_date}.pkl'
    
    if header_path.exists() and data_xml_path.exists():
        print("✅ Dados disponíveis para hoje")
        
        # Carregar um pouco dos dados para verificar
        try:
            with open(header_path, 'rb') as f:
                header = pkl.load(f)
            
            pl = header.get('patliq', 0)
            cota = header.get('valorcota', 0)
            print(f"   PL: R$ {pl:,.2f}")
            print(f"   Cota: {cota}")
            return True
            
        except Exception as e:
            print(f"⚠️ Erro ao verificar dados: {e}")
            return False
    else:
        print("❌ Dados não disponíveis para hoje")
        print(f"   Header: {header_path.exists()}")
        print(f"   Data XML: {data_xml_path.exists()}")
        return False

def main():
    print("🏦 Avalon FIA Dashboard - Versão Minimal")
    print("=" * 50)
    
    # Verificar dados
    if not check_data_availability():
        print("\n❌ Dados não disponíveis. Verifique se a API foi executada hoje.")
        input("Pressione Enter para sair...")
        return
    
    print("\n🚀 Iniciando dashboard...")
    print("📊 O navegador será aberto automaticamente")
    print("⏹️ Pressione Ctrl+C para parar o servidor")
    print("-" * 50)
    
    # Executar a aplicação
    try:
        # Adicionar trackfia ao path
        sys.path.append(str(Path(__file__).parent))
        
        from trackfia.app_minimal import run_server
        run_server()
        
    except KeyboardInterrupt:
        print("\n🛑 Dashboard parado pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro ao iniciar dashboard: {e}")
        import traceback
        traceback.print_exc()
        input("\nPressione Enter para sair...")

if __name__ == '__main__':
    main()