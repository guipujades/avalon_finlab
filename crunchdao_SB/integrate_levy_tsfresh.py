#!/usr/bin/env python3
"""
Script para integrar features de Lévy com TSFresh para o desafio CrunchDAO SB.
Combina as duas abordagens para criar um conjunto de features mais robusto.

Author: CrunchDAO SB Team
Date: 2025-06-26
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from src.features.levy_sections import LevySectionsAnalyzer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, classification_report
import matplotlib.pyplot as plt
import seaborn as sns


def load_existing_features():
    """
    Carrega features já extraídas (TSFresh e outras).
    
    Returns:
        Dict com DataFrames de features
    """
    print("\n📊 Carregando features existentes...")
    
    features = {}
    feature_files = {
        'tsfresh': 'database/features_tsfresh.parquet',
        'tsfresh_clean': 'database/tsfresh_clean_features.parquet',
        'tsfresh_top100': 'database/tsfresh_top100_features.parquet',
        'simple': 'database/features_simple.parquet'
    }
    
    for name, path in feature_files.items():
        if Path(path).exists():
            features[name] = pd.read_parquet(path)
            print(f"   ✓ {name}: {features[name].shape}")
        else:
            print(f"   ✗ {name}: não encontrado")
    
    return features


def extract_levy_features_for_all(X_train, tau_values=[0.005, 0.01], q=5, max_series=None):
    """
    Extrai features de Lévy para todas as séries.
    
    Args:
        X_train: DataFrame com séries temporais
        tau_values: Lista de valores de tau
        q: Parâmetro q
        max_series: Número máximo de séries (None = todas)
        
    Returns:
        DataFrame com features de Lévy
    """
    print(f"\n🔍 Extraindo features de Lévy para {len(X_train) if max_series is None else max_series} séries...")
    print(f"   Parâmetros: tau={tau_values}, q={q}")
    
    all_features = []
    series_to_process = X_train.index[:max_series] if max_series else X_train.index
    
    for i, series_id in enumerate(series_to_process):
        if i % 100 == 0:
            print(f"   Processando: {i}/{len(series_to_process)}")
        
        series_data = X_train.loc[series_id].values
        series_clean = series_data[~np.isnan(series_data)]
        
        if len(series_clean) < 20:
            continue
            
        # Calcular diferenças
        returns = np.diff(series_clean)
        
        if len(returns) < 10:
            continue
        
        # Features para cada tau
        series_features = {'series_id': series_id}
        
        for tau in tau_values:
            analyzer = LevySectionsAnalyzer(tau=tau, q=q)
            
            try:
                analyzer.compute_levy_sections(returns)
                features = analyzer.extract_features()
                
                # Adicionar prefixo com tau
                for key, value in features.items():
                    series_features[f'{key}_tau{tau}'] = value
                    
            except Exception as e:
                # Preencher com NaN em caso de erro
                continue
        
        if len(series_features) > 1:  # Tem features além do ID
            all_features.append(series_features)
    
    levy_df = pd.DataFrame(all_features)
    levy_df.set_index('series_id', inplace=True)
    
    print(f"✅ Features de Lévy extraídas: {levy_df.shape}")
    
    return levy_df


def combine_features(features_dict, levy_features):
    """
    Combina features de Lévy com outras features.
    
    Args:
        features_dict: Dicionário com DataFrames de features
        levy_features: DataFrame com features de Lévy
        
    Returns:
        Dict com combinações de features
    """
    print("\n🔗 Combinando features...")
    
    combined = {}
    
    # Alinhar índices
    common_index = levy_features.index
    
    for name, feat_df in features_dict.items():
        if feat_df is not None and len(feat_df) > 0:
            # Encontrar índice comum
            common_idx = common_index.intersection(feat_df.index)
            
            if len(common_idx) > 0:
                # Combinar
                combined_df = pd.concat([
                    feat_df.loc[common_idx],
                    levy_features.loc[common_idx]
                ], axis=1)
                
                combined[f'{name}_levy'] = combined_df
                print(f"   ✓ {name} + Lévy: {combined_df.shape}")
    
    # Apenas Lévy
    combined['levy_only'] = levy_features
    
    return combined


def evaluate_feature_sets(combined_features, y_train, n_folds=5):
    """
    Avalia diferentes conjuntos de features.
    
    Args:
        combined_features: Dict com diferentes combinações de features
        y_train: Labels verdadeiros
        n_folds: Número de folds para cross-validation
        
    Returns:
        DataFrame com resultados
    """
    print(f"\n🎯 Avaliando conjuntos de features (CV {n_folds}-fold)...")
    
    results = []
    
    for name, features_df in combined_features.items():
        print(f"\n   Testando: {name}")
        
        # Alinhar com labels
        common_idx = features_df.index.intersection(y_train.index)
        
        if len(common_idx) < 50:
            print(f"      ⚠️ Poucos exemplos ({len(common_idx)})")
            continue
        
        X = features_df.loc[common_idx]
        y = y_train.loc[common_idx, 'target']
        
        # Remover features com muitos NaN
        nan_ratio = X.isna().sum() / len(X)
        valid_features = nan_ratio[nan_ratio < 0.5].index
        X = X[valid_features]
        
        # Preencher NaN restantes
        X = X.fillna(X.mean())
        
        # Padronizar
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Modelo
        rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        # Cross-validation
        scores = cross_val_score(rf, X_scaled, y, cv=n_folds, scoring='roc_auc', n_jobs=-1)
        
        result = {
            'feature_set': name,
            'n_features': X.shape[1],
            'n_samples': X.shape[0],
            'roc_auc_mean': scores.mean(),
            'roc_auc_std': scores.std(),
            'scores': scores
        }
        
        results.append(result)
        
        print(f"      ROC-AUC: {scores.mean():.4f} ± {scores.std():.4f}")
        print(f"      Features: {X.shape[1]}, Amostras: {X.shape[0]}")
    
    return pd.DataFrame(results)


def analyze_feature_importance(combined_features, y_train, feature_set_name='tsfresh_levy'):
    """
    Analisa importância das features de Lévy vs outras.
    
    Args:
        combined_features: Dict com features combinadas
        y_train: Labels
        feature_set_name: Nome do conjunto para analisar
    """
    print(f"\n📊 Analisando importância das features ({feature_set_name})...")
    
    if feature_set_name not in combined_features:
        print(f"   ❌ Conjunto '{feature_set_name}' não encontrado")
        return
    
    features_df = combined_features[feature_set_name]
    
    # Alinhar com labels
    common_idx = features_df.index.intersection(y_train.index)
    X = features_df.loc[common_idx].fillna(features_df.mean())
    y = y_train.loc[common_idx, 'target']
    
    # Treinar modelo
    rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    rf.fit(X, y)
    
    # Importâncias
    importances = pd.DataFrame({
        'feature': X.columns,
        'importance': rf.feature_importances_
    }).sort_values('importance', ascending=False)
    
    # Separar features de Lévy
    levy_features = importances[importances['feature'].str.contains('levy_')]
    other_features = importances[~importances['feature'].str.contains('levy_')]
    
    # Visualizar top features
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Top 20 geral
    top20 = importances.head(20)
    ax1.barh(range(len(top20)), top20['importance'])
    ax1.set_yticks(range(len(top20)))
    ax1.set_yticklabels(top20['feature'])
    ax1.set_xlabel('Importância')
    ax1.set_title('Top 20 Features Mais Importantes')
    ax1.invert_yaxis()
    
    # Destacar features de Lévy
    for i, feat in enumerate(top20['feature']):
        if 'levy_' in feat:
            ax1.get_children()[i].set_color('red')
    
    # Comparação agregada
    levy_total = levy_features['importance'].sum()
    other_total = other_features['importance'].sum()
    
    ax2.pie([levy_total, other_total], 
            labels=['Features Lévy', 'Outras Features'],
            autopct='%1.1f%%',
            colors=['red', 'blue'])
    ax2.set_title('Contribuição Total por Tipo de Feature')
    
    plt.tight_layout()
    plt.savefig('outputs/crunchdao_levy/feature_importance_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\n📈 Resumo de importância:")
    print(f"   Features de Lévy: {len(levy_features)} ({levy_total:.1%} da importância total)")
    print(f"   Outras features: {len(other_features)} ({other_total:.1%} da importância total)")
    print(f"\n   Top 10 features de Lévy:")
    print(levy_features.head(10).to_string(index=False))


def create_final_feature_set(levy_features, tsfresh_features=None, feature_importance_threshold=0.001):
    """
    Cria conjunto final otimizado de features.
    
    Args:
        levy_features: Features de Lévy
        tsfresh_features: Features TSFresh (opcional)
        feature_importance_threshold: Limiar mínimo de importância
        
    Returns:
        DataFrame com features finais
    """
    print("\n🎯 Criando conjunto final de features...")
    
    if tsfresh_features is not None:
        # Combinar
        common_idx = levy_features.index.intersection(tsfresh_features.index)
        final_features = pd.concat([
            tsfresh_features.loc[common_idx],
            levy_features.loc[common_idx]
        ], axis=1)
    else:
        final_features = levy_features
    
    print(f"   Features totais: {final_features.shape}")
    
    # Remover features com muitos NaN
    nan_ratio = final_features.isna().sum() / len(final_features)
    valid_features = nan_ratio[nan_ratio < 0.3].index
    final_features = final_features[valid_features]
    
    print(f"   Após remover NaN excessivos: {final_features.shape}")
    
    return final_features


def main():
    """Função principal"""
    print("\n" + "="*60)
    print("INTEGRAÇÃO LÉVY + TSFRESH - CRUNCHDAO SB")
    print("="*60)
    
    # Criar diretórios
    output_dir = Path("outputs/crunchdao_levy")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Carregar dados
    print("\n📂 Carregando dados...")
    X_train = pd.read_parquet('database/X_train.parquet')
    y_train = pd.read_parquet('database/y_train.parquet')
    
    # Carregar features existentes
    existing_features = load_existing_features()
    
    # Extrair features de Lévy
    levy_features = extract_levy_features_for_all(
        X_train,
        tau_values=[0.001, 0.005, 0.01, 0.02],
        q=5,
        max_series=None  # Processar todas
    )
    
    # Salvar features de Lévy
    levy_features.to_parquet('database/features_levy.parquet')
    print(f"\n💾 Features de Lévy salvas em: database/features_levy.parquet")
    
    # Combinar com outras features
    combined_features = combine_features(existing_features, levy_features)
    
    # Avaliar diferentes combinações
    evaluation_results = evaluate_feature_sets(combined_features, y_train)
    
    # Salvar resultados da avaliação
    eval_path = output_dir / 'feature_evaluation_results.csv'
    evaluation_results.to_csv(eval_path, index=False)
    
    print("\n" + "="*60)
    print("RESULTADOS DA AVALIAÇÃO")
    print("="*60)
    print(evaluation_results.sort_values('roc_auc_mean', ascending=False).to_string(index=False))
    
    # Análise de importância
    best_set = evaluation_results.sort_values('roc_auc_mean', ascending=False).iloc[0]['feature_set']
    if 'levy' in best_set and best_set in combined_features:
        analyze_feature_importance(combined_features, y_train, best_set)
    
    # Criar e salvar conjunto final
    if 'tsfresh_clean' in existing_features:
        final_features = create_final_feature_set(
            levy_features, 
            existing_features['tsfresh_clean']
        )
    else:
        final_features = levy_features
    
    final_features.to_parquet('database/features_tsfresh_levy_combined.parquet')
    print(f"\n💾 Features combinadas finais salvas em: database/features_tsfresh_levy_combined.parquet")
    print(f"   Shape: {final_features.shape}")
    
    print("\n✨ INTEGRAÇÃO CONCLUÍDA!")
    print(f"   Melhor conjunto: {best_set}")
    print(f"   ROC-AUC: {evaluation_results.sort_values('roc_auc_mean', ascending=False).iloc[0]['roc_auc_mean']:.4f}")


if __name__ == "__main__":
    main()