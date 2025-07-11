"""
Financial Investment Analysis Utilities

This module provides a collection of utility functions for analyzing financial investment data,
particularly focused on fund portfolios, administration fees, and cost calculations.

The module includes functions for:
- Loading and saving serialized variables
- Processing fund portfolios
- Calculating administration fees and costs
- Analyzing fund evolution and costs
- Generating visualizations and reports

Dependencies:
- pandas: For data manipulation and analysis
- numpy: For numerical operations
- matplotlib: For data visualization
- seaborn: For enhanced statistical visualizations
- os: For file and directory operations
- datetime: For date handling
- re: For regular expressions
- zipfile: For handling compressed files
- shutil: For file operations
- io: For handling file streams
"""

import os
import re
import io
import math
import shutil
import zipfile
from datetime import datetime
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mtick
import pickle
import glob
from matplotlib.ticker import FuncFormatter
from typing import List, Dict, Optional, Union


def load_serialized_variable(file_path):
    """
    Load a serialized variable from a file.
    
    Args:
        file_path (str): Path to the file containing the serialized variable.
        
    Returns:
        The deserialized variable if successful, None otherwise.
    """
    try:
        with open(file_path, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Error loading serialized variable from {file_path}: {str(e)}")
        return None

def save_serialized_variable(variable, file_path):
    """
    Save a variable to a file using serialization.
    
    Args:
        variable: The variable to be serialized.
        file_path (str): Path where the serialized variable will be saved.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        with open(file_path, 'wb') as f:
            pickle.dump(variable, f)
        return True
    except Exception as e:
        print(f"Error saving serialized variable to {file_path}: {str(e)}")
        return False

def ensure_directory_exists(directory):
    """
    Ensure that a directory exists, creating it if necessary.
    
    Args:
        directory (str): Path to the directory to check/create.
        
    Returns:
        bool: True if directory exists or was created, False otherwise.
    """
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
        return True
    except Exception as e:
        print(f"Error creating directory {directory}: {str(e)}")
        return False

def salvar_variaveis_serial(base_dir, serie_custos, media_custos, valor_investido, nome=None):
    """
    Save analysis variables to serialized files.
    
    Args:
        base_dir (str): Base directory for saving files.
        serie_custos (pd.Series): Series containing cost data.
        media_custos (float): Average cost value.
        valor_investido (float): Total invested value.
        nome (str, optional): Name prefix for saved files.
        
    Returns:
        bool: True if all variables were saved successfully, False otherwise.
    """
    try:
        if nome:
            base_dir = os.path.join(base_dir, nome)
        ensure_directory_exists(base_dir)
        
        save_serialized_variable(serie_custos, os.path.join(base_dir, 'serie_custos.pkl'))
        save_serialized_variable(media_custos, os.path.join(base_dir, 'media_custos.pkl'))
        save_serialized_variable(valor_investido, os.path.join(base_dir, 'valor_investido.pkl'))
        return True
    except Exception as e:
        print(f"Error saving variables: {str(e)}")
        return False
    
def carregar_variaveis_serial(base_dir, nome=None):
    """
    Load analysis variables from serialized files.
    
    Args:
        base_dir (str): Base directory containing the files.
        nome (str, optional): Name prefix for files to load.
        
    Returns:
        tuple: (serie_custos, media_custos, valor_investido) if successful,
               (None, None, None) otherwise.
    """
    try:
        if nome:
            base_dir = os.path.join(base_dir, nome)
            
        serie_custos = load_serialized_variable(os.path.join(base_dir, 'serie_custos.pkl'))
        media_custos = load_serialized_variable(os.path.join(base_dir, 'media_custos.pkl'))
        valor_investido = load_serialized_variable(os.path.join(base_dir, 'valor_investido.pkl'))
        
        if all(v is not None for v in [serie_custos, media_custos, valor_investido]):
            return serie_custos, media_custos, valor_investido
        return None, None, None
    except Exception as e:
        print(f"Error loading variables: {str(e)}")
        return None, None, None

def carregar_todos_fundos(base_dir, lista_fundos):
    """
    Carrega dados de múltiplos fundos e os consolida.
    
    Args:
        base_dir (str): Diretório base onde os dados estão armazenados
        lista_fundos (list): Lista com os nomes dos fundos a serem carregados
        
    Returns:
        tuple: (serie_custos_consolidado, valor_investido_consolidado)
    """
    try:
        # Inicializar dicionários consolidados
        serie_custos_consolidado = pd.DataFrame()
        valor_investido_consolidado = {}
        
        # Carregar dados de cada fundo
        for nome_fundo in lista_fundos:
            serie_custos, media_custos, valor_investido = carregar_variaveis_serial(base_dir, nome_fundo)

            if serie_custos is not None:
                df_atual = serie_custos.copy()
                df_atual['fundo'] = nome_fundo  # Adicionar coluna identificando o fundo
                serie_custos_consolidado = pd.concat([serie_custos_consolidado, df_atual], ignore_index=True)
                
            if valor_investido is not None:
                # Adicionar valores investidos ao dicionário consolidado
                for data, valor in valor_investido.items():
                    chave = f"{data}_{nome_fundo}"
                    valor_investido_consolidado[chave] = valor

        return serie_custos_consolidado, valor_investido_consolidado
    except Exception as e:
        print(f"Erro ao carregar dados dos fundos: {str(e)}")
        return pd.DataFrame(), {}

def processar_carteiras(cnpj_fundo, base_dir, limite_arquivos=None):
    """
    Processa as carteiras de um fundo.
    
    Args:
        cnpj_fundo (str): CNPJ do fundo
        base_dir (str): Diretório base dos dados
        limite_arquivos (int, optional): Limite de arquivos a processar
        
    Returns:
        tuple: (carteiras_processadas, info_fundo) ou (None, None) em caso de erro
    """
    try:
        # Carregar dados básicos
        carteiras = carregar_dados_fundo(cnpj_fundo, base_dir)
        if carteiras is None:
            return None, None
            
        # Processar dados
        carteiras_processadas = processar_dados_carteira(carteiras)
        if carteiras_processadas is None:
            return None, None
        
        # Extrair informações do fundo
        info_fundo = extrair_info_fundo(carteiras_processadas, cnpj_fundo)
        
        return carteiras_processadas, info_fundo
    except Exception as e:
        print(f"Erro ao processar carteiras do fundo {cnpj_fundo}: {str(e)}")
        return None, None

def processar_dados_carteira(carteiras):
    """
    Process and clean portfolio data with comprehensive validation and error handling.
    
    This function performs data cleaning, validation, and transformation on portfolio data,
    including handling missing values, data type conversion, and consistency checks.
    
    Args:
        carteiras (pd.DataFrame): DataFrame containing portfolio data.
        
    Returns:
        pd.DataFrame: Processed and validated portfolio data.
        
    Raises:
        ValueError: If input data is invalid or processing fails
    """
    try:
        # Input validation
        if carteiras is None or carteiras.empty:
            raise ValueError("Invalid input data: portfolio data is None or empty")
            
        # Create a copy to avoid modifying the original
        carteiras_processadas = carteiras.copy()
        
        # Remove duplicates with logging
        n_duplicates = carteiras_processadas.duplicated().sum()
        if n_duplicates > 0:
            print(f"Removing {n_duplicates} duplicate rows")
            carteiras_processadas = carteiras_processadas.drop_duplicates()
            
        # Convert date columns
        date_columns = [col for col in carteiras_processadas.columns if 'data' in col.lower()]
        for col in date_columns:
            try:
                carteiras_processadas[col] = pd.to_datetime(carteiras_processadas[col])
            except Exception as e:
                print(f"Warning: Could not convert column {col} to datetime: {str(e)}")
                
        # Sort by date if available
        if 'data' in carteiras_processadas.columns:
            carteiras_processadas = carteiras_processadas.sort_values('data')
            
        # Validate and clean numeric columns
        numeric_columns = ['pl', 'valor_investido', 'taxa_administracao']
        for col in numeric_columns:
            if col in carteiras_processadas.columns:
                try:
                    # Convert to numeric, replacing non-numeric values with NaN
                    carteiras_processadas[col] = pd.to_numeric(carteiras_processadas[col], errors='coerce')
                    
                    # Check for negative values
                    if (carteiras_processadas[col] < 0).any():
                        print(f"Warning: Negative values found in column {col}")
                        
                    # Check for outliers using IQR method
                    Q1 = carteiras_processadas[col].quantile(0.25)
                    Q3 = carteiras_processadas[col].quantile(0.75)
                    IQR = Q3 - Q1
                    outliers = carteiras_processadas[
                        (carteiras_processadas[col] < (Q1 - 1.5 * IQR)) | 
                        (carteiras_processadas[col] > (Q3 + 1.5 * IQR))
                    ]
                    if not outliers.empty:
                        print(f"Warning: {len(outliers)} outliers found in column {col}")
                except Exception as e:
                    print(f"Warning: Could not process numeric column {col}: {str(e)}")
        
        return carteiras_processadas
    except Exception as e:
        print(f"Error processing portfolio data: {str(e)}")
        return None

def calcular_valores_carteira(carteiras):
    """
    Calcula valores derivados da carteira.
    
    Args:
        carteiras (pd.DataFrame): DataFrame com dados da carteira
        
    Returns:
        pd.DataFrame: DataFrame com valores calculados
    """
    try:
        # Calcular PL
        carteiras['pl'] = carteiras['quantidade'] * carteiras['preco_medio']
        
        # Calcular variação
        carteiras['variacao'] = carteiras['preco_medio'].pct_change()
        
        return carteiras
    except Exception as e:
        print(f"Erro ao calcular valores da carteira: {str(e)}")
        return carteiras

def extrair_info_fundo(carteiras, cnpj_fundo):
    """
    Extrai informações relevantes do fundo.
    
    Args:
        carteiras (pd.DataFrame): DataFrame com dados da carteira
        cnpj_fundo (str): CNPJ do fundo
        
    Returns:
        dict: Dicionário com informações do fundo
    """
    try:
        info = {
            'cnpj': cnpj_fundo,
            'data_inicio': carteiras['data'].min(),
            'data_fim': carteiras['data'].max(),
            'pl_medio': carteiras['pl'].mean(),
            'variacao_media': carteiras['variacao'].mean()
        }
        return info
    except Exception as e:
        print(f"Erro ao extrair informações do fundo {cnpj_fundo}: {str(e)}")
        return None

def calcular_custos_taxas(carteiras_com_taxas, dir_saida):
    """
    Calcula custos e taxas das carteiras.
    
    Args:
        carteiras_com_taxas (pd.DataFrame): DataFrame com carteiras e taxas
        dir_saida (str): Diretório para salvar resultados
        
    Returns:
        dict: Dicionário com resultados da análise
    """
    try:
        # Preparar diretório de saída
        if not criar_diretorio_saida(dir_saida):
            return None
            
        # Calcular custos
        custos = calcular_custos_por_periodo(carteiras_com_taxas)
        if custos is None:
            return None
            
        # Calcular médias
        medias = calcular_medias_custos(custos)
        if medias is None:
            return None
            
        # Salvar resultados
        if not salvar_resultados_custos(custos, medias, dir_saida):
            return None
            
        return {
            'custos': custos,
            'medias': medias
        }
    except Exception as e:
        print(f"Erro ao calcular custos e taxas: {str(e)}")
        return None

def calcular_custos_por_periodo(carteiras):
    """
    Calcula custos por período.
    
    Args:
        carteiras (pd.DataFrame): DataFrame com carteiras e taxas
        
    Returns:
        pd.DataFrame: DataFrame com custos por período
    """
    try:
        # Agrupar por data e calcular somas e médias
        custos = carteiras.groupby('data').agg({
            'pl': 'sum',
            'taxa_administracao': 'mean',
            'taxa_performance': 'mean'
        }).reset_index()
        
        # Calcular custo total
        custos['custo_total'] = custos['pl'] * (custos['taxa_administracao'] + custos['taxa_performance'])
        
        # Calcular custo mensal
        custos['custo_mensal'] = custos['custo_total'] / 12
        
        # Calcular percentual de custo
        custos['percentual_custo'] = (custos['custo_mensal'] / custos['pl']) * 100
        
        return custos
    except Exception as e:
        print(f"Erro ao calcular custos por período: {str(e)}")
        return None

def calcular_medias_custos(custos):
    """
    Calcula médias dos custos.
    
    Args:
        custos (pd.DataFrame): DataFrame com custos por período
        
    Returns:
        dict: Dicionário com médias calculadas
    """
    try:
        return {
            'pl_medio': custos['pl'].mean(),
            'taxa_adm_media': custos['taxa_administracao'].mean(),
            'taxa_perf_media': custos['taxa_performance'].mean(),
            'custo_total_medio': custos['custo_total'].mean(),
            'custo_mensal_medio': custos['custo_mensal'].mean(),
            'percentual_custo_medio': custos['percentual_custo'].mean()
        }
    except Exception as e:
        print(f"Erro ao calcular médias dos custos: {str(e)}")
        return None

def salvar_resultados_custos(custos, medias, dir_saida):
    """
    Salva resultados dos custos.
    
    Args:
        custos (pd.DataFrame): DataFrame com custos por período
        medias (dict): Dicionário com médias calculadas
        dir_saida (str): Diretório para salvar resultados
        
    Returns:
        bool: True se salvou com sucesso, False caso contrário
    """
    try:
        # Criar diretório se não existir
        if not os.path.exists(dir_saida):
            os.makedirs(dir_saida)
            
        # Salvar custos por período
        arquivo_custos = os.path.join(dir_saida, 'custos_por_periodo.csv')
        custos.to_csv(arquivo_custos, index=False, encoding='utf-8-sig')
        
        # Salvar médias
        arquivo_medias = os.path.join(dir_saida, 'medias_custos.csv')
        pd.DataFrame([medias]).to_csv(arquivo_medias, index=False, encoding='utf-8-sig')
        
        print(f"Resultados salvos em:")
        print(f"- Custos por período: {arquivo_custos}")
        print(f"- Médias dos custos: {arquivo_medias}")
        
        return True
    except Exception as e:
        print(f"Erro ao salvar resultados dos custos: {str(e)}")
        return False

def criar_diretorio_saida(dir_saida):
    """
    Cria o diretório de saída se não existir.
    
    Args:
        dir_saida (str): Caminho do diretório de saída
        
    Returns:
        bool: True se o diretório existe ou foi criado, False caso contrário
    """
    try:
        if not os.path.exists(dir_saida):
            os.makedirs(dir_saida)
        return True
    except Exception as e:
        print(f"Erro ao criar diretório de saída {dir_saida}: {str(e)}")
        return False

def adicionar_taxas_administracao(carteiras, fund_info):
    """
    Adiciona taxas de administração às carteiras.
    
    Args:
        carteiras (dict): Dicionário com DataFrames das carteiras por período
        fund_info (pd.DataFrame): DataFrame com informações dos fundos
        
    Returns:
        dict: Dicionário com carteiras atualizadas com taxas
    """
    try:
        carteiras_com_taxas = {}
        
        for data_ref, df_carteira in carteiras.items():
            print(f"Processando taxas para o período {data_ref}...")
            
            # Identificar coluna de CNPJ
            coluna_cnpj = identificar_coluna_cnpj(df_carteira)
            if coluna_cnpj is None:
                print(f"  - Não foi possível identificar coluna com CNPJ para {data_ref}")
                carteiras_com_taxas[data_ref] = df_carteira
                continue
        
            # Processar carteira
            df_processado = processar_carteira_com_taxas(df_carteira, coluna_cnpj, fund_info)
            if df_processado is not None:
                carteiras_com_taxas[data_ref] = df_processado
            else:
                carteiras_com_taxas[data_ref] = df_carteira
                
        return carteiras_com_taxas
    except Exception as e:
        print(f"Erro ao adicionar taxas de administração: {str(e)}")
        return carteiras

def identificar_coluna_cnpj(df):
    """
    Identifica a coluna que contém o CNPJ dos fundos.
    
    Args:
        df (pd.DataFrame): DataFrame com dados da carteira
        
    Returns:
        str: Nome da coluna com CNPJ ou None se não encontrada
    """
    colunas_cnpj = ['CNPJ_FUNDO_CLASSE_COTA', 'CNPJ_FUNDO_COTA', 'CPF_CNPJ_EMISSOR', 'CNPJ_EMISSOR']
    for col in colunas_cnpj:
        if col in df.columns:
            return col
    return None

def processar_carteira_com_taxas(df_carteira, coluna_cnpj, fund_info):
    """
    Processa uma carteira adicionando taxas de administração.
    
    Args:
        df_carteira (pd.DataFrame): DataFrame da carteira
        coluna_cnpj (str): Nome da coluna com CNPJ
        fund_info (pd.DataFrame): DataFrame com informações dos fundos
        
    Returns:
        pd.DataFrame: Carteira processada com taxas ou None em caso de erro
    """
    try:
        # Criar cópia do DataFrame
        df_processado = df_carteira.copy()
        
        # Preparar mapeamento de taxas
        taxa_por_cnpj = preparar_mapeamento_taxas(fund_info)
        
        # Adicionar taxas
        df_processado = adicionar_taxas_ao_dataframe(df_processado, coluna_cnpj, taxa_por_cnpj)
        
        # Verificar resultados
        total_fundos = len(df_processado)
        fundos_com_taxa = df_processado['TAXA_ADM'].notna().sum()
        print(f"  - {fundos_com_taxa} de {total_fundos} fundos possuem taxa ({fundos_com_taxa/total_fundos*100:.1f}%)")
        
        return df_processado
    except Exception as e:
        print(f"Erro ao processar carteira: {str(e)}")
        return None

def preparar_mapeamento_taxas(fund_info):
    """
    Prepara dicionário de mapeamento CNPJ -> taxa.
    
    Args:
        fund_info (pd.DataFrame): DataFrame com informações dos fundos
        
    Returns:
        dict: Dicionário com mapeamento CNPJ -> taxa
    """
    try:
        # Limpar dados duplicados
        fund_info_clean = fund_info[['CNPJ_FUNDO', 'TAXA_ADM']].copy()
        fund_info_clean = fund_info_clean.drop_duplicates(subset=['CNPJ_FUNDO'], keep='first')
        
        # Criar dicionário
        return dict(zip(fund_info_clean['CNPJ_FUNDO'], fund_info_clean['TAXA_ADM']))
    except Exception as e:
        print(f"Erro ao preparar mapeamento de taxas: {str(e)}")
        return {}

def adicionar_taxas_ao_dataframe(df, coluna_cnpj, taxa_por_cnpj):
    """
    Adiciona taxas ao DataFrame baseado no CNPJ.
    
    Args:
        df (pd.DataFrame): DataFrame a ser processado
        coluna_cnpj (str): Nome da coluna com CNPJ
        taxa_por_cnpj (dict): Dicionário com mapeamento CNPJ -> taxa
        
    Returns:
        pd.DataFrame: DataFrame com taxas adicionadas
    """
    try:
        # Renomear coluna existente se necessário
        if 'TAXA_ADM' in df.columns:
            df = df.rename(columns={'TAXA_ADM': 'TAXA_ADM_ORIGINAL'})
            
        # Mapear taxas
        df['TAXA_ADM'] = df[coluna_cnpj].map(taxa_por_cnpj)
        
        # Converter para numérico
        df['TAXA_ADM'] = pd.to_numeric(df['TAXA_ADM'], errors='coerce')
        
        return df
    except Exception as e:
        print(f"Erro ao adicionar taxas ao DataFrame: {str(e)}")
        return df

def adicionar_taxas_manuais(carteiras, fund_info):
    """
    Adiciona taxas manuais às carteiras.
    
    Args:
        carteiras (dict): Dicionário com DataFrames das carteiras por período
        fund_info (pd.DataFrame): DataFrame com informações dos fundos
        
    Returns:
        dict: Dicionário com carteiras atualizadas com taxas manuais
    """
    try:
        # Carregar taxas manuais
        taxas_manuais = carregar_taxas_manuais()
        
        carteiras_com_taxas = {}
        
        for data_ref, df_carteira in carteiras.items():
            print(f"Processando taxas manuais para o período {data_ref}...")
            
            # Identificar coluna de CNPJ
            coluna_cnpj = identificar_coluna_cnpj(df_carteira)
            if coluna_cnpj is None:
                print(f"  - Não foi possível identificar coluna com CNPJ para {data_ref}")
                carteiras_com_taxas[data_ref] = df_carteira
                continue
                
            # Processar carteira com taxas manuais
            df_processado = processar_carteira_com_taxas_manuais(df_carteira, coluna_cnpj, fund_info, taxas_manuais)
            if df_processado is not None:
                carteiras_com_taxas[data_ref] = df_processado
            else:
                carteiras_com_taxas[data_ref] = df_carteira
                
        return carteiras_com_taxas
    except Exception as e:
        print(f"Erro ao adicionar taxas manuais: {str(e)}")
        return carteiras

def carregar_taxas_manuais():
    """
    Carrega o dicionário de taxas manuais.
    
    Returns:
        dict: Dicionário com taxas manuais por CNPJ
    """
    return {
        '05.584.551/0001-63': 0.00,
        '07.096.546/0001-37': 0.00,
        '09.145.104/0001-69': 0.00,
        '11.858.506/0001-52': 0.35,
        '12.138.862/0001-64': 2.50,
        '15.603.942/0001-31': 1.96,
        '17.329.489/0001-42': 0.00,
        '18.138.913/0001-34': 0.15,
        '18.489.912/0001-34': 2.20,
        '21.407.105/0001-30': 0.20,
        '22.014.217/0001-93': 0.10,
        '24.546.223/0001-17': 0.00,
        '26.262.541/0001-81': 0.20,
        '28.653.719/0001-40': 0.50,
        '29.941.680/0001-20': 0.35,
        '29.993.554/0001-19': 1.90,
        '31.819.421/0001-72': 0.00,
        '32.311.914/0001-60': 0.00,
        '32.745.001/0001-51': 1.98,
        '31.820.746/0001-75': 0.35,
        '32.320.730/0001-66': 1.90,
        '37.052.449/0001-03': 1.90,
        '40.635.100/0001-09': 2.00,
        '41.535.122/0001-60': 0.00001,
        '42.317.906/0001-84': 1.90,
        '50.324.325/0001-06': 0.00,
        '55.345.429/0001-02': 0.00001,
        '55.419.784/0001-89': 0.00,
        '55.655.844/0001-62': 2.00,
        '56.430.872/0001-44': 0.00,
        '58.132.740/0001-61': 0.50
    }
    
def processar_carteira_com_taxas_manuais(df_carteira, coluna_cnpj, fund_info, taxas_manuais):
    """
    Processa uma carteira adicionando taxas manuais.
    
    Args:
        df_carteira (pd.DataFrame): DataFrame da carteira
        coluna_cnpj (str): Nome da coluna com CNPJ
        fund_info (pd.DataFrame): DataFrame com informações dos fundos
        taxas_manuais (dict): Dicionário com taxas manuais
        
    Returns:
        pd.DataFrame: Carteira processada com taxas manuais ou None em caso de erro
    """
    try:
        # Criar cópia do DataFrame
        df_processado = df_carteira.copy()
        
        # Preparar mapeamento de taxas
        taxa_por_cnpj = preparar_mapeamento_taxas(fund_info)
        
        # Adicionar taxas manuais ao mapeamento
        taxa_por_cnpj.update(taxas_manuais)
        
        # Adicionar taxas
        df_processado = adicionar_taxas_ao_dataframe(df_processado, coluna_cnpj, taxa_por_cnpj)
        
        # Verificar resultados
        total_fundos = len(df_processado)
        fundos_com_taxa = df_processado['TAXA_ADM'].notna().sum()
        print(f"  - {fundos_com_taxa} de {total_fundos} fundos possuem taxa ({fundos_com_taxa/total_fundos*100:.1f}%)")
        
        return df_processado
    except Exception as e:
        print(f"Erro ao processar carteira com taxas manuais: {str(e)}")
        return None

def extrair_cnpjs_sem_taxa(carteiras_com_taxas):
 
    # Dicionário para armazenar os CNPJs sem taxa por período
    cnpjs_sem_taxa_por_periodo = {}
    
    # Conjunto para armazenar todos os CNPJs sem taxa (para eliminar duplicatas)
    todos_cnpjs_sem_taxa = set()
    
    # Processa cada período
    for data, df in carteiras_com_taxas.items():
        print(f"Processando período: {data}")
        
        # Verifica se a coluna TAXA_ADM existe
        if 'TAXA_ADM' not in df.columns:
            print(f"  - Coluna TAXA_ADM não encontrada para o período {data}")
            continue
        
        # Identifica a coluna que contém o CNPJ dos fundos
        coluna_cnpj = None
        for col in ['CNPJ_FUNDO_CLASSE_COTA', 'CNPJ_FUNDO_COTA', 'CPF_CNPJ_EMISSOR', 'CNPJ_EMISSOR']:
            if col in df.columns:
                coluna_cnpj = col
                break
        
        if coluna_cnpj is None:
            print(f"  - Não foi possível identificar coluna com CNPJ dos fundos para {data}")
            continue
        
        # Identifica a coluna de nome dos fundos, se disponível
        coluna_nome = None
        for col in ['NM_FUNDO_CLASSE_SUBCLASSE_COTA', 'NM_FUNDO_COTA', 'DENOM_SOCIAL_EMISSOR']:
            if col in df.columns:
                coluna_nome = col
                break
        
        # Filtra fundos com taxa 0 ou NaN
        df_sem_taxa = df[(df['TAXA_ADM'].isna()) | (df['TAXA_ADM'] == 0)]
        
        if len(df_sem_taxa) > 0:
            # Extrai os CNPJs únicos
            cnpjs_periodo = set(df_sem_taxa[coluna_cnpj].unique())
            cnpjs_sem_taxa_por_periodo[data] = cnpjs_periodo
            
            # Adiciona ao conjunto global
            todos_cnpjs_sem_taxa.update(cnpjs_periodo)
            
            print(f"  - Encontrados {len(cnpjs_periodo)} CNPJs únicos com taxa 0 ou NaN")
            
            # Se tivermos a coluna de nome, exibe alguns exemplos
            if coluna_nome:
                print("  - Exemplos:")
                for _, row in df_sem_taxa.head(3).iterrows():
                    cnpj = row[coluna_cnpj]
                    nome = row[coluna_nome]
                    taxa = row['TAXA_ADM']
                    taxa_str = 'NaN' if pd.isna(taxa) else taxa
                    print(f"    - {nome} (CNPJ: {cnpj}, Taxa: {taxa_str})")
    
    # Converte o conjunto para lista e ordena
    lista_cnpjs_sem_taxa = sorted(list(todos_cnpjs_sem_taxa))
    
    # Resumo final
    print(f"\nTotal de CNPJs únicos com taxa 0 ou NaN em todos os períodos: {len(lista_cnpjs_sem_taxa)}")
    
    # Análise de frequência
    frequencia_por_cnpj = {}
    for cnpj in lista_cnpjs_sem_taxa:
        frequencia = sum(1 for cnpjs_periodo in cnpjs_sem_taxa_por_periodo.values() if cnpj in cnpjs_periodo)
        frequencia_por_cnpj[cnpj] = frequencia
    
    # Ordena por frequência (decrescente)
    cnpjs_ordenados = sorted(frequencia_por_cnpj.items(), key=lambda x: x[1], reverse=True)
    
    # Exibe os CNPJs mais frequentes
    total_periodos = len(cnpjs_sem_taxa_por_periodo)
    print("\nTop CNPJs que aparecem com mais frequência como tendo taxa 0 ou NaN:")
    for cnpj, freq in cnpjs_ordenados[:10]:  # Top 10
        percentual = freq / total_periodos * 100
        print(f"  - CNPJ: {cnpj} - Aparece em {freq}/{total_periodos} períodos ({percentual:.1f}%)")
    
    return lista_cnpjs_sem_taxa

def analisar_evolucao_custos(custos: pd.DataFrame, dir_saida: Optional[str] = None) -> Dict[str, Union[pd.DataFrame, Dict[str, float]]]:
    """
    Analisa evolução dos custos ao longo do tempo.
    
    Args:
        custos (pd.DataFrame): DataFrame com custos por período
        dir_saida (str, optional): Diretório para salvar resultados
        
    Returns:
        dict: Dicionário com resultados da análise
    """
    try:
        # Calcular estatísticas
        stats = calcular_estatisticas_custos(custos)
        if stats is None:
            return {}
            
        # Gerar visualizações
        if dir_saida:
            gerar_visualizacoes_custos(custos, stats, dir_saida)
            
        return {
            'estatisticas': stats,
            'custos': custos
        }
    except Exception as e:
        print(f"Erro ao analisar evolução dos custos: {str(e)}")
        return {}

def calcular_estatisticas_custos(custos: pd.DataFrame) -> Optional[Dict[str, float]]:
    """
    Calcula estatísticas dos custos.
    
    Args:
        custos (pd.DataFrame): DataFrame com custos por período
        
    Returns:
        dict: Dicionário com estatísticas calculadas
    """
    try:
        return {
            'pl_maximo': custos['pl'].max(),
            'pl_minimo': custos['pl'].min(),
            'pl_medio': custos['pl'].mean(),
            'custo_total_maximo': custos['custo_total'].max(),
            'custo_total_minimo': custos['custo_total'].min(),
            'custo_total_medio': custos['custo_total'].mean(),
            'percentual_custo_maximo': custos['percentual_custo'].max(),
            'percentual_custo_minimo': custos['percentual_custo'].min(),
            'percentual_custo_medio': custos['percentual_custo'].mean()
        }
    except Exception as e:
        print(f"Erro ao calcular estatísticas dos custos: {str(e)}")
        return None

def gerar_visualizacoes_custos(custos: pd.DataFrame, stats: Dict[str, float], dir_saida: str) -> bool:
    """
    Gera visualizações dos custos.
    
    Args:
        custos (pd.DataFrame): DataFrame com custos por período
        stats (dict): Dicionário com estatísticas calculadas
        dir_saida (str): Diretório para salvar visualizações
        
    Returns:
        bool: True se gerou com sucesso, False caso contrário
    """
    try:
        ensure_directory_exists(dir_saida)
        
        # Configurar estilo dos gráficos
        plt.style.use('seaborn')
        
        # Gráfico de evolução do PL
        plt.figure(figsize=(12, 6))
        plt.plot(custos['data'], custos['pl'], label='PL')
        plt.title('Evolução do PL')
        plt.xlabel('Data')
        plt.ylabel('PL (R$)')
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(dir_saida, 'evolucao_pl.png'))
        plt.close()

        # Gráfico de evolução dos custos
        plt.figure(figsize=(12, 6))
        plt.plot(custos['data'], custos['custo_total'], label='Custo Total')
        plt.plot(custos['data'], custos['custo_mensal'], label='Custo Mensal')
        plt.title('Evolução dos Custos')
        plt.xlabel('Data')
        plt.ylabel('Custo (R$)')
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(dir_saida, 'evolucao_custos.png'))
        plt.close()
        
        # Gráfico de percentual de custo
        plt.figure(figsize=(12, 6))
        plt.plot(custos['data'], custos['percentual_custo'], label='% Custo')
        plt.title('Evolução do Percentual de Custo')
        plt.xlabel('Data')
        plt.ylabel('Percentual (%)')
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(dir_saida, 'evolucao_percentual_custo.png'))
        plt.close()

        print(f"Visualizações salvas em: {dir_saida}")
        return True
    except Exception as e:
        print(f"Erro ao gerar visualizações dos custos: {str(e)}")
        return False

def analisar_fundos_sem_taxa(carteiras: pd.DataFrame, dir_saida: Optional[str] = None) -> Dict[str, Union[pd.DataFrame, Dict[str, float]]]:
    """
    Analisa fundos sem taxa de administração.
    
    Args:
        carteiras (pd.DataFrame): DataFrame com dados das carteiras
        dir_saida (str, optional): Diretório para salvar resultados
        
    Returns:
        dict: Dicionário com resultados da análise
    """
    try:
        # Identificar fundos sem taxa
        fundos_sem_taxa = identificar_fundos_sem_taxa(carteiras)
        if fundos_sem_taxa is None:
            return {}
            
        # Calcular estatísticas
        stats = calcular_estatisticas_fundos_sem_taxa(fundos_sem_taxa)
        if stats is None:
            return {}
            
        # Gerar visualizações
        if dir_saida:
            gerar_visualizacoes_fundos_sem_taxa(fundos_sem_taxa, stats, dir_saida)
            
        return {
            'fundos_sem_taxa': fundos_sem_taxa,
            'estatisticas': stats
        }
    except Exception as e:
        print(f"Erro ao analisar fundos sem taxa: {str(e)}")
        return {}

def identificar_fundos_sem_taxa(carteiras: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Identifica fundos sem taxa de administração.
    
    Args:
        carteiras (pd.DataFrame): DataFrame com dados das carteiras
        
    Returns:
        pd.DataFrame: DataFrame com fundos sem taxa
    """
    try:
        # Filtrar fundos com taxa zero
        fundos_sem_taxa = carteiras[carteiras['taxa_administracao'] == 0].copy()
        
        # Agrupar por CNPJ e calcular estatísticas
        fundos_sem_taxa = fundos_sem_taxa.groupby('cnpj').agg({
            'pl': ['mean', 'sum', 'count'],
            'variacao': 'mean'
                                }).reset_index()
                            
        # Renomear colunas
        fundos_sem_taxa.columns = ['cnpj', 'pl_medio', 'pl_total', 'num_periodos', 'variacao_media']
        
        return fundos_sem_taxa
    except Exception as e:
        print(f"Erro ao identificar fundos sem taxa: {str(e)}")
        return None

def calcular_estatisticas_fundos_sem_taxa(fundos_sem_taxa: pd.DataFrame) -> Optional[Dict[str, float]]:
    """
    Calcula estatísticas dos fundos sem taxa.
    
    Args:
        fundos_sem_taxa (pd.DataFrame): DataFrame com fundos sem taxa
        
    Returns:
        dict: Dicionário com estatísticas calculadas
    """
    try:
        return {
            'num_fundos': len(fundos_sem_taxa),
            'pl_total_medio': fundos_sem_taxa['pl_total'].mean(),
            'pl_medio_medio': fundos_sem_taxa['pl_medio'].mean(),
            'variacao_media_media': fundos_sem_taxa['variacao_media'].mean()
        }
    except Exception as e:
        print(f"Erro ao calcular estatísticas dos fundos sem taxa: {str(e)}")
        return None

def gerar_visualizacoes_fundos_sem_taxa(fundos_sem_taxa: pd.DataFrame, stats: Dict[str, float], dir_saida: str) -> bool:
    """
    Gera visualizações dos fundos sem taxa.
    
    Args:
        fundos_sem_taxa (pd.DataFrame): DataFrame com fundos sem taxa
        stats (dict): Dicionário com estatísticas calculadas
        dir_saida (str): Diretório para salvar visualizações
        
    Returns:
        bool: True se gerou com sucesso, False caso contrário
    """
    try:
        ensure_directory_exists(dir_saida)
        
        # Configurar estilo dos gráficos
        plt.style.use('seaborn')
        
        # Gráfico de PL total por fundo
        plt.figure(figsize=(12, 6))
        plt.bar(fundos_sem_taxa['cnpj'], fundos_sem_taxa['pl_total'])
        plt.title('PL Total por Fundo Sem Taxa')
        plt.xlabel('CNPJ')
        plt.ylabel('PL Total (R$)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(dir_saida, 'pl_total_fundos_sem_taxa.png'))
        plt.close()
        
        # Gráfico de variação média por fundo
        plt.figure(figsize=(12, 6))
        plt.bar(fundos_sem_taxa['cnpj'], fundos_sem_taxa['variacao_media'])
        plt.title('Variação Média por Fundo Sem Taxa')
        plt.xlabel('CNPJ')
        plt.ylabel('Variação Média (%)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(dir_saida, 'variacao_media_fundos_sem_taxa.png'))
        plt.close()
        
        print(f"Visualizações salvas em: {dir_saida}")
        return True
    except Exception as e:
        print(f"Erro ao gerar visualizações dos fundos sem taxa: {str(e)}")
        return False

def calcular_taxa_efetiva_fundos_zero_taxa(carteiras_originais: pd.DataFrame, cnpjs_sem_taxa: List[str], dir_saida: str, base_dir: Optional[str] = None, limite_arquivos: int = 10) -> Dict[str, Union[pd.DataFrame, Dict[str, float]]]:
    """
    Calcula taxa efetiva para fundos sem taxa de administração.
    
    Args:
        carteiras_originais (pd.DataFrame): DataFrame com dados das carteiras originais
        cnpjs_sem_taxa (list): Lista de CNPJs dos fundos sem taxa
        dir_saida (str): Diretório para salvar resultados
        base_dir (str, optional): Diretório base para carregar dados adicionais
        limite_arquivos (int): Limite de arquivos a serem processados
        
    Returns:
        dict: Dicionário com resultados do cálculo
    """
    try:
        # Criar diretório de saída
        ensure_directory_exists(dir_saida)
        
        # Filtrar fundos sem taxa
        fundos_sem_taxa = carteiras_originais[carteiras_originais['cnpj'].isin(cnpjs_sem_taxa)].copy()
        if fundos_sem_taxa.empty:
            print("Nenhum fundo sem taxa encontrado")
            return {}
            
        # Calcular estatísticas
        stats = calcular_estatisticas_fundos_sem_taxa(fundos_sem_taxa)
        if stats is None:
            return {}
            
        # Gerar visualizações
        gerar_visualizacoes_fundos_sem_taxa(fundos_sem_taxa, stats, dir_saida)
        
        return {
            'fundos_sem_taxa': fundos_sem_taxa,
            'estatisticas': stats
        }
    except Exception as e:
        print(f"Erro ao calcular taxa efetiva para fundos sem taxa: {str(e)}")
        return {}

def combinar_taxas_efetivas(carteiras: pd.DataFrame, taxas_efetivas: Dict[str, float]) -> pd.DataFrame:
    """
    Combina taxas efetivas com dados das carteiras.
    
    Args:
        carteiras (pd.DataFrame): DataFrame com dados das carteiras
        taxas_efetivas (dict): Dicionário com taxas efetivas por CNPJ
        
    Returns:
        pd.DataFrame: DataFrame com taxas efetivas combinadas
    """
    try:
        # Criar cópia do DataFrame
        carteiras_com_taxas = carteiras.copy()
        
        # Adicionar coluna de taxa efetiva
        carteiras_com_taxas['taxa_efetiva'] = carteiras_com_taxas['cnpj'].map(taxas_efetivas)
        
        # Preencher valores nulos com taxa de administração
        carteiras_com_taxas['taxa_efetiva'] = carteiras_com_taxas['taxa_efetiva'].fillna(carteiras_com_taxas['taxa_administracao'])
        
        return carteiras_com_taxas
    except Exception as e:
        print(f"Erro ao combinar taxas efetivas: {str(e)}")
        return carteiras

def extrair_pl_taxas(carteiras: pd.DataFrame) -> pd.DataFrame:
    """
    Extrai PL e taxas das carteiras.
    
    Args:
        carteiras (pd.DataFrame): DataFrame com dados das carteiras
        
    Returns:
        pd.DataFrame: DataFrame com PL e taxas
    """
    try:
        # Selecionar colunas relevantes
        pl_taxas = carteiras[['cnpj', 'pl', 'taxa_administracao', 'taxa_efetiva']].copy()
        
        # Agrupar por CNPJ e calcular médias
        pl_taxas = pl_taxas.groupby('cnpj').agg({
            'pl': 'mean',
            'taxa_administracao': 'mean',
            'taxa_efetiva': 'mean'
        }).reset_index()
        
        return pl_taxas
    except Exception as e:
        print(f"Erro ao extrair PL e taxas: {str(e)}")
        return pd.DataFrame()

def plotar_pl_custos_niveis(df_pl: pd.DataFrame, valores_investidos: Dict[str, float], titulo: str = "Fundo Aconcagua", caminho_saida: Optional[str] = None) -> None:
    """
    Gera gráfico de PL e custos por nível.
    
    Args:
        df_pl (pd.DataFrame): DataFrame com dados de PL e custos
        valores_investidos (dict): Dicionário com valores investidos por período
        titulo (str): Título do gráfico
        caminho_saida (str, optional): Caminho para salvar o gráfico
    """
    try:
        # Criar figura
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Plotar PL
        ax.plot(df_pl['data'], df_pl['pl'], label='PL', color='blue')
        
        # Plotar custos por nível
        ax.plot(df_pl['data'], df_pl['nivel_1'], label='Nível 1', color='green')
        ax.plot(df_pl['data'], df_pl['nivel_2'], label='Nível 2', color='orange')
        ax.plot(df_pl['data'], df_pl['nivel_3'], label='Nível 3', color='red')
        
        # Configurar eixos
        ax.set_title(titulo)
        ax.set_xlabel('Data')
        ax.set_ylabel('Valor (R$)')
        ax.legend()
        ax.grid(True)
        
        # Formatar eixos
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x:,.2f}'))
        plt.xticks(rotation=45)
        
        # Ajustar layout
        plt.tight_layout()
        
        # Salvar gráfico
        if caminho_saida:
            plt.savefig(caminho_saida)
            plt.close()
        else:
            plt.show()
            
    except Exception as e:
        print(f"Erro ao gerar gráfico de PL e custos: {str(e)}")

def plotar_pl_custos_niveis_multi_fundos(df_pl_list: List[pd.DataFrame], titulos: List[str], caminho_saida: Optional[str] = None) -> None:
    """
    Gera gráfico de PL e custos por nível para múltiplos fundos.
    
    Args:
        df_pl_list (list): Lista de DataFrames com dados de PL e custos
        titulos (list): Lista de títulos para cada fundo
        caminho_saida (str, optional): Caminho para salvar o gráfico
    """
    try:
        # Criar figura
        fig, axes = plt.subplots(len(df_pl_list), 1, figsize=(12, 6*len(df_pl_list)))
        
        # Plotar cada fundo
        for i, (df_pl, titulo) in enumerate(zip(df_pl_list, titulos)):
            ax = axes[i] if len(df_pl_list) > 1 else axes
            
            # Plotar PL
            ax.plot(df_pl['data'], df_pl['pl'], label='PL', color='blue')
            
            # Plotar custos por nível
            ax.plot(df_pl['data'], df_pl['nivel_1'], label='Nível 1', color='green')
            ax.plot(df_pl['data'], df_pl['nivel_2'], label='Nível 2', color='orange')
            ax.plot(df_pl['data'], df_pl['nivel_3'], label='Nível 3', color='red')
            
            # Configurar eixos
            ax.set_title(titulo)
            ax.set_xlabel('Data')
            ax.set_ylabel('Valor (R$)')
            ax.legend()
            ax.grid(True)
            
            # Formatar eixos
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x:,.2f}'))
            plt.xticks(rotation=45)
        
        # Ajustar layout
        plt.tight_layout()
        
        # Salvar gráfico
        if caminho_saida:
            plt.savefig(caminho_saida)
            plt.close()
        else:
            plt.show()
    
    except Exception as e:
        print(f"Erro ao gerar gráfico de PL e custos para múltiplos fundos: {str(e)}")

def plotar_pl_custos_niveis_multi_fundos(serie_custos_consolidado, valor_investido_consolidado, titulo="Fundos Consolidados", caminho_saida=None):
    """
    Gera um gráfico com barras empilhadas para o PL de diferentes fundos, área preenchida para o valor investido,
    e três linhas em tons de vermelho para os diferentes níveis de custo somados.
    
    Args:
        serie_custos_consolidado (DataFrame): DataFrame com dados dos fundos
        valor_investido_consolidado (dict): Valores investidos por fundo e período no formato 'YYYY-MM_fundo': valor
        titulo (str): Título do gráfico
        caminho_saida (str): Caminho para salvar o gráfico (opcional)
    
    Returns:
        matplotlib.figure.Figure: Objeto figura do matplotlib
    """
    df_dados = serie_custos_consolidado
    
    # Verificar se temos dados
    if df_dados is None or df_dados.empty:
        print("Sem dados para plotar.")
        return None
    
    # Converter para datetime se não for
    if not pd.api.types.is_datetime64_any_dtype(df_dados['data']):
        df_dados['data'] = pd.to_datetime(df_dados['data'])
    
    # Adicionar coluna de ano_mes para facilitar o agrupamento
    df_dados['ano_mes'] = df_dados['data'].dt.strftime('%Y-%m')
    
    # Identificar fundos únicos
    fundos = df_dados['fundo'].unique()
    
    # Criar figura com tamanho adequado
    plt.figure(figsize=(16, 10))
    
    # Criar dois eixos Y (um para o PL/investido e outro para o custo)
    ax1 = plt.subplot(111)
    ax2 = ax1.twinx()
    
    # Configurar cores para os fundos
    cores_fundos = {
        'chimborazo': '#CD853F',   # Marrom mais claro (Peru/Tan)
        'aconcagua': '#A0A0A0',    # Cinza claro (da função original)
        'alpamayo': '#1A5276'      # Azul escuro
    }
    
    # Caso haja mais fundos que não estejam no dicionário, adicionar cores padrão
    cores_adicionais = ['#9B59B6', '#F39C12', '#1ABC9C', '#34495E', '#D35400']
    for i, fundo in enumerate([f for f in fundos if f not in cores_fundos]):
        if i < len(cores_adicionais):
            cores_fundos[fundo] = cores_adicionais[i]
        else:
            cores_fundos[fundo] = f'C{i}'  # Cores padrão do matplotlib
    
    # Configurar outras cores para o gráfico
    cor_investido = '#2C3E50'   # Azul escuro para área de valores investidos, mantido da função original
    cor_nivel1 = '#FF9999'      # Vermelho claro para nível 1
    cor_nivel2 = '#FF3333'      # Vermelho médio para nível 2
    cor_nivel3 = '#990000'      # Vermelho escuro para nível 3
    
    # Extrair datas únicas ordenadas
    datas_unicas = sorted(df_dados['data'].unique())
    
    # Somar níveis de custo para cada data
    df_custos = df_dados.groupby('data').agg({
        'nivel_1': 'sum',
        'nivel_2': 'sum',
        'nivel_3': 'sum'
    }).reindex(datas_unicas)
    
    # Preparar valores investidos consolidados por data
    valores_investidos_por_data = {}
    for data in datas_unicas:
        ano_mes = data.strftime('%Y-%m')
        # Somar valores investidos para todos os fundos nesta data
        soma_investido = 0
        for fundo in fundos:
            chave = f'{ano_mes}_{fundo}'
            if chave in valor_investido_consolidado:
                soma_investido += valor_investido_consolidado[chave]
        valores_investidos_por_data[data] = soma_investido
    
    # Gerar dados para barras empilhadas
    barras_por_fundo = {}
    dados_por_fundo = {}
    
    # Criar um dicionário com os dados de cada fundo em cada data
    for fundo in fundos:
        dados_por_fundo[fundo] = {}
        for data in datas_unicas:
            # Filtrar dados para este fundo e esta data
            filtro = (df_dados['fundo'] == fundo) & (df_dados['data'] == data)
            if filtro.any():
                dados_por_fundo[fundo][data] = df_dados.loc[filtro, 'pl'].values[0]
            else:
                dados_por_fundo[fundo][data] = 0
    
    # Ordem de plotagem: primeiro plotar as barras
    bottom = np.zeros(len(datas_unicas))
    barras_por_fundo = {}
    
    # Ordem de plotagem: primeiro Aconcagua (embaixo), depois Alpamayo (meio), por fim Chimborazo (topo)
    ordem_fundos = ['aconcagua', 'alpamayo', 'chimborazo']
    
    # Plotar na ordem específica
    for fundo in ordem_fundos:
        if fundo in fundos:
            valores = [dados_por_fundo[fundo].get(data, 0) for data in datas_unicas]
            barras = ax1.bar(datas_unicas, valores, bottom=bottom, width=20,
                          color=cores_fundos[fundo], label=f'PL {fundo.capitalize()}',
                          alpha=0.9, zorder=1)
            barras_por_fundo[fundo] = barras
            bottom += valores
    
    # Depois plotar a área preenchida para o valor investido POR CIMA das barras
    valores_investidos_lista = [valores_investidos_por_data.get(data, 0) for data in datas_unicas]
    area_inv = ax1.fill_between(datas_unicas, valores_investidos_lista, color=cor_investido, alpha=0.5,
                             label='Valor Total Investido em Fundos', zorder=2)
    
    # Plotar os três níveis de custo no eixo secundário (com zorder alto para ficar por cima de tudo)
    linha_nivel1 = ax2.plot(datas_unicas, df_custos['nivel_1'].values, color=cor_nivel1, 
                          linewidth=1.5, marker='o', markersize=5, 
                          label='Custos Nível 1 - Custo Itaú', zorder=3)
    
    linha_nivel2 = ax2.plot(datas_unicas, df_custos['nivel_2'].values, color=cor_nivel2, 
                          linewidth=1.5, marker='s', markersize=5, 
                          label='Custos Nível 2 - Custo Itaú e Fundos', zorder=3)
    
    linha_nivel3 = ax2.plot(datas_unicas, df_custos['nivel_3'].values, color=cor_nivel3, 
                          linewidth=1.5, marker='d', markersize=5, 
                          label='Custos Nível 3 - Custo Itaú e Efetivo Fundos', zorder=3)
    
    # Configurar eixo X (datas) com ajuste automático de intervalo
    n_datas = len(datas_unicas)
    if n_datas <= 12:
        intervalo = 1
    elif n_datas <= 24:
        intervalo = 2
    elif n_datas <= 36:
        intervalo = 3
    else:
        intervalo = 6
    
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b/%Y'))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=intervalo))
    plt.xticks(rotation=45, ha='right')
    
    # Formatação do eixo Y1 (PL e Investido)
    ax1.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, p: f'R$ {x/1e6:.0f}M'))
    ax1.set_ylabel('Patrimônio Líquido (R$)', fontsize=12, color='#555555', fontweight='bold')
    ax1.tick_params(axis='y', colors='#555555')
    ax1.set_ylim(bottom=0)  # Começar do zero para melhor visualização da área preenchida
    
    # Formatação do eixo Y2 (Custos)
    ax2.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, p: f'R$ {x/1e3:.0f}K'))
    ax2.set_ylabel('Custo Mensal (R$)', fontsize=12, color='#AA0000', fontweight='bold')
    ax2.tick_params(axis='y', colors='#AA0000')
    
    # Título e grid
    plt.title(f'{titulo}', fontsize=16, pad=20, fontweight='bold')
    ax1.grid(True, linestyle='--', alpha=0.3)
    
    # Combinar legendas de ambos os eixos na ordem correta das barras
    handles = []
    labels = []
    
    # Adicionar legendas na ordem certa (de cima para baixo)
    for fundo in ['chimborazo', 'alpamayo', 'aconcagua']:
        if fundo in barras_por_fundo:
            handles.append(barras_por_fundo[fundo][0])
            labels.append(f'PL {fundo.capitalize()}')
    
    handles.append(area_inv)
    labels.append('Valor Total Investido em Fundos')
    handles.extend([linha_nivel1[0], linha_nivel2[0], linha_nivel3[0]])
    labels.extend(['Custos Nível 1 - Itaú', 'Custos Nível 2 - Itaú e Adm. Fundos', 'Custos Nível 3 - Itaú e Adm. Efetiva Fundos'])
    
    ax1.legend(handles, labels, loc='upper left', frameon=True, framealpha=0.9)
    
    plt.tight_layout()
    
    # Salvar se caminho fornecido
    if caminho_saida:
        diretorio = os.path.dirname(caminho_saida)
        if diretorio and not os.path.exists(diretorio):
            os.makedirs(diretorio, exist_ok=True)
        plt.savefig(caminho_saida, dpi=300, bbox_inches='tight')
        print(f"Gráfico salvo em: {caminho_saida}")
    
    return plt.gcf()


