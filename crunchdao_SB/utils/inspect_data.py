import pandas as pd
import numpy as np

print("Investigando estrutura dos dados...\n")

try:
    X_train = pd.read_parquet('database/X_train.parquet')
    y_train = pd.read_parquet('database/y_train.parquet')
    
    print("X_train info:")
    print(f"  - Tipo: {type(X_train)}")
    print(f"  - Shape: {X_train.shape}")
    print(f"  - Colunas: {list(X_train.columns)}")
    print(f"  - Index names: {X_train.index.names}")
    print(f"  - É MultiIndex? {isinstance(X_train.index, pd.MultiIndex)}")
    
    print("\nPrimeiras 5 linhas de X_train:")
    print(X_train.head())
    
    print("\n" + "="*50 + "\n")
    
    print("y_train info:")
    print(f"  - Tipo: {type(y_train)}")
    print(f"  - Shape: {y_train.shape}")
    print(f"  - Colunas: {list(y_train.columns)}")
    print(f"  - Index names: {y_train.index.names}")
    
    print("\nPrimeiras 5 linhas de y_train:")
    print(y_train.head())
    
    if isinstance(X_train.index, pd.MultiIndex):
        print("\n" + "="*50 + "\n")
        print("X_train tem MultiIndex!")
        print("Resetando index para análise...")
        X_train_reset = X_train.reset_index()
        print(f"Colunas após reset: {list(X_train_reset.columns)}")
        print("\nPrimeiras 5 linhas após reset:")
        print(X_train_reset.head())
        
except Exception as e:
    print(f"Erro: {e}")
    import traceback
    traceback.print_exc()