"""
Main script for structural break detection feature extraction and analysis.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys

sys.path.append('src')

from features.extractor import (
    parallel_feature_extraction, 
    create_feature_importance_summary,
    extract_features_before_after
)


def load_data(data_path: Path = Path('database')):
    """
    Load training data from parquet files.
    
    Parameters
    ----------
    data_path : Path
        Path to data directory
        
    Returns
    -------
    X_train, y_train : pd.DataFrame
        Training data and labels
    """
    X_train = pd.read_parquet(data_path / 'X_train.parquet')
    y_train = pd.read_parquet(data_path / 'y_train.parquet')
    
    print(f"Loaded {len(X_train['id'].unique())} time series")
    print(f"Break rate: {y_train['label'].mean():.2%}")
    
    return X_train, y_train


def analyze_sample_series(X_train: pd.DataFrame, y_train: pd.DataFrame, n_samples: int = 6):
    """
    Visualize sample time series with and without breaks.
    
    Parameters
    ----------
    X_train : pd.DataFrame
        Training data
    y_train : pd.DataFrame
        Labels
    n_samples : int
        Number of samples to plot
    """
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    axes = axes.flatten()
    
    break_ids = y_train[y_train['label'] == True]['id'].values[:3]
    no_break_ids = y_train[y_train['label'] == False]['id'].values[:3]
    
    sample_ids = list(break_ids) + list(no_break_ids)
    
    for idx, (ax, series_id) in enumerate(zip(axes, sample_ids)):
        series = X_train[X_train['id'] == series_id]
        label = y_train[y_train['id'] == series_id]['label'].values[0]
        
        before = series[series['period'] == 0]
        after = series[series['period'] == 1]
        
        ax.plot(range(len(before)), before['value'].values, 
                label='Before', alpha=0.8, linewidth=1.5)
        ax.plot(range(len(before), len(before) + len(after)), 
                after['value'].values, 
                label='After', alpha=0.8, linewidth=1.5)
        
        ax.axvline(x=len(before), color='red', linestyle='--', 
                  alpha=0.5, label='Boundary')
        
        title = f'Series {series_id[:8]}... - Break: {label}'
        ax.set_title(title, fontsize=10)
        ax.grid(True, alpha=0.3)
        
        if idx == 0:
            ax.legend(fontsize=8)
    
    plt.tight_layout()
    plt.savefig('sample_series_analysis.png', dpi=150)
    plt.close()
    
    print("Sample series visualization saved to sample_series_analysis.png")


def run_feature_extraction(X_train: pd.DataFrame, y_train: pd.DataFrame, 
                         sample_size: int = 1000):
    """
    Run feature extraction on a sample of the data.
    
    Parameters
    ----------
    X_train : pd.DataFrame
        Training data
    y_train : pd.DataFrame
        Labels
    sample_size : int
        Number of series to process
        
    Returns
    -------
    features_df : pd.DataFrame
        Extracted features
    """
    print(f"\nExtracting features for {sample_size} series...")
    
    sample_ids = np.random.choice(X_train['id'].unique(), 
                                 size=min(sample_size, len(X_train['id'].unique())), 
                                 replace=False)
    
    X_sample = X_train[X_train['id'].isin(sample_ids)]
    y_sample = y_train[y_train['id'].isin(sample_ids)]
    
    features_df = parallel_feature_extraction(X_sample, y_sample, n_jobs=4, batch_size=50)
    
    print(f"Extracted {features_df.shape[1]} features for {features_df.shape[0]} series")
    
    features_df.to_parquet('extracted_features_sample.parquet')
    print("Features saved to extracted_features_sample.parquet")
    
    return features_df


def analyze_feature_importance(features_df: pd.DataFrame):
    """
    Analyze and visualize feature importance.
    
    Parameters
    ----------
    features_df : pd.DataFrame
        DataFrame with extracted features
    """
    labels = features_df['label']
    feature_cols = [col for col in features_df.columns if col not in ['id', 'label']]
    
    importance_df = create_feature_importance_summary(features_df[feature_cols], labels)
    
    print("\nTop 20 most discriminative features:")
    print(importance_df.head(20)[['feature', 'cohen_d', 'p_value', 'ks_statistic']])
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    top_features = importance_df.head(20)
    axes[0, 0].barh(range(len(top_features)), top_features['abs_cohen_d'])
    axes[0, 0].set_yticks(range(len(top_features)))
    axes[0, 0].set_yticklabels(top_features['feature'], fontsize=8)
    axes[0, 0].set_xlabel("Cohen's d (absolute)")
    axes[0, 0].set_title("Feature Importance by Effect Size")
    axes[0, 0].invert_yaxis()
    
    axes[0, 1].scatter(importance_df['cohen_d'], -np.log10(importance_df['p_value']), 
                      alpha=0.5, s=20)
    axes[0, 1].axhline(y=-np.log10(0.05), color='r', linestyle='--', alpha=0.5)
    axes[0, 1].set_xlabel("Cohen's d")
    axes[0, 1].set_ylabel("-log10(p-value)")
    axes[0, 1].set_title("Volcano Plot")
    
    top_4_features = importance_df.head(4)['feature'].values
    
    for idx, feature in enumerate(top_4_features[:2]):
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
    plt.savefig('feature_importance_analysis.png', dpi=150)
    plt.close()
    
    print("\nFeature importance visualization saved to feature_importance_analysis.png")
    
    importance_df.to_csv('feature_importance.csv', index=False)
    print("Feature importance summary saved to feature_importance.csv")


def create_feature_correlation_analysis(features_df: pd.DataFrame, top_n: int = 30):
    """
    Analyze correlations between top features.
    
    Parameters
    ----------
    features_df : pd.DataFrame
        DataFrame with extracted features
    top_n : int
        Number of top features to analyze
    """
    labels = features_df['label']
    feature_cols = [col for col in features_df.columns if col not in ['id', 'label']]
    
    importance_df = create_feature_importance_summary(features_df[feature_cols], labels)
    top_features = importance_df.head(top_n)['feature'].values
    
    corr_matrix = features_df[top_features].corr()
    
    plt.figure(figsize=(12, 10))
    mask = np.triu(np.ones_like(corr_matrix), k=1)
    sns.heatmap(corr_matrix, mask=mask, cmap='coolwarm', center=0,
                square=True, linewidths=0.5, cbar_kws={"shrink": 0.8},
                vmin=-1, vmax=1)
    plt.title(f'Correlation Matrix of Top {top_n} Features')
    plt.tight_layout()
    plt.savefig('feature_correlation_matrix.png', dpi=150)
    plt.close()
    
    print(f"\nFeature correlation matrix saved to feature_correlation_matrix.png")


def main():
    """
    Main execution function.
    """
    print("Starting structural break analysis pipeline...")
    
    X_train, y_train = load_data()
    
    analyze_sample_series(X_train, y_train)
    
    features_df = run_feature_extraction(X_train, y_train, sample_size=1000)
    
    analyze_feature_importance(features_df)
    
    create_feature_correlation_analysis(features_df)
    
    print("\nAnalysis complete!")


if __name__ == '__main__':
    main()