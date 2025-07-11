import pandas as pd
import numpy as np
import os
import zipfile
from pathlib import Path
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

# Configuração
BASE_DIR = Path("C:/Users/guilh/Documents/GitHub/database/funds_cvm")
OUTPUT_DIR = Path("C:/Users/guilh/Documents/GitHub/database/chimpa")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def processar_teste():
    """Processa apenas 3 meses para teste rápido"""
    inf_diario_dir = BASE_DIR / "INF_DIARIO"
    
    # Pegar apenas 3 arquivos recentes
    arquivos = [f for f in inf_diario_dir.glob("inf_diario_fi_2024*.zip")][:3]
    
    print(f"Processando {len(arquivos)} arquivos para teste...")
    
    todos_fundos = {}
    
    for arquivo in tqdm(arquivos):
        try:
            with zipfile.ZipFile(arquivo, 'r') as zf:
                for nome in zf.namelist():
                    if nome.endswith('.csv'):
                        df = pd.read_csv(zf.open(nome), sep=';', encoding='ISO-8859-1',
                                       usecols=['DT_COMPTC', 'CNPJ_FUNDO', 'VL_QUOTA'])
                        
                        df['DT_COMPTC'] = pd.to_datetime(df['DT_COMPTC'])
                        
                        # Pegar apenas primeiros 100 fundos
                        cnpjs = df['CNPJ_FUNDO'].unique()[:100]
                        
                        for cnpj in cnpjs:
                            df_fundo = df[df['CNPJ_FUNDO'] == cnpj].copy()
                            df_fundo = df_fundo.set_index('DT_COMPTC')['VL_QUOTA']
                            
                            if cnpj not in todos_fundos:
                                todos_fundos[cnpj] = []
                            todos_fundos[cnpj].append(df_fundo)
                        break
        except Exception as e:
            print(f"Erro: {e}")
    
    # Consolidar
    retornos = {}
    for cnpj, series in todos_fundos.items():
        serie_completa = pd.concat(series).sort_index()
        serie_completa = serie_completa[~serie_completa.index.duplicated()]
        retorno = serie_completa.pct_change().dropna()
        if len(retorno) > 0:
            retornos[cnpj] = retorno
    
    if retornos:
        df_final = pd.DataFrame(retornos)
        df_final.to_csv(OUTPUT_DIR / "teste_retornos.csv")
        print(f"Teste salvo com {len(df_final.columns)} fundos")
    
if __name__ == "__main__":
    processar_teste()