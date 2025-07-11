"""
Cumulant calculations for time series analysis.

Cumulants are alternatives to moments that have better properties for 
heavy-tailed distributions and provide a more complete characterization
of probability distributions.
"""

import numpy as np
from scipy import stats
from typing import Union, Tuple, List


def raw_moment(x: np.ndarray, order: int) -> float:
    """
    Calculate raw moment of given order.
    
    Parameters
    ----------
    x : np.ndarray
        Input data array
    order : int
        Order of the moment
        
    Returns
    -------
    float
        Raw moment of specified order
        
    Examples
    --------
    >>> x = np.random.normal(0, 1, 1000)
    >>> raw_moment(x, 1)  # Should be close to 0
    >>> raw_moment(x, 2)  # Should be close to 1
    """
    return np.mean(x ** order)


def central_moment(x: np.ndarray, order: int) -> float:
    """
    Calculate central moment of given order.
    
    Parameters
    ----------
    x : np.ndarray
        Input data array
    order : int
        Order of the moment
        
    Returns
    -------
    float
        Central moment of specified order
        
    Examples
    --------
    >>> x = np.random.normal(0, 1, 1000)
    >>> central_moment(x, 2)  # Variance, should be close to 1
    >>> central_moment(x, 3)  # Should be close to 0 for normal dist
    """
    return np.mean((x - np.mean(x)) ** order)


def cumulant(x: np.ndarray, order: int) -> float:
    """
    Calculate cumulant of given order using moment-cumulant relations.
    
    For orders 1-4, uses direct formulas. For higher orders, uses
    recursive relations.
    
    Parameters
    ----------
    x : np.ndarray
        Input data array
    order : int
        Order of the cumulant (1-6 supported)
        
    Returns
    -------
    float
        Cumulant of specified order
        
    Examples
    --------
    >>> x = np.random.normal(0, 1, 1000)
    >>> cumulant(x, 1)  # Mean
    >>> cumulant(x, 2)  # Variance
    >>> cumulant(x, 3)  # Related to skewness
    >>> cumulant(x, 4)  # Related to excess kurtosis
    """
    if order == 1:
        return np.mean(x)
    elif order == 2:
        return np.var(x)
    elif order == 3:
        m1 = np.mean(x)
        m2 = raw_moment(x, 2)
        m3 = raw_moment(x, 3)
        return m3 - 3*m2*m1 + 2*m1**3
    elif order == 4:
        m1 = np.mean(x)
        m2 = raw_moment(x, 2)
        m3 = raw_moment(x, 3)
        m4 = raw_moment(x, 4)
        return m4 - 4*m3*m1 - 3*m2**2 + 12*m2*m1**2 - 6*m1**4
    elif order == 5:
        m1 = np.mean(x)
        m2 = raw_moment(x, 2)
        m3 = raw_moment(x, 3)
        m4 = raw_moment(x, 4)
        m5 = raw_moment(x, 5)
        return (m5 - 5*m4*m1 - 10*m3*m2 + 20*m3*m1**2 + 30*m2**2*m1 
                - 60*m2*m1**3 + 24*m1**5)
    elif order == 6:
        m1 = np.mean(x)
        m2 = raw_moment(x, 2)
        m3 = raw_moment(x, 3)
        m4 = raw_moment(x, 4)
        m5 = raw_moment(x, 5)
        m6 = raw_moment(x, 6)
        return (m6 - 6*m5*m1 - 15*m4*m2 + 30*m4*m1**2 - 10*m3**2 
                + 120*m3*m2*m1 - 120*m3*m1**3 + 30*m2**3 
                - 270*m2**2*m1**2 + 360*m2*m1**4 - 120*m1**6)
    else:
        raise ValueError(f"Cumulant of order {order} not implemented")


def standardized_cumulant(x: np.ndarray, order: int) -> float:
    """
    Calculate standardized cumulant (normalized by appropriate power of std).
    
    Parameters
    ----------
    x : np.ndarray
        Input data array
    order : int
        Order of the cumulant
        
    Returns
    -------
    float
        Standardized cumulant
        
    Examples
    --------
    >>> x = np.random.normal(0, 1, 1000)
    >>> standardized_cumulant(x, 3)  # Skewness
    >>> standardized_cumulant(x, 4)  # Excess kurtosis
    """
    k_n = cumulant(x, order)
    k_2 = cumulant(x, 2)
    
    if k_2 == 0:
        return np.nan
    
    return k_n / (k_2 ** (order/2))


def cumulant_features(x: np.ndarray, max_order: int = 6) -> dict:
    """
    Extract cumulant-based features from time series.
    
    Parameters
    ----------
    x : np.ndarray
        Input time series
    max_order : int, default=6
        Maximum order of cumulants to calculate
        
    Returns
    -------
    dict
        Dictionary containing cumulants and derived features
        
    Examples
    --------
    >>> x = np.random.normal(0, 1, 1000)
    >>> features = cumulant_features(x)
    >>> features.keys()
    dict_keys(['cumulant_1', 'cumulant_2', ..., 'skewness', 'excess_kurtosis'])
    """
    features = {}
    
    for order in range(1, max_order + 1):
        try:
            features[f'cumulant_{order}'] = cumulant(x, order)
            if order > 2:
                features[f'std_cumulant_{order}'] = standardized_cumulant(x, order)
        except:
            features[f'cumulant_{order}'] = np.nan
            if order > 2:
                features[f'std_cumulant_{order}'] = np.nan
    
    features['skewness'] = stats.skew(x)
    features['kurtosis'] = stats.kurtosis(x)
    features['jarque_bera'] = stats.jarque_bera(x)[0]
    
    return features


def log_cumulants(x: np.ndarray, orders: List[int] = [1, 2, 3, 4]) -> dict:
    """
    Calculate log-cumulants for heavy-tailed distribution analysis.
    
    Log-cumulants are cumulants of the log-transformed data, useful
    for analyzing multiplicative processes and heavy-tailed distributions.
    
    Parameters
    ----------
    x : np.ndarray
        Input data (must be positive)
    orders : List[int]
        Orders of cumulants to calculate
        
    Returns
    -------
    dict
        Dictionary of log-cumulants
    """
    x_positive = x[x > 0]
    
    if len(x_positive) < len(x) * 0.9:
        return {f'log_cumulant_{o}': np.nan for o in orders}
    
    log_x = np.log(x_positive)
    
    return {
        f'log_cumulant_{order}': cumulant(log_x, order)
        for order in orders
    }