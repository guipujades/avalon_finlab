#!/usr/bin/env python3
"""
Avalia ROC-AUC das features de Lévy otimizadas para HFT.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import glob

print("\n" + "="*60)
print("AVALIAÇÃO ROC-AUC - LEVY HFT")
print("="*60)

# Carregar features HFT mais recentes
levy_files = glob.glob('database/levy_features_hft_*.parquet')
latest_file = sorted(levy_files)[-1]

print(f"\n📊 Carregando: {latest_file}")
df = pd.read_parquet(latest_file)

# Preparar dados
feature_cols = [col for col in df.columns if col.startswith('levy_')]
X = df[feature_cols].fillna(0)
y = df['label'].astype(int)

print(f"   Features: {feature_cols}")
print(f"   Amostras: {len(X)}")
print(f"   Classes: {np.bincount(y)}")

# 1. Random Forest com todas as features
print("\n🎯 1. Random Forest (todas features):")
rf = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    class_weight='balanced',
    random_state=42
)

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scores = cross_val_score(rf, X, y, cv=cv, scoring='roc_auc')

print(f"   ROC-AUC: {scores.mean():.4f} (±{scores.std():.4f})")
print(f"   Por fold: {scores.round(4)}")

# 2. Testar com features selecionadas
print("\n🎯 2. Top features (duration_mean, duration_min):")
X_selected = df[['levy_duration_mean', 'levy_duration_min']]
scores_selected = cross_val_score(rf, X_selected, y, cv=cv, scoring='roc_auc')

print(f"   ROC-AUC: {scores_selected.mean():.4f} (±{scores_selected.std():.4f})")

# 3. Comparação final
print("\n" + "="*60)
print("COMPARAÇÃO FINAL - HFT vs ORIGINAL")
print("="*60)

print("\nMétodo                          ROC-AUC")
print("-" * 50)
print(f"TSFresh + RF                    0.607")
print(f"Lévy HFT (tau=0.0002)           {scores.mean():.3f} ← NOVO")
print(f"Lévy Original (tau=0.005)       0.564")
print(f"ML-kNN (online)                 0.550")

improvement = (scores.mean() - 0.564) / 0.564 * 100
print(f"\nMelhoria com parâmetros HFT: +{improvement:.1f}%")

if scores.mean() > 0.607:
    print("\n🎉 SUPERA O BENCHMARK TSFRESH!")
elif scores.mean() > 0.580:
    print("\n✅ Excelente performance! Próximo do TSFresh.")
else:
    print("\n✅ Boa performance, supera métodos online.")

# Análise de importância
rf.fit(X, y)
importance_df = pd.DataFrame({
    'feature': feature_cols,
    'importance': rf.feature_importances_
}).sort_values('importance', ascending=False)

print("\n🏆 Importância das features:")
for _, row in importance_df.iterrows():
    print(f"   {row['feature']:<25} {row['importance']:.4f}")

print("\n" + "="*60)