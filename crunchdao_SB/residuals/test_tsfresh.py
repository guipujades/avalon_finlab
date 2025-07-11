"""
Test TSFresh feature extraction on structural break data.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sys
sys.path.append('src')

from features.tsfresh_extractor import TSFreshExtractor, create_tsfresh_report, TSFRESH_AVAILABLE


def test_tsfresh_extraction():
    """Test TSFresh feature extraction."""
    
    if not TSFRESH_AVAILABLE:
        print("TSFresh not installed. Install with:")
        print("pip install -r requirements_tsfresh.txt")
        return
    
    print("Loading data...")
    X_train = pd.read_parquet('database/X_train.parquet').reset_index()
    y_train = pd.read_parquet('database/y_train.parquet')
    y_train = y_train.rename(columns={'structural_breakpoint': 'label'})
    
    sample_size = 500
    unique_ids = X_train['id'].unique()[:sample_size]
    X_sample = X_train[X_train['id'].isin(unique_ids)]
    y_sample = y_train.loc[unique_ids].reset_index()
    y_sample = y_sample.rename(columns={'index': 'id'})
    
    print(f"\nProcessing {sample_size} series...")
    print(f"Break rate in sample: {y_sample['label'].mean():.2%}")
    
    print("\n" + "="*60)
    print("TESTING MINIMAL FEATURE SET (fast)")
    print("="*60)
    
    extractor_minimal = TSFreshExtractor(feature_set='minimal')
    features_minimal = extractor_minimal.extract_and_select(
        X_sample, 
        y_sample, 
        n_jobs=1,  # Mudando para 1 para evitar problemas de multiprocessing
        fdr_level=0.05
    )
    
    print(f"\nMinimal features shape: {features_minimal.shape}")
    
    print("\n" + "="*60)
    print("TESTING EFFICIENT FEATURE SET (recommended)")
    print("="*60)
    
    extractor_efficient = TSFreshExtractor(feature_set='efficient')
    features_efficient = extractor_efficient.extract_and_select(
        X_sample, 
        y_sample, 
        n_jobs=1,  # Sem paralelização
        fdr_level=0.05
    )
    
    print(f"\nEfficient features shape: {features_efficient.shape}")
    
    y_aligned = y_sample.set_index('id')['label']
    y_aligned = y_aligned.loc[features_efficient.index]
    
    importance = extractor_efficient.get_feature_importance(features_efficient, y_aligned)
    
    create_tsfresh_report(features_efficient, importance, 'tsfresh_analysis_report.txt')
    
    visualize_tsfresh_results(features_efficient, y_aligned, importance)
    
    test_feature_predictive_power(features_efficient, y_aligned)
    
    if features_efficient.shape[1] > 0:
        print("\nTop 10 selected features:")
        for i, feat in enumerate(features_efficient.columns[:10]):
            print(f"  {i+1}. {feat}")


def visualize_tsfresh_results(features, labels, importance):
    """Visualize TSFresh analysis results."""
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    top_features = importance.head(20)
    axes[0, 0].barh(range(len(top_features)), top_features['abs_cohen_d'])
    axes[0, 0].set_yticks(range(len(top_features)))
    axes[0, 0].set_yticklabels([f[:40] + '...' if len(f) > 40 else f 
                                for f in top_features['feature']], fontsize=8)
    axes[0, 0].set_xlabel("Cohen's d (absolute)")
    axes[0, 0].set_title("Top 20 TSFresh Features by Effect Size")
    axes[0, 0].invert_yaxis()
    
    feature_types = importance['feature_type'].value_counts().head(10)
    axes[0, 1].bar(range(len(feature_types)), feature_types.values)
    axes[0, 1].set_xticks(range(len(feature_types)))
    axes[0, 1].set_xticklabels(feature_types.index, rotation=45, ha='right')
    axes[0, 1].set_ylabel('Count')
    axes[0, 1].set_title('Distribution of Selected Feature Types')
    
    top_2_features = importance.head(2)['feature'].values
    
    for idx, feature in enumerate(top_2_features):
        ax = axes[1, idx]
        
        no_break = features.loc[labels == False, feature].dropna()
        with_break = features.loc[labels == True, feature].dropna()
        
        ax.hist([no_break, with_break], bins=30, alpha=0.7, 
                label=['No Break', 'Break'], density=True)
        ax.set_xlabel(feature[:50] + '...' if len(feature) > 50 else feature)
        ax.set_ylabel('Density')
        ax.legend()
        ax.set_title(f'Distribution of Top Feature #{idx+1}')
    
    plt.tight_layout()
    plt.savefig('tsfresh_feature_analysis.png', dpi=150)
    plt.close()
    
    print("\nVisualization saved to tsfresh_feature_analysis.png")


def test_feature_predictive_power(features, labels):
    """Test predictive power of TSFresh features."""
    from sklearn.model_selection import cross_val_score
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
    
    print("\n" + "="*60)
    print("TESTING PREDICTIVE POWER")
    print("="*60)
    
    if features.shape[1] == 0:
        print("No features selected!")
        return
    
    features_clean = features.fillna(features.median())
    features_clean = features_clean.replace([np.inf, -np.inf], features_clean.median())
    
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('rf', RandomForestClassifier(n_estimators=100, random_state=42))
    ])
    
    scores = cross_val_score(pipeline, features_clean, labels, 
                           cv=5, scoring='roc_auc', n_jobs=-1)
    
    print(f"\nRandom Forest with TSFresh features:")
    print(f"ROC AUC: {np.mean(scores):.3f} (+/- {np.std(scores):.3f})")
    
    if features.shape[1] > 100:
        print("\nTesting with top 50 features only...")
        top_50_features = features[features.columns[:50]]
        
        scores_top50 = cross_val_score(pipeline, top_50_features, labels, 
                                     cv=5, scoring='roc_auc', n_jobs=-1)
        
        print(f"ROC AUC (top 50): {np.mean(scores_top50):.3f} (+/- {np.std(scores_top50):.3f})")
    
    from sklearn.decomposition import PCA
    
    pca = PCA(n_components=min(20, features_clean.shape[1]))
    features_pca = pca.fit_transform(features_clean)
    
    plt.figure(figsize=(10, 8))
    scatter = plt.scatter(features_pca[:, 0], features_pca[:, 1], 
                         c=labels, cmap='coolwarm', alpha=0.6)
    plt.colorbar(scatter, label='Has Break')
    plt.xlabel('First Principal Component')
    plt.ylabel('Second Principal Component')
    plt.title('TSFresh Features - PCA Visualization')
    plt.savefig('tsfresh_pca_visualization.png', dpi=150)
    plt.close()
    
    print("\nPCA visualization saved to tsfresh_pca_visualization.png")


def compare_with_custom_features():
    """Compare TSFresh with our custom features."""
    print("\n" + "="*60)
    print("COMPARISON WITH CUSTOM FEATURES")
    print("="*60)
    
    try:
        custom_features = pd.read_parquet('features_simple.parquet')
        print(f"Custom features: {custom_features.shape[1]} features")
        
        tsfresh_report = pd.read_csv('tsfresh_analysis_report.txt', nrows=0)
        print("See tsfresh_analysis_report.txt for detailed comparison")
        
    except:
        print("Run simple_analysis.py first to generate custom features for comparison")


def main():
    """Run TSFresh analysis."""
    print("="*60)
    print("TSFRESH FEATURE EXTRACTION ANALYSIS")
    print("="*60)
    
    test_tsfresh_extraction()
    
    compare_with_custom_features()
    
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)
    print("\nGenerated files:")
    print("- tsfresh_analysis_report.txt")
    print("- tsfresh_feature_analysis.png")
    print("- tsfresh_pca_visualization.png")
    
    print("\nNext steps:")
    print("1. Review the report to see which features are most important")
    print("2. Use selected features with constellation classifier")
    print("3. Combine TSFresh + custom domain features for best results")


if __name__ == '__main__':
    main()