def plotar_pl_custos_niveis_multi_fundos_alterado(serie_custos_consolidado, valor_investido_consolidado, relacoes_entre_fundos=None, titulo="Fundos Consolidados", caminho_saida=None):
    """
    Gera um gráfico com barras empilhadas para o PL de diferentes fundos, área preenchida para o valor investido,
    e três linhas em tons de vermelho para os diferentes níveis de custo somados.
    
    Args:
        serie_custos_consolidado (DataFrame): DataFrame com dados dos fundos
        valor_investido_consolidado (dict): Valores investidos por fundo e período no formato 'YYYY-MM_fundo': valor
        relacoes_entre_fundos (dict): Dicionário que indica quanto de um fundo está investido em outro
            Ex: {'alpamayo': {'investido_por': {'chimborazo': {'2024-10': 98000000, ...}}}}
        titulo (str): Título do gráfico
        caminho_saida (str): Caminho para salvar o gráfico (opcional)
    
    Returns:
        matplotlib.figure.Figure: Objeto figura do matplotlib
    """
    df_dados = serie_custos_consolidado.copy()
    
    # Verificar se temos dados
    if df_dados is None or df_dados.empty:
        print("Sem dados para plotar.")
        return None
    
    # Converter para datetime se não for
    if not pd.api.types.is_datetime64_any_dtype(df_dados['data']):
        df_dados['data'] = pd.to_datetime(df_dados['data'])
    
    # Adicionar coluna de ano_mes para facilitar o agrupamento
    df_dados['ano_mes'] = df_dados['data'].dt.strftime('%Y-%m')
    
    # Identificar fundos únicos
    fundos = df_dados['fundo'].unique()
    print(f"Fundos encontrados: {fundos}")
    
    # Se nenhuma relação entre fundos foi fornecida, inicializar um dicionário vazio
    if relacoes_entre_fundos is None:
        relacoes_entre_fundos = {}
    
    # Criar figura com tamanho adequado
    plt.figure(figsize=(16, 10))
    
    # Criar dois eixos Y (um para o PL/investido e outro para o custo)
    ax1 = plt.subplot(111)
    ax2 = ax1.twinx()
    
    # Configurar cores para os fundos
    cores_fundos = {
        'chimborazo': '#CD853F',   # Marrom mais claro (Peru/Tan)
        'aconcagua': '#A0A0A0',    # Cinza claro (da função original)
        'alpamayo': '#1A5276'      # Azul escuro
    }
    
    # Caso haja mais fundos que não estejam no dicionário, adicionar cores padrão
    cores_adicionais = ['#9B59B6', '#F39C12', '#1ABC9C', '#34495E', '#D35400']
    for i, fundo in enumerate([f for f in fundos if f not in cores_fundos]):
        if i < len(cores_adicionais):
            cores_fundos[fundo] = cores_adicionais[i]
        else:
            cores_fundos[fundo] = f'C{i}'  # Cores padrão do matplotlib
    
    # Configurar outras cores para o gráfico
    cor_investido = '#2C3E50'   # Azul escuro para área de valores investidos
    cor_nivel1 = '#FF9999'      # Vermelho claro para nível 1
    cor_nivel2 = '#FF3333'      # Vermelho médio para nível 2
    cor_nivel3 = '#990000'      # Vermelho escuro para nível 3
    
    # Extrair datas únicas ordenadas
    datas_unicas = sorted(df_dados['data'].unique())
    
    # Criar um dicionário com os dados de cada fundo em cada data
    dados_por_fundo = {}
    for fundo in fundos:
        dados_por_fundo[fundo] = {}
        for data in datas_unicas:
            # Filtrar dados para este fundo e esta data
            filtro = (df_dados['fundo'] == fundo) & (df_dados['data'] == data)
            if filtro.any():
                dados_por_fundo[fundo][data] = df_dados.loc[filtro, 'pl'].values[0]
            else:
                dados_por_fundo[fundo][data] = 0
    
    # Para o Alpamayo, ajustar o valor investido pelo Chimborazo para nunca exceder 99.5% do PL
    for data in datas_unicas:
        ano_mes = data.strftime('%Y-%m')
        if 'alpamayo' in fundos and 'alpamayo' in relacoes_entre_fundos and 'investido_por' in relacoes_entre_fundos['alpamayo']:
            if 'chimborazo' in relacoes_entre_fundos['alpamayo']['investido_por']:
                pl_alpamayo = dados_por_fundo['alpamayo'].get(data, 0)
                if pl_alpamayo > 0:
                    valores_chim = relacoes_entre_fundos['alpamayo']['investido_por']['chimborazo']
                    if isinstance(valores_chim, dict) and ano_mes in valores_chim:
                        # Limitar o valor investido pelo Chimborazo a 99.5% do PL do Alpamayo
                        max_investimento = pl_alpamayo * 0.995
                        if valores_chim[ano_mes] > max_investimento:
                            # Atualizar o valor para não exceder o limite
                            relacoes_entre_fundos['alpamayo']['investido_por']['chimborazo'][ano_mes] = max_investimento
                            print(f"Ajustado investimento do Chimborazo no Alpamayo para {ano_mes}: {max_investimento:.2f} (era {valores_chim[ano_mes]:.2f})")
    
    # Debug das proporções para Alpamayo após ajustes
    for fundo in fundos:
        if fundo == 'alpamayo':
            filtro = df_dados['fundo'] == fundo
            df_alpamayo = df_dados[filtro].sort_values('data')
            meses_recentes = ['2024-10', '2024-11', '2024-12', '2025-01', '2025-02']
            for mes in meses_recentes:
                filtro_mes = df_alpamayo['ano_mes'] == mes
                if filtro_mes.any():
                    pl_total = df_alpamayo.loc[filtro_mes, 'pl'].values[0]
                    valor_chimborazo = relacoes_entre_fundos['alpamayo']['investido_por']['chimborazo'].get(mes, 0)
                    pl_proprio = pl_total - valor_chimborazo
                    print(f"Alpamayo {mes}: PL Total={pl_total:.2f}, Investido por Chimborazo={valor_chimborazo:.2f}, Próprio={pl_proprio:.2f} ({pl_proprio/pl_total*100:.2f}%)")
    
    # Ajustar valores de PL para mostrar apenas a parte própria do Alpamayo
    for data in datas_unicas:
        ano_mes = data.strftime('%Y-%m')
        for fundo in fundos:
            if fundo == 'alpamayo' and fundo in relacoes_entre_fundos and 'investido_por' in relacoes_entre_fundos[fundo]:
                # Para o Alpamayo, mostrar apenas a parte própria
                filtro = (df_dados['fundo'] == fundo) & (df_dados['data'] == data)
                if filtro.any():
                    pl_total = df_dados.loc[filtro, 'pl'].values[0]
                    
                    # Verificar se temos um valor específico do Chimborazo para este período
                    valor_investido_por_chimborazo = 0
                    
                    # Obter o valor investido pelo Chimborazo
                    valores_chim = relacoes_entre_fundos['alpamayo']['investido_por']['chimborazo']
                    if isinstance(valores_chim, dict):
                        if ano_mes in valores_chim:
                            valor_investido_por_chimborazo = valores_chim[ano_mes]
                        elif ano_mes < min(valores_chim.keys(), default="9999-99"):
                            # Para períodos históricos, assumir uma porcentagem maior investida pelo Chimborazo
                            # Começar com 100% nos períodos mais antigos e ir diminuindo
                            primeiro_periodo = min(valores_chim.keys(), default="9999-99")
                            valor_investido_por_chimborazo = min(pl_total * 0.9995, pl_total)  # 99.95%
                    
                    # Calcular a parte própria do Alpamayo
                    parte_propria = pl_total - valor_investido_por_chimborazo
                    
                    # Garantir que a parte própria seja pelo menos 0.5% do PL total
                    parte_propria = max(parte_propria, pl_total * 0.005)
                    
                    # Atualizar o valor no dicionário
                    dados_por_fundo[fundo][data] = parte_propria
    
    # Somar níveis de custo para cada data
    df_custos = df_dados.groupby('data').agg({
        'nivel_1': 'sum',
        'nivel_2': 'sum',
        'nivel_3': 'sum'
    }).reindex(datas_unicas)
    
    # Calcular valores investidos consolidados
    valores_investidos_por_data = {}
    for data in datas_unicas:
        ano_mes = data.strftime('%Y-%m')
        soma_investido = 0
        
        # Primeiro obter o valor investido total por fundo
        for fundo in fundos:
            chave = f'{ano_mes}_{fundo}'
            
            # Se for Alpamayo, adicionar apenas a parte própria
            if fundo == 'alpamayo':
                # Usar o valor que já calculamos para a parte própria
                valor_proprio = dados_por_fundo[fundo].get(data, 0)
                soma_investido += valor_proprio
            else:
                # Para outros fundos, adicionar o valor total
                soma_investido += valor_investido_consolidado.get(chave, 0)
        
        valores_investidos_por_data[data] = soma_investido
    
    # Ordem de plotagem
    ordem_fundos = ['aconcagua', 'alpamayo', 'chimborazo']
    ordem_plotagem = [f for f in ordem_fundos if f in fundos]
    
    # Verificar os valores totais para períodos-chave
    for data in datas_unicas:
        if data.strftime('%Y-%m') == '2025-02':
            total_pl = sum(dados_por_fundo[fundo].get(data, 0) for fundo in fundos)
            print(f"\nTotal PL para 2025-02: {total_pl:.2f}")
            for fundo in fundos:
                print(f"  {fundo}: {dados_por_fundo[fundo].get(data, 0):.2f}")
    
    # Plotar barras empilhadas
    bottom = np.zeros(len(datas_unicas))
    barras_por_fundo = {}
    
    for fundo in ordem_plotagem:
        valores = [dados_por_fundo[fundo].get(data, 0) for data in datas_unicas]
        valores = [max(0, val) for val in valores]  # Eliminar valores negativos
        
        barras = ax1.bar(datas_unicas, valores, bottom=bottom, width=20,
                       color=cores_fundos[fundo], label=f'PL {fundo.capitalize()}',
                       alpha=0.9, zorder=1)
        barras_por_fundo[fundo] = barras
        bottom += valores
    
    # Plotar área preenchida para o valor investido
    valores_investidos_lista = [valores_investidos_por_data.get(data, 0) for data in datas_unicas]
    area_inv = ax1.fill_between(datas_unicas, valores_investidos_lista, color=cor_investido, alpha=0.5,
                             label='Valor Total Investido em Fundos', zorder=2)
    
    # Plotar os três níveis de custo
    linha_nivel1 = ax2.plot(datas_unicas, df_custos['nivel_1'].values, color=cor_nivel1, 
                          linewidth=1.5, marker='o', markersize=5, 
                          label='Custos Nível 1 - Custo Itaú', zorder=3)
    
    linha_nivel2 = ax2.plot(datas_unicas, df_custos['nivel_2'].values, color=cor_nivel2, 
                          linewidth=1.5, marker='s', markersize=5, 
                          label='Custos Nível 2 - Custo Itaú e Fundos', zorder=3)
    
    linha_nivel3 = ax2.plot(datas_unicas, df_custos['nivel_3'].values, color=cor_nivel3, 
                          linewidth=1.5, marker='d', markersize=5, 
                          label='Custos Nível 3 - Custo Itaú e Efetivo Fundos', zorder=3)
    
    # Configurar eixo X (datas)
    n_datas = len(datas_unicas)
    intervalo = max(1, n_datas // 12)
    
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b/%Y'))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=intervalo))
    plt.xticks(rotation=45, ha='right')
    
    # Formatação dos eixos Y
    ax1.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, p: f'R$ {x/1e6:.0f}M'))
    ax1.set_ylabel('Patrimônio Líquido (R$)', fontsize=12, color='#555555', fontweight='bold')
    ax1.tick_params(axis='y', colors='#555555')
    ax1.set_ylim(bottom=0)
    
    ax2.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, p: f'R$ {x/1e3:.0f}K'))
    ax2.set_ylabel('Custo Mensal (R$)', fontsize=12, color='#AA0000', fontweight='bold')
    ax2.tick_params(axis='y', colors='#AA0000')
    
    # Título e grid
    plt.title(f'{titulo}', fontsize=16, pad=20, fontweight='bold')
    ax1.grid(True, linestyle='--', alpha=0.3)
    
    # Legendas
    handles = []
    labels = []
    
    for fundo in ['chimborazo', 'alpamayo', 'aconcagua']:
        if fundo in barras_por_fundo:
            handles.append(barras_por_fundo[fundo][0])
            labels.append(f'PL {fundo.capitalize()}')
    
    handles.append(area_inv)
    labels.append('Valor Total Investido em Fundos')
    handles.extend([linha_nivel1[0], linha_nivel2[0], linha_nivel3[0]])
    labels.extend(['Custos Nível 1 - Itaú', 'Custos Nível 2 - Itaú e Adm. Fundos', 'Custos Nível 3 - Itaú e Adm. Efetiva Fundos'])
    
    ax1.legend(handles, labels, loc='upper left', frameon=True, framealpha=0.9)
    
    plt.tight_layout()
    plt.show()
    
    # Salvar se caminho fornecido
    if caminho_saida:
        diretorio = os.path.dirname(caminho_saida)
        if diretorio and not os.path.exists(diretorio):
            os.makedirs(diretorio, exist_ok=True)
        plt.savefig(caminho_saida, dpi=300, bbox_inches='tight')
        print(f"Gráfico salvo em: {caminho_saida}")
    
    return plt.gcf()


