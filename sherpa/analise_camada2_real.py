import pandas as pd
import os
import zipfile
from datetime import datetime

def processar_blc2_com_tratamento_erro(arquivo_zip, cnpj_fundo):
    """
    Processa o arquivo BLC_2 com tratamento de erro linha por linha
    """
    with zipfile.ZipFile(arquivo_zip, 'r') as zip_ref:
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

def analisar_camada2_completa():
    """
    Analisa a camada 2 com dados REAIS dos fundos aninhados
    """
    from pathlib import Path
    home = Path.home()
    BASE_DIR = Path(home, 'Documents', 'GitHub', 'sherpa', 'database')
    
    # Fundos do Chimborazo (Camada 1)
    fundos_chimborazo = [
        {'cnpj': '56.430.872/0001-44', 'nome': 'ALPAMAYO', 'valor': 17_244_736.89, 'taxa_c1': 0.0004},
        {'cnpj': '12.809.201/0001-13', 'nome': 'CAPSTONE MACRO A', 'valor': 26_862_668.12, 'taxa_c1': 0.019},
        {'cnpj': '41.287.689/0001-64', 'nome': 'ITAÚ DOLOMITAS', 'valor': 27_225_653.63, 'taxa_c1': 0.0006},
        {'cnpj': '18.138.913/0001-34', 'nome': 'ITAÚ VÉRTICE COMPROMISSO', 'valor': 12_917_838.67, 'taxa_c1': 0.0015},
        {'cnpj': '14.096.710/0001-71', 'nome': 'ITAÚ VÉRTICE IBOVESPA', 'valor': 15_957_765.48, 'taxa_c1': 0.0},
        {'cnpj': '55.419.784/0001-89', 'nome': 'ITAÚ CAIXA AÇÕES', 'valor': 13_853_061.98, 'taxa_c1': 0.0},
        {'cnpj': '32.311.914/0001-60', 'nome': 'VINCI CAPITAL PARTNERS III FIP', 'valor': 11_380_404.94, 'taxa_c1': 0.0},
        {'cnpj': '41.535.122/0001-60', 'nome': 'KINEA PRIVATE EQUITY V', 'valor': 11_180_663.91, 'taxa_c1': 0.0},
        {'cnpj': '12.138.862/0001-64', 'nome': 'SILVERADO MAXIMUM II FIDC', 'valor': 10_669_862.09, 'taxa_c1': 0.0},
    ]
    
    print("=== ANÁLISE REAL DA CAMADA 2 - FUNDOS ANINHADOS ===")
    print("="*80)
    
    resultados_camada2 = []
    
    # Processar cada fundo
    for fundo_c1 in fundos_chimborazo:
        print(f"\n\n{'='*80}")
        print(f"ANALISANDO: {fundo_c1['nome']}")
        print(f"CNPJ: {fundo_c1['cnpj']} | Valor no Chimborazo: R$ {fundo_c1['valor']:,.2f}")
        print(f"Taxa Camada 1: {fundo_c1['taxa_c1']*100:.2f}%")
        print("-"*80)
        
        carteira_encontrada = False
        
        # Tentar vários meses (mais recente primeiro)
        meses = ['202505', '202504', '202503', '202502', '202501', '202412']
        
        for mes in meses:
            arquivo_zip = BASE_DIR / 'CDA' / f'cda_fi_{mes}.zip'
            
            if not arquivo_zip.exists():
                continue
                
            try:
                # Tentar processar o BLC_2
                df_fundo = processar_blc2_com_tratamento_erro(str(arquivo_zip), fundo_c1['cnpj'])
                
                if df_fundo is not None and len(df_fundo) > 0:
                    # Filtrar fundos
                    fundos_aninhados = df_fundo[df_fundo['TP_APLIC'] == 'Cotas de Fundos'].copy()
                    
                    if len(fundos_aninhados) > 0:
                        print(f"\n✓ CARTEIRA ENCONTRADA EM {mes[:4]}-{mes[4:]} com {len(fundos_aninhados)} fundos")
                        carteira_encontrada = True
                        
                        # Converter valores
                        fundos_aninhados['VL_MERC_POS_FINAL'] = pd.to_numeric(
                            fundos_aninhados['VL_MERC_POS_FINAL'].str.replace(',', '.'), 
                            errors='coerce'
                        )
                        
                        # Calcular total do fundo
                        total_fundo = df_fundo['VL_MERC_POS_FINAL'].astype(str).str.replace(',', '.').astype(float).sum()
                        
                        print("\nFundos aninhados encontrados:")
                        print("-"*100)
                        
                        custo_c2_fundo = 0
                        
                        for _, f2 in fundos_aninhados.iterrows():
                            cnpj_f2 = f2['CNPJ_FUNDO_CLASSE_COTA']
                            nome_f2 = f2['NM_FUNDO_CLASSE_SUBCLASSE_COTA']
                            valor_f2 = f2['VL_MERC_POS_FINAL']
                            peso_no_fundo = valor_f2 / total_fundo if total_fundo > 0 else 0
                            valor_efetivo = fundo_c1['valor'] * peso_no_fundo
                            
                            # Buscar taxa real
                            taxa_f2 = obter_taxa_fundo_aninhado(cnpj_f2, nome_f2)
                            
                            if taxa_f2['taxa'] is not None:
                                custo_anual = valor_efetivo * taxa_f2['taxa']
                                custo_c2_fundo += custo_anual
                                
                                print(f"{nome_f2[:50]:50} | Peso: {peso_no_fundo*100:>5.1f}% | Taxa: {taxa_f2['taxa']*100:>5.2f}% ({taxa_f2['fonte']}) | Custo: R$ {custo_anual:>10,.2f}")
                                
                                resultados_camada2.append({
                                    'fundo_c1': fundo_c1['nome'],
                                    'fundo_c2': nome_f2,
                                    'cnpj_c2': cnpj_f2,
                                    'valor_efetivo': valor_efetivo,
                                    'taxa': taxa_f2['taxa'],
                                    'fonte_taxa': taxa_f2['fonte'],
                                    'custo_anual': custo_anual,
                                    'data_carteira': f"{mes[:4]}-{mes[4:]}"
                                })
                            else:
                                print(f"{nome_f2[:50]:50} | Peso: {peso_no_fundo*100:>5.1f}% | Taxa: ??? (SEM DADOS) | CNPJ: {cnpj_f2}")
                                
                                resultados_camada2.append({
                                    'fundo_c1': fundo_c1['nome'],
                                    'fundo_c2': nome_f2,
                                    'cnpj_c2': cnpj_f2,
                                    'valor_efetivo': valor_efetivo,
                                    'taxa': 0,
                                    'fonte_taxa': 'SEM DADOS',
                                    'custo_anual': 0,
                                    'data_carteira': f"{mes[:4]}-{mes[4:]}"
                                })
                        
                        print("-"*100)
                        print(f"CUSTO TOTAL CAMADA 2 para {fundo_c1['nome']}: R$ {custo_c2_fundo:,.2f}")
                        break
                        
            except Exception as e:
                continue
        
        if not carteira_encontrada:
            print("\n✗ CARTEIRA NÃO ENCONTRADA - Usando estimativa")
            
            # Estimativas por tipo de fundo
            if 'PRIVATE EQUITY' in fundo_c1['nome'] or 'FIP' in fundo_c1['nome']:
                taxa_est = 0.018  # 1.8% para PE
                fonte = 'ESTIMATIVA PE'
            elif 'FIDC' in fundo_c1['nome']:
                taxa_est = 0.01  # 1% para FIDC
                fonte = 'ESTIMATIVA FIDC'
            else:
                taxa_est = 0
                fonte = 'SEM ESTIMATIVA'
            
            if taxa_est > 0:
                custo_est = fundo_c1['valor'] * taxa_est
                print(f"Taxa estimada: {taxa_est*100:.2f}% ({fonte})")
                print(f"Custo estimado: R$ {custo_est:,.2f}")
                
                resultados_camada2.append({
                    'fundo_c1': fundo_c1['nome'],
                    'fundo_c2': 'Carteira não disponível',
                    'cnpj_c2': 'N/A',
                    'valor_efetivo': fundo_c1['valor'],
                    'taxa': taxa_est,
                    'fonte_taxa': fonte,
                    'custo_anual': custo_est,
                    'data_carteira': 'N/A'
                })
    
    # Resumo final
    print(f"\n\n{'='*80}")
    print("RESUMO DA CAMADA 2")
    print("="*80)
    
    df_resultado = pd.DataFrame(resultados_camada2)
    
    # Agrupar por fonte
    print("\nCustos por tipo de fonte:")
    for fonte in df_resultado['fonte_taxa'].unique():
        custos_fonte = df_resultado[df_resultado['fonte_taxa'] == fonte]['custo_anual'].sum()
        print(f"  {fonte:20} R$ {custos_fonte:>15,.2f}")
    
    custo_total_c2 = df_resultado['custo_anual'].sum()
    print(f"\nCUSTO TOTAL CAMADA 2: R$ {custo_total_c2:,.2f}")
    
    # Salvar resultados
    df_resultado.to_excel('camada2_detalhada.xlsx', index=False)
    print(f"\n✓ Resultados salvos em: camada2_detalhada.xlsx")
    
    return df_resultado

