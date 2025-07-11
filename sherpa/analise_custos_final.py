"""
Análise de Custos em 3 Camadas - Fundo Chimborazo
Foco: Taxa de Administração Anual
"""

# Dados do Chimborazo em Maio/2025
VALOR_TOTAL_CARTEIRA = 148_072_426.33

# Fundos na carteira (valores de maio/2025)
FUNDOS_CHIMBORAZO = [
    {'cnpj': '32.311.914/0001-60', 'nome': 'VINCI CAPITAL PARTNERS III', 'valor': 11_380_404.94},
    {'cnpj': '41.535.122/0001-60', 'nome': 'KINEA PRIVATE EQUITY V', 'valor': 11_180_663.91},
    {'cnpj': '12.138.862/0001-64', 'nome': 'SILVERADO MAXIMUM II FIDC', 'valor': 10_669_862.09},
    {'cnpj': '41.287.689/0001-64', 'nome': 'ITAÚ DOLOMITAS', 'valor': 27_225_653.63},
    {'cnpj': '12.809.201/0001-13', 'nome': 'CAPSTONE MACRO A', 'valor': 26_862_668.12},
    {'cnpj': '56.430.872/0001-44', 'nome': 'ALPAMAYO', 'valor': 17_244_736.89},
    {'cnpj': '14.096.710/0001-71', 'nome': 'ITAÚ VÉRTICE IBOVESPA', 'valor': 15_957_765.48},
    {'cnpj': '18.138.913/0001-34', 'nome': 'ITAÚ VÉRTICE COMPROMISSO', 'valor': 12_917_838.67},
    {'cnpj': '55.419.784/0001-89', 'nome': 'ITAÚ CAIXA AÇÕES', 'valor': 13_853_061.98},
]

# Taxas de administração anuais (confirmadas)
TAXAS_ADMIN = {
    '32.311.914/0001-60': 0.0000,  # 0% na camada 1
    '41.535.122/0001-60': 0.0000,  # 0% na camada 1
    '12.138.862/0001-64': 0.0000,  # 0% na camada 1
    '41.287.689/0001-64': 0.0006,  # 0.06%
    '12.809.201/0001-13': 0.0190,  # 1.90%
    '56.430.872/0001-44': 0.0004,  # 0.04%
    '14.096.710/0001-71': 0.0000,  # 0%
    '18.138.913/0001-34': 0.0015,  # 0.15%
    '55.419.784/0001-89': 0.0000,  # 0%
}

# Estimativas para Camada 2 (fundos que não reportam ou têm taxa 0)
CAMADA2_ESTIMATIVAS = {
    '32.311.914/0001-60': {'descricao': 'Private Equity - Taxa típica nas investidas', 'taxa': 0.018},  # 1.8%
    '41.535.122/0001-60': {'descricao': 'Private Equity - Taxa típica nas investidas', 'taxa': 0.018},  # 1.8%
    '12.138.862/0001-64': {'descricao': 'FIDC - Taxa típica de administração', 'taxa': 0.01},  # 1%
}

