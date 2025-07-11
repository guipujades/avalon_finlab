#!/usr/bin/env python3
"""
Demonstração do Sistema Interativo de Perplexity
==============================================
Este script demonstra as novas funcionalidades implementadas:
1. Aprovação/rejeição de perguntas
2. Modificação de perguntas
3. Fornecimento de respostas manuais
4. Desconsideração de análises
5. Alertas sobre impactos
"""

def demonstrar_fluxo():
    print("DEMONSTRAÇÃO: Sistema Interativo de Perplexity")
    print("=" * 60)
    
    print("\nFLUXO DE INTERAÇÃO IMPLEMENTADO:")
    print("-" * 40)
    
    print("1. PERGUNTA PROPOSTA:")
    print("   O sistema mostra a pergunta que será enviada")
    print("   Usuário escolhe: [E]nviar / [M]odificar / [P]ular")
    
    print("\n2. RESPOSTA RECEBIDA:")
    print("   Sistema mostra a resposta do Perplexity")
    print("   Exibe fontes e citações")
    print("   Usuário escolhe: [S]im / [N]ão")
    
    print("\n3. SE REJEITADA:")
    print("   Sistema oferece: [F]ornecer resposta / [D]esconsiderar")
    print("   Se fornecer: usuário digita resposta manual")
    print("   Se desconsiderar: análise é excluída com alertas")
    
    print("\n4. RELATÓRIO FINAL:")
    print("   Estatísticas detalhadas por tipo de resposta")
    print("   Alertas sobre análises impactadas")
    print("   Identificação clara no TXT (manual vs Perplexity)")
    
    print("\nEXEMPLO DE USO:")
    print("-" * 30)
    print("# Valuation temporal (automático):")
    print("python3 valuation_empresa_temporal.py BBAS3")
    print()
    print("# Valuation regular (opcional):")
    print("python3 valuation_empresa.py BBAS3 --mercado")
    
    print("\nEXEMPLO DE INTERAÇÃO:")
    print("-" * 30)
    print("Pergunta: Qual o preço atual da ação BBAS3?")
    print("[E]nviar / [M]odificar / [P]ular: E")
    print("Resposta: A ação está cotada a R$ 25,40...")
    print("Aceitar? [S]im / [N]ão: N")
    print("[F]ornecer resposta / [D]esconsiderar: F")
    print("Digite resposta: R$ 26,15 (fonte: B3 tempo real)")
    print("Resposta manual salva!")
    
    print("\nTIPOS DE RESULTADO:")
    print("-" * 25)
    print("Perplexity aprovadas: Respostas da IA aceitas")
    print("Respostas manuais: Fornecidas pelo usuário") 
    print("Desconsideradas: Análises excluídas")
    print("Puladas: Perguntas não enviadas")
    print("Erros: Falhas técnicas")
    
    print("\nSISTEMA DE ALERTAS:")
    print("-" * 22)
    print("- Sem preço atual -> Múltiplos não calculados")
    print("- Sem nº ações -> Market cap indisponível") 
    print("- Sem múltiplos setor -> Comparação limitada")
    print("- Sem dividend yield -> Análise dividendos off")
    
    print("\nVANTAGENS IMPLEMENTADAS:")
    print("-" * 28)
    print("- Controle total sobre dados utilizados")
    print("- Qualidade assegurada das informações")
    print("- Transparência nas fontes")
    print("- Flexibilidade para correções")
    print("- Adaptação inteligente das análises")
    print("- Rastreabilidade completa no relatório")

if __name__ == "__main__":
    demonstrar_fluxo()