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

print("ANÁLISE DE TAXAS DE ADMINISTRAÇÃO - VALORES CORRIGIDOS")
print("="*80)

# Taxas corretas fornecidas pelo usuário
taxas_corretas = {
    '56.430.872/0001-44': {'nome': 'ALPAMAYO', 'taxa': 0.04, 'observacao': 'Corrigido de 1.5% para 0.04%'},
    '36.248.791/0001-10': {'nome': 'CAPSTONE MACRO A', 'taxa': 1.90, 'observacao': 'Confirmado'},
    '32.311.914/0001-60': {'nome': 'VINCI CAPITAL PARTNERS III', 'taxa': 0.0, 'observacao': 'Taxa 0 - investigar 2ª camada'},
    '41.535.122/0001-60': {'nome': 'KINEA PRIVATE EQUITY V', 'taxa': 0.0, 'observacao': 'Taxa 0 - investigar 2ª camada'},
    '55.419.784/0001-89': {'nome': 'ITAÚ DOLOMITAS', 'taxa': 0.06, 'observacao': 'Corrigido de 2% para 0.06%'},
    '21.407.105/0001-30': {'nome': 'ITAÚ VÉRTICE RF DI FIF', 'taxa': 0.0, 'observacao': 'Taxa 0 confirmada'},
    '18.138.913/0001-34': {'nome': 'ITAÚ VÉRTICE COMPROMISSO RF DI', 'taxa': 0.15, 'observacao': 'Confirmado'},
    '07.096.546/0001-37': {'nome': 'ITAÚ CAIXA AÇÕES', 'taxa': 0.0, 'observacao': 'Taxa 0 confirmada'},
    '12.138.862/0001-64': {'nome': 'FIDC SILVERADO', 'taxa': 0.0, 'observacao': 'Taxa 0'},
    '24.546.223/0001-17': {'nome': 'ITAÚ VÉRTICE IBOVESPA', 'taxa': 0.0, 'observacao': 'Taxa 0'}
}

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
        valor_total_carteira = df_carteira['VL_MERC_POS_FINAL'].sum()
        print(f"  Valor total: R$ {valor_total_carteira:,.2f}")
except Exception as e:
    print(f"✗ Erro ao carregar carteira: {e}")
    exit(1)

# 2. Identificar fundos na carteira
print("\n2. Identificando fundos na carteira...")
df_fundos = df_carteira[df_carteira['CATEGORIA_ATIVO'] == 'Fundos'].copy()
fundos_agrupados = df_fundos.groupby('CNPJ_FUNDO_CLASSE_COTA').agg({
    'VL_MERC_POS_FINAL': 'sum',
    'NM_FUNDO_CLASSE_SUBCLASSE_COTA': 'first'
}).reset_index()
print(f"✓ Fundos únicos: {len(fundos_agrupados)}")

# 3. Calcular custos com taxas corretas
print("\n3. Calculando custos com taxas corretas...")
print("-"*80)

resultados = []
fundos_taxa_zero = []
custo_total = 0

for _, fundo in fundos_agrupados.iterrows():
    cnpj = fundo['CNPJ_FUNDO_CLASSE_COTA']
    nome = fundo['NM_FUNDO_CLASSE_SUBCLASSE_COTA']
    valor = fundo['VL_MERC_POS_FINAL']
    
    if cnpj in taxas_corretas:
        info = taxas_corretas[cnpj]
        taxa = info['taxa']
        custo_anual = valor * (taxa / 100)
        custo_total += custo_anual
        
        resultado = {
            'CNPJ': cnpj,
            'Nome': nome,
            'Valor': valor,
            'Taxa_Adm_%': taxa,
            'Custo_Anual': custo_anual,
            'Observação': info['observacao']
        }
        resultados.append(resultado)
        
        print(f"\n{nome[:50]}")
        print(f"  CNPJ: {cnpj}")
        print(f"  Valor: R$ {valor:,.2f}")
        print(f"  Taxa: {taxa:.2f}%")
        print(f"  Custo anual: R$ {custo_anual:,.2f}")
        print(f"  Obs: {info['observacao']}")
        
        if taxa == 0:
            fundos_taxa_zero.append(resultado)
    else:
        print(f"\n✗ {nome[:50]} - CNPJ {cnpj} não encontrado nas taxas fornecidas")

# 4. Resumo
print("\n" + "="*80)
print("RESUMO DA ANÁLISE COM TAXAS CORRIGIDAS:")
print("="*80)

df_resultados = pd.DataFrame(resultados)
valor_total_fundos = df_resultados['Valor'].sum()
taxa_media_ponderada = (df_resultados['Taxa_Adm_%'] * df_resultados['Valor']).sum() / valor_total_fundos

print(f"\nValor total da carteira: R$ {valor_total_carteira:,.2f}")
print(f"Valor em fundos: R$ {valor_total_fundos:,.2f} ({valor_total_fundos/valor_total_carteira*100:.1f}%)")
print(f"\nTaxa média ponderada: {taxa_media_ponderada:.4f}%")
print(f"Custo total anual (1ª camada): R$ {custo_total:,.2f}")
print(f"Custo sobre patrimônio: {custo_total/valor_total_carteira*100:.4f}%")
print(f"Custo mensal estimado: R$ {custo_total/12:,.2f}")

