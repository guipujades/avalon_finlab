#!/usr/bin/env python3
"""
DOWNLOADER AUTOMÁTICO CVM - BAIXA DOCUMENTOS REAIS
==================================================

Este módulo efetivamente BAIXA os documentos PDF e arquivos da CVM
para sua máquina local, organizando por empresa e tipo.

Funcionalidades:
- ✅ Download automático de PDFs
- ✅ Organização por pastas (empresa/tipo/ano)
- ✅ Controle de duplicatas
- ✅ Retry automático em caso de erro
- ✅ Progress bar para acompanhar downloads
- ✅ Validação de arquivos baixados
- ✅ Resumo de downloads realizados
"""

import os
import sys
import requests
import time
import json
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from typing import List, Dict, Optional
import logging
from datetime import datetime
import hashlib
import mimetypes

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CVMDocumentDownloader:
    """
    Classe para download automático de documentos da CVM.
    """
    
    def __init__(self, base_download_dir: str = "documentos_cvm_baixados"):
        """
        Inicializa o downloader.
        
        Args:
            base_download_dir: Diretório base onde salvar os documentos
        """
        self.base_dir = Path(base_download_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Configurar session com headers apropriados
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Configurações de download
        self.timeout = 30
        self.max_retries = 3
        self.delay_between_downloads = 2  # segundos
        
        # Estatísticas
        self.stats = {
            'total_tentativas': 0,
            'downloads_sucesso': 0,
            'downloads_erro': 0,
            'arquivos_existentes': 0,
            'bytes_baixados': 0
        }
        
        print(f"📁 Downloader inicializado: {self.base_dir.absolute()}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitiza nome do arquivo para ser válido no sistema de arquivos.
        """
        # Caracteres inválidos para nomes de arquivo
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Limitar tamanho
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:200-len(ext)] + ext
        
        return filename.strip()
    
    def _get_file_extension_from_url(self, url: str) -> str:
        """
        Tenta determinar a extensão do arquivo pela URL.
        """
        # Verificar se há extensão na URL
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        if path.endswith('.pdf'):
            return '.pdf'
        elif path.endswith('.zip'):
            return '.zip'
        elif path.endswith('.xml'):
            return '.xml'
        elif path.endswith('.xls'):
            return '.xls'
        elif path.endswith('.xlsx'):
            return '.xlsx'
        else:
            # Padrão para documentos CVM
            return '.pdf'
    
    def _get_filename_from_document(self, doc: Dict) -> str:
        """
        Gera nome do arquivo baseado nos metadados do documento.
        """
        # Componentes do nome
        data = doc.get('data_entrega', '').replace('-', '')
        categoria = doc.get('categoria', 'documento').replace(' ', '_')
        assunto = doc.get('assunto', '')
        
        # Sanitizar assunto
        if assunto:
            assunto = self._sanitize_filename(assunto)
            assunto = assunto[:50]  # Limitar tamanho
        
        # Montar nome
        if assunto:
            filename = f"{data}_{categoria}_{assunto}"
        else:
            filename = f"{data}_{categoria}"
        
        # Adicionar ID único se disponível
        if 'protocolo' in doc:
            protocolo = doc['protocolo'][-10:]  # Últimos 10 caracteres
            filename += f"_{protocolo}"
        
        return self._sanitize_filename(filename)
    
    def _create_directory_structure(self, empresa: str, categoria: str, ano: str) -> Path:
        """
        Cria estrutura de diretórios organizada.
        """
        # Sanitizar nome da empresa
        empresa_clean = self._sanitize_filename(empresa.upper())
        categoria_clean = self._sanitize_filename(categoria.replace(' ', '_'))
        
        # Estrutura: base/empresa/ano/categoria/
        dir_path = self.base_dir / empresa_clean / ano / categoria_clean
        dir_path.mkdir(parents=True, exist_ok=True)
        
        return dir_path
    
    def download_document(self, doc: Dict, empresa: str, force_redownload: bool = False) -> Dict:
        """
        Baixa um documento específico.
        
        Args:
            doc: Dicionário com metadados do documento
            empresa: Nome da empresa
            force_redownload: Se True, baixa mesmo se arquivo já existir
            
        Returns:
            Dict com resultado do download
        """
        self.stats['total_tentativas'] += 1
        
        # Extrair informações
        url = doc.get('link_download', '')
        if not url:
            return {'status': 'erro', 'motivo': 'URL não encontrada'}
        
        categoria = doc.get('categoria', 'outros')
        ano = doc.get('data_entrega', '2024')[:4]
        
        # Criar diretório
        target_dir = self._create_directory_structure(empresa, categoria, ano)
        
        # Gerar nome do arquivo
        base_filename = self._get_filename_from_document(doc)
        extension = self._get_file_extension_from_url(url)
        filename = base_filename + extension
        
        file_path = target_dir / filename
        
        # Verificar se arquivo já existe
        if file_path.exists() and not force_redownload:
            self.stats['arquivos_existentes'] += 1
            return {
                'status': 'existente',
                'arquivo': str(file_path),
                'tamanho': file_path.stat().st_size
            }
        
        # Tentar download
        for tentativa in range(self.max_retries):
            try:
                logger.info(f"Baixando: {filename} (tentativa {tentativa + 1})")
                
                response = self.session.get(url, timeout=self.timeout, stream=True)
                response.raise_for_status()
                
                # Verificar se é realmente um arquivo
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' in content_type:
                    # Provavelmente uma página de erro
                    return {'status': 'erro', 'motivo': 'URL retornou HTML (possível erro)'}
                
                # Salvar arquivo
                total_size = 0
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            total_size += len(chunk)
                
                # Verificar se arquivo foi salvo corretamente
                if total_size == 0:
                    file_path.unlink(missing_ok=True)
                    return {'status': 'erro', 'motivo': 'Arquivo vazio'}
                
                self.stats['downloads_sucesso'] += 1
                self.stats['bytes_baixados'] += total_size
                
                logger.info(f"✅ Download concluído: {filename} ({total_size:,} bytes)")
                
                return {
                    'status': 'sucesso',
                    'arquivo': str(file_path),
                    'tamanho': total_size,
                    'url': url
                }
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Erro na tentativa {tentativa + 1}: {e}")
                if tentativa < self.max_retries - 1:
                    time.sleep(2 ** tentativa)  # Backoff exponencial
                continue
            except Exception as e:
                logger.error(f"Erro inesperado: {e}")
                break
        
        # Se chegou aqui, todas as tentativas falharam
        self.stats['downloads_erro'] += 1
        return {'status': 'erro', 'motivo': f'Falha após {self.max_retries} tentativas'}
    
    def download_company_documents(self, empresa_docs: Dict, empresa: str, 
                                 tipos_documento: List[str] = None,
                                 limite_por_tipo: int = None) -> Dict:
        """
        Baixa todos os documentos de uma empresa.
        
        Args:
            empresa_docs: Dicionários com documentos da empresa
            empresa: Nome da empresa
            tipos_documento: Lista de tipos a baixar (None = todos)
            limite_por_tipo: Limite de documentos por tipo (None = sem limite)
            
        Returns:
            Dict com resultados dos downloads
        """
        print(f"\n📥 Iniciando downloads para: {empresa}")
        
        # Tipos padrão se não especificado
        if tipos_documento is None:
            tipos_documento = ['fatos_relevantes', 'comunicados', 'documentos_estruturados', 'assembleias']
        
        resultados = {
            'empresa': empresa,
            'inicio': datetime.now().isoformat(),
            'downloads': {},
            'estatisticas': {}
        }
        
        total_documentos = 0
        
        for tipo in tipos_documento:
            if tipo not in empresa_docs:
                continue
            
            documentos = empresa_docs[tipo]
            if not isinstance(documentos, list):
                continue
            
            # Aplicar limite se especificado
            if limite_por_tipo:
                documentos = documentos[:limite_por_tipo]
            
            print(f"\n📄 Baixando {len(documentos)} documentos do tipo: {tipo}")
            
            resultados['downloads'][tipo] = []
            
            for i, doc in enumerate(documentos, 1):
                print(f"   {i:3d}/{len(documentos)}: ", end='', flush=True)
                
                # Download do documento
                resultado = self.download_document(doc, empresa)
                
                # Adicionar metadados do documento ao resultado
                resultado.update({
                    'documento_original': doc,
                    'tipo': tipo,
                    'indice': i
                })
                
                resultados['downloads'][tipo].append(resultado)
                
                # Status do download
                if resultado['status'] == 'sucesso':
                    print(f"✅ {Path(resultado['arquivo']).name}")
                elif resultado['status'] == 'existente':
                    print(f"📁 {Path(resultado['arquivo']).name} (já existe)")
                else:
                    print(f"❌ Erro: {resultado['motivo']}")
                
                total_documentos += 1
                
                # Pausa entre downloads
                if i < len(documentos):
                    time.sleep(self.delay_between_downloads)
        
        # Estatísticas finais
        resultados['fim'] = datetime.now().isoformat()
        resultados['estatisticas'] = {
            'total_documentos': total_documentos,
            'downloads_sucesso': sum(1 for tipo_docs in resultados['downloads'].values() 
                                   for doc in tipo_docs if doc['status'] == 'sucesso'),
            'downloads_erro': sum(1 for tipo_docs in resultados['downloads'].values() 
                                for doc in tipo_docs if doc['status'] == 'erro'),
            'arquivos_existentes': sum(1 for tipo_docs in resultados['downloads'].values() 
                                     for doc in tipo_docs if doc['status'] == 'existente')
        }
        
        print(f"\n📊 Resumo para {empresa}:")
        print(f"   ✅ Sucessos: {resultados['estatisticas']['downloads_sucesso']}")
        print(f"   ❌ Erros: {resultados['estatisticas']['downloads_erro']}")
        print(f"   📁 Já existiam: {resultados['estatisticas']['arquivos_existentes']}")
        
        return resultados
    
    def download_multiple_companies(self, empresas_docs: Dict, 
                                  tipos_documento: List[str] = None,
                                  limite_por_empresa: int = None) -> Dict:
        """
        Baixa documentos de múltiplas empresas.
        
        Args:
            empresas_docs: Dict com {empresa: documentos}
            tipos_documento: Tipos de documento a baixar
            limite_por_empresa: Limite de documentos por empresa
            
        Returns:
            Dict com resultados de todas as empresas
        """
        print(f"🚀 Iniciando downloads de {len(empresas_docs)} empresas")
        
        resultados_gerais = {
            'inicio': datetime.now().isoformat(),
            'empresas': {},
            'estatisticas_gerais': {}
        }
        
        for i, (empresa, docs) in enumerate(empresas_docs.items(), 1):
            print(f"\n{'='*60}")
            print(f"📊 Empresa {i}/{len(empresas_docs)}: {empresa}")
            print(f"{'='*60}")
            
            try:
                resultado = self.download_company_documents(
                    docs, empresa, tipos_documento, limite_por_empresa
                )
                resultados_gerais['empresas'][empresa] = resultado
                
            except Exception as e:
                logger.error(f"Erro ao processar {empresa}: {e}")
                resultados_gerais['empresas'][empresa] = {
                    'erro': str(e),
                    'status': 'falha'
                }
        
        # Estatísticas gerais
        resultados_gerais['fim'] = datetime.now().isoformat()
        resultados_gerais['estatisticas_gerais'] = self.stats.copy()
        
        print(f"\n{'='*60}")
        print(f"📊 RESUMO GERAL DOS DOWNLOADS")
        print(f"{'='*60}")
        print(f"🏢 Empresas processadas: {len(empresas_docs)}")
        print(f"✅ Downloads bem-sucedidos: {self.stats['downloads_sucesso']}")
        print(f"❌ Downloads com erro: {self.stats['downloads_erro']}")
        print(f"📁 Arquivos já existentes: {self.stats['arquivos_existentes']}")
        print(f"💾 Total baixado: {self.stats['bytes_baixados']:,} bytes ({self.stats['bytes_baixados']/1024/1024:.1f} MB)")
        
        return resultados_gerais
    
    def save_download_report(self, resultados: Dict, filename: str = None) -> str:
        """
        Salva relatório detalhado dos downloads.
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"relatorio_downloads_{timestamp}.json"
        
        report_path = self.base_dir / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"📄 Relatório salvo: {report_path}")
        return str(report_path)
    
    def list_downloaded_files(self, empresa: str = None) -> Dict:
        """
        Lista arquivos baixados, opcionalmente filtrados por empresa.
        """
        arquivos = []
        
        if empresa:
            empresa_clean = self._sanitize_filename(empresa.upper())
            search_path = self.base_dir / empresa_clean
        else:
            search_path = self.base_dir
        
        if search_path.exists():
            for arquivo in search_path.rglob('*'):
                if arquivo.is_file():
                    arquivos.append({
                        'arquivo': str(arquivo),
                        'tamanho': arquivo.stat().st_size,
                        'modificado': arquivo.stat().st_mtime,
                        'empresa': arquivo.parts[-4] if len(arquivo.parts) >= 4 else 'desconhecida',
                        'ano': arquivo.parts[-3] if len(arquivo.parts) >= 3 else 'desconhecido',
                        'categoria': arquivo.parts[-2] if len(arquivo.parts) >= 2 else 'desconhecida'
                    })
        
        return {
            'total_arquivos': len(arquivos),
            'total_tamanho': sum(a['tamanho'] for a in arquivos),
            'arquivos': sorted(arquivos, key=lambda x: x['modificado'], reverse=True)
        }


def main():
    """
    Função principal para demonstrar o uso do downloader.
    """
    print("📥 DOWNLOADER AUTOMÁTICO CVM")
    print("=" * 40)
    
    # Exemplo de uso
    try:
        # Importar extrator para obter metadados
        from cvm_extractor_complete import CVMCompleteDocumentExtractor
        
        # Inicializar extrator e downloader
        extractor = CVMCompleteDocumentExtractor()
        downloader = CVMDocumentDownloader()
        
        # Extrair metadados de uma empresa
        empresa = "B3"
        print(f"🔍 Extraindo metadados de {empresa}...")
        
        docs = extractor.extract_company_documents(empresa, year=2024)
        
        if docs:
            # Baixar apenas alguns documentos para teste
            print(f"📥 Iniciando downloads de {empresa}...")
            
            resultados = downloader.download_company_documents(
                docs, 
                empresa,
                tipos_documento=['fatos_relevantes', 'comunicados'],
                limite_por_tipo=3  # Apenas 3 de cada tipo para teste
            )
            
            # Salvar relatório
            downloader.save_download_report(resultados)
            
            # Listar arquivos baixados
            arquivos = downloader.list_downloaded_files(empresa)
            print(f"\n📁 Total de arquivos baixados: {arquivos['total_arquivos']}")
            
        else:
            print(f"❌ Nenhum documento encontrado para {empresa}")
    
    except ImportError:
        print("❌ Módulo cvm_extractor_complete não encontrado")
        print("   Execute primeiro o extrator para obter os metadados")
    except Exception as e:
        print(f"❌ Erro: {e}")


if __name__ == "__main__":
    main()

