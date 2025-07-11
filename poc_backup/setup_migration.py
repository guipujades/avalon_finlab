"""
setup_migration.py - Script para configurar e migrar o sistema
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime

def setup_folder_structure():
    """Cria estrutura de pastas necessária"""
    folders = [
        "knowledge_base",
        "knowledge_base/novos_docs",
        "knowledge_base/docs_processados",
        "knowledge_base/documentos",
        "knowledge_base/documentos/resumos",
        "knowledge_base/documentos/extratos",
        "knowledge_base/documentos/relatorios",  # Compatibilidade
        "knowledge_base/indices",
        "logs",
        "cache"
    ]
    
    print("📁 Criando estrutura de pastas...")
    for folder in folders:
        Path(folder).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {folder}")
    
    print("\n✅ Estrutura de pastas criada com sucesso!")

def create_env_template():
    """Cria template do arquivo .env"""
    env_template = """# Configurações do Sistema Multi-Agente

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Tavily (para busca web)
TAVILY_KEY=your_tavily_api_key_here

# LlamaParse (opcional - para processamento avançado de PDFs)
LLAMA_CLOUD_API_KEY=your_llama_cloud_api_key_here

# Configurações opcionais
LOG_LEVEL=INFO
CACHE_ENABLED=true
"""
    
    if not Path(".env").exists():
        with open(".env", "w") as f:
            f.write(env_template)
        print("📝 Arquivo .env criado - adicione suas API keys!")
    else:
        print("⚠️  Arquivo .env já existe - verifique suas API keys")

def migrate_old_registry():
    """Migra registro antigo para novo formato"""
    old_registry_path = Path("document_registry.json")
    
    if not old_registry_path.exists():
        print("📋 Nenhum registro antigo encontrado - criando novo...")
        return create_new_registry()
    
    print("🔄 Migrando registro antigo...")
    
    try:
        with open(old_registry_path, 'r', encoding='utf-8') as f:
            old_registry = json.load(f)
        
        # Cria backup
        backup_path = f"document_registry_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        shutil.copy(old_registry_path, backup_path)
        print(f"   📦 Backup criado: {backup_path}")
        
        # Migra para novo formato
        new_registry = {
            "documents": {},
            "categories": {},
            "topics_index": {},
            "entities_index": {},
            "resumos": old_registry.get("resumos", {}),
            "last_scan": old_registry.get("last_scan"),
            "version": "2.0"
        }
        
        # Migra documentos
        for doc_id, doc_info in old_registry.get("documents", {}).items():
            # Detecta categoria
            categories = detect_categories(doc_info.get("name", ""), doc_info.get("summary_preview", ""))
            
            # Atualiza informações
            new_doc_info = doc_info.copy()
            new_doc_info["categories"] = categories
            new_doc_info["topics"] = []  # Será preenchido no próximo scan
            new_doc_info["entities"] = []  # Será preenchido no próximo scan
            
            new_registry["documents"][doc_id] = new_doc_info
            
            # Atualiza índice de categorias
            for cat in categories:
                if cat not in new_registry["categories"]:
                    new_registry["categories"][cat] = []
                new_registry["categories"][cat].append(doc_id)
        
        # Salva novo registro
        with open(old_registry_path, 'w', encoding='utf-8') as f:
            json.dump(new_registry, f, ensure_ascii=False, indent=2)
        
        print(f"   ✅ Registro migrado: {len(new_registry['documents'])} documentos")
        print(f"   📊 Categorias: {list(new_registry['categories'].keys())}")
        
        return new_registry
        
    except Exception as e:
        print(f"   ❌ Erro na migração: {e}")
        print("   💡 Criando novo registro...")
        return create_new_registry()

def detect_categories(filename, content=""):
    """Detecta categorias baseado no nome e conteúdo"""
    categories = []
    text = f"{filename} {content}".lower()
    
    category_keywords = {
        "financial_reports": ["earnings", "resultado", "balanço", "financial"],
        "market_data": ["cotação", "preço", "price", "ticker"],
        "research_analysis": ["análise", "research", "recomendação"],
        "macroeconomic": ["macro", "economia", "inflação", "pib"],
        "news_updates": ["notícia", "news", "atualização"],
        "educational": ["livro", "book", "curso", "tutorial"],
        "company_specific": ["empresa", "company", "corporate"],
        "sector_analysis": ["setor", "indústria", "sector"],
        "regulatory": ["regulação", "regulatory", "compliance"]
    }
    
    for category, keywords in category_keywords.items():
        if any(keyword in text for keyword in keywords):
            categories.append(category)
    
    if not categories:
        categories.append("general")
    
    return categories

def create_new_registry():
    """Cria novo registro"""
    registry = {
        "documents": {},
        "categories": {},
        "topics_index": {},
        "entities_index": {},
        "resumos": {},
        "last_scan": None,
        "version": "2.0"
    }
    
    with open("document_registry.json", 'w', encoding='utf-8') as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
    
    return registry

def check_dependencies():
    """Verifica dependências necessárias"""
    print("\n🔍 Verificando dependências...")
    
    dependencies = {
        "openai": "OpenAI API",
        "tavily": "Tavily (busca web)",
        "llama_index": "LlamaIndex",
        "llama_parse": "LlamaParse (opcional)",
        "python-dotenv": "dotenv"
    }
    
    missing = []
    optional_missing = []
    
    for package, name in dependencies.items():
        try:
            __import__(package.replace("-", "_"))
            print(f"   ✅ {name}")
        except ImportError:
            if "opcional" in name:
                optional_missing.append(f"{package} ({name})")
                print(f"   ⚠️  {name} - não instalado")
            else:
                missing.append(f"{package} ({name})")
                print(f"   ❌ {name} - NECESSÁRIO")
    
    if missing:
        print(f"\n❌ Dependências faltando! Instale com:")
        print(f"   pip install {' '.join([m.split()[0] for m in missing])}")
    
    if optional_missing:
        print(f"\n💡 Dependências opcionais:")
        print(f"   pip install {' '.join([m.split()[0] for m in optional_missing])}")
    
    return len(missing) == 0

def create_sample_queries():
    """Cria arquivo com queries de exemplo"""
    sample_queries = {
        "queries": [
            {
                "tipo": "empresa_especifica",
                "query": "Qual foi o resultado da Petrobras no último trimestre?",
                "estrategia_esperada": "local_first"
            },
            {
                "tipo": "dados_tempo_real",
                "query": "Qual a cotação atual do dólar?",
                "estrategia_esperada": "web_priority"
            },
            {
                "tipo": "analise_comparativa",
                "query": "Compare os múltiplos das empresas do setor bancário",
                "estrategia_esperada": "both"
            },
            {
                "tipo": "macroeconomica",
                "query": "Quais as expectativas para a Selic em 2025?",
                "estrategia_esperada": "web_complement"
            },
            {
                "tipo": "educacional",
                "query": "Explique o conceito de valor intrínseco",
                "estrategia_esperada": "local_only"
            }
        ],
        "dicas": [
            "Seja específico ao mencionar empresas ou períodos",
            "Use termos do mercado brasileiro quando relevante",
            "Para dados em tempo real, mencione 'atual' ou 'hoje'",
            "Para análises profundas, peça 'análise detalhada'"
        ]
    }
    
    with open("sample_queries.json", 'w', encoding='utf-8') as f:
        json.dump(sample_queries, f, ensure_ascii=False, indent=2)
    
    print("\n📝 Arquivo sample_queries.json criado com exemplos!")

def run_system_check():
    """Executa verificação completa do sistema"""
    print("\n🏥 Verificação de Saúde do Sistema")
    print("=" * 50)
    
    checks = {
        "folders": check_folders(),
        "registry": check_registry(),
        "env_file": check_env_file(),
        "documents": check_documents()
    }
    
    # Resumo
    print("\n📊 Resumo da Verificação:")
    all_good = True
    for check, status in checks.items():
        icon = "✅" if status else "❌"
        print(f"   {icon} {check}")
        if not status:
            all_good = False
    
    if all_good:
        print("\n🎉 Sistema pronto para uso!")
    else:
        print("\n⚠️  Alguns problemas encontrados - verifique acima")
    
    return all_good

def check_folders():
    """Verifica se pastas existem"""
    required_folders = [
        "knowledge_base",
        "knowledge_base/novos_docs",
        "knowledge_base/documentos/resumos"
    ]
    
    for folder in required_folders:
        if not Path(folder).exists():
            return False
    return True

def check_registry():
    """Verifica registro"""
    registry_path = Path("document_registry.json")
    if not registry_path.exists():
        return False
    
    try:
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        return "version" in registry
    except:
        return False

def check_env_file():
    """Verifica arquivo .env"""
    if not Path(".env").exists():
        return False
    
    with open(".env", 'r') as f:
        content = f.read()
    
    return "OPENAI_API_KEY" in content and "TAVILY_KEY" in content

def check_documents():
    """Verifica se há documentos"""
    novos_docs = list(Path("knowledge_base/novos_docs").glob("*"))
    processados = list(Path("knowledge_base/docs_processados").glob("*")) if Path("knowledge_base/docs_processados").exists() else []
    
    total = len(novos_docs) + len(processados)
    
    if total > 0:
        print(f"\n   📄 Documentos encontrados:")
        print(f"      - Novos: {len(novos_docs)}")
        print(f"      - Processados: {len(processados)}")
    
    return True  # Não é erro não ter documentos

def main():
    """Função principal do setup"""
    print("🚀 Setup do Sistema Multi-Agente")
    print("=" * 50)
    
    # Menu
    print("\nO que deseja fazer?")
    print("1. Setup completo (novo sistema)")
    print("2. Migrar sistema existente")
    print("3. Verificar saúde do sistema")
    print("4. Criar arquivos de exemplo")
    print("5. Verificar dependências")
    
    choice = input("\nEscolha (1-5): ")
    
    if choice == "1":
        print("\n🔧 Executando setup completo...")
        setup_folder_structure()
        create_env_template()
        create_new_registry()
        create_sample_queries()
        check_dependencies()
        print("\n✅ Setup completo! Próximos passos:")
        print("1. Adicione suas API keys no arquivo .env")
        print("2. Coloque documentos em knowledge_base/novos_docs")
        print("3. Execute o sistema!")
        
    elif choice == "2":
        print("\n🔄 Migrando sistema existente...")
        setup_folder_structure()
        migrate_old_registry()
        print("\n✅ Migração completa!")
        
    elif choice == "3":
        run_system_check()
        
    elif choice == "4":
        create_sample_queries()
        print("✅ Arquivos de exemplo criados!")
        
    elif choice == "5":
        if check_dependencies():
            print("\n✅ Todas as dependências necessárias instaladas!")
    
    else:
        print("❌ Opção inválida!")

if __name__ == "__main__":
    main()