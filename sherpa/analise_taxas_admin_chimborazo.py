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

# Importar funções necessárias dos módulos existentes
from carteiras_analysis_utils import (
    carregar_carteira_serializada,
    processar_carteira_completa
)

def carregar_dados_cadastrais_fundos(base_dir):
    """
    Carrega dados cadastrais dos fundos para obter taxas de administração
    """
    try:
        # Tentar carregar cache completo se existir
        cache_path = os.path.join(base_dir, 'cache_cadastro_completo.pkl')
        if os.path.exists(cache_path):
            print("Carregando dados do cache...")
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        
        print("Carregando dados cadastrais e de taxas...")
        
        # Carregar arquivo principal de cadastro
        caminho_cad = os.path.join(base_dir, 'CAD', 'cad_fi.csv')
        df_cadastro = pd.read_csv(caminho_cad, encoding='latin-1', delimiter=';', low_memory=False)
        print(f"Cadastro principal carregado: {len(df_cadastro)} registros")
        
        # Carregar arquivo de taxas de administração
        caminho_taxa_adm = os.path.join(base_dir, 'CAD', 'cad_fi_hist_taxa_adm.csv')
        df_taxa_adm = pd.read_csv(caminho_taxa_adm, encoding='latin-1', delimiter=';', low_memory=False)
        print(f"Taxas de administração carregadas: {len(df_taxa_adm)} registros")
        
        # Pegar as taxas mais recentes para cada fundo
        if 'DT_REG' in df_taxa_adm.columns:
            df_taxa_adm['DT_REG'] = pd.to_datetime(df_taxa_adm['DT_REG'])
            df_taxa_adm_recente = df_taxa_adm.sort_values('DT_REG').groupby('CNPJ_FUNDO').last().reset_index()
        else:
            df_taxa_adm_recente = df_taxa_adm.groupby('CNPJ_FUNDO').last().reset_index()
        
        # Merge dos dados
        df_completo = df_cadastro.merge(
            df_taxa_adm_recente[['CNPJ_FUNDO', 'TAXA_ADM']], 
            on='CNPJ_FUNDO', 
            how='left'
        )
        
        print(f"Dados completos preparados: {len(df_completo)} registros")
        
        # Salvar cache
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
    print(f"Categorias de ativos: {df_carteira['CATEGORIA_ATIVO'].unique() if 'CATEGORIA_ATIVO' in df_carteira.columns else 'N/A'}")
    
    # Primeiro, verificar pela categoria de ativo
    if 'CATEGORIA_ATIVO' in df_carteira.columns:
        df_fundos = df_carteira[df_carteira['CATEGORIA_ATIVO'] == 'Fundos'].copy()
        print(f"Fundos encontrados pela categoria: {len(df_fundos)}")
        
        if len(df_fundos) > 0:
            # Agrupar por CNPJ_FUNDO_CLASSE_COTA que é onde está o CNPJ do fundo investido
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
    
    return pd.DataFrame(fundos)

def carregar_taxas_manuais():
    """
    Carrega taxas de administração manuais para fundos conhecidos
    """
    taxas_manuais = {
        # Private Equity
        '41.535.122/0001-60': {'nome': 'KINEA PRIVATE EQUITY V', 'taxa_adm': 0.02},
        '32.311.914/0001-60': {'nome': 'VINCI CAPITAL PARTNERS III', 'taxa_adm': 0.02},
        
        # FIDC
        '12.138.862/0001-64': {'nome': 'SILVERADO MAXIMUM II', 'taxa_adm': 0.015},
        
        # Fundos conhecidos
        '56.430.872/0001-44': {'nome': 'ALPAMAYO', 'taxa_adm': 0.015},
        '07.096.546/0001-37': {'nome': 'ITAÚ VÉRTICE RF DI', 'taxa_adm': 0.003},
        '55.419.784/0001-89': {'nome': 'ITAÚ DOLOMITAS', 'taxa_adm': 0.02},
        '24.546.223/0001-17': {'nome': 'ITAÚ VÉRTICE IBOVESPA', 'taxa_adm': 0.003},
        '21.407.105/0001-30': {'nome': 'ITAÚ VÉRTICE RF DI FIF', 'taxa_adm': 0.003},
        '18.138.913/0001-34': {'nome': 'ITAÚ VÉRTICE COMPROMISSO RF DI', 'taxa_adm': 0.003},
        '36.248.791/0001-10': {'nome': 'CAPSTONE MACRO A', 'taxa_adm': 0.02},
    }
    
    return taxas_manuais

