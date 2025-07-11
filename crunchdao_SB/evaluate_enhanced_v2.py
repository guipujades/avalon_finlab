#!/usr/bin/env python3
"""
Avalia ROC-AUC da versão Enhanced V2 com várias estratégias.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import glob

print("\n" + "="*60)
print("AVALIAÇÃO LEVY ENHANCED V2 - MÚLTIPLAS ESTRATÉGIAS")
print("="*60)

# Carregar dados
files = glob.glob('database/levy_enhanced_v2_*.parquet')
latest = sorted(files)[-1]

df = pd.read_parquet(latest)
print(f"\n📊 Dataset: {latest}")
print(f"   Shape: {df.shape}")

# Preparar dados
all_features = [c for c in df.columns if c.startswith('levy_')]
X_all = df[all_features].fillna(0)
y = df['label'].astype(int)

print(f"   Total de features: {len(all_features)}")
print(f"   Distribuição: {np.bincount(y)}")

# Estratégias de seleção de features
print("\n🎯 Testando diferentes estratégias:")
print("-" * 60)

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
results = []

# 1. Todas as features
rf = RandomForestClassifier(n_estimators=100, max_depth=10, class_weight='balanced', random_state=42)
scores = cross_val_score(rf, X_all, y, cv=cv, scoring='roc_auc')
results.append(('Todas features (34)', scores.mean(), scores.std()))
print(f"\n1. Todas as features: {scores.mean():.4f} (±{scores.std():.4f})")

# 2. Features de trend (mais discriminativas segundo análise)
trend_features = [f for f in all_features if 'trend' in f]
if trend_features:
    X_trend = df[trend_features].fillna(0)
    scores = cross_val_score(rf, X_trend, y, cv=cv, scoring='roc_auc')
    results.append((f'Trends ({len(trend_features)} feat)', scores.mean(), scores.std()))
    print(f"\n2. Features de trend: {scores.mean():.4f} (±{scores.std():.4f})")

# 3. Features de média + interação
mean_inter_features = [f for f in all_features if any(x in f for x in ['mean', 'scale_', 'cv_prop', 'break_sig'])]
X_mean_inter = df[mean_inter_features].fillna(0)
scores = cross_val_score(rf, X_mean_inter, y, cv=cv, scoring='roc_auc')
results.append((f'Médias+Interação ({len(mean_inter_features)} feat)', scores.mean(), scores.std()))
print(f"\n3. Médias + Interação: {scores.mean():.4f} (±{scores.std():.4f})")

# 4. Top features por importância
# Treinar para obter importâncias
rf.fit(X_all, y)
importances = pd.DataFrame({
    'feature': all_features,
    'importance': rf.feature_importances_
}).sort_values('importance', ascending=False)

for n_top in [5, 10, 15]:
    top_features = importances.head(n_top)['feature'].tolist()
    X_top = df[top_features]
    scores = cross_val_score(rf, X_top, y, cv=cv, scoring='roc_auc')
    results.append((f'Top {n_top} features', scores.mean(), scores.std()))
    print(f"\n4.{n_top//5}. Top {n_top} features: {scores.mean():.4f} (±{scores.std():.4f})")

# 5. Gradient Boosting (pode capturar interações complexas)
print("\n5. Gradient Boosting:")
gb = GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=42)
scores = cross_val_score(gb, X_all, y, cv=cv, scoring='roc_auc')
results.append(('GradientBoosting', scores.mean(), scores.std()))
print(f"   ROC-AUC: {scores.mean():.4f} (±{scores.std():.4f})")

# 6. Criar features de razão customizadas
print("\n6. Features customizadas (razões):")
custom_features = []

# Razões entre escalas adjacentes
for i in range(len(['ultra_micro', 'micro', 'media', 'macro'])):
    scales = ['ultra_micro', 'micro', 'media', 'macro', 'ultra_macro']
    if i < len(scales)-1:
        f1 = f'levy_{scales[i]}_mean'
        f2 = f'levy_{scales[i+1]}_mean'
        if f1 in df.columns and f2 in df.columns:
            ratio_name = f'ratio_{scales[i]}_{scales[i+1]}'
            df[ratio_name] = df[f2] / (df[f1] + 1e-10)
            custom_features.append(ratio_name)

# Produto de features importantes
df['trend_product'] = df['levy_micro_trend'] * df['levy_macro_trend']
df['cv_diff_x_ratio'] = df['levy_cv_propagation'] * df['levy_scale_ratio']
custom_features.extend(['trend_product', 'cv_diff_x_ratio'])

# Adicionar features originais importantes
best_original = ['levy_ultra_macro_mean', 'levy_micro_trend', 'levy_cv_propagation']
X_custom = df[custom_features + best_original].fillna(0)

scores = cross_val_score(rf, X_custom, y, cv=cv, scoring='roc_auc')
results.append((f'Custom ({len(custom_features + best_original)} feat)', scores.mean(), scores.std()))
print(f"   ROC-AUC: {scores.mean():.4f} (±{scores.std():.4f})")

# Resumo final
print("\n\n" + "="*60)
print("RESUMO DOS RESULTADOS")
print("="*60)

# Ordenar por ROC-AUC
results_df = pd.DataFrame(results, columns=['Estratégia', 'ROC-AUC', 'Std'])
results_df = results_df.sort_values('ROC-AUC', ascending=False)

print("\nRanking de estratégias:")
print("-" * 50)
for _, row in results_df.iterrows():
    print(f"{row['Estratégia']:<30} {row['ROC-AUC']:.4f} (±{row['Std']:.4f})")

best_score = results_df.iloc[0]['ROC-AUC']

print("\n📊 Comparação com benchmarks:")
print("-" * 50)
print(f"TSFresh + RF:              0.607")
print(f"Lévy Enhanced V2:          {best_score:.3f} ← MELHOR")
print(f"Lévy Single-scale:         0.564")
print(f"ML-kNN:                    0.550")

if best_score > 0.58:
    print("\n🎉 EXCELENTE! Melhoria significativa com multi-escala enhanced!")
elif best_score > 0.564:
    print("\n✅ Boa melhoria sobre single-scale!")
else:
    print("\n⚠️  Performance similar ou inferior ao single-scale")

print("\n💡 Features mais importantes:")
for _, row in importances.head(5).iterrows():
    print(f"   {row['feature']:<35} {row['importance']:.4f}")

print("\n" + "="*60)