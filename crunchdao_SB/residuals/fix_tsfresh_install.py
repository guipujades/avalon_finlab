"""
Script para corrigir instalação do TSFresh
"""

import subprocess
import sys

def fix_installation():
    """Corrigir instalação do TSFresh."""
    
    print("="*60)
    print("CORRIGINDO INSTALAÇÃO DO TSFRESH")
    print("="*60)
    
    # Primeiro instalar setuptools que contém pkg_resources
    essential_packages = [
        'setuptools',
        'wheel',
        'pip --upgrade'
    ]
    
    print("\n1. Instalando pacotes essenciais...")
    for package in essential_packages:
        print(f"\nInstalando {package}...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + package.split())
            print(f"✓ {package} instalado")
        except Exception as e:
            print(f"✗ Erro: {e}")
    
    # Agora instalar TSFresh
    print("\n2. Instalando TSFresh e dependências...")
    tsfresh_packages = [
        'numpy',
        'pandas',
        'scipy',
        'scikit-learn',
        'tsfresh'
    ]
    
    for package in tsfresh_packages:
        print(f"\nInstalando {package}...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✓ {package} instalado")
        except Exception as e:
            print(f"✗ Erro: {e}")
    
    print("\n" + "="*60)
    print("VERIFICANDO INSTALAÇÃO")
    print("="*60)
    
    try:
        import pkg_resources
        print("✓ pkg_resources funcionando")
        
        import tsfresh
        print(f"✓ TSFresh versão {tsfresh.__version__} instalado com sucesso!")
        
        print("\n" + "="*60)
        print("INSTALAÇÃO CORRIGIDA COM SUCESSO!")
        print("="*60)
        print("\nAgora execute:")
        print("python test_tsfresh.py")
        
    except ImportError as e:
        print(f"✗ Erro: {e}")
        print("\nSe continuar com erro, tente:")
        print("1. pip install --upgrade setuptools")
        print("2. pip install tsfresh")

if __name__ == "__main__":
    fix_installation()