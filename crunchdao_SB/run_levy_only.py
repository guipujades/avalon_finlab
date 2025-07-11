#!/usr/bin/env python3
"""
Script simplificado para executar APENAS análise de seções de Lévy nos dados do CrunchDAO.
Primeira rodada focada exclusivamente nas features de Lévy.

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
import seaborn as sns
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

from src.features.levy_sections import LevySectionsAnalyzer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, classification_report, confusion_matrix


def load_data():
    """
    Carrega os dados de treino do CrunchDAO.
    
    Returns:
        X_train: DataFrame com séries temporais
        y_train: DataFrame com labels
    """
    print("\n📊 Carregando dados do CrunchDAO...")
    
    # Caminhos dos arquivos
    X_train = pd.read_parquet('database/X_train.parquet')
    y_train = pd.read_parquet('database/y_train.parquet')
    
    print(f"✅ Dados carregados:")
    print(f"   X_train: {X_train.shape}")
    print(f"   y_train: {y_train.shape}")
    print(f"   Classes: {y_train['target'].value_counts().to_dict()}")
    
    return X_train, y_train


def extract_levy_features_single(series_data, tau=0.005, q=5):
    """
    Extrai features de Lévy para uma única série.
    
    Args:
        series_data: Array com valores da série
        tau: Parâmetro tau
        q: Parâmetro q
        
    Returns:
        Dict com features ou None se falhar
    """
    # Remover NaNs
    series_clean = series_data[~np.isnan(series_data)]
    
    if len(series_clean) < 20:
        return None
    
    # Calcular diferenças (retornos)
    returns = np.diff(series_clean)
    
    if len(returns) < 10:
        return None
    
    # Criar analisador
    analyzer = LevySectionsAnalyzer(tau=tau, q=q)
    
    try:
        # Calcular seções de Lévy
        analyzer.compute_levy_sections(returns)
        
        # Extrair features
        features = analyzer.extract_features()
        
        return features
        
    except Exception as e:
        return None


def extract_all_levy_features(X_train, tau_values=[0.005], q=5):
    """
    Extrai features de Lévy para todas as séries com um único tau.
    
    Args:
        X_train: DataFrame com séries temporais
        tau_values: Lista com valores de tau (usar apenas um para simplificar)
        q: Parâmetro q
        
    Returns:
        DataFrame com features
    """
    print(f"\n🔍 Extraindo features de Lévy...")
    print(f"   Parâmetros: tau={tau_values[0]}, q={q}")
    print(f"   Total de séries: {len(X_train)}")
    
    all_features = []
    
    # Processar todas as séries com barra de progresso
    for series_id in tqdm(X_train.index, desc="Processando séries"):
        series_data = X_train.loc[series_id].values
        
        # Extrair features
        features = extract_levy_features_single(series_data, tau=tau_values[0], q=q)
        
        if features is not None:
            features['series_id'] = series_id
            all_features.append(features)
    
    # Criar DataFrame
    features_df = pd.DataFrame(all_features)
    features_df.set_index('series_id', inplace=True)
    
    print(f"\n✅ Features extraídas com sucesso!")
    print(f"   Séries processadas: {len(features_df)}")
    print(f"   Features por série: {len(features_df.columns)}")
    print(f"   Taxa de sucesso: {len(features_df)/len(X_train)*100:.1f}%")
    
    return features_df


def analyze_features(features_df, y_train):
    """
    Analisa as features extraídas.
    
    Args:
        features_df: DataFrame com features
        y_train: Labels verdadeiros
    """
    print("\n📊 Analisando features extraídas...")
    
    # Alinhar com labels
    common_idx = features_df.index.intersection(y_train.index)
    features_aligned = features_df.loc[common_idx]
    labels_aligned = y_train.loc[common_idx, 'target']
    
    # Estatísticas por classe
    print("\n📈 Estatísticas por classe:")
    
    # Criar visualizações
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.ravel()
    
    # Features selecionadas para visualização
    features_to_plot = [
        'levy_duration_mean',
        'levy_duration_cv',
        'levy_duration_kurtosis',
        'levy_norm_kurtosis',
        'levy_shapiro_pvalue',
        'levy_n_sections'
    ]
    
    for i, feature in enumerate(features_to_plot):
        if feature in features_aligned.columns:
            ax = axes[i]
            
            # Boxplot por classe
            data_class_0 = features_aligned[labels_aligned == 0][feature].dropna()
            data_class_1 = features_aligned[labels_aligned == 1][feature].dropna()
            
            ax.boxplot([data_class_0, data_class_1], labels=['Classe 0', 'Classe 1'])
            ax.set_title(feature.replace('levy_', '').replace('_', ' ').title())
            ax.set_ylabel('Valor')
            
            # Teste estatístico
            from scipy import stats
            _, p_value = stats.ttest_ind(data_class_0, data_class_1)
            ax.text(0.5, 0.95, f'p-value: {p_value:.4f}', 
                   transform=ax.transAxes, ha='center', va='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig('outputs/levy_features_by_class.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✅ Análise visual salva em: outputs/levy_features_by_class.png")
    
    # Correlação entre features
    plt.figure(figsize=(10, 8))
    corr_matrix = features_aligned.corr()
    sns.heatmap(corr_matrix, cmap='coolwarm', center=0, 
                square=True, linewidths=0.5, cbar_kws={"shrink": 0.8})
    plt.title('Correlação entre Features de Lévy')
    plt.tight_layout()
    plt.savefig('outputs/levy_features_correlation.png', dpi=300, bbox_inches='tight')
    plt.close()


def train_model_levy_only(features_df, y_train):
    """
    Treina modelo usando apenas features de Lévy.
    
    Args:
        features_df: DataFrame com features
        y_train: Labels
        
    Returns:
        Modelo treinado e métricas
    """
    print("\n🎯 Treinando modelo com features de Lévy...")
    
    # Alinhar dados
    common_idx = features_df.index.intersection(y_train.index)
    X = features_df.loc[common_idx]
    y = y_train.loc[common_idx, 'target']
    
    print(f"   Amostras: {len(X)}")
    print(f"   Features: {X.shape[1]}")
    
    # Tratar valores faltantes
    X = X.fillna(X.mean())
    
    # Dividir dados
    X_train, X_test, y_train_split, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Padronizar
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Treinar modelo
    print("\n   Treinando Random Forest...")
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    
    rf.fit(X_train_scaled, y_train_split)
    
    # Avaliar no conjunto de teste
    y_pred = rf.predict(X_test_scaled)
    y_pred_proba = rf.predict_proba(X_test_scaled)[:, 1]
    
    # Métricas
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    
    print(f"\n📊 Resultados no conjunto de teste:")
    print(f"   ROC-AUC: {roc_auc:.4f}")
    print("\n" + classification_report(y_test, y_pred))
    
    # Cross-validation
    print("\n   Executando cross-validation (5-fold)...")
    cv_scores = cross_val_score(rf, X, y, cv=5, scoring='roc_auc', n_jobs=-1)
    print(f"   ROC-AUC (CV): {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    
    # Importância das features
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': rf.feature_importances_
    }).sort_values('importance', ascending=False)
    
    # Plotar top features
    plt.figure(figsize=(10, 6))
    top_features = feature_importance.head(15)
    plt.barh(range(len(top_features)), top_features['importance'])
    plt.yticks(range(len(top_features)), top_features['feature'])
    plt.xlabel('Importância')
    plt.title('Top 15 Features de Lévy Mais Importantes')
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig('outputs/levy_feature_importance.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Matriz de confusão
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['Classe 0', 'Classe 1'],
                yticklabels=['Classe 0', 'Classe 1'])
    plt.title('Matriz de Confusão - Features de Lévy')
    plt.ylabel('Verdadeiro')
    plt.xlabel('Predito')
    plt.tight_layout()
    plt.savefig('outputs/levy_confusion_matrix.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return rf, scaler, roc_auc, cv_scores


def save_results(features_df, model_metrics):
    """
    Salva todos os resultados.
    
    Args:
        features_df: DataFrame com features
        model_metrics: Métricas do modelo
    """
    print("\n💾 Salvando resultados...")
    
    # Criar diretório se não existir
    Path("outputs").mkdir(exist_ok=True)
    
    # Salvar features
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    features_file = f'database/levy_features_only_{timestamp}.parquet'
    features_df.to_parquet(features_file)
    print(f"   ✓ Features salvas em: {features_file}")
    
    # Salvar resumo
    summary_file = f'outputs/levy_only_summary_{timestamp}.txt'
    with open(summary_file, 'w') as f:
        f.write("="*60 + "\n")
        f.write("ANÁLISE APENAS COM FEATURES DE LÉVY\n")
        f.write("="*60 + "\n\n")
        f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total de séries processadas: {len(features_df)}\n")
        f.write(f"Features extraídas: {len(features_df.columns)}\n")
        f.write(f"\nMODELO RANDOM FOREST:\n")
        f.write(f"ROC-AUC (teste): {model_metrics['roc_auc']:.4f}\n")
        f.write(f"ROC-AUC (CV): {model_metrics['cv_mean']:.4f} ± {model_metrics['cv_std']:.4f}\n")
        f.write(f"\nParâmetros utilizados:\n")
        f.write(f"tau = 0.005\n")
        f.write(f"q = 5\n")
    
    print(f"   ✓ Resumo salvo em: {summary_file}")


def main():
    """Função principal"""
    print("\n" + "="*60)
    print("ANÁLISE COM SEÇÕES DE LÉVY - PRIMEIRA RODADA")
    print("="*60)
    
    # Criar diretório de saída
    Path("outputs").mkdir(exist_ok=True)
    
    # 1. Carregar dados
    X_train, y_train = load_data()
    
    # 2. Extrair features de Lévy (usando apenas tau=0.005 para simplificar)
    features_df = extract_all_levy_features(X_train, tau_values=[0.005], q=5)
    
    # 3. Analisar features
    analyze_features(features_df, y_train)
    
    # 4. Treinar modelo
    model, scaler, roc_auc, cv_scores = train_model_levy_only(features_df, y_train)
    
    # 5. Salvar resultados
    model_metrics = {
        'roc_auc': roc_auc,
        'cv_mean': cv_scores.mean(),
        'cv_std': cv_scores.std()
    }
    save_results(features_df, model_metrics)
    
    print("\n" + "="*60)
    print("✨ ANÁLISE CONCLUÍDA!")
    print("="*60)
    print(f"\n📊 Resumo Final:")
    print(f"   Features de Lévy extraídas: {len(features_df.columns)}")
    print(f"   Séries processadas: {len(features_df)}/{len(X_train)}")
    print(f"   ROC-AUC (teste): {roc_auc:.4f}")
    print(f"   ROC-AUC (CV 5-fold): {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    print(f"\n📂 Arquivos gerados:")
    print(f"   - Features: database/levy_features_only_*.parquet")
    print(f"   - Visualizações: outputs/levy_*.png")
    print(f"   - Resumo: outputs/levy_only_summary_*.txt")


if __name__ == "__main__":
    main()