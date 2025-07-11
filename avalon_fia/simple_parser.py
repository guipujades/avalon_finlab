
import pickle as pkl
from pathlib import Path
from datetime import datetime

def parse_portfolio_simple():
    """Parser simples sem pandas"""
    try:
        pickle_dir = Path('/mnt/c/Users/guilh/Documents/GitHub/database/dados_api')
        
        # Buscar arquivos mais recentes
        data_files = sorted(pickle_dir.glob('data_xml_*.pkl'), reverse=True)
        header_files = sorted(pickle_dir.glob('header_*.pkl'), reverse=True)
        
        if not data_files or not header_files:
            return None, None
        
        # Carregar dados
        with open(data_files[0], 'rb') as f:
            data_xml = pkl.load(f)
        
        with open(header_files[0], 'rb') as f:
            header = pkl.load(f)
        
        return data_xml, header
        
    except Exception as e:
        print(f"Erro: {e}")
        return None, None

# Testar
data, header = parse_portfolio_simple()
if data and header:
    print(f"✅ Dados carregados!")
    print(f"📊 Header: {header}")
    print(f"📈 Data type: {type(data)}")
    if isinstance(data, list) and len(data) > 0:
        print(f"📝 Primeiro item: {data[0]}")
else:
    print("❌ Falha ao carregar")
