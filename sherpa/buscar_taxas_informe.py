"""
Busca taxas de administração nos informes mensais da CVM
"""

import pandas as pd
import zipfile
from pathlib import Path
import os

def buscar_taxa_no_informe(cnpj, base_dir, mes='202505'):
    """
    Busca a taxa de administração nos arquivos de informe mensal
    """
    # Tentar no informe mensal
    arquivo_inf = base_dir / 'INF' / f'inf_mensal_fi_{mes}.zip'
    
    if arquivo_inf.exists():
        try:
            with zipfile.ZipFile(str(arquivo_inf), 'r') as zip_ref:
                # Procurar arquivo de informe
                for arquivo in zip_ref.namelist():
                    if arquivo.endswith('.csv'):
                        with zip_ref.open(arquivo) as f:
                            df = pd.read_csv(f, sep=';', encoding='latin-1', low_memory=False)
                            
                            # Verificar colunas disponíveis
                            colunas_taxa = [col for col in df.columns if 'TX' in col.upper() or 'TAX' in col.upper() or 'ADM' in col.upper()]
                            
                            if colunas_taxa:
                                # Procurar o CNPJ
                                df_fundo = df[df['CNPJ_FUNDO'] == cnpj] if 'CNPJ_FUNDO' in df.columns else pd.DataFrame()
                                
                                if not df_fundo.empty:
                                    for col in colunas_taxa:
                                        if col in df_fundo.columns:
                                            taxa = df_fundo[col].iloc[0]
                                            if pd.notna(taxa):
                                                return float(taxa)
        except Exception as e:
            pass
    
    return None

def buscar_taxa_cadastro_geral():
    """
    Busca taxas no cadastro geral de fundos
    """
    from pathlib import Path
    
    BASE_DIR = Path('/mnt/c/Users/guilh/Documents/GitHub/sherpa/database')
    
    print("=== BUSCA DE TAXAS NO CADASTRO GERAL ===")
    print("="*80)
    
    # Verificar se existe arquivo de cadastro geral
    for arquivo in os.listdir(BASE_DIR):
        if 'cadastro' in arquivo.lower() or 'cad_' in arquivo.lower():
            print(f"Arquivo encontrado: {arquivo}")
            
            try:
                if arquivo.endswith('.csv'):
                    df = pd.read_csv(BASE_DIR / arquivo, sep=';', encoding='latin-1', low_memory=False)
                    print(f"Colunas: {list(df.columns)[:10]}...")
                    
                    # Procurar colunas de taxa
                    for col in df.columns:
                        if 'TX' in col.upper() or 'TAX' in col.upper() or 'ADM' in col.upper():
                            print(f"  → Coluna de taxa encontrada: {col}")
                            
                elif arquivo.endswith('.xlsx'):
                    df = pd.read_excel(BASE_DIR / arquivo)
                    print(f"Colunas: {list(df.columns)[:10]}...")
            except Exception as e:
                print(f"Erro ao ler {arquivo}: {e}")
    
    # Tentar em pastas específicas
    pastas = ['CADASTRO', 'CAD', 'FI', 'FUNDOS']
    for pasta in pastas:
        pasta_path = BASE_DIR / pasta
        if pasta_path.exists():
            print(f"\nVerificando pasta: {pasta}")
            for arquivo in os.listdir(pasta_path):
                if arquivo.endswith(('.csv', '.xlsx')):
                    print(f"  - {arquivo}")

def analisar_estrutura_completa():
    """
    Analisa toda a estrutura de dados para encontrar onde estão as taxas
    """
    from pathlib import Path
    
    BASE_DIR = Path('/mnt/c/Users/guilh/Documents/GitHub/sherpa/database')
    
    print("\n=== ANÁLISE DA ESTRUTURA DE DADOS ===")
    print("="*80)
    
    # Listar todas as pastas
    print("\nPastas disponíveis:")
    for pasta in os.listdir(BASE_DIR):
        pasta_path = BASE_DIR / pasta
        if os.path.isdir(pasta_path):
            print(f"\n{pasta}/")
            # Listar alguns arquivos
            arquivos = os.listdir(pasta_path)[:5]
            for arq in arquivos:
                print(f"  - {arq}")
            if len(os.listdir(pasta_path)) > 5:
                print(f"  ... e mais {len(os.listdir(pasta_path)) - 5} arquivos")

def buscar_em_serializado():
    """
    Verifica se temos dados serializados com taxas
    """
    from pathlib import Path
    import pickle
    
    BASE_DIR = Path('/mnt/c/Users/guilh/Documents/GitHub/sherpa/database')
    serial_dir = BASE_DIR / 'serial_carteiras'
    
    print("\n=== VERIFICANDO DADOS SERIALIZADOS ===")
    print("="*80)
    
    if serial_dir.exists():
        for arquivo in os.listdir(serial_dir):
            if arquivo.endswith('.pkl'):
                print(f"\nArquivo: {arquivo}")
                try:
                    with open(serial_dir / arquivo, 'rb') as f:
                        dados = pickle.load(f)
                        
                    if isinstance(dados, dict):
                        print(f"  Chaves: {list(dados.keys())}")
                        
                        # Verificar se tem informações de taxas
                        if 'cadastro' in dados or 'taxas' in dados:
                            print("  → Possível informação de taxas encontrada!")
                except Exception as e:
                    print(f"  Erro: {e}")

if __name__ == "__main__":
    # Analisar estrutura completa
    analisar_estrutura_completa()
    
    # Buscar no cadastro geral
    buscar_taxa_cadastro_geral()
    
    # Verificar dados serializados
    buscar_em_serializado()