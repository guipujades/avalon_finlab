"""
Robust statistical measures for time series characterization.

These statistics are less sensitive to outliers and heavy tails
compared to traditional moment-based measures.
"""

import numpy as np
from scipy import stats
from typing import Union, Tuple, List, Optional


def mad(x: np.ndarray, center: Optional[float] = None) -> float:
    """
    Median Absolute Deviation - robust measure of scale.
    
    Parameters
    ----------
    x : np.ndarray
        Input data
    center : float, optional
        Center point for deviations. If None, uses median
        
    Returns
    -------
    float
        Median absolute deviation
        
    Examples
    --------
    >>> x = np.random.normal(0, 1, 1000)
    >>> mad(x)  # Should be close to 0.6745 * 1 for normal dist
    """
    if center is None:
        center = np.median(x)
    
    return np.median(np.abs(x - center))


def robust_scale(x: np.ndarray, method: str = 'mad') -> float:
    """
    Calculate robust scale estimate.
    
    Parameters
    ----------
    x : np.ndarray
        Input data
    method : str
        Method to use: 'mad', 'iqr', 'sn', 'qn'
        
    Returns
    -------
    float
        Robust scale estimate
    """
    if method == 'mad':
        return mad(x) * 1.4826
    elif method == 'iqr':
        return np.percentile(x, 75) - np.percentile(x, 25)
    elif method == 'sn':
        return sn_scale(x)
    elif method == 'qn':
        return qn_scale(x)
    else:
        raise ValueError(f"Unknown method: {method}")


def sn_scale(x: np.ndarray) -> float:
    """
    Rousseeuw & Croux's Sn scale estimator.
    
    More efficient than MAD, with 58% efficiency at normal distribution.
    
    Parameters
    ----------
    x : np.ndarray
        Input data
        
    Returns
    -------
    float
        Sn scale estimate
    """
    n = len(x)
    if n < 2:
        return 0.0
    
    medians = np.empty(n)
    for i in range(n):
        medians[i] = np.median(np.abs(x - x[i]))
    
    return 1.1926 * np.median(medians)


def qn_scale(x: np.ndarray) -> float:
    """
    Rousseeuw & Croux's Qn scale estimator.
    
    Even more efficient than Sn, with 82% efficiency at normal distribution.
    
    Parameters
    ----------
    x : np.ndarray
        Input data
        
    Returns
    -------
    float
        Qn scale estimate
    """
    n = len(x)
    if n < 2:
        return 0.0
    
    h = n // 2 + 1
    differences = []
    
    for i in range(n-1):
        for j in range(i+1, n):
            differences.append(abs(x[i] - x[j]))
    
    differences.sort()
    k = h * (h - 1) // 2
    
    return 2.2219 * differences[k-1] if k > 0 else 0.0


def trimmed_stats(x: np.ndarray, trim: float = 0.1) -> dict:
    """
    Calculate trimmed mean and variance.
    
    Parameters
    ----------
    x : np.ndarray
        Input data
    trim : float
        Proportion to trim from each end
        
    Returns
    -------
    dict
        Dictionary with trimmed statistics
    """
    return {
        'trimmed_mean': stats.trim_mean(x, trim),
        'trimmed_std': np.sqrt(stats.trimvar(x, (trim, trim))),
        'winsorized_mean': stats.mstats.winsorize(x, (trim, trim)).mean(),
        'winsorized_std': stats.mstats.winsorize(x, (trim, trim)).std()
    }


def quantile_features(x: np.ndarray) -> dict:
    """
    Extract quantile-based features.
    
    Parameters
    ----------
    x : np.ndarray
        Input data
        
    Returns
    -------
    dict
        Dictionary of quantile features
    """
    percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    quantiles = np.percentile(x, percentiles)
    
    features = {f'q{p}': q for p, q in zip(percentiles, quantiles)}
    
    features['iqr'] = features['q75'] - features['q25']
    features['iqr_scale'] = features['iqr'] / 1.349
    features['range_90'] = features['q95'] - features['q5']
    features['range_98'] = features['q99'] - features['q1']
    features['midhinge'] = (features['q75'] + features['q25']) / 2
    features['trimean'] = (features['q25'] + 2*features['q50'] + features['q75']) / 4
    
    features['tail_ratio'] = (features['q95'] - features['q50']) / (features['q50'] - features['q5'])
    features['skew_yule'] = ((features['q75'] - features['q50']) - (features['q50'] - features['q25'])) / features['iqr']
    features['skew_kelly'] = (features['q90'] - features['q50'] - features['q10']) / (features['q90'] - features['q10'])
    
    return features


def medcouple(x: np.ndarray) -> float:
    """
    Calculate medcouple - robust measure of skewness.
    
    Parameters
    ----------
    x : np.ndarray
        Input data
        
    Returns
    -------
    float
        Medcouple value between -1 and 1
    """
    x_sorted = np.sort(x)
    n = len(x_sorted)
    median = np.median(x_sorted)
    
    x_plus = x_sorted[x_sorted >= median]
    x_minus = x_sorted[x_sorted <= median]
    
    if len(x_plus) == 0 or len(x_minus) == 0:
        return 0.0
    
    h_values = []
    for x_i in x_minus:
        for x_j in x_plus:
            if x_j != x_i:
                h = (x_j + x_i - 2*median) / (x_j - x_i)
                h_values.append(h)
    
    return np.median(h_values) if h_values else 0.0


def robust_features(x: np.ndarray) -> dict:
    """
    Extract comprehensive set of robust features.
    
    Parameters
    ----------
    x : np.ndarray
        Input time series
        
    Returns
    -------
    dict
        Dictionary of robust statistics
    """
    features = {}
    
    features['median'] = np.median(x)
    features['mad'] = mad(x)
    features['mad_scaled'] = features['mad'] * 1.4826
    
    features.update(quantile_features(x))
    features.update(trimmed_stats(x))
    
    features['sn_scale'] = sn_scale(x)
    features['qn_scale'] = qn_scale(x)
    features['medcouple'] = medcouple(x)
    
    features['cv_robust'] = features['mad'] / features['median'] if features['median'] != 0 else np.nan
    features['efficiency_ratio'] = features['mad_scaled'] / np.std(x) if np.std(x) > 0 else np.nan
    
    return features