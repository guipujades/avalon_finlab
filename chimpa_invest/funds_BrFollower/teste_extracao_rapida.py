import pandas as pd
import numpy as np
import os
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

home = Path.home()
BASE_DIR = Path(home, 'Documents', 'GitHub', 'sherpa', 'database')

def teste_extracao_rapida():
    """Testa a extração com apenas 2 meses de dados para verificar se funciona"""
    
    print("="*60)
    print("TESTE RÁPIDO DE EXTRAÇÃO DE RETORNOS")
    print("="*60)
    
    inf_diario_dir = os.path.join(BASE_DIR, "INF_DIARIO")
    
    # Verificar se o diretório existe
    if not os.path.exists(inf_diario_dir):
        print(f"ERRO: Diretório não encontrado: {inf_diario_dir}")
        return
    
    # Listar arquivos disponíveis
    arquivos = [f for f in os.listdir(inf_diario_dir) if f.endswith('.zip')]
    arquivos_filtrados = [f for f in arquivos if '202408' in f or '202407' in f]
    
    print(f"\nDiretório: {inf_diario_dir}")
    print(f"Total de arquivos .zip encontrados: {len(arquivos)}")
    print(f"Arquivos para teste (Jul-Ago 2024): {len(arquivos_filtrados)}")
    
    if not arquivos_filtrados:
        print("\nNenhum arquivo de jul/ago 2024 encontrado. Pegando os 2 últimos disponíveis...")
        arquivos_filtrados = sorted(arquivos)[-2:] if len(arquivos) >= 2 else arquivos
    
    print(f"\nArquivos selecionados para teste:")
    for arq in arquivos_filtrados:
        print(f"  - {arq}")
    
    # Processar arquivos
    fundos_encontrados = {}
    
    print("\nProcessando arquivos...")
    for arquivo in tqdm(arquivos_filtrados, desc="Arquivos"):
        arquivo_path = os.path.join(inf_diario_dir, arquivo)
        
        try:
            with zipfile.ZipFile(arquivo_path, 'r') as zip_file:
                for nome_interno in zip_file.namelist():
                    if nome_interno.endswith('.csv'):
                        with zip_file.open(nome_interno) as f:
                            df = pd.read_csv(f, sep=';', encoding='ISO-8859-1', nrows=1000)  # Apenas primeiras 1000 linhas
                            
                            if 'CNPJ_FUNDO' in df.columns and 'VL_QUOTA' in df.columns:
                                cnpjs = df['CNPJ_FUNDO'].unique()[:10]  # Apenas 10 fundos
                                
                                for cnpj in cnpjs:
                                    if cnpj not in fundos_encontrados:
                                        fundos_encontrados[cnpj] = df[df['CNPJ_FUNDO'] == cnpj]['DENOM_SOCIAL'].iloc[0] if 'DENOM_SOCIAL' in df.columns else 'Nome não disponível'
                                
                                print(f"\n  Arquivo interno: {nome_interno}")
                                print(f"  Colunas encontradas: {list(df.columns)[:5]}...")
                                print(f"  Fundos processados: {len(cnpjs)}")
                                break
        except Exception as e:
            print(f"\n  Erro ao processar {arquivo}: {str(e)}")
    
    print(f"\n\nRESUMO DO TESTE:")
    print(f"Total de fundos encontrados: {len(fundos_encontrados)}")
    
    if fundos_encontrados:
        print("\nPrimeiros 5 fundos:")
        for i, (cnpj, nome) in enumerate(list(fundos_encontrados.items())[:5]):
            print(f"  {i+1}. {cnpj}: {nome}")
    
    # Salvar amostra
    if fundos_encontrados:
        os.makedirs("dados_teste", exist_ok=True)
        df_teste = pd.DataFrame(list(fundos_encontrados.items()), columns=['CNPJ', 'Nome'])
        df_teste.to_csv("dados_teste/fundos_amostra.csv", index=False)
        print(f"\nAmostra salva em: dados_teste/fundos_amostra.csv")
    
    print("\n" + "="*60)
    print("TESTE CONCLUÍDO!")
    print("="*60)
    
    return fundos_encontrados


if __name__ == "__main__":
    teste_extracao_rapida()