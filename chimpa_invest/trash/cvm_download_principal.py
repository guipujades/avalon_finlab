#!/usr/bin/env python3
"""
CVM Download Principal - Menu Unificado
=======================================
Script principal para downloads da CVM com todas as opções.
"""

import os
import sys
from pathlib import Path

def limpar_tela():
    """Limpa a tela do terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')

def verificar_arquivo_ipe():
    """Verifica se existe arquivo IPE."""
    anos_disponiveis = []
    for ano in [2023, 2024, 2025]:
        if Path(f"ipe_cia_aberta_{ano}.csv").exists():
            anos_disponiveis.append(ano)
    return anos_disponiveis

def menu_principal():
    """Menu principal do sistema."""
    limpar_tela()
    print("=" * 70)
    print("  SISTEMA CVM DOWNLOAD - MENU PRINCIPAL")
    print("=" * 70)
    
    # Verificar arquivos IPE
    anos_ipe = verificar_arquivo_ipe()
    
    print("\n STATUS DO SISTEMA:")
    if anos_ipe:
        print(f"    Arquivos IPE disponíveis: {', '.join(map(str, anos_ipe))}")
    else:
        print("    Nenhum arquivo IPE encontrado")
        print("    Execute a opção 1 primeiro")
    
    print("\n OPÇÕES DISPONÍVEIS:")
    print("\n1️⃣  PREPARAÇÃO")
    print("   [1] Baixar registro de empresas (IPE)")
    
    print("\n2️⃣  DOWNLOADS DE PDFs")
    print("   [2] Baixar TODOS os releases (PDFs)")
    print("   [3] Baixar APENAS releases trimestrais (Earnings Releases)")
    print("   [4] Download personalizado por categoria")
    
    print("\n3️⃣  DADOS ESTRUTURADOS")
    print("   [5] Baixar ITR/DFP (dados estruturados ZIP/CSV)")
    print("   [6] Baixar outros dados estruturados (FCA, FRE, IPE)")
    
    print("\n4️⃣  FERRAMENTAS")
    print("   [7] Analisar empresas disponíveis")
    print("   [8] Verificar downloads realizados")
    print("   [9]  Agente Economista (resumos executivos)")
    print("   [10]  Análise Real de PDFs (extração local)")
    
    print("\n5️⃣  UTILITÁRIOS")
    print("   [11] Limpar pastas temporárias")
    
    print("\n   [0] Sair")
    
    print("\n" + "=" * 70)
    return input("Escolha uma opção: ").strip()

def executar_opcao(opcao):
    """Executa a opção escolhida."""
    
    if opcao == "1":
        print("\n Executando extrator de dados IPE...")
        os.system("python 00_cvm_extrator_dados_ipe.py")
        
    elif opcao == "2":
        print("\n Executando download de TODOS os releases...")
        print("\n DICA: Este modo baixa todos os tipos de documentos")
        print("   - Releases trimestrais vão para 'documents/pending'")
        print("   - Outros documentos vão para 'documents/residuals'")
        input("\nPressione Enter para continuar...")
        
        # Criar arquivo temporário com configuração
        with open("temp_config.txt", "w") as f:
            f.write("modo_todos_releases")
        
        os.system("python 01_cvm_download_releases_multiplas_empresas.py")
        
        # Limpar arquivo temporário
        if Path("temp_config.txt").exists():
            Path("temp_config.txt").unlink()
        
    elif opcao == "3":
        print("\n Executando download APENAS de releases trimestrais...")
        print("\n DICA: Este modo baixa apenas:")
        print("    Earnings Releases / Release de Resultados")
        print("    Desempenho trimestral (Ex: 'Desempenho da Vale no 1T25')")
        print("    Ignora: atas, comunicados, relatórios administrativos")
        input("\nPressione Enter para continuar...")
        
        # Criar arquivo temporário com configuração
        with open("temp_config.txt", "w") as f:
            f.write("modo_apenas_trimestrais")
        
        os.system("python 01_cvm_download_releases_multiplas_empresas.py")
        
        # Limpar arquivo temporário
        if Path("temp_config.txt").exists():
            Path("temp_config.txt").unlink()
    
    elif opcao == "4":
        print("\n Download personalizado...")
        print("\n CATEGORIAS DISPONÍVEIS:")
        print("   1. Assembleia")
        print("   2. Comunicado ao Mercado")
        print("   3. Dados Econômico-Financeiros")
        print("   4. Fato Relevante")
        print("   5. Aviso aos Acionistas")
        categoria = input("\nEscolha a categoria (1-5): ").strip()
        
        # Implementar filtro por categoria (futuro)
        print("\n  Funcionalidade em desenvolvimento...")
        input("Pressione Enter para voltar...")
        
    elif opcao == "5":
        print("\n Executando download de ITR/DFP estruturados...")
        print("\n DICA: Este modo baixa arquivos ZIP com CSVs contendo:")
        print("   - ITR: Informações Trimestrais completas")
        print("   - DFP: Demonstrações Financeiras Padronizadas anuais")
        print("   - Dados estruturados para análise em massa")
        input("\nPressione Enter para continuar...")
        os.system("python 02_cvm_download_documentos_estruturados.py")
        
    elif opcao == "6":
        print("\n Executando download de outros dados estruturados...")
        print("\n Tipos disponíveis: FCA, FRE, IPE")
        input("\nPressione Enter para continuar...")
        os.system("python 02_cvm_download_documentos_estruturados.py")
        
    elif opcao == "7":
        print("\n ANALISANDO EMPRESAS DISPONÍVEIS...")
        anos_ipe = verificar_arquivo_ipe()
        if anos_ipe:
            ano = input(f"\nEscolha o ano {anos_ipe}: ").strip()
            if ano.isdigit() and int(ano) in anos_ipe:
                analisar_empresas(int(ano))
        else:
            print(" Nenhum arquivo IPE encontrado!")
        input("\nPressione Enter para voltar...")
        
    elif opcao == "8":
        print("\n VERIFICANDO DOWNLOADS REALIZADOS...")
        verificar_downloads()
        input("\nPressione Enter para voltar...")
        
    elif opcao == "9":
        print("\n INICIANDO AGENTE ECONOMISTA...")
        os.system("python 03_analise_economista.py")
        
    elif opcao == "10":
        print("\n INICIANDO ANÁLISE REAL DE PDFs...")
        os.system("python analise_pdf_real.py")
        
    elif opcao == "11":
        print("\n  LIMPANDO PASTAS TEMPORÁRIAS...")
        limpar_pastas_temp()
        input("\nPressione Enter para voltar...")
        
    elif opcao == "0":
        print("\n Saindo do sistema...")
        return False
    
    else:
        print("\n Opção inválida!")
        input("Pressione Enter para continuar...")
    
    return True

def analisar_empresas(ano):
    """Analisa empresas disponíveis no arquivo IPE."""
    try:
        import pandas as pd
        df = pd.read_csv(f"ipe_cia_aberta_{ano}.csv", sep=';', encoding='latin-1')
        
        print(f"\n ANÁLISE DO ARQUIVO IPE {ano}")
        print(f"   Total de registros: {len(df):,}")
        print(f"   Empresas únicas: {df['Nome_Companhia'].nunique()}")
        
        print("\n TOP 20 EMPRESAS (por número de documentos):")
        top_empresas = df['Nome_Companhia'].value_counts().head(20)
        for i, (empresa, count) in enumerate(top_empresas.items(), 1):
            print(f"   {i:2d}. {empresa:<50} {count:>5} docs")
            
    except Exception as e:
        print(f" Erro ao analisar: {e}")

def verificar_downloads():
    """Verifica arquivos baixados."""
    pastas = {
        'documents/pending': 'Releases Trimestrais',
        'documents/residuals': 'Outros Documentos',
        'documents/cvm_estruturados/ITR': 'ITR Estruturados',
        'documents/cvm_estruturados/DFP': 'DFP Estruturados'
    }
    
    print("\n ARQUIVOS BAIXADOS:")
    total = 0
    
    for pasta, nome in pastas.items():
        path = Path(pasta)
        if path.exists():
            arquivos = list(path.glob('*.pdf')) + list(path.glob('*.zip'))
            qtd = len(arquivos)
            total += qtd
            print(f"\n{nome}:")
            print(f"   📂 {pasta}")
            print(f"    {qtd} arquivos")
            
            if qtd > 0 and qtd <= 5:
                for arq in sorted(arquivos)[:5]:
                    print(f"      - {arq.name}")
            elif qtd > 5:
                for arq in sorted(arquivos)[:3]:
                    print(f"      - {arq.name}")
                print(f"      ... e mais {qtd - 3} arquivos")
    
    print(f"\n TOTAL GERAL: {total} arquivos")

def limpar_pastas_temp():
    """Limpa pastas temporárias."""
    pastas_temp = ['temp_downloads', '__pycache__']
    arquivos_temp = ['temp_config.txt', '*.log']
    
    limpos = 0
    
    for pasta in pastas_temp:
        path = Path(pasta)
        if path.exists() and path.is_dir():
            import shutil
            shutil.rmtree(path)
            print(f" Pasta {pasta} removida")
            limpos += 1
    
    for pattern in arquivos_temp:
        for arquivo in Path('.').glob(pattern):
            arquivo.unlink()
            print(f" Arquivo {arquivo} removido")
            limpos += 1
    
    print(f"\n🧹 {limpos} itens limpos")

def main():
    """Função principal."""
    # Verificar se foi chamado com modo específico
    if Path("temp_config.txt").exists():
        with open("temp_config.txt", "r") as f:
            modo = f.read().strip()
        
        if modo == "modo_apenas_trimestrais":
            # Configurar para modo apenas trimestrais
            print("\n MODO: Apenas releases trimestrais")
            # O script 01 vai ler este arquivo e configurar adequadamente
    
    continuar = True
    while continuar:
        opcao = menu_principal()
        continuar = executar_opcao(opcao)
    
    print("\n Sistema finalizado com sucesso!")

if __name__ == "__main__":
    main()