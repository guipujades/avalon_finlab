#!/usr/bin/env python3
"""
Versão otimizada e rápida do ensemble multi-escala.
Usa apenas 3 escalas principais: micro, média e macro.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import time

print("\n" + "="*60)
print("LEVY MULTI-ESCALA RÁPIDO - 3 ESCALAS")
print("="*60)

def calculate_levy_3scales(returns, q=20):
    """
    Calcula features em 3 escalas principais:
    - Micro (tau=0.0002): quebras rápidas
    - Média (tau=0.001): quebras intraday
    - Macro (tau=0.005): quebras de regime
    """
    tau_scales = [0.0002, 0.001, 0.005]
    scale_names = ['micro', 'media', 'macro']
    
    features = {}
    returns_clean = returns[~np.isnan(returns)]
    
    if len(returns_clean) < 100:
        return None
    
    # Pré-calcular volatilidades (mais eficiente)
    n_vol = len(returns_clean) - 2*q
    if n_vol < 50:
        return None
    
    # Volatilidade vetorizada
    vol_squared = np.array([
        np.mean(returns_clean[i:i+2*q+1]**2) 
        for i in range(n_vol)
    ])
    
    # Para cada escala
    for tau, scale in zip(tau_scales, scale_names):
        # Encontrar seções
        cumsum = np.cumsum(vol_squared)
        breaks = [0]
        last_reset = 0
        
        for i in range(1, len(cumsum)):
            if cumsum[i] - cumsum[last_reset] >= tau:
                breaks.append(i)
                last_reset = i
        
        if len(breaks) < 3:
            features[f'levy_{scale}_valid'] = 0
            features[f'levy_{scale}_mean'] = 0
            features[f'levy_{scale}_cv'] = 0
        else:
            durations = np.diff(breaks)
            features[f'levy_{scale}_valid'] = 1
            features[f'levy_{scale}_mean'] = np.mean(durations)
            features[f'levy_{scale}_cv'] = np.std(durations) / (np.mean(durations) + 1e-10)
            features[f'levy_{scale}_n_sections'] = len(durations)
            
            # Mudança entre início e fim (detecta quebra)
            if len(durations) > 5:
                early = np.mean(durations[:3])
                late = np.mean(durations[-3:])
                features[f'levy_{scale}_trend'] = (late - early) / (early + 1e-10)
            else:
                features[f'levy_{scale}_trend'] = 0
    
    # Feature importante: consistência entre escalas
    valid_means = []
    for scale in scale_names:
        if features.get(f'levy_{scale}_valid', 0) == 1:
            valid_means.append(features[f'levy_{scale}_mean'])
    
    if len(valid_means) >= 2:
        # Quebras reais aparecem em múltiplas escalas
        features['levy_multiscale_consistency'] = np.std(valid_means) / (np.mean(valid_means) + 1e-10)
    else:
        features['levy_multiscale_consistency'] = 0
    
    return features

# Processar dados
print("\n📊 Processando dados com 3 escalas...")
X_train = pd.read_parquet('database/X_train.parquet')
y_train = pd.read_parquet('database/y_train.parquet')

n_series = 300  # Menos séries para teste rápido
sample_ids = X_train.index.get_level_values('id').unique()[:n_series]

features_list = []
labels = []
start_time = time.time()

for i, series_id in enumerate(sample_ids):
    if i % 30 == 0:
        elapsed = time.time() - start_time
        rate = i / (elapsed + 1e-10)
        eta = (n_series - i) / (rate + 1e-10)
        print(f"   {i}/{n_series} ({i/n_series*100:.1f}%) - ETA: {eta:.0f}s", end='\r')
    
    returns = X_train.loc[series_id, 'value'].values
    features = calculate_levy_3scales(returns)
    
    if features is not None:
        features['id'] = series_id
        features_list.append(features)
        label = y_train.loc[series_id].iloc[0] if hasattr(y_train.loc[series_id], 'iloc') else y_train.loc[series_id]
        labels.append(int(label))

print(f"\n\n✅ Processadas {len(features_list)} séries em {time.time()-start_time:.1f}s")

if features_list:
    df = pd.DataFrame(features_list)
    df['label'] = labels
    
    # Análise rápida
    print("\n📊 Poder discriminativo por escala:")
    print("-" * 50)
    
    for scale in ['micro', 'media', 'macro']:
        feat = f'levy_{scale}_mean'
        valid = f'levy_{scale}_valid'
        
        mask = df[valid] == 1
        if mask.sum() > 10:
            m0 = df[mask & (df['label']==0)][feat].mean()
            m1 = df[mask & (df['label']==1)][feat].mean()
            diff = (m1-m0)/m0*100 if m0 > 0 else 0
            
            print(f"\n{scale.upper()}:")
            print(f"   Válidas: {mask.sum()}/{len(df)}")
            print(f"   Média sem quebra: {m0:.1f}")
            print(f"   Média com quebra: {m1:.1f}")
            print(f"   Diferença: {diff:+.1f}%")
    
    # Consistência multi-escala
    print("\n📊 Consistência entre escalas:")
    m0 = df[df['label']==0]['levy_multiscale_consistency'].mean()
    m1 = df[df['label']==1]['levy_multiscale_consistency'].mean()
    print(f"   Sem quebra: {m0:.3f}")
    print(f"   Com quebra: {m1:.3f}")
    print(f"   Diferença: {(m1-m0)/m0*100:+.1f}%")
    
    # Salvar
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'database/levy_3scales_{timestamp}.parquet'
    df.to_parquet(output_file)
    print(f"\n💾 Salvo: {output_file}")

print("\n" + "="*60)