def calcular_custos():
    print("="*80)
    print("ANÁLISE DE CUSTOS EM 3 CAMADAS - FUNDO CHIMBORAZO")
    print("Data base: Maio/2025")
    print("Foco: TAXA DE ADMINISTRAÇÃO ANUAL")
    print("="*80)
    
    # CAMADA 0 - Taxa Itaú
    print("\nCAMADA 0 - TAXA DE ADMINISTRAÇÃO ITAÚ")
    print("-"*60)
    taxa_itau = 0.0035  # 0.35%
    custo_c0 = VALOR_TOTAL_CARTEIRA * taxa_itau
    print(f"Patrimônio Total: R$ {VALOR_TOTAL_CARTEIRA:,.2f}")
    print(f"Taxa: 0.35% a.a.")
    print(f"Custo anual: R$ {custo_c0:,.2f}")
    
    # CAMADA 1 - Fundos Diretos
    print("\n\nCAMADA 1 - FUNDOS DIRETOS")
    print("-"*60)
    print(f"{'Fundo':<40} {'Valor (R$)':>18} {'Taxa':>8} {'Custo Anual':>15}")
    print("-"*81)
    
    custo_c1 = 0
    fundos_sem_taxa_c1 = []
    
    for fundo in FUNDOS_CHIMBORAZO:
        taxa = TAXAS_ADMIN.get(fundo['cnpj'], 0)
        custo = fundo['valor'] * taxa
        custo_c1 += custo
        
        if taxa == 0:
            fundos_sem_taxa_c1.append(fundo)
        
        print(f"{fundo['nome']:<40} {fundo['valor']:>18,.2f} {taxa*100:>7.2f}% {custo:>15,.2f}")
    
    print("-"*81)
    print(f"{'TOTAL CAMADA 1':<40} {sum(f['valor'] for f in FUNDOS_CHIMBORAZO):>18,.2f} {'':>8} {custo_c1:>15,.2f}")
    
    # CAMADA 2 - Fundos Aninhados (Estimativas)
    print("\n\nCAMADA 2 - FUNDOS ANINHADOS (ESTIMATIVAS)")
    print("-"*60)
    print("Nota: Fundos com taxa 0% na Camada 1 cobram taxas nos ativos/fundos investidos")
    print()
    
    custo_c2 = 0
    
    for fundo in fundos_sem_taxa_c1:
        if fundo['cnpj'] in CAMADA2_ESTIMATIVAS:
            est = CAMADA2_ESTIMATIVAS[fundo['cnpj']]
            custo = fundo['valor'] * est['taxa']
            custo_c2 += custo
            
            print(f"{fundo['nome']:<40}")
            print(f"  → {est['descricao']}")
            print(f"  → Taxa estimada: {est['taxa']*100:.2f}% | Custo: R$ {custo:,.2f}")
            print()
    
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
    
    # Observações
    print("\n\nOBSERVAÇÕES IMPORTANTES:")
    print("-"*60)
    print("1. Camada 0: Taxa de administração cobrada pelo Itaú como gestor do Chimborazo")
    print("2. Camada 1: Taxas dos fundos investidos diretamente")
    print("3. Camada 2: Estimativas baseadas em práticas de mercado para fundos que:")
    print("   - Private Equity: cobram ~1.8% nas empresas investidas")
    print("   - FIDC: cobra ~1% na carteira de crédito")
    print("   - FICs com taxa 0%: sem estimativa por enquanto")
    print("\n4. Alguns fundos (Alpamayo, Capstone) têm carteiras reportadas mas com")
    print("   erros de leitura nos arquivos CVM, impedindo análise detalhada da Camada 2")
    
    # Salvar resultado
    print("\n\nSALVANDO RESULTADOS...")
    
    with open('custos_chimborazo_resultado_final.txt', 'w') as f:
        f.write("ANÁLISE DE CUSTOS - FUNDO CHIMBORAZO\n")
        f.write("="*60 + "\n\n")
        f.write(f"Data base: Maio/2025\n")
        f.write(f"Patrimônio Total: R$ {VALOR_TOTAL_CARTEIRA:,.2f}\n\n")
        
        f.write("RESUMO DOS CUSTOS:\n")
        f.write(f"Camada 0 (Itaú 0.35%): R$ {custo_c0:,.2f}\n")
        f.write(f"Camada 1 (Fundos):     R$ {custo_c1:,.2f}\n")
        f.write(f"Camada 2 (Estimado):   R$ {custo_c2:,.2f}\n")
        f.write(f"TOTAL ANUAL:           R$ {custo_total:,.2f}\n")
        f.write(f"TAXA EFETIVA TOTAL:    {custo_total/VALOR_TOTAL_CARTEIRA*100:.4f}%\n")
    
    print("✓ Resultados salvos em 'custos_chimborazo_resultado_final.txt'")
    
    return {
        'camada_0': custo_c0,
        'camada_1': custo_c1,
        'camada_2': custo_c2,
        'total': custo_total,
        'taxa_efetiva': custo_total/VALOR_TOTAL_CARTEIRA*100
    }

if __name__ == "__main__":
    resultados = calcular_custos()