#!/usr/bin/env python3
"""
Download Automático CVM com Selenium Undetected
===============================================
Versão robusta usando undetected-chromedriver para bypass de detecções.
"""

import os
import time
import json
import shutil
from pathlib import Path
from datetime import datetime
import pandas as pd
import re
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Verificar dependências
try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_DISPONIVEL = True
except ImportError:
    SELENIUM_DISPONIVEL = False
    print("\n⚠️  DEPENDÊNCIAS NÃO INSTALADAS!")
    print("Para instalar, execute:")
    print("   pip install undetected-chromedriver selenium pandas")
    print("\nTambém é necessário ter o Google Chrome instalado.\n")


class DownloaderSeleniumUC:
    """
    Downloader usando Selenium com undetected-chromedriver.
    """
    
    def __init__(self, pasta_destino: str = "documents/releases_selenium_uc"):
        self.pasta_destino = Path(pasta_destino)
        self.pasta_destino.mkdir(parents=True, exist_ok=True)
        self.driver = None
        self.download_dir = None
        
    def configurar_driver(self, headless: bool = False) -> bool:
        """
        Configura o Chrome driver com undetected-chromedriver.
        """
        try:
            # Criar pasta temporária para downloads
            self.download_dir = self.pasta_destino / "temp_downloads"
            self.download_dir.mkdir(exist_ok=True)
            
            # Opções do Chrome
            options = uc.ChromeOptions()
            
            # Configurações de download
            prefs = {
                "download.default_directory": str(self.download_dir.absolute()),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
                "plugins.always_open_pdf_externally": True,
                "profile.default_content_setting_values.automatic_downloads": 1,
                "profile.default_content_settings.popups": 0
            }
            options.add_experimental_option("prefs", prefs)
            
            # Outras opções
            if headless:
                options.add_argument('--headless=new')
            
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            # Criar driver
            self.driver = uc.Chrome(options=options, version_main=None)
            
            # Configurar timeouts
            self.driver.set_page_load_timeout(30)
            self.wait = WebDriverWait(self.driver, 20)
            
            logger.info("✅ Driver configurado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar driver: {e}")
            return False
    
    def fechar_driver(self):
        """
        Fecha o driver e limpa recursos.
        """
        if self.driver:
            self.driver.quit()
            logger.info("✅ Driver fechado")
        
        # Limpar pasta temporária
        if self.download_dir and self.download_dir.exists():
            shutil.rmtree(self.download_dir, ignore_errors=True)
    
    def aguardar_download(self, timeout: int = 30) -> Optional[Path]:
        """
        Aguarda um download ser concluído e retorna o arquivo.
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Listar arquivos na pasta de download
            arquivos = list(self.download_dir.glob("*"))
            
            # Filtrar apenas PDFs completos (sem .crdownload)
            pdfs = [f for f in arquivos if f.suffix.lower() == '.pdf' 
                   and not f.name.endswith('.crdownload')]
            
            if pdfs:
                # Aguardar um pouco para garantir que terminou
                time.sleep(1)
                # Retornar o PDF mais recente
                return max(pdfs, key=lambda f: f.stat().st_mtime)
            
            time.sleep(0.5)
        
        return None
    
    def extrair_pdf_javascript(self) -> Optional[str]:
        """
        Tenta extrair URL do PDF usando JavaScript.
        """
        try:
            # Procurar por PDFs em iframes
            pdf_urls = self.driver.execute_script("""
                var pdfs = [];
                
                // Procurar em iframes
                var iframes = document.querySelectorAll('iframe');
                for (var i = 0; i < iframes.length; i++) {
                    var src = iframes[i].src;
                    if (src && (src.includes('.pdf') || src.includes('PDF'))) {
                        pdfs.push(src);
                    }
                }
                
                // Procurar em links
                var links = document.querySelectorAll('a[href*=".pdf"], a[href*="PDF"]');
                for (var i = 0; i < links.length; i++) {
                    pdfs.push(links[i].href);
                }
                
                // Procurar em embeds
                var embeds = document.querySelectorAll('embed[src*=".pdf"], embed[type="application/pdf"]');
                for (var i = 0; i < embeds.length; i++) {
                    pdfs.push(embeds[i].src);
                }
                
                return pdfs;
            """)
            
            if pdf_urls:
                logger.info(f"🔍 Encontrados {len(pdf_urls)} PDFs via JavaScript")
                return pdf_urls[0]
                
        except Exception as e:
            logger.debug(f"Erro ao extrair PDF via JS: {e}")
        
        return None
    
    def baixar_documento(self, url: str, nome_arquivo: str, empresa: str) -> Dict:
        """
        Baixa um documento específico.
        """
        try:
            logger.info(f"📥 Acessando: {url}")
            
            # Limpar pasta de downloads temporários
            for arquivo in self.download_dir.glob("*"):
                arquivo.unlink()
            
            # Navegar para URL
            self.driver.get(url)
            time.sleep(3)  # Aguardar carregamento inicial
            
            # Verificar se é um PDF direto pelo content-type
            if "application/pdf" in self.driver.execute_script("return document.contentType || ''"):
                logger.info("📄 PDF detectado diretamente")
                arquivo_baixado = self.aguardar_download(10)
                
                if arquivo_baixado:
                    return self._mover_arquivo(arquivo_baixado, nome_arquivo, empresa, "pdf_direto")
            
            # Estratégia 1: Clicar em botões/links de download
            selectors_download = [
                "//a[contains(translate(text(), 'DOWNLOAD', 'download'), 'download')]",
                "//button[contains(translate(text(), 'DOWNLOAD', 'download'), 'download')]",
                "//a[contains(translate(text(), 'BAIXAR', 'baixar'), 'baixar')]",
                "//input[@type='button' and contains(@value, 'Download')]",
                "//a[contains(@href, '.pdf')]",
                "//img[contains(@alt, 'download')]/parent::a",
                "//a[@target='_blank' and contains(@href, 'pdf')]"
            ]
            
            for selector in selectors_download:
                try:
                    elementos = self.driver.find_elements(By.XPATH, selector)
                    if elementos:
                        logger.info(f"🔗 Encontrado elemento de download: {selector}")
                        
                        # Tentar clicar no primeiro elemento visível
                        for elem in elementos:
                            if elem.is_displayed():
                                elem.click()
                                time.sleep(2)
                                
                                # Verificar se iniciou download
                                arquivo_baixado = self.aguardar_download(15)
                                if arquivo_baixado:
                                    return self._mover_arquivo(arquivo_baixado, nome_arquivo, empresa, "click_download")
                                
                                break
                                
                except Exception as e:
                    logger.debug(f"Erro com selector {selector}: {e}")
                    continue
            
            # Estratégia 2: Verificar iframes
            try:
                iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                for i, iframe in enumerate(iframes):
                    src = iframe.get_attribute("src")
                    if src and (".pdf" in src.lower() or "gerarpdf" in src.lower()):
                        logger.info(f"📄 PDF em iframe encontrado: {src}")
                        
                        # Abrir PDF em nova aba
                        self.driver.execute_script(f"window.open('{src}', '_blank');")
                        time.sleep(2)
                        
                        # Mudar para nova aba
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        time.sleep(3)
                        
                        # Verificar download
                        arquivo_baixado = self.aguardar_download(15)
                        
                        # Voltar para aba original
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])
                        
                        if arquivo_baixado:
                            return self._mover_arquivo(arquivo_baixado, nome_arquivo, empresa, "iframe_pdf")
                            
            except Exception as e:
                logger.debug(f"Erro ao verificar iframes: {e}")
            
            # Estratégia 3: JavaScript para encontrar PDFs
            pdf_url = self.extrair_pdf_javascript()
            if pdf_url:
                logger.info(f"🔍 Abrindo PDF encontrado via JS: {pdf_url}")
                self.driver.get(pdf_url)
                time.sleep(3)
                
                arquivo_baixado = self.aguardar_download(15)
                if arquivo_baixado:
                    return self._mover_arquivo(arquivo_baixado, nome_arquivo, empresa, "javascript_pdf")
            
            # Estratégia 4: Forçar download via JavaScript
            try:
                # Injetar função de download
                self.driver.execute_script("""
                    function forceDownload(url) {
                        var a = document.createElement('a');
                        a.href = url;
                        a.download = '';
                        a.click();
                    }
                    
                    // Tentar baixar primeiro PDF encontrado
                    var links = document.querySelectorAll('a[href*=".pdf"]');
                    if (links.length > 0) {
                        forceDownload(links[0].href);
                    }
                """)
                
                time.sleep(3)
                arquivo_baixado = self.aguardar_download(10)
                if arquivo_baixado:
                    return self._mover_arquivo(arquivo_baixado, nome_arquivo, empresa, "force_download")
                    
            except Exception as e:
                logger.debug(f"Erro ao forçar download: {e}")
            
            # Se chegou aqui, não conseguiu baixar
            logger.warning("❌ Não foi possível baixar o PDF")
            
            # Salvar screenshot para debug
            empresa_dir = self.pasta_destino / empresa.upper()
            empresa_dir.mkdir(exist_ok=True)
            screenshot_path = empresa_dir / f"erro_{nome_arquivo.replace('.pdf', '.png')}"
            self.driver.save_screenshot(str(screenshot_path))
            
            return {
                'status': 'erro',
                'motivo': 'PDF não encontrado',
                'screenshot': str(screenshot_path)
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar documento: {e}")
            return {'status': 'erro', 'motivo': str(e)}
    
    def _mover_arquivo(self, arquivo_origem: Path, nome_final: str, empresa: str, metodo: str) -> Dict:
        """
        Move arquivo baixado para pasta final.
        """
        try:
            empresa_dir = self.pasta_destino / empresa.upper()
            empresa_dir.mkdir(exist_ok=True)
            
            arquivo_destino = empresa_dir / nome_final
            shutil.move(str(arquivo_origem), str(arquivo_destino))
            
            logger.info(f"✅ Arquivo salvo: {arquivo_destino.name}")
            
            return {
                'status': 'sucesso',
                'metodo': metodo,
                'arquivo': str(arquivo_destino),
                'tamanho': arquivo_destino.stat().st_size
            }
            
        except Exception as e:
            logger.error(f"Erro ao mover arquivo: {e}")
            return {'status': 'erro', 'motivo': f'Erro ao mover arquivo: {e}'}
    
    def extrair_releases_ipe(self, empresa: str, ano: int = 2025) -> List[Dict]:
        """
        Extrai releases do arquivo IPE.
        """
        ipe_file = f"ipe_cia_aberta_{ano}.csv"
        if not Path(ipe_file).exists():
            logger.error(f"Arquivo {ipe_file} não encontrado")
            return []
        
        # Ler arquivo
        df = pd.read_csv(ipe_file, sep=';', encoding='latin-1')
        
        # Filtrar empresa
        df_empresa = df[df['Nome_Companhia'].str.contains(empresa.upper(), case=False, na=False)]
        
        # Filtrar releases
        palavras = ['resultado', 'trimestre', 'itr', '1t', '2t', '3t', '4t', 'release', 'earnings']
        mask = df_empresa['Assunto'].str.lower().str.contains('|'.join(palavras), na=False)
        releases = df_empresa[mask]
        
        # Converter para lista
        releases_list = []
        for _, row in releases.iterrows():
            releases_list.append({
                'data': row['Data_Entrega'],
                'assunto': row['Assunto'],
                'categoria': row['Categoria'],
                'url': row['Link_Download']
            })
        
        releases_list.sort(key=lambda x: x['data'], reverse=True)
        return releases_list
    
    def baixar_releases_empresa(self, empresa: str, ano: int = 2025, 
                               limite: Optional[int] = None, 
                               headless: bool = False):
        """
        Baixa releases de uma empresa.
        """
        print(f"\n🏢 DOWNLOAD AUTOMÁTICO - {empresa} ({ano})")
        print("=" * 60)
        
        # Extrair releases
        releases = self.extrair_releases_ipe(empresa, ano)
        
        if not releases:
            print(f"❌ Nenhum release encontrado para {empresa}")
            return
        
        print(f"✅ Encontrados {len(releases)} releases")
        
        if limite:
            releases = releases[:limite]
            print(f"📊 Limitando a {limite} releases")
        
        # Configurar driver
        if not self.configurar_driver(headless):
            return
        
        # Baixar releases
        resultados = []
        sucessos = 0
        erros = 0
        existentes = 0
        
        for i, release in enumerate(releases, 1):
            print(f"\n[{i}/{len(releases)}] {release['data'][:10]} - {release['assunto'][:60]}...")
            
            # Gerar nome do arquivo
            data_clean = release['data'].replace('-', '')[:8]
            assunto_clean = re.sub(r'[^\w\s-]', '', release['assunto'])[:50]
            nome_arquivo = f"{data_clean}_{assunto_clean}.pdf"
            
            # Verificar se existe
            arquivo_path = self.pasta_destino / empresa.upper() / nome_arquivo
            if arquivo_path.exists():
                print(f"   📁 Já existe: {arquivo_path.name}")
                existentes += 1
                resultados.append({
                    **release,
                    'status': 'existente',
                    'arquivo': str(arquivo_path)
                })
                continue
            
            # Baixar
            resultado = self.baixar_documento(release['url'], nome_arquivo, empresa)
            
            if resultado['status'] == 'sucesso':
                sucessos += 1
                print(f"   ✅ Baixado via {resultado['metodo']}")
            else:
                erros += 1
                print(f"   ❌ Erro: {resultado.get('motivo', 'Desconhecido')}")
            
            resultados.append({**release, **resultado})
            
            # Pausa entre downloads
            if i < len(releases):
                time.sleep(2)
        
        # Fechar driver
        self.fechar_driver()
        
        # Salvar relatório
        self._salvar_relatorio(empresa, ano, releases, resultados, sucessos, erros, existentes)
        
        # Resumo
        print(f"\n{'='*60}")
        print(f"📊 RESUMO - {empresa}")
        print(f"   ✅ Baixados: {sucessos}")
        print(f"   📁 Existentes: {existentes}")
        print(f"   ❌ Erros: {erros}")
        print(f"   📂 Pasta: {self.pasta_destino / empresa.upper()}")
    
    def _salvar_relatorio(self, empresa, ano, releases, resultados, sucessos, erros, existentes):
        """
        Salva relatório da execução.
        """
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
        empresa_dir.mkdir(exist_ok=True)
        
        relatorio_path = empresa_dir / f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(relatorio_path, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📝 Relatório salvo: {relatorio_path}")


def main():
    """
    Função principal.
    """
    print("🚀 DOWNLOAD AUTOMÁTICO CVM COM SELENIUM UC")
    print("=" * 50)
    
    if not SELENIUM_DISPONIVEL:
        return
    
    print("\n✅ Selenium e undetected-chromedriver detectados!")
    
    # Menu
    empresa = input("\n🏢 Nome da empresa: ").strip().upper()
    if not empresa:
        print("❌ Nome obrigatório")
        return
    
    ano_str = input("📅 Ano [2025]: ").strip()
    ano = int(ano_str) if ano_str.isdigit() else 2025
    
    limite_str = input("📊 Quantos releases? (Enter = todos): ").strip()
    limite = int(limite_str) if limite_str.isdigit() else None
    
    headless = input("🖥️  Modo invisível? (s/N): ").strip().lower() == 's'
    
    # Executar
    downloader = DownloaderSeleniumUC()
    
    try:
        downloader.baixar_releases_empresa(empresa, ano, limite, headless)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompido pelo usuário")
        downloader.fechar_driver()
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        downloader.fechar_driver()


if __name__ == "__main__":
    if not Path("ipe_cia_aberta_2025.csv").exists():
        print("❌ Arquivo IPE não encontrado!")
    else:
        main()