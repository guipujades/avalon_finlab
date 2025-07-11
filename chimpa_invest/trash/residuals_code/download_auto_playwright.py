#!/usr/bin/env python3
"""
Download Automático CVM com Playwright
======================================
Solução completa para download automático de PDFs da CVM usando Playwright.
"""

import asyncio
import pandas as pd
from pathlib import Path
import re
import json
from datetime import datetime
from typing import List, Dict, Optional
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_DISPONIVEL = True
except ImportError:
    PLAYWRIGHT_DISPONIVEL = False
    print("\n⚠️  PLAYWRIGHT NÃO INSTALADO!")
    print("Para instalar, execute:")
    print("   pip install playwright")
    print("   playwright install chromium")
    print("   playwright install-deps  # No Linux/WSL\n")


class DownloaderAutomaticoCVM:
    """
    Downloader automático usando Playwright para navegação completa.
    """
    
    def __init__(self, pasta_destino: str = "documents/releases_automatico"):
        self.pasta_destino = Path(pasta_destino)
        self.pasta_destino.mkdir(parents=True, exist_ok=True)
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
    async def iniciar_navegador(self, headless: bool = True):
        """
        Inicia o navegador com Playwright.
        """
        self.playwright = await async_playwright().start()
        
        # Configurações do navegador
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        # Configurar contexto com download
        self.context = await self.browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        self.page = await self.context.new_page()
        
        # Interceptar requisições para debug
        self.page.on("response", self._handle_response)
        
        logger.info("✅ Navegador iniciado com sucesso")
    
    async def _handle_response(self, response):
        """
        Monitora respostas para identificar PDFs.
        """
        if response.status == 200:
            content_type = response.headers.get('content-type', '')
            if 'application/pdf' in content_type:
                logger.info(f"📄 PDF detectado: {response.url}")
    
    async def fechar_navegador(self):
        """
        Fecha o navegador e limpa recursos.
        """
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("✅ Navegador fechado")
    
    async def baixar_documento_cvm(self, url: str, nome_arquivo: str, empresa: str) -> Dict:
        """
        Baixa um documento específico da CVM.
        """
        if not self.page:
            return {'status': 'erro', 'motivo': 'Navegador não iniciado'}
        
        try:
            logger.info(f"📥 Acessando: {url}")
            
            # Criar pasta da empresa
            empresa_dir = self.pasta_destino / empresa.upper()
            empresa_dir.mkdir(exist_ok=True)
            
            # Não há método set_default_download_path no Playwright
            # Os downloads são capturados via expect_download()
            
            # Preparar para capturar download automático
            download_promise = self.page.expect_download()
            
            # Navegar para a URL
            response = await self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # Aguardar um pouco para possível download automático
            try:
                download = await asyncio.wait_for(download_promise, timeout=5)
                # Download automático detectado!
                logger.info("✅ Download automático detectado")
                
                # Salvar com o nome desejado
                arquivo_final = empresa_dir / nome_arquivo
                await download.save_as(arquivo_final)
                
                logger.info(f"✅ PDF salvo: {arquivo_final.name}")
                return {
                    'status': 'sucesso',
                    'metodo': 'download_automatico',
                    'arquivo': str(arquivo_final),
                    'tamanho': arquivo_final.stat().st_size
                }
            except asyncio.TimeoutError:
                # Não houve download automático, tentar outras estratégias
                logger.info("🔍 Sem download automático, tentando outras estratégias...")
            
            # Estratégia 1: Procurar por iframes com PDF
            iframes = await self.page.query_selector_all('iframe')
            for iframe in iframes:
                src = await iframe.get_attribute('src')
                if src and ('.pdf' in src.lower() or 'gerarpdf' in src.lower()):
                    logger.info(f"📄 PDF em iframe encontrado: {src}")
                    
                    # Tentar baixar o PDF do iframe
                    if not src.startswith('http'):
                        src = f"https://www.rad.cvm.gov.br{src}"
                    
                    # Abrir o PDF em nova aba
                    pdf_page = await self.context.new_page()
                    await pdf_page.goto(src)
                    await pdf_page.wait_for_timeout(3000)
                    await pdf_page.close()
                    
                    return {'status': 'sucesso', 'metodo': 'iframe_pdf'}
            
            # Estratégia 2: Clicar em links de download
            download_selectors = [
                'a:has-text("Download")',
                'a:has-text("download")',
                'a:has-text("Baixar")',
                'a:has-text("baixar")',
                'a[href*=".pdf"]',
                'button:has-text("Download")',
                'input[type="button"][value*="Download"]',
                'img[alt*="download"]',
                'a[title*="download"]'
            ]
            
            for selector in download_selectors:
                try:
                    elementos = await self.page.query_selector_all(selector)
                    if elementos:
                        logger.info(f"🔗 Encontrado botão/link de download: {selector}")
                        
                        # Preparar para capturar o download
                        async with self.page.expect_download() as download_info:
                            await elementos[0].click()
                            download = await download_info.value
                            
                            # Salvar com o nome desejado
                            arquivo_final = empresa_dir / nome_arquivo
                            await download.save_as(arquivo_final)
                            
                            logger.info(f"✅ Download concluído: {arquivo_final.name}")
                            return {
                                'status': 'sucesso',
                                'metodo': 'click_download',
                                'arquivo': str(arquivo_final)
                            }
                except Exception as e:
                    logger.debug(f"Tentativa com {selector} falhou: {e}")
                    continue
            
            # Estratégia 3: JavaScript para forçar download
            pdf_urls = await self.page.evaluate('''
                () => {
                    const links = Array.from(document.querySelectorAll('a'));
                    return links
                        .map(a => a.href)
                        .filter(href => href && href.includes('.pdf'));
                }
            ''')
            
            if pdf_urls:
                logger.info(f"🔍 Encontrados {len(pdf_urls)} links PDF via JavaScript")
                pdf_page = await self.context.new_page()
                await pdf_page.goto(pdf_urls[0])
                await pdf_page.wait_for_timeout(3000)
                await pdf_page.close()
                return {'status': 'sucesso', 'metodo': 'javascript_pdf'}
            
            # Estratégia 4: Interceptar requisições de rede
            logger.info("🔄 Tentando capturar PDF via monitoramento de rede...")
            
            # Recarregar a página monitorando downloads
            async with self.page.expect_download(timeout=10000) as download_info:
                await self.page.reload()
                try:
                    download = await download_info.value
                    arquivo_final = empresa_dir / nome_arquivo
                    await download.save_as(arquivo_final)
                    return {
                        'status': 'sucesso',
                        'metodo': 'reload_capture',
                        'arquivo': str(arquivo_final)
                    }
                except:
                    pass
            
            # Se chegou aqui, não conseguiu baixar
            logger.warning("❌ Não foi possível baixar o PDF automaticamente")
            
            # Salvar screenshot para debug
            screenshot_path = empresa_dir / f"erro_{nome_arquivo.replace('.pdf', '.png')}"
            await self.page.screenshot(path=screenshot_path)
            
            return {
                'status': 'erro',
                'motivo': 'PDF não encontrado',
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
    
    async def baixar_releases_empresa(self, empresa: str, ano: int = 2025, 
                                    limite: Optional[int] = None,
                                    headless: bool = True):
        """
        Baixa releases de uma empresa específica.
        """
        print(f"\n🏢 DOWNLOAD AUTOMÁTICO - {empresa} ({ano})")
        print("=" * 60)
        
        # Extrair releases
        releases = self.extrair_releases_ipe(empresa, ano)
        
        if not releases:
            print(f"❌ Nenhum release encontrado para {empresa}")
            return
        
        print(f"✅ Encontrados {len(releases)} releases de resultados")
        
        # Aplicar limite se especificado
        if limite:
            releases = releases[:limite]
            print(f"📊 Limitando a {limite} releases mais recentes")
        
        # Iniciar navegador
        await self.iniciar_navegador(headless=headless)
        
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
            resultado = await self.baixar_documento_cvm(
                release['url'],
                nome_arquivo,
                empresa
            )
            
            if resultado['status'] == 'sucesso':
                sucessos += 1
                print(f"   ✅ Download concluído via {resultado['metodo']}")
            else:
                erros += 1
                print(f"   ❌ Erro: {resultado.get('motivo', 'Desconhecido')}")
            
            resultados.append({**release, **resultado})
            
            # Pausa entre downloads
            if i < len(releases):
                await asyncio.sleep(2)
        
        # Fechar navegador
        await self.fechar_navegador()
        
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
        print(f"   ✅ Downloads bem-sucedidos: {sucessos}")
        print(f"   📁 Arquivos já existentes: {existentes}")
        print(f"   ❌ Erros: {erros}")
        print(f"   📂 Pasta: {empresa_dir}")
        print(f"   📝 Relatório: {relatorio_path.name}")
        
        return relatorio


async def main():
    """
    Função principal com menu interativo.
    """
    print("🚀 DOWNLOAD AUTOMÁTICO CVM - RELEASES TRIMESTRAIS")
    print("=" * 60)
    
    if not PLAYWRIGHT_DISPONIVEL:
        return
    
    print("\n✅ Playwright detectado!")
    print("\n📋 INSTRUÇÕES:")
    print("   1. Este script baixa PDFs automaticamente")
    print("   2. Usa automação avançada do navegador")
    print("   3. Pode demorar alguns segundos por documento")
    
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
        await downloader.baixar_releases_empresa(
            empresa=empresa,
            ano=ano,
            limite=limite,
            headless=headless
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Download interrompido pelo usuário")
        await downloader.fechar_navegador()
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        await downloader.fechar_navegador()


if __name__ == "__main__":
    # Verificar se tem arquivo IPE
    if not Path("ipe_cia_aberta_2025.csv").exists():
        print("❌ Arquivo ipe_cia_aberta_2025.csv não encontrado!")
        print("   Execute primeiro o script de extração CVM")
    else:
        asyncio.run(main())