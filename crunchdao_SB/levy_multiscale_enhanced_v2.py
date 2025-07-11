#!/usr/bin/env python3
"""
Versão MELHORADA do ensemble multi-escala - V2 corrigida.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import time

print("\n" + "="*60)
print("LEVY MULTI-ESCALA ENHANCED V2")
print("="*60)

def calculate_levy_enhanced_v2(returns, q=20):
    """
    Versão melhorada com múltiplas técnicas de otimização.
    """
    # 5 escalas estratégicas
    tau_scales = [0.0001, 0.0003, 0.001, 0.003, 0.01]
    scale_names = ['ultra_micro', 'micro', 'media', 'macro', 'ultra_macro']
    
    features = {}
    returns_clean = returns[~np.isnan(returns)]
    
    if len(returns_clean) < 150:
        return None
    
    # Calcular volatilidades
    n_vol = len(returns_clean) - 2*q
    if n_vol < 100:
        return None
    
    vol_squared = np.array([
        np.mean(returns_clean[i:i+2*q+1]**2) 
        for i in range(n_vol)
    ])
    
    # Guardar estatísticas por escala
    scale_stats = {}
    
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
            features[f'levy_{scale}_mean'] = -1
            features[f'levy_{scale}_cv'] = -1
            scale_stats[scale] = None
        else:
            durations = np.diff(breaks)
            
            features[f'levy_{scale}_valid'] = 1
            features[f'levy_{scale}_mean'] = np.mean(durations)
            features[f'levy_{scale}_std'] = np.std(durations)
            features[f'levy_{scale}_cv'] = np.std(durations) / (np.mean(durations) + 1e-10)
            features[f'levy_{scale}_n_sections'] = len(durations)
            
            # Guardar para análise entre escalas
            scale_stats[scale] = {
                'mean': np.mean(durations),
                'cv': features[f'levy_{scale}_cv'],
                'n': len(durations)
            }
            
            # Detecção de mudança
            if len(durations) > 6:
                mid = len(durations) // 2
                first_half = np.mean(durations[:mid])
                second_half = np.mean(durations[mid:])
                features[f'levy_{scale}_trend'] = (second_half - first_half) / (first_half + 1e-10)
            else:
                features[f'levy_{scale}_trend'] = 0
    
    # FEATURES ENTRE ESCALAS
    valid_stats = [v for v in scale_stats.values() if v is not None]
    
    if len(valid_stats) >= 2:
        # Padrão de crescimento entre escalas
        means = [s['mean'] for s in valid_stats]
        cvs = [s['cv'] for s in valid_stats]
        
        # As durações devem crescer com tau maior
        if len(means) >= 3:
            # Correlação indica se o padrão é normal
            features['levy_scale_correlation'] = np.corrcoef(range(len(means)), means)[0, 1]
        else:
            features['levy_scale_correlation'] = 0
        
        # Razão entre escalas extremas
        features['levy_scale_ratio'] = means[-1] / (means[0] + 1e-10)
        
        # Propagação de variabilidade
        features['levy_cv_propagation'] = cvs[-1] - cvs[0]
    else:
        features['levy_scale_correlation'] = 0
        features['levy_scale_ratio'] = 1
        features['levy_cv_propagation'] = 0
    
    # ASSINATURA DE QUEBRA
    # Combinação dos padrões mais discriminativos
    micro_mean = features.get('levy_micro_mean', -1)
    macro_mean = features.get('levy_macro_mean', -1)
    
    if micro_mean > 0 and macro_mean > 0:
        # Quebras têm micro pequeno e macro grande
        features['levy_break_signature'] = macro_mean / micro_mean
    else:
        features['levy_break_signature'] = 0
    
    return features

# Função para avaliar features
def evaluate_features(df, feature_cols):
    """Avalia o poder discriminativo das features."""
    results = []
    
    for feat in feature_cols:
        if feat in df.columns:
            # Apenas valores válidos
            valid = df[feat] > -1 if 'mean' in feat or 'cv' in feat else df[feat].notna()
            
            if valid.sum() > 20:
                m0 = df[valid & (df['label']==0)][feat].mean()
                m1 = df[valid & (df['label']==1)][feat].mean()
                
                if abs(m0) > 1e-10:
                    diff_pct = (m1 - m0) / abs(m0) * 100
                    results.append({
                        'feature': feat,
                        'mean_0': m0,
                        'mean_1': m1,
                        'diff_pct': diff_pct,
                        'abs_diff': abs(diff_pct)
                    })
    
    return pd.DataFrame(results).sort_values('abs_diff', ascending=False)

# Processar dados
print("\n📊 Processando dados com técnicas melhoradas...")
X_train = pd.read_parquet('database/X_train.parquet')
y_train = pd.read_parquet('database/y_train.parquet')

n_series = 400  # Mais séries para melhor estimativa
sample_ids = X_train.index.get_level_values('id').unique()[:n_series]

features_list = []
labels = []

for i, series_id in enumerate(sample_ids):
    if i % 40 == 0:
        print(f"   Processadas: {i}/{n_series}", end='\r')
    
    returns = X_train.loc[series_id, 'value'].values
    features = calculate_levy_enhanced_v2(returns)
    
    if features is not None:
        features['id'] = series_id
        features_list.append(features)
        label = y_train.loc[series_id].iloc[0] if hasattr(y_train.loc[series_id], 'iloc') else y_train.loc[series_id]
        labels.append(int(label))

print(f"\n✅ Processadas {len(features_list)} séries com sucesso")

if features_list:
    df = pd.DataFrame(features_list)
    df['label'] = labels
    
    # Avaliar todas as features
    feature_cols = [c for c in df.columns if c.startswith('levy_')]
    eval_df = evaluate_features(df, feature_cols)
    
    print("\n📊 Top 10 Features mais discriminativas:")
    print("-" * 70)
    print(f"{'Feature':<35} {'Sem quebra':>12} {'Com quebra':>12} {'Diff %':>10}")
    print("-" * 70)
    
    for _, row in eval_df.head(10).iterrows():
        print(f"{row['feature']:<35} {row['mean_0']:>12.3f} {row['mean_1']:>12.3f} {row['diff_pct']:>10.1f}%")
    
    # Features especiais de interação
    print("\n📊 Features de Interação Multi-Escala:")
    print("-" * 60)
    
    special_features = ['levy_scale_correlation', 'levy_scale_ratio', 
                       'levy_cv_propagation', 'levy_break_signature']
    
    for feat in special_features:
        if feat in eval_df['feature'].values:
            row = eval_df[eval_df['feature'] == feat].iloc[0]
            print(f"\n{feat}:")
            print(f"   Sem quebra: {row['mean_0']:.3f}")
            print(f"   Com quebra: {row['mean_1']:.3f}")
            print(f"   Diferença: {row['diff_pct']:+.1f}%")
    
    # Salvar
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'database/levy_enhanced_v2_{timestamp}.parquet'
    df.to_parquet(output_file)
    
    print(f"\n💾 Salvo: {output_file}")
    print(f"   Features: {len(feature_cols)}")
    
    # Sugestões de melhorias adicionais
    print("\n💡 PRÓXIMAS MELHORIAS POSSÍVEIS:")
    print("-" * 60)
    print("1. Feature Engineering:")
    print("   - Criar razões entre features de diferentes escalas")
    print("   - Adicionar features polinomiais das melhores")
    print("   - Usar transformações log nas durações")
    
    print("\n2. Seleção Automática:")
    print("   - Usar mutual information para seleção")
    print("   - Aplicar PCA nas features por escala")
    print("   - Criar meta-features com autoencoders")
    
    print("\n3. Ensemble de Modelos:")
    print("   - Treinar um modelo por escala")
    print("   - Combinar predições com stacking")
    print("   - Usar gradient boosting com features customizadas")

print("\n" + "="*60)