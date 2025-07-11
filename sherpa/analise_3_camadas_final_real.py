"""
Análise de Custos em 3 Camadas - Com Taxas REAIS
"""

def calcular_custos_final():
    print("="*80)
    print("ANÁLISE DE CUSTOS EM 3 CAMADAS - FUNDO CHIMBORAZO")
    print("Data base: Maio/2025")
    print("Com taxas REAIS dos fundos aninhados")
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
        {'nome': 'VINCI CAPITAL PARTNERS III', 'valor': 11_380_404.94, 'taxa': 0.0000},
        {'nome': 'KINEA PRIVATE EQUITY V', 'valor': 11_180_663.91, 'taxa': 0.0000},
        {'nome': 'SILVERADO MAXIMUM II FIDC', 'valor': 10_669_862.09, 'taxa': 0.0000},
        {'nome': 'ITAÚ DOLOMITAS', 'valor': 27_225_653.63, 'taxa': 0.0006},
        {'nome': 'CAPSTONE MACRO A', 'valor': 26_862_668.12, 'taxa': 0.0190},
        {'nome': 'ALPAMAYO', 'valor': 17_244_736.89, 'taxa': 0.0004},
        {'nome': 'ITAÚ VÉRTICE IBOVESPA', 'valor': 15_957_765.48, 'taxa': 0.0000},
        {'nome': 'ITAÚ VÉRTICE COMPROMISSO', 'valor': 12_917_838.67, 'taxa': 0.0015},
        {'nome': 'ITAÚ CAIXA AÇÕES', 'valor': 13_853_061.98, 'taxa': 0.0000},
    ]
    
    custo_c1 = 0
    print(f"{'Fundo':<40} {'Valor (R$)':>18} {'Taxa':>8} {'Custo Anual':>15}")
    print("-"*81)
    
    for fundo in fundos_c1:
        custo = fundo['valor'] * fundo['taxa']
        custo_c1 += custo
        print(f"{fundo['nome']:<40} {fundo['valor']:>18,.2f} {fundo['taxa']*100:>7.2f}% {custo:>15,.2f}")
    
    print("-"*81)
    print(f"{'TOTAL CAMADA 1':<40} {sum(f['valor'] for f in fundos_c1):>18,.2f} {'':>8} {custo_c1:>15,.2f}")
    
    # CAMADA 2
    print("\n\nCAMADA 2 - FUNDOS ANINHADOS (TAXAS REAIS)")
    print("-"*60)
    
    # Detalhamento dos custos
    custo_alpamayo = 332_668.22  # Com taxas reais da CVM
    custo_capstone = 537_253.36  # SPX Raptor 2%
    custo_pe_fidc = 512_797.86   # Estimativas PE/FIDC
    
    custo_c2 = custo_alpamayo + custo_capstone + custo_pe_fidc
    
    print("\nALPAMAYO (18 fundos):")
    print("  - 14 fundos com taxas REAIS da CVM (1.35% a 2.8%)")
    print("  - 4 fundos com taxa média estimada (1.85%)")
    print(f"  → Custo: R$ {custo_alpamayo:,.2f}")
    
    print("\nCAPSTONE (1 fundo):")
    print("  - SPX Raptor Master: taxa REAL 2.0%")
    print(f"  → Custo: R$ {custo_capstone:,.2f}")
    
    print("\nPE/FIDC (estimativas):")
    print("  - VINCI PE: 1.8% = R$ 204,847.29")
    print("  - KINEA PE: 1.8% = R$ 201,251.95")
    print("  - SILVERADO FIDC: 1.0% = R$ 106,698.62")
    print(f"  → Subtotal: R$ {custo_pe_fidc:,.2f}")
    
    print(f"\nTOTAL CAMADA 2: R$ {custo_c2:,.2f}")
    
    # RESUMO FINAL
    print("\n" + "="*80)
    print("RESUMO FINAL")
    print("="*80)
    
    custo_total = custo_c0 + custo_c1 + custo_c2
    
    print(f"\nCamada 0 (Taxa Itaú 0.35%):     R$ {custo_c0:>15,.2f} ({custo_c0/VALOR_TOTAL_CARTEIRA*100:>6.4f}%)")
    print(f"Camada 1 (Fundos diretos):      R$ {custo_c1:>15,.2f} ({custo_c1/VALOR_TOTAL_CARTEIRA*100:>6.4f}%)")
    print(f"Camada 2 (Fundos aninhados):    R$ {custo_c2:>15,.2f} ({custo_c2/VALOR_TOTAL_CARTEIRA*100:>6.4f}%)")
    print("-"*80)
    print(f"CUSTO TOTAL ANUAL:              R$ {custo_total:>15,.2f} ({custo_total/VALOR_TOTAL_CARTEIRA*100:>6.4f}%)")
    print(f"CUSTO MENSAL MÉDIO:             R$ {custo_total/12:>15,.2f}")
    
    print("\n\nDETALHE DOS CUSTOS DA CAMADA 2:")
    print("-"*60)
    print(f"Fundos com taxas REAIS (CVM):  R$ {custo_alpamayo + custo_capstone:>15,.2f}")
    print(f"PE/FIDC (estimativas):          R$ {custo_pe_fidc:>15,.2f}")
    
    # Salvar
    with open('custos_chimborazo_final_taxas_reais.txt', 'w') as f:
        f.write("ANÁLISE DE CUSTOS - FUNDO CHIMBORAZO\n")
        f.write("Com taxas REAIS dos fundos aninhados\n")
        f.write("="*60 + "\n\n")
        f.write(f"Data base: Maio/2025\n")
        f.write(f"Patrimônio Total: R$ {VALOR_TOTAL_CARTEIRA:,.2f}\n\n")
        
        f.write("RESUMO DOS CUSTOS:\n")
        f.write(f"Camada 0 (Itaú 0.35%):       R$ {custo_c0:,.2f}\n")
        f.write(f"Camada 1 (Fundos diretos):   R$ {custo_c1:,.2f}\n")
        f.write(f"Camada 2 (Fundos aninhados): R$ {custo_c2:,.2f}\n")
        f.write(f"  - Com taxas reais:         R$ {custo_alpamayo + custo_capstone:,.2f}\n")
        f.write(f"  - Estimativas PE/FIDC:     R$ {custo_pe_fidc:,.2f}\n")
        f.write(f"TOTAL ANUAL:                 R$ {custo_total:,.2f}\n")
        f.write(f"TAXA EFETIVA TOTAL:          {custo_total/VALOR_TOTAL_CARTEIRA*100:.4f}%\n")
    
    print("\n✓ Resultados salvos em 'custos_chimborazo_final_taxas_reais.txt'")

if __name__ == "__main__":
    calcular_custos_final()