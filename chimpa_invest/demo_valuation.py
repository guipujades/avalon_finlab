#!/usr/bin/env python3
"""
Demonstração do Sistema de Valuation
====================================
Script interativo para demonstrar o valuation de empresas
"""

import os
import sys

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def mostrar_menu():
    print("=" * 60)
    print("       SISTEMA DE VALUATION - CHIMPA INVEST")
    print("=" * 60)
    print("\nEMPRESAS DISPONÍVEIS PARA DEMONSTRAÇÃO:\n")
    print("1. VALE S.A. (VALE3)")
    print("2. PETROBRAS (PETR4)")
    print("3. ITAÚ UNIBANCO (ITUB4)")
    print("4. AMBEV (ABEV3)")
    print("5. Buscar outra empresa")
    print("\n0. Sair")
    print("\n" + "=" * 60)

def executar_valuation(empresa, preco=None):
    """Executa valuation de uma empresa"""
    comando = f'python valuation_empresa.py "{empresa}"'
    
    if preco:
        comando += f' --preco {preco}'
    
    print(f"\nExecutando valuation de {empresa}...")
    print(f"Comando: {comando}")
    print("-" * 60)
    
    os.system(comando)
    
    input("\nPressione ENTER para continuar...")

def main():
    empresas = {
        '1': ('VALE3', 70.00),
        '2': ('PETR4', 38.50),
        '3': ('ITUB4', 33.20),
        '4': ('ABEV3', 13.45)
    }
    
    while True:
        limpar_tela()
        mostrar_menu()
        
        opcao = input("\nEscolha uma opção: ")
        
        if opcao in empresas:
            ticker, preco_ref = empresas[opcao]
            
            usar_preco = input(f"\nUsar preço de referência R$ {preco_ref:.2f}? (S/N): ")
            
            if usar_preco.upper() == 'S':
                executar_valuation(ticker, preco_ref)
            else:
                preco_custom = input("Digite o preço atual da ação: R$ ")
                try:
                    preco = float(preco_custom.replace(',', '.'))
                    executar_valuation(ticker, preco)
                except:
                    executar_valuation(ticker)
                    
        elif opcao == '5':
            print("\nBUSCAR EMPRESA")
            print("-" * 40)
            termo = input("Digite o ticker, nome ou código CVM: ")
            
            preco_str = input("Preço da ação (opcional): R$ ")
            preco = None
            if preco_str:
                try:
                    preco = float(preco_str.replace(',', '.'))
                except:
                    pass
            
            executar_valuation(termo, preco)
            
        elif opcao == '0':
            print("\nEncerrando sistema...")
            break
        else:
            print("\n[ERRO] Opção inválida!")
            input("Pressione ENTER para continuar...")

if __name__ == "__main__":
    print("\nBem-vindo ao Sistema de Valuation!")
    print("Análise completa de empresas da bolsa")
    input("\nPressione ENTER para iniciar...")
    main()