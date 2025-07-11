"""
Análise detalhada da Camada 2 - identificando fundos e suas taxas
"""

from pathlib import Path
import pandas as pd
import zipfile

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

def buscar_taxa_cadastro_cvm(cnpj):
    """
    Busca taxa de administração no cadastro CVM
    """
    # Aqui você pode implementar busca no cadastro
    # Por enquanto vamos usar as taxas conhecidas
    taxas_conhecidas = {
        # Fundos conhecidos
        '16.478.741/0001-12': 0.020,  # Squadra Long-Only - estimativa
        '24.546.223/0001-17': 0.004,  # Itaú Vértice Ibovespa Equities
        '07.096.546/0001-37': 0.000,  # Itaú Caixa Ações
        '21.407.105/0001-30': 0.003,  # Itaú Vértice RF DI
        '35.823.433/0001-21': 0.000,  # Itaú Zeragem
        '12.808.980/0001-32': 0.020,  # SPX Raptor Master
        # Adicione mais conforme encontrar
    }
    return taxas_conhecidas.get(cnpj, None)

def analisar_camada2_detalhada():
    """
    Análise detalhada mostrando cada fundo e sua situação
    """
    # WSL path
    BASE_DIR = Path('/mnt/c/Users/guilh/Documents/GitHub/sherpa/database')
    
    # Fundos do Chimborazo
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
    
    print("=== ANÁLISE DETALHADA DA CAMADA 2 ===")
    print("="*80)
    
    total_custo_c2 = 0
    resumo_fundos = []
    
    for fundo_c1 in fundos_chimborazo:
        print(f"\n{'='*60}")
        print(f"{fundo_c1['nome']}")
        print(f"Valor no Chimborazo: R$ {fundo_c1['valor']:,.2f}")
        
        nome_upper = fundo_c1['nome'].upper()
        
        # Verificar se é PE ou FIDC
        if 'PRIVATE EQUITY' in nome_upper or 'FIP' in nome_upper:
            taxa_est = 0.018
            custo_est = fundo_c1['valor'] * taxa_est
            total_custo_c2 += custo_est
            
            print(f"→ Tipo: Private Equity")
            print(f"→ Não reporta carteira detalhada à CVM")
            print(f"→ Taxa estimada: {taxa_est*100:.1f}%")
            print(f"→ Custo anual: R$ {custo_est:,.2f}")
            
            resumo_fundos.append({
                'origem': fundo_c1['nome'],
                'tipo': 'PE',
                'status': 'Estimativa aplicada',
                'custo': custo_est
            })
            
        elif 'FIDC' in nome_upper:
            taxa_est = 0.01
            custo_est = fundo_c1['valor'] * taxa_est
            total_custo_c2 += custo_est
            
            print(f"→ Tipo: FIDC")
            print(f"→ Não reporta carteira detalhada à CVM")
            print(f"→ Taxa estimada: {taxa_est*100:.1f}%")
            print(f"→ Custo anual: R$ {custo_est:,.2f}")
            
            resumo_fundos.append({
                'origem': fundo_c1['nome'],
                'tipo': 'FIDC',
                'status': 'Estimativa aplicada',
                'custo': custo_est
            })
            
        else:
            # Fundo comum - buscar carteira
            arquivo_zip = BASE_DIR / 'CDA' / 'cda_fi_202505.zip'
            
            if arquivo_zip.exists():
                try:
                    df_fundo = processar_blc2_com_tratamento_erro(arquivo_zip, fundo_c1['cnpj'])
                    
                    if df_fundo is not None and len(df_fundo) > 0:
                        fundos_aninhados = df_fundo[df_fundo['TP_APLIC'] == 'Cotas de Fundos'].copy()
                        
                        if len(fundos_aninhados) > 0:
                            print(f"→ Carteira com {len(fundos_aninhados)} fundos")
                            
                            # Converter valores
                            fundos_aninhados['VL_MERC_POS_FINAL'] = pd.to_numeric(
                                fundos_aninhados['VL_MERC_POS_FINAL'].str.replace(',', '.'), 
                                errors='coerce'
                            )
                            
                            total_fundo = df_fundo['VL_MERC_POS_FINAL'].astype(str).str.replace(',', '.').astype(float).sum()
                            
                            custo_c2_fundo = 0
                            fundos_com_taxa = 0
                            fundos_sem_taxa = 0
                            
                            print("\nFundos principais:")
                            
                            # Ordenar por valor
                            fundos_aninhados = fundos_aninhados.sort_values('VL_MERC_POS_FINAL', ascending=False)
                            
                            # Mostrar top 5
                            for i, (_, f2) in enumerate(fundos_aninhados.head(5).iterrows()):
                                cnpj_f2 = f2['CNPJ_FUNDO_CLASSE_COTA']
                                nome_f2 = f2['NM_FUNDO_CLASSE_SUBCLASSE_COTA']
                                valor_f2 = f2['VL_MERC_POS_FINAL']
                                peso = valor_f2 / total_fundo * 100 if total_fundo > 0 else 0
                                
                                taxa = buscar_taxa_cadastro_cvm(cnpj_f2)
                                
                                if taxa is not None:
                                    valor_efetivo = fundo_c1['valor'] * (valor_f2 / total_fundo)
                                    custo = valor_efetivo * taxa
                                    custo_c2_fundo += custo
                                    fundos_com_taxa += 1
                                    print(f"  {i+1}. {nome_f2[:40]:40} ({peso:.1f}%) - Taxa: {taxa*100:.2f}%")
                                else:
                                    fundos_sem_taxa += 1
                                    print(f"  {i+1}. {nome_f2[:40]:40} ({peso:.1f}%) - Taxa: ???")
                            
                            if len(fundos_aninhados) > 5:
                                print(f"  ... e mais {len(fundos_aninhados)-5} fundos")
                            
                            print(f"\n→ Fundos com taxa conhecida: {fundos_com_taxa}")
                            print(f"→ Fundos sem taxa: {fundos_sem_taxa}")
                            
                            if custo_c2_fundo > 0:
                                print(f"→ Custo parcial calculado: R$ {custo_c2_fundo:,.2f}")
                                total_custo_c2 += custo_c2_fundo
                            
                            resumo_fundos.append({
                                'origem': fundo_c1['nome'],
                                'tipo': 'Fundo comum',
                                'status': f'{fundos_com_taxa} com taxa, {fundos_sem_taxa} sem',
                                'custo': custo_c2_fundo
                            })
                            
                        else:
                            print("→ Sem fundos aninhados")
                            resumo_fundos.append({
                                'origem': fundo_c1['nome'],
                                'tipo': 'Fundo comum',
                                'status': 'Sem fundos aninhados',
                                'custo': 0
                            })
                    else:
                        print("→ Sem dados disponíveis")
                        resumo_fundos.append({
                            'origem': fundo_c1['nome'],
                            'tipo': 'Fundo comum',
                            'status': 'Sem dados',
                            'custo': 0
                        })
                        
                except Exception as e:
                    print(f"→ Erro: {str(e)[:50]}")
                    resumo_fundos.append({
                        'origem': fundo_c1['nome'],
                        'tipo': 'Fundo comum',
                        'status': 'Erro ao processar',
                        'custo': 0
                    })
    
    # Resumo final
    print(f"\n\n{'='*80}")
    print("RESUMO DA CAMADA 2")
    print("="*80)
    
    print("\nStatus por fundo:")
    for rf in resumo_fundos:
        print(f"\n{rf['origem']}:")
        print(f"  Tipo: {rf['tipo']}")
        print(f"  Status: {rf['status']}")
        if rf['custo'] > 0:
            print(f"  Custo: R$ {rf['custo']:,.2f}")
    
    print(f"\n\nCUSTO TOTAL CAMADA 2: R$ {total_custo_c2:,.2f}")

if __name__ == "__main__":
    analisar_camada2_detalhada()