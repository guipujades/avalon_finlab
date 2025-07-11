"""
Distribution characterization and testing for time series.

Provides tools to identify and quantify the distributional properties
of time series data.
"""

import numpy as np
from scipy import stats
from typing import Tuple, Dict, Optional
import warnings


def test_normality(x: np.ndarray) -> dict:
    """
    Comprehensive normality testing suite.
    
    Parameters
    ----------
    x : np.ndarray
        Input data
        
    Returns
    -------
    dict
        Dictionary with test statistics and p-values
        
    Examples
    --------
    >>> x = np.random.normal(0, 1, 1000)
    >>> results = test_normality(x)
    >>> results['shapiro_p'] > 0.05  # Should be True for normal data
    """
    results = {}
    
    if len(x) >= 3:
        stat, p = stats.shapiro(x)
        results['shapiro_stat'] = stat
        results['shapiro_p'] = p
    
    if len(x) >= 8:
        stat, p = stats.normaltest(x)
        results['dagostino_stat'] = stat
        results['dagostino_p'] = p
    
    if len(x) >= 20:
        stat, crit, sig = stats.anderson(x, dist='norm')
        results['anderson_stat'] = stat
        results['anderson_15pct'] = stat < crit[2]
    
    stat, p = stats.kstest(x, 'norm', args=(np.mean(x), np.std(x)))
    results['ks_stat'] = stat
    results['ks_p'] = p
    
    results['lilliefors_stat'] = lilliefors_test(x)
    
    return results


def lilliefors_test(x: np.ndarray) -> float:
    """
    Lilliefors test statistic for normality.
    
    More appropriate than KS test when parameters are estimated from data.
    
    Parameters
    ----------
    x : np.ndarray
        Input data
        
    Returns
    -------
    float
        Test statistic
    """
    x_standardized = (x - np.mean(x)) / np.std(x)
    
    n = len(x)
    x_sorted = np.sort(x_standardized)
    
    empirical_cdf = np.arange(1, n + 1) / n
    theoretical_cdf = stats.norm.cdf(x_sorted)
    
    d_plus = np.max(empirical_cdf - theoretical_cdf)
    d_minus = np.max(theoretical_cdf - np.concatenate(([0], empirical_cdf[:-1])))
    
    return max(d_plus, d_minus)


def fit_distributions(x: np.ndarray) -> dict:
    """
    Fit various distributions and return goodness-of-fit metrics.
    
    Parameters
    ----------
    x : np.ndarray
        Input data
        
    Returns
    -------
    dict
        Dictionary with fit results for each distribution
    """
    distributions = {
        'norm': stats.norm,
        't': stats.t,
        'cauchy': stats.cauchy,
        'laplace': stats.laplace,
        'logistic': stats.logistic,
        'gumbel_r': stats.gumbel_r,
        'expon': stats.expon,
        'gamma': stats.gamma,
        'lognorm': stats.lognorm
    }
    
    results = {}
    
    for name, dist in distributions.items():
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                params = dist.fit(x)
                
                ks_stat, ks_p = stats.kstest(x, lambda x: dist.cdf(x, *params))
                
                pdf_values = dist.pdf(x, *params)
                log_likelihood = np.sum(np.log(pdf_values[pdf_values > 0]))
                
                n_params = len(params)
                aic = 2 * n_params - 2 * log_likelihood
                bic = n_params * np.log(len(x)) - 2 * log_likelihood
                
                results[name] = {
                    'params': params,
                    'ks_stat': ks_stat,
                    'ks_p': ks_p,
                    'aic': aic,
                    'bic': bic,
                    'log_likelihood': log_likelihood
                }
        except:
            results[name] = {
                'params': None,
                'ks_stat': np.nan,
                'ks_p': np.nan,
                'aic': np.nan,
                'bic': np.nan,
                'log_likelihood': np.nan
            }
    
    return results


