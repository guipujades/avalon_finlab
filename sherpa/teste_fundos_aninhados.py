import pandas as pd
import pickle
import os
from carteiras_analysis_utils import processar_carteira_completa

def testar_fundo_aninhado():
    """
    Testa se conseguimos acessar a carteira de um fundo específico
    """
    # Testar com o Alpamayo que sabemos que existe
    cnpj_teste = '56.430.872/0001-44'  # ALPAMAYO
    base_dir = r"C:\Users\guilh\Documents\GitHub\sherpa\database"
    
    print(f"Testando acesso à carteira do fundo: {cnpj_teste}")
    print("="*60)
    
    # Tentar processar carteira
    carteiras = processar_carteira_completa(
        cnpj_fundo=cnpj_teste,
        base_dir=base_dir,
        limite_arquivos=6
    )
    
    if carteiras:
        print(f"\n✓ Carteiras encontradas para as datas: {sorted(carteiras.keys())}")
        
        # Pegar a mais recente
        data_recente = max(carteiras.keys())
        df = carteiras[data_recente]
        
        print(f"\nCarteira de {data_recente}:")
        print(f"Total de registros: {len(df)}")
        
        if 'TP_APLIC' in df.columns:
            print("\nTipos de aplicação:")
            for tp, count in df['TP_APLIC'].value_counts().items():
                print(f"  - {tp}: {count}")
                
        # Verificar se tem fundos
        if 'TP_APLIC' in df.columns:
            fundos = df[df['TP_APLIC'] == 'Cotas de Fundos']
            print(f"\nFundos encontrados: {len(fundos)}")
            
            if len(fundos) > 0:
                print("\nExemplos de fundos aninhados:")
                for i, (_, row) in enumerate(fundos.head(3).iterrows()):
                    nome = row.get('NM_FUNDO_CLASSE_SUBCLASSE_COTA', 'N/A')
                    cnpj = row.get('CNPJ_FUNDO_CLASSE_COTA', 'N/A')
                    print(f"  {i+1}. {cnpj} - {nome}")
    else:
        print("✗ Nenhuma carteira encontrada!")
        
def verificar_todos_fundos_nivel1():
    """
    Verifica quais fundos do Chimborazo têm carteiras disponíveis
    """
    # Carregar carteira do Chimborazo
    caminho_pkl = r"C:\Users\guilh\Documents\GitHub\sherpa\database\serial_carteiras\carteira_chimborazo_completa.pkl"
    
    with open(caminho_pkl, 'rb') as f:
        dados = pickle.load(f)
    
    carteiras = dados['carteira_categorizada']
    df_maio = carteiras['2025-05']
    
    # Converter valores
    df_maio['VL_MERC_POS_FINAL'] = pd.to_numeric(
        df_maio['VL_MERC_POS_FINAL'].astype(str).str.replace(',', '.'), 
        errors='coerce'
    )
    
    # Pegar fundos
    fundos = df_maio[df_maio['TP_APLIC'] == 'Cotas de Fundos']
    
    print("VERIFICANDO DISPONIBILIDADE DE CARTEIRAS DOS FUNDOS DO CHIMBORAZO")
    print("="*80)
    
    base_dir = r"C:\Users\guilh\Documents\GitHub\sherpa\database"
    
    for _, fundo in fundos.iterrows():
        cnpj = fundo['CNPJ_FUNDO_CLASSE_COTA']
        nome = fundo['NM_FUNDO_CLASSE_SUBCLASSE_COTA']
        valor = fundo['VL_MERC_POS_FINAL']
        
        print(f"\n{nome}")
        print(f"CNPJ: {cnpj} | Valor: R$ {valor:,.2f}")
        
        # Verificar se tem carteira
        carteiras = processar_carteira_completa(
            cnpj_fundo=cnpj,
            base_dir=base_dir,
            limite_arquivos=12
        )
        
        if carteiras:
            datas = sorted(carteiras.keys())
            print(f"✓ Carteiras disponíveis: {datas[-3:]}...")  # Mostrar últimas 3 datas
            
            # Verificar a mais recente
            data_recente = max(datas)
            df_fundo = carteiras[data_recente]
            
            if 'TP_APLIC' in df_fundo.columns:
                fundos_aninhados = df_fundo[df_fundo['TP_APLIC'] == 'Cotas de Fundos']
                print(f"  → {len(fundos_aninhados)} fundos aninhados em {data_recente}")
        else:
            print("✗ Nenhuma carteira disponível")

if __name__ == "__main__":
    # Primeiro teste com um fundo específico
    testar_fundo_aninhado()
    
    print("\n\n" + "="*80 + "\n")
    
    # Depois verificar todos
    verificar_todos_fundos_nivel1()