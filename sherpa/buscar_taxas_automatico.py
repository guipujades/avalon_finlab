"""
Busca automática de taxas de administração nos arquivos CVM
"""

import pandas as pd
import zipfile
from pathlib import Path
import os

def buscar_taxa_no_cadastro(cnpj, base_dir, mes='202505'):
    """
    Busca a taxa de administração de um fundo no cadastro CVM
    """
    arquivo_zip = base_dir / 'CDA' / f'cda_fi_{mes}.zip'
    
    if not arquivo_zip.exists():
        return None
    
    try:
        with zipfile.ZipFile(str(arquivo_zip), 'r') as zip_ref:
            # Procurar arquivo de cadastro
            for arquivo in zip_ref.namelist():
                if 'CAD' in arquivo.upper() and arquivo.endswith('.csv'):
                    # Ler o arquivo de cadastro
                    with zip_ref.open(arquivo) as f:
                        df_cad = pd.read_csv(f, sep=';', encoding='latin-1', low_memory=False)
                        
                        # Procurar o CNPJ
                        df_fundo = df_cad[df_cad['CNPJ_FUNDO'] == cnpj]
                        
                        if not df_fundo.empty:
                            # Procurar campo de taxa de administração
                            if 'TX_ADM' in df_fundo.columns:
                                taxa = df_fundo['TX_ADM'].iloc[0]
                                return float(taxa) if pd.notna(taxa) else None
                            elif 'TAXA_ADM' in df_fundo.columns:
                                taxa = df_fundo['TAXA_ADM'].iloc[0]
                                return float(taxa) if pd.notna(taxa) else None
    except Exception as e:
        print(f"Erro ao buscar taxa para {cnpj}: {e}")
    
    return None

def buscar_todas_taxas_camada2():
    """
    Busca automática de todas as taxas dos fundos aninhados
    """
    from pathlib import Path
    
    # WSL path
    BASE_DIR = Path('/mnt/c/Users/guilh/Documents/GitHub/sherpa/database')
    
    print("=== BUSCA AUTOMÁTICA DE TAXAS DE ADMINISTRAÇÃO ===")
    print("="*80)
    
    # Lista de todos os fundos aninhados que precisamos buscar
    fundos_buscar = [
        # ALPAMAYO
        {'origem': 'ALPAMAYO', 'cnpj': '12.809.201/0001-13', 'nome': 'SPX RAPTOR FEEDER'},
        {'origem': 'ALPAMAYO', 'cnpj': '43.551.227/0001-38', 'nome': 'ATIT VÉRTICE FOF'},
        {'origem': 'ALPAMAYO', 'cnpj': '16.478.741/0001-12', 'nome': 'SQUADRA LONG-ONLY'},
        {'origem': 'ALPAMAYO', 'cnpj': '42.317.906/0001-84', 'nome': 'VÉRTICE DYN COU'},
        {'origem': 'ALPAMAYO', 'cnpj': '24.546.223/0001-17', 'nome': 'ITAÚ VÉRTICE IBOVESPA EQUITIES'},
        {'origem': 'ALPAMAYO', 'cnpj': '50.324.325/0001-06', 'nome': 'OCEANA VALOR A3'},
        {'origem': 'ALPAMAYO', 'cnpj': '34.793.093/0001-70', 'nome': 'NAVI CRUISE A'},
        {'origem': 'ALPAMAYO', 'cnpj': '14.096.710/0001-71', 'nome': 'ITAÚ AÇÕES FUND OF FUNDS'},
        {'origem': 'ALPAMAYO', 'cnpj': '56.125.991/0001-93', 'nome': 'SPX PATRIOT ITAÚ'},
        {'origem': 'ALPAMAYO', 'cnpj': '42.827.012/0001-34', 'nome': 'PROWLER 2'},
        {'origem': 'ALPAMAYO', 'cnpj': '37.887.733/0001-08', 'nome': 'SHARP LONG BIASED A'},
        {'origem': 'ALPAMAYO', 'cnpj': '39.573.804/0001-15', 'nome': 'NAVI FENDER A'},
        {'origem': 'ALPAMAYO', 'cnpj': '19.781.902/0001-30', 'nome': 'OCEANA LONG BIASED FEEDER I'},
        {'origem': 'ALPAMAYO', 'cnpj': '46.098.790/0001-90', 'nome': 'ABSOLUTE PACE A'},
        {'origem': 'ALPAMAYO', 'cnpj': '28.140.793/0001-63', 'nome': 'ITAÚ VÉRTICE FUNDAMENTA LATAM'},
        {'origem': 'ALPAMAYO', 'cnpj': '41.287.689/0001-64', 'nome': 'ITAÚ VÉRTICE RISING STARS'},
        {'origem': 'ALPAMAYO', 'cnpj': '21.407.105/0001-30', 'nome': 'ITAÚ VÉRTICE RENDA FIXA DI'},
        {'origem': 'ALPAMAYO', 'cnpj': '07.096.546/0001-37', 'nome': 'ITAÚ CAIXA AÇÕES'},
        
        # CAPSTONE
        {'origem': 'CAPSTONE', 'cnpj': '12.808.980/0001-32', 'nome': 'SPX RAPTOR MASTER'},
        
        # ITAÚ DOLOMITAS
        {'origem': 'ITAÚ DOLOMITAS', 'cnpj': '41.272.876/0001-74', 'nome': 'ITAÚ MASTER RISING STARS'},
        {'origem': 'ITAÚ DOLOMITAS', 'cnpj': '51.533.573/0001-11', 'nome': 'ITAÚ VÉRTICE SOBERANO Z'},
        {'origem': 'ITAÚ DOLOMITAS', 'cnpj': '24.552.905/0001-32', 'nome': 'ITAÚ SOBERANO RF DI LP'},
        
        # ITAÚ VÉRTICE COMPROMISSO
        {'origem': 'ITAÚ VÉRTICE COMPROMISSO', 'cnpj': '35.823.433/0001-21', 'nome': 'ITAÚ ZERAGEM'},
        
        # Adicionar mais conforme necessário...
    ]
    
    # Tentar vários meses
    meses = ['202505', '202504', '202503', '202502', '202501', '202412']
    
    resultados = []
    
    for fundo in fundos_buscar:
        print(f"\nBuscando: {fundo['nome']} ({fundo['cnpj']})")
        
        taxa_encontrada = None
        mes_encontrado = None
        
        # Tentar em vários meses
        for mes in meses:
            taxa = buscar_taxa_no_cadastro(fundo['cnpj'], BASE_DIR, mes)
            
            if taxa is not None:
                taxa_encontrada = taxa
                mes_encontrado = mes
                break
        
        if taxa_encontrada is not None:
            print(f"  ✓ Taxa encontrada: {taxa_encontrada*100:.2f}% (mês {mes_encontrado})")
            resultados.append({
                'origem': fundo['origem'],
                'cnpj': fundo['cnpj'],
                'nome': fundo['nome'],
                'taxa': taxa_encontrada,
                'mes': mes_encontrado
            })
        else:
            print(f"  ✗ Taxa não encontrada")
            resultados.append({
                'origem': fundo['origem'],
                'cnpj': fundo['cnpj'],
                'nome': fundo['nome'],
                'taxa': None,
                'mes': None
            })
    
    # Resumo
    print("\n\n" + "="*80)
    print("RESUMO DAS TAXAS ENCONTRADAS")
    print("="*80)
    
    df_resultado = pd.DataFrame(resultados)
    
    # Por origem
    for origem in df_resultado['origem'].unique():
        print(f"\n{origem}:")
        df_origem = df_resultado[df_resultado['origem'] == origem]
        
        encontradas = df_origem[df_origem['taxa'].notna()]
        nao_encontradas = df_origem[df_origem['taxa'].isna()]
        
        print(f"  - Taxas encontradas: {len(encontradas)}")
        print(f"  - Taxas não encontradas: {len(nao_encontradas)}")
        
        if len(encontradas) > 0:
            print("\n  Taxas encontradas:")
            for _, row in encontradas.iterrows():
                print(f"    {row['nome']:<40} {row['taxa']*100:>6.2f}%")
    
    # Salvar resultados
    df_resultado.to_csv('taxas_fundos_aninhados_automatico.csv', index=False)
    print("\n✓ Resultados salvos em: taxas_fundos_aninhados_automatico.csv")
    
    return df_resultado

