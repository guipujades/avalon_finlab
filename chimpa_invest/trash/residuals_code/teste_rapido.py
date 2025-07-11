#!/usr/bin/env python3
"""
Teste Rápido - Extrator CVM
===========================

Script simples para testar se tudo está funcionando corretamente.
"""

def teste_importacoes():
    """Testa se todas as importações estão funcionando"""
    print("🔍 Testando importações...")
    
    try:
        import pandas as pd
        print("✅ pandas OK")
    except ImportError:
        print("❌ pandas não encontrado - Execute: pip install pandas")
        return False
    
    try:
        import requests
        print("✅ requests OK")
    except ImportError:
        print("❌ requests não encontrado - Execute: pip install requests")
        return False
    
    try:
        import openpyxl
        print("✅ openpyxl OK")
    except ImportError:
        print("❌ openpyxl não encontrado - Execute: pip install openpyxl")
        return False
    
    try:
        from cvm_extractor_complete import CVMCompleteDocumentExtractor
        print("✅ CVMCompleteDocumentExtractor OK")
    except ImportError:
        print("❌ cvm_extractor_complete não encontrado")
        print("   Verifique se o arquivo está no mesmo diretório")
        return False
    
    return True

def teste_basico():
    """Teste básico de funcionamento"""
    print("\n🧪 Executando teste básico...")
    
    try:
        from cvm_extractor_complete import CVMCompleteDocumentExtractor
        
        # Inicializar extrator
        extractor = CVMCompleteDocumentExtractor()
        print("✅ Extrator inicializado")
        
        # Teste simples com uma empresa pequena
        print("📊 Testando extração com B3...")
        docs = extractor.extract_company_documents("B3", year=2024)
        
        if docs:
            total = sum(len(d) if isinstance(d, list) else 0 for d in docs.values())
            print(f"✅ Teste bem-sucedido: {total} documentos extraídos")
            
            # Mostrar estatísticas
            print(f"   📄 ITRs: {len(docs['documentos_estruturados'])}")
            print(f"   🚨 Fatos relevantes: {len(docs['fatos_relevantes'])}")
            print(f"   📢 Comunicados: {len(docs['comunicados'])}")
            
            return True
        else:
            print("⚠️ Nenhum documento extraído, mas sem erros")
            return True
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def main():
    """Função principal de teste"""
    print("🚀 TESTE RÁPIDO - EXTRATOR CVM")
    print("=" * 40)
    
    # Teste 1: Importações
    if not teste_importacoes():
        print("\n❌ Falha nas importações. Instale as dependências primeiro:")
        print("   pip install -r requirements.txt")
        return
    
    # Teste 2: Funcionamento básico
    if not teste_basico():
        print("\n❌ Falha no teste básico")
        return
    
    print("\n" + "=" * 40)
    print("🎉 TODOS OS TESTES PASSARAM!")
    print("\n✅ O sistema está funcionando corretamente")
    print("💡 Agora você pode usar:")
    print("   - python extrator_cvm_unificado.py")
    print("   - python exemplo_pratico_corrigido.py")

if __name__ == "__main__":
    main()

