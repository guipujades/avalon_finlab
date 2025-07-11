import sys
print(f"Python: {sys.version}")

try:
    import pandas as pd
    print("✓ pandas importado")
    
    import numpy as np
    print("✓ numpy importado")
    
    import matplotlib
    matplotlib.use('Agg')  # Usar backend sem GUI
    import matplotlib.pyplot as plt
    print("✓ matplotlib importado")
    
    # Testar o script principal sem seaborn/scipy
    from analise_temporal_fundos import AnalisadorTemporalFundos
    print("✓ Script principal importado com sucesso!")
    
    # Teste rápido
    cnpj_teste = "38.351.476/0001-40"
    print(f"\nTestando com CNPJ: {cnpj_teste}")
    analisador = AnalisadorTemporalFundos(cnpj_teste, "Teste", periodo_minimo_anos=5)
    print(f"✓ Analisador criado")
    print(f"✓ Diretório de saída: {analisador.output_dir}")
    
except Exception as e:
    print(f"✗ Erro: {e}")
    import traceback
    traceback.print_exc()