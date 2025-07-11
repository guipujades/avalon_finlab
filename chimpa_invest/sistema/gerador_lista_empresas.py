#!/usr/bin/env python3
"""
Gerador de Lista Completa de Empresas CVM
=========================================

Este módulo extrai e organiza uma lista completa de todas as empresas
registradas na CVM com seus dados principais para facilitar buscas.

Dados extraídos:
- Nome completo da empresa
- CNPJ
- Código CVM
- Último documento entregue
- Quantidade de documentos
- Categorias de documentos
- Links para documentos
"""

import requests
import pandas as pd
import json
import zipfile
import io
from typing import List, Dict, Optional
import logging
from datetime import datetime
import time

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CVMCompanyListGenerator:
    """
    Gerador de lista completa de empresas da CVM.
    """
    
    def __init__(self):
        self.base_ipe_url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/"
        self.base_itr_url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/"
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def download_ipe_data(self, year: int) -> pd.DataFrame:
        """
        Baixa dados IPE para extrair lista de empresas.
        """
        try:
            url = f"{self.base_ipe_url}ipe_cia_aberta_{year}.zip"
            logger.info(f"Baixando dados IPE para {year}...")
            
            response = self.session.get(url)
            response.raise_for_status()
            
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                csv_file = f"ipe_cia_aberta_{year}.csv"
                
                with zip_file.open(csv_file) as f:
                    df = pd.read_csv(f, sep=';', encoding='latin-1')
            
            logger.info(f"Dados IPE {year} carregados: {len(df)} registros")
            return df
            
        except Exception as e:
            logger.error(f"Erro ao baixar dados IPE {year}: {e}")
            return pd.DataFrame()
    
    def download_itr_data(self, year: int) -> pd.DataFrame:
        """
        Baixa dados ITR para complementar informações das empresas.
        """
        try:
            url = f"{self.base_itr_url}itr_cia_aberta_{year}.zip"
            logger.info(f"Baixando dados ITR para {year}...")
            
            response = self.session.get(url)
            response.raise_for_status()
            
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                csv_file = f"itr_cia_aberta_{year}.csv"
                
                if csv_file in zip_file.namelist():
                    with zip_file.open(csv_file) as f:
                        df = pd.read_csv(f, sep=';', encoding='latin-1')
                    
                    logger.info(f"Dados ITR {year} carregados: {len(df)} registros")
                    return df
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Erro ao baixar dados ITR {year}: {e}")
            return pd.DataFrame()
    
    def generate_complete_company_list(self, year: int = 2024) -> List[Dict]:
        """
        Gera lista completa de empresas com todos os dados relevantes.
        """
        logger.info(f"Gerando lista completa de empresas para {year}")
        
        # Baixar dados IPE e ITR
        ipe_data = self.download_ipe_data(year)
        itr_data = self.download_itr_data(year)
        
        companies = []
        
        if not ipe_data.empty:
            # Agrupar por empresa para obter estatísticas
            logger.info("Processando dados IPE...")
            
            # Agrupar por CNPJ e Nome para evitar duplicatas
            company_groups = ipe_data.groupby(['CNPJ_Companhia', 'Nome_Companhia', 'Codigo_CVM']).agg({
                'Data_Entrega': ['min', 'max', 'count'],
                'Categoria': lambda x: list(x.unique()),
                'Tipo': lambda x: list(x.unique()),
                'Link_Download': 'first',
                'Data_Referencia': ['min', 'max']
            }).reset_index()
            
            # Flatten column names
            company_groups.columns = [
                'cnpj', 'nome_completo', 'codigo_cvm',
                'primeira_entrega', 'ultima_entrega', 'total_documentos',
                'categorias_documentos', 'tipos_documentos', 
                'link_exemplo', 'primeira_referencia', 'ultima_referencia'
            ]
            
            for _, row in company_groups.iterrows():
                company_info = {
                    'nome_completo': row['nome_completo'],
                    'nome_busca': self._extract_search_name(row['nome_completo']),
                    'cnpj': row['cnpj'],
                    'codigo_cvm': int(row['codigo_cvm']) if pd.notna(row['codigo_cvm']) else None,
                    'total_documentos_ipe': int(row['total_documentos']),
                    'primeira_entrega': row['primeira_entrega'],
                    'ultima_entrega': row['ultima_entrega'],
                    'primeira_referencia': row['primeira_referencia'],
                    'ultima_referencia': row['ultima_referencia'],
                    'categorias_documentos': row['categorias_documentos'],
                    'tipos_documentos': row['tipos_documentos'],
                    'link_exemplo': row['link_exemplo'],
                    'tem_fatos_relevantes': 'Fato Relevante' in row['categorias_documentos'],
                    'tem_comunicados': 'Comunicado ao Mercado' in row['categorias_documentos'],
                    'tem_assembleias': 'Assembleia' in row['categorias_documentos'],
                    'total_documentos_itr': 0,
                    'tem_itr': False
                }
                
                companies.append(company_info)
        
        # Complementar com dados ITR
        if not itr_data.empty:
            logger.info("Complementando com dados ITR...")
            
            itr_groups = itr_data.groupby(['CNPJ_CIA', 'DENOM_CIA', 'CD_CVM']).agg({
                'DT_RECEB': 'count'
            }).reset_index()
            
            itr_groups.columns = ['cnpj', 'nome_completo', 'codigo_cvm', 'total_itr']
            
            # Criar dicionário para lookup rápido
            itr_lookup = {}
            for _, row in itr_groups.iterrows():
                key = (row['cnpj'], row['codigo_cvm'])
                itr_lookup[key] = row['total_itr']
            
            # Atualizar empresas com dados ITR
            for company in companies:
                key = (company['cnpj'], company['codigo_cvm'])
                if key in itr_lookup:
                    company['total_documentos_itr'] = int(itr_lookup[key])
                    company['tem_itr'] = True
        
        # Ordenar por nome
        companies.sort(key=lambda x: x['nome_completo'])
        
        logger.info(f"Lista completa gerada: {len(companies)} empresas")
        return companies
    
    def _extract_search_name(self, full_name: str) -> str:
        """
        Extrai nome simplificado para busca.
        """
        if not full_name:
            return ""
        
        # Remover sufixos comuns
        suffixes = [
            ' S.A.', ' S/A', ' LTDA', ' LTDA.', ' S.A', ' SA',
            ' - BRASIL, BOLSA, BALCÃO', ' - PETROBRAS',
            ' PARTICIPAÇÕES', ' PARTICIPACOES', ' HOLDING'
        ]
        
        search_name = full_name.upper()
        for suffix in suffixes:
            search_name = search_name.replace(suffix, '')
        
        # Pegar primeira palavra significativa
        words = search_name.split()
        if words:
            # Filtrar palavras muito comuns
            common_words = ['CIA', 'COMPANHIA', 'BANCO', 'BRASIL', 'BRASILEIRA', 'NACIONAL']
            significant_words = [w for w in words if w not in common_words and len(w) > 2]
            
            if significant_words:
                return significant_words[0]
            else:
                return words[0] if words else ""
        
        return ""
    
    def generate_search_index(self, companies: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Gera índice de busca por diferentes critérios.
        """
        logger.info("Gerando índices de busca...")
        
        search_index = {
            'por_nome': {},
            'por_cnpj': {},
            'por_codigo_cvm': {},
            'por_setor': {},
            'com_fatos_relevantes': [],
            'com_comunicados': [],
            'com_itr': [],
            'mais_ativas': []  # Empresas com mais documentos
        }
        
        for company in companies:
            # Índice por nome
            nome_busca = company['nome_busca']
            if nome_busca:
                if nome_busca not in search_index['por_nome']:
                    search_index['por_nome'][nome_busca] = []
                search_index['por_nome'][nome_busca].append(company)
            
            # Índice por CNPJ
            cnpj = company['cnpj'].replace('.', '').replace('/', '').replace('-', '')
            search_index['por_cnpj'][cnpj] = company
            
            # Índice por código CVM
            if company['codigo_cvm']:
                search_index['por_codigo_cvm'][company['codigo_cvm']] = company
            
            # Listas especiais
            if company['tem_fatos_relevantes']:
                search_index['com_fatos_relevantes'].append(company)
            
            if company['tem_comunicados']:
                search_index['com_comunicados'].append(company)
            
            if company['tem_itr']:
                search_index['com_itr'].append(company)
        
        # Empresas mais ativas (por total de documentos)
        search_index['mais_ativas'] = sorted(
            companies, 
            key=lambda x: x['total_documentos_ipe'] + x['total_documentos_itr'], 
            reverse=True
        )[:100]
        
        return search_index
    
    def save_company_list(self, companies: List[Dict], filename: str = "empresas_cvm_completa"):
        """
        Salva lista de empresas em múltiplos formatos.
        """
        logger.info(f"Salvando lista de empresas...")
        
        # Salvar em JSON
        json_file = f"{filename}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(companies, f, ensure_ascii=False, indent=2, default=str)
        logger.info(f"JSON salvo: {json_file}")
        
        # Salvar em Excel
        excel_file = f"{filename}.xlsx"
        df = pd.DataFrame(companies)
        
        # Converter listas para strings para Excel
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].apply(lambda x: str(x) if isinstance(x, list) else x)
        
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # Aba principal
            df.to_excel(writer, sheet_name='Empresas_Completa', index=False)
            
            # Aba resumida
            df_resumo = df[['nome_completo', 'nome_busca', 'cnpj', 'codigo_cvm', 
                          'total_documentos_ipe', 'total_documentos_itr', 
                          'tem_fatos_relevantes', 'tem_comunicados', 'tem_itr']].copy()
            df_resumo.to_excel(writer, sheet_name='Resumo', index=False)
            
            # Aba com fatos relevantes
            df_fatos = df[df['tem_fatos_relevantes'] == True][
                ['nome_completo', 'cnpj', 'codigo_cvm', 'total_documentos_ipe']
            ].copy()
            df_fatos.to_excel(writer, sheet_name='Com_Fatos_Relevantes', index=False)
            
            # Aba mais ativas
            df_ativas = df.nlargest(50, 'total_documentos_ipe')[
                ['nome_completo', 'cnpj', 'codigo_cvm', 'total_documentos_ipe', 'total_documentos_itr']
            ].copy()
            df_ativas.to_excel(writer, sheet_name='Mais_Ativas', index=False)
        
        logger.info(f"Excel salvo: {excel_file}")
        
        # Salvar CSV simples
        csv_file = f"{filename}_resumo.csv"
        df_csv = df[['nome_completo', 'nome_busca', 'cnpj', 'codigo_cvm', 
                    'total_documentos_ipe', 'tem_fatos_relevantes', 'tem_comunicados']].copy()
        df_csv.to_csv(csv_file, index=False, encoding='utf-8')
        logger.info(f"CSV salvo: {csv_file}")
        
        return {
            'json': json_file,
            'excel': excel_file,
            'csv': csv_file
        }
    
    def save_search_index(self, search_index: Dict, filename: str = "indice_busca_empresas.json"):
        """
        Salva índice de busca.
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(search_index, f, ensure_ascii=False, indent=2, default=str)
        logger.info(f"Índice de busca salvo: {filename}")
    
    def generate_statistics(self, companies: List[Dict]) -> Dict:
        """
        Gera estatísticas da lista de empresas.
        """
        stats = {
            'total_empresas': len(companies),
            'com_fatos_relevantes': sum(1 for c in companies if c['tem_fatos_relevantes']),
            'com_comunicados': sum(1 for c in companies if c['tem_comunicados']),
            'com_assembleias': sum(1 for c in companies if c['tem_assembleias']),
            'com_itr': sum(1 for c in companies if c['tem_itr']),
            'total_documentos_ipe': sum(c['total_documentos_ipe'] for c in companies),
            'total_documentos_itr': sum(c['total_documentos_itr'] for c in companies),
            'empresa_mais_ativa': max(companies, key=lambda x: x['total_documentos_ipe'])['nome_completo'],
            'documentos_mais_ativa': max(companies, key=lambda x: x['total_documentos_ipe'])['total_documentos_ipe']
        }
        
        return stats


def main():
    """
    Função principal para gerar lista completa de empresas.
    """
    print("=== GERADOR DE LISTA COMPLETA DE EMPRESAS CVM ===\n")
    
    generator = CVMCompanyListGenerator()
    
    # Gerar lista completa
    print("1. Gerando lista completa de empresas...")
    companies = generator.generate_complete_company_list(year=2025)
    
    if not companies:
        print("[ERRO] Erro: Não foi possível gerar a lista de empresas")
        return
    
    # Gerar estatísticas
    print("2. Gerando estatísticas...")
    stats = generator.generate_statistics(companies)
    
    print(f"Lista gerada com sucesso!")
    print(f"   📊 Total de empresas: {stats['total_empresas']:,}")
    print(f"   📄 Total documentos IPE: {stats['total_documentos_ipe']:,}")
    print(f"   📄 Total documentos ITR: {stats['total_documentos_itr']:,}")
    print(f"   🚨 Com fatos relevantes: {stats['com_fatos_relevantes']:,}")
    print(f"   📢 Com comunicados: {stats['com_comunicados']:,}")
    print(f"   📊 Com ITRs: {stats['com_itr']:,}")
    print(f"   🏆 Mais ativa: {stats['empresa_mais_ativa']} ({stats['documentos_mais_ativa']:,} docs)")
    
    # Gerar índice de busca
    print("\n3. Gerando índices de busca...")
    search_index = generator.generate_search_index(companies)
    
    # Salvar arquivos
    print("\n4. Salvando arquivos...")
    files = generator.save_company_list(companies)
    generator.save_search_index(search_index)
    
    print(f"Arquivos salvos:")
    for tipo, arquivo in files.items():
        print(f"   {tipo.upper()}: {arquivo}")
    
    # Mostrar exemplos
    print(f"\n5. Exemplos de empresas:")
    for i, company in enumerate(companies[:5], 1):
        print(f"   {i}. {company['nome_completo']}")
        print(f"      CNPJ: {company['cnpj']}")
        print(f"      Código CVM: {company['codigo_cvm']}")
        print(f"      Documentos: {company['total_documentos_ipe']} IPE + {company['total_documentos_itr']} ITR")
        print(f"      Fatos relevantes: {'SIM' if company['tem_fatos_relevantes'] else 'NAO'}")
        print()
    
    print("🎉 Processo concluído com sucesso!")
    print("\nUse os arquivos gerados para:")
    print("- Buscar empresas por nome, CNPJ ou código CVM")
    print("- Filtrar empresas com fatos relevantes")
    print("- Identificar empresas mais ativas")
    print("- Automatizar extrações em lote")


if __name__ == "__main__":
    main()

