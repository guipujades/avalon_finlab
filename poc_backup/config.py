"""
config.py - Configurações do Sistema Multi-Agente
"""

# Configurações do Document Agent
DOCUMENT_AGENT_CONFIG = {
    "base_path": "knowledge_base",
    
    # Categorias de conteúdo (pode adicionar/modificar)
    "content_categories": {
        "financial_reports": {
            "keywords": ["earnings", "resultado", "balanço", "demonstração", "financial statement", 
                        "10-k", "10-q", "dre", "dfp", "itr"],
            "priority": "high"
        },
        "market_data": {
            "keywords": ["cotação", "preço", "price", "ticker", "trading", "mercado", 
                        "índice", "index", "volume", "volatilidade"],
            "priority": "high"
        },
        "research_analysis": {
            "keywords": ["análise", "research", "recomendação", "target", "rating", 
                        "buy", "sell", "hold", "outperform", "underperform"],
            "priority": "high"
        },
        "macroeconomic": {
            "keywords": ["macro", "economia", "inflação", "pib", "gdp", "selic", "fed", 
                        "banco central", "copom", "fomc", "taxa de juros"],
            "priority": "medium"
        },
        "news_updates": {
            "keywords": ["notícia", "news", "atualização", "update", "evento", 
                        "announcement", "fato relevante", "comunicado"],
            "priority": "medium"
        },
        "educational": {
            "keywords": ["livro", "book", "curso", "tutorial", "guia", "manual", 
                        "teoria", "conceito", "educação", "aprendizado"],
            "priority": "low"
        },
        "company_specific": {
            "keywords": ["empresa", "company", "corporate", "perfil", "profile", 
                        "histórico", "governança", "management"],
            "priority": "high"
        },
        "sector_analysis": {
            "keywords": ["setor", "indústria", "sector", "industry", "segmento", 
                        "vertical", "mercado", "competição"],
            "priority": "medium"
        },
        "regulatory": {
            "keywords": ["regulação", "regulatory", "compliance", "lei", "norma", 
                        "cvm", "sec", "bacen", "susep", "aneel"],
            "priority": "medium"
        },
        "technical_analysis": {
            "keywords": ["técnica", "gráfico", "chart", "tendência", "suporte", 
                        "resistência", "fibonacci", "média móvel"],
            "priority": "low"
        }
    },
    
    # Configurações de processamento
    "processing": {
        "max_preview_length": 2000,  # Caracteres para preview
        "max_entities_per_doc": 20,  # Máximo de entidades a indexar
        "min_entity_length": 3,      # Tamanho mínimo de entidade
    },
    
    # Configurações de busca
    "search": {
        "max_results_per_category": 10,
        "relevance_thresholds": {
            "perfect_match": 5,
            "good_match": 3,
            "partial_match": 1
        }
    }
}

# Configurações do Research Agent
RESEARCH_AGENT_CONFIG = {
    # Critérios de decisão
    "decision_criteria": {
        "use_local_only": {
            "confidence_threshold": 0.8,
            "coverage_threshold": 0.9,
            "min_perfect_matches": 2
        },
        "use_web_only": {
            "local_confidence_below": 0.3,
            "requires_realtime": True,
            "no_local_matches": True
        },
        "use_both": {
            "default": True,
            "confidence_range": [0.3, 0.8]
        }
    },
    
    # Configurações de busca web
    "web_search": {
        "max_results": 10,
        "search_depth": "advanced",
        "relevance_threshold": 0.5,
        "max_content_per_result": 500
    },
    
    # Configurações de análise
    "analysis": {
        "query_classification": {
            "types": ["factual", "analytical", "comparative", "exploratory"],
            "domains": ["finance", "macro", "company", "market", "general"],
            "complexity_levels": ["simple", "moderate", "complex"]
        },
        "extraction": {
            "max_documents_deep_analysis": 5,
            "content_limit_per_doc": 8000
        }
    },
    
    # Configurações de síntese
    "synthesis": {
        "include_sources": True,
        "include_confidence": True,
        "max_response_length": 2000,
        "formatting": {
            "use_sections": True,
            "use_bullets": True,
            "highlight_numbers": True
        }
    }
}

# Configurações de Sistema
SYSTEM_CONFIG = {
    # Modelos LLM
    "llm": {
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 2000
    },
    
    # Paths
    "paths": {
        "knowledge_base": "knowledge_base",
        "new_documents": "knowledge_base/novos_docs",
        "processed_documents": "knowledge_base/docs_processados",
        "summaries": "knowledge_base/documentos/resumos",
        "extracts": "knowledge_base/documentos/extratos",
        "indices": "knowledge_base/indices"
    },
    
    # Cache
    "cache": {
        "enable": True,
        "ttl_hours": 24,
        "max_size_mb": 100
    },
    
    # Logging
    "logging": {
        "level": "INFO",
        "file": "system.log",
        "max_file_size_mb": 10,
        "backup_count": 5
    },
    
    # Performance
    "performance": {
        "max_concurrent_requests": 5,
        "timeout_seconds": 30,
        "retry_attempts": 3
    }
}

