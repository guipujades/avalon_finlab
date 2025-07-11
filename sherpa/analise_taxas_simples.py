import os
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Configurações
BASE_DIR = "/mnt/c/Users/guilh/Documents/GitHub/sherpa/database"
CNPJ_CHIMBORAZO = '54.195.596/0001-51'

print("Analisando taxas de administração - Versão Simplificada")
print("="*80)

# Lista de CNPJs da carteira Chimborazo
cnpjs_chimborazo = [
    '07.096.546/0001-37',  # ITAÚ VÉRTICE RF DI
    '12.138.862/0001-64',  # SILVERADO MAXIMUM II
    '18.138.913/0001-34',  # ITAÚ VÉRTICE COMPROMISSO RF DI
    '21.407.105/0001-30',  # ITAÚ VÉRTICE RF DI FIF
    '24.546.223/0001-17',  # ITAÚ VÉRTICE IBOVESPA
    '32.311.914/0001-60',  # VINCI CAPITAL PARTNERS III
    '36.248.791/0001-10',  # CAPSTONE MACRO A
    '41.535.122/0001-60',  # KINEA PRIVATE EQUITY V
    '55.419.784/0001-89',  # ITAÚ DOLOMITAS
    '56.430.872/0001-44',  # ALPAMAYO
]

print("\n1. Carregando arquivo cad_fi.csv...")
caminho_cad = os.path.join(BASE_DIR, 'CAD', 'cad_fi.csv')

try:
    # Tentar carregar com engine python (mais robusto)
    df_cad = pd.read_csv(caminho_cad, 
                         encoding='latin-1', 
                         delimiter=';', 
                         engine='python',
                         on_bad_lines='skip')
    print(f"✓ Arquivo carregado com sucesso! Total de registros: {len(df_cad)}")
except Exception as e:
    print(f"✗ Erro ao carregar arquivo: {e}")
    exit(1)

# Verificar colunas
print(f"\n2. Colunas disponíveis: {df_cad.columns.tolist()[:20]}...")

# Buscar fundos específicos
print(f"\n3. Buscando os {len(cnpjs_chimborazo)} fundos da carteira Chimborazo...")
print("-"*80)

fundos_encontrados = []
fundos_nao_encontrados = []

for cnpj in cnpjs_chimborazo:
    try:
        fundo = df_cad[df_cad['CNPJ_FUNDO'] == cnpj]
        
        if not fundo.empty:
            registro = fundo.iloc[0]
            nome = registro.get('DENOM_SOCIAL', 'N/A')
            situacao = registro.get('SIT', 'N/A')
            taxa_adm = registro.get('TAXA_ADM', 'N/A')
            taxa_perf = registro.get('TAXA_PERFM', 'N/A')
            classe = registro.get('CLASSE', 'N/A')
            
            print(f"\n✓ ENCONTRADO: {cnpj}")
            print(f"  Nome: {nome[:60]}")
            print(f"  Situação: {situacao}")
            print(f"  Taxa Admin: {taxa_adm}")
            print(f"  Taxa Perf: {taxa_perf}")
            print(f"  Classe: {classe}")
            
            fundos_encontrados.append({
                'CNPJ': cnpj,
                'Nome': nome,
                'Situação': situacao,
                'Taxa_Adm': taxa_adm,
                'Taxa_Perf': taxa_perf,
                'Classe': classe
            })
        else:
            print(f"\n✗ NÃO ENCONTRADO: {cnpj}")
            fundos_nao_encontrados.append(cnpj)
            
    except Exception as e:
        print(f"\n! ERRO ao processar {cnpj}: {e}")
        fundos_nao_encontrados.append(cnpj)

# Resumo
print("\n" + "="*80)
print("RESUMO:")
print(f"- Fundos encontrados: {len(fundos_encontrados)}")
print(f"- Fundos não encontrados: {len(fundos_nao_encontrados)}")

if fundos_nao_encontrados:
    print(f"\nCNPJs não encontrados no cadastro CVM:")
    for cnpj in fundos_nao_encontrados:
        print(f"  - {cnpj}")

# Salvar resultados
if fundos_encontrados:
    df_resultado = pd.DataFrame(fundos_encontrados)
    arquivo_saida = os.path.join(BASE_DIR, 'fundos_chimborazo_taxas.csv')
    df_resultado.to_csv(arquivo_saida, index=False, encoding='utf-8')
    print(f"\n✓ Resultados salvos em: {arquivo_saida}")

print("\nAnálise concluída!")