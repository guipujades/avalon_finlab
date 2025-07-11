import io
import os
import re
import zipfile
import shutil
import pickle
import pandas as pd
import numpy as np
import seaborn as sns
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mtick
import matplotlib.patches as patches


def salvar_variaveis_serial(base_dir, serie_custos, media_custos, valor_investido, nome=None):
    dir_serial = os.path.join(base_dir, 'serial')
    os.makedirs(dir_serial, exist_ok=True)

    # Salvando as variáveis
    arquivos = {
        f'serie_custos_{nome}.pkl': serie_custos,
        f'media_custos_{nome}.pkl': media_custos,
        f'valor_investido_{nome}.pkl': valor_investido
    }

    for nome_arquivo, dados in arquivos.items():
        caminho = os.path.join(dir_serial, nome_arquivo)
        with open(caminho, 'wb') as f:
            pickle.dump(dados, f)

    print(f"Variáveis salvas com sucesso em '{dir_serial}'")
    
    
def carregar_variaveis_serial(base_dir, nome=None):
    dir_serial = os.path.join(base_dir, 'serial')

    arquivos = [f'serie_custos_{nome}.pkl', f'media_custos_{nome}.pkl', f'valor_investido_{nome}.pkl']
    dados_carregados = {}

    for nome_arquivo in arquivos:
        caminho = os.path.join(dir_serial, nome_arquivo)
        with open(caminho, 'rb') as f:
            dados_carregados[nome_arquivo.replace('.pkl', '')] = pickle.load(f)

    print(f"Variáveis carregadas com sucesso de '{dir_serial}'")
    return dados_carregados


def carregar_todos_fundos(base_dir, lista_fundos):
    """Carrega dados de múltiplos fundos e os consolida."""
    # Inicializar dicionários consolidados
    serie_custos_consolidado = pd.DataFrame()
    valor_investido_consolidado = {}
    
    # Carregar dados de cada fundo
    for nome_fundo in lista_fundos:
        dados = carregar_variaveis_serial(base_dir, nome_fundo)

        df_atual = dados[f'serie_custos_{nome_fundo}'].copy()
        df_atual['fundo'] = nome_fundo  # Adicionar coluna identificando o fundo
        serie_custos_consolidado = pd.concat([serie_custos_consolidado, df_atual], ignore_index=True)
        
        # Adicionar valores investidos ao dicionário consolidado
        for data, valor in dados[f'valor_investido_{nome_fundo}'].items():
            chave = f"{data}_{nome_fundo}"
            valor_investido_consolidado[chave] = valor

    return serie_custos_consolidado, valor_investido_consolidado


def processar_carteiras(cnpj_fundo, base_dir, limite_arquivos=None):

    print(f"Processando carteiras para o fundo {cnpj_fundo}...")
    
    # Diretório onde estão os dados
    pasta_cda = os.path.join(base_dir, 'CDA')
    
    # Diretório temporário para extração
    dir_temp = os.path.join(base_dir, 'temp_extract')
    os.makedirs(dir_temp, exist_ok=True)
    
    # Dicionário para armazenar os dados por data
    carteiras_por_data = {}
    
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
                # Extrai e processa os arquivos BLC_2
                with zipfile.ZipFile(arquivo_zip, 'r') as zip_ref:
                    # Filtra apenas arquivos BLC_2
                    arquivos_no_zip = zip_ref.namelist()
                    arquivos_blc2 = [arq for arq in arquivos_no_zip if 'BLC_2' in arq and arq.endswith('.csv')]
                    
                    if not arquivos_blc2:
                        print(f"  - Nenhum arquivo BLC_2 encontrado em {nome_arquivo}")
                        
                        # Para arquivos anuais, pode haver subdiretórios, então extraímos tudo
                        if eh_anual:
                            print("  - Extraindo todos os arquivos para buscar BLC_2 em subdiretórios...")
                            zip_ref.extractall(data_dir)
                            
                            # Procura por arquivos BLC_2 em todos os subdiretórios
                            arquivos_blc2 = []
                            for root, _, files in os.walk(data_dir):
                                for file in files:
                                    if 'BLC_2' in file and file.endswith('.csv'):
                                        arquivos_blc2.append(os.path.join(root, file))
                            
                            print("  - Encontrados {len(arquivos_blc2)} arquivos BLC_2 nos subdiretórios")
                        
                        if not arquivos_blc2:
                            continue
                    else:
                        print(f"  - Encontrados {len(arquivos_blc2)} arquivos BLC_2")
                        
                        # Extrai apenas os arquivos BLC_2
                        for arq_blc2 in arquivos_blc2:
                            zip_ref.extract(arq_blc2, data_dir)
                            arquivos_blc2 = [os.path.join(data_dir, arq_blc2)]
                    
                    # Processa cada arquivo BLC_2 encontrado
                    for arquivo_csv in arquivos_blc2:
                        try:
                            # Carrega o CSV
                            df = pd.read_csv(arquivo_csv, sep=';', encoding='ISO-8859-1', low_memory=False)
                            
                            # Identifica coluna correta para CNPJ do fundo
                            coluna_cnpj_fundo = None
                            if 'CNPJ_FUNDO_CLASSE' in df.columns:
                                coluna_cnpj_fundo = 'CNPJ_FUNDO_CLASSE'
                            elif 'CNPJ_FUNDO' in df.columns:
                                coluna_cnpj_fundo = 'CNPJ_FUNDO'
                            elif 'CD_FUNDO' in df.columns:
                                coluna_cnpj_fundo = 'CD_FUNDO'
                            
                            if coluna_cnpj_fundo is None:
                                print("  ✗ Não foi possível identificar coluna com CNPJ do fundo")
                                continue
                            
                            # Filtra pelo CNPJ do fundo
                            df_fundo = df[df[coluna_cnpj_fundo] == cnpj_fundo]
                            
                            if len(df_fundo) > 0:
                                # Se é arquivo anual, pode ter múltiplas datas no mesmo arquivo
                                if eh_anual and 'DT_COMPTC' in df_fundo.columns:
                                    # Agrupa por data de competência
                                    for data, grupo in df_fundo.groupby('DT_COMPTC'):
                                        # Converte para formato YYYY-MM
                                        try:
                                            data_obj = datetime.strptime(data, '%Y-%m-%d')
                                            data_mes = f"{data_obj.year}-{data_obj.month:02d}"
                                            
                                            # Filtra por cotas de fundos
                                            if 'TP_APLIC' in grupo.columns:
                                                grupo_cotas = grupo[grupo['TP_APLIC'] == 'Cotas de Fundos']
                                                if len(grupo_cotas) > 0:
                                                    print(f"  ✓ Encontrados {len(grupo_cotas)} investimentos em cotas para {data_mes}")
                                                    
                                                    # Adiciona ao dicionário de carteiras
                                                    if data_mes in carteiras_por_data:
                                                        carteiras_por_data[data_mes] = pd.concat([carteiras_por_data[data_mes], grupo_cotas], ignore_index=True)
                                                    else:
                                                        carteiras_por_data[data_mes] = grupo_cotas
                                        except Exception as e:
                                            print(f"  ✗ Erro ao processar data {data}: {str(e)}")
                                else:
                                    # Para arquivos mensais, usa a data do arquivo
                                    print(f"  ✓ Encontrados {len(df_fundo)} investimentos para {data_formatada}")
                                    
                                    # Filtra por cotas de fundos se tiver a coluna
                                    if 'TP_APLIC' in df_fundo.columns:
                                        df_fundo = df_fundo[df_fundo['TP_APLIC'] == 'Cotas de Fundos']
                                    
                                    if len(df_fundo) > 0:
                                        print(f"  ✓ Encontrados {len(df_fundo)} investimentos em cotas para {data_formatada}")
                                        
                                        # Adiciona ao dicionário de carteiras
                                        if data_formatada in carteiras_por_data:
                                            carteiras_por_data[data_formatada] = pd.concat([carteiras_por_data[data_formatada], df_fundo], ignore_index=True)
                                        else:
                                            carteiras_por_data[data_formatada] = df_fundo
                                    else:
                                        print(f"  - Nenhum investimento em cotas encontrado para {data_formatada}")
                            else:
                                print(f"  - Nenhum investimento encontrado para o fundo {cnpj_fundo}")
                        
                        except Exception as e:
                            print(f"  ✗ Erro ao processar {os.path.basename(arquivo_csv)}: {str(e)}")
            
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
    num_datas = len(carteiras_por_data)
    datas = sorted(list(carteiras_por_data.keys()))
    
    print(f"\n{'=' * 50}")
    print(f"Processamento concluído! Dados encontrados para {num_datas} datas distintas.")
    
    if num_datas > 0:
        print(f"Range de datas: {datas[0]} a {datas[-1]}")
        
        # Mostra algumas estatísticas
        print("\nEstatísticas por data:")
        for data in datas:
            df = carteiras_por_data[data]
            num_fundos = len(df)
            
            if 'VL_MERC_POS_FINAL' in df.columns:
                df['VL_MERC_POS_FINAL'] = pd.to_numeric(df['VL_MERC_POS_FINAL'], errors='coerce')
                valor_total = df['VL_MERC_POS_FINAL'].sum()
                print(f"  {data}: {num_fundos} fundos, Valor total: R$ {valor_total:,.2f}")
            else:
                print(f"  {data}: {num_fundos} fundos")
    
    return carteiras_por_data


def adicionar_taxas_administracao(carteiras, fund_info):
 
    carteiras_com_taxas = {}
    
    for data_ref, df_carteira in carteiras.items():
        print(f"Adicionando taxas para o período {data_ref}...")
        
        # Identifica a coluna que contém o CNPJ dos fundos investidos
        coluna_cnpj = None
        for col in ['CNPJ_FUNDO_CLASSE_COTA', 'CNPJ_FUNDO_COTA', 'CPF_CNPJ_EMISSOR', 'CNPJ_EMISSOR']:
            if col in df_carteira.columns:
                coluna_cnpj = col
                break
        
        if coluna_cnpj is None:
            print(f"  - Não foi possível identificar coluna com CNPJ dos fundos investidos para {data_ref}")
            carteiras_com_taxas[data_ref] = df_carteira
            continue
        
        # Cria uma cópia do DataFrame para evitar modificar o original
        df_carteira_copy = df_carteira.copy()
        
        # Cria uma versão limpa do fund_info para o mapeamento
        fund_info_clean = fund_info[['CNPJ_FUNDO', 'TAXA_ADM']].copy()
        fund_info_clean = fund_info_clean.drop_duplicates(subset=['CNPJ_FUNDO'], keep='first')
        
        # Se o DataFrame já tem TAXA_ADM, renomeie para evitar conflitos
        if 'TAXA_ADM' in df_carteira_copy.columns:
            df_carteira_copy = df_carteira_copy.rename(columns={'TAXA_ADM': 'TAXA_ADM_ORIGINAL'})
        
        # Preparando dicionário para mapear CNPJs para taxas
        taxa_por_cnpj = dict(zip(fund_info_clean['CNPJ_FUNDO'], fund_info_clean['TAXA_ADM']))
        
        # Mapeando taxas diretamente usando o dicionário
        df_carteira_copy['TAXA_ADM'] = df_carteira_copy[coluna_cnpj].map(taxa_por_cnpj)
        
        # Converte a TAXA_ADM para número (float)
        df_carteira_copy['TAXA_ADM'] = pd.to_numeric(df_carteira_copy['TAXA_ADM'], errors='coerce')
        
        # Verifica quantos fundos têm taxa
        total_fundos = len(df_carteira_copy)
        fundos_com_taxa = df_carteira_copy['TAXA_ADM'].notna().sum()
        
        print(f"  - {fundos_com_taxa} de {total_fundos} fundos possuem taxa de administração ({fundos_com_taxa/total_fundos*100:.1f}%)")
        
        # Salva no dicionário
        carteiras_com_taxas[data_ref] = df_carteira_copy
    
    return carteiras_com_taxas


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


