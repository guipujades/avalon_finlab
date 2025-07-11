#!/usr/bin/env python3
"""
Script de teste para verificar a integracao com a API BTG apos as mudancas de 21/01
"""

import json
from pathlib import Path
from datetime import datetime
import sys
import os

# Adicionar o diretorio trackfia ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'trackfia'))

from api_btg_utils import auth_apiBTG, get_position_by_partner_refresh, get_partner_position, portfolio_api

def test_new_api_endpoints():
    """Testa os novos endpoints da API BTG"""
    
    print("=== TESTE DOS NOVOS ENDPOINTS API BTG ===\n")
    
    # Carregar configuracoes
    json_path = Path.home() / 'Desktop' / 'api_btg_info.json'
    
    if not json_path.exists():
        print(f"ERRO: Arquivo de configuracao nao encontrado em {json_path}")
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    print("1. Autenticando na API BTG...")
    try:
        token, data = auth_apiBTG(config)
        print("   ✓ Autenticacao bem-sucedida\n")
    except Exception as e:
        print(f"   ✗ Erro na autenticacao: {e}")
        return
    
    # Testar refresh de posicoes
    print("2. Testando endpoint get-position-by-partner-refresh...")
    try:
        refresh_result = get_position_by_partner_refresh(token)
        if refresh_result:
            print("   ✓ Refresh iniciado com sucesso")
            print(f"   Resposta: {refresh_result}\n")
        else:
            print("   ✗ Falha no refresh\n")
    except Exception as e:
        print(f"   ✗ Erro no refresh: {e}\n")
    
    # Aguardar processamento
    print("3. Aguardando processamento (10 segundos)...")
    import time
    time.sleep(10)
    
    # Testar obtencao de posicoes
    print("\n4. Testando endpoint get-partner-position...")
    try:
        position_response = get_partner_position(token)
        if position_response and position_response.status_code == 200:
            print("   ✓ Posicoes obtidas com sucesso")
            print(f"   Content-Type: {position_response.headers.get('Content-Type')}")
            print(f"   Tamanho do arquivo: {len(position_response.content)} bytes\n")
        else:
            print("   ✗ Falha ao obter posicoes\n")
    except Exception as e:
        print(f"   ✗ Erro ao obter posicoes: {e}\n")
    
    # Testar funcao portfolio_api atualizada
    print("5. Testando funcao portfolio_api atualizada...")
    try:
        date_today = datetime.today().strftime('%Y-%m-%d')
        response = portfolio_api(token, data, start_date=date_today, end_date=date_today, type_report=3, page_size=100)
        
        if response and response.status_code == 200:
            print("   ✓ Portfolio obtido com sucesso")
            print(f"   Content-Type: {response.headers.get('Content-Type')}")
            print(f"   Tamanho do arquivo: {len(response.content)} bytes")
        else:
            print("   ✗ Falha ao obter portfolio")
            if response:
                print(f"   Status: {response.status_code}")
                print(f"   Resposta: {response.text}")
    except Exception as e:
        print(f"   ✗ Erro ao obter portfolio: {e}")
    
    print("\n=== FIM DOS TESTES ===")


if __name__ == "__main__":
    test_new_api_endpoints()