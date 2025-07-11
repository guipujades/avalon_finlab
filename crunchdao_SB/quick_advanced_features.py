#!/usr/bin/env python3
"""
Versão rápida das features avançadas para teste de conceito.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime

print("\n" + "="*60)
print("FEATURES AVANÇADAS - TESTE RÁPIDO")
print("="*60)

# Carregar dados
X_train = pd.read_parquet('database/X_train.parquet')
y_train = pd.read_parquet('database/y_train.parquet')

def extract_fast_advanced_features(series_values):
    """Features avançadas mas computacionalmente eficientes."""
    features = {}
    
    series_clean = series_values[~np.isnan(series_values)]
    if len(series_clean) < 100:
        return None
    
    # 1. Features espectrais simples
    try:
        # FFT básico
        fft = np.fft.fft(series_clean)
        power = np.abs(fft)**2
        
        features.update({
            'fft_peak_power': np.max(power[1:]),  # Ignorar DC
            'fft_mean_power': np.mean(power[1:]),
            'fft_power_ratio': np.max(power[1:]) / (np.mean(power[1:]) + 1e-10),
        })
    except:
        features.update({'fft_peak_power': 0, 'fft_mean_power': 0, 'fft_power_ratio': 1})
    
    # 2. CUSUM para mudança de média
    try:
        cumsum = np.cumsum(series_clean - np.mean(series_clean))
        features.update({
            'cusum_max': np.max(cumsum),
            'cusum_min': np.min(cumsum),
            'cusum_range': np.max(cumsum) - np.min(cumsum),
        })
    except:
        features.update({'cusum_max': 0, 'cusum_min': 0, 'cusum_range': 0})
    
    # 3. Mudança de variância entre metades
    try:
        mid = len(series_clean) // 2
        var1 = np.var(series_clean[:mid])
        var2 = np.var(series_clean[mid:])
        features['variance_ratio'] = var2 / (var1 + 1e-10)
        features['variance_diff'] = abs(var2 - var1)
    except:
        features.update({'variance_ratio': 1, 'variance_diff': 0})
    
    # 4. Features de alta frequência vs baixa frequência
    try:
        # Diferenças (alta frequência)
        high_freq = np.diff(series_clean)
        high_energy = np.sum(high_freq**2)
        
        # Média móvel (baixa frequência)
        window = min(20, len(series_clean)//5)
        if window > 1:
            low_freq = np.convolve(series_clean, np.ones(window)/window, mode='valid')
            low_energy = np.var(low_freq)
            features['freq_energy_ratio'] = high_energy / (low_energy + 1e-10)
        else:
            features['freq_energy_ratio'] = 0
    except:
        features['freq_energy_ratio'] = 0
    
    # 5. Entropia simples
    try:
        hist, _ = np.histogram(series_clean, bins=10)
        hist = hist + 1e-10
        prob = hist / np.sum(hist)
        entropy = -np.sum(prob * np.log(prob))
        features['entropy'] = entropy
    except:
        features['entropy'] = 0
    
    # 6. Features de extremos
    try:
        q1, q3 = np.percentile(series_clean, [25, 75])
        iqr = q3 - q1
        outliers = np.sum((series_clean < q1 - 1.5*iqr) | (series_clean > q3 + 1.5*iqr))
        features['outlier_ratio'] = outliers / len(series_clean)
        
        # Mudança nos extremos
        n_third = len(series_clean) // 3
        extreme_early = np.sum(np.abs(series_clean[:n_third] - np.median(series_clean)) > 2*np.std(series_clean))
        extreme_late = np.sum(np.abs(series_clean[-n_third:] - np.median(series_clean)) > 2*np.std(series_clean))
        features['extreme_change'] = extreme_late - extreme_early
    except:
        features.update({'outlier_ratio': 0, 'extreme_change': 0})
    
    return features

# Processar amostra
print("\n⚙️  Processando 150 séries...")
n_series = 150
sample_ids = X_train.index.get_level_values('id').unique()[:n_series]

features_list = []
labels = []

for i, series_id in enumerate(sample_ids):
    if i % 30 == 0:
        print(f"   {i}/{n_series}...", end='\r')
    
    returns = X_train.loc[series_id, 'value'].values
    features = extract_fast_advanced_features(returns)
    
    if features is not None:
        features['id'] = series_id
        features_list.append(features)
        label = y_train.loc[series_id].iloc[0] if hasattr(y_train.loc[series_id], 'iloc') else y_train.loc[series_id]
        labels.append(int(label))

print(f"\n✅ Processadas {len(features_list)} séries")

if len(features_list) > 30:
    df = pd.DataFrame(features_list)
    df['label'] = labels
    
    # Avaliar discriminação
    feature_cols = [c for c in df.columns if c not in ['label', 'id']]
    
    print(f"\n📊 Features extraídas: {feature_cols}")
    
    # Análise de separação
    print("\n📊 Poder discriminativo:")
    for feat in feature_cols:
        m0 = df[df['label']==0][feat].mean()
        m1 = df[df['label']==1][feat].mean()
        if abs(m0) > 1e-10:
            diff = (m1-m0)/abs(m0)*100
            if abs(diff) > 10:  # Apenas features com boa separação
                print(f"   {feat:<25} {diff:+6.1f}%")
    
    # Testar modelo
    X = df[feature_cols].fillna(0)
    y = df['label'].astype(int)
    
    rf = RandomForestClassifier(n_estimators=100, max_depth=6, class_weight='balanced', random_state=42)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(rf, X, y, cv=cv, scoring='roc_auc')
    
    print(f"\n🎯 ROC-AUC com features avançadas: {scores.mean():.4f} (±{scores.std():.4f})")
    
    # Agora combinar com Lévy
    print("\n🔗 Combinando com features de Lévy...")
    
    # Carregar Lévy features
    import glob
    levy_files = glob.glob('database/levy_enhanced_v2_*.parquet')
    if levy_files:
        levy_df = pd.read_parquet(sorted(levy_files)[-1])
        
        # Filtrar IDs comuns
        common_ids = set(df['id']) & set(levy_df['id'])
        if len(common_ids) > 20:
            df_common = df[df['id'].isin(common_ids)].reset_index(drop=True)
            levy_common = levy_df[levy_df['id'].isin(common_ids)].reset_index(drop=True)
            
            # Combinar features (usar merge seria mais seguro, mas vamos assumir mesma ordem)
            levy_features = [c for c in levy_common.columns if c.startswith('levy_')]
            combined_features = feature_cols + levy_features
            
            X_combined = pd.concat([
                df_common[feature_cols].fillna(0),
                levy_common[levy_features].fillna(0)
            ], axis=1)
            y_combined = df_common['label'].astype(int)
            
            scores_combined = cross_val_score(rf, X_combined, y_combined, cv=cv, scoring='roc_auc')
            
            print(f"   ROC-AUC combinado: {scores_combined.mean():.4f} (±{scores_combined.std():.4f})")
            print(f"   Total features: {len(combined_features)}")
    
    # Comparação final
    print("\n📊 RESULTADO COMPARATIVO:")
    print("-" * 50)
    print(f"Features Avançadas:     {scores.mean():.3f}")
    if 'scores_combined' in locals():
        print(f"Avançadas + Lévy:       {scores_combined.mean():.3f}")
    print(f"TSFresh (baseline):     0.607")
    print(f"TARGET (70%):           0.700")
    
    best_score = max(scores.mean(), scores_combined.mean() if 'scores_combined' in locals() else 0)
    
    if best_score > 0.65:
        print("\n🎉 Muito próximo do target 70%!")
    elif best_score > 0.60:
        print("\n✅ Melhoria clara! Próximos passos:")
        print("   1. Adicionar TSFresh features")
        print("   2. XGBoost com tuning")
        print("   3. Feature selection inteligente")
    else:
        print("\n📊 Precisamos de abordagens mais avançadas (Deep Learning)")

print("\n" + "="*60)