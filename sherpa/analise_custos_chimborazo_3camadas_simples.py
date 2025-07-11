import os
import pandas as pd
import numpy as np
from datetime import datetime
import pickle
import matplotlib.pyplot as plt
from pathlib import Path

from carteiras_analysis_utils import processar_carteira_completa

def carregar_taxas_manuais():
    """
    Carrega taxas de administração manuais - APENAS TAXA ADMIN ANUAL
    """
    taxas_manuais = {
        # Fundos com taxas confirmadas
        '56.430.872/0001-44': {'nome': 'ALPAMAYO', 'taxa_adm': 0.0004},  # 0.04%
        '12.809.201/0001-13': {'nome': 'CAPSTONE MACRO A', 'taxa_adm': 0.019},  # 1.90%
        
        # Private Equity - Taxa 0% na camada 1
        '32.311.914/0001-60': {'nome': 'VINCI CAPITAL PARTNERS III', 'taxa_adm': 0.0},
        '41.535.122/0001-60': {'nome': 'KINEA PRIVATE EQUITY V', 'taxa_adm': 0.0},
        
        # Fundos Itaú
        '41.287.689/0001-64': {'nome': 'ITAÚ DOLOMITAS', 'taxa_adm': 0.0006},  # 0.06%
        '14.096.710/0001-71': {'nome': 'ITAÚ VÉRTICE IBOVESPA', 'taxa_adm': 0.0},
        '18.138.913/0001-34': {'nome': 'ITAÚ VÉRTICE COMPROMISSO', 'taxa_adm': 0.0015},  # 0.15%
        '55.419.784/0001-89': {'nome': 'ITAÚ CAIXA AÇÕES', 'taxa_adm': 0.0},
        
        # FIDC
        '12.138.862/0001-64': {'nome': 'SILVERADO MAXIMUM II', 'taxa_adm': 0.0},
        
        # Outros
        '21.407.105/0001-30': {'nome': 'ITAÚ VÉRTICE RF DI', 'taxa_adm': 0.003},  # 0.30%
    }
    
    return taxas_manuais

def obter_taxa_admin_fundo(cnpj_fundo):
    """
    Obtém apenas a taxa de administração anual do fundo
    """
    taxas_manuais = carregar_taxas_manuais()
    
    if cnpj_fundo in taxas_manuais:
        return taxas_manuais[cnpj_fundo]['taxa_adm']
    
    # Se não encontrou, retorna 0
    print(f"  ⚠ Taxa não encontrada para CNPJ {cnpj_fundo}")
    return 0.0

def calcular_custos_camada_zero(valor_total_carteira):
    """
    Calcula os custos da camada zero - Taxa de administração do Itaú
    """
    TAXA_ADMIN_ITAU_ANUAL = 0.0035  # 0.35% ao ano
    
    custo_anual = valor_total_carteira * TAXA_ADMIN_ITAU_ANUAL
    
    print(f"\nCAMADA 0 - TAXA ITAÚ:")
    print(f"  Patrimônio: R$ {valor_total_carteira:,.2f}")
    print(f"  Taxa: 0.35% a.a.")
    print(f"  Custo anual: R$ {custo_anual:,.2f}")
    
    return {
        'camada': 0,
        'descricao': 'Taxa de Administração Itaú',
        'valor_base': valor_total_carteira,
        'taxa_admin_anual': TAXA_ADMIN_ITAU_ANUAL,
        'custo_admin_anual': custo_anual
    }

def calcular_custos_primeira_camada(df_fundos, valor_total_carteira):
    """
    Calcula os custos da primeira camada - Apenas taxa de administração anual
    """
    print(f"\nCAMADA 1 - FUNDOS DIRETOS:")
    print("-" * 80)
    
    resultados = []
    custo_total_camada = 0
    
    for _, fundo in df_fundos.iterrows():
        cnpj = fundo['cnpj']
        nome = fundo['nome']
        valor = fundo['valor']
        peso = valor / valor_total_carteira
        
        # Obter taxa de administração anual
        taxa_admin = obter_taxa_admin_fundo(cnpj)
        custo_admin_anual = valor * taxa_admin
        
        resultados.append({
            'camada': 1,
            'cnpj': cnpj,
            'nome': nome,
            'valor_investido': valor,
            'peso_carteira': peso,
            'taxa_admin_anual': taxa_admin,
            'custo_admin_anual': custo_admin_anual
        })
        
        custo_total_camada += custo_admin_anual
        
        print(f"  {nome[:50]:50} | Valor: R$ {valor:>15,.2f} | Taxa: {taxa_admin*100:>5.2f}% | Custo: R$ {custo_admin_anual:>12,.2f}")
    
    print(f"\n  TOTAL CAMADA 1: R$ {custo_total_camada:,.2f}")
    
    return pd.DataFrame(resultados)

