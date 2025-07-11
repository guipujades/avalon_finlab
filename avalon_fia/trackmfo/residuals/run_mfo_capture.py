#!/usr/bin/env python3
"""
Script principal para executar captura de dados MFO
Este é o script que você deve usar!
"""

import sys
import time
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Executa o processo completo de captura MFO"""
    
    print("=" * 60)
    print("Sistema de Captura MFO - Multi Family Office")
    print("=" * 60)
    
    # Importar módulo de captura v2 (usa API de fundos)
    from capture_mfo_clients_v2 import MFOClientCaptureV2 as MFOClientCapture
    
    # Verificar se o app está rodando
    print("\n1. Verificando se o app MFO está rodando...")
    print("   Se não estiver, execute em outro terminal:")
    print("   $ python app.py")
    print("\n   Aguardando 5 segundos...")
    time.sleep(5)
    
    # Criar instância do capturador
    print("\n2. Iniciando captura de dados...")
    capture = MFOClientCapture()
    
    # Executar captura e envio
    print("\n3. Capturando dados de todos os clientes MFO...")
    success = capture.run_capture_and_send(
        app_url='http://localhost:5000/update_data',
        use_cache=False  # Forçar captura nova
    )
    
    if success:
        print("\n✅ SUCESSO! Dados capturados e enviados para o app")
        
        # Mostrar resumo
        summary = capture.get_summary()
        print(f"\nResumo da captura:")
        print(f"- Total de clientes: {summary.get('total_clients', 0)}")
        print(f"- Valor total: R$ {summary.get('total_value', 0):,.2f}")
        
        print("\n4. Acesse o dashboard em: http://localhost:5000")
        print("   Login: admin")
        print("   Senha: Avalon@123")
        
    else:
        print("\n❌ ERRO na captura ou envio dos dados")
        print("\nPossíveis soluções:")
        print("1. Verifique se o app.py está rodando")
        print("2. Verifique as credenciais da API BTG")
        print("3. Verifique a conexão com a internet")
        print("4. Olhe os logs acima para mais detalhes")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()