# Fundos com taxa zero
print(f"\nFundos com taxa 0% (necessitam análise 2ª camada): {len(fundos_taxa_zero)}")
valor_taxa_zero = sum(f['Valor'] for f in fundos_taxa_zero)
print(f"Valor em fundos taxa 0%: R$ {valor_taxa_zero:,.2f} ({valor_taxa_zero/valor_total_fundos*100:.1f}% dos fundos)")

# Top custos
df_com_custo = df_resultados[df_resultados['Custo_Anual'] > 0].sort_values('Custo_Anual', ascending=False)
if len(df_com_custo) > 0:
    print("\nTop 5 fundos por custo anual:")
    for _, f in df_com_custo.head(5).iterrows():
        print(f"  {f['Nome'][:40]:40} | Taxa: {f['Taxa_Adm_%']:>5.2f}% | Custo: R$ {f['Custo_Anual']:>12,.2f}")

# Comparação com análise anterior
print("\n" + "="*80)
print("COMPARAÇÃO COM ANÁLISE ANTERIOR:")
print("="*80)
custo_anterior = 2178360.05  # Da análise anterior
economia = custo_anterior - custo_total
print(f"Custo anterior (incorreto): R$ {custo_anterior:,.2f}")
print(f"Custo correto: R$ {custo_total:,.2f}")
print(f"Diferença: R$ {economia:,.2f} ({economia/custo_anterior*100:.1f}% menor)")

# 5. Salvar resultados
arquivo_saida = os.path.join(BASE_DIR, 'analise_taxas_corrigidas.xlsx')
with pd.ExcelWriter(arquivo_saida, engine='openpyxl') as writer:
    # Todos os fundos
    df_resultados.to_excel(writer, sheet_name='Todos_Fundos', index=False)
    
    # Fundos com taxa zero
    if fundos_taxa_zero:
        pd.DataFrame(fundos_taxa_zero).to_excel(writer, sheet_name='Fundos_Taxa_Zero', index=False)
    
    # Fundos com custo
    df_com_custo.to_excel(writer, sheet_name='Fundos_Com_Custo', index=False)
    
    # Resumo
    resumo = pd.DataFrame({
        'Métrica': [
            'Valor Total Carteira',
            'Valor em Fundos', 
            '% em Fundos',
            'Taxa Média Ponderada (%)',
            'Custo Total Anual',
            'Custo % Patrimônio',
            'Custo Mensal',
            'Fundos com Taxa 0%',
            'Valor em Fundos Taxa 0%',
            'Economia vs Análise Anterior'
        ],
        'Valor': [
            valor_total_carteira,
            valor_total_fundos,
            valor_total_fundos/valor_total_carteira*100,
            taxa_media_ponderada,
            custo_total,
            custo_total/valor_total_carteira*100,
            custo_total/12,
            len(fundos_taxa_zero),
            valor_taxa_zero,
            economia
        ]
    })
    resumo.to_excel(writer, sheet_name='Resumo', index=False)

print(f"\n✓ Análise salva em: {arquivo_saida}")

# 6. Criar visualização
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

# Gráfico 1: Distribuição de custos
df_com_custo_sorted = df_com_custo.sort_values('Custo_Anual', ascending=True)
if len(df_com_custo_sorted) > 0:
    y_pos = np.arange(len(df_com_custo_sorted))
    ax1.barh(y_pos, df_com_custo_sorted['Custo_Anual'] / 1000)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels([nome[:30] + '...' if len(nome) > 30 else nome 
                         for nome in df_com_custo_sorted['Nome']], fontsize=10)
    ax1.set_xlabel('Custo Anual (R$ mil)')
    ax1.set_title('Custos de Administração por Fundo')
    ax1.grid(axis='x', alpha=0.3)
    
    # Adicionar valores
    for i, (idx, row) in enumerate(df_com_custo_sorted.iterrows()):
        ax1.text(row['Custo_Anual']/1000 + 5, i, 
                f"R$ {row['Custo_Anual']/1000:.1f}k ({row['Taxa_Adm_%']:.2f}%)", 
                va='center', fontsize=9)

# Gráfico 2: Composição da carteira
categorias = ['Com Taxa > 0', 'Taxa Zero', 'Outros Ativos']
valores = [
    df_com_custo['Valor'].sum() / 1e6,
    valor_taxa_zero / 1e6,
    (valor_total_carteira - valor_total_fundos) / 1e6
]
cores = ['#ff9999', '#66b3ff', '#99ff99']

wedges, texts, autotexts = ax2.pie(valores, labels=categorias, autopct='%1.1f%%', 
                                    colors=cores, startangle=90)
ax2.set_title('Composição da Carteira por Tipo de Taxa')

# Adicionar valores em milhões
for i, (wedge, text, autotext) in enumerate(zip(wedges, texts, autotexts)):
    angle = (wedge.theta2 + wedge.theta1) / 2
    x = wedge.r * 0.7 * np.cos(np.radians(angle))
    y = wedge.r * 0.7 * np.sin(np.radians(angle))
    ax2.text(x, y, f'R$ {valores[i]:.1f}M', ha='center', va='center', fontsize=10, weight='bold')

plt.tight_layout()
grafico_path = os.path.join(BASE_DIR, 'taxas_admin_corrigidas.png')
plt.savefig(grafico_path, dpi=150, bbox_inches='tight')
plt.close()

print(f"✓ Gráfico salvo em: {grafico_path}")
print("\nAnálise concluída!")