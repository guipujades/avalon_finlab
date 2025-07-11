#!/usr/bin/env python3
"""
EXEMPLO COMPLETO - EXTRAÇÃO + DOWNLOAD REAL
===========================================

Este exemplo mostra como usar o sistema completo para:
1. Extrair metadados de documentos CVM
2. Baixar os arquivos reais (PDFs) para sua máquina
3. Organizar tudo em pastas estruturadas

ATENÇÃO: Este exemplo baixa arquivos reais da CVM!
"""

from cvm_extractor_complete import CVMCompleteDocumentExtractor
from cvm_document_downloader import CVMDocumentDownloader
import json
from datetime import datetime

def exemplo_download_real():
    """
    Exemplo de download real de documentos CVM.
    """
    print("🚀 EXEMPLO COMPLETO - EXTRAÇÃO + DOWNLOAD REAL")
    print("=" * 60)
    print("⚠️  ATENÇÃO: Este exemplo baixa arquivos reais da CVM!")
    print("=" * 60)
    
    # Confirmar se usuário quer continuar
    confirma = input("\nDeseja continuar com o download real? (s/N): ").lower()
    if not confirma.startswith('s'):
        print("❌ Operação cancelada pelo usuário")
        return
    
    # Inicializar sistemas
    print("\n🔧 Inicializando sistemas...")
    extractor = CVMCompleteDocumentExtractor()
    downloader = CVMDocumentDownloader("documentos_reais_cvm")
    
    # Empresa para teste (escolher uma menor para não sobrecarregar)
    empresa = "B3"  # B3 tem menos documentos, ideal para teste
    
    print(f"\n📊 Extraindo metadados de {empresa}...")
    docs = extractor.extract_company_documents(empresa, year=2024)
    
    if not docs:
        print(f"❌ Nenhum documento encontrado para {empresa}")
        return
    
    # Mostrar estatísticas
    total_docs = sum(len(d) if isinstance(d, list) else 0 for d in docs.values())
    print(f"✅ Metadados extraídos: {total_docs} documentos")
    print(f"   📄 ITRs: {len(docs['documentos_estruturados'])}")
    print(f"   🚨 Fatos relevantes: {len(docs['fatos_relevantes'])}")
    print(f"   📢 Comunicados: {len(docs['comunicados'])}")
    print(f"   🏛️ Assembleias: {len(docs['assembleias'])}")
    
    # Perguntar quantos baixar
    print(f"\n📥 CONFIGURAÇÃO DE DOWNLOAD:")
    limite_str = input("Quantos documentos baixar por tipo? (ENTER = 2): ").strip()
    limite = int(limite_str) if limite_str.isdigit() else 2
    
    tipos_escolhidos = []
    if input("Baixar fatos relevantes? (S/n): ").lower() != 'n':
        tipos_escolhidos.append('fatos_relevantes')
    if input("Baixar comunicados? (s/N): ").lower().startswith('s'):
        tipos_escolhidos.append('comunicados')
    if input("Baixar ITRs? (s/N): ").lower().startswith('s'):
        tipos_escolhidos.append('documentos_estruturados')
    
    if not tipos_escolhidos:
        print("❌ Nenhum tipo selecionado")
        return
    
    print(f"\n📥 Iniciando downloads de {empresa}...")
    print(f"   📋 Tipos: {', '.join(tipos_escolhidos)}")
    print(f"   🔢 Limite por tipo: {limite}")
    
    # Realizar downloads
    resultado = downloader.download_company_documents(
        docs, 
        empresa,
        tipos_documento=tipos_escolhidos,
        limite_por_tipo=limite
    )
    
    # Salvar relatório
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"relatorio_download_{empresa.lower()}_{timestamp}.json"
    downloader.save_download_report(resultado, report_file)
    
    # Mostrar resultados
    stats = resultado['estatisticas']
    print(f"\n📊 RESULTADOS FINAIS:")
    print(f"   ✅ Downloads bem-sucedidos: {stats['downloads_sucesso']}")
    print(f"   ❌ Downloads com erro: {stats['downloads_erro']}")
    print(f"   📁 Arquivos já existentes: {stats['arquivos_existentes']}")
    
    # Listar arquivos baixados
    arquivos = downloader.list_downloaded_files(empresa)
    if arquivos['arquivos']:
        print(f"\n📁 Arquivos baixados ({arquivos['total_arquivos']}):")
        for arquivo in arquivos['arquivos'][:5]:  # Mostrar apenas os primeiros 5
            nome = arquivo['arquivo'].split('/')[-1]
            tamanho_kb = arquivo['tamanho'] / 1024
            print(f"   📄 {nome} ({tamanho_kb:.1f} KB)")
        
        if len(arquivos['arquivos']) > 5:
            print(f"   ... e mais {len(arquivos['arquivos']) - 5} arquivos")
    
    print(f"\n💾 Relatório detalhado salvo: {report_file}")
    print(f"📁 Arquivos salvos em: documentos_reais_cvm/{empresa.upper()}/")
    
    return resultado

