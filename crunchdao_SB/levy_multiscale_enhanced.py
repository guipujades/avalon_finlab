#!/usr/bin/env python3
"""
Versão MELHORADA do ensemble multi-escala de Lévy.
Incorpora várias técnicas para aumentar o ROC-AUC.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import time

print("\n" + "="*60)
print("LEVY MULTI-ESCALA ENHANCED - VERSÃO MELHORADA")
print("="*60)

def calculate_levy_enhanced(returns, q=20):
    """
    Versão melhorada com:
    1. Mais escalas (5 em vez de 3)
    2. Features de interação entre escalas
    3. Features de transição/mudança
    4. Detecção de anomalias por escala
    """
    # 5 escalas para melhor cobertura
    tau_scales = [0.0001, 0.0003, 0.001, 0.003, 0.01]
    scale_names = ['ultra_micro', 'micro', 'media', 'macro', 'ultra_macro']
    
    features = {}
    returns_clean = returns[~np.isnan(returns)]
    
    if len(returns_clean) < 150:  # Precisamos de mais pontos
        return None
    
    # Pré-calcular volatilidades
    n_vol = len(returns_clean) - 2*q
    if n_vol < 100:
        return None
    
    # Volatilidade local com diferentes métodos
    vol_squared = np.array([
        np.mean(returns_clean[i:i+2*q+1]**2) 
        for i in range(n_vol)
    ])
    
    # Volatilidade usando desvio absoluto (mais robusto)
    vol_mad = np.array([
        np.mean(np.abs(returns_clean[i:i+2*q+1])) 
        for i in range(n_vol)
    ])
    
    scale_durations = {}
    scale_sections = {}
    
    # Para cada escala
    for scale_idx, (tau, scale) in enumerate(zip(tau_scales, scale_names)):
        # Usar volatilidade ao quadrado para tau pequeno, MAD para tau grande
        if scale_idx < 2:  # Ultra micro e micro
            vol_to_use = vol_squared
        else:  # Escalas maiores
            vol_to_use = vol_mad**2
        
        # Encontrar seções
        cumsum = np.cumsum(vol_to_use)
        breaks = [0]
        last_reset = 0
        
        for i in range(1, len(cumsum)):
            if cumsum[i] - cumsum[last_reset] >= tau:
                breaks.append(i)
                last_reset = i
        
        if len(breaks) < 3:
            features[f'levy_{scale}_valid'] = 0
            scale_durations[scale] = []
        else:
            durations = np.diff(breaks)
            scale_durations[scale] = durations
            scale_sections[scale] = len(durations)
            
            features[f'levy_{scale}_valid'] = 1
            features[f'levy_{scale}_mean'] = np.mean(durations)
            features[f'levy_{scale}_median'] = np.median(durations)
            features[f'levy_{scale}_cv'] = np.std(durations) / (np.mean(durations) + 1e-10)
            features[f'levy_{scale}_iqr'] = np.percentile(durations, 75) - np.percentile(durations, 25)
            features[f'levy_{scale}_n_sections'] = len(durations)
            
            # Feature importante: razão entre quartis
            q1 = np.percentile(durations, 25)
            q3 = np.percentile(durations, 75)
            features[f'levy_{scale}_q3q1_ratio'] = q3 / (q1 + 1e-10)
            
            # Detectar mudança ao longo do tempo
            if len(durations) > 10:
                # Dividir em 3 partes
                n_third = len(durations) // 3
                early = np.mean(durations[:n_third])
                middle = np.mean(durations[n_third:2*n_third])
                late = np.mean(durations[2*n_third:])
                
                # Padrão de evolução
                features[f'levy_{scale}_early_late_ratio'] = late / (early + 1e-10)
                features[f'levy_{scale}_acceleration'] = (late - early) / (middle + 1e-10)
                
                # Detectar ponto de mudança
                max_diff = 0
                change_point = 0
                for i in range(3, len(durations)-3):
                    before = np.mean(durations[:i])
                    after = np.mean(durations[i:])
                    diff = abs(after - before) / (before + 1e-10)
                    if diff > max_diff:
                        max_diff = diff
                        change_point = i / len(durations)
                
                features[f'levy_{scale}_max_change'] = max_diff
                features[f'levy_{scale}_change_position'] = change_point
            else:
                features[f'levy_{scale}_early_late_ratio'] = 1.0
                features[f'levy_{scale}_acceleration'] = 0.0
                features[f'levy_{scale}_max_change'] = 0.0
                features[f'levy_{scale}_change_position'] = 0.5
    
    # FEATURES DE INTERAÇÃO ENTRE ESCALAS (muito importantes!)
    valid_scales = [s for s in scale_names if scale_durations.get(s, [])]
    
    if len(valid_scales) >= 2:
        # 1. Consistência de padrões entre escalas
        mean_durations = []
        cv_values = []
        
        for scale in valid_scales:
            if len(scale_durations[scale]) > 0:
                mean_durations.append(np.mean(scale_durations[scale]))
                cv_values.append(np.std(scale_durations[scale]) / (np.mean(scale_durations[scale]) + 1e-10))
        
        # Padrão de escala (deve ser crescente para séries normais)
        if len(mean_durations) >= 3:
            # Correlação entre índice de escala e duração média
            scale_correlation = np.corrcoef(range(len(mean_durations)), mean_durations)[0, 1]
            features['levy_scale_pattern'] = scale_correlation
            
            # Razão entre escalas extremas
            features['levy_extreme_scales_ratio'] = mean_durations[-1] / (mean_durations[0] + 1e-10)
            
            # Variabilidade entre escalas
            features['levy_cross_scale_std'] = np.std(mean_durations) / (np.mean(mean_durations) + 1e-10)
        else:
            features['levy_scale_pattern'] = 0
            features['levy_extreme_scales_ratio'] = 1
            features['levy_cross_scale_std'] = 0
        
        # 2. Propagação de instabilidade entre escalas
        if len(cv_values) >= 2:
            # CV deve aumentar com quebra
            features['levy_cv_trend'] = cv_values[-1] - cv_values[0]
            features['levy_cv_ratio'] = cv_values[-1] / (cv_values[0] + 1e-10)
    
    # 3. Features de detecção de anomalia multi-escala
    n_valid_scales = sum(1 for s in scale_names if features.get(f'levy_{s}_valid', 0) == 1)
    features['levy_n_valid_scales'] = n_valid_scales
    
    # Razão de seções entre escalas consecutivas (deve ser ~2-3 normalmente)
    section_ratios = []
    for i in range(len(scale_names)-1):
        if (features.get(f'levy_{scale_names[i]}_valid', 0) == 1 and 
            features.get(f'levy_{scale_names[i+1]}_valid', 0) == 1):
            n1 = features.get(f'levy_{scale_names[i]}_n_sections', 0)
            n2 = features.get(f'levy_{scale_names[i+1]}_n_sections', 0)
            if n2 > 0:
                section_ratios.append(n1 / n2)
    
    if section_ratios:
        features['levy_section_ratio_mean'] = np.mean(section_ratios)
        features['levy_section_ratio_std'] = np.std(section_ratios)
    else:
        features['levy_section_ratio_mean'] = 0
        features['levy_section_ratio_std'] = 0
    
    # 4. Feature especial: "Assinatura Multi-Escala de Quebra"
    # Combina os padrões mais discriminativos
    if n_valid_scales >= 3:
        micro_mean = features.get('levy_micro_mean', 0)
        macro_mean = features.get('levy_macro_mean', 0)
        
        if micro_mean > 0 and macro_mean > 0:
            # Quebras estruturais têm: micro pequeno, macro grande
            features['levy_break_signature'] = macro_mean / micro_mean
        else:
            features['levy_break_signature'] = 1
    else:
        features['levy_break_signature'] = 0
    
    return features

# Processar dados
print("\n📊 Carregando dados...")
X_train = pd.read_parquet('database/X_train.parquet')
y_train = pd.read_parquet('database/y_train.parquet')

print("\n🔧 Configuração Enhanced:")
print("   - 5 escalas (ultra_micro até ultra_macro)")
print("   - Features de interação entre escalas")
print("   - Detecção de pontos de mudança")
print("   - Assinatura multi-escala de quebra")

# Processar amostra
n_series = 300
sample_ids = X_train.index.get_level_values('id').unique()[:n_series]

features_list = []
labels = []
start_time = time.time()

print(f"\n⚙️  Processando {n_series} séries...")
for i, series_id in enumerate(sample_ids):
    if i % 30 == 0:
        print(f"   {i}/{n_series} ({i/n_series*100:.1f}%)", end='\r')
    
    returns = X_train.loc[series_id, 'value'].values
    features = calculate_levy_enhanced(returns)
    
    if features is not None:
        features['id'] = series_id
        features_list.append(features)
        label = y_train.loc[series_id].iloc[0] if hasattr(y_train.loc[series_id], 'iloc') else y_train.loc[series_id]
        labels.append(int(label))

print(f"\n\n✅ Processadas {len(features_list)} séries em {time.time()-start_time:.1f}s")

if features_list:
    df = pd.DataFrame(features_list)
    df['label'] = labels
    
    # Análise das features mais importantes
    print("\n📊 Features Enhanced mais discriminativas:")
    print("-" * 60)
    
    # Features de interação
    interaction_features = [
        'levy_scale_pattern',
        'levy_extreme_scales_ratio', 
        'levy_cross_scale_std',
        'levy_cv_trend',
        'levy_cv_ratio',
        'levy_break_signature'
    ]
    
    for feat in interaction_features:
        if feat in df.columns:
            # Remover valores inválidos
            valid_mask = ~df[feat].isna() & (df[feat] != 0)
            if valid_mask.sum() > 20:
                m0 = df[valid_mask & (df['label']==0)][feat].mean()
                m1 = df[valid_mask & (df['label']==1)][feat].mean()
                
                if abs(m0) > 1e-10:
                    diff = (m1-m0)/abs(m0)*100
                    print(f"\n{feat}:")
                    print(f"   Sem quebra: {m0:.3f}")
                    print(f"   Com quebra: {m1:.3f}")
                    print(f"   Diferença: {diff:+.1f}%")
    
    # Salvar
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'database/levy_enhanced_{timestamp}.parquet'
    df.to_parquet(output_file)
    
    print(f"\n💾 Features Enhanced salvas: {output_file}")
    print(f"   Total de features: {len([c for c in df.columns if c.startswith('levy_')])}")

print("\n" + "="*60)
print("💡 MELHORIAS IMPLEMENTADAS:")
print("1. Mais escalas (5) para melhor cobertura")
print("2. Features de interação entre escalas") 
print("3. Detecção de pontos de mudança")
print("4. Métricas de propagação de instabilidade")
print("5. Assinatura multi-escala de quebra")
print("="*60)