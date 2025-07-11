#!/usr/bin/env python3
"""
Script para avaliar a performance das features de Lévy e comparar com benchmarks.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, classification_report
import matplotlib.pyplot as plt
from datetime import datetime
import glob
import os

print("\n" + "="*60)
print("AVALIAÇÃO DE PERFORMANCE - FEATURES DE LÉVY")
print("="*60)

# 1. Carregar features de Lévy mais recentes
print("\n📊 Carregando features de Lévy...")
levy_files = glob.glob('database/levy_features_*.parquet')
if not levy_files:
    print("❌ Nenhum arquivo de features de Lévy encontrado!")
    exit(1)

latest_levy = sorted(levy_files)[-1]
print(f"   Usando: {latest_levy}")

levy_features = pd.read_parquet(latest_levy)
print(f"   Shape: {levy_features.shape}")

# 2. Preparar dados
print("\n🔧 Preparando dados...")
# Separar features e labels
feature_cols = [col for col in levy_features.columns if col.startswith('levy_')]
X = levy_features[feature_cols]
y = levy_features['label'].astype(int)

print(f"   Features: {len(feature_cols)}")
print(f"   Amostras: {len(X)}")
print(f"   Distribuição de classes: {y.value_counts().to_dict()}")

# Tratar valores faltantes
X = X.fillna(X.mean())

# 3. Avaliar com RandomForest (mesmo modelo do benchmark TSFresh)
print("\n🎯 Treinando RandomForest...")

# Split treino/teste
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Padronizar
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Treinar modelo
rf = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    random_state=42,
    n_jobs=-1
)

rf.fit(X_train_scaled, y_train)

# Predições
y_pred = rf.predict(X_test_scaled)
y_pred_proba = rf.predict_proba(X_test_scaled)[:, 1]

# ROC-AUC no conjunto de teste
roc_auc_test = roc_auc_score(y_test, y_pred_proba)

print(f"\n📊 ROC-AUC (conjunto de teste): {roc_auc_test:.4f}")

# 4. Cross-validation (mais robusto)
print("\n📊 Cross-validation (5-fold)...")
cv_scores = cross_val_score(rf, X, y, cv=5, scoring='roc_auc', n_jobs=-1)
print(f"   ROC-AUC médio: {cv_scores.mean():.4f} (±{cv_scores.std():.4f})")
print(f"   Scores por fold: {cv_scores.round(4)}")

# 5. Comparar com benchmarks
print("\n" + "="*60)
print("📈 COMPARAÇÃO COM BENCHMARKS")
print("="*60)

benchmarks = {
    'TSFresh + RF (batch)': 0.607,
    'ML-kNN (online)': 0.550,
    'ECC': 0.536,
    'Binary Relevance': 0.535,
    'Classifier Chain': 0.535,
    'OSML-ELM': 0.533,
    'PCT': 0.532
}

levy_score = cv_scores.mean()

print("\nMétodo                    ROC-AUC    Diferença")
print("-" * 50)
for method, score in benchmarks.items():
    diff = levy_score - score
    symbol = "↑" if diff > 0 else "↓" if diff < 0 else "="
    print(f"{method:<25} {score:.3f}      {diff:+.3f} {symbol}")

print("-" * 50)
print(f"{'Lévy Features + RF':<25} {levy_score:.3f}      ---")

# 6. Análise de importância das features
print("\n🏆 Top 10 features mais importantes:")
feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': rf.feature_importances_
}).sort_values('importance', ascending=False)

for idx, row in feature_importance.head(10).iterrows():
    print(f"   {row['feature']:<30} {row['importance']:.4f}")

# 7. Visualizar resultados
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Importância das features
ax = axes[0, 0]
top_features = feature_importance.head(10)
ax.barh(range(len(top_features)), top_features['importance'])
ax.set_yticks(range(len(top_features)))
ax.set_yticklabels(top_features['feature'])
ax.set_xlabel('Importância')
ax.set_title('Top 10 Features de Lévy')
ax.invert_yaxis()

# Comparação com benchmarks
ax = axes[0, 1]
methods = list(benchmarks.keys()) + ['Lévy + RF']
scores = list(benchmarks.values()) + [levy_score]
colors = ['blue']*len(benchmarks) + ['red']
ax.barh(range(len(methods)), scores, color=colors)
ax.set_yticks(range(len(methods)))
ax.set_yticklabels(methods)
ax.set_xlabel('ROC-AUC')
ax.set_title('Comparação com Benchmarks')
ax.axvline(x=0.5, color='gray', linestyle='--', alpha=0.5)
ax.set_xlim(0.45, 0.65)

# Distribuição das predições
ax = axes[1, 0]
ax.hist(y_pred_proba[y_test == 0], bins=30, alpha=0.5, label='Sem breakpoint', density=True)
ax.hist(y_pred_proba[y_test == 1], bins=30, alpha=0.5, label='Com breakpoint', density=True)
ax.set_xlabel('Probabilidade Predita')
ax.set_ylabel('Densidade')
ax.set_title('Distribuição das Probabilidades')
ax.legend()

# CV scores
ax = axes[1, 1]
ax.plot(range(1, 6), cv_scores, 'o-', markersize=10)
ax.axhline(y=cv_scores.mean(), color='red', linestyle='--', label=f'Média: {cv_scores.mean():.3f}')
ax.set_xlabel('Fold')
ax.set_ylabel('ROC-AUC')
ax.set_title('Cross-Validation Scores')
ax.set_ylim(cv_scores.min() - 0.02, cv_scores.max() + 0.02)
ax.legend()
ax.grid(True, alpha=0.3)

plt.suptitle(f'Avaliação das Features de Lévy - ROC-AUC: {levy_score:.3f}', fontsize=14)
plt.tight_layout()

# Salvar
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
plt.savefig(f'outputs/levy_evaluation_{timestamp}.png', dpi=300, bbox_inches='tight')
print(f"\n💾 Gráfico salvo em: outputs/levy_evaluation_{timestamp}.png")

# 8. Salvar relatório
report_file = f'outputs/levy_performance_report_{timestamp}.txt'
with open(report_file, 'w') as f:
    f.write("="*60 + "\n")
    f.write("RELATÓRIO DE PERFORMANCE - FEATURES DE LÉVY\n")
    f.write("="*60 + "\n\n")
    f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Features de Lévy: {len(feature_cols)}\n")
    f.write(f"Amostras: {len(X)}\n\n")
    f.write(f"ROC-AUC (teste): {roc_auc_test:.4f}\n")
    f.write(f"ROC-AUC (CV 5-fold): {levy_score:.4f} (±{cv_scores.std():.4f})\n\n")
    f.write("Comparação com Benchmarks:\n")
    f.write("-"*40 + "\n")
    
    if levy_score > 0.607:
        f.write("✅ SUPERA o melhor benchmark (TSFresh 0.607)!\n")
    elif levy_score > 0.550:
        f.write("✅ Supera métodos online (ML-kNN 0.550)\n")
    else:
        f.write("⚠️  Performance abaixo dos benchmarks principais\n")
    
    f.write("\nTop 5 Features:\n")
    for idx, row in feature_importance.head(5).iterrows():
        f.write(f"   {row['feature']}: {row['importance']:.4f}\n")

print(f"   Relatório salvo em: {report_file}")

print("\n" + "="*60)
print("✨ AVALIAÇÃO CONCLUÍDA!")
print("="*60)