def processar_carteira_fundos(carteira_fundos):
    """
    Process and clean the fund portfolio data with enhanced error handling and validation.
    
    This function performs comprehensive data cleaning and validation on fund portfolio data,
    including handling duplicates, date conversions, and data type validation.
    
    Args:
        carteira_fundos (pd.DataFrame): DataFrame containing fund portfolio data.
        
    Returns:
        pd.DataFrame: Processed and cleaned fund portfolio data.
        
    Raises:
        ValueError: If input data is empty or invalid
        TypeError: If input data is not a DataFrame
    """
    try:
        # Input validation
        if carteira_fundos is None:
            raise ValueError("Input portfolio data cannot be None")
            
        if not isinstance(carteira_fundos, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame")
            
        if carteira_fundos.empty:
            raise ValueError("Input portfolio data is empty")
            
        # Create a copy to avoid modifying the original
        carteira_processada = carteira_fundos.copy()
        
        # Remove duplicates with logging
        n_duplicates = carteira_processada.duplicated().sum()
        if n_duplicates > 0:
            print(f"Removing {n_duplicates} duplicate rows")
            carteira_processada = carteira_processada.drop_duplicates()
            
        # Convert date columns
        date_columns = [col for col in carteira_processada.columns if 'data' in col.lower()]
        for col in date_columns:
            try:
                carteira_processada[col] = pd.to_datetime(carteira_processada[col])
            except Exception as e:
                print(f"Warning: Could not convert column {col} to datetime: {str(e)}")
                
        # Sort by date if available
        if 'data' in carteira_processada.columns:
            carteira_processada = carteira_processada.sort_values('data')
            
        # Validate numeric columns
        numeric_columns = ['pl', 'valor_investido', 'taxa_administracao']
        for col in numeric_columns:
            if col in carteira_processada.columns:
                try:
                    carteira_processada[col] = pd.to_numeric(carteira_processada[col], errors='coerce')
                    n_invalid = carteira_processada[col].isna().sum()
                    if n_invalid > 0:
                        print(f"Warning: Found {n_invalid} invalid values in column {col}")
                except Exception as e:
                    print(f"Warning: Could not convert column {col} to numeric: {str(e)}")
                    
        return carteira_processada
        
    except Exception as e:
        print(f"Error processing portfolio: {str(e)}")
        raise

def carregar_dados_fundo(cnpj_fundo, base_dir, data_inicio=None, data_fim=None):
    """
    Carrega os dados de um fundo específico.
    
    Args:
        cnpj_fundo (str): CNPJ do fundo
        base_dir (str): Diretório base dos dados
        data_inicio (str, optional): Data inicial no formato 'YYYY-MM'
        data_fim (str, optional): Data final no formato 'YYYY-MM'
        
    Returns:
        pd.DataFrame: DataFrame com os dados do fundo ou None em caso de erro
    """
    try:
        arquivos = buscar_arquivos_fundo(cnpj_fundo, base_dir, data_inicio, data_fim)
        if not arquivos:
            print(f"Nenhum arquivo encontrado para o fundo {cnpj_fundo}")
            return None
            
        dados = []
        for arquivo in arquivos:
            df = pd.read_csv(arquivo)
            dados.append(df)
            
        return pd.concat(dados, ignore_index=True)
    except Exception as e:
        print(f"Erro ao carregar dados do fundo {cnpj_fundo}: {str(e)}")
        return None

def buscar_arquivos_fundo(cnpj_fundo, base_dir, data_inicio=None, data_fim=None):
    """
    Busca os arquivos de um fundo dentro de um período.
    
    Args:
        cnpj_fundo (str): CNPJ do fundo
        base_dir (str): Diretório base
        data_inicio (str, optional): Data inicial no formato 'YYYY-MM'
        data_fim (str, optional): Data final no formato 'YYYY-MM'
        
    Returns:
        list: Lista de caminhos dos arquivos encontrados
    """
    try:
        padrao = f"*{cnpj_fundo}*.csv"
        arquivos = glob.glob(os.path.join(base_dir, padrao))
        
        if data_inicio and data_fim:
            arquivos = filtrar_arquivos_por_data(arquivos, data_inicio, data_fim)
            
        return sorted(arquivos)
    except Exception as e:
        print(f"Erro ao buscar arquivos do fundo {cnpj_fundo}: {str(e)}")
        return []

def filtrar_arquivos_por_data(arquivos, data_inicio, data_fim):
    """
    Filtra arquivos por período de datas.
    
    Args:
        arquivos (list): Lista de caminhos de arquivos
        data_inicio (str): Data inicial no formato 'YYYY-MM'
        data_fim (str): Data final no formato 'YYYY-MM'
        
    Returns:
        list: Lista de arquivos dentro do período
    """
    try:
        data_inicio = pd.to_datetime(data_inicio)
        data_fim = pd.to_datetime(data_fim)
        
        arquivos_filtrados = []
        for arquivo in arquivos:
            data_arquivo = extrair_data_arquivo(arquivo)
            if data_inicio <= data_arquivo <= data_fim:
                arquivos_filtrados.append(arquivo)
                
        return arquivos_filtrados
    except Exception as e:
        print(f"Erro ao filtrar arquivos por data: {str(e)}")
        return []

def extrair_data_arquivo(caminho_arquivo):
    """
    Extrai a data do nome do arquivo.
    
    Args:
        caminho_arquivo (str): Caminho do arquivo
        
    Returns:
        pd.Timestamp: Data extraída do nome do arquivo
    """
    try:
        nome_arquivo = os.path.basename(caminho_arquivo)
        # Assumindo que a data está no formato YYYYMM no nome do arquivo
        data_str = re.search(r'\d{6}', nome_arquivo).group()
        return pd.to_datetime(data_str, format='%Y%m')
    except Exception as e:
        print(f"Erro ao extrair data do arquivo {caminho_arquivo}: {str(e)}")
        return None

def processar_carteira_fundos(carteira_fundos):
    """
    Processa e limpa os dados da carteira de fundos.
    
    Args:
        carteira_fundos (pd.DataFrame): DataFrame com dados da carteira
        
    Returns:
        pd.DataFrame: DataFrame processado ou None em caso de erro
    """
    try:
        carteira_fundos = remover_duplicatas(carteira_fundos)
        carteira_fundos = converter_datas(carteira_fundos)
        carteira_fundos = ordenar_por_data(carteira_fundos)
        return carteira_fundos
    except Exception as e:
        print(f"Erro ao processar carteira de fundos: {str(e)}")
        return None

def remover_duplicatas(df):
    """
    Remove linhas duplicadas do DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame a ser processado
        
    Returns:
        pd.DataFrame: DataFrame sem duplicatas
    """
    return df.drop_duplicates()

def converter_datas(df):
    """
    Converte colunas de data para o tipo datetime.
    
    Args:
        df (pd.DataFrame): DataFrame com colunas de data
        
    Returns:
        pd.DataFrame: DataFrame com datas convertidas
    """
    colunas_data = [col for col in df.columns if 'data' in col.lower()]
    for col in colunas_data:
        df[col] = pd.to_datetime(df[col])
    return df

def ordenar_por_data(df):
    """
    Ordena o DataFrame por data.
    
    Args:
        df (pd.DataFrame): DataFrame a ser ordenado
        
    Returns:
        pd.DataFrame: DataFrame ordenado por data
    """
    if 'data' in df.columns:
        return df.sort_values('data')
    return df

def analisar_evolucao_custos(carteiras: pd.DataFrame, dir_saida: str) -> None:
    """
    Analisa a evolução dos custos ao longo do tempo.
    
    Args:
        carteiras (pd.DataFrame): DataFrame com dados das carteiras
        dir_saida (str): Diretório para salvar os resultados
    """
    try:
        # Criar diretório de saída se necessário
        os.makedirs(dir_saida, exist_ok=True)
        
        # Agrupar por data e calcular estatísticas
        evolucao = carteiras.groupby('data').agg({
            'custo_total': ['sum', 'mean', 'std'],
            'taxa_administracao': ['mean', 'std'],
            'pl': ['sum', 'mean', 'std']
        }).reset_index()
        
        # Calcular percentuais
        evolucao['custo_percentual'] = (evolucao[('custo_total', 'sum')] / evolucao[('pl', 'sum')]) * 100
        
        # Salvar resultados
        evolucao.to_csv(os.path.join(dir_saida, 'evolucao_custos.csv'), index=False)
        
        # Gerar gráficos
        plotar_evolucao_custos(evolucao, dir_saida)
        
    except Exception as e:
        print(f"Erro ao analisar evolução dos custos: {str(e)}")

def plotar_evolucao_custos(evolucao: pd.DataFrame, dir_saida: str) -> None:
    """
    Gera gráficos da evolução dos custos.
    
    Args:
        evolucao (pd.DataFrame): DataFrame com dados de evolução
        dir_saida (str): Diretório para salvar os gráficos
    """
    try:
        # Criar figura
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Plotar custos totais
        ax1.plot(evolucao['data'], evolucao[('custo_total', 'sum')], label='Custo Total', color='blue')
        ax1.set_title('Evolução dos Custos Totais')
        ax1.set_xlabel('Data')
        ax1.set_ylabel('Valor (R$)')
        ax1.legend()
        ax1.grid(True)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x:,.2f}'))
        
        # Plotar percentual de custos
        ax2.plot(evolucao['data'], evolucao['custo_percentual'], label='% Custo/PL', color='red')
        ax2.set_title('Evolução do Percentual de Custos')
        ax2.set_xlabel('Data')
        ax2.set_ylabel('Percentual (%)')
        ax2.legend()
        ax2.grid(True)
        
        # Ajustar layout
        plt.tight_layout()
        
        # Salvar gráfico
        plt.savefig(os.path.join(dir_saida, 'evolucao_custos.png'))
        plt.close()
        
    except Exception as e:
        print(f"Erro ao gerar gráficos de evolução dos custos: {str(e)}")

