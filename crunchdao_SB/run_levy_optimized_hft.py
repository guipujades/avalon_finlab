#!/usr/bin/env python3
"""
Extração otimizada de features de Lévy para dados de média/alta frequência.
Adaptado para RETORNOS (não preços) com ~2400 pontos por série.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import glob
import os

print("\n" + "="*60)
print("LEVY SECTIONS - OTIMIZADO PARA RETORNOS HFT")
print("="*60)

def calculate_levy_features_returns(returns, tau=0.0002, q=20):
    """
    Calcula features de Lévy diretamente de retornos (não preços).
    
    Para ~2400 pontos de retornos:
    - tau: 0.0001-0.0005 (captura 50-200 seções)
    - q: 15-30 (estabilidade em alta frequência)
    """
    try:
        # Remover NaN
        returns_clean = returns[~np.isnan(returns)]
        if len(returns_clean) < 2 * q + 50:
            return None
        
        # 1. Estimar volatilidade local (realized volatility)
        volatilities = []
        for i in range(q, len(returns_clean) - q):
            # Janela centrada
            window = returns_clean[i-q:i+q+1]
            # Realized volatility
            vol = np.sqrt(np.mean(window**2))
            volatilities.append(max(vol, 1e-10))
        
        volatilities = np.array(volatilities)
        
        # 2. Construir seções de Lévy
        cumsum = 0
        section_starts = [0]
        section_durations = []
        section_vols = []
        
        for i in range(len(volatilities)):
            cumsum += volatilities[i]**2
            
            if cumsum >= tau:
                duration = i - section_starts[-1]
                if duration > 0:
                    section_durations.append(duration)
                    # Volatilidade média da seção
                    section_vol = np.mean(volatilities[section_starts[-1]:i])
                    section_vols.append(section_vol)
                    section_starts.append(i)
                    cumsum = 0
        
        if len(section_durations) < 10:  # Precisamos de mais seções em HFT
            return None
        
        durations = np.array(section_durations)
        vols = np.array(section_vols)
        
        # 3. Features adaptadas para HFT
        features = {
            # Durações (tempo de volatilidade)
            'levy_duration_mean': np.mean(durations),
            'levy_duration_std': np.std(durations),
            'levy_duration_cv': np.std(durations) / np.mean(durations),
            'levy_duration_min': np.min(durations),
            'levy_duration_max': np.max(durations),
            'levy_duration_skew': _safe_skew(durations),
            
            # Mudanças de regime (crucial em HFT)
            'levy_regime_stability': np.min(durations) / np.max(durations),
            'levy_duration_jumps': _count_jumps(durations, threshold=2.0),
            
            # Volatilidade por seção
            'levy_vol_mean': np.mean(vols),
            'levy_vol_cv': np.std(vols) / np.mean(vols) if np.mean(vols) > 0 else 0,
            
            # Aceleração/desaceleração
            'levy_acceleration': _measure_acceleration(durations),
            
            # Contagens
            'levy_n_sections': len(durations),
            
            # Normalização (validação teórica)
            'levy_norm_test': _test_normalization(returns_clean, section_starts, tau),
        }
        
        return features
        
    except Exception as e:
        return None

def _safe_skew(x):
    """Skewness seguro."""
    if len(x) < 3:
        return 0
    mean = np.mean(x)
    std = np.std(x)
    if std == 0:
        return 0
    return np.mean(((x - mean) / std) ** 3)

def _count_jumps(durations, threshold=2.0):
    """Conta mudanças abruptas (jumps) nas durações."""
    if len(durations) < 2:
        return 0
    jumps = 0
    for i in range(1, len(durations)):
        ratio = durations[i] / durations[i-1]
        if ratio > threshold or ratio < 1/threshold:
            jumps += 1
    return jumps

def _measure_acceleration(durations):
    """Mede tendência de aceleração/desaceleração."""
    if len(durations) < 3:
        return 0
    # Regressão linear simples no log das durações
    x = np.arange(len(durations))
    y = np.log(durations + 1)
    if np.std(x) == 0 or np.std(y) == 0:
        return 0
    correlation = np.corrcoef(x, y)[0, 1]
    return correlation  # Negativo = aceleração, Positivo = desaceleração

def _test_normalization(returns, section_starts, tau):
    """Testa se as somas normalizadas são ~N(0,1)."""
    if len(section_starts) < 2:
        return 0
    
    normalized_sums = []
    for i in range(len(section_starts)-1):
        start = section_starts[i]
        end = section_starts[i+1]
        section_sum = np.sum(returns[start:end])
        # Normalizar por sqrt(tau)
        norm_sum = section_sum / np.sqrt(tau)
        normalized_sums.append(norm_sum)
    
    if len(normalized_sums) < 4:
        return 0
    
    # Kurtosis deve ser ~0 para normal
    return abs(_safe_kurtosis(normalized_sums))

def _safe_kurtosis(x):
    """Kurtosis excess seguro."""
    if len(x) < 4:
        return 0
    mean = np.mean(x)
    std = np.std(x)
    if std == 0:
        return 0
    return np.mean(((x - mean) / std) ** 4) - 3

# Processar dados
print("\n📊 Carregando dados...")
X_train = pd.read_parquet('database/X_train.parquet')
y_train = pd.read_parquet('database/y_train.parquet')

# Parâmetros otimizados para ~2400 pontos
configs = [
    {'tau': 0.0001, 'q': 20, 'desc': 'Muitas seções (~200)'},
    {'tau': 0.0002, 'q': 20, 'desc': 'Balanceado (~100 seções)'},
    {'tau': 0.0003, 'q': 25, 'desc': 'Menos seções (~70)'},
    {'tau': 0.0005, 'q': 30, 'desc': 'Poucas seções (~40)'},
]

print("\n🔬 Testando configurações otimizadas:")
print("-" * 60)

best_config = None
best_separation = 0

for config in configs:
    print(f"\nTau={config['tau']}, q={config['q']} - {config['desc']}")
    
    # Processar amostra
    n_test = 200
    sample_ids = X_train.index.get_level_values('id').unique()[:n_test]
    
    features_list = []
    labels = []
    
    for series_id in sample_ids:
        series_data = X_train.loc[series_id]
        returns = series_data['value'].values
        
        features = calculate_levy_features_returns(
            returns, 
            tau=config['tau'], 
            q=config['q']
        )
        
        if features is not None:
            features_list.append(features)
            label = y_train.loc[series_id].iloc[0] if hasattr(y_train.loc[series_id], 'iloc') else y_train.loc[series_id]
            labels.append(int(label))
    
    if len(features_list) > 50:
        df_features = pd.DataFrame(features_list)
        df_features['label'] = labels
        
        # Análise de separação
        mean_0 = df_features[df_features['label']==0]['levy_duration_mean'].mean()
        mean_1 = df_features[df_features['label']==1]['levy_duration_mean'].mean()
        sep = abs(mean_1 - mean_0) / (mean_0 + 0.001) * 100
        
        jumps_0 = df_features[df_features['label']==0]['levy_duration_jumps'].mean()
        jumps_1 = df_features[df_features['label']==1]['levy_duration_jumps'].mean()
        
        print(f"   ✓ Sucesso: {len(features_list)}/{n_test}")
        print(f"   Duração média: {mean_0:.1f} vs {mean_1:.1f} (sep: {sep:.1f}%)")
        print(f"   Jumps médios: {jumps_0:.1f} vs {jumps_1:.1f}")
        print(f"   Seções/série: {df_features['levy_n_sections'].mean():.0f}")
        
        if sep > best_separation:
            best_separation = sep
            best_config = config

# Processar dataset completo com melhor configuração
if best_config:
    print(f"\n🎯 Melhor configuração: tau={best_config['tau']}, q={best_config['q']}")
    print("   Processando dataset completo...")
    
    n_series = min(1000, len(X_train.index.get_level_values('id').unique()))
    sample_ids = X_train.index.get_level_values('id').unique()[:n_series]
    
    all_features = []
    all_labels = []
    
    for i, series_id in enumerate(sample_ids):
        if i % 100 == 0:
            print(f"   Processando {i}/{n_series}...", end='\r')
        
        series_data = X_train.loc[series_id]
        returns = series_data['value'].values
        
        features = calculate_levy_features_returns(
            returns,
            tau=best_config['tau'],
            q=best_config['q']
        )
        
        if features is not None:
            features['id'] = series_id
            all_features.append(features)
            label = y_train.loc[series_id].iloc[0] if hasattr(y_train.loc[series_id], 'iloc') else y_train.loc[series_id]
            all_labels.append(int(label))
    
    # Salvar
    df_final = pd.DataFrame(all_features)
    df_final['label'] = all_labels
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'database/levy_features_hft_{timestamp}.parquet'
    df_final.to_parquet(output_file)
    
    print(f"\n\n✅ Features salvas: {output_file}")
    print(f"   Total: {len(df_final)} séries processadas")
    print(f"   Sucesso: {len(df_final)/n_series*100:.1f}%")

print("\n" + "="*60)