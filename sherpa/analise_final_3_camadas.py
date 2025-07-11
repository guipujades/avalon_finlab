"""
Análise de Custos em 3 Camadas - Fundo Chimborazo
Estimativas apenas na Camada 1 para PE e FIDC
"""

from pathlib import Path
import pandas as pd

def calcular_custos():
    print("="*80)
    print("ANÁLISE DE CUSTOS EM 3 CAMADAS - FUNDO CHIMBORAZO")
    print("Data base: Maio/2025")
    print("Foco: TAXA DE ADMINISTRAÇÃO ANUAL")
    print("="*80)
    
    # Dados do Chimborazo
    VALOR_TOTAL_CARTEIRA = 148_072_426.33
    
    # Fundos na carteira
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
    
    # Taxas de administração confirmadas (Camada 1)
    TAXAS_ADMIN = {
        '32.311.914/0001-60': 0.0000,  # PE - cobra na camada 2
        '41.535.122/0001-60': 0.0000,  # PE - cobra na camada 2
        '12.138.862/0001-64': 0.0000,  # FIDC - cobra na camada 2
        '41.287.689/0001-64': 0.0006,  # 0.06%
        '12.809.201/0001-13': 0.0190,  # 1.90%
        '56.430.872/0001-44': 0.0004,  # 0.04%
        '14.096.710/0001-71': 0.0000,  # 0%
        '18.138.913/0001-34': 0.0015,  # 0.15%
        '55.419.784/0001-89': 0.0000,  # 0%
    }
    
    # CAMADA 0 - Taxa Itaú
    print("\nCAMADA 0 - TAXA DE ADMINISTRAÇÃO ITAÚ")
    print("-"*60)
    taxa_itau = 0.0035  # 0.35%
    custo_c0 = VALOR_TOTAL_CARTEIRA * taxa_itau
    print(f"Patrimônio Total: R$ {VALOR_TOTAL_CARTEIRA:,.2f}")
    print(f"Taxa: 0.35% a.a.")
    print(f"Custo anual: R$ {custo_c0:,.2f}")
    
    # CAMADA 1 - Fundos Diretos + Estimativas para PE/FIDC
    print("\n\nCAMADA 1 - FUNDOS DIRETOS")
    print("-"*60)
    print(f"{'Fundo':<40} {'Valor (R$)':>18} {'Taxa':>8} {'Custo Anual':>15}")
    print("-"*81)
    
    custo_c1_direto = 0
    
    for fundo in FUNDOS_CHIMBORAZO:
        taxa = TAXAS_ADMIN.get(fundo['cnpj'], 0)
        custo = fundo['valor'] * taxa
        custo_c1_direto += custo
        
        print(f"{fundo['nome']:<40} {fundo['valor']:>18,.2f} {taxa*100:>7.2f}% {custo:>15,.2f}")
    
    print("-"*81)
    print(f"{'TOTAL CAMADA 1':<40} {sum(f['valor'] for f in FUNDOS_CHIMBORAZO):>18,.2f} {'':>8} {custo_c1_direto:>15,.2f}")
    
    # CAMADA 2 - Fundos Aninhados
    print("\n\nCAMADA 2 - FUNDOS ANINHADOS")
    print("-"*60)
    
    custo_c2 = 0
    
    # Para PE e FIDC, a Camada 2 é igual à estimativa da Camada 1
    for fundo in FUNDOS_CHIMBORAZO:
        nome_upper = fundo['nome'].upper()
        taxa_c1 = TAXAS_ADMIN.get(fundo['cnpj'], 0)
        
        if taxa_c1 == 0:  # Só tem custo na camada 2 se não tem na camada 1
            if 'PRIVATE EQUITY' in nome_upper or 'PARTNERS' in nome_upper:
                # PE - mesma taxa da camada 1
                taxa_est = 0.018  # 1.8%
                custo_est = fundo['valor'] * taxa_est
                custo_c2 += custo_est
                print(f"{fundo['nome']}: R$ {custo_est:,.2f} (PE - 1.8%)")
            elif 'FIDC' in nome_upper:
                # FIDC - mesma taxa da camada 1
                taxa_est = 0.01  # 1.0%
                custo_est = fundo['valor'] * taxa_est
                custo_c2 += custo_est
                print(f"{fundo['nome']}: R$ {custo_est:,.2f} (FIDC - 1.0%)")
    
    if custo_c2 > 0:
        print(f"\nSUBTOTAL PE/FIDC: R$ {custo_c2:,.2f}")
    
    print("\nFundos com carteiras - status das taxas:")
    print("  - ALPAMAYO: 18 fundos (2 com taxa conhecida)")
    print("  - CAPSTONE MACRO A: 1 fundo (taxa conhecida: SPX Raptor 2%)")
    print("  - ITAÚ DOLOMITAS: 3 fundos (nenhum com taxa)")
    print("  - ITAÚ VÉRTICE COMPROMISSO: 1 fundo (Itaú Zeragem 0%)")
    print("  - ITAÚ VÉRTICE IBOVESPA: 12 fundos (nenhum com taxa)")
    print("  - ITAÚ CAIXA AÇÕES: 4 fundos (1 com taxa)")
    
    # Custos parciais conhecidos
    custo_c2_parcial = 575_214.20  # Alpamayo + Capstone
    print(f"\n→ Custo parcial (fundos com taxa conhecida): R$ {custo_c2_parcial:,.2f}")
    
    custo_c2_total = custo_c2 + custo_c2_parcial
    
    # RESUMO FINAL
    print("\n" + "="*80)
    print("RESUMO FINAL")
    print("="*80)
    
    custo_total = custo_c0 + custo_c1_direto + custo_c2_total
    
    print(f"\nCamada 0 (Taxa Itaú 0.35%):     R$ {custo_c0:>15,.2f} ({custo_c0/VALOR_TOTAL_CARTEIRA*100:>6.4f}%)")
    print(f"Camada 1 (Fundos diretos):      R$ {custo_c1_direto:>15,.2f} ({custo_c1_direto/VALOR_TOTAL_CARTEIRA*100:>6.4f}%)")
    print(f"Camada 2 - PE/FIDC (estimado):  R$ {custo_c2:>15,.2f} ({custo_c2/VALOR_TOTAL_CARTEIRA*100:>6.4f}%)")
    print(f"Camada 2 - Outros (parcial):    R$ {custo_c2_parcial:>15,.2f} ({custo_c2_parcial/VALOR_TOTAL_CARTEIRA*100:>6.4f}%)")
    print("-"*80)
    print(f"CUSTO TOTAL CALCULÁVEL:         R$ {custo_total:>15,.2f} ({custo_total/VALOR_TOTAL_CARTEIRA*100:>6.4f}%)")
    print(f"CUSTO MENSAL MÉDIO:             R$ {custo_total/12:>15,.2f}")
    
    # Observações
    print("\n\nOBSERVAÇÕES IMPORTANTES:")
    print("-"*60)
    print("1. Camada 0: Taxa de administração cobrada pelo Itaú (0.35%)")
    print("2. Camada 1: Taxas diretas dos fundos (quando cobram na camada 1)")
    print("3. Camada 2: ")
    print("   - PE e FIDC: Estimativas de 1.8% e 1.0% respectivamente")
    print("   - Outros fundos: Custo parcial com taxas conhecidas")
    print("     • ALPAMAYO: Squadra (2%) e Itaú Ibovespa (0.4%)")
    print("     • CAPSTONE: SPX Raptor (2%)")
    print("   - Maioria dos fundos aninhados sem taxa conhecida")
    
    # Salvar resultado
    with open('custos_chimborazo_3camadas.txt', 'w') as f:
        f.write("ANÁLISE DE CUSTOS - FUNDO CHIMBORAZO\n")
        f.write("="*60 + "\n\n")
        f.write(f"Data base: Maio/2025\n")
        f.write(f"Patrimônio Total: R$ {VALOR_TOTAL_CARTEIRA:,.2f}\n\n")
        
        f.write("RESUMO DOS CUSTOS:\n")
        f.write(f"Camada 0 (Itaú 0.35%):          R$ {custo_c0:,.2f}\n")
        f.write(f"Camada 1 (Fundos diretos):      R$ {custo_c1_direto:,.2f}\n")
        f.write(f"Camada 2 - PE/FIDC (estimado):  R$ {custo_c2:,.2f}\n")
        f.write(f"Camada 2 - Outros (parcial):    R$ {custo_c2_parcial:,.2f}\n")
        f.write(f"TOTAL CALCULÁVEL:               R$ {custo_total:,.2f}\n")
        f.write(f"TAXA EFETIVA:                   {custo_total/VALOR_TOTAL_CARTEIRA*100:.4f}%\n")
    
    print("\n✓ Resultados salvos em 'custos_chimborazo_3camadas.txt'")

if __name__ == "__main__":
    calcular_custos()