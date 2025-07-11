import pandas as pd
import warnings
warnings.filterwarnings('ignore')

def buscar_taxas_por_nome():
    print("Carregando cadastro CVM...")
    try:
        cad_fi = pd.read_csv('./database/CAD/cad_fi.csv', sep=';', encoding='latin-1')
        print(f"Cadastro carregado: {len(cad_fi)} fundos\n")
    except Exception as e:
        print(f"Erro ao carregar cadastro: {e}")
        return
    
    # Palavras-chave para buscar
    palavras_chave = [
        ('ITAU', 'MULTIGESTOR X'),
        ('SPX', 'RAPTOR', 'MASTER'),
        ('ALPAMAYO',),
        ('KADIMA', 'HIGH'),
        ('SOLANA', 'LONG'),
        ('GIANT', 'ZARATHUSTRA'),
        ('BOTZMANN',),
        ('IGUANA',),
        ('KAPITALO',),
        ('MOAT',),
        ('BOGARI',),
        ('ANDROMEDA',),
        ('SHARP', 'EQUITY'),
        ('GT', 'VOLT'),
        ('VALORA',),
        ('ATMOS',),
        ('ADAM',),
        ('AZ QUEST',),
        ('JGP',),
        ('KADIMA',),
        ('ITAU', 'DOLOMITAS'),
        ('CAPSTONE',),
    ]
    
    print("Buscando fundos por nome...\n")
    
    todos_resultados = []
    
    for palavras in palavras_chave:
        # Criar filtro para todas as palavras
        filtro = pd.Series([True] * len(cad_fi))
        for palavra in palavras:
            filtro = filtro & cad_fi['DENOM_SOCIAL'].str.contains(palavra, case=False, na=False)
        
        resultado = cad_fi[filtro]
        
        if not resultado.empty:
            print(f"\n{'='*80}")
            print(f"Buscando por: {' + '.join(palavras)}")
            print(f"Encontrados: {len(resultado)} fundos")
            print('='*80)
            
            for idx, row in resultado.iterrows():
                taxa_adm = row['TAXA_ADM']
                info_taxa = row['INF_TAXA_ADM'] if pd.notna(row['INF_TAXA_ADM']) else ''
                
                resultado_dict = {
                    'Busca': ' + '.join(palavras),
                    'CNPJ': row['CNPJ_FUNDO'],
                    'Nome': row['DENOM_SOCIAL'],
                    'Taxa ADM (%)': taxa_adm,
                    'Info Taxa': info_taxa,
                    'Situação': row['SIT']
                }
                todos_resultados.append(resultado_dict)
                
                print(f"\nCNPJ: {row['CNPJ_FUNDO']}")
                print(f"Nome: {row['DENOM_SOCIAL']}")
                print(f"Taxa ADM: {taxa_adm}%")
                if info_taxa:
                    print(f"Info Taxa: {info_taxa}")
                print(f"Situação: {row['SIT']}")
    
    # Salvar todos os resultados
    if todos_resultados:
        df_resultados = pd.DataFrame(todos_resultados)
        df_resultados.to_csv('taxas_fundos_por_nome.csv', index=False, encoding='utf-8')
        print(f"\n\nResultados salvos em taxas_fundos_por_nome.csv")
        print(f"Total de fundos encontrados: {len(todos_resultados)}")
        
        # Mostrar resumo das taxas válidas
        print("\n\nRESUMO DAS TAXAS ENCONTRADAS (apenas fundos em funcionamento):")
        print("-" * 100)
        for res in todos_resultados:
            if res['Situação'] == 'EM FUNCIONAMENTO NORMAL' and pd.notna(res['Taxa ADM (%)']):
                nome_curto = res['Nome'][:60] + "..." if len(res['Nome']) > 60 else res['Nome']
                print(f"{res['CNPJ']} | {nome_curto} | Taxa: {res['Taxa ADM (%)']}%")
    
    return todos_resultados

if __name__ == "__main__":
    buscar_taxas_por_nome()