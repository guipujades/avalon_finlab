#!/usr/bin/env python3
"""
Claude MCP CLI - Versão com suporte a .env
===========================================
Usa o Claude via API para analisar PDFs diretamente.
"""

import os
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional
import anthropic
from datetime import datetime

# Carregar variáveis do .env
from dotenv import load_dotenv
load_dotenv()


class ClaudeMCPCLI:
    """
    Interface CLI para usar Claude com análise de PDFs.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa o cliente.
        
        Args:
            api_key: Chave da API Anthropic. Se não fornecida, busca em ANTHROPIC_API_KEY
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError(
                "API key não encontrada! Configure:\n"
                "1. No arquivo .env: ANTHROPIC_API_KEY=sua-chave\n"
                "2. Ou export ANTHROPIC_API_KEY='sua-chave-aqui'"
            )
        
        print(f"✅ API Key carregada: {self.api_key[:8]}...")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.results_dir = Path("analises_mcp")
        self.results_dir.mkdir(exist_ok=True)
    
    def analyze_with_content(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Extrai texto do PDF e envia para Claude analisar.
        """
        
        print(f"\n📄 Processando: {pdf_path.name}")
        
        # Extrair texto primeiro
        text = self._extract_pdf_text(pdf_path)
        
        if not text:
            return {"error": "Não foi possível extrair texto do PDF"}
        
        print(f"📝 Texto extraído: {len(text)} caracteres")
        print("🤖 Enviando para Claude...")
        
        # Limitar tamanho do texto (tokens)
        max_chars = 50000  # ~12k tokens
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[... documento truncado ...]"
            print(f"⚠️  Texto truncado para {max_chars} caracteres")
        
        prompt = f"""Você é um analista financeiro especializado em empresas brasileiras.
        
Analise o seguinte relatório financeiro e extraia informações estruturadas:

{text}

Por favor, organize a análise em formato JSON com a seguinte estrutura:

{{
    "empresa": {{
        "nome": "Nome da empresa",
        "cnpj": "CNPJ se disponível",
        "setor": "Setor de atuação"
    }},
    "periodo": {{
        "trimestre": "Ex: 3T24",
        "ano": 2024,
        "data_publicacao": "YYYY-MM-DD se disponível"
    }},
    "metricas_financeiras": {{
        "receita": {{
            "valor": 0,
            "moeda": "BRL ou USD",
            "unidade": "milhões",
            "variacao_trimestre": 0,
            "variacao_ano": 0
        }},
        "ebitda": {{
            "valor": 0,
            "margem": 0,
            "variacao_ano": 0
        }},
        "lucro_liquido": {{
            "valor": 0,
            "margem": 0,
            "variacao_ano": 0
        }},
        "divida_liquida": {{
            "valor": 0,
            "divida_ebitda": 0
        }}
    }},
    "destaques": [
        "Liste 3-5 principais destaques positivos"
    ],
    "riscos": [
        "Liste 2-3 principais riscos ou desafios"
    ],
    "guidance": {{
        "producao": "Se houver guidance de produção",
        "receita": "Se houver guidance de receita",
        "investimentos": "Se houver guidance de CAPEX"
    }}
}}

Retorne APENAS o JSON, sem texto adicional."""
        
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",  # Mais barato para testes
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
                # Se vier com markdown, extrair
                import re
                json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group(1))
                else:
                    # Tentar parse direto
                    analysis = json.loads(response_text)
            except:
                # Se não conseguir, retornar texto
                print("⚠️  Não foi possível parsear JSON, retornando texto bruto")
                analysis = {"raw_response": response_text}
            
            result = {
                "status": "success",
                "pdf": pdf_path.name,
                "method": "text_extraction",
                "analysis": analysis,
                "timestamp": datetime.now().isoformat(),
                "usage": {
                    "model": "claude-3-sonnet-20240229",
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "cost_usd": (response.usage.input_tokens * 0.003 + 
                                response.usage.output_tokens * 0.015) / 1000
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
        
        print("📄 Tentando extrair texto do PDF...")
        
        # Tentar pdftotext primeiro (mais rápido)
        try:
            import subprocess
            result = subprocess.run(
                ['pdftotext', '-layout', str(pdf_path), '-'],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0 and result.stdout:
                print("✅ Texto extraído com pdftotext")
                return result.stdout
        except Exception as e:
            print(f"⚠️  pdftotext não disponível: {e}")
        
        # Tentar PyPDF2
        try:
            import PyPDF2
            text = ""
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                num_pages = len(reader.pages)
                print(f"📖 Extraindo {num_pages} páginas com PyPDF2...")
                
                for i, page in enumerate(reader.pages):
                    text += page.extract_text() + "\n"
                    if (i + 1) % 10 == 0:
                        print(f"   Processadas {i + 1}/{num_pages} páginas...")
                
            print("✅ Texto extraído com PyPDF2")
            return text
        except Exception as e:
            print(f"⚠️  PyPDF2 falhou: {e}")
        
        # Tentar pdfplumber como última opção
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                num_pages = len(pdf.pages)
                print(f"📖 Extraindo {num_pages} páginas com pdfplumber...")
                
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    
                    # Extrair tabelas também
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            text += " | ".join(str(cell) for cell in row if cell) + "\n"
                    
                    if (i + 1) % 10 == 0:
                        print(f"   Processadas {i + 1}/{num_pages} páginas...")
                
            print("✅ Texto extraído com pdfplumber")
            return text
        except Exception as e:
            print(f"❌ pdfplumber falhou: {e}")
        
        return ""
    
    def _save_result(self, result: Dict[str, Any], base_name: str):
        """Salva resultado da análise."""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.results_dir / f"analise_{base_name}_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Análise salva em: {output_file}")
    
    def display_results(self, result: Dict[str, Any]):
        """Exibe resultados formatados."""
        
        if result.get('status') != 'success':
            print(f"\n❌ Erro: {result.get('error')}")
            return
        
        print("\n" + "="*60)
        print("📊 RESULTADO DA ANÁLISE")
        print("="*60)
        
        analysis = result.get('analysis', {})
        
        if 'raw_response' in analysis:
            print("\n📝 Resposta do Claude:")
            print(analysis['raw_response'][:500] + "...")
        else:
            # Empresa
            empresa = analysis.get('empresa', {})
            print(f"\n🏢 EMPRESA: {empresa.get('nome', 'N/A')}")
            if empresa.get('cnpj'):
                print(f"   CNPJ: {empresa['cnpj']}")
            if empresa.get('setor'):
                print(f"   Setor: {empresa['setor']}")
            
            # Período
            periodo = analysis.get('periodo', {})
            if periodo:
                print(f"\n📅 PERÍODO: {periodo.get('trimestre', '')} {periodo.get('ano', '')}")
            
            # Métricas
            metricas = analysis.get('metricas_financeiras', {})
            if metricas:
                print("\n💰 MÉTRICAS FINANCEIRAS:")
                
                # Receita
                receita = metricas.get('receita', {})
                if receita:
                    print(f"\n   Receita:")
                    print(f"   • Valor: {receita.get('moeda', 'R$')} {receita.get('valor', 0):,.0f} {receita.get('unidade', '')}")
                    if receita.get('variacao_ano'):
                        print(f"   • Variação anual: {receita['variacao_ano']:+.1f}%")
                
                # EBITDA
                ebitda = metricas.get('ebitda', {})
                if ebitda:
                    print(f"\n   EBITDA:")
                    print(f"   • Valor: R$ {ebitda.get('valor', 0):,.0f} milhões")
                    print(f"   • Margem: {ebitda.get('margem', 0):.1f}%")
                
                # Lucro
                lucro = metricas.get('lucro_liquido', {})
                if lucro:
                    print(f"\n   Lucro Líquido:")
                    print(f"   • Valor: R$ {lucro.get('valor', 0):,.0f} milhões")
                    print(f"   • Margem: {lucro.get('margem', 0):.1f}%")
            
            # Destaques
            destaques = analysis.get('destaques', [])
            if destaques:
                print("\n✨ DESTAQUES:")
                for destaque in destaques[:5]:
                    print(f"   • {destaque}")
            
            # Riscos
            riscos = analysis.get('riscos', [])
            if riscos:
                print("\n⚠️  RISCOS:")
                for risco in riscos[:3]:
                    print(f"   • {risco}")
        
        # Uso e custo
        usage = result.get('usage', {})
        print(f"\n📊 USO DA API:")
        print(f"   • Modelo: {usage.get('model', 'N/A')}")
        print(f"   • Tokens entrada: {usage.get('input_tokens', 0):,}")
        print(f"   • Tokens saída: {usage.get('output_tokens', 0):,}")
        print(f"   • 💰 Custo: ${usage.get('cost_usd', 0):.4f}")


def test_single_pdf():
    """Função para testar com um PDF."""
    
    print("🧪 TESTE DE ANÁLISE DE PDF COM CLAUDE")
    print("="*60)
    
    # Verificar bibliotecas
    print("\n📦 Verificando dependências...")
    
    try:
        import dotenv
        print("✅ python-dotenv instalado")
    except:
        print("❌ python-dotenv não instalado")
        print("   Execute: pip install python-dotenv")
        return
    
    try:
        import anthropic
        print("✅ anthropic instalado")
    except:
        print("❌ anthropic não instalado")
        print("   Execute: pip install anthropic")
        return
    
    try:
        import PyPDF2
        print("✅ PyPDF2 instalado")
    except:
        print("⚠️  PyPDF2 não instalado (opcional)")
        print("   Para instalar: pip install PyPDF2")
    
    # Criar cliente
    try:
        cli = ClaudeMCPCLI()
    except Exception as e:
        print(f"\n❌ Erro ao criar cliente: {e}")
        return
    
    # Buscar PDFs para teste
    print("\n🔍 Buscando PDFs para teste...")
    
    test_folders = ["documents/pending", "documents/processed", "documents", "."]
    pdf_found = None
    
    for folder in test_folders:
        folder_path = Path(folder)
        if folder_path.exists():
            pdfs = list(folder_path.glob("*.pdf"))
            if pdfs:
                # Preferir PDFs da VALE
                vale_pdfs = [p for p in pdfs if "VALE" in p.name.upper()]
                if vale_pdfs:
                    pdf_found = vale_pdfs[0]
                else:
                    pdf_found = pdfs[0]
                break
    
    if not pdf_found:
        print("\n❌ Nenhum PDF encontrado para teste!")
        print("   Execute primeiro: python cvm_download_principal.py")
        print("   E baixe alguns releases (opção 3)")
        return
    
    print(f"\n🎯 PDF selecionado para teste: {pdf_found.name}")
    print(f"   Tamanho: {pdf_found.stat().st_size / (1024*1024):.1f} MB")
    
    # Confirmar
    resposta = input("\n▶️  Continuar com a análise? (s/N): ")
    if resposta.lower() != 's':
        print("❌ Análise cancelada")
        return
    
    # Analisar
    print("\n🚀 Iniciando análise...")
    result = cli.analyze_with_content(pdf_found)
    
    # Exibir resultados
    cli.display_results(result)
    
    print("\n✅ Teste concluído!")


if __name__ == "__main__":
    # Executar teste direto
    test_single_pdf()