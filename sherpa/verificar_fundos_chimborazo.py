import pandas as pd
import pickle
import os

def verificar_dados_chimborazo():
    """
    Verifica os dados serializados do Chimborazo e mostra o que está sendo capturado
    """
    # Carregar dados serializados
    caminho_serial = "/mnt/c/Users/guilh/Documents/GitHub/sherpa/database/serial_carteiras/carteira_chimborazo.pkl"
    
    with open(caminho_serial, 'rb') as f:
        dados = pickle.load(f)
    
    carteiras = dados.get('carteira_categorizada', {})
    
    # Pegar a data mais recente
    data_mais_recente = max(carteiras.keys())
    df = carteiras[data_mais_recente]
    
    print(f"Analisando dados de {data_mais_recente}")
    print(f"Total de registros: {len(df)}")
    print(f"\nColunas disponíveis: {df.columns.tolist()}")
    
    # Verificar valores únicos de TP_APLIC
    if 'TP_APLIC' in df.columns:
        print("\nValores únicos de TP_APLIC:")
        for tp in df['TP_APLIC'].unique():
            count = len(df[df['TP_APLIC'] == tp])
            print(f"  - {tp}: {count} registros")
    
    # Verificar se existem fundos
    print("\n\nVERIFICANDO FUNDOS:")
    
    # Método 1: Por TP_APLIC
    if 'TP_APLIC' in df.columns:
        fundos_tp_aplic = df[df['TP_APLIC'] == 'Cotas de Fundos']
        print(f"\nFundos por TP_APLIC='Cotas de Fundos': {len(fundos_tp_aplic)}")
        if len(fundos_tp_aplic) > 0:
            print("Primeiros 5 fundos:")
            for i, (idx, row) in enumerate(fundos_tp_aplic.head().iterrows()):
                nome = row.get('NM_FUNDO_CLASSE_SUBCLASSE_COTA', row.get('DS_ATIVO', 'Nome não encontrado'))
                valor = row.get('VL_MERC_POS_FINAL', 0)
                print(f"  {i+1}. {nome}: R$ {valor:,.2f}")
    
    # Método 2: Por TP_ATIVO
    if 'TP_ATIVO' in df.columns:
        print("\nValores únicos de TP_ATIVO:")
        for tp in df['TP_ATIVO'].unique():
            count = len(df[df['TP_ATIVO'] == tp])
            print(f"  - {tp}: {count} registros")
    
    # Método 3: Por CNPJ_FUNDO_CLASSE_COTA
    if 'CNPJ_FUNDO_CLASSE_COTA' in df.columns:
        fundos_cnpj = df[df['CNPJ_FUNDO_CLASSE_COTA'].notna()]
        print(f"\nFundos com CNPJ_FUNDO_CLASSE_COTA preenchido: {len(fundos_cnpj)}")
    
    # Verificar total investido
    if 'VL_MERC_POS_FINAL' in df.columns:
        total_carteira = df['VL_MERC_POS_FINAL'].sum()
        print(f"\nValor total da carteira: R$ {total_carteira:,.2f}")
        
        if 'TP_APLIC' in df.columns:
            # Agrupar por TP_APLIC
            resumo = df.groupby('TP_APLIC')['VL_MERC_POS_FINAL'].sum().sort_values(ascending=False)
            print("\nResumo por TP_APLIC:")
            for tp, valor in resumo.items():
                pct = (valor / total_carteira * 100) if total_carteira > 0 else 0
                print(f"  - {tp}: R$ {valor:,.2f} ({pct:.2f}%)")

def carregar_carteira_completa():
    """
    Carrega os dados brutos da carteira para análise
    """
    from carteiras_analysis_utils import processar_carteira_completa
    
    CNPJ_CHIMBORAZO = '54.195.596/0001-51'
    BASE_DIR = r"C:\Users\guilh\Documents\GitHub\sherpa\database"
    
    print("\nReprocessando carteira completa (últimos 6 meses)...")
    
    carteiras = processar_carteira_completa(
        cnpj_fundo=CNPJ_CHIMBORAZO,
        base_dir=BASE_DIR,
        limite_arquivos=6
    )
    
    if carteiras:
        # Pegar a data mais recente
        data_mais_recente = max(carteiras.keys())
        df = carteiras[data_mais_recente]
        
        print(f"\nDados brutos de {data_mais_recente}:")
        print(f"Total de registros: {len(df)}")
        
        # Salvar amostra para análise
        amostra = df.head(20)
        amostra.to_csv('amostra_chimborazo.csv', index=False)
        print("\nAmostra salva em 'amostra_chimborazo.csv'")
        
        # Verificar fundos nos dados brutos
        if 'TP_APLIC' in df.columns:
            fundos = df[df['TP_APLIC'] == 'Cotas de Fundos']
            print(f"\nFundos encontrados nos dados brutos: {len(fundos)}")
            
            if len(fundos) > 0:
                print("\nPrimeiros 10 fundos:")
                for i, (idx, row) in enumerate(fundos.head(10).iterrows()):
                    cnpj = row.get('CNPJ_FUNDO_CLASSE_COTA', 'N/A')
                    nome = row.get('NM_FUNDO_CLASSE_SUBCLASSE_COTA', row.get('DS_ATIVO', 'N/A'))
                    valor = row.get('VL_MERC_POS_FINAL', 0)
                    print(f"  {i+1}. {cnpj} - {nome}: R$ {valor:,.2f}")
                
                # Salvar dados completos com fundos
                fundos.to_excel('fundos_chimborazo_completo.xlsx', index=False)
                print(f"\nDados completos dos fundos salvos em 'fundos_chimborazo_completo.xlsx'")

if __name__ == "__main__":
    print("=== VERIFICAÇÃO DE DADOS DO CHIMBORAZO ===\n")
    
    # Verificar dados serializados atuais
    verificar_dados_chimborazo()
    
    # Carregar dados brutos para comparação
    print("\n" + "="*60)
    carregar_carteira_completa()