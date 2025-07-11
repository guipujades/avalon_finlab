import pandas as pd
import numpy as np

print("Testando carregamento dos dados...")

try:
    X_train = pd.read_parquet('database/X_train.parquet')
    y_train = pd.read_parquet('database/y_train.parquet')
    
    print(f"✓ Dados carregados com sucesso!")
    print(f"  - Total de séries: {len(X_train['id'].unique())}")
    print(f"  - Taxa de quebras: {y_train['label'].mean():.2%}")
    print(f"  - Colunas em X_train: {list(X_train.columns)}")
    
    sample_id = X_train['id'].unique()[0]
    sample = X_train[X_train['id'] == sample_id]
    print(f"\n✓ Exemplo de série {sample_id}:")
    print(f"  - Tamanho: {len(sample)} pontos")
    print(f"  - Pontos antes: {len(sample[sample['period']==0])}")
    print(f"  - Pontos depois: {len(sample[sample['period']==1])}")
    
    print("\nTudo pronto para rodar main.py!")
    
except Exception as e:
    print(f"✗ Erro: {e}")
    print("\nVerifique se está no diretório correto e se instalou pyarrow")