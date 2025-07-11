#!/usr/bin/env python3
"""
Implementação do Ensemble Multi-escala de Lévy para IDENTIFICAÇÃO de quebras estruturais.
Objetivo: Classificar se uma série temporal TEM ou NÃO quebra estrutural.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import time

print("\n" + "="*60)
print("LEVY MULTI-ESCALA - IDENTIFICAÇÃO DE QUEBRAS")
print("="*60)

def calculate_levy_multiscale_features(returns, tau_scales=[0.0001, 0.0005, 0.001, 0.005, 0.01], q=20):
    """
    Extrai features de Lévy em múltiplas escalas temporais.
    Cada escala captura diferentes tipos de quebras estruturais.
    """
    all_features = {}
    
    # Limpar dados
    returns_clean = returns[~np.isnan(returns)]
    if len(returns_clean) < 2 * q + 50:
        return None
    
    for tau_idx, tau in enumerate(tau_scales):
        scale_name = f"s{tau_idx+1}"  # s1=micro, s2, s3, s4, s5=macro
        
        try:
            # Calcular volatilidade local
            volatilities = []
            for i in range(q, len(returns_clean) - q):
                window = returns_clean[i-q:i+q+1]
                vol = np.sqrt(np.mean(window**2))
                volatilities.append(max(vol, 1e-10))
            
            # Construir seções de Lévy
            cumsum = 0
            section_durations = []
            section_starts = [0]
            
            for i, vol in enumerate(volatilities):
                cumsum += vol**2
                
                if cumsum >= tau:
                    duration = i - section_starts[-1]
                    if duration > 0:
                        section_durations.append(duration)
                        section_starts.append(i)
                        cumsum = 0
            
            # Se tiver poucas seções nesta escala, ainda é informativo
            if len(section_durations) < 2:
                # Escala muito pequena ou muito grande para esta série
                all_features[f'levy_valid_{scale_name}'] = 0
                all_features[f'levy_duration_mean_{scale_name}'] = -1
                all_features[f'levy_duration_cv_{scale_name}'] = -1
                all_features[f'levy_n_sections_{scale_name}'] = len(section_durations)
            else:
                durations = np.array(section_durations)
                
                # Features que indicam quebras estruturais
                all_features[f'levy_valid_{scale_name}'] = 1
                all_features[f'levy_duration_mean_{scale_name}'] = np.mean(durations)
                all_features[f'levy_duration_cv_{scale_name}'] = np.std(durations) / (np.mean(durations) + 1e-10)
                all_features[f'levy_duration_range_{scale_name}'] = np.max(durations) - np.min(durations)
                all_features[f'levy_n_sections_{scale_name}'] = len(durations)
                
                # Detector de mudança abrupta (sinal de quebra)
                if len(durations) > 5:
                    # Razão entre primeira e última metade
                    mid = len(durations) // 2
                    first_half_mean = np.mean(durations[:mid])
                    second_half_mean = np.mean(durations[mid:])
                    all_features[f'levy_trend_ratio_{scale_name}'] = second_half_mean / (first_half_mean + 1e-10)
                else:
                    all_features[f'levy_trend_ratio_{scale_name}'] = 1.0
                    
        except Exception as e:
            # Se falhar nesta escala, marcar como inválida
            all_features[f'levy_valid_{scale_name}'] = 0
            all_features[f'levy_duration_mean_{scale_name}'] = -1
    
    # Features agregadas entre escalas (muito importantes!)
    valid_means = [all_features[f'levy_duration_mean_s{i+1}'] 
                   for i in range(len(tau_scales)) 
                   if all_features.get(f'levy_valid_s{i+1}', 0) == 1 
                   and all_features.get(f'levy_duration_mean_s{i+1}', -1) > 0]
    
    if len(valid_means) >= 2:
        # Consistência entre escalas (quebras reais aparecem em múltiplas escalas)
        all_features['levy_cross_scale_cv'] = np.std(valid_means) / (np.mean(valid_means) + 1e-10)
        all_features['levy_cross_scale_range'] = np.max(valid_means) - np.min(valid_means)
        
        # Padrão de aceleração através das escalas
        if len(valid_means) >= 3:
            # Se durações diminuem com tau maior = quebra estrutural
            correlation = np.corrcoef(range(len(valid_means)), valid_means)[0, 1]
            all_features['levy_scale_correlation'] = correlation
        else:
            all_features['levy_scale_correlation'] = 0
    else:
        all_features['levy_cross_scale_cv'] = 0
        all_features['levy_cross_scale_range'] = 0
        all_features['levy_scale_correlation'] = 0
    
    return all_features

# Processar dados
print("\n📊 Carregando dados de treino...")
X_train = pd.read_parquet('database/X_train.parquet')
y_train = pd.read_parquet('database/y_train.parquet')

# Configuração multi-escala
tau_scales = [0.0001, 0.0005, 0.001, 0.005, 0.01]
print(f"\n🔧 Configuração multi-escala:")
print(f"   Escalas tau: {tau_scales}")
print(f"   Total de features por série: ~{len(tau_scales) * 5 + 3}")

# Processar amostra
n_series = 500
sample_ids = X_train.index.get_level_values('id').unique()[:n_series]

print(f"\n⚙️  Processando {n_series} séries...")
features_list = []
labels = []
start_time = time.time()

for i, series_id in enumerate(sample_ids):
    if i % 50 == 0:
        print(f"   Processadas: {i}/{n_series} ({i/n_series*100:.1f}%)", end='\r')
    
    # Obter retornos
    returns = X_train.loc[series_id, 'value'].values
    
    # Calcular features multi-escala
    features = calculate_levy_multiscale_features(returns, tau_scales)
    
    if features is not None:
        features['id'] = series_id
        features_list.append(features)
        
        # Label
        label = y_train.loc[series_id].iloc[0] if hasattr(y_train.loc[series_id], 'iloc') else y_train.loc[series_id]
        labels.append(int(label))

elapsed = time.time() - start_time
print(f"\n\n✅ Processamento concluído em {elapsed:.1f}s")
print(f"   Sucesso: {len(features_list)}/{n_series} ({len(features_list)/n_series*100:.1f}%)")

if len(features_list) > 0:
    # Criar DataFrame
    df = pd.DataFrame(features_list)
    df['label'] = labels
    
    # Análise por escala
    print("\n📊 Análise de discriminação por escala:")
    print("-" * 60)
    
    scales = ['s1 (micro)', 's2', 's3 (média)', 's4', 's5 (macro)']
    for i, scale in enumerate(scales):
        scale_id = f's{i+1}'
        feat_name = f'levy_duration_mean_{scale_id}'
        
        if feat_name in df.columns:
            # Apenas séries válidas nesta escala
            valid_mask = df[f'levy_valid_{scale_id}'] == 1
            if valid_mask.sum() > 10:
                mean_0 = df[valid_mask & (df['label'] == 0)][feat_name].mean()
                mean_1 = df[valid_mask & (df['label'] == 1)][feat_name].mean()
                
                if not np.isnan(mean_0) and not np.isnan(mean_1) and mean_0 > 0:
                    diff = (mean_1 - mean_0) / mean_0 * 100
                    n_valid = valid_mask.sum()
                    print(f"\n{scale} (tau={tau_scales[i]}):")
                    print(f"   Séries válidas: {n_valid}/{len(df)} ({n_valid/len(df)*100:.1f}%)")
                    print(f"   Duração média - Sem quebra: {mean_0:.1f}")
                    print(f"   Duração média - Com quebra: {mean_1:.1f}")
                    print(f"   Diferença: {diff:+.1f}%")
    
    # Features agregadas
    print("\n📊 Features multi-escala agregadas:")
    print("-" * 60)
    
    agg_features = ['levy_cross_scale_cv', 'levy_cross_scale_range', 'levy_scale_correlation']
    for feat in agg_features:
        if feat in df.columns:
            mean_0 = df[df['label'] == 0][feat].mean()
            mean_1 = df[df['label'] == 1][feat].mean()
            diff = (mean_1 - mean_0) / (abs(mean_0) + 1e-10) * 100
            print(f"\n{feat}:")
            print(f"   Sem quebra: {mean_0:.3f}")
            print(f"   Com quebra: {mean_1:.3f}")
            print(f"   Diferença: {diff:+.1f}%")
    
    # Salvar
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'database/levy_multiscale_{timestamp}.parquet'
    df.to_parquet(output_file)
    
    print(f"\n💾 Features salvas: {output_file}")
    print(f"   Shape: {df.shape}")
    print(f"   Features por série: {len([c for c in df.columns if c.startswith('levy_')])}")

print("\n" + "="*60)
print("✨ Multi-escala permite identificar quebras em QUALQUER horizonte!")
print("="*60)