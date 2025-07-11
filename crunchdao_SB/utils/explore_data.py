import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

X_train = pd.read_parquet('database/X_train.parquet')
y_train = pd.read_parquet('database/y_train.parquet')

print(f"Formato X_train: {X_train.shape}")
print(f"Formato y_train: {y_train.shape}")
print(f"\nColunas X_train: {X_train.columns.tolist()}")
print(f"\nPrimeiras linhas X_train:")
print(X_train.head(10))
print(f"\nDistribuição de labels:")
print(y_train['label'].value_counts())
print(f"Percentual com quebra: {y_train['label'].mean():.2%}")

unique_ids = X_train['id'].unique()
print(f"\nTotal de séries: {len(unique_ids)}")

sample_id = unique_ids[0]
sample_series = X_train[X_train['id'] == sample_id]
print(f"\nExemplo série {sample_id}:")
print(f"Tamanho: {len(sample_series)}")
print(f"Períodos únicos: {sample_series['period'].unique()}")

series_lengths = X_train.groupby('id').size()
print(f"\nEstatísticas de tamanho das séries:")
print(series_lengths.describe())

fig, axes = plt.subplots(2, 2, figsize=(12, 10))

for i, (ax, series_id) in enumerate(zip(axes.flat, unique_ids[:4])):
    series = X_train[X_train['id'] == series_id]
    label = y_train[y_train['id'] == series_id]['label'].values[0]
    
    before = series[series['period'] == 0]['value']
    after = series[series['period'] == 1]['value']
    
    ax.plot(before.index, before.values, label='Antes', alpha=0.7)
    ax.plot(after.index, after.values, label='Depois', alpha=0.7)
    ax.axvline(x=len(before), color='red', linestyle='--', alpha=0.5)
    ax.set_title(f'Série {series_id} - Quebra: {label}')
    ax.legend()
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('sample_series.png')
plt.close()

def analyze_series(series_data):
    before = series_data[series_data['period'] == 0]['value']
    after = series_data[series_data['period'] == 1]['value']
    
    stats_dict = {
        'mean_before': before.mean(),
        'mean_after': after.mean(),
        'std_before': before.std(),
        'std_after': after.std(),
        'min_before': before.min(),
        'min_after': after.min(),
        'max_before': before.max(),
        'max_after': after.max(),
        'skew_before': before.skew(),
        'skew_after': after.skew(),
        'kurt_before': before.kurtosis(),
        'kurt_after': after.kurtosis(),
        'len_before': len(before),
        'len_after': len(after),
        'mean_diff': after.mean() - before.mean(),
        'std_ratio': after.std() / before.std() if before.std() > 0 else np.nan,
        'range_before': before.max() - before.min(),
        'range_after': after.max() - after.min()
    }
    
    return stats_dict

all_stats = []
for series_id in unique_ids[:1000]:
    series = X_train[X_train['id'] == series_id]
    label = y_train[y_train['id'] == series_id]['label'].values[0]
    
    stats = analyze_series(series)
    stats['id'] = series_id
    stats['label'] = label
    all_stats.append(stats)

stats_df = pd.DataFrame(all_stats)

print("\nEstatísticas por tipo de quebra:")
print(stats_df.groupby('label')[['mean_diff', 'std_ratio']].describe())

fig, axes = plt.subplots(2, 2, figsize=(12, 10))

axes[0, 0].scatter(stats_df[stats_df['label']==False]['mean_diff'], 
                   stats_df[stats_df['label']==False]['std_ratio'], 
                   alpha=0.5, label='Sem quebra')
axes[0, 0].scatter(stats_df[stats_df['label']==True]['mean_diff'], 
                   stats_df[stats_df['label']==True]['std_ratio'], 
                   alpha=0.5, label='Com quebra')
axes[0, 0].set_xlabel('Diferença de média')
axes[0, 0].set_ylabel('Razão de desvio padrão')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

axes[0, 1].hist([stats_df[stats_df['label']==False]['mean_diff'],
                 stats_df[stats_df['label']==True]['mean_diff']], 
                label=['Sem quebra', 'Com quebra'], bins=30, alpha=0.7)
axes[0, 1].set_xlabel('Diferença de média')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

axes[1, 0].hist([stats_df[stats_df['label']==False]['std_ratio'],
                 stats_df[stats_df['label']==True]['std_ratio']], 
                label=['Sem quebra', 'Com quebra'], bins=30, alpha=0.7)
axes[1, 0].set_xlabel('Razão de desvio padrão')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

axes[1, 1].boxplot([stats_df[stats_df['label']==False]['skew_before'],
                    stats_df[stats_df['label']==True]['skew_before'],
                    stats_df[stats_df['label']==False]['skew_after'],
                    stats_df[stats_df['label']==True]['skew_after']])
axes[1, 1].set_xticklabels(['Sem Q\nAntes', 'Com Q\nAntes', 'Sem Q\nDepois', 'Com Q\nDepois'])
axes[1, 1].set_ylabel('Assimetria')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('stats_analysis.png')
plt.close()

print("\nAnálise concluída. Gráficos salvos.")