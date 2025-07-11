#!/usr/bin/env python3
"""
Script de debug para verificar especificamente os dados de ações
"""

import pickle as pkl
import sys
from pathlib import Path
from datetime import datetime

# Adicionar trackfia ao path
sys.path.append(str(Path(__file__).parent))

def debug_stocks_data():
    """Debug detalhado dos dados de ações"""
    print("🔍 Debug: Dados de Ações")
    print("=" * 50)
    
    try:
        current_date = datetime.now().strftime('%Y-%m-%d')
        pickle_dir = Path('/mnt/c/Users/guilh/Documents/GitHub/database/dados_api')
        
        # Carregar dados
        df_xml_path = pickle_dir / f'df_xml_{current_date}.pkl'
        
        if not df_xml_path.exists():
            print(f"❌ Arquivo não encontrado: {df_xml_path}")
            return
        
        with open(df_xml_path, 'rb') as f:
            df_xml = pkl.load(f)
        
        print(f"✅ Dados carregados: {len(df_xml)} registros")
        print(f"📊 Colunas disponíveis: {list(df_xml.columns)}")
        print()
        
        # Verificar tipos de ativos
        tipos = df_xml['tipo'].value_counts() if 'tipo' in df_xml.columns else {}
        print("📈 Tipos de ativos:")
        for tipo, count in tipos.items():
            print(f"  {tipo}: {count} registros")
        print()
        
        # Focar em ações
        if 'tipo' in df_xml.columns:
            df_acoes = df_xml[df_xml['tipo'] == 'ACOES']
            print(f"🎯 Ações encontradas: {len(df_acoes)} registros")
            
            if len(df_acoes) > 0:
                print("\n📋 Primeiras 5 ações:")
                for idx, row in df_acoes.head().iterrows():
                    codigo = row.get('codigo', 'N/A')
                    quantidade = row.get('quantidade', 'N/A')
                    preco_medio = row.get('precomedio', 'N/A')
                    valor_fin = row.get('valorfindisp', 'N/A')
                    
                    print(f"  {codigo}:")
                    print(f"    Quantidade: {quantidade}")
                    print(f"    Preço Médio: {preco_medio}")
                    print(f"    Valor Financeiro: {valor_fin}")
                    print(f"    Tipos: {type(quantidade)} | {type(preco_medio)} | {type(valor_fin)}")
                    
                    # Verificar se são NaN
                    if str(quantidade).lower() == 'nan':
                        print(f"    ⚠️ Quantidade é NaN!")
                    if str(preco_medio).lower() == 'nan':
                        print(f"    ⚠️ Preço médio é NaN!")
                    if str(valor_fin).lower() == 'nan':
                        print(f"    ⚠️ Valor financeiro é NaN!")
                    print()
        
        # Verificar estrutura dos dados
        print("🔍 Amostra de dados brutos:")
        if len(df_xml) > 0:
            primeiro_registro = df_xml.iloc[0]
            for col, value in primeiro_registro.items():
                print(f"  {col}: {value} ({type(value)})")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

def test_portfolio_processor():
    """Testar o processador de portfolio"""
    print("\n" + "=" * 50)
    print("🧪 Testando Portfolio Processor")
    print("=" * 50)
    
    try:
        sys.path.append('/mnt/c/Users/guilh/Documents/GitHub/avalon_fia')
        from trackfia.portfolio_processor import process_portfolio_from_api
        
        portfolio_data = process_portfolio_from_api()
        
        if portfolio_data:
            positions = portfolio_data.get('positions', {})
            stocks = portfolio_data.get('stocks', {})
            options = portfolio_data.get('options', {})
            
            print(f"✅ Portfolio processado:")
            print(f"  Total de posições: {len(positions)}")
            print(f"  Ações: {len(stocks)}")
            print(f"  Opções: {len(options)}")
            
            if stocks:
                print(f"\n📈 Primeiras 3 ações processadas:")
                for i, (ticker, data) in enumerate(list(stocks.items())[:3]):
                    print(f"  {ticker}:")
                    print(f"    Quantidade: {data.get('quantity', 'N/A')}")
                    print(f"    Preço Médio: {data.get('average_price', 'N/A')}")
                    print(f"    Valor Atual: {data.get('current_value', 'N/A')}")
                    print(f"    % Portfolio: {data.get('pcts_port', 'N/A'):.2f}%")
            else:
                print("❌ Nenhuma ação encontrada!")
        else:
            print("❌ Falha ao processar portfolio")
            
    except Exception as e:
        print(f"❌ Erro no processor: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_stocks_data()
    test_portfolio_processor()