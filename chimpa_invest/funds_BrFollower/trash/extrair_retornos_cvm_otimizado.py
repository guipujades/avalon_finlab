import pandas as pd
import numpy as np
import os
import zipfile
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
warnings.filterwarnings('ignore')

# Configuração dos diretórios
BASE_DIR = Path("C:/Users/guilh/Documents/GitHub/database/funds_cvm")
OUTPUT_DIR = Path("C:/Users/guilh/Documents/GitHub/database/chimpa")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def processar_arquivo_zip(arquivo_path):
    """Processa um único arquivo zip e retorna dados dos fundos"""
    fundos_periodo = {}
    
    try:
        with zipfile.ZipFile(arquivo_path, 'r') as zip_file:
            for nome_interno in zip_file.namelist():
                if nome_interno.endswith('.csv'):
                    with zip_file.open(nome_interno) as f:
                        df = pd.read_csv(f, sep=';', encoding='ISO-8859-1', 
                                       usecols=['DT_COMPTC', 'CNPJ_FUNDO', 'VL_QUOTA'],
                                       dtype={'CNPJ_FUNDO': str})
                        
                        df['DT_COMPTC'] = pd.to_datetime(df['DT_COMPTC'])
                        
                        # Processar por grupos de CNPJ
                        for cnpj, grupo in df.groupby('CNPJ_FUNDO'):
                            df_fundo = grupo[['DT_COMPTC', 'VL_QUOTA']].copy()
                            df_fundo = df_fundo.sort_values('DT_COMPTC')
                            df_fundo.set_index('DT_COMPTC', inplace=True)
                            
                            if len(df_fundo) > 0 and df_fundo['VL_QUOTA'].notna().sum() > 0:
                                fundos_periodo[cnpj] = df_fundo
                    break  # Só precisa processar o primeiro CSV
    except Exception as e:
        print(f"\nErro em {arquivo_path.name}: {e}")
    
    return fundos_periodo

def extrair_periodo_arquivo(nome_arquivo):
    """Extrai período do nome do arquivo"""
    periodo = nome_arquivo.replace("inf_diario_fi_", "").replace(".zip", "")
    if len(periodo) == 6:
        return f"{periodo[:4]}-{periodo[4:6]}"
    return periodo

def main():
    periodo_inicial = "2020-01"
    periodo_final = "2024-12"
    
    periodo_inicial_dt = datetime.strptime(periodo_inicial, "%Y-%m")
    periodo_final_dt = datetime.strptime(periodo_final, "%Y-%m")
    
    inf_diario_dir = BASE_DIR / "INF_DIARIO"
    
    # Coletar arquivos do período
    arquivos_processar = []
    for arquivo in sorted(os.listdir(inf_diario_dir)):
        if arquivo.startswith("inf_diario_fi_") and arquivo.endswith(".zip"):
            periodo_str = extrair_periodo_arquivo(arquivo)
            try:
                periodo_dt = datetime.strptime(periodo_str, "%Y-%m")
                if periodo_inicial_dt <= periodo_dt <= periodo_final_dt:
                    arquivos_processar.append(inf_diario_dir / arquivo)
            except:
                continue
    
    print(f"Arquivos para processar: {len(arquivos_processar)}")
    
    # Processar arquivos em paralelo
    series_cotas = {}
    num_cores = multiprocessing.cpu_count() - 1
    
    print(f"Processando com {num_cores} cores...")
    
    with ProcessPoolExecutor(max_workers=num_cores) as executor:
        futures = {executor.submit(processar_arquivo_zip, arquivo): arquivo 
                  for arquivo in arquivos_processar}
        
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processando"):
            fundos_periodo = future.result()
            
            for cnpj, df_cotas in fundos_periodo.items():
                if cnpj not in series_cotas:
                    series_cotas[cnpj] = []
                series_cotas[cnpj].append(df_cotas)
    
    # Consolidar séries
    print("\nConsolidando dados...")
    retornos_mensais = {}
    
    for cnpj, lista_dfs in tqdm(series_cotas.items(), desc="Consolidando"):
        if lista_dfs:
            df_completo = pd.concat(lista_dfs)
            df_completo = df_completo[~df_completo.index.duplicated(keep='first')]
            df_completo = df_completo.sort_index()
            
            if len(df_completo) >= 20:
                # Calcular retornos diários
                df_completo['retorno'] = df_completo['VL_QUOTA'].pct_change()
                
                # Calcular retornos mensais
                retorno_mensal = df_completo['retorno'].resample('M').apply(
                    lambda x: (1 + x).prod() - 1 if len(x) > 0 else np.nan
                )
                
                if retorno_mensal.notna().sum() >= 12:
                    retornos_mensais[cnpj] = retorno_mensal
    
    # Criar DataFrame final
    if retornos_mensais:
        df_retornos = pd.DataFrame(retornos_mensais)
        
        # Remover fundos com muitos NaN
        min_observacoes = len(df_retornos) * 0.5
        df_retornos = df_retornos.dropna(thresh=min_observacoes, axis=1)
        
        # Salvar resultados
        output_file = OUTPUT_DIR / "retornos_fundos_cvm.csv"
        df_retornos.to_csv(output_file)
        
        # Estatísticas
        stats = pd.DataFrame({
            'retorno_medio': df_retornos.mean(),
            'volatilidade': df_retornos.std(),
            'sharpe_ratio': df_retornos.mean() / df_retornos.std() * np.sqrt(12),
            'min_retorno': df_retornos.min(),
            'max_retorno': df_retornos.max(),
            'qtd_observacoes': df_retornos.count()
        })
        stats.to_csv(OUTPUT_DIR / "estatisticas_fundos_cvm.csv")
        
        print(f"\nRetornos salvos em: {output_file}")
        print(f"Total de fundos: {len(df_retornos.columns)}")
        print(f"Período: {df_retornos.index[0].strftime('%Y-%m')} a {df_retornos.index[-1].strftime('%Y-%m')}")
    else:
        print("\nNenhum dado processado!")

if __name__ == "__main__":
    main()