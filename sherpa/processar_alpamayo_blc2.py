import zipfile
import pandas as pd
import os

def processar_alpamayo_fevereiro():
    """
    Processa especificamente o Alpamayo em fevereiro/2025 onde sabemos que tem fundos
    """
    CNPJ_ALPAMAYO = '56.430.872/0001-44'
    arquivo_zip = r"C:\Users\guilh\Documents\GitHub\sherpa\database\CDA\cda_fi_202502.zip"
    
    print("=== PROCESSANDO CARTEIRA DO ALPAMAYO - FEVEREIRO/2025 ===")
    print("="*60)
    
    with zipfile.ZipFile(arquivo_zip, 'r') as zip_ref:
        # Processar BLC_2 que tem os fundos
        blc2_name = 'cda_fi_BLC_2_202502.csv'
        
        print(f"Extraindo e processando {blc2_name}...")
        
        # Extrair para diretório temporário
        temp_dir = "temp_alpamayo"
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            zip_ref.extract(blc2_name, temp_dir)
            arquivo_csv = os.path.join(temp_dir, blc2_name)
            
            # Ler com pandas pulando linhas com erro
            print("Lendo arquivo CSV...")
            df = pd.read_csv(arquivo_csv, sep=';', encoding='latin-1', 
                           on_bad_lines='skip', low_memory=False)
            
            print(f"Total de registros lidos: {len(df)}")
            
            # Filtrar Alpamayo
            df_alpamayo = df[df['CNPJ_FUNDO_CLASSE'] == CNPJ_ALPAMAYO].copy()
            print(f"\nRegistros do Alpamayo: {len(df_alpamayo)}")
            
            if len(df_alpamayo) > 0:
                # Converter valores
                df_alpamayo['VL_MERC_POS_FINAL'] = pd.to_numeric(
                    df_alpamayo['VL_MERC_POS_FINAL'].str.replace(',', '.'), 
                    errors='coerce'
                )
                
                # Filtrar fundos
                fundos = df_alpamayo[df_alpamayo['TP_APLIC'] == 'Cotas de Fundos'].copy()
                
                print(f"\n✓ FUNDOS ENCONTRADOS: {len(fundos)}")
                
                if len(fundos) > 0:
                    # Ordenar por valor
                    fundos = fundos.sort_values('VL_MERC_POS_FINAL', ascending=False)
                    
                    print("\nFUNDOS NA CARTEIRA DO ALPAMAYO:")
                    print("="*100)
                    print(f"{'#':<3} {'Nome do Fundo':<60} {'CNPJ':<20} {'Valor (R$)':>20}")
                    print("-"*100)
                    
                    total_fundos = 0
                    fundos_para_analise = []
                    
                    for i, (_, fundo) in enumerate(fundos.iterrows()):
                        cnpj = fundo['CNPJ_FUNDO_CLASSE_COTA']
                        nome = fundo['NM_FUNDO_CLASSE_SUBCLASSE_COTA']
                        valor = fundo['VL_MERC_POS_FINAL']
                        
                        print(f"{i+1:<3} {nome[:60]:<60} {cnpj:<20} {valor:>20,.2f}")
                        
                        total_fundos += valor
                        fundos_para_analise.append({
                            'cnpj': cnpj,
                            'nome': nome,
                            'valor': valor
                        })
                    
                    print("-"*100)
                    print(f"{'TOTAL':<84} {total_fundos:>20,.2f}")
                    
                    # Análise de taxas
                    print("\n\nANÁLISE DE TAXAS DE ADMINISTRAÇÃO:")
                    print("="*80)
                    
                    # Taxas conhecidas ou estimadas
                    taxas_conhecidas = {
                        '10.407.122/0001-90': 0.0050,  # Stone Index FIM: 0.50%
                        '14.917.907/0001-44': 0.0150,  # Stone Macro Strategy: 1.50%
                        '38.267.696/0001-23': 0.0100,  # Stone Ibovespa Index: 1.00%
                        '25.046.689/0001-10': 0.0025,  # BTG Tesouro IPCA: 0.25%
                        '18.318.213/0001-54': 0.0020,  # Stone Credit: 0.20%
                        '08.838.719/0001-69': 0.0000,  # Tesouro Selic ETF: 0%
                        '35.791.006/0001-06': 0.0000,  # Debentures diretas: 0%
                    }
                    
                    custo_total_anual = 0
                    
                    for fundo in fundos_para_analise:
                        taxa = taxas_conhecidas.get(fundo['cnpj'], 0.005)  # Default 0.5%
                        custo_anual = fundo['valor'] * taxa
                        custo_total_anual += custo_anual
                        
                        print(f"{fundo['nome'][:50]:50} | Taxa: {taxa*100:>5.2f}% | Custo: R$ {custo_anual:>12,.2f}")
                    
                    print("-"*80)
                    print(f"{'CUSTO TOTAL ANUAL DOS FUNDOS DO ALPAMAYO':50} | {'':>11} | R$ {custo_total_anual:>12,.2f}")
                    
                    # Taxa efetiva
                    taxa_efetiva = (custo_total_anual / total_fundos * 100) if total_fundos > 0 else 0
                    print(f"\nTAXA EFETIVA DA CAMADA 2 DO ALPAMAYO: {taxa_efetiva:.3f}%")
                    
                    # Salvar dados
                    df_resultado = pd.DataFrame(fundos_para_analise)
                    df_resultado.to_csv('alpamayo_fundos_fev2025.csv', index=False)
                    print(f"\n✓ Dados salvos em: alpamayo_fundos_fev2025.csv")
                    
        except Exception as e:
            print(f"Erro ao processar: {e}")
            
        finally:
            # Limpar diretório temporário
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

if __name__ == "__main__":
    processar_alpamayo_fevereiro()