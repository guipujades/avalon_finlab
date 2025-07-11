import os
import pandas as pd
import numpy as np
from datetime import datetime
import pickle
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import tempfile
import shutil

from carteiras_analysis_utils import (
    carregar_carteira_serializada,
    processar_carteira_completa
)

def carregar_dados_cadastrais_fundos(base_dir):
    """
    Carrega dados cadastrais dos fundos para obter taxas de administração e performance
    """
    try:
        cache_path = os.path.join(base_dir, 'cache_cadastro_completo.pkl')
        if os.path.exists(cache_path):
            print("Carregando dados do cache...")
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        
        print("Carregando dados cadastrais e de taxas...")
        
        caminho_cad = os.path.join(base_dir, 'CAD', 'cad_fi.csv')
        df_cadastro = pd.read_csv(caminho_cad, encoding='latin-1', delimiter=';', low_memory=False)
        print(f"Cadastro principal carregado: {len(df_cadastro)} registros")
        
        caminho_taxa_adm = os.path.join(base_dir, 'CAD', 'cad_fi_hist_taxa_adm.csv')
        df_taxa_adm = pd.read_csv(caminho_taxa_adm, encoding='latin-1', delimiter=';', low_memory=False)
        print(f"Taxas de administração carregadas: {len(df_taxa_adm)} registros")
        
        caminho_taxa_perf = os.path.join(base_dir, 'CAD', 'cad_fi_hist_taxa_perfm.csv')
        df_taxa_perf = pd.read_csv(caminho_taxa_perf, encoding='latin-1', delimiter=';', low_memory=False)
        print(f"Taxas de performance carregadas: {len(df_taxa_perf)} registros")
        
        if 'DT_REG' in df_taxa_adm.columns:
            df_taxa_adm['DT_REG'] = pd.to_datetime(df_taxa_adm['DT_REG'])
            df_taxa_adm_recente = df_taxa_adm.sort_values('DT_REG').groupby('CNPJ_FUNDO').last().reset_index()
        else:
            df_taxa_adm_recente = df_taxa_adm.groupby('CNPJ_FUNDO').last().reset_index()
        
        if 'DT_REG' in df_taxa_perf.columns:
            df_taxa_perf['DT_REG'] = pd.to_datetime(df_taxa_perf['DT_REG'])
            df_taxa_perf_recente = df_taxa_perf.sort_values('DT_REG').groupby('CNPJ_FUNDO').last().reset_index()
        else:
            df_taxa_perf_recente = df_taxa_perf.groupby('CNPJ_FUNDO').last().reset_index()
        
        df_completo = df_cadastro.merge(
            df_taxa_adm_recente[['CNPJ_FUNDO', 'TAXA_ADM']], 
            on='CNPJ_FUNDO', 
            how='left'
        )
        df_completo = df_completo.merge(
            df_taxa_perf_recente[['CNPJ_FUNDO', 'VL_TAXA_PERFM']], 
            on='CNPJ_FUNDO', 
            how='left'
        )
        
        print(f"Dados completos preparados: {len(df_completo)} registros")
        
        with open(cache_path, 'wb') as f:
            pickle.dump(df_completo, f)
        print("Cache salvo para uso futuro")
        
        return df_completo
                    
    except Exception as e:
        print(f"Erro ao carregar dados cadastrais: {e}")
        return None

