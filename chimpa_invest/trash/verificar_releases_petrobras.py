import requests
import pandas as pd
import zipfile
import io
from datetime import datetime

# Baixar dados IPE
print("Baixando dados IPE...")
url = f'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/ipe_cia_aberta_{datetime.now().year}.zip'

response = requests.get(url, timeout=30)
with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
    df = pd.read_csv(
        zip_file.open(f'ipe_cia_aberta_{datetime.now().year}.csv'),
        sep=';',
        encoding='latin-1'
    )

# Filtrar Petrobras
df_petro = df[df['Nome_Companhia'] == 'PETRÓLEO BRASILEIRO  S.A.  - PETROBRAS'].copy()
print(f"\nTotal de documentos Petrobras: {len(df_petro)}")

# Converter data
df_petro['Data_Entrega'] = pd.to_datetime(df_petro['Data_Entrega'], errors='coerce')

# Ordenar por data
df_petro = df_petro.sort_values('Data_Entrega', ascending=False)

# Tipos únicos
print("\nTipos de documentos:")
for tipo in df_petro['Tipo'].unique():
    count = len(df_petro[df_petro['Tipo'] == tipo])
    print(f"  {tipo}: {count}")

# Filtrar por palavras relacionadas a resultados
print("\n--- Documentos com 'resultado' ou 'desempenho' ---")
mask_resultado = df_petro['Assunto'].str.contains('resultado|desempenho|trimestre|1T|2T|3T|4T|earnings', case=False, na=False)
df_resultados = df_petro[mask_resultado]

for idx, row in df_resultados.head(10).iterrows():
    assunto = str(row['Assunto'])[:100] if pd.notna(row['Assunto']) else 'N/A'
    print(f"\n{row['Data_Entrega'].strftime('%Y-%m-%d')} - {row['Tipo']}")
    print(f"  {assunto}")

# Buscar padrões específicos
print("\n--- Análise de padrões de assunto ---")
padroes = ['Desempenho', 'Release', 'ITR', 'Resultado', 'Trimestre', 'Financeiro']
for padrao in padroes:
    mask = df_petro['Assunto'].str.contains(padrao, case=False, na=False)
    count = mask.sum()
    if count > 0:
        print(f"\n'{padrao}': {count} documentos")
        exemplo = df_petro[mask].iloc[0]
        print(f"  Exemplo: {exemplo['Data_Entrega'].strftime('%Y-%m-%d')} - {str(exemplo['Assunto'])[:80]}...")