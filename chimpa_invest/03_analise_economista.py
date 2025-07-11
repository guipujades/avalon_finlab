#!/usr/bin/env python3
"""
Interface para Análise com Agente Economista
============================================
Analisa releases financeiros e gera resumos executivos de 1 minuto.
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent / 'agents'))

from economist_agent_free import EconomistAgentFree


def menu_principal():
    """Menu principal do agente economista."""
    
    agent = EconomistAgentFree()
    
    while True:
        print("\nAGENTE ECONOMISTA - Análise de Releases")
        print("="*60)
        print("[1] Analisar release mais recente (qualquer empresa)")
        print("[2] Analisar release mais recente de empresa específica")
        print("[3] Ver resumos anteriores")
        print("[4] Verificar documentos disponíveis")
        print("[0] Voltar ao menu principal")
        
        escolha = input("\nEscolha uma opção: ")
        
        if escolha == "0":
            break
            
        elif escolha == "1":
            print("\nAnalisando release mais recente...")
            result = agent.process_latest_release()
            
            if result:
                print(f"\nAnálise concluída!")
                print(f"Resumo salvo em: {result['file']}")
            
        elif escolha == "2":
            empresa = input("\nDigite o nome da empresa (ex: VALE, PETROBRAS): ").strip().upper()
            if empresa:
                print(f"\nAnalisando release mais recente de {empresa}...")
                result = agent.process_latest_release(empresa)
                
                if result:
                    print(f"\nAnálise concluída!")
                    print(f"Resumo salvo em: {result['file']}")
            
        elif escolha == "3":
            summaries_dir = Path("summaries")
            if summaries_dir.exists():
                summaries = list(summaries_dir.glob("*.md"))
                if summaries:
                    print(f"\nResumos disponíveis ({len(summaries)}):")
                    
                    # Ordenar por data (mais recente primeiro)
                    summaries.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                    
                    for i, summary in enumerate(summaries[:10], 1):
                        mod_time = datetime.fromtimestamp(summary.stat().st_mtime)
                        print(f"[{i}] {summary.name} - {mod_time.strftime('%d/%m/%Y %H:%M')}")
                    
                    if len(summaries) > 10:
                        print(f"... e mais {len(summaries)-10} resumos")
                    
                    # Opção de visualizar
                    ver = input("\nDigite o número para visualizar (ou Enter para voltar): ")
                    if ver.isdigit() and 1 <= int(ver) <= min(10, len(summaries)):
                        with open(summaries[int(ver)-1], 'r', encoding='utf-8') as f:
                            print("\n" + "="*60)
                            print(f.read())
                            print("="*60)
                else:
                    print("\nNenhum resumo encontrado ainda")
            else:
                print("\nPasta de resumos não existe ainda")
        
        elif escolha == "4":
            parsed_dir = Path("documents/parsed")
            if parsed_dir.exists():
                docs = list(parsed_dir.glob("*.json"))
                if docs:
                    print(f"\nDocumentos processados disponíveis ({len(docs)}):")
                    
                    # Ordenar por data
                    docs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                    
                    # Agrupar por empresa
                    by_company = {}
                    for doc in docs:
                        company = doc.name.split('_')[0]
                        if company not in by_company:
                            by_company[company] = []
                        by_company[company].append(doc)
                    
                    for company, company_docs in by_company.items():
                        print(f"\n{company}: {len(company_docs)} documentos")
                        for doc in company_docs[:3]:
                            mod_time = datetime.fromtimestamp(doc.stat().st_mtime)
                            print(f"  - {doc.name} ({mod_time.strftime('%d/%m/%Y')})")
                        if len(company_docs) > 3:
                            print(f"  ... e mais {len(company_docs)-3}")
                else:
                    print("\nNenhum documento processado encontrado")
                    print("   Execute o document_agent primeiro para processar PDFs")
            else:
                print("\nPasta 'documents/parsed' não encontrada")
        
        if escolha != "0":
            input("\nPressione ENTER para continuar...")


if __name__ == "__main__":
    menu_principal()