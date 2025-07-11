#!/usr/bin/env python3
"""
Script para executar análise de seções de Lévy nos dados do CrunchDAO SB.
Adaptado para trabalhar com os dados de treino do desafio de quebras estruturais.

Author: CrunchDAO SB Team
Date: 2025-06-26
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from src.features.levy_sections import LevySectionsAnalyzer, analyze_structural_breaks_for_series


def load_crunchdao_data():
    """
    Carrega os dados de treino do CrunchDAO.
    
    Returns:
        X_train: DataFrame com séries temporais
        y_train: DataFrame com labels
    """
    print("\n📊 Carregando dados do CrunchDAO...")
    
    # Caminhos dos arquivos
    data_dir = Path("database")
    x_train_path = data_dir / "X_train.parquet"
    y_train_path = data_dir / "y_train.parquet"
    
    if not x_train_path.exists() or not y_train_path.exists():
        print("❌ Arquivos de treino não encontrados!")
        print(f"   Procurando em: {data_dir.absolute()}")
        sys.exit(1)
    
    # Carregar dados
    X_train = pd.read_parquet(x_train_path)
    y_train = pd.read_parquet(y_train_path)
    
    print(f"✅ X_train carregado: {X_train.shape}")
    print(f"✅ y_train carregado: {y_train.shape}")
    
    return X_train, y_train


def analyze_single_series(series_data, series_id, tau=0.005, q=5, plot=True):
    """
    Analisa uma única série temporal.
    
    Args:
        series_data: Array com valores da série
        series_id: ID da série
        tau: Parâmetro tau
        q: Parâmetro q
        plot: Se True, gera visualização
        
    Returns:
        Dicionário com resultados
    """
    print(f"\n🔍 Analisando série {series_id}...")
    
    # Remover NaNs se houver
    series_clean = series_data[~np.isnan(series_data)]
    
    if len(series_clean) < 20:
        print(f"   ⚠️ Série muito curta ({len(series_clean)} pontos)")
        return None
    
    # Calcular retornos (diferenças)
    # Nota: Ajustar conforme a natureza dos dados
    returns = np.diff(series_clean)
    
    if len(returns) < 10:
        return None
    
    # Criar analisador
    analyzer = LevySectionsAnalyzer(tau=tau, q=q)
    
    try:
        # Calcular seções de Lévy
        levy_result = analyzer.compute_levy_sections(returns)
        
        # Detectar quebras
        breaks_info = analyzer.detect_structural_breaks(min_sections=10)
        
        # Extrair features
        features = analyzer.extract_features()
        
        # Preparar resultados
        results = {
            'series_id': series_id,
            'n_observations': len(series_clean),
            'n_sections': len(levy_result.S_tau),
            'mean_duration': np.mean(levy_result.durations),
            'std_duration': np.std(levy_result.durations),
            'n_breaks': len(breaks_info['breaks']),
            'breaks': breaks_info['breaks'],
            'features': features,
            'analyzer': analyzer,
            'levy_result': levy_result,
            'breaks_info': breaks_info
        }
        
        # Plotar se solicitado
        if plot and len(levy_result.S_tau) > 5:
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            
            # 1. Série original
            ax = axes[0, 0]
            ax.plot(series_clean, linewidth=0.8)
            ax.set_title(f'Série {series_id} - Dados Originais')
            ax.set_xlabel('Tempo')
            ax.set_ylabel('Valor')
            
            # 2. Retornos/Diferenças
            ax = axes[0, 1]
            ax.plot(returns, linewidth=0.5, alpha=0.7)
            ax.set_title('Retornos (Diferenças)')
            ax.set_xlabel('Tempo')
            ax.set_ylabel('Retorno')
            
            # 3. Durações das seções
            ax = axes[1, 0]
            section_indices = np.arange(len(levy_result.durations))
            ax.plot(section_indices, levy_result.durations, 'o-', markersize=4)
            
            # Marcar quebras
            for brk in breaks_info['breaks']:
                if brk['index'] < len(section_indices):
                    ax.axvline(x=brk['index'], color='red', linestyle='--', alpha=0.7)
            
            ax.set_title(f'Durações das Seções (tau={tau})')
            ax.set_xlabel('Índice da Seção')
            ax.set_ylabel('Duração')
            
            # 4. Histograma das somas normalizadas
            ax = axes[1, 1]
            S_tau_norm = levy_result.S_tau / np.sqrt(tau)
            ax.hist(S_tau_norm, bins=20, density=True, alpha=0.7, edgecolor='black')
            
            # Sobrepor normal teórica
            from scipy import stats
            x = np.linspace(S_tau_norm.min(), S_tau_norm.max(), 100)
            ax.plot(x, stats.norm.pdf(x, 0, 1), 'r-', linewidth=2, label='N(0,1)')
            ax.set_title('Distribuição das Somas Normalizadas')
            ax.set_xlabel('Valor')
            ax.set_ylabel('Densidade')
            ax.legend()
            
            plt.tight_layout()
            
            # Salvar figura
            output_dir = Path("outputs/crunchdao_levy")
            output_dir.mkdir(parents=True, exist_ok=True)
            fig_path = output_dir / f"series_{series_id}_analysis.png"
            plt.savefig(fig_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"   ✓ Visualização salva em: {fig_path}")
        
        return results
        
    except Exception as e:
        print(f"   ❌ Erro na análise: {str(e)}")
        return None


def batch_analyze_series(X_train, y_train, max_series=100, tau_values=[0.001, 0.005, 0.01], q=5):
    """
    Analisa múltiplas séries em lote.
    
    Args:
        X_train: DataFrame com séries temporais
        y_train: DataFrame com labels
        max_series: Número máximo de séries para analisar
        tau_values: Lista de valores de tau
        q: Parâmetro q
        
    Returns:
        DataFrame com resultados consolidados
    """
    print(f"\n🔄 Analisando {min(max_series, len(X_train))} séries...")
    
    all_results = []
    all_features = []
    
    # Selecionar séries aleatórias ou primeiras N
    series_to_analyze = X_train.index[:max_series]
    
    for i, series_id in enumerate(series_to_analyze):
        print(f"\n[{i+1}/{len(series_to_analyze)}] Série {series_id}")
        
        # Obter dados da série
        series_data = X_train.loc[series_id].values
        
        # Testar diferentes valores de tau
        for tau in tau_values:
            result = analyze_single_series(
                series_data, 
                series_id, 
                tau=tau, 
                q=q, 
                plot=(i < 10 and tau == tau_values[1])  # Plotar apenas algumas
            )
            
            if result:
                # Resumo para tabela
                summary = {
                    'series_id': series_id,
                    'tau': tau,
                    'n_observations': result['n_observations'],
                    'n_sections': result['n_sections'],
                    'mean_duration': result['mean_duration'],
                    'n_breaks': result['n_breaks'],
                    'norm_kurtosis': result['features']['levy_norm_kurtosis'],
                    'shapiro_pvalue': result['features']['levy_shapiro_pvalue'],
                    'actual_label': y_train.loc[series_id, 'target'] if series_id in y_train.index else None
                }
                all_results.append(summary)
                
                # Features completas
                features_row = result['features'].copy()
                features_row['series_id'] = series_id
                features_row['tau'] = tau
                all_features.append(features_row)
    
    # Criar DataFrames
    results_df = pd.DataFrame(all_results)
    features_df = pd.DataFrame(all_features)
    
    return results_df, features_df


def analyze_results_vs_labels(results_df, y_train):
    """
    Compara resultados com labels reais.
    
    Args:
        results_df: DataFrame com resultados da análise
        y_train: DataFrame com labels verdadeiros
    """
    print("\n📊 Comparando com labels reais...")
    
    # Filtrar apenas séries com labels
    results_with_labels = results_df[results_df['actual_label'].notna()]
    
    if results_with_labels.empty:
        print("   ⚠️ Nenhuma série com label encontrada")
        return
    
    # Análise por classe
    print("\n📈 Estatísticas por classe:")
    grouped = results_with_labels.groupby(['actual_label', 'tau']).agg({
        'n_breaks': ['mean', 'std', 'min', 'max'],
        'mean_duration': ['mean', 'std'],
        'norm_kurtosis': 'mean'
    }).round(3)
    
    print(grouped)
    
    # Criar visualização
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # 1. Número de quebras por classe
    ax = axes[0, 0]
    for tau in results_with_labels['tau'].unique():
        data = results_with_labels[results_with_labels['tau'] == tau]
        data.boxplot(column='n_breaks', by='actual_label', ax=ax)
    ax.set_title('Número de Quebras por Classe')
    ax.set_xlabel('Classe Real')
    ax.set_ylabel('Número de Quebras Detectadas')
    
    # 2. Duração média por classe
    ax = axes[0, 1]
    for label in results_with_labels['actual_label'].unique():
        data = results_with_labels[results_with_labels['actual_label'] == label]
        ax.scatter(data['tau'], data['mean_duration'], label=f'Classe {int(label)}', alpha=0.6)
    ax.set_xlabel('Tau')
    ax.set_ylabel('Duração Média das Seções')
    ax.set_title('Duração Média vs Tau por Classe')
    ax.legend()
    ax.set_xscale('log')
    
    # 3. Curtose normalizada
    ax = axes[1, 0]
    pivot_kurt = results_with_labels.pivot_table(
        values='norm_kurtosis', 
        index='series_id', 
        columns='tau', 
        aggfunc='first'
    )
    pivot_kurt.plot(ax=ax, alpha=0.5)
    ax.set_title('Curtose Normalizada para Diferentes Tau')
    ax.set_xlabel('Série')
    ax.set_ylabel('Curtose Normalizada')
    ax.axhline(y=0, color='red', linestyle='--', alpha=0.5)
    
    # 4. Correlação entre número de quebras e label
    ax = axes[1, 1]
    tau_median = results_with_labels['tau'].median()
    data_median = results_with_labels[results_with_labels['tau'] == tau_median]
    ax.scatter(data_median['actual_label'], data_median['n_breaks'], alpha=0.6)
    ax.set_xlabel('Label Real')
    ax.set_ylabel('Número de Quebras')
    ax.set_title(f'Quebras vs Label (tau={tau_median})')
    
    plt.tight_layout()
    
    # Salvar
    output_path = Path("outputs/crunchdao_levy/results_vs_labels.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\n✅ Análise comparativa salva em: {output_path}")


def save_levy_features(features_df, output_name="levy_features.parquet"):
    """
    Salva features de Lévy para uso posterior.
    
    Args:
        features_df: DataFrame com features
        output_name: Nome do arquivo de saída
    """
    output_path = Path("database") / output_name
    features_df.to_parquet(output_path)
    print(f"\n💾 Features salvas em: {output_path}")
    print(f"   Shape: {features_df.shape}")
    print(f"   Colunas: {list(features_df.columns)[:10]}...")


def main():
    """Função principal"""
    print("\n" + "="*60)
    print("ANÁLISE DE SEÇÕES DE LÉVY - DADOS CRUNCHDAO SB")
    print("="*60)
    
    # Carregar dados
    X_train, y_train = load_crunchdao_data()
    
    # Informações sobre os dados
    print(f"\n📋 Informações dos dados:")
    print(f"   Número de séries: {len(X_train)}")
    print(f"   Comprimento das séries: {X_train.shape[1]}")
    print(f"   Séries com label: {len(y_train)}")
    print(f"   Distribuição de labels: {y_train['target'].value_counts().to_dict()}")
    
    # Analisar amostra de séries
    print("\n" + "="*60)
    print("ANÁLISE EM LOTE")
    print("="*60)
    
    # Parâmetros
    max_series = 100  # Ajustar conforme necessário
    tau_values = [0.001, 0.005, 0.01, 0.02]
    q = 5
    
    # Executar análise
    results_df, features_df = batch_analyze_series(
        X_train, 
        y_train, 
        max_series=max_series,
        tau_values=tau_values,
        q=q
    )
    
    # Salvar resultados
    print("\n💾 Salvando resultados...")
    
    # Criar diretório de saída
    output_dir = Path("outputs/crunchdao_levy")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Salvar CSVs
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_df.to_csv(output_dir / f"levy_analysis_results_{timestamp}.csv", index=False)
    features_df.to_csv(output_dir / f"levy_features_{timestamp}.csv", index=False)
    
    # Salvar features em parquet para uso com modelos
    save_levy_features(features_df, f"levy_features_{timestamp}.parquet")
    
    # Análise comparativa com labels
    if 'actual_label' in results_df.columns:
        analyze_results_vs_labels(results_df, y_train)
    
    # Estatísticas finais
    print("\n" + "="*60)
    print("RESUMO DA ANÁLISE")
    print("="*60)
    
    print(f"\n📊 Estatísticas gerais:")
    print(f"   Séries analisadas: {results_df['series_id'].nunique()}")
    print(f"   Total de configurações testadas: {len(results_df)}")
    print(f"   Média de quebras detectadas: {results_df['n_breaks'].mean():.2f}")
    print(f"   Média de seções por série: {results_df['n_sections'].mean():.2f}")
    
    # Melhores parâmetros por número de quebras
    print(f"\n🎯 Parâmetros com mais detecções:")
    tau_summary = results_df.groupby('tau')['n_breaks'].agg(['mean', 'std', 'sum'])
    print(tau_summary.round(2))
    
    print("\n✨ ANÁLISE CONCLUÍDA!")
    print(f"📂 Resultados salvos em: {output_dir}/")


if __name__ == "__main__":
    main()