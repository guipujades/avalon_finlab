#!/usr/bin/env python3
"""
CVM Download Releases - Múltiplas Empresas
==========================================
Baixa releases trimestrais de múltiplas empresas automaticamente.
Separa releases de resultados em 'pending' e outros em 'residuals'.
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
    print("\nSELENIUM NÃO INSTALADO!")
    print("Para instalar, execute:")
    print("   pip install selenium webdriver-manager")


class CVMReleasesDownloader:
    """
    Downloader de releases CVM para múltiplas empresas.
    """
    
    def __init__(self, apenas_releases_trimestrais: bool = False):
        # Estrutura de pastas
        self.pasta_pending = Path("documents/pending")
        self.pasta_residuals = Path("documents/residuals")
        self.pasta_pending.mkdir(parents=True, exist_ok=True)
        self.pasta_residuals.mkdir(parents=True, exist_ok=True)
        
        self.driver = None
        self.empresas_processadas = []
        self.apenas_releases_trimestrais = apenas_releases_trimestrais
        
    def configurar_chrome_para_download(self, pasta_download: str):
        """
        Configura Chrome para download automático.
        """
        chrome_options = Options()
        
        prefs = {
            "download.default_directory": pasta_download,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": False,
            "plugins.always_open_pdf_externally": True,
            "profile.default_content_settings.popups": 0,
            "profile.default_content_setting_values.automatic_downloads": 1,
        }
        
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        return chrome_options
    
    def iniciar_navegador(self, headless: bool = True):
        """
        Inicia navegador configurado.
        """
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            
            # Usar pasta temporária para downloads
            temp_dir = str(Path.cwd() / "temp_downloads")
            os.makedirs(temp_dir, exist_ok=True)
            
            chrome_options = self.configurar_chrome_para_download(temp_dir)
            if headless:
                chrome_options.add_argument("--headless=new")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Habilitar download em headless
            if headless:
                params = {"behavior": "allow", "downloadPath": temp_dir}
                self.driver.execute_cdp_cmd("Page.setDownloadBehavior", params)
            
            logger.info("Navegador iniciado")
            
        except Exception as e:
            logger.error(f"Erro ao iniciar navegador: {e}")
            raise
    
    def fechar_navegador(self):
        """
        Fecha navegador.
        """
        if self.driver:
            self.driver.quit()
            logger.info("Navegador fechado")
    
    def e_release_trimestral(self, assunto: str, categoria: str = '', tipo: str = '') -> bool:
        """
        Verifica se é um Release de Resultados / Earnings Release trimestral.
        """
        assunto_lower = assunto.lower() if assunto else ''
        categoria_lower = str(categoria).lower() if categoria and str(categoria) != 'nan' else ''
        tipo_lower = str(tipo).lower() if tipo and str(tipo) != 'nan' else ''
        
        # Verificar se é categoria de dados econômico-financeiros + press-release
        if 'econômico-financeiro' in categoria_lower or 'economico-financeiro' in categoria_lower:
            if 'press-release' in tipo_lower or 'press release' in tipo_lower:
                # É um press-release financeiro - verificar se é de resultados
                padroes_resultados = [
                    r'desempenho',  # Padrão Vale/Petrobras
                    r'release.*resultado', r'earnings.*release',
                    r'resultado.*\d+t\d{2}',  # Resultado 1T25
                    r'\d+t\d{2}.*resultado',  # 1T25 Resultado
                    r'relatório.*desempenho'  # Relatório de Desempenho
                ]
                
                for padrao in padroes_resultados:
                    if re.search(padrao, assunto_lower):
                        return True
        
        # Padrões diretos de release de resultados
        padroes_release = [
            r'release\s*de\s*resultado',  # Release de Resultados
            r'earnings\s*release',  # Earnings Release
            r'desempenho.*\d+t\d{2}',  # Desempenho da Vale no 1T25
            r'relatório\s*de\s*desempenho',  # Relatório de Desempenho
            r'resultado.*trimestral.*\d+t\d{2}'  # Resultado Trimestral 1T25
        ]
        
        for padrao in padroes_release:
            if re.search(padrao, assunto_lower):
                return True
        
        # Evitar documentos que NÃO são releases de resultados
        termos_excluir = [
            'relatório.*administração', 'relatorio.*administracao',
            'ata', 'edital', 'aviso aos', 'comunicado ao mercado',
            'fato relevante', 'produção e vendas',  # Relatório operacional
            'conference call',  # Apresentação, não o release
            'apresentação'  # Slides
        ]
        
        for termo in termos_excluir:
            if re.search(termo, assunto_lower):
                return False
        
        # Verificar se tem indicação de trimestre
        tem_trimestre = any(re.search(padrao, assunto_lower) for padrao in [
            r'\b1t\d{2}\b', r'\b2t\d{2}\b', r'\b3t\d{2}\b', r'\b4t\d{2}\b',
            r'primeiro\s+trimestre', r'segundo\s+trimestre', 
            r'terceiro\s+trimestre', r'quarto\s+trimestre'
        ])
        
        # Se tem trimestre e menciona resultado/desempenho, provavelmente é um release
        if tem_trimestre and any(termo in assunto_lower for termo in ['resultado', 'desempenho', 'earnings']):
            return True
        
        return False
    
    def aguardar_download(self, timeout: int = 30) -> Optional[Path]:
        """
        Aguarda download e retorna o arquivo baixado.
        """
        temp_dir = Path("temp_downloads")
        tempo_inicial = time.time()
        ultimo_pdf = None
        
        while time.time() - tempo_inicial < timeout:
            # Verificar arquivos em download
            arquivos_temp = list(temp_dir.glob("*.crdownload")) + list(temp_dir.glob("*.tmp"))
            
            if not arquivos_temp:
                # Procurar PDFs novos
                pdfs = list(temp_dir.glob("*.pdf"))
                if pdfs:
                    # Pegar o mais recente
                    ultimo_pdf = max(pdfs, key=lambda p: p.stat().st_mtime)
                    return ultimo_pdf
            
            time.sleep(0.5)
        
        return None
    
    def baixar_documento(self, url: str, nome_empresa: str, data: str, assunto: str, categoria: str = '', tipo: str = '') -> Dict:
        """
        Baixa um documento e move para a pasta apropriada.
        """
        # Se apenas releases trimestrais e não é trimestral, pular
        if self.apenas_releases_trimestrais and not self.e_release_trimestral(assunto, categoria, tipo):
            logger.info(f"Pulando (não é ITR/demonstração financeira): {assunto[:50]}...")
            return {'status': 'pulado', 'motivo': 'Não é ITR/demonstração financeira trimestral'}
        
        try:
            logger.info(f"Baixando: {nome_empresa} - {assunto[:50]}...")
            
            # Limpar pasta temporária
            temp_dir = Path("temp_downloads")
            for f in temp_dir.glob("*.pdf"):
                f.unlink()
            
            # Acessar URL
            self.driver.get(url)
            time.sleep(3)
            
            # Aguardar download
            pdf_baixado = self.aguardar_download(timeout=15)
            
            if pdf_baixado and pdf_baixado.exists():
                # Gerar nome final
                data_clean = data.replace('-', '')[:8]
                empresa_clean = re.sub(r'[^\w\s-]', '', nome_empresa)[:30]
                assunto_clean = re.sub(r'[^\w\s-]', '', assunto)[:50]
                nome_arquivo = f"{empresa_clean}_{data_clean}_{assunto_clean}.pdf"
                
                # Determinar pasta destino
                if self.e_release_trimestral(assunto, categoria, tipo):
                    pasta_destino = self.pasta_pending
                    tipo_doc = "trimestral"
                else:
                    pasta_destino = self.pasta_residuals
                    tipo_doc = "outros"
                
                # Mover arquivo
                arquivo_final = pasta_destino / nome_arquivo
                pdf_baixado.rename(arquivo_final)
                
                logger.info(f"Salvo em {tipo_doc}: {arquivo_final.name}")
                
                return {
                    'status': 'sucesso',
                    'arquivo': str(arquivo_final),
                    'tipo': tipo_doc,
                    'tamanho': arquivo_final.stat().st_size
                }
            else:
                # Tentar clique em botões de download
                try:
                    selectors = [
                        "//a[contains(@href, '.pdf')]",
                        "//a[contains(text(), 'Download')]",
                        "//button[contains(text(), 'Download')]",
                    ]
                    
                    for selector in selectors:
                        elementos = self.driver.find_elements(By.XPATH, selector)
                        if elementos:
                            elementos[0].click()
                            time.sleep(3)
                            
                            pdf_baixado = self.aguardar_download(timeout=10)
                            if pdf_baixado:
                                # Processar como acima
                                data_clean = data.replace('-', '')[:8]
                                empresa_clean = re.sub(r'[^\w\s-]', '', nome_empresa)[:30]
                                assunto_clean = re.sub(r'[^\w\s-]', '', assunto)[:50]
                                nome_arquivo = f"{empresa_clean}_{data_clean}_{assunto_clean}.pdf"
                                
                                if self.e_release_trimestral(assunto, categoria, tipo):
                                    pasta_destino = self.pasta_pending
                                    tipo_doc = "trimestral"
                                else:
                                    pasta_destino = self.pasta_residuals
                                    tipo_doc = "outros"
                                
                                arquivo_final = pasta_destino / nome_arquivo
                                pdf_baixado.rename(arquivo_final)
                                
                                return {
                                    'status': 'sucesso',
                                    'arquivo': str(arquivo_final),
                                    'tipo': tipo_doc
                                }
                except:
                    pass
                
                return {'status': 'erro', 'motivo': 'Download não iniciou'}
                
        except Exception as e:
            logger.error(f"[ERRO] Erro: {e}")
            return {'status': 'erro', 'motivo': str(e)}
    
    def extrair_releases_empresa(self, nome_empresa: str, ano: int = 2025) -> List[Dict]:
        """
        Extrai todos os releases de uma empresa do arquivo IPE.
        """
        ipe_file = f"ipe_cia_aberta_{ano}.csv"
        if not Path(ipe_file).exists():
            logger.error(f"Arquivo {ipe_file} não encontrado")
            return []
        
        # Ler arquivo
        df = pd.read_csv(ipe_file, sep=';', encoding='latin-1')
        
        # Filtrar por empresa
        df_empresa = df[df['Nome_Companhia'].str.contains(nome_empresa.upper(), case=False, na=False)]
        
        # Se apenas releases trimestrais, focar em press-releases de resultados
        if self.apenas_releases_trimestrais:
            # Filtrar por categoria e tipo
            if 'Categoria' in df_empresa.columns and 'Tipo' in df_empresa.columns:
                # Priorizar: Dados Econômico-Financeiros + Press-release
                mask_categoria = df_empresa['Categoria'].str.contains('Dados Econômico-Financeiros', case=False, na=False)
                mask_tipo = df_empresa['Tipo'].str.contains('Press-release', case=False, na=False)
                df_press_releases = df_empresa[mask_categoria & mask_tipo]
                
                # Também buscar por palavras-chave de release de resultados
                palavras_release = [
                    'release.*resultado', 'earnings.*release', 'desempenho',
                    'resultado.*trimestral', 'relatório.*desempenho'
                ]
                padrao = '|'.join(palavras_release)
                mask_assunto = df_empresa['Assunto'].str.lower().str.contains(padrao, na=False, regex=True)
                df_releases_assunto = df_empresa[mask_assunto]
                
                # Combinar ambos os filtros
                releases = pd.concat([df_press_releases, df_releases_assunto]).drop_duplicates()
            else:
                # Fallback: buscar apenas por palavras no assunto
                palavras_release = [
                    'release.*resultado', 'earnings.*release', r'desempenho.*\d+t',
                    r'resultado.*\d+t', r'relatório.*desempenho.*\d+t'
                ]
                padrao = '|'.join(palavras_release)
                mask = df_empresa['Assunto'].str.lower().str.contains(padrao, na=False, regex=True)
                releases = df_empresa[mask]
        else:
            # Filtrar releases relevantes em geral
            palavras_release = [
                'resultado', 'trimestre', 'itr', 'dfp', 'release', 'earnings',
                'desempenho', 'demonstrações', 'balanço', 'financeiro'
            ]
            padrao = '|'.join(palavras_release)
            mask = df_empresa['Assunto'].str.lower().str.contains(padrao, na=False, regex=True)
            releases = df_empresa[mask]
        
        # Converter para lista
        releases_list = []
        for _, row in releases.iterrows():
            categoria = row.get('Categoria', '')
            tipo = row.get('Tipo', '')
            
            # Se apenas releases trimestrais, fazer segunda verificação mais rigorosa
            if self.apenas_releases_trimestrais:
                if not self.e_release_trimestral(row['Assunto'], categoria, tipo):
                    continue
            
            releases_list.append({
                'data': row['Data_Entrega'],
                'assunto': row['Assunto'],
                'categoria': categoria,
                'tipo': tipo,
                'url': row['Link_Download'],
                'nome_empresa': row['Nome_Companhia']
            })
        
        return releases_list
    
    def processar_multiplas_empresas(self, empresas: List[str], anos: List[int], 
                                   limite_por_empresa: Optional[int] = None,
                                   headless: bool = True):
        """
        Processa downloads de múltiplas empresas.
        """
        print("\nCVM DOWNLOAD - MÚLTIPLAS EMPRESAS")
        print("=" * 60)
        
        # Iniciar navegador
        self.iniciar_navegador(headless)
        
        # Estatísticas gerais
        total_geral = {
            'releases_trimestrais': 0,
            'outros_documentos': 0,
            'erros': 0,
            'pulados': 0,
            'empresas_processadas': []
        }
        
        # Processar cada empresa
        for empresa in empresas:
            print(f"\nProcessando {empresa}...")
            print("-" * 40)
            
            releases_empresa = []
            for ano in anos:
                releases_ano = self.extrair_releases_empresa(empresa, ano)
                releases_empresa.extend(releases_ano)
            
            # Ordenar por data (mais recente primeiro)
            releases_empresa.sort(key=lambda x: x['data'], reverse=True)
            
            # Aplicar limite se especificado
            if limite_por_empresa:
                releases_empresa = releases_empresa[:limite_por_empresa]
            
            print(f"Encontrados {len(releases_empresa)} releases para {empresa}")
            
            # Processar cada release
            trimestrais = 0
            outros = 0
            erros = 0
            pulados = 0
            
            for i, release in enumerate(releases_empresa, 1):
                print(f"\n[{i}/{len(releases_empresa)}] {release['data'][:10]} - {release['assunto'][:60]}...")
                
                resultado = self.baixar_documento(
                    release['url'],
                    empresa,
                    release['data'],
                    release['assunto'],
                    release.get('categoria', ''),
                    release.get('tipo', '')
                )
                
                if resultado['status'] == 'sucesso':
                    if resultado['tipo'] == 'trimestral':
                        trimestrais += 1
                    else:
                        outros += 1
                elif resultado['status'] == 'pulado':
                    pulados += 1
                else:
                    erros += 1
                
                # Pausa entre downloads
                time.sleep(2)
            
            # Atualizar estatísticas gerais
            total_geral['releases_trimestrais'] += trimestrais
            total_geral['outros_documentos'] += outros
            total_geral['erros'] += erros
            if 'pulados' not in total_geral:
                total_geral['pulados'] = 0
            total_geral['pulados'] += pulados
            
            total_geral['empresas_processadas'].append({
                'empresa': empresa,
                'trimestrais': trimestrais,
                'outros': outros,
                'erros': erros,
                'pulados': pulados,
                'total': len(releases_empresa)
            })
            
            resumo_msg = f"\n{empresa} concluída: {trimestrais} trimestrais"
            if not self.apenas_releases_trimestrais:
                resumo_msg += f", {outros} outros"
            if pulados > 0:
                resumo_msg += f", {pulados} pulados"
            resumo_msg += f", {erros} erros"
            print(resumo_msg)
        
        # Fechar navegador
        self.fechar_navegador()
        
        # Limpar pasta temporária
        temp_dir = Path("temp_downloads")
        if temp_dir.exists():
            for f in temp_dir.glob("*"):
                f.unlink()
        
        # Salvar relatório geral
        relatorio = {
            'data_execucao': datetime.now().isoformat(),
            'empresas_solicitadas': empresas,
            'anos_processados': anos,
            'limite_por_empresa': limite_por_empresa,
            'apenas_releases_trimestrais': self.apenas_releases_trimestrais,
            'resumo_geral': total_geral,
            'pasta_pending': str(self.pasta_pending),
            'pasta_residuals': str(self.pasta_residuals)
        }
        
        relatorio_path = Path(f"relatorio_download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(relatorio_path, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)
        
        # Resumo final
        print(f"\n{'='*60}")
        print("RESUMO FINAL")
        print(f"   Releases Trimestrais (pending): {total_geral['releases_trimestrais']}")
        if not self.apenas_releases_trimestrais:
            print(f"   Outros Documentos (residuals): {total_geral['outros_documentos']}")
        if total_geral.get('pulados', 0) > 0:
            print(f"   Documentos pulados: {total_geral['pulados']}")
        print(f"   Erros: {total_geral['erros']}")
        print(f"   Empresas processadas: {len(empresas)}")
        print(f"   Relatório salvo: {relatorio_path}")
        
        return relatorio


def main():
    """
    Interface para download de múltiplas empresas.
    """
    if not SELENIUM_DISPONIVEL:
        return
    
    # Verificar se foi chamado com modo específico
    modo_config = None
    if Path("temp_config.txt").exists():
        with open("temp_config.txt", "r") as f:
            modo_config = f.read().strip()
    
    print("CVM DOWNLOAD - RELEASES MÚLTIPLAS EMPRESAS")
    print("=" * 60)
    print("\nEste script:")
    print("   Baixa releases de múltiplas empresas automaticamente")
    print("   Separa releases trimestrais em 'documents/pending'")
    print("   Outros documentos vão para 'documents/residuals'")
    print("   Nomeia arquivos: EMPRESA_DATA_ASSUNTO.pdf")
    
    # Configurar empresas
    print("\nCONFIGURAÇÃO:")
    print("\nDigite as empresas separadas por vírgula")
    print("Exemplo: VALE, PETROBRAS, ITAU, AMBEV")
    empresas_input = input("Empresas: ").strip()
    
    if not empresas_input:
        print("[ERRO] Nenhuma empresa informada")
        return
    
    # Processar lista de empresas
    empresas = [e.strip().upper() for e in empresas_input.split(',')]
    print(f"\nEmpresas selecionadas: {', '.join(empresas)}")
    
    # Anos
    anos_input = input("\nAnos (ex: 2023,2024,2025) [2025]: ").strip()
    if anos_input:
        anos = [int(a.strip()) for a in anos_input.split(',')]
    else:
        anos = [2025]
    
    print(f"Anos: {', '.join(map(str, anos))}")
    
    # Limite por empresa
    limite_input = input("\nLimite de releases por empresa (Enter = todos): ").strip()
    limite = int(limite_input) if limite_input.isdigit() else None
    
    # Opção de apenas releases trimestrais
    if modo_config == "modo_apenas_trimestrais":
        apenas_trimestrais = True
        print("\nMODO: Apenas releases trimestrais (Earnings Releases)")
    elif modo_config == "modo_todos_releases":
        apenas_trimestrais = False
        print("\nMODO: Todos os releases")
    else:
        print("\nTIPO DE DOWNLOAD:")
        print("   1. Todos os releases (padrão)")
        print("   2. Apenas releases trimestrais")
        tipo_download = input("Escolha (1 ou 2) [1]: ").strip()
        apenas_trimestrais = tipo_download == '2'
    
    # Modo headless
    headless_input = input("\nExecutar em modo invisível? (S/n): ").strip().lower()
    headless = headless_input != 'n'
    
    # Confirmar
    print(f"\nRESUMO:")
    print(f"   Empresas: {', '.join(empresas)}")
    print(f"   Anos: {', '.join(map(str, anos))}")
    print(f"   Limite por empresa: {limite if limite else 'Todos'}")
    print(f"   Tipo de download: {'Apenas releases trimestrais' if apenas_trimestrais else 'Todos os releases'}")
    print(f"   Modo invisível: {'Sim' if headless else 'Não'}")
    
    confirmar = input("\nIniciar download? (S/n): ").strip().lower()
    if confirmar == 'n':
        print("[ERRO] Operação cancelada")
        return
    
    # Executar
    downloader = CVMReleasesDownloader(apenas_releases_trimestrais=apenas_trimestrais)
    
    try:
        downloader.processar_multiplas_empresas(
            empresas=empresas,
            anos=anos,
            limite_por_empresa=limite,
            headless=headless
        )
    except KeyboardInterrupt:
        print("\n\nDownload interrompido pelo usuário")
        downloader.fechar_navegador()
    except Exception as e:
        print(f"\n[ERRO] Erro: {e}")
        import traceback
        traceback.print_exc()
        downloader.fechar_navegador()


if __name__ == "__main__":
    # Verificar arquivo IPE
    anos_disponiveis = []
    for ano in [2023, 2024, 2025]:
        if Path(f"ipe_cia_aberta_{ano}.csv").exists():
            anos_disponiveis.append(ano)
    
    if not anos_disponiveis:
        print("[ERRO] Nenhum arquivo IPE encontrado!")
        print("   Execute primeiro o script de extração CVM")
    else:
        print(f"Arquivos IPE disponíveis para os anos: {', '.join(map(str, anos_disponiveis))}")
        main()