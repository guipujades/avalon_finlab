import csv
import urllib.parse
from collections import Counter

def analyze_ipe_structure():
    """Analisa a estrutura do arquivo IPE e os links de download"""
    
    with open('ipe_cia_aberta_2025.csv', 'r', encoding='latin-1') as file:
        reader = csv.DictReader(file, delimiter=';')
        
        # Converter para lista para análise
        data = list(reader)
        
        print("=== INFORMAÇÕES GERAIS ===")
        print(f"Total de registros: {len(data)}")
        
        if data:
            print(f"\nColunas disponíveis:")
            for i, col in enumerate(data[0].keys(), 1):
                print(f"{i}. {col}")
            
            print("\n=== ANÁLISE DOS TIPOS DE DOCUMENTOS ===")
            
            # Contar categorias
            categorias = Counter(row['Categoria'] for row in data)
            print("\nTop 10 Categorias:")
            for cat, count in categorias.most_common(10):
                print(f"  {cat}: {count}")
            
            # Contar tipos
            tipos = Counter(row['Tipo'] for row in data)
            print("\nTop 10 Tipos:")
            for tipo, count in tipos.most_common(10):
                print(f"  {tipo}: {count}")
            
            # Contar espécies
            especies = Counter(row['Especie'] for row in data if row['Especie'])
            print("\nTop 10 Espécies:")
            for especie, count in especies.most_common(10):
                print(f"  {especie}: {count}")
            
            print("\n=== ANÁLISE DOS LINKS ===")
            # Analisar estrutura dos links
            sample_link = data[0]['Link_Download']
            print(f"\nExemplo de link:")
            print(sample_link)
            
            # Parse do link
            parsed = urllib.parse.urlparse(sample_link)
            params = urllib.parse.parse_qs(parsed.query)
            
            print(f"\nParâmetros do link:")
            for key, value in params.items():
                print(f"  {key}: {value}")
            
            print("\n=== EMPRESAS COM MAIS DOCUMENTOS ===")
            empresas = Counter((row['Codigo_CVM'], row['Nome_Companhia']) for row in data)
            for (codigo, nome), count in empresas.most_common(10):
                print(f"{codigo} - {nome}: {count} documentos")
            
            print("\n=== EXEMPLO DE REGISTROS ===")
            print("\nPrimeiros 3 registros completos:")
            for idx, row in enumerate(data[:3]):
                print(f"\nRegistro {idx + 1}:")
                for key, value in row.items():
                    print(f"  {key}: {value}")

if __name__ == "__main__":
    analyze_ipe_structure()