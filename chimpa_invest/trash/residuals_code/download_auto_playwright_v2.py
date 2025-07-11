#!/usr/bin/env python3
"""
Download Automático CVM com Playwright - Versão Aprimorada
=========================================================
Solução robusta para download de PDFs da CVM com tratamento especial
para downloads diretos e páginas com conteúdo dinâmico.
"""

import asyncio
import pandas as pd
from pathlib import Path
import re
import json
from datetime import datetime
from typing import List, Dict, Optional
import logging
import time
from urllib.parse import urljoin, urlparse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from playwright.async_api import async_playwright, Browser, Page, Download
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
    Downloader automático robusto usando Playwright.
    """
    
    def __init__(self, pasta_destino: str = "documents/releases_automatico"):
        self.pasta_destino = Path(pasta_destino)
        self.pasta_destino.mkdir(parents=True, exist_ok=True)
        self.browser: Optional[Browser] = None
        self.context = None
        self.downloads_em_progresso = {}
        
    async def iniciar_navegador(self, headless: bool = True):
        """
        Inicia o navegador com configurações otimizadas.
        """
        self.playwright = await async_playwright().start()
        
        # Criar pasta temporária para downloads
        self.temp_download_dir = self.pasta_destino / "temp_downloads"
        self.temp_download_dir.mkdir(exist_ok=True)
        
        # Configurações otimizadas do navegador
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-gpu',
                '--window-size=1920,1080'
            ]
        )
        
        # Contexto com configurações especiais
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            accept_downloads=True,
            ignore_https_errors=True,
            java_script_enabled=True
        )
        
        # Adicionar headers extras
        await self.context.set_extra_http_headers({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        logger.info("✅ Navegador iniciado com sucesso")
    
    async def fechar_navegador(self):
        """
        Fecha o navegador e limpa recursos.
        """
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("✅ Navegador fechado")
    
    async def baixar_documento_cvm(self, url: str, nome_arquivo: str, empresa: str) -> Dict:
        """
        Baixa um documento com múltiplas estratégias e fallbacks.
        """
        try:
            logger.info(f"📥 Tentando baixar: {url}")
            
            # Criar pasta da empresa
            empresa_dir = self.pasta_destino / empresa.upper()
            empresa_dir.mkdir(exist_ok=True)
            arquivo_final = empresa_dir / nome_arquivo
            
            # Estratégia 1: Download direto via navegador
            page = await self.context.new_page()
            
            # Configurar listener para downloads
            download_capturado = None
            
            async def handle_download(download: Download):
                nonlocal download_capturado
                download_capturado = download
                logger.info(f"📄 Download detectado: {download.suggested_filename}")
            
            page.on("download", handle_download)
            
            try:
                # Navegar com timeout maior
                response = await page.goto(url, timeout=60000, wait_until='networkidle')
                
                # Aguardar possível download automático
                await page.wait_for_timeout(3000)
                
                # Se houve download, processar
                if download_capturado:
                    await download_capturado.save_as(arquivo_final)
                    await page.close()
                    
                    if arquivo_final.exists():
                        logger.info(f"✅ Download direto bem-sucedido: {arquivo_final.name}")
                        return {
                            'status': 'sucesso',
                            'metodo': 'download_direto',
                            'arquivo': str(arquivo_final),
                            'tamanho': arquivo_final.stat().st_size
                        }
                
                # Estratégia 2: Verificar se a página é um PDF inline
                content_type = response.headers.get('content-type', '') if response else ''
                if 'application/pdf' in content_type:
                    logger.info("📄 PDF inline detectado")
                    
                    # Forçar download via JavaScript
                    pdf_url = page.url
                    await page.evaluate(f'''
                        () => {{
                            const link = document.createElement('a');
                            link.href = '{pdf_url}';
                            link.download = '{nome_arquivo}';
                            document.body.appendChild(link);
                            link.click();
                            document.body.removeChild(link);
                        }}
                    ''')
                    
                    await page.wait_for_timeout(5000)
                    
                    if download_capturado:
                        await download_capturado.save_as(arquivo_final)
                        await page.close()
                        return {
                            'status': 'sucesso',
                            'metodo': 'pdf_inline_download',
                            'arquivo': str(arquivo_final)
                        }
                
                # Estratégia 3: Buscar iframes com PDF
                iframes = await page.query_selector_all('iframe')
                for iframe in iframes:
                    src = await iframe.get_attribute('src')
                    if src and ('.pdf' in src.lower() or 'documento' in src.lower()):
                        logger.info(f"📄 PDF em iframe: {src}")
                        
                        # Construir URL completa se necessário
                        if not src.startswith('http'):
                            base_url = 'https://www.rad.cvm.gov.br'
                            src = urljoin(base_url, src)
                        
                        # Abrir iframe em nova página
                        iframe_page = await self.context.new_page()
                        iframe_page.on("download", handle_download)
                        
                        await iframe_page.goto(src, timeout=30000)
                        await iframe_page.wait_for_timeout(3000)
                        
                        if download_capturado:
                            await download_capturado.save_as(arquivo_final)
                            await iframe_page.close()
                            await page.close()
                            return {
                                'status': 'sucesso',
                                'metodo': 'iframe_pdf',
                                'arquivo': str(arquivo_final)
                            }
                        
                        await iframe_page.close()
                
                # Estratégia 4: Procurar links e botões de download
                selectors_download = [
                    'a[href*=".pdf"]',
                    'a[href*="download"]',
                    'a[href*="Download"]',
                    'button:has-text("Download")',
                    'button:has-text("Baixar")',
                    'input[type="button"][value*="Download"]',
                    'a:has-text("PDF")',
                    'a[title*="download"]',
                    'img[src*="pdf"]',
                    'img[alt*="pdf"]'
                ]
                
                for selector in selectors_download:
                    elementos = await page.query_selector_all(selector)
                    if elementos:
                        logger.info(f"🔗 Encontrado elemento: {selector}")
                        
                        for elemento in elementos[:3]:  # Tentar os primeiros 3
                            try:
                                # Resetar captura de download
                                download_capturado = None
                                
                                # Clicar e aguardar
                                await elemento.click()
                                await page.wait_for_timeout(3000)
                                
                                if download_capturado:
                                    await download_capturado.save_as(arquivo_final)
                                    await page.close()
                                    return {
                                        'status': 'sucesso',
                                        'metodo': f'click_{selector}',
                                        'arquivo': str(arquivo_final)
                                    }
                            except Exception as e:
                                logger.debug(f"Erro ao clicar em {selector}: {e}")
                                continue
                
                # Estratégia 5: JavaScript para encontrar e baixar PDFs
                pdf_links = await page.evaluate('''
                    () => {
                        const allLinks = Array.from(document.querySelectorAll('a'));
                        const pdfLinks = allLinks
                            .map(a => ({href: a.href, text: a.textContent}))
                            .filter(link => 
                                link.href && (
                                    link.href.toLowerCase().includes('.pdf') ||
                                    link.href.toLowerCase().includes('download') ||
                                    link.text.toLowerCase().includes('pdf')
                                )
                            );
                        return pdfLinks;
                    }
                ''')
                
                if pdf_links:
                    logger.info(f"🔍 Encontrados {len(pdf_links)} links PDF via JS")
                    for link in pdf_links[:3]:
                        try:
                            download_capturado = None
                            await page.goto(link['href'], timeout=30000)
                            await page.wait_for_timeout(3000)
                            
                            if download_capturado:
                                await download_capturado.save_as(arquivo_final)
                                await page.close()
                                return {
                                    'status': 'sucesso',
                                    'metodo': 'javascript_link',
                                    'arquivo': str(arquivo_final)
                                }
                        except:
                            continue
                
                # Se não conseguiu baixar, salvar screenshot para debug
                screenshot_path = empresa_dir / f"erro_{nome_arquivo.replace('.pdf', '.png')}"
                await page.screenshot(path=screenshot_path, full_page=True)
                logger.warning(f"❌ Não foi possível baixar o PDF. Screenshot salvo: {screenshot_path}")
                
                await page.close()
                return {
                    'status': 'erro',
                    'motivo': 'PDF não encontrado ou download bloqueado',
                    'screenshot': str(screenshot_path)
                }
                
            except Exception as e:
                logger.error(f"❌ Erro durante o download: {e}")
                if page:
                    await page.close()
                return {
                    'status': 'erro',
                    'motivo': str(e)
                }
                
        except Exception as e:
            logger.error(f"❌ Erro geral: {e}")
            return {
                'status': 'erro',
                'motivo': str(e)
            }
    
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
                await asyncio.sleep(3)
        
        # Fechar navegador
        await self.fechar_navegador()
        
        # Limpar pasta temporária
        if self.temp_download_dir.exists():
            for f in self.temp_download_dir.glob('*'):
                f.unlink()
        
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
    print("🚀 DOWNLOAD AUTOMÁTICO CVM - RELEASES TRIMESTRAIS V2")
    print("=" * 60)
    
    if not PLAYWRIGHT_DISPONIVEL:
        return
    
    print("\n✅ Playwright detectado!")
    print("\n📋 INSTRUÇÕES:")
    print("   1. Este script baixa PDFs automaticamente")
    print("   2. Usa múltiplas estratégias para garantir o download")
    print("   3. Salva screenshots em caso de erro para debug")
    
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
        import traceback
        traceback.print_exc()
        await downloader.fechar_navegador()


if __name__ == "__main__":
    # Verificar se tem arquivo IPE
    if not Path("ipe_cia_aberta_2025.csv").exists():
        print("❌ Arquivo ipe_cia_aberta_2025.csv não encontrado!")
        print("   Execute primeiro o script de extração CVM")
    else:
        asyncio.run(main())