def entropy_measures(x: np.ndarray, bins: int = 30) -> dict:
    """
    Calculate various entropy measures.
    
    Parameters
    ----------
    x : np.ndarray
        Input data
    bins : int
        Number of bins for histogram
        
    Returns
    -------
    dict
        Dictionary of entropy measures
    """
    hist, edges = np.histogram(x, bins=bins, density=True)
    bin_width = edges[1] - edges[0]
    
    p = hist * bin_width
    p = p[p > 0]
    
    shannon_entropy = -np.sum(p * np.log(p))
    
    renyi_2 = -np.log(np.sum(p**2))
    renyi_3 = -0.5 * np.log(np.sum(p**3))
    
    sorted_p = np.sort(p)[::-1]
    cumsum_p = np.cumsum(sorted_p)
    gini = 1 - 2 * np.sum(cumsum_p) / len(p)
    
    return {
        'shannon_entropy': shannon_entropy,
        'renyi_entropy_2': renyi_2,
        'renyi_entropy_3': renyi_3,
        'gini_coefficient': gini,
        'entropy_ratio': shannon_entropy / np.log(bins)
    }


def tail_behavior(x: np.ndarray) -> dict:
    """
    Analyze tail behavior of distribution.
    
    Parameters
    ----------
    x : np.ndarray
        Input data
        
    Returns
    -------
    dict
        Dictionary of tail behavior metrics
    """
    x_sorted = np.sort(x)
    n = len(x_sorted)
    
    tail_sizes = [0.01, 0.05, 0.1]
    features = {}
    
    for alpha in tail_sizes:
        n_tail = int(n * alpha)
        if n_tail > 0:
            left_tail = x_sorted[:n_tail]
            right_tail = x_sorted[-n_tail:]
            
            features[f'left_tail_mean_{alpha}'] = np.mean(left_tail)
            features[f'right_tail_mean_{alpha}'] = np.mean(right_tail)
            features[f'tail_ratio_{alpha}'] = np.mean(right_tail) / np.abs(np.mean(left_tail)) if np.mean(left_tail) != 0 else np.nan
            
            features[f'hill_estimator_{alpha}'] = hill_estimator(x_sorted, n_tail)
    
    threshold = np.percentile(np.abs(x - np.mean(x)), 95)
    features['extreme_value_index'] = extreme_value_index(x, threshold)
    
    return features


def hill_estimator(x_sorted: np.ndarray, k: int) -> float:
    """
    Hill estimator for tail index.
    
    Parameters
    ----------
    x_sorted : np.ndarray
        Sorted data (ascending)
    k : int
        Number of order statistics to use
        
    Returns
    -------
    float
        Hill estimator
    """
    if k <= 0 or k >= len(x_sorted):
        return np.nan
    
    x_max = x_sorted[-1]
    
    if x_max <= 0:
        return np.nan
    
    sum_log = 0
    for i in range(1, k+1):
        if x_sorted[-i] > 0:
            sum_log += np.log(x_sorted[-i] / x_sorted[-(k+1)])
    
    return k / sum_log if sum_log > 0 else np.nan


def extreme_value_index(x: np.ndarray, threshold: float) -> float:
    """
    Estimate extreme value index using peaks over threshold.
    
    Parameters
    ----------
    x : np.ndarray
        Input data
    threshold : float
        Threshold for extreme values
        
    Returns
    -------
    float
        Extreme value index estimate
    """
    exceedances = x[x > threshold] - threshold
    
    if len(exceedances) < 10:
        return np.nan
    
    return np.mean(exceedances) / np.std(exceedances) if np.std(exceedances) > 0 else np.nan


def distribution_features(x: np.ndarray) -> dict:
    """
    Extract comprehensive distribution features.
    
    Parameters
    ----------
    x : np.ndarray
        Input time series
        
    Returns
    -------
    dict
        Dictionary of distribution features
    """
    features = {}
    
    features.update(test_normality(x))
    features.update(entropy_measures(x))
    features.update(tail_behavior(x))
    
    features['mean_median_ratio'] = np.mean(x) / np.median(x) if np.median(x) != 0 else np.nan
    features['std_mad_ratio'] = np.std(x) / (1.4826 * np.median(np.abs(x - np.median(x))))
    
    return features