def adicionar_taxas_manuais(carteiras, fund_info):
    
    # Base manual de taxas de administração
    taxas_manuais = {
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
        '32.311.914/0001-60': 0.00,
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
    
    carteiras_com_taxas = {}
    
    for data_ref, df_carteira in carteiras.items():
        print(f"Adicionando taxas para o período {data_ref}...")
        
        # Identifica a coluna que contém o CNPJ dos fundos investidos
        coluna_cnpj = None
        for col in ['CNPJ_FUNDO_CLASSE_COTA', 'CNPJ_FUNDO_COTA', 'CPF_CNPJ_EMISSOR', 'CNPJ_EMISSOR']:
            if col in df_carteira.columns:
                coluna_cnpj = col
                break
        
        if coluna_cnpj is None:
            print(f"  - Não foi possível identificar coluna com CNPJ dos fundos investidos para {data_ref}")
            carteiras_com_taxas[data_ref] = df_carteira
            continue
        
        # Cria uma cópia do DataFrame para evitar modificar o original
        df_carteira_copy = df_carteira.copy()
        
        # Se o DataFrame já tem TAXA_ADM, renomeie para evitar conflitos
        if 'TAXA_ADM' in df_carteira_copy.columns:
            df_carteira_copy = df_carteira_copy.rename(columns={'TAXA_ADM': 'TAXA_ADM_ORIGINAL'})
        
        # Cria dicionário de taxas do fund_info
        taxa_por_cnpj = dict(zip(fund_info['CNPJ_FUNDO'], fund_info['TAXA_ADM']))
        
        # Adiciona as taxas manuais ao dicionário (sobrescreve se existirem)
        taxa_por_cnpj.update(taxas_manuais)
        
        # Mapeando taxas diretamente usando o dicionário
        df_carteira_copy['TAXA_ADM'] = df_carteira_copy[coluna_cnpj].map(taxa_por_cnpj)
        
        # Converte a TAXA_ADM para número (float)
        df_carteira_copy['TAXA_ADM'] = pd.to_numeric(df_carteira_copy['TAXA_ADM'], errors='coerce')
        
        # Verifica quantos fundos têm taxa
        total_fundos = len(df_carteira_copy)
        fundos_com_taxa = df_carteira_copy['TAXA_ADM'].notna().sum()
        
        print(f"  - {fundos_com_taxa} de {total_fundos} fundos possuem taxa de administração ({fundos_com_taxa/total_fundos*100:.1f}%)")
        
        # Salva no dicionário
        carteiras_com_taxas[data_ref] = df_carteira_copy
    
    return carteiras_com_taxas


def calcular_custos_taxas(carteiras_com_taxas, dir_saida):

    print("\nCalculando custos financeiros das taxas de administração...")
    
    # Dicionário para armazenar resultados
    resultados = {}
    
    # DataFrame para armazenar resultados consolidados
    registros_consolidados = []
    
    # Para cada período
    for data, df in carteiras_com_taxas.items():
        
        print(f"\nProcessando período: {data}")
        
        # Verifica se as colunas necessárias existem
        if 'TAXA_ADM' not in df.columns or 'VL_MERC_POS_FINAL' not in df.columns:
            print(f"  - ERRO: Colunas necessárias não encontradas para o período {data}")
            continue
        
        # Converte para numérico
        df['TAXA_ADM'] = pd.to_numeric(df['TAXA_ADM'], errors='coerce')
        df['VL_MERC_POS_FINAL'] = pd.to_numeric(df['VL_MERC_POS_FINAL'], errors='coerce')
        
        # Calcula o custo mensal (1/12 da taxa anual sobre o valor investido)
        df_calc = df.copy()
        df_calc['CUSTO_MENSAL'] = df_calc['VL_MERC_POS_FINAL'] * (df_calc['TAXA_ADM'] / 100) / 12
        
        # Calcula o valor total investido
        valor_total_investido = df_calc['VL_MERC_POS_FINAL'].sum()
        
        # Calcula o custo total mensal
        custo_total_mensal = df_calc['CUSTO_MENSAL'].sum()
        
        # Calcula o percentual do custo sobre o total investido
        percentual_custo = (custo_total_mensal / valor_total_investido) * 100 if valor_total_investido > 0 else 0
        
        # Calcula a taxa média ponderada
        taxa_media_ponderada = np.average(
            df_calc['TAXA_ADM'], 
            weights=df_calc['VL_MERC_POS_FINAL'],
            returned=False
        ) if valor_total_investido > 0 else 0
        
        # Extrai o ano e mês da data
        partes_data = data.split('-')
        if len(partes_data) >= 2:
            ano = partes_data[0]
            mes = partes_data[1] if len(partes_data) > 1 else '01'
        else:
            ano = data
            mes = '01'
        
        # Armazena os resultados
        resultados[data] = {
            'valor_total_investido': valor_total_investido,
            'custo_total_mensal': custo_total_mensal,
            'percentual_custo': percentual_custo,
            'taxa_media_ponderada': taxa_media_ponderada,
            'detalhes': df_calc
        }
        
        # Exibe os resultados
        print(f"  - Valor total investido: R$ {valor_total_investido:,.2f}")
        print(f"  - Custo total mensal com taxas: R$ {custo_total_mensal:,.2f}")
        print(f"  - Percentual do custo sobre total investido: {percentual_custo:.4f}%")
        print(f"  - Taxa média ponderada: {taxa_media_ponderada:.4f}%")
        
        # Adiciona ao DataFrame consolidado
        registros_consolidados.append({
            'Periodo': data,
            'Ano': ano,
            'Mes': mes,
            'Valor_Total_Investido': valor_total_investido,
            'Custo_Mensal_Total': custo_total_mensal,
            'Percentual_Custo': percentual_custo,
            'Taxa_Media_Ponderada': taxa_media_ponderada,
            'Numero_Fundos': len(df_calc)
        })
        
        # Analisa os fundos com maior custo
        top_fundos = df_calc.sort_values('CUSTO_MENSAL', ascending=False).head(5)
        print("\n  - Top 5 fundos com maior custo mensal:")
        for i, (_, row) in enumerate(top_fundos.iterrows(), 1):
            nome_fundo = None
            for col in ['NM_FUNDO_COTA', 'NM_FUNDO_CLASSE_SUBCLASSE_COTA', 'DENOM_SOCIAL_EMISSOR']:
                if col in row.index and not pd.isna(row[col]):
                    nome_fundo = row[col]
                    break
                    
            if nome_fundo is None:
                nome_fundo = "Nome não disponível"
                
            cnpj = None
            for col in ['CNPJ_FUNDO_COTA', 'CNPJ_FUNDO_CLASSE_COTA', 'CPF_CNPJ_EMISSOR']:
                if col in row.index and not pd.isna(row[col]):
                    cnpj = row[col]
                    break
                    
            if cnpj is None:
                cnpj = "CNPJ não disponível"
                
            print(f"    {i}. {nome_fundo[:60]}...")
            print(f"       CNPJ: {cnpj}")
            print(f"       Valor Investido: R$ {row['VL_MERC_POS_FINAL']:,.2f}")
            print(f"       Taxa ADM: {row['TAXA_ADM']:.2f}%")
            print(f"       Custo Mensal: R$ {row['CUSTO_MENSAL']:,.2f}")
    
    # Cria DataFrame com resultados consolidados
    df_consolidado = pd.DataFrame(registros_consolidados)
    
    # Ordena por período
    if not df_consolidado.empty:
        df_consolidado = df_consolidado.sort_values('Periodo')
        
        # Calcula valores anualizados
        df_consolidado['Custo_Anual_Estimado'] = df_consolidado['Custo_Mensal_Total'] * 12
        
        # Exibe estatísticas consolidadas
        print("\nEstatísticas consolidadas:")
        print(f"Número total de períodos analisados: {len(df_consolidado)}")
        
        if len(df_consolidado) > 0:
            media_taxa = df_consolidado['Taxa_Media_Ponderada'].mean()
            media_percentual_custo = df_consolidado['Percentual_Custo'].mean()
            media_valor_investido = df_consolidado['Valor_Total_Investido'].mean()
            media_custo_mensal = df_consolidado['Custo_Mensal_Total'].mean()
            
            print(f"Taxa média ponderada média: {media_taxa:.4f}%")
            print(f"Percentual de custo médio: {media_percentual_custo:.4f}%")
            print(f"Valor médio investido: R$ {media_valor_investido:,.2f}")
            print(f"Custo mensal médio: R$ {media_custo_mensal:,.2f}")
            print(f"Custo anual estimado médio: R$ {media_custo_mensal*12:,.2f}")
        
        # Salva resultados se especificado
        if dir_saida:
            import os
            
            # Cria diretório se não existir
            if not os.path.exists(dir_saida):
                os.makedirs(dir_saida)
                
            # Salva o consolidado
            arquivo_consolidado = os.path.join(dir_saida, "custos_taxas_consolidado.csv")
            df_consolidado.to_csv(arquivo_consolidado, index=False, encoding='utf-8-sig')
            print(f"\nArquivo consolidado salvo em: {arquivo_consolidado}")
            
            # Salva os detalhes de cada período
            dir_detalhes = os.path.join(dir_saida, "detalhes_por_periodo")
            if not os.path.exists(dir_detalhes):
                os.makedirs(dir_detalhes)
                
            for data, resultado in resultados.items():
                arquivo_detalhe = os.path.join(dir_detalhes, f"custos_{data.replace('-', '')}.csv")
                resultado['detalhes'].to_csv(arquivo_detalhe, index=False, encoding='utf-8-sig')
            
            print(f"Detalhes por período salvos em: {dir_detalhes}")
    
    return resultados


def analisar_evolucao_custos(resultados, dir_saida=None):

    if not resultados:
        print("Sem resultados para analisar.")
        return
    
    print("\nAnalisando evolução dos custos ao longo do tempo...")
    
    # Extrair dados consolidados
    dados = [
        {
            'Periodo': data,
            'Valor_Total': resultado['valor_total_investido'],
            'Custo_Mensal': resultado['custo_total_mensal'],
            'Percentual_Custo': resultado['percentual_custo'],
            'Taxa_Media': resultado['taxa_media_ponderada']
        }
        for data, resultado in resultados.items()
    ]
    
    # Converter para DataFrame
    df_evolucao = pd.DataFrame(dados)
    
    # Ordenar por período
    df_evolucao = df_evolucao.sort_values('Periodo')
    
    # Converter período para datetime para melhor formatação nos gráficos
    df_evolucao['Data'] = pd.to_datetime(df_evolucao['Periodo'] + '-01', errors='coerce', format='%Y-%m-%d')
    
    # Calcular custo anualizado
    df_evolucao['Custo_Anual'] = df_evolucao['Custo_Mensal'] * 12
    
    # Calcular variações
    df_evolucao['Var_Valor_Total'] = df_evolucao['Valor_Total'].pct_change() * 100
    df_evolucao['Var_Custo_Mensal'] = df_evolucao['Custo_Mensal'].pct_change() * 100
    df_evolucao['Var_Taxa_Media'] = df_evolucao['Taxa_Media'] - df_evolucao['Taxa_Media'].shift(1)
    
    # Exibir resumo
    print("\nResumo da evolução:")
    if len(df_evolucao) > 1:
        primeiro_periodo = df_evolucao.iloc[0]['Periodo']
        ultimo_periodo = df_evolucao.iloc[-1]['Periodo']
        
        primeiro_valor = df_evolucao.iloc[0]['Valor_Total']
        ultimo_valor = df_evolucao.iloc[-1]['Valor_Total']
        
        primeiro_custo = df_evolucao.iloc[0]['Custo_Mensal']
        ultimo_custo = df_evolucao.iloc[-1]['Custo_Mensal']
        
        primeira_taxa = df_evolucao.iloc[0]['Taxa_Media']
        ultima_taxa = df_evolucao.iloc[-1]['Taxa_Media']
        
        var_valor = ((ultimo_valor / primeiro_valor) - 1) * 100
        var_custo = ((ultimo_custo / primeiro_custo) - 1) * 100
        var_taxa = ultima_taxa - primeira_taxa
        
        print(f"Período de análise: {primeiro_periodo} a {ultimo_periodo}")
        print(f"Variação no valor total investido: {var_valor:.2f}%")
        print(f"Variação no custo mensal: {var_custo:.2f}%")
        print(f"Variação na taxa média ponderada: {var_taxa:.4f} pontos percentuais")
        
        # Tendências
        tendencia_valor = "crescente" if var_valor > 0 else "decrescente"
        tendencia_custo = "crescente" if var_custo > 0 else "decrescente"
        tendencia_taxa = "crescente" if var_taxa > 0 else "decrescente"
        
        print(f"\nTendências identificadas:")
        print(f"- Valor total investido: {tendencia_valor}")
        print(f"- Custo mensal: {tendencia_custo}")
        print(f"- Taxa média ponderada: {tendencia_taxa}")
    
    # Salvar análise
    if dir_saida:
        import os
        
        # Cria diretório se não existir
        if not os.path.exists(dir_saida):
            os.makedirs(dir_saida)
            
        # Salva a evolução
        arquivo_evolucao = os.path.join(dir_saida, "evolucao_custos.csv")
        df_evolucao.to_csv(arquivo_evolucao, index=False, encoding='utf-8-sig')
        print(f"\nEvolução dos custos salva em: {arquivo_evolucao}")
        
        # Tenta gerar gráficos melhorados se matplotlib estiver disponível
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            import matplotlib.ticker as mtick
            from matplotlib.ticker import FuncFormatter
            import seaborn as sns
            
            # Configurações gerais para os gráficos
            sns.set_style("whitegrid", {'grid.linestyle': ':'})
            plt.rcParams['font.family'] = 'sans-serif'
            plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
            plt.rcParams['axes.facecolor'] = 'white'
            plt.rcParams['axes.edgecolor'] = '#666666'
            plt.rcParams['axes.labelcolor'] = '#333333'
            plt.rcParams['figure.facecolor'] = 'white'
            plt.rcParams['text.color'] = '#333333'
            plt.rcParams['grid.color'] = '#aaaaaa'
            plt.rcParams['grid.alpha'] = 0.3
            
            # Cria diretório para gráficos
            dir_graficos = os.path.join(dir_saida, "graficos")
            if not os.path.exists(dir_graficos):
                os.makedirs(dir_graficos)
            
            # Formatador para valores em reais
            def formatador_reais(x, pos):
                return f'R$ {x/1e6:.1f}M' if x >= 1e6 else f'R$ {x/1e3:.0f}K'
            
            # Formatador para datas mais legíveis
            # Selecionar algumas datas representativas para o eixo X
            num_datas = len(df_evolucao)
            
            # Definir intervalo de datas para o eixo X
            if num_datas <= 12:
                # Se houver 12 ou menos datas, mostrar todas
                datas_eixo = df_evolucao['Data']
                intervalo = 1
            elif num_datas <= 24:
                # Se houver entre 13 e 24 datas, mostrar a cada 2 meses
                intervalo = 2
            elif num_datas <= 36:
                # Se houver entre 25 e 36 datas, mostrar a cada 3 meses
                intervalo = 3
            elif num_datas <= 60:
                # Se houver entre 37 e 60 datas, mostrar a cada 6 meses
                intervalo = 6
            else:
                # Se houver mais de 60 datas, mostrar a cada 12 meses
                intervalo = 12
            
            # Gráfico 1: Evolução do valor total investido e custo mensal
            plt.figure(figsize=(12, 7))
            
            # Dois eixos Y para diferentes escalas
            ax1 = plt.gca()
            ax2 = ax1.twinx()
            
            # Cores mais atraentes
            cor_valor = '#1f77b4'  # Azul mais intenso
            cor_custo = '#ff7f0e'  # Laranja mais intenso
            
            # Plotar valor total no eixo Y1
            ax1.plot(df_evolucao['Data'], df_evolucao['Valor_Total'], color=cor_valor, marker='o', 
                    markersize=4, linewidth=2, label='Valor Total Investido')
            ax1.set_ylabel('Valor Total Investido', fontsize=12, color=cor_valor)
            ax1.tick_params(axis='y', labelcolor=cor_valor)
            ax1.yaxis.set_major_formatter(FuncFormatter(formatador_reais))
            
            # Plotar custo mensal no eixo Y2
            ax2.plot(df_evolucao['Data'], df_evolucao['Custo_Mensal'], color=cor_custo, marker='x', 
                    markersize=5, linewidth=2, label='Custo Mensal')
            ax2.set_ylabel('Custo Mensal', fontsize=12, color=cor_custo)
            ax2.tick_params(axis='y', labelcolor=cor_custo)
            ax2.yaxis.set_major_formatter(FuncFormatter(formatador_reais))
            
            # Configuração do eixo X para mostrar datas em formato legível
            ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=intervalo))
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b/%Y'))
            plt.xticks(rotation=45, ha='right')
            
            # Configurações do gráfico
            plt.title('Evolução do Valor Total Investido e Custo Mensal', fontsize=14, pad=20)
            
            # Legenda combinada
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', frameon=True, 
                      facecolor='white', framealpha=0.9, fontsize=10)
            
            plt.tight_layout()
            
            # Adicionar bordas sutis
            for spine in ax1.spines.values():
                spine.set_color('#dddddd')
                spine.set_linewidth(0.8)
            
            # Salvar gráfico com melhor resolução
            plt.savefig(os.path.join(dir_graficos, "evolucao_valor_custo.png"), dpi=300, bbox_inches='tight')
            plt.close()
            
            # Gráfico 2: Evolução da taxa média ponderada
            plt.figure(figsize=(12, 6))
            
            cor_taxa = '#2ca02c'  # Verde mais intenso
            
            ax = plt.gca()
            plt.plot(df_evolucao['Data'], df_evolucao['Taxa_Media'], color=cor_taxa, marker='o', 
                   markersize=4, linewidth=2)
            
            # Formatação do eixo Y como percentual
            ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=2))
            
            # Configuração do eixo X para mostrar datas em formato legível
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=intervalo))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b/%Y'))
            plt.xticks(rotation=45, ha='right')
            
            plt.title('Evolução da Taxa Média Ponderada', fontsize=14, pad=20)
            plt.ylabel('Taxa Média', fontsize=12)
            
            # Grade mais sutil
            plt.grid(alpha=0.3, linestyle=':')
            
            # Adicionar bordas sutis
            for spine in ax.spines.values():
                spine.set_color('#dddddd')
                spine.set_linewidth(0.8)
            
            plt.tight_layout()
            
            # Salvar gráfico com melhor resolução
            plt.savefig(os.path.join(dir_graficos, "evolucao_taxa_media.png"), dpi=300, bbox_inches='tight')
            plt.close()
            
            # Gráfico 3: Evolução do percentual de custo
            plt.figure(figsize=(12, 6))
            
            cor_percentual = '#d62728'  # Vermelho mais intenso
            
            ax = plt.gca()
            plt.plot(df_evolucao['Data'], df_evolucao['Percentual_Custo'], color=cor_percentual, marker='o', 
                   markersize=4, linewidth=2)
            
            # Formatação do eixo Y como percentual
            ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=3))
            
            # Configuração do eixo X para mostrar datas em formato legível
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=intervalo))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b/%Y'))
            plt.xticks(rotation=45, ha='right')
            
            plt.title('Evolução do Percentual de Custo Mensal', fontsize=14, pad=20)
            plt.ylabel('Percentual de Custo', fontsize=12)
            
            # Grade mais sutil
            plt.grid(alpha=0.3, linestyle=':')
            
            # Adicionar bordas sutis
            for spine in ax.spines.values():
                spine.set_color('#dddddd')
                spine.set_linewidth(0.8)
            
            plt.tight_layout()
            
            # Salvar gráfico com melhor resolução
            plt.savefig(os.path.join(dir_graficos, "evolucao_percentual_custo.png"), dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"Gráficos aprimorados salvos em: {dir_graficos}")
        except Exception as e:
            print(f"Não foi possível gerar gráficos: {str(e)}")


