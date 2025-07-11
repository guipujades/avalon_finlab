#!/usr/bin/env python3
"""
EXTRATOR COMPLETO CVM - SISTEMA UNIFICADO
=========================================

Sistema completo para extração de documentos da CVM com interface interativa.
Replica o método do dadosdemercado.com.br com todas as funcionalidades.

Funcionalidades:
-  Extração de fatos relevantes
-  Extração de comunicados ao mercado  
-  Extração de ITRs e dados estruturados
-  Extração de assembleias e atas
-  Busca por empresa específica ou múltiplas
-  Filtros por tipo de documento
-  Salvamento automático organizado
-  Interface interativa de linha de comando
-  Lista completa de 774 empresas

Autor: Baseado em engenharia reversa do dadosdemercado.com.br
Fonte: Portal de Dados Abertos da CVM
"""

import os
import sys
import json
import pandas as pd
import requests
import zipfile
import io
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime
import time
from pathlib import Path

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CVMExtractorUnificado:
    """
    Sistema unificado para extração completa de documentos CVM.
    """
    
    def __init__(self, output_dir: str = "dados_cvm_extraidos"):
        """
        Inicializa o extrator unificado.
        
        Args:
            output_dir: Diretório onde salvar os dados extraídos
        """
        # URLs base
        self.base_ipe_url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/"
        self.base_itr_url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/"
        
        # Configurar diretório de saída
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Subdiretórios organizados
        self.dirs = {
            'empresas': self.output_dir / "empresas",
            'fatos_relevantes': self.output_dir / "fatos_relevantes", 
            'comunicados': self.output_dir / "comunicados",
            'itrs': self.output_dir / "itrs",
            'assembleias': self.output_dir / "assembleias",
            'multiplas': self.output_dir / "multiplas_empresas",
            'listas': self.output_dir / "listas_empresas"
        }
        
        # Criar todos os diretórios
        for dir_path in self.dirs.values():
            dir_path.mkdir(exist_ok=True)
        
        # Session para requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Cache para dados
        self.cache = {}
        
        # Lista de empresas
        self.companies_list = None
        
        print(f" Extrator CVM Unificado inicializado")
        print(f" Dados serão salvos em: {self.output_dir.absolute()}")
    
    def download_ipe_data(self, year: int) -> pd.DataFrame:
        """Baixa dados IPE (fatos relevantes, comunicados, etc.)"""
        cache_key = f'ipe_{year}'
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            url = f"{self.base_ipe_url}ipe_cia_aberta_{year}.zip"
            logger.info(f"Baixando dados IPE para {year}...")
            
            response = self.session.get(url)
            response.raise_for_status()
            
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                csv_file = f"ipe_cia_aberta_{year}.csv"
                with zip_file.open(csv_file) as f:
                    df = pd.read_csv(f, sep=';', encoding='latin-1')
            
            self.cache[cache_key] = df
            logger.info(f"Dados IPE {year} carregados: {len(df)} registros")
            return df
            
        except Exception as e:
            logger.error(f"Erro ao baixar dados IPE {year}: {e}")
            return pd.DataFrame()
    
    def download_itr_data(self, year: int) -> pd.DataFrame:
        """Baixa dados ITR (demonstrações financeiras estruturadas)"""
        cache_key = f'itr_{year}'
        if cache_key in self.cache:
            return self.cache[cache_key]
        
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
                    
                    self.cache[cache_key] = df
                    logger.info(f"Dados ITR {year} carregados: {len(df)} registros")
                    return df
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Erro ao baixar dados ITR {year}: {e}")
            return pd.DataFrame()
    
    def gerar_lista_empresas(self, year: int = 2024, force_update: bool = False) -> List[Dict]:
        """
        Gera lista completa de empresas com metadados.
        """
        lista_file = self.dirs['listas'] / f"empresas_completa_{year}.json"
        
        # Usar cache se existir e não forçar atualização
        if lista_file.exists() and not force_update:
            logger.info("Carregando lista de empresas do cache...")
            with open(lista_file, 'r', encoding='utf-8') as f:
                self.companies_list = json.load(f)
            return self.companies_list
        
        logger.info(f"Gerando lista completa de empresas para {year}...")
        
        # Baixar dados
        ipe_data = self.download_ipe_data(year)
        itr_data = self.download_itr_data(year)
        
        companies = []
        
        if not ipe_data.empty:
            # Agrupar por empresa
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
                    'categorias_documentos': row['categorias_documentos'],
                    'tem_fatos_relevantes': 'Fato Relevante' in row['categorias_documentos'],
                    'tem_comunicados': 'Comunicado ao Mercado' in row['categorias_documentos'],
                    'tem_assembleias': 'Assembleia' in row['categorias_documentos'],
                    'total_documentos_itr': 0,
                    'tem_itr': False
                }
                companies.append(company_info)
        
        # Complementar com dados ITR
        if not itr_data.empty:
            itr_groups = itr_data.groupby(['CNPJ_CIA', 'CD_CVM']).size().reset_index(columns=['total_itr'])
            itr_lookup = {(row['CNPJ_CIA'], row['CD_CVM']): row['total_itr'] for _, row in itr_groups.iterrows()}
            
            for company in companies:
                key = (company['cnpj'], company['codigo_cvm'])
                if key in itr_lookup:
                    company['total_documentos_itr'] = int(itr_lookup[key])
                    company['tem_itr'] = True
        
        # Ordenar por nome
        companies.sort(key=lambda x: x['nome_completo'])
        
        # Salvar cache
        with open(lista_file, 'w', encoding='utf-8') as f:
            json.dump(companies, f, ensure_ascii=False, indent=2, default=str)
        
        self.companies_list = companies
        logger.info(f"Lista de empresas gerada: {len(companies)} empresas")
        
        return companies
    
    def _extract_search_name(self, full_name: str) -> str:
        """Extrai nome simplificado para busca"""
        if not full_name:
            return ""
        
        suffixes = [' S.A.', ' S/A', ' LTDA', ' LTDA.', ' S.A', ' SA', ' - BRASIL, BOLSA, BALCÃO', ' - PETROBRAS']
        search_name = full_name.upper()
        for suffix in suffixes:
            search_name = search_name.replace(suffix, '')
        
        words = search_name.split()
        if words:
            common_words = ['CIA', 'COMPANHIA', 'BANCO', 'BRASIL', 'BRASILEIRA', 'NACIONAL']
            significant_words = [w for w in words if w not in common_words and len(w) > 2]
            return significant_words[0] if significant_words else words[0]
        
        return ""
    
    def buscar_empresas(self, termo_busca: str) -> List[Dict]:
        """
        Busca empresas por nome, CNPJ ou código CVM.
        """
        if not self.companies_list:
            self.gerar_lista_empresas()
        
        termo = termo_busca.upper().strip()
        resultados = []
        
        for company in self.companies_list:
            # Busca por nome
            if termo in company['nome_completo'].upper():
                resultados.append(company)
            # Busca por CNPJ
            elif termo.replace('.', '').replace('/', '').replace('-', '') in company['cnpj'].replace('.', '').replace('/', '').replace('-', ''):
                resultados.append(company)
            # Busca por código CVM
            elif termo.isdigit() and company['codigo_cvm'] == int(termo):
                resultados.append(company)
        
        return resultados
    
    def extrair_empresa_especifica(self, empresa_nome: str, year: int = 2024, 
                                 incluir_estruturados: bool = True,
                                 incluir_fatos: bool = True,
                                 incluir_comunicados: bool = True,
                                 incluir_assembleias: bool = True) -> Dict:
        """
        Extrai documentos de uma empresa específica com filtros.
        """
        logger.info(f"Extraindo documentos de {empresa_nome} ({year})")
        
        resultados = {
            'empresa': empresa_nome,
            'ano': year,
            'timestamp': datetime.now().isoformat(),
            'documentos_estruturados': [],
            'fatos_relevantes': [],
            'comunicados': [],
            'assembleias': [],
            'outros_documentos': []
        }
        
        # Dados estruturados (ITRs)
        if incluir_estruturados:
            itr_data = self.download_itr_data(year)
            if not itr_data.empty:
                company_itrs = itr_data[
                    itr_data['DENOM_CIA'].str.contains(empresa_nome.upper(), case=False, na=False)
                ]
                
                for _, row in company_itrs.iterrows():
                    doc = {
                        'tipo': 'ITR',
                        'categoria': row.get('CATEG_DOC', ''),
                        'empresa': row.get('DENOM_CIA', ''),
                        'cnpj': row.get('CNPJ_CIA', ''),
                        'codigo_cvm': row.get('CD_CVM', ''),
                        'data_referencia': row.get('DT_REFER', ''),
                        'data_entrega': row.get('DT_RECEB', ''),
                        'link_download': row.get('LINK_DOC', ''),
                        'id_documento': row.get('ID_DOC', '')
                    }
                    resultados['documentos_estruturados'].append(doc)
        
        # Documentos eventuais (IPEs)
        ipe_data = self.download_ipe_data(year)
        if not ipe_data.empty:
            company_ipes = ipe_data[
                ipe_data['Nome_Companhia'].str.contains(empresa_nome.upper(), case=False, na=False)
            ]
            
            for _, row in company_ipes.iterrows():
                doc = {
                    'tipo': 'IPE',
                    'categoria': row.get('Categoria', ''),
                    'tipo_doc': row.get('Tipo', ''),
                    'especie': row.get('Especie', ''),
                    'empresa': row.get('Nome_Companhia', ''),
                    'cnpj': row.get('CNPJ_Companhia', ''),
                    'codigo_cvm': row.get('Codigo_CVM', ''),
                    'data_referencia': row.get('Data_Referencia', ''),
                    'data_entrega': row.get('Data_Entrega', ''),
                    'assunto': row.get('Assunto', ''),
                    'protocolo': row.get('Protocolo_Entrega', ''),
                    'versao': row.get('Versao', ''),
                    'link_download': row.get('Link_Download', '')
                }
                
                # Categorizar por tipo
                categoria = row.get('Categoria', '').upper()
                if 'FATO' in categoria and incluir_fatos:
                    resultados['fatos_relevantes'].append(doc)
                elif 'COMUNICADO' in categoria and incluir_comunicados:
                    resultados['comunicados'].append(doc)
                elif 'ASSEMBLEIA' in categoria and incluir_assembleias:
                    resultados['assembleias'].append(doc)
                else:
                    resultados['outros_documentos'].append(doc)
        
        # Estatísticas
        total_docs = sum(len(docs) for docs in resultados.values() if isinstance(docs, list))
        logger.info(f"Extraídos {total_docs} documentos de {empresa_nome}")
        
        return resultados
    
    def extrair_multiplas_empresas(self, empresas: List[str], year: int = 2024, **filtros) -> Dict:
        """
        Extrai documentos de múltiplas empresas.
        """
        logger.info(f"Extraindo documentos de {len(empresas)} empresas")
        
        resultados = {}
        
        for i, empresa in enumerate(empresas, 1):
            print(f"\n Processando {i}/{len(empresas)}: {empresa}")
            
            try:
                docs = self.extrair_empresa_especifica(empresa, year, **filtros)
                resultados[empresa] = docs
                
                # Pausa para evitar sobrecarga
                if i < len(empresas):
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Erro ao processar {empresa}: {e}")
                resultados[empresa] = {'erro': str(e)}
        
        return resultados
    
    def salvar_resultados(self, dados: Dict, nome_arquivo: str, tipo_extracao: str = "empresa") -> Dict[str, str]:
        """
        Salva resultados em múltiplos formatos organizados.
        """
        # Determinar diretório baseado no tipo
        if tipo_extracao == "multiplas":
            base_dir = self.dirs['multiplas']
        elif tipo_extracao == "fatos":
            base_dir = self.dirs['fatos_relevantes']
        elif tipo_extracao == "comunicados":
            base_dir = self.dirs['comunicados']
        elif tipo_extracao == "itrs":
            base_dir = self.dirs['itrs']
        else:
            base_dir = self.dirs['empresas']
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{nome_arquivo}_{timestamp}"
        
        arquivos_salvos = {}
        
        # Salvar JSON
        json_file = base_dir / f"{base_name}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2, default=str)
        arquivos_salvos['json'] = str(json_file)
        
        # Salvar Excel
        excel_file = base_dir / f"{base_name}.xlsx"
        try:
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                if isinstance(dados, dict) and 'empresa' in dados:
                    # Dados de uma empresa
                    for tipo_doc, documentos in dados.items():
                        if isinstance(documentos, list) and documentos:
                            df = pd.DataFrame(documentos)
                            sheet_name = tipo_doc[:31]
                            df.to_excel(writer, sheet_name=sheet_name, index=False)
                else:
                    # Dados de múltiplas empresas
                    for empresa, empresa_dados in dados.items():
                        if isinstance(empresa_dados, dict):
                            for tipo_doc, documentos in empresa_dados.items():
                                if isinstance(documentos, list) and documentos:
                                    df = pd.DataFrame(documentos)
                                    sheet_name = f"{empresa}_{tipo_doc}"[:31]
                                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            arquivos_salvos['excel'] = str(excel_file)
        except Exception as e:
            logger.warning(f"Erro ao salvar Excel: {e}")
        
        # Salvar CSV resumo
        csv_file = base_dir / f"{base_name}_resumo.csv"
        try:
            if isinstance(dados, dict) and 'fatos_relevantes' in dados:
                # Resumo de uma empresa
                resumo = []
                for tipo_doc, documentos in dados.items():
                    if isinstance(documentos, list):
                        for doc in documentos:
                            if isinstance(doc, dict):
                                resumo.append({
                                    'empresa': dados.get('empresa', ''),
                                    'tipo_documento': tipo_doc,
                                    'categoria': doc.get('categoria', ''),
                                    'data_entrega': doc.get('data_entrega', ''),
                                    'assunto': doc.get('assunto', '')[:100] if doc.get('assunto') else '',
                                    'link': doc.get('link_download', '')
                                })
                
                if resumo:
                    pd.DataFrame(resumo).to_csv(csv_file, index=False, encoding='utf-8')
                    arquivos_salvos['csv'] = str(csv_file)
        except Exception as e:
            logger.warning(f"Erro ao salvar CSV: {e}")
        
        logger.info(f"Resultados salvos em {len(arquivos_salvos)} formatos")
        return arquivos_salvos
    
    def interface_interativa(self):
        """
        Interface interativa de linha de comando.
        """
        print("\n" + "="*60)
        print(" EXTRATOR COMPLETO CVM - SISTEMA UNIFICADO")
        print("="*60)
        print("Replica o método do dadosdemercado.com.br")
        print("Fonte: Portal de Dados Abertos da CVM")
        print("="*60)
        
        while True:
            print("\n OPÇÕES DISPONÍVEIS:")
            print("1.  Extrair documentos de empresa específica")
            print("2.  Extrair documentos de múltiplas empresas")
            print("3.  Extrair apenas fatos relevantes")
            print("4.  Extrair apenas comunicados ao mercado")
            print("5.  Extrair apenas ITRs (dados estruturados)")
            print("6.  Buscar empresas na base")
            print("7.  Gerar lista completa de empresas")
            print("8.  Configurações")
            print("9.  Sair")
            
            try:
                opcao = input("\n Escolha uma opção (1-9): ").strip()
                
                if opcao == "1":
                    self._interface_empresa_especifica()
                elif opcao == "2":
                    self._interface_multiplas_empresas()
                elif opcao == "3":
                    self._interface_fatos_relevantes()
                elif opcao == "4":
                    self._interface_comunicados()
                elif opcao == "5":
                    self._interface_itrs()
                elif opcao == "6":
                    self._interface_buscar_empresas()
                elif opcao == "7":
                    self._interface_gerar_lista()
                elif opcao == "8":
                    self._interface_configuracoes()
                elif opcao == "9":
                    print("\n Obrigado por usar o Extrator CVM!")
                    break
                else:
                    print(" Opção inválida. Tente novamente.")
                    
            except KeyboardInterrupt:
                print("\n\n Saindo...")
                break
            except Exception as e:
                print(f"\n Erro: {e}")
    
    def _interface_empresa_especifica(self):
        """Interface para extração de empresa específica"""
        print("\n EXTRAÇÃO DE EMPRESA ESPECÍFICA")
        print("-" * 40)
        
        # Buscar empresa
        termo = input("Digite o nome da empresa (ou parte): ").strip()
        if not termo:
            print(" Nome da empresa é obrigatório")
            return
        
        empresas = self.buscar_empresas(termo)
        
        if not empresas:
            print(f" Nenhuma empresa encontrada para '{termo}'")
            return
        
        if len(empresas) > 1:
            print(f"\n Encontradas {len(empresas)} empresas:")
            for i, emp in enumerate(empresas[:10], 1):
                print(f"{i:2d}. {emp['nome_completo']}")
                print(f"     CNPJ: {emp['cnpj']}, CVM: {emp['codigo_cvm']}")
            
            try:
                escolha = int(input(f"\nEscolha uma empresa (1-{min(len(empresas), 10)}): ")) - 1
                empresa_escolhida = empresas[escolha]
            except (ValueError, IndexError):
                print(" Escolha inválida")
                return
        else:
            empresa_escolhida = empresas[0]
        
        print(f"\n Empresa selecionada: {empresa_escolhida['nome_completo']}")
        
        # Configurar filtros
        print("\n CONFIGURAR EXTRAÇÃO:")
        incluir_estruturados = input("Incluir ITRs/dados estruturados? (s/N): ").lower().startswith('s')
        incluir_fatos = input("Incluir fatos relevantes? (S/n): ").lower() != 'n'
        incluir_comunicados = input("Incluir comunicados ao mercado? (S/n): ").lower() != 'n'
        incluir_assembleias = input("Incluir assembleias? (S/n): ").lower() != 'n'
        
        # Ano
        try:
            ano = int(input("Ano dos documentos (2024): ") or "2024")
        except ValueError:
            ano = 2024
        
        # Extrair
        print(f"\n Extraindo documentos de {empresa_escolhida['nome_busca']}...")
        
        resultados = self.extrair_empresa_especifica(
            empresa_escolhida['nome_busca'],
            year=ano,
            incluir_estruturados=incluir_estruturados,
            incluir_fatos=incluir_fatos,
            incluir_comunicados=incluir_comunicados,
            incluir_assembleias=incluir_assembleias
        )
        
        # Mostrar estatísticas
        print(f"\n RESULTADOS:")
        print(f"    ITRs: {len(resultados['documentos_estruturados'])}")
        print(f"    Fatos relevantes: {len(resultados['fatos_relevantes'])}")
        print(f"    Comunicados: {len(resultados['comunicados'])}")
        print(f"    Assembleias: {len(resultados['assembleias'])}")
        print(f"    Outros: {len(resultados['outros_documentos'])}")
        
        # Salvar
        nome_arquivo = empresa_escolhida['nome_busca'].lower().replace(' ', '_')
        arquivos = self.salvar_resultados(resultados, nome_arquivo, "empresa")
        
        print(f"\n ARQUIVOS SALVOS:")
        for tipo, caminho in arquivos.items():
            print(f"    {tipo.upper()}: {caminho}")
    
    def _interface_multiplas_empresas(self):
        """Interface para extração de múltiplas empresas"""
        print("\n EXTRAÇÃO DE MÚLTIPLAS EMPRESAS")
        print("-" * 40)
        
        print("Digite os nomes das empresas (uma por linha).")
        print("Digite 'FIM' quando terminar:")
        
        empresas = []
        while True:
            empresa = input(f"Empresa {len(empresas)+1}: ").strip()
            if empresa.upper() == 'FIM':
                break
            if empresa:
                empresas.append(empresa)
        
        if not empresas:
            print(" Nenhuma empresa informada")
            return
        
        print(f"\n Empresas para extração: {len(empresas)}")
        for i, emp in enumerate(empresas, 1):
            print(f"   {i}. {emp}")
        
        # Configurar filtros
        print("\n CONFIGURAR EXTRAÇÃO:")
        incluir_estruturados = input("Incluir ITRs/dados estruturados? (s/N): ").lower().startswith('s')
        incluir_fatos = input("Incluir fatos relevantes? (S/n): ").lower() != 'n'
        incluir_comunicados = input("Incluir comunicados ao mercado? (S/n): ").lower() != 'n'
        incluir_assembleias = input("Incluir assembleias? (S/n): ").lower() != 'n'
        
        try:
            ano = int(input("Ano dos documentos (2024): ") or "2024")
        except ValueError:
            ano = 2024
        
        # Extrair
        print(f"\n Extraindo documentos de {len(empresas)} empresas...")
        
        resultados = self.extrair_multiplas_empresas(
            empresas,
            year=ano,
            incluir_estruturados=incluir_estruturados,
            incluir_fatos=incluir_fatos,
            incluir_comunicados=incluir_comunicados,
            incluir_assembleias=incluir_assembleias
        )
        
        # Mostrar estatísticas
        print(f"\n RESUMO GERAL:")
        total_docs = 0
        for empresa, dados in resultados.items():
            if isinstance(dados, dict) and 'erro' not in dados:
                empresa_total = sum(len(docs) for docs in dados.values() if isinstance(docs, list))
                total_docs += empresa_total
                print(f"   {empresa}: {empresa_total} documentos")
        
        print(f"\n Total geral: {total_docs} documentos")
        
        # Salvar
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"multiplas_empresas_{timestamp}"
        arquivos = self.salvar_resultados(resultados, nome_arquivo, "multiplas")
        
        print(f"\n ARQUIVOS SALVOS:")
        for tipo, caminho in arquivos.items():
            print(f"    {tipo.upper()}: {caminho}")
    
    def _interface_fatos_relevantes(self):
        """Interface para extração apenas de fatos relevantes"""
        print("\n EXTRAÇÃO DE FATOS RELEVANTES")
        print("-" * 40)
        
        opcao = input("Extrair de (1) empresa específica ou (2) todas com fatos relevantes? (1/2): ")
        
        if opcao == "1":
            # Empresa específica
            termo = input("Digite o nome da empresa: ").strip()
            empresas = self.buscar_empresas(termo)
            
            if not empresas:
                print(f" Empresa '{termo}' não encontrada")
                return
            
            empresa = empresas[0]
            print(f" Extraindo fatos relevantes de: {empresa['nome_completo']}")
            
            resultados = self.extrair_empresa_especifica(
                empresa['nome_busca'],
                incluir_estruturados=False,
                incluir_fatos=True,
                incluir_comunicados=False,
                incluir_assembleias=False
            )
            
            nome_arquivo = f"fatos_{empresa['nome_busca'].lower()}"
            
        elif opcao == "2":
            # Todas as empresas com fatos relevantes
            if not self.companies_list:
                self.gerar_lista_empresas()
            
            empresas_com_fatos = [emp for emp in self.companies_list if emp['tem_fatos_relevantes']]
            print(f" Encontradas {len(empresas_com_fatos)} empresas com fatos relevantes")
            
            limite = input(f"Quantas empresas processar? (máximo {len(empresas_com_fatos)}): ")
            try:
                limite = int(limite) if limite else len(empresas_com_fatos)
                limite = min(limite, len(empresas_com_fatos))
            except ValueError:
                limite = 10
            
            empresas_nomes = [emp['nome_busca'] for emp in empresas_com_fatos[:limite]]
            
            resultados = self.extrair_multiplas_empresas(
                empresas_nomes,
                incluir_estruturados=False,
                incluir_fatos=True,
                incluir_comunicados=False,
                incluir_assembleias=False
            )
            
            nome_arquivo = f"fatos_relevantes_top_{limite}"
        else:
            print(" Opção inválida")
            return
        
        # Salvar
        arquivos = self.salvar_resultados(resultados, nome_arquivo, "fatos")
        
        print(f"\n FATOS RELEVANTES SALVOS:")
        for tipo, caminho in arquivos.items():
            print(f"    {tipo.upper()}: {caminho}")
    
    def _interface_comunicados(self):
        """Interface para extração de comunicados"""
        print("\n EXTRAÇÃO DE COMUNICADOS AO MERCADO")
        print("-" * 40)
        
        termo = input("Digite o nome da empresa (ou ENTER para top empresas): ").strip()
        
        if termo:
            empresas = self.buscar_empresas(termo)
            if not empresas:
                print(f" Empresa '{termo}' não encontrada")
                return
            
            empresa = empresas[0]
            resultados = self.extrair_empresa_especifica(
                empresa['nome_busca'],
                incluir_estruturados=False,
                incluir_fatos=False,
                incluir_comunicados=True,
                incluir_assembleias=False
            )
            nome_arquivo = f"comunicados_{empresa['nome_busca'].lower()}"
        else:
            # Top empresas com comunicados
            if not self.companies_list:
                self.gerar_lista_empresas()
            
            empresas_com_comunicados = [emp for emp in self.companies_list if emp['tem_comunicados']][:10]
            empresas_nomes = [emp['nome_busca'] for emp in empresas_com_comunicados]
            
            resultados = self.extrair_multiplas_empresas(
                empresas_nomes,
                incluir_estruturados=False,
                incluir_fatos=False,
                incluir_comunicados=True,
                incluir_assembleias=False
            )
            nome_arquivo = "comunicados_top_10"
        
        arquivos = self.salvar_resultados(resultados, nome_arquivo, "comunicados")
        
        print(f"\n COMUNICADOS SALVOS:")
        for tipo, caminho in arquivos.items():
            print(f"    {tipo.upper()}: {caminho}")
    
    def _interface_itrs(self):
        """Interface para extração de ITRs"""
        print("\n EXTRAÇÃO DE ITRs (DADOS ESTRUTURADOS)")
        print("-" * 40)
        
        termo = input("Digite o nome da empresa (ou ENTER para top empresas): ").strip()
        
        if termo:
            empresas = self.buscar_empresas(termo)
            if not empresas:
                print(f" Empresa '{termo}' não encontrada")
                return
            
            empresa = empresas[0]
            resultados = self.extrair_empresa_especifica(
                empresa['nome_busca'],
                incluir_estruturados=True,
                incluir_fatos=False,
                incluir_comunicados=False,
                incluir_assembleias=False
            )
            nome_arquivo = f"itrs_{empresa['nome_busca'].lower()}"
        else:
            # Top empresas com ITRs
            if not self.companies_list:
                self.gerar_lista_empresas()
            
            empresas_com_itrs = [emp for emp in self.companies_list if emp['tem_itr']][:10]
            empresas_nomes = [emp['nome_busca'] for emp in empresas_com_itrs]
            
            resultados = self.extrair_multiplas_empresas(
                empresas_nomes,
                incluir_estruturados=True,
                incluir_fatos=False,
                incluir_comunicados=False,
                incluir_assembleias=False
            )
            nome_arquivo = "itrs_top_10"
        
        arquivos = self.salvar_resultados(resultados, nome_arquivo, "itrs")
        
        print(f"\n ITRs SALVOS:")
        for tipo, caminho in arquivos.items():
            print(f"    {tipo.upper()}: {caminho}")
    
    def _interface_buscar_empresas(self):
        """Interface para buscar empresas"""
        print("\n BUSCAR EMPRESAS")
        print("-" * 40)
        
        termo = input("Digite nome, CNPJ ou código CVM: ").strip()
        if not termo:
            return
        
        empresas = self.buscar_empresas(termo)
        
        if not empresas:
            print(f" Nenhuma empresa encontrada para '{termo}'")
            return
        
        print(f"\n Encontradas {len(empresas)} empresas:")
        for i, emp in enumerate(empresas[:20], 1):
            print(f"\n{i:2d}. {emp['nome_completo']}")
            print(f"     CNPJ: {emp['cnpj']}")
            print(f"     Código CVM: {emp['codigo_cvm']}")
            print(f"     Documentos: {emp['total_documentos_ipe']} IPE + {emp['total_documentos_itr']} ITR")
            print(f"     Fatos relevantes: {'' if emp['tem_fatos_relevantes'] else ''}")
            print(f"     Comunicados: {'' if emp['tem_comunicados'] else ''}")
    
    def _interface_gerar_lista(self):
        """Interface para gerar lista de empresas"""
        print("\n GERAR LISTA COMPLETA DE EMPRESAS")
        print("-" * 40)
        
        force_update = input("Forçar atualização da lista? (s/N): ").lower().startswith('s')
        
        try:
            ano = int(input("Ano para análise (2024): ") or "2024")
        except ValueError:
            ano = 2024
        
        print(f"\n Gerando lista de empresas para {ano}...")
        
        empresas = self.gerar_lista_empresas(year=ano, force_update=force_update)
        
        # Estatísticas
        com_fatos = sum(1 for emp in empresas if emp['tem_fatos_relevantes'])
        com_comunicados = sum(1 for emp in empresas if emp['tem_comunicados'])
        com_itrs = sum(1 for emp in empresas if emp['tem_itr'])
        
        print(f"\n ESTATÍSTICAS:")
        print(f"    Total de empresas: {len(empresas):,}")
        print(f"    Com fatos relevantes: {com_fatos:,}")
        print(f"    Com comunicados: {com_comunicados:,}")
        print(f"    Com ITRs: {com_itrs:,}")
        
        # Salvar lista
        lista_dados = {
            'estatisticas': {
                'total_empresas': len(empresas),
                'com_fatos_relevantes': com_fatos,
                'com_comunicados': com_comunicados,
                'com_itrs': com_itrs,
                'ano': ano,
                'gerado_em': datetime.now().isoformat()
            },
            'empresas': empresas
        }
        
        arquivos = self.salvar_resultados(lista_dados, f"lista_empresas_{ano}", "empresa")
        
        print(f"\n LISTA SALVA:")
        for tipo, caminho in arquivos.items():
            print(f"    {tipo.upper()}: {caminho}")
    
    def _interface_configuracoes(self):
        """Interface de configurações"""
        print("\n CONFIGURAÇÕES")
        print("-" * 40)
        print(f" Diretório de saída: {self.output_dir.absolute()}")
        print(f" Cache ativo: {len(self.cache)} datasets")
        print(f" Lista de empresas: {'Carregada' if self.companies_list else 'Não carregada'}")
        
        print("\nOpções:")
        print("1. Limpar cache")
        print("2. Recarregar lista de empresas")
        print("3. Mostrar estrutura de diretórios")
        print("4. Voltar")
        
        opcao = input("\nEscolha uma opção: ").strip()
        
        if opcao == "1":
            self.cache.clear()
            print(" Cache limpo")
        elif opcao == "2":
            self.companies_list = None
            self.gerar_lista_empresas(force_update=True)
            print(" Lista de empresas recarregada")
        elif opcao == "3":
            print(f"\n ESTRUTURA DE DIRETÓRIOS:")
            for nome, caminho in self.dirs.items():
                print(f"   {nome}: {caminho}")


def main():
    """
    Função principal do sistema.
    """
    try:
        # Verificar diretório de saída personalizado
        output_dir = "dados_cvm_extraidos"
        if len(sys.argv) > 1:
            output_dir = sys.argv[1]
        
        # Inicializar extrator
        extrator = CVMExtractorUnificado(output_dir=output_dir)
        
        # Executar interface interativa
        extrator.interface_interativa()
        
    except KeyboardInterrupt:
        print("\n\n Programa interrompido pelo usuário")
    except Exception as e:
        print(f"\n Erro fatal: {e}")
        logger.exception("Erro fatal no sistema")


if __name__ == "__main__":
    main()

