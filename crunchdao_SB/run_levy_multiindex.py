#!/usr/bin/env python3
"""
Script adaptado para processar dados com multi-índice (id, time).
Estrutura: índice=(id, time), colunas=['value', 'period']
"""

import numpy as np
import pandas as pd
from datetime import datetime
import os

print("\n" + "="*60)
print("EXTRAÇÃO DE FEATURES DE LÉVY - DADOS CRUNCHDAO")
print("="*60)

# 1. Carregar dados
print("\n📊 Carregando dados...")
X_train = pd.read_parquet('database/X_train.parquet')
y_train = pd.read_parquet('database/y_train.parquet')

print(f"✅ X_train: {X_train.shape}")
print(f"✅ y_train: {y_train.shape}")
print(f"   Multi-índice: {X_train.index.names}")
print(f"   Colunas: {list(X_train.columns)}")

# 2. Obter IDs únicos
print("\n🔍 Analisando estrutura...")
# Resetar índice para trabalhar mais facilmente
X_train_reset = X_train.reset_index()
unique_ids = X_train_reset['id'].unique()
print(f"   Número de séries (IDs únicos): {len(unique_ids)}")

# Verificar tamanho das séries
series_lengths = X_train_reset.groupby('id').size()
print(f"   Comprimento das séries: min={series_lengths.min()}, max={series_lengths.max()}, média={series_lengths.mean():.0f}")

# 3. Função para calcular features de Lévy
def calculate_levy_features(series_values, tau=0.005, q=5):
    """Calcula features de Lévy para uma série."""
    # Remover NaN
    series_clean = series_values[~np.isnan(series_values)]
    if len(series_clean) < 20:
        return None
    
    # Calcular retornos (diferenças)
    returns = np.diff(series_clean)
    if len(returns) < 2*q + 1:
        return None
    
    # Calcular volatilidades locais
    n = len(returns)
    volatilities = []
    
    for i in range(q, n - q):
        window = returns[(i - q):(i + q + 1)]
        vol = np.var(window)
        volatilities.append(vol)
    
    if len(volatilities) == 0:
        return None
    
    # Construir seções de Lévy
    sections = []
    durations = []
    i = 0
    
    while i < len(volatilities):
        acc_var = 0
        j = i
        
        # Acumular variância até atingir tau
        while j < len(volatilities) and acc_var + volatilities[j] <= tau:
            acc_var += volatilities[j]
            j += 1
        
        if j > i:
            # Calcular soma da seção
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
    sections_norm = sections / np.sqrt(tau)  # Normalização teórica
    
    features = {
        'levy_duration_mean': np.mean(durations),
        'levy_duration_std': np.std(durations),
        'levy_duration_cv': np.std(durations) / np.mean(durations) if np.mean(durations) > 0 else 0,
        'levy_duration_min': np.min(durations),
        'levy_duration_max': np.max(durations),
        'levy_duration_skew': ((durations - np.mean(durations))**3).mean() / (np.std(durations)**3) if np.std(durations) > 0 else 0,
        'levy_n_sections': len(sections),
        'levy_sum_mean': np.mean(sections),
        'levy_sum_std': np.std(sections),
        'levy_norm_std': np.std(sections_norm),
        'levy_norm_kurtosis': ((sections_norm - np.mean(sections_norm))**4).mean() / (np.std(sections_norm)**4) - 3 if np.std(sections_norm) > 0 else 0
    }
    
    return features

# 4. Processar séries
print("\n🔍 Processando séries...")
results = []
sample_size = min(1000, len(unique_ids))  # Processar até 1000 séries

for i, series_id in enumerate(unique_ids[:sample_size]):
    if i % 100 == 0:
        print(f"   Processadas: {i}/{sample_size}")
    
    # Extrair valores da série específica
    series_data = X_train.loc[series_id, 'value'].values
    
    # Calcular features
    features = calculate_levy_features(series_data, tau=0.005, q=5)
    
    if features is not None:
        features['series_id'] = series_id
        
        # Adicionar label se existir
        if series_id in y_train.index:
            features['label'] = y_train.loc[series_id, 'structural_breakpoint']
        
        results.append(features)