def analisar_fundos_sem_taxa(carteiras_com_taxas, dir_saida=None):
 
    print("Iniciando análise de fundos com taxa zero ou sem taxa...")
    
    if dir_saida and not os.path.exists(dir_saida):
        os.makedirs(dir_saida)
    
    # Dicionário para armazenar os resultados
    fundos_sem_taxa = {}
    
    # Para cada período, identifica fundos sem taxa
    for data, df in carteiras_com_taxas.items():
        print(f"\nAnalisando período: {data}")
        
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
        
        # Identifica a coluna que contém o nome dos fundos
        coluna_nome = None
        for col in ['NM_FUNDO_CLASSE_SUBCLASSE_COTA', 'NM_FUNDO_COTA', 'DENOM_SOCIAL_EMISSOR']:
            if col in df.columns:
                coluna_nome = col
                break
        
        # Seleção de fundos com taxa zero ou NaN
        df_sem_taxa = df[(df['TAXA_ADM'].isna()) | (df['TAXA_ADM'] == 0)]
        
        # Conta fundos por categoria
        total_fundos = len(df)
        n_taxa_zero = len(df[df['TAXA_ADM'] == 0])
        n_taxa_nan = len(df[df['TAXA_ADM'].isna()])
        
        print(f"  - Total de fundos: {total_fundos}")
        print(f"  - Fundos com taxa zero: {n_taxa_zero} ({n_taxa_zero/total_fundos*100:.1f}%)")
        print(f"  - Fundos sem informação de taxa: {n_taxa_nan} ({n_taxa_nan/total_fundos*100:.1f}%)")
        
        # Se houver fundos sem taxa, processa cada um
        if len(df_sem_taxa) > 0:
            print(f"  - Detalhando {len(df_sem_taxa)} fundos sem taxa ou com taxa zero:")
            
            for _, row in df_sem_taxa.iterrows():
                cnpj = row[coluna_cnpj]
                
                # Obtém o nome do fundo
                nome_fundo = row[coluna_nome] if coluna_nome in df.columns else "Nome não disponível"
                
                # Informações de valor
                valor = row['VL_MERC_POS_FINAL'] if 'VL_MERC_POS_FINAL' in df.columns else np.nan
                
                # Inicializa o dicionário para este fundo se ainda não existir
                if cnpj not in fundos_sem_taxa:
                    fundos_sem_taxa[cnpj] = {
                        'nome': nome_fundo,
                        'periodos': {},
                        'total_periodos': 0,
                        'valor_medio': 0,
                        'tipo_taxa': 'zero' if row['TAXA_ADM'] == 0 else 'nan'
                    }
                
                # Adiciona informações deste período
                fundos_sem_taxa[cnpj]['periodos'][data] = {
                    'valor': valor,
                    'taxa': row['TAXA_ADM'],
                    'dados_completos': row.to_dict()
                }
                
                fundos_sem_taxa[cnpj]['total_periodos'] += 1
            
            # Se especificado, salva a análise do período
            if dir_saida:
                arquivo_periodo = os.path.join(dir_saida, f"fundos_sem_taxa_{data.replace('-', '')}.csv")
                df_sem_taxa.to_csv(arquivo_periodo, index=False, encoding='utf-8-sig')
                print(f"  - Análise do período salva em: {arquivo_periodo}")
    
    # Calcula estatísticas agregadas para cada fundo
    for cnpj, info in fundos_sem_taxa.items():
        valores = [periodo['valor'] for periodo in info['periodos'].values() 
                   if not np.isnan(periodo['valor'])]
        
        if valores:
            info['valor_medio'] = np.mean(valores)
            info['valor_total_ultimo'] = valores[-1] if valores else np.nan
    
    # Gera um relatório consolidado com os fundos sem taxa
    if fundos_sem_taxa:
        # Converte para DataFrame para facilitar a análise
        df_resumo = pd.DataFrame([
            {
                'CNPJ': cnpj,
                'Nome': info['nome'],
                'Tipo_Taxa': info['tipo_taxa'],
                'Total_Periodos': info['total_periodos'],
                'Valor_Medio': info['valor_medio'],
                'Valor_Total_Ultimo': info.get('valor_total_ultimo', np.nan)
            }
            for cnpj, info in fundos_sem_taxa.items()
        ])
        
        # Ordena por número de períodos (decrescente)
        df_resumo = df_resumo.sort_values('Total_Periodos', ascending=False)
        
        print("\nResumo dos fundos sem taxa ou com taxa zero:")
        print(f"Total de fundos identificados: {len(fundos_sem_taxa)}")
        
        # Exibe os top fundos
        top_n = min(10, len(df_resumo))
        print(f"\nTop {top_n} fundos por número de períodos:")
        for i, row in df_resumo.head(top_n).iterrows():
            print(f"  {row['Nome']} (CNPJ: {row['CNPJ']})")
            print(f"    - Períodos: {row['Total_Periodos']}")
            print(f"    - Tipo: Taxa {'Zero' if row['Tipo_Taxa'] == 'zero' else 'Não Informada'}")
            print(f"    - Valor Médio: R$ {row['Valor_Medio']:,.2f}")
        
        # Se especificado, salva o relatório consolidado
        if dir_saida:
            arquivo_resumo = os.path.join(dir_saida, "resumo_fundos_sem_taxa.csv")
            df_resumo.to_csv(arquivo_resumo, index=False, encoding='utf-8-sig')
            print(f"\nRelatório consolidado salvo em: {arquivo_resumo}")
            
            # Cria visualização dos dados
            if len(df_resumo) > 1:
                try:
                    # Gráfico de barras com os top fundos por número de períodos
                    plt.figure(figsize=(12, 8))
                    
                    # Limita o número de fundos para visualização
                    df_plot = df_resumo.head(min(15, len(df_resumo)))
                    
                    # Cria nomes curtos para o gráfico
                    df_plot['Nome_Curto'] = df_plot['Nome'].str.slice(0, 30) + '...'
                    
                    # Barras coloridas por tipo de taxa
                    cores = {'zero': 'blue', 'nan': 'orange'}
                    
                    # Cria o gráfico
                    ax = sns.barplot(
                        x='Total_Periodos', 
                        y='Nome_Curto', 
                        data=df_plot,
                        hue='Tipo_Taxa',
                        palette=cores
                    )
                    
                    plt.title('Top Fundos sem Taxa ou com Taxa Zero por Número de Períodos')
                    plt.xlabel('Número de Períodos')
                    plt.ylabel('Fundo')
                    plt.tight_layout()
                    
                    # Salva o gráfico
                    arquivo_grafico = os.path.join(dir_saida, "grafico_fundos_sem_taxa.png")
                    plt.savefig(arquivo_grafico)
                    print(f"Gráfico salvo em: {arquivo_grafico}")
                except Exception as e:
                    print(f"Erro ao gerar gráfico: {str(e)}")
    
    return fundos_sem_taxa


