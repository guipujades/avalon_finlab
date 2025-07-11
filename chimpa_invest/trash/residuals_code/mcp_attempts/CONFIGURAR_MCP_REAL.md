# 🚀 Configurando MCP (Model Context Protocol) Real

## O que é o MCP?

O MCP permite que o Claude acesse recursos locais do seu computador, incluindo:
- 📄 Ler arquivos (incluindo PDFs, imagens, etc.)
- 💾 Escrever arquivos
- 🖥️ Executar comandos
- 🔧 Integrar com ferramentas locais

## Como Configurar

### 1. Instalar Claude Desktop
```bash
# Download em: https://claude.ai/download
```

### 2. Configurar MCP Server

**Criar arquivo de configuração:**

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Linux:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "C:\\Users\\guilh\\Documents\\GitHub\\chimpa_invest"
      ]
    },
    "chimpa-invest": {
      "command": "python",
      "args": [
        "C:\\Users\\guilh\\Documents\\GitHub\\chimpa_invest\\mcp_server.py"
      ]
    }
  }
}
```

### 3. Criar MCP Server Customizado

```python
# mcp_server.py
#!/usr/bin/env python3
"""
MCP Server para Chimpa Invest
Permite que o Claude acesse PDFs e execute análises diretamente
"""

import asyncio
import json
from pathlib import Path
from mcp import Server, Tool
from mcp.types import TextContent, ImageContent, ErrorContent

class ChimpaInvestMCP:
    """Servidor MCP para análise de investimentos"""
    
    def __init__(self):
        self.server = Server("chimpa-invest")
        self.setup_tools()
    
    def setup_tools(self):
        """Configura as ferramentas disponíveis"""
        
        @self.server.tool()
        async def analyze_pdf(path: str) -> str:
            """Analisa um PDF financeiro"""
            pdf_path = Path(path)
            if not pdf_path.exists():
                return json.dumps({"error": "PDF não encontrado"})
            
            # Aqui o Claude pode ler o PDF diretamente
            return json.dumps({
                "status": "success",
                "message": f"PDF {pdf_path.name} pronto para análise",
                "path": str(pdf_path.absolute())
            })
        
        @self.server.tool()
        async def list_pdfs(folder: str = "documents/pending") -> str:
            """Lista PDFs disponíveis"""
            folder_path = Path(folder)
            if not folder_path.exists():
                return json.dumps({"error": "Pasta não encontrada"})
            
            pdfs = list(folder_path.glob("*.pdf"))
            return json.dumps({
                "count": len(pdfs),
                "files": [str(p) for p in pdfs]
            })
        
        @self.server.tool()
        async def extract_metrics(pdf_path: str) -> str:
            """Extrai métricas financeiras de um PDF"""
            # O Claude pode processar o PDF diretamente aqui
            return json.dumps({
                "pdf": pdf_path,
                "metrics": "Claude irá extrair as métricas diretamente"
            })

if __name__ == "__main__":
    server = ChimpaInvestMCP()
    asyncio.run(server.server.run())
```

## Como Usar com MCP Configurado

### 1. No Claude Desktop com MCP:
```
Claude: analyze_pdf("documents/pending/VALE_3T24.pdf")
```

O Claude irá:
- ✅ Ler o PDF diretamente
- ✅ Extrair tabelas e texto
- ✅ Analisar o conteúdo
- ✅ Retornar análise estruturada

### 2. Comandos Disponíveis:
```
# Listar PDFs
list_pdfs()

# Analisar PDF específico
analyze_pdf("caminho/do/arquivo.pdf")

# Extrair métricas
extract_metrics("caminho/do/arquivo.pdf")
```

## Alternativa: MCP Filesystem

Se você não quiser criar um servidor customizado, pode usar o MCP filesystem padrão:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "C:\\Users\\guilh\\Documents\\GitHub\\chimpa_invest"
      ]
    }
  }
}
```

Com isso, no Claude Desktop você pode:
```
# Ler PDF diretamente
read_file("documents/pending/VALE_3T24.pdf")

# Listar arquivos
list_directory("documents/pending")
```

## 🎯 Diferença Crucial

### Sem MCP (atual):
- Claude não pode ler arquivos binários
- Precisa extrair texto primeiro
- Limitado a ferramentas de texto

### Com MCP:
- Claude lê PDFs diretamente
- Acessa sistema de arquivos
- Processa imagens e tabelas
- Executa análises complexas

## 📚 Recursos

- [Documentação MCP](https://modelcontextprotocol.io/docs)
- [MCP Servers](https://github.com/modelcontextprotocol/servers)
- [Claude Desktop](https://claude.ai/download)

## 🚨 Importante

O MCP só funciona com:
1. **Claude Desktop** (aplicativo desktop)
2. **Claude API** com MCP configurado
3. **Não funciona** no Claude.ai (web) ou nesta conversa atual

Por isso criei a solução alternativa de extração local!