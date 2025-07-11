# Avalon Fund Tracker - Sistema Interno

Sistema de rastreamento de fundos de investimento para uso interno com logging de memória e persistência de dados.

## Instalação

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar ambiente
```bash
python setup.py
```

### 3. Configurar credenciais
Edite o arquivo `.env` com suas credenciais:
```bash
# BTG API
AVALON_BTG_API_KEY=sua_chave_api
AVALON_BTG_API_SECRET=seu_secret

# MetaTrader 5 (opcional)
AVALON_MT5_LOGIN=seu_login
AVALON_MT5_PASSWORD=sua_senha
AVALON_MT5_SERVER=seu_servidor
```

## Executar o Sistema

### Modo de Teste (executa uma vez)
```bash
python internal_runner.py
```

### Modo Produção (execução contínua)
Edite `internal_runner.py` e descomente a linha no final:
```python
# runner.run_continuous()
```

Então execute:
```bash
python internal_runner.py
```

## Monitoramento

### Logs em tempo real
```bash
tail -f logs/fund_runner_*.log
```

### Relatório diário
```bash
cat logs/daily_report_*.json | jq
```

### Operações do dia
```bash
cat logs/operations_*.jsonl | jq
```

## Estrutura de Dados

- `internal_data/current_data.json` - Dados atuais do sistema
- `data/avalon_fund.db` - Banco de dados SQLite
- `logs/` - Todos os logs e relatórios

## Agendamento

O sistema executa automaticamente:
- **09:00** - Rotina diária completa
- **A cada 30 min** - Atualização de preços (horário de mercado)
- **15:30** - Atualização de preços final
- **16:00** - Cálculos de portfolio e risco

## Comandos Úteis

### Verificar memória do processo
```bash
ps aux | grep internal_runner
```

### Backup dos dados
```bash
cp -r internal_data/ backup_$(date +%Y%m%d)/
cp data/avalon_fund.db backup_avalon_$(date +%Y%m%d).db
```

### Limpar logs antigos (manter últimos 30 dias)
```bash
find logs/ -name "*.log" -mtime +30 -delete
find logs/ -name "*.jsonl" -mtime +30 -delete
```