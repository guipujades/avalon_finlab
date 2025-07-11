import os
import sys
import pandas as pd
from datetime import datetime

# Adicionar o caminho do flab ao sys.path
sys.path.insert(0, r'C:\Users\guilh\Documents\GitHub\flab')

from carteiras_analysis_utils import processar_carteira_completa, salvar_carteira_serializada

def processar_carteira_mais_recente():
    """
    Processa a carteira do Chimborazo forçando busca pelos dados mais recentes
    """
    CNPJ_CHIMBORAZO = '54.195.596/0001-51'
    NOME_CHIMBORAZO = 'chimborazo'
    BASE_DIR = r"C:\Users\guilh\Documents\GitHub\flab\database"
    
    print("Processando carteira do Chimborazo com dados mais recentes...")
    print("="*80)
    
    # Forçar processamento sem usar cache
    print("\n1. Processando todos os arquivos disponíveis...")
    carteiras = processar_carteira_completa(
        cnpj_fundo=CNPJ_CHIMBORAZO,
        base_dir=BASE_DIR,
        limite_arquivos=None  # Processar TODOS os arquivos
    )
    
    if carteiras:
        print(f"\n2. Datas encontradas: {sorted(carteiras.keys())}")
        data_mais_recente = max(carteiras.keys())
        print(f"\n3. Data mais recente: {data_mais_recente}")
        
        # Salvar dados atualizados
        print("\n4. Salvando dados atualizados...")
        salvar_carteira_serializada(
            carteiras=carteiras,
            nome_fundo=NOME_CHIMBORAZO,
            base_dir=BASE_DIR
        )
        
        # Mostrar resumo da carteira mais recente
        df_carteira = carteiras[data_mais_recente]
        valor_total = df_carteira['VL_MERC_POS_FINAL'].sum()
        
        print(f"\n5. Resumo da carteira em {data_mais_recente}:")
        print(f"   - Número de posições: {len(df_carteira)}")
        print(f"   - Valor total: R$ {valor_total:,.2f}")
        
        # Verificar fundos
        if 'CATEGORIA_ATIVO' in df_carteira.columns:
            df_fundos = df_carteira[df_carteira['CATEGORIA_ATIVO'] == 'Fundos']
            print(f"   - Fundos na carteira: {len(df_fundos.groupby('CNPJ_FUNDO_CLASSE_COTA'))}")
            print(f"   - Valor em fundos: R$ {df_fundos['VL_MERC_POS_FINAL'].sum():,.2f}")
        
        return carteiras
    else:
        print("Erro: Nenhuma carteira encontrada!")
        return None

if __name__ == "__main__":
    carteiras = processar_carteira_mais_recente()