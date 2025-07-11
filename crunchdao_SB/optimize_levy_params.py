#!/usr/bin/env python3
"""
Otimiza os parâmetros tau e q para as features de Lévy.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
import time

print("\n" + "="*60)
print("OTIMIZAÇÃO DE PARÂMETROS - LEVY SECTIONS")
print("="*60)

# Carregar dados originais
print("\n📊 Carregando dados de treino...")
X_train = pd.read_parquet('database/X_train.parquet')
y_train = pd.read_parquet('database/y_train.parquet')

# Configurar grid de parâmetros
tau_values = [0.001, 0.005, 0.01, 0.02, 0.05]
q_values = [3, 5, 10, 15, 20]

print(f"\n🔍 Grid de busca:")
print(f"   tau: {tau_values}")
print(f"   q: {q_values}")
print(f"   Total de combinações: {len(tau_values) * len(q_values)}")

# Função para calcular features de Lévy
def calculate_levy_features(series_values, tau=0.005, q=5):
    """Calcula features de Lévy para uma série."""
    try:
        # Remover NaN
        series_clean = series_values[~np.isnan(series_values)]
        if len(series_clean) < 2 * q + 10:
            return None
        
        # Calcular retornos
        returns = np.diff(series_clean)
        if len(returns) < 2 * q + 2:
            return None
        
        # Estimar volatilidades locais
        volatilities = []
        for i in range(q, len(returns) - q):
            window = returns[i-q:i+q+1]
            vol = np.std(window)
            volatilities.append(vol if vol > 0 else 1e-8)
        
        volatilities = np.array(volatilities)
        
        # Construir seções de Lévy
        cumsum = 0
        section_starts = [0]
        section_durations = []
        
        for i in range(len(volatilities)):
            cumsum += volatilities[i]**2
            if cumsum >= tau:
                duration = i - section_starts[-1]
                section_durations.append(duration)
                section_starts.append(i)
                cumsum = 0
        
        if len(section_durations) < 3:
            return None
        
        # Extrair features
        durations = np.array(section_durations)
        
        features = {
            'levy_duration_mean': np.mean(durations),
            'levy_duration_std': np.std(durations),
            'levy_duration_cv': np.std(durations) / np.mean(durations) if np.mean(durations) > 0 else 0,
            'levy_duration_min': np.min(durations),
            'levy_duration_max': np.max(durations),
            'levy_n_sections': len(durations),
        }
        
        return features
        
    except Exception:
        return None

# Testar diferentes combinações
results = []
best_score = 0
best_params = None

print("\n🎯 Testando combinações de parâmetros...")
print("-" * 60)

for tau in tau_values:
    for q in q_values:
        print(f"\nTestando tau={tau}, q={q}...")
        start_time = time.time()
        
        # Processar subset de séries para teste rápido
        n_test = 200  # Usar apenas 200 séries para otimização
        sample_ids = X_train.index.get_level_values('id').unique()[:n_test]
        
        features_list = []
        labels = []
        
        for i, series_id in enumerate(sample_ids):
            if i % 50 == 0:
                print(f"   Processando série {i}/{n_test}...", end='\r')
            
            # Obter série
            series_data = X_train.loc[series_id]
            if 'value' in series_data.columns:
                series_values = series_data['value'].values
            else:
                series_values = series_data.iloc[:, 0].values
            
            # Calcular features
            features = calculate_levy_features(series_values, tau=tau, q=q)
            
            if features is not None:
                features_list.append(features)
                # Obter label
                label = y_train.loc[series_id].iloc[0] if hasattr(y_train.loc[series_id], 'iloc') else y_train.loc[series_id]
                labels.append(int(label))
        
        if len(features_list) < 50:
            print(f"   ⚠️  Apenas {len(features_list)} séries processadas com sucesso")
            continue
        
        # Criar DataFrame
        features_df = pd.DataFrame(features_list)
        y = np.array(labels)
        
        # Avaliar com Random Forest
        rf = RandomForestClassifier(
            n_estimators=50,  # Menos árvores para teste rápido
            max_depth=10,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        )
        
        cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
        scores = cross_val_score(rf, features_df, y, cv=cv, scoring='roc_auc', n_jobs=-1)
        score_mean = scores.mean()
        
        elapsed = time.time() - start_time
        
        result = {
            'tau': tau,
            'q': q,
            'roc_auc': score_mean,
            'std': scores.std(),
            'n_features': len(features_list),
            'time': elapsed
        }
        results.append(result)
        
        print(f"   ✓ ROC-AUC: {score_mean:.4f} (±{scores.std():.4f})")
        print(f"   Features extraídas: {len(features_list)}/{n_test}")
        print(f"   Tempo: {elapsed:.1f}s")
        
        if score_mean > best_score:
            best_score = score_mean
            best_params = {'tau': tau, 'q': q}

# Resumo dos resultados
print("\n" + "="*60)
print("RESULTADOS DA OTIMIZAÇÃO")
print("="*60)

# Ordenar por ROC-AUC
results_df = pd.DataFrame(results).sort_values('roc_auc', ascending=False)

print("\nTop 10 combinações:")
print("-" * 60)
print("tau     q      ROC-AUC    std      n_feat   tempo")
print("-" * 60)

for idx, row in results_df.head(10).iterrows():
    print(f"{row['tau']:<7.3f} {row['q']:<6} {row['roc_auc']:<10.4f} {row['std']:<8.4f} {row['n_features']:<8} {row['time']:.1f}s")

print("\n" + "="*60)
print(f"MELHORES PARÂMETROS: tau={best_params['tau']}, q={best_params['q']}")
print(f"ROC-AUC: {best_score:.4f}")
print("="*60)

# Salvar resultados
results_df.to_csv('outputs/levy_param_optimization.csv', index=False)
print("\n💾 Resultados salvos em: outputs/levy_param_optimization.csv")