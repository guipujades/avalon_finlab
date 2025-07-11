import pandas as pd
import numpy as np

try:
    X_train = pd.read_parquet('database/X_train.parquet')
    y_train = pd.read_parquet('database/y_train.parquet')
    
    print("Dados carregados com sucesso!")
    print(f"\nFormato X_train: {X_train.shape}")
    print(f"Formato y_train: {y_train.shape}")
    print(f"\nColunas X_train: {X_train.columns.tolist()}")
    print(f"\nPrimeiras 20 linhas X_train:")
    print(X_train.head(20))
    
    print(f"\nDistribuição de labels:")
    print(y_train['label'].value_counts())
    print(f"Percentual com quebra: {y_train['label'].mean():.2%}")
    
    unique_ids = X_train['id'].unique()
    print(f"\nTotal de séries temporais: {len(unique_ids)}")
    
    print("\nAnalisando estrutura dos dados...")
    print(f"Valores únicos de 'period': {X_train['period'].unique()}")
    
    sample_ids = unique_ids[:5]
    print("\nExemplos de séries temporais:")
    
    for sid in sample_ids:
        series = X_train[X_train['id'] == sid]
        label = y_train[y_train['id'] == sid]['label'].values[0]
        
        before = series[series['period'] == 0]
        after = series[series['period'] == 1]
        
        print(f"\nSérie {sid} (Quebra: {label}):")
        print(f"  Pontos antes: {len(before)}")
        print(f"  Pontos depois: {len(after)}")
        print(f"  Média antes: {before['value'].mean():.4f}")
        print(f"  Média depois: {after['value'].mean():.4f}")
        print(f"  Std antes: {before['value'].std():.4f}")
        print(f"  Std depois: {after['value'].std():.4f}")
        
except Exception as e:
    print(f"Erro: {e}")
    print("\nTentando com caminho completo...")
    
    try:
        X_train = pd.read_parquet('/mnt/c/Users/guilh/Documents/GitHub/crunchdao_SB/database/X_train.parquet')
        y_train = pd.read_parquet('/mnt/c/Users/guilh/Documents/GitHub/crunchdao_SB/database/y_train.parquet')
        print("Carregamento com caminho completo funcionou!")
    except Exception as e2:
        print(f"Erro também com caminho completo: {e2}")