# def calcular_taxa_efetiva_fundos_zero_taxa(carteiras_originais, cnpjs_sem_taxa, dir_saida=None, base_dir=None, limite_arquivos=10):
    
#     # Verificar se o diretório base foi fornecido
#     if base_dir is None:
#         raise ValueError("base_dir é necessário para processar as carteiras")
    
#     print("\nCalculando taxas efetivas para fundos sem taxa...")
    
#     # Cria diretório de saída se especificado
#     if dir_saida and not os.path.exists(dir_saida):
#         os.makedirs(dir_saida)
    
#     # Carregar cadastro de fundos (só uma vez)
#     arquivo_local = os.path.join(base_dir, 'CAD', 'cad_fi.csv')
#     fund_info = pd.read_csv(arquivo_local, sep=';', encoding='ISO-8859-1', low_memory=False)
    
#     # Dicionário para armazenar resultados
#     taxas_efetivas = {}
    
#     # DataFrame para consolidar resultados
#     registros_consolidados = []
    
#     # Para cada fundo sem taxa
#     for i, cnpj_alvo in enumerate(cnpjs_sem_taxa):
#         print(f"\n[{i+1}/{len(cnpjs_sem_taxa)}] Analisando fundo com CNPJ: {cnpj_alvo}")
        
#         # Obter o nome do fundo (se disponível)
#         nome_fundo = "Nome não disponível"
#         for data, df in carteiras_originais.items():
#             coluna_cnpj = None
#             for col in ['CNPJ_FUNDO_CLASSE_COTA', 'CNPJ_FUNDO_COTA', 'CPF_CNPJ_EMISSOR', 'CNPJ_EMISSOR']:
#                 if col in df.columns:
#                     coluna_cnpj = col
#                     break
            
#             if coluna_cnpj is None:
#                 continue
                
#             coluna_nome = None
#             for col in ['NM_FUNDO_CLASSE_SUBCLASSE_COTA', 'NM_FUNDO_COTA', 'DENOM_SOCIAL_EMISSOR']:
#                 if col in df.columns:
#                     coluna_nome = col
#                     break
                    
#             df_fundo = df[df[coluna_cnpj] == cnpj_alvo]
#             if len(df_fundo) > 0 and coluna_nome in df.columns:
#                 nome_fundo = df_fundo.iloc[0][coluna_nome]
#                 break
        
#         print(f"Processando carteiras para o fundo: {nome_fundo}")
        
#         try:
#             # Processar as carteiras deste fundo
#             carteiras_fundo = processar_carteiras(cnpj_alvo, base_dir, limite_arquivos)
            
#             # Verificar se encontrou algum dado
#             if not carteiras_fundo:
#                 print(f"  - Nenhuma carteira encontrada para o fundo {cnpj_alvo}")
#                 continue
                
#             # Adicionar taxas de administração
#             carteiras_com_taxas = adicionar_taxas_administracao(carteiras_fundo, fund_info)
            
#             if adicionar_taxas_manuais:
#                 # Adicionar taxas manuais se a função estiver disponível
#                 carteiras_com_taxas = adicionar_taxas_manuais(carteiras_com_taxas, fund_info)
            
#             # Calcular a taxa efetiva para cada período
#             resultados_por_periodo = {}
            
#             for data, df_carteira in carteiras_com_taxas.items():
#                 # Verificar colunas necessárias
#                 if 'TAXA_ADM' not in df_carteira.columns or 'VL_MERC_POS_FINAL' not in df_carteira.columns:
#                     print(f"  - Colunas necessárias não encontradas para o período {data}")
#                     continue
                
#                 # Converter para numérico
#                 df_carteira['TAXA_ADM'] = pd.to_numeric(df_carteira['TAXA_ADM'], errors='coerce')
#                 df_carteira['VL_MERC_POS_FINAL'] = pd.to_numeric(df_carteira['VL_MERC_POS_FINAL'], errors='coerce')
                
#                 # Filtra apenas registros com dados válidos
#                 df_validos = df_carteira.dropna(subset=['TAXA_ADM', 'VL_MERC_POS_FINAL'])
                
#                 # Verificar se tem dados suficientes
#                 if len(df_validos) == 0:
#                     print(f"  - Sem dados válidos para o período {data}")
#                     continue
                
#                 # Calcular valor total investido
#                 valor_total = df_validos['VL_MERC_POS_FINAL'].sum()
                
#                 if valor_total == 0:
#                     print(f"  - Valor total investido é zero no período {data}")
#                     continue
                
#                 # Calcular taxa média ponderada
#                 taxa_ponderada = np.average(
#                     df_validos['TAXA_ADM'],
#                     weights=df_validos['VL_MERC_POS_FINAL'],
#                     returned=False
#                 )
                
#                 # Calcular outras estatísticas
#                 n_fundos_investidos = len(df_validos)
#                 n_sem_taxa = df_validos['TAXA_ADM'].isna().sum() + (df_validos['TAXA_ADM'] == 0).sum()
#                 perc_sem_taxa = (n_sem_taxa / n_fundos_investidos * 100) if n_fundos_investidos > 0 else 0
                
#                 print(f"  - Período {data}: Taxa efetiva = {taxa_ponderada:.4f}%, {n_fundos_investidos} fundos, R$ {valor_total:,.2f}")
                
#                 # Armazenar o resultado
#                 resultados_por_periodo[data] = {
#                     'taxa_efetiva': taxa_ponderada,
#                     'valor_total': valor_total,
#                     'num_fundos': n_fundos_investidos,
#                     'num_sem_taxa': n_sem_taxa,
#                     'perc_sem_taxa': perc_sem_taxa,
#                     'detalhes': df_validos.copy()
#                 }
                
#                 # Adicionar ao consolidado
#                 registros_consolidados.append({
#                     'CNPJ': cnpj_alvo,
#                     'Nome': nome_fundo,
#                     'Periodo': data,
#                     'Taxa_Efetiva': taxa_ponderada,
#                     'Valor_Total': valor_total,
#                     'Num_Fundos': n_fundos_investidos,
#                     'Num_Sem_Taxa': n_sem_taxa,
#                     'Perc_Sem_Taxa': perc_sem_taxa
#                 })
            
#             # Adicionar ao dicionário de resultados
#             if resultados_por_periodo:
#                 # Calcular média da taxa efetiva ao longo do tempo
#                 taxas = [res['taxa_efetiva'] for res in resultados_por_periodo.values()]
#                 taxa_media = sum(taxas) / len(taxas) if taxas else 0
                
#                 # Último valor disponível
#                 ultimo_periodo = max(resultados_por_periodo.keys()) if resultados_por_periodo else None
#                 ultima_taxa = resultados_por_periodo[ultimo_periodo]['taxa_efetiva'] if ultimo_periodo else 0
                
#                 taxas_efetivas[cnpj_alvo] = {
#                     'nome': nome_fundo,
#                     'taxa_media': taxa_media,
#                     'ultima_taxa': ultima_taxa,
#                     'ultimo_periodo': ultimo_periodo,
#                     'total_periodos': len(resultados_por_periodo),
#                     'resultados': resultados_por_periodo
#                 }
                
#                 print(f"  ✓ Taxa efetiva média: {taxa_media:.4f}%")
#                 if ultimo_periodo:
#                     print(f"  ✓ Taxa no último período ({ultimo_periodo}): {ultima_taxa:.4f}%")
#             else:
#                 print(f"  ✗ Nenhum período com dados válidos encontrado")
                
#         except Exception as e:
#             print(f"  ✗ Erro ao processar fundo {cnpj_alvo}: {str(e)}")
    
#     # Criar DataFrame consolidado
#     df_consolidado = pd.DataFrame(registros_consolidados)
    
#     # Salvar resultados
#     if dir_saida and not df_consolidado.empty:
#         # Salvar consolidado
#         arquivo_consolidado = os.path.join(dir_saida, "taxas_efetivas_consolidado.csv")
#         df_consolidado.to_csv(arquivo_consolidado, index=False, encoding='utf-8-sig')
#         print(f"\nArquivo consolidado salvo em: {arquivo_consolidado}")
        
#         # Gerar resumo por fundo
#         df_resumo = df_consolidado.groupby('CNPJ').agg({
#             'Nome': 'first',
#             'Taxa_Efetiva': ['mean', 'min', 'max', 'std'],
#             'Valor_Total': 'mean',
#             'Periodo': 'count'
#         }).reset_index()
        
#         # Renomear colunas
#         df_resumo.columns = ['CNPJ', 'Nome', 'Taxa_Media', 'Taxa_Min', 'Taxa_Max', 
#                             'Taxa_Desvio', 'Valor_Medio', 'Num_Periodos']
        
#         # Ordenar por taxa média
#         df_resumo = df_resumo.sort_values('Taxa_Media', ascending=False)
        
#         # Salvar resumo
#         arquivo_resumo = os.path.join(dir_saida, "taxas_efetivas_resumo.csv")
#         df_resumo.to_csv(arquivo_resumo, index=False, encoding='utf-8-sig')
#         print(f"Resumo por fundo salvo em: {arquivo_resumo}")
        
#         # Criar visualizações
#         try:
#             # Configurar estilo
#             sns.set_style("whitegrid")
            
#             # Diretório para gráficos
#             dir_graficos = os.path.join(dir_saida, "graficos")
#             if not os.path.exists(dir_graficos):
#                 os.makedirs(dir_graficos)
            
#             # Gráfico 1: Comparação de taxas efetivas entre fundos
#             if len(df_resumo) > 1:
#                 plt.figure(figsize=(12, 8))
                
#                 # Limita o número de fundos para visualização
#                 df_plot = df_resumo.head(min(15, len(df_resumo)))
                
#                 # Cria nomes curtos para o gráfico
#                 df_plot['Nome_Curto'] = df_plot['Nome'].str.slice(0, 30) + '...'
                
#                 # Cria o gráfico
#                 ax = sns.barplot(
#                     x='Taxa_Media', 
#                     y='Nome_Curto',
#                     data=df_plot
#                 )
                
#                 plt.title('Taxa Efetiva Média por Fundo')
#                 plt.xlabel('Taxa Efetiva (%)')
#                 plt.ylabel('Fundo')
#                 plt.tight_layout()
                
#                 # Salva o gráfico
#                 arquivo_grafico = os.path.join(dir_graficos, "comparacao_taxas_efetivas.png")
#                 plt.savefig(arquivo_grafico)
#                 plt.close()
                
#                 print(f"Gráfico de comparação de taxas salvo em: {arquivo_grafico}")
            
#             # Gráfico 2: Evolução da taxa efetiva ao longo do tempo para os principais fundos
#             top_cnpjs = df_resumo.head(5)['CNPJ'].tolist()
            
#             # Filtrar apenas os top fundos
#             df_top = df_consolidado[df_consolidado['CNPJ'].isin(top_cnpjs)]
            
#             if not df_top.empty:
#                 plt.figure(figsize=(12, 6))
                
#                 # Converter período para datetime
#                 df_top['Data'] = pd.to_datetime(df_top['Periodo'] + '-01', errors='coerce', format='%Y-%m-%d')
                
#                 # Plotar cada fundo
#                 for cnpj in top_cnpjs:
#                     df_fundo = df_top[df_top['CNPJ'] == cnpj]
#                     if not df_fundo.empty:
#                         nome_curto = df_fundo['Nome'].iloc[0][:20] + '...'
#                         plt.plot(df_fundo['Data'], df_fundo['Taxa_Efetiva'], marker='o', label=nome_curto)
                
#                 plt.title('Evolução da Taxa Efetiva dos Principais Fundos')
#                 plt.xlabel('Período')
#                 plt.ylabel('Taxa Efetiva (%)')
#                 plt.legend()
#                 plt.grid(True, alpha=0.3)
#                 plt.tight_layout()
                
