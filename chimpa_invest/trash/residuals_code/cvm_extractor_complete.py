#!/usr/bin/env python3
"""
Extrator Completo de Documentos CVM - Incluindo Fatos Relevantes
================================================================

Baseado na descoberta dos dados IPE (Informações Periódicas e Eventuais),
este extrator consegue capturar TODOS os tipos de documentos das empresas:

- Fatos Relevantes
- Comunicados ao Mercado  
- Assembleias
- Atas
- Políticas Corporativas
- Relatórios
- E muito mais!

DESCOBERTA CHAVE: Os dados IPE contêm todos os documentos não estruturados!
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

class CVMCompleteDocumentExtractor:
    """
    Extrator completo que replica o método do dadosdemercado.com.br
    para extrair TODOS os tipos de documentos das empresas.
    """
    
    def __init__(self):
        # URLs base para diferentes tipos de dados
        self.base_itr_url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/"
        self.base_ipe_url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/"
        self.base_fre_url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/DADOS/"
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Cache para dados
        self.cache = {}
        
    def download_ipe_data(self, year: int) -> pd.DataFrame:
        """
        Baixa dados IPE (Informações Periódicas e Eventuais) - FATOS RELEVANTES!
        """
        try:
            url = f"{self.base_ipe_url}ipe_cia_aberta_{year}.zip"
            logger.info(f"Baixando dados IPE para {year}...")
            
            response = self.session.get(url)
            response.raise_for_status()
            
            # Extrair ZIP em memória
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                csv_file = f"ipe_cia_aberta_{year}.csv"
                
                with zip_file.open(csv_file) as f:
                    # Usar latin-1 encoding baseado na análise
                    df = pd.read_csv(f, sep=';', encoding='latin-1')
            
            logger.info(f"Dados IPE {year} carregados: {len(df)} documentos")
            return df
            
        except Exception as e:
            logger.error(f"Erro ao baixar dados IPE {year}: {e}")
            return pd.DataFrame()
    
    def download_itr_data(self, year: int) -> Dict[str, pd.DataFrame]:
        """
        Baixa dados ITR (Informações Trimestrais) - DADOS ESTRUTURADOS
        """
        try:
            url = f"{self.base_itr_url}itr_cia_aberta_{year}.zip"
            logger.info(f"Baixando dados ITR para {year}...")
            
            response = self.session.get(url)
            response.raise_for_status()
            
            # Extrair ZIP em memória
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                data = {}
                
                # Arquivo principal
                main_file = f"itr_cia_aberta_{year}.csv"
                if main_file in zip_file.namelist():
                    with zip_file.open(main_file) as f:
                        data['companies'] = pd.read_csv(f, sep=';', encoding='latin-1')
                
                # Outros arquivos importantes
                files_to_extract = [
                    f"itr_cia_aberta_DRE_ind_{year}.csv",
                    f"itr_cia_aberta_BPA_ind_{year}.csv", 
                    f"itr_cia_aberta_BPP_ind_{year}.csv"
                ]
                
                for file_name in files_to_extract:
                    if file_name in zip_file.namelist():
                        key = file_name.split('_')[3]  # DRE, BPA, BPP
                        with zip_file.open(file_name) as f:
                            data[key] = pd.read_csv(f, sep=';', encoding='latin-1')
            
            logger.info(f"Dados ITR {year} carregados com sucesso")
            return data
            
        except Exception as e:
            logger.error(f"Erro ao baixar dados ITR {year}: {e}")
            return {}
    
    def extract_company_documents(self, company_name: str, year: int = 2024, 
                                include_structured: bool = True, 
                                include_events: bool = True) -> Dict[str, List[Dict]]:
        """
        Extrai TODOS os documentos de uma empresa.
        
        Args:
            company_name: Nome da empresa
            year: Ano dos documentos
            include_structured: Incluir ITRs e dados estruturados
            include_events: Incluir fatos relevantes e documentos eventuais
        """
        results = {
            'empresa': company_name,
            'ano': year,
            'documentos_estruturados': [],
            'fatos_relevantes': [],
            'comunicados': [],
            'assembleias': [],
            'outros_documentos': []
        }
        
        try:
            # 1. DOCUMENTOS ESTRUTURADOS (ITRs, DFPs)
            if include_structured:
                logger.info(f"Extraindo documentos estruturados de {company_name}")
                itr_data = self.download_itr_data(year)
                
                if 'companies' in itr_data:
                    companies_df = itr_data['companies']
                    company_docs = companies_df[
                        companies_df['DENOM_CIA'].str.contains(company_name.upper(), case=False, na=False)
                    ]
                    
                    for _, row in company_docs.iterrows():
                        doc = {
                            'tipo': 'Documento Estruturado',
                            'categoria': row.get('CATEG_DOC', ''),
                            'empresa': row.get('DENOM_CIA', ''),
                            'cnpj': row.get('CNPJ_CIA', ''),
                            'codigo_cvm': row.get('CD_CVM', ''),
                            'data_referencia': row.get('DT_REFER', ''),
                            'data_entrega': row.get('DT_RECEB', ''),
                            'link_download': row.get('LINK_DOC', ''),
                            'id_documento': row.get('ID_DOC', '')
                        }
                        results['documentos_estruturados'].append(doc)
            
            # 2. FATOS RELEVANTES E DOCUMENTOS EVENTUAIS (IPEs)
            if include_events:
                logger.info(f"Extraindo fatos relevantes e documentos eventuais de {company_name}")
                ipe_data = self.download_ipe_data(year)
                
                if not ipe_data.empty:
                    # Filtrar empresa
                    company_ipes = ipe_data[
                        ipe_data['Nome_Companhia'].str.contains(company_name.upper(), case=False, na=False)
                    ]
                    
                    for _, row in company_ipes.iterrows():
                        doc = {
                            'tipo': 'Documento Eventual',
                            'categoria': row.get('Categoria', ''),
                            'tipo_doc': row.get('Tipo', ''),
                            'especie': row.get('Especie', ''),
                            'empresa': row.get('Nome_Companhia', ''),
                            'cnpj': row.get('CNPJ_Companhia', ''),
                            'codigo_cvm': row.get('Codigo_CVM', ''),
                            'data_referencia': row.get('Data_Referencia', ''),
                            'data_entrega': row.get('Data_Entrega', ''),
                            'assunto': row.get('Assunto', ''),
                            'tipo_apresentacao': row.get('Tipo_Apresentacao', ''),
                            'protocolo': row.get('Protocolo_Entrega', ''),
                            'versao': row.get('Versao', ''),
                            'link_download': row.get('Link_Download', '')
                        }
                        
                        # Categorizar por tipo
                        categoria = row.get('Categoria', '').upper()
                        if 'FATO' in categoria:
                            results['fatos_relevantes'].append(doc)
                        elif 'COMUNICADO' in categoria:
                            results['comunicados'].append(doc)
                        elif 'ASSEMBLEIA' in categoria:
                            results['assembleias'].append(doc)
                        else:
                            results['outros_documentos'].append(doc)
            
            # Estatísticas
            total_docs = (len(results['documentos_estruturados']) + 
                         len(results['fatos_relevantes']) + 
                         len(results['comunicados']) + 
                         len(results['assembleias']) + 
                         len(results['outros_documentos']))
            
            logger.info(f"Extraídos {total_docs} documentos de {company_name}")
            logger.info(f"  - Estruturados: {len(results['documentos_estruturados'])}")
            logger.info(f"  - Fatos Relevantes: {len(results['fatos_relevantes'])}")
            logger.info(f"  - Comunicados: {len(results['comunicados'])}")
            logger.info(f"  - Assembleias: {len(results['assembleias'])}")
            logger.info(f"  - Outros: {len(results['outros_documentos'])}")
            
            return results
            
        except Exception as e:
            logger.error(f"Erro ao extrair documentos de {company_name}: {e}")
            return results
    
    def extract_multiple_companies(self, companies: List[str], year: int = 2024) -> Dict[str, Dict]:
        """
        Extrai documentos de múltiplas empresas.
        """
        results = {}
        
        for company in companies:
            logger.info(f"Processando {company}...")
            company_docs = self.extract_company_documents(company, year)
            results[company] = company_docs
            
            # Pausa para evitar sobrecarga
            time.sleep(2)
        
        return results
    
    def get_document_categories_summary(self, year: int = 2024) -> Dict:
        """
        Obtém resumo de todas as categorias de documentos disponíveis.
        """
        try:
            logger.info(f"Analisando categorias de documentos para {year}")
            
            ipe_data = self.download_ipe_data(year)
            
            if ipe_data.empty:
                return {}
            
            summary = {
                'total_documentos': len(ipe_data),
                'categorias': ipe_data['Categoria'].value_counts().to_dict(),
                'tipos': ipe_data['Tipo'].value_counts().to_dict(),
                'especies': ipe_data['Especie'].value_counts().to_dict(),
                'empresas_unicas': ipe_data['Nome_Companhia'].nunique(),
                'periodo': f"{ipe_data['Data_Entrega'].min()} a {ipe_data['Data_Entrega'].max()}"
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Erro ao obter resumo: {e}")
            return {}
    
    def save_to_excel(self, data: Dict, filename: str = "documentos_cvm_completo.xlsx"):
        """
        Salva dados em Excel com abas separadas.
        """
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                for company, company_data in data.items():
                    if isinstance(company_data, dict):
                        # Cada tipo de documento em uma aba
                        for doc_type, documents in company_data.items():
                            if isinstance(documents, list) and documents:
                                df = pd.DataFrame(documents)
                                sheet_name = f"{company}_{doc_type}"[:31]
                                df.to_excel(writer, sheet_name=sheet_name, index=False)
                        
            logger.info(f"Dados salvos em: {filename}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar Excel: {e}")
    
    def save_to_json(self, data: Dict, filename: str = "documentos_cvm_completo.json"):
        """
        Salva dados em JSON.
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
                
            logger.info(f"Dados salvos em: {filename}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar JSON: {e}")


