#!/usr/bin/env python3
"""
CVM Extrator de Dados IPE
=========================
Baixa e extrai dados de todas as empresas listadas na CVM.
Este é o primeiro script a ser executado - cria a base de dados.
"""

import requests
import pandas as pd
from pathlib import Path
import zipfile
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def baixar_arquivo_ipe(ano: int = 2025) -> bool:
    """
    Baixa o arquivo IPE do ano especificado.
    """
    url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/ipe_cia_aberta_{ano}.zip"
    nome_arquivo = f"ipe_cia_aberta_{ano}.zip"
    
    print(f"\nBaixando arquivo IPE {ano}...")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        # Salvar arquivo
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        
        with open(nome_arquivo, 'wb') as f:
            downloaded = 0
            for data in response.iter_content(block_size):
                downloaded += len(data)
                f.write(data)
                
                # Mostrar progresso
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\r   Progresso: {percent:.1f}%", end='')
        
        print(f"\nDownload concluído: {nome_arquivo}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"\n[ERRO] Erro ao baixar arquivo: {e}")
        return False


def extrair_arquivo_ipe(ano: int = 2025) -> bool:
    """
    Extrai o arquivo ZIP do IPE.
    """
    nome_zip = f"ipe_cia_aberta_{ano}.zip"
    nome_csv = f"ipe_cia_aberta_{ano}.csv"
    
    if not Path(nome_zip).exists():
        print(f"[ERRO] Arquivo {nome_zip} não encontrado")
        return False
    
    print(f"\nExtraindo {nome_zip}...")
    
    try:
        with zipfile.ZipFile(nome_zip, 'r') as zip_ref:
            # Listar conteúdo
            arquivos = zip_ref.namelist()
            print(f"   Arquivos no ZIP: {', '.join(arquivos)}")
            
            # Extrair
            zip_ref.extractall('.')
        
        print(f"Extração concluída")
        
        # Remover ZIP após extrair
        Path(nome_zip).unlink()
        print(f"Arquivo ZIP removido")
        
        return True
        
    except Exception as e:
        print(f"[ERRO] Erro ao extrair: {e}")
        return False


def analisar_dados_ipe(ano: int = 2025):
    """
    Analisa e mostra estatísticas do arquivo IPE.
    """
    nome_csv = f"ipe_cia_aberta_{ano}.csv"
    
    if not Path(nome_csv).exists():
        print(f"[ERRO] Arquivo {nome_csv} não encontrado")
        return
    
    print(f"\nAnalisando dados IPE {ano}...")
    
    try:
        # Ler CSV
        df = pd.read_csv(nome_csv, sep=';', encoding='latin-1')
        
        print(f"\nDados carregados com sucesso!")
        print(f"   Total de registros: {len(df):,}")
        print(f"   Colunas: {', '.join(df.columns)}")
        
        # Estatísticas por empresa
        print(f"\nESTATÍSTICAS:")
        print(f"   Empresas únicas: {df['Nome_Companhia'].nunique()}")
        print(f"   Categorias: {df['Categoria'].nunique()}")
        
        # Top 10 empresas com mais registros
        print(f"\nTOP 10 EMPRESAS (por número de comunicados):")
        top_empresas = df['Nome_Companhia'].value_counts().head(10)
        for i, (empresa, count) in enumerate(top_empresas.items(), 1):
            print(f"   {i:2d}. {empresa:<40} {count:>5} registros")
        
        # Tipos de documentos mais comuns
        print(f"\nCATEGORIAS MAIS COMUNS:")
        top_categorias = df['Categoria'].value_counts().head(10)
        for i, (categoria, count) in enumerate(top_categorias.items(), 1):
            print(f"   {i:2d}. {categoria:<50} {count:>5} registros")
        
        # Salvar lista de empresas
        empresas_unicas = df[['Nome_Companhia', 'CNPJ_Companhia']].drop_duplicates()
        empresas_unicas = empresas_unicas.sort_values('Nome_Companhia')
        
        arquivo_empresas = f"lista_empresas_cvm_{ano}.csv"
        empresas_unicas.to_csv(arquivo_empresas, index=False, encoding='utf-8')
        print(f"\nLista de empresas salva em: {arquivo_empresas}")
        
    except Exception as e:
        print(f"[ERRO] Erro ao analisar dados: {e}")
        import traceback
        traceback.print_exc()


def main():
    """
    Função principal - baixa e processa dados IPE.
    """
    print("CVM EXTRATOR DE DADOS IPE")
    print("=" * 60)
    print("\nEste script baixa os dados de TODAS as empresas da CVM")
    print("   É o primeiro passo para usar os outros scripts")
    
    # Solicitar ano
    ano_input = input("\nDigite o ano (Enter para 2025): ").strip()
    ano = int(ano_input) if ano_input.isdigit() else 2025
    
    print(f"\nProcessando dados do ano: {ano}")
    
    # Verificar se já existe
    nome_csv = f"ipe_cia_aberta_{ano}.csv"
    if Path(nome_csv).exists():
        print(f"\nArquivo {nome_csv} já existe!")
        substituir = input("   Deseja baixar novamente? (s/N): ").strip().lower()
        if substituir != 's':
            print("\nAnalisando arquivo existente...")
            analisar_dados_ipe(ano)
            return
    
    # Baixar arquivo
    if baixar_arquivo_ipe(ano):
        # Extrair
        if extrair_arquivo_ipe(ano):
            # Analisar
            analisar_dados_ipe(ano)
            
            print(f"\nPROCESSO CONCLUÍDO!")
            print(f"\nPRÓXIMOS PASSOS:")
            print(f"   1. Use '01_cvm_download_releases_multiplas_empresas.py' para baixar releases")
            print(f"   2. Use '02_cvm_download_documentos_estruturados.py' para ITR/DFP")
        else:
            print("\n[ERRO] Falha na extração")
    else:
        print("\n[ERRO] Falha no download")


if __name__ == "__main__":
    main()