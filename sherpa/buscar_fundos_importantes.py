import pandas as pd
import warnings
warnings.filterwarnings('ignore')

def buscar_fundos_importantes():
    print("Carregando cadastro CVM...")
    try:
        cad_fi = pd.read_csv('./database/CAD/cad_fi.csv', sep=';', encoding='latin-1')
        print(f"Cadastro carregado: {len(cad_fi)} fundos\n")
    except Exception as e:
        print(f"Erro ao carregar cadastro: {e}")
        return
    
    # Buscar especificamente os fundos mencionados pelo usuário
    fundos_importantes = []
    
    # 1. ITAÚ AÇÕES FUND OF FUNDS MULTIGESTOR X
    print("1. Buscando ITAÚ AÇÕES FUND OF FUNDS MULTIGESTOR X...")
    resultado = cad_fi[
        cad_fi['DENOM_SOCIAL'].str.contains('ITAU', case=False, na=False) & 
        cad_fi['DENOM_SOCIAL'].str.contains('MULTIGESTOR', case=False, na=False) &
        cad_fi['DENOM_SOCIAL'].str.contains('X', case=False, na=False)
    ]
    
    if not resultado.empty:
        for _, row in resultado.iterrows():
            print(f"  CNPJ: {row['CNPJ_FUNDO']}")
            print(f"  Nome: {row['DENOM_SOCIAL']}")
            print(f"  Taxa ADM: {row['TAXA_ADM']}%")
            print(f"  Situação: {row['SIT']}\n")
            fundos_importantes.append(row)
    
    # 2. SPX RAPTOR MASTER
    print("2. Buscando SPX RAPTOR MASTER...")
    resultado = cad_fi[
        cad_fi['DENOM_SOCIAL'].str.contains('SPX', case=False, na=False) & 
        cad_fi['DENOM_SOCIAL'].str.contains('RAPTOR', case=False, na=False) &
        cad_fi['DENOM_SOCIAL'].str.contains('MASTER', case=False, na=False)
    ]
    
    if not resultado.empty:
        for _, row in resultado.iterrows():
            print(f"  CNPJ: {row['CNPJ_FUNDO']}")
            print(f"  Nome: {row['DENOM_SOCIAL']}")
            print(f"  Taxa ADM: {row['TAXA_ADM']}%")
            print(f"  Situação: {row['SIT']}\n")
            fundos_importantes.append(row)
    
    # 3. ITAÚ DOLOMITAS
    print("3. Buscando ITAÚ DOLOMITAS...")
    resultado = cad_fi[
        cad_fi['DENOM_SOCIAL'].str.contains('ITAU', case=False, na=False) & 
        cad_fi['DENOM_SOCIAL'].str.contains('DOLOMITAS', case=False, na=False)
    ]
    
    if not resultado.empty:
        for _, row in resultado.iterrows():
            print(f"  CNPJ: {row['CNPJ_FUNDO']}")
            print(f"  Nome: {row['DENOM_SOCIAL']}")
            print(f"  Taxa ADM: {row['TAXA_ADM']}%")
            print(f"  Situação: {row['SIT']}\n")
            fundos_importantes.append(row)
    
    # 4. Buscar fundos com taxa próxima de 0.06% (como mencionado para o Itaú)
    print("4. Buscando fundos ITAU com taxa próxima a 0.06%...")
    resultado = cad_fi[
        (cad_fi['DENOM_SOCIAL'].str.contains('ITAU', case=False, na=False)) & 
        (cad_fi['TAXA_ADM'] >= 0.05) & 
        (cad_fi['TAXA_ADM'] <= 0.1) &
        (cad_fi['SIT'] == 'EM FUNCIONAMENTO NORMAL')
    ]
    
    if not resultado.empty:
        print(f"  Encontrados {len(resultado)} fundos Itaú com taxa entre 0.05% e 0.1%:")
        for _, row in resultado.head(10).iterrows():
            print(f"    - {row['CNPJ_FUNDO']} | {row['DENOM_SOCIAL'][:60]}... | Taxa: {row['TAXA_ADM']}%")
    
    # 5. Buscar fundos SPX RAPTOR com taxa próxima de 1.9%
    print("\n5. Buscando fundos SPX RAPTOR com taxa próxima a 1.9%...")
    resultado = cad_fi[
        (cad_fi['DENOM_SOCIAL'].str.contains('SPX', case=False, na=False)) & 
        (cad_fi['DENOM_SOCIAL'].str.contains('RAPTOR', case=False, na=False)) &
        (cad_fi['TAXA_ADM'] >= 1.5) & 
        (cad_fi['TAXA_ADM'] <= 2.5) &
        (cad_fi['SIT'] == 'EM FUNCIONAMENTO NORMAL')
    ]
    
    if not resultado.empty:
        print(f"  Encontrados {len(resultado)} fundos SPX Raptor com taxa entre 1.5% e 2.5%:")
        for _, row in resultado.iterrows():
            print(f"    CNPJ: {row['CNPJ_FUNDO']}")
            print(f"    Nome: {row['DENOM_SOCIAL']}")
            print(f"    Taxa: {row['TAXA_ADM']}%")
            print(f"    Situação: {row['SIT']}\n")
    
    return fundos_importantes

if __name__ == "__main__":
    buscar_fundos_importantes()