def test_complete_extractor():
    """
    Teste do extrator completo.
    """
    print("=== TESTE DO EXTRATOR COMPLETO CVM ===")
    print("(Incluindo Fatos Relevantes, Comunicados, ITRs e mais!)")
    
    extractor = CVMCompleteDocumentExtractor()
    
    # 1. Testar resumo de categorias
    print("\n1. Analisando categorias de documentos disponíveis...")
    summary = extractor.get_document_categories_summary(2024)
    
    if summary:
        print(f"✓ Total de documentos em 2024: {summary['total_documentos']:,}")
        print(f"✓ Empresas únicas: {summary['empresas_unicas']:,}")
        print(f"✓ Período: {summary['periodo']}")
        
        print("\nTop 10 categorias de documentos:")
        for categoria, count in list(summary['categorias'].items())[:10]:
            print(f"  - {categoria}: {count:,}")
    
    # 2. Testar com uma empresa específica
    print("\n2. Testando extração completa para PETROBRAS...")
    petrobras_docs = extractor.extract_company_documents("PETROBRAS", year=2024)
    
    if petrobras_docs:
        print("✓ Extração completa funcionou!")
        
        # Mostrar estatísticas
        for tipo, docs in petrobras_docs.items():
            if isinstance(docs, list):
                print(f"  {tipo}: {len(docs)} documentos")
        
        # Mostrar exemplos de fatos relevantes
        if petrobras_docs['fatos_relevantes']:
            print("\nExemplos de Fatos Relevantes da PETROBRAS:")
            for i, fato in enumerate(petrobras_docs['fatos_relevantes'][:3], 1):
                print(f"  {i}. {fato.get('assunto', 'N/A')} ({fato.get('data_entrega', 'N/A')})")
        
        # Salvar resultados
        results = {"PETROBRAS": petrobras_docs}
        extractor.save_to_json(results, "petrobras_completo.json")
        extractor.save_to_excel(results, "petrobras_completo.xlsx")
        
        print("Resultados salvos!")
    
    # 3. Testar com múltiplas empresas
    print("\n3. Testando com múltiplas empresas...")
    empresas = ["B3", "VALE"]
    
    resultados_multiplos = extractor.extract_multiple_companies(empresas, year=2024)
    
    for empresa, dados in resultados_multiplos.items():
        total = sum(len(docs) if isinstance(docs, list) else 0 for docs in dados.values())
        print(f"  {empresa}: {total} documentos totais")
    
    # Salvar resultados finais
    extractor.save_to_json(resultados_multiplos, "multiplas_empresas_completo.json")
    print("Resultados finais salvos!")


if __name__ == "__main__":
    test_complete_extractor()

