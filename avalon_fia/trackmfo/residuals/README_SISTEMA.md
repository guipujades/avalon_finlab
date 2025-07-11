# Sistema Track MFO - Documentação

## Visão Geral

O sistema Track MFO foi atualizado para capturar e gerenciar dados de múltiplas carteiras de investimento, mantendo compatibilidade com o sistema original.

## Estrutura do Sistema

### 1. **Captura de Dados**

O sistema suporta dois modos de captura:

#### A) Modo Original (via POST)
- Os dados chegam via POST no endpoint `/update_data`
- Formato esperado:
```json
{
    "clients": {
        "account_id": "json_string_com_dados_da_conta",
        ...
    },
    "data_btg": {
        "Conta": [...],
        "Id": [...],
        "Taxas": [...]
    }
}
```

#### B) Modo API Direta
- Captura dados diretamente das APIs BTG
- Suporta fundos (API de fundos) e contas digitais (API digital)
- Usa as correções implementadas no código do Avalon FIA

### 2. **Componentes Principais**

#### `mfo_data_receiver.py`
- Recebe e processa dados no formato original
- Calcula taxas e cobranças
- Mantém compatibilidade total com `app.py` original

#### `portfolio_capture.py`
- Captura dados diretamente das APIs BTG
- Suporta múltiplos tipos de carteira
- Usa a API corrigida (com refresh) para fundos

#### `data_storage.py`
- Armazenamento estruturado em SQLite
- Organização de arquivos por tipo
- Sistema de limpeza automática

#### `website_integration.py`
- Processa dados para visualização web
- Gera gráficos e métricas
- Exporta JSON para consumo do frontend

#### `app_enhanced.py`
- Versão melhorada do `app.py` original
- Mantém endpoints originais
- Adiciona novos endpoints REST API

### 3. **Como Usar**

#### Execução Rápida
```bash
cd trackmfo
python run_capture.py
```

#### Com Interface Web (Modo Original)
```bash
python app.py
```

#### Com Interface Web Melhorada
```bash
python app_enhanced.py
```

#### Captura Agendada
```bash
python capture_portfolios.py --config portfolios_config.json
```

### 4. **Fluxo de Dados**

1. **Entrada de Dados**:
   - Via POST (sistema original)
   - Via API BTG direta

2. **Processamento**:
   - `process_account_data()` processa dados brutos
   - Cálculo de taxas e cobranças
   - Organização por tipo de ativo

3. **Armazenamento**:
   - SQLite para metadados
   - Pickle para dados brutos
   - JSON para exportação web

4. **Visualização**:
   - Dashboard Flask
   - Arquivos JSON para website
   - Relatórios Excel

### 5. **Configuração**

Edite `portfolios_config.json` para:
- Adicionar/remover portfolios
- Configurar agendamento
- Definir formatos de saída

### 6. **APIs Utilizadas**

#### API de Fundos (Avalon FIA)
- URL: `https://funds.btgpactual.com`
- Credenciais: Configuradas no código
- Requer refresh após 21/01

#### API Digital (Contas BTG)
- URL: `https://api.btgpactual.com`
- Credenciais: Via arquivo JSON
- OAuth2 com token bearer

### 7. **Manutenção da Compatibilidade**

O sistema mantém total compatibilidade com o código original:
- Mesmo formato de dados de entrada
- Mesma lógica de processamento
- Mesmos cálculos de taxas
- Templates originais funcionam sem alteração

### 8. **Melhorias Implementadas**

- Armazenamento estruturado
- Histórico de capturas
- API REST completa
- Geração automática de relatórios
- Sistema de logs
- Tratamento de erros robusto

## Próximos Passos

1. Testar com dados reais
2. Ajustar templates se necessário
3. Configurar webhooks para recepção automática
4. Implementar alertas e notificações