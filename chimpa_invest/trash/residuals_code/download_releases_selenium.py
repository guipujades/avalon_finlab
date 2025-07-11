#!/usr/bin/env python3
"""
Download de Releases com Selenium
=================================
Usa Selenium para baixar PDFs que exigem JavaScript ou redirecionamentos complexos.
"""

import os
import time
import json
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import re


class ReleaseDownloaderSelenium:
    """
    Downloader de releases usando Selenium para navegação automatizada.
    """
    
    def __init__(self, download_dir: str = None):
        if download_dir is None:
            download_dir = str(Path.cwd() / "documents" / "releases_selenium")
        
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar Chrome
        self.chrome_options = Options()
        self.chrome_options.add_experimental_option('prefs', {
            'download.default_directory': str(self.download_dir),
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'safebrowsing.enabled': True,
            'plugins.always_open_pdf_externally': True
        })
        
        # Adicionar opções para headless (sem interface gráfica)
        # Comente a linha abaixo se quiser ver o navegador funcionando
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        
        self.driver = None
    
    def iniciar_navegador(self):
        """
        Inicia o navegador Chrome.
        """
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            print("✅ Navegador iniciado com sucesso")
            return True
        except Exception as e:
            print(f"❌ Erro ao iniciar navegador: {e}")
            print("\n⚠️  Certifique-se de ter o Chrome e o ChromeDriver instalados!")
            print("   Download ChromeDriver: https://chromedriver.chromium.org/")
            return False
    
    def fechar_navegador(self):
        """
        Fecha o navegador.
        """
        if self.driver:
            self.driver.quit()
            print("✅ Navegador fechado")
    
    def baixar_documento_cvm(self, url: str, nome_arquivo: str, timeout: int = 30) -> bool:
        """
        Baixa um documento da CVM usando Selenium.
        """
        if not self.driver:
            print("❌ Navegador não iniciado")
            return False
        
        try:
            print(f"📥 Acessando: {url}")
            self.driver.get(url)
            
            # Aguardar página carregar
            time.sleep(3)
            
            # Verificar se é um PDF direto
            if "application/pdf" in self.driver.execute_script("return document.contentType"):
                print("✅ PDF carregado diretamente")
                return True
            
            # Procurar por links de download na página
            download_links = self.driver.find_elements(By.PARTIAL_LINK_TEXT, "Download")
            if not download_links:
                download_links = self.driver.find_elements(By.PARTIAL_LINK_TEXT, "Baixar")
            
            if download_links:
                print(f"🔗 Encontrado {len(download_links)} link(s) de download")
                download_links[0].click()
                time.sleep(5)  # Aguardar download iniciar
                return True
            
            # Procurar por iframes com PDF
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                src = iframe.get_attribute("src")
                if src and (".pdf" in src or "frmGeraPDF" in src):
                    print(f"📄 PDF encontrado em iframe: {src}")
                    self.driver.get(src)
                    time.sleep(5)
                    return True
            
            # Última tentativa: procurar qualquer link com .pdf
            pdf_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf')]")
            if pdf_links:
                print(f"📎 Encontrado link PDF direto")
                pdf_links[0].click()
                time.sleep(5)
                return True
            
            print("❌ Não foi possível encontrar o PDF na página")
            return False
            
        except Exception as e:
            print(f"❌ Erro ao baixar documento: {e}")
            return False
    
    def extrair_releases_ipe(self, empresa: str, ano: int = 2025) -> list:
        """
        Extrai releases de resultados do arquivo IPE.
        """
        ipe_file = f"ipe_cia_aberta_{ano}.csv"
        if not Path(ipe_file).exists():
            print(f"❌ Arquivo {ipe_file} não encontrado")
            return []
        
        # Ler arquivo IPE
        df = pd.read_csv(ipe_file, sep=';', encoding='latin-1')
        
        # Filtrar por empresa
        df_empresa = df[df['Nome_Companhia'].str.contains(empresa.upper(), case=False, na=False)]
        
        # Palavras-chave para releases de resultados
        palavras_resultado = ['resultado', 'trimestre', 'itr', '1t', '2t', '3t', '4t', 
                            'release', 'earnings', 'desempenho', 'demonstrações']
        
        # Filtrar por assunto
        mask = df_empresa['Assunto'].str.lower().str.contains('|'.join(palavras_resultado), na=False)
        releases = df_empresa[mask]
        
        # Converter para lista de dicionários
        releases_list = []
        for _, row in releases.iterrows():
            releases_list.append({
                'empresa': row['Nome_Companhia'],
                'data': row['Data_Entrega'],
                'assunto': row['Assunto'],
                'categoria': row['Categoria'],
                'url': row['Link_Download']
            })
        
        # Ordenar por data (mais recente primeiro)
        releases_list.sort(key=lambda x: x['data'], reverse=True)
        
        return releases_list
    
    def baixar_releases_empresa(self, empresa: str, ano: int = 2025, limite: int = None):
        """
        Baixa releases de uma empresa.
        """
        print(f"\n🏢 Baixando releases de {empresa} - {ano}")
        print("=" * 50)
        
        # Extrair releases
        releases = self.extrair_releases_ipe(empresa, ano)
        
        if not releases:
            print(f"❌ Nenhum release encontrado para {empresa}")
            return
        
        print(f"✅ Encontrados {len(releases)} releases")
        
        # Aplicar limite se especificado
        if limite:
            releases = releases[:limite]
        
        # Iniciar navegador
        if not self.iniciar_navegador():
            return
        
        # Criar pasta da empresa
        empresa_dir = self.download_dir / empresa.upper()
        empresa_dir.mkdir(exist_ok=True)
        
        # Baixar cada release
        sucessos = 0
        erros = 0
        
        for i, release in enumerate(releases, 1):
            print(f"\n[{i}/{len(releases)}] {release['assunto'][:60]}...")
            
            # Gerar nome do arquivo
            data_clean = release['data'].replace('-', '')[:8]
            assunto_clean = re.sub(r'[^\w\s-]', '', release['assunto'])[:50]
            nome_arquivo = f"{data_clean}_{assunto_clean}.pdf"
            
            # Baixar
            if self.baixar_documento_cvm(release['url'], nome_arquivo):
                sucessos += 1
                print(f"✅ Download concluído")
            else:
                erros += 1
                print(f"❌ Falha no download")
            
            # Pausa entre downloads
            if i < len(releases):
                time.sleep(2)
        
        # Fechar navegador
        self.fechar_navegador()
        
        # Resumo
        print(f"\n📊 RESUMO:")
        print(f"   ✅ Downloads bem-sucedidos: {sucessos}")
        print(f"   ❌ Downloads com erro: {erros}")
        print(f"   📁 Arquivos salvos em: {empresa_dir}")
        
        # Salvar relatório
        relatorio = {
            'empresa': empresa,
            'data_execucao': datetime.now().isoformat(),
            'releases_encontrados': len(releases),
            'downloads_sucesso': sucessos,
            'downloads_erro': erros,
            'pasta_destino': str(empresa_dir),
            'releases': releases
        }
        
        relatorio_file = empresa_dir / f"relatorio_{empresa}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(relatorio_file, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)
        
        print(f"\n📝 Relatório salvo: {relatorio_file}")


