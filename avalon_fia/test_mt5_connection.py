#!/usr/bin/env python3
"""
Script para testar a conexão com MetaTrader 5
"""

import sys
from pathlib import Path

print("=== Teste de Conexão MetaTrader 5 ===\n")

# Tentar importar MT5
try:
    import MetaTrader5 as mt5
    print("✅ MetaTrader5 importado com sucesso")
except ImportError:
    print("❌ MetaTrader5 não está instalado")
    print("   Execute: pip install MetaTrader5")
    sys.exit(1)

# Configurações
mt5_path = Path('C:/', 'Program Files', 'Rico - MetaTrader 5', 'terminal64.exe')
server = 'GenialInvestimentos-PRD'
login = 156691
password = 'Avca@1985'

print(f"\nConfiguração:")
print(f"  Caminho: {mt5_path}")
print(f"  Servidor: {server}")
print(f"  Login: {login}")
print(f"  Senha: {'*' * len(password)}")

# Verificar se o arquivo existe
if not mt5_path.exists():
    print(f"\n❌ MetaTrader não encontrado em: {mt5_path}")
    print("   Verifique se o MetaTrader está instalado corretamente")
    sys.exit(1)

print(f"\n✅ MetaTrader encontrado")

# Tentar inicializar
print("\nTentando conectar...")
if not mt5.initialize(path=str(mt5_path), server=server, login=login, password=password):
    print(f"❌ Falha ao inicializar MetaTrader: {mt5.last_error()}")
    sys.exit(1)

print("✅ MetaTrader inicializado com sucesso!")

# Obter informações da conta
account_info = mt5.account_info()
if account_info:
    print("\nInformações da conta:")
    print(f"  Nome: {account_info.name}")
    print(f"  Servidor: {account_info.server}")
    print(f"  Empresa: {account_info.company}")
    print(f"  Saldo: {account_info.balance}")
    print(f"  Moeda: {account_info.currency}")

# Testar símbolos
print("\nTestando símbolos de mercado:")
test_symbols = ['PETR4', 'VALE3', 'IBOV', 'USDBRL']

for symbol in test_symbols:
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info:
        print(f"  ✅ {symbol}: Disponível")
    else:
        print(f"  ❌ {symbol}: Não encontrado")

# Finalizar
mt5.shutdown()
print("\n✅ Teste concluído com sucesso!")
print("\nO MetaTrader 5 está configurado corretamente.")
print("Você pode executar o dashboard completo agora.")