"""
Script Python para instalar TSFresh
"""

import subprocess
import sys

def install_tsfresh():
    """Instalar TSFresh e dependências."""
    
    print("="*60)
    print("INSTALANDO TSFRESH")
    print("="*60)
    
    packages = [
        'tsfresh>=0.20.0',
        'pandas>=1.3.0',
        'numpy>=1.21.0',
        'scipy>=1.7.0',
        'scikit-learn>=0.24.0',
        'statsmodels>=0.12.0',
        'patsy>=0.5.1',
        'distributed>=2021.10.0',
        'dask>=2021.10.0'
    ]
    
    for package in packages:
        print(f"\nInstalando {package}...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✓ {package} instalado com sucesso")
        except Exception as e:
            print(f"✗ Erro ao instalar {package}: {e}")
    
    print("\n" + "="*60)
    print("VERIFICANDO INSTALAÇÃO")
    print("="*60)
    
    try:
        import tsfresh
        print(f"✓ TSFresh versão {tsfresh.__version__} instalado com sucesso!")
        
        # Testar importações básicas
        from tsfresh import extract_features, select_features
        from tsfresh.feature_extraction import ComprehensiveFCParameters
        print("✓ Todas as importações funcionando!")
        
        print("\n" + "="*60)
        print("INSTALAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*60)
        print("\nAgora você pode executar:")
        print("python test_tsfresh.py")
        
    except ImportError as e:
        print(f"✗ Erro ao importar TSFresh: {e}")
        print("\nTente instalar manualmente com:")
        print("pip install tsfresh")

if __name__ == "__main__":
    install_tsfresh()