def processar_fundos_aninhados_simples(df_primeira_camada, base_dir):
    """
    Versão simplificada para processar fundos aninhados
    """
    print(f"\nCAMADA 2 - FUNDOS ANINHADOS:")
    print("-" * 80)
    
    resultados_segunda_camada = []
    
    # Para cada fundo da primeira camada
    for _, fundo_n1 in df_primeira_camada.iterrows():
        if fundo_n1['taxa_admin_anual'] > 0:
            # Se já tem taxa na camada 1, pular camada 2
            continue
            
        cnpj_fundo = fundo_n1['cnpj']
        nome_fundo = fundo_n1['nome']
        valor_fundo_n1 = fundo_n1['valor_investido']
        
        print(f"\n  Analisando: {nome_fundo}")
        
        # Tipos especiais que precisam análise manual
        fundos_especiais = {
            '32.311.914/0001-60': {  # VINCI PE
                'fundos_aninhados': [
                    {'nome': 'Empresas Portfolio', 'peso': 1.0, 'taxa_admin': 0.02}  # 2% típico de PE
                ]
            },
            '41.535.122/0001-60': {  # KINEA PE
                'fundos_aninhados': [
                    {'nome': 'Empresas Portfolio', 'peso': 1.0, 'taxa_admin': 0.02}  # 2% típico de PE
                ]
            },
            '12.138.862/0001-64': {  # SILVERADO FIDC
                'fundos_aninhados': [
                    {'nome': 'Carteira de Crédito', 'peso': 1.0, 'taxa_admin': 0.015}  # 1.5% típico de FIDC
                ]
            }
        }
        
        if cnpj_fundo in fundos_especiais:
            # Usar dados manuais para fundos especiais
            dados = fundos_especiais[cnpj_fundo]
            for fundo_n2 in dados['fundos_aninhados']:
                valor_efetivo = valor_fundo_n1 * fundo_n2['peso']
                custo_anual = valor_efetivo * fundo_n2['taxa_admin']
                
                resultados_segunda_camada.append({
                    'camada': 2,
                    'fundo_nivel1_nome': nome_fundo,
                    'nome': fundo_n2['nome'],
                    'valor_efetivo': valor_efetivo,
                    'peso_no_n1': fundo_n2['peso'],
                    'taxa_admin_anual': fundo_n2['taxa_admin'],
                    'custo_admin_anual': custo_anual,
                    'tipo': 'manual'
                })
                
                print(f"    → {fundo_n2['nome']}: Taxa {fundo_n2['taxa_admin']*100:.2f}% | Custo: R$ {custo_anual:,.2f}")
        else:
            # Tentar buscar carteira real
            try:
                carteiras = processar_carteira_completa(
                    cnpj_fundo=cnpj_fundo,
                    base_dir=base_dir,
                    limite_arquivos=12
                )
                
                if carteiras and len(carteiras) > 0:
                    data_recente = max(carteiras.keys())
                    df_carteira_n2 = carteiras[data_recente]
                    
                    print(f"    ✓ Carteira encontrada em {data_recente}")
                    
                    # Processar fundos aninhados reais
                    # ... código para processar ...
                else:
                    print(f"    ✗ Sem carteira disponível")
                    
            except Exception as e:
                print(f"    ✗ Erro: {e}")
    
    return pd.DataFrame(resultados_segunda_camada)

