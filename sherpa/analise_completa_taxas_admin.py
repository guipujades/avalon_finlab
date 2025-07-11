import os
import pandas as pd
import numpy as np
import pickle
from datetime import datetime
import matplotlib.pyplot as plt

# Configurações
BASE_DIR = "/mnt/c/Users/guilh/Documents/GitHub/sherpa/database"
CNPJ_CHIMBORAZO = '54.195.596/0001-51'
NOME_CHIMBORAZO = 'chimborazo'

print("ANÁLISE COMPLETA DE TAXAS DE ADMINISTRAÇÃO - FUNDO CHIMBORAZO")
print("="*80)

# 1. Carregar dados do Chimborazo
print("\n1. Carregando carteira do Chimborazo...")
serial_path = os.path.join(BASE_DIR, 'serial_carteiras', 'carteira_chimborazo.pkl')

try:
    with open(serial_path, 'rb') as f:
        dados = pickle.load(f)
    
    if 'carteira_categorizada' in dados:
        carteiras = dados['carteira_categorizada']
        data_mais_recente = max(carteiras.keys())
        df_carteira = carteiras[data_mais_recente]
        print(f"✓ Carteira carregada para: {data_mais_recente}")
        print(f"  Total de posições: {len(df_carteira)}")
        print(f"  Valor total: R$ {df_carteira['VL_MERC_POS_FINAL'].sum():,.2f}")
    else:
        print("✗ Erro: Estrutura de dados não reconhecida")
        exit(1)
        
except Exception as e:
    print(f"✗ Erro ao carregar carteira: {e}")
    exit(1)

# 2. Identificar fundos na carteira
print("\n2. Identificando fundos na carteira...")
if 'CATEGORIA_ATIVO' in df_carteira.columns:
    df_fundos = df_carteira[df_carteira['CATEGORIA_ATIVO'] == 'Fundos'].copy()
    print(f"✓ Fundos encontrados: {len(df_fundos)}")
    
    # Agrupar por CNPJ
    fundos_agrupados = df_fundos.groupby('CNPJ_FUNDO_CLASSE_COTA').agg({
        'VL_MERC_POS_FINAL': 'sum',
        'NM_FUNDO_CLASSE_SUBCLASSE_COTA': 'first'
    }).reset_index()
    
    print(f"✓ Fundos únicos: {len(fundos_agrupados)}")
else:
    print("✗ Coluna CATEGORIA_ATIVO não encontrada")
    exit(1)

# 3. Carregar dados de taxas do histórico
print("\n3. Carregando taxas de administração...")
arquivo_hist = os.path.join(BASE_DIR, 'CAD', 'cad_fi_hist_taxa_adm.csv')

try:
    df_hist = pd.read_csv(arquivo_hist, 
                          encoding='latin-1', 
                          delimiter=';',
                          dtype={'CNPJ_FUNDO': str})
    
    # Converter data e pegar taxa mais recente
    if 'DT_REG' in df_hist.columns:
        df_hist['DT_REG'] = pd.to_datetime(df_hist['DT_REG'], errors='coerce')
        df_hist_recente = df_hist.sort_values('DT_REG').groupby('CNPJ_FUNDO').last()
    else:
        df_hist_recente = df_hist.groupby('CNPJ_FUNDO').last()
    
    print(f"✓ Histórico carregado: {len(df_hist_recente)} fundos com taxa")
    
except Exception as e:
    print(f"✗ Erro ao carregar histórico: {e}")
    df_hist_recente = pd.DataFrame()

# 4. Taxas manuais conhecidas
taxas_manuais = {
    '41.535.122/0001-60': {'nome': 'KINEA PRIVATE EQUITY V', 'taxa': 2.0},
    '32.311.914/0001-60': {'nome': 'VINCI CAPITAL PARTNERS III', 'taxa': 2.0},
    '12.138.862/0001-64': {'nome': 'SILVERADO MAXIMUM II', 'taxa': 1.5},
    '56.430.872/0001-44': {'nome': 'ALPAMAYO', 'taxa': 1.5},
    '55.419.784/0001-89': {'nome': 'ITAÚ DOLOMITAS', 'taxa': 2.0},
}

# 5. Analisar cada fundo
print("\n4. Analisando taxas de administração...")
print("-"*80)

resultados = []
total_sem_taxa = 0
valor_sem_taxa = 0

