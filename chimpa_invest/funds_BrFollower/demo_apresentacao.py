"""
Script de Demonstração para Apresentação
Análise de Fundos de Investimento - Sistema Chimpa Invest
"""

import os
import sys
import time
from datetime import datetime

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def mostrar_menu():
    print("=" * 60)
    print("       SISTEMA DE ANÁLISE DE FUNDOS - CHIMPA INVEST")
    print("=" * 60)
    print("\nOPÇÕES DE DEMONSTRAÇÃO:\n")
    print("1. Análise Completa - Fundo Capstone")
    print("2. Análise Rápida - Múltiplos Fundos")
    print("3. Exportar Dados para Excel")
    print("4. Visualizar Relatório HTML")
    print("5. Mostrar Estrutura de Dados")
    print("6. Análise Personalizada (inserir CNPJ)")
    print("\n0. Sair")
    print("\n" + "=" * 60)

def executar_analise_capstone():
    print("\nIniciando análise do Fundo Capstone...")
    print("CNPJ: 35.803.288/0001-17")
    time.sleep(1)
    
    comando = 'python analise_temporal_fundos.py 35.803.288/0001-17 --nome "Capstone FIC FIM"'
    print(f"\nExecutando: {comando}")
    print("-" * 60)
    
    os.system(comando)
    
    print("\nAnálise concluída!")
    print(f"Resultados salvos em: dados\\35803288000117\\")
    input("\nPressione ENTER para continuar...")

def analisar_multiplos_fundos():
    fundos = [
        ("35.803.288/0001-17", "Capstone"),
        ("38.351.476/0001-40", "Exemplo Fund"),
    ]
    
    print("\nAnalisando múltiplos fundos...")
    
    for cnpj, nome in fundos:
        print(f"\n{'='*40}")
        print(f"Analisando: {nome}")
        print(f"CNPJ: {cnpj}")
        print(f"{'='*40}")
        
        comando = f'python analise_temporal_fundos.py {cnpj} --nome "{nome}"'
        os.system(comando)
        
        cnpj_limpo = cnpj.replace('.', '').replace('/', '').replace('-', '')
        print(f"\n{nome} - Concluído!")
        print(f"Dados em: dados\\{cnpj_limpo}\\")
        time.sleep(2)
    
    input("\nTodos os fundos analisados! Pressione ENTER para continuar...")

def exportar_para_excel():
    print("\nExportando dados para formato Excel (CSV)...")
    
    cnpj = input("Digite o CNPJ do fundo (ou ENTER para Capstone): ")
    if not cnpj:
        cnpj = "35.803.288/0001-17"
    
    comando = f'python analise_temporal_fundos.py {cnpj} --formato csv'
    print(f"\nExecutando: {comando}")
    print("-" * 60)
    
    os.system(comando)
    
    cnpj_limpo = cnpj.replace('.', '').replace('/', '').replace('-', '')
    print(f"\nArquivos CSV exportados!")
    print(f"Localização: dados\\{cnpj_limpo}\\csv\\")
    print("\nArquivos gerados:")
    print("  - evolucao_patrimonio.csv")
    print("  - posicoes_acoes.csv")
    print("  - serie_cotas.csv")
    print("  - retornos_mensais.csv")
    print("  - indicadores.csv")
    
    input("\nPressione ENTER para continuar...")

def visualizar_relatorio():
    print("\nAbrindo relatório HTML...")
    
    cnpj = input("Digite o CNPJ do fundo (ou ENTER para Capstone): ")
    if not cnpj:
        cnpj = "35.803.288/0001-17"
    
    cnpj_limpo = cnpj.replace('.', '').replace('/', '').replace('-', '')
    caminho_html = f"dados\\{cnpj_limpo}\\relatorio_temporal.html"
    
    if os.path.exists(caminho_html):
        print(f"Abrindo: {caminho_html}")
        os.system(f'start {caminho_html}')
    else:
        print(f"[ERRO] Relatório não encontrado. Execute a análise primeiro!")
    
    input("\nPressione ENTER para continuar...")

def mostrar_estrutura():
    print("\nESTRUTURA DE DADOS GERADA:\n")
    
    estrutura = """
dados/
└── [CNPJ_LIMPO]/              # Ex: 35803288000117/
    │
    ├── VISUALIZAÇÕES
    │   ├── analise_temporal.png    # 10 gráficos de análise
    │   └── relatorio_temporal.html # Relatório interativo
    │
    ├── DADOS COMPLETOS
    │   ├── dados_fundo.pkl         # Formato binário (Python)
    │   └── dados_fundo.json        # Formato JSON
    │
    └── ARQUIVOS CSV/
        ├── evolucao_patrimonio.csv # Evolução do patrimônio
        ├── posicoes_acoes.csv      # Detalhes das ações
        ├── serie_cotas.csv         # Histórico de cotas
        ├── retornos_mensais.csv    # Retornos mensais
        ├── indicadores.csv         # Indicadores calculados
        └── carteiras_resumo.csv    # Resumo das carteiras
    """
    
    print(estrutura)
    
    print("\nINDICADORES CALCULADOS:")
    print("  • Retorno Total e Anualizado")
    print("  • Volatilidade (Risco)")
    print("  • Sharpe Ratio (Retorno/Risco)")
    print("  • Maximum Drawdown")
    print("  • Performance por Ano")
    
    input("\nPressione ENTER para continuar...")

def analise_personalizada():
    print("\nANÁLISE PERSONALIZADA\n")
    
    cnpj = input("Digite o CNPJ do fundo: ")
    nome = input("Digite o nome do fundo (opcional): ")
    anos = input("Período mínimo em anos (padrão 5): ")
    
    if not cnpj:
        print("[ERRO] CNPJ é obrigatório!")
        input("\nPressione ENTER para continuar...")
        return
    
    comando = f'python analise_temporal_fundos.py {cnpj}'
    
    if nome:
        comando += f' --nome "{nome}"'
    if anos:
        comando += f' --anos {anos}'
    
    print(f"\nExecutando: {comando}")
    print("-" * 60)
    
    os.system(comando)
    
    cnpj_limpo = cnpj.replace('.', '').replace('/', '').replace('-', '')
    print(f"\nAnálise concluída!")
    print(f"Resultados em: dados\\{cnpj_limpo}\\")
    
    input("\nPressione ENTER para continuar...")

def main():
    while True:
        limpar_tela()
        mostrar_menu()
        
        opcao = input("\nEscolha uma opção: ")
        
        if opcao == "1":
            executar_analise_capstone()
        elif opcao == "2":
            analisar_multiplos_fundos()
        elif opcao == "3":
            exportar_para_excel()
        elif opcao == "4":
            visualizar_relatorio()
        elif opcao == "5":
            mostrar_estrutura()
        elif opcao == "6":
            analise_personalizada()
        elif opcao == "0":
            print("\nEncerrando sistema...")
            break
        else:
            print("\n[ERRO] Opção inválida!")
            time.sleep(1)

if __name__ == "__main__":
    print("\nBem-vindo ao Sistema de Análise de Fundos!")
    print(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    time.sleep(2)
    main()