def main():
    """
    Menu principal.
    """
    print("🌐 DOWNLOAD DE RELEASES COM SELENIUM")
    print("=" * 40)
    print("\n⚠️  REQUISITOS:")
    print("   - Google Chrome instalado")
    print("   - ChromeDriver compatível com sua versão do Chrome")
    print("   - pip install selenium pandas")
    
    downloader = ReleaseDownloaderSelenium()
    
    # Verificar se arquivo IPE existe
    ano = 2025
    ipe_file = f"ipe_cia_aberta_{ano}.csv"
    if not Path(ipe_file).exists():
        print(f"\n❌ Arquivo {ipe_file} não encontrado!")
        print("   Execute primeiro o script de extração CVM")
        return
    
    # Menu interativo
    print("\n📊 DOWNLOAD INTERATIVO")
    empresa = input("🏢 Digite o nome da empresa (ex: VALE, PETROBRAS): ").strip().upper()
    
    if not empresa:
        print("❌ Nome da empresa é obrigatório")
        return
    
    limite_str = input("📥 Quantos releases baixar? (Enter = todos): ").strip()
    limite = int(limite_str) if limite_str.isdigit() else None
    
    # Executar download
    downloader.baixar_releases_empresa(empresa, ano, limite)


if __name__ == "__main__":
    main()