#                 # Salva o gráfico
#                 arquivo_grafico = os.path.join(dir_graficos, "evolucao_taxas_efetivas.png")
#                 plt.savefig(arquivo_grafico)
#                 plt.close()
                
#                 print(f"Gráfico de evolução de taxas salvo em: {arquivo_grafico}")
                
#             # Gráfico 3: Distribuição das taxas efetivas
#             if len(df_resumo) > 5:
#                 plt.figure(figsize=(10, 6))
                
#                 sns.histplot(df_resumo['Taxa_Media'], kde=True)
                
#                 plt.title('Distribuição das Taxas Efetivas Médias')
#                 plt.xlabel('Taxa Efetiva (%)')
#                 plt.ylabel('Frequência')
#                 plt.tight_layout()
                
#                 # Salva o gráfico
#                 arquivo_grafico = os.path.join(dir_graficos, "distribuicao_taxas_efetivas.png")
#                 plt.savefig(arquivo_grafico)
#                 plt.close()
                
#                 print(f"Gráfico de distribuição de taxas salvo em: {arquivo_grafico}")
                
#         except Exception as e:
#             print(f"Erro ao gerar gráficos: {str(e)}")
    
#     print("\nProcessamento concluído!")
#     return taxas_efetivas


def calcular_taxa_efetiva_fundos_zero_taxa(carteiras_originais, cnpjs_sem_taxa, dir_saida, base_dir=None, limite_arquivos=10):
    import math
    import os
    import pandas as pd
    import numpy as np
    import seaborn as sns
    import matplotlib.pyplot as plt

    # Verificar se o diretório base foi fornecido
    if base_dir is None:
        raise ValueError("base_dir é necessário para processar as carteiras")

    print("\nCalculando taxas efetivas para fundos sem taxa...")

    # Cria diretório de saída se especificado
    if dir_saida and not os.path.exists(dir_saida):
        os.makedirs(dir_saida)

    # Carregar cadastro de fundos (só uma vez)
    arquivo_local = os.path.join(base_dir, 'CAD', 'cad_fi.csv')
    fund_info = pd.read_csv(arquivo_local, sep=';', encoding='ISO-8859-1', low_memory=False)

    # Dicionário para armazenar resultados
    taxas_efetivas = {}

    # DataFrame para consolidar resultados
    registros_consolidados = []

    # Para cada fundo sem taxa
    for i, cnpj_alvo in enumerate(cnpjs_sem_taxa):
        print(f"\n[{i+1}/{len(cnpjs_sem_taxa)}] Analisando fundo com CNPJ: {cnpj_alvo}")

        # Obter o nome do fundo (se disponível)
        nome_fundo = "Nome não disponível"
        for data, df in carteiras_originais.items():
            coluna_cnpj = None
            for col in ['CNPJ_FUNDO_CLASSE_COTA', 'CNPJ_FUNDO_COTA', 'CPF_CNPJ_EMISSOR', 'CNPJ_EMISSOR']:
                if col in df.columns:
                    coluna_cnpj = col
                    break

            if coluna_cnpj is None:
                continue

            coluna_nome = None
            for col in ['NM_FUNDO_CLASSE_SUBCLASSE_COTA', 'NM_FUNDO_COTA', 'DENOM_SOCIAL_EMISSOR']:
                if col in df.columns:
                    coluna_nome = col
                    break

            df_fundo = df[df[coluna_cnpj] == cnpj_alvo]
            if len(df_fundo) > 0 and coluna_nome in df.columns:
                nome_fundo = df_fundo.iloc[0][coluna_nome]
                break

        print(f"Processando carteiras para o fundo: {nome_fundo}")

        try:
            # Processar as carteiras deste fundo
            carteiras_fundo = processar_carteiras(cnpj_alvo, base_dir, limite_arquivos)

            # Verificar se encontrou algum dado
            if not carteiras_fundo:
                print(f"  - Nenhuma carteira encontrada para o fundo {cnpj_alvo}")
                continue

            # Adicionar taxas de administração
            carteiras_com_taxas = adicionar_taxas_administracao(carteiras_fundo, fund_info)

            if adicionar_taxas_manuais:
                # Adicionar taxas manuais se a função estiver disponível
                carteiras_com_taxas = adicionar_taxas_manuais(carteiras_com_taxas, fund_info)

            # Calcular a taxa efetiva para cada período
            resultados_por_periodo = {}

            for data, df_carteira in carteiras_com_taxas.items():
                # Verificar colunas necessárias
                if 'TAXA_ADM' not in df_carteira.columns or 'VL_MERC_POS_FINAL' not in df_carteira.columns:
                    print(f"  - Colunas necessárias não encontradas para o período {data}")
                    continue

                # Converter para numérico
                df_carteira['TAXA_ADM'] = pd.to_numeric(df_carteira['TAXA_ADM'], errors='coerce')
                df_carteira['VL_MERC_POS_FINAL'] = pd.to_numeric(df_carteira['VL_MERC_POS_FINAL'], errors='coerce')

                # Filtra apenas registros com dados válidos
                df_validos = df_carteira.dropna(subset=['TAXA_ADM', 'VL_MERC_POS_FINAL'])

                # Verificar se tem dados suficientes
                if len(df_validos) == 0:
                    print(f"  - Sem dados válidos para o período {data}")
                    continue

                # Calcular valor total investido
                valor_total = df_validos['VL_MERC_POS_FINAL'].sum()

                if valor_total == 0:
                    print(f"  - Valor total investido é zero no período {data}")
                    continue

                # Calcular taxa média ponderada
                taxa_ponderada = np.average(
                    df_validos['TAXA_ADM'],
                    weights=df_validos['VL_MERC_POS_FINAL'],
                    returned=False
                )

                # Calcular outras estatísticas
                n_fundos_investidos = len(df_validos)
                n_sem_taxa = df_validos['TAXA_ADM'].isna().sum() + (df_validos['TAXA_ADM'] == 0).sum()
                perc_sem_taxa = (n_sem_taxa / n_fundos_investidos * 100) if n_fundos_investidos > 0 else 0

                print(f"  - Período {data}: Taxa efetiva = {taxa_ponderada:.4f}%, {n_fundos_investidos} fundos, R$ {valor_total:,.2f}")

                # Armazenar o resultado
                resultados_por_periodo[data] = {
                    'taxa_efetiva': taxa_ponderada,
                    'valor_total': valor_total,
                    'num_fundos': n_fundos_investidos,
                    'num_sem_taxa': n_sem_taxa,
                    'perc_sem_taxa': perc_sem_taxa,
                    'detalhes': df_validos.copy()
                }

                # Adicionar ao consolidado
                registros_consolidados.append({
                    'CNPJ': cnpj_alvo,
                    'Nome': nome_fundo,
                    'Periodo': data,
                    'Taxa_Efetiva': taxa_ponderada,
                    'Valor_Total': valor_total,
                    'Num_Fundos': n_fundos_investidos,
                    'Num_Sem_Taxa': n_sem_taxa,
                    'Perc_Sem_Taxa': perc_sem_taxa
                })

            # Adicionar ao dicionário de resultados
            if resultados_por_periodo:
                # Calcular média da taxa efetiva ao longo do tempo
                taxas = [res['taxa_efetiva'] for res in resultados_por_periodo.values()]
                taxa_media = sum(taxas) / len(taxas) if taxas else 0

                # Último valor disponível
                ultimo_periodo = max(resultados_por_periodo.keys()) if resultados_por_periodo else None
                ultima_taxa = resultados_por_periodo[ultimo_periodo]['taxa_efetiva'] if ultimo_periodo else 0

                taxas_efetivas[cnpj_alvo] = {
                    'nome': nome_fundo,
                    'taxa_media': taxa_media,
                    'ultima_taxa': ultima_taxa,
                    'ultimo_periodo': ultimo_periodo,
                    'total_periodos': len(resultados_por_periodo),
                    'resultados': resultados_por_periodo
                }

                print(f"  ✓ Taxa efetiva média: {taxa_media:.4f}%")
                if ultimo_periodo:
                    print(f"  ✓ Taxa no último período ({ultimo_periodo}): {ultima_taxa:.4f}%")
            else:
                print(f"  ✗ Nenhum período com dados válidos encontrado")

        except Exception as e:
            print(f"  ✗ Erro ao processar fundo {cnpj_alvo}: {str(e)}")

    # Criar DataFrame consolidado
    df_consolidado = pd.DataFrame(registros_consolidados)

    # Salvar resultados
    if dir_saida and not df_consolidado.empty:
        # Salvar consolidado
        arquivo_consolidado = os.path.join(dir_saida, "taxas_efetivas_consolidado.csv")
        df_consolidado.to_csv(arquivo_consolidado, index=False, encoding='utf-8-sig')
        print(f"\nArquivo consolidado salvo em: {arquivo_consolidado}")

        # Gerar resumo por fundo
        df_resumo = df_consolidado.groupby('CNPJ').agg({
            'Nome': 'first',
            'Taxa_Efetiva': ['mean', 'min', 'max', 'std'],
            'Valor_Total': 'mean',
            'Periodo': 'count'
        }).reset_index()

        # Renomear colunas
        df_resumo.columns = [
            'CNPJ', 'Nome', 'Taxa_Media', 'Taxa_Min',
            'Taxa_Max', 'Taxa_Desvio', 'Valor_Medio', 'Num_Periodos'
        ]

        # Ordenar por taxa média
        df_resumo = df_resumo.sort_values('Taxa_Media', ascending=False)

        # Salvar resumo
        arquivo_resumo = os.path.join(dir_saida, "taxas_efetivas_resumo.csv")
        df_resumo.to_csv(arquivo_resumo, index=False, encoding='utf-8-sig')
        print(f"Resumo por fundo salvo em: {arquivo_resumo}")

        # Criar visualizações
        try:
            # Configurar estilo
            sns.set_style("whitegrid")

            # Diretório para gráficos
            dir_graficos = os.path.join(dir_saida, "graficos")
            if not os.path.exists(dir_graficos):
                os.makedirs(dir_graficos)

            # Gráfico 1: Comparação de taxas efetivas entre fundos (Histórico)
            if len(df_resumo) > 1:
                plt.figure(figsize=(12, 8))

                # Limita o número de fundos para visualização
                df_plot = df_resumo.head(min(15, len(df_resumo)))

                # Cria nomes curtos para o gráfico
                df_plot['Nome_Curto'] = df_plot['Nome'].str.slice(0, 30) + '...'

                ax = sns.barplot(
                    x='Taxa_Media', 
                    y='Nome_Curto',
                    data=df_plot,
                    palette='Greys_d'
                )

                plt.title('Taxa Efetiva Média Histórica por Fundo')
                plt.xlabel('Taxa Efetiva (%)')
                plt.ylabel('Fundo')
                plt.grid(True, alpha=0.3)

                # Ajustar limite do eixo X
                max_taxa = df_plot['Taxa_Media'].max()
                max_limit = math.ceil(max_taxa * 4) / 4  # Arredonda para o próximo 0.25
                plt.xlim(0, max(1.75, max_limit))

                plt.tight_layout()

                arquivo_grafico = os.path.join(dir_graficos, "comparacao_taxas_efetivas.png")
                plt.savefig(arquivo_grafico)
                plt.close()

                print(f"Gráfico de comparação de taxas históricas salvo em: {arquivo_grafico}")

            # Gráfico 2: Evolução da taxa efetiva ao longo do tempo (para os top 5 fundos)
            top_cnpjs = df_resumo.head(5)['CNPJ'].tolist()
            df_top = df_consolidado[df_consolidado['CNPJ'].isin(top_cnpjs)]

            if not df_top.empty:
                plt.figure(figsize=(12, 6))
                # Converter período para datetime
                df_top['Data'] = pd.to_datetime(
                    df_top['Periodo'] + '-01',
                    errors='coerce',
                    format='%Y-%m-%d'
                )

                for cnpj in top_cnpjs:
                    df_fundo = df_top[df_top['CNPJ'] == cnpj]
                    if not df_fundo.empty:
                        nome_curto = df_fundo['Nome'].iloc[0][:20] + '...'
                        plt.plot(df_fundo['Data'], df_fundo['Taxa_Efetiva'], marker='o', label=nome_curto)

                plt.title('Evolução da Taxa Efetiva dos Principais Fundos')
                plt.xlabel('Período')
                plt.ylabel('Taxa Efetiva (%)')
                plt.legend()
                plt.grid(True, alpha=0.3)
                plt.tight_layout()

                arquivo_grafico = os.path.join(dir_graficos, "evolucao_taxas_efetivas.png")
                plt.savefig(arquivo_grafico)
                plt.close()

                print(f"Gráfico de evolução de taxas salvo em: {arquivo_grafico}")

            # Gráfico 3: **Distribuição das taxas efetivas** (ajuste de formatação)
            if len(df_resumo) > 5:
                plt.figure(figsize=(10, 6))

                # Plot do histograma com style mais consistente
                sns.histplot(
                    data=df_resumo,
                    x='Taxa_Media',
                    kde=True,
                    color='grey'  # Ajusta cor para manter consistência com 'Greys_d'
                )

                plt.title('Distribuição das Taxas Efetivas Médias')
                plt.xlabel('Taxa Efetiva (%)')
                plt.ylabel('Frequência')

                # Adicionar grid e ajustar limite do eixo X
                plt.grid(True, alpha=0.3)
                max_taxa = df_resumo['Taxa_Media'].max()
                max_limit = math.ceil(max_taxa * 4) / 4
                plt.xlim(0, max(1.75, max_limit))

                plt.tight_layout()

                arquivo_grafico = os.path.join(dir_graficos, "distribuicao_taxas_efetivas.png")
                plt.savefig(arquivo_grafico)
                plt.close()

                print(f"Gráfico de distribuição de taxas salvo em: {arquivo_grafico}")

            # NOVOS GRÁFICOS - CARTEIRA ATUAL
            try:
                # Obter a última data disponível
                ultima_data = df_consolidado['Periodo'].max()

                if ultima_data:
                    print(f"\nGerando gráfico da carteira atual (período: {ultima_data})...")
                    
                    # CORREÇÃO: 
                    # 1. Primeiro obter os dados originais para identificar os fundos presentes na carteira atual
                    # 2. Depois fazer merge com as taxas efetivas calculadas em df_consolidado
                    
                    if ultima_data in carteiras_originais:
                        df_carteira_original = carteiras_originais[ultima_data].copy()
                        
                        # Identificar as colunas disponíveis
                        coluna_cnpj = None
                        for col in ['CNPJ_FUNDO_CLASSE_COTA', 'CNPJ_FUNDO_COTA', 'CPF_CNPJ_EMISSOR', 'CNPJ_EMISSOR']:
                            if col in df_carteira_original.columns:
                                coluna_cnpj = col
                                break
                                
                        coluna_nome = None
                        for col in ['NM_FUNDO_CLASSE_SUBCLASSE_COTA', 'NM_FUNDO_COTA', 'DENOM_SOCIAL_EMISSOR']:
                            if col in df_carteira_original.columns:
                                coluna_nome = col
                                break
                                
                        coluna_valor = 'VL_MERC_POS_FINAL'
                        
                        # Verificar se temos as colunas necessárias
                        if coluna_cnpj and coluna_nome and coluna_valor in df_carteira_original.columns:
                            # Converter para numérico
                            df_carteira_original[coluna_valor] = pd.to_numeric(
                                df_carteira_original[coluna_valor], errors='coerce'
                            )
                            
                            # Certificar que temos a coluna TAXA_ADM disponível (mesmo que seja para backup)
                            taxa_adm_presente = 'TAXA_ADM' in df_carteira_original.columns
                            if taxa_adm_presente:
                                df_carteira_original['TAXA_ADM'] = pd.to_numeric(
                                    df_carteira_original['TAXA_ADM'], errors='coerce'
                                )
                            
                            # Filtrar apenas linhas com valores válidos
                            df_atual_clean = df_carteira_original.dropna(subset=[coluna_valor])
                            
                            # Criar um DataFrame com CNPJs, Nomes e Valores para depois fazer merge
                            df_fundos_atuais = pd.DataFrame({
                                'CNPJ': df_atual_clean[coluna_cnpj],
                                'Nome': df_atual_clean[coluna_nome],
                                'Valor_Total': df_atual_clean[coluna_valor]
                            })
                            
                            # Se tivermos taxa de administração, incluir
                            if taxa_adm_presente:
                                df_fundos_atuais['TAXA_ADM_ORIGINAL'] = df_atual_clean['TAXA_ADM']
                            
                            # Agrupar por CNPJ e Nome (para caso de múltiplas linhas)
                            if taxa_adm_presente:
                                df_fundos_atuais = df_fundos_atuais.groupby(['CNPJ', 'Nome']).agg({
                                    'Valor_Total': 'sum',
                                    'TAXA_ADM_ORIGINAL': lambda x: np.average(x, weights=df_fundos_atuais.loc[x.index, 'Valor_Total'])
                                }).reset_index()
                            else:
                                df_fundos_atuais = df_fundos_atuais.groupby(['CNPJ', 'Nome']).agg({
                                    'Valor_Total': 'sum'
                                }).reset_index()
                            
                            # Filtrar em df_consolidado apenas os registros do período atual
                            df_taxas_periodo_atual = df_consolidado[df_consolidado['Periodo'] == ultima_data]
                            
                            # Fazer o merge para obter as taxas efetivas calculadas
                            df_atual = pd.merge(
                                df_fundos_atuais,
                                df_taxas_periodo_atual[['CNPJ', 'Taxa_Efetiva', 'Num_Fundos', 'Num_Sem_Taxa', 'Perc_Sem_Taxa']],
                                on='CNPJ',
                                how='left'
                            )
                            
                            # IMPORTANTE: Para fundos sem taxa efetiva calculada, usar a taxa de administração original
                            if taxa_adm_presente:
                                # Identificar registros sem taxa efetiva
                                sem_taxa_efetiva = df_atual['Taxa_Efetiva'].isna()
                                
                                # Para esses registros, usar a taxa de administração original
                                df_atual.loc[sem_taxa_efetiva, 'Taxa_Efetiva'] = df_atual.loc[sem_taxa_efetiva, 'TAXA_ADM_ORIGINAL']
                                
                                print(f"Aplicadas taxas administrativas originais para {sem_taxa_efetiva.sum()} fundos sem taxa efetiva calculada.")
                            
                            # Preencher valores faltantes (CNPJs que não estão no registro de taxas e sem taxa ADM disponível)
                            df_atual['Taxa_Efetiva'].fillna(0, inplace=True)
                            df_atual['Num_Fundos'].fillna(1, inplace=True)
                            df_atual['Num_Sem_Taxa'].fillna(0, inplace=True)
                            df_atual['Perc_Sem_Taxa'].fillna(0, inplace=True)
                            
                            # Adicionar período
                            df_atual['Periodo'] = ultima_data
                            
                            # Ordenar por taxa efetiva
                            df_atual = df_atual.sort_values('Taxa_Efetiva', ascending=False)
                            
                            # Salvar DF para debug
                            df_atual.to_csv(
                                os.path.join(dir_saida, f"carteira_atual_{ultima_data}_com_taxas_efetivas.csv"),
                                index=False,
                                encoding='utf-8-sig'
                            )
                            
                            print(f"Encontrados {len(df_atual)} fundos na carteira atual. Taxas aplicadas com sucesso.")
                        else:
                            print("Colunas necessárias não encontradas na carteira atual, usando dados consolidados")
                            df_atual = df_consolidado[df_consolidado['Periodo'] == ultima_data]
                    else:
                        print(f"Dados originais para o período {ultima_data} não encontrados, usando dados consolidados")
                        df_atual = df_consolidado[df_consolidado['Periodo'] == ultima_data]

                    if not df_atual.empty:
                        df_atual = df_atual.sort_values('Taxa_Efetiva', ascending=False)

                        df_plot = df_atual.head(min(15, len(df_atual)))
                        df_plot['Nome_Curto'] = df_plot['Nome'].str.slice(0, 30) + '...'

                        plt.figure(figsize=(12, 8))
                        ax = sns.barplot(
                            x='Taxa_Efetiva', 
                            y='Nome_Curto',
                            data=df_plot,
                            palette='Blues_d'
                        )

                        plt.title(f'Taxa Efetiva por Fundo (Período Atual: {ultima_data})')
                        plt.xlabel('Taxa Efetiva (%)')
                        plt.ylabel('Fundo')
                        plt.grid(True, alpha=0.3)

                        max_taxa = df_plot['Taxa_Efetiva'].max()
                        max_limit = math.ceil(max_taxa * 4) / 4
                        plt.xlim(0, max(1.75, max_limit))

                        plt.tight_layout()
                        
                        arquivo_grafico = os.path.join(dir_graficos, "taxas_efetivas_carteira_atual.png")
                        plt.savefig(arquivo_grafico)
                        plt.close()
                        print(f"Gráfico da carteira atual salvo em: {arquivo_grafico}")

                        # Gráfico adicional - pizza mostrando alocação por fundo
                        plt.figure(figsize=(12, 12))
                        df_pizza = df_atual.copy()
                        if len(df_pizza) > 10:
                            df_pizza = df_pizza.sort_values('Valor_Total', ascending=False)
                            top10 = df_pizza.head(10)
                            outros = df_pizza.iloc[10:]
                            outros_linha = pd.DataFrame([{
                                'Nome': 'Outros Fundos',
                                'Valor_Total': outros['Valor_Total'].sum(),
                                'Taxa_Efetiva': (
                                    outros['Taxa_Efetiva'] * outros['Valor_Total']
                                ).sum() / outros['Valor_Total'].sum() if outros['Valor_Total'].sum() > 0 else 0
                            }])
                            df_pizza = pd.concat([top10, outros_linha])

                        df_pizza['Legenda'] = (
                            df_pizza['Nome'].str.slice(0, 25)
                            + ' (' + df_pizza['Taxa_Efetiva'].round(2).astype(str) + '%)'
                        )

                        plt.pie(
                            df_pizza['Valor_Total'], 
                            labels=df_pizza['Legenda'],
                            autopct='%1.1f%%',
                            startangle=90,
                            shadow=False,
                            explode=[0.05] * len(df_pizza)
                        )
                        plt.axis('equal')
                        plt.title(f'Alocação da Carteira por Fundo (Período: {ultima_data})')
                        plt.tight_layout()

                        arquivo_grafico = os.path.join(dir_graficos, "alocacao_carteira_atual.png")
                        plt.savefig(arquivo_grafico)
                        plt.close()
                        print(f"Gráfico de alocação atual salvo em: {arquivo_grafico}")

                        # Gráfico de dispersão - Taxa Efetiva vs Valor Alocado
                        plt.figure(figsize=(12, 8))
                        tamanhos = df_atual['Valor_Total'] / df_atual['Valor_Total'].max() * 1000
                        tamanhos = tamanhos.clip(lower=100)

                        scatter = plt.scatter(
                            df_atual['Taxa_Efetiva'],
                            range(len(df_atual)),
                            s=tamanhos,
                            alpha=0.6,
                            c=df_atual['Taxa_Efetiva'],
                            cmap='viridis'
                        )

                        for i, txt in enumerate(df_atual['Nome'].str.slice(0, 20) + '...'):
                            plt.annotate(
                                txt, 
                                (df_atual['Taxa_Efetiva'].iloc[i], i),
                                xytext=(10, 0),
                                textcoords='offset points',
                                fontsize=8
                            )

                        plt.colorbar(scatter, label='Taxa Efetiva (%)')
                        plt.title(f'Relação entre Taxa Efetiva e Valor Alocado (Período: {ultima_data})')
                        plt.xlabel('Taxa Efetiva (%)')
                        plt.yticks([])
                        plt.grid(True, alpha=0.3)
                        plt.tight_layout()

                        arquivo_grafico = os.path.join(dir_graficos, "taxa_vs_valor_atual.png")
                        plt.savefig(arquivo_grafico)
                        plt.close()
                        print(f"Gráfico de relação taxa vs valor salvo em: {arquivo_grafico}")

                        # Tabela com informações do último período
                        plt.figure(figsize=(8, 4))
                        plt.axis('off')

                        valor_total_carteira = df_atual['Valor_Total'].sum()
                        taxa_media_pond = (
                            (df_atual['Taxa_Efetiva'] * df_atual['Valor_Total']).sum()
                            / valor_total_carteira if valor_total_carteira > 0 else 0
                        )

                        tabela_dados = [
                            ["Data de Referência:", ultima_data],
                            ["Valor Total da Carteira:", f"R$ {valor_total_carteira:,.2f}"],
                            ["Taxa Média Ponderada:", f"{taxa_media_pond:.4f}%"],
                            ["Número de Fundos:", f"{len(df_atual)}"],
                            ["Maior Taxa:", f"{df_atual['Taxa_Efetiva'].max():.4f}%"],
                            ["Menor Taxa:", f"{df_atual['Taxa_Efetiva'].min():.4f}%"]
                        ]

                        tbl = plt.table(
                            cellText=tabela_dados,
                            loc='center',
                            cellLoc='left',
                            colWidths=[0.3, 0.7]
                        )

                        tbl.auto_set_font_size(False)
                        tbl.set_fontsize(12)
                        tbl.scale(1, 1.5)

                        plt.title("Resumo da Carteira Atual", fontsize=14, pad=20)
                        plt.tight_layout()

                        arquivo_tabela = os.path.join(dir_graficos, "resumo_carteira_atual.png")
                        plt.savefig(arquivo_tabela)
                        plt.close()
                        print(f"Tabela resumo da carteira atual salva em: {arquivo_tabela}")

                        df_atual.to_csv(
                            os.path.join(dir_saida, f"carteira_atual_{ultima_data}.csv"),
                            index=False,
                            encoding='utf-8-sig'
                        )
                    else:
                        print(f"Sem dados para o último período ({ultima_data})")
                else:
                    print("Não foi possível determinar o último período disponível")
            except Exception as e:
                print(f"Erro ao gerar gráficos da carteira atual: {str(e)}")
                import traceback
                traceback.print_exc()

        except Exception as e:
            print(f"Erro ao gerar gráficos: {str(e)}")

    print("\nProcessamento concluído!")
    return taxas_efetivas


