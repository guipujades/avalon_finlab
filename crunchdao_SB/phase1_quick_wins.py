#!/usr/bin/env python3
"""
FASE 1: Quick Wins para alcançar 70% ROC-AUC
- TSFresh completo
- Wavelets + FFT features
- XGBoost com tuning
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("\n" + "="*80)
print("FASE 1: QUICK WINS - TARGET 70% ROC-AUC")
print("="*80)

# Carregar dados
print("\n📊 Carregando dados...")
X_train = pd.read_parquet('database/X_train.parquet')
y_train = pd.read_parquet('database/y_train.parquet')

print(f"   Shape: {X_train.shape}")

def extract_advanced_features(series_values):
    """
    Extrai features avançadas: Wavelets, FFT, estatísticas deslizantes, etc.
    """
    features = {}
    
    # Limpar dados
    series_clean = series_values[~np.isnan(series_values)]
    if len(series_clean) < 100:
        return None
    
    # 1. FEATURES DE FFT (ESPECTRAIS)
    print("   Calculando features espectrais...", end='')
    try:
        fft = np.fft.fft(series_clean)
        fft_freq = np.fft.fftfreq(len(series_clean))
        
        # Power spectrum
        power_spectrum = np.abs(fft)**2
        
        features.update({
            'fft_mean_power': np.mean(power_spectrum),
            'fft_max_power': np.max(power_spectrum),
            'fft_peak_freq': fft_freq[np.argmax(power_spectrum[1:])+1],  # Ignorar DC
            'fft_spectral_centroid': np.sum(fft_freq[1:] * power_spectrum[1:]) / (np.sum(power_spectrum[1:]) + 1e-10),
            'fft_spectral_rolloff': np.percentile(power_spectrum, 85),
            'fft_spectral_spread': np.sqrt(np.sum((fft_freq[1:] - features.get('fft_spectral_centroid', 0))**2 * power_spectrum[1:]) / (np.sum(power_spectrum[1:]) + 1e-10)),
        })
        print("✓")
    except:
        print("✗")
        features.update({f'fft_{name}': 0 for name in ['mean_power', 'max_power', 'peak_freq', 'spectral_centroid', 'spectral_rolloff', 'spectral_spread']})
    
    # 2. FEATURES DE WAVELETS (simplificadas)
    print("   Calculando wavelets...", end='')
    try:
        # Simulação de decomposição wavelet usando filtros simples
        # (substituição para scipy.signal.cwt que pode não estar disponível)
        
        # High-pass filter (detecta mudanças rápidas)
        diff1 = np.diff(series_clean)
        high_freq_energy = np.sum(diff1**2)
        
        # Low-pass filter (tendências)
        window = min(50, len(series_clean)//4)
        if window > 1:
            low_freq = np.convolve(series_clean, np.ones(window)/window, mode='valid')
            low_freq_energy = np.var(low_freq)
        else:
            low_freq_energy = 0
        
        features.update({
            'wavelet_high_energy': high_freq_energy,
            'wavelet_low_energy': low_freq_energy,
            'wavelet_energy_ratio': high_freq_energy / (low_freq_energy + 1e-10),
        })
        print("✓")
    except:
        print("✗")
        features.update({f'wavelet_{name}': 0 for name in ['high_energy', 'low_energy', 'energy_ratio']})
    
    # 3. FEATURES ESTATÍSTICAS DESLIZANTES
    print("   Calculando features deslizantes...", end='')
    try:
        windows = [10, 50, 100, 200]
        for w in windows:
            if len(series_clean) > w * 2:
                # Estatísticas de janela deslizante
                rolling_mean = []
                rolling_std = []
                rolling_skew = []
                
                for i in range(w, len(series_clean) - w):
                    window_data = series_clean[i-w:i+w]
                    rolling_mean.append(np.mean(window_data))
                    rolling_std.append(np.std(window_data))
                    if len(window_data) > 2:
                        # Skewness simples
                        centered = window_data - np.mean(window_data)
                        skew = np.mean(centered**3) / (np.std(window_data)**3 + 1e-10)
                        rolling_skew.append(skew)
                
                if rolling_mean:
                    features.update({
                        f'rolling_mean_std_w{w}': np.std(rolling_mean),
                        f'rolling_std_mean_w{w}': np.mean(rolling_std),
                        f'rolling_std_std_w{w}': np.std(rolling_std),
                    })
                    
                    if rolling_skew:
                        features[f'rolling_skew_std_w{w}'] = np.std(rolling_skew)
        print("✓")
    except:
        print("✗")
    
    # 4. FEATURES DE MUDANÇA DE REGIME (CUSUM-like)
    print("   Calculando detectores de mudança...", end='')
    try:
        # CUSUM simples para detectar mudança de média
        cumsum = np.cumsum(series_clean - np.mean(series_clean))
        
        features.update({
            'cusum_max': np.max(cumsum),
            'cusum_min': np.min(cumsum),
            'cusum_range': np.max(cumsum) - np.min(cumsum),
            'cusum_final': cumsum[-1],
            'cusum_max_pos': np.argmax(cumsum) / len(cumsum),  # Posição normalizada
            'cusum_min_pos': np.argmin(cumsum) / len(cumsum),
        })
        
        # Teste de mudança de variância
        mid = len(series_clean) // 2
        var_first_half = np.var(series_clean[:mid])
        var_second_half = np.var(series_clean[mid:])
        features['variance_ratio'] = var_second_half / (var_first_half + 1e-10)
        
        print("✓")
    except:
        print("✗")
    
    # 5. FEATURES DE ENTROPIA
    print("   Calculando entropia...", end='')
    try:
        # Entropia aproximada usando histograma
        hist, _ = np.histogram(series_clean, bins=20)
        hist = hist + 1e-10  # Evitar log(0)
        prob = hist / np.sum(hist)
        entropy = -np.sum(prob * np.log(prob))
        
        features['entropy'] = entropy
        
        # Entropia de diferenças (captura irregularidade)
        if len(series_clean) > 1:
            diffs = np.diff(series_clean)
            hist_diff, _ = np.histogram(diffs, bins=15)
            hist_diff = hist_diff + 1e-10
            prob_diff = hist_diff / np.sum(hist_diff)
            entropy_diff = -np.sum(prob_diff * np.log(prob_diff))
            features['entropy_diff'] = entropy_diff
        
        print("✓")
    except:
        print("✗")
        features.update({'entropy': 0, 'entropy_diff': 0})
    
    return features

# Processar amostra de séries
print("\n⚙️  Extraindo features avançadas...")
n_series = 200  # Amostra para teste rápido
sample_ids = X_train.index.get_level_values('id').unique()[:n_series]

features_list = []
labels = []

for i, series_id in enumerate(sample_ids):
    if i % 20 == 0:
        print(f"\n   Série {i+1}/{n_series}:")
    
    returns = X_train.loc[series_id, 'value'].values
    features = extract_advanced_features(returns)
    
    if features is not None:
        features['id'] = series_id
        features_list.append(features)
        label = y_train.loc[series_id].iloc[0] if hasattr(y_train.loc[series_id], 'iloc') else y_train.loc[series_id]
        labels.append(int(label))

print(f"\n\n✅ Extraídas features de {len(features_list)} séries")

if len(features_list) > 50:
    # Criar DataFrame
    df = pd.DataFrame(features_list)
    df['label'] = labels
    
    # Analisar poder discriminativo
    feature_cols = [c for c in df.columns if c != 'label' and c != 'id']
    X = df[feature_cols].fillna(0)
    y = df['label'].astype(int)
    
    print(f"\n📊 Total de features avançadas: {len(feature_cols)}")
    
    # Avaliar com Random Forest
    print("\n🎯 Avaliando com Random Forest...")
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        min_samples_leaf=3,
        class_weight='balanced',
        random_state=42
    )
    
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(rf, X, y, cv=cv, scoring='roc_auc')
    
    print(f"   ROC-AUC: {scores.mean():.4f} (±{scores.std():.4f})")
    print(f"   Scores: {scores.round(4)}")
    
    # Analisar features mais importantes
    rf.fit(X, y)
    importance_df = pd.DataFrame({
        'feature': feature_cols,
        'importance': rf.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\n🏆 Top 15 features mais importantes:")
    for _, row in importance_df.head(15).iterrows():
        print(f"   {row['feature']:<35} {row['importance']:.4f}")
    
    # Comparar com benchmarks
    print("\n📊 RESULTADO FASE 1:")
    print("-" * 50)
    print(f"Features Avançadas:     {scores.mean():.3f}")
    print(f"TSFresh (baseline):     0.607")
    print(f"Lévy Ultimate:          0.588")
    print(f"TARGET (70%):           0.700")
    
    if scores.mean() > 0.65:
        print("\n🎉 EXCELENTE! Próximo do target 70%!")
    elif scores.mean() > 0.60:
        print("\n✅ Boa melhoria! Combinando com outras abordagens pode atingir 70%")
    else:
        print("\n📊 Precisamos da FASE 2 para alcançar 70%")
    
    # Salvar resultados
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'database/advanced_features_{timestamp}.parquet'
    df.to_parquet(output_file)
    print(f"\n💾 Features salvas: {output_file}")

print("\n" + "="*80)
print("PRÓXIMOS PASSOS:")
print("1. Combinar features avançadas com Lévy e TSFresh")
print("2. Implementar XGBoost com tuning extensivo")
print("3. Se não atingir 70%, partir para FASE 2")
print("="*80)