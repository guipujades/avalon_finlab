#!/usr/bin/env python3
"""
Script para executar o sistema MFO completo
Inicia o servidor e captura dados
"""

import subprocess
import time
import sys
import os
import threading
import webbrowser


def run_server():
    """Executa o servidor Flask em thread separada"""
    print("Iniciando servidor Flask...")
    subprocess.run([sys.executable, "app.py"])


def main():
    print("=" * 60)
    print("Sistema MFO - Iniciando servidor e captura")
    print("=" * 60)
    
    # Iniciar servidor em thread separada
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Aguardar servidor iniciar
    print("\nAguardando servidor iniciar...")
    time.sleep(5)
    
    # Executar captura
    print("\nExecutando captura de dados...")
    result = subprocess.run([sys.executable, "run_mfo_capture.py"], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    # Se sucesso, abrir navegador
    if "✅ SUCESSO!" in result.stdout:
        print("\nAbrindo navegador...")
        webbrowser.open("http://localhost:5000")
        
        print("\n" + "=" * 60)
        print("Sistema rodando!")
        print("Acesse: http://localhost:5000")
        print("Login: admin")
        print("Senha: Avalon@123")
        print("\nPressione Ctrl+C para parar")
        print("=" * 60)
        
        # Manter rodando
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nParando sistema...")
    else:
        print("\nErro na captura. Verifique os logs acima.")


if __name__ == '__main__':
    main()