def combinar_taxas_efetivas(carteiras_com_taxas_manuais, taxas_efetivas):

 
    print("\nCombinando taxas efetivas com carteiras...")
    
    # Criar uma cópia do dicionário original para não modificá-lo
    carteiras_finais = {}
    
    # Para cada período nas carteiras
    for data, df_carteira in carteiras_com_taxas_manuais.items():
        
        print(f"\nProcessando período: {data}")
        
        # Criar uma cópia do DataFrame para evitar modificar o original
        df_final = df_carteira.copy()
        
        # Identificar a coluna que contém o CNPJ dos fundos
        coluna_cnpj = None
        for col in ['CNPJ_FUNDO_CLASSE_COTA', 'CNPJ_FUNDO_COTA', 'CPF_CNPJ_EMISSOR', 'CNPJ_EMISSOR']:
            if col in df_final.columns:
                coluna_cnpj = col
                break
        
        if coluna_cnpj is None:
            print(f"  - Não foi possível identificar coluna com CNPJ dos fundos para {data}")
            carteiras_finais[data] = df_final
            continue
        
        # Identificar fundos com taxa zero
        df_final['TAXA_ADM'] = pd.to_numeric(df_final['TAXA_ADM'], errors='coerce')
        fundos_taxa_zero = df_final[df_final['TAXA_ADM'] == 0][coluna_cnpj].unique()
        
        print(f"  - Encontrados {len(fundos_taxa_zero)} fundos com taxa zero")
        
        # Contar atualizações
        contador_atualizacoes = 0
        
        # Para cada fundo com taxa zero, verificar se temos uma taxa efetiva calculada
        for cnpj in fundos_taxa_zero:
            
            if cnpj in taxas_efetivas:
                info_taxa = taxas_efetivas[cnpj]
                
                # Verificar se temos a taxa para este período específico
                if 'resultados' in info_taxa and data in info_taxa['resultados']:
                    taxa_efetiva = info_taxa['resultados'][data]['taxa_efetiva']
                    print(f"  - Substituindo taxa do fundo {cnpj}: 0.00 -> {taxa_efetiva:.4f}%")
                    
                    # Atualizar a taxa no DataFrame
                    df_final.loc[df_final[coluna_cnpj] == cnpj, 'TAXA_ADM'] = taxa_efetiva
                    contador_atualizacoes += 1
        
        print(f"  - Atualizados {contador_atualizacoes} fundos com taxas efetivas")
        
        # Recalcular o custo mensal (1/12 da taxa anual sobre o valor investido)
        if 'VL_MERC_POS_FINAL' in df_final.columns:
            df_final['VL_MERC_POS_FINAL'] = pd.to_numeric(df_final['VL_MERC_POS_FINAL'], errors='coerce')
            df_final['CUSTO_MENSAL'] = df_final['VL_MERC_POS_FINAL'] * (df_final['TAXA_ADM'] / 100) / 12
            
            # Calcular o custo total para este período
            custo_total = df_final['CUSTO_MENSAL'].sum()
            print(f"  - Custo total mensal após ajustes: R$ {custo_total:,.2f}")
        
        # Adicionar ao dicionário final
        carteiras_finais[data] = df_final
    
    print("\nProcessamento concluído!")
    return carteiras_finais


