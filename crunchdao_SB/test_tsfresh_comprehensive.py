"""
TSFresh Comprehensive Analysis - Extração máxima de features
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from tsfresh import extract_features, select_features
from tsfresh.feature_extraction import ComprehensiveFCParameters, EfficientFCParameters
from tsfresh.utilities.dataframe_functions import impute
from tsfresh.feature_selection.relevance import calculate_relevance_table

from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.metrics import roc_auc_score, classification_report


def prepare_tsfresh_data(X_train, sample_size=None):
    """Preparar dados no formato TSFresh."""
    print(f"\nPreparando dados para TSFresh...")
    
    if sample_size:
        unique_ids = X_train['id'].unique()[:sample_size]
        X_train = X_train[X_train['id'].isin(unique_ids)]
    
    df_list = []
    id_mapping = {}
    
    for i, series_id in enumerate(X_train['id'].unique()):
        series_data = X_train[X_train['id'] == series_id]
        
        # Mapear ID original para ID simplificado
        id_mapping[i] = series_id
        
        # Separar períodos
        for period in [0, 1]:
            period_data = series_data[series_data['period'] == period].copy()
            if len(period_data) > 0:
                period_data['id'] = f"{i}_{period}"
                period_data['time'] = range(len(period_data))
                df_list.append(period_data[['id', 'time', 'value']])
    
    tsfresh_df = pd.concat(df_list, ignore_index=True)
    print(f"Total de pontos de dados: {len(tsfresh_df):,}")
    print(f"Séries únicas: {len(id_mapping)}")
    
    return tsfresh_df, id_mapping


def extract_all_features(tsfresh_df, feature_set='comprehensive'):
    """Extrair todas as features possíveis."""
    print(f"\n{'='*60}")
    print(f"EXTRAINDO FEATURES - {feature_set.upper()}")
    print('='*60)
    
    # Configurar parâmetros
    if feature_set == 'comprehensive':
        fc_parameters = ComprehensiveFCParameters()
    elif feature_set == 'efficient':
        fc_parameters = EfficientFCParameters()
    else:
        # Custom parameters focados em quebras estruturais
        fc_parameters = {
            # Estatísticas básicas
            "mean": None,
            "median": None,
            "standard_deviation": None,
            "variance": None,
            "skewness": None,
            "kurtosis": None,
            
            # Percentis e quantis
            "quantile": [{"q": q} for q in [0.1, 0.25, 0.5, 0.75, 0.9]],
            
            # Autocorrelação
            "autocorrelation": [{"lag": lag} for lag in range(1, 11)],
            "partial_autocorrelation": [{"lag": lag} for lag in range(1, 11)],
            
            # Estatísticas de mudança
            "change_quantiles": [
                {"ql": 0.0, "qh": 0.2, "isabs": True, "f_agg": "mean"},
                {"ql": 0.0, "qh": 0.2, "isabs": True, "f_agg": "var"},
                {"ql": 0.8, "qh": 1.0, "isabs": True, "f_agg": "mean"},
                {"ql": 0.8, "qh": 1.0, "isabs": True, "f_agg": "var"}
            ],
            
            # Tendência
            "linear_trend": [{"attr": attr} for attr in ["slope", "intercept", "stderr", "rvalue", "pvalue"]],
            
            # Entropia
            "sample_entropy": None,
            "approximate_entropy": [{"m": 2, "r": 0.5}],
            "binned_entropy": [{"max_bins": bins} for bins in [5, 10, 20]],
            
            # FFT
            "fft_coefficient": [
                {"coeff": k, "attr": "real"} for k in range(0, 20)
            ] + [
                {"coeff": k, "attr": "imag"} for k in range(0, 20)
            ] + [
                {"coeff": k, "attr": "abs"} for k in range(0, 20)
            ] + [
                {"coeff": k, "attr": "angle"} for k in range(0, 20)
            ],
            
            # Wavelets e energia
            "energy_ratio_by_chunks": [{"num_segments": 10, "segment_focus": i} for i in range(10)],
            "spkt_welch_density": [{"coeff": i} for i in range(5)],
            
            # Estatísticas robustas
            "large_standard_deviation": [{"r": r} for r in np.arange(0.05, 1.0, 0.05)],
            
            # Características específicas
            "number_peaks": [{"n": n} for n in [1, 3, 5, 10]],
            "number_crossing_m": [{"m": m} for m in [-1, 0, 1]],
            "longest_strike_above_mean": None,
            "longest_strike_below_mean": None,
            
            # Testes estatísticos
            "augmented_dickey_fuller": [{"attr": "teststat"}, {"attr": "pvalue"}],
            
            # Outras
            "ratio_beyond_r_sigma": [{"r": r} for r in [0.5, 1, 1.5, 2, 2.5, 3]],
            "count_above_mean": None,
            "count_below_mean": None,
            "last_location_of_maximum": None,
            "first_location_of_minimum": None,
            "percentage_of_reoccurring_datapoints_to_all_datapoints": None,
            "percentage_of_reoccurring_values_to_all_values": None,
            "sum_of_reoccurring_data_points": None,
            "sum_of_reoccurring_values": None
        }
    
    start_time = datetime.now()
    
    # Extrair features
    features = extract_features(
        tsfresh_df,
        column_id='id',
        column_sort='time',
        column_value='value',
        default_fc_parameters=fc_parameters,
        impute_function=impute,
        n_jobs=1,  # Evitar problemas de multiprocessing
        show_warnings=False,
        disable_progressbar=False
    )
    
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\nTempo de extração: {elapsed:.1f} segundos")
    print(f"Features extraídas: {features.shape[1]}")
    print(f"Séries processadas: {features.shape[0]}")
    
    return features


def combine_period_features(features):
    """Combinar features de antes/depois e calcular diferenças."""
    print("\nCombinando features de períodos...")
    
    combined_data = []
    
    # Agrupar por série base
    for idx in features.index:
        if idx.endswith('_0'):  # Período antes
            base_id = idx.replace('_0', '')
            after_id = f"{base_id}_1"
            
            if after_id in features.index:
                row = {'id': int(base_id)}
                
                # Para cada feature
                for col in features.columns:
                    before_val = features.loc[idx, col]
                    after_val = features.loc[after_id, col]
                    
                    # Features básicas
                    row[f"{col}_before"] = before_val
                    row[f"{col}_after"] = after_val
                    
                    # Diferenças
                    row[f"{col}_diff"] = after_val - before_val
                    row[f"{col}_abs_diff"] = abs(after_val - before_val)
                    
                    # Ratios (com proteção contra divisão por zero)
                    if abs(before_val) > 1e-10:
                        ratio = after_val / before_val
                        row[f"{col}_ratio"] = np.clip(ratio, -100, 100)
                        row[f"{col}_log_ratio"] = np.log1p(abs(ratio)) * np.sign(ratio)
                    else:
                        row[f"{col}_ratio"] = 1.0
                        row[f"{col}_log_ratio"] = 0.0
                    
                    # Mudança percentual
                    if abs(before_val) > 1e-10:
                        row[f"{col}_pct_change"] = ((after_val - before_val) / abs(before_val)) * 100
                    else:
                        row[f"{col}_pct_change"] = 0.0
                
                combined_data.append(row)
    
    combined_df = pd.DataFrame(combined_data)
    print(f"Features combinadas: {combined_df.shape[1]} features para {combined_df.shape[0]} séries")
    
    return combined_df


def analyze_feature_relevance(features_df, y_train, id_mapping):
    """Análise detalhada de relevância das features."""
    print("\n" + "="*60)
    print("ANÁLISE DE RELEVÂNCIA")
    print("="*60)
    
    # Preparar labels
    y_mapped = []
    for idx in features_df['id']:
        original_id = id_mapping[idx]
        if original_id in y_train.index:
            y_mapped.append(y_train.loc[original_id, 'structural_breakpoint'])
        else:
            y_mapped.append(0)
    
    features_df['label'] = y_mapped
    
    # Separar features e labels
    feature_cols = [col for col in features_df.columns if col not in ['id', 'label']]
    X = features_df[feature_cols]
    y = features_df['label']
    
    print(f"\nDistribuição de classes:")
    print(f"Sem quebra: {(y == 0).sum()} ({(y == 0).mean():.1%})")
    print(f"Com quebra: {(y == 1).sum()} ({(y == 1).mean():.1%})")
    
    # Limpar dados
    print("\nLimpando dados...")
    # Remover colunas com muitos NaN
    nan_threshold = 0.5
    nan_ratio = X.isna().sum() / len(X)
    valid_cols = nan_ratio[nan_ratio < nan_threshold].index
    X = X[valid_cols]
    print(f"Colunas removidas por excesso de NaN: {len(feature_cols) - len(valid_cols)}")
    
    # Preencher NaN restantes
    X = X.fillna(X.median())
    
    # Remover colunas constantes
    constant_cols = X.columns[X.nunique() <= 1]
    X = X.drop(columns=constant_cols)
    print(f"Colunas constantes removidas: {len(constant_cols)}")
    
    # Substituir infinitos
    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.fillna(X.median())
    
    print(f"\nFeatures finais: {X.shape[1]}")
    
    return X, y, features_df


def evaluate_models(X, y):
    """Avaliar diferentes modelos com as features."""
    print("\n" + "="*60)
    print("AVALIAÇÃO DE MODELOS")
    print("="*60)
    
    # Normalizar dados
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Modelos para testar
    models = {
        'RandomForest': RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        ),
        'GradientBoosting': GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
    }
    
    # Cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    results = {}
    
    for name, model in models.items():
        print(f"\n{name}:")
        
        # ROC AUC scores
        scores = cross_val_score(model, X_scaled, y, cv=cv, scoring='roc_auc', n_jobs=-1)
        print(f"ROC AUC: {np.mean(scores):.3f} (+/- {np.std(scores):.3f})")
        
        # Treinar no conjunto completo para análise
        model.fit(X_scaled, y)
        
        # Feature importance
        if hasattr(model, 'feature_importances_'):
            importance = pd.DataFrame({
                'feature': X.columns,
                'importance': model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            print("\nTop 20 features:")
            for idx, row in importance.head(20).iterrows():
                print(f"  {row['feature']}: {row['importance']:.4f}")
            
            results[name] = {
                'scores': scores,
                'importance': importance,
                'model': model
            }
    
    return results


def visualize_results(X, y, results, features_df):
    """Criar visualizações detalhadas."""
    print("\n" + "="*60)
    print("GERANDO VISUALIZAÇÕES")
    print("="*60)
    
    # Preparar dados
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Criar figura principal
    fig = plt.figure(figsize=(20, 15))
    
    # 1. Feature Importance Comparison
    plt.subplot(3, 3, 1)
    for i, (name, res) in enumerate(results.items()):
        if 'importance' in res:
            top_features = res['importance'].head(10)
            plt.barh(np.arange(len(top_features)) + i*0.4, 
                    top_features['importance'],
                    height=0.4, 
                    label=name,
                    alpha=0.8)
    
    plt.yticks(np.arange(10) + 0.2, 
              [f[:30] + '...' if len(f) > 30 else f 
               for f in results[list(results.keys())[0]]['importance'].head(10)['feature']],
              fontsize=8)
    plt.xlabel('Importância')
    plt.title('Top 10 Features por Modelo')
    plt.legend()
    plt.gca().invert_yaxis()
    
    # 2. PCA Visualization
    plt.subplot(3, 3, 2)
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    scatter = plt.scatter(X_pca[:, 0], X_pca[:, 1], 
                         c=y, cmap='coolwarm', alpha=0.6, s=30)
    plt.colorbar(scatter, label='Quebra Estrutural')
    plt.xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%})')
    plt.ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%})')
    plt.title('PCA das Features TSFresh')
    
    # 3. t-SNE Visualization
    plt.subplot(3, 3, 3)
    print("Calculando t-SNE...")
    tsne = TSNE(n_components=2, random_state=42, perplexity=min(30, len(X)-1))
    X_tsne = tsne.fit_transform(X_scaled[:min(500, len(X))])
    scatter = plt.scatter(X_tsne[:, 0], X_tsne[:, 1], 
                         c=y[:min(500, len(y))], cmap='coolwarm', alpha=0.6, s=30)
    plt.colorbar(scatter, label='Quebra Estrutural')
    plt.xlabel('t-SNE 1')
    plt.ylabel('t-SNE 2')
    plt.title('t-SNE das Features TSFresh')
    
    # 4. Distribuição das top features por classe
    best_model = list(results.values())[0]
    top_features = best_model['importance'].head(6)['feature']
    
    for i, feature in enumerate(top_features):
        plt.subplot(3, 3, 4 + i)
        
        # Plotar distribuições
        data_no_break = X.loc[y == 0, feature]
        data_break = X.loc[y == 1, feature]
        
        # Remover outliers extremos para melhor visualização
        q99_no = np.percentile(data_no_break.dropna(), 99)
        q99_yes = np.percentile(data_break.dropna(), 99)
        q1_no = np.percentile(data_no_break.dropna(), 1)
        q1_yes = np.percentile(data_break.dropna(), 1)
        
        data_no_break_clean = data_no_break[(data_no_break >= q1_no) & (data_no_break <= q99_no)]
        data_break_clean = data_break[(data_break >= q1_yes) & (data_break <= q99_yes)]
        
        plt.hist([data_no_break_clean, data_break_clean], 
                bins=30, alpha=0.6, label=['Sem quebra', 'Com quebra'], density=True)
        plt.xlabel(feature[:40] + '...' if len(feature) > 40 else feature, fontsize=8)
        plt.ylabel('Densidade')
        plt.legend(fontsize=8)
        plt.title(f'Feature #{i+1}', fontsize=10)
    
    plt.tight_layout()
    plt.savefig('tsfresh_comprehensive_analysis.png', dpi=150, bbox_inches='tight')
    print("Visualização salva: tsfresh_comprehensive_analysis.png")
    
    # Segunda figura - Análise temporal
    fig2, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # 1. Importância por tipo de feature
    ax = axes[0, 0]
    feature_types = {}
    for feat in X.columns:
        # Extrair tipo da feature
        if '__' in feat:
            base_type = feat.split('__')[1].split('_')[0]
        else:
            base_type = feat.split('_')[-1]
        
        if base_type not in feature_types:
            feature_types[base_type] = []
        
        imp = best_model['importance'][best_model['importance']['feature'] == feat]['importance'].values
        if len(imp) > 0:
            feature_types[base_type].append(imp[0])
    
    # Calcular média por tipo
    type_importance = {k: np.mean(v) for k, v in feature_types.items() if len(v) > 0}
    type_importance = dict(sorted(type_importance.items(), key=lambda x: x[1], reverse=True)[:15])
    
    ax.bar(range(len(type_importance)), type_importance.values())
    ax.set_xticks(range(len(type_importance)))
    ax.set_xticklabels(type_importance.keys(), rotation=45, ha='right')
    ax.set_ylabel('Importância Média')
    ax.set_title('Importância por Tipo de Feature')
    
    # 2. Correlação entre top features
    ax = axes[0, 1]
    top_10_features = best_model['importance'].head(10)['feature']
    corr_matrix = X[top_10_features].corr()
    sns.heatmap(corr_matrix, cmap='coolwarm', center=0, 
                xticklabels=[f[:15] for f in top_10_features],
                yticklabels=[f[:15] for f in top_10_features],
                ax=ax, cbar_kws={'label': 'Correlação'})
    ax.set_title('Correlação entre Top 10 Features')
    
    # 3. Evolução das métricas
    ax = axes[1, 0]
    for name, res in results.items():
        scores = res['scores']
        ax.plot(range(len(scores)), scores, 'o-', label=f"{name} ({np.mean(scores):.3f})", markersize=8)
    
    ax.axhline(0.5, color='red', linestyle='--', alpha=0.5, label='Baseline (0.5)')
    ax.set_xlabel('Fold')
    ax.set_ylabel('ROC AUC')
    ax.set_title('Performance por Fold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 4. Análise de features por transformação
    ax = axes[1, 1]
    transform_types = ['diff', 'ratio', 'pct_change', 'before', 'after']
    transform_importance = {}
    
    for transform in transform_types:
        transform_feats = [f for f in X.columns if f.endswith(f'_{transform}')]
        if transform_feats:
            imp_values = best_model['importance'][
                best_model['importance']['feature'].isin(transform_feats)
            ]['importance'].values
            if len(imp_values) > 0:
                transform_importance[transform] = {
                    'mean': np.mean(imp_values),
                    'max': np.max(imp_values),
                    'count': len(imp_values)
                }
    
    if transform_importance:
        transforms = list(transform_importance.keys())
        means = [transform_importance[t]['mean'] for t in transforms]
        maxs = [transform_importance[t]['max'] for t in transforms]
        
        x = np.arange(len(transforms))
        width = 0.35
        
        ax.bar(x - width/2, means, width, label='Média', alpha=0.8)
        ax.bar(x + width/2, maxs, width, label='Máximo', alpha=0.8)
        
        ax.set_xlabel('Tipo de Transformação')
        ax.set_ylabel('Importância')
        ax.set_xticks(x)
        ax.set_xticklabels(transforms)
        ax.set_title('Importância por Tipo de Transformação')
        ax.legend()
    
    plt.tight_layout()
    plt.savefig('tsfresh_detailed_analysis.png', dpi=150, bbox_inches='tight')
    print("Análise detalhada salva: tsfresh_detailed_analysis.png")
    
    plt.close('all')


def save_results(X, y, features_df, results, id_mapping):
    """Salvar resultados para uso posterior."""
    print("\n" + "="*60)
    print("SALVANDO RESULTADOS")
    print("="*60)
    
    # Salvar features
    features_df.to_parquet('tsfresh_all_features.parquet')
    print("Features completas salvas: tsfresh_all_features.parquet")
    
    # Salvar features limpas
    X_clean = X.copy()
    X_clean['label'] = y
    X_clean['id'] = features_df['id']
    X_clean.to_parquet('tsfresh_clean_features.parquet')
    print("Features limpas salvas: tsfresh_clean_features.parquet")
    
    # Salvar relatório
    with open('tsfresh_comprehensive_report.txt', 'w') as f:
        f.write("="*60 + "\n")
        f.write("RELATÓRIO COMPLETO - TSFRESH ANALYSIS\n")
        f.write("="*60 + "\n\n")
        
        f.write(f"Total de séries processadas: {len(id_mapping)}\n")
        f.write(f"Features extraídas inicialmente: {features_df.shape[1]}\n")
        f.write(f"Features após limpeza: {X.shape[1]}\n")
        f.write(f"Taxa de quebra estrutural: {y.mean():.1%}\n\n")
        
        for name, res in results.items():
            f.write(f"\n{name}:\n")
            f.write(f"ROC AUC: {np.mean(res['scores']):.3f} (+/- {np.std(res['scores']):.3f})\n")
            f.write("\nTop 30 features:\n")
            for idx, row in res['importance'].head(30).iterrows():
                f.write(f"  {row['feature']}: {row['importance']:.4f}\n")
        
        # Análise por tipo de transformação
        f.write("\n\nANÁLISE POR TIPO DE TRANSFORMAÇÃO:\n")
        f.write("-"*40 + "\n")
        
        for transform in ['diff', 'ratio', 'pct_change', 'log_ratio', 'abs_diff']:
            transform_feats = [f for f in X.columns if f.endswith(f'_{transform}')]
            if transform_feats and 'importance' in results[list(results.keys())[0]]:
                importance_df = results[list(results.keys())[0]]['importance']
                transform_imp = importance_df[importance_df['feature'].isin(transform_feats)]
                
                if len(transform_imp) > 0:
                    f.write(f"\n{transform.upper()}:\n")
                    f.write(f"  Total features: {len(transform_feats)}\n")
                    f.write(f"  Importância média: {transform_imp['importance'].mean():.4f}\n")
                    f.write(f"  Importância máxima: {transform_imp['importance'].max():.4f}\n")
                    f.write(f"  Top 5:\n")
                    for idx, row in transform_imp.head(5).iterrows():
                        f.write(f"    - {row['feature']}: {row['importance']:.4f}\n")
    
    print("Relatório salvo: tsfresh_comprehensive_report.txt")
    
    # Salvar melhores features para uso rápido
    best_model = results[list(results.keys())[0]]
    top_features = best_model['importance'].head(100)['feature'].tolist()
    
    X_best = X[top_features].copy()
    X_best['label'] = y
    X_best.to_parquet('tsfresh_top100_features.parquet')
    print("Top 100 features salvas: tsfresh_top100_features.parquet")


def main():
    """Executar análise completa do TSFresh."""
    print("="*60)
    print("TSFRESH COMPREHENSIVE ANALYSIS")
    print("="*60)
    
    # Carregar dados
    print("\nCarregando dados...")
    X_train = pd.read_parquet('database/X_train.parquet').reset_index()
    y_train = pd.read_parquet('database/y_train.parquet')
    
    # Usar mais dados
    sample_size = 2000  # Aumentar significativamente
    print(f"Usando {sample_size} séries para análise")
    
    # Preparar dados
    tsfresh_df, id_mapping = prepare_tsfresh_data(X_train, sample_size)
    
    # Extrair features - Comprehensive
    features_comprehensive = extract_all_features(tsfresh_df, 'comprehensive')
    
    # Combinar períodos
    combined_features = combine_period_features(features_comprehensive)
    
    # Análise de relevância
    X, y, features_df = analyze_feature_relevance(combined_features, y_train, id_mapping)
    
    # Avaliar modelos
    results = evaluate_models(X, y)
    
    # Visualizar
    visualize_results(X, y, results, features_df)
    
    # Salvar resultados
    save_results(X, y, features_df, results, id_mapping)
    
    print("\n" + "="*60)
    print("ANÁLISE COMPLETA FINALIZADA!")
    print("="*60)
    print("\nArquivos gerados:")
    print("- tsfresh_comprehensive_analysis.png")
    print("- tsfresh_detailed_analysis.png")
    print("- tsfresh_comprehensive_report.txt")
    print("- tsfresh_all_features.parquet")
    print("- tsfresh_clean_features.parquet")
    print("- tsfresh_top100_features.parquet")


if __name__ == "__main__":
    main()