def identificar_fundos_na_carteira(df_carteira):
    """
    Identifica fundos de investimento na carteira baseado nas colunas disponíveis
    """
    fundos = []
    
    print(f"Colunas disponíveis: {df_carteira.columns.tolist()}")
    
    # Primeiro, verificar por TP_APLIC que é mais confiável
    if 'TP_APLIC' in df_carteira.columns:
        print(f"Tipos de aplicação únicos: {df_carteira['TP_APLIC'].unique()}")
        df_fundos = df_carteira[df_carteira['TP_APLIC'] == 'Cotas de Fundos'].copy()
        print(f"Fundos encontrados por TP_APLIC='Cotas de Fundos': {len(df_fundos)}")
        
        if len(df_fundos) > 0:
            # Verificar se os valores são strings e converter
            if 'VL_MERC_POS_FINAL' in df_fundos.columns:
                # Converter valores para numérico
                df_fundos['VL_MERC_POS_FINAL'] = pd.to_numeric(
                    df_fundos['VL_MERC_POS_FINAL'].astype(str).str.replace(',', '.'), 
                    errors='coerce'
                )
            
            # Agrupar por CNPJ_FUNDO_CLASSE_COTA
            if 'CNPJ_FUNDO_CLASSE_COTA' in df_fundos.columns:
                fundos_agrupados = df_fundos.groupby('CNPJ_FUNDO_CLASSE_COTA').agg({
                    'VL_MERC_POS_FINAL': 'sum',
                    'NM_FUNDO_CLASSE_SUBCLASSE_COTA': 'first'
                }).reset_index()
                
                for _, row in fundos_agrupados.iterrows():
                    fundos.append({
                        'cnpj': row['CNPJ_FUNDO_CLASSE_COTA'],
                        'nome': row['NM_FUNDO_CLASSE_SUBCLASSE_COTA'],
                        'valor': row['VL_MERC_POS_FINAL']
                    })
                    
                print(f"Fundos agrupados: {len(fundos)}")
                return pd.DataFrame(fundos)
    
    # Se não encontrou por TP_APLIC, tentar por CATEGORIA_ATIVO
    if len(fundos) == 0 and 'CATEGORIA_ATIVO' in df_carteira.columns:
        df_fundos = df_carteira[df_carteira['CATEGORIA_ATIVO'] == 'Fundos'].copy()
        print(f"Fundos encontrados pela categoria: {len(df_fundos)}")
        
        if len(df_fundos) > 0:
            if 'VL_MERC_POS_FINAL' in df_fundos.columns:
                df_fundos['VL_MERC_POS_FINAL'] = pd.to_numeric(
                    df_fundos['VL_MERC_POS_FINAL'].astype(str).str.replace(',', '.'), 
                    errors='coerce'
                )
                
            if 'CNPJ_FUNDO_CLASSE_COTA' in df_fundos.columns:
                fundos_agrupados = df_fundos.groupby('CNPJ_FUNDO_CLASSE_COTA').agg({
                    'VL_MERC_POS_FINAL': 'sum',
                    'NM_FUNDO_CLASSE_SUBCLASSE_COTA': 'first'
                }).reset_index()
                
                for _, row in fundos_agrupados.iterrows():
                    fundos.append({
                        'cnpj': row['CNPJ_FUNDO_CLASSE_COTA'],
                        'nome': row['NM_FUNDO_CLASSE_SUBCLASSE_COTA'],
                        'valor': row['VL_MERC_POS_FINAL']
                    })
    
    # Se ainda não encontrou, tentar outros métodos
    if len(fundos) == 0:
        if 'NM_FUNDO_CLASSE_SUBCLASSE_COTA' in df_carteira.columns:
            df_fundos = df_carteira[df_carteira['NM_FUNDO_CLASSE_SUBCLASSE_COTA'].notna()].copy()
            print(f"Fundos encontrados por NM_FUNDO_CLASSE: {len(df_fundos)}")
            
            if 'CNPJ_FUNDO_INVESTIDO' in df_fundos.columns:
                fundos_agrupados = df_fundos.groupby('CNPJ_FUNDO_INVESTIDO').agg({
                    'VL_MERC_POS_FINAL': 'sum',
                    'NM_FUNDO_CLASSE_SUBCLASSE_COTA': 'first'
                }).reset_index()
                
                for _, row in fundos_agrupados.iterrows():
                    fundos.append({
                        'cnpj': row['CNPJ_FUNDO_INVESTIDO'],
                        'nome': row['NM_FUNDO_CLASSE_SUBCLASSE_COTA'],
                        'valor': row['VL_MERC_POS_FINAL']
                    })
    
    if len(fundos) > 0:
        df_fundos = pd.DataFrame(fundos)
        
        if 'cnpj' in df_fundos.columns:
            fundos_com_cnpj = df_fundos[df_fundos['cnpj'].notna()]
            fundos_sem_cnpj = df_fundos[df_fundos['cnpj'].isna()]
            
            if not fundos_com_cnpj.empty:
                fundos_com_cnpj = fundos_com_cnpj.groupby('cnpj').agg({
                    'nome': 'first',
                    'valor': 'sum'
                }).reset_index()
            
            df_fundos = pd.concat([fundos_com_cnpj, fundos_sem_cnpj], ignore_index=True)
        
        return df_fundos
    
    return pd.DataFrame(fundos)

