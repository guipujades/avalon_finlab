#!/usr/bin/env python3
"""
Analisa as features de Lévy em mais detalhes.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
import glob

print("\n" + "="*60)
print("ANÁLISE DETALHADA - FEATURES DE LÉVY")
print("="*60)

# Carregar dados
levy_file = sorted(glob.glob('database/levy_features_*.parquet'))[-1]
df = pd.read_parquet(levy_file)

print(f"\n📊 Dados carregados: {levy_file}")
print(f"   Shape: {df.shape}")
print(f"   Colunas: {df.columns.tolist()}")

# Análise das features
feature_cols = [col for col in df.columns if col.startswith('levy_')]
print(f"\n📊 Features de Lévy encontradas: {len(feature_cols)}")
for col in feature_cols:
    print(f"   - {col}")

# Estatísticas por classe
print("\n📊 Estatísticas das features por classe:")
print("-"*60)

for col in feature_cols:
    if df[col].notna().sum() > 0:  # Apenas se houver dados válidos
        class_0 = df[df['label']==0][col].dropna()
        class_1 = df[df['label']==1][col].dropna()
        
        if len(class_0) > 0 and len(class_1) > 0:
            mean_0 = class_0.mean()
            mean_1 = class_1.mean()
            diff_pct = ((mean_1 - mean_0) / mean_0 * 100) if mean_0 != 0 else 0
            
            print(f"\n{col}:")
            print(f"   Classe 0 (sem break): {mean_0:.4f} (n={len(class_0)})")
            print(f"   Classe 1 (com break): {mean_1:.4f} (n={len(class_1)})")
            print(f"   Diferença: {diff_pct:+.1f}%")

# Verificar valores faltantes
print("\n📊 Valores faltantes por feature:")
for col in feature_cols:
    missing = df[col].isna().sum()
    if missing > 0:
        print(f"   {col}: {missing} ({missing/len(df)*100:.1f}%)")

# Treinar modelo simples para ver importância
X = df[feature_cols].fillna(df[feature_cols].mean())
y = df['label'].astype(int)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)

# Predições
y_pred = rf.predict(X_test)
y_pred_proba = rf.predict_proba(X_test)[:, 1]

print("\n📊 Performance no conjunto de teste:")
print(f"   ROC-AUC: {roc_auc_score(y_test, y_pred_proba):.4f}")
print("\nRelatório de classificação:")
print(classification_report(y_test, y_pred))

# Importância das features
print("\n🏆 Importância das features:")
importance_df = pd.DataFrame({
    'feature': feature_cols,
    'importance': rf.feature_importances_
}).sort_values('importance', ascending=False)

for idx, row in importance_df.iterrows():
    print(f"   {row['feature']:<30} {row['importance']:.4f}")

print("\n" + "="*60)
print("CONCLUSÃO DA ANÁLISE")
print("="*60)