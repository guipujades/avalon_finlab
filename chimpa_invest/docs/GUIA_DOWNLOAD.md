# GUIA COMPLETO DE DOWNLOAD AUTOMÁTICO

## 🎯 Visão Geral

Este guia explica como usar o sistema de download automático para baixar documentos reais (PDFs) da CVM para sua máquina.

## 📥 Como Funciona o Download

### **1. Processo Automático**
```
1. Sistema extrai metadados dos documentos
2. Identifica URLs de download da CVM
3. Baixa arquivos PDF automaticamente
4. Organiza em pastas estruturadas
5. Gera relatórios detalhados
```

### **2. Estrutura de Pastas**
```
documentos_cvm_completos/
├── [EMPRESA]/
│   ├── [ANO]/
│   │   ├── Fato_Relevante/
│   │   ├── Comunicado_ao_Mercado/
│   │   ├── ITR/
│   │   └── Assembleia/
```

### **3. Nomenclatura dos Arquivos**
```
Formato: [DATA]_[CATEGORIA]_[ASSUNTO]_[PROTOCOLO].pdf
Exemplo: 20240307_Fato_Relevante_Dividendos_ABC123.pdf
```

## 🚀 Guia Passo a Passo

### **Passo 1: Executar Sistema**
```bash
python sistema_cvm_completo.py
```

### **Passo 2: Escolher Opção**
```
1. 🏢 Processar empresa específica (metadados + download)
```

### **Passo 3: Configurar Download**
```
Digite o nome da empresa: PETROBRAS
Ano dos documentos (2024): 2024

Tipos de documento a processar:
1. Todos os tipos
2. Apenas fatos relevantes  ← Recomendado para teste
3. Apenas comunicados
4. Apenas ITRs
5. Personalizado

Escolha (1-5): 2

Limite de documentos por tipo (ENTER = sem limite): 5
Baixar arquivos reais (PDFs)? (S/n): S
```

### **Passo 4: Acompanhar Download**
```
📊 Extraindo metadados de PETROBRAS...
✅ Metadados extraídos: 385 documentos
   🚨 Fatos relevantes: 37

📥 Iniciando downloads de PETROBRAS...
   📋 Tipos: fatos_relevantes
   🔢 Limite por tipo: 5

📄 Baixando 5 documentos do tipo: fatos_relevantes
     1/5: ✅ 20240307_Fato_Relevante_Dividendos_ABC123.pdf
     2/5: ✅ 20240315_Fato_Relevante_Resultados_DEF456.pdf
     3/5: ✅ 20240322_Fato_Relevante_Producao_GHI789.pdf
     4/5: ❌ Erro: URL retornou HTML (possível erro)
     5/5: ✅ 20240401_Fato_Relevante_Vendas_JKL012.pdf

📊 Resumo para PETROBRAS:
   ✅ Sucessos: 4
   ❌ Erros: 1
   📁 Já existiam: 0
```

### **Passo 5: Verificar Resultados**
```
📁 Arquivos baixados (4):
   📄 20240307_Fato_Relevante_Dividendos_ABC123.pdf (245.3 KB)
   📄 20240315_Fato_Relevante_Resultados_DEF456.pdf (189.7 KB)
   📄 20240322_Fato_Relevante_Producao_GHI789.pdf (156.2 KB)
   📄 20240401_Fato_Relevante_Vendas_JKL012.pdf (203.8 KB)

💾 Relatório detalhado salvo: relatorio_download_petrobras_20240619_094531.json
📁 Arquivos salvos em: documentos_cvm_completos/PETROBRAS/
```

## 📋 Tipos de Documentos Disponíveis

### **1. Fatos Relevantes** 🚨
- **O que são**: Eventos importantes da empresa
- **Exemplos**: Dividendos, resultados, mudanças na administração
- **Formato**: PDF
- **Frequência**: Conforme necessário

### **2. Comunicados ao Mercado** 📢
- **O que são**: Esclarecimentos e informações adicionais
- **Exemplos**: Apresentações, esclarecimentos públicos
- **Formato**: PDF
- **Frequência**: Regular

### **3. ITRs (Informações Trimestrais)** 📊
- **O que são**: Demonstrações financeiras trimestrais
- **Exemplos**: Balanços, DRE, fluxo de caixa
- **Formato**: PDF estruturado
- **Frequência**: Trimestral

### **4. Assembleias** 🏛️
- **O que são**: Atas e convocações de assembleias
- **Exemplos**: AGO, AGE, boletins de voto
- **Formato**: PDF
- **Frequência**: Anual/conforme necessário

## ⚙️ Configurações de Download

### **Configurações Básicas**
```python
downloader = CVMDocumentDownloader("meu_diretorio")

# Timeout por download (segundos)
downloader.timeout = 30

# Máximo de tentativas por arquivo
downloader.max_retries = 3

# Pausa entre downloads (segundos)
downloader.delay_between_downloads = 2
```

### **Configurações Avançadas**
```python
# Configurar headers HTTP personalizados
downloader.session.headers.update({
    'User-Agent': 'Meu Bot CVM 1.0'
})

# Configurar proxy (se necessário)
downloader.session.proxies = {
    'http': 'http://proxy:8080',
    'https': 'https://proxy:8080'
}
```

