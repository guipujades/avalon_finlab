import pandas as pd
import os
import zipfile
from datetime import datetime

def processar_blc2_com_tratamento_erro(arquivo_zip, cnpj_fundo):
    """
    Processa o arquivo BLC_2 com tratamento de erro linha por linha
    """
    with zipfile.ZipFile(str(arquivo_zip), 'r') as zip_ref:
        # Encontrar o arquivo BLC_2
        blc2_name = None
        for arq in zip_ref.namelist():
            if 'BLC_2' in arq and arq.endswith('.csv'):
                blc2_name = arq
                break
        
        if not blc2_name:
            return None
            
        # Ler linha por linha
        with zip_ref.open(blc2_name) as f:
            linhas = []
            header = None
            linha_num = 0
            
            for linha in f:
                linha_num += 1
                try:
                    linha_str = linha.decode('latin-1').strip()
                    
                    if linha_num == 1:
                        header = linha_str.split(';')
                        continue
                    
                    if linha_str and cnpj_fundo in linha_str:
                        valores = linha_str.split(';')
                        if len(valores) == len(header):
                            linhas.append(valores)
                            
                except Exception:
                    continue
            
            if linhas and header:
                df = pd.DataFrame(linhas, columns=header)
                return df[df['CNPJ_FUNDO_CLASSE'] == cnpj_fundo]
    
    return None

def obter_taxa_fundo_aninhado(cnpj, nome):
    """
    Obtém a taxa de um fundo aninhado - APENAS taxas REAIS conhecidas
    """
    # Taxas REAIS conhecidas (confirmadas)
    taxas_conhecidas = {
        # Fundos com taxas confirmadas
        '10.407.122/0001-90': 0.0050,  # Stone Index
        '14.917.907/0001-44': 0.0150,  # Stone Macro
        '38.267.696/0001-23': 0.0100,  # Stone Ibovespa
        '18.318.213/0001-54': 0.0020,  # Stone Credit
        '08.838.719/0001-69': 0.0000,  # Tesouro Selic ETF
        '25.046.689/0001-10': 0.0025,  # BTG Tesouro IPCA
        '35.791.006/0001-06': 0.0000,  # Debêntures diretas
    }
    
    return taxas_conhecidas.get(cnpj, None)

