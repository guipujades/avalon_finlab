import os
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

# Configurações
BASE_DIR = r"C:\Users\guilh\Documents\GitHub\sherpa\database"
CNPJ_CHIMBORAZO = '54.195.596/0001-51'

print("Analisando taxas de administração usando cad_fi.csv")
print("="*80)

# 1. Carregar arquivo cad_fi.csv
print("\n1. Carregando arquivo cad_fi.csv...")
caminho_cad = os.path.join(BASE_DIR, 'CAD', 'cad_fi.csv')
df_cad = pd.read_csv(caminho_cad, encoding='latin-1', delimiter=';', low_memory=False)
print(f"Total de fundos no cadastro: {len(df_cad)}")

# 2. Filtrar apenas fundos ativos
df_ativos = df_cad[df_cad['SIT'] == 'EM FUNCIONAMENTO NORMAL'].copy()
print(f"Fundos em funcionamento normal: {len(df_ativos)}")

# 3. Analisar colunas de taxas
print("\n2. Analisando colunas de taxas...")
print(f"Colunas relacionadas a taxas: {[col for col in df_cad.columns if 'TAXA' in col]}")

# 4. Converter taxa de administração
df_ativos['TAXA_ADM_NUM'] = pd.to_numeric(df_ativos['TAXA_ADM'].str.replace(',', '.'), errors='coerce')
df_ativos['TAXA_PERFM_NUM'] = pd.to_numeric(df_ativos['TAXA_PERFM'].str.replace(',', '.'), errors='coerce')

# 5. Estatísticas gerais
print("\n3. Estatísticas de taxas de administração:")
print(f"Fundos com taxa informada: {df_ativos['TAXA_ADM_NUM'].notna().sum()}")
print(f"Taxa média: {df_ativos['TAXA_ADM_NUM'].mean():.3f}%")
print(f"Taxa mediana: {df_ativos['TAXA_ADM_NUM'].median():.3f}%")
print(f"Taxa máxima: {df_ativos['TAXA_ADM_NUM'].max():.3f}%")

# 6. Analisar por classe
print("\n4. Taxas médias por classe de fundo:")
taxas_por_classe = df_ativos.groupby('CLASSE')['TAXA_ADM_NUM'].agg(['mean', 'count']).sort_values('mean', ascending=False)
for classe, row in taxas_por_classe.head(10).iterrows():
    if row['count'] > 10:  # Apenas classes com mais de 10 fundos
        print(f"  {classe[:40]:40} | Taxa média: {row['mean']:>6.3f}% | Qtd: {row['count']:>5}")

# 7. Buscar fundos específicos para análise do Chimborazo
print("\n5. Buscando fundos específicos do Chimborazo...")

# Lista de CNPJs conhecidos da carteira
cnpjs_conhecidos = [
    '41.535.122/0001-60',  # KINEA PRIVATE EQUITY V
    '32.311.914/0001-60',  # VINCI CAPITAL PARTNERS III
    '12.138.862/0001-64',  # SILVERADO MAXIMUM II
    '56.430.872/0001-44',  # ALPAMAYO
    '07.096.546/0001-37',  # ITAÚ VÉRTICE RF DI
    '55.419.784/0001-89',  # ITAÚ DOLOMITAS
    '24.546.223/0001-17',  # ITAÚ VÉRTICE IBOVESPA
    '21.407.105/0001-30',  # ITAÚ VÉRTICE RF DI FIF
    '18.138.913/0001-34',  # ITAÚ VÉRTICE COMPROMISSO RF DI
    '36.248.791/0001-10',  # CAPSTONE MACRO A
]

print("\nFundos encontrados no cadastro CVM:")
for cnpj in cnpjs_conhecidos:
    fundo = df_cad[df_cad['CNPJ_FUNDO'] == cnpj]
    if not fundo.empty:
        nome = fundo.iloc[0]['DENOM_SOCIAL']
        taxa_adm = fundo.iloc[0]['TAXA_ADM']
        situacao = fundo.iloc[0]['SIT']
        print(f"\n  CNPJ: {cnpj}")
        print(f"  Nome: {nome[:60]}")
        print(f"  Taxa Admin: {taxa_adm}")
        print(f"  Situação: {situacao}")
    else:
        print(f"\n  CNPJ: {cnpj} - NÃO ENCONTRADO")

