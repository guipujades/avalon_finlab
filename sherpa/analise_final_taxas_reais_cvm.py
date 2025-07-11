"""
Análise Final com Taxas REAIS da CVM
"""

def calcular_custos_taxas_reais_cvm():
    print("="*80)
    print("ANÁLISE DE CUSTOS EM 3 CAMADAS - FUNDO CHIMBORAZO")
    print("Data base: Maio/2025")
    print("Com taxas REAIS do cadastro CVM")
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
    
    # CAMADA 2 - Com taxas REAIS da CVM
    print("\n\nCAMADA 2 - FUNDOS ANINHADOS (TAXAS REAIS CVM)")
    print("-"*60)
    
    # Taxas encontradas no cadastro CVM
    taxas_cvm = {
        # ALPAMAYO - fundos com taxas confirmadas
        '43.551.227/0001-38': 0.0135,  # ATIT VÉRTICE FOF - 1.35%
        '16.478.741/0001-12': 0.0280,  # SQUADRA LONG-ONLY - 2.80%
        '42.317.906/0001-84': 0.0190,  # VÉRTICE DYN COU - 1.90%
        '24.546.223/0001-17': 0.0000,  # ITAÚ VÉRTICE IBOVESPA EQUITIES - 0%
        '34.793.093/0001-70': 0.0200,  # NAVI CRUISE A - 2.00%
        '42.827.012/0001-34': 0.0070,  # PROWLER 2 - 0.70%
        '37.887.733/0001-08': 0.0195,  # SHARP LONG BIASED A - 1.95%
        '39.573.804/0001-15': 0.0200,  # NAVI FENDER A - 2.00%
        '28.140.793/0001-63': 0.0000,  # ITAÚ VÉRTICE FUNDAMENTA LATAM - 0%
        '21.407.105/0001-30': 0.0025,  # ITAÚ VÉRTICE RENDA FIXA DI - 0.25%
        '07.096.546/0001-37': 0.0000,  # ITAÚ CAIXA AÇÕES - 0%
        
        # Capstone - usando taxa correta informada
        '12.808.980/0001-32': 0.0190,  # SPX RAPTOR MASTER - 1.90%
        
        # Fundos ainda sem taxa (usar estimativa ou informação do usuário)
        '12.809.201/0001-13': 0.0200,  # SPX RAPTOR FEEDER - 2.00% (estimativa)
        '14.096.710/0001-71': 0.0006,  # ITAÚ AÇÕES FUND OF FUNDS - 0.06% (informado pelo usuário)
    }
    
    # ALPAMAYO
    alpamayo_valor = 17_244_736.89
    alpamayo_composicao = [
        {'cnpj': '12.809.201/0001-13', 'nome': 'SPX RAPTOR FEEDER', 'peso': 0.185},
        {'cnpj': '43.551.227/0001-38', 'nome': 'ATIT VÉRTICE FOF', 'peso': 0.103},
        {'cnpj': '16.478.741/0001-12', 'nome': 'SQUADRA LONG-ONLY', 'peso': 0.092},
        {'cnpj': '42.317.906/0001-84', 'nome': 'VÉRTICE DYN COU', 'peso': 0.092},
        {'cnpj': '24.546.223/0001-17', 'nome': 'ITAÚ VÉRTICE IBOVESPA EQUITIES', 'peso': 0.090},
        {'cnpj': '50.324.325/0001-06', 'nome': 'OCEANA VALOR A3', 'peso': 0.062},
        {'cnpj': '34.793.093/0001-70', 'nome': 'NAVI CRUISE A', 'peso': 0.061},
        {'cnpj': '14.096.710/0001-71', 'nome': 'ITAÚ AÇÕES FUND OF FUNDS', 'peso': 0.055},
        {'cnpj': '56.125.991/0001-93', 'nome': 'SPX PATRIOT ITAÚ', 'peso': 0.049},
        {'cnpj': '42.827.012/0001-34', 'nome': 'PROWLER 2', 'peso': 0.040},
        {'cnpj': '37.887.733/0001-08', 'nome': 'SHARP LONG BIASED A', 'peso': 0.035},
        {'cnpj': '39.573.804/0001-15', 'nome': 'NAVI FENDER A', 'peso': 0.032},
        {'cnpj': '19.781.902/0001-30', 'nome': 'OCEANA LONG BIASED FEEDER I', 'peso': 0.018},
        {'cnpj': '46.098.790/0001-90', 'nome': 'ABSOLUTE PACE A', 'peso': 0.018},
        {'cnpj': '28.140.793/0001-63', 'nome': 'ITAÚ VÉRTICE FUNDAMENTA LATAM', 'peso': 0.031},
        {'cnpj': '41.287.689/0001-64', 'nome': 'ITAÚ VÉRTICE RISING STARS', 'peso': 0.017},
        {'cnpj': '21.407.105/0001-30', 'nome': 'ITAÚ VÉRTICE RENDA FIXA DI', 'peso': 0.016},
        {'cnpj': '07.096.546/0001-37', 'nome': 'ITAÚ CAIXA AÇÕES', 'peso': 0.005},
    ]
    
    print("\nALPAMAYO - Fundos aninhados:")
    custo_alpamayo = 0
    fundos_com_taxa = 0
    fundos_sem_taxa = 0
    
    for fundo in alpamayo_composicao:
        valor_efetivo = alpamayo_valor * fundo['peso']
        
        if fundo['cnpj'] in taxas_cvm:
            taxa = taxas_cvm[fundo['cnpj']]
            custo = valor_efetivo * taxa
            custo_alpamayo += custo
            fundos_com_taxa += 1
            status = "CVM" if fundo['cnpj'] not in ['12.809.201/0001-13', '14.096.710/0001-71'] else "EST"
            print(f"  {fundo['nome']:<35} {fundo['peso']*100:>5.1f}% | Taxa: {taxa*100:>5.2f}% ({status}) | R$ {custo:>10,.2f}")
        else:
            fundos_sem_taxa += 1
            print(f"  {fundo['nome']:<35} {fundo['peso']*100:>5.1f}% | Taxa:   ??? | R$       0.00")
    
    print(f"\n  Fundos com taxa: {fundos_com_taxa} | Sem taxa: {fundos_sem_taxa}")
    print(f"  Custo Alpamayo: R$ {custo_alpamayo:,.2f}")
    
    # CAPSTONE
    print("\nCAPSTONE:")
    capstone_valor = 26_862_668.12
    taxa_spx_raptor = 0.0190  # 1.9% conforme informado
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
    print(f"Camada 2 (Taxas reais CVM):     R$ {custo_c2:>15,.2f} ({custo_c2/VALOR_TOTAL_CARTEIRA*100:>6.4f}%)")
    print("-"*80)
    print(f"CUSTO TOTAL ANUAL:              R$ {custo_total:>15,.2f} ({custo_total/VALOR_TOTAL_CARTEIRA*100:>6.4f}%)")
    print(f"CUSTO MENSAL MÉDIO:             R$ {custo_total/12:>15,.2f}")
    
    print("\n\nFONTES DAS TAXAS:")
    print("-"*60)
    print("CVM: Cadastro histórico de taxas de administração (cad_fi_hist_taxa_adm.csv)")
    print("EST: Estimativas baseadas em fundos similares")
    print("USR: Informado pelo usuário")

if __name__ == "__main__":
    calcular_custos_taxas_reais_cvm()