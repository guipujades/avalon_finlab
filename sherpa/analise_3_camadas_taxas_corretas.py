"""
Análise de Custos em 3 Camadas - Com Taxas CORRETAS
"""

def calcular_custos_taxas_corretas():
    print("="*80)
    print("ANÁLISE DE CUSTOS EM 3 CAMADAS - FUNDO CHIMBORAZO")
    print("Data base: Maio/2025")
    print("Com taxas CORRETAS dos fundos")
    print("="*80)
    
    VALOR_TOTAL_CARTEIRA = 148_072_426.33
    
    # CAMADA 0
    print("\nCAMADA 0 - TAXA DE ADMINISTRAÇÃO ITAÚ")
    print("-"*60)
    taxa_itau = 0.0035
    custo_c0 = VALOR_TOTAL_CARTEIRA * taxa_itau
    print(f"Patrimônio Total: R$ {VALOR_TOTAL_CARTEIRA:,.2f}")
    print(f"Taxa: 0.35% a.a.")
    print(f"Custo anual: R$ {custo_c0:,.2f}")
    
    # CAMADA 1
    print("\n\nCAMADA 1 - FUNDOS DIRETOS")
    print("-"*60)
    
    fundos_c1 = [
        {'nome': 'VINCI CAPITAL PARTNERS III', 'valor': 11_380_404.94, 'taxa': 0.0000, 'tipo': 'PE'},
        {'nome': 'KINEA PRIVATE EQUITY V', 'valor': 11_180_663.91, 'taxa': 0.0000, 'tipo': 'PE'},
        {'nome': 'SILVERADO MAXIMUM II FIDC', 'valor': 10_669_862.09, 'taxa': 0.0000, 'tipo': 'FIDC'},
        {'nome': 'ITAÚ DOLOMITAS', 'valor': 27_225_653.63, 'taxa': 0.0006, 'tipo': 'FUNDO'},
        {'nome': 'CAPSTONE MACRO A', 'valor': 26_862_668.12, 'taxa': 0.0190, 'tipo': 'FUNDO'},
        {'nome': 'ALPAMAYO', 'valor': 17_244_736.89, 'taxa': 0.0004, 'tipo': 'FUNDO'},
        {'nome': 'ITAÚ VÉRTICE IBOVESPA', 'valor': 15_957_765.48, 'taxa': 0.0000, 'tipo': 'FUNDO'},
        {'nome': 'ITAÚ VÉRTICE COMPROMISSO', 'valor': 12_917_838.67, 'taxa': 0.0015, 'tipo': 'FUNDO'},
        {'nome': 'ITAÚ CAIXA AÇÕES', 'valor': 13_853_061.98, 'taxa': 0.0000, 'tipo': 'FUNDO'},
    ]
    
    custo_c1_direto = 0
    custo_c1_estimado = 0
    
    print(f"{'Fundo':<40} {'Valor (R$)':>18} {'Taxa':>8} {'Custo Anual':>15}")
    print("-"*81)
    
    for fundo in fundos_c1:
        custo_direto = fundo['valor'] * fundo['taxa']
        custo_c1_direto += custo_direto
        
        if fundo['tipo'] == 'PE':
            custo_est = fundo['valor'] * 0.018
            custo_c1_estimado += custo_est
            print(f"{fundo['nome']:<40} {fundo['valor']:>18,.2f} {fundo['taxa']*100:>7.2f}% {custo_direto:>15,.2f}")
            print(f"  → Estimativa PE: 1.8% = R$ {custo_est:,.2f}")
        elif fundo['tipo'] == 'FIDC':
            custo_est = fundo['valor'] * 0.01
            custo_c1_estimado += custo_est
            print(f"{fundo['nome']:<40} {fundo['valor']:>18,.2f} {fundo['taxa']*100:>7.2f}% {custo_direto:>15,.2f}")
            print(f"  → Estimativa FIDC: 1.0% = R$ {custo_est:,.2f}")
        else:
            print(f"{fundo['nome']:<40} {fundo['valor']:>18,.2f} {fundo['taxa']*100:>7.2f}% {custo_direto:>15,.2f}")
    
    custo_c1_total = custo_c1_direto + custo_c1_estimado
    
    print("-"*81)
    print(f"{'TOTAL CAMADA 1':<40} {sum(f['valor'] for f in fundos_c1):>18,.2f} {'':>8} {custo_c1_total:>15,.2f}")
    
    # CAMADA 2 - Com taxas CORRETAS
    print("\n\nCAMADA 2 - FUNDOS ANINHADOS (TAXAS CORRETAS)")
    print("-"*60)
    
    # ALPAMAYO - com taxas corretas
    alpamayo_valor = 17_244_736.89
    
    fundos_alpamayo = [
        {'nome': 'SPX RAPTOR FEEDER', 'peso': 0.185, 'taxa': 0.020},  # 2.0% confirmado
        {'nome': 'ATIT VÉRTICE FOF', 'peso': 0.103, 'taxa': None},     # Buscar
        {'nome': 'SQUADRA LONG-ONLY', 'peso': 0.092, 'taxa': None},    # Buscar
        {'nome': 'VÉRTICE DYN COU', 'peso': 0.092, 'taxa': None},      # Buscar
        {'nome': 'ITAÚ VÉRTICE IBOVESPA EQUITIES', 'peso': 0.090, 'taxa': None},  # Buscar
        {'nome': 'OCEANA VALOR A3', 'peso': 0.062, 'taxa': None},      # Buscar
        {'nome': 'NAVI CRUISE A', 'peso': 0.061, 'taxa': None},        # Buscar
        {'nome': 'ITAÚ AÇÕES FUND OF FUNDS', 'peso': 0.055, 'taxa': 0.0006},  # 0.06% CORRETO
        {'nome': 'SPX PATRIOT ITAÚ', 'peso': 0.049, 'taxa': None},     # Buscar
        {'nome': 'PROWLER 2', 'peso': 0.040, 'taxa': None},            # Buscar
        {'nome': 'SHARP LONG BIASED A', 'peso': 0.035, 'taxa': None},  # Buscar
        {'nome': 'NAVI FENDER A', 'peso': 0.032, 'taxa': None},        # Buscar
        {'nome': 'OCEANA LONG BIASED FEEDER I', 'peso': 0.018, 'taxa': None},  # Buscar
        {'nome': 'ABSOLUTE PACE A', 'peso': 0.018, 'taxa': None},      # Buscar
        {'nome': 'ITAÚ VÉRTICE FUNDAMENTA LATAM', 'peso': 0.031, 'taxa': None},
        {'nome': 'ITAÚ VÉRTICE RISING STARS', 'peso': 0.017, 'taxa': None},
        {'nome': 'ITAÚ VÉRTICE RENDA FIXA DI', 'peso': 0.016, 'taxa': None},
        {'nome': 'ITAÚ CAIXA AÇÕES', 'peso': 0.005, 'taxa': None},
    ]
    
    print("\nALPAMAYO - Fundos aninhados:")
    custo_alpamayo = 0
    
    for fundo in fundos_alpamayo:
        valor_efetivo = alpamayo_valor * fundo['peso']
        
        if fundo['taxa'] is not None:
            custo = valor_efetivo * fundo['taxa']
            custo_alpamayo += custo
            print(f"  {fundo['nome']:<35} {fundo['peso']*100:>5.1f}% | Taxa: {fundo['taxa']*100:>5.2f}% | R$ {custo:>10,.2f}")
        else:
            # Taxa 0 se não tiver informação
            print(f"  {fundo['nome']:<35} {fundo['peso']*100:>5.1f}% | Taxa:   ??? | R$       0.00")
    
    print(f"\n  Custo Alpamayo: R$ {custo_alpamayo:,.2f}")
    
    # CAPSTONE - taxa CORRETA
    print("\nCAPSTONE:")
    capstone_valor = 26_862_668.12
    taxa_spx_raptor = 0.019  # 1.9% CORRETO
    custo_capstone = capstone_valor * taxa_spx_raptor
    print(f"  SPX RAPTOR MASTER                  100.0% | Taxa:  1.90% | R$ {custo_capstone:>10,.2f}")
    
    custo_c2 = custo_alpamayo + custo_capstone
    
    print(f"\nTOTAL CAMADA 2: R$ {custo_c2:,.2f}")
    
    # RESUMO FINAL
    print("\n" + "="*80)
    print("RESUMO FINAL")
    print("="*80)
    
    custo_total = custo_c0 + custo_c1_total + custo_c2
    
    print(f"\nCamada 0 (Taxa Itaú 0.35%):     R$ {custo_c0:>15,.2f} ({custo_c0/VALOR_TOTAL_CARTEIRA*100:>6.4f}%)")
    print(f"Camada 1 (Fundos diretos):      R$ {custo_c1_total:>15,.2f} ({custo_c1_total/VALOR_TOTAL_CARTEIRA*100:>6.4f}%)")
    print(f"Camada 2 (Taxas reais apenas):  R$ {custo_c2:>15,.2f} ({custo_c2/VALOR_TOTAL_CARTEIRA*100:>6.4f}%)")
    print("-"*80)
    print(f"CUSTO TOTAL ANUAL:              R$ {custo_total:>15,.2f} ({custo_total/VALOR_TOTAL_CARTEIRA*100:>6.4f}%)")
    print(f"CUSTO MENSAL MÉDIO:             R$ {custo_total/12:>15,.2f}")
    
    print("\n\nNOTA: Fundos sem taxa conhecida = 0 (conforme solicitado)")

if __name__ == "__main__":
    calcular_custos_taxas_corretas()