def obter_taxa_fundo_aninhado(cnpj, nome):
    """
    Obtém a taxa de um fundo aninhado - APENAS taxas REAIS conhecidas
    """
    # Taxas REAIS conhecidas (confirmadas)
    taxas_conhecidas = {
        # Fundos Stone (do Alpamayo)
        '10.407.122/0001-90': {'taxa': 0.0050, 'fonte': 'REAL'},  # Stone Index
        '14.917.907/0001-44': {'taxa': 0.0150, 'fonte': 'REAL'},  # Stone Macro
        '38.267.696/0001-23': {'taxa': 0.0100, 'fonte': 'REAL'},  # Stone Ibovespa
        '18.318.213/0001-54': {'taxa': 0.0020, 'fonte': 'REAL'},  # Stone Credit
        
        # ETFs e Tesouro
        '08.838.719/0001-69': {'taxa': 0.0000, 'fonte': 'REAL'},  # Tesouro Selic ETF
        '25.046.689/0001-10': {'taxa': 0.0025, 'fonte': 'REAL'},  # BTG Tesouro IPCA
        
        # Outros conhecidos
        '35.791.006/0001-06': {'taxa': 0.0000, 'fonte': 'REAL'},  # Debêntures diretas
    }
    
    # Se temos a taxa real
    if cnpj in taxas_conhecidas:
        return taxas_conhecidas[cnpj]
    
    # Sem fallback - retornar None para indicar que não temos dados
    return {'taxa': None, 'fonte': 'SEM DADOS', 'nome': nome, 'cnpj': cnpj}

if __name__ == "__main__":
    df_camada2 = analisar_camada2_completa()