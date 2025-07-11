# Como Usar o Sistema Track MFO

## 🎯 Script Principal: `run_mfo_capture.py`

Este é o script que você deve usar para capturar dados de múltiplas carteiras de clientes!

## Passo a Passo

### 1. Primeiro, inicie o servidor web:
```bash
cd trackmfo
python app.py
```

### 2. Em outro terminal, execute a captura:
```bash
cd trackmfo
python run_mfo_capture.py
```

## O que este script faz:

1. **Conecta na API BTG de Parceiros**
2. **Baixa um arquivo ZIP com dados de TODOS os clientes**
3. **Processa os dados de cada conta**
4. **Envia para o app.py no formato esperado**
5. **O app.py processa e exibe no dashboard**

## Estrutura dos Scripts

- `run_mfo_capture.py` - **USE ESTE!** Script principal simplificado
- `capture_mfo_clients.py` - Lógica de captura via API de parceiros
- `app.py` - Servidor web que recebe e exibe os dados
- `mfo_data_receiver.py` - Processa dados recebidos

## Fluxo de Dados

```
API BTG (Parceiro) 
    ↓
capture_mfo_clients.py (baixa ZIP com todas as contas)
    ↓
run_mfo_capture.py (coordena o processo)
    ↓
POST → app.py/update_data
    ↓
mfo_data_receiver.py (processa)
    ↓
Dashboard Web (visualização)
```

## Diferença dos outros scripts:

- `run_capture.py` - Captura apenas Avalon FIA (não é o que você quer)
- `capture_portfolios.py` - Sistema genérico para múltiplos tipos
- `run_mfo_capture.py` - **Específico para clientes MFO via API de parceiros**

## Troubleshooting

Se der erro de credenciais:
1. Verifique se existe o arquivo: `~/Desktop/api_btg_info.json`
2. O arquivo deve ter o formato:
```json
{
    "client_id": "seu_client_id",
    "client_secret": "seu_client_secret"
}
```

Se der erro 404 ou 405:
- A API de parceiros pode estar com problemas
- Tente usar o cache: remova `use_cache=False` do script

## Dados de Exemplo

O sistema captura automaticamente dados de TODOS os clientes vinculados ao parceiro, incluindo:
- Fundos de investimento
- Renda fixa
- Ações
- COEs
- Derivativos
- E muito mais...

Cada cliente terá seus dados processados e as taxas calculadas automaticamente.