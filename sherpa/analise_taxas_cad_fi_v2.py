import os
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

# Configurações
BASE_DIR = "/mnt/c/Users/guilh/Documents/GitHub/sherpa/database"
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

# Verificar tipo de dados da coluna TAXA_ADM
print(f"\nTipo da coluna TAXA_ADM: {df_cad['TAXA_ADM'].dtype}")
print(f"Primeiros valores de TAXA_ADM: {df_cad['TAXA_ADM'].head(10).tolist()}")

# 4. Converter taxa de administração (tratando diferentes formatos)
def converter_taxa(valor):
    """Converte taxa para formato numérico, tratando diferentes formatos"""
    if pd.isna(valor):
        return np.nan
    if isinstance(valor, (int, float)):
        return float(valor)
    if isinstance(valor, str):
        # Remove espaços e substitui vírgula por ponto
        valor_limpo = valor.strip().replace(',', '.')
        try:
            return float(valor_limpo)
        except:
            return np.nan
    return np.nan

df_ativos['TAXA_ADM_NUM'] = df_ativos['TAXA_ADM'].apply(converter_taxa)
df_ativos['TAXA_PERFM_NUM'] = df_ativos['TAXA_PERFM'].apply(converter_taxa)

# 5. Estatísticas gerais
print("\n3. Estatísticas de taxas de administração:")
fundos_com_taxa = df_ativos['TAXA_ADM_NUM'].notna().sum()
print(f"Fundos com taxa informada: {fundos_com_taxa} ({fundos_com_taxa/len(df_ativos)*100:.1f}%)")
print(f"Taxa média: {df_ativos['TAXA_ADM_NUM'].mean():.3f}%")
print(f"Taxa mediana: {df_ativos['TAXA_ADM_NUM'].median():.3f}%")
print(f"Taxa máxima: {df_ativos['TAXA_ADM_NUM'].max():.3f}%")

# Distribuição de taxas
print("\nDistribuição de taxas:")
print(f"  Até 0.5%: {(df_ativos['TAXA_ADM_NUM'] <= 0.5).sum()}")
print(f"  0.5% - 1%: {((df_ativos['TAXA_ADM_NUM'] > 0.5) & (df_ativos['TAXA_ADM_NUM'] <= 1)).sum()}")
print(f"  1% - 2%: {((df_ativos['TAXA_ADM_NUM'] > 1) & (df_ativos['TAXA_ADM_NUM'] <= 2)).sum()}")
print(f"  2% - 3%: {((df_ativos['TAXA_ADM_NUM'] > 2) & (df_ativos['TAXA_ADM_NUM'] <= 3)).sum()}")
print(f"  Acima de 3%: {(df_ativos['TAXA_ADM_NUM'] > 3).sum()}")

# 6. Analisar por classe
print("\n4. Taxas médias por classe de fundo (min 20 fundos):")
taxas_por_classe = df_ativos.groupby('CLASSE')['TAXA_ADM_NUM'].agg(['mean', 'count', 'median']).sort_values('mean', ascending=False)
for classe, row in taxas_por_classe.iterrows():
    if row['count'] >= 20:  # Apenas classes com mais de 20 fundos
        print(f"  {classe[:40]:40} | Média: {row['mean']:>5.2f}% | Mediana: {row['median']:>5.2f}% | Qtd: {row['count']:>5}")

# 7. Buscar fundos específicos para análise do Chimborazo
print("\n5. Buscando fundos específicos do Chimborazo...")

# Lista de CNPJs conhecidos da carteira (da análise anterior)
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
fundos_encontrados = []
fundos_nao_encontrados = []

for cnpj in cnpjs_conhecidos:
    fundo = df_cad[df_cad['CNPJ_FUNDO'] == cnpj]
    if not fundo.empty:
        nome = fundo.iloc[0]['DENOM_SOCIAL']
        taxa_adm = fundo.iloc[0]['TAXA_ADM']
        taxa_adm_num = converter_taxa(taxa_adm)
        situacao = fundo.iloc[0]['SIT']
        classe = fundo.iloc[0]['CLASSE'] if 'CLASSE' in fundo.columns else 'N/A'
        
        fundos_encontrados.append({
            'CNPJ': cnpj,
            'Nome': nome[:60],
            'Taxa_Adm': taxa_adm,
            'Taxa_Adm_Num': taxa_adm_num,
            'Situação': situacao,
            'Classe': classe
        })
        
        print(f"\n  ✓ CNPJ: {cnpj}")
        print(f"    Nome: {nome[:60]}")
        print(f"    Taxa Admin: {taxa_adm} ({taxa_adm_num:.2f}% se numérico)")
        print(f"    Situação: {situacao}")
        print(f"    Classe: {classe}")
    else:
        fundos_nao_encontrados.append(cnpj)
        print(f"\n  ✗ CNPJ: {cnpj} - NÃO ENCONTRADO NO CADASTRO CVM")

