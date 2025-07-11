#!/usr/bin/env python3
"""
Versão rápida para extrair features de Lévy otimizadas para HFT.
"""

import pandas as pd
import numpy as np
from datetime import datetime

print("\n" + "="*60)
print("LEVY HFT - EXTRAÇÃO RÁPIDA")
print("="*60)

# Parâmetros otimizados para ~2400 pontos de retornos
TAU = 0.0002  # Para ~100 seções por série
Q = 20        # Janela de volatilidade

def calculate_levy_features_fast(returns):
    """Versão simplificada e rápida."""
    try:
        returns_clean = returns[~np.isnan(returns)]
        if len(returns_clean) < 100:
            return None
        
        # Volatilidade local simples
        vol_window = 2 * Q + 1
        n_points = len(returns_clean) - vol_window + 1
        
        if n_points < 50:
            return None
        
        # Calcular volatilidades de forma vetorizada
        vol_squared = np.zeros(n_points)
        for i in range(n_points):
            window = returns_clean[i:i+vol_window]
            vol_squared[i] = np.mean(window**2)
        
        # Encontrar seções
        cumsum = np.cumsum(vol_squared)
        section_indices = [0]
        last_reset = 0
        
        for i in range(1, len(cumsum)):
            if cumsum[i] - cumsum[last_reset] >= TAU:
                section_indices.append(i)
                last_reset = i
        
        if len(section_indices) < 5:
            return None
        
        # Durações
        durations = np.diff(section_indices)
        
        # Features básicas mas discriminativas
        return {
            'levy_duration_mean': np.mean(durations),
            'levy_duration_cv': np.std(durations) / (np.mean(durations) + 1e-10),
            'levy_duration_min': np.min(durations),
            'levy_duration_max': np.max(durations),
            'levy_n_sections': len(durations),
            'levy_jump_ratio': np.sum(durations > 2*np.median(durations)) / len(durations),
        }
        
    except:
        return None

# Processar dados
print(f"\n📊 Configuração: tau={TAU}, q={Q}")
print("   Processando 500 séries...")

X_train = pd.read_parquet('database/X_train.parquet')
y_train = pd.read_parquet('database/y_train.parquet')

n_series = 500
sample_ids = X_train.index.get_level_values('id').unique()[:n_series]

features_list = []
labels = []
success = 0

for i, series_id in enumerate(sample_ids):
    if i % 50 == 0:
        print(f"   {i}/{n_series}...", end='\r')
    
    returns = X_train.loc[series_id, 'value'].values
    features = calculate_levy_features_fast(returns)
    
    if features is not None:
        features['id'] = series_id
        features_list.append(features)
        label = y_train.loc[series_id].iloc[0] if hasattr(y_train.loc[series_id], 'iloc') else y_train.loc[series_id]
        labels.append(int(label))
        success += 1

print(f"\n\n✅ Processamento concluído!")
print(f"   Sucesso: {success}/{n_series} ({success/n_series*100:.1f}%)")

if len(features_list) > 0:
    df = pd.DataFrame(features_list)
    df['label'] = labels
    
    # Análise rápida
    for feat in [col for col in df.columns if col.startswith('levy_')]:
        mean_0 = df[df['label']==0][feat].mean()
        mean_1 = df[df['label']==1][feat].mean()
        diff = (mean_1 - mean_0) / (abs(mean_0) + 1e-10) * 100
        if abs(diff) > 5:
            print(f"\n{feat}:")
            print(f"   Classe 0: {mean_0:.2f}")
            print(f"   Classe 1: {mean_1:.2f}")
            print(f"   Diferença: {diff:+.1f}%")
    
    # Salvar
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'database/levy_features_hft_{timestamp}.parquet'
    df.to_parquet(output_file)
    print(f"\n💾 Salvo em: {output_file}")

print("\n" + "="*60)