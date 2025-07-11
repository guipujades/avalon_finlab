"""
TSFresh-based feature extraction for structural break detection.

TSFresh extracts 700+ time series features and automatically
selects statistically relevant ones using hypothesis tests.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

try:
    from tsfresh import extract_features, select_features
    from tsfresh.utilities.dataframe_functions import impute
    from tsfresh.feature_extraction import ComprehensiveFCParameters, EfficientFCParameters
    TSFRESH_AVAILABLE = True
except ImportError:
    TSFRESH_AVAILABLE = False
    print("TSFresh not available. Install with: pip install tsfresh")


class TSFreshExtractor:
    """
    Extract and select relevant features using TSFresh.
    """
    
    def __init__(self, feature_set: str = 'efficient'):
        """
        Initialize TSFresh extractor.
        
        Parameters
        ----------
        feature_set : str
            'comprehensive' for all 700+ features
            'efficient' for faster subset
            'minimal' for basic features only
        """
        if not TSFRESH_AVAILABLE:
            raise ImportError("TSFresh not installed")
        
        self.feature_set = feature_set
        self.settings = self._get_feature_settings()
        self.selected_features = None
        
    def _get_feature_settings(self):
        """Get feature extraction settings based on chosen set."""
        if self.feature_set == 'comprehensive':
            return ComprehensiveFCParameters()
        elif self.feature_set == 'efficient':
            return EfficientFCParameters()
        else:
            return {
                "mean": None,
                "median": None,
                "standard_deviation": None,
                "variance": None,
                "maximum": None,
                "minimum": None,
                "sum_values": None,
                "length": None,
                "quantile": [{"q": 0.25}, {"q": 0.75}],
                "autocorrelation": [{"lag": 1}, {"lag": 2}, {"lag": 3}],
                "skewness": None,
                "kurtosis": None,
                "fft_coefficient": [{"coeff": 0, "attr": "real"}, {"coeff": 1, "attr": "real"}],
                "linear_trend": [{"attr": "slope"}, {"attr": "intercept"}],
                "number_peaks": [{"n": 3}],
                "binned_entropy": [{"max_bins": 5}]
            }
    
    def prepare_data_for_tsfresh(self, X_train: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare data in TSFresh format.
        
        TSFresh expects format:
        - id: identifier for time series
        - time: time index
        - value: measurement
        
        Parameters
        ----------
        X_train : pd.DataFrame
            Input data with columns ['id', 'time', 'value', 'period']
            
        Returns
        -------
        pd.DataFrame
            Data in TSFresh format
        """
        df_list = []
        
        unique_ids = X_train['id'].unique()
        
        for series_id in unique_ids:
            series_data = X_train[X_train['id'] == series_id]
            
            before = series_data[series_data['period'] == 0].copy()
            after = series_data[series_data['period'] == 1].copy()
            
            before['id'] = f"{series_id}_before"
            after['id'] = f"{series_id}_after"
            
            before['time'] = range(len(before))
            after['time'] = range(len(after))
            
            df_list.extend([before[['id', 'time', 'value']], 
                          after[['id', 'time', 'value']]])
        
        return pd.concat(df_list, ignore_index=True)
    
    def extract_features(self, X_data: pd.DataFrame, n_jobs: int = 4) -> pd.DataFrame:
        """
        Extract features using TSFresh.
        
        Parameters
        ----------
        X_data : pd.DataFrame
            Data in TSFresh format
        n_jobs : int
            Number of parallel jobs
            
        Returns
        -------
        pd.DataFrame
            Extracted features
        """
        print(f"Extracting {self.feature_set} features with TSFresh...")
        
        features = extract_features(
            X_data,
            column_id='id',
            column_sort='time',
            default_fc_parameters=self.settings,
            impute_function=impute,
            n_jobs=n_jobs,
            show_warnings=False,
            disable_progressbar=False
        )
        
        print(f"Extracted {features.shape[1]} features for {features.shape[0]} series segments")
        
        return features
    
    def combine_before_after_features(self, features: pd.DataFrame) -> pd.DataFrame:
        """
        Combine before/after features and calculate differences.
        
        Parameters
        ----------
        features : pd.DataFrame
            TSFresh features with IDs like "series_before" and "series_after"
            
        Returns
        -------
        pd.DataFrame
            Combined features with differences and ratios
        """
        combined_list = []
        
        unique_base_ids = set([idx.split('_')[0] for idx in features.index])
        
        for base_id in unique_base_ids:
            before_id = f"{base_id}_before"
            after_id = f"{base_id}_after"
            
            if before_id in features.index and after_id in features.index:
                before_features = features.loc[before_id]
                after_features = features.loc[after_id]
                
                row_data = {'id': base_id}
                
                for col in features.columns:
                    before_val = before_features[col]
                    after_val = after_features[col]
                    
                    # Tratar NaN
                    if np.isnan(before_val) or np.isnan(after_val):
                        before_val = 0.0
                        after_val = 0.0
                    
                    row_data[f"{col}_before"] = before_val
                    row_data[f"{col}_after"] = after_val
                    
                    diff = after_val - before_val
                    row_data[f"{col}_diff"] = diff
                    
                    if before_val != 0 and not np.isnan(before_val) and not np.isinf(before_val):
                        ratio = after_val / before_val
                        # Limitar ratio para evitar valores extremos
                        row_data[f"{col}_ratio"] = np.clip(ratio, -10, 10)
                    else:
                        row_data[f"{col}_ratio"] = 1.0
                    
                    row_data[f"{col}_abs_diff"] = abs(diff)
                
                combined_list.append(row_data)
        
        combined_df = pd.DataFrame(combined_list)
        # Converter o índice para string para garantir compatibilidade
        combined_df['id'] = combined_df['id'].astype(str)
        combined_df.set_index('id', inplace=True)
        
        return combined_df
    
    def select_relevant_features(self, features: pd.DataFrame, 
                               y: pd.Series, 
                               fdr_level: float = 0.05) -> pd.DataFrame:
        """
        Select statistically relevant features.
        
        Uses Benjamini-Hochberg procedure to control false discovery rate.
        
        Parameters
        ----------
        features : pd.DataFrame
            All extracted features
        y : pd.Series
            Target labels
        fdr_level : float
            False discovery rate threshold
            
        Returns
        -------
        pd.DataFrame
            Only relevant features
        """
        print(f"\nSelecting relevant features (FDR level: {fdr_level})...")
        
        y_aligned = y.loc[features.index]
        
        relevant_features = select_features(
            features, 
            y_aligned,
            fdr_level=fdr_level
        )
        
        self.selected_features = list(relevant_features.columns)
        
        print(f"Selected {len(self.selected_features)} relevant features from {features.shape[1]}")
        
        return relevant_features
    
    def extract_and_select(self, X_train: pd.DataFrame, 
                          y_train: pd.DataFrame,
                          n_jobs: int = 4,
                          fdr_level: float = 0.05) -> pd.DataFrame:
        """
        Full pipeline: extract features and select relevant ones.
        
        Parameters
        ----------
        X_train : pd.DataFrame
            Training data with columns ['id', 'time', 'value', 'period']
        y_train : pd.DataFrame
            Labels with columns ['id', 'label']
        n_jobs : int
            Number of parallel jobs
        fdr_level : float
            False discovery rate for feature selection
            
        Returns
        -------
        pd.DataFrame
            Selected relevant features
        """
        tsfresh_data = self.prepare_data_for_tsfresh(X_train)
        
        raw_features = self.extract_features(tsfresh_data, n_jobs=n_jobs)
        
        combined_features = self.combine_before_after_features(raw_features)
        
        y_aligned = y_train.set_index('id')['label']
        # Garantir que os índices são strings
        y_aligned.index = y_aligned.index.astype(str)
        # Usar apenas os índices que existem em ambos
        common_indices = combined_features.index.intersection(y_aligned.index)
        combined_features = combined_features.loc[common_indices]
        y_aligned = y_aligned.loc[common_indices]
        
        # Limpar NaN e infinitos antes de selecionar features
        combined_features = combined_features.replace([np.inf, -np.inf], np.nan)
        combined_features = combined_features.fillna(combined_features.median())
        
        relevant_features = self.select_relevant_features(
            combined_features, 
            y_aligned, 
            fdr_level=fdr_level
        )
        
        return relevant_features
    
    def get_feature_importance(self, features: pd.DataFrame, 
                             y: pd.Series) -> pd.DataFrame:
        """
        Calculate feature importance using statistical tests.
        
        Parameters
        ----------
        features : pd.DataFrame
            Feature matrix
        y : pd.Series
            Target labels
            
        Returns
        -------
        pd.DataFrame
            Feature importance scores
        """
        from scipy import stats
        
        importance_list = []
        
        for col in features.columns:
            values = features[col].values
            mask = ~np.isnan(values) & ~np.isinf(values)
            
            if mask.sum() < 10:
                continue
            
            values_clean = values[mask]
            labels_clean = y.values[mask]
            
            group0 = values_clean[labels_clean == 0]
            group1 = values_clean[labels_clean == 1]
            
            if len(group0) < 5 or len(group1) < 5:
                continue
            
            t_stat, p_value = stats.ttest_ind(group0, group1)
            
            ks_stat, ks_p = stats.ks_2samp(group0, group1)
            
            mean_diff = np.mean(group1) - np.mean(group0)
            std_pooled = np.sqrt((np.var(group0) + np.var(group1)) / 2)
            cohen_d = mean_diff / std_pooled if std_pooled > 0 else 0
            
            from sklearn.feature_selection import mutual_info_classif
            mi_score = mutual_info_classif(
                values_clean.reshape(-1, 1), 
                labels_clean, 
                random_state=42
            )[0]
            
            importance_list.append({
                'feature': col,
                't_statistic': t_stat,
                'p_value': p_value,
                'ks_statistic': ks_stat,
                'cohen_d': cohen_d,
                'mutual_info': mi_score,
                'abs_cohen_d': abs(cohen_d),
                'feature_type': col.split('__')[-1] if '__' in col else 'unknown'
            })
        
        importance_df = pd.DataFrame(importance_list)
        importance_df = importance_df.sort_values('abs_cohen_d', ascending=False)
        
        return importance_df


