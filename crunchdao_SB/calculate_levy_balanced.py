#!/usr/bin/env python3
"""
Calcula ROC-AUC com balanceamento de classes.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import glob

print("\n" + "="*60)
print("ROC-AUC COM BALANCEAMENTO - FEATURES DE LÉVY")
print("="*60)

# Carregar dados
levy_file = sorted(glob.glob('database/levy_features_*.parquet'))[-1]
df = pd.read_parquet(levy_file)

# Preparar dados
feature_cols = [col for col in df.columns if col.startswith('levy_')]
X = df[feature_cols].fillna(df[feature_cols].mean())
y = df['label'].astype(int)

print(f"\n📊 Dados:")
print(f"   Features: {len(feature_cols)}")
print(f"   Amostras: {len(X)}")
print(f"   Classe 0: {sum(y==0)} ({sum(y==0)/len(y)*100:.1f}%)")
print(f"   Classe 1: {sum(y==1)} ({sum(y==1)/len(y)*100:.1f}%)")

# 1. Random Forest com class_weight='balanced'
print("\n🎯 1. Random Forest Balanceado:")
rf_balanced = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    class_weight='balanced',  # Ajusta para desbalanceamento
    random_state=42,
    n_jobs=-1
)

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scores_rf = cross_val_score(rf_balanced, X, y, cv=cv, scoring='roc_auc', n_jobs=-1)

print(f"   ROC-AUC: {scores_rf.mean():.4f} (±{scores_rf.std():.4f})")
print(f"   Por fold: {scores_rf.round(4)}")

# 2. Logistic Regression (geralmente melhor para features limitadas)
print("\n🎯 2. Logistic Regression:")
lr_pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('lr', LogisticRegression(
        class_weight='balanced',
        max_iter=1000,
        random_state=42
    ))
])

scores_lr = cross_val_score(lr_pipeline, X, y, cv=cv, scoring='roc_auc', n_jobs=-1)
print(f"   ROC-AUC: {scores_lr.mean():.4f} (±{scores_lr.std():.4f})")
print(f"   Por fold: {scores_lr.round(4)}")

# 3. Random Forest com diferentes profundidades
print("\n🎯 3. Random Forest - Otimização de Profundidade:")
best_score = 0
best_depth = 0

for depth in [3, 5, 7, 10, 15, None]:
    rf_test = RandomForestClassifier(
        n_estimators=100,
        max_depth=depth,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    scores = cross_val_score(rf_test, X, y, cv=cv, scoring='roc_auc', n_jobs=-1)
    score_mean = scores.mean()
    print(f"   Depth={depth}: ROC-AUC = {score_mean:.4f}")
    
    if score_mean > best_score:
        best_score = score_mean
        best_depth = depth

print(f"\n   Melhor profundidade: {best_depth} (ROC-AUC = {best_score:.4f})")

# 4. Seleção de features mais importantes
print("\n🎯 4. Testando com Top Features:")
# Treinar modelo para obter importâncias
rf_balanced.fit(X, y)
importances = rf_balanced.feature_importances_
top_indices = np.argsort(importances)[::-1]

for n_features in [3, 5, 7]:
    X_selected = X.iloc[:, top_indices[:n_features]]
    scores = cross_val_score(rf_balanced, X_selected, y, cv=cv, scoring='roc_auc', n_jobs=-1)
    print(f"   Top {n_features} features: ROC-AUC = {scores.mean():.4f}")

# Resultado final
best_model_score = max(scores_rf.mean(), scores_lr.mean(), best_score)

print("\n" + "="*60)
print("📈 COMPARAÇÃO FINAL:")
print("="*60)

benchmarks = [
    ('TSFresh + RF', 0.607),
    ('Lévy (Balanceado)', best_model_score),
    ('ML-kNN (online)', 0.550),
    ('ECC', 0.536),
    ('Outros online', 0.535)
]

print("\nMétodo                    ROC-AUC")
print("-" * 40)
for method, score in sorted(benchmarks, key=lambda x: x[1], reverse=True):
    marker = " ← NOSSO RESULTADO" if "Lévy" in method else ""
    print(f"{method:<25} {score:.3f}{marker}")

print("\n" + "="*60)
print(f"MELHOR ROC-AUC: {best_model_score:.4f}")
print("="*60)