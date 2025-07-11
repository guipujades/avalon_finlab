# Sistema CVM Downloads

## Scripts Essenciais (apenas estes!)

1. **`cvm_download_principal.py`** - Menu principal (USE ESTE!)
2. **`00_cvm_extrator_dados_ipe.py`** - Baixa registro de empresas
3. **`01_cvm_download_releases_multiplas_empresas.py`** - Baixa PDFs 
4. **`02_cvm_download_documentos_estruturados.py`** - Baixa ITR/DFP

## Como Usar

### 1. Instalar dependências
```bash
pip install pandas selenium webdriver-manager requests
```

### 2. Executar o menu principal
```bash
python cvm_download_principal.py
```

### 3. Seguir esta ordem:
1. **Opção 1**: Baixar registro de empresas (fazer primeiro!)
2. **Opção 3**: Baixar apenas Earnings Releases (PDFs)
3. **Opção 5**: Baixar ITR/DFP estruturados (se precisar)

## Pastas de Saída

- `documents/pending/` - Releases trimestrais (Earnings Releases)
- `documents/residuals/` - Outros documentos
- `documents/cvm_estruturados/` - ITR/DFP em formato CSV

## Exemplo Rápido

```bash
# No menu principal:
Opção: 1  # Baixar registro
Ano: 2025

Opção: 3  # Earnings Releases apenas
Empresas: VALE, PETROBRAS, ITAU
Anos: 2025
```

Pronto! Os PDFs estarão em `documents/pending/`