print("Testando imports...")

try:
    import pandas as pd
    print("✓ pandas OK")
except Exception as e:
    print(f"✗ pandas ERRO: {e}")

try:
    import numpy as np
    print("✓ numpy OK")
except Exception as e:
    print(f"✗ numpy ERRO: {e}")

try:
    import matplotlib.pyplot as plt
    print("✓ matplotlib OK")
except Exception as e:
    print(f"✗ matplotlib ERRO: {e}")

try:
    import seaborn
    print("✓ seaborn OK")
except Exception as e:
    print(f"✗ seaborn ERRO: {e}")

try:
    import scipy
    print("✓ scipy OK")
except Exception as e:
    print(f"✗ scipy ERRO: {e}")

print("\nTestando script principal...")
try:
    from analise_temporal_fundos import AnalisadorTemporalFundos
    print("✓ Import do analisador OK")
except Exception as e:
    print(f"✗ Import do analisador ERRO: {e}")