#!/usr/bin/env python3
"""
Script de teste rápido para verificar se tudo está configurado
"""

import sys
from pathlib import Path

print("🧪 VERIFICAÇÃO DO SISTEMA CLAUDE API")
print("="*50)

# 1. Verificar arquivo .env
env_file = Path(".env")
if env_file.exists():
    print("✅ Arquivo .env encontrado")
    
    # Verificar se tem a chave
    with open(".env", "r") as f:
        content = f.read()
        if "ANTHROPIC_API_KEY" in content:
            print("✅ ANTHROPIC_API_KEY encontrada no .env")
        else:
            print("❌ ANTHROPIC_API_KEY não encontrada no .env")
            print("   Adicione: ANTHROPIC_API_KEY=sua-chave-aqui")
            sys.exit(1)
else:
    print("❌ Arquivo .env não encontrado")
    sys.exit(1)

# 2. Verificar dependências Python
print("\n📦 Verificando dependências Python...")

dependencies = {
    "python-dotenv": "Para carregar .env",
    "anthropic": "Cliente da API Claude",
    "PyPDF2": "Extração de texto de PDF (opcional)",
    "pdfplumber": "Extração avançada de PDF (opcional)"
}

missing = []
optional_missing = []

for package, description in dependencies.items():
    try:
        __import__(package.replace("-", "_"))
        print(f"✅ {package} - {description}")
    except ImportError:
        if package in ["PyPDF2", "pdfplumber"]:
            optional_missing.append(package)
            print(f"⚠️  {package} - {description}")
        else:
            missing.append(package)
            print(f"❌ {package} - {description}")

# 3. Verificar PDFs disponíveis
print("\n📄 Verificando PDFs disponíveis...")

pdf_count = 0
for folder in ["documents/pending", "documents/processed", "documents", "."]:
    folder_path = Path(folder)
    if folder_path.exists():
        pdfs = list(folder_path.glob("*.pdf"))
        if pdfs:
            print(f"✅ {folder}: {len(pdfs)} PDFs")
            pdf_count += len(pdfs)

if pdf_count == 0:
    print("⚠️  Nenhum PDF encontrado")
    print("   Execute: python cvm_download_principal.py")
    print("   E baixe alguns releases (opção 3)")

# 4. Resultado final
print("\n" + "="*50)
print("📊 RESULTADO DA VERIFICAÇÃO:")

if missing:
    print(f"\n❌ Dependências obrigatórias faltando: {', '.join(missing)}")
    print("\n🔧 Para instalar:")
    print(f"   pip install {' '.join(missing)}")
else:
    print("\n✅ Todas as dependências obrigatórias instaladas!")

if optional_missing:
    print(f"\n⚠️  Dependências opcionais faltando: {', '.join(optional_missing)}")
    print("   Para melhor extração de PDF, instale:")
    print(f"   pip install {' '.join(optional_missing)}")

if not missing and pdf_count > 0:
    print("\n🚀 SISTEMA PRONTO PARA TESTE!")
    print("\n   Execute: python claude_mcp_cli_env.py")
else:
    print("\n⚠️  Resolva os problemas acima antes de testar")

print("\n💡 Dica: Para instalar tudo de uma vez:")
print("   pip install python-dotenv anthropic PyPDF2 pdfplumber")