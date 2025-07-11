#!/usr/bin/env python3
"""
Calcula o ROC-AUC real usando as features de Lévy já extraídas.
"""

print("\n" + "="*60)
print("CÁLCULO ROC-AUC - FEATURES DE LÉVY")
print("="*60)

try:
    import pandas as pd
    import numpy as np
    from sklearn.model_selection import cross_val_score, StratifiedKFold
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import roc_auc_score
    import glob
    
    # 1. Carregar features
    print("\n📊 Carregando features de Lévy...")
    levy_files = glob.glob('database/levy_features_*.parquet')
    if not levy_files:
        print("❌ Nenhum arquivo encontrado!")
        exit(1)
    
    latest_levy = sorted(levy_files)[-1]
    print(f"   Arquivo: {latest_levy}")
    
    df = pd.read_parquet(latest_levy)
    print(f"   Shape: {df.shape}")
    
    # 2. Preparar dados
    feature_cols = [col for col in df.columns if col.startswith('levy_')]
    X = df[feature_cols]
    y = df['label'].astype(int)
    
    print(f"\n📊 Dados:")
    print(f"   Features: {len(feature_cols)}")
    print(f"   Amostras: {len(X)}")
    print(f"   Classe 0: {sum(y==0)} ({sum(y==0)/len(y)*100:.1f}%)")
    print(f"   Classe 1: {sum(y==1)} ({sum(y==1)/len(y)*100:.1f}%)")
    
    # Tratar NaN
    X = X.fillna(X.mean())
    
    # 3. Cross-validation com RandomForest
    print("\n🎯 Treinando RandomForest com cross-validation...")
    
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(rf, X, y, cv=cv, scoring='roc_auc', n_jobs=-1)
    
    print(f"\n📊 Resultados Cross-Validation (5-fold):")
    print(f"   ROC-AUC por fold: {scores.round(4)}")
    print(f"   ROC-AUC médio: {scores.mean():.4f} (±{scores.std():.4f})")
    
    # 4. Comparar com benchmarks
    roc_auc_levy = scores.mean()
    
    print("\n📈 COMPARAÇÃO COM BENCHMARKS:")
    print("-"*50)
    print(f"TSFresh + RF:     0.607")
    print(f"Lévy + RF:        {roc_auc_levy:.3f} {'✓' if roc_auc_levy > 0.550 else ''}")
    print(f"ML-kNN (online):  0.550")
    print(f"Outros online:    0.532-0.536")
    
    if roc_auc_levy > 0.607:
        print("\n✅ SUPERA o benchmark TSFresh!")
    elif roc_auc_levy > 0.550:
        print("\n✅ Supera todos os métodos online!")
    else:
        print("\n⚠️  Performance abaixo do esperado")
    
    print("\n" + "="*60)
    print(f"ROC-AUC FINAL: {roc_auc_levy:.4f}")
    print("="*60)
    
except ImportError as e:
    print(f"\n❌ Erro de importação: {e}")
    print("\nInstalando dependências necessárias...")
    import subprocess
    subprocess.run(['pip', 'install', 'pandas', 'scikit-learn'])
    print("\nExecute o script novamente após a instalação.")
except Exception as e:
    print(f"\n❌ Erro: {e}")
    print("\nVerifique se o arquivo de features existe em database/")