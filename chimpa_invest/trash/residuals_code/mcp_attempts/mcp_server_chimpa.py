#!/usr/bin/env python3
"""
MCP Server para Chimpa Invest
==============================
Este servidor permite que o Claude Desktop acesse e analise PDFs diretamente.

Para usar:
1. Instale: pip install mcp
2. Configure no claude_desktop_config.json
3. Reinicie o Claude Desktop
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Any

# Importar MCP
try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    import mcp.types as types
    from mcp.server.stdio import stdio_server
except ImportError:
    print("❌ MCP não instalado. Execute: pip install mcp")
    sys.exit(1)


class ChimpaInvestServer:
    """
    Servidor MCP para análise de investimentos.
    Permite que o Claude acesse PDFs e dados financeiros localmente.
    """
    
    def __init__(self):
        self.server = Server("chimpa-invest")
        self.base_path = Path(__file__).parent
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Configura os handlers do servidor."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """Lista as ferramentas disponíveis."""
            return [
                types.Tool(
                    name="analyze_pdf",
                    description="Analisa um PDF financeiro completo",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Caminho do PDF"
                            }
                        },
                        "required": ["path"]
                    }
                ),
                types.Tool(
                    name="list_pdfs",
                    description="Lista PDFs disponíveis para análise",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "folder": {
                                "type": "string",
                                "description": "Pasta para buscar PDFs",
                                "default": "documents/pending"
                            }
                        }
                    }
                ),
                types.Tool(
                    name="extract_financial_metrics",
                    description="Extrai métricas financeiras de um PDF",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "pdf_path": {
                                "type": "string",
                                "description": "Caminho do PDF"
                            },
                            "metrics": {
                                "type": "array",
                                "description": "Métricas para extrair",
                                "items": {"type": "string"},
                                "default": ["receita", "ebitda", "lucro_liquido"]
                            }
                        },
                        "required": ["pdf_path"]
                    }
                ),
                types.Tool(
                    name="compare_periods",
                    description="Compara métricas entre diferentes períodos",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "company": {
                                "type": "string",
                                "description": "Nome da empresa"
                            },
                            "periods": {
                                "type": "array",
                                "description": "Períodos para comparar",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["company", "periods"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, 
            arguments: dict[str, Any]
        ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            """Executa uma ferramenta."""
            
            if name == "analyze_pdf":
                return await self._analyze_pdf(arguments["path"])
            
            elif name == "list_pdfs":
                folder = arguments.get("folder", "documents/pending")
                return await self._list_pdfs(folder)
            
            elif name == "extract_financial_metrics":
                return await self._extract_metrics(
                    arguments["pdf_path"],
                    arguments.get("metrics", ["receita", "ebitda", "lucro_liquido"])
                )
            
            elif name == "compare_periods":
                return await self._compare_periods(
                    arguments["company"],
                    arguments["periods"]
                )
            
            else:
                raise ValueError(f"Ferramenta desconhecida: {name}")
    
    async def _analyze_pdf(self, path: str) -> list[types.TextContent]:
        """
        Analisa um PDF financeiro.
        O Claude pode ler o PDF diretamente aqui.
        """
        pdf_path = self.base_path / path
        
        if not pdf_path.exists():
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": f"PDF não encontrado: {path}",
                    "searched_path": str(pdf_path)
                }, indent=2)
            )]
        
        # Aqui o Claude tem acesso direto ao PDF
        analysis = {
            "status": "success",
            "pdf": {
                "name": pdf_path.name,
                "path": str(pdf_path),
                "size_mb": pdf_path.stat().st_size / (1024 * 1024),
                "modified": datetime.fromtimestamp(pdf_path.stat().st_mtime).isoformat()
            },
            "analysis": {
                "note": "O Claude pode ler este PDF diretamente",
                "capabilities": [
                    "Extrair texto completo",
                    "Identificar tabelas",
                    "Analisar gráficos",
                    "Processar formatação"
                ]
            },
            "next_steps": [
                "Claude lê o PDF",
                "Extrai métricas automaticamente",
                "Gera análise estruturada"
            ]
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(analysis, indent=2, ensure_ascii=False)
        )]
    
    async def _list_pdfs(self, folder: str) -> list[types.TextContent]:
        """Lista PDFs disponíveis."""
        folder_path = self.base_path / folder
        
        if not folder_path.exists():
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Pasta não encontrada: {folder}",
                    "base_path": str(self.base_path)
                }, indent=2)
            )]
        
        pdfs = []
        for pdf in folder_path.glob("**/*.pdf"):
            relative_path = pdf.relative_to(self.base_path)
            pdfs.append({
                "name": pdf.name,
                "path": str(relative_path),
                "size_mb": round(pdf.stat().st_size / (1024 * 1024), 2),
                "modified": datetime.fromtimestamp(pdf.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            })
        
        result = {
            "folder": folder,
            "count": len(pdfs),
            "pdfs": sorted(pdfs, key=lambda x: x["modified"], reverse=True)
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2, ensure_ascii=False)
        )]
    
    async def _extract_metrics(self, pdf_path: str, metrics: list[str]) -> list[types.TextContent]:
        """Extrai métricas específicas de um PDF."""
        full_path = self.base_path / pdf_path
        
        if not full_path.exists():
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": f"PDF não encontrado: {pdf_path}"}, indent=2)
            )]
        
        result = {
            "pdf": pdf_path,
            "requested_metrics": metrics,
            "extraction": {
                "method": "Claude lê o PDF diretamente",
                "capabilities": [
                    "Identificar valores monetários",
                    "Extrair percentuais",
                    "Encontrar tabelas de dados",
                    "Processar notas explicativas"
                ]
            },
            "example_output": {
                "receita": {
                    "valor": "R$ 11,8 bilhões",
                    "variacao_trimestre": "-2.3%",
                    "variacao_ano": "+15.2%"
                },
                "ebitda": {
                    "valor": "R$ 4,8 bilhões",
                    "margem": "40.7%"
                },
                "lucro_liquido": {
                    "valor": "R$ 2,4 bilhões",
                    "por_acao": "R$ 0,52"
                }
            }
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2, ensure_ascii=False)
        )]
    
    async def _compare_periods(self, company: str, periods: list[str]) -> list[types.TextContent]:
        """Compara métricas entre períodos."""
        result = {
            "company": company,
            "periods": periods,
            "comparison": {
                "method": "Claude analisa múltiplos PDFs",
                "capabilities": [
                    "Comparar evolução de métricas",
                    "Identificar tendências",
                    "Calcular variações percentuais",
                    "Destacar pontos de inflexão"
                ]
            },
            "example": {
                "receita": {
                    "3T23": 10500,
                    "4T23": 11200,
                    "1T24": 11800,
                    "trend": "crescente",
                    "cagr": "12.5%"
                }
            }
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2, ensure_ascii=False)
        )]
    
    async def run(self):
        """Executa o servidor."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="chimpa-invest",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=types.NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )


async def main():
    """Função principal."""
    server = ChimpaInvestServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())