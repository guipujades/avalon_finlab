#!/usr/bin/env python3
"""
Script para processar dados em formato longo (long format).
Adaptado para a estrutura real dos dados do CrunchDAO.
"""

import numpy as np
import pandas as pd
from datetime import datetime
import os

print("\n" + "="*60)
print("EXTRAÇÃO DE FEATURES DE LÉVY - FORMATO LONGO")
print("="*60)

# 1. Carregar dados
print("\n📊 Carregando dados...")
X_train = pd.read_parquet('database/X_train.parquet')
y_train = pd.read_parquet('database/y_train.parquet')

print(f"✅ X_train: {X_train.shape}")
print(f"✅ y_train: {y_train.shape}")

# 2. Verificar estrutura
print("\n🔍 Analisando estrutura dos dados...")
print(f"   Colunas: {list(X_train.columns)}")

# Assumindo que temos (id, value) ou similar
if X_train.shape[1] == 2:
    id_col = X_train.columns[0]
    value_col = X_train.columns[1]
    
    print(f"   Coluna ID: {id_col}")
    print(f"   Coluna Valor: {value_col}")
    
    # Contar séries únicas
    unique_ids = X_train[id_col].unique()
    print(f"   Número de séries únicas: {len(unique_ids)}")
    
    # Calcular comprimento médio das séries
    series_lengths = X_train.groupby(id_col).size()
    print(f"   Comprimento médio das séries: {series_lengths.mean():.0f}")
    print(f"   Comprimento mínimo: {series_lengths.min()}")
    print(f"   Comprimento máximo: {series_lengths.max()}")

# 3. Função para processar uma série
def calculate_levy_features_long(series_data, tau=0.005, q=5):
    """Calcula features de Lévy para uma série em formato array."""
    # Remover NaN
    series_clean = series_data[~np.isnan(series_data)]
    if len(series_clean) < 20:
        return None
    
    # Calcular diferenças
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
    
    # Construir seções
    sections = []
    durations = []
    i = 0
    
    while i < len(volatilities):
        acc_var = 0
        j = i
        
        while j < len(volatilities) and acc_var + volatilities[j] <= tau:
            acc_var += volatilities[j]
            j += 1
        
        if j > i:
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
    
    return {
        'duration_mean': np.mean(durations),
        'duration_std': np.std(durations),
        'duration_cv': np.std(durations) / np.mean(durations) if np.mean(durations) > 0 else 0,
        'duration_min': np.min(durations),
        'duration_max': np.max(durations),
        'n_sections': len(sections),
        'sum_mean': np.mean(sections),
        'sum_std': np.std(sections)
    }

# 4. Processar séries
print("\n🔍 Processando séries...")
results = []
sample_size = min(100, len(unique_ids))

for i, series_id in enumerate(unique_ids[:sample_size]):
    if i % 20 == 0:
        print(f"   Processadas: {i}/{sample_size}")
    
    # Extrair dados da série
    series_data = X_train[X_train[id_col] == series_id][value_col].values
    
    # Calcular features
    features = calculate_levy_features_long(series_data)
    
    if features is not None:
        features['series_id'] = series_id
        # Adicionar label se existir
        if series_id in y_train.index:
            features['label'] = y_train.loc[series_id, 'target']
        results.append(features)

print(f"\n✅ Séries processadas com sucesso: {len(results)}")

# 5. Salvar e analisar resultados
if results:
    df = pd.DataFrame(results)
    
    # Estatísticas
    print("\n📈 Estatísticas das features:")
    for col in ['duration_mean', 'n_sections', 'duration_cv']:
        if col in df.columns:
            print(f"   {col}: média={df[col].mean():.4f}, std={df[col].std():.4f}")
    
    # Comparar por classe se houver labels
    if 'label' in df.columns:
        print("\n🎯 Comparação por classe:")
        for feature in ['duration_mean', 'n_sections']:
            print(f"\n   {feature}:")
            for label in df['label'].unique():
                if pd.notna(label):
                    mask = df['label'] == label
                    mean_val = df.loc[mask, feature].mean()
                    count = mask.sum()
                    print(f"      Classe {int(label)}: {mean_val:.4f} (n={count})")
    
    # Salvar
    os.makedirs('outputs', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    csv_file = f'outputs/levy_features_long_{timestamp}.csv'
    df.to_csv(csv_file, index=False)
    print(f"\n💾 Features salvas em: {csv_file}")
    
    # Salvar também em parquet
    parquet_file = f'database/levy_features_{timestamp}.parquet'
    df.to_parquet(parquet_file)
    print(f"   Formato parquet: {parquet_file}")
    
    print("\n✨ Análise concluída!")
else:
    print("\n❌ Nenhuma série processada com sucesso.")
    print("   Verifique se o formato dos dados está correto.")

print("="*60)