# 8. Criar visualização
print("\n6. Criando visualizações...")
fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# Histograma de taxas
ax1 = axes[0, 0]
taxas_validas = df_ativos['TAXA_ADM_NUM'].dropna()
ax1.hist(taxas_validas[taxas_validas <= 5], bins=50, edgecolor='black')
ax1.set_xlabel('Taxa de Administração (%)')
ax1.set_ylabel('Quantidade de Fundos')
ax1.set_title('Distribuição de Taxas de Administração (até 5%)')

# Box plot por tipo de fundo
ax2 = axes[0, 1]
tipos_principais = df_ativos['TP_FUNDO'].value_counts().head(5).index
df_tipos = df_ativos[df_ativos['TP_FUNDO'].isin(tipos_principais)]
df_tipos.boxplot(column='TAXA_ADM_NUM', by='TP_FUNDO', ax=ax2)
ax2.set_title('Taxas por Tipo de Fundo')
ax2.set_ylabel('Taxa de Administração (%)')

# Top 20 classes por taxa média
ax3 = axes[1, 0]
top_classes = taxas_por_classe[taxas_por_classe['count'] > 50].head(20)
top_classes['mean'].plot(kind='barh', ax=ax3)
ax3.set_xlabel('Taxa Média (%)')
ax3.set_title('Top 20 Classes por Taxa Média (min 50 fundos)')

# Scatter: Patrimônio vs Taxa
ax4 = axes[1, 1]
df_com_pl = df_ativos[df_ativos['VL_PATRIM_LIQ'].notna()].copy()
df_com_pl['VL_PATRIM_LIQ_NUM'] = pd.to_numeric(df_com_pl['VL_PATRIM_LIQ'].str.replace(',', '.'), errors='coerce')
df_com_pl = df_com_pl[(df_com_pl['VL_PATRIM_LIQ_NUM'] > 0) & (df_com_pl['TAXA_ADM_NUM'] > 0)]

if len(df_com_pl) > 0:
    ax4.scatter(df_com_pl['VL_PATRIM_LIQ_NUM'] / 1e6, 
                df_com_pl['TAXA_ADM_NUM'],
                alpha=0.3, s=10)
    ax4.set_xscale('log')
    ax4.set_xlabel('Patrimônio Líquido (R$ milhões)')
    ax4.set_ylabel('Taxa de Administração (%)')
    ax4.set_title('Relação Patrimônio vs Taxa Admin')

plt.tight_layout()
plt.savefig(os.path.join(BASE_DIR, 'analise_taxas_cad_fi.png'), dpi=150)
plt.close()

print("\n7. Salvando análise detalhada...")
# Salvar Excel com análise
with pd.ExcelWriter(os.path.join(BASE_DIR, 'analise_taxas_cad_fi.xlsx'), engine='openpyxl') as writer:
    # Estatísticas gerais
    resumo = pd.DataFrame({
        'Métrica': ['Total Fundos', 'Fundos Ativos', 'Com Taxa Admin', 'Taxa Média', 'Taxa Mediana'],
        'Valor': [len(df_cad), len(df_ativos), df_ativos['TAXA_ADM_NUM'].notna().sum(), 
                  df_ativos['TAXA_ADM_NUM'].mean(), df_ativos['TAXA_ADM_NUM'].median()]
    })
    resumo.to_excel(writer, sheet_name='Resumo', index=False)
    
    # Taxas por classe
    taxas_por_classe.to_excel(writer, sheet_name='Por_Classe')
    
    # Fundos específicos
    df_especificos = pd.DataFrame()
    for cnpj in cnpjs_conhecidos:
        fundo = df_cad[df_cad['CNPJ_FUNDO'] == cnpj]
        if not fundo.empty:
            df_especificos = pd.concat([df_especificos, fundo])
    
    if not df_especificos.empty:
        df_especificos.to_excel(writer, sheet_name='Fundos_Chimborazo', index=False)

print("\nAnálise concluída!")
print(f"Arquivos salvos em: {BASE_DIR}")