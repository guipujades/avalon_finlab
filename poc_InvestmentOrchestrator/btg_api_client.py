#!/usr/bin/env python3
"""
Cliente BTG API - Versão Corrigida
Focado em: Token Real + Carteiras + Rentabilidade + Movimentação
"""

import os
import json
import base64
import uuid
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BTGAPIClient:
    """Cliente para APIs do BTG Pactual Digital - APENAS API REAL"""
    
    def __init__(self, credentials_path: Optional[str] = None, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        """
        Inicializa o cliente com credenciais
        
        Args:
            credentials_path: Caminho para arquivo JSON com credenciais
            client_id: ID do cliente (alternativa ao arquivo)
            client_secret: Secret do cliente (alternativa ao arquivo)
        """
        if credentials_path:
            self.credentials_path = Path(credentials_path)
            self.client_id, self.client_secret = self._load_credentials()
        elif client_id and client_secret:
            self.client_id = client_id
            self.client_secret = client_secret
            self.credentials_path = None
        else:
            raise ValueError("Forneça credentials_path OU client_id/client_secret")
        
        self.base_url = "https://api.btgpactual.com"
        self.token = None
        self.token_expiry = None
        
        logger.info("✅ BTG API Client inicializado (REAL API)")

    def _load_credentials(self) -> Tuple[str, str]:
        """Carrega credenciais do arquivo JSON"""
        try:
            with open(self.credentials_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data['client_id'], data['client_secret']
        except FileNotFoundError:
            raise FileNotFoundError(f"Arquivo de credenciais não encontrado: {self.credentials_path}")
        except KeyError as e:
            raise KeyError(f"Chave {e} não encontrada no arquivo de credenciais")

    def get_access_token(self) -> str:
        """
        Obtém token de acesso OAuth2 - CORRIGIDO
        
        Returns:
            Token de acesso válido
        """
        # Verifica se token ainda é válido
        if self.token and self.token_expiry and datetime.now() < self.token_expiry:
            logger.info("✅ Usando token válido existente")
            return self.token
        
        logger.info("🔄 Obtendo novo token de acesso...")
        
        # Codifica credenciais em Base64
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_b64 = base64.b64encode(auth_string.encode()).decode()
        
        # Prepara requisição OAuth2
        url = f"{self.base_url}/iaas-auth/api/v1/authorization/oauth2/accesstoken"
        headers = {
            'x-id-partner-request': str(uuid.uuid4()),
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # *** CORREÇÃO: Usar 'data' em vez de 'params' ***
        body_data = {'grant_type': 'client_credentials'}
        
        try:
            response = requests.post(url, headers=headers, data=body_data, timeout=30)
            
            if response.status_code == 200:
                # Token vem no header
                self.token = response.headers.get('access_token')
                if not self.token:
                    raise ValueError("Token não encontrado na resposta")
                
                # Define expiração (1 hora por padrão)
                self.token_expiry = datetime.now() + timedelta(hours=1)
                
                logger.info("✅ Token obtido com sucesso!")
                logger.info(f"🔑 Token: {self.token[:50]}...")
                return self.token
            else:
                logger.error(f"❌ Erro ao obter token: {response.status_code}")
                logger.error(f"Resposta: {response.text}")
                response.raise_for_status()
                
        except requests.RequestException as e:
            logger.error(f"❌ Erro de requisição: {e}")
            raise

    def _make_authenticated_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Faz requisição autenticada
        
        Args:
            method: Método HTTP
            endpoint: Endpoint da API
            **kwargs: Argumentos adicionais
            
        Returns:
            Response object
        """
        url = f"{self.base_url}{endpoint}"
        
        # Headers padrão
        headers = kwargs.get('headers', {})
        headers.update({
            'x-id-partner-request': str(uuid.uuid4()),
            'access_token': self.get_access_token(),
            'Content-Type': 'application/json'
        })
        kwargs['headers'] = headers
        kwargs.setdefault('timeout', 30)
        
        try:
            response = requests.request(method, url, **kwargs)
            
            if not response.ok:
                logger.error(f"❌ Erro na requisição {method} {endpoint}: {response.status_code}")
                logger.error(f"Resposta: {response.text}")
            
            response.raise_for_status()
            return response
            
        except requests.RequestException as e:
            logger.error(f"❌ Erro na requisição: {e}")
            raise

    # ============= CARTEIRAS DE CLIENTES =============

    def get_account_position(self, account_number: str) -> Dict:
        """
        Obtém posição completa de uma conta (carteira)
        
        Args:
            account_number: Número da conta
            
        Returns:
            Dados completos da posição
        """
        logger.info(f"📊 Obtendo posição da conta {account_number}")
        
        endpoint = f"/iaas-api-position/api/v1/position/{account_number}"
        
        try:
            response = self._make_authenticated_request('GET', endpoint)
            data = response.json()
            
            total_amount = data.get('TotalAmount', 0)
            logger.info(f"✅ Posição obtida - Total: R$ {total_amount:,.2f}")
            return data
            
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                logger.error(f"❌ Conta {account_number} não encontrada")
            raise

    def get_all_accounts_positions(self) -> Dict:
        """
        Obtém posições de todas as contas do parceiro
        
        Returns:
            Informações sobre o download das posições
        """
        logger.info("📊 Obtendo posições de todas as contas")
        
        endpoint = "/iaas-api-position/api/v1/position/partner"
        
        response = self._make_authenticated_request('GET', endpoint)
        data = response.json()
        
        logger.info("✅ URLs de download obtidas")
        return data

    def get_account_info(self, account_number: str) -> Dict:
        """
        Obtém informações básicas de uma conta
        
        Args:
            account_number: Número da conta
            
        Returns:
            Informações da conta
        """
        logger.info(f"ℹ️ Obtendo informações da conta {account_number}")
        
        endpoint = f"/iaas-account-management/api/v1/account-management/account/{account_number}/information"
        
        response = self._make_authenticated_request('GET', endpoint)
        data = response.json()
        
        logger.info("✅ Informações da conta obtidas")
        return data

    # ============= RENTABILIDADE =============

    def get_monthly_profitability(self, reference_month: str, reference_year: str) -> Dict:
        """
        Obtém rentabilidade mensal consolidada
        
        Args:
            reference_month: Mês (01-12)
            reference_year: Ano (YYYY)
            
        Returns:
            Dados de rentabilidade (via webhook)
        """
        logger.info(f"📈 Obtendo rentabilidade {reference_month}/{reference_year}")
        
        endpoint = "/api-partner-report-hub/api/v1/report/customer-profitability"
        
        body = {
            "referenceMonth": reference_month,
            "referenceYear": reference_year
        }
        
        response = self._make_authenticated_request('POST', endpoint, json=body)
        
        if response.status_code == 202:
            logger.info("✅ Requisição aceita - dados serão enviados via webhook")
        
        return response.json()

    # ============= MOVIMENTAÇÃO =============

    def get_account_movements(self, account_number: str, start_date: Optional[str] = None, 
                            end_date: Optional[str] = None) -> Dict:
        """
        Obtém histórico de movimentações
        
        Args:
            account_number: Número da conta
            start_date: Data inicial (YYYY-MM-DD)
            end_date: Data final (YYYY-MM-DD)
            
        Returns:
            Dados de movimentação (via webhook)
        """
        logger.info(f"📋 Obtendo movimentações da conta {account_number}")
        
        endpoint = f"/iaas-api-operation/api/v1/operation/history/{account_number}"
        
        params = {}
        if start_date:
            params['startDate'] = start_date
        if end_date:
            params['endDate'] = end_date
        
        response = self._make_authenticated_request('GET', endpoint, params=params)
        
        if response.status_code == 202:
            logger.info("✅ Requisição aceita - dados serão enviados via webhook")
        
        return response.json()

    # ============= MÉTODOS AUXILIARES =============

    def test_connection(self) -> bool:
        """
        Testa a conexão com a API
        
        Returns:
            True se conexão OK
        """
        try:
            logger.info("🔄 Testando conexão com API BTG...")
            token = self.get_access_token()
            
            if token:
                logger.info("✅ Conexão estabelecida com sucesso")
                return True
            else:
                logger.error("❌ Falha na obtenção do token")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro no teste de conexão: {e}")
            return False

    def search_artesanal_funds(self) -> Dict:
        """
        Busca específica por fundos Artesanal em todas as contas
        
        Returns:
            Dados consolidados dos fundos Artesanal
        """
        logger.info("🔍 Buscando fundos Artesanal em todas as contas...")
        
        try:
            # Primeiro, obter todas as posições
            all_positions = self.get_all_accounts_positions()
            
            # Aqui seria necessário fazer download e processar o ZIP
            # Por enquanto, retorna estrutura básica
            result = {
                "total_artesanal": 0,
                "accounts_with_artesanal": [],
                "fund_details": [],
                "data_source": "API Real BTG",
                "note": "Para implementação completa, é necessário processar ZIP de posições"
            }
            
            logger.info("⚠️ Implementação completa requer processamento do ZIP de posições")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro na busca Artesanal: {e}")
            raise

    def __repr__(self):
        return f"BTGAPIClient(base_url='{self.base_url}', authenticated={bool(self.token)})"


# ============= FUNÇÕES AUXILIARES =============

def create_btg_client() -> BTGAPIClient:
    """
    Cria cliente BTG real
    
    Returns:
        Cliente configurado
    """
    credentials_paths = [
        Path.home() / 'Desktop' / 'api_btg_access.json',
        Path.cwd() / 'api_btg_access.json',
        Path.cwd() / 'credentials' / 'api_btg_access.json'
    ]
    
    credentials_file = None
    for path in credentials_paths:
        if path.exists():
            credentials_file = str(path)
            break
    
    if not credentials_file:
        raise FileNotFoundError("Arquivo de credenciais não encontrado. Verifique: api_btg_access.json")
    
    logger.info(f"🔄 Criando cliente BTG real com credenciais: {credentials_file}")
    return BTGAPIClient(credentials_path=credentials_file)


if __name__ == "__main__":
    # Teste básico do código fornecido pelo usuário
    print("🧪 TESTE BÁSICO - TOKEN BTG")
    print("="*50)
    
    try:
        client = create_btg_client()
        token = client.get_access_token()
        print(f"✅ Token obtido: {token[:50]}...")
        
        # Testa conexão
        if client.test_connection():
            print("✅ Conexão OK - Sistema pronto!")
        
    except Exception as e:
        print(f"❌ Erro: {e}") 