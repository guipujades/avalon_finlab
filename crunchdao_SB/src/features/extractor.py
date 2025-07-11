"""
Main feature extraction pipeline for time series classification.

Combines all feature extraction modules into a unified interface.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
import warnings

from .cumulants import cumulant_features
from .robust_stats import robust_features
from .distribution import distribution_features
from .noise import noise_features
from .temporal import temporal_features


def extract_all_features(series: pd.Series, feature_groups: Optional[List[str]] = None) -> dict:
    """
    Extract all features from a time series.
    
    Parameters
    ----------
    series : pd.Series
        Time series data with 'value' column
    feature_groups : List[str], optional
        List of feature groups to extract. If None, extracts all.
        Options: 'cumulants', 'robust', 'distribution', 'noise', 'temporal'
        
    Returns
    -------
    dict
        Dictionary of extracted features
    """
    if feature_groups is None:
        feature_groups = ['cumulants', 'robust', 'distribution', 'noise', 'temporal']
    
    values = series['value'].values
    
    features = {}
    
    if 'cumulants' in feature_groups:
        try:
            features.update(cumulant_features(values))
        except Exception as e:
            print(f"Error in cumulant features: {e}")
    
    if 'robust' in feature_groups:
        try:
            features.update(robust_features(values))
        except Exception as e:
            print(f"Error in robust features: {e}")
    
    if 'distribution' in feature_groups:
        try:
            features.update(distribution_features(values))
        except Exception as e:
            print(f"Error in distribution features: {e}")
    
    if 'noise' in feature_groups:
        try:
            features.update(noise_features(values))
        except Exception as e:
            print(f"Error in noise features: {e}")
    
    if 'temporal' in feature_groups:
        try:
            features.update(temporal_features(values))
        except Exception as e:
            print(f"Error in temporal features: {e}")
    
    return features


def extract_features_before_after(series_data: pd.DataFrame, series_id: str) -> dict:
    """
    Extract features separately for before and after periods.
    
    Parameters
    ----------
    series_data : pd.DataFrame
        DataFrame with columns 'value' and 'period'
    series_id : str
        ID of the series
        
    Returns
    -------
    dict
        Dictionary with features for both periods and differences
    """
    before = series_data[series_data['period'] == 0]
    after = series_data[series_data['period'] == 1]
    
    features = {'id': series_id}
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        
        features_before = extract_all_features(before)
        features_after = extract_all_features(after)
    
    for key, value in features_before.items():
        features[f'{key}_before'] = value
    
    for key, value in features_after.items():
        features[f'{key}_after'] = value
    
    for key in features_before.keys():
        if key in features_after:
            diff = features_after[key] - features_before[key]
            ratio = features_after[key] / features_before[key] if features_before[key] != 0 else np.nan
            
            features[f'{key}_diff'] = diff
            features[f'{key}_ratio'] = ratio
            features[f'{key}_abs_diff'] = abs(diff)
            features[f'{key}_log_ratio'] = np.log(abs(ratio)) if ratio > 0 else np.nan
    
    features['n_before'] = len(before)
    features['n_after'] = len(after)
    features['n_ratio'] = len(after) / len(before) if len(before) > 0 else np.nan
    
    return features


def process_series_batch(X_batch: pd.DataFrame, y_batch: pd.DataFrame = None) -> pd.DataFrame:
    """
    Process a batch of series to extract features.
    
    Parameters
    ----------
    X_batch : pd.DataFrame
        Input data with columns 'id', 'value', 'period'
    y_batch : pd.DataFrame, optional
        Labels with columns 'id', 'label'
        
    Returns
    -------
    pd.DataFrame
        DataFrame with extracted features
    """
    unique_ids = X_batch['id'].unique()
    results = []
    
    for series_id in unique_ids:
        series_data = X_batch[X_batch['id'] == series_id]
        
        features = extract_features_before_after(series_data, series_id)
        
        if y_batch is not None:
            label = y_batch[y_batch['id'] == series_id]['label'].values[0]
            features['label'] = label
        
        results.append(features)
    
    return pd.DataFrame(results)


def parallel_feature_extraction(X: pd.DataFrame, y: pd.DataFrame = None, 
                              n_jobs: int = -1, batch_size: int = 100) -> pd.DataFrame:
    """
    Extract features in parallel for large datasets.
    
    Parameters
    ----------
    X : pd.DataFrame
        Input data
    y : pd.DataFrame, optional
        Labels
    n_jobs : int
        Number of parallel jobs (-1 for all CPUs)
    batch_size : int
        Number of series per batch
        
    Returns
    -------
    pd.DataFrame
        DataFrame with all extracted features
    """
    import multiprocessing
    
    if n_jobs == -1:
        n_jobs = multiprocessing.cpu_count()
    
    unique_ids = X['id'].unique()
    n_batches = (len(unique_ids) + batch_size - 1) // batch_size
    
    print(f"Processing {len(unique_ids)} series in {n_batches} batches using {n_jobs} workers")
    
    futures = []
    results = []
    
    with ProcessPoolExecutor(max_workers=n_jobs) as executor:
        for i in range(0, len(unique_ids), batch_size):
            batch_ids = unique_ids[i:i+batch_size]
            X_batch = X[X['id'].isin(batch_ids)]
            y_batch = y[y['id'].isin(batch_ids)] if y is not None else None
            
            future = executor.submit(process_series_batch, X_batch, y_batch)
            futures.append(future)
        
        for i, future in enumerate(as_completed(futures)):
            try:
                result = future.result()
                results.append(result)
                print(f"Completed batch {i+1}/{n_batches}")
            except Exception as e:
                print(f"Error in batch {i+1}: {e}")
    
    return pd.concat(results, ignore_index=True)


def create_feature_importance_summary(features_df: pd.DataFrame, labels: pd.Series) -> pd.DataFrame:
    """
    Create summary of feature importance based on simple statistical tests.
    
    Parameters
    ----------
    features_df : pd.DataFrame
        DataFrame with extracted features
    labels : pd.Series
        Binary labels
        
    Returns
    -------
    pd.DataFrame
        Summary of feature importance
    """
    from scipy import stats
    
    importance = []
    
    for col in features_df.columns:
        if col in ['id', 'label']:
            continue
        
        try:
            values = features_df[col].values
            mask = ~np.isnan(values) & ~np.isinf(values)
            
            if mask.sum() < 10:
                continue
            
            values = values[mask]
            labels_masked = labels[mask]
            
            group0 = values[labels_masked == 0]
            group1 = values[labels_masked == 1]
            
            if len(group0) < 5 or len(group1) < 5:
                continue
            
            t_stat, p_value = stats.ttest_ind(group0, group1)
            
            ks_stat, ks_p = stats.ks_2samp(group0, group1)
            
            mean_diff = np.mean(group1) - np.mean(group0)
            std_pooled = np.sqrt((np.var(group0) + np.var(group1)) / 2)
            cohen_d = mean_diff / std_pooled if std_pooled > 0 else 0
            
            importance.append({
                'feature': col,
                't_statistic': t_stat,
                'p_value': p_value,
                'ks_statistic': ks_stat,
                'ks_p_value': ks_p,
                'cohen_d': cohen_d,
                'mean_diff': mean_diff,
                'mean_no_break': np.mean(group0),
                'mean_break': np.mean(group1)
            })
        except Exception as e:
            continue
    
    importance_df = pd.DataFrame(importance)
    importance_df['abs_cohen_d'] = np.abs(importance_df['cohen_d'])
    importance_df = importance_df.sort_values('abs_cohen_d', ascending=False)
    
    return importance_df