def exemplo_multiplas_empresas():
    """
    Exemplo de download de múltiplas empresas (quantidade limitada).
    """
    print("\n🏭 EXEMPLO - MÚLTIPLAS EMPRESAS")
    print("=" * 40)
    
    # Lista de empresas pequenas para teste
    empresas_teste = ["B3", "AMBEV"]  # Empresas com menos documentos
    
    print(f"📋 Empresas para teste: {', '.join(empresas_teste)}")
    confirma = input("Continuar com download? (s/N): ").lower()
    
    if not confirma.startswith('s'):
        print("❌ Operação cancelada")
        return
    
    # Inicializar sistemas
    extractor = CVMCompleteDocumentExtractor()
    downloader = CVMDocumentDownloader("downloads_multiplas")
    
    resultados = {}
    
    for i, empresa in enumerate(empresas_teste, 1):
        print(f"\n📊 Processando {i}/{len(empresas_teste)}: {empresa}")
        print("-" * 30)
        
        # Extrair metadados
        docs = extractor.extract_company_documents(empresa, year=2024)
        
        if docs:
            # Baixar apenas 1 fato relevante de cada empresa para teste
            resultado = downloader.download_company_documents(
                docs, 
                empresa,
                tipos_documento=['fatos_relevantes'],
                limite_por_tipo=1
            )
            
            resultados[empresa] = resultado
            
            stats = resultado['estatisticas']
            print(f"   ✅ {stats['downloads_sucesso']} downloads, {stats['downloads_erro']} erros")
        else:
            print(f"   ❌ Nenhum documento encontrado")
    
    # Relatório final
    total_downloads = sum(r['estatisticas']['downloads_sucesso'] for r in resultados.values())
    total_erros = sum(r['estatisticas']['downloads_erro'] for r in resultados.values())
    
    print(f"\n📊 RESUMO FINAL:")
    print(f"   🏢 Empresas processadas: {len(resultados)}")
    print(f"   ✅ Total de downloads: {total_downloads}")
    print(f"   ❌ Total de erros: {total_erros}")
    
    return resultados

def exemplo_apenas_metadados():
    """
    Exemplo de extração apenas de metadados (sem download).
    """
    print("\n📊 EXEMPLO - APENAS METADADOS")
    print("=" * 35)
    
    extractor = CVMCompleteDocumentExtractor()
    
    empresa = "PETROBRAS"
    print(f"📋 Extraindo metadados de {empresa}...")
    
    docs = extractor.extract_company_documents(empresa, year=2024)
    
    if docs:
        # Salvar metadados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"metadados_{empresa.lower()}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(docs, f, ensure_ascii=False, indent=2, default=str)
        
        # Estatísticas
        total_docs = sum(len(d) if isinstance(d, list) else 0 for d in docs.values())
        print(f"✅ {total_docs} documentos catalogados")
        print(f"💾 Metadados salvos: {filename}")
        
        # Mostrar alguns exemplos de links
        if docs['fatos_relevantes']:
            print(f"\n🔗 Exemplos de links de fatos relevantes:")
            for i, fato in enumerate(docs['fatos_relevantes'][:3], 1):
                print(f"   {i}. {fato['assunto'][:50]}...")
                print(f"      Link: {fato['link_download']}")
        
        return docs
    else:
        print(f"❌ Nenhum documento encontrado")
        return None

def main():
    """
    Função principal com menu de exemplos.
    """
    print("🎯 EXEMPLOS DE DOWNLOAD REAL CVM")
    print("=" * 40)
    print("Escolha um exemplo para executar:")
    print()
    print("1. 📥 Download real de uma empresa (B3)")
    print("2. 🏭 Download de múltiplas empresas (limitado)")
    print("3. 📊 Apenas extrair metadados (sem download)")
    print("4. ❌ Sair")
    
    while True:
        try:
            opcao = input("\n👉 Escolha uma opção (1-4): ").strip()
            
            if opcao == "1":
                exemplo_download_real()
                break
            elif opcao == "2":
                exemplo_multiplas_empresas()
                break
            elif opcao == "3":
                exemplo_apenas_metadados()
                break
            elif opcao == "4":
                print("👋 Saindo...")
                break
            else:
                print("❌ Opção inválida. Tente novamente.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Exemplo interrompido pelo usuário")
            break
        except Exception as e:
            print(f"\n❌ Erro: {e}")
            break

if __name__ == "__main__":
    main()

