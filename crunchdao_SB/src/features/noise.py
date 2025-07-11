"""
Noise characterization and signal-to-noise ratio estimation.

Methods for quantifying the noise level and structure in time series data.
"""

import numpy as np
from scipy import signal, stats
from scipy.fftpack import fft, fftfreq
from typing import Tuple, Dict, Optional


def estimate_noise_std(x: np.ndarray, method: str = 'mad') -> float:
    """
    Estimate noise standard deviation using various methods.
    
    Parameters
    ----------
    x : np.ndarray
        Input time series
    method : str
        Method to use: 'mad', 'wavelet', 'differences', 'highpass'
        
    Returns
    -------
    float
        Estimated noise standard deviation
    """
    if method == 'mad':
        differences = np.diff(x)
        mad = np.median(np.abs(differences - np.median(differences)))
        return mad / 0.6745
    
    elif method == 'wavelet':
        return wavelet_noise_estimate(x)
    
    elif method == 'differences':
        differences = np.diff(x)
        return np.std(differences) / np.sqrt(2)
    
    elif method == 'highpass':
        return highpass_noise_estimate(x)
    
    else:
        raise ValueError(f"Unknown method: {method}")


def wavelet_noise_estimate(x: np.ndarray) -> float:
    """
    Estimate noise using wavelet-based method (Donoho & Johnstone).
    
    Uses the median absolute deviation of the finest wavelet coefficients.
    
    Parameters
    ----------
    x : np.ndarray
        Input time series
        
    Returns
    -------
    float
        Noise standard deviation estimate
    """
    n = len(x)
    
    coeffs = []
    for i in range(n-1):
        coeffs.append((x[i+1] - x[i]) / np.sqrt(2))
    
    mad = np.median(np.abs(coeffs))
    
    return mad / 0.6745


def highpass_noise_estimate(x: np.ndarray, cutoff_ratio: float = 0.8) -> float:
    """
    Estimate noise from high-frequency components.
    
    Parameters
    ----------
    x : np.ndarray
        Input time series
    cutoff_ratio : float
        Ratio of Nyquist frequency for highpass filter
        
    Returns
    -------
    float
        Noise standard deviation estimate
    """
    nyquist = 0.5
    cutoff = cutoff_ratio * nyquist
    
    b, a = signal.butter(4, cutoff, btype='high')
    filtered = signal.filtfilt(b, a, x)
    
    return np.std(filtered)


def signal_to_noise_ratio(x: np.ndarray, method: str = 'decomposition') -> float:
    """
    Estimate signal-to-noise ratio.
    
    Parameters
    ----------
    x : np.ndarray
        Input time series
    method : str
        Method to use: 'decomposition', 'spectral', 'autocorrelation'
        
    Returns
    -------
    float
        Signal-to-noise ratio (in dB)
    """
    if method == 'decomposition':
        return snr_decomposition(x)
    elif method == 'spectral':
        return snr_spectral(x)
    elif method == 'autocorrelation':
        return snr_autocorrelation(x)
    else:
        raise ValueError(f"Unknown method: {method}")


def snr_decomposition(x: np.ndarray) -> float:
    """
    SNR using signal decomposition approach.
    
    Decomposes signal into trend + noise using lowpass filtering.
    """
    b, a = signal.butter(4, 0.1)
    trend = signal.filtfilt(b, a, x)
    noise = x - trend
    
    signal_power = np.var(trend)
    noise_power = np.var(noise)
    
    if noise_power == 0:
        return np.inf
    
    return 10 * np.log10(signal_power / noise_power)


