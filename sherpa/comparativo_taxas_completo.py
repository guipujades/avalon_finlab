"""
Análise completa das taxas - CVM vs Internet/Estimativas
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

def buscar_todas_taxas_cvm():
    """
    Busca todas as taxas no cadastro CVM para todos os fundos aninhados
    """
    BASE_DIR = Path('/mnt/c/Users/guilh/Documents/GitHub/sherpa/database')
    arquivo_taxas = BASE_DIR / 'CAD' / 'cad_fi_hist_taxa_adm.csv'
    
    # Ler arquivo de taxas
    df_taxas = pd.read_csv(arquivo_taxas, sep=';', encoding='latin-1', low_memory=False)
    
    # Converter datas
    df_taxas['DT_INI_TAXA_ADM'] = pd.to_datetime(df_taxas['DT_INI_TAXA_ADM'], errors='coerce')
    
    # Lista completa de TODOS os fundos aninhados
    todos_fundos = {
        # ALPAMAYO (18 fundos)
        '12.809.201/0001-13': {'nome': 'SPX RAPTOR FEEDER', 'origem': 'ALPAMAYO', 'peso': 18.5},
        '43.551.227/0001-38': {'nome': 'ATIT VÉRTICE FOF', 'origem': 'ALPAMAYO', 'peso': 10.3},
        '16.478.741/0001-12': {'nome': 'SQUADRA LONG-ONLY', 'origem': 'ALPAMAYO', 'peso': 9.2},
        '42.317.906/0001-84': {'nome': 'VÉRTICE DYN COU', 'origem': 'ALPAMAYO', 'peso': 9.2},
        '24.546.223/0001-17': {'nome': 'ITAÚ VÉRTICE IBOVESPA EQUITIES', 'origem': 'ALPAMAYO', 'peso': 9.0},
        '50.324.325/0001-06': {'nome': 'OCEANA VALOR A3', 'origem': 'ALPAMAYO', 'peso': 6.2},
        '34.793.093/0001-70': {'nome': 'NAVI CRUISE A', 'origem': 'ALPAMAYO', 'peso': 6.1},
        '14.096.710/0001-71': {'nome': 'ITAÚ AÇÕES FUND OF FUNDS', 'origem': 'ALPAMAYO', 'peso': 5.5},
        '56.125.991/0001-93': {'nome': 'SPX PATRIOT ITAÚ', 'origem': 'ALPAMAYO', 'peso': 4.9},
        '42.827.012/0001-34': {'nome': 'PROWLER 2', 'origem': 'ALPAMAYO', 'peso': 4.0},
        '37.887.733/0001-08': {'nome': 'SHARP LONG BIASED A', 'origem': 'ALPAMAYO', 'peso': 3.5},
        '39.573.804/0001-15': {'nome': 'NAVI FENDER A', 'origem': 'ALPAMAYO', 'peso': 3.2},
        '19.781.902/0001-30': {'nome': 'OCEANA LONG BIASED FEEDER I', 'origem': 'ALPAMAYO', 'peso': 1.8},
        '46.098.790/0001-90': {'nome': 'ABSOLUTE PACE A', 'origem': 'ALPAMAYO', 'peso': 1.8},
        '28.140.793/0001-63': {'nome': 'ITAÚ VÉRTICE FUNDAMENTA LATAM', 'origem': 'ALPAMAYO', 'peso': 3.1},
        '41.287.689/0001-64': {'nome': 'ITAÚ VÉRTICE RISING STARS', 'origem': 'ALPAMAYO', 'peso': 1.7},
        '21.407.105/0001-30': {'nome': 'ITAÚ VÉRTICE RENDA FIXA DI', 'origem': 'ALPAMAYO', 'peso': 1.6},
        '07.096.546/0001-37': {'nome': 'ITAÚ CAIXA AÇÕES', 'origem': 'ALPAMAYO', 'peso': 0.5},
        
        # CAPSTONE (1 fundo)
        '12.808.980/0001-32': {'nome': 'SPX RAPTOR MASTER', 'origem': 'CAPSTONE', 'peso': 100.0},
        
        # ITAÚ DOLOMITAS (3 fundos)
        '41.272.876/0001-74': {'nome': 'ITAÚ MASTER RISING STARS', 'origem': 'ITAÚ DOLOMITAS', 'peso': 94.9},
        '51.533.573/0001-11': {'nome': 'ITAÚ VÉRTICE SOBERANO Z', 'origem': 'ITAÚ DOLOMITAS', 'peso': 1.1},
        '24.552.905/0001-32': {'nome': 'ITAÚ SOBERANO RF DI LP', 'origem': 'ITAÚ DOLOMITAS', 'peso': 4.0},
        
        # ITAÚ VÉRTICE COMPROMISSO (1 fundo)
        '35.823.433/0001-21': {'nome': 'ITAÚ ZERAGEM', 'origem': 'ITAÚ VÉRTICE COMPROMISSO', 'peso': 100.0},
        
        # ITAÚ VÉRTICE IBOVESPA (12 fundos)
        '34.793.111/0001-14': {'nome': 'MOAT CAPITAL TOTAL RETURN', 'origem': 'ITAÚ VÉRTICE IBOVESPA', 'peso': 10.1},
        '42.336.988/0001-04': {'nome': 'ITAÚ VÉRTICE IBOVESPA EQUITIES II', 'origem': 'ITAÚ VÉRTICE IBOVESPA', 'peso': 8.2},
        '47.512.303/0001-57': {'nome': 'TB A FUNDO', 'origem': 'ITAÚ VÉRTICE IBOVESPA', 'peso': 13.2},
        '45.561.094/0001-06': {'nome': 'TENAX AÇÕES A', 'origem': 'ITAÚ VÉRTICE IBOVESPA', 'peso': 17.4},
        '51.152.703/0001-76': {'nome': '3 ILHAS A', 'origem': 'ITAÚ VÉRTICE IBOVESPA', 'peso': 4.6},
        '52.817.512/0001-49': {'nome': 'MAGNUS VALOR', 'origem': 'ITAÚ VÉRTICE IBOVESPA', 'peso': 19.6},
        '39.992.830/0001-88': {'nome': 'ACE CAPITAL ABSOLUTO', 'origem': 'ITAÚ VÉRTICE IBOVESPA', 'peso': 10.0},
        '44.346.897/0001-85': {'nome': 'ASTER A', 'origem': 'ITAÚ VÉRTICE IBOVESPA', 'peso': 8.6},
        '53.600.131/0001-76': {'nome': 'ACUTO', 'origem': 'ITAÚ VÉRTICE IBOVESPA', 'peso': 7.0},
        
        # ITAÚ CAIXA AÇÕES (4 fundos)
        '56.415.135/0001-72': {'nome': 'ITAÚ CRÉDITO ESTRUTURADO DOLOMITAS I FIDC', 'origem': 'ITAÚ CAIXA AÇÕES', 'peso': 32.1},
        '55.263.898/0001-82': {'nome': 'ITAÚ DOLOMITAS LISTADOS', 'origem': 'ITAÚ CAIXA AÇÕES', 'peso': 1.1},
        '55.264.830/0001-18': {'nome': 'ITAÚ DOLOMITAS VÉRTICE DEB INCENTIVADAS', 'origem': 'ITAÚ CAIXA AÇÕES', 'peso': 66.5},
    }
    
    # Taxas conhecidas de outras fontes (internet/usuário)
    taxas_outras_fontes = {
        '12.809.201/0001-13': 0.020,   # SPX RAPTOR FEEDER - 2.0%
        '14.096.710/0001-71': 0.0006,  # ITAÚ AÇÕES FUND OF FUNDS - 0.06% (usuário)
        '12.808.980/0001-32': 0.019,   # SPX RAPTOR MASTER - 1.9% (usuário)
        '16.478.741/0001-12': 0.028,   # SQUADRA - 2.8% (internet)
        '43.551.227/0001-38': 0.0135,  # ATIT - 1.35% (internet)
        '42.317.906/0001-84': 0.019,   # VÉRTICE DYN - 1.9% (internet)
        '34.793.093/0001-70': 0.018,   # NAVI CRUISE - 1.8% (internet)
        '39.573.804/0001-15': 0.018,   # NAVI FENDER - 1.8% (internet)
        '37.887.733/0001-08': 0.000,   # SHARP - 0% (internet - exclusivo?)
        '46.098.790/0001-90': 0.015,   # ABSOLUTE PACE - 1.5% (internet)
        '50.324.325/0001-06': 0.028,   # OCEANA VALOR - 2.8% (internet)
        '19.781.902/0001-30': 0.028,   # OCEANA LONG BIASED - 2.8% (internet)
    }
    
    resultados = []
    
    for cnpj, info in todos_fundos.items():
        # Buscar na CVM
        df_fundo = df_taxas[df_taxas['CNPJ_FUNDO'] == cnpj]
        
        taxa_cvm = None
        data_cvm = None
        
        if len(df_fundo) > 0:
            # Pegar a mais recente
            df_fundo = df_fundo.sort_values('DT_INI_TAXA_ADM', ascending=False)
            taxa_cvm = df_fundo.iloc[0]['TAXA_ADM'] / 100 if pd.notna(df_fundo.iloc[0]['TAXA_ADM']) else None
            data_cvm = df_fundo.iloc[0]['DT_INI_TAXA_ADM']
        
        # Taxa de outras fontes
        taxa_outra = taxas_outras_fontes.get(cnpj, None)
        
        # Diferença
        diferenca = None
        if taxa_cvm is not None and taxa_outra is not None:
            diferenca = abs(taxa_cvm - taxa_outra)
        
        resultados.append({
            'CNPJ': cnpj,
            'Nome Fundo': info['nome'],
            'Fundo Origem': info['origem'],
            'Peso (%)': info['peso'],
            'Taxa CVM (%)': taxa_cvm * 100 if taxa_cvm is not None else None,
            'Data CVM': data_cvm,
            'Taxa Internet/Usuário (%)': taxa_outra * 100 if taxa_outra is not None else None,
            'Diferença (%)': diferenca * 100 if diferenca is not None else None,
            'Status': 'OK' if taxa_cvm is not None else 'SEM DADOS CVM'
        })
    
    # Criar DataFrame
    df_resultado = pd.DataFrame(resultados)
    
    # Estatísticas
    print("="*80)
    print("ANÁLISE DE EFICIÊNCIA - BUSCA DE TAXAS")
    print("="*80)
    
    total_fundos = len(todos_fundos)
    fundos_com_cvm = df_resultado['Taxa CVM (%)'].notna().sum()
    fundos_com_internet = df_resultado['Taxa Internet/Usuário (%)'].notna().sum()
    fundos_com_ambos = df_resultado[df_resultado['Taxa CVM (%)'].notna() & df_resultado['Taxa Internet/Usuário (%)'].notna()]
    
    print(f"\nTOTAL DE FUNDOS ANINHADOS: {total_fundos}")
    print(f"Fundos com taxa na CVM: {fundos_com_cvm} ({fundos_com_cvm/total_fundos*100:.1f}%)")
    print(f"Fundos com taxa Internet/Usuário: {fundos_com_internet} ({fundos_com_internet/total_fundos*100:.1f}%)")
    print(f"Fundos com ambas as fontes: {len(fundos_com_ambos)} ({len(fundos_com_ambos)/total_fundos*100:.1f}%)")
    
    # Por origem
    print("\n\nPOR FUNDO DE ORIGEM:")
    for origem in df_resultado['Fundo Origem'].unique():
        df_origem = df_resultado[df_resultado['Fundo Origem'] == origem]
        total_origem = len(df_origem)
        com_cvm = df_origem['Taxa CVM (%)'].notna().sum()
        print(f"\n{origem}:")
        print(f"  Total de fundos: {total_origem}")
        print(f"  Com taxa CVM: {com_cvm} ({com_cvm/total_origem*100:.1f}%)")
    
    # Maiores diferenças
    if len(fundos_com_ambos) > 0:
        print("\n\nMAIORES DIFERENÇAS ENTRE FONTES:")
        df_dif = fundos_com_ambos.sort_values('Diferença (%)', ascending=False).head(10)
        for _, row in df_dif.iterrows():
            if row['Diferença (%)'] > 0.01:  # Só mostrar diferenças relevantes
                print(f"{row['Nome Fundo']}: CVM {row['Taxa CVM (%)']:.2f}% vs Internet {row['Taxa Internet/Usuário (%)']:.2f}% (dif: {row['Diferença (%)']:.2f}%)")
    
    # Salvar em Excel
    arquivo_saida = 'comparativo_taxas_cvm_internet.xlsx'
    
    with pd.ExcelWriter(arquivo_saida, engine='openpyxl') as writer:
        # Aba principal
        df_resultado.to_excel(writer, sheet_name='Comparativo_Completo', index=False)
        
        # Aba resumo
        resumo = pd.DataFrame([
            {'Métrica': 'Total de Fundos', 'Valor': total_fundos},
            {'Métrica': 'Fundos com Taxa CVM', 'Valor': fundos_com_cvm},
            {'Métrica': 'Fundos com Taxa Internet', 'Valor': fundos_com_internet},
            {'Métrica': 'Fundos com Ambas', 'Valor': len(fundos_com_ambos)},
            {'Métrica': 'Taxa de Sucesso CVM (%)', 'Valor': round(fundos_com_cvm/total_fundos*100, 1)},
        ])
        resumo.to_excel(writer, sheet_name='Resumo', index=False)
        
        # Aba só com taxas encontradas
        df_com_taxa = df_resultado[df_resultado['Taxa CVM (%)'].notna()].sort_values('Nome Fundo')
        df_com_taxa.to_excel(writer, sheet_name='Taxas_Encontradas_CVM', index=False)
        
        # Formatar
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
    
    print(f"\n\n✓ Arquivo salvo: {arquivo_saida}")
    
    return df_resultado

if __name__ == "__main__":
    df_taxas = buscar_todas_taxas_cvm()