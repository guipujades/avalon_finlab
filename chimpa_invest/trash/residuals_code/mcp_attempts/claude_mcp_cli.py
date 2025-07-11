#!/usr/bin/env python3
"""
Claude MCP CLI - Interface de linha de comando
==============================================
Usa o Claude via API com MCP para analisar PDFs diretamente.
"""

import os
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional
import anthropic
from datetime import datetime


class ClaudeMCPCLI:
    """
    Interface CLI para usar Claude com MCP.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa o cliente.
        
        Args:
            api_key: Chave da API Anthropic. Se não fornecida, busca em ANTHROPIC_API_KEY
        """
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError(
                "API key não encontrada! Configure:\n"
                "1. export ANTHROPIC_API_KEY='sua-chave-aqui'\n"
                "2. Ou passe api_key ao criar ClaudeMCPCLI"
            )
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.results_dir = Path("analises_mcp")
        self.results_dir.mkdir(exist_ok=True)
    
    def analyze_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Analisa um PDF usando Claude com acesso direto ao arquivo.
        
        IMPORTANTE: Para funcionar com MCP real, você precisa:
        1. Usar a API com MCP habilitado
        2. Ou usar Claude via SDK com servidor MCP rodando
        """
        
        if not pdf_path.exists():
            return {"error": f"PDF não encontrado: {pdf_path}"}
        
        print(f"\n📄 Analisando: {pdf_path.name}")
        print(f"📍 Caminho: {pdf_path.absolute()}")
        print("🤖 Enviando para Claude via API...")
        
        # Preparar mensagem
        prompt = f"""Por favor, analise o PDF financeiro localizado em: {pdf_path.absolute()}

Extraia e organize:

1. IDENTIFICAÇÃO:
   - Empresa, período, data

2. MÉTRICAS FINANCEIRAS:
   - Receita (valor e variação %)
   - EBITDA (valor, margem e variação %)
   - Lucro líquido (valor e variação %)
   - Dívida líquida e alavancagem
   - Geração de caixa

3. DESTAQUES OPERACIONAIS:
   - Volumes, preços, market share
   - Eficiência e produtividade

4. ANÁLISE QUALITATIVA:
   - Principais pontos positivos
   - Riscos e desafios
   - Guidance e perspectivas

Retorne a análise em formato JSON estruturado."""
        
        try:
            # Fazer a chamada para o Claude
            response = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4000,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                # Aqui é onde o MCP entraria - permitindo anexar o arquivo
                # No momento, a API padrão não suporta anexos diretos
                metadata={
                    "pdf_path": str(pdf_path.absolute()),
                    "analysis_type": "financial_report"
                }
            )
            
            # Processar resposta
            result = {
                "status": "success",
                "pdf": pdf_path.name,
                "analysis": response.content[0].text,
                "timestamp": datetime.now().isoformat(),
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            }
            
            # Salvar resultado
            self._save_result(result, pdf_path.stem)
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "pdf": pdf_path.name
            }
    
    def analyze_with_content(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Alternativa: Extrai texto do PDF e envia para Claude.
        
        Esta é a abordagem que funciona hoje com a API padrão.
        """
        
        print(f"\n📄 Processando: {pdf_path.name}")
        
        # Extrair texto primeiro
        text = self._extract_pdf_text(pdf_path)
        
        if not text:
            return {"error": "Não foi possível extrair texto do PDF"}
        
        print(f"📝 Texto extraído: {len(text)} caracteres")
        print("🤖 Analisando com Claude...")
        
        # Limitar tamanho do texto (tokens)
        max_chars = 50000  # ~12k tokens
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[... documento truncado ...]"
        
        prompt = f"""Analise o seguinte relatório financeiro e extraia informações estruturadas:

{text}

Por favor, organize a análise em:
1. Empresa e período
2. Métricas financeiras principais
3. Destaques operacionais
4. Riscos identificados
5. Perspectivas

Retorne em formato JSON."""
        
        try:
            response = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4000,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Tentar parsear JSON da resposta
            response_text = response.content[0].text
            
            try:
                # Extrair JSON se estiver em markdown
                import re
                json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group(1))
                else:
                    # Tentar parse direto
                    analysis = json.loads(response_text)
            except:
                # Se não conseguir, retornar texto
                analysis = {"raw_response": response_text}
            
            result = {
                "status": "success",
                "pdf": pdf_path.name,
                "method": "text_extraction",
                "analysis": analysis,
                "timestamp": datetime.now().isoformat(),
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "cost_usd": (response.usage.input_tokens * 0.015 + 
                                response.usage.output_tokens * 0.075) / 1000
                }
            }
            
            self._save_result(result, pdf_path.stem)
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "pdf": pdf_path.name
            }
    
    def _extract_pdf_text(self, pdf_path: Path) -> str:
        """Extrai texto do PDF."""
        
        # Tentar pdftotext primeiro
        try:
            import subprocess
            result = subprocess.run(
                ['pdftotext', '-layout', str(pdf_path), '-'],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout
        except:
            pass
        
        # Fallback para PyPDF2
        try:
            import PyPDF2
            text = ""
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except:
            pass
        
        return ""
    
    def _save_result(self, result: Dict[str, Any], base_name: str):
        """Salva resultado da análise."""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.results_dir / f"analise_{base_name}_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Análise salva em: {output_file}")
    
    def batch_analyze(self, pdf_folder: Path, max_files: int = 5) -> Dict[str, Any]:
        """Analisa múltiplos PDFs em lote."""
        
        pdfs = list(pdf_folder.glob("*.pdf"))[:max_files]
        results = {}
        
        print(f"\n📊 Analisando {len(pdfs)} PDFs em lote...")
        
        for i, pdf in enumerate(pdfs, 1):
            print(f"\n[{i}/{len(pdfs)}] {pdf.name}")
            results[pdf.name] = self.analyze_with_content(pdf)
            
            # Mostrar custo acumulado
            total_cost = sum(
                r.get('usage', {}).get('cost_usd', 0) 
                for r in results.values() 
                if r.get('status') == 'success'
            )
            print(f"💰 Custo acumulado: ${total_cost:.4f}")
        
        return results


