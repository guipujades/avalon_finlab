import pandas as pd
import urllib.parse

def analyze_ipe_structure():
    """Analisa a estrutura do arquivo IPE e os links de download"""
    
    # Ler o arquivo CSV
    df = pd.read_csv('ipe_cia_aberta_2025.csv', sep=';', encoding='latin-1')
    
    print("=== INFORMAÇÕES GERAIS ===")
    print(f"Total de registros: {len(df)}")
    print(f"\nColunas disponíveis:")
    for i, col in enumerate(df.columns, 1):
        print(f"{i}. {col}")
    
    print("\n=== ANÁLISE DOS TIPOS DE DOCUMENTOS ===")
    print("\nCategorias únicas:")
    print(df['Categoria'].value_counts().head(10))
    
    print("\nTipos únicos:")
    print(df['Tipo'].value_counts().head(10))
    
    print("\nEspécies únicas:")
    print(df['Especie'].value_counts().head(10))
    
    print("\n=== ANÁLISE DOS LINKS ===")
    # Analisar estrutura dos links
    sample_link = df['Link_Download'].iloc[0]
    print(f"\nExemplo de link:")
    print(sample_link)
    
    # Parse do link
    parsed = urllib.parse.urlparse(sample_link)
    params = urllib.parse.parse_qs(parsed.query)
    
    print(f"\nParâmetros do link:")
    for key, value in params.items():
        print(f"  {key}: {value}")
    
    print("\n=== EMPRESAS COM MAIS DOCUMENTOS ===")
    top_companies = df.groupby(['Codigo_CVM', 'Nome_Companhia']).size().reset_index(name='count')
    top_companies = top_companies.sort_values('count', ascending=False).head(10)
    for _, row in top_companies.iterrows():
        print(f"{row['Codigo_CVM']} - {row['Nome_Companhia']}: {row['count']} documentos")
    
    print("\n=== EXEMPLO DE REGISTROS ===")
    print("\nPrimeiros 3 registros completos:")
    for idx in range(min(3, len(df))):
        print(f"\nRegistro {idx + 1}:")
        for col in df.columns:
            print(f"  {col}: {df.iloc[idx][col]}")

if __name__ == "__main__":
    analyze_ipe_structure()