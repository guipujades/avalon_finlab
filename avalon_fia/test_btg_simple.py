#!/usr/bin/env python3
"""
Teste simples e direto da API BTG focando no problema do erro 404
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), 'trackfia'))

from api_btg_utils import auth_apiBTG, portfolio_api
from api_btg import fund_data


def main():
    print("=== TESTE SIMPLES API BTG ===\n")
    
    # 1. Carregar configurações
    json_path = Path.home() / 'Desktop' / 'api_btg_info.json'
    with open(json_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    print("1. Autenticando...")
    token, data = auth_apiBTG(config)
    
    if token:
        print("✓ Token obtido com sucesso!\n")
    else:
        print("✗ Falha na autenticação")
        return
    
    # 2. Testar método tradicional que estava funcionando
    print("2. Testando método tradicional (Portfolio)...")
    
    # Tentar com data de hoje
    date_today = datetime.today().strftime('%Y-%m-%d')
    print(f"   Data: {date_today}")
    
    response = portfolio_api(token, data, 
                           start_date=date_today, 
                           end_date=date_today, 
                           type_report=3, 
                           page_size=100)
    
    if response and response.status_code == 200:
        print("   ✓ Resposta obtida!")
        print(f"   Content-Type: {response.headers.get('Content-Type')}")
    else:
        print(f"   ✗ Erro: {response.status_code if response else 'Sem resposta'}")
        
        # Tentar com data anterior
        print("\n3. Tentando com datas anteriores...")
        for days_back in [1, 2, 3, 5, 10]:
            date_ref = datetime.today() - timedelta(days=days_back)
            date_str = date_ref.strftime('%Y-%m-%d')
            print(f"\n   Tentando com {date_str} ({days_back} dias atrás)...")
            
            response = portfolio_api(token, data,
                                   start_date=date_str,
                                   end_date=date_str,
                                   type_report=3,
                                   page_size=100)
            
            if response and response.status_code == 200:
                print(f"   ✓ Sucesso com data {date_str}!")
                content_type = response.headers.get('Content-Type', '')
                
                if 'application/json' in content_type:
                    try:
                        result = response.json()
                        print(f"   Ticket: {result.get('ticket', 'N/A')}")
                    except:
                        pass
                elif 'application/zip' in content_type or 'application/octet-stream' in content_type:
                    print(f"   Arquivo recebido: {len(response.content)} bytes")
                
                break
            else:
                print(f"   ✗ Erro: {response.status_code if response else 'Sem resposta'}")
    
    # 4. Testar usando a função fund_data
    print("\n4. Testando função fund_data()...")
    try:
        df_xml, data_xml, header = fund_data(find_type='xml')
        
        if df_xml is not None and not df_xml.empty:
            print("   ✓ Dados XML obtidos com sucesso!")
            print(f"   Registros: {len(df_xml)}")
            if header:
                print(f"   Fundo: {header.get('nome', 'N/A')}")
                print(f"   Data: {header.get('dtposicao', 'N/A')}")
                print(f"   PL: R$ {header.get('patliq', 0):,.2f}")
        else:
            print("   ✗ Não foi possível obter dados XML")
    except Exception as e:
        print(f"   ✗ Erro: {e}")


if __name__ == "__main__":
    main()