def calcular_custos_taxas(carteiras: pd.DataFrame, dir_saida: str) -> None:
    """
    Calcula custos e taxas das carteiras.
    
    Args:
        carteiras (pd.DataFrame): DataFrame com dados das carteiras
        dir_saida (str): Diretório para salvar os resultados
    """
    try:
        # Criar diretório de saída se necessário
        os.makedirs(dir_saida, exist_ok=True)
        
        # Calcular custos totais
        carteiras['custo_total'] = carteiras['taxa_administracao'] * carteiras['pl']
        
        # Agrupar por CNPJ e calcular estatísticas
        custos_por_fundo = carteiras.groupby('cnpj').agg({
            'custo_total': ['sum', 'mean', 'std'],
            'taxa_administracao': ['mean', 'std'],
            'pl': ['sum', 'mean', 'std']
        }).reset_index()
        
        # Calcular percentuais
        custos_por_fundo['custo_percentual'] = (custos_por_fundo[('custo_total', 'sum')] / custos_por_fundo[('pl', 'sum')]) * 100
        
        # Salvar resultados
        custos_por_fundo.to_csv(os.path.join(dir_saida, 'custos_por_fundo.csv'), index=False)
        
        # Gerar gráficos
        plotar_custos_por_fundo(custos_por_fundo, dir_saida)
        
    except Exception as e:
        print(f"Erro ao calcular custos e taxas: {str(e)}")