# 8. Criar visualização
print("\n6. Criando visualizações...")
plt.style.use('default')
fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# Histograma de taxas
ax1 = axes[0, 0]
taxas_validas = df_ativos['TAXA_ADM_NUM'].dropna()
taxas_ate_5 = taxas_validas[taxas_validas <= 5]
ax1.hist(taxas_ate_5, bins=50, edgecolor='black', alpha=0.7)
ax1.axvline(taxas_ate_5.mean(), color='red', linestyle='--', label=f'Média: {taxas_ate_5.mean():.2f}%')
ax1.set_xlabel('Taxa de Administração (%)')
ax1.set_ylabel('Quantidade de Fundos')
ax1.set_title('Distribuição de Taxas de Administração (até 5%)')
ax1.legend()

# Box plot por tipo de fundo
ax2 = axes[0, 1]
# Selecionar apenas tipos com mais de 100 fundos
tipos_counts = df_ativos['TP_FUNDO'].value_counts()
tipos_principais = tipos_counts[tipos_counts > 100].index[:5]
df_tipos = df_ativos[df_ativos['TP_FUNDO'].isin(tipos_principais) & df_ativos['TAXA_ADM_NUM'].notna()]

if len(df_tipos) > 0:
    box_data = [df_tipos[df_tipos['TP_FUNDO'] == tipo]['TAXA_ADM_NUM'].values for tipo in tipos_principais]
    ax2.boxplot(box_data, labels=tipos_principais)
    ax2.set_ylabel('Taxa de Administração (%)')
    ax2.set_title('Taxas por Tipo de Fundo')
    ax2.tick_params(axis='x', rotation=45)

# Top 15 classes por taxa média
ax3 = axes[1, 0]
top_classes = taxas_por_classe[taxas_por_classe['count'] >= 50].head(15)
if len(top_classes) > 0:
    top_classes['mean'].plot(kind='barh', ax=ax3)
    ax3.set_xlabel('Taxa Média (%)')
    ax3.set_title('Top 15 Classes por Taxa Média (min 50 fundos)')

# Análise específica dos fundos do Chimborazo
ax4 = axes[1, 1]
if fundos_encontrados:
    df_encontrados = pd.DataFrame(fundos_encontrados)
    df_encontrados_com_taxa = df_encontrados[df_encontrados['Taxa_Adm_Num'].notna()]
    
    if len(df_encontrados_com_taxa) > 0:
        y_pos = np.arange(len(df_encontrados_com_taxa))
        ax4.barh(y_pos, df_encontrados_com_taxa['Taxa_Adm_Num'])
        ax4.set_yticks(y_pos)
        ax4.set_yticklabels([nome[:30] + '...' if len(nome) > 30 else nome 
                             for nome in df_encontrados_com_taxa['Nome']])
        ax4.set_xlabel('Taxa de Administração (%)')
        ax4.set_title('Taxas dos Fundos na Carteira Chimborazo')
        
        # Adicionar valores nas barras
        for i, (idx, row) in enumerate(df_encontrados_com_taxa.iterrows()):
            ax4.text(row['Taxa_Adm_Num'] + 0.01, i, f"{row['Taxa_Adm_Num']:.2f}%", 
                    va='center', fontsize=9)

plt.tight_layout()
plt.savefig(os.path.join(BASE_DIR, 'analise_taxas_cad_fi.png'), dpi=150, bbox_inches='tight')
plt.close()

# 9. Salvar análise detalhada
print("\n7. Salvando análise detalhada...")
with pd.ExcelWriter(os.path.join(BASE_DIR, 'analise_taxas_cad_fi.xlsx'), engine='openpyxl') as writer:
    # Resumo geral
    resumo = pd.DataFrame({
        'Métrica': ['Total Fundos', 'Fundos Ativos', 'Com Taxa Admin', 'Taxa Média', 'Taxa Mediana', 
                    'Taxa Mínima', 'Taxa Máxima', 'Fundos Chimborazo Encontrados', 'Fundos Chimborazo Não Encontrados'],
        'Valor': [len(df_cad), len(df_ativos), df_ativos['TAXA_ADM_NUM'].notna().sum(), 
                  df_ativos['TAXA_ADM_NUM'].mean(), df_ativos['TAXA_ADM_NUM'].median(),
                  df_ativos['TAXA_ADM_NUM'].min(), df_ativos['TAXA_ADM_NUM'].max(),
                  len(fundos_encontrados), len(fundos_nao_encontrados)]
    })
    resumo.to_excel(writer, sheet_name='Resumo', index=False)
    
    # Taxas por classe
    taxas_por_classe.reset_index().to_excel(writer, sheet_name='Por_Classe', index=False)
    
    # Fundos do Chimborazo
    if fundos_encontrados:
        pd.DataFrame(fundos_encontrados).to_excel(writer, sheet_name='Fundos_Chimborazo', index=False)
    
    # Fundos não encontrados
    if fundos_nao_encontrados:
        pd.DataFrame({'CNPJ_Não_Encontrado': fundos_nao_encontrados}).to_excel(writer, sheet_name='Nao_Encontrados', index=False)

print("\nAnálise concluída!")
print(f"Arquivos salvos em: {BASE_DIR}")
print(f"\nResumo final:")
print(f"- Fundos do Chimborazo encontrados no CVM: {len(fundos_encontrados)}")
print(f"- Fundos do Chimborazo NÃO encontrados: {len(fundos_nao_encontrados)}")
if fundos_nao_encontrados:
    print(f"  CNPJs não encontrados: {', '.join(fundos_nao_encontrados)}")