def obter_taxa_admin_fundo(cnpj_fundo, df_cadastro):
    """
    Obtém a taxa de administração de um fundo
    """
    # Primeiro tentar taxas manuais
    taxas_manuais = carregar_taxas_manuais()
    if cnpj_fundo in taxas_manuais:
        taxa = taxas_manuais[cnpj_fundo]
        return {
            'taxa_adm': taxa['taxa_adm'], 
            'fonte': 'manual',
            'nome_manual': taxa['nome']
        }
    
    # Se não encontrou nas manuais, tentar no cadastro CVM
    if df_cadastro is None:
        return {'taxa_adm': None, 'fonte': 'não_encontrado', 'nome_manual': None}
    
    try:
        # Limpar CNPJ
        cnpj_limpo = str(cnpj_fundo).replace('.', '').replace('/', '').replace('-', '')
        
        # Buscar no cadastro
        if 'CNPJ_FUNDO' in df_cadastro.columns:
            df_cadastro['CNPJ_FUNDO'] = df_cadastro['CNPJ_FUNDO'].astype(str)
            mask = df_cadastro['CNPJ_FUNDO'].str.replace('.', '').str.replace('/', '').str.replace('-', '') == cnpj_limpo
            fundo = df_cadastro[mask]
            
            if not fundo.empty:
                taxa_adm = 0
                
                # Obter taxa de administração
                if 'TAXA_ADM' in fundo.columns:
                    val = fundo['TAXA_ADM'].iloc[0]
                    if pd.notna(val):
                        if isinstance(val, str):
                            taxa_adm = float(val.replace(',', '.'))
                        else:
                            taxa_adm = float(val)
                        
                        # As taxas já vêm em percentual, então dividimos por 100
                        return {'taxa_adm': taxa_adm / 100, 'fonte': 'CVM', 'nome_manual': None}
        
    except Exception as e:
        print(f"Erro ao obter taxa do fundo {cnpj_fundo}: {e}")
    
    return {'taxa_adm': None, 'fonte': 'não_encontrado', 'nome_manual': None}

def calcular_custos_primeira_camada(df_fundos, df_cadastro, valor_total_carteira):
    """
    Calcula os custos de administração da primeira camada
    """
    resultados = []
    fundos_sem_taxa = []
    
    for _, fundo in df_fundos.iterrows():
        cnpj = fundo.get('cnpj', fundo.get('identificador', 'N/A'))
        nome = fundo['nome']
        valor = fundo['valor']
        peso = valor / valor_total_carteira
        
        # Obter taxa de administração
        info_taxa = obter_taxa_admin_fundo(cnpj, df_cadastro)
        
        if info_taxa['taxa_adm'] is not None:
            taxa_adm = info_taxa['taxa_adm']
            custo_adm_anual = valor * taxa_adm
            
            resultados.append({
                'camada': 1,
                'cnpj': cnpj,
                'nome': nome,
                'valor_investido': valor,
                'peso_carteira': peso,
                'taxa_adm': taxa_adm,
                'taxa_adm_pct': taxa_adm * 100,
                'custo_adm_anual': custo_adm_anual,
                'fonte_taxa': info_taxa['fonte']
            })
            
            if info_taxa['fonte'] == 'manual':
                print(f"✓ {nome[:50]:50} | Taxa: {taxa_adm*100:.2f}% (manual)")
            else:
                print(f"✓ {nome[:50]:50} | Taxa: {taxa_adm*100:.2f}% (CVM)")
        else:
            fundos_sem_taxa.append({
                'cnpj': cnpj,
                'nome': nome,
                'valor': valor,
                'peso': peso
            })
            print(f"✗ {nome[:50]:50} | Taxa não encontrada")
    
    df_resultados = pd.DataFrame(resultados)
    df_sem_taxa = pd.DataFrame(fundos_sem_taxa)
    
    return df_resultados, df_sem_taxa