def extrair_pl_taxas(cnpj_fundo, base_dir, inicio='2019-01', fim='2025-02'):
    """
    Extrai a série do PL do fundo Aconcagua a partir dos arquivos INF_DIARIO.
    
    Args:
        cnpj_fundo (str): CNPJ do fundo Aconcagua
        base_dir (str): Diretório base onde estão os arquivos
        inicio (str): Data inicial (YYYY-MM)
        fim (str): Data final (YYYY-MM)
        
    Returns:
        DataFrame: Série temporal com data, PL e custo mensal
    """
    print(f"Extraindo série de PL para o fundo {cnpj_fundo}...")
    
    # Diretório onde estão os arquivos INF_DIARIO
    pasta_inf_diario = os.path.join(base_dir, 'INF_DIARIO')
    
    # Diretório temporário para extração
    dir_temp = os.path.join(base_dir, 'temp_extract_pl')
    os.makedirs(dir_temp, exist_ok=True)
    
    # Lista para armazenar os dados de PL por mês
    dados_pl = []
    
    try:
        # Encontrar todos os arquivos ZIP do tipo inf_diario_fi_*
        arquivos_zip = []
        for root, _, files in os.walk(pasta_inf_diario):
            for file in files:
                if file.endswith('.zip') and 'inf_diario_fi_' in file:
                    arquivos_zip.append(os.path.join(root, file))
                elif not file.endswith('.zip') and file.startswith('inf_diario_fi_'):
                    # Se for um arquivo CSV diretamente
                    arquivos_zip.append(os.path.join(root, file))
        
        # Converter as datas de início e fim para datetime
        inicio_dt = datetime.strptime(inicio, '%Y-%m')
        fim_dt = datetime.strptime(fim, '%Y-%m')
        
        # Filtrar arquivos pelo período
        arquivos_filtrados = []
        for arquivo in arquivos_zip:
            nome_arquivo = os.path.basename(arquivo)
            
            # Extrair a data do nome do arquivo
            match = re.search(r'inf_diario_fi_(\d{4})(\d{2})', nome_arquivo)
            if match:
                ano = int(match.group(1))
                mes = int(match.group(2))
                data_arquivo = datetime(ano, mes, 1)
                
                # Verificar se está dentro do período
                if inicio_dt <= data_arquivo <= fim_dt:
                    arquivos_filtrados.append((arquivo, ano, mes))
        
        # Ordenar arquivos por data (crescente)
        arquivos_filtrados.sort(key=lambda x: (x[1], x[2]))
        
        print(f"Encontrados {len(arquivos_filtrados)} arquivos para o período {inicio} a {fim}")
        
        # Processar cada arquivo
        for arquivo, ano, mes in arquivos_filtrados:
            nome_arquivo = os.path.basename(arquivo)
            periodo = f"{ano}-{mes:02d}"
            
            print(f"Processando {nome_arquivo} ({periodo})...")
            
            try:
                # Verificar se é um arquivo ZIP ou CSV
                if arquivo.endswith('.zip'):
                    # Preparar diretório para extração
                    mes_dir = os.path.join(dir_temp, f"inf_diario_fi_{ano}{mes:02d}")
                    os.makedirs(mes_dir, exist_ok=True)
                    
                    # Extrair o conteúdo do ZIP
                    with zipfile.ZipFile(arquivo, 'r') as zip_ref:
                        # Listar arquivos no ZIP
                        arquivos_csv = [f for f in zip_ref.namelist() if f.endswith('.csv')]
                        
                        if arquivos_csv:
                            # Extrair apenas o primeiro CSV
                            arquivo_csv = arquivos_csv[0]
                            with zip_ref.open(arquivo_csv) as f:
                                content = f.read()
                                try:
                                    df = pd.read_csv(io.BytesIO(content), sep=';', encoding='ISO-8859-1', low_memory=False)
                                except:
                                    # Tentar com encoding alternativo
                                    df = pd.read_csv(io.BytesIO(content), sep=';', encoding='utf-8', low_memory=False)
                        else:
                            print(f"  - Nenhum arquivo CSV encontrado em {nome_arquivo}")
                            continue
                else:
                    # Ler diretamente o CSV
                    try:
                        df = pd.read_csv(arquivo, sep=';', encoding='ISO-8859-1', low_memory=False)
                    except:
                        # Tentar com encoding alternativo
                        df = pd.read_csv(arquivo, sep=';', encoding='utf-8', low_memory=False)
                
                # Identificar as colunas corretamente
                # Lista de possíveis nomes para a coluna de CNPJ
                colunas_cnpj = ['CNPJ_FUNDO', 'CNPJ', 'CD_CNPJ_FUNDO', 'CD_FUNDO', 'CNPJ_FUNDO_CLASSE']
                coluna_cnpj = None
                
                # Encontrar a primeira coluna que existe no DataFrame
                for col in colunas_cnpj:
                    if col in df.columns:
                        coluna_cnpj = col
                        break
                
                if coluna_cnpj is None:
                    # Se não encontrar nenhuma coluna conhecida, mostrar as colunas disponíveis
                    print(f"  - Erro: Não foi possível identificar a coluna de CNPJ. Colunas disponíveis: {', '.join(df.columns)}")
                    if 'CNPJ' in ' '.join(df.columns):
                        print(f"  - Detectada coluna CNPJ em outro formato. Tentando encontrar...")
                        # Procurar por colunas que contenham "CNPJ"
                        cols_with_cnpj = [col for col in df.columns if 'CNPJ' in col]
                        if cols_with_cnpj:
                            coluna_cnpj = cols_with_cnpj[0]
                            print(f"  - Utilizando coluna: {coluna_cnpj}")
                
                # Verificar se encontrou a coluna de CNPJ
                if coluna_cnpj is None:
                    print(f"  - Erro: Não foi possível encontrar a coluna de CNPJ no arquivo {nome_arquivo}")
                    continue
                
                # Lista de possíveis nomes para a coluna de data
                colunas_data = ['DT_COMPTC', 'DATA', 'DT_REF', 'DT', 'DATA_REFERENCIA']
                coluna_data = None
                
                # Encontrar a primeira coluna que existe no DataFrame
                for col in colunas_data:
                    if col in df.columns:
                        coluna_data = col
                        break
                
                if coluna_data is None:
                    print(f"  - Erro: Não foi possível identificar a coluna de data no arquivo {nome_arquivo}")
                    # Tenta usar a data do nome do arquivo
                    print(f"  - Utilizando a data do nome do arquivo: {periodo}-01")
                    df['DATA_ARTIFICIAL'] = f"{periodo}-01"
                    coluna_data = 'DATA_ARTIFICIAL'
                
                # Lista de possíveis nomes para a coluna de PL
                colunas_pl = ['VL_PATRIM_LIQ', 'PATRIMONIO_LIQUIDO', 'PL', 'VL_PL']
                coluna_pl = None
                
                # Encontrar a primeira coluna que existe no DataFrame
                for col in colunas_pl:
                    if col in df.columns:
                        coluna_pl = col
                        break
                
                if coluna_pl is None:
                    print(f"  - Erro: Não foi possível identificar a coluna de PL no arquivo {nome_arquivo}")
                    continue
                
                # Filtrar pelo CNPJ do fundo
                try:
                    df_fundo = df[df[coluna_cnpj] == cnpj_fundo].copy()
                except Exception as e:
                    print(f"  - Erro ao filtrar pelo CNPJ: {str(e)}")
                    # Tentar converter a coluna para string primeiro
                    df[coluna_cnpj] = df[coluna_cnpj].astype(str).str.strip()
                    df_fundo = df[df[coluna_cnpj] == cnpj_fundo].copy()
                
                if len(df_fundo) > 0:
                    # Converter a data para datetime
                    try:
                        df_fundo[coluna_data] = pd.to_datetime(df_fundo[coluna_data])
                        
                        # Pegar o último dia do mês
                        ultima_data = df_fundo[coluna_data].max()
                        df_ultimo_dia = df_fundo[df_fundo[coluna_data] == ultima_data]
                    except:
                        # Se não conseguir converter, utilizar todos os registros
                        print(f"  - Erro ao converter data. Utilizando todos os registros.")
                        df_ultimo_dia = df_fundo
                    
                    if len(df_ultimo_dia) > 0:
                        # Converter coluna de PL para numérico
                        df_ultimo_dia[coluna_pl] = pd.to_numeric(df_ultimo_dia[coluna_pl], errors='coerce')
                        
                        # Obter o PL (soma se houver múltiplos registros)
                        pl = df_ultimo_dia[coluna_pl].sum()
                        
                        # Calcular o custo mensal (0,38% ao ano / 12)
                        custo_mensal = pl * 0.0038 / 12
                        
                        # Adicionar aos dados
                        dados_pl.append({
                            'data': datetime(ano, mes, 1),
                            'pl': pl,
                            'custo_mensal': custo_mensal
                        })
                        
                        data_str = ultima_data.strftime('%Y-%m-%d') if hasattr(ultima_data, 'strftime') else periodo
                        print(f"  - PL em {data_str}: R$ {pl:,.2f}")
                        print(f"  - Custo mensal (0,38% a.a.): R$ {custo_mensal:,.2f}")
                    else:
                        print(f"  - Nenhum registro para o último dia do mês")
                else:
                    print(f"  - Fundo {cnpj_fundo} não encontrado no arquivo {nome_arquivo}")
            
            except Exception as e:
                print(f"  - Erro ao processar {nome_arquivo}: {str(e)}")
                # Mostrar mais detalhes do erro
                import traceback
                traceback.print_exc()
    
    finally:
        # Limpar diretório temporário
        if os.path.exists(dir_temp):
            try:
                shutil.rmtree(dir_temp)
                print("\nDiretório temporário removido")
            except:
                print("\nNão foi possível remover o diretório temporário")
    
    # Converter para DataFrame
    df_pl = pd.DataFrame(dados_pl)
    
    # Ordenar por data
    if not df_pl.empty:
        df_pl = df_pl.sort_values('data')
    
    # Informações finais
    if not df_pl.empty:
        print(f"\nPeríodo: {df_pl['data'].min().strftime('%Y-%m')} a {df_pl['data'].max().strftime('%Y-%m')}")
        print(f"Total de meses: {len(df_pl)}")
        print(f"PL médio: R$ {df_pl['pl'].mean():,.2f}")
        print(f"PL final: R$ {df_pl['pl'].iloc[-1]:,.2f}")
        
        # Salvar CSV com os dados extraídos
        csv_path = os.path.join(base_dir, 'pl_aconcagua.csv')
        df_pl.to_csv(csv_path, index=False)
        print(f"\nDados salvos em: {csv_path}")
    else:
        print("Nenhum dado de PL encontrado para o período especificado.")
    
    return df_pl


