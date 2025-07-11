"""
Test TSFresh - versão robusta com tratamento de índices
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sys
sys.path.append('src')

from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler


def test_tsfresh_robust():
    """Test TSFresh com tratamento robusto de índices."""
    
    try:
        from tsfresh import extract_features, select_features
        from tsfresh.feature_extraction import MinimalFCParameters
        from tsfresh.utilities.dataframe_functions import impute
    except ImportError:
        print("TSFresh não instalado!")
        return
    
    print("="*60)
    print("TSFRESH ANÁLISE ROBUSTA")
    print("="*60)
    
    # Carregar dados
    print("\nCarregando dados...")
    X_train = pd.read_parquet('database/X_train.parquet').reset_index()
    y_train = pd.read_parquet('database/y_train.parquet')
    y_train = y_train.rename(columns={'structural_breakpoint': 'label'})
    
    # Amostra menor para teste
    sample_size = 100
    unique_ids = X_train['id'].unique()[:sample_size]
    X_sample = X_train[X_train['id'].isin(unique_ids)]
    
    print(f"Processando {sample_size} séries...")
    print(f"Taxa de quebra: {y_train.loc[unique_ids, 'label'].mean():.2%}")
    
    # Preparar dados para TSFresh
    print("\nPreparando dados para TSFresh...")
    df_list = []
    
    for series_id in unique_ids:
        series_data = X_sample[X_sample['id'] == series_id]
        
        # Separar antes/depois
        before = series_data[series_data['period'] == 0].copy()
        after = series_data[series_data['period'] == 1].copy()
        
        # Criar IDs únicos
        before_id = f"id_{series_id}_before"
        after_id = f"id_{series_id}_after"
        
        before['id'] = before_id
        after['id'] = after_id
        
        before['time'] = range(len(before))
        after['time'] = range(len(after))
        
        df_list.extend([
            before[['id', 'time', 'value']], 
            after[['id', 'time', 'value']]
        ])
    
    tsfresh_data = pd.concat(df_list, ignore_index=True)
    
    # Extrair features
    print("\nExtraindo features...")
    features = extract_features(
        tsfresh_data,
        column_id='id',
        column_sort='time',
        default_fc_parameters=MinimalFCParameters(),
        impute_function=impute,
        n_jobs=1,
        show_warnings=False,
        disable_progressbar=False
    )
    
    print(f"Features extraídas: {features.shape}")
    
    # Combinar before/after
    print("\nCombinando features before/after...")
    combined_list = []
    
    for series_id in unique_ids:
        before_id = f"id_{series_id}_before"
        after_id = f"id_{series_id}_after"
        
        if before_id in features.index and after_id in features.index:
            row = {'series_id': series_id}
            
            # Calcular diferenças para cada feature
            for col in features.columns:
                before_val = features.loc[before_id, col]
                after_val = features.loc[after_id, col]
                
                row[f"{col}_diff"] = after_val - before_val
                row[f"{col}_ratio"] = after_val / before_val if before_val != 0 else 0
                row[f"{col}_before"] = before_val
                row[f"{col}_after"] = after_val
            
            combined_list.append(row)
    
    combined_df = pd.DataFrame(combined_list)
    print(f"Features combinadas: {combined_df.shape}")
    
    # Preparar labels
    y_combined = []
    for series_id in combined_df['series_id']:
        if series_id in y_train.index:
            y_combined.append(y_train.loc[series_id, 'label'])
        else:
            y_combined.append(0)  # Default
    
    combined_df['label'] = y_combined
    
    # Análise de features
    print("\nAnálise de features mais discriminativas...")
    
    # Selecionar features numéricas
    feature_cols = [col for col in combined_df.columns 
                   if col not in ['series_id', 'label']]
    
    X = combined_df[feature_cols]
    y = combined_df['label']
    
    # Remover NaN e infinitos
    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.fillna(X.median())
    
    # Importância das features
    rf = RandomForestClassifier(n_estimators=50, random_state=42)
    rf.fit(X, y)
    
    importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': rf.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\nTop 10 features mais importantes:")
    for i, row in importance.head(10).iterrows():
        print(f"{row['feature']}: {row['importance']:.4f}")
    
    # Validação cruzada
    print("\nValidação cruzada...")
    scores = cross_val_score(rf, X, y, cv=5, scoring='roc_auc')
    print(f"ROC AUC: {np.mean(scores):.3f} (+/- {np.std(scores):.3f})")
    
    # Visualização
    plt.figure(figsize=(12, 8))
    
    # Top features
    plt.subplot(2, 2, 1)
    top_features = importance.head(15)
    plt.barh(range(len(top_features)), top_features['importance'])
    plt.yticks(range(len(top_features)), 
               [f[:30] + '...' if len(f) > 30 else f for f in top_features['feature']])
    plt.xlabel('Importância')
    plt.title('Top 15 Features Mais Importantes')
    plt.gca().invert_yaxis()
    
    # Distribuição de uma feature importante
    plt.subplot(2, 2, 2)
    best_feature = importance.iloc[0]['feature']
    plt.hist([X[y==0][best_feature], X[y==1][best_feature]], 
             bins=20, alpha=0.7, label=['Sem quebra', 'Com quebra'])
    plt.xlabel(best_feature[:40])
    plt.ylabel('Frequência')
    plt.legend()
    plt.title('Distribuição da Feature Mais Importante')
    
    # PCA
    from sklearn.decomposition import PCA
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    
    plt.subplot(2, 2, 3)
    scatter = plt.scatter(X_pca[:, 0], X_pca[:, 1], c=y, cmap='coolwarm', alpha=0.6)
    plt.colorbar(scatter, label='Tem quebra')
    plt.xlabel('PC1')
    plt.ylabel('PC2')
    plt.title('PCA das Features TSFresh')
    
    # Matriz de correlação das top features
    plt.subplot(2, 2, 4)
    top_10_cols = importance.head(10)['feature'].tolist()
    corr_matrix = X[top_10_cols].corr()
    sns.heatmap(corr_matrix, cmap='coolwarm', center=0, 
                xticklabels=[c[:15] for c in top_10_cols],
                yticklabels=[c[:15] for c in top_10_cols])
    plt.title('Correlação entre Top 10 Features')
    
    plt.tight_layout()
    plt.savefig('tsfresh_analysis_robust.png', dpi=150)
    plt.close()
    
    print("\nAnálise salva em tsfresh_analysis_robust.png")
    
    # Salvar features para uso posterior
    combined_df.to_parquet('features_tsfresh.parquet')
    print("Features salvas em features_tsfresh.parquet")
    
    print("\n" + "="*60)
    print("ANÁLISE CONCLUÍDA COM SUCESSO!")
    print("="*60)


if __name__ == "__main__":
    test_tsfresh_robust()