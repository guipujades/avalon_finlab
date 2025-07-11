"""
Test document agent configuration and status.
"""

from document_agent import DocumentAgent, LLAMA_PARSE_AVAILABLE
import os


def test_document_agent():
    """Test if document agent is properly configured."""
    
    print("="*60)
    print("DOCUMENT AGENT STATUS CHECK")
    print("="*60)
    
    print(f"\n1. LlamaParse disponível: {'✓' if LLAMA_PARSE_AVAILABLE else '✗'}")
    
    if not LLAMA_PARSE_AVAILABLE:
        print("   → Instale com: pip install llama-parse")
        return
    
    api_key = os.getenv("LLAMA_CLOUD_API_KEY")
    print(f"\n2. API Key configurada: {'✓' if api_key else '✗'}")
    
    if not api_key:
        print("   → Configure a variável de ambiente LLAMA_CLOUD_API_KEY")
        print("   → Ou crie um arquivo .env com: LLAMA_CLOUD_API_KEY=sua_chave_aqui")
        print("   → Obtenha sua chave em: https://cloud.llamaindex.ai/")
    
    print("\n3. Criando agent...")
    try:
        agent = DocumentAgent()
        print("   ✓ Agent criado com sucesso")
        
        print(f"\n4. Parser configurado: {'✓' if agent.parser else '✗'}")
        
        print("\n5. Estrutura de diretórios:")
        for dir_name in ['pending', 'processed', 'parsed', 'summaries']:
            dir_path = agent.documents_dir / dir_name
            print(f"   - {dir_name}: {'✓ existe' if dir_path.exists() else '✗ não existe'}")
        
        print("\n6. Status de processamento:")
        status = agent.get_processing_status()
        print(f"   - Documentos pendentes: {status['pending_documents']}")
        print(f"   - Total processados: {status['total_processed']}")
        print(f"   - Última verificação: {status['last_check']}")
        
        if status['pending_documents'] > 0:
            print("\n   Arquivos pendentes:")
            for file in status['pending_files']:
                print(f"   - {file}")
        
        if status['total_processed'] > 0:
            print("\n   Arquivos processados:")
            for file in status['processed_files'][:5]:
                print(f"   - {file}")
            if len(status['processed_files']) > 5:
                print(f"   ... e mais {len(status['processed_files']) - 5} arquivos")
        
    except Exception as e:
        print(f"   ✗ Erro ao criar agent: {e}")
    
    print("\n" + "="*60)
    print("INSTRUÇÕES PARA USO:")
    print("="*60)
    print("\n1. Configure a API key do Llama Cloud")
    print("2. Coloque PDFs na pasta 'documents/pending'")
    print("3. Execute: python document_agent.py")
    print("\nO agent irá:")
    print("- Processar todos os PDFs pendentes")
    print("- Extrair o texto completo")
    print("- Criar resumos automáticos")
    print("- Mover PDFs processados para 'processed'")
    print("\nPara processar um PDF específico:")
    print(">>> from document_agent import DocumentAgent")
    print(">>> agent = DocumentAgent()")
    print(">>> result = agent.parse_pdf_sync('caminho/para/arquivo.pdf')")


if __name__ == "__main__":
    test_document_agent()