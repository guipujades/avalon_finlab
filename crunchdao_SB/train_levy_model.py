#!/usr/bin/env python3
"""
Treina modelo com features de Lévy e calcula ROC-AUC.
Versão sem dependências externas além de pandas e numpy.
"""

import pandas as pd
import numpy as np
import glob
from datetime import datetime

print("\n" + "="*60)
print("TREINAMENTO E AVALIAÇÃO - FEATURES DE LÉVY")
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
print(f"   Colunas: {levy_features.columns.tolist()}")

# 2. Preparar dados
print("\n🔧 Preparando dados...")
feature_cols = [col for col in levy_features.columns if col.startswith('levy_')]
X = levy_features[feature_cols].values
y = levy_features['label'].astype(int).values

print(f"   Features: {len(feature_cols)}")
print(f"   Amostras: {len(X)}")
print(f"   Distribuição: {np.bincount(y)}")

# Tratar valores faltantes com média
col_means = np.nanmean(X, axis=0)
for i in range(X.shape[1]):
    X[np.isnan(X[:, i]), i] = col_means[i]

# 3. Implementar validação cruzada manual (5-fold)
print("\n🎯 Treinando modelo com validação cruzada...")
n_samples = len(X)
n_folds = 5
indices = np.arange(n_samples)
np.random.seed(42)
np.random.shuffle(indices)

fold_size = n_samples // n_folds
cv_scores = []

for fold in range(n_folds):
    print(f"\n   Fold {fold + 1}/{n_folds}:")
    
    # Dividir dados
    test_start = fold * fold_size
    test_end = test_start + fold_size if fold < n_folds - 1 else n_samples
    
    test_idx = indices[test_start:test_end]
    train_idx = np.concatenate([indices[:test_start], indices[test_end:]])
    
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
    # Padronizar features
    mean = X_train.mean(axis=0)
    std = X_train.std(axis=0) + 1e-10
    X_train_scaled = (X_train - mean) / std
    X_test_scaled = (X_test - mean) / std
    
    # Treinar modelo simples (Logistic Regression manual)
    # Implementação simplificada sem sklearn
    n_features = X_train_scaled.shape[1]
    weights = np.zeros(n_features)
    bias = 0.0
    learning_rate = 0.01
    n_iterations = 1000
    
    # Gradient descent
    for _ in range(n_iterations):
        # Forward pass
        z = np.dot(X_train_scaled, weights) + bias
        predictions = 1 / (1 + np.exp(-np.clip(z, -500, 500)))
        
        # Calculate gradients
        dz = predictions - y_train
        dw = np.dot(X_train_scaled.T, dz) / len(y_train)
        db = np.mean(dz)
        
        # Update parameters
        weights -= learning_rate * dw
        bias -= learning_rate * db
    
    # Predict probabilities on test set
    z_test = np.dot(X_test_scaled, weights) + bias
    y_pred_proba = 1 / (1 + np.exp(-np.clip(z_test, -500, 500)))
    
    # Calculate ROC-AUC manually
    # Sort by predicted probability
    sorted_indices = np.argsort(y_pred_proba)[::-1]
    y_true_sorted = y_test[sorted_indices]
    
    # Calculate TPR and FPR for different thresholds
    n_positives = np.sum(y_test == 1)
    n_negatives = np.sum(y_test == 0)
    
    tpr_values = []
    fpr_values = []
    
    for i in range(len(y_test) + 1):
        if i == 0:
            tp = 0
            fp = 0
        else:
            tp = np.sum(y_true_sorted[:i] == 1)
            fp = np.sum(y_true_sorted[:i] == 0)
        
        tpr = tp / n_positives if n_positives > 0 else 0
        fpr = fp / n_negatives if n_negatives > 0 else 0
        
        tpr_values.append(tpr)
        fpr_values.append(fpr)
    
    # Calculate AUC using trapezoidal rule
    auc = 0
    for i in range(1, len(fpr_values)):
        auc += (fpr_values[i] - fpr_values[i-1]) * (tpr_values[i] + tpr_values[i-1]) / 2
    
    cv_scores.append(auc)
    print(f"      ROC-AUC: {auc:.4f}")

