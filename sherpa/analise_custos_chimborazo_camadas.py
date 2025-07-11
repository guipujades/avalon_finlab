import os
import pandas as pd
import numpy as np
from datetime import datetime
import pickle
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Importar funções necessárias dos módulos existentes
from carteiras_analysis_utils import (
    carregar_carteira_serializada,
    processar_carteira_completa
)

def carregar_dados_cadastrais_fundos(base_dir):
    """
    Carrega dados cadastrais dos fundos para obter taxas de administração e performance
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
        
        # Carregar arquivo de taxas de performance
        caminho_taxa_perf = os.path.join(base_dir, 'CAD', 'cad_fi_hist_taxa_perfm.csv')
        df_taxa_perf = pd.read_csv(caminho_taxa_perf, encoding='latin-1', delimiter=';', low_memory=False)
        print(f"Taxas de performance carregadas: {len(df_taxa_perf)} registros")
        
        # Pegar as taxas mais recentes para cada fundo
        # Taxa de administração
        if 'DT_REG' in df_taxa_adm.columns:
            df_taxa_adm['DT_REG'] = pd.to_datetime(df_taxa_adm['DT_REG'])
            df_taxa_adm_recente = df_taxa_adm.sort_values('DT_REG').groupby('CNPJ_FUNDO').last().reset_index()
        else:
            df_taxa_adm_recente = df_taxa_adm.groupby('CNPJ_FUNDO').last().reset_index()
        
        # Taxa de performance
        if 'DT_REG' in df_taxa_perf.columns:
            df_taxa_perf['DT_REG'] = pd.to_datetime(df_taxa_perf['DT_REG'])
            df_taxa_perf_recente = df_taxa_perf.sort_values('DT_REG').groupby('CNPJ_FUNDO').last().reset_index()
        else:
            df_taxa_perf_recente = df_taxa_perf.groupby('CNPJ_FUNDO').last().reset_index()
        
        # Merge dos dados
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
    
    # Se não encontrou pela categoria, tentar outros métodos
    if len(fundos) == 0:
        # Verificar se existe coluna que identifica fundos
        if 'NM_FUNDO_CLASSE_SUBCLASSE_COTA' in df_carteira.columns:
            df_fundos = df_carteira[df_carteira['NM_FUNDO_CLASSE_SUBCLASSE_COTA'].notna()].copy()
            print(f"Fundos encontrados por NM_FUNDO_CLASSE: {len(df_fundos)}")
            
            # Agrupar por CNPJ do fundo investido
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
        
        # Verificar também por tipo de aplicação
        elif 'TP_APLIC' in df_carteira.columns:
            df_fundos = df_carteira[df_carteira['TP_APLIC'].str.contains('Cotas de Fundos', case=False, na=False)].copy()
            print(f"Fundos encontrados por TP_APLIC: {len(df_fundos)}")
            
            if 'CD_ISIN' in df_fundos.columns:
                fundos_agrupados = df_fundos.groupby(['CD_ISIN', 'DS_ATIVO']).agg({
                    'VL_MERC_POS_FINAL': 'sum'
                }).reset_index()
                
                for _, row in fundos_agrupados.iterrows():
                    fundos.append({
                        'identificador': row['CD_ISIN'],
                        'nome': row['DS_ATIVO'],
                        'valor': row['VL_MERC_POS_FINAL']
                    })
    
    # Agrupar fundos duplicados
    if len(fundos) > 0:
        df_fundos = pd.DataFrame(fundos)
        
        # Se tem CNPJ, agrupar por CNPJ
        if 'cnpj' in df_fundos.columns:
            fundos_com_cnpj = df_fundos[df_fundos['cnpj'].notna()]
            fundos_sem_cnpj = df_fundos[df_fundos['cnpj'].isna()]
            
            if not fundos_com_cnpj.empty:
                fundos_com_cnpj = fundos_com_cnpj.groupby('cnpj').agg({
                    'nome': 'first',
                    'valor': 'sum'
                }).reset_index()
            
            # Concatenar de volta
            df_fundos = pd.concat([fundos_com_cnpj, fundos_sem_cnpj], ignore_index=True)
        
        return df_fundos
    
    return pd.DataFrame(fundos)

def carregar_taxas_manuais():
    """
    Carrega taxas manuais para fundos que não estão no cadastro CVM
    Baseado em dados de mercado e informações públicas
    """
    taxas_manuais = {
        # Private Equity - geralmente 2% adm + 20% performance
        '41.535.122/0001-60': {'nome': 'KINEA PRIVATE EQUITY V', 'taxa_adm': 0.02, 'taxa_perf': 0.20},
        '32.311.914/0001-60': {'nome': 'VINCI CAPITAL PARTNERS III', 'taxa_adm': 0.02, 'taxa_perf': 0.20},
        
        # FIDC - geralmente 1-2% adm
        '12.138.862/0001-64': {'nome': 'SILVERADO MAXIMUM II', 'taxa_adm': 0.015, 'taxa_perf': 0},
        
        # Fundos conhecidos
        '56.430.872/0001-44': {'nome': 'ALPAMAYO', 'taxa_adm': 0.015, 'taxa_perf': 0.20},
        '07.096.546/0001-37': {'nome': 'ITAÚ VÉRTICE RF DI', 'taxa_adm': 0.003, 'taxa_perf': 0},
        '55.419.784/0001-89': {'nome': 'ITAÚ CAIXA AÇÕES', 'taxa_adm': 0.02, 'taxa_perf': 0},
        '24.546.223/0001-17': {'nome': 'ITAÚ VÉRTICE COMPROMISSO RF DI', 'taxa_adm': 0.003, 'taxa_perf': 0},
        '41.287.689/0001-64': {'nome': 'ITAÚ DOLOMITAS', 'taxa_adm': 0.01, 'taxa_perf': 0},
        '14.096.710/0001-71': {'nome': 'ITAÚ VÉRTICE IBOVESPA', 'taxa_adm': 0.01, 'taxa_perf': 0},
        '12.809.201/0001-13': {'nome': 'CAPSTONE MACRO A', 'taxa_adm': 0.02, 'taxa_perf': 0.20},
    }
    
    return taxas_manuais

def obter_taxas_fundo(cnpj_fundo, df_cadastro):
    """
    Obtém as taxas de administração e performance de um fundo
    Primeiro tenta no cadastro CVM, depois nas taxas manuais
    """
    # Primeiro tentar taxas manuais (mais confiável para fundos específicos)
    taxas_manuais = carregar_taxas_manuais()
    if cnpj_fundo in taxas_manuais:
        taxas = taxas_manuais[cnpj_fundo]
        print(f"Usando taxas manuais para {taxas['nome']}: Adm {taxas['taxa_adm']*100:.2f}%, Perf {taxas['taxa_perf']*100:.1f}%")
        return {'taxa_adm': taxas['taxa_adm'], 'taxa_perf': taxas['taxa_perf']}
    
    # Se não encontrou nas manuais, tentar no cadastro CVM
    if df_cadastro is None:
        return {'taxa_adm': 0, 'taxa_perf': 0}
    
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
                taxa_perf = 0
                
                # Obter taxa de administração
                if 'TAXA_ADM' in fundo.columns:
                    val = fundo['TAXA_ADM'].iloc[0]
                    if pd.notna(val):
                        if isinstance(val, str):
                            taxa_adm = float(val.replace(',', '.'))
                        else:
                            taxa_adm = float(val)
                
                # Obter taxa de performance
                if 'VL_TAXA_PERFM' in fundo.columns:
                    val = fundo['VL_TAXA_PERFM'].iloc[0]
                    if pd.notna(val):
                        if isinstance(val, str):
                            taxa_perf = float(val.replace(',', '.'))
                        else:
                            taxa_perf = float(val)
                
                print(f"Taxas do cadastro CVM para {cnpj_fundo}: Adm {taxa_adm:.2f}%, Perf {taxa_perf:.1f}%")
                # As taxas já vêm em percentual, então dividimos por 100
                return {'taxa_adm': taxa_adm / 100, 'taxa_perf': taxa_perf / 100}
        
    except Exception as e:
        print(f"Erro ao obter taxas do fundo {cnpj_fundo}: {e}")
    
    print(f"Fundo {cnpj_fundo} não encontrado - será necessário adicionar manualmente")
    # Retorna zero para fundos não encontrados - usuário adicionará manualmente
    return {'taxa_adm': 0, 'taxa_perf': 0}

def calcular_custos_primeira_camada(df_fundos, df_cadastro, valor_total_carteira):
    """
    Calcula os custos da primeira camada (fundos diretos na carteira)
    """
    resultados = []
    
    for _, fundo in df_fundos.iterrows():
        cnpj = fundo.get('cnpj', fundo.get('identificador', 'N/A'))
        nome = fundo['nome']
        valor = fundo['valor']
        peso = valor / valor_total_carteira
        
        # Obter taxas
        taxas = obter_taxas_fundo(cnpj, df_cadastro)
        
        # Calcular custos
        custo_adm_anual = valor * taxas['taxa_adm']
        custo_perf_anual = valor * taxas['taxa_perf']
        custo_total_anual = custo_adm_anual + custo_perf_anual
        
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
            'custo_total_pct': (custo_total_anual / valor * 100) if valor > 0 else 0
        })
    
    return pd.DataFrame(resultados)

def processar_segunda_camada(df_primeira_camada, base_dir, df_cadastro):
    """
    Processa a segunda camada - fundos dentro dos fundos
    """
    resultados_segunda_camada = []
    
    for _, fundo_nivel1 in df_primeira_camada.iterrows():
        cnpj_fundo = fundo_nivel1['cnpj']
        valor_fundo_nivel1 = fundo_nivel1['valor_investido']
        
        print(f"\nProcessando 2ª camada do fundo: {fundo_nivel1['nome']}")
        
        try:
            # Tentar carregar a carteira deste fundo
            carteira_fundo = processar_carteira_completa(
                cnpj_fundo=cnpj_fundo,
                base_dir=base_dir,
                limite_arquivos=1  # Apenas o mais recente
            )
            
            if carteira_fundo and len(carteira_fundo) > 0:
                # Pegar a carteira mais recente
                data_mais_recente = max(carteira_fundo.keys())
                df_carteira_nivel2 = carteira_fundo[data_mais_recente]
                
                # Identificar fundos nesta carteira
                fundos_nivel2 = identificar_fundos_na_carteira(df_carteira_nivel2)
                
                if not fundos_nivel2.empty:
                    valor_total_nivel2 = df_carteira_nivel2['VL_MERC_POS_FINAL'].sum()
                    
                    for _, fundo_n2 in fundos_nivel2.iterrows():
                        cnpj_n2 = fundo_n2.get('cnpj', fundo_n2.get('identificador', 'N/A'))
                        valor_n2 = fundo_n2['valor']
                        peso_n2_no_n1 = valor_n2 / valor_total_nivel2 if valor_total_nivel2 > 0 else 0
                        
                        # Valor efetivo na carteira do Chimborazo
                        valor_efetivo = valor_fundo_nivel1 * peso_n2_no_n1
                        
                        # Obter taxas
                        taxas = obter_taxas_fundo(cnpj_n2, df_cadastro)
                        
                        # Calcular custos
                        custo_adm_anual = valor_efetivo * taxas['taxa_adm']
                        custo_perf_anual = valor_efetivo * taxas['taxa_perf']
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
                            'custo_total_pct': (custo_total_anual / valor_efetivo * 100) if valor_efetivo > 0 else 0
                        })
                        
        except Exception as e:
            print(f"Erro ao processar 2ª camada do fundo {cnpj_fundo}: {e}")
            
    return pd.DataFrame(resultados_segunda_camada)

def gerar_relatorio_custos(df_primeira_camada, df_segunda_camada, valor_total_carteira, base_dir):
    """
    Gera relatório consolidado dos custos
    """
    print("\n" + "="*80)
    print("RELATÓRIO DE CUSTOS - FUNDO CHIMBORAZO")
    print("="*80)
    
    # Resumo 1ª Camada
    print("\n1ª CAMADA - FUNDOS DIRETOS NA CARTEIRA:")
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
    
    # Resumo Total
    print("\n\nRESUMO TOTAL:")
    print("="*60)
    custo_total_geral = custo_total_1a + (custo_total_2a if not df_segunda_camada.empty else 0)
    print(f"Custo total anual (1ª + 2ª camadas): R$ {custo_total_geral:,.2f}")
    print(f"Custo total % sobre patrimônio: {(custo_total_geral / valor_total_carteira * 100):.4f}%")
    print(f"Custo mensal estimado: R$ {custo_total_geral / 12:,.2f}")
    
    # Salvar resultados em Excel
    caminho_saida = os.path.join(base_dir, 'analise_custos_chimborazo.xlsx')
    with pd.ExcelWriter(caminho_saida, engine='openpyxl') as writer:
        df_primeira_camada.to_excel(writer, sheet_name='1a_Camada', index=False)
        if not df_segunda_camada.empty:
            df_segunda_camada.to_excel(writer, sheet_name='2a_Camada', index=False)
        
        # Criar resumo
        resumo = pd.DataFrame([
            {'Métrica': 'Valor Total Carteira', 'Valor': valor_total_carteira},
            {'Métrica': 'Custo Total 1ª Camada', 'Valor': custo_total_1a},
            {'Métrica': 'Custo Total 2ª Camada', 'Valor': custo_total_2a if not df_segunda_camada.empty else 0},
            {'Métrica': 'Custo Total Geral', 'Valor': custo_total_geral},
            {'Métrica': 'Custo % sobre Patrimônio', 'Valor': (custo_total_geral / valor_total_carteira * 100)}
        ])
        resumo.to_excel(writer, sheet_name='Resumo', index=False)
    
    print(f"\nRelatório salvo em: {caminho_saida}")
    
    return {
        'primeira_camada': df_primeira_camada,
        'segunda_camada': df_segunda_camada,
        'custo_total': custo_total_geral,
        'custo_percentual': (custo_total_geral / valor_total_carteira * 100)
    }

def plotar_analise_custos(df_primeira_camada, df_segunda_camada, base_dir):
    """
    Cria visualizações da análise de custos
    """
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Análise de Custos - Fundo Chimborazo', fontsize=16)
    
    # 1. Pizza - Distribuição de custos 1ª camada
    ax1 = axes[0, 0]
    top10_1a = df_primeira_camada.nlargest(10, 'custo_total_anual')
    outros_1a = df_primeira_camada[~df_primeira_camada.index.isin(top10_1a.index)]['custo_total_anual'].sum()
    
    valores_pizza = top10_1a['custo_total_anual'].tolist()
    labels_pizza = [nome[:30] + '...' if len(nome) > 30 else nome for nome in top10_1a['nome'].tolist()]
    
    if outros_1a > 0:
        valores_pizza.append(outros_1a)
        labels_pizza.append('Outros')
    
    ax1.pie(valores_pizza, labels=labels_pizza, autopct='%1.1f%%', startangle=90)
    ax1.set_title('Distribuição de Custos - 1ª Camada (Top 10)')
    
    # 2. Barras - Comparação taxas médias
    ax2 = axes[0, 1]
    if not df_segunda_camada.empty:
        dados_barras = pd.DataFrame({
            '1ª Camada': [df_primeira_camada['taxa_adm'].mean() * 100, 
                          df_primeira_camada['taxa_perf'].mean() * 100],
            '2ª Camada': [df_segunda_camada['taxa_adm'].mean() * 100,
                          df_segunda_camada['taxa_perf'].mean() * 100]
        }, index=['Taxa Admin', 'Taxa Performance'])
        
        dados_barras.plot(kind='bar', ax=ax2)
        ax2.set_ylabel('Taxa (%)')
        ax2.set_title('Comparação de Taxas Médias por Camada')
        ax2.legend()
    
    # 3. Scatter - Relação Valor x Custo
    ax3 = axes[1, 0]
    ax3.scatter(df_primeira_camada['valor_investido'] / 1e6, 
                df_primeira_camada['custo_total_anual'] / 1e3,
                alpha=0.6, s=100)
    ax3.set_xlabel('Valor Investido (R$ milhões)')
    ax3.set_ylabel('Custo Anual (R$ mil)')
    ax3.set_title('Relação Valor Investido x Custo - 1ª Camada')
    ax3.grid(True, alpha=0.3)
    
    # 4. Histograma - Distribuição de taxas totais
    ax4 = axes[1, 1]
    taxa_total_1a = (df_primeira_camada['taxa_adm'] + df_primeira_camada['taxa_perf']) * 100
    ax4.hist(taxa_total_1a, bins=20, alpha=0.7, color='blue', label='1ª Camada')
    
    if not df_segunda_camada.empty:
        taxa_total_2a = (df_segunda_camada['taxa_adm'] + df_segunda_camada['taxa_perf']) * 100
        ax4.hist(taxa_total_2a, bins=20, alpha=0.7, color='red', label='2ª Camada')
    
    ax4.set_xlabel('Taxa Total (%)')
    ax4.set_ylabel('Frequência')
    ax4.set_title('Distribuição de Taxas Totais')
    ax4.legend()
    
    plt.tight_layout()
    caminho_grafico = os.path.join(base_dir, 'analise_custos_chimborazo_graficos.png')
    plt.savefig(caminho_grafico, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Gráficos salvos em: {caminho_grafico}")

def main():
    """
    Função principal para executar a análise
    """
    # Configurações
    CNPJ_CHIMBORAZO = '54.195.596/0001-51'
    NOME_CHIMBORAZO = 'chimborazo'
    BASE_DIR = r"C:\Users\guilh\Documents\GitHub\flab\database"
    
    print("Iniciando análise de custos em duas camadas - Fundo Chimborazo")
    print("="*80)
    
    # 1. Carregar dados cadastrais dos fundos
    print("\n1. Carregando dados cadastrais dos fundos...")
    df_cadastro = carregar_dados_cadastrais_fundos(BASE_DIR)
    
    # 2. Carregar carteira do Chimborazo
    print("\n2. Carregando carteira do Chimborazo...")
    try:
        # Tentar primeiro carregar dados serializados
        dados_chimborazo = carregar_carteira_serializada(BASE_DIR, NOME_CHIMBORAZO)
        if dados_chimborazo and 'carteira_categorizada' in dados_chimborazo:
            carteiras = dados_chimborazo['carteira_categorizada']
            # Pegar a data mais recente
            data_mais_recente = max(carteiras.keys())
            df_carteira_chimborazo = carteiras[data_mais_recente]
            print(f"Carteira carregada para data: {data_mais_recente}")
        else:
            # Se não houver dados serializados, processar
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
    print("\n4. Calculando custos da 1ª camada...")
    df_custos_1a_camada = calcular_custos_primeira_camada(
        df_fundos_nivel1, 
        df_cadastro,
        valor_total_carteira
    )
    
    # 6. Processar 2ª camada
    print("\n5. Processando 2ª camada (fundos dentro dos fundos)...")
    df_custos_2a_camada = processar_segunda_camada(
        df_custos_1a_camada,
        BASE_DIR,
        df_cadastro
    )
    
    # 7. Gerar relatório
    print("\n6. Gerando relatório consolidado...")
    resultados = gerar_relatorio_custos(
        df_custos_1a_camada,
        df_custos_2a_camada,
        valor_total_carteira,
        BASE_DIR
    )
    
    # 8. Gerar visualizações
    print("\n7. Gerando visualizações...")
    plotar_analise_custos(df_custos_1a_camada, df_custos_2a_camada, BASE_DIR)
    
    print("\nAnálise concluída!")
    
    return resultados

if __name__ == "__main__":
    resultados = main()