def main():
    """Função principal CLI."""
    
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analisa PDFs financeiros usando Claude API"
    )
    parser.add_argument(
        "pdf", 
        nargs="?",
        help="Caminho do PDF para analisar"
    )
    parser.add_argument(
        "--batch",
        help="Analisa todos os PDFs em uma pasta",
        metavar="PASTA"
    )
    parser.add_argument(
        "--api-key",
        help="Chave da API Anthropic (ou use ANTHROPIC_API_KEY)",
        metavar="KEY"
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=5,
        help="Máximo de arquivos para análise em lote (padrão: 5)"
    )
    
    args = parser.parse_args()
    
    # Verificar API key
    api_key = args.api_key or os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ Erro: API key não configurada!")
        print("\nConfigure de uma das formas:")
        print("1. export ANTHROPIC_API_KEY='sua-chave-aqui'")
        print("2. python claude_mcp_cli.py --api-key sua-chave-aqui arquivo.pdf")
        print("\nObtenha sua chave em: https://console.anthropic.com/")
        return
    
    # Criar cliente
    try:
        cli = ClaudeMCPCLI(api_key)
    except Exception as e:
        print(f"❌ Erro ao criar cliente: {e}")
        return
    
    # Executar análise
    if args.batch:
        # Análise em lote
        folder = Path(args.batch)
        if not folder.exists():
            print(f"❌ Pasta não encontrada: {folder}")
            return
        
        results = cli.batch_analyze(folder, args.max_files)
        
        # Resumo
        success = sum(1 for r in results.values() if r.get('status') == 'success')
        total_cost = sum(
            r.get('usage', {}).get('cost_usd', 0) 
            for r in results.values() 
            if r.get('status') == 'success'
        )
        
        print(f"\n✅ Análise concluída!")
        print(f"   Sucessos: {success}/{len(results)}")
        print(f"   Custo total: ${total_cost:.4f}")
        
    elif args.pdf:
        # Análise individual
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            print(f"❌ PDF não encontrado: {pdf_path}")
            return
        
        result = cli.analyze_with_content(pdf_path)
        
        if result.get('status') == 'success':
            print("\n✅ Análise concluída com sucesso!")
            
            # Mostrar preview da análise
            analysis = result.get('analysis', {})
            if isinstance(analysis, dict):
                print("\n📊 Preview da análise:")
                print(json.dumps(analysis, indent=2, ensure_ascii=False)[:500] + "...")
            
            # Mostrar custo
            cost = result.get('usage', {}).get('cost_usd', 0)
            print(f"\n💰 Custo: ${cost:.4f}")
        else:
            print(f"\n❌ Erro: {result.get('error')}")
    
    else:
        # Modo interativo
        print("\n🤖 CLAUDE MCP CLI - Modo Interativo")
        print("="*50)
        
        # Buscar PDFs
        pdfs = []
        for folder in ["documents/pending", "documents", "."]:
            folder_path = Path(folder)
            if folder_path.exists():
                pdfs.extend(folder_path.glob("*.pdf"))
        
        if not pdfs:
            print("❌ Nenhum PDF encontrado!")
            return
        
        print(f"\n📄 PDFs disponíveis ({len(pdfs)}):")
        for i, pdf in enumerate(pdfs[:10], 1):
            print(f"[{i}] {pdf.name}")
        
        if len(pdfs) > 10:
            print(f"... e mais {len(pdfs)-10} arquivos")
        
        try:
            choice = int(input("\nEscolha o PDF (número): ")) - 1
            if 0 <= choice < len(pdfs):
                result = cli.analyze_with_content(pdfs[choice])
                
                if result.get('status') == 'success':
                    print("\n✅ Análise concluída!")
                    cost = result.get('usage', {}).get('cost_usd', 0)
                    print(f"💰 Custo: ${cost:.4f}")
        except:
            print("❌ Escolha inválida")


if __name__ == "__main__":
    main()