"""
Multi-dimensional probabilistic classification system for time series.

Each series is classified along multiple dimensions simultaneously,
creating a probabilistic positioning in a multi-dimensional grid.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Callable
from dataclasses import dataclass
from scipy import stats


@dataclass
class ClassificationDimension:
    """
    Represents one dimension of classification.
    
    Attributes
    ----------
    name : str
        Name of the classification dimension
    classifier : Callable
        Function that takes series values and returns probability
    description : str
        Description of what this dimension represents
    """
    name: str
    classifier: Callable[[np.ndarray], float]
    description: str


class StationarityClassifier:
    """
    Classifies series based on stationarity properties.
    
    Returns probability of being stationary (0-1).
    """
    
    def __init__(self):
        self.tests = {
            'adf': self._adf_test,
            'kpss': self._kpss_test,
            'pp': self._pp_test
        }
    
    def _adf_test(self, x: np.ndarray) -> float:
        """Augmented Dickey-Fuller test for unit root."""
        from statsmodels.tsa.stattools import adfuller
        try:
            result = adfuller(x, autolag='AIC')
            p_value = result[1]
            return 1 - p_value
        except:
            return 0.5
    
    def _kpss_test(self, x: np.ndarray) -> float:
        """KPSS test for stationarity."""
        from statsmodels.tsa.stattools import kpss
        try:
            result = kpss(x, regression='c')
            p_value = result[1]
            return p_value
        except:
            return 0.5
    
    def _pp_test(self, x: np.ndarray) -> float:
        """Phillips-Perron test."""
        try:
            n = len(x)
            y_lag = x[:-1]
            y_diff = np.diff(x)
            
            coef = np.corrcoef(y_lag, y_diff)[0, 1]
            t_stat = coef * np.sqrt(n - 1)
            
            p_value = 2 * (1 - stats.norm.cdf(abs(t_stat)))
            return 1 - p_value
        except:
            return 0.5
    
    def classify(self, x: np.ndarray) -> float:
        """
        Combine multiple stationarity tests into single probability.
        
        Parameters
        ----------
        x : np.ndarray
            Time series values
            
        Returns
        -------
        float
            Probability of being stationary (0-1)
        """
        scores = []
        weights = [0.4, 0.4, 0.2]
        
        for i, (name, test) in enumerate(self.tests.items()):
            score = test(x)
            scores.append(score * weights[i])
        
        return np.clip(sum(scores), 0, 1)


class NoiseClassifier:
    """
    Classifies series based on noise characteristics.
    
    Returns probability from clean (0) to noisy (1).
    """
    
    def classify(self, x: np.ndarray) -> float:
        """
        Estimate noise level using multiple methods.
        
        Parameters
        ----------
        x : np.ndarray
            Time series values
            
        Returns
        -------
        float
            Noise level probability (0=clean, 1=very noisy)
        """
        diff1 = np.diff(x)
        diff2 = np.diff(diff1)
        
        noise_ratio = np.std(diff1) / (np.std(x) + 1e-8)
        
        acf1 = np.corrcoef(x[:-1], x[1:])[0, 1] if len(x) > 1 else 0
        noise_score = 1 - abs(acf1)
        
        high_freq_power = np.sum(np.abs(np.fft.fft(x)[len(x)//4:]))**2
        total_power = np.sum(np.abs(np.fft.fft(x)))**2
        freq_ratio = high_freq_power / (total_power + 1e-8)
        
        combined = 0.4 * noise_ratio + 0.3 * noise_score + 0.3 * freq_ratio
        
        return np.clip(combined, 0, 1)


class DistributionClassifier:
    """
    Classifies series based on distributional properties.
    
    Multiple sub-classifiers for different aspects.
    """
    
    def classify_normality(self, x: np.ndarray) -> float:
        """Probability of being normally distributed."""
        try:
            _, p_shapiro = stats.shapiro(x)
            _, p_dagostino = stats.normaltest(x)
            
            return (p_shapiro + p_dagostino) / 2
        except:
            return 0.5
    
    def classify_tail_heaviness(self, x: np.ndarray) -> float:
        """Probability of having heavy tails."""
        kurt = stats.kurtosis(x)
        
        tail_ratio = self._tail_ratio(x, 0.05)
        
        kurt_score = 1 / (1 + np.exp(-kurt/2))
        tail_score = 1 / (1 + np.exp(-(tail_ratio - 3)/2))
        
        return 0.6 * kurt_score + 0.4 * tail_score
    
    def _tail_ratio(self, x: np.ndarray, alpha: float) -> float:
        """Ratio of tail values to central values."""
        q_low = np.percentile(x, alpha * 100)
        q_high = np.percentile(x, (1 - alpha) * 100)
        q_median = np.median(x)
        
        if q_median != q_low:
            return (q_high - q_median) / (q_median - q_low)
        return 1.0
    
    def classify_symmetry(self, x: np.ndarray) -> float:
        """Probability of being symmetric (0=asymmetric, 1=symmetric)."""
        skew = abs(stats.skew(x))
        
        medcouple = self._medcouple(x)
        
        skew_score = np.exp(-skew**2)
        mc_score = 1 - abs(medcouple)
        
        return 0.6 * skew_score + 0.4 * mc_score
    
    def _medcouple(self, x: np.ndarray) -> float:
        """Robust measure of skewness."""
        median = np.median(x)
        x_plus = x[x >= median]
        x_minus = x[x <= median]
        
        if len(x_plus) == 0 or len(x_minus) == 0:
            return 0
        
        h_values = []
        for xi in x_minus:
            for xj in x_plus:
                if xj != xi:
                    h = (xj + xi - 2*median) / (xj - xi)
                    h_values.append(h)
        
        return np.median(h_values) if h_values else 0


class TrendClassifier:
    """
    Classifies series based on trend characteristics.
    """
    
    def classify_trend_strength(self, x: np.ndarray) -> float:
        """Probability of having strong trend."""
        t = np.arange(len(x))
        
        slope, _, r_value, _, _ = stats.linregress(t, x)
        
        detrended = x - (slope * t + x[0])
        trend_var = np.var(slope * t)
        total_var = np.var(x)
        
        r2_score = r_value**2
        var_ratio = trend_var / (total_var + 1e-8)
        
        return 0.6 * r2_score + 0.4 * var_ratio
    
    def classify_nonlinearity(self, x: np.ndarray) -> float:
        """Probability of having nonlinear patterns."""
        t = np.arange(len(x))
        
        poly2 = np.polyfit(t, x, 2)
        poly3 = np.polyfit(t, x, 3)
        
        linear_fit = np.polyval([poly2[-2], poly2[-1]], t)
        quad_fit = np.polyval(poly2, t)
        cubic_fit = np.polyval(poly3, t)
        
        r2_linear = 1 - np.var(x - linear_fit) / np.var(x)
        r2_quad = 1 - np.var(x - quad_fit) / np.var(x)
        r2_cubic = 1 - np.var(x - cubic_fit) / np.var(x)
        
        nonlin_score = max(0, r2_cubic - r2_linear)
        
        return np.clip(nonlin_score * 2, 0, 1)


class MultiDimensionalClassifier:
    """
    Main classifier that combines all dimensions.
    """
    
    def __init__(self):
        """Initialize all classification dimensions."""
        self.stationarity = StationarityClassifier()
        self.noise = NoiseClassifier()
        self.distribution = DistributionClassifier()
        self.trend = TrendClassifier()
        
        self.dimensions = [
            ClassificationDimension(
                'stationary', 
                self.stationarity.classify,
                'Probability of being stationary'
            ),
            ClassificationDimension(
                'noisy',
                self.noise.classify,
                'Noise level (0=clean, 1=very noisy)'
            ),
            ClassificationDimension(
                'normal',
                self.distribution.classify_normality,
                'Probability of normal distribution'
            ),
            ClassificationDimension(
                'heavy_tailed',
                self.distribution.classify_tail_heaviness,
                'Probability of heavy tails'
            ),
            ClassificationDimension(
                'symmetric',
                self.distribution.classify_symmetry,
                'Probability of symmetry'
            ),
            ClassificationDimension(
                'trending',
                self.trend.classify_trend_strength,
                'Strength of trend'
            ),
            ClassificationDimension(
                'nonlinear',
                self.trend.classify_nonlinearity,
                'Degree of nonlinearity'
            )
        ]
    
    def classify_series(self, x: np.ndarray) -> Dict[str, float]:
        """
        Classify series along all dimensions.
        
        Parameters
        ----------
        x : np.ndarray
            Time series values
            
        Returns
        -------
        Dict[str, float]
            Probability scores for each dimension
        """
        results = {}
        
        for dim in self.dimensions:
            try:
                results[dim.name] = dim.classifier(x)
            except Exception as e:
                results[dim.name] = 0.5
        
        return results
    
    def classify_before_after(self, before: np.ndarray, after: np.ndarray) -> Dict[str, Dict[str, float]]:
        """
        Classify before and after segments separately.
        
        Parameters
        ----------
        before : np.ndarray
            Values before boundary
        after : np.ndarray
            Values after boundary
            
        Returns
        -------
        Dict containing classifications and changes
        """
        class_before = self.classify_series(before)
        class_after = self.classify_series(after)
        
        changes = {}
        for key in class_before:
            changes[f'{key}_change'] = class_after[key] - class_before[key]
            changes[f'{key}_abs_change'] = abs(class_after[key] - class_before[key])
        
        return {
            'before': class_before,
            'after': class_after,
            'changes': changes
        }
    
    def get_position_vector(self, x: np.ndarray) -> np.ndarray:
        """
        Get position vector in multi-dimensional space.
        
        Parameters
        ----------
        x : np.ndarray
            Time series values
            
        Returns
        -------
        np.ndarray
            Position vector
        """
        classifications = self.classify_series(x)
        return np.array([classifications[dim.name] for dim in self.dimensions])
    
    def get_grid_position(self, before: np.ndarray, after: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Get grid position considering before/after changes.
        
        Returns position vectors and change vector.
        """
        pos_before = self.get_position_vector(before)
        pos_after = self.get_position_vector(after)
        change_vector = pos_after - pos_before
        
        combined_position = np.concatenate([
            pos_before,
            pos_after,
            change_vector,
            np.abs(change_vector)
        ])
        
        return {
            'before': pos_before,
            'after': pos_after,
            'change': change_vector,
            'combined': combined_position,
            'dimension_names': [dim.name for dim in self.dimensions]
        }