def snr_spectral(x: np.ndarray, signal_band: Tuple[float, float] = (0.0, 0.1)) -> float:
    """
    SNR using spectral analysis.
    
    Parameters
    ----------
    x : np.ndarray
        Input time series
    signal_band : Tuple[float, float]
        Frequency band considered as signal (normalized 0-0.5)
    """
    n = len(x)
    freqs = fftfreq(n)
    fft_vals = np.abs(fft(x))
    
    normalized_freqs = np.abs(freqs[:n//2])
    power_spectrum = fft_vals[:n//2]**2
    
    signal_mask = (normalized_freqs >= signal_band[0]) & (normalized_freqs <= signal_band[1])
    
    signal_power = np.sum(power_spectrum[signal_mask])
    total_power = np.sum(power_spectrum)
    noise_power = total_power - signal_power
    
    if noise_power == 0:
        return np.inf
    
    return 10 * np.log10(signal_power / noise_power)


def snr_autocorrelation(x: np.ndarray) -> float:
    """
    SNR estimation using autocorrelation structure.
    
    Assumes noise is white and signal has autocorrelation.
    """
    acf = np.correlate(x - np.mean(x), x - np.mean(x), mode='full')
    acf = acf[len(acf)//2:]
    acf = acf / acf[0]
    
    noise_var_estimate = np.var(x) * (1 - acf[1])
    signal_var_estimate = np.var(x) - noise_var_estimate
    
    if noise_var_estimate <= 0:
        return np.inf
    
    return 10 * np.log10(signal_var_estimate / noise_var_estimate)


def noise_color(x: np.ndarray) -> dict:
    """
    Characterize noise color (white, pink, brown, etc).
    
    Analyzes the spectral slope to determine noise type.
    
    Parameters
    ----------
    x : np.ndarray
        Input time series
        
    Returns
    -------
    dict
        Dictionary with spectral slope and noise type
    """
    n = len(x)
    freqs = fftfreq(n)[:n//2]
    fft_vals = np.abs(fft(x))[:n//2]
    
    mask = (freqs > 0) & (fft_vals > 0)
    log_freqs = np.log10(freqs[mask])
    log_power = np.log10(fft_vals[mask]**2)
    
    slope, intercept = np.polyfit(log_freqs, log_power, 1)
    
    noise_types = {
        'white': 0,
        'pink': -1,
        'brown': -2,
        'blue': 1,
        'violet': 2
    }
    
    closest_type = min(noise_types.items(), key=lambda x: abs(x[1] - slope))[0]
    
    return {
        'spectral_slope': slope,
        'noise_type': closest_type,
        'slope_deviation': abs(slope - noise_types[closest_type])
    }


def local_noise_variation(x: np.ndarray, window_size: int = None) -> dict:
    """
    Analyze how noise characteristics vary over time.
    
    Parameters
    ----------
    x : np.ndarray
        Input time series
    window_size : int, optional
        Window size for local analysis
        
    Returns
    -------
    dict
        Dictionary of local noise statistics
    """
    if window_size is None:
        window_size = max(10, len(x) // 20)
    
    n_windows = len(x) - window_size + 1
    local_stds = np.zeros(n_windows)
    
    for i in range(n_windows):
        window = x[i:i+window_size]
        detrended = signal.detrend(window)
        local_stds[i] = np.std(detrended)
    
    return {
        'noise_std_mean': np.mean(local_stds),
        'noise_std_std': np.std(local_stds),
        'noise_std_cv': np.std(local_stds) / np.mean(local_stds) if np.mean(local_stds) > 0 else np.nan,
        'noise_std_trend': np.polyfit(range(len(local_stds)), local_stds, 1)[0],
        'heteroscedasticity': np.std(local_stds) / np.mean(local_stds) > 0.1
    }


def noise_features(x: np.ndarray) -> dict:
    """
    Extract comprehensive noise characterization features.
    
    Parameters
    ----------
    x : np.ndarray
        Input time series
        
    Returns
    -------
    dict
        Dictionary of noise features
    """
    features = {}
    
    for method in ['mad', 'wavelet', 'differences', 'highpass']:
        features[f'noise_std_{method}'] = estimate_noise_std(x, method)
    
    for method in ['decomposition', 'spectral', 'autocorrelation']:
        features[f'snr_{method}'] = signal_to_noise_ratio(x, method)
    
    features.update(noise_color(x))
    features.update(local_noise_variation(x))
    
    features['coefficient_of_variation'] = np.std(x) / np.mean(x) if np.mean(x) != 0 else np.nan
    
    return features