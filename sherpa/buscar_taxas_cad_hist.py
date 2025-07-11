"""
Busca taxas de administração no arquivo histórico de taxas da CVM
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

def buscar_taxas_historicas():
    """
    Busca as taxas de administração no arquivo histórico
    """
    BASE_DIR = Path('/mnt/c/Users/guilh/Documents/GitHub/sherpa/database')
    
    # Arquivo de taxas históricas
    arquivo_taxas = BASE_DIR / 'CAD' / 'cad_fi_hist_taxa_adm.csv'
    
    print("=== BUSCA DE TAXAS NO HISTÓRICO CVM ===")
    print("="*80)
    
    if not arquivo_taxas.exists():
        print(f"Arquivo não encontrado: {arquivo_taxas}")
        return None
    
    # Ler arquivo
    print(f"Lendo arquivo: {arquivo_taxas}")
    df_taxas = pd.read_csv(arquivo_taxas, sep=';', encoding='latin-1', low_memory=False)
    
    print(f"Total de registros: {len(df_taxas)}")
    print(f"Colunas: {list(df_taxas.columns)}")
    
    # Lista de CNPJs que precisamos
    cnpjs_buscar = {
        # ALPAMAYO
        '12.809.201/0001-13': 'SPX RAPTOR FEEDER',
        '43.551.227/0001-38': 'ATIT VÉRTICE FOF',
        '16.478.741/0001-12': 'SQUADRA LONG-ONLY',
        '42.317.906/0001-84': 'VÉRTICE DYN COU',
        '24.546.223/0001-17': 'ITAÚ VÉRTICE IBOVESPA EQUITIES',
        '50.324.325/0001-06': 'OCEANA VALOR A3',
        '34.793.093/0001-70': 'NAVI CRUISE A',
        '14.096.710/0001-71': 'ITAÚ AÇÕES FUND OF FUNDS',
        '56.125.991/0001-93': 'SPX PATRIOT ITAÚ',
        '42.827.012/0001-34': 'PROWLER 2',
        '37.887.733/0001-08': 'SHARP LONG BIASED A',
        '39.573.804/0001-15': 'NAVI FENDER A',
        '19.781.902/0001-30': 'OCEANA LONG BIASED FEEDER I',
        '46.098.790/0001-90': 'ABSOLUTE PACE A',
        '28.140.793/0001-63': 'ITAÚ VÉRTICE FUNDAMENTA LATAM',
        '41.287.689/0001-64': 'ITAÚ VÉRTICE RISING STARS',
        '21.407.105/0001-30': 'ITAÚ VÉRTICE RENDA FIXA DI',
        '07.096.546/0001-37': 'ITAÚ CAIXA AÇÕES',
        
        # CAPSTONE
        '12.808.980/0001-32': 'SPX RAPTOR MASTER',
        
        # ITAÚ DOLOMITAS
        '41.272.876/0001-74': 'ITAÚ MASTER RISING STARS',
        '51.533.573/0001-11': 'ITAÚ VÉRTICE SOBERANO Z',
        '24.552.905/0001-32': 'ITAÚ SOBERANO RF DI LP',
        
        # ITAÚ VÉRTICE COMPROMISSO
        '35.823.433/0001-21': 'ITAÚ ZERAGEM',
    }
    
    # Converter datas se existir coluna de data
    colunas_data = [col for col in df_taxas.columns if 'DT' in col.upper() or 'DATA' in col.upper()]
    if colunas_data:
        for col in colunas_data:
            try:
                df_taxas[col] = pd.to_datetime(df_taxas[col], format='%Y-%m-%d', errors='coerce')
            except:
                pass
    
    print("\n" + "="*80)
    print("TAXAS ENCONTRADAS:")
    print("="*80)
    
    taxas_encontradas = {}
    
    for cnpj, nome in cnpjs_buscar.items():
        # Buscar no dataframe
        df_fundo = df_taxas[df_taxas['CNPJ_FUNDO'] == cnpj] if 'CNPJ_FUNDO' in df_taxas.columns else pd.DataFrame()
        
        if len(df_fundo) > 0:
            # Ordenar por data se existir
            if colunas_data:
                df_fundo = df_fundo.sort_values(by=colunas_data[0], ascending=False)
            
            # Pegar a taxa mais recente
            registro = df_fundo.iloc[0]
            
            # Buscar coluna de taxa
            taxa = None
            for col in df_fundo.columns:
                if 'TX' in col.upper() or 'TAX' in col.upper() or 'ADM' in col.upper():
                    if pd.notna(registro[col]):
                        try:
                            taxa = float(registro[col]) / 100  # Converter de percentual para decimal
                            break
                        except:
                            pass
            
            if taxa is not None:
                print(f"\n{nome} ({cnpj})")
                print(f"  Taxa: {taxa:.4f} ({taxa*100:.2f}%)")
                if colunas_data:
                    print(f"  Data: {registro[colunas_data[0]]}")
                
                taxas_encontradas[cnpj] = {
                    'nome': nome,
                    'taxa': taxa,
                    'data': registro[colunas_data[0]] if colunas_data else None
                }
        else:
            print(f"\n{nome} ({cnpj})")
            print(f"  ✗ Não encontrado")
    
    return taxas_encontradas

def criar_analise_final_com_taxas_reais(taxas_encontradas):
    """
    Cria análise final usando as taxas reais encontradas
    """
    print("\n\n" + "="*80)
    print("ANÁLISE FINAL COM TAXAS REAIS")
    print("="*80)
    
    # Valores dos fundos no Chimborazo
    fundos_chimborazo = {
        '56.430.872/0001-44': {'nome': 'ALPAMAYO', 'valor': 17_244_736.89},
        '12.809.201/0001-13': {'nome': 'CAPSTONE MACRO A', 'valor': 26_862_668.12},
    }
    
    # Pesos dos fundos no Alpamayo
    alpamayo_composicao = {
        '12.809.201/0001-13': 0.185,  # SPX RAPTOR FEEDER
        '43.551.227/0001-38': 0.103,  # ATIT VÉRTICE FOF
        '16.478.741/0001-12': 0.092,  # SQUADRA LONG-ONLY
        '42.317.906/0001-84': 0.092,  # VÉRTICE DYN COU
        '24.546.223/0001-17': 0.090,  # ITAÚ VÉRTICE IBOVESPA EQUITIES
        '50.324.325/0001-06': 0.062,  # OCEANA VALOR A3
        '34.793.093/0001-70': 0.061,  # NAVI CRUISE A
        '14.096.710/0001-71': 0.055,  # ITAÚ AÇÕES FUND OF FUNDS
        '56.125.991/0001-93': 0.049,  # SPX PATRIOT ITAÚ
        '42.827.012/0001-34': 0.040,  # PROWLER 2
        '37.887.733/0001-08': 0.035,  # SHARP LONG BIASED A
        '39.573.804/0001-15': 0.032,  # NAVI FENDER A
        '19.781.902/0001-30': 0.018,  # OCEANA LONG BIASED FEEDER I
        '46.098.790/0001-90': 0.018,  # ABSOLUTE PACE A
    }
    
    # Calcular custo do Alpamayo
    valor_alpamayo = 17_244_736.89
    custo_alpamayo = 0
    
    print("\nALPAMAYO - Custos com taxas reais:")
    for cnpj, peso in alpamayo_composicao.items():
        if cnpj in taxas_encontradas:
            taxa = taxas_encontradas[cnpj]['taxa']
            valor_efetivo = valor_alpamayo * peso
            custo = valor_efetivo * taxa
            custo_alpamayo += custo
            print(f"  {taxas_encontradas[cnpj]['nome'][:35]:35} | Taxa: {taxa*100:>5.2f}% | Custo: R$ {custo:>10,.2f}")
    
    print(f"\nTOTAL ALPAMAYO: R$ {custo_alpamayo:,.2f}")
    
    # Capstone (se encontrado)
    if '12.808.980/0001-32' in taxas_encontradas:
        valor_capstone = 26_862_668.12
        taxa_capstone = taxas_encontradas['12.808.980/0001-32']['taxa']
        custo_capstone = valor_capstone * taxa_capstone
        print(f"\nCAPSTONE - SPX Raptor Master:")
        print(f"  Taxa: {taxa_capstone*100:.2f}% | Custo: R$ {custo_capstone:,.2f}")
    
    # Salvar resultados
    df_resultado = pd.DataFrame([
        {
            'CNPJ': cnpj,
            'Nome': info['nome'],
            'Taxa': info['taxa'],
            'Taxa %': f"{info['taxa']*100:.2f}%"
        }
        for cnpj, info in taxas_encontradas.items()
    ])
    
    df_resultado.to_csv('taxas_fundos_aninhados_cvm.csv', index=False)
    print("\n✓ Taxas salvas em: taxas_fundos_aninhados_cvm.csv")

if __name__ == "__main__":
    taxas = buscar_taxas_historicas()
    
    if taxas:
        criar_analise_final_com_taxas_reais(taxas)