def carregar_taxas_manuais():
    """
    Carrega taxas manuais para fundos que não estão no cadastro CVM
    Baseado em dados fornecidos pelo usuário - Camada 1
    """
    taxas_manuais = {
        # Fundos com taxas confirmadas pelo usuário
        '56.430.872/0001-44': {'nome': 'ALPAMAYO', 'taxa_adm': 0.0004, 'taxa_perf': 0.20},  # 0.04% - OK
        '12.809.201/0001-13': {'nome': 'CAPSTONE MACRO A', 'taxa_adm': 0.019, 'taxa_perf': 0.20},  # 1.90% - OK
        
        # Private Equity - Taxa 0% na camada 1 (cobram na camada 2)
        '32.311.914/0001-60': {'nome': 'VINCI CAPITAL PARTNERS III MASTER P FIP MULTIESTRATÉGIA', 'taxa_adm': 0.0, 'taxa_perf': 0.0},
        '41.535.122/0001-60': {'nome': 'KINEA PRIVATE EQUITY V FEEDER PRIVATE FIP', 'taxa_adm': 0.0, 'taxa_perf': 0.0},
        
        # Fundos Itaú
        '41.287.689/0001-64': {'nome': 'ITAÚ DOLOMITAS CENTRALIZADOR FIF DA CIC MULTIMERCADO CP RL', 'taxa_adm': 0.0006, 'taxa_perf': 0},  # 0.06%
        '14.096.710/0001-71': {'nome': 'ITAÚ VÉRTICE IBOVESPA EQUITIES FI FINANCEIRO AÇÕES RL', 'taxa_adm': 0.0, 'taxa_perf': 0},
        '18.138.913/0001-34': {'nome': 'ITAÚ VÉRTICE COMPROMISSO RF REFERENCIADO DI FIF CIC RL', 'taxa_adm': 0.0015, 'taxa_perf': 0},  # 0.15%
        '55.419.784/0001-89': {'nome': 'ITAÚ CAIXA AÇÕES FI FINANCEIRO RL', 'taxa_adm': 0.0, 'taxa_perf': 0},
        
        # FIDC
        '12.138.862/0001-64': {'nome': 'FIDC MULTISETORIAL SILVERADO MAXIMUM II', 'taxa_adm': 0.0, 'taxa_perf': 0},
        
        # Outros fundos que podem aparecer
        '07.096.546/0001-37': {'nome': 'ITAÚ VÉRTICE RF DI', 'taxa_adm': 0.003, 'taxa_perf': 0},
        '24.546.223/0001-17': {'nome': 'ITAÚ VÉRTICE COMPROMISSO RF DI', 'taxa_adm': 0.003, 'taxa_perf': 0},
        '21.407.105/0001-30': {'nome': 'ITAÚ VÉRTICE RENDA FIXA REFERENCIADO DI FIF', 'taxa_adm': 0.003, 'taxa_perf': 0},
        
        # Fundos com taxa zero que precisam análise de 2ª camada
        '11.119.584/0001-30': {'nome': 'CSHG ALLOCATION FIC FIM', 'taxa_adm': 0, 'taxa_perf': 0},
        '24.621.986/0001-81': {'nome': 'CSHG MASTER FIM', 'taxa_adm': 0, 'taxa_perf': 0},
        '10.245.075/0001-65': {'nome': 'AXA WF EUR CREDIT SHORT DURATION', 'taxa_adm': 0, 'taxa_perf': 0},
        '09.553.491/0001-45': {'nome': 'ROBECO QI EMERGING CONSERVATIVE EQUITIES', 'taxa_adm': 0, 'taxa_perf': 0},
        '41.263.033/0001-63': {'nome': 'BTG PACTUAL TESOURO SELIC FI RF REF DI', 'taxa_adm': 0, 'taxa_perf': 0},
        '50.618.869/0001-37': {'nome': 'ITAÚ CARTEIRA LIVRE AÇÕES FIC', 'taxa_adm': 0, 'taxa_perf': 0},
        '11.861.450/0001-90': {'nome': 'MAUÁ INSTITUCIONAL FIC FIM', 'taxa_adm': 0, 'taxa_perf': 0},
        '04.740.906/0001-48': {'nome': 'ITAÚ VÉRTICE CASH RF FI', 'taxa_adm': 0, 'taxa_perf': 0},
        '13.977.901/0001-01': {'nome': 'ASHMORE EMERGING MARKETS EQUITY', 'taxa_adm': 0, 'taxa_perf': 0},
        '00.832.424/0001-12': {'nome': 'SANTANDER FI CURTO PRAZO', 'taxa_adm': 0, 'taxa_perf': 0},
        '13.990.090/0001-42': {'nome': 'ITAÚ TOP DI RF FICFI', 'taxa_adm': 0, 'taxa_perf': 0},
        '00.864.265/0001-96': {'nome': 'VOTORANTIM FIC RF CRED PRIV INFLAÇÃO CURTA', 'taxa_adm': 0, 'taxa_perf': 0},
        '12.462.636/0001-74': {'nome': 'MFS MERIDIAN ASIA EX-JAPAN', 'taxa_adm': 0, 'taxa_perf': 0},
    }
    
    return taxas_manuais

def obter_taxas_fundo(cnpj_fundo, df_cadastro):
    """
    Obtém as taxas de administração e performance de um fundo
    Primeiro tenta nas taxas manuais, depois no cadastro CVM
    """
    taxas_manuais = carregar_taxas_manuais()
    if cnpj_fundo in taxas_manuais:
        taxas = taxas_manuais[cnpj_fundo]
        print(f"Usando taxas manuais para {taxas['nome']}: Adm {taxas['taxa_adm']*100:.2f}%, Perf {taxas['taxa_perf']*100:.1f}%")
        return {'taxa_adm': taxas['taxa_adm'], 'taxa_perf': taxas['taxa_perf']}
    
    if df_cadastro is None:
        return {'taxa_adm': 0, 'taxa_perf': 0}
    
    try:
        cnpj_limpo = str(cnpj_fundo).replace('.', '').replace('/', '').replace('-', '')
        
        if 'CNPJ_FUNDO' in df_cadastro.columns:
            df_cadastro['CNPJ_FUNDO'] = df_cadastro['CNPJ_FUNDO'].astype(str)
            mask = df_cadastro['CNPJ_FUNDO'].str.replace('.', '').str.replace('/', '').str.replace('-', '') == cnpj_limpo
            fundo = df_cadastro[mask]
            
            if not fundo.empty:
                taxa_adm = 0
                taxa_perf = 0
                
                if 'TAXA_ADM' in fundo.columns:
                    val = fundo['TAXA_ADM'].iloc[0]
                    if pd.notna(val):
                        if isinstance(val, str):
                            taxa_adm = float(val.replace(',', '.'))
                        else:
                            taxa_adm = float(val)
                
                if 'VL_TAXA_PERFM' in fundo.columns:
                    val = fundo['VL_TAXA_PERFM'].iloc[0]
                    if pd.notna(val):
                        if isinstance(val, str):
                            taxa_perf = float(val.replace(',', '.'))
                        else:
                            taxa_perf = float(val)
                
                print(f"Taxas do cadastro CVM para {cnpj_fundo}: Adm {taxa_adm:.2f}%, Perf {taxa_perf:.1f}%")
                return {'taxa_adm': taxa_adm / 100, 'taxa_perf': taxa_perf / 100}
        
    except Exception as e:
        print(f"Erro ao obter taxas do fundo {cnpj_fundo}: {e}")
    
    print(f"Fundo {cnpj_fundo} não encontrado - será necessário adicionar manualmente")
    return {'taxa_adm': 0, 'taxa_perf': 0}