def explorar_estrutura_cadastro():
    """
    Explora a estrutura do arquivo de cadastro para encontrar campos de taxa
    """
    from pathlib import Path
    
    BASE_DIR = Path('/mnt/c/Users/guilh/Documents/GitHub/sherpa/database')
    arquivo_zip = BASE_DIR / 'CDA' / 'cda_fi_202505.zip'
    
    print("\n\n=== EXPLORANDO ESTRUTURA DO CADASTRO ===")
    print("="*80)
    
    try:
        with zipfile.ZipFile(str(arquivo_zip), 'r') as zip_ref:
            for arquivo in zip_ref.namelist():
                if 'CAD' in arquivo.upper() and arquivo.endswith('.csv'):
                    print(f"\nArquivo encontrado: {arquivo}")
                    
                    with zip_ref.open(arquivo) as f:
                        # Ler apenas as primeiras linhas para ver estrutura
                        df_sample = pd.read_csv(f, sep=';', encoding='latin-1', nrows=5)
                        
                        print("\nColunas disponíveis:")
                        for col in df_sample.columns:
                            if 'TX' in col.upper() or 'TAX' in col.upper() or 'ADM' in col.upper():
                                print(f"  → {col} (possível campo de taxa)")
                            else:
                                print(f"    {col}")
                        
                        # Mostrar um exemplo
                        if len(df_sample) > 0:
                            print("\nExemplo de registro:")
                            for col in df_sample.columns:
                                if 'TX' in col.upper() or 'TAX' in col.upper():
                                    print(f"  {col}: {df_sample[col].iloc[0]}")
                    
                    break
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    # Primeiro explorar estrutura
    explorar_estrutura_cadastro()
    
    # Depois buscar todas as taxas
    df_taxas = buscar_todas_taxas_camada2()