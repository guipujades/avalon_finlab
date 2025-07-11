#!/usr/bin/env python3
"""
Exemplo de uso do Agente Economista
====================================
Demonstra como usar o agente para analisar documentos da VALE.
"""

from pathlib import Path
from economist_agent import EconomistAgent
from mcp_pdf_reader import MCPPDFReader

def analisar_release_vale():
    """
    Exemplo: Analisar release de resultados da VALE.
    """
    # Inicializar agente
    agent = EconomistAgent()
    
    # Caminho para o PDF (assumindo que foi baixado pelo sistema CVM)
    pdf_path = Path("documents/pending/VALE_release_resultados_3T24.pdf")
    
    if not pdf_path.exists():
        print("❌ PDF não encontrado. Execute primeiro o download de releases.")
        return
    
    print("🤖 ANÁLISE DO AGENTE ECONOMISTA - VALE")
    print("=" * 60)
    
    # 1. Ler e processar o PDF
    print("\n📄 Processando PDF...")
    pdf_reader = MCPPDFReader()
    chunks = pdf_reader.read_pdf(pdf_path)
    print(f"✅ PDF processado: {len(chunks)} chunks")
    
    # 2. Extrair dados financeiros
    print("\n📊 Extraindo dados financeiros...")
    financial_data = pdf_reader.extract_financial_data(pdf_path)
    
    if financial_data:
        print("✅ Dados extraídos:")
        for table_name, df in financial_data.items():
            print(f"   - {table_name}: {df.shape[0]} linhas x {df.shape[1]} colunas")
    
    # 3. Análise do agente
    print("\n🔍 Análise do Economista:")
    
    # Interpretar release
    interpretation = agent.interpret_earnings_release(
        pdf_path,
        company_name="VALE",
        ticker="VALE3"
    )
    
    print("\n📈 PRINCIPAIS DESTAQUES:")
    for highlight in interpretation.get('highlights', []):
        print(f"   • {highlight}")
    
    print("\n💰 MÉTRICAS FINANCEIRAS:")
    metrics = interpretation.get('metrics', {})
    for metric, value in metrics.items():
        print(f"   • {metric}: {value}")
    
    print("\n📊 ANÁLISE SETORIAL:")
    print(f"   • Setor: {interpretation.get('sector_comparison', {}).get('sector', 'Mineração')}")
    print(f"   • Performance vs Setor: {interpretation.get('sector_comparison', {}).get('performance', 'N/A')}")
    
    print("\n🎯 RISCOS IDENTIFICADOS:")
    for risk in interpretation.get('risks', []):
        print(f"   ⚠️ {risk}")
    
    print("\n💡 OPORTUNIDADES:")
    for opportunity in interpretation.get('opportunities', []):
        print(f"   ✨ {opportunity}")
    
    # 4. Gerar tese de investimento
    print("\n📝 TESE DE INVESTIMENTO:")
    thesis = agent.generate_investment_thesis(
        company_data=interpretation,
        market_context={
            'selic': 11.25,
            'ipca_12m': 4.5,
            'ibovespa_ytd': 8.2
        }
    )
    
    print(f"\nRecomendação: {thesis.get('recommendation', 'NEUTRO')}")
    print(f"Preço Alvo: R$ {thesis.get('target_price', 'N/A')}")
    print(f"Potencial: {thesis.get('upside', 'N/A')}%")
    
    print("\nRacional:")
    for point in thesis.get('rationale', []):
        print(f"   • {point}")
    
    return interpretation, thesis


def comparar_multiplas_empresas():
    """
    Exemplo: Comparar múltiplas empresas do setor.
    """
    agent = EconomistAgent()
    
    empresas = [
        {'ticker': 'VALE3', 'nome': 'Vale'},
        {'ticker': 'PETR4', 'nome': 'Petrobras'},
        {'ticker': 'ITUB4', 'nome': 'Itaú Unibanco'}
    ]
    
    print("\n🏢 ANÁLISE COMPARATIVA DE EMPRESAS")
    print("=" * 60)
    
    for empresa in empresas:
        print(f"\n📊 {empresa['nome']} ({empresa['ticker']}):")
        
        # Simular dados (em produção viriam dos CSVs da CVM)
        mock_data = {
            'revenue': 100000000,
            'ebitda': 40000000,
            'net_income': 20000000,
            'total_assets': 200000000,
            'equity': 100000000
        }
        
        # Análise
        analysis = agent.analyze_financial_statement(
            company_data=mock_data,
            company_name=empresa['nome']
        )
        
        # Comparar com mercado
        comparison = agent.compare_with_market(
            company_metrics=analysis['metrics'],
            sector='materials' if 'VALE' in empresa['ticker'] else 'energy' if 'PETR' in empresa['ticker'] else 'financial'
        )
        
        print(f"   ROE: {analysis['metrics'].get('roe', 0):.1f}% (Setor: {comparison.get('sector_avg_roe', 0):.1f}%)")
        print(f"   Margem EBITDA: {analysis['metrics'].get('ebitda_margin', 0):.1f}%")
        print(f"   Rating: {comparison.get('rating', 'N/A')}")


def analisar_contexto_economico():
    """
    Exemplo: Análise do contexto econômico brasileiro.
    """
    from financial_knowledge import FinancialKnowledge
    
    knowledge = FinancialKnowledge()
    
    print("\n🇧🇷 CONTEXTO ECONÔMICO BRASILEIRO")
    print("=" * 60)
    
    # Indicadores atuais (em produção viriam de APIs)
    indicadores = {
        'SELIC': 11.25,
        'IPCA_12M': 4.50,
        'IGP-M_12M': 3.80,
        'CDI': 11.15,
        'DOLAR': 5.02,
        'IBOVESPA': 128500
    }
    
    print("\n📊 INDICADORES ECONÔMICOS:")
    for indicador, valor in indicadores.items():
        info = knowledge.indicators.get(indicador, {})
        print(f"\n{indicador}:")
        print(f"   Valor: {valor}")
        print(f"   Descrição: {info.get('description', 'N/A')}")
        
        # Interpretação
        if indicador == 'SELIC' and valor > 10:
            print("   ⚠️ Taxa de juros elevada pode impactar valuations")
        elif indicador == 'IPCA_12M' and valor > 4:
            print("   ⚠️ Inflação próxima/acima da meta")
    
    print("\n🎯 IMPLICAÇÕES PARA INVESTIMENTOS:")
    print("   • Juros altos favorecem renda fixa")
    print("   • Empresas alavancadas podem sofrer pressão")
    print("   • Setores defensivos mais atrativos")
    print("   • Atenção a empresas com pricing power")


def main():
    """
    Executa exemplos de uso.
    """
    print("🤖 EXEMPLOS DE USO DO AGENTE ECONOMISTA")
    print("=" * 60)
    
    # Verificar se há PDFs para análise
    pending_path = Path("documents/pending")
    if pending_path.exists() and any(pending_path.glob("*.pdf")):
        print("\n1. Analisando release de resultados...")
        analisar_release_vale()
    else:
        print("\n⚠️ Nenhum PDF encontrado em documents/pending/")
        print("   Execute primeiro o download de releases trimestrais")
    
    # Outros exemplos
    print("\n2. Comparando empresas...")
    comparar_multiplas_empresas()
    
    print("\n3. Analisando contexto econômico...")
    analisar_contexto_economico()


if __name__ == "__main__":
    main()