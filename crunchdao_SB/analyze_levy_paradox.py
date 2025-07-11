#!/usr/bin/env python3
"""
Analisa o paradoxo: maior separação mas menor ROC-AUC.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, classification_report
import glob

print("\n" + "="*60)
print("ANÁLISE DO PARADOXO - LEVY HFT")
print("="*60)

# Carregar ambos os datasets
print("\n📊 Carregando datasets...")

# Original (tau=0.005)
original_file = 'database/levy_features_20250627_100112.parquet'
df_original = pd.read_parquet(original_file)
print(f"   Original: {df_original.shape}")

# HFT (tau=0.0002)
hft_files = glob.glob('database/levy_features_hft_*.parquet')
df_hft = pd.read_parquet(sorted(hft_files)[-1])
print(f"   HFT: {df_hft.shape}")

# Análise comparativa
print("\n📊 Comparação de separação entre classes:")
print("-" * 60)

datasets = [
    ('Original (tau=0.005)', df_original, ['levy_duration_mean', 'levy_duration_cv']),
    ('HFT (tau=0.0002)', df_hft, ['levy_duration_mean', 'levy_duration_cv'])
]

for name, df, features in datasets:
    print(f"\n{name}:")
    for feat in features:
        if feat in df.columns:
            mean_0 = df[df['label']==0][feat].mean()
            mean_1 = df[df['label']==1][feat].mean()
            std_0 = df[df['label']==0][feat].std()
            std_1 = df[df['label']==1][feat].std()
            
            # Separação relativa
            sep = abs(mean_1 - mean_0) / (mean_0 + 1e-10) * 100
            
            # Overlap (quanto menor, melhor)
            overlap = min(mean_0 + std_0, mean_1 + std_1) - max(mean_0 - std_0, mean_1 - std_1)
            overlap_pct = overlap / (max(mean_0 + std_0, mean_1 + std_1) - min(mean_0 - std_0, mean_1 - std_1)) * 100
            
            print(f"   {feat}:")
            print(f"      Médias: {mean_0:.2f} vs {mean_1:.2f} (sep: {sep:.1f}%)")
            print(f"      Desvios: {std_0:.2f} vs {std_1:.2f}")
            print(f"      Overlap: {overlap_pct:.1f}%")

# Teste com diferentes modelos
print("\n🎯 Testando diferentes modelos:")
print("-" * 60)

for name, df in [('Original', df_original), ('HFT', df_hft)]:
    print(f"\n{name}:")
    
    # Preparar dados
    feature_cols = [col for col in df.columns if col.startswith('levy_')]
    X = df[feature_cols].fillna(0)
    y = df['label'].astype(int)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Escalar
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    models = [
        ('RandomForest', RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)),
        ('LogisticReg', LogisticRegression(class_weight='balanced', max_iter=1000)),
        ('RF_shallow', RandomForestClassifier(n_estimators=50, max_depth=3, class_weight='balanced', random_state=42))
    ]
    
    for model_name, model in models:
        if 'Logistic' in model_name:
            model.fit(X_train_scaled, y_train)
            y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
        else:
            model.fit(X_train, y_train)
            y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        auc = roc_auc_score(y_test, y_pred_proba)
        print(f"   {model_name}: ROC-AUC = {auc:.4f}")

# Diagnóstico
print("\n🔍 DIAGNÓSTICO DO PARADOXO:")
print("-" * 60)

print("\n1. Possíveis causas:")
print("   - HFT tem menos amostras (495 vs 1000)")
print("   - Parâmetros muito sensíveis capturam ruído")
print("   - Features podem estar correlacionadas")
print("   - Distribuição diferente entre treino/teste")

print("\n2. Soluções sugeridas:")
print("   - Usar tau intermediário (0.0005-0.001)")
print("   - Adicionar regularização mais forte")
print("   - Combinar features de múltiplas escalas")
print("   - Usar ensemble de diferentes tau")

print("\n" + "="*60)