#!/usr/bin/env python3
"""
Download Automático CVM com Selenium
====================================
Solução 100% automatizada para download de PDFs da CVM.
"""

import time
import pandas as pd
from pathlib import Path
import re
import json
from datetime import datetime
from typing import List, Dict, Optional
import logging
import requests
from urllib.parse import urljoin
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_DISPONIVEL = True
except ImportError:
    SELENIUM_DISPONIVEL = False
    print("\n⚠️  SELENIUM NÃO INSTALADO!")
    print("Para instalar, execute:")
    print("   pip install selenium")
    print("   pip install webdriver-manager")


class DownloaderAutomaticoCVM:
    """
    Downloader 100% automático usando Selenium.
    """
    
    def __init__(self, pasta_destino: str = "documents/releases_automatico"):
        self.pasta_destino = Path(pasta_destino).resolve()
        self.pasta_destino.mkdir(parents=True, exist_ok=True)
        self.driver = None
        
    def configurar_chrome_para_download_automatico(self, empresa: str):
        """
        Configura o Chrome para download automático sem confirmação.
        """
        chrome_options = Options()
        
        # Criar pasta específica da empresa
        empresa_dir = self.pasta_destino / empresa.upper()
        empresa_dir.mkdir(exist_ok=True)
        download_dir = str(empresa_dir.resolve())
        
        # Preferências para download automático
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": False,
            "plugins.always_open_pdf_externally": True,  # Força download de PDFs
            "profile.default_content_settings.popups": 0,
            "profile.default_content_setting_values.automatic_downloads": 1,
            "download.extensions_to_open": "applications/pdf",
            "profile.content_settings.exceptions.automatic_downloads.*.setting": 1
        }
        
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Opções para evitar detecção de automação
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Outras opções úteis
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        
        # Modo headless opcional
        if hasattr(self, 'headless') and self.headless:
            chrome_options.add_argument("--headless=new")
        
        return chrome_options
    
    def iniciar_navegador(self, empresa: str, headless: bool = True):
        """
        Inicia o navegador com configurações para download automático.
        """
        self.headless = headless
        
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            
            chrome_options = self.configurar_chrome_para_download_automatico(empresa)
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Habilitar download em modo headless (Chrome 100+)
            if headless:
                params = {
                    "behavior": "allow",
                    "downloadPath": str((self.pasta_destino / empresa.upper()).resolve())
                }
                self.driver.execute_cdp_cmd("Page.setDownloadBehavior", params)
            
            logger.info("✅ Navegador iniciado com download automático configurado")
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar navegador: {e}")
            logger.info("Tentando usar o Chrome já instalado...")
            
            chrome_options = self.configurar_chrome_para_download_automatico(empresa)
            self.driver = webdriver.Chrome(options=chrome_options)
            
            if headless:
                params = {
                    "behavior": "allow",
                    "downloadPath": str((self.pasta_destino / empresa.upper()).resolve())
                }
                self.driver.execute_cdp_cmd("Page.setDownloadBehavior", params)
    
    def fechar_navegador(self):
        """
        Fecha o navegador.
        """
        if self.driver:
            self.driver.quit()
            logger.info("✅ Navegador fechado")
    
    def aguardar_download(self, timeout: int = 30) -> bool:
        """
        Aguarda o download ser concluído verificando a pasta.
        """
        tempo_inicial = time.time()
        
        while time.time() - tempo_inicial < timeout:
            # Verificar se há arquivos .crdownload (download em progresso)
            arquivos_temp = list(self.pasta_destino.rglob("*.crdownload"))
            arquivos_tmp = list(self.pasta_destino.rglob("*.tmp"))
            
            if not arquivos_temp and not arquivos_tmp:
                # Verificar se há novos PDFs
                time.sleep(1)
                return True
            
            time.sleep(0.5)
        
        return False
    
    def baixar_documento_cvm(self, url: str, nome_arquivo: str, empresa: str) -> Dict:
        """
        Baixa um documento da CVM de forma totalmente automática.
        """
        try:
            logger.info(f"📥 Acessando: {url}")
            
            empresa_dir = self.pasta_destino / empresa.upper()
            
            # Contar PDFs antes do download
            pdfs_antes = list(empresa_dir.glob("*.pdf"))
            
            # Acessar a URL
            self.driver.get(url)
            
            # Aguardar página carregar
            time.sleep(3)
            
            # Verificar se é um PDF direto
            if "application/pdf" in self.driver.execute_script("return document.contentType || '';"):
                logger.info("📄 PDF direto detectado, download automático em andamento...")
                
                # Aguardar download
                if self.aguardar_download():
                    # Encontrar o novo PDF
                    pdfs_depois = list(empresa_dir.glob("*.pdf"))
                    novos_pdfs = [p for p in pdfs_depois if p not in pdfs_antes]
                    
                    if novos_pdfs:
                        # Renomear o arquivo baixado
                        pdf_baixado = novos_pdfs[0]
                        arquivo_final = empresa_dir / nome_arquivo
                        pdf_baixado.rename(arquivo_final)
                        
                        logger.info(f"✅ Download automático concluído: {arquivo_final.name}")
                        return {
                            'status': 'sucesso',
                            'metodo': 'download_direto',
                            'arquivo': str(arquivo_final),
                            'tamanho': arquivo_final.stat().st_size
                        }
            
            # Procurar por iframes com PDF
            try:
                iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                for iframe in iframes:
                    src = iframe.get_attribute("src")
                    if src and ('.pdf' in src.lower() or 'documento' in src.lower()):
                        logger.info(f"📄 PDF em iframe encontrado")
                        
                        # Construir URL completa
                        if not src.startswith('http'):
                            src = urljoin("https://www.rad.cvm.gov.br", src)
                        
                        # Abrir o PDF do iframe
                        self.driver.get(src)
                        time.sleep(3)
                        
                        if self.aguardar_download():
                            pdfs_depois = list(empresa_dir.glob("*.pdf"))
                            novos_pdfs = [p for p in pdfs_depois if p not in pdfs_antes]
                            
                            if novos_pdfs:
                                pdf_baixado = novos_pdfs[0]
                                arquivo_final = empresa_dir / nome_arquivo
                                pdf_baixado.rename(arquivo_final)
                                
                                return {
                                    'status': 'sucesso',
                                    'metodo': 'iframe_pdf',
                                    'arquivo': str(arquivo_final)
                                }
            except Exception as e:
                logger.debug(f"Erro ao verificar iframes: {e}")
            
            # Procurar e clicar em links/botões de download automaticamente
            selectors = [
                "//a[contains(@href, '.pdf')]",
                "//a[contains(translate(text(), 'DOWNLOAD', 'download'), 'download')]",
                "//button[contains(translate(text(), 'DOWNLOAD', 'download'), 'download')]",
                "//a[contains(translate(text(), 'PDF', 'pdf'), 'pdf')]",
                "//img[contains(@src, 'pdf')]/..",
                "//a[contains(@title, 'download')]",
                "//a[contains(@title, 'Download')]"
            ]
            
            for selector in selectors:
                try:
                    elementos = self.driver.find_elements(By.XPATH, selector)
                    if elementos:
                        logger.info(f"🔗 Encontrado elemento de download: {selector}")
                        
                        # Clicar no primeiro elemento válido
                        for elemento in elementos[:3]:
                            try:
                                # Scroll até o elemento
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", elemento)
                                time.sleep(1)
                                
                                # Clicar
                                elemento.click()
                                logger.info("🖱️ Clique automático realizado")
                                
                                # Aguardar download
                                if self.aguardar_download(timeout=10):
                                    pdfs_depois = list(empresa_dir.glob("*.pdf"))
                                    novos_pdfs = [p for p in pdfs_depois if p not in pdfs_antes]
                                    
                                    if novos_pdfs:
                                        pdf_baixado = novos_pdfs[0]
                                        arquivo_final = empresa_dir / nome_arquivo
                                        pdf_baixado.rename(arquivo_final)
                                        
                                        return {
                                            'status': 'sucesso',
                                            'metodo': f'clique_automatico_{selector}',
                                            'arquivo': str(arquivo_final)
                                        }
                            except Exception as e:
                                logger.debug(f"Erro ao clicar: {e}")
                                continue
                except Exception as e:
                    logger.debug(f"Erro com selector {selector}: {e}")
            
            # Última tentativa: download direto via requests
            logger.info("🔄 Tentando download direto via requests...")
            try:
                # Obter cookies do navegador
                cookies = self.driver.get_cookies()
                session = requests.Session()
                for cookie in cookies:
                    session.cookies.set(cookie['name'], cookie['value'])
                
                # Headers do navegador
                headers = {
                    'User-Agent': self.driver.execute_script("return navigator.userAgent;"),
                    'Accept': 'application/pdf,*/*',
                    'Referer': self.driver.current_url
                }
                
                # Baixar
                response = session.get(url, headers=headers, allow_redirects=True, timeout=30)
                
                if response.status_code == 200 and len(response.content) > 1000:
                    arquivo_final = empresa_dir / nome_arquivo
                    arquivo_final.write_bytes(response.content)
                    
                    logger.info(f"✅ Download via requests bem-sucedido")
                    return {
                        'status': 'sucesso',
                        'metodo': 'requests_direto',
                        'arquivo': str(arquivo_final),
                        'tamanho': len(response.content)
                    }
            except Exception as e:
                logger.debug(f"Erro no download via requests: {e}")
            
            # Se chegou aqui, não conseguiu baixar
            logger.warning("❌ Não foi possível baixar o PDF automaticamente")
            
            # Salvar screenshot para debug
            screenshot_path = empresa_dir / f"erro_{nome_arquivo.replace('.pdf', '.png')}"
            self.driver.save_screenshot(str(screenshot_path))
            
            return {
                'status': 'erro',
                'motivo': 'PDF não encontrado ou download bloqueado',
                'screenshot': str(screenshot_path)
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao baixar documento: {e}")
            return {'status': 'erro', 'motivo': str(e)}
    
    def extrair_releases_ipe(self, empresa: str, ano: int = 2025) -> List[Dict]:
        """
        Extrai releases de resultados do arquivo IPE.
        """
        ipe_file = f"ipe_cia_aberta_{ano}.csv"
        if not Path(ipe_file).exists():
            logger.error(f"Arquivo {ipe_file} não encontrado")
            return []
        
        # Ler arquivo IPE
        df = pd.read_csv(ipe_file, sep=';', encoding='latin-1')
        
        # Filtrar por empresa
        df_empresa = df[df['Nome_Companhia'].str.contains(empresa.upper(), case=False, na=False)]
        
        # Palavras-chave para releases de resultados
        palavras_resultado = [
            'resultado', 'trimestre', 'itr', '1t', '2t', '3t', '4t',
            'release', 'earnings', 'desempenho', 'demonstrações'
        ]
        
        # Criar padrão regex
        padrao = '|'.join(palavras_resultado)
        mask = df_empresa['Assunto'].str.lower().str.contains(padrao, na=False)
        releases = df_empresa[mask]
        
        # Converter para lista
        releases_list = []
        for _, row in releases.iterrows():
            releases_list.append({
                'data': row['Data_Entrega'],
                'assunto': row['Assunto'],
                'categoria': row['Categoria'],
                'url': row['Link_Download'],
                'protocolo': row.get('Protocolo_Entrega', '')
            })
        
        # Ordenar por data (mais recente primeiro)
        releases_list.sort(key=lambda x: x['data'], reverse=True)
        
        return releases_list
    
    def baixar_releases_empresa(self, empresa: str, ano: int = 2025, 
                               limite: Optional[int] = None,
                               headless: bool = True):
        """
        Baixa releases de uma empresa de forma 100% automática.
        """
        print(f"\n🏢 DOWNLOAD 100% AUTOMÁTICO - {empresa} ({ano})")
        print("=" * 60)
        
        # Extrair releases
        releases = self.extrair_releases_ipe(empresa, ano)
        
        if not releases:
            print(f"❌ Nenhum release encontrado para {empresa}")
            return
        
        print(f"✅ Encontrados {len(releases)} releases de resultados")
        
        # Aplicar limite
        if limite:
            releases = releases[:limite]
            print(f"📊 Limitando a {limite} releases mais recentes")
        
        # Iniciar navegador
        self.iniciar_navegador(empresa, headless)
        
        # Resultados
        resultados = []
        sucessos = 0
        erros = 0
        existentes = 0
        
        # Baixar cada release
        for i, release in enumerate(releases, 1):
            print(f"\n[{i}/{len(releases)}] {release['data'][:10]} - {release['assunto'][:60]}...")
            
            # Gerar nome do arquivo
            data_clean = release['data'].replace('-', '')[:8]
            assunto_clean = re.sub(r'[^\w\s-]', '', release['assunto'])[:50]
            nome_arquivo = f"{data_clean}_{assunto_clean}.pdf"
            
            # Verificar se já existe
            arquivo_path = self.pasta_destino / empresa.upper() / nome_arquivo
            if arquivo_path.exists():
                print(f"   📁 Arquivo já existe: {arquivo_path.name}")
                existentes += 1
                resultados.append({
                    **release,
                    'status': 'existente',
                    'arquivo': str(arquivo_path)
                })
                continue
            
            # Baixar
            resultado = self.baixar_documento_cvm(
                release['url'],
                nome_arquivo,
                empresa
            )
            
            if resultado['status'] == 'sucesso':
                sucessos += 1
                print(f"   ✅ Download automático concluído via {resultado['metodo']}")
            else:
                erros += 1
                print(f"   ❌ Erro: {resultado.get('motivo', 'Desconhecido')}")
            
            resultados.append({**release, **resultado})
            
            # Pausa entre downloads
            if i < len(releases):
                time.sleep(3)
        
        # Fechar navegador
        self.fechar_navegador()
        
        # Salvar relatório
        relatorio = {
            'empresa': empresa,
            'data_execucao': datetime.now().isoformat(),
            'ano': ano,
            'releases_encontrados': len(releases),
            'downloads_sucesso': sucessos,
            'downloads_erro': erros,
            'arquivos_existentes': existentes,
            'resultados': resultados
        }
        
        empresa_dir = self.pasta_destino / empresa.upper()
        relatorio_path = empresa_dir / f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(relatorio_path, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)
        
        # Resumo final
        print(f"\n{'='*60}")
        print(f"📊 RESUMO FINAL - {empresa}")
        print(f"   ✅ Downloads automáticos bem-sucedidos: {sucessos}")
        print(f"   📁 Arquivos já existentes: {existentes}")
        print(f"   ❌ Erros: {erros}")
        print(f"   📂 Pasta: {empresa_dir}")
        print(f"   📝 Relatório: {relatorio_path.name}")
        
        return relatorio


def main():
    """
    Função principal com menu interativo.
    """
    print("🚀 DOWNLOAD 100% AUTOMÁTICO CVM - SELENIUM")
    print("=" * 60)
    
    if not SELENIUM_DISPONIVEL:
        return
    
    print("\n✅ Selenium detectado!")
    print("\n📋 CARACTERÍSTICAS:")
    print("   ✅ Download 100% automático - sem interação manual")
    print("   ✅ Cliques automáticos quando necessário")
    print("   ✅ Múltiplas estratégias de download")
    print("   ✅ Funciona em modo invisível (headless)")
    
    # Configurações
    print("\n⚙️  CONFIGURAÇÕES:")
    
    empresa = input("🏢 Nome da empresa (ex: VALE, PETROBRAS): ").strip().upper()
    if not empresa:
        print("❌ Nome obrigatório")
        return
    
    ano_str = input("📅 Ano [2025]: ").strip()
    ano = int(ano_str) if ano_str.isdigit() else 2025
    
    limite_str = input("📊 Quantos releases baixar? (Enter = todos): ").strip()
    limite = int(limite_str) if limite_str.isdigit() else None
    
    headless_str = input("🖥️  Executar em modo invisível? (S/n): ").strip().lower()
    headless = headless_str != 'n'
    
    # Executar download
    downloader = DownloaderAutomaticoCVM()
    
    try:
        downloader.baixar_releases_empresa(
            empresa=empresa,
            ano=ano,
            limite=limite,
            headless=headless
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Download interrompido pelo usuário")
        downloader.fechar_navegador()
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        downloader.fechar_navegador()


if __name__ == "__main__":
    # Verificar se tem arquivo IPE
    if not Path("ipe_cia_aberta_2025.csv").exists():
        print("❌ Arquivo ipe_cia_aberta_2025.csv não encontrado!")
        print("   Execute primeiro o script de extração CVM")
    else:
        main()