def calcular_custos_camada_zero(valor_total_carteira):
    """
    Calcula os custos da camada zero - Taxa de administração do Itaú sobre o Chimborazo
    """
    TAXA_ADMIN_ITAU = 0.0035  # 0,35% ao ano
    
    custo_anual = valor_total_carteira * TAXA_ADMIN_ITAU
    
    resultado = {
        'camada': 0,
        'nome': 'TAXA DE ADMINISTRAÇÃO ITAÚ - CHIMBORAZO',
        'valor_base': valor_total_carteira,
        'taxa_adm': TAXA_ADMIN_ITAU,
        'taxa_adm_pct': TAXA_ADMIN_ITAU * 100,
        'custo_adm_anual': custo_anual,
        'custo_total_anual': custo_anual,
        'custo_total_pct': TAXA_ADMIN_ITAU * 100
    }
    
    return pd.DataFrame([resultado])

def calcular_custos_primeira_camada(df_fundos, df_cadastro, valor_total_carteira, retorno_anual_estimado=0.12):
    """
    Calcula os custos da primeira camada (fundos diretos na carteira)
    
    Parâmetros:
    - retorno_anual_estimado: retorno anual estimado para cálculo da taxa de performance (default 12%)
    """
    resultados = []
    
    for _, fundo in df_fundos.iterrows():
        cnpj = fundo.get('cnpj', fundo.get('identificador', 'N/A'))
        nome = fundo['nome']
        valor = fundo['valor']
        peso = valor / valor_total_carteira
        
        taxas = obter_taxas_fundo(cnpj, df_cadastro)
        
        custo_adm_anual = valor * taxas['taxa_adm']
        
        # Taxa de performance é cobrada sobre o RETORNO, não sobre o valor total
        retorno_estimado = valor * retorno_anual_estimado
        # Performance fee é cobrada sobre o retorno que excede o benchmark (geralmente CDI)
        # Para simplificar, vamos usar 80% do retorno como base para performance fee
        base_performance = retorno_estimado * 0.8
        custo_perf_anual = base_performance * taxas['taxa_perf']
        
        custo_total_anual = custo_adm_anual + custo_perf_anual
        
        custo_total_pct = (custo_total_anual / valor * 100) if valor > 0 else 0
        
        resultados.append({
            'camada': 1,
            'cnpj': cnpj,
            'nome': nome,
            'valor_investido': valor,
            'peso_carteira': peso,
            'taxa_adm': taxas['taxa_adm'],
            'taxa_perf': taxas['taxa_perf'],
            'custo_adm_anual': custo_adm_anual,
            'custo_perf_anual': custo_perf_anual,
            'custo_total_anual': custo_total_anual,
            'custo_total_pct': custo_total_pct,
            'retorno_base_perf': base_performance
        })
    
    return pd.DataFrame(resultados)

