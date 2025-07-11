#!/usr/bin/env python3
"""
Analisa características dos dados para entender melhor a natureza HFT.
"""

import pandas as pd
import numpy as np

print("\n" + "="*60)
print("ANÁLISE DE DADOS - HIGH FREQUENCY CHARACTERISTICS")
print("="*60)

# Carregar amostra dos dados
print("\n📊 Carregando amostra dos dados...")
X_train = pd.read_parquet('database/X_train.parquet')

# Analisar estrutura
print(f"\n📊 Estrutura dos dados:")
print(f"   Shape total: {X_train.shape}")
print(f"   Colunas: {X_train.columns.tolist()}")

# Pegar algumas séries de exemplo
sample_ids = X_train.index.get_level_values('id').unique()[:5]

print(f"\n📊 Análise de séries individuais:")
print("-" * 60)

for i, series_id in enumerate(sample_ids):
    series_data = X_train.loc[series_id]
    
    if 'value' in series_data.columns:
        values = series_data['value'].values
    else:
        values = series_data.iloc[:, 0].values
    
    # Remove NaN para análise
    clean_values = values[~np.isnan(values)]
    
    print(f"\nSérie {i+1} (ID: {series_id}):")
    print(f"   Pontos: {len(values)} (válidos: {len(clean_values)})")
    print(f"   Range: [{np.min(clean_values):.6f}, {np.max(clean_values):.6f}]")
    print(f"   Média: {np.mean(clean_values):.6f}")
    print(f"   Std: {np.std(clean_values):.6f}")
    
    # Verificar se são retornos ou preços
    if np.min(clean_values) < -0.1 or np.max(clean_values) > 10:
        print(f"   Tipo provável: PREÇOS")
    else:
        print(f"   Tipo provável: RETORNOS")
    
    # Verificar zeros e negativos
    n_zeros = np.sum(clean_values == 0)
    n_negative = np.sum(clean_values < 0)
    
    if n_zeros > 0:
        print(f"   ⚠️  Zeros encontrados: {n_zeros}")
    if n_negative > 0:
        print(f"   ⚠️  Valores negativos: {n_negative}")
    
    # Calcular algumas estatísticas de HFT
    if len(clean_values) > 1:
        # Se forem preços, calcular retornos
        if np.min(clean_values) > 0:  # Provavelmente preços
            returns = np.diff(clean_values) / clean_values[:-1]
        else:  # Já são retornos
            returns = clean_values[1:]
        
        if len(returns) > 0:
            print(f"   Retornos - média: {np.mean(returns):.6f}, std: {np.std(returns):.6f}")

# Análise agregada
print(f"\n📊 Estatísticas agregadas (primeiras 100 séries):")
print("-" * 60)

sample_ids_100 = X_train.index.get_level_values('id').unique()[:100]
all_lengths = []
all_means = []
all_stds = []

for series_id in sample_ids_100:
    series_data = X_train.loc[series_id]
    if 'value' in series_data.columns:
        values = series_data['value'].values
    else:
        values = series_data.iloc[:, 0].values
    
    clean_values = values[~np.isnan(values)]
    if len(clean_values) > 0:
        all_lengths.append(len(clean_values))
        all_means.append(np.mean(clean_values))
        all_stds.append(np.std(clean_values))

print(f"\nComprimento das séries:")
print(f"   Média: {np.mean(all_lengths):.0f}")
print(f"   Min: {np.min(all_lengths)}")
print(f"   Max: {np.max(all_lengths)}")

print(f"\nValores das séries:")
print(f"   Média geral: {np.mean(all_means):.6f}")
print(f"   Std médio: {np.mean(all_stds):.6f}")

# Determinar se são dados HFT
avg_length = np.mean(all_lengths)
if avg_length > 10000:
    print(f"\n✅ CONFIRMADO: Dados de alta frequência (média {avg_length:.0f} pontos/série)")
elif avg_length > 1000:
    print(f"\n⚠️  Dados de média frequência (média {avg_length:.0f} pontos/série)")
else:
    print(f"\n❌ Dados de baixa frequência (média {avg_length:.0f} pontos/série)")

print("\n" + "="*60)
print("RECOMENDAÇÕES BASEADAS NA ANÁLISE:")
print("="*60)

if avg_length < 1000:
    print("\n🎯 Para dados de menor frequência:")
    print("   - Use tau maior: 0.005 - 0.02")
    print("   - Use q menor: 3 - 10")
    print("   - Foque em mudanças de regime de médio prazo")
else:
    print("\n🎯 Para dados de alta frequência:")
    print("   - Use tau menor: 0.0001 - 0.001")
    print("   - Use q maior: 10 - 30")
    print("   - Considere microestrutura e ruído")

print("\n" + "="*60)