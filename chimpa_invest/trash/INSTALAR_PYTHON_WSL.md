# Guia de Instalação Python e Bibliotecas no WSL

## 1. Atualizar o sistema
```bash
sudo apt update
sudo apt upgrade -y
```

## 2. Instalar Python e pip
```bash
# Instalar Python 3 e pip
sudo apt install python3 python3-pip python3-venv -y

# Instalar ferramentas de desenvolvimento (necessário para algumas bibliotecas)
sudo apt install python3-dev build-essential -y
```

## 3. Verificar instalação
```bash
python3 --version
pip3 --version
```

## 4. Instalar bibliotecas globalmente (para todos os usuários)
```bash
# Opção 1: Instalar via pip (recomendado)
sudo pip3 install pandas requests tqdm openpyxl numpy matplotlib seaborn

# Opção 2: Instalar via apt (versões do sistema)
sudo apt install python3-pandas python3-requests python3-tqdm python3-openpyxl -y
```

## 5. Criar alias para python (opcional)
```bash
# Adicionar ao arquivo ~/.bashrc
echo "alias python=python3" >> ~/.bashrc
echo "alias pip=pip3" >> ~/.bashrc

# Recarregar configurações
source ~/.bashrc
```

## 6. Testar instalação
```bash
# Criar script de teste
cat > test_libs.py << 'EOF'
import sys
print(f"Python: {sys.version}")

try:
    import pandas as pd
    print(f"✓ pandas {pd.__version__}")
except ImportError:
    print("✗ pandas não instalado")

try:
    import requests
    print(f"✓ requests {requests.__version__}")
except ImportError:
    print("✗ requests não instalado")

try:
    import tqdm
    print(f"✓ tqdm {tqdm.__version__}")
except ImportError:
    print("✗ tqdm não instalado")

try:
    import numpy as np
    print(f"✓ numpy {np.__version__}")
except ImportError:
    print("✗ numpy não instalado")
EOF

# Executar teste
python3 test_libs.py
```

## 7. Configurar pip para não dar warnings
```bash
# Criar arquivo de configuração pip
mkdir -p ~/.config/pip
cat > ~/.config/pip/pip.conf << 'EOF'
[global]
break-system-packages = true
user = false
EOF
```

## 8. Instalar bibliotecas adicionais úteis para análise de dados
```bash
# Bibliotecas para ciência de dados
sudo pip3 install jupyter notebook ipython scikit-learn

# Bibliotecas para web scraping
sudo pip3 install beautifulsoup4 selenium lxml

# Bibliotecas para trabalhar com APIs
sudo pip3 install httpx aiohttp

# Bibliotecas para visualização
sudo pip3 install plotly dash
```

## 9. Comandos úteis

### Listar bibliotecas instaladas
```bash
pip3 list
```

### Atualizar uma biblioteca
```bash
sudo pip3 install --upgrade pandas
```

### Instalar versão específica
```bash
sudo pip3 install pandas==2.0.0
```

### Desinstalar biblioteca
```bash
sudo pip3 uninstall pandas
```

## 10. Solução de problemas comuns

### Erro: "externally-managed-environment"
```bash
# Opção 1: Usar --break-system-packages
sudo pip3 install pandas --break-system-packages

# Opção 2: Usar ambiente virtual (recomendado para projetos)
python3 -m venv venv
source venv/bin/activate
pip install pandas requests tqdm
```

### Erro: "Permission denied"
```bash
# Sempre use sudo para instalação global
sudo pip3 install [biblioteca]
```

### Erro: "No module named pip"
```bash
# Reinstalar pip
sudo apt install --reinstall python3-pip
```

## Instalação Rápida (copie e cole)

```bash
# Comando único para instalar tudo
sudo apt update && \
sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential && \
sudo pip3 install --break-system-packages pandas requests tqdm openpyxl numpy matplotlib seaborn jupyter && \
echo "alias python=python3" >> ~/.bashrc && \
echo "alias pip=pip3" >> ~/.bashrc && \
source ~/.bashrc && \
echo "Instalação concluída!"
```

## Verificar se tudo está funcionando

Após a instalação, você pode usar Python e as bibliotecas em qualquer pasta:

```bash
cd /qualquer/pasta
python3 -c "import pandas, requests, tqdm; print('Todas as bibliotecas estão funcionando!')"
```