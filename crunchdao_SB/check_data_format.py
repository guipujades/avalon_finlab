#!/usr/bin/env python3
"""
Script para verificar o formato dos dados e processar corretamente.
"""

import numpy as np
import pandas as pd

print("\n" + "="*60)
print("VERIFICANDO FORMATO DOS DADOS")
print("="*60)

# Carregar dados
print("\n📊 Carregando dados...")
X_train = pd.read_parquet('database/X_train.parquet')
y_train = pd.read_parquet('database/y_train.parquet')

print(f"\n📋 Informações dos dados:")
print(f"   X_train shape: {X_train.shape}")
print(f"   X_train columns: {list(X_train.columns)}")
print(f"   X_train index name: {X_train.index.name}")
print(f"\n   Primeiras linhas do X_train:")
print(X_train.head(10))

print(f"\n   y_train shape: {y_train.shape}")
print(f"   y_train columns: {list(y_train.columns)}")
print(f"\n   Primeiras linhas do y_train:")
print(y_train.head())

# Verificar valores únicos na primeira coluna
if len(X_train.columns) > 0:
    first_col = X_train.columns[0]
    print(f"\n   Valores únicos em '{first_col}': {X_train[first_col].nunique()}")
    print(f"   Primeiros valores únicos: {X_train[first_col].unique()[:10]}")

# Verificar se é formato longo
if X_train.shape[1] == 2:
    print("\n🔍 Parece ser formato longo (id, valor)")
    col1, col2 = X_train.columns
    print(f"   Coluna 1 ({col1}): {X_train[col1].dtype}, únicos: {X_train[col1].nunique()}")
    print(f"   Coluna 2 ({col2}): {X_train[col2].dtype}")
    
    # Tentar pivotar para formato largo
    print("\n   Tentando converter para formato largo...")
    try:
        # Adicionar índice temporal se necessário
        if X_train[col1].nunique() < len(X_train) / 100:
            # col1 parece ser o ID da série
            X_train['time_idx'] = X_train.groupby(col1).cumcount()
            X_wide = X_train.pivot(index=col1, columns='time_idx', values=col2)
            print(f"   ✅ Convertido! Shape: {X_wide.shape}")
            print(f"   Primeiras linhas:")
            print(X_wide.head())
            
            # Salvar para uso posterior
            X_wide.to_parquet('database/X_train_wide.parquet')
            print("\n   💾 Formato largo salvo em: database/X_train_wide.parquet")
    except Exception as e:
        print(f"   ❌ Erro ao converter: {e}")

print("\n" + "="*60)