def processar_segunda_camada_otimizada(df_primeira_camada, base_dir, df_cadastro):
    """
    Processa a segunda camada de forma otimizada para evitar problemas de memória
    Busca a carteira mais recente disponível para cada fundo, voltando até 12 meses
    """
    resultados_segunda_camada = []
    
    temp_base = tempfile.mkdtemp(prefix='sherpa_temp_')
    
    try:
        for _, fundo_nivel1 in df_primeira_camada.iterrows():
            cnpj_fundo = fundo_nivel1['cnpj']
            valor_fundo_nivel1 = fundo_nivel1['valor_investido']
            
            print(f"\nProcessando 2ª camada do fundo: {fundo_nivel1['nome']}")
            
            try:
                cache_file = os.path.join(base_dir, f'cache_carteira_{cnpj_fundo.replace("/", "_").replace(".", "_")}.pkl')
                
                df_carteira_nivel2 = None
                data_carteira_encontrada = None
                
                # Verificar cache primeiro
                if os.path.exists(cache_file):
                    mod_time = os.path.getmtime(cache_file)
                    if (datetime.now().timestamp() - mod_time) < 86400:  # Cache de 24 horas
                        print(f"Usando cache para {cnpj_fundo}")
                        with open(cache_file, 'rb') as f:
                            cache_data = pickle.load(f)
                            if isinstance(cache_data, dict) and 'data' in cache_data:
                                df_carteira_nivel2 = cache_data['carteira']
                                data_carteira_encontrada = cache_data['data']
                            else:
                                df_carteira_nivel2 = cache_data
                
                # Se não tem cache válido, buscar dados
                if df_carteira_nivel2 is None:
                    os.environ['TMPDIR'] = temp_base
                    
                    # Tentar buscar carteira dos últimos 12 meses
                    print(f"  Buscando carteira mais recente (últimos 12 meses)...")
                    carteira_fundo = processar_carteira_completa(
                        cnpj_fundo=cnpj_fundo,
                        base_dir=base_dir,
                        limite_arquivos=12  # Buscar até 12 meses para trás
                    )
                    
                    if carteira_fundo and len(carteira_fundo) > 0:
                        # Pegar a data mais recente disponível
                        data_mais_recente = max(carteira_fundo.keys())
                        df_carteira_nivel2 = carteira_fundo[data_mais_recente]
                        data_carteira_encontrada = data_mais_recente
                        
                        print(f"  ✓ Carteira encontrada em: {data_carteira_encontrada}")
                        
                        # Salvar cache com data
                        cache_data = {
                            'carteira': df_carteira_nivel2,
                            'data': data_carteira_encontrada
                        }
                        with open(cache_file, 'wb') as f:
                            pickle.dump(cache_data, f)
                    else:
                        print(f"  ✗ Nenhuma carteira encontrada nos últimos 12 meses")
                        continue
                
                fundos_nivel2 = identificar_fundos_na_carteira(df_carteira_nivel2)
                
                if not fundos_nivel2.empty:
                    valor_total_nivel2 = df_carteira_nivel2['VL_MERC_POS_FINAL'].sum()
                    
                    for _, fundo_n2 in fundos_nivel2.iterrows():
                        cnpj_n2 = fundo_n2.get('cnpj', fundo_n2.get('identificador', 'N/A'))
                        valor_n2 = fundo_n2['valor']
                        peso_n2_no_n1 = valor_n2 / valor_total_nivel2 if valor_total_nivel2 > 0 else 0
                        
                        valor_efetivo = valor_fundo_nivel1 * peso_n2_no_n1
                        
                        taxas = obter_taxas_fundo(cnpj_n2, df_cadastro)
                        
                        custo_adm_anual = valor_efetivo * taxas['taxa_adm']
                        
                        retorno_estimado = valor_efetivo * 0.12  # 12% de retorno anual estimado
                        base_performance = retorno_estimado * 0.8
                        custo_perf_anual = base_performance * taxas['taxa_perf']
                        
                        custo_total_anual = custo_adm_anual + custo_perf_anual
                        
                        resultados_segunda_camada.append({
                            'camada': 2,
                            'fundo_nivel1_cnpj': cnpj_fundo,
                            'fundo_nivel1_nome': fundo_nivel1['nome'],
                            'cnpj': cnpj_n2,
                            'nome': fundo_n2['nome'],
                            'valor_investido_direto': valor_n2,
                            'peso_no_fundo_n1': peso_n2_no_n1,
                            'valor_efetivo_chimborazo': valor_efetivo,
                            'taxa_adm': taxas['taxa_adm'],
                            'taxa_perf': taxas['taxa_perf'],
                            'custo_adm_anual': custo_adm_anual,
                            'custo_perf_anual': custo_perf_anual,
                            'custo_total_anual': custo_total_anual,
                            'custo_total_pct': (custo_total_anual / valor_efetivo * 100) if valor_efetivo > 0 else 0,
                            'retorno_base_perf': base_performance,
                            'data_carteira': data_carteira_encontrada  # Adicionar data da carteira
                        })
                        
            except Exception as e:
                print(f"Erro ao processar 2ª camada do fundo {cnpj_fundo}: {e}")
                
    finally:
        if os.path.exists(temp_base):
            shutil.rmtree(temp_base)
            
    return pd.DataFrame(resultados_segunda_camada)

