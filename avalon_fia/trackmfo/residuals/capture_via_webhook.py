#!/usr/bin/env python3
"""
Script para capturar carteiras via webhook API BTG
Versão simplificada sem servidor webhook
"""

import json
import requests
import base64
import uuid
import time
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CapturaViaWebhook:
    """Captura dados usando webhook API"""
    
    def __init__(self):
        self.json_file = Path.home() / 'Desktop' / 'api_btg_access.json'
        self.output_dir = Path.home() / 'Desktop' / 'Carteiras_BTG'
        self.output_dir.mkdir(exist_ok=True)
        
    def get_token(self):
        """Obtém token da API"""
        with open(self.json_file) as f:
            data = json.load(f)
        
        credentials = f"{data['client_id']}:{data['client_secret']}"
        base64_string = base64.b64encode(credentials.encode()).decode()
        
        url = 'https://api.btgpactual.com/iaas-auth/api/v1/authorization/oauth2/accesstoken'
        headers = {
            'x-id-partner-request': str(uuid.uuid4()),
            'Authorization': f'Basic {base64_string}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = requests.post(url, data={'grant_type': 'client_credentials'}, headers=headers)
        
        if response.status_code == 200:
            return response.headers.get('access_token')
        return None
    
    def solicitar_posicoes(self, token, date=None):
        """Solicita posições via webhook"""
        
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        headers = {
            'x-id-partner-request': str(uuid.uuid4()),
            'access_token': token,
            'Content-Type': 'application/json'
        }
        
        # URL temporária para receber webhook (não será usada realmente)
        webhook_url = "https://webhook.site/teste-btg"
        
        print(f"\nSolicitando posições para data: {date}")
        
        # 1. Tentar webhook de posições
        url = 'https://api.btgpactual.com/iaas-api-position/api/v1/position/webhook'
        body = {
            "webhookUrl": webhook_url,
            "date": date
        }
        
        response = requests.post(url, headers=headers, json=body)
        print(f"Status webhook posições: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Solicitação de posições enviada")
            return response.json()
        else:
            print(f"Response: {response.text}")
            
        # 2. Tentar refresh de posições
        print("\nTentando refresh de posições...")
        url = 'https://api.btgpactual.com/iaas-api-position/api/v1/position/refresh'
        body = {"date": date}
        
        response = requests.post(url, headers=headers, json=body)
        print(f"Status refresh: {response.status_code}")
        
        if response.status_code in [200, 202]:
            print("✅ Refresh solicitado")
            # Aguardar processamento
            time.sleep(5)
            
            # Tentar obter arquivo do parceiro novamente
            url = 'https://api.btgpactual.com/iaas-api-position/api/v1/position/partner'
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('response') and data['response'].get('url'):
                    print("✅ Arquivo de posições disponível!")
                    return data
        
        return None
    
    def processar_resposta_webhook(self, response_data):
        """Processa resposta do webhook"""
        
        if not response_data:
            print("❌ Sem dados para processar")
            return
        
        # Salvar resposta para análise
        output_file = self.output_dir / f'webhook_response_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(response_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Resposta salva em: {output_file}")
        print("\nAnálise da resposta:")
        print(f"- Tipo: {type(response_data)}")
        
        if isinstance(response_data, dict):
            print(f"- Chaves: {list(response_data.keys())}")
            
            # Se tiver URL de arquivo
            if 'response' in response_data:
                resp = response_data['response']
                if isinstance(resp, dict) and 'url' in resp:
                    print(f"\n📥 URL de download encontrada: {resp['url']}")
                    print("\nPróximos passos:")
                    print("1. Baixar o arquivo ZIP da URL")
                    print("2. Extrair os JSONs das contas")
                    print("3. Processar cada conta individualmente")
                    
                    # Aqui você poderia implementar o download e processamento
                    # Similar ao que fizemos antes
    
    def solicitar_movimentacoes(self, token, account_number, start_date=None, end_date=None):
        """Solicita movimentações de uma conta"""
        
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        headers = {
            'x-id-partner-request': str(uuid.uuid4()),
            'access_token': token,
            'Content-Type': 'application/json'
        }
        
        webhook_url = "https://webhook.site/teste-btg"
        
        print(f"\nSolicitando movimentações da conta {account_number}")
        print(f"Período: {start_date} a {end_date}")
        
        url = f'https://api.btgpactual.com/iaas-api-operation/api/v1/operation/history/{account_number}'
        params = {
            'startDate': start_date,
            'endDate': end_date,
            'webhookUrl': webhook_url
        }
        
        response = requests.get(url, headers=headers, params=params)
        print(f"Status: {response.status_code}")
        
        if response.status_code in [200, 202]:
            print("✅ Solicitação enviada")
            return response.json()
        else:
            print(f"Response: {response.text}")
            return None
    
    def solicitar_rentabilidade(self, token, month, year):
        """Solicita rentabilidade mensal"""
        
        headers = {
            'x-id-partner-request': str(uuid.uuid4()),
            'access_token': token,
            'Content-Type': 'application/json'
        }
        
        webhook_url = "https://webhook.site/teste-btg"
        
        print(f"\nSolicitando rentabilidade {month}/{year}")
        
        url = 'https://api.btgpactual.com/api-partner-report-hub/api/v1/report/customer-profitability'
        body = {
            'referenceMonth': str(month).zfill(2),
            'referenceYear': str(year),
            'webhookUrl': webhook_url
        }
        
        response = requests.post(url, headers=headers, json=body)
        print(f"Status: {response.status_code}")
        
        if response.status_code in [200, 202]:
            print("✅ Solicitação enviada")
            return response.json()
        else:
            print(f"Response: {response.text}")
            return None


def main():
    """Função principal"""
    print("="*60)
    print("Captura de Carteiras BTG via Webhook")
    print("="*60)
    
    captura = CapturaViaWebhook()
    
    # Obter token
    token = captura.get_token()
    if not token:
        print("❌ Falha ao obter token")
        return
    
    print("✅ Token obtido")
    
    # Menu de opções
    while True:
        print("\n" + "-"*40)
        print("Escolha uma opção:")
        print("1. Solicitar posições (todas as contas)")
        print("2. Solicitar movimentações (conta específica)")
        print("3. Solicitar rentabilidade mensal")
        print("4. Sair")
        
        opcao = input("\nOpção: ").strip()
        
        if opcao == '1':
            # Posições
            date = input("Data (YYYY-MM-DD) ou Enter para hoje: ").strip()
            if not date:
                date = None
            
            result = captura.solicitar_posicoes(token, date)
            captura.processar_resposta_webhook(result)
            
        elif opcao == '2':
            # Movimentações
            account = input("Número da conta: ").strip()
            if account:
                result = captura.solicitar_movimentacoes(token, account)
                captura.processar_resposta_webhook(result)
            
        elif opcao == '3':
            # Rentabilidade
            month = input("Mês (1-12): ").strip()
            year = input("Ano (YYYY): ").strip()
            
            if month and year:
                result = captura.solicitar_rentabilidade(token, month, year)
                captura.processar_resposta_webhook(result)
                
        elif opcao == '4':
            break
        
        else:
            print("Opção inválida")
    
    print("\n✅ Finalizado")


if __name__ == '__main__':
    main()