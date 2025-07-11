#!/usr/bin/env python3
"""
Script de debug para testar o processamento do portfolio
"""

import sys
import os
import pickle as pkl
from pathlib import Path
from datetime import datetime

# Adicionar o diretório ao path
sys.path.append(str(Path(__file__).parent))

def test_portfolio_processing():
    """Testa o processamento do portfolio sem Flask"""
    
    print("🔍 Testando processamento do portfolio...")
    
    # Configurar caminhos
    current_date = datetime.now().strftime('%Y-%m-%d')
    pickle_dir = Path('/mnt/c/Users/guilh/Documents/GitHub/database/dados_api')
    
    # Caminhos dos arquivos pickle
    df_xml_path = pickle_dir / f'df_xml_{current_date}.pkl'
    data_xml_path = pickle_dir / f'data_xml_{current_date}.pkl'
    header_path = pickle_dir / f'header_{current_date}.pkl'
    
    print(f"📅 Data atual: {current_date}")
    print(f"📁 Diretório pickle: {pickle_dir}")
    
    # Verificar se arquivos existem
    print(f"📄 Header existe: {header_path.exists()}")
    print(f"📄 DF XML existe: {df_xml_path.exists()}")
    print(f"📄 Data XML existe: {data_xml_path.exists()}")
    
    if not all(p.exists() for p in [df_xml_path, data_xml_path, header_path]):
        print("❌ Nem todos os arquivos estão disponíveis")
        return False
    
    try:
        # Carregar header
        with open(header_path, 'rb') as f:
            header = pkl.load(f)
        
        # Carregar data_xml
        with open(data_xml_path, 'rb') as f:
            data_xml = pkl.load(f)
        
        print("✅ Dados carregados com sucesso!")
        
        # Extrair informações do header
        pl_fundo = header.get('patliq', 0)
        data_dados = header.get('dtposicao', datetime.now())
        cota_fia = header.get('valorcota', 0)
        a_receber = header.get('valorreceber', 0)
        a_pagar = header.get('valorpagar', 0)
        
        print("🏦 Informações do fundo:")
        print(f"  PL: R$ {pl_fundo:,.2f}")
        print(f"  Cota: {cota_fia}")
        print(f"  Data posição: {data_dados}")
        print(f"  A receber: R$ {a_receber:,.2f}")
        print(f"  A pagar: R$ {a_pagar:,.2f}")
        
        # Processar dados XML simples
        try:
            # Tentar importar pandas
            import pandas as pd
            
            # Carregar DF XML
            with open(df_xml_path, 'rb') as f:
                df_xml = pkl.load(f)
            
            print("📊 Dados do DataFrame:")
            print(f"  Total de posições: {len(df_xml)}")
            
            if not df_xml.empty:
                print(f"  Tipos de ativos: {list(df_xml['tipo'].unique())}")
                print(f"  Colunas disponíveis: {list(df_xml.columns)}")
                
                # Agrupar por tipo
                portfolio_summary = {}
                for tipo in df_xml['tipo'].unique():
                    assets = df_xml[df_xml['tipo'] == tipo]
                    total_val = assets['valorfindisp'].sum() if 'valorfindisp' in assets.columns else 0
                    portfolio_summary[tipo] = {
                        'count': int(len(assets)),
                        'total_value': float(total_val)
                    }
                
                print("📈 Resumo do portfolio:")
                for tipo, info in portfolio_summary.items():
                    print(f"  {tipo}: {info['count']} posições, R$ {info['total_value']:,.2f}")
                
                # Calcular métricas básicas
                total_ativos = df_xml['valorfindisp'].sum() if 'valorfindisp' in df_xml.columns else 0
                enquadramento = total_ativos / pl_fundo if pl_fundo > 0 else 0
                
                print(f"📊 Métricas:")
                print(f"  Total ativos: R$ {total_ativos:,.2f}")
                print(f"  Enquadramento: {enquadramento:.2%}")
                
                return True
                
        except ImportError:
            print("⚠️ Pandas não disponível, processando dados brutos...")
            
            # Processar dados sem pandas
            if isinstance(data_xml, list):
                print(f"  Elementos no data_xml: {len(data_xml)}")
                
                # Tentar extrair informações básicas
                ativos_count = 0
                tipos_set = set()
                
                for item in data_xml:
                    if isinstance(item, dict):
                        if 'tipo' in item:
                            tipos_set.add(item['tipo'])
                        ativos_count += 1
                
                print(f"  Ativos processados: {ativos_count}")
                print(f"  Tipos encontrados: {list(tipos_set)}")
                
                return True
            
    except Exception as e:
        print(f"❌ Erro durante processamento: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_portfolio_processing()