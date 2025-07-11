# Atualização da API BTG - Correção do Erro 404

## Problema Identificado
Após 21/01, a API do BTG passou a exigir o uso de novos endpoints para obter posições de parceiros. O erro reportado foi:
```
{'errors': [{'code': 404, 'message': 'There are no positions file for partner with cnpj 47952345000109'}], 'response': None}
```

## Solução Implementada

### 1. Novos Endpoints Adicionados
Foram implementadas duas novas funções em `trackfia/api_btg_utils.py`:

- **`get_position_by_partner_refresh()`**: Chama o endpoint para atualizar as posições para D0
- **`get_partner_position()`**: Obtém as posições atualizadas em formato ZIP

### 2. Fluxo Atualizado
A função `portfolio_api()` foi modificada para:
1. Primeiro chamar `get_position_by_partner_refresh()` para atualizar as posições
2. Aguardar o processamento
3. Chamar `get_partner_position()` para obter o arquivo ZIP
4. Se falhar, tentar o método antigo como fallback

### 3. Processamento de ZIP
Nova função `process_partner_position_zip()` foi adicionada para processar o arquivo ZIP retornado pelos novos endpoints.

## Como Testar

### 1. Teste Manual
Execute o script de teste criado:
```bash
cd /mnt/c/Users/guilh/Documents/GitHub/avalon_fia
python test_api_btg.py
```

### 2. Teste Integrado
Execute o código principal:
```bash
cd trackfia
python api_btg.py
```

### 3. Verificar Logs
O sistema agora imprime mensagens de status durante a execução:
- "Refresh de posicoes iniciado com sucesso para CNPJ..."
- "Posicoes recuperadas com sucesso para CNPJ..."
- "Tentando metodo antigo de relatorios..." (se o novo falhar)

## Webhook (Opcional)

Se necessário configurar um webhook para receber notificações:

1. Execute o servidor webhook:
```bash
python webhook_config.py
```

2. Configure o endpoint no BTG:
- URL: `http://seu-servidor:5000/webhook/positions-by-partner`
- Método: POST

## Observações Importantes

1. **CNPJ Avalon**: O CNPJ padrão configurado é `47952345000109`
2. **Tempo de Espera**: O sistema aguarda 5 segundos após o refresh antes de tentar obter as posições
3. **Fallback**: Se o novo método falhar, o sistema tentará automaticamente o método antigo
4. **Compatibilidade**: O código mantém compatibilidade com o método antigo para garantir continuidade

## Arquivos Modificados
- `trackfia/api_btg_utils.py`: Novas funções e lógica atualizada
- `trackfia/api_btg.py`: Importação da nova função de processamento
- `test_api_btg.py`: Script de teste (novo)
- `webhook_config.py`: Configuração de webhook (novo)

## Próximos Passos
1. Executar os testes para verificar se o erro foi resolvido
2. Monitorar os logs para garantir que as chamadas estão funcionando
3. Se necessário, ajustar o tempo de espera ou implementar retry logic