"""
Análise de Custos em 3 Camadas - Versão Corrigida
PE/FIDC: estimativas apenas na Camada 1
Camada 2: apenas taxas reais (0 se não tiver)
"""

def calcular_custos_corrigido():
    print("="*80)
    print("ANÁLISE DE CUSTOS EM 3 CAMADAS - FUNDO CHIMBORAZO")
    print("Data base: Maio/2025")
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
    
    # CAMADA 1 - Com estimativas para PE/FIDC
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
        
        # Aplicar estimativa para PE/FIDC
        if fundo['tipo'] == 'PE':
            custo_est = fundo['valor'] * 0.018  # 1.8%
            custo_c1_estimado += custo_est
            print(f"{fundo['nome']:<40} {fundo['valor']:>18,.2f} {fundo['taxa']*100:>7.2f}% {custo_direto:>15,.2f}")
            print(f"  → Estimativa PE: 1.8% = R$ {custo_est:,.2f}")
        elif fundo['tipo'] == 'FIDC':
            custo_est = fundo['valor'] * 0.01  # 1.0%
            custo_c1_estimado += custo_est
            print(f"{fundo['nome']:<40} {fundo['valor']:>18,.2f} {fundo['taxa']*100:>7.2f}% {custo_direto:>15,.2f}")
            print(f"  → Estimativa FIDC: 1.0% = R$ {custo_est:,.2f}")
        else:
            print(f"{fundo['nome']:<40} {fundo['valor']:>18,.2f} {fundo['taxa']*100:>7.2f}% {custo_direto:>15,.2f}")
    
    custo_c1_total = custo_c1_direto + custo_c1_estimado
    
    print("-"*81)
    print(f"{'SUBTOTAL - Taxas diretas':<40} {sum(f['valor'] for f in fundos_c1):>18,.2f} {'':>8} {custo_c1_direto:>15,.2f}")
    print(f"{'SUBTOTAL - Estimativas PE/FIDC':<40} {'':>18} {'':>8} {custo_c1_estimado:>15,.2f}")
    print(f"{'TOTAL CAMADA 1':<40} {'':>18} {'':>8} {custo_c1_total:>15,.2f}")
    
    # CAMADA 2 - Apenas taxas reais
    print("\n\nCAMADA 2 - FUNDOS ANINHADOS (APENAS TAXAS REAIS)")
    print("-"*60)
    
    # Custos reais encontrados
    custo_alpamayo_real = 281_942.83  # Apenas fundos com taxas conhecidas
    custo_capstone_real = 537_253.36  # SPX Raptor 2%
    
    custo_c2 = custo_alpamayo_real + custo_capstone_real
    
    print("\nALPAMAYO:")
    print("  - 14 fundos com taxas REAIS (1.35% a 2.8%)")
    print("  - 4 fundos sem informação (taxa = 0)")
    print(f"  → Custo (apenas taxas reais): R$ {custo_alpamayo_real:,.2f}")
    
    print("\nCAPSTONE:")
    print("  - SPX Raptor Master: taxa REAL 2.0%")
    print(f"  → Custo: R$ {custo_capstone_real:,.2f}")
    
    print("\nOUTROS FUNDOS:")
    print("  - ITAÚ DOLOMITAS: 3 fundos sem taxa = R$ 0")
    print("  - ITAÚ VÉRTICE COMPROMISSO: 1 fundo (Zeragem 0%) = R$ 0")
    print("  - ITAÚ VÉRTICE IBOVESPA: 12 fundos sem taxa = R$ 0")
    print("  - ITAÚ CAIXA AÇÕES: 4 fundos sem taxa = R$ 0")
    
    print(f"\nTOTAL CAMADA 2: R$ {custo_c2:,.2f}")
    
    # RESUMO FINAL
    print("\n" + "="*80)
    print("RESUMO FINAL")
    print("="*80)
    
    custo_total = custo_c0 + custo_c1_total + custo_c2
    
    print(f"\nCamada 0 (Taxa Itaú 0.35%):     R$ {custo_c0:>15,.2f} ({custo_c0/VALOR_TOTAL_CARTEIRA*100:>6.4f}%)")
    print(f"Camada 1 - Taxas diretas:       R$ {custo_c1_direto:>15,.2f}")
    print(f"Camada 1 - Estimativas PE/FIDC: R$ {custo_c1_estimado:>15,.2f}")
    print(f"Camada 1 - TOTAL:               R$ {custo_c1_total:>15,.2f} ({custo_c1_total/VALOR_TOTAL_CARTEIRA*100:>6.4f}%)")
    print(f"Camada 2 (Taxas reais apenas):  R$ {custo_c2:>15,.2f} ({custo_c2/VALOR_TOTAL_CARTEIRA*100:>6.4f}%)")
    print("-"*80)
    print(f"CUSTO TOTAL ANUAL:              R$ {custo_total:>15,.2f} ({custo_total/VALOR_TOTAL_CARTEIRA*100:>6.4f}%)")
    print(f"CUSTO MENSAL MÉDIO:             R$ {custo_total/12:>15,.2f}")
    
    # Salvar
    with open('custos_chimborazo_final_corrigido.txt', 'w') as f:
        f.write("ANÁLISE DE CUSTOS - FUNDO CHIMBORAZO\n")
        f.write("="*60 + "\n\n")
        f.write(f"Data base: Maio/2025\n")
        f.write(f"Patrimônio Total: R$ {VALOR_TOTAL_CARTEIRA:,.2f}\n\n")
        
        f.write("RESUMO DOS CUSTOS:\n")
        f.write(f"Camada 0 (Itaú 0.35%):          R$ {custo_c0:,.2f}\n")
        f.write(f"Camada 1 (Fundos diretos):      R$ {custo_c1_total:,.2f}\n")
        f.write(f"  - Taxas diretas:              R$ {custo_c1_direto:,.2f}\n")
        f.write(f"  - Estimativas PE/FIDC:        R$ {custo_c1_estimado:,.2f}\n")
        f.write(f"Camada 2 (Fundos aninhados):    R$ {custo_c2:,.2f}\n")
        f.write(f"  - Apenas taxas reais CVM\n")
        f.write(f"TOTAL ANUAL:                    R$ {custo_total:,.2f}\n")
        f.write(f"TAXA EFETIVA TOTAL:             {custo_total/VALOR_TOTAL_CARTEIRA*100:.4f}%\n")
    
    print("\n✓ Resultados salvos em 'custos_chimborazo_final_corrigido.txt'")

if __name__ == "__main__":
    calcular_custos_corrigido()