def main():
    """
    Função principal simplificada
    """
    BASE_DIR = "/mnt/c/Users/guilh/Documents/GitHub/sherpa/database"
    
    print("=== ANÁLISE DE CUSTOS EM 3 CAMADAS - FUNDO CHIMBORAZO ===")
    print("Foco: APENAS TAXA DE ADMINISTRAÇÃO ANUAL\n")
    
    # 1. Carregar carteira do Chimborazo
    print("1. Carregando carteira...")
    caminho_pkl = os.path.join(BASE_DIR, 'serial_carteiras', 'carteira_chimborazo_completa.pkl')
    
    with open(caminho_pkl, 'rb') as f:
        dados = pickle.load(f)
    
    carteiras = dados['carteira_categorizada']
    df_maio = carteiras['2025-05']
    
    # Converter valores
    df_maio['VL_MERC_POS_FINAL'] = pd.to_numeric(
        df_maio['VL_MERC_POS_FINAL'].astype(str).str.replace(',', '.'), 
        errors='coerce'
    )
    
    valor_total = df_maio['VL_MERC_POS_FINAL'].sum()
    print(f"Valor total da carteira: R$ {valor_total:,.2f}")
    
    # 2. Identificar fundos
    fundos_df = df_maio[df_maio['TP_APLIC'] == 'Cotas de Fundos'].copy()
    fundos_agrupados = fundos_df.groupby('CNPJ_FUNDO_CLASSE_COTA').agg({
        'VL_MERC_POS_FINAL': 'sum',
        'NM_FUNDO_CLASSE_SUBCLASSE_COTA': 'first'
    }).reset_index()
    
    fundos_lista = []
    for _, row in fundos_agrupados.iterrows():
        fundos_lista.append({
            'cnpj': row['CNPJ_FUNDO_CLASSE_COTA'],
            'nome': row['NM_FUNDO_CLASSE_SUBCLASSE_COTA'],
            'valor': row['VL_MERC_POS_FINAL']
        })
    
    df_fundos = pd.DataFrame(fundos_lista)
    print(f"Fundos identificados: {len(df_fundos)}")
    
    # 3. Calcular custos por camada
    print("\n" + "="*80)
    
    # Camada 0
    custos_c0 = calcular_custos_camada_zero(valor_total)
    
    # Camada 1
    df_custos_c1 = calcular_custos_primeira_camada(df_fundos, valor_total)
    
    # Camada 2
    df_custos_c2 = processar_fundos_aninhados_simples(df_custos_c1, BASE_DIR)
    
    # 4. Resumo final
    print("\n" + "="*80)
    print("RESUMO FINAL:")
    print("="*80)
    
    custo_c0 = custos_c0['custo_admin_anual']
    custo_c1 = df_custos_c1['custo_admin_anual'].sum()
    custo_c2 = df_custos_c2['custo_admin_anual'].sum() if len(df_custos_c2) > 0 else 0
    custo_total = custo_c0 + custo_c1 + custo_c2
    
    print(f"\nCamada 0 (Taxa Itaú):        R$ {custo_c0:>15,.2f} ({custo_c0/valor_total*100:>6.3f}%)")
    print(f"Camada 1 (Fundos diretos):   R$ {custo_c1:>15,.2f} ({custo_c1/valor_total*100:>6.3f}%)")
    print(f"Camada 2 (Fundos aninhados): R$ {custo_c2:>15,.2f} ({custo_c2/valor_total*100:>6.3f}%)")
    print(f"\nCUSTO TOTAL ANUAL:           R$ {custo_total:>15,.2f} ({custo_total/valor_total*100:>6.3f}%)")
    print(f"CUSTO MENSAL MÉDIO:          R$ {custo_total/12:>15,.2f}")
    
    # 5. Salvar resultados
    print("\nSalvando resultados...")
    
    # Criar DataFrame consolidado
    todos_custos = []
    
    # Camada 0
    todos_custos.append({
        'Camada': 0,
        'Fundo': 'Taxa de Administração Itaú - Chimborazo',
        'CNPJ': 'N/A',
        'Valor Base': valor_total,
        'Taxa Admin (%)': 0.35,
        'Custo Anual': custo_c0
    })
    
    # Camada 1
    for _, row in df_custos_c1.iterrows():
        todos_custos.append({
            'Camada': 1,
            'Fundo': row['nome'],
            'CNPJ': row['cnpj'],
            'Valor Base': row['valor_investido'],
            'Taxa Admin (%)': row['taxa_admin_anual'] * 100,
            'Custo Anual': row['custo_admin_anual']
        })
    
    # Camada 2
    for _, row in df_custos_c2.iterrows():
        todos_custos.append({
            'Camada': 2,
            'Fundo': f"{row['fundo_nivel1_nome']} → {row['nome']}",
            'CNPJ': 'N/A',
            'Valor Base': row['valor_efetivo'],
            'Taxa Admin (%)': row['taxa_admin_anual'] * 100,
            'Custo Anual': row['custo_admin_anual']
        })
    
    df_resultado = pd.DataFrame(todos_custos)
    
    # Salvar Excel
    arquivo_saida = os.path.join(BASE_DIR, 'custos_chimborazo_3camadas.xlsx')
    with pd.ExcelWriter(arquivo_saida) as writer:
        df_resultado.to_excel(writer, sheet_name='Custos_Detalhados', index=False)
        
        # Resumo
        resumo = pd.DataFrame([
            {'Descrição': 'Valor Total Carteira', 'Valor': valor_total},
            {'Descrição': 'Custo Camada 0 (Itaú)', 'Valor': custo_c0},
            {'Descrição': 'Custo Camada 1 (Fundos)', 'Valor': custo_c1},
            {'Descrição': 'Custo Camada 2 (Aninhados)', 'Valor': custo_c2},
            {'Descrição': 'Custo Total Anual', 'Valor': custo_total},
            {'Descrição': 'Taxa Efetiva Total (%)', 'Valor': (custo_total/valor_total*100)}
        ])
        resumo.to_excel(writer, sheet_name='Resumo', index=False)
    
    print(f"✓ Resultados salvos em: {arquivo_saida}")

if __name__ == "__main__":
    main()