#!/usr/bin/env python3
"""
Script BÁSICO para extrair features de Lévy - SEM scipy, SEM matplotlib, SEM sklearn.
Apenas numpy e pandas puros.

Author: CrunchDAO SB Team  
Date: 2025-06-26
"""

import numpy as np
import pandas as pd
from datetime import datetime
import os

print("\n" + "="*60)
print("EXTRAÇÃO BÁSICA DE FEATURES DE LÉVY")
print("="*60)

# 1. Carregar dados
print("\n📊 Carregando dados...")
try:
    X_train = pd.read_parquet('database/X_train.parquet')
    y_train = pd.read_parquet('database/y_train.parquet')
    print(f"✅ X_train: {X_train.shape}")
    print(f"✅ y_train: {y_train.shape}")
except Exception as e:
    print(f"❌ Erro ao carregar dados: {e}")
    exit(1)

# 2. Função para calcular features de Lévy
def calculate_levy_features(series, tau=0.005, q=5):
    """Calcula features básicas de Lévy para uma série."""
    # Limpar dados
    series_clean = series[~np.isnan(series)]
    if len(series_clean) < 20:
        return None
    
    # Calcular retornos
    returns = np.diff(series_clean)
    if len(returns) < 10:
        return None
    
    # Calcular volatilidades locais (janela móvel)
    n = len(returns)
    volatilities = []
    
    for i in range(q, n - q):
        window = returns[(i - q):(i + q + 1)]
        vol = np.var(window)
        volatilities.append(vol)
    
    # Construir seções
    sections = []
    durations = []
    i = 0
    volatilities = np.array(volatilities)
    
    while i < len(volatilities):
        acc_var = 0
        j = i
        
        # Acumular até tau
        while j < len(volatilities) and acc_var + volatilities[j] <= tau:
            acc_var += volatilities[j]
            j += 1
        
        if j > i:
            # Soma da seção
            section_sum = np.sum(returns[i+q:j+q])
            sections.append(section_sum)
            durations.append(j - i)
            i = j
        else:
            i += 1
    
    if len(sections) == 0:
        return None
    
    # Calcular features
    durations = np.array(durations)
    sections = np.array(sections)
    
    features = {
        'duration_mean': np.mean(durations),
        'duration_std': np.std(durations),
        'duration_min': np.min(durations),
        'duration_max': np.max(durations),
        'n_sections': len(sections),
        'sum_mean': np.mean(sections),
        'sum_std': np.std(sections)
    }
    
    return features

# 3. Processar amostra de séries
print("\n🔍 Processando amostra de séries...")
sample_size = 100
results = []

for i, series_id in enumerate(X_train.index[:sample_size]):
    if i % 20 == 0:
        print(f"   Processadas: {i}/{sample_size}")
    
    series = X_train.loc[series_id].values
    features = calculate_levy_features(series)
    
    if features is not None:
        features['series_id'] = series_id
        features['label'] = y_train.loc[series_id, 'target'] if series_id in y_train.index else None
        results.append(features)

# 4. Criar DataFrame com resultados
print(f"\n✅ Séries processadas com sucesso: {len(results)}")

if results:
    df = pd.DataFrame(results)
    
    # 5. Mostrar estatísticas
    print("\n📈 Estatísticas das features:")
    print("\nMédias gerais:")
    for col in ['duration_mean', 'n_sections', 'sum_std']:
        if col in df.columns:
            print(f"   {col}: {df[col].mean():.4f}")
    
    # 6. Comparar por classe
    if 'label' in df.columns:
        print("\n🎯 Comparação por classe:")
        for feature in ['duration_mean', 'n_sections']:
            print(f"\n   {feature}:")
            for label in [0, 1]:
                mask = df['label'] == label
                if mask.any():
                    mean_val = df.loc[mask, feature].mean()
                    print(f"      Classe {label}: {mean_val:.4f}")
    
    # 7. Salvar resultados
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'levy_features_basic_{timestamp}.csv'
    df.to_csv(output_file, index=False)
    print(f"\n💾 Features salvas em: {output_file}")
    
    # Criar pasta outputs se não existir
    os.makedirs('outputs', exist_ok=True)
    
    # Salvar resumo
    summary_file = f'outputs/levy_summary_{timestamp}.txt'
    with open(summary_file, 'w') as f:
        f.write("RESUMO DA ANÁLISE DE LÉVY\n")
        f.write("="*40 + "\n\n")
        f.write(f"Séries processadas: {len(results)}/{sample_size}\n")
        f.write(f"Taxa de sucesso: {len(results)/sample_size*100:.1f}%\n\n")
        f.write("Médias das features:\n")
        for col in df.columns:
            if col not in ['series_id', 'label']:
                f.write(f"   {col}: {df[col].mean():.4f}\n")
    
    print(f"   Resumo salvo em: {summary_file}")
    
    print("\n✨ Análise concluída!")
else:
    print("\n❌ Nenhuma série foi processada com sucesso.")

print("="*60)