def gerar_relatorio_custos_3camadas(df_camada_zero, df_primeira_camada, df_segunda_camada, valor_total_carteira, base_dir):
    """
    Gera relatório consolidado dos custos em 3 camadas
    """
    print("\n" + "="*80)
    print("RELATÓRIO DE CUSTOS EM 3 CAMADAS - FUNDO CHIMBORAZO")
    print("="*80)
    
    # Camada Zero - Taxa Itaú
    print("\nCAMADA ZERO - TAXA DE ADMINISTRAÇÃO ITAÚ:")
    print("-"*60)
    custo_itau = df_camada_zero['custo_total_anual'].sum()
    print(f"Taxa de administração Itaú: 0.35%")
    print(f"Valor base (patrimônio total): R$ {valor_total_carteira:,.2f}")
    print(f"Custo anual: R$ {custo_itau:,.2f}")
    print(f"Custo mensal: R$ {custo_itau/12:,.2f}")
    
    # Resumo 1ª Camada
    print("\n\n1ª CAMADA - FUNDOS DIRETOS NA CARTEIRA:")
    print("-"*60)
    
    custo_total_1a = df_primeira_camada['custo_total_anual'].sum()
    custo_adm_1a = df_primeira_camada['custo_adm_anual'].sum()
    custo_perf_1a = df_primeira_camada['custo_perf_anual'].sum()
    
    print(f"Número de fundos: {len(df_primeira_camada)}")
    print(f"Valor total em fundos: R$ {df_primeira_camada['valor_investido'].sum():,.2f}")
    print(f"% da carteira em fundos: {(df_primeira_camada['valor_investido'].sum() / valor_total_carteira * 100):.2f}%")
    print(f"\nCusto total anual 1ª camada: R$ {custo_total_1a:,.2f}")
    print(f"  - Taxa de administração: R$ {custo_adm_1a:,.2f}")
    print(f"  - Taxa de performance: R$ {custo_perf_1a:,.2f}")
    print(f"Custo % sobre patrimônio: {(custo_total_1a / valor_total_carteira * 100):.4f}%")
    
    print("\nNota: Taxa de performance calculada sobre retorno estimado de 12% a.a.")
    
    # Top 5 fundos por custo
    print("\nTop 5 fundos por custo absoluto:")
    top5 = df_primeira_camada.nlargest(5, 'custo_total_anual')
    for _, fundo in top5.iterrows():
        print(f"  {fundo['nome'][:50]:50} | R$ {fundo['custo_total_anual']:>12,.2f} | {fundo['custo_total_pct']:>6.2f}%")
    
    # Resumo 2ª Camada
    if not df_segunda_camada.empty:
        print("\n\n2ª CAMADA - FUNDOS DENTRO DOS FUNDOS:")
        print("-"*60)
        
        custo_total_2a = df_segunda_camada['custo_total_anual'].sum()
        custo_adm_2a = df_segunda_camada['custo_adm_anual'].sum()
        custo_perf_2a = df_segunda_camada['custo_perf_anual'].sum()
        
        print(f"Número de fundos: {len(df_segunda_camada)}")
        print(f"Valor efetivo na carteira: R$ {df_segunda_camada['valor_efetivo_chimborazo'].sum():,.2f}")
        print(f"\nCusto total anual 2ª camada: R$ {custo_total_2a:,.2f}")
        print(f"  - Taxa de administração: R$ {custo_adm_2a:,.2f}")
        print(f"  - Taxa de performance: R$ {custo_perf_2a:,.2f}")
        print(f"Custo % sobre patrimônio: {(custo_total_2a / valor_total_carteira * 100):.4f}%")
        
        # Fundos com maior presença na 2ª camada
        print("\nFundos nível 1 com mais subfundos:")
        contagem = df_segunda_camada.groupby('fundo_nivel1_nome').size().sort_values(ascending=False).head(5)
        for nome, count in contagem.items():
            print(f"  {nome[:50]:50} | {count} subfundos")
            
        # Mostrar datas das carteiras aninhadas se diferentes
        if 'data_carteira' in df_segunda_camada.columns:
            datas_unicas = df_segunda_camada['data_carteira'].unique()
            if len(datas_unicas) > 1:
                print("\nATENÇÃO: Carteiras de fundos aninhados de diferentes datas:")
                for data in sorted(datas_unicas):
                    fundos_data = df_segunda_camada[df_segunda_camada['data_carteira'] == data]['fundo_nivel1_nome'].unique()
                    print(f"  {data}: {', '.join([f[:30] for f in fundos_data[:3]])}{'...' if len(fundos_data) > 3 else ''}")
    else:
        custo_total_2a = 0
        custo_adm_2a = 0
        custo_perf_2a = 0
    
    # Resumo Total
    print("\n\nRESUMO TOTAL DAS 3 CAMADAS:")
    print("="*60)
    custo_total_geral = custo_itau + custo_total_1a + custo_total_2a
    print(f"Camada 0 (Taxa Itaú 0.35%): R$ {custo_itau:,.2f}")
    print(f"Camada 1 (Fundos diretos): R$ {custo_total_1a:,.2f}")
    print(f"Camada 2 (Fundos aninhados): R$ {custo_total_2a:,.2f}")
    print(f"\nCUSTO TOTAL ANUAL: R$ {custo_total_geral:,.2f}")
    print(f"CUSTO TOTAL % SOBRE PATRIMÔNIO: {(custo_total_geral / valor_total_carteira * 100):.4f}%")
    print(f"CUSTO MENSAL ESTIMADO: R$ {custo_total_geral / 12:,.2f}")
    
    # Detalhamento por tipo de custo
    print("\n\nDETALHAMENTO POR TIPO DE CUSTO:")
    print("-"*60)
    total_admin = custo_itau + custo_adm_1a + custo_adm_2a
    total_perf = custo_perf_1a + custo_perf_2a
    print(f"Total Taxa de Administração: R$ {total_admin:,.2f} ({(total_admin/valor_total_carteira*100):.4f}%)")
    print(f"Total Taxa de Performance: R$ {total_perf:,.2f} ({(total_perf/valor_total_carteira*100):.4f}%)")
    
    # Salvar resultados em Excel
    caminho_saida = os.path.join(base_dir, 'analise_custos_chimborazo_3camadas.xlsx')
    with pd.ExcelWriter(caminho_saida, engine='openpyxl') as writer:
        df_camada_zero.to_excel(writer, sheet_name='Camada_0_Taxa_Itau', index=False)
        df_primeira_camada.to_excel(writer, sheet_name='Camada_1_Fundos_Diretos', index=False)
        if not df_segunda_camada.empty:
            df_segunda_camada.to_excel(writer, sheet_name='Camada_2_Fundos_Aninhados', index=False)
        
        # Criar resumo
        resumo = pd.DataFrame([
            {'Métrica': 'Valor Total Carteira', 'Valor': valor_total_carteira},
            {'Métrica': 'Custo Camada 0 (Taxa Itaú)', 'Valor': custo_itau},
            {'Métrica': 'Custo Camada 1 (Fundos Diretos)', 'Valor': custo_total_1a},
            {'Métrica': 'Custo Camada 2 (Fundos Aninhados)', 'Valor': custo_total_2a},
            {'Métrica': 'Custo Total Geral', 'Valor': custo_total_geral},
            {'Métrica': 'Custo % sobre Patrimônio', 'Valor': (custo_total_geral / valor_total_carteira * 100)},
            {'Métrica': 'Custo Total Admin', 'Valor': total_admin},
            {'Métrica': 'Custo Total Performance', 'Valor': total_perf}
        ])
        resumo.to_excel(writer, sheet_name='Resumo', index=False)
    
    print(f"\nRelatório salvo em: {caminho_saida}")
    
    return {
        'camada_zero': df_camada_zero,
        'primeira_camada': df_primeira_camada,
        'segunda_camada': df_segunda_camada,
        'custo_total': custo_total_geral,
        'custo_percentual': (custo_total_geral / valor_total_carteira * 100)
    }

