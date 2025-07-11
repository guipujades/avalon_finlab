#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import shutil
from database_schema import DatabaseManager
from config import initialize_config


def setup_environment():
    print("🚀 Configurando ambiente Avalon Fund Tracker...")
    
    # 1. Criar diretórios necessários
    directories = [
        "logs",
        "data",
        "internal_data",
        "temp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Diretório '{directory}' criado")
    
    # 2. Verificar arquivo .env
    if not Path(".env").exists():
        if Path(".env.example").exists():
            shutil.copy(".env.example", ".env")
            print("✓ Arquivo .env criado a partir do .env.example")
            print("⚠️  IMPORTANTE: Edite o arquivo .env com suas credenciais")
        else:
            print("❌ Arquivo .env.example não encontrado")
            return False
    
    # 3. Inicializar configuração
    try:
        config = initialize_config()
        print("✓ Configuração carregada")
    except Exception as e:
        print(f"❌ Erro ao carregar configuração: {e}")
        return False
    
    # 4. Criar banco de dados
    try:
        db = DatabaseManager(config.database.connection_string)
        db.create_tables()
        db.init_default_data()
        print("✓ Banco de dados criado e inicializado")
    except Exception as e:
        print(f"❌ Erro ao criar banco de dados: {e}")
        return False
    
    print("\n✅ Setup concluído com sucesso!")
    print("\nPróximos passos:")
    print("1. Edite o arquivo .env com suas credenciais")
    print("2. Execute: python internal_runner.py")
    
    return True


if __name__ == "__main__":
    if not setup_environment():
        sys.exit(1)