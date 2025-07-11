import pandas as pd
import warnings
warnings.filterwarnings('ignore')

def buscar_em_arquivo_cda(arquivo, cnpjs_buscar):
    """Busca CNPJs em arquivo CDA específico"""
    try:
        # Tentar ler o arquivo
        df = pd.read_csv(arquivo, sep=';', encoding='latin-1')
        
        # Verificar se tem coluna CNPJ
        colunas_cnpj = [col for col in df.columns if 'CNPJ' in col.upper()]
        colunas_taxa = [col for col in df.columns if 'TAX' in col.upper() or 'ADM' in col.upper()]
        
        if colunas_cnpj and colunas_taxa:
            print(f"\nArquivo: {arquivo}")
            print(f"Colunas CNPJ: {colunas_cnpj}")
            print(f"Colunas Taxa: {colunas_taxa}")
            
            # Buscar CNPJs
            for cnpj in cnpjs_buscar:
                for col_cnpj in colunas_cnpj:
                    resultado = df[df[col_cnpj] == cnpj]
                    if not resultado.empty:
                        print(f"\nEncontrado CNPJ {cnpj}:")
                        for col in df.columns:
                            if not resultado.iloc[0][col] is None and str(resultado.iloc[0][col]).strip() != '':
                                print(f"  {col}: {resultado.iloc[0][col]}")
        
        return True
    except Exception as e:
        return False

def buscar_taxas_cda():
    # CNPJs para buscar
    cnpjs_buscar = [
        '14.096.710/0001-71',  # ITAÚ AÇÕES FUND OF FUNDS MULTIGESTOR X
        '12.808.980/0001-32',  # SPX RAPTOR MASTER
    ]
    
    print("Buscando taxas nos arquivos CDA...\n")
    
    # 1. Verificar arquivo PL (pode ter informações de taxa)
    arquivo_pl = './database/CDA/cda_fi_202505_extracted/cda_fi_PL_202505.csv'
    print(f"Verificando arquivo PL...")
    try:
        df_pl = pd.read_csv(arquivo_pl, sep=';', encoding='latin-1')
        print(f"Colunas do arquivo PL: {list(df_pl.columns)}")
        
        # Buscar fundos
        for cnpj in cnpjs_buscar:
            resultado = df_pl[df_pl['CNPJ_FUNDO'] == cnpj]
            if not resultado.empty:
                print(f"\n✓ Encontrado no PL: {cnpj}")
                for col in ['CNPJ_FUNDO', 'VL_PATRIM_LIQ', 'DT_COMPTC']:
                    if col in df_pl.columns:
                        print(f"  {col}: {resultado.iloc[0][col]}")
    except Exception as e:
        print(f"Erro ao ler arquivo PL: {e}")
    
    # 2. Verificar arquivos BLC (balanços)
    for i in range(1, 9):
        arquivo_blc = f'./database/CDA/cda_fi_202505_extracted/cda_fi_BLC_{i}_202505.csv'
        print(f"\nVerificando arquivo BLC_{i}...")
        try:
            df_blc = pd.read_csv(arquivo_blc, sep=';', encoding='latin-1', nrows=5)
            colunas = list(df_blc.columns)
            
            # Procurar colunas relacionadas a taxa
            colunas_interessantes = [col for col in colunas if any(palavra in col.upper() for palavra in ['TAXA', 'ADM', 'DESP', 'REMUN'])]
            
            if colunas_interessantes:
                print(f"  Colunas potencialmente relevantes: {colunas_interessantes}")
                
                # Ler arquivo completo e buscar
                df_blc_full = pd.read_csv(arquivo_blc, sep=';', encoding='latin-1')
                
                for cnpj in cnpjs_buscar:
                    if 'CNPJ_FUNDO' in df_blc_full.columns:
                        resultado = df_blc_full[df_blc_full['CNPJ_FUNDO'] == cnpj]
                        if not resultado.empty:
                            print(f"\n  ✓ Encontrado {cnpj} em BLC_{i}")
                            for col in colunas_interessantes:
                                if col in df_blc_full.columns:
                                    valor = resultado.iloc[0][col]
                                    if pd.notna(valor) and str(valor).strip() != '':
                                        print(f"    {col}: {valor}")
        except Exception as e:
            pass
    
    # 3. Verificar arquivo CONFID
    arquivo_confid = './database/CDA/cda_fi_202505_extracted/cda_fi_CONFID_202505.csv'
    print(f"\nVerificando arquivo CONFID...")
    try:
        df_confid = pd.read_csv(arquivo_confid, sep=';', encoding='latin-1')
        print(f"Colunas do arquivo CONFID: {list(df_confid.columns)[:10]}...")
        
        # Buscar fundos
        for cnpj in cnpjs_buscar:
            if 'CNPJ_FUNDO' in df_confid.columns:
                resultado = df_confid[df_confid['CNPJ_FUNDO'] == cnpj]
                if not resultado.empty:
                    print(f"\n✓ Encontrado no CONFID: {cnpj}")
                    # Mostrar primeiras colunas não vazias
                    for col in df_confid.columns[:20]:
                        valor = resultado.iloc[0][col]
                        if pd.notna(valor) and str(valor).strip() != '':
                            print(f"  {col}: {valor}")
    except Exception as e:
        print(f"Erro ao ler arquivo CONFID: {e}")

if __name__ == "__main__":
    buscar_taxas_cda()