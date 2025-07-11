#!/usr/bin/env python3
"""
CVM Document Downloader Enhanced
================================
Versão melhorada do downloader com suporte a redirecionamentos e cookies.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
from pathlib import Path
import logging
from urllib.parse import urlparse, parse_qs
import re
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CVMDownloaderEnhanced:
    """
    Downloader melhorado para documentos CVM com tratamento de redirecionamentos.
    """
    
    def __init__(self, base_dir: str = "documents"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Configurar sessão com retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Headers mais completos para parecer um navegador real
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def extract_direct_link(self, html_content: str) -> Optional[str]:
        """
        Extrai o link direto do PDF de uma página HTML da CVM.
        """
        # Padrões comuns em páginas da CVM
        patterns = [
            r'window\.open\(["\']([^"\']+\.pdf)["\']',
            r'href=["\']([^"\']+\.pdf)["\']',
            r'location\.href=["\']([^"\']+\.pdf)["\']',
            r'src=["\']([^"\']+\.pdf)["\']',
            r'<iframe[^>]+src=["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            if matches:
                # Se encontrou um link relativo, construir URL completa
                pdf_url = matches[0]
                if not pdf_url.startswith('http'):
                    pdf_url = f"https://www.rad.cvm.gov.br{pdf_url}"
                return pdf_url
        
        return None
    
    def download_with_redirect_handling(self, url: str, filepath: Path, max_redirects: int = 5) -> bool:
        """
        Baixa documento com tratamento especial para redirecionamentos.
        """
        try:
            current_url = url
            redirect_count = 0
            
            while redirect_count < max_redirects:
                logger.info(f"Tentando acessar: {current_url}")
                
                # Primeira requisição para obter cookies e possível redirecionamento
                response = self.session.get(current_url, allow_redirects=True, timeout=30)
                
                # Verificar tipo de conteúdo
                content_type = response.headers.get('Content-Type', '').lower()
                
                if 'application/pdf' in content_type or response.content[:4] == b'%PDF':
                    # É um PDF! Salvar diretamente
                    logger.info("PDF encontrado! Salvando...")
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    return True
                
                elif 'text/html' in content_type:
                    # É HTML, pode conter link para o PDF
                    logger.info("Página HTML recebida, procurando link do PDF...")
                    
                    # Tentar extrair link direto do HTML
                    pdf_url = self.extract_direct_link(response.text)
                    
                    if pdf_url:
                        logger.info(f"Link do PDF encontrado: {pdf_url}")
                        current_url = pdf_url
                        redirect_count += 1
                        time.sleep(1)  # Pequena pausa para não sobrecarregar
                        continue
                    
                    # Se não encontrou link, tentar outras estratégias
                    # Verificar se há meta refresh
                    meta_refresh = re.search(r'<meta[^>]+http-equiv=["\']refresh["\'][^>]+content=["\']([^"\']+)["\']', response.text, re.IGNORECASE)
                    if meta_refresh:
                        content = meta_refresh.group(1)
                        url_match = re.search(r'url=([^;\s]+)', content, re.IGNORECASE)
                        if url_match:
                            new_url = url_match.group(1)
                            if not new_url.startswith('http'):
                                new_url = f"https://www.rad.cvm.gov.br{new_url}"
                            logger.info(f"Meta refresh encontrado: {new_url}")
                            current_url = new_url
                            redirect_count += 1
                            time.sleep(2)
                            continue
                    
                    # Última tentativa: procurar por links de download
                    download_links = re.findall(r'(?:download|baixar)[^>]*href=["\']([^"\']+)["\']', response.text, re.IGNORECASE)
                    if download_links:
                        for link in download_links:
                            if not link.startswith('http'):
                                link = f"https://www.rad.cvm.gov.br{link}"
                            logger.info(f"Link de download encontrado: {link}")
                            current_url = link
                            redirect_count += 1
                            break
                        continue
                    
                    logger.error("Não foi possível encontrar o PDF na página")
                    return False
                
                else:
                    logger.error(f"Tipo de conteúdo inesperado: {content_type}")
                    return False
            
            logger.error(f"Máximo de redirecionamentos ({max_redirects}) atingido")
            return False
            
        except Exception as e:
            logger.error(f"Erro ao baixar: {e}")
            return False
    
    def download_cvm_document(self, url: str, empresa: str, filename: str, categoria: str = "releases") -> Dict:
        """
        Baixa um documento CVM com tratamento completo.
        """
        # Criar estrutura de diretórios
        save_dir = self.base_dir / empresa / categoria
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Limpar nome do arquivo
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        if not filename.endswith('.pdf'):
            filename += '.pdf'
        
        filepath = save_dir / filename
        
        # Verificar se já existe
        if filepath.exists():
            logger.info(f"Arquivo já existe: {filepath}")
            return {
                'status': 'existe',
                'arquivo': str(filepath),
                'tamanho': filepath.stat().st_size
            }
        
        # Tentar download
        logger.info(f"Baixando: {filename}")
        success = self.download_with_redirect_handling(url, filepath)
        
        if success and filepath.exists():
            tamanho = filepath.stat().st_size
            if tamanho > 0:
                logger.info(f"✅ Download concluído: {filename} ({tamanho:,} bytes)")
                return {
                    'status': 'sucesso',
                    'arquivo': str(filepath),
                    'tamanho': tamanho
                }
            else:
                filepath.unlink()
                return {'status': 'erro', 'motivo': 'Arquivo vazio'}
        
        return {'status': 'erro', 'motivo': 'Falha no download'}


def teste_download():
    """
    Testa o download de um documento.
    """
    downloader = CVMDownloaderEnhanced("documents/teste_enhanced")
    
    # URL de teste (você pode pegar uma do relatório de erro)
    test_url = "https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?Tela=ext&descTipo=IPE&CodigoInstituicao=1&numProtocolo=1371158&numSequencia=895870&numVersao=1"
    
    resultado = downloader.download_cvm_document(
        url=test_url,
        empresa="VALE",
        filename="teste_release_vale",
        categoria="testes"
    )
    
    print(f"\nResultado: {resultado}")
    return resultado


if __name__ == "__main__":
    teste_download()