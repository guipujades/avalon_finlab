"""
Simplified analysis script for structural break detection.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


def load_data():
    """Load and prepare data."""
    X_train = pd.read_parquet('database/X_train.parquet').reset_index()
    y_train = pd.read_parquet('database/y_train.parquet')
    y_train = y_train.rename(columns={'structural_breakpoint': 'label'})
    
    print(f"Loaded {len(X_train['id'].unique())} time series")
    print(f"Break rate: {y_train['label'].mean():.2%}")
    
    return X_train, y_train


def extract_basic_features(series_data):
    """Extract basic statistical features."""
    before = series_data[series_data['period'] == 0]['value'].values
    after = series_data[series_data['period'] == 1]['value'].values
    
    features = {}
    
    # Basic statistics
    features['mean_before'] = np.mean(before)
    features['mean_after'] = np.mean(after)
    features['std_before'] = np.std(before)
    features['std_after'] = np.std(after)
    features['median_before'] = np.median(before)
    features['median_after'] = np.median(after)
    
    # Differences and ratios
    features['mean_diff'] = features['mean_after'] - features['mean_before']
    features['mean_abs_diff'] = abs(features['mean_diff'])
    features['std_ratio'] = features['std_after'] / features['std_before'] if features['std_before'] > 0 else np.nan
    
    # Quantiles
    features['q25_before'] = np.percentile(before, 25)
    features['q75_before'] = np.percentile(before, 75)
    features['q25_after'] = np.percentile(after, 25)
    features['q75_after'] = np.percentile(after, 75)
    features['iqr_before'] = features['q75_before'] - features['q25_before']
    features['iqr_after'] = features['q75_after'] - features['q25_after']
    features['iqr_ratio'] = features['iqr_after'] / features['iqr_before'] if features['iqr_before'] > 0 else np.nan
    
    # Higher moments
    features['skew_before'] = np.mean(((before - features['mean_before']) / features['std_before'])**3) if features['std_before'] > 0 else 0
    features['skew_after'] = np.mean(((after - features['mean_after']) / features['std_after'])**3) if features['std_after'] > 0 else 0
    features['kurt_before'] = np.mean(((before - features['mean_before']) / features['std_before'])**4) - 3 if features['std_before'] > 0 else 0
    features['kurt_after'] = np.mean(((after - features['mean_after']) / features['std_after'])**4) - 3 if features['std_after'] > 0 else 0
    
    # Autocorrelation
    if len(before) > 1:
        features['acf1_before'] = np.corrcoef(before[:-1], before[1:])[0, 1]
    else:
        features['acf1_before'] = 0
        
    if len(after) > 1:
        features['acf1_after'] = np.corrcoef(after[:-1], after[1:])[0, 1]
    else:
        features['acf1_after'] = 0
    
    # Size info
    features['n_before'] = len(before)
    features['n_after'] = len(after)
    features['n_ratio'] = len(after) / len(before)
    
    return features


def analyze_sample_series(X_train, y_train):
    """Visualize sample series."""
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    axes = axes.flatten()
    
    break_ids = y_train[y_train['label'] == True].index.values[:3]
    no_break_ids = y_train[y_train['label'] == False].index.values[:3]
    sample_ids = list(break_ids) + list(no_break_ids)
    
    for idx, (ax, series_id) in enumerate(zip(axes, sample_ids)):
        series = X_train[X_train['id'] == series_id]
        label = y_train.loc[series_id, 'label']
        
        before = series[series['period'] == 0]
        after = series[series['period'] == 1]
        
        ax.plot(before['time'].values, before['value'].values, 
                label='Before', alpha=0.8, linewidth=1.5)
        ax.plot(after['time'].values, after['value'].values, 
                label='After', alpha=0.8, linewidth=1.5)
        
        boundary_time = before['time'].max()
        ax.axvline(x=boundary_time, color='red', linestyle='--', 
                  alpha=0.5, label='Boundary')
        
        ax.set_title(f'Series {series_id} - Break: {label}', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('Time')
        ax.set_ylabel('Value')
        
        if idx == 0:
            ax.legend(fontsize=8)
    
    plt.tight_layout()
    plt.savefig('sample_series_analysis.png', dpi=150)
    plt.close()
    print("Sample series visualization saved")


def extract_features_batch(X_train, y_train, n_samples=1000):
    """Extract features for a batch of series."""
    unique_ids = X_train['id'].unique()
    sample_ids = np.random.choice(unique_ids, size=min(n_samples, len(unique_ids)), replace=False)
    
    results = []
    
    for i, series_id in enumerate(sample_ids):
        if i % 100 == 0:
            print(f"Processing series {i+1}/{len(sample_ids)}")
        
        series_data = X_train[X_train['id'] == series_id]
        label = y_train.loc[series_id, 'label']
        
        features = extract_basic_features(series_data)
        features['id'] = series_id
        features['label'] = label
        
        results.append(features)
    
    return pd.DataFrame(results)


def analyze_features(features_df):
    """Analyze feature importance."""
    from scipy import stats
    
    feature_cols = [col for col in features_df.columns if col not in ['id', 'label']]
    importance = []
    
    for col in feature_cols:
        try:
            values = features_df[col].values
            mask = ~np.isnan(values) & ~np.isinf(values)
            
            if mask.sum() < 10:
                continue
            
            values = values[mask]
            labels = features_df['label'].values[mask]
            
            group0 = values[labels == False]
            group1 = values[labels == True]
            
            if len(group0) < 5 or len(group1) < 5:
                continue
            
            t_stat, p_value = stats.ttest_ind(group0, group1)
            mean_diff = np.mean(group1) - np.mean(group0)
            std_pooled = np.sqrt((np.var(group0) + np.var(group1)) / 2)
            cohen_d = mean_diff / std_pooled if std_pooled > 0 else 0
            
            importance.append({
                'feature': col,
                't_statistic': t_stat,
                'p_value': p_value,
                'cohen_d': cohen_d,
                'mean_no_break': np.mean(group0),
                'mean_break': np.mean(group1)
            })
        except:
            continue
    
    importance_df = pd.DataFrame(importance)
    importance_df['abs_cohen_d'] = np.abs(importance_df['cohen_d'])
    importance_df = importance_df.sort_values('abs_cohen_d', ascending=False)
    
    print("\nTop 15 most discriminative features:")
    print(importance_df.head(15)[['feature', 'cohen_d', 'p_value']])
    
    # Visualizations
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # Feature importance
    top_features = importance_df.head(15)
    axes[0, 0].barh(range(len(top_features)), top_features['abs_cohen_d'])
    axes[0, 0].set_yticks(range(len(top_features)))
    axes[0, 0].set_yticklabels(top_features['feature'], fontsize=8)
    axes[0, 0].set_xlabel("Cohen's d (absolute)")
    axes[0, 0].set_title("Feature Importance by Effect Size")
    axes[0, 0].invert_yaxis()
    
    # Volcano plot
    axes[0, 1].scatter(importance_df['cohen_d'], -np.log10(importance_df['p_value']), alpha=0.5)
    axes[0, 1].axhline(y=-np.log10(0.05), color='r', linestyle='--', alpha=0.5)
    axes[0, 1].set_xlabel("Cohen's d")
    axes[0, 1].set_ylabel("-log10(p-value)")
    axes[0, 1].set_title("Volcano Plot")
    
    # Top 2 features distribution
    for idx, feature in enumerate(top_features['feature'].values[:2]):
        ax = axes[1, idx]
        no_break = features_df[features_df['label'] == False][feature].dropna()
        with_break = features_df[features_df['label'] == True][feature].dropna()
        
        ax.hist([no_break, with_break], bins=30, alpha=0.7, 
                label=['No Break', 'Break'], density=True)
        ax.set_xlabel(feature)
        ax.set_ylabel('Density')
        ax.legend()
        ax.set_title(f'Distribution of {feature}')
    
    plt.tight_layout()
    plt.savefig('feature_analysis.png', dpi=150)
    plt.close()
    print("Feature analysis saved")
    
    importance_df.to_csv('feature_importance.csv', index=False)
    return importance_df


def main():
    """Run the analysis."""
    print("Starting simplified structural break analysis...")
    
    # Load data
    X_train, y_train = load_data()
    
    # Visualize samples
    analyze_sample_series(X_train, y_train)
    
    # Extract features
    print("\nExtracting features...")
    features_df = extract_features_batch(X_train, y_train, n_samples=1000)
    print(f"Extracted {features_df.shape[1]} features for {features_df.shape[0]} series")
    
    # Save features
    features_df.to_parquet('features_simple.parquet')
    print("Features saved to features_simple.parquet")
    
    # Analyze features
    importance_df = analyze_features(features_df)
    
    print("\nAnalysis complete! Check the generated files:")
    print("- sample_series_analysis.png")
    print("- feature_analysis.png")
    print("- feature_importance.csv")
    print("- features_simple.parquet")


if __name__ == '__main__':
    main()