def taxas_niveis(cnpj_fundo, base_dir, resultados, carteiras_finais):
    
    # Nível 1
    serie_custos = extrair_pl_taxas(cnpj_fundo, base_dir)
    
    # Nível 2
    serie_custos['custo_fundo_mensal'] = None
    for i, row in serie_custos.iterrows():
        data_str = row['data'].strftime('%Y-%m')
        if data_str in resultados:
            # Se existir, atualizar o valor na coluna 'custo_fundo_mensal'
            serie_custos.at[i, 'custo_fundo_mensal'] = resultados[data_str]['custo_total_mensal']
    
    # Nïvel 3
    zero_cost = calcular_custos_taxas(carteiras_finais, dir_saida=None)
    serie_custos['custo_fundo_mensal_efetivo'] = None
    for i, row in serie_custos.iterrows():
        data_str = row['data'].strftime('%Y-%m')
        if data_str in zero_cost:
            # Se existir, atualizar o valor na coluna 'custo_fundo_mensal'
            serie_custos.at[i, 'custo_fundo_mensal_efetivo'] = zero_cost[data_str]['custo_total_mensal']
    
    serie_custos['nivel_1'] = serie_custos['custo_mensal']
    serie_custos['nivel_2'] = serie_custos['custo_mensal'] + serie_custos['custo_fundo_mensal']
    serie_custos['nivel_3'] = serie_custos['custo_mensal'] + serie_custos['custo_fundo_mensal_efetivo']
    serie_custos['pct'] = (serie_custos['nivel_3'] / serie_custos['pl']) * 100
    
    media = np.mean(serie_custos['pct'])
    
    return serie_custos, media


def plotar_pl_custos_niveis(df_pl, valores_investidos, titulo="Fundo Aconcagua", caminho_saida=None):
    """
    Versão corrigida da função original que gera um gráfico com barras para o PL,
    área preenchida para valores investidos em fundos, e linhas para os diferentes níveis de custo.
    
    Compatível com diferentes formatos de entrada para valores_investidos.
    
    Args:
        df_pl (DataFrame): DataFrame com colunas 'data', 'pl', 'nivel_1', 'nivel_2', 'nivel_3'
        valores_investidos (list/dict): Lista de valores ou dicionário com data como chave
        titulo (str): Título do gráfico
        caminho_saida (str): Caminho para salvar o gráfico
        
    Returns:
        matplotlib.figure.Figure: Objeto figura do matplotlib
    """
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import matplotlib.ticker as mtick
    import os
    
    # 1. PREPARAÇÃO DOS DADOS
    # ----------------------
    # Criar cópia para não modificar o original
    df_trabalho = df_pl.copy()
    
    # Garantir que a coluna 'data' está no formato datetime
    if not pd.api.types.is_datetime64_any_dtype(df_trabalho['data']):
        df_trabalho['data'] = pd.to_datetime(df_trabalho['data'])
    
    # Ordenar por data
    df_trabalho = df_trabalho.sort_values('data')
    
    # Obter datas como lista
    datas = df_trabalho['data'].tolist()
    
    # Verificar formato de valores_investidos e preparar para plotagem
    if isinstance(valores_investidos, list) or isinstance(valores_investidos, np.ndarray):
        # Se for lista ou array, verificar comprimento
        if len(valores_investidos) == len(datas):
            valores_inv_lista = list(valores_investidos)
        else:
            print(f"AVISO: Lista de valores_investidos (len={len(valores_investidos)}) não tem o mesmo comprimento que datas (len={len(datas)})")
            # Usar aproximação como último recurso (60% do PL)
            valores_inv_lista = [row['pl'] * 0.6 for _, row in df_trabalho.iterrows()]
    
    elif isinstance(valores_investidos, dict):
        # Se for dicionário, extrair valores para cada data
        valores_inv_lista = []
        for data in datas:
            data_str = data.strftime('%Y-%m')
            if data_str in valores_investidos:
                valores_inv_lista.append(valores_investidos[data_str])
            else:
                # Usar aproximação como último recurso
                idx = df_trabalho['data'] == data
                if any(idx):
                    valores_inv_lista.append(df_trabalho.loc[idx, 'pl'].iloc[0] * 0.6)
                else:
                    valores_inv_lista.append(0)
    
    else:
        # Se não for nem lista nem dicionário, usar aproximação
        print("AVISO: valores_investidos não é uma lista ou dicionário. Usando aproximação.")
        valores_inv_lista = [row['pl'] * 0.6 for _, row in df_trabalho.iterrows()]
    
    # Debug: Imprimir estatísticas principais
    print(f"Número de datas: {len(datas)}")
    print(f"Número de valores de PL: {len(df_trabalho['pl'])}")
    print(f"Número de valores investidos: {len(valores_inv_lista)}")
    print(f"Valor mínimo de PL: {df_trabalho['pl'].min():,.2f}")
    print(f"Valor máximo de PL: {df_trabalho['pl'].max():,.2f}")
    print(f"Primeiro valor de PL ({df_trabalho['data'].iloc[0].strftime('%Y-%m')}): {df_trabalho['pl'].iloc[0]:,.2f}")
    print(f"Último valor de PL ({df_trabalho['data'].iloc[-1].strftime('%Y-%m')}): {df_trabalho['pl'].iloc[-1]:,.2f}")
    
    # Últimos 5 valores para debug
    print("\nÚltimos 5 valores de PL:")
    for i in range(min(5, len(df_trabalho))):
        idx = -(i+1)
        data_str = df_trabalho['data'].iloc[idx].strftime('%Y-%m')
        pl_valor = df_trabalho['pl'].iloc[idx]
        print(f"{data_str}: {pl_valor:,.2f}")
    
    # 2. CRIAÇÃO DO GRÁFICO
    # --------------------
    plt.figure(figsize=(16, 10))
    ax1 = plt.subplot(111)
    ax2 = ax1.twinx()
    
    # Cores
    cor_barras = '#A0A0A0'      # Cinza para as barras de PL
    cor_investido = '#2C3E50'   # Azul escuro para área de valores investidos
    cor_nivel1 = '#FF9999'      # Vermelho claro para nível 1
    cor_nivel2 = '#FF3333'      # Vermelho médio para nível 2
    cor_nivel3 = '#990000'      # Vermelho escuro para nível 3
    
    # Converter para arrays numpy para evitar problemas
    pl_valores = np.array(df_trabalho['pl'].tolist())
    valores_inv_np = np.array(valores_inv_lista)
    
    # Plotar barras para PL
    barras = ax1.bar(datas, pl_valores, color=cor_barras, width=20, alpha=0.9)
    
    # Plotar área para valores investidos
    area_inv = ax1.fill_between(datas, valores_inv_np, color=cor_investido, alpha=0.7)
    
    # Plotar linhas para níveis
    nivel1_valores = df_trabalho['nivel_1'].tolist() if 'nivel_1' in df_trabalho.columns else None
    nivel2_valores = df_trabalho['nivel_2'].tolist() if 'nivel_2' in df_trabalho.columns else None
    nivel3_valores = df_trabalho['nivel_3'].tolist() if 'nivel_3' in df_trabalho.columns else None
    
    linha_nivel1 = ax2.plot(datas, nivel1_valores, color=cor_nivel1, linewidth=1.5, 
                          marker='o', markersize=5) if nivel1_valores else None
    
    linha_nivel2 = ax2.plot(datas, nivel2_valores, color=cor_nivel2, linewidth=1.5, 
                          marker='s', markersize=5) if nivel2_valores else None
    
    linha_nivel3 = ax2.plot(datas, nivel3_valores, color=cor_nivel3, linewidth=1.5, 
                          marker='d', markersize=5) if nivel3_valores else None
    
    # 3. FORMATAÇÃO
    # -----------
    # Configurar eixo X (datas)
    n_datas = len(datas)
    intervalo = 6 if n_datas > 36 else (3 if n_datas > 24 else (2 if n_datas > 12 else 1))
    
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b/%Y'))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=intervalo))
    plt.xticks(rotation=45, ha='right')
    
    # Configurar eixo Y1 (PL)
    max_pl = np.max(pl_valores)
    if max_pl >= 1e9:
        ax1.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, p: f'R$ {x/1e9:.1f}B'))
    else:
        ax1.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, p: f'R$ {x/1e6:.1f}M'))
    
    ax1.set_ylabel('Patrimônio Líquido (R$)', fontsize=12, color='#555555', fontweight='bold')
    ax1.tick_params(axis='y', colors='#555555')
    ax1.set_ylim(bottom=0)
    
    # Configurar eixo Y2 (Custos)
    max_custo = 0
    if nivel1_valores:
        max_custo = max(max_custo, max(nivel1_valores))
    if nivel2_valores:
        max_custo = max(max_custo, max(nivel2_valores))
    if nivel3_valores:
        max_custo = max(max_custo, max(nivel3_valores))
    
    if max_custo >= 1e6:
        ax2.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, p: f'R$ {x/1e6:.1f}M'))
    else:
        ax2.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, p: f'R$ {x/1e3:.1f}K'))
    
    ax2.set_ylabel('Custo Mensal (R$)', fontsize=12, color='#AA0000', fontweight='bold')
    ax2.tick_params(axis='y', colors='#AA0000')
    
    # Título e grid
    plt.title(titulo, fontsize=16, pad=20, fontweight='bold')
    ax1.grid(True, linestyle='--', alpha=0.3)
    
    # Legendas
    handles = [barras[0], area_inv]
    labels = ['Patrimônio Líquido', 'Valor Investido em Fundos']
    
    if linha_nivel1:
        handles.append(linha_nivel1[0])
        labels.append('Custos Nível 1 - Itaú')
    
    if linha_nivel2:
        handles.append(linha_nivel2[0])
        labels.append('Custos Nível 2 - Itaú e Adm. Fundos')
    
    if linha_nivel3:
        handles.append(linha_nivel3[0])
        labels.append('Custos Nível 3 - Itaú e Adm. Efetiva Fundos')
    
    ax1.legend(handles, labels, loc='upper left', frameon=True, framealpha=0.9)
    
    plt.tight_layout()
    plt.show()
    
    # 4. SALVAR GRÁFICO
    # ---------------
    if caminho_saida:
        diretorio = os.path.dirname(caminho_saida)
        if diretorio and not os.path.exists(diretorio):
            os.makedirs(diretorio, exist_ok=True)
        plt.savefig(caminho_saida, dpi=300, bbox_inches='tight')
        print(f"Gráfico salvo em: {caminho_saida}")
    
    return plt.gcf()


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