# 4. Resultados finais
mean_auc = np.mean(cv_scores)
std_auc = np.std(cv_scores)

print("\n" + "="*60)
print("📊 RESULTADOS FINAIS")
print("="*60)
print(f"\nROC-AUC médio: {mean_auc:.4f} (±{std_auc:.4f})")
print(f"Scores por fold: {[f'{s:.4f}' for s in cv_scores]}")

# 5. Comparação com benchmarks
print("\n📈 COMPARAÇÃO COM BENCHMARKS:")
print("-"*50)

benchmarks = {
    'TSFresh + RF (batch)': 0.607,
    'ML-kNN (online)': 0.550,
    'ECC': 0.536,
    'Binary Relevance': 0.535,
    'Classifier Chain': 0.535,
    'OSML-ELM': 0.533,
    'PCT': 0.532
}

for method, score in sorted(benchmarks.items(), key=lambda x: x[1], reverse=True):
    diff = mean_auc - score
    symbol = "↑" if diff > 0 else "↓" if diff < 0 else "="
    print(f"{method:<25} {score:.3f}      {diff:+.3f} {symbol}")

print("-"*50)
print(f"{'Lévy Features (Log Reg)':<25} {mean_auc:.3f}      ---")

# 6. Análise de features importantes
print("\n🏆 Importância das features (baseada nos pesos):")
# Treinar modelo final com todos os dados
mean = X.mean(axis=0)
std = X.std(axis=0) + 1e-10
X_scaled = (X - mean) / std

weights = np.zeros(n_features)
bias = 0.0

for _ in range(n_iterations):
    z = np.dot(X_scaled, weights) + bias
    predictions = 1 / (1 + np.exp(-np.clip(z, -500, 500)))
    dz = predictions - y
    dw = np.dot(X_scaled.T, dz) / len(y)
    db = np.mean(dz)
    weights -= learning_rate * dw
    bias -= learning_rate * db

# Ordenar features por importância (valor absoluto dos pesos)
feature_importance = [(feature_cols[i], abs(weights[i])) for i in range(len(feature_cols))]
feature_importance.sort(key=lambda x: x[1], reverse=True)

print("\nTop 10 features mais importantes:")
for i, (feature, importance) in enumerate(feature_importance[:10], 1):
    print(f"   {i}. {feature:<30} {importance:.4f}")

# 7. Salvar relatório
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
report_file = f'outputs/levy_roc_auc_report_{timestamp}.txt'

with open(report_file, 'w') as f:
    f.write("="*60 + "\n")
    f.write("RELATÓRIO ROC-AUC - FEATURES DE LÉVY\n")
    f.write("="*60 + "\n\n")
    f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Arquivo de features: {latest_levy}\n")
    f.write(f"Número de features: {len(feature_cols)}\n")
    f.write(f"Número de amostras: {len(X)}\n\n")
    
    f.write(f"ROC-AUC (5-fold CV): {mean_auc:.4f} (±{std_auc:.4f})\n")
    f.write(f"Scores por fold: {cv_scores}\n\n")
    
    f.write("Comparação com benchmarks:\n")
    if mean_auc > 0.607:
        f.write("✅ SUPERA o melhor benchmark (TSFresh 0.607)!\n")
    elif mean_auc > 0.550:
        f.write("✅ Supera métodos online (ML-kNN 0.550)\n")
    elif mean_auc > 0.535:
        f.write("⚠️  Performance similar aos métodos online básicos\n")
    else:
        f.write("❌ Performance abaixo dos benchmarks principais\n")
    
    f.write("\nTop 5 features:\n")
    for i, (feature, importance) in enumerate(feature_importance[:5], 1):
        f.write(f"   {i}. {feature}: {importance:.4f}\n")

print(f"\n💾 Relatório salvo em: {report_file}")

print("\n" + "="*60)
print("✨ AVALIAÇÃO CONCLUÍDA!")
print("="*60)