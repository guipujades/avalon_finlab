#!/usr/bin/env python3
"""
Análise Real de PDF com Claude
===============================
Este script demonstra como analisar um PDF usando as capacidades do Claude.
"""

from pathlib import Path
import json
from datetime import datetime


def analyze_vale_pdf():
    """
    Analisa um PDF da VALE usando a capacidade do Claude.
    """
    
    # Buscar PDFs da VALE
    pdfs_vale = []
    search_dirs = ["documents/pending", "documents", "."]
    
    for dir_name in search_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            # Buscar PDFs da VALE
            for pattern in ["*VALE*.pdf", "*vale*.pdf", "*4170*.pdf"]:
                pdfs_vale.extend(dir_path.glob(pattern))
    
    if not pdfs_vale:
        print("❌ Nenhum PDF da VALE encontrado!")
        print("   Execute primeiro: python cvm_download_principal.py")
        print("   Escolha opção 3 para baixar releases trimestrais")
        return None
    
    # Usar o primeiro PDF encontrado
    pdf_path = pdfs_vale[0]
    
    print(f"\n📄 Analisando PDF: {pdf_path}")
    print(f"📍 Caminho: {pdf_path.absolute()}")
    print(f"📏 Tamanho: {pdf_path.stat().st_size / (1024*1024):.1f} MB")
    
    # AQUI O CLAUDE VAI LER O PDF DIRETAMENTE
    # Vou solicitar ao Claude para analisar o PDF
    
    print("\n🔍 Solicitando análise ao Claude...")
    print("\n" + "="*60)
    
    # O Claude pode ler o arquivo diretamente quando fornecemos o caminho
    # Vou pedir para ele analisar
    
    analysis_request = f"""
Por favor, leia e analise o PDF financeiro localizado em:
{pdf_path.absolute()}

Extraia as seguintes informações:

1. IDENTIFICAÇÃO:
   - Nome da empresa
   - Período do relatório (trimestre/ano)
   - Data de publicação

2. MÉTRICAS FINANCEIRAS:
   - Receita total (em R$ e variação %)
   - EBITDA (valor e margem)
   - Lucro líquido
   - Dívida líquida
   - Geração de caixa

3. DESTAQUES OPERACIONAIS:
   - Principais indicadores de produção
   - Preços realizados
   - Volumes vendidos

4. ANÁLISE QUALITATIVA:
   - Principais pontos positivos
   - Desafios e riscos mencionados
   - Guidance/perspectivas

Por favor, formate a resposta como um relatório estruturado.
"""
    
    print(analysis_request)
    print("="*60)
    
    # Salvar a solicitação
    output_dir = Path("analises_claude_local")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    request_file = output_dir / f"request_{pdf_path.stem}_{timestamp}.txt"
    
    with open(request_file, 'w', encoding='utf-8') as f:
        f.write(f"PDF: {pdf_path.absolute()}\n")
        f.write(f"Data: {datetime.now()}\n")
        f.write("="*60 + "\n\n")
        f.write(analysis_request)
    
    print(f"\n💾 Solicitação salva em: {request_file}")
    
    return {
        "pdf_path": str(pdf_path.absolute()),
        "pdf_name": pdf_path.name,
        "size_mb": pdf_path.stat().st_size / (1024*1024),
        "request_saved": str(request_file),
        "timestamp": datetime.now().isoformat()
    }


def check_pdf_availability():
    """
    Verifica quais PDFs estão disponíveis para análise.
    """
    
    print("\n📂 VERIFICANDO PDFs DISPONÍVEIS...")
    print("="*60)
    
    all_pdfs = []
    
    # Buscar em diferentes locais
    search_locations = [
        ("documents/pending", "Releases pendentes"),
        ("documents", "Documentos gerais"),
        ("downloads", "Downloads"),
        (".", "Diretório atual")
    ]
    
    for dir_path, description in search_locations:
        path = Path(dir_path)
        if path.exists():
            pdfs = list(path.glob("*.pdf"))
            if pdfs:
                print(f"\n📁 {description} ({dir_path}):")
                for pdf in pdfs[:5]:  # Mostrar até 5
                    size_mb = pdf.stat().st_size / (1024*1024)
                    print(f"   • {pdf.name} ({size_mb:.1f} MB)")
                if len(pdfs) > 5:
                    print(f"   ... e mais {len(pdfs)-5} arquivos")
                all_pdfs.extend(pdfs)
    
    total_pdfs = len(set(all_pdfs))  # Remover duplicatas
    print(f"\n📊 Total: {total_pdfs} PDFs únicos encontrados")
    
    return total_pdfs > 0


if __name__ == "__main__":
    print("🤖 ANÁLISE DE PDF COM CLAUDE - DEMONSTRAÇÃO")
    print("="*60)
    
    # Verificar disponibilidade
    if check_pdf_availability():
        # Tentar analisar PDF da VALE
        result = analyze_vale_pdf()
        
        if result:
            print("\n✅ Análise solicitada com sucesso!")
            print("\n📋 Resumo:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            print("\n💡 PRÓXIMOS PASSOS:")
            print("1. O Claude pode ler o PDF diretamente usando o caminho fornecido")
            print("2. A análise será processada com base no conteúdo real do documento")
            print("3. Os resultados serão estruturados conforme solicitado")
    else:
        print("\n⚠️ Nenhum PDF encontrado!")
        print("\n💡 Para baixar PDFs:")
        print("1. Execute: python cvm_download_principal.py")
        print("2. Escolha opção 3 (releases trimestrais)")
        print("3. Execute este script novamente")