# Palavras-chave específicas do domínio brasileiro
BRAZILIAN_MARKET_KEYWORDS = {
    "companies": [
        # Bancos
        "itaú", "bradesco", "santander", "banco do brasil", "caixa",
        # Varejo
        "magazine luiza", "magalu", "via", "americanas", "carrefour",
        # Commodities
        "vale", "petrobras", "petrobrás", "suzano", "klabin",
        # Energia
        "eletrobras", "cemig", "copel", "cpfl", "light",
        # Outros
        "ambev", "jbs", "brf", "natura", "gerdau"
    ],
    "indices": [
        "ibovespa", "ibov", "ibrx", "ibrx50", "small11", "dolfut", "indx"
    ],
    "regulators": [
        "cvm", "bacen", "banco central", "anbima", "b3", "susep"
    ]
}

# Templates de prompts personalizáveis
PROMPT_TEMPLATES = {
    "query_analysis": """Analise esta query financeira e determine a melhor estratégia.

QUERY: {query}

Considere:
1. Tipo de informação necessária
2. Atualidade requerida
3. Complexidade da análise
4. Disponibilidade provável na base local

Retorne análise estruturada em JSON.""",
    
    "document_extraction": """Extraia informações relevantes considerando:

QUERY: {query}
DOCUMENTO: {document_name}

Foque em:
1. Dados quantitativos
2. Insights qualitativos
3. Riscos e oportunidades
4. Contexto temporal

Retorne informações estruturadas.""",
    
    "synthesis": """Sintetize uma resposta profissional para investidores.

PERGUNTA: {query}
INFORMAÇÕES: {information}

Estruture a resposta com:
1. Resposta direta
2. Dados de suporte
3. Análise e contexto
4. Conclusões acionáveis"""
}

# Configurações para diferentes perfis de uso
USAGE_PROFILES = {
    "research": {
        "decision_criteria": {
            "use_local_only": {"confidence_threshold": 0.9},
            "use_web_only": {"local_confidence_below": 0.2}
        },
        "synthesis": {"max_response_length": 3000}
    },
    
    "quick_answers": {
        "decision_criteria": {
            "use_local_only": {"confidence_threshold": 0.7},
            "use_web_only": {"local_confidence_below": 0.4}
        },
        "synthesis": {"max_response_length": 500}
    },
    
    "comprehensive": {
        "decision_criteria": {
            "use_local_only": {"confidence_threshold": 0.95},
            "use_both": {"default": True}
        },
        "web_search": {"max_results": 20},
        "analysis": {"extraction": {"max_documents_deep_analysis": 10}}
    }
}

def get_config(profile="default"):
    """Retorna configuração baseada no perfil"""
    config = {
        "document_agent": DOCUMENT_AGENT_CONFIG.copy(),
        "research_agent": RESEARCH_AGENT_CONFIG.copy(),
        "system": SYSTEM_CONFIG.copy(),
        "keywords": BRAZILIAN_MARKET_KEYWORDS.copy(),
        "prompts": PROMPT_TEMPLATES.copy()
    }
    
    # Aplica perfil se especificado
    if profile in USAGE_PROFILES:
        profile_config = USAGE_PROFILES[profile]
        # Merge configurações do perfil
        if "decision_criteria" in profile_config:
            config["research_agent"]["decision_criteria"].update(
                profile_config["decision_criteria"]
            )
        if "synthesis" in profile_config:
            config["research_agent"]["synthesis"].update(
                profile_config["synthesis"]
            )
        if "web_search" in profile_config:
            config["research_agent"]["web_search"].update(
                profile_config["web_search"]
            )
    
    return config

# Validação de configuração
def validate_config(config):
    """Valida se a configuração está completa e correta"""
    required_keys = {
        "document_agent": ["base_path", "content_categories"],
        "research_agent": ["decision_criteria", "web_search"],
        "system": ["llm", "paths"]
    }
    
    for section, keys in required_keys.items():
        if section not in config:
            raise ValueError(f"Seção '{section}' faltando na configuração")
        for key in keys:
            if key not in config[section]:
                raise ValueError(f"Chave '{key}' faltando em '{section}'")
    
    return True

# Exemplo de uso
if __name__ == "__main__":
    # Carrega configuração padrão
    config = get_config()
    print("Configuração padrão carregada")
    
    # Carrega configuração para research detalhado
    research_config = get_config("research")
    print("Configuração de research carregada")
    
    # Valida configuração
    if validate_config(config):
        print("Configuração válida!")
        
    # Mostra algumas configurações
    print(f"\nCategorias disponíveis: {list(config['document_agent']['content_categories'].keys())}")
    print(f"Threshold de confiança: {config['research_agent']['decision_criteria']['use_local_only']['confidence_threshold']}")