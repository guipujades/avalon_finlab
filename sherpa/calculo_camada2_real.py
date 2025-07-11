"""
Cálculo da Camada 2 com taxas REAIS dos fundos
"""

def calcular_camada2_com_taxas_reais():
    print("=== CÁLCULO CAMADA 2 COM TAXAS REAIS ===")
    print("="*80)
    
    # ALPAMAYO - 18 fundos com taxas reais encontradas
    alpamayo_valor = 17_244_736.89
    
    fundos_alpamayo = [
        # TOP 5
        {'nome': 'SPX RAPTOR FEEDER', 'peso': 0.185, 'taxa': 0.020},  # 2.0%
        {'nome': 'ATIT VÉRTICE FOF', 'peso': 0.103, 'taxa': 0.0135},  # 1.35%
        {'nome': 'SQUADRA LONG-ONLY', 'peso': 0.092, 'taxa': 0.028},  # 2.8%
        {'nome': 'VÉRTICE DYN COU', 'peso': 0.092, 'taxa': 0.019},  # 1.9%
        {'nome': 'ITAÚ VÉRTICE IBOVESPA EQUITIES', 'peso': 0.090, 'taxa': None},  # Não encontrado
        
        # Outros com taxa conhecida
        {'nome': 'OCEANA VALOR A3', 'peso': 0.062, 'taxa': 0.028},  # 2.8%
        {'nome': 'NAVI CRUISE A', 'peso': 0.061, 'taxa': 0.018},  # 1.8%
        {'nome': 'ITAÚ AÇÕES FUND OF FUNDS', 'peso': 0.055, 'taxa': 0.020},  # 2.0%
        {'nome': 'SPX PATRIOT ITAÚ', 'peso': 0.049, 'taxa': 0.019},  # 1.9%
        {'nome': 'PROWLER 2', 'peso': 0.040, 'taxa': 0.018},  # 1.8%
        {'nome': 'SHARP LONG BIASED A', 'peso': 0.035, 'taxa': 0.000},  # 0% (exclusivo?)
        {'nome': 'NAVI FENDER A', 'peso': 0.032, 'taxa': 0.018},  # 1.8%
        {'nome': 'OCEANA LONG BIASED FEEDER I', 'peso': 0.018, 'taxa': 0.028},  # 2.8%
        {'nome': 'ABSOLUTE PACE A', 'peso': 0.018, 'taxa': 0.015},  # 1.5%
        
        # Sem taxa encontrada
        {'nome': 'ITAÚ VÉRTICE FUNDAMENTA LATAM', 'peso': 0.031, 'taxa': None},
        {'nome': 'ITAÚ VÉRTICE RISING STARS', 'peso': 0.017, 'taxa': None},
        {'nome': 'ITAÚ VÉRTICE RENDA FIXA DI', 'peso': 0.016, 'taxa': None},
        {'nome': 'ITAÚ CAIXA AÇÕES', 'peso': 0.005, 'taxa': None},
    ]
    
    print("\nALPAMAYO - Fundos aninhados:")
    print("-"*80)
    
    custo_alpamayo = 0
    custo_estimado = 0
    
    for fundo in fundos_alpamayo:
        valor_efetivo = alpamayo_valor * fundo['peso']
        
        if fundo['taxa'] is not None:
            custo = valor_efetivo * fundo['taxa']
            custo_alpamayo += custo
            print(f"{fundo['nome']:<40} {fundo['peso']*100:>5.1f}% | Taxa: {fundo['taxa']*100:>5.2f}% | Custo: R$ {custo:>10,.2f}")
        else:
            # Usar média dos fundos conhecidos (1.85%)
            taxa_media = 0.0185
            custo = valor_efetivo * taxa_media
            custo_estimado += custo
            print(f"{fundo['nome']:<40} {fundo['peso']*100:>5.1f}% | Taxa: ~{taxa_media*100:>4.2f}% | Custo: R$ {custo:>10,.2f} (est)")
    
    print("-"*80)
    print(f"Custo com taxas reais: R$ {custo_alpamayo:,.2f}")
    print(f"Custo estimado (média): R$ {custo_estimado:,.2f}")
    print(f"TOTAL ALPAMAYO: R$ {custo_alpamayo + custo_estimado:,.2f}")
    
    # CAPSTONE - 1 fundo
    print("\n\nCAPSTONE MACRO A:")
    print("-"*80)
    capstone_valor = 26_862_668.12
    # SPX Raptor Master - 100% - Taxa 2.0%
    custo_capstone = capstone_valor * 0.02
    print(f"SPX RAPTOR MASTER                        100.0% | Taxa:  2.00% | Custo: R$ {custo_capstone:>10,.2f}")
    
    # PE e FIDC - estimativas
    print("\n\nPE e FIDC (estimativas):")
    print("-"*80)
    
    pe_fidc = [
        {'nome': 'VINCI CAPITAL PARTNERS III', 'valor': 11_380_404.94, 'tipo': 'PE', 'taxa': 0.018},
        {'nome': 'KINEA PRIVATE EQUITY V', 'valor': 11_180_663.91, 'tipo': 'PE', 'taxa': 0.018},
        {'nome': 'SILVERADO MAXIMUM II FIDC', 'valor': 10_669_862.09, 'tipo': 'FIDC', 'taxa': 0.01},
    ]
    
    custo_pe_fidc = 0
    for fundo in pe_fidc:
        custo = fundo['valor'] * fundo['taxa']
        custo_pe_fidc += custo
        print(f"{fundo['nome']:<40} {fundo['tipo']:>5} | Taxa: {fundo['taxa']*100:>5.2f}% | Custo: R$ {custo:>10,.2f}")
    
    # RESUMO
    print("\n\n" + "="*80)
    print("RESUMO CAMADA 2")
    print("="*80)
    
    total_c2 = custo_alpamayo + custo_estimado + custo_capstone + custo_pe_fidc
    
    print(f"\nALPAMAYO (taxas reais + estimativas):   R$ {custo_alpamayo + custo_estimado:>15,.2f}")
    print(f"CAPSTONE (taxa real):                   R$ {custo_capstone:>15,.2f}")
    print(f"PE/FIDC (estimativas):                  R$ {custo_pe_fidc:>15,.2f}")
    print("-"*80)
    print(f"TOTAL CAMADA 2:                         R$ {total_c2:>15,.2f}")
    
    return total_c2

if __name__ == "__main__":
    calcular_camada2_com_taxas_reais()