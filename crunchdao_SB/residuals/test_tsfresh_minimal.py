"""
Test TSFresh minimal - versão simplificada sem multiprocessing
"""

import pandas as pd
import numpy as np
import sys
sys.path.append('src')

from features.tsfresh_extractor import TSFreshExtractor, create_tsfresh_report, TSFRESH_AVAILABLE


def test_minimal():
    """Teste mínimo do TSFresh."""
    
    if not TSFRESH_AVAILABLE:
        print("TSFresh não instalado!")
        return
    
    print("="*60)
    print("TESTE MÍNIMO TSFRESH")
    print("="*60)
    
    # Criar dados sintéticos simples
    print("\nCriando dados sintéticos...")
    
    # Criar 10 séries temporais simples
    data_list = []
    labels = []
    
    for i in range(10):
        # Série com 100 pontos
        t = np.arange(100)
        
        # Metade com quebra, metade sem
        if i < 5:
            # Com quebra estrutural
            value = np.concatenate([
                np.sin(t[:50] * 0.1) + np.random.normal(0, 0.1, 50),
                np.sin(t[50:] * 0.1) + 2 + np.random.normal(0, 0.1, 50)  # Mudança de nível
            ])
            labels.append(1)
        else:
            # Sem quebra
            value = np.sin(t * 0.1) + np.random.normal(0, 0.1, 100)
            labels.append(0)
        
        # Formato TSFresh
        for j, v in enumerate(value[:50]):
            data_list.append({
                'id': f"{i}_before",
                'time': j,
                'value': v
            })
        
        for j, v in enumerate(value[50:]):
            data_list.append({
                'id': f"{i}_after", 
                'time': j,
                'value': v
            })
    
    df_tsfresh = pd.DataFrame(data_list)
    print(f"Dados criados: {len(df_tsfresh)} pontos")
    
    # Extrair features com n_jobs=1 para evitar problemas de multiprocessing
    print("\nExtraindo features (sem paralelização)...")
    
    try:
        from tsfresh import extract_features
        from tsfresh.feature_extraction import MinimalFCParameters
        
        features = extract_features(
            df_tsfresh,
            column_id='id',
            column_sort='time',
            default_fc_parameters=MinimalFCParameters(),
            n_jobs=1,  # Sem paralelização
            show_warnings=False,
            disable_progressbar=True
        )
        
        print(f"\nFeatures extraídas: {features.shape}")
        print(f"Primeiras features:\n{features.columns[:10].tolist()}")
        
        # Combinar before/after
        print("\nCombinando features before/after...")
        
        combined_list = []
        for i in range(10):
            before_id = f"{i}_before"
            after_id = f"{i}_after"
            
            if before_id in features.index and after_id in features.index:
                row = {'id': i, 'label': labels[i]}
                
                for col in features.columns[:5]:  # Apenas primeiras 5 features
                    row[f"{col}_diff"] = features.loc[after_id, col] - features.loc[before_id, col]
                
                combined_list.append(row)
        
        result_df = pd.DataFrame(combined_list)
        print(f"\nResultado final: {result_df.shape}")
        print(result_df.head())
        
        # Teste de classificação simples
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import cross_val_score
        
        X = result_df.drop(['id', 'label'], axis=1)
        y = result_df['label']
        
        clf = RandomForestClassifier(n_estimators=10, random_state=42)
        scores = cross_val_score(clf, X, y, cv=3)
        
        print(f"\nAcurácia média: {np.mean(scores):.2f}")
        
        print("\n" + "="*60)
        print("TESTE CONCLUÍDO COM SUCESSO!")
        print("="*60)
        
    except Exception as e:
        print(f"\nErro: {e}")
        print("\nTente instalar versão específica:")
        print("pip install tsfresh==0.20.1")


if __name__ == "__main__":
    test_minimal()