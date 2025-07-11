"""
Implementação das Seções de Lévy para detecção de quebras estruturais
e extração de features para séries temporais financeiras.

Baseado no artigo de Figueiredo et al. (2022) e na conversa sobre
aplicações das seções de Lévy para análise de risco e quebras estruturais.

Author: CrunchDAO SB Team
Date: 2025-06-26
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple, Optional
import warnings
from dataclasses import dataclass
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns


@dataclass
class LevySectionResult:
    """Resultado do cálculo das seções de Lévy"""
    S_tau: np.ndarray  # Somas das seções
    durations: np.ndarray  # Durações (delta_tau) de cada seção
    start_indices: np.ndarray  # Índices de início de cada seção
    end_indices: np.ndarray  # Índices de fim de cada seção
    tau: float  # Parâmetro tau usado
    q: int  # Parâmetro q usado
    

class LevySectionsAnalyzer:
    """
    Classe para análise de séries temporais usando seções de Lévy.
    
    Esta classe implementa o método das seções de Lévy para:
    1. Transformar séries temporais em "tempo de volatilidade"
    2. Detectar quebras estruturais no regime de volatilidade
    3. Extrair features robustas para machine learning
    """
    
    def __init__(self, tau: float = 0.01, q: int = 5):
        """
        Inicializa o analisador de seções de Lévy.
        
        Args:
            tau: Limiar de variância acumulada que define o fim de uma seção
            q: Semi-largura da janela móvel para estimar volatilidade local
        """
        self.tau = tau
        self.q = q
        self.results = None
        
    def compute_local_volatilities(self, returns: np.ndarray) -> np.ndarray:
        """
        Estima volatilidades locais usando janelas móveis.
        
        Args:
            returns: Array de retornos
            
        Returns:
            Array de variâncias locais estimadas
        """
        n = len(returns)
        m2 = np.full(n, np.nan)
        
        # Calcular variância local para cada janela
        for i in range(self.q, n - self.q):
            window = returns[(i - self.q):(i + self.q + 1)]
            m2[i] = np.var(window, ddof=1)
            
        # Preencher bordas com valores mais próximos
        m2[:self.q] = m2[self.q]
        m2[-self.q:] = m2[-(self.q + 1)]
        
        return m2
    
    def compute_levy_sections(self, returns: np.ndarray) -> LevySectionResult:
        """
        Calcula as seções de Lévy para uma série de retornos.
        
        Args:
            returns: Array de retornos (log-retornos preferencialmente)
            
        Returns:
            LevySectionResult com as seções calculadas
        """
        # Estimar volatilidades locais
        m2 = self.compute_local_volatilities(returns)
        
        # Remover bordas afetadas pela janela móvel
        m2_adj = m2[self.q:-self.q]
        returns_adj = returns[self.q:-self.q]
        n = len(returns_adj)
        
        # Construir seções
        sections = []
        durations = []
        start_indices = []
        end_indices = []
        
        i = 0
        while i < n:
            acc_var = 0
            j = i
            
            # Acumular variância até atingir tau
            while j < n and acc_var + m2_adj[j] <= self.tau:
                acc_var += m2_adj[j]
                j += 1
                
            if j > i:
                # Calcular soma da seção
                S_tau = np.sum(returns_adj[i:j])
                sections.append(S_tau)
                
                # Registrar duração e índices
                durations.append(j - i)
                start_indices.append(i + self.q)  # Ajustar para índice original
                end_indices.append(j - 1 + self.q)
                
                i = j
            else:
                i += 1
                
        self.results = LevySectionResult(
            S_tau=np.array(sections),
            durations=np.array(durations),
            start_indices=np.array(start_indices),
            end_indices=np.array(end_indices),
            tau=self.tau,
            q=self.q
        )
        
        return self.results
    
    def detect_structural_breaks(self, min_sections: int = 20) -> Dict:
        """
        Detecta quebras estruturais na série de durações.
        
        Args:
            min_sections: Número mínimo de seções para análise confiável
            
        Returns:
            Dicionário com informações sobre as quebras detectadas
        """
        if self.results is None:
            raise ValueError("Execute compute_levy_sections primeiro")
            
        durations = self.results.durations
        
        if len(durations) < min_sections:
            warnings.warn(f"Apenas {len(durations)} seções. Recomenda-se pelo menos {min_sections}.")
            
        # Método 1: CUSUM (Cumulative Sum)
        mean_dur = np.mean(durations)
        cusum = np.cumsum(durations - mean_dur)
        
        # Encontrar pontos de máximo desvio no CUSUM
        cusum_abs = np.abs(cusum)
        potential_breaks = []
        
        # Detectar mudanças significativas usando janela deslizante
        window = max(5, len(durations) // 10)
        for i in range(window, len(durations) - window):
            left_mean = np.mean(durations[i-window:i])
            right_mean = np.mean(durations[i:i+window])
            
            # Teste t para diferença de médias
            t_stat, p_value = stats.ttest_ind(
                durations[i-window:i],
                durations[i:i+window],
                equal_var=False
            )
            
            if p_value < 0.01:  # Significância de 1%
                change_ratio = right_mean / left_mean
                potential_breaks.append({
                    'index': i,
                    'p_value': p_value,
                    'mean_before': left_mean,
                    'mean_after': right_mean,
                    'change_ratio': change_ratio
                })
        
        # Filtrar quebras muito próximas
        filtered_breaks = []
        if potential_breaks:
            filtered_breaks.append(potential_breaks[0])
            for brk in potential_breaks[1:]:
                if brk['index'] - filtered_breaks[-1]['index'] > window:
                    filtered_breaks.append(brk)
                    
        return {
            'breaks': filtered_breaks,
            'cusum': cusum,
            'mean_duration': mean_dur,
            'std_duration': np.std(durations)
        }
    
    def extract_features(self) -> Dict[str, float]:
        """
        Extrai features das seções de Lévy para uso em machine learning.
        
        Returns:
            Dicionário com features calculadas
        """
        if self.results is None:
            raise ValueError("Execute compute_levy_sections primeiro")
            
        S_tau = self.results.S_tau
        durations = self.results.durations
        
        # Normalizar somas pelo sqrt(tau) conforme teoria
        S_tau_norm = S_tau / np.sqrt(self.tau)
        
        features = {
            # Features das durações (delta_tau)
            'levy_duration_mean': np.mean(durations),
            'levy_duration_std': np.std(durations),
            'levy_duration_cv': np.std(durations) / np.mean(durations),  # Coef. variação
            'levy_duration_kurtosis': stats.kurtosis(durations),
            'levy_duration_skew': stats.skew(durations),
            'levy_duration_min': np.min(durations),
            'levy_duration_max': np.max(durations),
            'levy_duration_q25': np.percentile(durations, 25),
            'levy_duration_q75': np.percentile(durations, 75),
            
            # Features das somas seccionais (S_tau)
            'levy_sum_mean': np.mean(S_tau),
            'levy_sum_std': np.std(S_tau),
            'levy_sum_kurtosis': stats.kurtosis(S_tau),
            'levy_sum_skew': stats.skew(S_tau),
            
            # Features da "Gaussianização"
            'levy_norm_kurtosis': stats.kurtosis(S_tau_norm),  # Deve tender a 0
            'levy_norm_var_ratio': np.var(S_tau_norm),  # Deve tender a 1
            
            # Features de estabilidade
            'levy_n_sections': len(S_tau),
            'levy_avg_trading_time': self.tau / np.mean(durations) if len(durations) > 0 else np.nan,
            
            # Teste de normalidade das seções normalizadas
            'levy_shapiro_pvalue': stats.shapiro(S_tau_norm)[1] if len(S_tau_norm) >= 3 else np.nan
        }
        
        # Adicionar autocorrelação das durações se houver dados suficientes
        if len(durations) > 10:
            features['levy_duration_autocorr'] = pd.Series(durations).autocorr(lag=1)
        else:
            features['levy_duration_autocorr'] = np.nan
            
        return features
    
    def plot_analysis(self, breaks_info: Optional[Dict] = None, 
                     title_prefix: str = ""):
        """
        Cria visualizações da análise de seções de Lévy.
        
        Args:
            breaks_info: Resultado de detect_structural_breaks()
            title_prefix: Prefixo para os títulos dos gráficos
        """
        if self.results is None:
            raise ValueError("Execute compute_levy_sections primeiro")
            
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # 1. Durações ao longo do tempo
        ax = axes[0, 0]
        section_indices = np.arange(len(self.results.durations))
        ax.plot(section_indices, self.results.durations, 'b-', linewidth=1)
        ax.scatter(section_indices, self.results.durations, c='darkblue', s=20)
        
        # Adicionar quebras se disponíveis
        if breaks_info and breaks_info['breaks']:
            for brk in breaks_info['breaks']:
                ax.axvline(x=brk['index'], color='red', linestyle='--', alpha=0.7)
                
        ax.set_xlabel('Índice da Seção')
        ax.set_ylabel('Duração (períodos)')
        ax.set_title(f'{title_prefix} - Durações das Seções de Lévy')
        ax.grid(True, alpha=0.3)
        
        # 2. CUSUM das durações
        if breaks_info:
            ax = axes[0, 1]
            ax.plot(section_indices[:len(breaks_info['cusum'])], 
                   breaks_info['cusum'], 'g-', linewidth=2)
            ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
            ax.set_xlabel('Índice da Seção')
            ax.set_ylabel('CUSUM')
            ax.set_title('CUSUM das Durações')
            ax.grid(True, alpha=0.3)
        
        # 3. Histograma das somas normalizadas
        ax = axes[1, 0]
        S_tau_norm = self.results.S_tau / np.sqrt(self.tau)
        ax.hist(S_tau_norm, bins=30, density=True, alpha=0.7, color='blue', edgecolor='black')
        
        # Sobrepor distribuição normal teórica
        x = np.linspace(S_tau_norm.min(), S_tau_norm.max(), 100)
        ax.plot(x, stats.norm.pdf(x, 0, 1), 'r-', linewidth=2, label='N(0,1)')
        ax.set_xlabel('Soma Normalizada')
        ax.set_ylabel('Densidade')
        ax.set_title('Distribuição das Somas Seccionais Normalizadas')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 4. QQ-plot
        ax = axes[1, 1]
        stats.probplot(S_tau_norm, dist="norm", plot=ax)
        ax.set_title('Q-Q Plot (Normalidade)')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    

def analyze_structural_breaks_for_series(
    returns: np.ndarray,
    dates: Optional[pd.DatetimeIndex] = None,
    tau_values: List[float] = [0.001, 0.005, 0.01, 0.02],
    q: int = 5
) -> pd.DataFrame:
    """
    Analisa quebras estruturais para diferentes valores de tau.
    
    Args:
        returns: Array de retornos
        dates: Índice de datas (opcional)
        tau_values: Lista de valores de tau para testar
        q: Parâmetro q para volatilidade local
        
    Returns:
        DataFrame com resumo das quebras detectadas
    """
    results = []
    
    for tau in tau_values:
        analyzer = LevySectionsAnalyzer(tau=tau, q=q)
        levy_result = analyzer.compute_levy_sections(returns)
        breaks_info = analyzer.detect_structural_breaks()
        
        for brk in breaks_info['breaks']:
            # Mapear para data se disponível
            if dates is not None and brk['index'] < len(levy_result.start_indices):
                section_start_idx = levy_result.start_indices[brk['index']]
                if section_start_idx < len(dates):
                    break_date = dates[section_start_idx]
                else:
                    break_date = None
            else:
                break_date = None
                
            results.append({
                'tau': tau,
                'break_section_index': brk['index'],
                'break_date': break_date,
                'mean_duration_before': brk['mean_before'],
                'mean_duration_after': brk['mean_after'],
                'change_ratio': brk['change_ratio'],
                'p_value': brk['p_value']
            })
            
    return pd.DataFrame(results)