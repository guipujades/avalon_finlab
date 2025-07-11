#!/usr/bin/env python3
"""
Análise com Agente Economista
==============================
Integra o agente economista com o sistema CVM para análise inteligente.
"""

import sys
from pathlib import Path
from datetime import datetime

# Adicionar pasta agents ao path
sys.path.append(str(Path(__file__).parent / 'agents'))

from economist_agent import EconomistAgent
from mcp_pdf_reader import MCPPDFReader
from financial_knowledge import FinancialKnowledge


class AnaliseAgenteEconomista:
    """
    Interface para análise com agente economista.
    """
    
    def __init__(self):
        self.agent = EconomistAgent()
        self.pdf_reader = MCPPDFReader()
        self.knowledge = FinancialKnowledge()
        
    def listar_pdfs_disponiveis(self):
        """
        Lista PDFs disponíveis para análise.
        """
        pending_path = Path("documents/pending")
        pdfs = []
        
        if pending_path.exists():
            pdfs = list(pending_path.glob("*.pdf"))
        
        if not pdfs:
            print("\n❌ Nenhum PDF encontrado em documents/pending/")
            print("   Execute primeiro o download de releases trimestrais (opção 3)")
            return []
        
        print(f"\n📄 PDFs disponíveis para análise ({len(pdfs)}):")
        for i, pdf in enumerate(pdfs, 1):
            size_mb = pdf.stat().st_size / (1024 * 1024)
            print(f"   [{i}] {pdf.name} ({size_mb:.1f} MB)")
        
        return pdfs
    
    def analisar_pdf(self, pdf_path):
        """
        Analisa um PDF específico.
        """
        print(f"\n🔍 Analisando: {pdf_path.name}")
        print("=" * 60)
        
        # Extrair nome da empresa do arquivo
        company_name = pdf_path.name.split('_')[0]
        
        # Processar PDF
        print("\n⏳ Processando documento...")
        try:
            chunks = self.pdf_reader.read_pdf(pdf_path)
            print(f"✅ Documento processado: {len(chunks)} chunks")
            
            # Extrair dados financeiros
            financial_data = self.pdf_reader.extract_financial_data(pdf_path)
            if financial_data:
                print(f"✅ Dados financeiros extraídos: {len(financial_data)} tabelas")
            
            # Análise do economista
            interpretation = self.agent.interpret_earnings_release(
                pdf_path,
                company_name=company_name,
                ticker=f"{company_name}3"  # Assumindo ação ON
            )
            
            # Exibir resultados
            self._exibir_analise(interpretation, company_name)
            
            # Salvar análise
            self._salvar_analise(interpretation, company_name)
            
            return interpretation
            
        except Exception as e:
            print(f"❌ Erro ao analisar PDF: {e}")
            return None
    
    def _exibir_analise(self, interpretation, company_name):
        """
        Exibe análise formatada.
        """
        print(f"\n📊 ANÁLISE DO AGENTE ECONOMISTA - {company_name}")
        print("=" * 60)
        
        # Destaques
        if 'highlights' in interpretation:
            print("\n📈 PRINCIPAIS DESTAQUES:")
            for highlight in interpretation['highlights']:
                print(f"   • {highlight}")
        
        # Métricas
        if 'metrics' in interpretation:
            print("\n💰 MÉTRICAS FINANCEIRAS:")
            for metric, value in interpretation['metrics'].items():
                print(f"   • {metric}: {value}")
        
        # Riscos
        if 'risks' in interpretation:
            print("\n⚠️ RISCOS IDENTIFICADOS:")
            for risk in interpretation['risks']:
                print(f"   • {risk}")
        
        # Oportunidades
        if 'opportunities' in interpretation:
            print("\n✨ OPORTUNIDADES:")
            for opp in interpretation['opportunities']:
                print(f"   • {opp}")
        
        # Recomendação
        if 'recommendation' in interpretation:
            print(f"\n🎯 RECOMENDAÇÃO: {interpretation['recommendation']}")
    
    def _salvar_analise(self, interpretation, company_name):
        """
        Salva análise em arquivo.
        """
        import json
        
        output_dir = Path("analises_agente")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"analise_{company_name}_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(interpretation, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Análise salva em: {output_file}")
    
    def comparar_empresas_setor(self):
        """
        Compara empresas do mesmo setor.
        """
        print("\n🏢 ANÁLISE COMPARATIVA SETORIAL")
        print("=" * 60)
        
        # Listar setores disponíveis
        setores = list(self.knowledge.sector_benchmarks.keys())
        
        print("\nSetores disponíveis:")
        for i, setor in enumerate(setores, 1):
            print(f"   [{i}] {setor}")
        
        try:
            escolha = int(input("\nEscolha o setor (número): ")) - 1
            setor = setores[escolha]
            
            print(f"\n📊 Benchmarks do setor {setor}:")
            benchmarks = self.knowledge.sector_benchmarks[setor]
            
            for metric, value in benchmarks.items():
                formula_info = self.knowledge.formulas.get(metric, {})
                print(f"\n{metric}:")
                print(f"   Valor médio: {value}")
                if formula_info:
                    print(f"   Fórmula: {formula_info['formula']}")
                    print(f"   Interpretação: {formula_info['interpretation']}")
            
        except (ValueError, IndexError):
            print("❌ Seleção inválida")
    
    def analisar_contexto_macro(self):
        """
        Análise do contexto macroeconômico.
        """
        print("\n🌍 ANÁLISE DO CONTEXTO MACROECONÔMICO")
        print("=" * 60)
        
        # Simulação de dados (em produção viriam de APIs)
        contexto = {
            'SELIC': {'valor': 11.25, 'variacao': -0.50},
            'IPCA': {'valor': 4.50, 'variacao': 0.15},
            'IGP-M': {'valor': 3.80, 'variacao': -0.20},
            'CDI': {'valor': 11.15, 'variacao': -0.50},
            'USD/BRL': {'valor': 5.02, 'variacao': 2.10},
            'IBOVESPA': {'valor': 128500, 'variacao': 8.5}
        }
        
        print("\n📊 INDICADORES ECONÔMICOS:")
        for indicador, dados in contexto.items():
            info = self.knowledge.indicators.get(indicador.replace('/', '_'), {})
            print(f"\n{indicador}:")
            print(f"   Valor atual: {dados['valor']}")
            print(f"   Variação YTD: {dados['variacao']:+.1f}%")
            if info:
                print(f"   Impacto: {info.get('impact', 'N/A')}")
        
        print("\n🎯 IMPLICAÇÕES PARA O MERCADO:")
        
        # Análise baseada nos indicadores
        if contexto['SELIC']['valor'] > 10:
            print("\n📌 Taxa de Juros Elevada:")
            print("   • Pressão sobre empresas alavancadas")
            print("   • Renda fixa mais atrativa")
            print("   • Valuations sob pressão")
        
        if contexto['IPCA']['valor'] > 4.0:
            print("\n📌 Inflação Próxima/Acima da Meta:")
            print("   • Empresas com pricing power beneficiadas")
            print("   • Atenção a margens de lucro")
            print("   • Possível alta adicional de juros")
        
        if contexto['USD/BRL']['valor'] > 5.0:
            print("\n📌 Dólar Elevado:")
            print("   • Exportadoras beneficiadas")
            print("   • Pressão sobre importadoras")
            print("   • Inflação importada")


def menu_analise_agente():
    """
    Menu principal da análise com agente.
    """
    analise = AnaliseAgenteEconomista()
    
    while True:
        print("\n🤖 ANÁLISE COM AGENTE ECONOMISTA")
        print("=" * 60)
        print("[1] Analisar PDF de release de resultados")
        print("[2] Análise comparativa setorial")
        print("[3] Contexto macroeconômico")
        print("[4] Voltar ao menu principal")
        
        escolha = input("\nEscolha uma opção: ")
        
        if escolha == '1':
            pdfs = analise.listar_pdfs_disponiveis()
            if pdfs:
                try:
                    idx = int(input("\nEscolha o PDF (número): ")) - 1
                    if 0 <= idx < len(pdfs):
                        analise.analisar_pdf(pdfs[idx])
                    else:
                        print("❌ Seleção inválida")
                except ValueError:
                    print("❌ Entrada inválida")
        
        elif escolha == '2':
            analise.comparar_empresas_setor()
        
        elif escolha == '3':
            analise.analisar_contexto_macro()
        
        elif escolha == '4':
            break
        
        else:
            print("❌ Opção inválida")
        
        input("\n✅ Pressione ENTER para continuar...")


if __name__ == "__main__":
    menu_analise_agente()