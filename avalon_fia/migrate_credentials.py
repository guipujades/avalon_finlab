#!/usr/bin/env python3
"""
Script para migrar credenciais do formato antigo para o novo
"""

import json
from pathlib import Path
import shutil


def migrate_credentials():
    """Migra credenciais do formato antigo para o novo"""
    
    # Caminhos dos arquivos
    old_file = Path.home() / 'Desktop' / 'api_btg_info.json'
    new_file = Path.home() / 'Desktop' / 'api_btg_access.json'
    
    print("=== MIGRAÇÃO DE CREDENCIAIS BTG ===\n")
    
    # Verificar se arquivo antigo existe
    if not old_file.exists():
        print(f"❌ Arquivo antigo não encontrado: {old_file}")
        return False
    
    # Verificar se novo arquivo já existe
    if new_file.exists():
        print(f"⚠️  Arquivo novo já existe: {new_file}")
        backup = input("Deseja fazer backup do arquivo existente? (s/n): ")
        if backup.lower() == 's':
            backup_file = new_file.with_suffix('.json.bak')
            shutil.copy2(new_file, backup_file)
            print(f"✅ Backup criado: {backup_file}")
    
    # Ler arquivo antigo
    try:
        with open(old_file, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
        
        print("\n📄 Credenciais encontradas no arquivo antigo:")
        print(f"   client_id: {old_data.get('client_id', 'NÃO ENCONTRADO')}")
        print(f"   client_secret: {'*' * 20} (oculto)")
        
        # Criar novo formato (mesmo conteúdo)
        new_data = {
            'client_id': old_data.get('client_id'),
            'client_secret': old_data.get('client_secret')
        }
        
        # Salvar novo arquivo
        with open(new_file, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, indent=2)
        
        print(f"\n✅ Novo arquivo criado: {new_file}")
        
        # Perguntar se quer manter o antigo
        keep_old = input("\nDeseja manter o arquivo antigo? (s/n): ")
        if keep_old.lower() != 's':
            old_file.rename(old_file.with_suffix('.json.old'))
            print(f"✅ Arquivo antigo renomeado para: {old_file.with_suffix('.json.old')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao processar arquivos: {e}")
        return False


if __name__ == "__main__":
    if migrate_credentials():
        print("\n✅ Migração concluída com sucesso!")
        print("\nPróximos passos:")
        print("1. Execute: python trackfia/btg_api_client.py")
        print("2. Para testar a conexão")
    else:
        print("\n❌ Migração falhou!")