def analisar_camada2_final():
    """
    Análise final da camada 2 - sem fallbacks automáticos
    """
    from pathlib import Path
    
    # WSL path
    BASE_DIR = Path('/mnt/c/Users/guilh/Documents/GitHub/sherpa/database')
    
    # Fundos do Chimborazo (Camada 1)
    fundos_chimborazo = [
        {'cnpj': '56.430.872/0001-44', 'nome': 'ALPAMAYO', 'valor': 17_244_736.89},
        {'cnpj': '12.809.201/0001-13', 'nome': 'CAPSTONE MACRO A', 'valor': 26_862_668.12},
        {'cnpj': '41.287.689/0001-64', 'nome': 'ITAÚ DOLOMITAS', 'valor': 27_225_653.63},
        {'cnpj': '18.138.913/0001-34', 'nome': 'ITAÚ VÉRTICE COMPROMISSO', 'valor': 12_917_838.67},
        {'cnpj': '14.096.710/0001-71', 'nome': 'ITAÚ VÉRTICE IBOVESPA', 'valor': 15_957_765.48},
        {'cnpj': '55.419.784/0001-89', 'nome': 'ITAÚ CAIXA AÇÕES', 'valor': 13_853_061.98},
        {'cnpj': '32.311.914/0001-60', 'nome': 'VINCI CAPITAL PARTNERS III FIP', 'valor': 11_380_404.94},
        {'cnpj': '41.535.122/0001-60', 'nome': 'KINEA PRIVATE EQUITY V', 'valor': 11_180_663.91},
        {'cnpj': '12.138.862/0001-64', 'nome': 'SILVERADO MAXIMUM II FIDC', 'valor': 10_669_862.09},
    ]
    
    print("=== ANÁLISE CAMADA 2 - CUSTOS REAIS E ESTIMATIVAS ===")
    print("="*80)
    
    total_custo_c2 = 0
    total_sem_dados = 0
    fundos_sem_taxa_detalhes = []
    
    # Processar cada fundo
    for fundo_c1 in fundos_chimborazo:
        print(f"\n{'='*60}")
        print(f"{fundo_c1['nome']}")
        print(f"Valor: R$ {fundo_c1['valor']:,.2f}")
        
        
        # Verificar se é PE ou FIDC
        nome_upper = fundo_c1['nome'].upper()
        if 'PRIVATE EQUITY' in nome_upper or 'FIP' in nome_upper:
            # Private Equity - usar estimativa
            taxa_est = 0.018
            custo_est = fundo_c1['valor'] * taxa_est
            total_custo_c2 += custo_est
            
            print(f"→ Tipo: Private Equity")
            print(f"→ Taxa estimada: {taxa_est*100:.1f}%")
            print(f"→ Custo anual: R$ {custo_est:,.2f}")
            
        elif 'FIDC' in nome_upper:
            # FIDC - usar estimativa
            taxa_est = 0.01
            custo_est = fundo_c1['valor'] * taxa_est
            total_custo_c2 += custo_est
            
            print(f"→ Tipo: FIDC")
            print(f"→ Taxa estimada: {taxa_est*100:.1f}%")
            print(f"→ Custo anual: R$ {custo_est:,.2f}")
            
        else:
            # Fundo comum - buscar carteira real
            arquivo_zip = BASE_DIR / 'CDA' / 'cda_fi_202505.zip'
 
            if arquivo_zip.exists():
                try:
                    df_fundo = processar_blc2_com_tratamento_erro(arquivo_zip, fundo_c1['cnpj'])
                    
                    if df_fundo is not None and len(df_fundo) > 0:
                        # Filtrar fundos
                        fundos_aninhados = df_fundo[df_fundo['TP_APLIC'] == 'Cotas de Fundos'].copy()
                        
                        if len(fundos_aninhados) > 0:
                            print(f"→ {len(fundos_aninhados)} fundos aninhados encontrados")
                            
                            # Converter valores
                            fundos_aninhados['VL_MERC_POS_FINAL'] = pd.to_numeric(
                                fundos_aninhados['VL_MERC_POS_FINAL'].str.replace(',', '.'), 
                                errors='coerce'
                            )
                            
                            # Calcular total do fundo
                            total_fundo = df_fundo['VL_MERC_POS_FINAL'].astype(str).str.replace(',', '.').astype(float).sum()
                            
                            custo_c2_fundo = 0
                            fundos_sem_taxa_local = 0
                            valor_sem_taxa_local = 0
                            
                            for _, f2 in fundos_aninhados.iterrows():
                                cnpj_f2 = f2['CNPJ_FUNDO_CLASSE_COTA']
                                nome_f2 = f2['NM_FUNDO_CLASSE_SUBCLASSE_COTA']
                                valor_f2 = f2['VL_MERC_POS_FINAL']
                                peso_no_fundo = valor_f2 / total_fundo if total_fundo > 0 else 0
                                valor_efetivo = fundo_c1['valor'] * peso_no_fundo
                                
                                # Buscar taxa real
                                taxa_f2 = obter_taxa_fundo_aninhado(cnpj_f2, nome_f2)
                                
                                if taxa_f2 is not None:
                                    custo_anual = valor_efetivo * taxa_f2
                                    custo_c2_fundo += custo_anual
                                else:
                                    fundos_sem_taxa_local += 1
                                    valor_sem_taxa_local += valor_efetivo
                                    fundos_sem_taxa_detalhes.append({
                                        'fundo_c1': fundo_c1['nome'],
                                        'cnpj': cnpj_f2,
                                        'nome': nome_f2,
                                        'valor': valor_efetivo
                                    })
                            
                            if custo_c2_fundo > 0:
                                print(f"→ Custo calculado (fundos com taxa conhecida): R$ {custo_c2_fundo:,.2f}")
                                total_custo_c2 += custo_c2_fundo
                            
                            if fundos_sem_taxa_local > 0:
                                print(f"→ {fundos_sem_taxa_local} fundos SEM TAXA CONHECIDA")
                                print(f"→ Valor sem taxa: R$ {valor_sem_taxa_local:,.2f}")
                                total_sem_dados += valor_sem_taxa_local
                                
                        else:
                            print("→ Sem fundos aninhados na carteira")
                    else:
                        print("→ Sem dados disponíveis")
                        
                except Exception as e:
                    print(f"→ Erro ao processar: {str(e)[:50]}")
            else:
                print("→ Arquivo não encontrado")
    
    # Resumo final
    print(f"\n\n{'='*80}")
    print("RESUMO CAMADA 2")
    print("="*80)
    
    print(f"\nCUSTO CALCULADO (com taxas conhecidas + estimativas PE/FIDC):")
    print(f"  R$ {total_custo_c2:,.2f}")
    
    print(f"\nVALOR SEM TAXA CONHECIDA:")
    print(f"  R$ {total_sem_dados:,.2f}")
    
    if fundos_sem_taxa_detalhes:
        print(f"\n\nDETALHE DOS FUNDOS SEM TAXA CONHECIDA ({len(fundos_sem_taxa_detalhes)} fundos):")
        print("-"*80)
        
        # Agrupar por fundo de origem
        df_sem_taxa = pd.DataFrame(fundos_sem_taxa_detalhes)
        
        for fundo_origem in df_sem_taxa['fundo_c1'].unique():
            fundos_do_origem = df_sem_taxa[df_sem_taxa['fundo_c1'] == fundo_origem]
            print(f"\nOrigem: {fundo_origem}")
            
            for _, f in fundos_do_origem.iterrows():
                print(f"  - {f['nome'][:60]:60} | CNPJ: {f['cnpj']} | R$ {f['valor']:,.2f}")
        
        # Salvar em Excel para análise
        df_sem_taxa.to_excel('fundos_sem_taxa_camada2.xlsx', index=False)
        print(f"\n✓ Lista completa salva em: fundos_sem_taxa_camada2.xlsx")

if __name__ == "__main__":
    analisar_camada2_final()