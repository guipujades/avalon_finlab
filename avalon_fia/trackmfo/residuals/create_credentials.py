#!/usr/bin/env python3
"""
Script para criar arquivo de credenciais BTG
"""

import json
from pathlib import Path

def create_credentials_file():
    """Cria arquivo de credenciais de exemplo"""
    
    print("Configuração de Credenciais BTG API")
    print("=" * 40)
    
    # Perguntar ao usuário
    print("\nPor favor, forneça suas credenciais da API BTG:")
    client_id = input("Client ID: ").strip()
    client_secret = input("Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("\n❌ Erro: Client ID e Client Secret são obrigatórios!")
        return False
    
    # Criar estrutura
    credentials = {
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    # Salvar arquivo
    file_path = Path.home() / 'Desktop' / 'api_btg_info.json'
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(credentials, f, indent=2)
        
        print(f"\n✅ Arquivo criado com sucesso: {file_path}")
        print("\nAgora você pode executar:")
        print("  python run_mfo_capture.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao criar arquivo: {e}")
        return False


if __name__ == '__main__':
    create_credentials_file()