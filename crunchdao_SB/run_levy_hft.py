#!/usr/bin/env python3
"""
Extração de features de Lévy otimizada para dados de alta frequência.
Adaptado para capturar microestrutura e quebras rápidas em HFT.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import time

print("\n" + "="*60)
print("LEVY SECTIONS - HIGH FREQUENCY TRADING")
print("="*60)

def calculate_levy_features_hft(series_values, tau=0.0001, q=10, min_sections=5):
    """
    Calcula features de Lévy adaptadas para dados de alta frequência.
    
    Parâmetros HFT:
    - tau: muito menor (0.0001-0.001) para capturar micro-quebras
    - q: maior (10-20) para estabilizar volatilidade em HFT
    - min_sections: mínimo de seções para considerar válido
    """
    try:
        # Remover NaN e verificar tamanho mínimo
        series_clean = series_values[~np.isnan(series_values)]
        if len(series_clean) < 2 * q + 50:  # Precisamos de mais pontos em HFT
            return None
        
        # Em HFT, usar log-retornos é mais estável
        log_prices = np.log(series_clean + 1e-10)  # Evitar log(0)
        returns = np.diff(log_prices)
        
        if len(returns) < 2 * q + 20:
            return None
        
        # 1. Estimar volatilidade instantânea (mais apropriado para HFT)
        # Usar realized volatility com janela menor
        volatilities = []
        for i in range(q, len(returns) - q):
            # Janela centralizada
            window = returns[i-q:i+q+1]
            # Realized volatility (mais robusto para HFT)
            vol = np.sqrt(np.sum(window**2) / len(window))
            volatilities.append(vol if vol > 1e-10 else 1e-10)
        
        volatilities = np.array(volatilities)
        
        # 2. Construir seções de Lévy com critério adaptado para HFT
        cumsum = 0
        section_starts = [0]
        section_durations = []
        section_returns = []
        
        for i in range(len(volatilities)):
            # Em HFT, acumular variância realizada
            cumsum += volatilities[i]**2
            
            if cumsum >= tau:
                duration = i - section_starts[-1]
                if duration > 0:  # Evitar seções vazias
                    section_durations.append(duration)
                    # Retorno acumulado da seção
                    section_return = np.sum(returns[section_starts[-1]:i])
                    section_returns.append(section_return)
                    section_starts.append(i)
                    cumsum = 0
        
        # Verificar se temos seções suficientes
        if len(section_durations) < min_sections:
            return None
        
        durations = np.array(section_durations)
        sect_returns = np.array(section_returns)
        
        # 3. Features específicas para HFT
        features = {
            # Features de duração (tempo de volatilidade)
            'levy_duration_mean': np.mean(durations),
            'levy_duration_std': np.std(durations),
            'levy_duration_cv': np.std(durations) / np.mean(durations) if np.mean(durations) > 0 else 0,
            'levy_duration_min': np.min(durations),
            'levy_duration_max': np.max(durations),
            'levy_duration_skew': _safe_skew(durations),
            'levy_duration_kurt': _safe_kurtosis(durations),
            
            # Features de microestrutura
            'levy_microstructure_ratio': np.min(durations) / np.max(durations),
            'levy_duration_acceleration': np.mean(np.diff(durations)) if len(durations) > 1 else 0,
            
            # Features de retorno por seção
            'levy_section_return_mean': np.mean(sect_returns),
            'levy_section_return_std': np.std(sect_returns),
            'levy_section_sharpe': np.mean(sect_returns) / np.std(sect_returns) if np.std(sect_returns) > 0 else 0,
            
            # Contagens
            'levy_n_sections': len(durations),
            'levy_sections_per_point': len(durations) / len(series_clean),
            
            # Detecção de regime
            'levy_regime_changes': _count_regime_changes(durations),
            'levy_volatility_clustering': _measure_clustering(volatilities[:sum(durations)]),
        }
        
        return features
        
    except Exception as e:
        print(f"Erro no cálculo: {e}")
        return None

def _safe_skew(x):
    """Calcula skewness de forma segura."""
    if len(x) < 3:
        return 0
    mean = np.mean(x)
    std = np.std(x)
    if std == 0:
        return 0
    return np.mean(((x - mean) / std) ** 3)

def _safe_kurtosis(x):
    """Calcula kurtosis de forma segura."""
    if len(x) < 4:
        return 0
    mean = np.mean(x)
    std = np.std(x)
    if std == 0:
        return 0
    return np.mean(((x - mean) / std) ** 4) - 3

def _count_regime_changes(durations):
    """Conta mudanças significativas de regime."""
    if len(durations) < 2:
        return 0
    # Mudança de regime: duração muda mais de 50%
    changes = 0
    for i in range(1, len(durations)):
        ratio = durations[i] / durations[i-1]
        if ratio > 1.5 or ratio < 0.67:
            changes += 1
    return changes

def _measure_clustering(volatilities):
    """Mede clustering de volatilidade (importante em HFT)."""
    if len(volatilities) < 2:
        return 0
    # Autocorrelação de volatilidade ao quadrado
    vol_sq = volatilities ** 2
    if np.std(vol_sq) == 0:
        return 0
    autocorr = np.corrcoef(vol_sq[:-1], vol_sq[1:])[0, 1]
    return autocorr if not np.isnan(autocorr) else 0

# Processar dados
print("\n📊 Carregando dados de treino...")
X_train = pd.read_parquet('database/X_train.parquet')
y_train = pd.read_parquet('database/y_train.parquet')

print(f"   Shape: {X_train.shape}")

# Testar diferentes configurações para HFT
configs_hft = [
    {'tau': 0.0001, 'q': 10, 'desc': 'Ultra sensível'},
    {'tau': 0.0005, 'q': 15, 'desc': 'Sensível'},
    {'tau': 0.001, 'q': 20, 'desc': 'Balanceado'},
    {'tau': 0.002, 'q': 10, 'desc': 'Robusto'},
]

print("\n🔬 Testando configurações para HFT:")
print("-" * 60)

for config in configs_hft:
    print(f"\nTestando: tau={config['tau']}, q={config['q']} ({config['desc']})")
    
    # Processar amostra
    n_test = 100
    sample_ids = X_train.index.get_level_values('id').unique()[:n_test]
    
    features_list = []
    labels = []
    success_count = 0
    
    start_time = time.time()
    
    for series_id in sample_ids:
        series_data = X_train.loc[series_id]
        if 'value' in series_data.columns:
            series_values = series_data['value'].values
        else:
            series_values = series_data.iloc[:, 0].values
        
        features = calculate_levy_features_hft(
            series_values, 
            tau=config['tau'], 
            q=config['q']
        )
        
        if features is not None:
            features_list.append(features)
            label = y_train.loc[series_id].iloc[0] if hasattr(y_train.loc[series_id], 'iloc') else y_train.loc[series_id]
            labels.append(int(label))
            success_count += 1
    
    elapsed = time.time() - start_time
    
    if len(features_list) > 0:
        # Análise rápida
        df_features = pd.DataFrame(features_list)
        df_features['label'] = labels
        
        # Estatísticas por classe
        class_0 = df_features[df_features['label'] == 0]['levy_duration_mean'].mean()
        class_1 = df_features[df_features['label'] == 1]['levy_duration_mean'].mean()
        diff_pct = ((class_1 - class_0) / class_0 * 100) if class_0 > 0 else 0
        
        print(f"   ✓ Sucesso: {success_count}/{n_test} ({success_count/n_test*100:.1f}%)")
        print(f"   Duração média - Classe 0: {class_0:.2f}")
        print(f"   Duração média - Classe 1: {class_1:.2f}")
        print(f"   Diferença: {diff_pct:+.1f}%")
        print(f"   Tempo: {elapsed:.1f}s")
        
        # Salvar melhor configuração
        if abs(diff_pct) > 15 and success_count > 80:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'database/levy_features_hft_{timestamp}.parquet'
            df_features.to_parquet(output_file)
            print(f"   💾 Features salvas: {output_file}")

print("\n" + "="*60)
print("ANÁLISE PARA HIGH FREQUENCY TRADING")
print("="*60)

print("\n📌 Características dos dados HFT:")
print("- Muitos pontos por série (alta resolução temporal)")
print("- Microestrutura importante (bid-ask, liquidez)")
print("- Quebras podem ocorrer em milissegundos")
print("- Ruído significativo em escalas muito pequenas")

print("\n🎯 Recomendações para HFT:")
print("1. Use tau entre 0.0001 e 0.001")
print("2. Use q entre 10 e 20 para estabilidade")
print("3. Considere features de microestrutura")
print("4. Combine com indicadores de liquidez")

print("\n✨ Próximos passos:")
print("1. Processar dataset completo com melhor configuração")
print("2. Adicionar features de liquidez e spread")
print("3. Testar com modelos online para trading em tempo real")

print("\n" + "="*60)