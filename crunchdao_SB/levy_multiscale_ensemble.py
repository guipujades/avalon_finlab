#!/usr/bin/env python3
"""
Demonstração: Ensemble de Múltiplas Escalas com Seções de Lévy

A ideia é extrair features usando DIFERENTES valores de tau simultaneamente,
capturando quebras estruturais em diferentes escalas temporais.
"""

import pandas as pd
import numpy as np
from datetime import datetime

print("\n" + "="*60)
print("ENSEMBLE DE MÚLTIPLAS ESCALAS - LEVY SECTIONS")
print("="*60)

print("\n📚 CONCEITO:")
print("-" * 50)
print("""
Imagine que quebras estruturais podem ocorrer em diferentes escalas:

1. MICRO-QUEBRAS (tau=0.0001)
   - Mudanças muito rápidas (segundos/minutos em HFT)
   - Picos de volatilidade momentâneos
   - Pode capturar ruído

2. QUEBRAS MÉDIAS (tau=0.001)
   - Mudanças de regime intraday
   - Alterações de liquidez
   - Balanço entre sinal e ruído

3. MACRO-QUEBRAS (tau=0.01)
   - Mudanças de regime de dias/semanas
   - Eventos macroeconômicos
   - Muito estável, mas pode perder eventos rápidos

SOLUÇÃO: Usar TODAS as escalas simultaneamente!
""")

def calculate_levy_multiscale(returns, tau_list=[0.0001, 0.0005, 0.001, 0.005, 0.01], q=20):
    """
    Calcula features de Lévy em múltiplas escalas.
    
    Retorna features para cada valor de tau, permitindo
    que o modelo aprenda qual escala é mais relevante.
    """
    all_features = {}
    
    for tau in tau_list:
        # Calcular features para este tau
        features = calculate_levy_features_single_scale(returns, tau, q)
        
        if features is not None:
            # Adicionar prefixo indicando a escala
            scale_name = f"tau{int(tau*10000)}"
            for key, value in features.items():
                all_features[f"{key}_{scale_name}"] = value
    
    return all_features if all_features else None

def calculate_levy_features_single_scale(returns, tau, q):
    """Calcula features para uma única escala (tau)."""
    try:
        returns_clean = returns[~np.isnan(returns)]
        if len(returns_clean) < 2 * q + 50:
            return None
        
        # Volatilidade local
        volatilities = []
        for i in range(q, len(returns_clean) - q):
            window = returns_clean[i-q:i+q+1]
            vol = np.sqrt(np.mean(window**2))
            volatilities.append(max(vol, 1e-10))
        
        # Construir seções
        cumsum = 0
        section_durations = []
        last_idx = 0
        
        for i, vol in enumerate(volatilities):
            cumsum += vol**2
            if cumsum >= tau:
                duration = i - last_idx
                if duration > 0:
                    section_durations.append(duration)
                    last_idx = i
                    cumsum = 0
        
        if len(section_durations) < 3:
            return None
        
        durations = np.array(section_durations)
        
        return {
            'duration_mean': np.mean(durations),
            'duration_cv': np.std(durations) / np.mean(durations),
            'n_sections': len(durations),
        }
        
    except:
        return None

# Exemplo com dados sintéticos
print("\n🔬 EXEMPLO PRÁTICO:")
print("-" * 50)

# Simular série com diferentes tipos de quebras
np.random.seed(42)
n_points = 2000

# Série 1: Quebra estrutural grande (macro evento)
returns1 = np.concatenate([
    np.random.normal(0, 0.01, 1000),    # Volatilidade baixa
    np.random.normal(0, 0.05, 1000)     # Volatilidade alta (5x maior)
])

# Série 2: Múltiplas micro-quebras (HFT)
returns2 = np.random.normal(0, 0.01, n_points)
# Adicionar spikes de volatilidade
for i in range(10):
    start = np.random.randint(0, n_points-50)
    returns2[start:start+50] *= 3

print("\nProcessando Série 1 (macro-quebra):")
features1 = calculate_levy_multiscale(returns1)
if features1:
    for key, value in sorted(features1.items()):
        if 'duration_mean' in key:
            print(f"   {key}: {value:.2f}")

print("\nProcessando Série 2 (micro-quebras):")
features2 = calculate_levy_multiscale(returns2)
if features2:
    for key, value in sorted(features2.items()):
        if 'duration_mean' in key:
            print(f"   {key}: {value:.2f}")

# Demonstrar como usar em ML
print("\n💡 VANTAGENS DO ENSEMBLE MULTI-ESCALA:")
print("-" * 50)

print("""
1. COBERTURA COMPLETA:
   - Não perde quebras em nenhuma escala temporal
   - Modelo aprende automaticamente quais escalas são relevantes

2. ROBUSTEZ:
   - Se uma escala captura ruído, outras compensam
   - Reduz dependência de escolher tau "perfeito"

3. INTERPRETABILIDADE:
   - Pode identificar TIPO de quebra estrutural
   - Ex: Se tau=0.01 detecta mas tau=0.0001 não → evento macro
   - Ex: Se tau=0.0001 detecta mas tau=0.01 não → micro-estrutura

4. APLICAÇÃO EM PRODUÇÃO:
""")

print("\n📊 EXEMPLO DE FEATURES FINAIS:")
print("-" * 50)
print("""
Para cada série, teríamos:
- levy_duration_mean_tau1    (tau=0.0001) → micro escala
- levy_duration_mean_tau5    (tau=0.0005)
- levy_duration_mean_tau10   (tau=0.001)  → média escala  
- levy_duration_mean_tau50   (tau=0.005)
- levy_duration_mean_tau100  (tau=0.01)   → macro escala

- levy_duration_cv_tau1
- levy_duration_cv_tau5
- ... (etc)

Total: ~15-20 features cobrindo todas as escalas
""")

print("\n🚀 IMPLEMENTAÇÃO PARA O CRUNCHDAO:")
print("-" * 50)

code_example = """
# Processar dados com múltiplas escalas
def process_crunchdao_multiscale(X_train, y_train, n_series=1000):
    tau_scales = [0.0001, 0.0005, 0.001, 0.005, 0.01]
    
    all_features = []
    for series_id in series_ids:
        returns = X_train.loc[series_id, 'value'].values
        
        # Extrair features multi-escala
        features = calculate_levy_multiscale(returns, tau_scales)
        
        if features:
            features['label'] = y_train.loc[series_id]
            all_features.append(features)
    
    # DataFrame com ~15 features por série
    df_multiscale = pd.DataFrame(all_features)
    
    # Treinar modelo
    rf = RandomForestClassifier()
    rf.fit(X, y)
    
    # Ver importância por escala
    plot_importance_by_scale(rf.feature_importances_)
"""

print(code_example)

print("\n" + "="*60)
print("CONCLUSÃO: Ensemble multi-escala captura quebras em TODOS os")
print("horizontes temporais, deixando o modelo decidir qual é relevante!")
print("="*60)