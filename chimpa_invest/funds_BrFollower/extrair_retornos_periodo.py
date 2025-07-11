import pandas as pd
import numpy as np
import os
import sys
import zipfile
from datetime import datetime
from pathlib import Path
import pickle
from typing import Dict, List, Tuple
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

home = Path.home()
BASE_DIR = Path(home, 'Documents', 'GitHub', 'sherpa', 'database')

def extrair_retornos_periodo_especifico(periodo_inicial: str = "2023-01", 
                                       periodo_final: str = "2024-08",
                                       max_fundos: int = None):
    """
    Extrai retornos de fundos para um período específico com visualização de progresso
    
    Args:
        periodo_inicial: Período inicial (YYYY-MM)
        periodo_final: Período final (YYYY-MM)
        max_fundos: Número máximo de fundos a processar (None = todos)
    """
    print("="*60)
    print("EXTRAÇÃO DE RETORNOS - PERÍODO ESPECÍFICO")
    print("="*60)
    print(f"Período: {periodo_inicial} a {periodo_final}")
    if max_fundos:
        print(f"Limitado a: {max_fundos} fundos")
    print("="*60)
    
    inf_diario_dir = os.path.join(BASE_DIR, "INF_DIARIO")
    
    # Verificar diretório
    if not os.path.exists(inf_diario_dir):
        print(f"ERRO: Diretório não encontrado: {inf_diario_dir}")
        return pd.DataFrame()
    
    # Converter períodos para datetime
    periodo_inicial_dt = datetime.strptime(periodo_inicial, "%Y-%m")
    periodo_final_dt = datetime.strptime(periodo_final, "%Y-%m")
    
    # Listar arquivos no período
    arquivos_periodo = []
    print("\nBuscando arquivos no período...")
    
    for arquivo in sorted(os.listdir(inf_diario_dir)):
        if arquivo.startswith("inf_diario_fi_") and arquivo.endswith(".zip"):
            # Extrair período do nome do arquivo
            periodo_str = arquivo.replace("inf_diario_fi_", "").replace(".zip", "")
            if len(periodo_str) == 6:
                periodo_str = f"{periodo_str[:4]}-{periodo_str[4:6]}"
                try:
                    periodo_dt = datetime.strptime(periodo_str, "%Y-%m")
                    if periodo_inicial_dt <= periodo_dt <= periodo_final_dt:
                        arquivos_periodo.append((arquivo, os.path.join(inf_diario_dir, arquivo)))
                except:
                    continue
    
    print(f"Arquivos encontrados: {len(arquivos_periodo)}")
    
    if not arquivos_periodo:
        print("ERRO: Nenhum arquivo encontrado no período especificado")
        return pd.DataFrame()
    
    # Processar arquivos
    series_fundos = {}
    info_fundos = {}
    fundos_processados = set()
    
    print("\nProcessando arquivos...")
    with tqdm(total=len(arquivos_periodo), desc="Arquivos") as pbar_arquivos:
        for nome_arquivo, arquivo_path in arquivos_periodo:
            try:
                with zipfile.ZipFile(arquivo_path, 'r') as zip_file:
                    for nome_interno in zip_file.namelist():
                        if nome_interno.endswith('.csv'):
                            # Ler arquivo CSV
                            with zip_file.open(nome_interno) as f:
                                df = pd.read_csv(f, sep=';', encoding='ISO-8859-1')
                                
                                # Verificar colunas necessárias
                                colunas_necessarias = ['DT_COMPTC', 'CNPJ_FUNDO', 'VL_QUOTA']
                                if all(col in df.columns for col in colunas_necessarias):
                                    # Converter data
                                    df['DT_COMPTC'] = pd.to_datetime(df['DT_COMPTC'])
                                    
                                    # Processar cada fundo
                                    cnpjs_unicos = df['CNPJ_FUNDO'].unique()
                                    
                                    # Limitar número de fundos se especificado
                                    if max_fundos and len(fundos_processados) >= max_fundos:
                                        cnpjs_unicos = [cnpj for cnpj in cnpjs_unicos 
                                                       if cnpj in fundos_processados]
                                    
                                    for cnpj in cnpjs_unicos:
                                        if max_fundos and len(fundos_processados) >= max_fundos and cnpj not in fundos_processados:
                                            continue
                                        
                                        df_fundo = df[df['CNPJ_FUNDO'] == cnpj][['DT_COMPTC', 'VL_QUOTA']].copy()
                                        df_fundo = df_fundo.sort_values('DT_COMPTC')
                                        df_fundo.set_index('DT_COMPTC', inplace=True)
                                        
                                        if len(df_fundo) > 0 and df_fundo['VL_QUOTA'].notna().any():
                                            if cnpj not in series_fundos:
                                                series_fundos[cnpj] = []
                                                fundos_processados.add(cnpj)
                                                
                                                # Guardar informações do fundo
                                                if 'DENOM_SOCIAL' in df.columns:
                                                    info_fundos[cnpj] = df[df['CNPJ_FUNDO'] == cnpj]['DENOM_SOCIAL'].iloc[0]
                                            
                                            series_fundos[cnpj].append(df_fundo)
                            break
            except Exception as e:
                print(f"\nErro ao processar {nome_arquivo}: {e}")
                continue
            
            pbar_arquivos.update(1)
            pbar_arquivos.set_postfix({"Fundos": len(fundos_processados)})
    
    print(f"\nTotal de fundos encontrados: {len(series_fundos)}")
    
    # Consolidar séries temporais
    print("\nConsolidando dados...")
    retornos_mensais = {}
    
    with tqdm(total=len(series_fundos), desc="Consolidando") as pbar:
        for cnpj, lista_dfs in series_fundos.items():
            if lista_dfs:
                # Concatenar todos os DataFrames
                df_completo = pd.concat(lista_dfs)
                df_completo = df_completo[~df_completo.index.duplicated(keep='first')]
                df_completo = df_completo.sort_index()
                
                # Calcular retornos
                if len(df_completo) >= 20:
                    df_completo['retorno_diario'] = df_completo['VL_QUOTA'].pct_change()
                    
                    # Calcular retorno mensal
                    retorno_mensal = df_completo['retorno_diario'].resample('M').apply(
                        lambda x: (1 + x).prod() - 1
                    )
                    
                    if len(retorno_mensal) >= 3:  # Pelo menos 3 meses
                        retornos_mensais[cnpj] = retorno_mensal
            
            pbar.update(1)
    
    # Criar DataFrame final
    if retornos_mensais:
        df_retornos = pd.DataFrame(retornos_mensais)
        
        # Remover fundos com muitos dados faltantes
        min_observacoes = len(df_retornos) * 0.5
        df_retornos = df_retornos.dropna(thresh=min_observacoes, axis=1)
        
        print(f"\nFundos com dados completos: {len(df_retornos.columns)}")
        print(f"Período de dados: {df_retornos.index[0].strftime('%Y-%m')} a {df_retornos.index[-1].strftime('%Y-%m')}")
        
        # Salvar dados
        os.makedirs("dados_universo", exist_ok=True)
        
        # Salvar retornos
        df_retornos.to_csv("dados_universo/retornos_periodo.csv")
        print("\nDados salvos em: dados_universo/retornos_periodo.csv")
        
        # Salvar informações dos fundos
        df_info = pd.DataFrame.from_dict(info_fundos, orient='index', columns=['Nome'])
        df_info.index.name = 'CNPJ'
        df_info.to_csv("dados_universo/info_fundos_periodo.csv")
        
        # Mostrar estatísticas
        print("\nEstatísticas dos retornos:")
        print(f"Retorno médio mensal: {df_retornos.mean().mean():.2%}")
        print(f"Volatilidade média: {df_retornos.std().mean():.2%}")
        print(f"Fundos com retorno médio positivo: {(df_retornos.mean() > 0).sum()}")
        
        return df_retornos
    else:
        print("\nNenhum dado processado!")
        return pd.DataFrame()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Extrai retornos de fundos para período específico')
    parser.add_argument('--inicio', default='2023-01', help='Período inicial (YYYY-MM)')
    parser.add_argument('--fim', default='2024-08', help='Período final (YYYY-MM)')
    parser.add_argument('--max-fundos', type=int, help='Número máximo de fundos')
    
    args = parser.parse_args()
    
    df = extrair_retornos_periodo_especifico(
        periodo_inicial=args.inicio,
        periodo_final=args.fim,
        max_fundos=args.max_fundos
    )