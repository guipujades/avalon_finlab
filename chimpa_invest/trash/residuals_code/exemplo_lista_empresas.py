#!/usr/bin/env python3
"""
Exemplo de Uso da Lista de Empresas CVM
=======================================

Este exemplo mostra como usar a lista completa de empresas
para facilitar buscas e extrações automatizadas.
"""

import json
import pandas as pd
from cvm_extractor_complete import CVMCompleteDocumentExtractor

class CVMCompanySearcher:
    """
    Classe para buscar empresas na lista completa.
    """
    
    def __init__(self, companies_file="empresas_cvm_completa.json", 
                 search_index_file="indice_busca_empresas.json"):
        """
        Inicializa com os arquivos de empresas e índice.
        """
        # Carregar lista de empresas
        with open(companies_file, 'r', encoding='utf-8') as f:
            self.companies = json.load(f)
        
        # Carregar índice de busca
        with open(search_index_file, 'r', encoding='utf-8') as f:
            self.search_index = json.load(f)
        
        print(f"✅ Lista carregada: {len(self.companies)} empresas")
    
    def search_by_name(self, name_part: str) -> list:
        """
        Busca empresas por parte do nome.
        """
        name_part = name_part.upper()
        results = []
        
        for company in self.companies:
            if name_part in company['nome_completo'].upper():
                results.append(company)
        
        return results
    
    def search_by_cnpj(self, cnpj: str) -> dict:
        """
        Busca empresa por CNPJ.
        """
        cnpj_clean = cnpj.replace('.', '').replace('/', '').replace('-', '')
        
        for company in self.companies:
            company_cnpj = company['cnpj'].replace('.', '').replace('/', '').replace('-', '')
            if cnpj_clean == company_cnpj:
                return company
        
        return None
    
    def search_by_cvm_code(self, cvm_code: int) -> dict:
        """
        Busca empresa por código CVM.
        """
        for company in self.companies:
            if company['codigo_cvm'] == cvm_code:
                return company
        
        return None
    
    def get_companies_with_relevant_facts(self) -> list:
        """
        Retorna empresas que têm fatos relevantes.
        """
        return [c for c in self.companies if c['tem_fatos_relevantes']]
    
    def get_most_active_companies(self, limit: int = 20) -> list:
        """
        Retorna empresas mais ativas (com mais documentos).
        """
        sorted_companies = sorted(
            self.companies, 
            key=lambda x: x['total_documentos_ipe'] + x['total_documentos_itr'], 
            reverse=True
        )
        return sorted_companies[:limit]
    
    def get_companies_by_sector(self, sector_keywords: list) -> list:
        """
        Busca empresas por palavras-chave do setor.
        """
        results = []
        
        for company in self.companies:
            name = company['nome_completo'].upper()
            for keyword in sector_keywords:
                if keyword.upper() in name:
                    results.append(company)
                    break
        
        return results

def exemplo_busca_empresas():
    """
    Exemplo de como buscar empresas na lista.
    """
    print("=== EXEMPLO: BUSCA DE EMPRESAS ===\n")
    
    # Inicializar buscador
    searcher = CVMCompanySearcher()
    
    # 1. Buscar por nome
    print("1. Busca por nome 'PETROBRAS':")
    petrobras_results = searcher.search_by_name("PETROBRAS")
    for company in petrobras_results:
        print(f"   - {company['nome_completo']}")
        print(f"     CNPJ: {company['cnpj']}, CVM: {company['codigo_cvm']}")
        print(f"     Documentos: {company['total_documentos_ipe']} IPE + {company['total_documentos_itr']} ITR")
    
    # 2. Buscar por CNPJ
    print(f"\n2. Busca por CNPJ '33.000.167/0001-01':")
    company = searcher.search_by_cnpj("33.000.167/0001-01")
    if company:
        print(f"   ✅ Encontrada: {company['nome_completo']}")
    
    # 3. Buscar por código CVM
    print(f"\n3. Busca por código CVM 9512:")
    company = searcher.search_by_cvm_code(9512)
    if company:
        print(f"   ✅ Encontrada: {company['nome_completo']}")
    
    # 4. Empresas com fatos relevantes
    print(f"\n4. Empresas com fatos relevantes (top 5):")
    companies_with_facts = searcher.get_companies_with_relevant_facts()
    for i, company in enumerate(companies_with_facts[:5], 1):
        print(f"   {i}. {company['nome_completo'][:50]} - {company['total_documentos_ipe']} docs")
    
    # 5. Empresas mais ativas
    print(f"\n5. Empresas mais ativas (top 5):")
    most_active = searcher.get_most_active_companies(5)
    for i, company in enumerate(most_active, 1):
        total = company['total_documentos_ipe'] + company['total_documentos_itr']
        print(f"   {i}. {company['nome_completo'][:50]} - {total} docs")
    
    # 6. Empresas por setor
    print(f"\n6. Bancos (busca por 'BANCO'):")
    banks = searcher.get_companies_by_sector(["BANCO"])
    for i, bank in enumerate(banks[:5], 1):
        print(f"   {i}. {bank['nome_completo']}")

