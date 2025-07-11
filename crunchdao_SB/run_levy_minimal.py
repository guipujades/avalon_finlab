#!/usr/bin/env python3
"""
Script MÍNIMO para extrair features de Lévy - apenas numpy e pandas.
Sem visualizações, sem modelos, apenas extração de features.

Author: CrunchDAO SB Team  
Date: 2025-06-26
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
from datetime import datetime

# Implementação mínima do analisador de Lévy
class LevySectionsAnalyzerMinimal:
    def __init__(self, tau=0.01, q=5):
        self.tau = tau
        self.q = q
        self.results = None
        
    def compute_local_volatilities(self, returns):
        n = len(returns)
        m2 = np.full(n, np.nan)
        
        for i in range(self.q, n - self.q):
            window = returns[(i - self.q):(i + self.q + 1)]
            m2[i] = np.var(window, ddof=1)
            
        m2[:self.q] = m2[self.q]
        m2[-self.q:] = m2[-(self.q + 1)]
        
        return m2
    
    def compute_levy_sections(self, returns):
        m2 = self.compute_local_volatilities(returns)
        m2_adj = m2[self.q:-self.q]
        returns_adj = returns[self.q:-self.q]
        n = len(returns_adj)
        
        sections = []
        durations = []
        
        i = 0
        while i < n:
            acc_var = 0
            j = i
            
            while j < n and acc_var + m2_adj[j] <= self.tau:
                acc_var += m2_adj[j]
                j += 1
                
            if j > i:
                S_tau = np.sum(returns_adj[i:j])
                sections.append(S_tau)
                durations.append(j - i)
                i = j
            else:
                i += 1
                
        self.S_tau = np.array(sections)
        self.durations = np.array(durations)
        
        return self
    
    def extract_features(self):
        if self.S_tau is None or len(self.S_tau) == 0:
            return {}
            
        S_tau_norm = self.S_tau / np.sqrt(self.tau)
        
        features = {
            'levy_duration_mean': np.mean(self.durations),
            'levy_duration_std': np.std(self.durations),
            'levy_duration_cv': np.std(self.durations) / np.mean(self.durations) if np.mean(self.durations) > 0 else np.nan,
            'levy_duration_min': np.min(self.durations),
            'levy_duration_max': np.max(self.durations),
            'levy_n_sections': len(self.S_tau),
            'levy_sum_mean': np.mean(self.S_tau),
            'levy_sum_std': np.std(self.S_tau),
            'levy_norm_std': np.std(S_tau_norm)
        }
        
        return features


def main():
    print("\n" + "="*60)
    print("EXTRAÇÃO MÍNIMA DE FEATURES DE LÉVY")
    print("="*60)
    
    # 1. Carregar dados
    print("\n📊 Carregando dados...")
    try:
        X_train = pd.read_parquet('database/X_train.parquet')
        y_train = pd.read_parquet('database/y_train.parquet')
        print(f"✅ Dados carregados: {X_train.shape}")
    except Exception as e:
        print(f"❌ Erro: {e}")
        return
    
    # 2. Processar amostra
    print("\n🔍 Processando amostra de 100 séries...")
    
    sample_size = 100
    sample_indices = X_train.index[:sample_size]
    
    all_features = []
    
    for i, series_id in enumerate(sample_indices):
        if i % 20 == 0:
            print(f"   Processadas: {i}/{sample_size}")
        
        series_data = X_train.loc[series_id].values
        series_clean = series_data[~np.isnan(series_data)]
        
        if len(series_clean) > 20:
            returns = np.diff(series_clean)
            
            if len(returns) > 10:
                try:
                    analyzer = LevySectionsAnalyzerMinimal(tau=0.005, q=5)
                    analyzer.compute_levy_sections(returns)
                    features = analyzer.extract_features()
                    features['series_id'] = series_id
                    all_features.append(features)
                except:
                    pass
    
    # 3. Criar DataFrame
    if all_features:
        features_df = pd.DataFrame(all_features)
        features_df.set_index('series_id', inplace=True)
        
        print(f"\n✅ Features extraídas: {features_df.shape}")
        
        # 4. Mostrar estatísticas
        print("\n📈 Estatísticas das features:")
        print(features_df.describe().round(4))
        
        # 5. Salvar
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'levy_features_minimal_{timestamp}.csv'
        features_df.to_csv(output_file)
        print(f"\n💾 Features salvas em: {output_file}")
        
        # 6. Comparar com labels
        common_idx = features_df.index.intersection(y_train.index)
        if len(common_idx) > 0:
            print("\n🎯 Comparação por classe:")
            labels = y_train.loc[common_idx, 'target']
            
            for feature in ['levy_duration_mean', 'levy_n_sections']:
                if feature in features_df.columns:
                    mean_0 = features_df.loc[labels == 0, feature].mean()
                    mean_1 = features_df.loc[labels == 1, feature].mean()
                    print(f"\n   {feature}:")
                    print(f"      Classe 0: {mean_0:.4f}")
                    print(f"      Classe 1: {mean_1:.4f}")
        
        print("\n✨ Concluído!")
    else:
        print("\n❌ Nenhuma feature extraída.")


if __name__ == "__main__":
    main()