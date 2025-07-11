import pandas as pd
import warnings
warnings.filterwarnings('ignore')

def buscar_taxas_fundos():
    print("Carregando cadastro CVM...")
    try:
        cad_fi = pd.read_csv('./database/CAD/cad_fi.csv', sep=';', encoding='latin-1')
        print(f"Cadastro carregado: {len(cad_fi)} fundos")
    except Exception as e:
        print(f"Erro ao carregar cadastro: {e}")
        return
    
    # Lista de fundos para buscar
    fundos_buscar = [
        # Itaú
        {'cnpj': '14.096.710/0001-71', 'nome': 'ITAÚ AÇÕES FUND OF FUNDS MULTIGESTOR X'},
        # SPX
        {'cnpj': '12.808.980/0001-32', 'nome': 'SPX RAPTOR MASTER'},
        # Fundos do Alpamayo
        {'cnpj': '20.331.288/0001-27', 'nome': 'ALPAMAYO'},
        {'cnpj': '29.451.041/0001-05', 'nome': 'KADIMA HIGH'},
        {'cnpj': '15.429.968/0001-36', 'nome': 'SOLANA LONG SHORT'},
        {'cnpj': '44.026.991/0001-18', 'nome': 'GIANT ZARATHUSTRA'},
        {'cnpj': '39.210.231/0001-12', 'nome': 'BOTZMANN'},
        {'cnpj': '21.458.997/0001-89', 'nome': 'IGUANA'},
        {'cnpj': '13.907.671/0001-59', 'nome': 'KAPITALO'},
        {'cnpj': '07.916.384/0001-68', 'nome': 'MOAT'},
        {'cnpj': '26.411.183/0001-72', 'nome': 'BOGARI'},
        {'cnpj': '11.960.794/0001-62', 'nome': 'EV ANDROMEDA'},
        {'cnpj': '17.433.678/0001-59', 'nome': 'SHARP EQUITY'},
        {'cnpj': '44.625.200/0001-16', 'nome': 'GT VOLT'},
        {'cnpj': '44.658.272/0001-84', 'nome': 'VALORA'},
        {'cnpj': '11.701.111/0001-07', 'nome': 'ATMOS'},
        {'cnpj': '27.331.597/0001-50', 'nome': 'ADAM'},
        {'cnpj': '26.202.616/0001-48', 'nome': 'AZ QUEST'},
        {'cnpj': '26.106.437/0001-21', 'nome': 'JGP'},
        {'cnpj': '29.451.760/0001-60', 'nome': 'KADIMA'},
        # Outros fundos
        {'cnpj': '09.226.139/0001-00', 'nome': 'ITAÚ DOLOMITAS'}
    ]
    
    print("\nBuscando taxas de administração...\n")
    
    resultados = []
    
    for fundo in fundos_buscar:
        # Busca por CNPJ
        resultado = cad_fi[cad_fi['CNPJ_FUNDO'] == fundo['cnpj']]
        
        # Se não encontrar por CNPJ, busca por nome parcial
        if resultado.empty:
            for palavra in fundo['nome'].split():
                if len(palavra) > 4:  # Palavras com mais de 4 caracteres
                    resultado = cad_fi[cad_fi['DENOM_SOCIAL'].str.contains(palavra, case=False, na=False)]
                    if not resultado.empty:
                        break
        
        if not resultado.empty:
            for _, row in resultado.iterrows():
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
                
                print(f"CNPJ: {row['CNPJ_FUNDO']}")
                print(f"Nome: {row['DENOM_SOCIAL']}")
                print(f"Taxa ADM: {taxa_adm}%")
                if info_taxa:
                    print(f"Info Taxa: {info_taxa}")
                print(f"Situação: {row['SIT']}")
                print("-" * 80)
    
    # Salvar resultados
    if resultados:
        df_resultados = pd.DataFrame(resultados)
        df_resultados.to_csv('taxas_fundos_cvm.csv', index=False, encoding='utf-8')
        print(f"\nResultados salvos em taxas_fundos_cvm.csv")
        print(f"Total de fundos encontrados: {len(resultados)}")
    else:
        print("\nNenhum fundo foi encontrado!")
    
    return resultados

if __name__ == "__main__":
    buscar_taxas_fundos()