## 🎯 Estratégias de Download

### **1. Download Conservador (Recomendado)**
```
- Limite: 5-10 documentos por tipo
- Delay: 3-5 segundos entre downloads
- Tipos: Apenas fatos relevantes
- Empresas: 1-2 por vez
```

### **2. Download Moderado**
```
- Limite: 10-20 documentos por tipo
- Delay: 2-3 segundos
- Tipos: Fatos relevantes + comunicados
- Empresas: 3-5 por vez
```

### **3. Download Intensivo (Cuidado)**
```
- Limite: 20+ documentos por tipo
- Delay: 1-2 segundos
- Tipos: Todos
- Empresas: 5+ por vez
```

## 📊 Monitoramento e Relatórios

### **Relatório de Download (JSON)**
```json
{
  "empresa": "PETROBRAS",
  "inicio": "2024-06-19T09:45:31",
  "downloads": {
    "fatos_relevantes": [
      {
        "status": "sucesso",
        "arquivo": "/path/to/documento.pdf",
        "tamanho": 245760,
        "url": "https://www.rad.cvm.gov.br/...",
        "documento_original": {
          "categoria": "Fato Relevante",
          "data_entrega": "2024-03-07",
          "assunto": "Dividendos..."
        }
      }
    ]
  },
  "estatisticas": {
    "total_documentos": 5,
    "downloads_sucesso": 4,
    "downloads_erro": 1,
    "arquivos_existentes": 0
  }
}
```

### **Estatísticas em Tempo Real**
```python
# Verificar estatísticas durante download
stats = downloader.stats
print(f"Sucessos: {stats['downloads_sucesso']}")
print(f"Erros: {stats['downloads_erro']}")
print(f"Total baixado: {stats['bytes_baixados']} bytes")
```

## 🛡️ Tratamento de Erros

### **Erros Comuns e Soluções**

**1. Timeout de Conexão**
```
Erro: requests.exceptions.Timeout
Solução: Aumentar timeout ou verificar conexão
```

**2. URL Inválida**
```
Erro: URL retornou HTML (possível erro)
Solução: URL pode estar incorreta ou documento indisponível
```

**3. Arquivo Vazio**
```
Erro: Arquivo vazio
Solução: Documento pode não estar disponível no momento
```

**4. Erro de Permissão**
```
Erro: Permission denied
Solução: Verificar permissões do diretório de destino
```

### **Sistema de Retry**
```python
# Sistema tenta automaticamente:
# Tentativa 1: Imediato
# Tentativa 2: Após 2 segundos
# Tentativa 3: Após 4 segundos
# Se falhar 3 vezes: Marca como erro
```

## 📁 Gerenciamento de Arquivos

### **Verificar Arquivos Baixados**
```python
# Listar todos os arquivos
arquivos = downloader.list_downloaded_files()
print(f"Total: {arquivos['total_arquivos']} arquivos")

# Listar arquivos de uma empresa
arquivos_petrobras = downloader.list_downloaded_files("PETROBRAS")
```

### **Evitar Downloads Duplicados**
```python
# Sistema verifica automaticamente se arquivo já existe
# Se existir: Pula download
# Se não existir: Baixa normalmente
# Para forçar re-download: force_redownload=True
```

### **Limpeza de Arquivos**
```bash
# Remover arquivos de uma empresa
rm -rf documentos_cvm_completos/PETROBRAS/

# Remover arquivos de um ano
rm -rf documentos_cvm_completos/*/2023/

# Remover apenas fatos relevantes
rm -rf documentos_cvm_completos/*/*/Fato_Relevante/
```

## 🚨 Boas Práticas e Limitações

### **✅ Boas Práticas**
- 🎯 **Comece pequeno**: Teste com poucos documentos
- ⏱️ **Respeite delays**: Não sobrecarregue o servidor CVM
- 📁 **Organize bem**: Use a estrutura de pastas sugerida
- 🔍 **Monitore erros**: Verifique relatórios regularmente
- 💾 **Backup**: Faça backup dos documentos importantes

### **⚠️ Limitações**
- 🌐 **Dependente da CVM**: Se site da CVM estiver fora, downloads falham
- 📄 **Apenas PDFs**: Sistema baixa principalmente PDFs
- ⏱️ **Velocidade limitada**: Delays necessários para não sobrecarregar
- 💾 **Espaço em disco**: PDFs podem ocupar muito espaço
- 🔗 **URLs podem mudar**: Links da CVM podem ficar indisponíveis

### **🚫 Não Recomendado**
- ❌ Downloads sem delay (pode ser bloqueado)
- ❌ Muitas empresas simultaneamente
- ❌ Downloads 24/7 contínuos
- ❌ Ignorar erros de rede

## 📞 Suporte

### **Logs Detalhados**
```bash
# Logs são salvos automaticamente
tail -f sistema_cvm.log
```

### **Debug Mode**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### **Verificação de Saúde**
```bash
python exemplos/teste_rapido.py
```

---

**💡 Dica**: Comece sempre com downloads pequenos para testar antes de fazer downloads em massa!