def create_tsfresh_report(features: pd.DataFrame, 
                         importance: pd.DataFrame,
                         output_file: str = 'tsfresh_report.txt'):
    """
    Create a report of TSFresh analysis.
    
    Parameters
    ----------
    features : pd.DataFrame
        Extracted features
    importance : pd.DataFrame
        Feature importance scores
    output_file : str
        Output file path
    """
    report = f"""
TSFresh Feature Extraction Report
=================================

Total Features Extracted: {features.shape[1]}
Total Series Analyzed: {features.shape[0]}

Top 20 Most Important Features
------------------------------
"""
    
    for idx, row in importance.head(20).iterrows():
        report += f"\n{row['feature']}"
        report += f"\n  - Cohen's d: {row['cohen_d']:.3f}"
        report += f"\n  - P-value: {row['p_value']:.3e}"
        report += f"\n  - Mutual Info: {row['mutual_info']:.3f}"
        report += f"\n  - Type: {row['feature_type']}\n"
    
    feature_types = importance['feature_type'].value_counts()
    report += "\nFeature Types Distribution\n"
    report += "--------------------------\n"
    for ftype, count in feature_types.items():
        report += f"{ftype}: {count}\n"
    
    with open(output_file, 'w') as f:
        f.write(report)
    
    print(f"Report saved to {output_file}")