#!/usr/bin/env python3
"""
Debug que lê os dados diretamente da API BTG sem pandas
"""

import pickle as pkl
import sys
from pathlib import Path
from datetime import datetime

def debug_raw_portfolio():
    """Debug dos dados brutos do portfolio"""
    print("🔍 Debug: Dados Brutos do Portfolio")
    print("=" * 50)
    
    try:
        # Buscar o arquivo de dados mais recente
        pickle_dir = Path('/mnt/c/Users/guilh/Documents/GitHub/database/dados_api')
        
        # Encontrar arquivos df_xml mais recentes
        df_files = sorted(pickle_dir.glob('df_xml_*.pkl'), reverse=True)
        
        if not df_files:
            print("❌ Nenhum arquivo df_xml encontrado")
            return
        
        print(f"📁 Arquivo mais recente: {df_files[0].name}")
        
        # Tentar ler sem pandas
        try:
            import pandas as pd
            print("⚠️ Pandas disponível, mas pode ter problemas com numpy")
            
            with open(df_files[0], 'rb') as f:
                df_xml = pkl.load(f)
            
            print(f"✅ DataFrame carregado: {len(df_xml)} registros")
            print(f"📊 Colunas: {list(df_xml.columns)}")
            
            # Verificar tipos
            tipos = df_xml['tipo'].value_counts() if 'tipo' in df_xml.columns else {}
            print("\n📈 Tipos de ativos:")
            for tipo, count in tipos.items():
                print(f"  {tipo}: {count}")
            
            # Verificar ações
            if 'tipo' in df_xml.columns:
                acoes = df_xml[df_xml['tipo'] == 'ACOES']
                print(f"\n🎯 Ações encontradas: {len(acoes)}")
                
                if len(acoes) > 0:
                    print("\n📋 Sample de ações:")
                    for i, (idx, row) in enumerate(acoes.head(3).iterrows()):
                        codigo = row.get('codigo', 'N/A')
                        quantidade = row.get('quantidade', 'N/A')
                        preco = row.get('precomedio', 'N/A')
                        valor = row.get('valorfindisp', 'N/A')
                        
                        print(f"  {codigo}: qtd={quantidade}, preço={preco}, valor={valor}")
                        
                        # Verificar se há NaN
                        for field, val in [('quantidade', quantidade), ('precomedio', preco), ('valorfindisp', valor)]:
                            if str(val).lower() == 'nan' or (hasattr(val, '__name__') and 'nan' in str(val).lower()):
                                print(f"    ⚠️ {field} é NaN!")
        
        except Exception as pandas_error:
            print(f"❌ Erro com pandas: {pandas_error}")
            print("🔄 Tentando leitura alternativa...")
            
            # Tentar ler o arquivo data_xml que pode ser mais simples
            data_files = sorted(pickle_dir.glob('data_xml_*.pkl'), reverse=True)
            if data_files:
                try:
                    with open(data_files[0], 'rb') as f:
                        data_xml = pkl.load(f)
                    print(f"✅ data_xml carregado: {type(data_xml)}")
                    
                    if isinstance(data_xml, list):
                        print(f"📊 {len(data_xml)} registros em data_xml")
                        if len(data_xml) > 0:
                            print(f"📝 Primeiro registro: {data_xml[0]}")
                    
                except Exception as e:
                    print(f"❌ Erro lendo data_xml: {e}")
            
        # Verificar header
        header_files = sorted(pickle_dir.glob('header_*.pkl'), reverse=True)
        if header_files:
            try:
                with open(header_files[0], 'rb') as f:
                    header = pkl.load(f)
                print(f"\n✅ Header carregado: {header}")
            except Exception as e:
                print(f"❌ Erro lendo header: {e}")
                
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()

def create_simple_portfolio_parser():
    """Criar um parser simples que não depende de pandas"""
    print("\n" + "=" * 50)
    print("🛠️ Criando Parser Simples")
    print("=" * 50)
    
    parser_code = '''
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
'''
    
    # Salvar e executar
    parser_file = Path('/mnt/c/Users/guilh/Documents/GitHub/avalon_fia/simple_parser.py')
    with open(parser_file, 'w') as f:
        f.write(parser_code)
    
    print(f"💾 Parser salvo em: {parser_file}")
    return parser_file

if __name__ == '__main__':
    debug_raw_portfolio()
    create_simple_portfolio_parser()