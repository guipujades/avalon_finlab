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

def analisar_camada2_diagnostico():
    """
    Versão de diagnóstico para entender porque não conseguimos dados
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
    
    print("=== DIAGNÓSTICO DETALHADO - CAMADA 2 ===")
    print("="*80)
    
    resultados_diagnostico = []
    fundos_sem_dados = []
    
    # Processar cada fundo
    for fundo_c1 in fundos_chimborazo:
        print(f"\n\n{'='*80}")
        print(f"ANALISANDO: {fundo_c1['nome']}")
        print(f"CNPJ: {fundo_c1['cnpj']}")
        print("-"*80)
        
        carteira_encontrada = False
        historico_busca = []
        
        # Tentar vários meses (mais recente primeiro)
        meses = ['202505', '202504', '202503', '202502', '202501', '202412', '202411', '202410']
        
        for mes in meses:
            arquivo_zip = BASE_DIR / 'CDA' / f'cda_fi_{mes}.zip'
            
            if not arquivo_zip.exists():
                historico_busca.append(f"{mes}: Arquivo não existe")
                continue
                
            try:
                # Tentar processar o BLC_2
                df_fundo = processar_blc2_com_tratamento_erro(str(arquivo_zip), fundo_c1['cnpj'])
                
                if df_fundo is not None and len(df_fundo) > 0:
                    # Verificar tipos de aplicação
                    tipos_aplic = df_fundo['TP_APLIC'].value_counts()
                    historico_busca.append(f"{mes}: {len(df_fundo)} registros encontrados")
                    
                    # Filtrar fundos
                    fundos_aninhados = df_fundo[df_fundo['TP_APLIC'] == 'Cotas de Fundos'].copy()
                    
                    if len(fundos_aninhados) > 0:
                        print(f"\n✓ CARTEIRA ENCONTRADA EM {mes[:4]}-{mes[4:]} com {len(fundos_aninhados)} fundos")
                        carteira_encontrada = True
                        
                        # Listar fundos sem taxas conhecidas
                        fundos_sem_taxa = []
                        
                        for _, f2 in fundos_aninhados.iterrows():
                            cnpj_f2 = f2['CNPJ_FUNDO_CLASSE_COTA']
                            nome_f2 = f2['NM_FUNDO_CLASSE_SUBCLASSE_COTA']
                            
                            # Verificar se temos taxa
                            taxas_conhecidas = ['10.407.122/0001-90', '14.917.907/0001-44', 
                                              '38.267.696/0001-23', '18.318.213/0001-54',
                                              '08.838.719/0001-69', '25.046.689/0001-10',
                                              '35.791.006/0001-06']
                            
                            if cnpj_f2 not in taxas_conhecidas:
                                fundos_sem_taxa.append({
                                    'cnpj': cnpj_f2,
                                    'nome': nome_f2
                                })
                        
                        if fundos_sem_taxa:
                            print(f"\nFUNDOS SEM TAXA CONHECIDA ({len(fundos_sem_taxa)}):")
                            for fst in fundos_sem_taxa:
                                print(f"  - {fst['nome']} (CNPJ: {fst['cnpj']})")
                        
                        break
                else:
                    if df_fundo is not None:
                        historico_busca.append(f"{mes}: Sem fundos na carteira")
                    else:
                        historico_busca.append(f"{mes}: Sem dados para este CNPJ")
                        
            except Exception as e:
                historico_busca.append(f"{mes}: Erro - {str(e)[:50]}")
        
        # Resumo do diagnóstico
        print(f"\nHISTÓRICO DE BUSCA:")
        for hist in historico_busca:
            print(f"  {hist}")
        
        if not carteira_encontrada:
            print("\n✗ NENHUMA CARTEIRA COM FUNDOS ENCONTRADA")
            
            # Verificar tipo do fundo
            nome_upper = fundo_c1['nome'].upper()
            if 'PRIVATE EQUITY' in nome_upper or 'FIP' in nome_upper:
                print("→ Tipo: Private Equity - Normal não ter carteira detalhada")
                print("→ Usar estimativa de 1.8% para taxa de administração")
            elif 'FIDC' in nome_upper:
                print("→ Tipo: FIDC - Normal não ter carteira detalhada") 
                print("→ Usar estimativa de 1.0% para taxa de administração")
            else:
                print("→ ATENÇÃO: Fundo comum sem dados de carteira!")
                fundos_sem_dados.append(fundo_c1)
    
    # Resumo final
    print(f"\n\n{'='*80}")
    print("RESUMO DO DIAGNÓSTICO")
    print("="*80)
    
    if fundos_sem_dados:
        print(f"\nFUNDOS COMUNS SEM DADOS DE CARTEIRA ({len(fundos_sem_dados)}):")
        for fsd in fundos_sem_dados:
            print(f"  - {fsd['nome']} (CNPJ: {fsd['cnpj']})")
        print("\nEsses fundos deveriam ter carteiras reportadas mas não encontramos dados.")
    else:
        print("\n✓ Todos os fundos comuns têm dados ou são PE/FIDC (esperado não ter carteira detalhada)")

if __name__ == "__main__":
    analisar_camada2_diagnostico()