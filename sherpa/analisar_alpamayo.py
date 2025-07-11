import pandas as pd
import os
from carteiras_analysis_utils import processar_carteira_completa

def analisar_alpamayo_detalhado():
    """
    Analisa especificamente a carteira do Alpamayo para encontrar fundos aninhados
    """
    CNPJ_ALPAMAYO = '56.430.872/0001-44'
    BASE_DIR = r"C:\Users\guilh\Documents\GitHub\sherpa\database"
    
    print("=== ANÁLISE DETALHADA DO ALPAMAYO ===")
    print(f"CNPJ: {CNPJ_ALPAMAYO}")
    print("="*60)
    
    # Processar carteira com mais meses
    print("\nBuscando carteiras do Alpamayo...")
    carteiras = processar_carteira_completa(
        cnpj_fundo=CNPJ_ALPAMAYO,
        base_dir=BASE_DIR,
        limite_arquivos=12  # Buscar 12 meses
    )
    
    if not carteiras:
        print("✗ Nenhuma carteira encontrada!")
        return
    
    print(f"\n✓ Carteiras encontradas para: {sorted(carteiras.keys())}")
    
    # Analisar cada período disponível
    for data in sorted(carteiras.keys(), reverse=True):
        df = carteiras[data]
        print(f"\n\n{'='*60}")
        print(f"CARTEIRA DE {data}")
        print(f"Total de registros: {len(df)}")
        
        # Converter valores
        if 'VL_MERC_POS_FINAL' in df.columns:
            df['VL_MERC_POS_FINAL'] = pd.to_numeric(
                df['VL_MERC_POS_FINAL'].astype(str).str.replace(',', '.'), 
                errors='coerce'
            )
            total = df['VL_MERC_POS_FINAL'].sum()
            print(f"Valor total: R$ {total:,.2f}")
        
        # Verificar tipos de aplicação
        if 'TP_APLIC' in df.columns:
            print("\nTipos de aplicação:")
            for tp, count in df['TP_APLIC'].value_counts().items():
                valor_tp = df[df['TP_APLIC'] == tp]['VL_MERC_POS_FINAL'].sum()
                pct = (valor_tp / total * 100) if total > 0 else 0
                print(f"  - {tp}: {count} registros | R$ {valor_tp:,.2f} ({pct:.1f}%)")
        
        # Focar nos fundos
        if 'TP_APLIC' in df.columns:
            fundos = df[df['TP_APLIC'] == 'Cotas de Fundos'].copy()
            
            if len(fundos) > 0:
                print(f"\n✓ FUNDOS ENCONTRADOS: {len(fundos)}")
                print("\nDetalhes dos fundos:")
                print("-"*80)
                
                # Ordenar por valor
                fundos = fundos.sort_values('VL_MERC_POS_FINAL', ascending=False)
                
                total_fundos = 0
                for i, (_, fundo) in enumerate(fundos.iterrows()):
                    cnpj = fundo.get('CNPJ_FUNDO_CLASSE_COTA', 'N/A')
                    nome = fundo.get('NM_FUNDO_CLASSE_SUBCLASSE_COTA', 'N/A')
                    valor = fundo.get('VL_MERC_POS_FINAL', 0)
                    peso = (valor / total * 100) if total > 0 else 0
                    
                    print(f"\n{i+1}. {nome}")
                    print(f"   CNPJ: {cnpj}")
                    print(f"   Valor: R$ {valor:,.2f} ({peso:.2f}% da carteira)")
                    
                    total_fundos += valor
                
                print(f"\n{'='*80}")
                print(f"TOTAL EM FUNDOS: R$ {total_fundos:,.2f} ({(total_fundos/total*100):.1f}% da carteira)")
                
                # Salvar detalhes dos fundos
                if len(fundos) > 0:
                    arquivo_saida = f'alpamayo_fundos_{data.replace("-", "")}.csv'
                    fundos.to_csv(arquivo_saida, index=False)
                    print(f"\n✓ Detalhes salvos em: {arquivo_saida}")
                
                # Parar após encontrar fundos
                if len(fundos) >= 10:  # Se tem uma carteira substancial
                    print(f"\n\n{'*'*60}")
                    print("ANÁLISE DE TAXAS DOS FUNDOS DO ALPAMAYO")
                    print("*"*60)
                    
                    # Aqui você pode adicionar as taxas conhecidas ou buscar no cadastro CVM
                    fundos_com_taxas = [
                        {'nome': 'STONE CAPITAL', 'taxa_admin': 0.015},  # 1.5% estimado
                        {'nome': 'TESOURO', 'taxa_admin': 0.0},  # Títulos públicos
                        {'nome': 'DEBENTURES', 'taxa_admin': 0.0},  # Crédito privado direto
                    ]
                    
                    print("\nEstimativa de taxas (baseado em tipos de fundos):")
                    for ft in fundos_com_taxas:
                        print(f"  - {ft['nome']}: {ft['taxa_admin']*100:.2f}%")
                    
                    break
            else:
                print("\n✗ Nenhum fundo encontrado neste período")
        
        # Mostrar apenas os 3 períodos mais recentes com dados relevantes
        if data < '2025-03' and len(fundos) == 0:
            break

if __name__ == "__main__":
    analisar_alpamayo_detalhado()