#!/usr/bin/env python3
"""
Versão simplificada do script de análise de Lévy sem dependências problemáticas.
Usa apenas numpy, pandas e matplotlib básico.

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
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# Importar apenas o essencial
from src.features.levy_sections import LevySectionsAnalyzer


def load_data():
    """Carrega os dados de treino do CrunchDAO."""
    print("\n📊 Carregando dados do CrunchDAO...")
    
    try:
        X_train = pd.read_parquet('database/X_train.parquet')
        y_train = pd.read_parquet('database/y_train.parquet')
        
        print(f"✅ Dados carregados:")
        print(f"   X_train: {X_train.shape}")
        print(f"   y_train: {y_train.shape}")
        print(f"   Classes: {y_train['target'].value_counts().to_dict()}")
        
        return X_train, y_train
    except Exception as e:
        print(f"❌ Erro ao carregar dados: {e}")
        sys.exit(1)


def extract_levy_features_batch(X_train, sample_size=100, tau=0.005, q=5):
    """
    Extrai features de Lévy para uma amostra das séries.
    
    Args:
        X_train: DataFrame com séries temporais
        sample_size: Número de séries para processar
        tau: Parâmetro tau
        q: Parâmetro q
        
    Returns:
        DataFrame com features
    """
    print(f"\n🔍 Extraindo features de Lévy (amostra de {sample_size} séries)...")
    print(f"   Parâmetros: tau={tau}, q={q}")
    
    # Selecionar amostra aleatória
    sample_indices = np.random.choice(X_train.index, size=min(sample_size, len(X_train)), replace=False)
    
    all_features = []
    success_count = 0
    
    for i, series_id in enumerate(sample_indices):
        if i % 10 == 0:
            print(f"   Processando: {i}/{len(sample_indices)}")
        
        series_data = X_train.loc[series_id].values
        
        # Remover NaNs
        series_clean = series_data[~np.isnan(series_data)]
        
        if len(series_clean) < 20:
            continue
        
        # Calcular diferenças (retornos)
        returns = np.diff(series_clean)
        
        if len(returns) < 10:
            continue
        
        # Criar analisador
        analyzer = LevySectionsAnalyzer(tau=tau, q=q)
        
        try:
            # Calcular seções de Lévy
            analyzer.compute_levy_sections(returns)
            
            # Extrair features
            features = analyzer.extract_features()
            features['series_id'] = series_id
            
            all_features.append(features)
            success_count += 1
            
        except Exception as e:
            continue
    
    # Criar DataFrame
    if all_features:
        features_df = pd.DataFrame(all_features)
        features_df.set_index('series_id', inplace=True)
        
        print(f"\n✅ Features extraídas com sucesso!")
        print(f"   Séries processadas: {success_count}/{len(sample_indices)}")
        print(f"   Features por série: {len(features_df.columns)}")
        print(f"   Taxa de sucesso: {success_count/len(sample_indices)*100:.1f}%")
        
        return features_df
    else:
        print("❌ Nenhuma feature foi extraída com sucesso.")
        return None


def analyze_and_visualize(features_df, y_train):
    """
    Analisa e visualiza as features extraídas.
    
    Args:
        features_df: DataFrame com features
        y_train: Labels verdadeiros
    """
    print("\n📊 Analisando features...")
    
    # Alinhar com labels
    common_idx = features_df.index.intersection(y_train.index)
    if len(common_idx) == 0:
        print("❌ Nenhum índice comum encontrado entre features e labels.")
        return
    
    features_aligned = features_df.loc[common_idx]
    labels_aligned = y_train.loc[common_idx, 'target']
    
    # Estatísticas básicas
    print(f"\n📈 Estatísticas por classe:")
    
    # Criar figura simples
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.ravel()
    
    # Features principais para visualizar
    features_to_plot = [
        'levy_duration_mean',
        'levy_duration_cv',
        'levy_norm_kurtosis',
        'levy_n_sections'
    ]
    
    for i, feature in enumerate(features_to_plot):
        if feature in features_aligned.columns:
            ax = axes[i]
            
            # Separar por classe
            class_0 = features_aligned[labels_aligned == 0][feature].dropna()
            class_1 = features_aligned[labels_aligned == 1][feature].dropna()
            
            # Histogramas sobrepostos
            ax.hist(class_0, bins=20, alpha=0.5, label='Classe 0', color='blue')
            ax.hist(class_1, bins=20, alpha=0.5, label='Classe 1', color='red')
            
            ax.set_xlabel(feature.replace('levy_', '').replace('_', ' ').title())
            ax.set_ylabel('Frequência')
            ax.legend()
            
            # Calcular estatísticas
            mean_0 = class_0.mean()
            mean_1 = class_1.mean()
            
            print(f"\n   {feature}:")
            print(f"      Classe 0: média = {mean_0:.4f}")
            print(f"      Classe 1: média = {mean_1:.4f}")
            print(f"      Diferença: {abs(mean_1 - mean_0):.4f}")
    
    plt.suptitle('Distribuição das Features de Lévy por Classe')
    plt.tight_layout()
    
    # Salvar figura
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    plt.savefig(output_dir / 'levy_features_analysis_simple.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print("\n✅ Visualização salva em: outputs/levy_features_analysis_simple.png")


def simple_model_evaluation(features_df, y_train):
    """
    Avaliação simples do poder discriminativo das features.
    
    Args:
        features_df: DataFrame com features
        y_train: Labels verdadeiros
    """
    print("\n🎯 Avaliação simples do modelo...")
    
    # Alinhar dados
    common_idx = features_df.index.intersection(y_train.index)
    X = features_df.loc[common_idx].fillna(features_df.mean())
    y = y_train.loc[common_idx, 'target']
    
    print(f"   Amostras: {len(X)}")
    print(f"   Features: {X.shape[1]}")
    
    # Dividir em treino e teste manualmente (80/20)
    n_samples = len(X)
    n_train = int(0.8 * n_samples)
    
    # Embaralhar índices
    indices = np.random.permutation(n_samples)
    train_idx = indices[:n_train]
    test_idx = indices[n_train:]
    
    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]
    y_train_split = y.iloc[train_idx]
    y_test = y.iloc[test_idx]
    
    # Normalizar dados
    mean = X_train.mean()
    std = X_train.std() + 1e-8
    X_train_scaled = (X_train - mean) / std
    X_test_scaled = (X_test - mean) / std
    
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.metrics import roc_auc_score, accuracy_score
        
        # Treinar Random Forest simples
        print("\n   Treinando Random Forest...")
        rf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
        rf.fit(X_train_scaled, y_train_split)
        
        # Predições
        y_pred = rf.predict(X_test_scaled)
        y_pred_proba = rf.predict_proba(X_test_scaled)[:, 1]
        
        # Métricas
        accuracy = accuracy_score(y_test, y_pred)
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        
        print(f"\n📊 Resultados:")
        print(f"   Acurácia: {accuracy:.4f}")
        print(f"   ROC-AUC: {roc_auc:.4f}")
        
        # Top features
        feature_importance = pd.DataFrame({
            'feature': X.columns,
            'importance': rf.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print(f"\n🏆 Top 5 features mais importantes:")
        for _, row in feature_importance.head(5).iterrows():
            print(f"   - {row['feature']}: {row['importance']:.4f}")
            
    except ImportError:
        print("   ⚠️ sklearn não disponível. Pulando avaliação do modelo.")


def save_features(features_df):
    """Salva as features extraídas."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'database/levy_features_simple_{timestamp}.parquet'
    
    features_df.to_parquet(output_file)
    print(f"\n💾 Features salvas em: {output_file}")
    
    # Salvar também em CSV para fácil visualização
    csv_file = f'outputs/levy_features_simple_{timestamp}.csv'
    features_df.head(100).to_csv(csv_file)
    print(f"   Amostra em CSV: {csv_file}")


def main():
    """Função principal"""
    print("\n" + "="*60)
    print("ANÁLISE SIMPLIFICADA COM SEÇÕES DE LÉVY")
    print("="*60)
    
    # 1. Carregar dados
    X_train, y_train = load_data()
    
    # 2. Extrair features de Lévy (amostra)
    features_df = extract_levy_features_batch(X_train, sample_size=500, tau=0.005, q=5)
    
    if features_df is not None:
        # 3. Analisar e visualizar
        analyze_and_visualize(features_df, y_train)
        
        # 4. Avaliação simples
        simple_model_evaluation(features_df, y_train)
        
        # 5. Salvar resultados
        save_features(features_df)
        
        print("\n" + "="*60)
        print("✨ ANÁLISE CONCLUÍDA!")
        print("="*60)
        
        # Resumo
        print(f"\n📋 Resumo:")
        print(f"   Features extraídas: {len(features_df.columns)}")
        print(f"   Séries analisadas: {len(features_df)}")
        
        # Lista de features
        print(f"\n📝 Features disponíveis:")
        for i, col in enumerate(features_df.columns, 1):
            print(f"   {i}. {col}")
    else:
        print("\n❌ Não foi possível extrair features.")


if __name__ == "__main__":
    main()