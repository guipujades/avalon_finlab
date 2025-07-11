#!/usr/bin/env python3
"""
Testar caminhos no Windows
"""

import os
import platform
from pathlib import Path

def test_paths():
    print("🔍 Testando Caminhos no Windows")
    print("=" * 50)
    
    print(f"Sistema: {platform.system()}")
    print(f"Diretório atual: {os.getcwd()}")
    
    # Testar caminhos possíveis
    possible_paths = [
        Path('C:/Users/guilh/Documents/GitHub/database/dados_api'),
        Path('C:\\Users\\guilh\\Documents\\GitHub\\database\\dados_api'),
        Path(os.path.expanduser('~/Documents/GitHub/database/dados_api')),
        Path('./database/dados_api'),
        Path('../database/dados_api')
    ]
    
    print(f"\n📁 Testando caminhos:")
    for path in possible_paths:
        exists = path.exists()
        if exists:
            files = list(path.glob('*.pkl'))
            print(f"  ✅ {path} - {len(files)} arquivos")
            if files:
                latest = max(files, key=lambda x: x.stat().st_mtime)
                print(f"     Mais recente: {latest.name}")
        else:
            print(f"  ❌ {path}")
    
    # Testar importação do processador
    print(f"\n🧪 Testando processador:")
    try:
        import sys
        sys.path.append('.')
        
        from trackfia.portfolio_processor_fixed import process_portfolio_from_api_fixed
        
        data = process_portfolio_from_api_fixed()
        if data:
            stocks = data.get('stocks', {})
            print(f"  ✅ Processador funcionando - {len(stocks)} ações")
        else:
            print(f"  ❌ Processador retornou dados vazios")
            
    except Exception as e:
        print(f"  ❌ Erro no processador: {e}")

if __name__ == '__main__':
    test_paths()