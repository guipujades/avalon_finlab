#!/usr/bin/env python3
"""
Script para atualizar dados da API BTG
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Adicionar trackfia ao path
sys.path.append(str(Path(__file__).parent / 'trackfia'))

def update_fund_data():
    """Atualiza dados do fundo via API BTG"""
    print("🔄 Atualizando dados do fundo...")
    
    try:
        from api_btg_funds import fund_data_corrected
        import pickle as pkl
        
        # Diretório dos dados
        pickle_dir = Path('/mnt/c/Users/guilh/Documents/GitHub/database/dados_api')
        pickle_dir.mkdir(parents=True, exist_ok=True)
        
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"📅 Data: {current_date}")
        print("🌐 Conectando à API BTG...")
        
        # Obter dados da API
        df_xml, data_xml, header = fund_data_corrected('xml')
        
        print("💾 Salvando dados...")
        
        # Salvar os dados
        df_xml_path = pickle_dir / f'df_xml_{current_date}.pkl'
        data_xml_path = pickle_dir / f'data_xml_{current_date}.pkl'
        header_path = pickle_dir / f'header_{current_date}.pkl'
        
        with open(df_xml_path, 'wb') as f:
            pkl.dump(df_xml, f)
        with open(data_xml_path, 'wb') as f:
            pkl.dump(data_xml, f)
        with open(header_path, 'wb') as f:
            pkl.dump(header, f)
        
        print("✅ Dados atualizados com sucesso!")
        
        # Mostrar resumo
        pl = header.get('patliq', 0)
        cota = header.get('valorcota', 0)
        data_posicao = header.get('dtposicao', 'N/A')
        
        print(f"📊 Resumo dos dados:")
        print(f"   PL: R$ {pl:,.2f}")
        print(f"   Cota: {cota}")
        print(f"   Data posição: {data_posicao}")
        print(f"   Ativos: {len(data_xml) if isinstance(data_xml, list) else 'N/A'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao atualizar dados: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🏦 Avalon FIA - Atualização de Dados")
    print("=" * 40)
    
    if update_fund_data():
        print("\n🎉 Atualização concluída com sucesso!")
        print("💡 Agora você pode executar o dashboard com: python3 run_minimal.py")
    else:
        print("\n❌ Falha na atualização dos dados")
        print("🔧 Verifique sua conexão e credenciais da API")
    
    input("\nPressione Enter para sair...")

if __name__ == '__main__':
    main()