#!/usr/bin/env python3
"""
Investigar que tipos de ativos existem no portfolio
"""

import pickle as pkl
from pathlib import Path
from collections import Counter

def investigate_portfolio_assets():
    """Investigar todos os tipos de ativos no portfolio"""
    print("🔍 Investigando Ativos do Portfolio")
    print("=" * 50)
    
    try:
        pickle_dir = Path('/mnt/c/Users/guilh/Documents/GitHub/database/dados_api')
        
        # Buscar arquivo mais recente
        data_files = sorted(pickle_dir.glob('data_xml_*.pkl'), reverse=True)
        
        if not data_files:
            print("❌ Nenhum arquivo encontrado")
            return
        
        # Carregar dados
        with open(data_files[0], 'rb') as f:
            data_xml = pkl.load(f)
        
        print(f"📊 Total de ativos: {len(data_xml)}")
        
        # Contar tipos
        tipos = Counter(asset.get('tipo', 'N/A') for asset in data_xml)
        print(f"\n📈 Tipos de ativos:")
        for tipo, count in tipos.most_common():
            print(f"  {tipo}: {count} ativos")
        
        # Investigar cada tipo
        for tipo in tipos.keys():
            print(f"\n🔍 Analisando tipo: {tipo}")
            assets_of_type = [asset for asset in data_xml if asset.get('tipo', '') == tipo]
            
            if assets_of_type:
                # Mostrar estrutura do primeiro ativo
                first_asset = assets_of_type[0]
                print(f"  📝 Campos disponíveis: {list(first_asset.keys())}")
                
                # Mostrar alguns exemplos
                for i, asset in enumerate(assets_of_type[:3]):
                    identifier = (asset.get('codigo') or 
                                 asset.get('cusip') or 
                                 asset.get('isin') or 
                                 asset.get('codativo') or 
                                 f"item_{i}")
                    
                    valor = asset.get('valorfindisp', 0)
                    quantidade = asset.get('quantidade') or asset.get('qtdisponivel', 0)
                    
                    print(f"    {identifier}: valor=R${valor:.2f}, qtd={quantidade}")
        
        # Calcular valor total por tipo
        print(f"\n💰 Valor por tipo:")
        total_geral = 0
        for tipo in tipos.keys():
            assets_of_type = [asset for asset in data_xml if asset.get('tipo', '') == tipo]
            valor_tipo = sum(asset.get('valorfindisp', 0) for asset in assets_of_type)
            print(f"  {tipo}: R$ {valor_tipo:,.2f}")
            total_geral += valor_tipo
        
        print(f"\n🎯 Valor total do portfolio: R$ {total_geral:,.2f}")
        
        # Verificar se existe algum com 'codigo' (provável ação)
        ativos_com_codigo = [asset for asset in data_xml if asset.get('codigo')]
        print(f"\n📋 Ativos com campo 'codigo': {len(ativos_com_codigo)}")
        
        if ativos_com_codigo:
            print("  Exemplos:")
            for asset in ativos_com_codigo[:5]:
                codigo = asset.get('codigo', 'N/A')
                tipo = asset.get('tipo', 'N/A')
                valor = asset.get('valorfindisp', 0)
                print(f"    {codigo} ({tipo}): R$ {valor:.2f}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    investigate_portfolio_assets()