def plotar_custos_por_fundo(custos_por_fundo: pd.DataFrame, dir_saida: str) -> None:
    """
    Gera gráficos dos custos por fundo.
    
    Args:
        custos_por_fundo (pd.DataFrame): DataFrame com dados de custos por fundo
        dir_saida (str): Diretório para salvar os gráficos
    """
    try:
        # Criar figura
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Plotar custos totais
        ax1.bar(custos_por_fundo['cnpj'], custos_por_fundo[('custo_total', 'sum')], color='blue')
        ax1.set_title('Custos Totais por Fundo')
        ax1.set_xlabel('CNPJ')
        ax1.set_ylabel('Valor (R$)')
        ax1.grid(True)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x:,.2f}'))
        plt.xticks(rotation=45)
        
        # Plotar percentual de custos
        ax2.bar(custos_por_fundo['cnpj'], custos_por_fundo['custo_percentual'], color='red')
        ax2.set_title('Percentual de Custos por Fundo')
        ax2.set_xlabel('CNPJ')
        ax2.set_ylabel('Percentual (%)')
        ax2.grid(True)
        plt.xticks(rotation=45)
        
        # Ajustar layout
        plt.tight_layout()
        
        # Salvar gráfico
        plt.savefig(os.path.join(dir_saida, 'custos_por_fundo.png'))
        plt.close()
        
    except Exception as e:
        print(f"Erro ao gerar gráficos de custos por fundo: {str(e)}")