print(f"\n✅ Séries processadas com sucesso: {len(results)}/{sample_size}")
print(f"   Taxa de sucesso: {len(results)/sample_size*100:.1f}%")

# 5. Criar DataFrame e analisar
if results:
    df_features = pd.DataFrame(results)
    
    print("\n📈 Estatísticas das features:")
    feature_cols = [col for col in df_features.columns if col.startswith('levy_')]
    for col in feature_cols[:5]:  # Mostrar apenas as 5 primeiras
        mean_val = df_features[col].mean()
        std_val = df_features[col].std()
        print(f"   {col}: média={mean_val:.4f}, std={std_val:.4f}")
    
    # Comparar por classe se houver labels
    if 'label' in df_features.columns:
        print("\n🎯 Comparação por classe (structural_breakpoint):")
        
        # Converter boolean para int para facilitar
        df_features['label_int'] = df_features['label'].astype(int)
        
        for feature in ['levy_duration_mean', 'levy_n_sections', 'levy_norm_kurtosis']:
            if feature in df_features.columns:
                print(f"\n   {feature}:")
                for label in [0, 1]:
                    mask = df_features['label_int'] == label
                    if mask.sum() > 0:
                        mean_val = df_features.loc[mask, feature].mean()
                        std_val = df_features.loc[mask, feature].std()
                        count = mask.sum()
                        print(f"      Breakpoint={label}: média={mean_val:.4f}, std={std_val:.4f}, n={count}")
    
    # 6. Salvar resultados
    os.makedirs('outputs', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # CSV para visualização
    csv_file = f'outputs/levy_features_{timestamp}.csv'
    df_features.to_csv(csv_file, index=False)
    print(f"\n💾 Features salvas em CSV: {csv_file}")
    
    # Parquet para uso em ML
    parquet_file = f'database/levy_features_{timestamp}.parquet'
    df_features.set_index('series_id').to_parquet(parquet_file)
    print(f"   Features salvas em Parquet: {parquet_file}")
    
    # Criar visualização simples
    if 'label' in df_features.columns:
        import matplotlib.pyplot as plt
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        axes = axes.ravel()
        
        features_to_plot = ['levy_duration_mean', 'levy_n_sections', 'levy_norm_kurtosis', 'levy_duration_cv']
        
        for idx, feature in enumerate(features_to_plot):
            if feature in df_features.columns and idx < 4:
                ax = axes[idx]
                
                # Boxplot por classe
                data_0 = df_features[df_features['label_int'] == 0][feature].dropna()
                data_1 = df_features[df_features['label_int'] == 1][feature].dropna()
                
                ax.boxplot([data_0, data_1], labels=['No Breakpoint', 'Breakpoint'])
                ax.set_title(feature.replace('levy_', '').replace('_', ' ').title())
                ax.set_ylabel('Value')
                ax.grid(True, alpha=0.3)
        
        plt.suptitle('Levy Features by Structural Breakpoint Class')
        plt.tight_layout()
        plt.savefig(f'outputs/levy_features_comparison_{timestamp}.png', dpi=150, bbox_inches='tight')
        print(f"   Gráfico salvo em: outputs/levy_features_comparison_{timestamp}.png")
        plt.close()
    
    # Resumo final
    print("\n" + "="*60)
    print("✨ ANÁLISE CONCLUÍDA COM SUCESSO!")
    print("="*60)
    print(f"\n📊 Resumo:")
    print(f"   Total de features extraídas: {len(feature_cols)}")
    print(f"   Séries processadas: {len(results)}")
    if 'label' in df_features.columns:
        print(f"   Séries com breakpoint=True: {df_features['label'].sum()}")
        print(f"   Séries com breakpoint=False: {(~df_features['label']).sum()}")
    
else:
    print("\n❌ Nenhuma série foi processada com sucesso.")

print("="*60)