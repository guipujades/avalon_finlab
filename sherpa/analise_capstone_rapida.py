import pandas as pd
import numpy as np
import os
import zipfile
import json
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

CNPJ_CAPSTONE = "35.803.288/0001-17"
BASE_DIR = "/mnt/c/Users/guilh/Documents/GitHub/sherpa/database"

def verificar_fundo_nos_arquivos():
    """
    Verifica rapidamente em quais arquivos o fundo Capstone aparece
    """
    cda_dir = os.path.join(BASE_DIR, "CDA")
    arquivos_com_capstone = []
    
    print(f"Verificando presença do fundo Capstone (CNPJ: {CNPJ_CAPSTONE})")
    
    # Testar apenas alguns arquivos recentes primeiro
    arquivos_teste = [
        "cda_fi_202412.zip",
        "cda_fi_202411.zip", 
        "cda_fi_202410.zip",
        "cda_fi_202409.zip",
        "cda_fi_202408.zip"
    ]
    
    for arquivo in arquivos_teste:
        arquivo_path = os.path.join(cda_dir, arquivo)
        if os.path.exists(arquivo_path):
            print(f"\nVerificando {arquivo}...")
            
            try:
                with zipfile.ZipFile(arquivo_path, 'r') as zip_file:
                    # Verificar cada BLC
                    for blc_num in range(1, 9):
                        for nome_interno in zip_file.namelist():
                            if f"BLC_{blc_num}" in nome_interno and nome_interno.endswith('.csv'):
                                try:
                                    with zip_file.open(nome_interno) as f:
                                        # Ler apenas primeiras linhas para verificar estrutura
                                        df_sample = pd.read_csv(f, sep=';', encoding='ISO-8859-1', nrows=5)
                                        
                                        # Verificar colunas disponíveis
                                        print(f"  BLC_{blc_num} - Colunas: {list(df_sample.columns)[:5]}...")
                                        
                                        # Ler todo arquivo e buscar CNPJ
                                        f.seek(0)
                                        df = pd.read_csv(f, sep=';', encoding='ISO-8859-1')
                                        
                                        # Buscar CNPJ em diferentes colunas
                                        cnpj_encontrado = False
                                        for col in ['CNPJ_FUNDO_CLASSE', 'CNPJ_FUNDO', 'CD_FUNDO']:
                                            if col in df.columns:
                                                df_cnpj = df[df[col].astype(str).str.strip() == CNPJ_CAPSTONE]
                                                if not df_cnpj.empty:
                                                    print(f"  ✓ Fundo encontrado em BLC_{blc_num} ({len(df_cnpj)} registros)")
                                                    cnpj_encontrado = True
                                                    arquivos_com_capstone.append({
                                                        'arquivo': arquivo,
                                                        'blc': f'BLC_{blc_num}',
                                                        'registros': len(df_cnpj)
                                                    })
                                                    break
                                        
                                        if not cnpj_encontrado and blc_num == 1:
                                            # Verificar se há algum fundo similar
                                            for col in ['CNPJ_FUNDO_CLASSE', 'CNPJ_FUNDO', 'CD_FUNDO']:
                                                if col in df.columns:
                                                    cnpjs_unicos = df[col].astype(str).str.strip().unique()
                                                    capstone_similar = [c for c in cnpjs_unicos if '35.803.288' in c]
                                                    if capstone_similar:
                                                        print(f"  ! CNPJs similares encontrados: {capstone_similar[:3]}")
                                                    break
                                                    
                                except Exception as e:
                                    print(f"  Erro ao ler BLC_{blc_num}: {e}")
                                    
            except Exception as e:
                print(f"Erro ao processar {arquivo}: {e}")
    
    return arquivos_com_capstone

def buscar_dados_cadastrais():
    """
    Busca dados cadastrais do fundo
    """
    cad_file = os.path.join(BASE_DIR, "CAD", "cad_fi.csv")
    
    if os.path.exists(cad_file):
        print("\nBuscando dados cadastrais...")
        df_cad = pd.read_csv(cad_file, sep=';', encoding='ISO-8859-1')
        
        # Buscar pelo CNPJ
        df_capstone = df_cad[df_cad['CNPJ_FUNDO'].astype(str).str.strip() == CNPJ_CAPSTONE]
        
        if not df_capstone.empty:
            print("\n✓ Fundo encontrado no cadastro!")
            info = df_capstone.iloc[0]
            print(f"Nome: {info.get('DENOM_SOCIAL', 'N/A')}")
            print(f"Situação: {info.get('SIT', 'N/A')}")
            print(f"Classe: {info.get('CLASSE', 'N/A')}")
            print(f"Tipo: {info.get('TP_FUNDO', 'N/A')}")
            print(f"Data Início: {info.get('DT_INI_ATIV', 'N/A')}")
            return True
        else:
            print("\n✗ Fundo NÃO encontrado no cadastro")
            # Buscar CNPJs similares
            cnpjs_similares = df_cad[df_cad['CNPJ_FUNDO'].astype(str).str.contains('35.803.288', na=False)]
            if not cnpjs_similares.empty:
                print("\nCNPJs similares encontrados:")
                for _, fundo in cnpjs_similares.iterrows():
                    print(f"- {fundo['CNPJ_FUNDO']} - {fundo.get('DENOM_SOCIAL', 'N/A')}")
    
    return False

def main():
    """
    Função principal para verificação rápida
    """
    print("=" * 60)
    print("VERIFICAÇÃO RÁPIDA - FUNDO CAPSTONE")
    print("=" * 60)
    
    # 1. Buscar dados cadastrais
    cadastro_ok = buscar_dados_cadastrais()
    
    # 2. Verificar presença nos arquivos CDA
    print("\n" + "=" * 60)
    arquivos_encontrados = verificar_fundo_nos_arquivos()
    
    # 3. Resumo
    print("\n" + "=" * 60)
    print("RESUMO DA VERIFICAÇÃO")
    print("=" * 60)
    
    if arquivos_encontrados:
        print(f"\n✓ Fundo encontrado em {len(arquivos_encontrados)} registros:")
        for reg in arquivos_encontrados:
            print(f"  - {reg['arquivo']} -> {reg['blc']} ({reg['registros']} registros)")
    else:
        print("\n✗ Fundo NÃO foi encontrado nos arquivos CDA verificados")
        print("\nPossíveis razões:")
        print("1. O CNPJ pode estar incorreto")
        print("2. O fundo pode não reportar dados à CVM")
        print("3. O fundo pode ser muito novo ou ter encerrado atividades")
        print("4. Os dados podem estar em períodos não verificados")
    
    if not cadastro_ok:
        print("\n⚠️  IMPORTANTE: O fundo não foi encontrado no cadastro da CVM")
        print("Isso sugere que o CNPJ pode estar incorreto ou o fundo não está registrado")

if __name__ == "__main__":
    main()