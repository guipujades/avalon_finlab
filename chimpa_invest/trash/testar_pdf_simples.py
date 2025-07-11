#!/usr/bin/env python3
"""
Teste simples de processamento de PDF
"""
from pathlib import Path
from document_agent_simples import DocumentAgentSimples

def main():
    agent = DocumentAgentSimples()
    
    # Pegar primeiro PDF da pasta pending
    pending_pdfs = list(agent.pending_dir.glob("*.pdf"))
    
    if not pending_pdfs:
        print("Nenhum PDF encontrado na pasta pending")
        return
    
    pdf_file = pending_pdfs[0]
    print(f"Processando: {pdf_file.name}")
    
    try:
        result = agent.parse_pdf(str(pdf_file), auto_move=False)
        
        if result["status"] == "success":
            print("✓ Processamento bem-sucedido!")
            print(f"  Arquivo de texto: {result['output_file']}")
            print(f"  Arquivo JSON: {result['json_file']}")
            print(f"  Resumo: {result['summary_file']}")
            print(f"  Caracteres: {result['characters']:,}")
            print(f"  Palavras: {result['words']:,}")
            print(f"  Método usado: {result['method_used']}")
            
            # Mostrar preview do texto gerado
            with open(result['output_file'], 'r', encoding='utf-8') as f:
                texto = f.read()
                print(f"\nPreview do texto extraído:")
                print("-" * 50)
                print(texto[:1000] + "..." if len(texto) > 1000 else texto)
                print("-" * 50)
                
            # Mostrar resumo
            with open(result['summary_file'], 'r', encoding='utf-8') as f:
                resumo = f.read()
                print(f"\nResumo gerado:")
                print("=" * 50)
                print(resumo)
                print("=" * 50)
        else:
            print("✗ Erro no processamento:")
            print(f"  {result['error']}")
            
    except Exception as e:
        print(f"✗ Exceção: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()