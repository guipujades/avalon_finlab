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

print(f"Total de registros: {len(df)}")

# Buscar empresas relacionadas
palavras_chave = ['PETRO', 'VALE', 'ITAU', 'BRADESCO', 'AMBEV', 'MAGAZ']

print("\nEmpresas encontradas:")
empresas_unicas = sorted(df['Nome_Companhia'].unique())

for palavra in palavras_chave:
    print(f"\n--- Empresas com '{palavra}' ---")
    empresas_filtradas = [emp for emp in empresas_unicas if palavra in emp.upper()]
    for emp in empresas_filtradas[:5]:
        print(f"  {emp}")

# Mostrar estrutura de dados
print("\n--- Colunas disponíveis ---")
print(df.columns.tolist())

# Mostrar exemplos de releases
print("\n--- Últimos 5 releases ---")
df['Data_Entrega'] = pd.to_datetime(df['Data_Entrega'], errors='coerce')
df_recentes = df.sort_values('Data_Entrega', ascending=False).head(5)

for _, row in df_recentes.iterrows():
    print(f"\n{row['Nome_Companhia']} - {row['Data_Entrega'].strftime('%Y-%m-%d')}")
    print(f"  Assunto: {row['Assunto'][:80]}...")
    print(f"  Tipo: {row['Tipo']}")