for _, fundo in fundos_agrupados.iterrows():
    cnpj = fundo['CNPJ_FUNDO_CLASSE_COTA']
    nome = fundo['NM_FUNDO_CLASSE_SUBCLASSE_COTA']
    valor = fundo['VL_MERC_POS_FINAL']
    
    taxa_adm = None
    fonte = None
    
    # Buscar no histórico CVM
    if cnpj in df_hist_recente.index:
        taxa_str = df_hist_recente.loc[cnpj, 'TAXA_ADM']
        try:
            if isinstance(taxa_str, str):
                taxa_adm = float(taxa_str.replace(',', '.'))
            else:
                taxa_adm = float(taxa_str) if not pd.isna(taxa_str) else None
            fonte = 'CVM'
        except:
            pass
    
    # Se não encontrou, buscar nas taxas manuais
    if taxa_adm is None and cnpj in taxas_manuais:
        taxa_adm = taxas_manuais[cnpj]['taxa']
        fonte = 'Manual'
    
    # Calcular custo
    if taxa_adm is not None:
        custo_anual = valor * (taxa_adm / 100)
        print(f"\n✓ {nome[:50]:50}")
        print(f"  CNPJ: {cnpj} | Valor: R$ {valor:,.2f}")
        print(f"  Taxa: {taxa_adm:.2f}% ({fonte}) | Custo anual: R$ {custo_anual:,.2f}")
        
        resultados.append({
            'CNPJ': cnpj,
            'Nome': nome,
            'Valor': valor,
            'Taxa_Adm': taxa_adm,
            'Fonte': fonte,
            'Custo_Anual': custo_anual
        })
    else:
        print(f"\n✗ {nome[:50]:50}")
        print(f"  CNPJ: {cnpj} | Valor: R$ {valor:,.2f}")
        print(f"  Taxa: NÃO ENCONTRADA")
        total_sem_taxa += 1
        valor_sem_taxa += valor

# 6. Resumo
print("\n" + "="*80)
print("RESUMO DA ANÁLISE:")
print("="*80)

valor_total_carteira = df_carteira['VL_MERC_POS_FINAL'].sum()
valor_total_fundos = fundos_agrupados['VL_MERC_POS_FINAL'].sum()

print(f"\nCarteira Total: R$ {valor_total_carteira:,.2f}")
print(f"Valor em Fundos: R$ {valor_total_fundos:,.2f} ({valor_total_fundos/valor_total_carteira*100:.1f}%)")

if resultados:
    df_resultados = pd.DataFrame(resultados)
    custo_total = df_resultados['Custo_Anual'].sum()
    taxa_media = (df_resultados['Taxa_Adm'] * df_resultados['Valor']).sum() / df_resultados['Valor'].sum()
    
    print(f"\nFundos com taxa identificada: {len(df_resultados)}")
    print(f"Valor com taxa: R$ {df_resultados['Valor'].sum():,.2f}")
    print(f"Taxa média ponderada: {taxa_media:.3f}%")
    print(f"Custo total anual: R$ {custo_total:,.2f}")
    print(f"Custo sobre patrimônio total: {custo_total/valor_total_carteira*100:.3f}%")
    
    print(f"\nFundos sem taxa: {total_sem_taxa}")
    print(f"Valor sem taxa: R$ {valor_sem_taxa:,.2f} ({valor_sem_taxa/valor_total_fundos*100:.1f}% dos fundos)")
    
    # Top 5 por custo
    print("\nTop 5 fundos por custo anual:")
    top5 = df_resultados.nlargest(5, 'Custo_Anual')
    for _, f in top5.iterrows():
        print(f"  {f['Nome'][:40]:40} | Taxa: {f['Taxa_Adm']:>5.2f}% | Custo: R$ {f['Custo_Anual']:>12,.2f}")
    
    # Salvar resultados
    arquivo_saida = os.path.join(BASE_DIR, 'analise_completa_taxas_admin.xlsx')
    with pd.ExcelWriter(arquivo_saida, engine='openpyxl') as writer:
        df_resultados.to_excel(writer, sheet_name='Fundos_Com_Taxa', index=False)
        
        # Resumo
        resumo = pd.DataFrame({
            'Métrica': ['Valor Total Carteira', 'Valor em Fundos', '% em Fundos', 
                       'Fundos com Taxa', 'Valor com Taxa', 'Taxa Média Ponderada',
                       'Custo Total Anual', 'Custo % Patrimônio', 'Fundos sem Taxa',
                       'Valor sem Taxa'],
            'Valor': [valor_total_carteira, valor_total_fundos, valor_total_fundos/valor_total_carteira*100,
                     len(df_resultados), df_resultados['Valor'].sum(), taxa_media,
                     custo_total, custo_total/valor_total_carteira*100, total_sem_taxa,
                     valor_sem_taxa]
        })
        resumo.to_excel(writer, sheet_name='Resumo', index=False)
    
    print(f"\n✓ Análise salva em: {arquivo_saida}")
    
    # Criar gráfico simples
    plt.figure(figsize=(10, 6))
    plt.bar(range(len(df_resultados)), df_resultados['Taxa_Adm'])
    plt.xlabel('Fundos')
    plt.ylabel('Taxa de Administração (%)')
    plt.title('Taxas de Administração - Fundos Chimborazo')
    plt.xticks(range(len(df_resultados)), [f"{i+1}" for i in range(len(df_resultados))], rotation=0)
    plt.grid(axis='y', alpha=0.3)
    
    grafico_path = os.path.join(BASE_DIR, 'taxas_admin_chimborazo.png')
    plt.savefig(grafico_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✓ Gráfico salvo em: {grafico_path}")

else:
    print("\n✗ Nenhum fundo com taxa identificada!")

print("\nAnálise concluída!")