def exemplo_extracao_automatizada():
    """
    Exemplo de extração automatizada usando a lista de empresas.
    """
    print("\n=== EXEMPLO: EXTRAÇÃO AUTOMATIZADA ===\n")
    
    # Inicializar buscador e extrator
    searcher = CVMCompanySearcher()
    extractor = CVMCompleteDocumentExtractor()
    
    # Pegar top 3 empresas com mais fatos relevantes
    companies_with_facts = searcher.get_companies_with_relevant_facts()
    top_companies = sorted(companies_with_facts, key=lambda x: x['total_documentos_ipe'], reverse=True)[:3]
    
    print("Extraindo documentos das 3 empresas com mais fatos relevantes:")
    
    results = {}
    
    for i, company in enumerate(top_companies, 1):
        nome_busca = company['nome_busca']
        nome_completo = company['nome_completo']
        
        print(f"\n{i}. Processando {nome_completo}...")
        print(f"   Nome para busca: {nome_busca}")
        print(f"   CNPJ: {company['cnpj']}")
        print(f"   Código CVM: {company['codigo_cvm']}")
        
        # Extrair documentos
        docs = extractor.extract_company_documents(nome_busca, year=2024)
        
        if docs:
            results[nome_completo] = docs
            
            print(f"   ✅ Extraídos:")
            print(f"      - Fatos relevantes: {len(docs['fatos_relevantes'])}")
            print(f"      - Comunicados: {len(docs['comunicados'])}")
            print(f"      - ITRs: {len(docs['documentos_estruturados'])}")
            
            # Mostrar último fato relevante
            if docs['fatos_relevantes']:
                ultimo_fato = docs['fatos_relevantes'][-1]
                print(f"      - Último fato: {ultimo_fato['data_entrega']} - {ultimo_fato['assunto']}")
    
    # Salvar resultados
    if results:
        extractor.save_to_json(results, "top_empresas_fatos_relevantes.json")
        extractor.save_to_excel(results, "top_empresas_fatos_relevantes.xlsx")
        print(f"\n✅ Resultados salvos!")

def exemplo_analise_setorial():
    """
    Exemplo de análise por setor usando a lista.
    """
    print("\n=== EXEMPLO: ANÁLISE SETORIAL ===\n")
    
    searcher = CVMCompanySearcher()
    
    # Definir setores para análise
    setores = {
        "Bancos": ["BANCO"],
        "Energia": ["ENERGIA", "ELETRICA", "ELETRICAS"],
        "Petróleo": ["PETRÓLEO", "PETROLEO", "PETROBRAS"],
        "Mineração": ["VALE", "MINERAÇÃO", "MINERACAO"],
        "Saneamento": ["SANEAMENTO", "SABESP"],
        "Telecomunicações": ["TELECOM", "TELEFONICA", "TIM", "VIVO"]
    }
    
    print("Análise por setor:")
    
    for setor, keywords in setores.items():
        companies = searcher.get_companies_by_sector(keywords)
        
        if companies:
            # Calcular estatísticas
            total_docs = sum(c['total_documentos_ipe'] for c in companies)
            com_fatos = sum(1 for c in companies if c['tem_fatos_relevantes'])
            
            print(f"\n📊 {setor}:")
            print(f"   - Empresas: {len(companies)}")
            print(f"   - Total documentos: {total_docs:,}")
            print(f"   - Com fatos relevantes: {com_fatos}")
            
            # Mostrar top 3 do setor
            top_setor = sorted(companies, key=lambda x: x['total_documentos_ipe'], reverse=True)[:3]
            print(f"   - Top 3:")
            for i, company in enumerate(top_setor, 1):
                print(f"     {i}. {company['nome_completo'][:40]} - {company['total_documentos_ipe']} docs")

if __name__ == "__main__":
    try:
        # Executar exemplos
        exemplo_busca_empresas()
        exemplo_extracao_automatizada()
        exemplo_analise_setorial()
        
        print("\n🎉 Todos os exemplos executados com sucesso!")
        
    except FileNotFoundError as e:
        print(f"\n❌ Erro: Arquivo não encontrado - {e}")
        print("Execute primeiro: python gerador_lista_empresas.py")
        
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")

