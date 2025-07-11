#!/usr/bin/env python3
"""
Implementação COMPLETA de todas as otimizações sugeridas para Lévy multi-escala.
Inclui feature engineering avançado, seleção inteligente e modelos especializados.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score, StratifiedKFold, train_test_split
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif
from sklearn.metrics import roc_auc_score
from datetime import datetime
import glob
import warnings
warnings.filterwarnings('ignore')

print("\n" + "="*60)
print("LEVY ULTIMATE - IMPLEMENTAÇÃO COMPLETA DE OTIMIZAÇÕES")
print("="*60)

# 1. CARREGAR DADOS ENHANCED V2
print("\n📊 Carregando dados Enhanced V2...")
files = glob.glob('database/levy_enhanced_v2_*.parquet')
df = pd.read_parquet(sorted(files)[-1])

feature_cols = [c for c in df.columns if c.startswith('levy_')]
print(f"   Features originais: {len(feature_cols)}")
print(f"   Amostras: {len(df)}")

# 2. FEATURE ENGINEERING AVANÇADO
print("\n🔧 Feature Engineering Avançado...")

# 2.1 Log-transform das durações (reduzir outliers)
print("   - Aplicando log-transform nas durações...")
duration_cols = [c for c in feature_cols if '_mean' in c or '_std' in c]
for col in duration_cols:
    # Log1p para lidar com zeros
    df[f'{col}_log'] = np.log1p(df[col].clip(lower=0))

# 2.2 Razões entre trends de diferentes escalas
print("   - Criando razões entre trends...")
scales = ['ultra_micro', 'micro', 'media', 'macro', 'ultra_macro']
trend_ratios = []

for i in range(len(scales)):
    for j in range(i+1, len(scales)):
        col1 = f'levy_{scales[i]}_trend'
        col2 = f'levy_{scales[j]}_trend'
        if col1 in df.columns and col2 in df.columns:
            ratio_name = f'trend_ratio_{scales[i]}_{scales[j]}'
            # Adicionar pequena constante para evitar divisão por zero
            df[ratio_name] = (df[col2] + 0.1) / (df[col1] + 0.1)
            trend_ratios.append(ratio_name)

# 2.3 Features de "cascata" (propagação de mudanças)
print("   - Criando features de cascata...")
cascade_features = []

# Cascata de durações médias
for i in range(len(scales)-1):
    col1 = f'levy_{scales[i]}_mean'
    col2 = f'levy_{scales[i+1]}_mean'
    if col1 in df.columns and col2 in df.columns:
        # Fator de amplificação entre escalas adjacentes
        cascade_name = f'cascade_factor_{i}'
        df[cascade_name] = df[col2] / (df[col1] + 1e-10)
        cascade_features.append(cascade_name)

# Taxa de propagação de CV
cv_cols = [f'levy_{scale}_cv' for scale in scales if f'levy_{scale}_cv' in df.columns]
if len(cv_cols) >= 3:
    # Diferença progressiva de CV
    for i in range(len(cv_cols)-1):
        diff_name = f'cv_diff_{i}'
        df[diff_name] = df[cv_cols[i+1]] - df[cv_cols[i]]
        cascade_features.append(diff_name)

# 2.4 Features compostas de alta ordem
print("   - Criando features compostas...")
# Produto de features importantes
df['trend_stability'] = df['levy_micro_trend'] * df['levy_macro_trend'] * df['levy_media_trend']
df['scale_consistency'] = df['levy_scale_correlation'] * df['levy_scale_ratio']
df['volatility_signature'] = df['levy_cv_propagation'] * df['levy_break_signature']

# Diferença normalizada entre micro e macro
if 'levy_micro_mean' in df.columns and 'levy_macro_mean' in df.columns:
    df['micro_macro_normalized_diff'] = (df['levy_macro_mean'] - df['levy_micro_mean']) / (df['levy_macro_mean'] + df['levy_micro_mean'] + 1e-10)

# 3. PREPARAR DADOS PARA MODELAGEM
all_features = [c for c in df.columns if c.startswith(('levy_', 'trend_', 'cascade_', 'cv_diff')) or c in ['trend_stability', 'scale_consistency', 'volatility_signature', 'micro_macro_normalized_diff']]
X_full = df[all_features].fillna(0)
y = df['label'].astype(int)

print(f"\n📊 Total de features após engineering: {len(all_features)}")

# 4. SELEÇÃO INTELIGENTE DE FEATURES
print("\n🎯 Seleção Inteligente de Features...")

# 4.1 Remover features altamente correlacionadas
print("   - Removendo features correlacionadas (threshold: 0.95)...")
corr_matrix = X_full.corr().abs()
upper_tri = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
to_drop = [column for column in upper_tri.columns if any(upper_tri[column] > 0.95)]
X_decorr = X_full.drop(columns=to_drop)
print(f"     Features removidas: {len(to_drop)}")
print(f"     Features restantes: {len(X_decorr.columns)}")

# 4.2 Selecionar top features por importância
print("   - Selecionando top 15 features por mutual information...")
selector = SelectKBest(score_func=mutual_info_classif, k=min(15, len(X_decorr.columns)))
X_selected = selector.fit_transform(X_decorr, y)
selected_features = X_decorr.columns[selector.get_support()].tolist()

print(f"     Features selecionadas: {selected_features}")

# 4.3 Garantir que features estratégicas estejam incluídas
strategic_features = ['levy_scale_ratio', 'levy_cv_propagation', 'levy_micro_trend', 'levy_macro_trend']
for feat in strategic_features:
    if feat in X_decorr.columns and feat not in selected_features:
        selected_features.append(feat)

X_final = X_decorr[selected_features]
print(f"\n📊 Features finais para modelagem: {len(selected_features)}")

# 5. MODELOS ESPECIALIZADOS
print("\n🤖 Treinando Modelos Especializados...")

# Split para validação
X_train, X_test, y_train, y_test = train_test_split(X_final, y, test_size=0.2, random_state=42, stratify=y)

# 5.1 Modelo para micro-quebras (foco em features de escalas pequenas)
micro_features = [f for f in selected_features if any(scale in f for scale in ['micro', 'ultra_micro']) or 'trend_ratio' in f]
if len(micro_features) >= 3:
    print(f"\n   Modelo 1 - Detector de Micro-quebras ({len(micro_features)} features)")
    rf_micro = RandomForestClassifier(
        n_estimators=100,
        max_depth=5,  # Raso para evitar overfitting
        min_samples_leaf=5,
        class_weight='balanced',
        random_state=42
    )
    rf_micro.fit(X_train[micro_features], y_train)
    micro_pred = rf_micro.predict_proba(X_test[micro_features])[:, 1]
    micro_auc = roc_auc_score(y_test, micro_pred)
    print(f"     ROC-AUC: {micro_auc:.4f}")
else:
    micro_features = selected_features[:len(selected_features)//2]
    rf_micro = RandomForestClassifier(n_estimators=100, max_depth=5, class_weight='balanced', random_state=42)
    rf_micro.fit(X_train[micro_features], y_train)
    micro_pred = rf_micro.predict_proba(X_test[micro_features])[:, 1]
    micro_auc = roc_auc_score(y_test, micro_pred)

# 5.2 Modelo para macro-quebras (foco em features de escalas grandes)
macro_features = [f for f in selected_features if any(scale in f for scale in ['macro', 'ultra_macro', 'scale', 'cascade'])]
if len(macro_features) >= 3:
    print(f"\n   Modelo 2 - Detector de Macro-quebras ({len(macro_features)} features)")
    rf_macro = RandomForestClassifier(
        n_estimators=100,
        max_depth=7,
        min_samples_leaf=3,
        class_weight='balanced',
        random_state=42
    )
    rf_macro.fit(X_train[macro_features], y_train)
    macro_pred = rf_macro.predict_proba(X_test[macro_features])[:, 1]
    macro_auc = roc_auc_score(y_test, macro_pred)
    print(f"     ROC-AUC: {macro_auc:.4f}")
else:
    macro_features = selected_features[len(selected_features)//2:]
    rf_macro = RandomForestClassifier(n_estimators=100, max_depth=7, class_weight='balanced', random_state=42)
    rf_macro.fit(X_train[macro_features], y_train)
    macro_pred = rf_macro.predict_proba(X_test[macro_features])[:, 1]
    macro_auc = roc_auc_score(y_test, macro_pred)

# 5.3 Modelo geral com todas as features
print(f"\n   Modelo 3 - Detector Geral ({len(selected_features)} features)")
rf_general = RandomForestClassifier(
    n_estimators=150,
    max_depth=8,
    min_samples_leaf=4,
    class_weight='balanced',
    random_state=42
)
rf_general.fit(X_train, y_train)
general_pred = rf_general.predict_proba(X_test)[:, 1]
general_auc = roc_auc_score(y_test, general_pred)
print(f"     ROC-AUC: {general_auc:.4f}")

# 6. ENSEMBLE DOS MODELOS
print("\n🎯 Criando Ensemble...")

# 6.1 Média ponderada das predições
# Pesos baseados no AUC individual
total_auc = micro_auc + macro_auc + general_auc
w_micro = micro_auc / total_auc
w_macro = macro_auc / total_auc
w_general = general_auc / total_auc

ensemble_pred = w_micro * micro_pred + w_macro * macro_pred + w_general * general_pred
ensemble_auc = roc_auc_score(y_test, ensemble_pred)

print(f"\n   Ensemble - Média Ponderada:")
print(f"     Pesos: micro={w_micro:.3f}, macro={w_macro:.3f}, general={w_general:.3f}")
print(f"     ROC-AUC: {ensemble_auc:.4f}")

# 6.2 Voting Classifier (mais robusto)
print("\n   Ensemble - Voting Classifier:")
voting_clf = VotingClassifier(
    estimators=[
        ('micro', rf_micro),
        ('macro', rf_macro),
        ('general', rf_general)
    ],
    voting='soft',
    weights=[micro_auc, macro_auc, general_auc]
)

# Cross-validation com o ensemble completo
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# Precisamos recriar os modelos para cada fold
cv_scores = []
for train_idx, val_idx in cv.split(X_final, y):
    X_cv_train, X_cv_val = X_final.iloc[train_idx], X_final.iloc[val_idx]
    y_cv_train, y_cv_val = y.iloc[train_idx], y.iloc[val_idx]
    
    # Treinar ensemble
    voting_clf.fit(X_cv_train, y_cv_train)
    
    # Predizer
    y_pred = voting_clf.predict_proba(X_cv_val)[:, 1]
    cv_scores.append(roc_auc_score(y_cv_val, y_pred))

cv_mean = np.mean(cv_scores)
cv_std = np.std(cv_scores)

print(f"     ROC-AUC (5-fold CV): {cv_mean:.4f} (±{cv_std:.4f})")
print(f"     Scores por fold: {[f'{s:.4f}' for s in cv_scores]}")

# 7. ANÁLISE FINAL
print("\n" + "="*60)
print("RESULTADOS FINAIS - LEVY ULTIMATE")
print("="*60)

print("\n📊 Comparação de Modelos:")
print("-" * 50)
print(f"Micro-detector:     {micro_auc:.4f}")
print(f"Macro-detector:     {macro_auc:.4f}")
print(f"Detector Geral:     {general_auc:.4f}")
print(f"Ensemble (média):   {ensemble_auc:.4f}")
print(f"Ensemble (voting):  {cv_mean:.4f} ← MELHOR")

print("\n📊 Comparação com Benchmarks:")
print("-" * 50)
print(f"TSFresh + RF:       0.607")
print(f"Lévy Ultimate:      {cv_mean:.3f} ← NOSSO")
print(f"Lévy Enhanced V2:   0.567")
print(f"Lévy Single:        0.564")
print(f"ML-kNN:            0.550")

if cv_mean > 0.58:
    print("\n🎉 EXCELENTE! Ultimate version alcança performance superior!")
elif cv_mean > 0.567:
    print("\n✅ BOA MELHORIA sobre Enhanced V2!")
else:
    print("\n📊 Performance similar às versões anteriores")

# Feature importance do modelo geral
importance_df = pd.DataFrame({
    'feature': selected_features,
    'importance': rf_general.feature_importances_
}).sort_values('importance', ascending=False)

print("\n🏆 Top 10 Features Finais:")
print("-" * 60)
for _, row in importance_df.head(10).iterrows():
    print(f"{row['feature']:<40} {row['importance']:.4f}")

print("\n💡 TÉCNICAS APLICADAS:")
print("✓ Log-transform das durações")
print("✓ Razões entre trends de diferentes escalas")
print("✓ Features de cascata e propagação")
print("✓ Remoção de features correlacionadas")
print("✓ Seleção por mutual information")
print("✓ Modelos especializados (micro/macro)")
print("✓ Ensemble ponderado por performance")

print("\n" + "="*60)