def plotar_analise_custos_3camadas(df_camada_zero, df_primeira_camada, df_segunda_camada, base_dir):
    """
    Cria visualizações da análise de custos em 3 camadas
    """
    plt.switch_backend('Agg')
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Análise de Custos em 3 Camadas - Fundo Chimborazo', fontsize=16)
    
    # 1. Pizza - Distribuição por camadas
    ax1 = axes[0, 0]
    custo_c0 = df_camada_zero['custo_total_anual'].sum()
    custo_c1 = df_primeira_camada['custo_total_anual'].sum()
    custo_c2 = df_segunda_camada['custo_total_anual'].sum() if not df_segunda_camada.empty else 0
    
    valores_camadas = [custo_c0, custo_c1, custo_c2]
    labels_camadas = ['Camada 0\n(Taxa Itaú)', 'Camada 1\n(Fundos Diretos)', 'Camada 2\n(Fundos Aninhados)']
    colors = ['#ff9999', '#66b3ff', '#99ff99']
    
    ax1.pie(valores_camadas, labels=labels_camadas, autopct='%1.1f%%', startangle=90, colors=colors)
    ax1.set_title('Distribuição de Custos por Camada')
    
    # 2. Barras empilhadas - Composição dos custos
    ax2 = axes[0, 1]
    
    # Preparar dados para barras empilhadas
    admin_c0 = custo_c0
    admin_c1 = df_primeira_camada['custo_adm_anual'].sum()
    admin_c2 = df_segunda_camada['custo_adm_anual'].sum() if not df_segunda_camada.empty else 0
    
    perf_c1 = df_primeira_camada['custo_perf_anual'].sum()
    perf_c2 = df_segunda_camada['custo_perf_anual'].sum() if not df_segunda_camada.empty else 0
    
    dados_barras = pd.DataFrame({
        'Taxa Admin': [admin_c0/1e6, admin_c1/1e6, admin_c2/1e6],
        'Taxa Perf': [0, perf_c1/1e6, perf_c2/1e6]
    }, index=['Camada 0', 'Camada 1', 'Camada 2'])
    
    dados_barras.plot(kind='bar', stacked=True, ax=ax2)
    ax2.set_ylabel('Custo (R$ milhões)')
    ax2.set_title('Composição de Custos por Camada')
    ax2.legend(title='Tipo de Taxa')
    ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45)
    
    # 3. Top 10 custos consolidados
    ax3 = axes[1, 0]
    
    # Consolidar todos os custos
    todos_custos = []
    
    # Camada 0
    todos_custos.append({
        'nome': 'Taxa Itaú (0.35%)',
        'custo': custo_c0,
        'camada': 'C0'
    })
    
    # Camada 1
    for _, fundo in df_primeira_camada.iterrows():
        todos_custos.append({
            'nome': fundo['nome'][:30],
            'custo': fundo['custo_total_anual'],
            'camada': 'C1'
        })
    
    # Camada 2
    if not df_segunda_camada.empty:
        for _, fundo in df_segunda_camada.iterrows():
            todos_custos.append({
                'nome': fundo['nome'][:30],
                'custo': fundo['custo_total_anual'],
                'camada': 'C2'
            })
    
    df_todos = pd.DataFrame(todos_custos)
    top10_total = df_todos.nlargest(10, 'custo')
    
    y_pos = np.arange(len(top10_total))
    bars = ax3.barh(y_pos, top10_total['custo'] / 1e3)
    
    # Colorir barras por camada
    for i, (idx, row) in enumerate(top10_total.iterrows()):
        if row['camada'] == 'C0':
            bars[i].set_color('#ff9999')
        elif row['camada'] == 'C1':
            bars[i].set_color('#66b3ff')
        else:
            bars[i].set_color('#99ff99')
    
    ax3.set_yticks(y_pos)
    ax3.set_yticklabels(top10_total['nome'])
    ax3.set_xlabel('Custo Anual (R$ mil)')
    ax3.set_title('Top 10 Maiores Custos (Todas as Camadas)')
    ax3.grid(True, alpha=0.3, axis='x')
    
    # 4. Evolução acumulada dos custos
    ax4 = axes[1, 1]
    
    camadas = ['Patrimônio\nInicial', 'Camada 0\n(Taxa Itaú)', 'Camada 1\n(Fundos)', 'Camada 2\n(Aninhados)']
    valores_acum = [0, custo_c0/1e6, (custo_c0 + custo_c1)/1e6, (custo_c0 + custo_c1 + custo_c2)/1e6]
    
    ax4.plot(camadas, valores_acum, 'o-', linewidth=2, markersize=10)
    ax4.fill_between(range(len(camadas)), valores_acum, alpha=0.3)
    ax4.set_ylabel('Custo Acumulado (R$ milhões)')
    ax4.set_title('Evolução Acumulada dos Custos por Camada')
    ax4.grid(True, alpha=0.3)
    
    # Adicionar valores nos pontos
    for i, v in enumerate(valores_acum):
        ax4.text(i, v + 0.1, f'R$ {v:.2f}M', ha='center')
    
    plt.tight_layout()
    caminho_grafico = os.path.join(base_dir, 'analise_custos_chimborazo_3camadas_graficos.png')
    plt.savefig(caminho_grafico, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Gráficos salvos em: {caminho_grafico}")

def main():
    """
    Função principal para executar a análise em 3 camadas
    """
    # Configurações
    CNPJ_CHIMBORAZO = '54.195.596/0001-51'
    NOME_CHIMBORAZO = 'chimborazo'
    BASE_DIR = r"C:\Users\guilh\Documents\GitHub\sherpa\database"
    
    print("Iniciando análise de custos em 3 camadas - Fundo Chimborazo")
    print("="*80)
    
    # 1. Carregar dados cadastrais dos fundos
    print("\n1. Carregando dados cadastrais dos fundos...")
    df_cadastro = carregar_dados_cadastrais_fundos(BASE_DIR)
    
    # 2. Carregar carteira do Chimborazo
    print("\n2. Carregando carteira do Chimborazo...")
    try:
        # Tentar primeiro o arquivo completo com fundos
        caminho_completo = os.path.join(BASE_DIR, 'serial_carteiras', 'carteira_chimborazo_completa.pkl')
        if os.path.exists(caminho_completo):
            print("Usando arquivo com carteira completa (inclui fundos)...")
            with open(caminho_completo, 'rb') as f:
                dados_chimborazo = pickle.load(f)
            carteiras = dados_chimborazo['carteira_categorizada']
            data_mais_recente = max(carteiras.keys())
            df_carteira_chimborazo = carteiras[data_mais_recente]
            print(f"Carteira carregada para data: {data_mais_recente}")
        else:
            # Fallback para arquivo antigo ou reprocessar
            dados_chimborazo = carregar_carteira_serializada(BASE_DIR, NOME_CHIMBORAZO)
            if dados_chimborazo and 'carteira_categorizada' in dados_chimborazo:
                carteiras = dados_chimborazo['carteira_categorizada']
                data_mais_recente = max(carteiras.keys())
                df_carteira_chimborazo = carteiras[data_mais_recente]
                print(f"Carteira carregada para data: {data_mais_recente}")
            else:
                carteiras = processar_carteira_completa(
                    cnpj_fundo=CNPJ_CHIMBORAZO,
                    base_dir=BASE_DIR,
                    limite_arquivos=6  # Processar últimos 6 meses
                )
                data_mais_recente = max(carteiras.keys())
                df_carteira_chimborazo = carteiras[data_mais_recente]
    except Exception as e:
        print(f"Erro ao carregar carteira: {e}")
        return
    
    # 3. Calcular valor total da carteira
    # Converter valores para numérico se necessário
    if 'VL_MERC_POS_FINAL' in df_carteira_chimborazo.columns:
        df_carteira_chimborazo['VL_MERC_POS_FINAL'] = pd.to_numeric(
            df_carteira_chimborazo['VL_MERC_POS_FINAL'].astype(str).str.replace(',', '.'), 
            errors='coerce'
        )
    valor_total_carteira = df_carteira_chimborazo['VL_MERC_POS_FINAL'].sum()
    print(f"\nValor total da carteira: R$ {valor_total_carteira:,.2f}")
    
    # 4. Calcular custos da Camada 0 (Taxa Itaú)
    print("\n3. Calculando custos da Camada 0 (Taxa de administração Itaú)...")
    df_custos_camada_zero = calcular_custos_camada_zero(valor_total_carteira)
    
    # 5. Identificar fundos na carteira (1ª camada)
    print("\n4. Identificando fundos na carteira (1ª camada)...")
    df_fundos_nivel1 = identificar_fundos_na_carteira(df_carteira_chimborazo)
    print(f"Encontrados {len(df_fundos_nivel1)} fundos na carteira")
    
    # 6. Calcular custos da 1ª camada
    print("\n5. Calculando custos da 1ª camada...")
    df_custos_1a_camada = calcular_custos_primeira_camada(
        df_fundos_nivel1, 
        df_cadastro,
        valor_total_carteira
    )
    
    # 7. Processar 2ª camada
    print("\n6. Processando 2ª camada (fundos dentro dos fundos)...")
    df_custos_2a_camada = processar_segunda_camada_otimizada(
        df_custos_1a_camada,
        BASE_DIR,
        df_cadastro
    )
    
    # 8. Gerar relatório
    print("\n7. Gerando relatório consolidado...")
    resultados = gerar_relatorio_custos_3camadas(
        df_custos_camada_zero,
        df_custos_1a_camada,
        df_custos_2a_camada,
        valor_total_carteira,
        BASE_DIR
    )
    
    # 9. Gerar visualizações
    print("\n8. Gerando visualizações...")
    plotar_analise_custos_3camadas(
        df_custos_camada_zero,
        df_custos_1a_camada, 
        df_custos_2a_camada, 
        BASE_DIR
    )
    
    print("\nAnálise concluída!")
    
    return resultados

if __name__ == "__main__":
    resultados = main()