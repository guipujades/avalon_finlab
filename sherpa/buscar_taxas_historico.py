import os
import pandas as pd
import numpy as np

# Configurações
BASE_DIR = "/mnt/c/Users/guilh/Documents/GitHub/sherpa/database"

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

print("Buscando taxas no histórico...")
print("="*80)

# Carregar arquivo de histórico de taxas
arquivo_hist = os.path.join(BASE_DIR, 'CAD', 'cad_fi_hist_taxa_adm.csv')
print(f"\nCarregando {arquivo_hist}...")

try:
    df_hist = pd.read_csv(arquivo_hist, 
                          encoding='latin-1', 
                          delimiter=';',
                          dtype={'CNPJ_FUNDO': str, 'TAXA_ADM': str})
    print(f"✓ Arquivo carregado! Total de registros: {len(df_hist)}")
    
    # Converter DT_REG para datetime se existir
    if 'DT_REG' in df_hist.columns:
        df_hist['DT_REG'] = pd.to_datetime(df_hist['DT_REG'], errors='coerce')
    
    print(f"\nColunas disponíveis: {df_hist.columns.tolist()}")
    
except Exception as e:
    print(f"✗ Erro ao carregar: {e}")
    exit(1)

# Buscar taxas para cada CNPJ
print(f"\nBuscando taxas para os fundos do Chimborazo...")
print("-"*80)

resultados = []

for cnpj in cnpjs_chimborazo:
    # Buscar no histórico
    fundos_hist = df_hist[df_hist['CNPJ_FUNDO'] == cnpj]
    
    if not fundos_hist.empty:
        # Pegar o registro mais recente
        if 'DT_REG' in fundos_hist.columns:
            fundo_recente = fundos_hist.sort_values('DT_REG').iloc[-1]
        else:
            fundo_recente = fundos_hist.iloc[-1]
        
        taxa_adm = fundo_recente.get('TAXA_ADM', 'N/A')
        data_reg = fundo_recente.get('DT_REG', 'N/A')
        
        print(f"\n✓ ENCONTRADO: {cnpj}")
        print(f"  Taxa Admin: {taxa_adm}")
        print(f"  Data registro: {data_reg}")
        print(f"  Total de registros históricos: {len(fundos_hist)}")
        
        # Converter taxa para numérico
        try:
            if isinstance(taxa_adm, str):
                taxa_num = float(taxa_adm.replace(',', '.'))
            else:
                taxa_num = float(taxa_adm) if not pd.isna(taxa_adm) else None
        except:
            taxa_num = None
            
        resultados.append({
            'CNPJ': cnpj,
            'Taxa_Adm_Original': taxa_adm,
            'Taxa_Adm_Num': taxa_num,
            'Data_Registro': data_reg,
            'Qtd_Registros': len(fundos_hist)
        })
    else:
        print(f"\n✗ NÃO ENCONTRADO: {cnpj}")

# Resumo
print("\n" + "="*80)
print("RESUMO:")
print(f"- Fundos com taxa encontrada: {len(resultados)}")
print(f"- Fundos sem taxa: {len(cnpjs_chimborazo) - len(resultados)}")

if resultados:
    df_resultado = pd.DataFrame(resultados)
    print(f"\nTaxas encontradas:")
    for _, row in df_resultado.iterrows():
        if row['Taxa_Adm_Num'] is not None:
            print(f"  {row['CNPJ']}: {row['Taxa_Adm_Num']:.2f}%")
        else:
            print(f"  {row['CNPJ']}: {row['Taxa_Adm_Original']} (não numérico)")
    
    # Salvar resultados
    arquivo_saida = os.path.join(BASE_DIR, 'taxas_historico_chimborazo.csv')
    df_resultado.to_csv(arquivo_saida, index=False)
    print(f"\n✓ Resultados salvos em: {arquivo_saida}")

print("\nAnálise concluída!")