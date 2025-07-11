import sys

packages = {
    'numpy': 'numpy',
    'pandas': 'pandas', 
    'scipy': 'scipy',
    'matplotlib': 'matplotlib',
    'seaborn': 'seaborn',
    'sklearn': 'scikit-learn'
}

missing = []

for module, package in packages.items():
    try:
        __import__(module)
        print(f"✓ {package} instalado")
    except ImportError:
        print(f"✗ {package} NÃO instalado")
        missing.append(package)

if missing:
    print(f"\nPacotes faltando: {', '.join(missing)}")
    print("\nPara instalar no Windows, abra o PowerShell ou CMD e execute:")
    print(f"pip install {' '.join(missing)}")
else:
    print("\nTodos os pacotes estão instalados!")
    
try:
    import pyarrow
    print("✓ pyarrow instalado")
except ImportError:
    print("✗ pyarrow NÃO instalado (necessário para ler parquet)")
    print("pip install pyarrow")