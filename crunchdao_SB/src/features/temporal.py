"""
Temporal and dynamic features for time series.

Captures autocorrelation structure, memory effects, and dynamic properties.
"""

import numpy as np
from scipy import stats, signal
from scipy.fftpack import fft
from typing import List, Tuple, Dict, Optional


def autocorrelation_features(x: np.ndarray, max_lag: int = 50) -> dict:
    """
    Extract features from autocorrelation function.
    
    Parameters
    ----------
    x : np.ndarray
        Input time series
    max_lag : int
        Maximum lag to compute
        
    Returns
    -------
    dict
        Dictionary of ACF-based features
    """
    n = len(x)
    max_lag = min(max_lag, n // 4)
    
    x_centered = x - np.mean(x)
    c0 = np.dot(x_centered, x_centered) / n
    
    acf = np.zeros(max_lag + 1)
    acf[0] = 1.0
    
    for k in range(1, max_lag + 1):
        c_k = np.dot(x_centered[:-k], x_centered[k:]) / n
        acf[k] = c_k / c0 if c0 > 0 else 0
    
    features = {
        'acf_1': acf[1] if len(acf) > 1 else np.nan,
        'acf_2': acf[2] if len(acf) > 2 else np.nan,
        'acf_3': acf[3] if len(acf) > 3 else np.nan,
        'acf_5': acf[5] if len(acf) > 5 else np.nan,
        'acf_10': acf[10] if len(acf) > 10 else np.nan
    }
    
    first_zero = np.where(acf[1:] <= 0)[0]
    features['first_zero_crossing'] = first_zero[0] + 1 if len(first_zero) > 0 else max_lag
    
    first_min = np.argmin(acf[1:]) + 1
    features['first_minimum'] = first_min
    features['first_minimum_value'] = acf[first_min]
    
    features['acf_sum'] = np.sum(acf[1:])
    features['acf_sum_squares'] = np.sum(acf[1:]**2)
    
    e_folding = np.where(acf[1:] <= 1/np.e)[0]
    features['decorrelation_time'] = e_folding[0] + 1 if len(e_folding) > 0 else max_lag
    
    return features


def partial_autocorrelation(x: np.ndarray, max_lag: int = 20) -> np.ndarray:
    """
    Calculate partial autocorrelation function using Yule-Walker.
    
    Parameters
    ----------
    x : np.ndarray
        Input time series
    max_lag : int
        Maximum lag
        
    Returns
    -------
    np.ndarray
        PACF values
    """
    pacf = np.zeros(max_lag + 1)
    pacf[0] = 1.0
    
    for k in range(1, max_lag + 1):
        r = np.zeros(k)
        for i in range(k):
            r[i] = np.corrcoef(x[:-k+i], x[k-i:])[0, 1]
        
        R = np.zeros((k, k))
        for i in range(k):
            for j in range(k):
                lag = abs(i - j)
                if lag == 0:
                    R[i, j] = 1.0
                else:
                    R[i, j] = r[lag-1]
        
        try:
            phi = np.linalg.solve(R, r)
            pacf[k] = phi[-1]
        except:
            pacf[k] = 0.0
    
    return pacf


def hurst_exponent(x: np.ndarray, min_window: int = 10) -> float:
    """
    Estimate Hurst exponent using R/S analysis.
    
    H < 0.5: anti-persistent
    H = 0.5: random walk
    H > 0.5: persistent (long memory)
    
    Parameters
    ----------
    x : np.ndarray
        Input time series
    min_window : int
        Minimum window size
        
    Returns
    -------
    float
        Hurst exponent estimate
    """
    n = len(x)
    max_window = n // 2
    
    window_sizes = []
    rs_values = []
    
    for w in range(min_window, max_window, max(1, (max_window - min_window) // 20)):
        rs_list = []
        
        for start in range(0, n - w, w):
            segment = x[start:start + w]
            
            mean_seg = np.mean(segment)
            deviations = np.cumsum(segment - mean_seg)
            
            R = np.max(deviations) - np.min(deviations)
            S = np.std(segment, ddof=1)
            
            if S > 0:
                rs_list.append(R / S)
        
        if rs_list:
            window_sizes.append(w)
            rs_values.append(np.mean(rs_list))
    
    if len(window_sizes) > 2:
        log_ws = np.log(window_sizes)
        log_rs = np.log(rs_values)
        
        hurst, _ = np.polyfit(log_ws, log_rs, 1)
        return hurst
    
    return 0.5


def detrended_fluctuation_analysis(x: np.ndarray, min_box: int = 4) -> float:
    """
    Detrended Fluctuation Analysis (DFA) for scaling exponent.
    
    Parameters
    ----------
    x : np.ndarray
        Input time series
    min_box : int
        Minimum box size
        
    Returns
    -------
    float
        DFA scaling exponent
    """
    n = len(x)
    integrated = np.cumsum(x - np.mean(x))
    
    max_box = n // 4
    box_sizes = np.unique(np.logspace(np.log10(min_box), np.log10(max_box), 20).astype(int))
    
    fluctuations = []
    
    for box_size in box_sizes:
        n_boxes = n // box_size
        
        if n_boxes == 0:
            continue
        
        f_box = []
        
        for i in range(n_boxes):
            segment = integrated[i*box_size:(i+1)*box_size]
            x_coord = np.arange(len(segment))
            
            coeffs = np.polyfit(x_coord, segment, 1)
            fit = np.polyval(coeffs, x_coord)
            
            f_box.append(np.sqrt(np.mean((segment - fit)**2)))
        
        if f_box:
            fluctuations.append((box_size, np.mean(f_box)))
    
    if len(fluctuations) > 2:
        box_sizes, f_values = zip(*fluctuations)
        log_boxes = np.log(box_sizes)
        log_f = np.log(f_values)
        
        alpha, _ = np.polyfit(log_boxes, log_f, 1)
        return alpha
    
    return 0.5


def spectral_features(x: np.ndarray) -> dict:
    """
    Extract features from power spectral density.
    
    Parameters
    ----------
    x : np.ndarray
        Input time series
        
    Returns
    -------
    dict
        Dictionary of spectral features
    """
    freqs, psd = signal.periodogram(x, scaling='density')
    
    total_power = np.sum(psd)
    
    cumsum_power = np.cumsum(psd) / total_power
    median_freq_idx = np.argmax(cumsum_power >= 0.5)
    
    peak_idx = np.argmax(psd[1:]) + 1
    
    weighted_freq = np.sum(freqs * psd) / total_power
    
    spectral_entropy = -np.sum(psd[psd > 0] / total_power * np.log(psd[psd > 0] / total_power))
    
    features = {
        'spectral_peak_freq': freqs[peak_idx],
        'spectral_peak_power': psd[peak_idx] / total_power,
        'spectral_median_freq': freqs[median_freq_idx],
        'spectral_mean_freq': weighted_freq,
        'spectral_entropy': spectral_entropy,
        'spectral_rolloff_95': freqs[np.argmax(cumsum_power >= 0.95)],
        'spectral_spread': np.sqrt(np.sum((freqs - weighted_freq)**2 * psd) / total_power)
    }
    
    low_freq_power = np.sum(psd[freqs < 0.1])
    high_freq_power = np.sum(psd[freqs >= 0.1])
    features['lf_hf_ratio'] = low_freq_power / high_freq_power if high_freq_power > 0 else np.nan
    
    return features


def nonlinearity_tests(x: np.ndarray) -> dict:
    """
    Test for nonlinearity in time series.
    
    Parameters
    ----------
    x : np.ndarray
        Input time series
        
    Returns
    -------
    dict
        Dictionary of nonlinearity test results
    """
    features = {}
    
    x_squared = x**2
    x_cubed = x**3
    
    corr_x2 = np.corrcoef(x[:-1], x_squared[1:])[0, 1]
    corr_x3 = np.corrcoef(x[:-1], x_cubed[1:])[0, 1]
    
    features['nonlin_corr_x2'] = corr_x2
    features['nonlin_corr_x3'] = corr_x3
    
    try:
        surrogate = np.random.permutation(x)
        orig_acf = autocorrelation_features(x, max_lag=10)
        surr_acf = autocorrelation_features(surrogate, max_lag=10)
        
        features['surrogate_test'] = abs(orig_acf['acf_1'] - surr_acf['acf_1'])
    except:
        features['surrogate_test'] = np.nan
    
    return features


def temporal_features(x: np.ndarray) -> dict:
    """
    Extract comprehensive temporal features.
    
    Parameters
    ----------
    x : np.ndarray
        Input time series
        
    Returns
    -------
    dict
        Dictionary of temporal features
    """
    features = {}
    
    features.update(autocorrelation_features(x))
    
    pacf = partial_autocorrelation(x, max_lag=10)
    features['pacf_1'] = pacf[1] if len(pacf) > 1 else np.nan
    features['pacf_2'] = pacf[2] if len(pacf) > 2 else np.nan
    features['pacf_5'] = pacf[5] if len(pacf) > 5 else np.nan
    
    features['hurst_exponent'] = hurst_exponent(x)
    features['dfa_exponent'] = detrended_fluctuation_analysis(x)
    
    features.update(spectral_features(x))
    features.update(nonlinearity_tests(x))
    
    features['mean_abs_change'] = np.mean(np.abs(np.diff(x)))
    features['mean_change'] = np.mean(np.diff(x))
    features['mean_second_derivative'] = np.mean(np.diff(np.diff(x)))
    
    return features