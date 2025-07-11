# Dashboard Avalon FIA - Instruções de Uso

## 📋 Pré-requisitos

1. **Python 3.8+** instalado no Windows
2. **MetaTrader 5** instalado (Rico - MetaTrader 5)
3. Conexão com internet para acessar a API BTG

## 🚀 Como Executar

### Opção 1: Dashboard Completo (com MetaTrader 5)

1. **No Windows Explorer**, navegue até:
   ```
   C:\Users\guilh\Documents\GitHub\avalon_fia
   ```

2. **Dê duplo clique** em:
   ```
   run_complete_windows.bat
   ```

3. O script irá:
   - Instalar automaticamente as dependências necessárias
   - Iniciar o dashboard em http://localhost:5000
   - Abrir automaticamente o navegador

### Opção 2: Dashboard Simplificado (sem MT5)

Se houver problemas com o MetaTrader 5, use a versão simplificada:

1. **Dê duplo clique** em:
   ```
   run_simple_windows.bat
   ```

2. Esta versão mostra:
   - Patrimônio Líquido
   - Valor da Cota
   - Dados básicos do fundo

## 🔧 Teste de Conexão MT5

Para verificar se o MetaTrader está configurado corretamente:

1. Execute no terminal do Windows:
   ```bash
   python test_mt5_connection.py
   ```

## 📊 Funcionalidades do Dashboard Completo

- **Visão Geral**: PL, Cota, Retorno Total
- **Portfolio**: Composição detalhada de ações e opções
- **Análise de Risco**: VaR, Volatilidade, Sharpe Ratio
- **Dados de Mercado**: IBOV e USD em tempo real
- **Gráficos Interativos**: Composição e concentração
- **Exportação**: Download dos dados em JSON

## ⚙️ Credenciais Configuradas

### API BTG (Funds)
- Client ID: `guilherme magalhães`
- Client Secret: `Cg21092013PM#`

### MetaTrader 5
- Servidor: `GenialInvestimentos-PRD`
- Login: `156691`
- Senha: `Avca@1985`

## 🆘 Solução de Problemas

### Erro: "No module named 'flask'"
Execute no terminal:
```bash
pip install flask pandas numpy requests matplotlib MetaTrader5
```

### Erro: "MetaTrader não encontrado"
1. Verifique se o MT5 está instalado em:
   ```
   C:\Program Files\Rico - MetaTrader 5\
   ```
2. Execute o teste de conexão

### Dashboard não abre
1. Verifique se a porta 5000 está livre
2. Tente acessar manualmente: http://localhost:5000

## 📞 Suporte

Em caso de dúvidas, os arquivos principais estão em:
- `trackfia/app_complete.py` - Dashboard completo
- `trackfia/app_local_simple.py` - Dashboard simplificado
- `trackfia/api_btg_funds.py` - Conexão com API BTG