import pandas as pd
import warnings
warnings.filterwarnings('ignore')

def buscar_taxas_especificas():
    print("Carregando cadastro CVM...")
    try:
        cad_fi = pd.read_csv('./database/CAD/cad_fi.csv', sep=';', encoding='latin-1')
        print(f"Cadastro carregado: {len(cad_fi)} fundos\n")
    except Exception as e:
        print(f"Erro ao carregar cadastro: {e}")
        return
    
    # CNPJs específicos para buscar
    cnpjs_buscar = [
        '14.096.710/0001-71',  # ITAÚ AÇÕES FUND OF FUNDS MULTIGESTOR X
        '12.808.980/0001-32',  # SPX RAPTOR MASTER
        # Fundos do Alpamayo
        '20.331.288/0001-27',  # ALPAMAYO
        '29.451.041/0001-05',  # KADIMA HIGH VOL
        '15.429.968/0001-36',  # SOLANA LONG SHORT
        '44.026.991/0001-18',  # GIANT ZARATHUSTRA
        '39.210.231/0001-12',  # BOTZMANN
        '21.458.997/0001-89',  # IGUANA INVEST
        '13.907.671/0001-59',  # KAPITALO
        '07.916.384/0001-68',  # MOAT
        '26.411.183/0001-72',  # BOGARI
        '11.960.794/0001-62',  # EV ANDROMEDA
        '17.433.678/0001-59',  # SHARP EQUITY
        '44.625.200/0001-16',  # GT VOLT
        '44.658.272/0001-84',  # VALORA
        '11.701.111/0001-07',  # ATMOS
        '27.331.597/0001-50',  # ADAM
        '26.202.616/0001-48',  # AZ QUEST
        '26.106.437/0001-21',  # JGP
        '29.451.760/0001-60',  # KADIMA
        # Outros fundos importantes
        '09.226.139/0001-00',  # ITAÚ DOLOMITAS
    ]
    
    print("Buscando taxas de administração dos fundos específicos...\n")
    
    resultados = []
    nao_encontrados = []
    
    for cnpj in cnpjs_buscar:
        # Busca direta por CNPJ
        resultado = cad_fi[cad_fi['CNPJ_FUNDO'] == cnpj]
        
        if not resultado.empty:
            row = resultado.iloc[0]
            taxa_adm = row['TAXA_ADM']
            info_taxa = row['INF_TAXA_ADM'] if pd.notna(row['INF_TAXA_ADM']) else ''
            
            resultado_dict = {
                'CNPJ': row['CNPJ_FUNDO'],
                'Nome': row['DENOM_SOCIAL'],
                'Taxa ADM (%)': taxa_adm,
                'Info Taxa': info_taxa,
                'Situação': row['SIT']
            }
            resultados.append(resultado_dict)
            
            print(f"✓ ENCONTRADO: {cnpj}")
            print(f"  Nome: {row['DENOM_SOCIAL']}")
            print(f"  Taxa ADM: {taxa_adm}%")
            if info_taxa:
                print(f"  Info Taxa: {info_taxa}")
            print(f"  Situação: {row['SIT']}")
            print("-" * 80)
        else:
            nao_encontrados.append(cnpj)
            print(f"✗ NÃO ENCONTRADO: {cnpj}")
    
    print(f"\n\nRESUMO:")
    print(f"Total de fundos encontrados: {len(resultados)}")
    print(f"Total de fundos não encontrados: {len(nao_encontrados)}")
    
    if nao_encontrados:
        print(f"\nCNPJs não encontrados:")
        for cnpj in nao_encontrados:
            print(f"  - {cnpj}")
    
    # Salvar resultados
    if resultados:
        df_resultados = pd.DataFrame(resultados)
        df_resultados.to_csv('taxas_fundos_especificos.csv', index=False, encoding='utf-8')
        print(f"\nResultados salvos em taxas_fundos_especificos.csv")
        
        # Mostrar resumo das taxas
        print("\nRESUMO DAS TAXAS ENCONTRADAS:")
        for res in resultados:
            if pd.notna(res['Taxa ADM (%)']):
                print(f"{res['CNPJ']} - {res['Nome'][:50]}... : {res['Taxa ADM (%)']}%")
    
    return resultados

if __name__ == "__main__":
    buscar_taxas_especificas()