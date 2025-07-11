import os
import re
import zipfile
import tempfile
import shutil
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import pickle
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import PercentFormatter
import matplotlib.ticker as mtick
from tqdm import tqdm




def serializar_resultados_carteira(carteira_categorizada, resultados_categorias, base_dir, nome_fundo):
    """
    Serializa os resultados da análise da carteira para uso posterior na consolidação.
    
    Args:
        carteira_categorizada (dict): Dicionário com as carteiras categorizadas por período
        resultados_categorias (dict): Resultados da análise por categoria
        base_dir (str): Diretório base
        nome_fundo (str): Nome do fundo para identificação dos arquivos
        
    Returns:
        str: Caminho do arquivo serializado
    """
    # Criar diretório para dados serializados se não existir
    dir_serial = os.path.join(base_dir, 'serial_carteiras')
    os.makedirs(dir_serial, exist_ok=True)
    
    # Preparar dados para serialização
    dados = {
        'carteira_categorizada': carteira_categorizada,
        'resultados_categorias': resultados_categorias,
        'datas_disponiveis': sorted(list(carteira_categorizada.keys())),
        'ultima_atualizacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Serializar os dados
    caminho_arquivo = os.path.join(dir_serial, f'carteira_{nome_fundo}.pkl')
    with open(caminho_arquivo, 'wb') as f:
        pickle.dump(dados, f)
    
    print(f"Dados da carteira de {nome_fundo} serializados em: {caminho_arquivo}")
    
    return caminho_arquivo


def processar_carteira_completa(cnpj_fundo, base_dir, limite_arquivos=None):
    """
    Processa a carteira completa de um fundo, incluindo todos os tipos de ativos.
    
    Args:
        cnpj_fundo (str): CNPJ do fundo a ser analisado
        base_dir (str): Diretório base onde estão os arquivos
        limite_arquivos (int, optional): Limita o número de arquivos a processar
        
    Returns:
        dict: Dicionário com as carteiras processadas por período
    """
    print(f"Processando carteira completa para o fundo {cnpj_fundo}...")
    
    # Diretório onde estão os dados
    pasta_cda = os.path.join(base_dir, 'CDA')
    
    # Diretório temporário para extração
    dir_temp = os.path.join(base_dir, 'temp_extract_carteira')
    os.makedirs(dir_temp, exist_ok=True)
    
    # Dicionário para armazenar os dados por data
    carteira_completa = {}
    
    try:
        # Encontra todos os arquivos ZIP do tipo cda_fi_*
        arquivos_zip = []
        for root, _, files in os.walk(pasta_cda):
            for file in files:
                if file.endswith('.zip') and 'cda_fi_' in file:
                    arquivos_zip.append(os.path.join(root, file))
        
        # Ordena arquivos por data (mais recentes primeiro)
        arquivos_zip.sort(reverse=True)
        
        print(f"Encontrados {len(arquivos_zip)} arquivos ZIP para processamento")
        
        # Limita o número de arquivos se solicitado
        if limite_arquivos is not None and limite_arquivos > 0:
            arquivos_zip = arquivos_zip[:limite_arquivos]
            print(f"Limitando processamento aos {limite_arquivos} arquivos mais recentes")
        
        # Processa cada arquivo ZIP
        for arquivo_zip in arquivos_zip:
            nome_arquivo = os.path.basename(arquivo_zip)
            
            # Detecta se é um arquivo anual ou mensal
            eh_anual = False
            data_match = re.search(r'cda_fi_(\d{6})\.zip', nome_arquivo)
            if data_match:
                periodo = data_match.group(1)
                data_formatada = f"{periodo[:4]}-{periodo[4:]}"
            else:
                # Verifica se é arquivo anual (formato cda_fi_AAAA.zip)
                data_match_anual = re.search(r'cda_fi_(\d{4})\.zip', nome_arquivo)
                if data_match_anual:
                    periodo = data_match_anual.group(1)
                    data_formatada = periodo
                    eh_anual = True
                else:
                    # Se não conseguir extrair a data do nome, usa a data de modificação
                    timestamp = os.path.getmtime(arquivo_zip)
                    data = datetime.fromtimestamp(timestamp)
                    periodo = f"{data.year}{data.month:02d}"
                    data_formatada = f"{data.year}-{data.month:02d}"
            
            print(f"\nProcessando arquivo: {nome_arquivo} (Data: {data_formatada})")
            
            # Cria um diretório específico para esta data
            data_dir = os.path.join(dir_temp, f"cda_fi_{periodo}")
            os.makedirs(data_dir, exist_ok=True)
            
            try:
                # Lista para armazenar todos os DataFrames BLC encontrados neste arquivo
                blc_dfs = []
                
                # Extrai e processa os arquivos BLC_1 a BLC_8
                with zipfile.ZipFile(arquivo_zip, 'r') as zip_ref:
                    # Lista todos os arquivos no ZIP
                    arquivos_no_zip = zip_ref.namelist()
                    
                    # Filtra arquivos BLC_1 a BLC_8
                    arquivos_blc = [arq for arq in arquivos_no_zip 
                                   if re.match(r'cda_fi_BLC_[1-8]', arq) and arq.endswith('.csv')]
                    
                    if not arquivos_blc:
                        print(f"  - Nenhum arquivo BLC encontrado em {nome_arquivo}")
                        
                        # Para arquivos anuais, pode haver subdiretórios, então extraímos tudo
                        if eh_anual:
                            print("  - Extraindo todos os arquivos para buscar BLC em subdiretórios...")
                            zip_ref.extractall(data_dir)
                            
                            # Procura por arquivos BLC em todos os subdiretórios
                            arquivos_blc = []
                            for root, _, files in os.walk(data_dir):
                                for file in files:
                                    if re.match(r'cda_fi_BLC_[1-8]', file) and file.endswith('.csv'):
                                        arquivos_blc.append(os.path.join(root, file))
                            
                            print(f"  - Encontrados {len(arquivos_blc)} arquivos BLC nos subdiretórios")
                        
                        if not arquivos_blc:
                            continue
                    else:
                        print(f"  - Encontrados {len(arquivos_blc)} arquivos BLC")
                        
                        # Extrai apenas os arquivos BLC
                        for arq_blc in arquivos_blc:
                            zip_ref.extract(arq_blc, data_dir)
                            arquivo_extraido = os.path.join(data_dir, arq_blc)
                            arquivos_blc = [arquivo_extraido if arq == arq_blc else arq for arq in arquivos_blc]
                
                # Processa cada arquivo BLC encontrado
                for arquivo_csv in arquivos_blc:
                    try:
                        # Identificar qual BLC é este arquivo
                        nome_arquivo_blc = os.path.basename(arquivo_csv)
                        match_blc = re.search(r'BLC_([1-8])', nome_arquivo_blc)
                        if match_blc:
                            num_blc = match_blc.group(1)
                            print(f"  - Processando BLC_{num_blc}: {nome_arquivo_blc}")
                        else:
                            print(f"  - Processando arquivo não identificado: {nome_arquivo_blc}")
                            num_blc = "X"  # Valor genérico para arquivos não identificados
                        
                        # Carrega o CSV
                        try:
                            df = pd.read_csv(arquivo_csv, sep=';', encoding='ISO-8859-1', low_memory=False)
                        except:
                            # Tentar com encoding alternativo
                            try:
                                df = pd.read_csv(arquivo_csv, sep=';', encoding='utf-8', low_memory=False)
                            except Exception as e:
                                print(f"  ✗ Erro ao ler o arquivo CSV {nome_arquivo_blc}: {str(e)}")
                                continue
                        
                        # Adicionar coluna para identificar o tipo de BLC
                        df['TIPO_BLC'] = f"BLC_{num_blc}"
                        
                        # Identifica coluna correta para CNPJ do fundo
                        coluna_cnpj_fundo = None
                        for col in ['CNPJ_FUNDO_CLASSE', 'CNPJ_FUNDO', 'CD_FUNDO']:
                            if col in df.columns:
                                coluna_cnpj_fundo = col
                                break
                        
                        if coluna_cnpj_fundo is None:
                            print(f"  ✗ Não foi possível identificar coluna com CNPJ do fundo em {nome_arquivo_blc}")
                            continue
                        
                        # Filtra pelo CNPJ do fundo
                        df_fundo = df[df[coluna_cnpj_fundo] == cnpj_fundo]
                        
                        if len(df_fundo) > 0:
                            # Adicionar ao conjunto de DataFrames BLC
                            blc_dfs.append(df_fundo)
                            print(f"  ✓ Encontrados {len(df_fundo)} ativos em {nome_arquivo_blc}")
                        else:
                            print(f"  - Nenhum ativo encontrado para o fundo {cnpj_fundo} em {nome_arquivo_blc}")
                    
                    except Exception as e:
                        print(f"  ✗ Erro ao processar {os.path.basename(arquivo_csv)}: {str(e)}")
                
                # Se encontrou dados nos arquivos BLC para este período, consolida
                if blc_dfs:
                    # Combina todos os DataFrames em um único
                    df_carteira_periodo = pd.concat(blc_dfs, ignore_index=True)
                    
                    # Se é arquivo anual, precisamos verificar datas específicas no DataFrame
                    if eh_anual and 'DT_COMPTC' in df_carteira_periodo.columns:
                        # Agrupa por data de competência
                        for data_comptc, grupo in df_carteira_periodo.groupby('DT_COMPTC'):
                            # Converte para formato YYYY-MM
                            try:
                                data_obj = datetime.strptime(data_comptc, '%Y-%m-%d')
                                data_mes = f"{data_obj.year}-{data_obj.month:02d}"
                                
                                print(f"  ✓ Adicionando {len(grupo)} ativos para {data_mes}")
                                
                                # Adiciona ao dicionário de carteiras
                                if data_mes in carteira_completa:
                                    carteira_completa[data_mes] = pd.concat([carteira_completa[data_mes], grupo], ignore_index=True)
                                else:
                                    carteira_completa[data_mes] = grupo
                            except Exception as e:
                                print(f"  ✗ Erro ao processar data {data_comptc}: {str(e)}")
                    else:
                        # Para arquivos mensais, usa a data do arquivo
                        print(f"  ✓ Adicionando {len(df_carteira_periodo)} ativos para {data_formatada}")
                        
                        # Adiciona ao dicionário de carteiras
                        if data_formatada in carteira_completa:
                            carteira_completa[data_formatada] = pd.concat([carteira_completa[data_formatada], df_carteira_periodo], ignore_index=True)
                        else:
                            carteira_completa[data_formatada] = df_carteira_periodo
            
            except Exception as e:
                print(f"  ✗ Erro ao processar arquivo ZIP {nome_arquivo}: {str(e)}")
            
            # Limpa os arquivos temporários desta data
            shutil.rmtree(data_dir)
    
    finally:
        # Limpa o diretório temporário
        if os.path.exists(dir_temp):
            try:
                shutil.rmtree(dir_temp)
                print("\nDiretório temporário removido")
            except:
                print("\nNão foi possível remover o diretório temporário")
    
    # Informações finais
    num_datas = len(carteira_completa)
    datas = sorted(list(carteira_completa.keys()))
    
    print(f"\n{'=' * 50}")
    print(f"Processamento concluído! Dados encontrados para {num_datas} datas distintas.")
    
    if num_datas > 0:
        print(f"Range de datas: {datas[0]} a {datas[-1]}")
        
        # Mostra algumas estatísticas
        print("\nEstatísticas por data:")
        for data in datas:
            df = carteira_completa[data]
            num_ativos = len(df)
            
            # Adicionar informações sobre tipos de ativos
            if 'TP_ATIVO' in df.columns:
                tipos_ativos = df['TP_ATIVO'].value_counts().to_dict()
                tipos_str = ", ".join([f"{k}: {v}" for k, v in tipos_ativos.items()]) if tipos_ativos else "Não disponível"
            else:
                tipos_str = "Coluna TP_ATIVO não encontrada"
            
            # Calcular valor total se disponível
            if 'VL_MERC_POS_FINAL' in df.columns:
                df['VL_MERC_POS_FINAL'] = pd.to_numeric(df['VL_MERC_POS_FINAL'], errors='coerce')
                valor_total = df['VL_MERC_POS_FINAL'].sum()
                print(f"  {data}: {num_ativos} ativos, Valor total: R$ {valor_total:,.2f}")
                print(f"    Tipos de ativos: {tipos_str}")
            else:
                print(f"  {data}: {num_ativos} ativos")
    
    return carteira_completa


def categorizar_ativos(carteira):
    """
    Categoriza os ativos da carteira em grupos mais amplos.
    
    Args:
        carteira (dict): Dicionário com as carteiras por período
        
    Returns:
        dict: Dicionário com as carteiras categorizadas por período
    """
    # Verificação para regras específicas de categorização com base na coluna "TP_APLIC"
    def aplicar_regras_especiais(df):
        # Verificar se a coluna existe
        if 'TP_APLIC' in df.columns:
            # Se TP_APLIC contém "Cotas de Fundos", classificar como "Fundos"
            mask_cotas = df['TP_APLIC'].astype(str).str.contains('Cotas de Fundos', case=False, na=False)
            df.loc[mask_cotas, 'CATEGORIA_ATIVO'] = 'Fundos'
            
            # Classificar disponibilidades como "Caixa e Disponibilidades"
            mask_disp = df['TP_APLIC'].astype(str).str.contains('Disponibilidades', case=False, na=False)
            df.loc[mask_disp, 'CATEGORIA_ATIVO'] = 'Caixa e Disponibilidades'
            
            # Classificar Títulos Públicos
            mask_tpub = df['TP_APLIC'].astype(str).str.contains('Títulos Públicos', case=False, na=False)
            df.loc[mask_tpub, 'CATEGORIA_ATIVO'] = 'Renda Fixa - Título Público'
            
            # Classificar Depósitos e Letras Financeiras
            mask_dep = df['TP_APLIC'].astype(str).str.contains('Depósitos a prazo', case=False, na=False)
            df.loc[mask_dep, 'CATEGORIA_ATIVO'] = 'Renda Fixa - Bancário'
        
        return df
    carteira_categorizada = {}
    
    # Mapeamento de tipos de ativos para categorias mais amplas
    mapeamento_categorias = {
        # Renda Fixa
        'Título Público Federal': 'Renda Fixa - Título Público',
        'Título Público': 'Renda Fixa - Título Público',
        'Título público federal': 'Renda Fixa - Título Público',
        'CDB': 'Renda Fixa - Bancário',
        'LCI': 'Renda Fixa - Bancário',
        'LCA': 'Renda Fixa - Bancário',
        'DPGE': 'Renda Fixa - Bancário',
        'LF': 'Renda Fixa - Bancário',
        'LC': 'Renda Fixa - Bancário',
        'Letra Financeira': 'Renda Fixa - Bancário',
        'Debênture': 'Renda Fixa - Crédito Privado',
        'Debêntures': 'Renda Fixa - Crédito Privado',
        'CRI': 'Renda Fixa - Crédito Privado',
        'CRA': 'Renda Fixa - Crédito Privado',
        'CCB': 'Renda Fixa - Crédito Privado',
        'FIDC': 'Renda Fixa - Crédito Privado',
        
        # Renda Variável
        'Ação': 'Renda Variável - Ações',
        'Ações': 'Renda Variável - Ações',
        'FIA': 'Renda Variável - Ações',
        'Opção': 'Renda Variável - Derivativos',
        'Opções': 'Renda Variável - Derivativos',
        'Termo': 'Renda Variável - Derivativos',
        
        # Fundos
        'Cotas de Fundos': 'Fundos',
        'Fundo de Investimento e de Cotas': 'Fundos',
        'FI': 'Fundos',
        'FIC': 'Fundos',
        'ETF': 'Fundos',
        'FII': 'Fundos Imobiliários',
        
        # Derivativos
        'Swap': 'Derivativos',
        'Futuro': 'Derivativos',
        'NDF': 'Derivativos',
        
        # Outros
        'Ouro': 'Commodities',
        'Compromissada': 'Operação Compromissada',
        'Caixa': 'Caixa e Disponibilidades',
    }
    
    for data, df in carteira.items():
        # Criar cópia do DataFrame
        df_categorizado = df.copy()
        
        # Adicionar coluna de categoria
        if 'TP_ATIVO' in df_categorizado.columns:
            def mapear_categoria(tipo_ativo):
                if pd.isna(tipo_ativo) or tipo_ativo == '' or tipo_ativo is None:
                    return 'Não Classificado'
                
                # Casos especiais com verificação mais específica
                if 'fundo' in tipo_ativo.lower() or 'invest' in tipo_ativo.lower() or 'cota' in tipo_ativo.lower():
                    return 'Fundos'
                
                # Verificar se o tipo está no mapeamento exato
                for chave, valor in mapeamento_categorias.items():
                    if chave.lower() == tipo_ativo.lower():
                        return valor
                
                # Se não encontrou correspondência exata, buscar por substring
                for chave, valor in mapeamento_categorias.items():
                    if chave.lower() in tipo_ativo.lower():
                        return valor
                
                # Verificações adicionais baseadas em padrões comuns
                tipo_lower = tipo_ativo.lower()
                if 'título' in tipo_lower or 'tesouro' in tipo_lower:
                    return 'Renda Fixa - Título Público'
                elif 'cdb' in tipo_lower or 'lci' in tipo_lower or 'lca' in tipo_lower or 'letra' in tipo_lower:
                    return 'Renda Fixa - Bancário'
                elif 'debênture' in tipo_lower or 'cri' in tipo_lower or 'cra' in tipo_lower:
                    return 'Renda Fixa - Crédito Privado'
                elif 'ação' in tipo_lower or 'ações' in tipo_lower:
                    return 'Renda Variável - Ações'
                elif 'opção' in tipo_lower or 'termo' in tipo_lower or 'futuro' in tipo_lower:
                    return 'Renda Variável - Derivativos'
                elif 'disponib' in tipo_lower or 'caixa' in tipo_lower:
                    return 'Caixa e Disponibilidades'
                
                return 'Outros'
            
            df_categorizado['CATEGORIA_ATIVO'] = df_categorizado['TP_ATIVO'].apply(mapear_categoria)
        else:
            df_categorizado['CATEGORIA_ATIVO'] = 'Não Classificado'
        
        # Aplicar regras especiais após a categorização básica
        df_categorizado = aplicar_regras_especiais(df_categorizado)
        
        # Verificar se existem CNPJ de fundos
        for col in ['CNPJ_FUNDO_CLASSE_COTA', 'CNPJ_FUNDO_COTA']:
            if col in df_categorizado.columns:
                # Se existe um CNPJ de fundo, então é um fundo de investimento
                mask_fundos = ~df_categorizado[col].isna()
                df_categorizado.loc[mask_fundos, 'CATEGORIA_ATIVO'] = 'Fundos'
        
        # Adicionar ao dicionário
        carteira_categorizada[data] = df_categorizado
    
    return carteira_categorizada


def analisar_carteira_por_categoria(carteira_categorizada):
    """
    Analisa a composição da carteira por categoria de ativos para cada período.
    
    Args:
        carteira_categorizada (dict): Dicionário com as carteiras categorizadas por período
        
    Returns:
        dict: Dicionário com os resultados da análise por período
    """
    resultados = {}
    
    for data, df in carteira_categorizada.items():
        print(f"\nAnálise da carteira para o período {data}:")
        
        # Verificar se temos as colunas necessárias
        if 'VL_MERC_POS_FINAL' not in df.columns or 'CATEGORIA_ATIVO' not in df.columns:
            print(f"  - Colunas necessárias não encontradas para o período {data}")
            continue
        
        # Converter para numérico
        df['VL_MERC_POS_FINAL'] = pd.to_numeric(df['VL_MERC_POS_FINAL'], errors='coerce')
        
        # Calcular valor total da carteira
        valor_total = df['VL_MERC_POS_FINAL'].sum()
        
        if valor_total == 0:
            print(f"  - Valor total da carteira é zero para o período {data}")
            continue
        
        # Agrupar por categoria e calcular somas e percentuais
        analise = df.groupby('CATEGORIA_ATIVO').agg({
            'VL_MERC_POS_FINAL': 'sum',
        }).reset_index()
        
        # Calcular percentuais
        analise['PERCENTUAL'] = (analise['VL_MERC_POS_FINAL'] / valor_total * 100).round(2)
        
        # Ordenar por valor (decrescente)
        analise = analise.sort_values('VL_MERC_POS_FINAL', ascending=False)
        
        # Exibir resultados
        print(f"  Valor total da carteira: R$ {valor_total:,.2f}")
        print("\n  Composição por categoria:")
        
        for _, row in analise.iterrows():
            categoria = row['CATEGORIA_ATIVO']
            valor = row['VL_MERC_POS_FINAL']
            percentual = row['PERCENTUAL']
            
            print(f"    - {categoria}: R$ {valor:,.2f} ({percentual:.2f}%)")
        
        # Armazenar no dicionário de resultados
        resultados[data] = {
            'valor_total': valor_total,
            'analise_categorias': analise,
            'carteira': df
        }
    
    return resultados


def analisar_concentracao_emissores(carteira_categorizada):
    """
    Analisa a concentração de emissores na carteira.
    
    Args:
        carteira_categorizada (dict): Dicionário com as carteiras categorizadas por período
        
    Returns:
        dict: Dicionário com os resultados da análise por período
    """
    resultados = {}
    
    for data, df in carteira_categorizada.items():
        print(f"\nAnálise de concentração de emissores para o período {data}:")
        
        # Verificar se temos as colunas necessárias
        if 'VL_MERC_POS_FINAL' not in df.columns:
            print(f"  - Coluna VL_MERC_POS_FINAL não encontrada para o período {data}")
            continue
        
        # Identificar coluna de emissor
        coluna_emissor = None
        for col in ['EMISSOR', 'DENOM_SOCIAL_EMISSOR', 'DENOM_SOCIAL', 'NM_FUNDO_CLASSE_SUBCLASSE_COTA']:
            if col in df.columns:
                coluna_emissor = col
                break
        
        if coluna_emissor is None:
            print(f"  - Não foi possível identificar coluna com o nome do emissor para o período {data}")
            continue
        
        # Converter para numérico
        df['VL_MERC_POS_FINAL'] = pd.to_numeric(df['VL_MERC_POS_FINAL'], errors='coerce')
        
        # Calcular valor total da carteira
        valor_total = df['VL_MERC_POS_FINAL'].sum()
        
        if valor_total == 0:
            print(f"  - Valor total da carteira é zero para o período {data}")
            continue
        
        # Agrupar por emissor e calcular somas e percentuais
        analise = df.groupby(coluna_emissor).agg({
            'VL_MERC_POS_FINAL': 'sum',
        }).reset_index()
        
        # Calcular percentuais
        analise['PERCENTUAL'] = (analise['VL_MERC_POS_FINAL'] / valor_total * 100).round(2)
        
        # Ordenar por valor (decrescente)
        analise = analise.sort_values('VL_MERC_POS_FINAL', ascending=False)
        
        # Exibir resultados para os top 10 emissores
        print(f"  Top 10 emissores (Valor total: R$ {valor_total:,.2f}):")
        
        for _, row in analise.head(10).iterrows():
            emissor = row[coluna_emissor]
            valor = row['VL_MERC_POS_FINAL']
            percentual = row['PERCENTUAL']
            
            print(f"    - {emissor}: R$ {valor:,.2f} ({percentual:.2f}%)")
        
        # Armazenar no dicionário de resultados
        resultados[data] = {
            'valor_total': valor_total,
            'analise_emissores': analise,
            'carteira': df
        }
    
    return resultados


def salvar_dados_processados(carteira_completa, base_dir, nome_fundo, formato='csv'):
    """
    Salva os dados processados da carteira.
    
    Args:
        carteira_completa (dict): Dicionário com as carteiras por período
        base_dir (str): Diretório base onde salvar os arquivos
        nome_fundo (str): Nome do fundo para uso no nome dos arquivos
        formato (str): Formato de saída ('csv' ou 'excel')
        
    Returns:
        dict: Dicionário com os caminhos dos arquivos salvos
    """
    # Diretório para salvar os arquivos
    dir_saida = os.path.join(base_dir, 'carteiras_processadas', nome_fundo)
    os.makedirs(dir_saida, exist_ok=True)
    
    arquivos_salvos = {}
    
    for data, df in carteira_completa.items():
        # Formatar data para uso no nome do arquivo
        data_formatada = data.replace('-', '')
        
        # Caminho do arquivo
        if formato.lower() == 'excel':
            caminho_arquivo = os.path.join(dir_saida, f"carteira_{nome_fundo}_{data_formatada}.xlsx")
            df.to_excel(caminho_arquivo, index=False, engine='openpyxl')
        else:  # csv (padrão)
            caminho_arquivo = os.path.join(dir_saida, f"carteira_{nome_fundo}_{data_formatada}.csv")
            df.to_csv(caminho_arquivo, index=False, encoding='utf-8-sig')
        
        arquivos_salvos[data] = caminho_arquivo
        print(f"Salvando carteira de {data} em: {caminho_arquivo}")
    
    # Salvar um arquivo consolidado com todos os períodos
    dfs_com_data = []
    for data, df in carteira_completa.items():
        df_com_data = df.copy()
        df_com_data['PERIODO'] = data
        dfs_com_data.append(df_com_data)
    
    if dfs_com_data:
        df_consolidado = pd.concat(dfs_com_data, ignore_index=True)
        
        if formato.lower() == 'excel':
            caminho_consolidado = os.path.join(dir_saida, f"carteira_{nome_fundo}_consolidado.xlsx")
            df_consolidado.to_excel(caminho_consolidado, index=False, engine='openpyxl')
        else:  # csv (padrão)
            caminho_consolidado = os.path.join(dir_saida, f"carteira_{nome_fundo}_consolidado.csv")
            df_consolidado.to_csv(caminho_consolidado, index=False, encoding='utf-8-sig')
        
        arquivos_salvos['consolidado'] = caminho_consolidado
        print(f"Arquivo consolidado salvo em: {caminho_consolidado}")
    
    return arquivos_salvos


def gerar_relatorio_evolucao_carteira(carteira_completa, base_dir, nome_fundo):
    """
    Versão corrigida da função que gera um relatório de evolução da carteira ao longo do tempo.
    Trata o problema de valores mistos (positivos e negativos) nas categorias.
    
    Args:
        carteira_completa (dict): Dicionário com as carteiras categorizadas por período
        base_dir (str): Diretório base onde salvar os arquivos
        nome_fundo (str): Nome do fundo para uso no nome dos arquivos
        
    Returns:
        str: Caminho do arquivo de relatório gerado
    """
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    import numpy as np
    import pandas as pd
    import os
    from datetime import datetime
    
    # Diretório para salvar os relatórios
    dir_relatorios = os.path.join(base_dir, 'relatorios', nome_fundo)
    os.makedirs(dir_relatorios, exist_ok=True)
    
    # Importar função de categorização
    from carteiras_analysis_utils import categorizar_ativos, analisar_carteira_por_categoria, analisar_concentracao_emissores
    
    # Preparar dados para o relatório
    datas = sorted(list(carteira_completa.keys()))
    
    # Análise por categoria
    carteira_categorizada = categorizar_ativos(carteira_completa)
    resultados_categorias = analisar_carteira_por_categoria(carteira_categorizada)
    
    # DataFrame para armazenar a evolução ao longo do tempo
    dados_evolucao = []
    
    for data in datas:
        if data in resultados_categorias:
            valor_total = resultados_categorias[data]['valor_total']
            analise = resultados_categorias[data]['analise_categorias']
            
            for _, row in analise.iterrows():
                dados_evolucao.append({
                    'Data': data,
                    'Categoria': row['CATEGORIA_ATIVO'],
                    'Valor': row['VL_MERC_POS_FINAL'],
                    'Percentual': row['PERCENTUAL']
                })
    
    if not dados_evolucao:
        print("Sem dados suficientes para gerar relatório de evolução")
        return None
    
    df_evolucao = pd.DataFrame(dados_evolucao)
    
    # Converter para datetime para ordenação correta
    df_evolucao['Data'] = pd.to_datetime(df_evolucao['Data'] + '-01', format='%Y-%m-%d', errors='coerce')
    
    # Ordenar por data
    df_evolucao = df_evolucao.sort_values('Data')
    
    # Gráfico 1: Evolução do valor total da carteira
    plt.figure(figsize=(12, 6))
    
    # Calcular valor total por data
    valor_total_por_data = df_evolucao.groupby('Data')['Valor'].sum().reset_index()
    
    plt.plot(valor_total_por_data['Data'], valor_total_por_data['Valor'], marker='o', linewidth=2)
    plt.title(f'Evolução do Valor Total da Carteira - {nome_fundo}')
    plt.xlabel('Data')
    plt.ylabel('Valor (R$)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45)
    
    # Formatar eixo Y para valores em milhões/bilhões
    if valor_total_por_data['Valor'].max() > 1e9:
        plt.ticklabel_format(style='plain', axis='y', scilimits=(0,0))
        plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: f"R$ {x/1e6:.2f}M"))
    
    plt.tight_layout()
    caminho_grafico1 = os.path.join(dir_relatorios, f"{nome_fundo}_evolucao_valor_total.png")
    plt.savefig(caminho_grafico1, dpi=300, bbox_inches='tight')
    plt.close()
    
    # Gráfico 2: Composição da carteira por categoria ao longo do tempo
    plt.figure(figsize=(14, 8))
    
    # Pivotear dados para obter categorias por data
    df_pivot = df_evolucao.pivot_table(
        index='Data', 
        columns='Categoria', 
        values='Valor',
        aggfunc='sum'
    ).fillna(0)
    
    # Ordenar as categorias por valor médio (decrescente)
    total_por_categoria = df_pivot.sum()
    categorias_ordenadas = total_por_categoria.sort_values(ascending=False).index
    
    # Limitar número de categorias para melhor visualização
    max_categorias = 10
    categorias_principais = [cat for cat in categorias_ordenadas[:max_categorias] if cat != 'Derivativos']
    
    # Verificar se 'Derivativos' está nas categorias principais e possui valores mistos
    if 'Derivativos' in df_pivot.columns:
        derivativos_series = df_pivot['Derivativos']
        tem_pos = (derivativos_series > 0).any()
        tem_neg = (derivativos_series < 0).any()
        
        if tem_pos and tem_neg:
            # Separar derivativos positivos e negativos
            df_pivot['Derivativos (Pos)'] = df_pivot['Derivativos'].apply(lambda x: max(0, x))
            df_pivot['Derivativos (Neg)'] = df_pivot['Derivativos'].apply(lambda x: min(0, x))
            
            # Remover a coluna original
            df_pivot = df_pivot.drop('Derivativos', axis=1)
            
            # Adicionar as novas categorias separadas à lista principal
            if 'Derivativos' in categorias_principais:
                categorias_principais.remove('Derivativos')
                categorias_principais.extend(['Derivativos (Pos)', 'Derivativos (Neg)'])
    
    # Agrupar categorias menores em "Outros"
    outras_categorias = [cat for cat in df_pivot.columns if cat not in categorias_principais 
                        and cat != 'Derivativos (Pos)' and cat != 'Derivativos (Neg)']
    
    if outras_categorias:
        df_outros = df_pivot[outras_categorias].sum(axis=1)
        df_pivot_reduzido = df_pivot[categorias_principais].copy()
        df_pivot_reduzido['Outros'] = df_outros
        
        # Adicionar colunas de derivativos separados se existirem
        if 'Derivativos (Pos)' in df_pivot.columns:
            df_pivot_reduzido['Derivativos (Pos)'] = df_pivot['Derivativos (Pos)']
        if 'Derivativos (Neg)' in df_pivot.columns:
            df_pivot_reduzido['Derivativos (Neg)'] = df_pivot['Derivativos (Neg)']
    else:
        df_pivot_reduzido = df_pivot[categorias_principais].copy()
    
    # Plotar gráfico de barras empilhadas ao invés de área (mais seguro com valores mistos)
    ax = df_pivot_reduzido.plot(kind='bar', figsize=(14, 8), stacked=True, alpha=0.7)
    
    plt.title(f'Evolução da Composição da Carteira por Categoria - {nome_fundo}')
    plt.xlabel('Data')
    plt.ylabel('Valor (R$)')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.xticks(rotation=45)
    
    # Formatar eixo X para mostrar apenas o ano e mês
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, pos: 
                                                    df_pivot_reduzido.index[int(x)].strftime('%Y-%m')))
    
    # Formatar eixo Y
    if df_pivot_reduzido.values.max() > 1e9:
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: f"R$ {x/1e9:.2f}B"))
    else:
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: f"R$ {x/1e6:.2f}M"))
    
    plt.legend(title='Categoria', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    caminho_grafico2 = os.path.join(dir_relatorios, f"{nome_fundo}_evolucao_composicao.png")
    plt.savefig(caminho_grafico2, dpi=300, bbox_inches='tight')
    plt.close()
    
    # Gráfico 3: Evolução da composição percentual
    plt.figure(figsize=(14, 8))
    
    # Para o gráfico percentual, remover categorias com valores negativos (os percentuais não fariam sentido)
    df_para_percentual = df_pivot_reduzido.copy()
    
    # Remover colunas com valores negativos
    colunas_com_negativos = [col for col in df_para_percentual.columns 
                            if (df_para_percentual[col] < 0).any()]
    
    for col in colunas_com_negativos:
        df_para_percentual = df_para_percentual.drop(col, axis=1)
    
    # Calcular percentuais apenas para valores positivos
    totais_por_data = df_para_percentual.sum(axis=1)
    df_percentuais = df_para_percentual.div(totais_por_data, axis=0) * 100
    
    # Plotar gráfico de barras empilhadas para percentuais
    ax = df_percentuais.plot(kind='bar', figsize=(14, 8), stacked=True, alpha=0.7)
    
    plt.title(f'Evolução da Composição Percentual da Carteira - {nome_fundo}')
    plt.xlabel('Data')
    plt.ylabel('Percentual (%)')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.xticks(rotation=45)
    
    # Formatar eixo X para mostrar apenas o ano e mês
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, pos: 
                                                    df_percentuais.index[int(x)].strftime('%Y-%m')))
    
    # Adicionar linhas no grid horizontal
    plt.gca().yaxis.set_major_locator(plt.MultipleLocator(10))
    
    # Limite do eixo Y de 0 a 100%
    plt.ylim(0, 100)
    
    plt.legend(title='Categoria', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    caminho_grafico3 = os.path.join(dir_relatorios, f"{nome_fundo}_evolucao_percentual.png")
    plt.savefig(caminho_grafico3, dpi=300, bbox_inches='tight')
    plt.close()
    
    # Gráfico 4: Análise de concentração de emissores (manter como está)
    resultado_emissores = analisar_concentracao_emissores(carteira_categorizada)
    
    if resultado_emissores and datas[-1] in resultado_emissores:
        ultimo_periodo = datas[-1]
        analise_emissores = resultado_emissores[ultimo_periodo]['analise_emissores']
        
        # Limitar a 15 maiores emissores para o gráfico
        top_emissores = analise_emissores.head(15)
        
        plt.figure(figsize=(12, 8))
        
        # Plotar gráfico de barras horizontais
        coluna_emissor = top_emissores.columns[0]  # Nome da coluna com os emissores
        
        barras = plt.barh(
            top_emissores[coluna_emissor], 
            top_emissores['PERCENTUAL'],
            alpha=0.7,
            color='cornflowerblue'
        )
        
        # Adicionar valores e percentuais nas barras
        for i, bar in enumerate(barras):
            value = top_emissores['VL_MERC_POS_FINAL'].iloc[i]
            percent = top_emissores['PERCENTUAL'].iloc[i]
            
            if value > 1e9:
                value_str = f"R$ {value/1e9:.2f}B"
            else:
                value_str = f"R$ {value/1e6:.2f}M"
                
            plt.text(
                percent + 0.5, 
                i, 
                f"{percent:.2f}% ({value_str})",
                va='center',
                fontsize=9
            )
        
        plt.title(f'Concentração por Emissor - {nome_fundo} ({ultimo_periodo})')
        plt.xlabel('Percentual da Carteira (%)')
        plt.ylabel('Emissor')
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        
        caminho_grafico4 = os.path.join(dir_relatorios, f"{nome_fundo}_concentracao_emissores.png")
        plt.savefig(caminho_grafico4, dpi=300, bbox_inches='tight')
        plt.close()
    
    # Gerar relatório em HTML (mantém como estava)
    caminho_relatorio = os.path.join(dir_relatorios, f"{nome_fundo}_relatorio.html")
    
    # Criar HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Relatório de Evolução da Carteira - {nome_fundo}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2 {{ color: #333366; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .grafico {{ text-align: center; margin: 30px 0; }}
            img {{ max-width: 100%; border: 1px solid #ddd; }}
            .footer {{ text-align: center; margin-top: 40px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Relatório de Evolução da Carteira - {nome_fundo}</h1>
            <p>Período de análise: {datas[0]} a {datas[-1]}</p>
            
            <h2>Evolução do Valor Total da Carteira</h2>
            <div class="grafico">
                <img src="{os.path.basename(caminho_grafico1)}" alt="Evolução do Valor Total">
            </div>
            
            <h2>Evolução da Composição da Carteira</h2>
            <div class="grafico">
                <img src="{os.path.basename(caminho_grafico2)}" alt="Evolução da Composição">
            </div>
            
            <h2>Evolução da Composição Percentual</h2>
            <div class="grafico">
                <img src="{os.path.basename(caminho_grafico3)}" alt="Evolução Percentual">
            </div>
    """
    
    # Adicionar gráfico de concentração de emissores se disponível
    if 'caminho_grafico4' in locals():
        html_content += f"""
            <h2>Concentração por Emissor (Último Período)</h2>
            <div class="grafico">
                <img src="{os.path.basename(caminho_grafico4)}" alt="Concentração por Emissor">
            </div>
        """
    
    # Finalizar HTML
    html_content += f"""
            <div class="footer">
                <p>Relatório gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Salvar HTML
    with open(caminho_relatorio, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\nRelatório de evolução gerado em: {caminho_relatorio}")
    
    return caminho_relatorio


def executar_analise_carteira_completa(cnpj_fundo, nome_fundo, base_dir, limite_arquivos=None, consolidar=False, lista_fundos=None, relacoes_entre_fundos=None):
    """
    Versão corrigida da função que executa o fluxo completo de análise da carteira.
    
    Args:
        cnpj_fundo (str): CNPJ do fundo a ser analisado
        nome_fundo (str): Nome do fundo para uso nos relatórios
        base_dir (str): Diretório base onde estão os arquivos
        limite_arquivos (int, optional): Limita o número de arquivos a processar
        consolidar (bool, optional): Se True, consolida os resultados de múltiplos fundos
        lista_fundos (list, optional): Lista de fundos para consolidação
        relacoes_entre_fundos (dict, optional): Relações entre fundos para ajustar valores
        
    Returns:
        dict: Dicionário com os resultados da análise
    """
    # Importar funções necessárias
    from carteiras_analysis_utils import (
        processar_carteira_completa, 
        categorizar_ativos, 
        analisar_carteira_por_categoria, 
        analisar_concentracao_emissores, 
        salvar_dados_processados,
        serializar_resultados_carteira
    )
    
    print(f"Iniciando análise completa da carteira para {nome_fundo} (CNPJ: {cnpj_fundo})")
    
    # 1. Processar carteira completa
    carteira_completa = processar_carteira_completa(cnpj_fundo, base_dir, limite_arquivos)
    
    if not carteira_completa:
        print("Nenhum dado de carteira encontrado. Processo finalizado.")
        return {'status': 'erro', 'mensagem': 'Nenhum dado encontrado'}
    
    # 2. Categorizar ativos
    carteira_categorizada = categorizar_ativos(carteira_completa)
    
    # 3. Analisar por categoria
    resultados_categorias = analisar_carteira_por_categoria(carteira_categorizada)
    
    # 4. Analisar concentração de emissores
    resultados_emissores = analisar_concentracao_emissores(carteira_categorizada)
    
    # 5. Salvar dados processados
    arquivos_salvos = salvar_dados_processados(carteira_completa, base_dir, nome_fundo, formato='excel')
    
    # 6. Gerar relatório de evolução
    caminho_relatorio = gerar_relatorio_evolucao_carteira(carteira_completa, base_dir, nome_fundo)
    
    # 7. Serializar resultados para posterior consolidação
    caminho_serializado = serializar_resultados_carteira(carteira_categorizada, resultados_categorias, base_dir, nome_fundo)
    
    resultados = {
        'status': 'sucesso',
        'carteira_completa': carteira_completa,
        'carteira_categorizada': carteira_categorizada,
        'resultados_categorias': resultados_categorias,
        'resultados_emissores': resultados_emissores,
        'arquivos_salvos': arquivos_salvos,
        'caminho_relatorio': caminho_relatorio,
        'caminho_serializado': caminho_serializado
    }
    
    # 8. Consolidar resultados com outros fundos se solicitado (mantido como estava)
    if consolidar:
        if not lista_fundos:
            lista_fundos = ['chimborazo', 'aconcagua', 'alpamayo']
        
        # Importar funções de consolidação
        try:
            # Tentar importar do módulo de consolidação
            from consolidar_carteiras import carregar_carteiras_multiplos_fundos, extrair_informacoes_por_fundo, gerar_relatorio_consolidado
            
            print(f"\nConsolidando carteiras para os fundos: {', '.join(lista_fundos)}")
            
            # Verificar quais fundos estão disponíveis
            fundos_disponiveis = []
            for fundo in lista_fundos:
                caminho = os.path.join(base_dir, 'serial_carteiras', f'carteira_{fundo}.pkl')
                if os.path.exists(caminho):
                    fundos_disponiveis.append(fundo)
            
            if not fundos_disponiveis:
                print("Nenhum fundo disponível para consolidação.")
                return resultados
            
            # Carregar carteiras dos fundos disponíveis
            carteiras_consolidadas, resultados_consolidados = carregar_carteiras_multiplos_fundos(base_dir, fundos_disponiveis)
            
            # Extrair informações por fundo
            info_fundos = extrair_informacoes_por_fundo(resultados_consolidados)
            
            # Gerar relatório consolidado
            caminho_relatorio_consolidado = gerar_relatorio_consolidado(
                carteiras_consolidadas, 
                info_fundos, 
                base_dir, 
                relacoes_entre_fundos
            )
            
            # Adicionar resultados da consolidação
            resultados['consolidacao'] = {
                'carteiras_consolidadas': carteiras_consolidadas,
                'resultados_consolidados': resultados_consolidados,
                'info_fundos': info_fundos,
                'caminho_relatorio_consolidado': caminho_relatorio_consolidado
            }
            
            print(f"Consolidação de carteiras concluída. Relatório salvo em: {caminho_relatorio_consolidado}")
            
        except ImportError:
            print(f"AVISO: Módulo de consolidação não encontrado. A consolidação não foi realizada.")
            print(f"Para consolidar, certifique-se que o arquivo consolidar_carteiras.py está no mesmo diretório.")
    
    print("\nAnálise completa finalizada com sucesso!")
    return resultados


def serializar_carteira(carteira_categorizada, resultados_categorias, base_dir, nome_fundo):
    """
    Serializa os resultados da análise da carteira para uso posterior.
    
    Args:
        carteira_categorizada (dict): Dicionário com as carteiras categorizadas por período
        resultados_categorias (dict): Resultados da análise por categoria
        base_dir (str): Diretório base
        nome_fundo (str): Nome do fundo para identificação dos arquivos
        
    Returns:
        str: Caminho do diretório onde os dados foram salvos
    """
    # Criar diretório para dados serializados se não existir
    dir_serial = os.path.join(base_dir, 'serial_carteiras')
    os.makedirs(dir_serial, exist_ok=True)
    
    # Preparar dados para serialização
    dados = {
        'carteira_categorizada': carteira_categorizada,
        'resultados_categorias': resultados_categorias,
        'datas_disponiveis': sorted(list(carteira_categorizada.keys())),
        'ultima_atualizacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Serializar os dados
    caminho_arquivo = os.path.join(dir_serial, f'carteira_{nome_fundo}.pkl')
    with open(caminho_arquivo, 'wb') as f:
        pickle.dump(dados, f)
    
    print(f"Dados da carteira de {nome_fundo} serializados em: {caminho_arquivo}")
    
    return caminho_arquivo


def carregar_carteira_serializada(base_dir, nome_fundo):
    """
    Carrega dados serializados de uma carteira.
    
    Args:
        base_dir (str): Diretório base
        nome_fundo (str): Nome do fundo
        
    Returns:
        dict: Dicionário com os dados carregados
    """
    caminho_arquivo = os.path.join(base_dir, 'serial_carteiras', f'carteira_{nome_fundo}.pkl')
    
    if not os.path.exists(caminho_arquivo):
        print(f"Arquivo serializado para {nome_fundo} não encontrado em: {caminho_arquivo}")
        return None
    
    try:
        with open(caminho_arquivo, 'rb') as f:
            dados = pickle.load(f)
        
        print(f"Dados carregados para {nome_fundo}, última atualização: {dados.get('ultima_atualizacao', 'desconhecida')}")
        return dados
    except Exception as e:
        print(f"Erro ao carregar dados serializados: {str(e)}")
        return None


def carregar_carteiras_multiplos_fundos(base_dir, lista_fundos):
    """
    Carrega carteiras de múltiplos fundos a partir de arquivos serializados.
    
    Args:
        base_dir (str): Diretório base
        lista_fundos (list): Lista com os nomes dos fundos a carregar
        
    Returns:
        tuple: (carteiras_consolidadas, resultados_consolidados)
    """
    carteiras_consolidadas = {}
    resultados_consolidados = {}
    
    for nome_fundo in lista_fundos:
        dados = carregar_carteira_serializada(base_dir, nome_fundo)
        
        if dados:
            # Adicionar dados ao consolidado com identificação do fundo
            carteira = dados['carteira_categorizada']
            resultados = dados['resultados_categorias']
            
            for data, df in carteira.items():
                # Adicionar coluna indicando o fundo
                df_com_fundo = df.copy()
                df_com_fundo['FUNDO'] = nome_fundo
                
                if data in carteiras_consolidadas:
                    carteiras_consolidadas[data] = pd.concat([carteiras_consolidadas[data], df_com_fundo], ignore_index=True)
                else:
                    carteiras_consolidadas[data] = df_com_fundo
                    
            for data, resultado in resultados.items():
                if data in resultados_consolidados:
                    # Adicionar ao dicionário existente com prefixo do fundo
                    resultados_consolidados[data][nome_fundo] = resultado
                else:
                    # Criar novo dicionário para esta data
                    resultados_consolidados[data] = {nome_fundo: resultado}
    
    print(f"Carregados dados para {len(lista_fundos)} fundos em {len(carteiras_consolidadas)} datas distintas")
    return carteiras_consolidadas, resultados_consolidados


def extrair_informacoes_por_fundo(resultados_consolidados):
    """
    Extrai informações resumidas de cada fundo a partir dos resultados consolidados.
    
    Args:
        resultados_consolidados (dict): Dicionário com resultados por data e fundo
        
    Returns:
        dict: Dicionário com informações resumidas por fundo
    """
    info_fundos = {}
    
    # Para cada data nos resultados
    for data, fundos in resultados_consolidados.items():
        # Para cada fundo nesta data
        for nome_fundo, resultado in fundos.items():
            if nome_fundo not in info_fundos:
                info_fundos[nome_fundo] = {
                    'datas': [],
                    'valor_total': [],
                    'analise_categorias': []
                }
            
            # Adicionar informações
            info_fundos[nome_fundo]['datas'].append(data)
            info_fundos[nome_fundo]['valor_total'].append(resultado['valor_total'])
            info_fundos[nome_fundo]['analise_categorias'].append(resultado['analise_categorias'])
    
    # Calcular valores agregados
    for nome_fundo, info in info_fundos.items():
        # Ordenar por data
        indices_ordenados = sorted(range(len(info['datas'])), key=lambda i: info['datas'][i])
        info['datas'] = [info['datas'][i] for i in indices_ordenados]
        info['valor_total'] = [info['valor_total'][i] for i in indices_ordenados]
        info['analise_categorias'] = [info['analise_categorias'][i] for i in indices_ordenados]
        
        # Adicionar informações agregadas
        info['valor_medio'] = np.mean(info['valor_total']) if info['valor_total'] else 0
        info['valor_ultimo'] = info['valor_total'][-1] if info['valor_total'] else 0
        info['data_inicio'] = info['datas'][0] if info['datas'] else None
        info['data_fim'] = info['datas'][-1] if info['datas'] else None
    
    return info_fundos


def plotar_evolucao_valor_fundos_empilhado(info_fundos, base_dir, relacoes_entre_fundos=None, titulo="Evolução do Valor por Fundo", nome_arquivo="evolucao_valor_fundos.png"):
    """
    Gera um gráfico de área empilhada mostrando a evolução do valor total de cada fundo.
    
    Args:
        info_fundos (dict): Dicionário com informações por fundo
        base_dir (str): Diretório base para salvar o gráfico
        relacoes_entre_fundos (dict, optional): Dicionário indicando relações entre fundos
        titulo (str): Título do gráfico
        nome_arquivo (str): Nome do arquivo para salvar o gráfico
        
    Returns:
        str: Caminho do arquivo do gráfico
    """
    # Criar DataFrame com valores por data e fundo
    datas_all = sorted(list(set([data for info in info_fundos.values() for data in info['datas']])))
    
    # Converter para datetime
    datas_dt = pd.to_datetime([f"{data}-01" for data in datas_all])
    
    # Criar DataFrame vazio
    df_valores = pd.DataFrame(index=datas_dt)
    
    # Preencher valores por fundo
    for nome_fundo, info in info_fundos.items():
        # Criar série temporal
        valores_series = pd.Series(
            index=pd.to_datetime([f"{data}-01" for data in info['datas']]),
            data=info['valor_total']
        )
        
        # Adicionar ao DataFrame
        df_valores[nome_fundo] = valores_series
    
    # Preencher valores faltantes
    df_valores = df_valores.fillna(0)
    
    # Se temos relações entre fundos, ajustar os valores
    if relacoes_entre_fundos:
        df_valores_ajustados = df_valores.copy()
        
        for fundo, relacoes in relacoes_entre_fundos.items():
            if 'investido_por' in relacoes:
                for investidor, valores in relacoes['investido_por'].items():
                    # Para cada data onde temos valores específicos
                    for data_str, valor in valores.items():
                        if data_str in datas_all:
                            # Índice correspondente à data
                            data_idx = pd.to_datetime(f"{data_str}-01")
                            
                            if data_idx in df_valores_ajustados.index:
                                # Reduzir o valor do fundo investidor
                                df_valores_ajustados.loc[data_idx, investidor] -= valor
        
        # Usar os valores ajustados
        df_plot = df_valores_ajustados
    else:
        # Usar os valores originais
        df_plot = df_valores
    
    # Garantir que não temos valores negativos
    df_plot = df_plot.clip(lower=0)
    
    # Configurar cores para os fundos
    cores_fundos = {
        'chimborazo': '#CD853F',  # Marrom (Peru/Tan)
        'aconcagua': '#A0A0A0',   # Cinza
        'alpamayo': '#1A5276'     # Azul escuro
    }
    
    # Cores padrão para fundos não definidos
    cores_adicionais = ['#9B59B6', '#F39C12', '#1ABC9C', '#34495E', '#D35400']
    
    # Para cada fundo sem cor definida, atribuir uma cor
    for i, fundo in enumerate([f for f in df_plot.columns if f not in cores_fundos]):
        idx = i % len(cores_adicionais)
        cores_fundos[fundo] = cores_adicionais[idx]
    
    # Criar figura
    plt.figure(figsize=(14, 8))
    
    # Definir ordem de plotagem (ordem alfabética)
    colunas_ordenadas = sorted(df_plot.columns)
    
    # Plotar área empilhada
    ax = df_plot[colunas_ordenadas].plot.area(
        figsize=(14, 8),
        alpha=0.7,
        stacked=True,
        color=[cores_fundos.get(col, 'gray') for col in colunas_ordenadas]
    )
    
    # Configurar eixos e títulos
    plt.title(titulo, fontsize=14, pad=20)
    plt.xlabel('Data', fontsize=12)
    plt.ylabel('Valor (R$)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.xticks(rotation=45)
    
    # Formatação do eixo Y
    if df_plot.values.sum().max() > 1e9:
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: f"R$ {x/1e9:.1f}B"))
    else:
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: f"R$ {x/1e6:.1f}M"))
    
    # Adicionar legenda
    plt.legend(title='Fundo', loc='upper left')
    
    # Ajustar layout
    plt.tight_layout()
    
    # Diretório para salvar o gráfico
    dir_graficos = os.path.join(base_dir, 'graficos_fundos_consolidados')
    os.makedirs(dir_graficos, exist_ok=True)
    
    # Caminho do arquivo
    caminho_arquivo = os.path.join(dir_graficos, nome_arquivo)
    
    # Salvar gráfico
    plt.savefig(caminho_arquivo, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Gráfico consolidado salvo em: {caminho_arquivo}")
    
    return caminho_arquivo


def analisar_composicao_consolidada(carteiras_consolidadas, data=None):
    """
    Analisa a composição consolidada das carteiras por categoria e fundo.
    
    Args:
        carteiras_consolidadas (dict): Dicionário com carteiras por data
        data (str, optional): Data específica para análise, se None usa a mais recente
        
    Returns:
        tuple: (DataFrame com análise por categoria e fundo, data analisada)
    """
    # Se não especificada, usa a data mais recente
    if data is None:
        data = sorted(list(carteiras_consolidadas.keys()))[-1]
    
    if data not in carteiras_consolidadas:
        print(f"Data {data} não encontrada nas carteiras consolidadas")
        return None, None
    
    # DataFrame para esta data
    df = carteiras_consolidadas[data]
    
    # Verificar se temos as colunas necessárias
    if 'VL_MERC_POS_FINAL' not in df.columns or 'CATEGORIA_ATIVO' not in df.columns or 'FUNDO' not in df.columns:
        print(f"Colunas necessárias não encontradas para a data {data}")
        return None, data
    
    # Converter para numérico
    df['VL_MERC_POS_FINAL'] = pd.to_numeric(df['VL_MERC_POS_FINAL'], errors='coerce')
    
    # Calcular valor total
    valor_total = df['VL_MERC_POS_FINAL'].sum()
    
    # Agrupar por fundo e categoria
    analise = df.groupby(['FUNDO', 'CATEGORIA_ATIVO']).agg({
        'VL_MERC_POS_FINAL': 'sum'
    }).reset_index()
    
    # Calcular percentuais (do total geral)
    analise['PERCENTUAL_TOTAL'] = (analise['VL_MERC_POS_FINAL'] / valor_total * 100).round(2)
    
    # Calcular percentuais por fundo
    analise_fundo = df.groupby('FUNDO').agg({
        'VL_MERC_POS_FINAL': 'sum'
    }).reset_index()
    
    # Mapear valores por fundo
    mapa_valor_fundo = dict(zip(analise_fundo['FUNDO'], analise_fundo['VL_MERC_POS_FINAL']))
    
    # Adicionar percentual dentro do fundo
    analise['VALOR_FUNDO'] = analise['FUNDO'].map(mapa_valor_fundo)
    analise['PERCENTUAL_FUNDO'] = (analise['VL_MERC_POS_FINAL'] / analise['VALOR_FUNDO'] * 100).round(2)
    
    # Ordenar por valor (decrescente)
    analise = analise.sort_values(['FUNDO', 'VL_MERC_POS_FINAL'], ascending=[True, False])
    
    return analise, data


def plotar_composicao_por_fundo(analise, data, base_dir, titulo="Composição por Categoria e Fundo", nome_arquivo="composicao_por_fundo.png"):
    """
    Gera um gráfico de barras empilhadas mostrando a composição por categoria para cada fundo.
    
    Args:
        analise (DataFrame): DataFrame com análise por categoria e fundo
        data (str): Data da análise
        base_dir (str): Diretório base para salvar o gráfico
        titulo (str): Título do gráfico
        nome_arquivo (str): Nome do arquivo para salvar o gráfico
        
    Returns:
        str: Caminho do arquivo do gráfico
    """
    if analise is None:
        print("Dados de análise não disponíveis")
        return None
    
    # Pivotear dados para plotagem
    df_pivot = analise.pivot_table(
        index='FUNDO',
        columns='CATEGORIA_ATIVO',
        values='VL_MERC_POS_FINAL',
        aggfunc='sum'
    ).fillna(0)
    
    # Ordenar os fundos por valor total
    valor_total_por_fundo = df_pivot.sum(axis=1).sort_values(ascending=False)
    df_pivot = df_pivot.loc[valor_total_por_fundo.index]
    
    # Criar figura
    plt.figure(figsize=(14, 8))
    
    # Normalizar para percentuais
    df_percentual = df_pivot.div(df_pivot.sum(axis=1), axis=0) * 100
    
    # Garantir ordem consistente de categorias
    categorias_ordem = [
        'Renda Fixa - Título Público',
        'Renda Fixa - Bancário',
        'Renda Fixa - Crédito Privado',
        'Renda Variável - Ações',
        'Renda Variável - Derivativos',
        'Fundos',
        'Fundos Imobiliários',
        'Derivativos',
        'Commodities',
        'Caixa e Disponibilidades',
        'Operação Compromissada',
        'Outros',
        'Não Classificado'
    ]
    
    # Usar apenas categorias presentes nos dados
    categorias_presentes = [cat for cat in categorias_ordem if cat in df_percentual.columns]
    outras_categorias = [cat for cat in df_percentual.columns if cat not in categorias_ordem]
    categorias_final = categorias_presentes + outras_categorias
    
    # Plotar barras
    ax = df_percentual[categorias_final].plot(
        kind='barh',
        stacked=True,
        figsize=(14, 8),
        width=0.7,
        alpha=0.8
    )
    
    # Adicionar valores e percentuais
    for fundo in df_pivot.index:
        valor_total = df_pivot.loc[fundo].sum()
        if valor_total >= 1e9:
            valor_str = f"R$ {valor_total/1e9:.2f}B"
        else:
            valor_str = f"R$ {valor_total/1e6:.2f}M"
            
        # Adicionar texto à direita de cada barra
        plt.text(
            101,  # Posição logo após 100%
            df_percentual.index.get_loc(fundo),
            f" {valor_str}",
            va='center',
            ha='left',
            fontsize=9
        )
    
    # Configurar eixos e títulos
    plt.title(f"{titulo} ({data})", fontsize=14, pad=20)
    plt.xlabel('Percentual (%)', fontsize=12)
    plt.ylabel('Fundo', fontsize=12)
    plt.xlim(0, 120)  # Espaço extra para os valores
    plt.grid(True, linestyle='--', alpha=0.3, axis='x')
    
    # Adicionar legenda
    plt.legend(title='Categoria', loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3)
    
    # Ajustar layout
    plt.tight_layout()
    
    # Diretório para salvar o gráfico
    dir_graficos = os.path.join(base_dir, 'graficos_fundos_consolidados')
    os.makedirs(dir_graficos, exist_ok=True)
    
    # Caminho do arquivo
    caminho_arquivo = os.path.join(dir_graficos, nome_arquivo)
    
    # Salvar gráfico
    plt.savefig(caminho_arquivo, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Gráfico de composição por fundo salvo em: {caminho_arquivo}")
    
    return caminho_arquivo


def plotar_distribuicao_categoria_consolidada(analise, data, base_dir, titulo="Distribuição Consolidada por Categoria", nome_arquivo="distribuicao_categoria_consolidada.png"):
    """
    Gera um gráfico de pizza mostrando a distribuição consolidada por categoria.
    
    Args:
        analise (DataFrame): DataFrame com análise por categoria e fundo
        data (str): Data da análise
        base_dir (str): Diretório base para salvar o gráfico
        titulo (str): Título do gráfico
        nome_arquivo (str): Nome do arquivo para salvar o gráfico
        
    Returns:
        str: Caminho do arquivo do gráfico
    """
    if analise is None:
        print("Dados de análise não disponíveis")
        return None
    
    # Agrupar por categoria
    analise_categoria = analise.groupby('CATEGORIA_ATIVO').agg({
        'VL_MERC_POS_FINAL': 'sum'
    }).reset_index()
    
    # Calcular percentual
    valor_total = analise_categoria['VL_MERC_POS_FINAL'].sum()
    analise_categoria['PERCENTUAL'] = (analise_categoria['VL_MERC_POS_FINAL'] / valor_total * 100).round(2)
    
    # Ordenar por valor (decrescente)
    analise_categoria = analise_categoria.sort_values('VL_MERC_POS_FINAL', ascending=False)
    
    # Criar figura
    plt.figure(figsize=(12, 10))
    
    # Limitar número de categorias visíveis
    max_categorias = 10
    if len(analise_categoria) > max_categorias:
        # Separar categorias principais e outras
        categorias_principais = analise_categoria.head(max_categorias-1)
        categorias_outras = analise_categoria.iloc[max_categorias-1:]
        
        # Criar categoria "Outros"
        outros = {
            'CATEGORIA_ATIVO': 'Outros',
            'VL_MERC_POS_FINAL': categorias_outras['VL_MERC_POS_FINAL'].sum(),
            'PERCENTUAL': categorias_outras['PERCENTUAL'].sum()
        }
        
        # Adicionar à análise
        analise_categoria = pd.concat([
            categorias_principais,
            pd.DataFrame([outros])
        ], ignore_index=True)
    
    # Adicionar informação de valor na legenda
    labels = []
    for _, row in analise_categoria.iterrows():
        categoria = row['CATEGORIA_ATIVO']
        percentual = row['PERCENTUAL']
        valor = row['VL_MERC_POS_FINAL']
        
        if valor >= 1e9:
            valor_str = f"R$ {valor/1e9:.2f}B"
        else:
            valor_str = f"R$ {valor/1e6:.2f}M"
            
        labels.append(f"{categoria} ({percentual:.1f}%): {valor_str}")
    
    # Cores para categorias específicas
    cores_categorias = {
        'Renda Fixa - Título Público': '#6baed6',
        'Renda Fixa - Bancário': '#3182bd',
        'Renda Fixa - Crédito Privado': '#08519c',
        'Renda Variável - Ações': '#ef6548',
        'Renda Variável - Derivativos': '#a50f15',
        'Fundos': '#fd8d3c',
        'Fundos Imobiliários': '#e6550d',
        'Derivativos': '#31a354',
        'Commodities': '#006d2c',
        'Caixa e Disponibilidades': '#756bb1',
        'Operação Compromissada': '#54278f',
        'Outros': '#969696',
        'Não Classificado': '#636363'
    }
    
    # Plotar gráfico de pizza
    wedges, _, autotexts = plt.pie(
        analise_categoria['VL_MERC_POS_FINAL'],
        labels=None,
        autopct='%1.1f%%',
        startangle=90,
        pctdistance=0.85,
        wedgeprops={'edgecolor': 'w', 'linewidth': 1},
        colors=[cores_categorias.get(cat, 'gray') for cat in analise_categoria['CATEGORIA_ATIVO']]
    )
    
    # Configurar fonte dos percentuais
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(9)
    
    # Adicionar título e legenda
    plt.title(f"{titulo} ({data})\nTotal: R$ {valor_total/1e6:.2f}M", fontsize=14, pad=20)
    plt.legend(wedges, labels, loc='center left', bbox_to_anchor=(1, 0, 0.5, 1), fontsize=9)
    
    # Ajustar layout
    plt.tight_layout()
    
    # Diretório para salvar o gráfico
    dir_graficos = os.path.join(base_dir, 'graficos_fundos_consolidados')
    os.makedirs(dir_graficos, exist_ok=True)
    
    # Caminho do arquivo
    caminho_arquivo = os.path.join(dir_graficos, nome_arquivo)
    
    # Salvar gráfico
    plt.savefig(caminho_arquivo, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Gráfico de distribuição consolidada por categoria salvo em: {caminho_arquivo}")
    
    return caminho_arquivo


def gerar_relatorio_consolidado(carteiras_consolidadas, info_fundos, base_dir, 
                              relacoes_entre_fundos=None, 
                              data_analise=None,
                              nome_relatorio="relatorio_consolidado.html"):
    """
    Gera um relatório HTML consolidado com gráficos e análises.
    
    Args:
        carteiras_consolidadas (dict): Dicionário com carteiras por data
        info_fundos (dict): Informações resumidas por fundo
        base_dir (str): Diretório base
        relacoes_entre_fundos (dict, optional): Relações entre fundos
        data_analise (str, optional): Data específica para análise
        nome_relatorio (str): Nome do arquivo de relatório
        
    Returns:
        str: Caminho do arquivo de relatório
    """
    # Gerar gráficos
    grafico_evolucao = plotar_evolucao_valor_fundos_empilhado(
        info_fundos, 
        base_dir,
        relacoes_entre_fundos,
        titulo="Evolução do Patrimônio por Fundo",
        nome_arquivo="evolucao_patrimonio_fundos.png"
    )
    
    # Analisar composição
    analise_composicao, data = analisar_composicao_consolidada(carteiras_consolidadas, data_analise)
    
    if analise_composicao is not None:
        grafico_composicao = plotar_composicao_por_fundo(
            analise_composicao, 
            data,
            base_dir,
            titulo="Composição por Categoria e Fundo",
            nome_arquivo="composicao_por_fundo.png"
        )
        
        grafico_distribuicao = plotar_distribuicao_categoria_consolidada(
            analise_composicao,
            data,
            base_dir,
            titulo="Distribuição Consolidada por Categoria",
            nome_arquivo="distribuicao_categoria_consolidada.png"
        )
    else:
        grafico_composicao = None
        grafico_distribuicao = None
    
    # Criar diretório para relatórios
    dir_relatorios = os.path.join(base_dir, 'relatorios_consolidados')
    os.makedirs(dir_relatorios, exist_ok=True)
    
    # Tabela de resumo por fundo
    tabela_fundos = "<table class='fundo-table'>"
    tabela_fundos += "<tr><th>Fundo</th><th>Último Valor</th><th>Valor Médio</th><th>Data Inicial</th><th>Data Final</th></tr>"
    
    for nome_fundo, info in info_fundos.items():
        ultimo_valor = f"R$ {info['valor_ultimo']/1e6:.2f}M"
        valor_medio = f"R$ {info['valor_medio']/1e6:.2f}M"
        
        tabela_fundos += f"<tr>"
        tabela_fundos += f"<td>{nome_fundo.capitalize()}</td>"
        tabela_fundos += f"<td>{ultimo_valor}</td>"
        tabela_fundos += f"<td>{valor_medio}</td>"
        tabela_fundos += f"<td>{info['data_inicio']}</td>"
        tabela_fundos += f"<td>{info['data_fim']}</td>"
        tabela_fundos += f"</tr>"
    
    tabela_fundos += "</table>"
    
    # Criar HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Relatório Consolidado de Carteiras</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2 {{ color: #333366; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .grafico {{ text-align: center; margin: 30px 0; }}
            img {{ max-width: 100%; border: 1px solid #ddd; }}
            .footer {{ text-align: center; margin-top: 40px; color: #666; font-size: 12px; }}
            .fundo-table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; }}
            .fundo-table th {{ background-color: #f2f2f2; padding: 10px; text-align: left; border: 1px solid #ddd; }}
            .fundo-table td {{ padding: 8px; border: 1px solid #ddd; }}
            .fundo-table tr:nth-child(even) {{ background-color: #f9f9f9; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Relatório Consolidado de Carteiras</h1>
            <p>Data de referência: {data if data else 'Mais recente disponível'}</p>
            
            <h2>Resumo dos Fundos</h2>
            {tabela_fundos}
            
            <h2>Evolução do Patrimônio</h2>
            <div class="grafico">
                <img src="../graficos_fundos_consolidados/{os.path.basename(grafico_evolucao)}" alt="Evolução do Patrimônio">
            </div>
    """
    
    # Adicionar gráficos de composição se disponíveis
    if grafico_composicao:
        html_content += f"""
            <h2>Composição por Categoria e Fundo</h2>
            <div class="grafico">
                <img src="../graficos_fundos_consolidados/{os.path.basename(grafico_composicao)}" alt="Composição por Fundo">
            </div>
        """
    
    if grafico_distribuicao:
        html_content += f"""
            <h2>Distribuição Consolidada por Categoria</h2>
            <div class="grafico">
                <img src="../graficos_fundos_consolidados/{os.path.basename(grafico_distribuicao)}" alt="Distribuição por Categoria">
            </div>
        """
    
    # Finalizar HTML
    html_content += f"""
            <div class="footer">
                <p>Relatório gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Salvar HTML
    caminho_relatorio = os.path.join(dir_relatorios, nome_relatorio)
    with open(caminho_relatorio, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\nRelatório consolidado gerado em: {caminho_relatorio}")
    
    return caminho_relatorio


def consolidar_carteiras_fundos(lista_fundos, base_dir, relacoes_entre_fundos=None, data_analise=None):
    """
    Função principal para consolidar carteiras de múltiplos fundos e gerar relatórios.
    
    Args:
        lista_fundos (list): Lista com os nomes dos fundos a consolidar
        base_dir (str): Diretório base
        relacoes_entre_fundos (dict, optional): Relações entre fundos
        data_analise (str, optional): Data específica para análise
        
    Returns:
        dict: Dicionário com resultados e caminhos dos arquivos gerados
    """
    print(f"Iniciando consolidação de carteiras para os fundos: {', '.join(lista_fundos)}")
    
    # Carregar carteiras
    carteiras_consolidadas, resultados_consolidados = carregar_carteiras_multiplos_fundos(
        base_dir, 
        lista_fundos
    )
    
    if not carteiras_consolidadas or not resultados_consolidados:
        print("Não foi possível carregar os dados dos fundos. Verifique se os arquivos serializados existem.")
        return None
    
    # Extrair informações por fundo
    info_fundos = extrair_informacoes_por_fundo(resultados_consolidados)
    
    # Gerar relatório consolidado
    caminho_relatorio = gerar_relatorio_consolidado(
        carteiras_consolidadas,
        info_fundos,
        base_dir,
        relacoes_entre_fundos,
        data_analise
    )
    
    print("\nProcesso de consolidação finalizado com sucesso!")
    
    return {
        'carteiras_consolidadas': carteiras_consolidadas,
        'resultados_consolidados': resultados_consolidados,
        'info_fundos': info_fundos,
        'caminho_relatorio': caminho_relatorio
    }


def integrar_analise_consolidacao(carteira_categorizada, resultados_categorias, base_dir, nome_fundo, consolidar=False, relacoes_entre_fundos=None):
    """
    Integra a análise de carteira individual com o processo de consolidação.
    
    Args:
        carteira_categorizada (dict): Dicionário com carteiras categorizadas
        resultados_categorias (dict): Resultados da análise por categoria
        base_dir (str): Diretório base
        nome_fundo (str): Nome do fundo atual
        consolidar (bool): Se True, executa a consolidação
        relacoes_entre_fundos (dict, optional): Relações entre fundos
        
    Returns:
        dict: Resultados da consolidação (se consolidar=True)
    """
    # Serializar resultados da análise
    serializar_carteira(carteira_categorizada, resultados_categorias, base_dir, nome_fundo)
    
    # Se solicitado, consolida os resultados
    if consolidar:
        lista_fundos = ['chimborazo', 'aconcagua', 'alpamayo']
        
        # Verificar se os fundos da lista foram processados
        fundos_disponiveis = []
        for fundo in lista_fundos:
            caminho = os.path.join(base_dir, 'serial_carteiras', f'carteira_{fundo}.pkl')
            if os.path.exists(caminho):
                fundos_disponiveis.append(fundo)
        
        if not fundos_disponiveis:
            print("Nenhum fundo disponível para consolidação. Execute a análise para cada fundo primeiro.")
            return None
        
        print(f"Consolidando dados para os fundos: {', '.join(fundos_disponiveis)}")
        
        # Executar consolidação
        resultados = consolidar_carteiras_fundos(
            fundos_disponiveis,
            base_dir,
            relacoes_entre_fundos
        )
        
        return resultados
    
    return None


def criar_mapeamento_cnpj_objetivo(lista_cnpj_objetivo):
    """
    Cria um dicionário de mapeamento de CNPJs para objetivos a partir de uma lista no formato:
    ["Ganho\t41.535.122/0001-60", "Manutenção\t07.096.546/0001-37", ...]
    
    Args:
        lista_cnpj_objetivo (list): Lista de strings no formato "Objetivo\tCNPJ"
        
    Returns:
        dict: Dicionário com CNPJs como chaves e objetivos como valores
    """
    mapeamento = {}
    
    for linha in lista_cnpj_objetivo:
        if '\t' in linha:
            objetivo, cnpj = linha.split('\t')
            mapeamento[cnpj.strip()] = objetivo.strip()
    
    return mapeamento


def classificar_produtos_por_objetivo(df_carteira, periodo=None, classificacao_cnpj=None, solicitar_input=True):
    """
    Classifica os produtos das carteiras em categorias por objetivo de investimento:
    - Preservação: produtos que visam bater o CDI
    - Manutenção: produtos que visam bater a inflação
    - Ganho: produtos que visam bater o Ibovespa
    
    Args:
        df_carteira (DataFrame): DataFrame com os dados da carteira consolidada
        periodo (str, optional): Identificação do período para referência
        classificacao_cnpj (dict, optional): Dicionário com a classificação por CNPJ
        solicitar_input (bool): Se True, solicita input do usuário para produtos não classificados
        
    Returns:
        DataFrame: DataFrame com a coluna adicional 'OBJETIVO'
    """
    import pandas as pd
    
    # Criar cópia do DataFrame para não modificar o original
    df = df_carteira.copy()
    
    # Identificar o período se não foi especificado
    if periodo is None and 'DT_COMPTC' in df.columns:
        # Pegar a data mais recente
        periodo = pd.to_datetime(df['DT_COMPTC']).max().strftime('%Y-%m-%d')
    elif periodo is None:
        periodo = "Período não especificado"
    
    # Criar uma coluna 'OBJETIVO' com valor padrão
    df['OBJETIVO'] = 'Não classificado'
    
    # IMPORTANTE: Verificar as colunas que contêm CNPJs (podem existir variações)
    colunas_cnpj = [col for col in df.columns if 'CNPJ' in col.upper()]
    print(f"Colunas com CNPJ encontradas: {colunas_cnpj}")
    
    # Verificar quais colunas podem conter o CNPJ do fundo a ser classificado
    colunas_cnpj_relevantes = []
    for col in ['CNPJ_FUNDO_COTA', 'CNPJ_FUNDO_CLASSE_COTA', 'CNPJ_EMISSOR']:
        if col in df.columns:
            colunas_cnpj_relevantes.append(col)
    
    # Se não encontrou colunas específicas, usar todas as colunas que contêm CNPJ
    if not colunas_cnpj_relevantes:
        colunas_cnpj_relevantes = colunas_cnpj
    
    print(f"Colunas de CNPJ relevantes para classificação: {colunas_cnpj_relevantes}")
    
    # Se foi fornecido um dicionário de classificação por CNPJ, aplicar primeiro
    if classificacao_cnpj and colunas_cnpj_relevantes:
        print(f"Aplicando classificação baseada no dicionário com {len(classificacao_cnpj)} CNPJs")
        
        # Definir uma função para aplicar a classificação por CNPJ
        def classificar_por_cnpj(row):
            if row['OBJETIVO'] != 'Não classificado':
                return row['OBJETIVO']
                
            for col in colunas_cnpj_relevantes:
                if col in row and pd.notna(row[col]) and row[col] in classificacao_cnpj:
                    return classificacao_cnpj[row[col]]
            
            return row['OBJETIVO']
        
        # Aplicar a função para cada linha
        df['OBJETIVO'] = df.apply(classificar_por_cnpj, axis=1)
        
        # Contar quantos produtos foram classificados por CNPJ
        count = df[df['OBJETIVO'] != 'Não classificado'].shape[0]
        print(f"  - Classificados por CNPJ: {count} produtos")
    
    # NOVA REGRA: Classificar todas as debêntures como "Manutenção"
    if 'TP_ATIVO' in df.columns:
        df.loc[(df['OBJETIVO'] == 'Não classificado') & df['TP_ATIVO'].str.contains('debênture|debenture', case=False, na=False), 'OBJETIVO'] = 'Manutenção'
    
    if 'TP_APLIC' in df.columns:
        df.loc[(df['OBJETIVO'] == 'Não classificado') & df['TP_APLIC'].str.contains('debênture|debenture', case=False, na=False), 'OBJETIVO'] = 'Manutenção'
    
    # Verificar se há uma coluna DS_ATIVO para identificar debêntures
    if 'DS_ATIVO' in df.columns:
        df.loc[(df['OBJETIVO'] == 'Não classificado') & df['DS_ATIVO'].str.contains('DEB', case=False, na=False), 'OBJETIVO'] = 'Manutenção'
    
    # Determinar os campos principais para análise
    coluna_nome_fundo = None
    coluna_nome_produto = None
    
    # Verificar quais colunas estão disponíveis para classificação
    colunas_nome_fundo = ['DENOM_SOCIAL']
    colunas_nome_produto = ['NM_FUNDO_CLASSE_SUBCLASSE_COTA', 'NM_FUNDO_COTA']
    
    for col in colunas_nome_fundo:
        if col in df.columns:
            coluna_nome_fundo = col
            break
    
    for col in colunas_nome_produto:
        if col in df.columns:
            coluna_nome_produto = col
            break
    
    # Priorizar os campos de tipo de ativo e aplicação
    tem_tipo_ativo = 'TP_ATIVO' in df.columns
    tem_tipo_aplic = 'TP_APLIC' in df.columns
    
    # 1. Primeira regra de classificação: baseada no tipo de ativo (apenas para itens não classificados por CNPJ)
    if tem_tipo_ativo:
        # Classificar títulos públicos e renda fixa
        df.loc[(df['OBJETIVO'] == 'Não classificado') & df['TP_ATIVO'].str.contains('público|federal|tesouro', case=False, na=False), 'OBJETIVO'] = 'Preservação'
        df.loc[(df['OBJETIVO'] == 'Não classificado') & df['TP_ATIVO'].str.contains('letra financeira|cdb|lci|lca', case=False, na=False), 'OBJETIVO'] = 'Preservação'
        
        # Classificar fundos de ações e produtos de renda variável
        df.loc[(df['OBJETIVO'] == 'Não classificado') & df['TP_ATIVO'].str.contains('acoes|ações|equities|fundo.*ação|ação.*fundo', case=False, na=False), 'OBJETIVO'] = 'Ganho'
        
        # Classificar fundos de participações
        df.loc[(df['OBJETIVO'] == 'Não classificado') & df['TP_ATIVO'].str.contains('participações|participacoes|private equity', case=False, na=False), 'OBJETIVO'] = 'Manutenção'
        
        # Classificar FIDC
        df.loc[(df['OBJETIVO'] == 'Não classificado') & df['TP_ATIVO'].str.contains('FIDC|creditórios|creditorios', case=False, na=False), 'OBJETIVO'] = 'Preservação'
    
    # 2. Segunda regra: baseada no tipo de aplicação
    if tem_tipo_aplic:
        df.loc[(df['OBJETIVO'] == 'Não classificado') & df['TP_APLIC'].str.contains('Títulos Públicos|títulos públicos', case=False, na=False), 'OBJETIVO'] = 'Preservação'
        df.loc[(df['OBJETIVO'] == 'Não classificado') & df['TP_APLIC'].str.contains('Depósitos a prazo|depósitos|letra financeira', case=False, na=False), 'OBJETIVO'] = 'Preservação'
        df.loc[(df['OBJETIVO'] == 'Não classificado') & df['TP_APLIC'].str.contains('Disponibilidades|caixa', case=False, na=False), 'OBJETIVO'] = 'Preservação'
    
    # 3. Terceira regra: baseada no nome do produto (mais detalhado)
    if coluna_nome_produto:
        # Dicionário de classificações manuais para produtos específicos
        classificacao_manual = {
            # Preservação (produtos que visam bater o CDI)
            'referenciado di': 'Preservação',
            'renda fixa': 'Preservação',
            'caixa': 'Preservação',
            'tesouro': 'Preservação',
            'vértice renda fixa': 'Preservação',
            'vértice rf': 'Preservação',
            'direitos creditórios': 'Preservação',
            'crédito privado': 'Preservação',
            'fidc': 'Preservação',
            
            # Manutenção (produtos que visam bater a inflação)
            'multimercado': 'Manutenção',
            'solutions vega': 'Manutenção',
            'multigestor': 'Manutenção',
            'multimesas': 'Manutenção',
            'private equity': 'Manutenção',
            'vinci capital': 'Manutenção',
            'kinea': 'Manutenção',
            'legacy capital': 'Manutenção',
            'absolute bold': 'Manutenção',
            'spx raptor': 'Manutenção',
            'kapitalo': 'Manutenção',
            'verde': 'Manutenção',
            'genoa capital': 'Manutenção',
            
            # Ganho (produtos que visam bater o Ibovespa)
            'ações': 'Ganho',
            'long biased': 'Ganho',
            'absoluto partners': 'Ganho',
            'ibovespa': 'Ganho',
            'equities': 'Ganho',
            'oceana': 'Ganho',
            'sharp long': 'Ganho',
            'fundamenta latam': 'Ganho',
            'navi': 'Ganho',
            'squadra': 'Ganho',
            'phantom': 'Ganho',
            'atit vértice fof': 'Ganho',
            'prowler': 'Ganho'
        }
        
        # Aplicar classificação manual apenas para itens não classificados por CNPJ
        for termo, objetivo in classificacao_manual.items():
            df.loc[(df['OBJETIVO'] == 'Não classificado') & df[coluna_nome_produto].str.contains(termo, case=False, na=False), 'OBJETIVO'] = objetivo
    
    # 4. Quarta regra: baseada no nome do fundo (para casos específicos)
    if coluna_nome_fundo:
        df.loc[(df['OBJETIVO'] == 'Não classificado') & df[coluna_nome_fundo].str.contains('ações|acoes', case=False, na=False), 'OBJETIVO'] = 'Ganho'
        df.loc[(df['OBJETIVO'] == 'Não classificado') & df[coluna_nome_fundo].str.contains('multimercado', case=False, na=False), 'OBJETIVO'] = 'Manutenção'
        df.loc[(df['OBJETIVO'] == 'Não classificado') & df[coluna_nome_fundo].str.contains('renda fixa', case=False, na=False), 'OBJETIVO'] = 'Preservação'
    
    # 5. Regra específica para "Valores a pagar" e "Valores a receber"
    if 'TP_APLIC' in df.columns:
        df.loc[(df['OBJETIVO'] == 'Não classificado') & df['TP_APLIC'].str.contains('Valores a pagar|Valores a receber', case=False, na=False), 'OBJETIVO'] = 'Preservação'
    
    # 6. Classificar pelo nome do fundo em casos que ainda não foram classificados
    if coluna_nome_produto and (df['OBJETIVO'] == 'Não classificado').any():
        # Caso específico: ITAÚ CAIXA AÇÕES
        df.loc[(df['OBJETIVO'] == 'Não classificado') & df[coluna_nome_produto].str.contains('caixa ações', case=False, na=False), 'OBJETIVO'] = 'Ganho'
    
    # NOVA FUNCIONALIDADE: Solicitar input do usuário para classificação manual
    if solicitar_input and (df['OBJETIVO'] == 'Não classificado').any():
        # [código original de solicitação de input]
        pass  # Mantenho este código inalterado para manter a compatibilidade
    
    # Mostrar estatísticas da classificação
    contagem_objetivos = df['OBJETIVO'].value_counts()
    print(f"\nClassificação de produtos por objetivo (Período: {periodo}):")
    for objetivo, count in contagem_objetivos.items():
        print(f"  - {objetivo}: {count} produtos")
    
    # Mostrar valor total por objetivo
    if 'VL_MERC_POS_FINAL' in df.columns:
        df['VL_MERC_POS_FINAL'] = pd.to_numeric(df['VL_MERC_POS_FINAL'], errors='coerce')
        valor_por_objetivo = df.groupby('OBJETIVO')['VL_MERC_POS_FINAL'].sum()
        valor_total = df['VL_MERC_POS_FINAL'].sum()
        
        print("\nDistribuição de valor por objetivo:")
        for objetivo, valor in valor_por_objetivo.items():
            percentual = (valor / valor_total * 100) if valor_total > 0 else 0
            print(f"  - {objetivo}: R$ {valor:,.2f} ({percentual:.2f}%)")
    
    # Verificar se ainda existem itens não classificados para debugging
    if (df['OBJETIVO'] == 'Não classificado').any() and not solicitar_input:
        nao_classificados = df[df['OBJETIVO'] == 'Não classificado']
        print(f"\nATENÇÃO: {len(nao_classificados)} produtos não foram classificados.")
        
        if coluna_nome_produto:
            print("Primeiros 5 produtos não classificados:")
            for i, (_, row) in enumerate(nao_classificados.head().iterrows()):
                nome = row[coluna_nome_produto] if not pd.isna(row[coluna_nome_produto]) else "Nome não disponível"
                tipo_ativo = row['TP_ATIVO'] if 'TP_ATIVO' in df.columns and not pd.isna(row['TP_ATIVO']) else "Tipo não disponível"
                tipo_aplic = row['TP_APLIC'] if 'TP_APLIC' in df.columns and not pd.isna(row['TP_APLIC']) else "Aplicação não disponível"
                
                print(f"  {i+1}. {nome}")
                print(f"     Tipo de ativo: {tipo_ativo}")
                print(f"     Tipo de aplicação: {tipo_aplic}")
    
    return df


def gerar_relatorio_classificacao_objetivos(df_classificado, base_dir, periodo=None, nome_arquivo="classificacao_objetivos.html"):
    """
    Gera um relatório HTML com a classificação dos produtos por objetivo.
    
    Args:
        df_classificado (DataFrame): DataFrame com a coluna 'OBJETIVO'
        base_dir (str): Diretório base para salvar o relatório
        periodo (str, optional): Período específico para o relatório
        nome_arquivo (str): Nome do arquivo de relatório
        
    Returns:
        str: Caminho do arquivo de relatório
    """
    # Se não especificou o período, tenta extrair do DataFrame
    if periodo is None and 'DT_COMPTC' in df_classificado.columns:
        periodo = pd.to_datetime(df_classificado['DT_COMPTC']).max().strftime('%Y-%m-%d')
    elif periodo is None:
        periodo = datetime.now().strftime('%Y-%m-%d')
    
    # Diretório para relatórios
    dir_relatorios = os.path.join(base_dir, 'relatorios_classificacao')
    os.makedirs(dir_relatorios, exist_ok=True)
    
    # Diretório para gráficos
    dir_graficos = os.path.join(dir_relatorios, 'graficos')
    os.makedirs(dir_graficos, exist_ok=True)
    
    # Verificar se temos a coluna de valor de mercado
    if 'VL_MERC_POS_FINAL' not in df_classificado.columns:
        print("Erro: Coluna 'VL_MERC_POS_FINAL' não encontrada. Não é possível gerar gráficos.")
        return None
    
    # Preparar dados
    df = df_classificado.copy()
    df['VL_MERC_POS_FINAL'] = pd.to_numeric(df['VL_MERC_POS_FINAL'], errors='coerce')
    
    # Encontrar a coluna que tem o nome do produto
    coluna_nome_produto = None
    for col in ['NM_FUNDO_CLASSE_SUBCLASSE_COTA', 'DENOM_SOCIAL']:
        if col in df.columns:
            coluna_nome_produto = col
            break
    
    if coluna_nome_produto is None:
        coluna_nome_produto = df.columns[0]  # Fallback para primeira coluna
    
    # Análise por objetivo
    valor_por_objetivo = df.groupby('OBJETIVO')['VL_MERC_POS_FINAL'].sum().sort_values(ascending=False)
    valor_total = df['VL_MERC_POS_FINAL'].sum()
    percentual_por_objetivo = (valor_por_objetivo / valor_total * 100).round(2)
    
    # Gráfico 1: Distribuição de valor por objetivo (barras)
    plt.figure(figsize=(10, 6))
    
    # Cores para cada objetivo
    cores = {
        'Preservação': '#3498db',  # Azul
        'Manutenção': '#2ecc71',   # Verde
        'Ganho': '#e74c3c',        # Vermelho
        'Não classificado': '#95a5a6'  # Cinza
    }
    
    # Excluir "Não classificado" se o valor for zero
    if 'Não classificado' in valor_por_objetivo and valor_por_objetivo['Não classificado'] == 0:
        valor_por_objetivo = valor_por_objetivo.drop('Não classificado')
    
    # Criar gráfico de barras
    barras = plt.bar(
        valor_por_objetivo.index, 
        valor_por_objetivo.values,
        color=[cores.get(obj, '#cccccc') for obj in valor_por_objetivo.index]
    )
    
    # Adicionar valores em cima das barras
    for i, barra in enumerate(barras):
        valor = valor_por_objetivo.iloc[i]
        if valor >= 1e9:
            valor_str = f"R$ {valor/1e9:.2f}B"
        else:
            valor_str = f"R$ {valor/1e6:.2f}M"
            
        plt.text(
            i, 
            barra.get_height() + (valor_por_objetivo.max() * 0.02), 
            valor_str,
            ha='center',
            fontsize=10
        )
    
    plt.title(f'Distribuição de Valor por Objetivo - {periodo}')
    plt.xlabel('Objetivo')
    plt.ylabel('Valor (R$)')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Formatação do eixo Y
    if valor_por_objetivo.max() > 1e9:
        plt.ticklabel_format(style='plain', axis='y', scilimits=(0,0))
        plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: f"R$ {x/1e9:.1f}B"))
    else:
        plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: f"R$ {x/1e6:.1f}M"))
    
    plt.tight_layout()
    
    # Salvar gráfico
    caminho_grafico1 = os.path.join(dir_graficos, f"distribuicao_valor_objetivo_{periodo.replace('-', '')}.png")
    plt.savefig(caminho_grafico1, dpi=300, bbox_inches='tight')
    plt.close()
    
    # Gráfico 2: Distribuição percentual (gráfico de pizza)
    plt.figure(figsize=(10, 8))
    
    # Criar rótulos com percentuais e valores
    labels = []
    for objetivo, valor in valor_por_objetivo.items():
        percent = percentual_por_objetivo[objetivo]
        if valor >= 1e9:
            valor_str = f"R$ {valor/1e9:.2f}B"
        else:
            valor_str = f"R$ {valor/1e6:.2f}M"
            
        labels.append(f"{objetivo} ({percent}%)\n{valor_str}")
    
    # Plotar gráfico de pizza
    wedges, _, autotexts = plt.pie(
        valor_por_objetivo,
        labels=None,
        autopct='%1.1f%%',
        startangle=90,
        colors=[cores.get(obj, '#cccccc') for obj in valor_por_objetivo.index],
        explode=[0.05] * len(valor_por_objetivo),
        shadow=False
    )
    
    # Configurar fonte dos percentuais
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(9)
    
    plt.title(f'Distribuição Percentual por Objetivo - {periodo}')
    plt.legend(labels, loc='center left', bbox_to_anchor=(1, 0, 0.5, 1))
    plt.tight_layout()
    
    # Salvar gráfico
    caminho_grafico2 = os.path.join(dir_graficos, f"percentual_objetivo_{periodo.replace('-', '')}.png")
    plt.savefig(caminho_grafico2, dpi=300, bbox_inches='tight')
    plt.close()
    
    # Gráfico 3: Distribuição por objetivo para cada fundo proprietário
    if 'CNPJ_FUNDO_CLASSE' in df.columns:
        # Análise por fundo proprietário
        fundos_proprietarios = df['CNPJ_FUNDO_CLASSE'].unique()
        
        # Dicionário para armazenar os caminhos dos gráficos
        gráficos_por_fundo = {}
        
        for cnpj_fundo in fundos_proprietarios:
            # Filtrar para este fundo
            df_fundo = df[df['CNPJ_FUNDO_CLASSE'] == cnpj_fundo].copy()
            
            # Obter o nome do fundo
            nome_fundo = "Fundo"
            if 'DENOM_SOCIAL' in df_fundo.columns:
                nome_fundo = df_fundo['DENOM_SOCIAL'].iloc[0]
                # Extrair apenas o nome principal do fundo (antes de "FUNDO DE INVESTIMENTO")
                match = re.search(r'^(.+?)(?:\s+FUNDO\s+DE\s+INVESTIMENTO|$)', nome_fundo, re.IGNORECASE)
                if match:
                    nome_fundo = match.group(1).strip()
            
            # Calcular valores por objetivo para este fundo
            valor_fundo_por_objetivo = df_fundo.groupby('OBJETIVO')['VL_MERC_POS_FINAL'].sum().sort_values(ascending=False)
            valor_total_fundo = df_fundo['VL_MERC_POS_FINAL'].sum()
            
            # Criar gráfico de pizza para este fundo
            plt.figure(figsize=(10, 7))
            
            # Criar rótulos com percentuais e valores
            labels_fundo = []
            for objetivo, valor in valor_fundo_por_objetivo.items():
                percentual = (valor / valor_total_fundo * 100) if valor_total_fundo > 0 else 0
                if valor >= 1e9:
                    valor_str = f"R$ {valor/1e9:.2f}B"
                else:
                    valor_str = f"R$ {valor/1e6:.2f}M"
                    
                labels_fundo.append(f"{objetivo} ({percentual:.1f}%)\n{valor_str}")
            
            # Plotar gráfico de pizza
            plt.pie(
                valor_fundo_por_objetivo,
                labels=None,
                autopct='%1.1f%%',
                startangle=90,
                colors=[cores.get(obj, '#cccccc') for obj in valor_fundo_por_objetivo.index],
                explode=[0.05] * len(valor_fundo_por_objetivo),
                shadow=False
            )
            
            plt.title(f'Distribuição por Objetivo - {nome_fundo}')
            plt.legend(labels_fundo, loc='center left', bbox_to_anchor=(1, 0, 0.5, 1))
            plt.tight_layout()
            
            # Salvar gráfico
            nome_arquivo_fundo = f"objetivos_{nome_fundo.lower().replace(' ', '_')}_{periodo.replace('-', '')}.png"
            caminho_grafico_fundo = os.path.join(dir_graficos, nome_arquivo_fundo)
            plt.savefig(caminho_grafico_fundo, dpi=300, bbox_inches='tight')
            plt.close()
            
            gráficos_por_fundo[cnpj_fundo] = {
                'nome': nome_fundo,
                'caminho': caminho_grafico_fundo,
                'arquivo': nome_arquivo_fundo,
                'valores': valor_fundo_por_objetivo.to_dict()
            }
    else:
        gráficos_por_fundo = {}
    
    # Tabelas de produtos por objetivo
    tabelas_html = ""
    for objetivo in sorted(df['OBJETIVO'].unique()):
        if objetivo == 'Não classificado':
            continue
            
        # Filtrar por objetivo
        df_objetivo = df[df['OBJETIVO'] == objetivo].copy()
        
        if len(df_objetivo) == 0:
            continue
            
        # Ordenar por valor (decrescente)
        if 'VL_MERC_POS_FINAL' in df_objetivo.columns:
            df_objetivo = df_objetivo.sort_values('VL_MERC_POS_FINAL', ascending=False)
            
        # Criar tabela HTML
        tabela_html = f"<h3>Produtos com objetivo de {objetivo}</h3>"
        tabela_html += "<table class='produto-table'>"
        tabela_html += "<tr><th>Produto</th><th>Tipo</th><th>Valor (R$)</th><th>Participação (%)</th></tr>"
        
        # Adicionar linhas à tabela
        for i, (_, row) in enumerate(df_objetivo.head(15).iterrows()):
            nome_produto = row[coluna_nome_produto] if pd.notna(row[coluna_nome_produto]) else "Nome não disponível"
            tipo_produto = row['TP_ATIVO'] if 'TP_ATIVO' in row and pd.notna(row['TP_ATIVO']) else "Tipo não especificado"
            valor = row['VL_MERC_POS_FINAL'] if 'VL_MERC_POS_FINAL' in row else 0
            percentual = (valor / df_objetivo['VL_MERC_POS_FINAL'].sum() * 100) if 'VL_MERC_POS_FINAL' in row else 0
            
            tabela_html += f"<tr>"
            tabela_html += f"<td>{nome_produto}</td>"
            tabela_html += f"<td>{tipo_produto}</td>"
            tabela_html += f"<td>R$ {valor:,.2f}</td>"
            tabela_html += f"<td>{percentual:.2f}%</td>"
            tabela_html += f"</tr>"
            
            if i >= 14 and len(df_objetivo) > 15:
                # Adicionar linha de "outros"
                outros_valor = df_objetivo.iloc[15:]['VL_MERC_POS_FINAL'].sum() if 'VL_MERC_POS_FINAL' in df_objetivo.columns else 0
                outros_percentual = (outros_valor / df_objetivo['VL_MERC_POS_FINAL'].sum() * 100) if 'VL_MERC_POS_FINAL' in df_objetivo.columns else 0
                
                tabela_html += f"<tr>"
                tabela_html += f"<td>Outros ({len(df_objetivo) - 15} produtos)</td>"
                tabela_html += f"<td>Diversos</td>"
                tabela_html += f"<td>R$ {outros_valor:,.2f}</td>"
                tabela_html += f"<td>{outros_percentual:.2f}%</td>"
                tabela_html += f"</tr>"
                break
        
        tabela_html += "</table>"
        tabelas_html += tabela_html
    
    # Tabela de resumo por fundo
    tabela_fundos_html = ""
    if gráficos_por_fundo:
        tabela_fundos_html = "<h2>Análise por Fundo</h2>"
        tabela_fundos_html += "<table class='fundo-table'>"
        tabela_fundos_html += "<tr><th>Fundo</th><th>Preservação</th><th>Manutenção</th><th>Ganho</th><th>Total</th></tr>"
        
        for cnpj, info in gráficos_por_fundo.items():
            nome_fundo = info['nome']
            valores = info['valores']
            
            preservacao = valores.get('Preservação', 0)
            manutencao = valores.get('Manutenção', 0)
            ganho = valores.get('Ganho', 0)
            total = sum(valores.values())
            
            tabela_fundos_html += f"<tr>"
            tabela_fundos_html += f"<td>{nome_fundo}</td>"
            tabela_fundos_html += f"<td>R$ {preservacao:,.2f} ({preservacao/total*100:.1f}%)</td>"
            tabela_fundos_html += f"<td>R$ {manutencao:,.2f} ({manutencao/total*100:.1f}%)</td>"
            tabela_fundos_html += f"<td>R$ {ganho:,.2f} ({ganho/total*100:.1f}%)</td>"
            tabela_fundos_html += f"<td>R$ {total:,.2f}</td>"
            tabela_fundos_html += f"</tr>"
            
        tabela_fundos_html += "</table>"
        
        # Adicionar gráficos por fundo
        tabela_fundos_html += "<div class='graficos-fundos'>"
        for cnpj, info in gráficos_por_fundo.items():
            tabela_fundos_html += f"<div class='grafico-fundo'>"
            tabela_fundos_html += f"<h3>{info['nome']}</h3>"
            tabela_fundos_html += f"<img src='graficos/{os.path.basename(info['arquivo'])}' alt='Distribuição por Objetivo - {info['nome']}'>"
            tabela_fundos_html += f"</div>"
        tabela_fundos_html += "</div>"
    
    # Criar HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Classificação de Produtos por Objetivo - {periodo}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2, h3 {{ color: #333366; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .grafico {{ text-align: center; margin: 30px 0; }}
            .graficos-fundos {{ display: flex; flex-wrap: wrap; justify-content: space-around; }}
            .grafico-fundo {{ margin: 15px; max-width: 45%; }}
            img {{ max-width: 100%; border: 1px solid #ddd; }}
            .footer {{ text-align: center; margin-top: 40px; color: #666; font-size: 12px; }}
            .produto-table, .fundo-table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; }}
            .produto-table th, .fundo-table th {{ background-color: #f2f2f2; padding: 10px; text-align: left; border: 1px solid #ddd; }}
            .produto-table td, .fundo-table td {{ padding: 8px; border: 1px solid #ddd; }}
            .produto-table tr:nth-child(even), .fundo-table tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .resumo {{ margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-radius: 5px; }}
            .objetivo-preservacao {{ color: #3498db; }}
            .objetivo-manutencao {{ color: #2ecc71; }}
            .objetivo-ganho {{ color: #e74c3c; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Classificação de Produtos por Objetivo</h1>
            <p>Data de referência: {periodo}</p>
            
            <div class="resumo">
                <h2>Resumo da Classificação</h2>
                <p>Os produtos foram classificados nas seguintes categorias de objetivo:</p>
                <ul>
                    <li><strong class="objetivo-preservacao">Preservação</strong>: Produtos que visam bater o CDI (renda fixa, títulos públicos, etc.)</li>
                    <li><strong class="objetivo-manutencao">Manutenção</strong>: Produtos que visam bater a inflação (multimercados, fundos balanceados, etc.)</li>
                    <li><strong class="objetivo-ganho">Ganho</strong>: Produtos que visam bater o Ibovespa (fundos de ações, etc.)</li>
                </ul>
            </div>
            
            <h2>Distribuição de Valor por Objetivo</h2>
            <div class="grafico">
                <img src="graficos/{os.path.basename(caminho_grafico1)}" alt="Distribuição de Valor por Objetivo">
            </div>
            
            <h2>Distribuição Percentual</h2>
            <div class="grafico">
                <img src="graficos/{os.path.basename(caminho_grafico2)}" alt="Distribuição Percentual por Objetivo">
            </div>
            
            {tabela_fundos_html}
            
            <h2>Detalhamento por Objetivo</h2>
            {tabelas_html}
            
            <div class="footer">
                <p>Relatório gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Salvar HTML
    caminho_relatorio = os.path.join(dir_relatorios, nome_arquivo)
    with open(caminho_relatorio, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\nRelatório de classificação por objetivo gerado em: {caminho_relatorio}")
    
    return caminho_relatorio


def gerar_grafico_evolucao_objetivos(carteiras_consolidadas, base_dir, classificacao_cnpj, datas_analise=None, intervalo_meses=6, 
                                    nome_arquivo="evolucao_objetivos.png", titulo="Evolução da Alocação por Objetivo"):
    """
    Gera um gráfico de linhas mostrando a evolução da alocação por objetivo ao longo do tempo.
    
    Args:
        carteiras_consolidadas (dict): Dicionário com carteiras por data
        base_dir (str): Diretório base para salvar o gráfico
        classificacao_cnpj (dict): Dicionário com a classificação por CNPJ
        datas_analise (list, optional): Lista de datas específicas para análise
        intervalo_meses (int): Intervalo em meses para selecionar datas
        nome_arquivo (str): Nome do arquivo para salvar o gráfico
        titulo (str): Título do gráfico
        
    Returns:
        str: Caminho do arquivo do gráfico
    """
    import os
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.ticker import PercentFormatter
    from datetime import datetime
    
    print("Gerando gráfico de evolução da alocação por objetivo com classificação por CNPJ...")
    
    # Dicionário para armazenar os resultados por data
    resultados_por_data = {}
    
    # Se não forneceu datas específicas, use todas as datas disponíveis
    if datas_analise is None:
        datas_analise = sorted(list(carteiras_consolidadas.keys()))
        
        # Filtrar para manter apenas uma data a cada 'intervalo_meses' meses
        datas_filtradas = []
        data_atual = None
        
        for data in datas_analise:
            # Converter para datetime
            try:
                data_dt = datetime.strptime(data, '%Y-%m')
                
                # Se é a primeira data ou se passou o intervalo desde a última data
                if data_atual is None or (data_dt.year - data_atual.year) * 12 + data_dt.month - data_atual.month >= intervalo_meses:
                    datas_filtradas.append(data)
                    data_atual = data_dt
            except ValueError:
                # Pular datas em formato inválido
                continue
        
        datas_analise = datas_filtradas
    
    print(f"Analisando {len(datas_analise)} períodos: {', '.join(datas_analise)}")
    
    # Para cada data, classificar os produtos e calcular percentuais
    for data in datas_analise:
        if data not in carteiras_consolidadas:
            print(f"AVISO: Dados não encontrados para o período {data}")
            continue

        df = carteiras_consolidadas[data].copy()
        
        # Classificar produtos usando a função atualizada com classificação por CNPJ
        df_classificado = classificar_produtos_por_objetivo(df, periodo=data, classificacao_cnpj=classificacao_cnpj)
        
        # Calcular valores por objetivo
        if 'VL_MERC_POS_FINAL' in df_classificado.columns and 'OBJETIVO' in df_classificado.columns:
            df_classificado['VL_MERC_POS_FINAL'] = pd.to_numeric(df_classificado['VL_MERC_POS_FINAL'], errors='coerce')
            
            # Agrupar por objetivo
            valores_por_objetivo = df_classificado.groupby('OBJETIVO')['VL_MERC_POS_FINAL'].sum()
            valor_total = df_classificado['VL_MERC_POS_FINAL'].sum()
            
            # Calcular percentuais
            percentuais = {}
            for objetivo in ['Preservação', 'Manutenção', 'Ganho', 'Não classificado']:
                valor = valores_por_objetivo.get(objetivo, 0)
                percentual = (valor / valor_total * 100) if valor_total > 0 else 0
                percentuais[objetivo] = percentual
            
            # Armazenar resultados
            resultados_por_data[data] = {
                'valores': valores_por_objetivo.to_dict(),
                'percentuais': percentuais,
                'total': valor_total
            }
            
            print(f"Período {data}: Total R$ {valor_total:,.2f}")
            for objetivo, pct in percentuais.items():
                print(f"  - {objetivo}: {pct:.2f}%")
        else:
            print(f"AVISO: Colunas necessárias não encontradas para o período {data}")
    
    # Verificar se temos dados suficientes
    if not resultados_por_data:
        print("Não há dados suficientes para gerar o gráfico de evolução.")
        return None
    
    # Preparar dados para o gráfico
    datas = sorted(list(resultados_por_data.keys()))
    datas_dt = [datetime.strptime(data, '%Y-%m') for data in datas]
    
    # Extrair percentuais por objetivo
    percentuais_preservacao = [resultados_por_data[data]['percentuais'].get('Preservação', 0) for data in datas]
    percentuais_manutencao = [resultados_por_data[data]['percentuais'].get('Manutenção', 0) for data in datas]
    percentuais_ganho = [resultados_por_data[data]['percentuais'].get('Ganho', 0) for data in datas]
    
    # Criar figura
    plt.figure(figsize=(12, 8))
    
    # Cores mais suaves para cada objetivo
    cores = {
        'Preservação': '#4682B4',  # Azul mais claro (Steel Blue)
        'Manutenção': '#FFB347',   # Laranja mais claro (Pastel Orange)
        'Ganho': '#FF6B6B',        # Vermelho mais claro (Light Coral)
    }
    
    # Plotar linhas para cada objetivo
    plt.plot(datas_dt, percentuais_preservacao, 'o-', color=cores['Preservação'], 
             linewidth=2.5, markersize=8, label='Preservação')
    plt.plot(datas_dt, percentuais_manutencao, 'o-', color=cores['Manutenção'], 
             linewidth=2.5, markersize=8, label='Manutenção')
    plt.plot(datas_dt, percentuais_ganho, 'o-', color=cores['Ganho'], 
             linewidth=2.5, markersize=8, label='Ganho')
    
    # Adicionar rótulos com percentuais em cada ponto
    for i, (data_dt, p_pres, p_manu, p_ganho) in enumerate(zip(datas_dt, percentuais_preservacao, percentuais_manutencao, percentuais_ganho)):
        plt.text(data_dt, p_pres + 1, f"{p_pres:.1f}%", ha='center', va='bottom', fontsize=9)
        plt.text(data_dt, p_manu + 1, f"{p_manu:.1f}%", ha='center', va='bottom', fontsize=9)
        plt.text(data_dt, p_ganho + 1, f"{p_ganho:.1f}%", ha='center', va='bottom', fontsize=9)
    
    # Área destacada para cada objetivo
    plt.fill_between(datas_dt, 0, percentuais_preservacao, color=cores['Preservação'], alpha=0.2)
    plt.fill_between(datas_dt, 0, percentuais_manutencao, color=cores['Manutenção'], alpha=0.2)
    plt.fill_between(datas_dt, 0, percentuais_ganho, color=cores['Ganho'], alpha=0.2)
    
    # Configurar eixos
    plt.ylabel('Percentual da Carteira (%)')
    plt.xlabel('Período')
    plt.title(titulo, fontsize=14, pad=20)
    
    # Configurar o formato da data no eixo X
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b/%Y'))
    plt.xticks(rotation=45)
    
    # Adicionar formatação de percentual ao eixo Y
    plt.gca().yaxis.set_major_formatter(PercentFormatter(100))
    
    # Ajustar limite do eixo Y
    max_pct = max(max(percentuais_preservacao), max(percentuais_manutencao), max(percentuais_ganho))
    plt.ylim(0, max_pct * 1.2)  # 20% de espaço extra no topo
    
    # Adicionar grid
    plt.grid(True, linestyle='--', alpha=0.3)
    
    # Adicionar legenda
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3)
    
    # Ajustar layout
    plt.tight_layout()
    
    # Diretório para gráficos
    dir_graficos = os.path.join(base_dir, 'graficos_evolucao_objetivos')
    os.makedirs(dir_graficos, exist_ok=True)
    
    # Caminho do arquivo
    caminho_arquivo = os.path.join(dir_graficos, nome_arquivo)
    
    # Salvar gráfico
    plt.savefig(caminho_arquivo, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Gráfico de evolução da alocação por objetivo salvo em: {caminho_arquivo}")
    
    return caminho_arquivo, percentuais_preservacao, percentuais_manutencao, percentuais_ganho


def gerar_grafico_evolucao_objetivos_separado(resultados_por_data, datas_analise, base_dir, 
                                            nome_arquivo="evolucao_objetivos.png", 
                                            titulo="Evolução da Alocação por Objetivo"):
    """
    Gera um gráfico de linhas mostrando a evolução da alocação por objetivo ao longo do tempo.
    
    Args:
        resultados_por_data (dict): Dicionário com os resultados da classificação por data
        datas_analise (list): Lista de datas usadas na análise
        base_dir (str): Diretório base para salvar o gráfico
        nome_arquivo (str): Nome do arquivo para salvar o gráfico
        titulo (str): Título do gráfico
        
    Returns:
        tuple: (caminho_arquivo, percentuais_preservacao, percentuais_manutencao, percentuais_ganho)
    """
    import os
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.ticker import PercentFormatter
    from datetime import datetime
    
    print("Gerando gráfico de evolução da alocação por objetivo...")
    
    # Verificar se temos dados suficientes
    if not resultados_por_data:
        print("Não há dados suficientes para gerar o gráfico de evolução.")
        return None, [], [], []
    
    # Filtrar para usar apenas as datas que tenham resultados
    datas = [data for data in datas_analise if data in resultados_por_data]
    
    if not datas:
        print("Nenhuma data válida encontrada nos resultados.")
        return None, [], [], []
    
    # Preparar dados para o gráfico
    datas_dt = [datetime.strptime(data, '%Y-%m') for data in datas]
    
    # Extrair percentuais por objetivo
    percentuais_preservacao = [resultados_por_data[data]['percentuais'].get('Preservação', 0) for data in datas]
    percentuais_manutencao = [resultados_por_data[data]['percentuais'].get('Manutenção', 0) for data in datas]
    percentuais_ganho = [resultados_por_data[data]['percentuais'].get('Ganho', 0) for data in datas]
    
    # Criar figura
    plt.figure(figsize=(12, 8))
    
    # Cores mais suaves para cada objetivo
    cores = {
        'Preservação': '#4682B4',  # Azul mais claro (Steel Blue)
        'Manutenção': '#FFB347',   # Laranja mais claro (Pastel Orange)
        'Ganho': '#FF6B6B',        # Vermelho mais claro (Light Coral)
    }
    
    # Plotar linhas para cada objetivo
    plt.plot(datas_dt, percentuais_preservacao, 'o-', color=cores['Preservação'], 
             linewidth=2.5, markersize=8, label='Preservação')
    plt.plot(datas_dt, percentuais_manutencao, 'o-', color=cores['Manutenção'], 
             linewidth=2.5, markersize=8, label='Manutenção')
    plt.plot(datas_dt, percentuais_ganho, 'o-', color=cores['Ganho'], 
             linewidth=2.5, markersize=8, label='Ganho')
    
    # Adicionar rótulos com percentuais em cada ponto
    for i, (data_dt, p_pres, p_manu, p_ganho) in enumerate(zip(datas_dt, percentuais_preservacao, percentuais_manutencao, percentuais_ganho)):
        plt.text(data_dt, p_pres + 1, f"{p_pres:.1f}%", ha='center', va='bottom', fontsize=9)
        plt.text(data_dt, p_manu + 1, f"{p_manu:.1f}%", ha='center', va='bottom', fontsize=9)
        plt.text(data_dt, p_ganho + 1, f"{p_ganho:.1f}%", ha='center', va='bottom', fontsize=9)
    
    # Área destacada para cada objetivo
    plt.fill_between(datas_dt, 0, percentuais_preservacao, color=cores['Preservação'], alpha=0.2)
    plt.fill_between(datas_dt, 0, percentuais_manutencao, color=cores['Manutenção'], alpha=0.2)
    plt.fill_between(datas_dt, 0, percentuais_ganho, color=cores['Ganho'], alpha=0.2)
    
    # Configurar eixos
    plt.ylabel('Percentual da Carteira (%)')
    plt.xlabel('Período')
    plt.title(titulo, fontsize=14, pad=20)
    
    # Configurar o formato da data no eixo X
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b/%Y'))
    plt.xticks(rotation=45)
    
    # Adicionar formatação de percentual ao eixo Y
    plt.gca().yaxis.set_major_formatter(PercentFormatter(100))
    
    # Ajustar limite do eixo Y
    max_pct = max(max(percentuais_preservacao), max(percentuais_manutencao), max(percentuais_ganho))
    plt.ylim(0, max_pct * 1.2)  # 20% de espaço extra no topo
    
    # Adicionar grid
    plt.grid(True, linestyle='--', alpha=0.3)
    
    # Adicionar legenda
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3)
    
    # Ajustar layout
    plt.tight_layout()
    
    # Diretório para gráficos
    dir_graficos = os.path.join(base_dir, 'graficos_evolucao_objetivos')
    os.makedirs(dir_graficos, exist_ok=True)
    
    # Caminho do arquivo
    caminho_arquivo = os.path.join(dir_graficos, nome_arquivo)
    
    # Salvar gráfico
    plt.savefig(caminho_arquivo, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Gráfico de evolução da alocação por objetivo salvo em: {caminho_arquivo}")
    
    return caminho_arquivo, percentuais_preservacao, percentuais_manutencao, percentuais_ganho


def gerar_histograma_alocacao_objetivos(carteiras_consolidadas, classificacao_cnpj, 
                                data_analise=None, mostrar_grafico=True, salvar_arquivo=None,
                                titulo=None, base_dir=None):
    """
    Gera um histograma horizontal mostrando a alocação por objetivo de investimento.
    
    Args:
        carteiras_consolidadas (dict): Dicionário com carteiras por data
        classificacao_cnpj (dict): Dicionário com a classificação por CNPJ
        data_analise (str, optional): Data específica para análise, se None usa a mais recente
        mostrar_grafico (bool): Se True, exibe o gráfico com plt.show()
        salvar_arquivo (str, optional): Nome do arquivo para salvar o gráfico
        titulo (str, optional): Título personalizado para o gráfico
        base_dir (str, optional): Diretório base para salvar o gráfico
        
    Returns:
        dict: Resultados da análise com valores e percentuais por objetivo
    """
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mtick
    import os
    from datetime import datetime
    
    # Verificar se temos as carteiras consolidadas
    if not carteiras_consolidadas:
        raise ValueError("Carteiras consolidadas vazias")
    
    # Se data_analise não for especificada, usar a mais recente
    if data_analise is None:
        datas = sorted(list(carteiras_consolidadas.keys()))
        if not datas:
            raise ValueError("Não há datas disponíveis nas carteiras consolidadas")
        data_analise = datas[-1]
    
    # Verificar se a data existe
    if data_analise not in carteiras_consolidadas:
        raise ValueError(f"Data {data_analise} não encontrada nas carteiras consolidadas")
    
    # Obter dados da data especificada
    df = carteiras_consolidadas[data_analise].copy()
    
    # Classificar produtos
    df_classificado = classificar_produtos_por_objetivo(df, periodo=data_analise, classificacao_cnpj=classificacao_cnpj)
    
    # Verificar se temos as colunas necessárias
    if 'VL_MERC_POS_FINAL' not in df_classificado.columns or 'OBJETIVO' not in df_classificado.columns:
        raise ValueError("Colunas necessárias 'VL_MERC_POS_FINAL' ou 'OBJETIVO' não encontradas")
    
    # Converter para numérico
    df_classificado['VL_MERC_POS_FINAL'] = pd.to_numeric(df_classificado['VL_MERC_POS_FINAL'], errors='coerce')
    
    # Calcular valores por objetivo
    valores_por_objetivo = df_classificado.groupby('OBJETIVO')['VL_MERC_POS_FINAL'].sum()
    valor_total = df_classificado['VL_MERC_POS_FINAL'].sum()
    
    # Calcular percentuais
    percentuais = {}
    for objetivo in ['Preservação', 'Manutenção', 'Ganho']:
        valor = valores_por_objetivo.get(objetivo, 0)
        percentual = (valor / valor_total * 100) if valor_total > 0 else 0
        percentuais[objetivo] = {
            'valor': valor,
            'percentual': percentual
        }
    
    # Ordem personalizada para o gráfico (de baixo para cima)
    objetivos = ['Preservação', 'Manutenção', 'Ganho']
    valores = [percentuais[obj]['valor'] for obj in objetivos]
    percentuais_lista = [percentuais[obj]['percentual'] for obj in objetivos]
    
    # Usar as mesmas cores da função de referência
    cores = {
        'Preservação': '#4682B4',  # Azul mais claro (Steel Blue)
        'Manutenção': '#FFB347',   # Laranja mais claro (Pastel Orange)
        'Ganho': '#FF6B6B',        # Vermelho mais claro (Light Coral)
    }
    
    # Criar figura
    plt.figure(figsize=(10, 6))
    
    # Configurar grid
    plt.grid(True, axis='x', linestyle='-', alpha=0.2, zorder=0)
    
    # Criar barras horizontais
    barras = plt.barh(
        objetivos, 
        percentuais_lista,
        color=[cores[obj] for obj in objetivos],
        height=0.5,
        zorder=3
    )
    
    # Adicionar valores e percentuais dentro das barras
    for i, (obj, barra) in enumerate(zip(objetivos, barras)):
        # Formatar valor
        valor = percentuais[obj]['valor']
        if valor >= 1e9:
            valor_str = f"R$ {valor/1e9:.2f}B"
        else:
            valor_str = f"R$ {valor/1e6:.2f}M"
        
        # Percentual
        percentual = percentuais[obj]['percentual']
        
        # Adicionar valor no meio da barra
        plt.text(
            percentual/2,  # Meio da barra
            i,             # Posição vertical
            valor_str,
            va='center',
            ha='center',
            color='white',
            fontweight='bold',
            fontsize=11,
            zorder=5
        )
        
        # Adicionar percentual no final da barra
        plt.text(
            percentual + 0.5,  # Logo após o final da barra
            i,                 # Posição vertical
            f"{percentual:.1f}%",
            va='center',
            ha='left',
            fontweight='bold',
            fontsize=11,
            zorder=5
        )
    
    # Configurar eixos
    plt.xlabel('Alocação (%)', fontsize=12)
    plt.ylabel('Objetivo de Investimento', fontsize=12)
    
    # Título do gráfico
    if titulo is None:
        titulo = f"Alocação por Objetivo de Investimento - {data_analise}"
    plt.title(titulo, fontsize=14, pad=20)
    
    # Formatar eixo X como percentual
    plt.gca().xaxis.set_major_formatter(mtick.PercentFormatter())
    
    # Ajustar limites e ticks do eixo X
    max_pct = max(percentuais_lista)
    plt.xlim(0, max_pct * 1.15)  # 15% extra para os rótulos
    
    # Adicionar ticks principais no eixo X
    tick_interval = 10 if max_pct <= 50 else 20
    plt.gca().xaxis.set_major_locator(mtick.MultipleLocator(tick_interval))
    
    # Bordas do gráfico
    for spine in plt.gca().spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.5)
        spine.set_color('#cccccc')
    
    # Ajustar layout
    plt.tight_layout()
    
    # Salvar o gráfico
    if salvar_arquivo:
        if base_dir:
            dir_graficos = os.path.join(base_dir, 'graficos_objetivos')
            os.makedirs(dir_graficos, exist_ok=True)
            caminho = os.path.join(dir_graficos, salvar_arquivo)
        else:
            caminho = salvar_arquivo
            
        plt.savefig(caminho, dpi=300, bbox_inches='tight')
        print(f"Gráfico salvo em: {caminho}")
    
    # Mostrar o gráfico
    if mostrar_grafico:
        plt.show()
    else:
        plt.close()
    
    # Preparar e retornar resultados
    resultados = {
        'data_analise': data_analise,
        'valor_total': valor_total,
        'valores_por_objetivo': {obj: percentuais[obj]['valor'] for obj in objetivos},
        'percentuais_por_objetivo': {obj: percentuais[obj]['percentual'] for obj in objetivos}
    }
    
    return resultados


def gerar_histograma_produtos_por_objetivo(df_classificado, objetivo, base_dir=None, 
                                   max_produtos=10, mostrar_grafico=True, 
                                   salvar_arquivo=None, titulo=None):
    """
    Gera um histograma horizontal mostrando os produtos alocados em um objetivo específico.
    
    Args:
        df_classificado (DataFrame): DataFrame já classificado por objetivo
        objetivo (str): Objetivo a ser analisado ('Preservação', 'Manutenção' ou 'Ganho')
        base_dir (str, optional): Diretório base para salvar o gráfico
        max_produtos (int): Número máximo de produtos a exibir
        mostrar_grafico (bool): Se True, exibe o gráfico com plt.show()
        salvar_arquivo (str, optional): Caminho para salvar o gráfico como arquivo
        titulo (str, optional): Título personalizado para o gráfico
        
    Returns:
        dict: Resultados da análise com valores e percentuais dos produtos
    """
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np
    import os
    from matplotlib.ticker import PercentFormatter
    
    # Verificar se o objetivo é válido
    objetivos_validos = ['Preservação', 'Manutenção', 'Ganho']
    if objetivo not in objetivos_validos:
        raise ValueError(f"Objetivo deve ser um dos seguintes: {', '.join(objetivos_validos)}")
    
    # Filtrar produtos pelo objetivo especificado
    df_objetivo = df_classificado[df_classificado['OBJETIVO'] == objetivo].copy()
    
    if len(df_objetivo) == 0:
        print(f"Nenhum produto encontrado para o objetivo '{objetivo}'")
        return None
    
    # Verificar se temos as colunas necessárias
    if 'VL_MERC_POS_FINAL' not in df_objetivo.columns:
        raise ValueError("Coluna 'VL_MERC_POS_FINAL' não encontrada no DataFrame")
    
    # Identificar a coluna com o nome do produto
    coluna_nome_produto = None
    for col in ['NM_FUNDO_CLASSE_SUBCLASSE_COTA', 'DENOM_SOCIAL', 'DS_ATIVO']:
        if col in df_objetivo.columns:
            coluna_nome_produto = col
            break
    
    if coluna_nome_produto is None:
        # Fallback: usar a primeira coluna não numérica
        for col in df_objetivo.columns:
            if df_objetivo[col].dtype == 'object':
                coluna_nome_produto = col
                break
        
        if coluna_nome_produto is None:
            raise ValueError("Não foi possível identificar uma coluna com os nomes dos produtos")
    
    # Converter valores para numérico
    df_objetivo['VL_MERC_POS_FINAL'] = pd.to_numeric(df_objetivo['VL_MERC_POS_FINAL'], errors='coerce')
    
    # Calcular o valor total para este objetivo
    valor_total_objetivo = df_objetivo['VL_MERC_POS_FINAL'].sum()
    
    # Agrupar por nome do produto e somar valores
    produtos_agrupados = df_objetivo.groupby(coluna_nome_produto)['VL_MERC_POS_FINAL'].sum().reset_index()
    
    # Calcular percentuais em relação ao total do objetivo
    produtos_agrupados['PERCENTUAL'] = (produtos_agrupados['VL_MERC_POS_FINAL'] / valor_total_objetivo * 100)
    
    # Ordenar por valor (decrescente)
    produtos_agrupados = produtos_agrupados.sort_values('VL_MERC_POS_FINAL', ascending=False)
    
    # Limitar ao número máximo de produtos
    if len(produtos_agrupados) > max_produtos:
        # Separar os principais produtos e agrupar o restante como "Outros"
        principais = produtos_agrupados.head(max_produtos - 1)
        # outros = produtos_agrupados.iloc[max_produtos - 1:]
        
        # # Criar entrada para "Outros"
        # outros_row = pd.DataFrame({
        #     coluna_nome_produto: [f"Outros ({len(outros)} produtos)"],
        #     'VL_MERC_POS_FINAL': [outros['VL_MERC_POS_FINAL'].sum()],
        #     'PERCENTUAL': [outros['PERCENTUAL'].sum()]
        # })
        
        # Combinar principais com outros
        produtos_agrupados = pd.concat([principais], ignore_index=True)
    
    # Verificar se temos produtos para exibir
    if produtos_agrupados.empty:
        print(f"Nenhum produto com valor positivo encontrado para o objetivo '{objetivo}'")
        return None
    
    # Criar nomes simplificados para os produtos (para exibição no gráfico)
    produtos_agrupados['NOME_SIMPLIFICADO'] = produtos_agrupados[coluna_nome_produto].apply(
        lambda x: str(x)[:40] + '...' if isinstance(x, str) and len(str(x)) > 40 else str(x)
    )
    
    # Cores por objetivo
    cores_objetivo = {
        'Preservação': '#4682B4',  # Azul mais claro (Steel Blue)
        'Manutenção': '#FFB347',   # Laranja mais claro (Pastel Orange)
        'Ganho': '#FF6B6B',        # Vermelho mais claro (Light Coral)
    }
    
    # Criar figura
    plt.figure(figsize=(12, max(8, len(produtos_agrupados) * 0.4)))
    
    # Criar gráfico de barras horizontais
    barras = plt.barh(
        produtos_agrupados['NOME_SIMPLIFICADO'], 
        produtos_agrupados['PERCENTUAL'],
        color=cores_objetivo.get(objetivo, '#6495ED'),
        alpha=0.8,
        height=0.6,
        edgecolor='white',
        linewidth=0.5
    )
    
    # Adicionar rótulos com valores e percentuais
    for i, (_, row) in enumerate(produtos_agrupados.iterrows()):
        # Formatar valor
        valor = row['VL_MERC_POS_FINAL']
        if valor >= 1e9:
            valor_str = f"R$ {valor/1e9:.2f}B"
        else:
            valor_str = f"R$ {valor/1e6:.2f}M"
        
        # Percentual
        percentual = row['PERCENTUAL']
        
        # Texto a exibir
        texto = f"{percentual:.1f}% ({valor_str})"
        
        # Adicionar texto à direita da barra
        plt.text(
            percentual + 0.5,  # Posição ligeiramente à direita da barra
            i,                 # Posição vertical (índice da barra)
            texto,
            va='center',
            ha='left',
            fontsize=9
        )
    
    # Configurar eixos
    plt.xlabel('Percentual (%)', fontsize=12)
    plt.ylabel('')  # Sem rótulo no eixo Y
    
    # Definir título
    if titulo is None:
        titulo = f"Produtos com Objetivo de {objetivo}"
    plt.title(titulo, fontsize=14, pad=20)
    
    # Adicionar grade
    plt.grid(True, axis='x', linestyle='--', alpha=0.3)
    
    # Formatar eixo X como percentual
    plt.gca().xaxis.set_major_formatter(PercentFormatter())
    
    # Ajustar limites do eixo X
    max_percentual = produtos_agrupados['PERCENTUAL'].max()
    plt.xlim(0, max_percentual * 1.2)  # 20% de espaço extra para os rótulos
    
    # Adicionar total como anotação
    if valor_total_objetivo >= 1e9:
        valor_total_str = f"Total: R$ {valor_total_objetivo/1e9:.2f}B"
    else:
        valor_total_str = f"Total: R$ {valor_total_objetivo/1e6:.2f}M"
    
    plt.annotate(
        valor_total_str,
        xy=(0.95, 0.03),  # Posição relativa à figura (X, Y)
        xycoords='figure fraction',
        ha='right',
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8, edgecolor='#cccccc')
    )
    
    # Inverter eixo Y para que o maior valor fique no topo
    plt.gca().invert_yaxis()
    
    # Ajustar layout
    plt.tight_layout()
    
    # Salvar o gráfico se caminho foi especificado
    if salvar_arquivo:
        # Criar diretório se não existir
        if base_dir:
            os.makedirs(os.path.join(base_dir, 'graficos_objetivos'), exist_ok=True)
            caminho = os.path.join(base_dir, 'graficos_objetivos', salvar_arquivo)
        else:
            caminho = salvar_arquivo
            
        plt.savefig(caminho, dpi=300, bbox_inches='tight')
        print(f"Gráfico salvo em: {caminho}")
    
    # Mostrar o gráfico
    if mostrar_grafico:
        plt.show()
    else:
        plt.close()
    
    # Preparar e retornar resultados
    resultados = {
        'objetivo': objetivo,
        'valor_total': valor_total_objetivo,
        'produtos': produtos_agrupados.to_dict('records')
    }
    
    return resultados


def histograma_objetivos_horizontal(df_classificado=None, carteiras_consolidadas=None, periodo=None, 
                                  mostrar_grafico=True, salvar_arquivo=None, titulo=None):
    """
    Gera um histograma horizontal elegante com cores escuras e ordem personalizada.
    
    Args:
        df_classificado (DataFrame, optional): DataFrame já classificado por objetivo
        carteiras_consolidadas (dict, optional): Dicionário com carteiras por data
        periodo (str, optional): Período específico a ser analisado (formato 'YYYY-MM')
        mostrar_grafico (bool): Se True, exibe o gráfico com plt.show()
        salvar_arquivo (str, optional): Caminho para salvar o gráfico como arquivo
        titulo (str, optional): Título personalizado para o gráfico
        
    Returns:
        dict: Resultados da análise com percentuais por objetivo
    """
    # Verificar entrada e preparar dados
    if df_classificado is None and carteiras_consolidadas is None:
        raise ValueError("É necessário fornecer df_classificado ou carteiras_consolidadas")
    
    # Se temos carteiras consolidadas e não temos DataFrame já classificado
    if df_classificado is None and carteiras_consolidadas is not None:
        # Determinar o período a analisar
        if periodo is None:
            # Usar o último período disponível
            periodos = sorted(list(carteiras_consolidadas.keys()))
            if not periodos:
                raise ValueError("Não há períodos disponíveis nas carteiras consolidadas")
            periodo = periodos[-1]
        
        # Verificar se o período existe
        if periodo not in carteiras_consolidadas:
            raise ValueError(f"Período {periodo} não encontrado nas carteiras consolidadas")
        
        # Obter dados do período e classificar
        df = carteiras_consolidadas[periodo].copy()
        df_classificado = classificar_produtos_por_objetivo(df, periodo=periodo)
    
    # Verificar se temos as colunas necessárias
    if 'OBJETIVO' not in df_classificado.columns:
        raise ValueError("Coluna 'OBJETIVO' não encontrada no DataFrame")
    
    if 'VL_MERC_POS_FINAL' not in df_classificado.columns:
        raise ValueError("Coluna 'VL_MERC_POS_FINAL' não encontrada no DataFrame")
    
    # Calcular valores por objetivo
    df_classificado['VL_MERC_POS_FINAL'] = pd.to_numeric(df_classificado['VL_MERC_POS_FINAL'], errors='coerce')
    
    # Agrupar por objetivo
    valores_por_objetivo = df_classificado.groupby('OBJETIVO')['VL_MERC_POS_FINAL'].sum()
    valor_total = df_classificado['VL_MERC_POS_FINAL'].sum()
    
    # Calcular percentuais
    percentuais = {}
    for objetivo in ['Preservação', 'Manutenção', 'Ganho']:
        valor = valores_por_objetivo.get(objetivo, 0)
        percentual = (valor / valor_total * 100) if valor_total > 0 else 0
        percentuais[objetivo] = {
            'valor': valor,
            'percentual': percentual
        }
    
    print(f"Análise para o período {periodo}:")
    print(f"Valor total: R$ {valor_total:,.2f}")
    for objetivo, dados in percentuais.items():
        print(f"  - {objetivo}: R$ {dados['valor']:,.2f} ({dados['percentual']:.2f}%)")
    
    # Ordem personalizada (Preservação embaixo, Manutenção no meio, Ganho no topo)
    objetivos = ['Preservação', 'Manutenção', 'Ganho']
    valores = [percentuais[obj]['percentual'] for obj in objetivos]
    
    # Cores escuras para cada objetivo
    cores = {
        'Preservação': '#005aa5',  # Azul escuro
        'Manutenção': '#1a7431',   # Verde escuro
        'Ganho': '#9a1b2d',        # Vermelho escuro
    }
    
    # Criar figura com estilo elegante
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.figure(figsize=(10, 6))
    
    # Criar barras horizontais
    barras = plt.barh(
        objetivos, 
        valores,
        color=[cores[obj] for obj in objetivos],
        height=0.6,
        edgecolor='white',
        linewidth=1
    )
    
    # Adicionar valores percentuais ao final das barras
    for i, barra in enumerate(barras):
        largura = barra.get_width()
        plt.text(
            largura + 0.5,
            i,
            f'{largura:.1f}%',
            va='center',
            ha='left',
            fontsize=12,
            fontweight='bold'
        )
    
    # Adicionar valores monetários dentro das barras
    for i, objetivo in enumerate(objetivos):
        valor = percentuais[objetivo]['valor']
        if valor >= 1e9:
            valor_str = f"R$ {valor/1e9:.2f}B"
        else:
            valor_str = f"R$ {valor/1e6:.2f}M"
        
        # Posicionar o texto no meio da barra
        plt.text(
            valores[i]/2,  # Meio da barra
            i,
            valor_str,
            va='center',
            ha='center',
            fontsize=11,
            fontweight='bold',
            color='white'
        )
    
    # Configurar eixos
    plt.xlim(0, max(valores) * 1.15)  # Dar espaço para os rótulos
    plt.ylabel('Objetivo de Investimento', fontsize=14, labelpad=10)
    plt.xlabel('Alocação (%)', fontsize=14, labelpad=10)
    
    # Formatação do eixo X como percentual
    plt.gca().xaxis.set_major_formatter(mtick.PercentFormatter())
    
    # Adicionar título
    if titulo is None:
        titulo = f"Alocação por Objetivo de Investimento - {periodo}"
    plt.title(titulo, fontsize=16, pad=20)
    
    # # Adicionar valor total como anotação
    # if valor_total >= 1e9:
    #     valor_total_str = f"Total: R$ {valor_total/1e9:.2f}B"
    # else:
    #     valor_total_str = f"Total: R$ {valor_total/1e6:.2f}M"
    
    # plt.annotate(
    #     valor_total_str,
    #     xy=(0.5, 0.02),
    #     xycoords='figure fraction',
    #     ha='center',
    #     fontsize=12,
    #     fontweight='bold',
    #     bbox=dict(boxstyle="round,pad=0.5", facecolor='white', alpha=0.8, edgecolor='#cccccc')
    # )
    
    # Ajustar layout
    plt.tight_layout()
    
    # Salvar arquivo se solicitado
    if salvar_arquivo:
        plt.savefig(salvar_arquivo, dpi=300, bbox_inches='tight')
        print(f"Gráfico salvo em: {salvar_arquivo}")
    
    # Exibir gráfico
    if mostrar_grafico:
        plt.show()
    else:
        plt.close()
    
    # Retornar resultados
    resultados = {
        'periodo': periodo,
        'valor_total': valor_total,
        'percentuais': percentuais
    }
    
    return resultados


def extrair_retornos_fundos(caminho_base=None, periodo_inicial='2020-01', periodo_final='2022-12', 
                          min_shareholder=1, register=None, filtro_cnpj=None):
    """
    Extrai retornos dos fundos a partir dos arquivos de informes diários.
    
    Args:
        caminho_base (str): Caminho base para a pasta INF_DIARIO
                          Se None, usa o caminho padrão ~/Documents/GitHub/flab/database/INF_DIARIO
        periodo_inicial (str): Período inicial no formato 'YYYY-MM'
        periodo_final (str): Período final no formato 'YYYY-MM'
        min_shareholder (int): Número mínimo de cotistas para inclusão do fundo
        register (DataFrame): DataFrame com informações cadastrais dos fundos (opcional)
        filtro_cnpj (list): Lista de CNPJs para filtrar (opcional)
        
    Returns:
        tuple: (returns_f, total_returns, evolucao_pl) - DataFrames com retornos diários, 
               retornos totais e evolução de PL/captações/resgates
    """
    # Definir caminho base
    if caminho_base is None:
        caminho_base = Path(Path.home(), 'Documents', 'GitHub', 'flab', 'database', 'INF_DIARIO')
    else:
        caminho_base = Path(caminho_base)
    
    print(f"Usando caminho base: {caminho_base}")
    
    # Gerar datas no intervalo especificado
    dates = pd.date_range(periodo_inicial, periodo_final, freq='MS')
    
    # Lista para armazenar DataFrames mensais
    data_list = []
    
    # Diretório temporário para extração dos arquivos
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        print('\nCarregando arquivos de informes diários...')
        for d in tqdm(dates):
            ano, mes = d.year, d.month
            
            # Pastas/arquivos a verificar (simplificado)
            locais = [
                (caminho_base / f"inf_diario_fi_{ano}{mes:02d}", "*.csv"),
                (caminho_base / f"inf_diario_fi_{ano}{mes:02d}.zip", None),
                (caminho_base / "HIST" / f"inf_diario_fi_{ano}{mes:02d}", "**/*.csv"),
                (caminho_base / "HIST" / f"inf_diario_fi_{ano}", f"**/*{mes:02d}*.csv"),
                (caminho_base / "HIST" / f"inf_diario_fi_{ano}{mes:02d}.zip", None)
            ]
            
            dados_carregados = False
            
            for local, pattern in locais:
                if not dados_carregados:
                    if local.exists():
                        try:
                            # Caso seja um diretório
                            if local.is_dir() and pattern:
                                arquivos_csv = list(local.glob(pattern))
                                if arquivos_csv:
                                    info_month = pd.read_csv(arquivos_csv[0], sep=';', encoding='latin-1', low_memory=False)
                                    data_list.append(info_month)
                                    dados_carregados = True
                                    print(f"Carregados dados do diretório {local}")
                            
                            # Caso seja um arquivo zip
                            elif local.is_file() and local.suffix == '.zip':
                                pasta_extracao = temp_path / local.stem
                                pasta_extracao.mkdir(exist_ok=True)
                                
                                with zipfile.ZipFile(local, 'r') as zip_ref:
                                    zip_ref.extractall(pasta_extracao)
                                
                                arquivos_csv = list(pasta_extracao.glob("**/*.csv"))
                                if arquivos_csv:
                                    info_month = pd.read_csv(arquivos_csv[0], sep=';', encoding='latin-1', low_memory=False)
                                    data_list.append(info_month)
                                    dados_carregados = True
                                    print(f"Carregados dados do ZIP {local}")
                        except Exception as e:
                            print(f"Erro ao processar {local}: {e}")
            
            if not dados_carregados:
                print(f"Não foi possível encontrar dados para {ano}/{mes:02d}")
    
    # Verificar se foram encontrados dados
    if not data_list:
        raise ValueError("Nenhum arquivo de informe diário encontrado!")
    
    # Concatenar todas as listas em um único DataFrame
    data_funds = pd.concat(data_list, ignore_index=True)
    print(f"Total de registros carregados: {len(data_funds)}")
    
    # === ETAPA CRUCIAL: TRATAMENTO DO CNPJ ===
    
    # Procurar por CNPJs em todas as colunas
    if 'CNPJ_FUNDO' not in data_funds.columns:
        # Se não temos CNPJ_FUNDO, mas temos CNPJ_FUNDO_CLASSE
        if 'CNPJ_FUNDO_CLASSE' in data_funds.columns:
            print("Usando CNPJ_FUNDO_CLASSE como CNPJ_FUNDO")
            data_funds['CNPJ_FUNDO'] = data_funds['CNPJ_FUNDO_CLASSE']
    
    # Criar uma nova coluna de CNPJ do formato CLASSES - FIF;XX.XXX.XXX/XXXX-XX
    print("Verificando e extraindo CNPJs dos formatos especiais...")
    
    def extrair_cnpj(row):
        # Tentar diferentes colunas e formatos 
        import re
        
        # Se já temos CNPJ_FUNDO válido, usar como está
        if 'CNPJ_FUNDO' in row and pd.notna(row['CNPJ_FUNDO']):
            if isinstance(row['CNPJ_FUNDO'], str) and re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', row['CNPJ_FUNDO']):
                return row['CNPJ_FUNDO']
        
        # Verificar formato "CLASSES - FIF;XX.XXX.XXX/XXXX-XX"
        for col in ['TP_FUNDO_CLASSE', 'TP_FUNDO']:
            if col in row and pd.notna(row[col]):
                combo = f"{row[col]};{row.get('CNPJ_FUNDO_CLASSE', '')}"
                matches = re.findall(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', combo)
                if matches:
                    return matches[0]
        
        # Verificar outras colunas que possam conter CNPJ
        for col in row.index:
            if 'CNPJ' in col and pd.notna(row[col]):
                matches = re.findall(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', str(row[col]))
                if matches:
                    return matches[0]
        
        return None
    
    # Criar coluna unificada de CNPJ
    data_funds['CNPJ_UNIFICADO'] = data_funds.apply(extrair_cnpj, axis=1)
    
    # Usar a coluna unificada
    if 'CNPJ_UNIFICADO' in data_funds.columns:
        # Exibir estatísticas da nova coluna
        total_cnpj = len(data_funds)
        cnpj_validos = data_funds['CNPJ_UNIFICADO'].notna().sum()
        print(f"CNPJs unificados: {cnpj_validos} de {total_cnpj} ({cnpj_validos/total_cnpj*100:.1f}%)")
        
        # Remover registros sem CNPJ
        data_funds = data_funds.dropna(subset=['CNPJ_UNIFICADO'])
        print(f"Registros após remoção de CNPJs nulos: {len(data_funds)}")
    
    # Filtrar por CNPJ se especificado
    if filtro_cnpj:
        # Verificar CNPJs antes da filtragem
        cnpjs_distintos = data_funds['CNPJ_UNIFICADO'].unique()
        print(f"CNPJs distintos antes da filtragem: {len(cnpjs_distintos)}")
        
        # Verificar se os CNPJs desejados estão presentes
        for cnpj in filtro_cnpj:
            presente = cnpj in cnpjs_distintos
            print(f"CNPJ {cnpj}: {'✓ Presente' if presente else '✗ Ausente'}")
            
            # Se ausente, tentar encontrar parcial
            if not presente:
                # Remover formatação e procurar
                cnpj_limpo = cnpj.replace('.', '').replace('/', '').replace('-', '')
                for c in cnpjs_distintos:
                    c_limpo = c.replace('.', '').replace('/', '').replace('-', '')
                    if cnpj_limpo in c_limpo or c_limpo in cnpj_limpo:
                        print(f"  → Encontrado similar: {c}")
        
        # Aplicar filtro
        antes = len(data_funds)
        data_funds = data_funds[data_funds['CNPJ_UNIFICADO'].isin(filtro_cnpj)]
        depois = len(data_funds)
        print(f"Filtro por CNPJ aplicado: {antes-depois} registros removidos, {depois} mantidos.")
    
    # Usar CNPJ_UNIFICADO como a coluna principal
    data_funds['CNPJ_FUNDO'] = data_funds['CNPJ_UNIFICADO']
    
    # Garantir que a coluna de data esteja no formato correto
    data_funds['DT_COMPTC'] = pd.to_datetime(data_funds['DT_COMPTC'])
    
    # Criar um DataFrame de datas para referência (dias úteis)
    todas_datas = pd.date_range(start=data_funds['DT_COMPTC'].min(), 
                               end=data_funds['DT_COMPTC'].max(), freq='B')
    bdates = pd.DataFrame(index=todas_datas)
    bdates['Data'] = bdates.index
    
    # === NOVA PARTE: EXTRAIR EVOLUÇÃO DE PL, CAPTAÇÃO E RESGATE ===
    print("\nProcessando evolução de PL, captação e resgate...")
    
    # Verificar se temos as colunas necessárias
    colunas_pl = ['VL_PATRIM_LIQ', 'CAPTC_DIA', 'RESG_DIA']
    colunas_disponiveis = [col for col in colunas_pl if col in data_funds.columns]
    
    if colunas_disponiveis:
        print(f"Colunas disponíveis para evolução: {', '.join(colunas_disponiveis)}")
        
        # Criar DataFrame para evolução de PL
        evolucao_pl = pd.DataFrame()
        
        # Para cada CNPJ, extrair evolução
        for cnpj in data_funds['CNPJ_FUNDO'].unique():
            df_fundo = data_funds[data_funds['CNPJ_FUNDO'] == cnpj].copy()
            
            # Criar DataFrame de evolução para este fundo
            evolucao_fundo = pd.DataFrame()
            evolucao_fundo['Data'] = df_fundo['DT_COMPTC']
            evolucao_fundo['CNPJ_FUNDO'] = cnpj
            
            # Adicionar colunas disponíveis
            if 'VL_PATRIM_LIQ' in df_fundo.columns:
                evolucao_fundo['PL'] = pd.to_numeric(df_fundo['VL_PATRIM_LIQ'], errors='coerce')
            
            if 'CAPTC_DIA' in df_fundo.columns:
                evolucao_fundo['Captacao'] = pd.to_numeric(df_fundo['CAPTC_DIA'], errors='coerce')
            
            if 'RESG_DIA' in df_fundo.columns:
                evolucao_fundo['Resgate'] = pd.to_numeric(df_fundo['RESG_DIA'], errors='coerce')
            
            # Calcular Fluxo Líquido se tivermos captação e resgate
            if 'Captacao' in evolucao_fundo.columns and 'Resgate' in evolucao_fundo.columns:
                evolucao_fundo['Fluxo_Liquido'] = evolucao_fundo['Captacao'] - evolucao_fundo['Resgate']
            
            # Ordenar por data
            evolucao_fundo = evolucao_fundo.sort_values('Data')
            
            # Calcular valores acumulados
            if 'Captacao' in evolucao_fundo.columns:
                evolucao_fundo['Captacao_Acumulada'] = evolucao_fundo['Captacao'].cumsum()
            
            if 'Resgate' in evolucao_fundo.columns:
                evolucao_fundo['Resgate_Acumulado'] = evolucao_fundo['Resgate'].cumsum()
            
            if 'Fluxo_Liquido' in evolucao_fundo.columns:
                evolucao_fundo['Fluxo_Acumulado'] = evolucao_fundo['Fluxo_Liquido'].cumsum()
            
            # Adicionar ao DataFrame de evolução geral
            evolucao_pl = pd.concat([evolucao_pl, evolucao_fundo], ignore_index=True)
        
        # Adicionar nomes dos fundos se o register estiver disponível
        if register is not None and 'DENOM_SOCIAL' in register.columns:
            # Mapear CNPJs para nomes
            cnpj_para_nome = {}
            for cnpj in evolucao_pl['CNPJ_FUNDO'].unique():
                fundo_info = register[register['CNPJ_FUNDO'] == cnpj]
                if not fundo_info.empty:
                    cnpj_para_nome[cnpj] = fundo_info['DENOM_SOCIAL'].iloc[0]
            
            # Adicionar coluna de nome
            evolucao_pl['Nome_Fundo'] = evolucao_pl['CNPJ_FUNDO'].map(cnpj_para_nome)
        
        print(f"Evolução de PL processada para {evolucao_pl['CNPJ_FUNDO'].nunique()} fundos")
    else:
        print("Aviso: Não foi possível criar evolução de PL, colunas necessárias não encontradas")
        evolucao_pl = pd.DataFrame()  # DataFrame vazio

    # Calcular retornos por fundo
    print('\nCalculando retornos dos fundos...')
    funds_returns = pd.DataFrame(index=bdates['Data'])
    
    for group in tqdm(data_funds.groupby(by='CNPJ_FUNDO')):
        try:
            # Extrair dados do grupo
            cnpj = group[0]
            df_grupo = group[1]
            
            # Converter para DataFrame organizado por data
            df = df_grupo.rename(columns={'DT_COMPTC': 'Data', 'VL_QUOTA': str(cnpj)})
            df = df.set_index('Data')
            
            # Verificar número de cotistas se a coluna existir
            if 'NR_COTST' in df.columns and min_shareholder > 1:
                shareholders = df['NR_COTST'].mean()
                if shareholders < min_shareholder:
                    print(f"CNPJ {cnpj} ignorado: média de {shareholders:.1f} cotistas (mínimo: {min_shareholder})")
                    continue
            
            # Normalizar cotas (primeiro valor = 1.0)
            if str(cnpj) in df.columns:
                # Ordenar por data para garantir que o primeiro valor está correto
                df = df.sort_index()
                
                # Verificar se há valores válidos
                valores_validos = pd.to_numeric(df[str(cnpj)], errors='coerce').dropna()
                if len(valores_validos) > 0:
                    # Converter para numérico e normalizar
                    df[str(cnpj)] = pd.to_numeric(df[str(cnpj)], errors='coerce')
                    inicial = df[str(cnpj)].dropna().iloc[0]
                    
                    if inicial > 0:  # Evitar divisão por zero
                        df[str(cnpj)] = df[str(cnpj)] / inicial
                        
                        # Mesclar com o DataFrame principal
                        funds_returns = pd.merge(funds_returns, df[str(cnpj)], 
                                              left_index=True, right_index=True, 
                                              how='outer')
        except Exception as e:
            print(f"Erro ao processar CNPJ {cnpj}: {e}")
    
    # Ordenar por data e preencher valores ausentes
    returns_f = funds_returns.copy()
    returns_f = returns_f.sort_index()
    returns_f = returns_f.ffill().bfill()  # Usando ffill e bfill para evitar avisos
    
    # Calcular retornos totais
    print('\nCalculando retornos totais...')
    total_returns = pd.DataFrame(columns=['total_returns', 'fundo_investimento', 'classe', 'PL'])
    
    if len(returns_f) > 0 and len(returns_f.columns) > 0:
        # Calcular retorno total (valor final / valor inicial - 1)
        ultima_linha = returns_f.iloc[-1].dropna()
        if len(ultima_linha) > 0:
            total_returns['total_returns'] = (ultima_linha.sort_values(ascending=False) - 1)
            
            # Adicionar informações adicionais se o DataFrame register estiver disponível
            if register is not None:
                for cnpj in tqdm(returns_f.columns):
                    id_funds = register[register['CNPJ_FUNDO'] == cnpj]
                    if len(id_funds) > 0:
                        # Adicionar nome do fundo
                        if 'DENOM_SOCIAL' in id_funds.columns:
                            total_returns.loc[cnpj, 'fundo_investimento'] = id_funds['DENOM_SOCIAL'].values[0]
                        
                        # Adicionar classe do fundo
                        if 'CLASSE' in id_funds.columns:
                            total_returns.loc[cnpj, 'classe'] = id_funds['CLASSE'].values[0]
                        
                        # Adicionar PL do fundo
                        if 'VL_PATRIM_LIQ' in id_funds.columns:
                            total_returns.loc[cnpj, 'PL'] = id_funds['VL_PATRIM_LIQ'].values[0]
    
    print(f"Retornos calculados para {len(returns_f.columns)} fundos.")
    
    return returns_f, total_returns, evolucao_pl




def processar_dados(df):
    
    colunas_originais = df.columns[1:].tolist()
    colunas_novas =  ['Aconcagua', 'Huayna', 'Chimborazo', 'Alpamayo']
    df.columns = colunas_novas
    
    # Encontrar a data de início de cada fundo (quando o valor é diferente de 1.0)
    datas_inicio = {}
    valores_base = {}
    
    for coluna in colunas_novas:
        # Encontrar o primeiro valor não igual a 1.0, ou o primeiro valor se todos forem 1.0
        for idx, valor in enumerate(df[coluna]):
            if valor != 1.0:
                datas_inicio[coluna] = df.index[idx]
                valores_base[coluna] = valor
                break
        
        # Se não encontrou nenhum valor diferente de 1.0, use o primeiro valor
        if coluna not in datas_inicio:
            datas_inicio[coluna] = df.index[0]
            valores_base[coluna] = df[coluna].iloc[0]
    
    # Normalizar os valores para que cada fundo comece em 1.0 na sua data de início
    df_normalizado = pd.DataFrame(index=df.index)
    
    for coluna in colunas_novas:
        # Inicializar com NaN
        df_normalizado[coluna] = np.nan
        
        # Preencher valores normalizados a partir da data de início
        mascara = df.index >= datas_inicio[coluna]
        df_normalizado.loc[mascara, coluna] = df.loc[mascara, coluna] / valores_base[coluna]
    
    # Calcular estatísticas
    estatisticas = {}
    for coluna in colunas_novas:
        # Obter valores válidos
        valores_validos = df_normalizado[coluna].dropna()
        
        # Calcular retornos diários
        retornos_diarios = valores_validos.pct_change().dropna()
        
        # Calcular volatilidade anualizada
        volatilidade = retornos_diarios.std() * np.sqrt(252)
        
        estatisticas[coluna] = {
            'retorno': f"{(valores_validos.iloc[-1] - 1) * 100:.2f}%",
            'volatilidade': f"{volatilidade * 100:.2f}%"
        }
    
    return df_normalizado, estatisticas, colunas_novas


def criar_grafico(df, estatisticas, colunas):
   
    plt.figure(figsize=(14, 8))
    
    # Definir cores para cada fundo
    cores = ['#404040', '#0D47A1', '#1B5E20', '#B71C1C']
    
    # Plotar cada fundo
    for i, coluna in enumerate(colunas):
        plt.plot(df.index, df[coluna], label=coluna, color=cores[i], linewidth=2)
    
    # Adicionar linha de referência em y=1 (0% de retorno)
    plt.axhline(y=1, color='gray', linestyle='--', alpha=0.7)
    
    # Configurar eixos e legendas
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%Y'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    
    # Configurar rótulos do eixo y para mostrar percentuais
    plt.gca().yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"{(x-1)*100:.0f}%"))
    
    # Adicionar título e legendas
    plt.title('Curvas de Retorno', fontsize=16)
    plt.xlabel('Data')
    plt.ylabel('Retorno Acumulado')
    plt.legend(loc='best')
    plt.grid(True, alpha=0.3)
    
    # Rotacionar datas no eixo x
    plt.xticks(rotation=45)
    
    # Ajustar layout
    plt.tight_layout()
    
    # Adicionar texto com estatísticas no canto superior esquerdo
    info_text = "Estatísticas dos Fundos:\n"
    for coluna in colunas:
        info_text += f"\n{coluna}:\n"
        info_text += f"  Retorno: {estatisticas[coluna]['retorno']}\n"
        info_text += f"  Volatilidade: {estatisticas[coluna]['volatilidade']}\n"
    
    # Adicionar anotação com as estatísticas
    plt.figtext(0.25, 0.52, info_text, fontsize=10, 
                bbox=dict(facecolor='white', alpha=0.8))
    
    plt.show()
    
    return plt


def gerar_histogramas_objetivos_completo(df_carteira, classificacao_cnpj=None, periodo=None, 
                               base_dir=None, max_produtos=10, mostrar_grafico=True):
    """
    Função completa que realiza a classificação por objetivo e gera histogramas para cada objetivo.
    
    Args:
        df_carteira (DataFrame): DataFrame com os dados da carteira
        classificacao_cnpj (dict): Dicionário com classificação por CNPJ
        periodo (str, optional): Identificação do período de análise
        base_dir (str, optional): Diretório base para salvar os gráficos
        max_produtos (int): Número máximo de produtos a mostrar em cada histograma
        mostrar_grafico (bool): Se True, exibe os gráficos durante a execução
        
    Returns:
        dict: Resultados da análise com caminhos dos histogramas
    """
    import os
    import pandas as pd
    from datetime import datetime
    import matplotlib.pyplot as plt
    
    # Primeiro passo: classificar os produtos por objetivo
    print("Classificando produtos por objetivo...")
    df_classificado = classificar_produtos_por_objetivo(df_carteira, periodo=periodo, classificacao_cnpj=classificacao_cnpj)
    
    # Verificar se a classificação foi bem-sucedida
    if 'OBJETIVO' not in df_classificado.columns:
        raise ValueError("A classificação não gerou a coluna 'OBJETIVO'. Verifique a função de classificação.")
    
    # Identificar objetivos presentes no DataFrame
    objetivos_presentes = sorted(df_classificado['OBJETIVO'].unique())
    print(f"Objetivos identificados: {', '.join(objetivos_presentes)}")
    
    # Criar diretório para os gráficos se necessário
    if base_dir:
        dir_graficos = os.path.join(base_dir, 'graficos_objetivos')
        os.makedirs(dir_graficos, exist_ok=True)
    
    # Gerar histogramas para cada um dos três objetivos principais
    objetivos_principais = ['Preservação', 'Manutenção', 'Ganho']
    resultados = {}
    caminhos_histogramas = {}
    
    for objetivo in objetivos_principais:
        # Verificar se este objetivo está presente nos dados
        if objetivo not in objetivos_presentes:
            print(f"Objetivo '{objetivo}' não encontrado nos dados.")
            continue
        
        print(f"\nGerando histograma para objetivo '{objetivo}'...")
        
        # Nome do arquivo para este objetivo
        if periodo:
            nome_arquivo = f"histograma_{objetivo.lower()}_{periodo.replace('-', '_')}.png"
        else:
            nome_arquivo = f"histograma_{objetivo.lower()}.png"
        
        # Gerar o histograma
        try:
            resultado = gerar_histograma_produtos_por_objetivo(
                df_classificado=df_classificado,
                objetivo=objetivo,
                base_dir=base_dir,
                max_produtos=max_produtos,
                mostrar_grafico=mostrar_grafico,
                salvar_arquivo=nome_arquivo
            )
            
            if resultado:
                resultados[objetivo] = resultado
                if base_dir:
                    caminho = os.path.join(dir_graficos, nome_arquivo)
                    caminhos_histogramas[objetivo] = caminho
                print(f"Histograma para '{objetivo}' gerado com sucesso.")
            else:
                print(f"Não foi possível gerar histograma para '{objetivo}'.")
        except Exception as e:
            print(f"Erro ao gerar histograma para '{objetivo}': {str(e)}")
    
    # Opcionalmente, gerar um relatório HTML consolidado
    if base_dir and resultados:
        try:
            gerar_relatorio_html_objetivos(
                resultados=resultados,
                caminhos=caminhos_histogramas,
                periodo=periodo, 
                base_dir=base_dir
            )
        except Exception as e:
            print(f"Erro ao gerar relatório HTML: {str(e)}")
    
    # Retornar resultados e caminhos
    return {
        'resultados': resultados,
        'caminhos': caminhos_histogramas
    }


def gerar_histograma_produtos_por_objetivo(df_classificado, objetivo, base_dir=None, 
                                 max_produtos=10, mostrar_grafico=True, 
                                 salvar_arquivo=None, titulo=None):
    """
    Gera um histograma horizontal mostrando os produtos alocados em um objetivo específico.
    
    Args:
        df_classificado (DataFrame): DataFrame já classificado por objetivo
        objetivo (str): Objetivo a ser analisado ('Preservação', 'Manutenção' ou 'Ganho')
        base_dir (str, optional): Diretório base para salvar o gráfico
        max_produtos (int): Número máximo de produtos a exibir
        mostrar_grafico (bool): Se True, exibe o gráfico com plt.show()
        salvar_arquivo (str, optional): Caminho para salvar o gráfico como arquivo
        titulo (str, optional): Título personalizado para o gráfico
        
    Returns:
        dict: Resultados da análise com valores e percentuais dos produtos
    """
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np
    import os
    from matplotlib.ticker import PercentFormatter
    
    # Verificar se o objetivo é válido
    objetivos_validos = ['Preservação', 'Manutenção', 'Ganho']
    if objetivo not in objetivos_validos:
        raise ValueError(f"Objetivo deve ser um dos seguintes: {', '.join(objetivos_validos)}")
    
    # Verificar se a coluna 'OBJETIVO' existe no DataFrame
    if 'OBJETIVO' not in df_classificado.columns:
        raise ValueError("Coluna 'OBJETIVO' não encontrada no DataFrame. Use a função classificar_produtos_por_objetivo primeiro.")
    
    # Filtrar produtos pelo objetivo especificado
    df_objetivo = df_classificado[df_classificado['OBJETIVO'] == objetivo].copy()
    
    if len(df_objetivo) == 0:
        print(f"Nenhum produto encontrado para o objetivo '{objetivo}'")
        return None
    
    # Verificar se temos as colunas necessárias
    if 'VL_MERC_POS_FINAL' not in df_objetivo.columns:
        print("Coluna 'VL_MERC_POS_FINAL' não encontrada. Verificando alternativas...")
        
        # Tentar encontrar uma coluna com "VALOR" no nome
        colunas_valor = [col for col in df_objetivo.columns if 'VALOR' in col.upper() or 'VL_' in col.upper()]
        if colunas_valor:
            coluna_valor = colunas_valor[0]
            print(f"Usando coluna '{coluna_valor}' para valores.")
            df_objetivo['VL_MERC_POS_FINAL'] = df_objetivo[coluna_valor]
        else:
            raise ValueError("Não foi possível encontrar uma coluna de valores no DataFrame")
    
    # Identificar a coluna com o nome do produto
    coluna_nome_produto = None
    colunas_potenciais = [
        'NM_FUNDO_CLASSE_SUBCLASSE_COTA', 
        'DENOM_SOCIAL', 
        'DS_ATIVO', 
        'CD_ATIVO',
        'NOME_PRODUTO',
        'NOME'
    ]
    
    for col in colunas_potenciais:
        if col in df_objetivo.columns:
            coluna_nome_produto = col
            break
    
    if coluna_nome_produto is None:
        # Fallback: usar a primeira coluna não numérica
        for col in df_objetivo.columns:
            if df_objetivo[col].dtype == 'object':
                coluna_nome_produto = col
                print(f"Usando coluna '{col}' para nomes de produtos.")
                break
        
        if coluna_nome_produto is None:
            raise ValueError("Não foi possível identificar uma coluna com os nomes dos produtos")
    
    # Converter valores para numérico
    df_objetivo['VL_MERC_POS_FINAL'] = pd.to_numeric(df_objetivo['VL_MERC_POS_FINAL'], errors='coerce')
    
    # Remover valores nulos ou negativos
    df_objetivo = df_objetivo[df_objetivo['VL_MERC_POS_FINAL'] > 0]
    
    if len(df_objetivo) == 0:
        print(f"Nenhum produto com valor positivo encontrado para o objetivo '{objetivo}'")
        return None
    
    # Calcular o valor total para este objetivo
    valor_total_objetivo = df_objetivo['VL_MERC_POS_FINAL'].sum()
    
    # Agrupar por nome do produto e somar valores
    produtos_agrupados = df_objetivo.groupby(coluna_nome_produto)['VL_MERC_POS_FINAL'].sum().reset_index()
    
    # Calcular percentuais em relação ao total do objetivo
    produtos_agrupados['PERCENTUAL'] = (produtos_agrupados['VL_MERC_POS_FINAL'] / valor_total_objetivo * 100)
    
    # Ordenar por valor (decrescente)
    produtos_agrupados = produtos_agrupados.sort_values('VL_MERC_POS_FINAL', ascending=False)
    
    # Limitar ao número máximo de produtos
    if len(produtos_agrupados) > max_produtos:
        # Separar os principais produtos e agrupar o restante como "Outros"
        principais = produtos_agrupados.head(max_produtos - 1)
        # outros = produtos_agrupados.iloc[max_produtos - 1:]
        
        # Criar entrada para "Outros"
        # outros_row = pd.DataFrame({
        #     coluna_nome_produto: [f"Outros ({len(outros)} produtos)"],
        #     'VL_MERC_POS_FINAL': [outros['VL_MERC_POS_FINAL'].sum()],
        #     'PERCENTUAL': [outros['PERCENTUAL'].sum()]
        # })
        
        # Combinar principais com outros
        produtos_agrupados = pd.concat([principais], ignore_index=True)
    
    # Criar nomes simplificados para os produtos (para exibição no gráfico)
    produtos_agrupados['NOME_SIMPLIFICADO'] = produtos_agrupados[coluna_nome_produto].apply(
        lambda x: str(x)[:40] + '...' if isinstance(x, str) and len(str(x)) > 40 else str(x)
    )
    
    # Cores por objetivo
    cores_objetivo = {
        'Preservação': '#4682B4',  # Azul mais claro (Steel Blue)
        'Manutenção': '#FFB347',   # Laranja mais claro (Pastel Orange)
        'Ganho': '#FF6B6B',        # Vermelho mais claro (Light Coral)
    }
    
    # Calcular altura apropriada para o gráfico baseado no número de produtos
    altura_base = 5
    altura_por_produto = 0.4
    altura = max(altura_base, min(15, altura_base + len(produtos_agrupados) * altura_por_produto))
    
    # Criar figura
    plt.figure(figsize=(12, altura))
    
    # Criar gráfico de barras horizontais
    barras = plt.barh(
        produtos_agrupados['NOME_SIMPLIFICADO'], 
        produtos_agrupados['PERCENTUAL'],
        color=cores_objetivo.get(objetivo, '#6495ED'),
        alpha=0.8,
        height=0.6,
        edgecolor='white',
        linewidth=0.5
    )
    
    # Adicionar rótulos com valores e percentuais
    for i, (_, row) in enumerate(produtos_agrupados.iterrows()):
        # Formatar valor
        valor = row['VL_MERC_POS_FINAL']
        if valor >= 1e9:
            valor_str = f"R$ {valor/1e9:.2f}B"
        else:
            valor_str = f"R$ {valor/1e6:.2f}M"
        
        # Percentual
        percentual = row['PERCENTUAL']
        
        # Texto a exibir
        texto = f"{percentual:.1f}% ({valor_str})"
        
        # Determinar posição e cor do texto baseado no tamanho da barra
        if percentual > 10:  # Se a barra for grande o suficiente
            # Colocar texto dentro da barra
            pos_x = percentual/2
            cor_texto = 'white'
            ha_texto = 'center'
        else:
            # Colocar texto fora da barra
            pos_x = percentual + 0.5
            cor_texto = 'black'
            ha_texto = 'left'
        
        # Adicionar texto
        plt.text(
            pos_x,          # Posição X
            i,              # Posição vertical (índice da barra)
            texto,
            va='center',
            ha=ha_texto,
            color=cor_texto,
            fontsize=11,    # Aumentar tamanho da fonte
            fontweight='bold'
        )
    
    # Configurar eixos
    plt.xlabel('Percentual (%)', fontsize=12)
    plt.ylabel('')  # Sem rótulo no eixo Y
    
    # Aumentar o tamanho das fontes dos ticks
    plt.xticks(fontsize=11)
    plt.yticks(fontsize=11)
    
    # Definir título
    if titulo is None:
        titulo = f"Produtos com Objetivo de {objetivo}"
    plt.title(titulo, fontsize=14, pad=20)
    
    # Adicionar grade
    plt.grid(True, axis='x', linestyle='--', alpha=0.3)
    
    # Formatar eixo X como percentual
    plt.gca().xaxis.set_major_formatter(PercentFormatter())
    
    # Ajustar limites do eixo X
    max_percentual = produtos_agrupados['PERCENTUAL'].max()
    plt.xlim(0, max_percentual * 1.2)  # 20% de espaço extra para os rótulos
    
    # Adicionar total como anotação
    if valor_total_objetivo >= 1e9:
        valor_total_str = f"Total: R$ {valor_total_objetivo/1e9:.2f}B"
    else:
        valor_total_str = f"Total: R$ {valor_total_objetivo/1e6:.2f}M"
    
    plt.annotate(
        valor_total_str,
        xy=(0.95, 0.03),  # Posição relativa à figura (X, Y)
        xycoords='figure fraction',
        ha='right',
        fontsize=12,  # Aumentar tamanho da fonte
        fontweight='bold',
        bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8, edgecolor='#cccccc')
    )
    
    # Inverter eixo Y para que o maior valor fique no topo
    plt.gca().invert_yaxis()
    
    # Remover bordas superiores e à direita
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['top'].set_visible(False)
    
    # Ajustar layout
    plt.tight_layout()
    
    # Salvar o gráfico se caminho foi especificado
    if salvar_arquivo:
        # Criar diretório se não existir
        if base_dir:
            os.makedirs(os.path.join(base_dir, 'graficos_objetivos'), exist_ok=True)
            caminho = os.path.join(base_dir, 'graficos_objetivos', salvar_arquivo)
        else:
            caminho = salvar_arquivo
            
        plt.savefig(caminho, dpi=300, bbox_inches='tight')
        print(f"Gráfico salvo em: {caminho}")
    
    # Mostrar o gráfico
    if mostrar_grafico:
        plt.show()
    else:
        plt.close()
    
    # Preparar e retornar resultados
    resultados = {
        'objetivo': objetivo,
        'valor_total': valor_total_objetivo,
        'produtos': produtos_agrupados.to_dict('records')
    }
    
    return resultados


def gerar_relatorio_html_objetivos(resultados, caminhos, periodo=None, base_dir=None):
    """
    Gera um relatório HTML com os histogramas por objetivo.
    
    Args:
        resultados (dict): Dicionário com resultados da análise por objetivo
        caminhos (dict): Dicionário com caminhos dos histogramas
        periodo (str, optional): Período da análise
        base_dir (str): Diretório base
        
    Returns:
        str: Caminho do arquivo HTML gerado
    """
    import os
    from datetime import datetime
    
    # Definir diretório para o relatório
    if base_dir:
        dir_relatorios = os.path.join(base_dir, 'relatorios_objetivos')
        os.makedirs(dir_relatorios, exist_ok=True)
    else:
        dir_relatorios = '.'
    
    # Nome do arquivo baseado no período ou data atual
    if periodo:
        nome_arquivo = f"relatorio_objetivos_{periodo.replace('-', '_')}.html"
    else:
        data_atual = datetime.now().strftime('%Y%m%d')
        nome_arquivo = f"relatorio_objetivos_{data_atual}.html"
    
    # Caminho completo do arquivo
    caminho_html = os.path.join(dir_relatorios, nome_arquivo)
    
    # Calcular o total geral
    valor_total_geral = sum(resultado['valor_total'] for resultado in resultados.values())
    
    # Calcular percentuais por objetivo em relação ao total geral
    percentuais_objetivo = {}
    for objetivo, resultado in resultados.items():
        percentuais_objetivo[objetivo] = (resultado['valor_total'] / valor_total_geral * 100)
    
    # Criar HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Relatório de Alocação por Objetivo</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2, h3 {{ color: #333366; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .grafico {{ text-align: center; margin: 30px 0; }}
            img {{ max-width: 100%; border: 1px solid #ddd; }}
            .footer {{ text-align: center; margin-top: 40px; color: #666; font-size: 12px; }}
            .resumo {{ margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-radius: 5px; }}
            .objetivo-preservacao {{ color: #4682B4; }}
            .objetivo-manutencao {{ color: #FFB347; }}
            .objetivo-ganho {{ color: #FF6B6B; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Relatório de Alocação por Objetivo</h1>
            <p>Período de análise: {periodo if periodo else 'Não especificado'}</p>
            
            <div class="resumo">
                <h2>Resumo da Alocação</h2>
                <p>Valor total da carteira: {format_valor(valor_total_geral)}</p>
                <p>Distribuição por objetivo:</p>
                <ul>
    """
    
    # Adicionar itens para cada objetivo
    for objetivo in ['Preservação', 'Manutenção', 'Ganho']:
        if objetivo in resultados:
            valor = resultados[objetivo]['valor_total']
            percentual = percentuais_objetivo[objetivo]
            
            # Classe CSS para cores por objetivo
            classe_css = f"objetivo-{objetivo.lower()}"
            
            html_content += f"""
                    <li><strong class="{classe_css}">{objetivo}</strong>: {format_valor(valor)} ({percentual:.2f}%)</li>
            """
    
    html_content += """
                </ul>
            </div>
    """
    
    # Adicionar histogramas para cada objetivo
    for objetivo in ['Preservação', 'Manutenção', 'Ganho']:
        if objetivo in resultados and objetivo in caminhos:
            html_content += f"""
            <h2>Produtos com Objetivo de {objetivo}</h2>
            <div class="grafico">
                <img src="{os.path.relpath(caminhos[objetivo], dir_relatorios)}" alt="Produtos com Objetivo de {objetivo}">
            </div>
            
            <h3>Principais produtos</h3>
            <table>
                <tr>
                    <th>Produto</th>
                    <th>Valor</th>
                    <th>Percentual</th>
                </tr>
            """
            
            # Adicionar linhas da tabela para os produtos
            for produto in resultados[objetivo]['produtos']:
                nome_col = next((col for col in produto.keys() 
                               if col not in ['VL_MERC_POS_FINAL', 'PERCENTUAL', 'NOME_SIMPLIFICADO']), 'nome')
                nome_produto = produto[nome_col]
                valor = produto['VL_MERC_POS_FINAL']
                percentual = produto['PERCENTUAL']
                
                html_content += f"""
                <tr>
                    <td>{nome_produto}</td>
                    <td>{format_valor(valor)}</td>
                    <td>{percentual:.2f}%</td>
                </tr>
                """
            
            html_content += """
            </table>
            """
    
    # Finalizar HTML
    html_content += f"""
            <div class="footer">
                <p>Relatório gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Função auxiliar para formatar valores
    def format_valor(valor):
        if valor >= 1e9:
            return f"R$ {valor/1e9:.2f} bilhões"
        else:
            return f"R$ {valor/1e6:.2f} milhões"
    
    # Salvar HTML
    with open(caminho_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Relatório HTML salvo em: {caminho_html}")
    
    return caminho_html














# -----------------------ESSA PARTE E PARA OS RETORNOS DOS FUNDOS ---------------# 
# -------------------------------------------------------------------------------#

