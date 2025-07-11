#!/usr/bin/env python3
"""
Exemplo Básico - Extrator CVM
=============================

Este exemplo mostra como usar o extrator de forma simples
para extrair documentos de uma empresa específica.
"""

from cvm_extractor_complete import CVMCompleteDocumentExtractor
import json

def exemplo_basico():
    """
    Exemplo básico de extração de documentos.
    """
    print("=== EXEMPLO BÁSICO - EXTRATOR CVM ===\n")
    
    # 1. Criar o extrator
    print("1. Inicializando extrator...")
    extractor = CVMCompleteDocumentExtractor()
    
    # 2. Extrair documentos de uma empresa
    empresa = "PETROBRAS"
    ano = 2024
    
    print(f"2. Extraindo documentos de {empresa} ({ano})...")
    documentos = extractor.extract_company_documents(empresa, year=ano)
    
    # 3. Mostrar estatísticas
    print(f"\n3. Resultados para {empresa}:")
    print(f"   ✓ Documentos estruturados: {len(documentos['documentos_estruturados'])}")
    print(f"   ✓ Fatos relevantes: {len(documentos['fatos_relevantes'])}")
    print(f"   ✓ Comunicados: {len(documentos['comunicados'])}")
    print(f"   ✓ Assembleias: {len(documentos['assembleias'])}")
    print(f"   ✓ Outros documentos: {len(documentos['outros_documentos'])}")
    
    total = sum(len(docs) if isinstance(docs, list) else 0 for docs in documentos.values())
    print(f"   📊 Total: {total} documentos")
    
    # 4. Mostrar exemplos de fatos relevantes
    if documentos['fatos_relevantes']:
        print(f"\n4. Últimos fatos relevantes:")
        for i, fato in enumerate(documentos['fatos_relevantes'][:5], 1):
            print(f"   {i}. {fato['data_entrega']}: {fato['assunto']}")
    
    # 5. Salvar resultados
    print(f"\n5. Salvando resultados...")
    
    # Salvar em JSON
    filename_json = f"{empresa.lower()}_documentos.json"
    extractor.save_to_json({empresa: documentos}, filename_json)
    print(f"   ✓ JSON salvo: {filename_json}")
    
    # Salvar em Excel
    filename_excel = f"{empresa.lower()}_documentos.xlsx"
    extractor.save_to_excel({empresa: documentos}, filename_excel)
    print(f"   ✓ Excel salvo: {filename_excel}")
    
    print(f"\n✅ Exemplo concluído com sucesso!")
    return documentos

def exemplo_fatos_relevantes():
    """
    Exemplo focado apenas em fatos relevantes.
    """
    print("\n=== EXEMPLO: APENAS FATOS RELEVANTES ===\n")
    
    extractor = CVMCompleteDocumentExtractor()
    
    # Extrair apenas documentos eventuais (sem ITRs)
    empresa = "VALE"
    documentos = extractor.extract_company_documents(
        empresa, 
        year=2024,
        include_structured=False,  # Não incluir ITRs
        include_events=True        # Incluir fatos relevantes
    )
    
    fatos = documentos['fatos_relevantes']
    print(f"Fatos relevantes da {empresa}: {len(fatos)}")
    
    if fatos:
        print("\nÚltimos 3 fatos relevantes:")
        for i, fato in enumerate(fatos[:3], 1):
            print(f"\n{i}. Data: {fato['data_entrega']}")
            print(f"   Assunto: {fato['assunto']}")
            print(f"   Link: {fato['link_download']}")
    
    return fatos

def exemplo_comunicados():
    """
    Exemplo focado em comunicados ao mercado.
    """
    print("\n=== EXEMPLO: COMUNICADOS AO MERCADO ===\n")
    
    extractor = CVMCompleteDocumentExtractor()
    
    empresa = "B3"
    documentos = extractor.extract_company_documents(empresa, year=2024)
    
    comunicados = documentos['comunicados']
    print(f"Comunicados da {empresa}: {len(comunicados)}")
    
    if comunicados:
        print("\nÚltimos 3 comunicados:")
        for i, com in enumerate(comunicados[:3], 1):
            print(f"\n{i}. Data: {com['data_entrega']}")
            print(f"   Assunto: {com['assunto']}")
            print(f"   Tipo: {com['tipo_doc']}")
    
    return comunicados

if __name__ == "__main__":
    # Executar exemplos
    try:
        # Exemplo básico completo
        docs = exemplo_basico()
        
        # Exemplo de fatos relevantes
        fatos = exemplo_fatos_relevantes()
        
        # Exemplo de comunicados
        comunicados = exemplo_comunicados()
        
        print("\n🎉 Todos os exemplos executados com sucesso!")
        
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        print("Verifique sua conexão com a internet e tente novamente.")

