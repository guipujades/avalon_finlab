#!/usr/bin/env python3
"""
Análise Direta com Claude
=========================
Interface para análise de PDFs usando a capacidade nativa do Claude.
"""

import sys
from pathlib import Path
from datetime import datetime
import json

sys.path.append(str(Path(__file__).parent / 'agents'))

from claude_pdf_analyzer import ClaudePDFAnalyzer, SmartPDFChat


class AnaliseClaudeDireto:
    """
    Interface simplificada para análise com Claude.
    """
    
    def __init__(self):
        self.analyzer = ClaudePDFAnalyzer()
        self.chat = SmartPDFChat()
        
    def menu_principal(self):
        """Menu principal de análise."""
        while True:
            print("\n🤖 ANÁLISE DE PDFs COM CLAUDE")
            print("=" * 60)
            print("\n📌 COMO FUNCIONA:")
            print("   1. Este sistema gera prompts otimizados")
            print("   2. Você fornece o PDF ao Claude")
            print("   3. Claude analisa diretamente o conteúdo")
            print("\n" + "=" * 60)
            
            print("\n📊 TIPOS DE ANÁLISE:")
            print("[1] Análise Financeira Completa")
            print("[2] Sumário Executivo")
            print("[3] Tese de Investimento")
            print("[4] Análise Comparativa (múltiplos PDFs)")
            print("[5] Chat Interativo sobre PDF")
            print("[6] Análise de Surpresas vs Consenso")
            print("[0] Voltar")
            
            escolha = input("\nEscolha o tipo de análise: ")
            
            if escolha == "0":
                break
            elif escolha in ["1", "2", "3", "5", "6"]:
                self.analisar_pdf_individual(escolha)
            elif escolha == "4":
                self.analisar_multiplos_pdfs()
            else:
                print("❌ Opção inválida")
    
    def listar_pdfs(self) -> list:
        """Lista PDFs disponíveis."""
        pending = Path("documents/pending")
        pdfs = []
        
        if pending.exists():
            pdfs = list(pending.glob("*.pdf"))
        
        if not pdfs:
            # Tentar outras pastas
            for folder in ["documents", "downloads", "."]:
                folder_path = Path(folder)
                if folder_path.exists():
                    pdfs.extend(folder_path.glob("*.pdf"))
        
        return sorted(set(pdfs))
    
    def analisar_pdf_individual(self, tipo_analise: str):
        """Analisa um PDF individual."""
        pdfs = self.listar_pdfs()
        
        if not pdfs:
            print("\n❌ Nenhum PDF encontrado!")
            print("   Coloque PDFs em 'documents/pending/' ou execute download primeiro")
            return
        
        print(f"\n📄 PDFs DISPONÍVEIS ({len(pdfs)}):")
        for i, pdf in enumerate(pdfs, 1):
            size_mb = pdf.stat().st_size / (1024 * 1024)
            print(f"[{i}] {pdf.name} ({size_mb:.1f} MB)")
        
        try:
            idx = int(input("\nEscolha o PDF (número): ")) - 1
            if 0 <= idx < len(pdfs):
                pdf_path = pdfs[idx]
                self.gerar_prompt_analise(pdf_path, tipo_analise)
            else:
                print("❌ Seleção inválida")
        except ValueError:
            print("❌ Entrada inválida")
    
    def gerar_prompt_analise(self, pdf_path: Path, tipo: str):
        """Gera e exibe prompt para análise."""
        print(f"\n📄 PDF Selecionado: {pdf_path.name}")
        print("=" * 60)
        
        if tipo == "1":
            # Análise completa
            result = self.analyzer.analyze_financial_pdf(pdf_path)
            prompt = result["prompt"]
            titulo = "ANÁLISE FINANCEIRA COMPLETA"
            
        elif tipo == "2":
            # Sumário executivo
            prompt = self.chat.generate_executive_summary(pdf_path)
            titulo = "SUMÁRIO EXECUTIVO"
            
        elif tipo == "3":
            # Tese de investimento
            market = self.obter_contexto_mercado()
            prompt = self.analyzer.generate_investment_thesis(pdf_path, market)
            titulo = "TESE DE INVESTIMENTO"
            
        elif tipo == "5":
            # Chat interativo
            session = self.chat.prepare_analysis_session(pdf_path)
            prompt = session["initial_prompt"]
            titulo = "CHAT INTERATIVO"
            
            print(f"\n💬 PERGUNTAS SUGERIDAS:")
            for q in session["suggested_questions"]:
                print(f"   • {q}")
            
        elif tipo == "6":
            # Análise de surpresas
            expectations = self.obter_expectativas()
            prompt = self.analyzer.analyze_earnings_surprises(pdf_path, expectations)
            titulo = "ANÁLISE DE SURPRESAS"
        
        # Exibir prompt
        print(f"\n📋 PROMPT PARA {titulo}:")
        print("=" * 60)
        print(prompt)
        print("=" * 60)
        
        # Salvar prompt
        self.salvar_prompt(prompt, pdf_path, titulo)
        
        print("\n✅ PRÓXIMOS PASSOS:")
        print("1. Copie o prompt acima")
        print("2. Abra uma nova conversa com Claude")
        print("3. Cole o prompt E forneça o PDF")
        print("4. Claude analisará o documento diretamente")
        
        print(f"\n💡 DICA: O PDF está em: {pdf_path.absolute()}")
    
    def analisar_multiplos_pdfs(self):
        """Análise comparativa de múltiplos PDFs."""
        pdfs = self.listar_pdfs()
        
        if len(pdfs) < 2:
            print("\n❌ Precisa de pelo menos 2 PDFs para análise comparativa")
            return
        
        print(f"\n📄 SELECIONE PDFs PARA COMPARAR ({len(pdfs)} disponíveis):")
        for i, pdf in enumerate(pdfs, 1):
            print(f"[{i}] {pdf.name}")
        
        print("\nDigite os números separados por vírgula (ex: 1,3,5):")
        try:
            indices = [int(x.strip())-1 for x in input().split(",")]
            pdfs_selecionados = [pdfs[i] for i in indices if 0 <= i < len(pdfs)]
            
            if len(pdfs_selecionados) >= 2:
                result = self.analyzer.analyze_multiple_pdfs(pdfs_selecionados)
                
                print("\n📋 PROMPT PARA ANÁLISE COMPARATIVA:")
                print("=" * 60)
                print(result["prompt"])
                print("=" * 60)
                
                print("\n✅ Forneça todos os PDFs listados ao Claude junto com o prompt")
            else:
                print("❌ Selecione pelo menos 2 PDFs")
                
        except (ValueError, IndexError):
            print("❌ Seleção inválida")
    
    def obter_contexto_mercado(self) -> dict:
        """Obtém contexto de mercado para análise."""
        print("\n📊 CONTEXTO DE MERCADO (Enter para usar padrão):")
        
        try:
            selic = input("Taxa SELIC atual (%) [10.50]: ").strip()
            selic = float(selic) if selic else 10.50
            
            inflacao = input("IPCA 12 meses (%) [4.50]: ").strip()
            inflacao = float(inflacao) if inflacao else 4.50
            
            dolar = input("USD/BRL [5.00]: ").strip()
            dolar = float(dolar) if dolar else 5.00
            
            ibov = input("IBOVESPA [125000]: ").strip()
            ibov = int(ibov) if ibov else 125000
            
            return {
                "selic": selic,
                "inflacao_ipca": inflacao,
                "dolar": dolar,
                "ibovespa": ibov,
                "data": datetime.now().strftime("%Y-%m-%d")
            }
        except ValueError:
            print("⚠️ Valores inválidos, usando padrões")
            return {
                "selic": 10.50,
                "inflacao_ipca": 4.50,
                "dolar": 5.00,
                "ibovespa": 125000,
                "data": datetime.now().strftime("%Y-%m-%d")
            }
    
    def obter_expectativas(self) -> dict:
        """Obtém expectativas de consenso."""
        print("\n📊 EXPECTATIVAS DE CONSENSO (Enter para pular):")
        
        exp = {}
        
        receita = input("Receita esperada (R$ mi): ").strip()
        if receita:
            exp["receita_esperada"] = float(receita)
        
        ebitda = input("EBITDA esperado (R$ mi): ").strip()
        if ebitda:
            exp["ebitda_esperado"] = float(ebitda)
        
        lucro = input("Lucro esperado (R$ mi): ").strip()
        if lucro:
            exp["lucro_esperado"] = float(lucro)
        
        if not exp:
            print("⚠️ Sem expectativas definidas")
            exp = {
                "nota": "Análise sem consenso prévio",
                "foco": "Comparação com trimestres anteriores"
            }
        
        return exp
    
    def salvar_prompt(self, prompt: str, pdf_path: Path, tipo: str):
        """Salva prompt gerado."""
        output_dir = Path("prompts_claude")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"prompt_{pdf_path.stem}_{tipo.lower().replace(' ', '_')}_{timestamp}.txt"
        
        output_path = output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"PDF: {pdf_path}\n")
            f.write(f"Tipo: {tipo}\n")
            f.write(f"Data: {datetime.now()}\n")
            f.write("=" * 60 + "\n\n")
            f.write(prompt)
        
        print(f"\n💾 Prompt salvo em: {output_path}")


def main():
    """Função principal."""
    print("🤖 ANÁLISE DIRETA COM CLAUDE")
    print("=" * 60)
    print("\n📌 Este sistema gera prompts otimizados para o Claude")
    print("   analisar PDFs financeiros usando sua capacidade nativa.")
    
    analise = AnaliseClaudeDireto()
    analise.menu_principal()


if __name__ == "__main__":
    main()