def processar_segunda_camada_otimizada(df_primeira_camada, base_dir, df_cadastro):
    """
    Processa a segunda camada focando apenas em taxas de administração
    """
    resultados_segunda_camada = []
    fundos_sem_taxa_2a = []
    
    # Usar diretório temporário específico
    temp_base = tempfile.mkdtemp(prefix='sherpa_temp_')
    
    try:
        for _, fundo_nivel1 in df_primeira_camada.iterrows():
            cnpj_fundo = fundo_nivel1['cnpj']
            valor_fundo_nivel1 = fundo_nivel1['valor_investido']
            
            print(f"\nProcessando 2ª camada do fundo: {fundo_nivel1['nome'][:50]}")
            
            try:
                # Criar cache específico para este fundo
                cache_file = os.path.join(base_dir, f'cache_carteira_{cnpj_fundo.replace("/", "_").replace(".", "_")}.pkl')
                
                # Verificar se existe cache recente
                df_carteira_nivel2 = None
                if os.path.exists(cache_file):
                    mod_time = os.path.getmtime(cache_file)
                    if (datetime.now().timestamp() - mod_time) < 86400:  # Cache de 24 horas
                        print(f"  Usando cache para {cnpj_fundo}")
                        with open(cache_file, 'rb') as f:
                            df_carteira_nivel2 = pickle.load(f)
                
                if df_carteira_nivel2 is None:
                    # Processar
                    os.environ['TMPDIR'] = temp_base
                    carteira_fundo = processar_carteira_completa(
                        cnpj_fundo=cnpj_fundo,
                        base_dir=base_dir,
                        limite_arquivos=1
                    )
                    
                    if carteira_fundo and len(carteira_fundo) > 0:
                        data_mais_recente = max(carteira_fundo.keys())
                        df_carteira_nivel2 = carteira_fundo[data_mais_recente]
                        
                        # Salvar cache
                        with open(cache_file, 'wb') as f:
                            pickle.dump(df_carteira_nivel2, f)
                    else:
                        continue
                
                # Identificar fundos nesta carteira
                fundos_nivel2 = identificar_fundos_na_carteira(df_carteira_nivel2)
                
                if not fundos_nivel2.empty:
                    valor_total_nivel2 = df_carteira_nivel2['VL_MERC_POS_FINAL'].sum()
                    print(f"  Encontrados {len(fundos_nivel2)} fundos na 2ª camada")
                    
                    for _, fundo_n2 in fundos_nivel2.iterrows():
                        cnpj_n2 = fundo_n2.get('cnpj', fundo_n2.get('identificador', 'N/A'))
                        valor_n2 = fundo_n2['valor']
                        peso_n2_no_n1 = valor_n2 / valor_total_nivel2 if valor_total_nivel2 > 0 else 0
                        
                        # Valor efetivo na carteira do Chimborazo
                        valor_efetivo = valor_fundo_nivel1 * peso_n2_no_n1
                        
                        # Obter taxa de administração
                        info_taxa = obter_taxa_admin_fundo(cnpj_n2, df_cadastro)
                        
                        if info_taxa['taxa_adm'] is not None:
                            taxa_adm = info_taxa['taxa_adm']
                            custo_adm_anual = valor_efetivo * taxa_adm
                            
                            resultados_segunda_camada.append({
                                'camada': 2,
                                'fundo_nivel1_cnpj': cnpj_fundo,
                                'fundo_nivel1_nome': fundo_nivel1['nome'],
                                'cnpj': cnpj_n2,
                                'nome': fundo_n2['nome'],
                                'valor_investido_direto': valor_n2,
                                'peso_no_fundo_n1': peso_n2_no_n1,
                                'valor_efetivo_chimborazo': valor_efetivo,
                                'taxa_adm': taxa_adm,
                                'taxa_adm_pct': taxa_adm * 100,
                                'custo_adm_anual': custo_adm_anual,
                                'fonte_taxa': info_taxa['fonte']
                            })
                            
                            print(f"    ✓ {fundo_n2['nome'][:40]:40} | Taxa: {taxa_adm*100:.2f}%")
                        else:
                            fundos_sem_taxa_2a.append({
                                'camada': 2,
                                'fundo_nivel1_nome': fundo_nivel1['nome'],
                                'cnpj': cnpj_n2,
                                'nome': fundo_n2['nome'],
                                'valor_efetivo': valor_efetivo,
                                'peso_efetivo': valor_efetivo / valor_total_carteira
                            })
                            print(f"    ✗ {fundo_n2['nome'][:40]:40} | Taxa não encontrada")
                        
            except Exception as e:
                print(f"  Erro ao processar 2ª camada: {e}")
                
    finally:
        # Limpar diretório temporário
        if os.path.exists(temp_base):
            shutil.rmtree(temp_base)
    
    df_resultados_2a = pd.DataFrame(resultados_segunda_camada)
    df_sem_taxa_2a = pd.DataFrame(fundos_sem_taxa_2a)
    
    return df_resultados_2a, df_sem_taxa_2a

