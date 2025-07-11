# 🎯 GUIA PASSO A PASSO - Downloads CVM

## Objetivo Final
1. **ITR 2025 estruturados** (dados em CSV)
2. **PDFs da VALE 2025** (Earnings Releases)

---

## PASSO 1: Verificar se tem o arquivo IPE
```bash
# No terminal, verificar se existe:
ls ipe_cia_aberta_2025.csv
```

✅ Se existir, pule para o PASSO 2
❌ Se não existir:
```bash
python 00_cvm_extrator_dados_ipe.py
# Digite: 2025
# Aguarde download (~30 segundos)
```

---

## PASSO 2: Baixar Earnings Releases da VALE (PDFs)
```bash
python cvm_download_principal.py
```

No menu:
1. Escolha opção: **3** (Apenas releases trimestrais)
2. Empresas: **VALE**
3. Anos: **2025**
4. Limite: **Enter** (para todos)
5. Modo invisível: **S**

⏱️ Tempo estimado: 2-3 minutos

📁 Os PDFs estarão em: `documents/pending/`

Você verá arquivos como:
- `VALE_20250424_Desempenho_da_Vale_no_1T25.pdf`
- `VALE_20250219_Desempenho_da_Vale_no_4T24_e_2024.pdf`

---

## PASSO 3: Baixar ITR 2025 Estruturados (CSV)
```bash
python cvm_download_principal.py
```

No menu:
1. Escolha opção: **5** (Baixar ITR/DFP estruturados)
2. Tipos: **ITR**
3. Anos: **2025**
4. Confirmar: **S**

⏱️ Tempo estimado: 1-2 minutos

📁 Os arquivos estarão em: `documents/cvm_estruturados/ITR/`

Você verá:
- `itr_cia_aberta_2025.zip`
- Pasta `itr_cia_aberta_2025/` com vários CSVs

---

## RESUMO RÁPIDO (copie e cole)

```bash
# 1. Se não tem IPE:
python 00_cvm_extrator_dados_ipe.py

# 2. PDFs da VALE:
python cvm_download_principal.py
# Opção 3 → VALE → 2025 → Enter → S

# 3. ITR estruturados:
python cvm_download_principal.py
# Opção 5 → ITR → 2025 → S
```

---

## RESULTADO FINAL

✅ **PDFs da VALE em:** `documents/pending/`
- Desempenho da Vale no 1T25.pdf
- Desempenho da Vale no 4T24.pdf
- etc...

✅ **ITR 2025 em:** `documents/cvm_estruturados/ITR/`
- Dados completos de todas empresas
- Formato CSV para análise

---

## PROBLEMAS COMUNS

**"Chrome not found"**
→ O script vai baixar automaticamente o driver

**"Arquivo IPE não encontrado"**
→ Execute o passo 1 primeiro

**"Permission denied"**
→ Execute como administrador ou use `sudo` no Linux