def gerar_relatorio_taxas_admin(df_primeira_camada, df_segunda_camada, df_sem_taxa_1a, df_sem_taxa_2a, valor_total_carteira, base_dir):
    """
    Gera relatório focado em taxas de administração
    """
    print("\n" + "="*80)
    print("RELATÓRIO DE TAXAS DE ADMINISTRAÇÃO - FUNDO CHIMBORAZO")
    print("="*80)
    
    # Resumo 1ª Camada
    print("\n1ª CAMADA - FUNDOS DIRETOS NA CARTEIRA:")
    print("-"*60)
    
    if not df_primeira_camada.empty:
        custo_adm_1a = df_primeira_camada['custo_adm_anual'].sum()
        taxa_media_1a = (df_primeira_camada['taxa_adm'] * df_primeira_camada['valor_investido']).sum() / df_primeira_camada['valor_investido'].sum()
        
        print(f"Fundos com taxa identificada: {len(df_primeira_camada)}")
        print(f"Valor total: R$ {df_primeira_camada['valor_investido'].sum():,.2f}")
        print(f"Taxa de administração média ponderada: {taxa_media_1a*100:.3f}%")
        print(f"Custo anual de administração: R$ {custo_adm_1a:,.2f}")
        print(f"Custo % sobre patrimônio total: {(custo_adm_1a / valor_total_carteira * 100):.4f}%")
        
        # Detalhamento por fundo
        print("\nDetalhamento por fundo:")
        df_1a_ordenado = df_primeira_camada.sort_values('custo_adm_anual', ascending=False)
        for _, fundo in df_1a_ordenado.iterrows():
            print(f"  {fundo['nome'][:40]:40} | Taxa: {fundo['taxa_adm_pct']:>5.2f}% | Custo: R$ {fundo['custo_adm_anual']:>10,.2f} | Fonte: {fundo['fonte_taxa']}")
    else:
        custo_adm_1a = 0
    
    # Fundos sem taxa - 1ª Camada
    if not df_sem_taxa_1a.empty:
        print(f"\nFUNDOS SEM TAXA IDENTIFICADA (1ª Camada): {len(df_sem_taxa_1a)}")
        valor_sem_taxa_1a = df_sem_taxa_1a['valor'].sum()
        print(f"Valor total sem taxa: R$ {valor_sem_taxa_1a:,.2f} ({valor_sem_taxa_1a/valor_total_carteira*100:.2f}% do patrimônio)")
        for _, fundo in df_sem_taxa_1a.iterrows():
            print(f"  ⚠ {fundo['nome'][:40]:40} | CNPJ: {fundo['cnpj']} | Valor: R$ {fundo['valor']:>10,.2f}")
    
    # Resumo 2ª Camada
    if not df_segunda_camada.empty:
        print("\n\n2ª CAMADA - FUNDOS DENTRO DOS FUNDOS:")
        print("-"*60)
        
        custo_adm_2a = df_segunda_camada['custo_adm_anual'].sum()
        taxa_media_2a = (df_segunda_camada['taxa_adm'] * df_segunda_camada['valor_efetivo_chimborazo']).sum() / df_segunda_camada['valor_efetivo_chimborazo'].sum()
        
        print(f"Fundos com taxa identificada: {len(df_segunda_camada)}")
        print(f"Valor efetivo na carteira: R$ {df_segunda_camada['valor_efetivo_chimborazo'].sum():,.2f}")
        print(f"Taxa de administração média ponderada: {taxa_media_2a*100:.3f}%")
        print(f"Custo anual de administração: R$ {custo_adm_2a:,.2f}")
        print(f"Custo % sobre patrimônio total: {(custo_adm_2a / valor_total_carteira * 100):.4f}%")
        
        # Fundos com maior custo na 2ª camada
        print("\nTop 10 fundos por custo (2ª camada):")
        top10_2a = df_segunda_camada.nlargest(10, 'custo_adm_anual')
        for _, fundo in top10_2a.iterrows():
            print(f"  {fundo['nome'][:35]:35} | Taxa: {fundo['taxa_adm_pct']:>5.2f}% | Custo: R$ {fundo['custo_adm_anual']:>9,.2f}")
    else:
        custo_adm_2a = 0
    
    # Fundos sem taxa - 2ª Camada
    if not df_sem_taxa_2a.empty:
        print(f"\nFUNDOS SEM TAXA IDENTIFICADA (2ª Camada): {len(df_sem_taxa_2a)}")
        valor_sem_taxa_2a = df_sem_taxa_2a['valor_efetivo'].sum()
        print(f"Valor efetivo sem taxa: R$ {valor_sem_taxa_2a:,.2f} ({valor_sem_taxa_2a/valor_total_carteira*100:.2f}% do patrimônio)")
        for _, fundo in df_sem_taxa_2a.iterrows():
            print(f"  ⚠ {fundo['nome'][:35]:35} | CNPJ: {fundo['cnpj']} | Via: {fundo['fundo_nivel1_nome'][:20]}")
    
    # Resumo Total
    print("\n\nRESUMO TOTAL:")
    print("="*60)
    custo_total_adm = custo_adm_1a + custo_adm_2a
    print(f"Custo total de administração (1ª + 2ª camadas): R$ {custo_total_adm:,.2f}")
    print(f"Taxa efetiva total sobre patrimônio: {(custo_total_adm / valor_total_carteira * 100):.4f}%")
    print(f"Custo mensal estimado: R$ {custo_total_adm / 12:,.2f}")
    
    # Análise de cobertura
    valor_com_taxa = df_primeira_camada['valor_investido'].sum() if not df_primeira_camada.empty else 0
    valor_com_taxa += df_segunda_camada['valor_efetivo_chimborazo'].sum() if not df_segunda_camada.empty else 0
    valor_sem_taxa = df_sem_taxa_1a['valor'].sum() if not df_sem_taxa_1a.empty else 0
    valor_sem_taxa += df_sem_taxa_2a['valor_efetivo'].sum() if not df_sem_taxa_2a.empty else 0
    
    print(f"\nANÁLISE DE COBERTURA:")
    print(f"Valor com taxa identificada: R$ {valor_com_taxa:,.2f} ({valor_com_taxa/valor_total_carteira*100:.1f}%)")
    print(f"Valor sem taxa identificada: R$ {valor_sem_taxa:,.2f} ({valor_sem_taxa/valor_total_carteira*100:.1f}%)")
    
    # Salvar resultados em Excel
    caminho_saida = os.path.join(base_dir, 'analise_taxas_admin_chimborazo.xlsx')
    with pd.ExcelWriter(caminho_saida, engine='openpyxl') as writer:
        # Dados principais
        if not df_primeira_camada.empty:
            df_primeira_camada.to_excel(writer, sheet_name='1a_Camada_Com_Taxa', index=False)
        if not df_segunda_camada.empty:
            df_segunda_camada.to_excel(writer, sheet_name='2a_Camada_Com_Taxa', index=False)
        if not df_sem_taxa_1a.empty:
            df_sem_taxa_1a.to_excel(writer, sheet_name='1a_Camada_Sem_Taxa', index=False)
        if not df_sem_taxa_2a.empty:
            df_sem_taxa_2a.to_excel(writer, sheet_name='2a_Camada_Sem_Taxa', index=False)
        
        # Criar resumo
        resumo = pd.DataFrame([
            {'Métrica': 'Valor Total Carteira', 'Valor': valor_total_carteira},
            {'Métrica': 'Custo Admin 1ª Camada', 'Valor': custo_adm_1a},
            {'Métrica': 'Custo Admin 2ª Camada', 'Valor': custo_adm_2a},
            {'Métrica': 'Custo Admin Total', 'Valor': custo_total_adm},
            {'Métrica': 'Taxa Efetiva Total (%)', 'Valor': (custo_total_adm / valor_total_carteira * 100)},
            {'Métrica': 'Valor com Taxa Identificada', 'Valor': valor_com_taxa},
            {'Métrica': 'Valor sem Taxa Identificada', 'Valor': valor_sem_taxa},
            {'Métrica': 'Cobertura (%)', 'Valor': (valor_com_taxa / (valor_com_taxa + valor_sem_taxa) * 100) if (valor_com_taxa + valor_sem_taxa) > 0 else 0}
        ])
        resumo.to_excel(writer, sheet_name='Resumo', index=False)
    
    print(f"\nRelatório salvo em: {caminho_saida}")
    
    return {
        'primeira_camada': df_primeira_camada,
        'segunda_camada': df_segunda_camada,
        'sem_taxa_1a': df_sem_taxa_1a,
        'sem_taxa_2a': df_sem_taxa_2a,
        'custo_total_admin': custo_total_adm,
        'taxa_efetiva': (custo_total_adm / valor_total_carteira * 100)
    }

def plotar_analise_taxas_admin(df_primeira_camada, df_segunda_camada, df_sem_taxa_1a, df_sem_taxa_2a, valor_total_carteira, base_dir):
    """
    Cria visualizações focadas em taxas de administração
    """
    plt.switch_backend('Agg')
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Análise de Taxas de Administração - Fundo Chimborazo', fontsize=16)
    
    # 1. Pizza - Distribuição de custos por fundo (1ª camada)
    ax1 = axes[0, 0]
    if not df_primeira_camada.empty:
        top10_1a = df_primeira_camada.nlargest(10, 'custo_adm_anual')
        outros_1a = df_primeira_camada[~df_primeira_camada.index.isin(top10_1a.index)]['custo_adm_anual'].sum()
        
        valores_pizza = top10_1a['custo_adm_anual'].tolist()
        labels_pizza = [f"{nome[:20]}... ({taxa:.2f}%)" for nome, taxa in zip(top10_1a['nome'], top10_1a['taxa_adm_pct'])]
        
        if outros_1a > 0:
            valores_pizza.append(outros_1a)
            labels_pizza.append('Outros')
        
        ax1.pie(valores_pizza, labels=labels_pizza, autopct='%1.1f%%', startangle=90)
        ax1.set_title('Distribuição de Custos Admin - 1ª Camada (Top 10)')
    
    # 2. Barras - Cobertura de taxas
    ax2 = axes[0, 1]
    valor_com_taxa_1a = df_primeira_camada['valor_investido'].sum() if not df_primeira_camada.empty else 0
    valor_sem_taxa_1a = df_sem_taxa_1a['valor'].sum() if not df_sem_taxa_1a.empty else 0
    valor_com_taxa_2a = df_segunda_camada['valor_efetivo_chimborazo'].sum() if not df_segunda_camada.empty else 0
    valor_sem_taxa_2a = df_sem_taxa_2a['valor_efetivo'].sum() if not df_sem_taxa_2a.empty else 0
    
    dados_cobertura = pd.DataFrame({
        'Com Taxa': [valor_com_taxa_1a/1e6, valor_com_taxa_2a/1e6],
        'Sem Taxa': [valor_sem_taxa_1a/1e6, valor_sem_taxa_2a/1e6]
    }, index=['1ª Camada', '2ª Camada'])
    
    dados_cobertura.plot(kind='bar', ax=ax2, stacked=True)
    ax2.set_ylabel('Valor (R$ milhões)')
    ax2.set_title('Cobertura de Identificação de Taxas')
    ax2.legend()
    
    # 3. Scatter - Taxa vs Valor (1ª camada)
    ax3 = axes[1, 0]
    if not df_primeira_camada.empty:
        ax3.scatter(df_primeira_camada['valor_investido'] / 1e6, 
                    df_primeira_camada['taxa_adm_pct'],
                    s=100, alpha=0.6)
        
        # Adicionar labels para os maiores
        top5 = df_primeira_camada.nlargest(5, 'valor_investido')
        for _, fundo in top5.iterrows():
            ax3.annotate(fundo['nome'][:15], 
                        (fundo['valor_investido']/1e6, fundo['taxa_adm_pct']),
                        fontsize=8, alpha=0.7)
        
        ax3.set_xlabel('Valor Investido (R$ milhões)')
        ax3.set_ylabel('Taxa de Administração (%)')
        ax3.set_title('Relação Valor vs Taxa Admin - 1ª Camada')
        ax3.grid(True, alpha=0.3)
    
    # 4. Histograma - Distribuição de taxas
    ax4 = axes[1, 1]
    todas_taxas = []
    if not df_primeira_camada.empty:
        todas_taxas.extend(df_primeira_camada['taxa_adm_pct'].tolist())
    if not df_segunda_camada.empty:
        todas_taxas.extend(df_segunda_camada['taxa_adm_pct'].tolist())
    
    if todas_taxas:
        ax4.hist(todas_taxas, bins=30, alpha=0.7, color='blue', edgecolor='black')
        ax4.axvline(np.mean(todas_taxas), color='red', linestyle='--', 
                   label=f'Média: {np.mean(todas_taxas):.2f}%')
        ax4.set_xlabel('Taxa de Administração (%)')
        ax4.set_ylabel('Frequência')
        ax4.set_title('Distribuição de Taxas de Administração')
        ax4.legend()
    
    plt.tight_layout()
    caminho_grafico = os.path.join(base_dir, 'analise_taxas_admin_graficos.png')
    plt.savefig(caminho_grafico, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Gráficos salvos em: {caminho_grafico}")

def main():
    """
    Função principal para executar a análise
    """
    # Configurações
    CNPJ_CHIMBORAZO = '54.195.596/0001-51'
    NOME_CHIMBORAZO = 'chimborazo'
    BASE_DIR = r"C:\Users\guilh\Documents\GitHub\sherpa\database"
    
    print("Iniciando análise de taxas de administração - Fundo Chimborazo")
    print("="*80)
    
    # 1. Carregar dados cadastrais dos fundos
    print("\n1. Carregando dados cadastrais dos fundos...")
    df_cadastro = carregar_dados_cadastrais_fundos(BASE_DIR)
    
    # 2. Carregar carteira do Chimborazo
    print("\n2. Carregando carteira do Chimborazo...")
    try:
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
                limite_arquivos=1
            )
            data_mais_recente = max(carteiras.keys())
            df_carteira_chimborazo = carteiras[data_mais_recente]
    except Exception as e:
        print(f"Erro ao carregar carteira: {e}")
        return
    
    # 3. Calcular valor total da carteira
    valor_total_carteira = df_carteira_chimborazo['VL_MERC_POS_FINAL'].sum()
    print(f"\nValor total da carteira: R$ {valor_total_carteira:,.2f}")
    
    # 4. Identificar fundos na carteira (1ª camada)
    print("\n3. Identificando fundos na carteira (1ª camada)...")
    df_fundos_nivel1 = identificar_fundos_na_carteira(df_carteira_chimborazo)
    print(f"Encontrados {len(df_fundos_nivel1)} fundos na carteira")
    
    # 5. Calcular custos da 1ª camada
    print("\n4. Calculando taxas de administração da 1ª camada...")
    df_custos_1a_camada, df_sem_taxa_1a = calcular_custos_primeira_camada(
        df_fundos_nivel1, 
        df_cadastro,
        valor_total_carteira
    )
    
    # 6. Processar 2ª camada
    print("\n5. Processando 2ª camada (fundos dentro dos fundos)...")
    df_custos_2a_camada, df_sem_taxa_2a = processar_segunda_camada_otimizada(
        df_custos_1a_camada,
        BASE_DIR,
        df_cadastro
    )
    
    # 7. Gerar relatório
    print("\n6. Gerando relatório consolidado...")
    resultados = gerar_relatorio_taxas_admin(
        df_custos_1a_camada,
        df_custos_2a_camada,
        df_sem_taxa_1a,
        df_sem_taxa_2a,
        valor_total_carteira,
        BASE_DIR
    )
    
    # 8. Gerar visualizações
    print("\n7. Gerando visualizações...")
    plotar_analise_taxas_admin(
        df_custos_1a_camada, 
        df_custos_2a_camada,
        df_sem_taxa_1a,
        df_sem_taxa_2a,
        valor_total_carteira, 
        BASE_DIR
    )
    
    print("\nAnálise concluída!")
    
    return resultados

if __name__ == "__main__":
    resultados = main()