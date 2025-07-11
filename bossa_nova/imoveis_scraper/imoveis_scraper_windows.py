import os
import json
import time
import re
from datetime import datetime
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ImoveisScraperWindows:
    def __init__(self):
        self.data_dir = 'dados_imoveis'
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.siglas_bairros = {
            'asa sul': 'ASS',
            'asa norte': 'ASN',
            'lago sul': 'LS',
            'lago norte': 'LN',
            'sudoeste': 'SW',
            'noroeste': 'NW',
            'águas claras': 'AC',
            'aguas claras': 'AC',
            'taguatinga': 'TAG',
            'ceilândia': 'CEI',
            'ceilandia': 'CEI',
            'samambaia': 'SAM',
            'vicente pires': 'VP',
            'guará': 'GUA',
            'guara': 'GUA',
            'sobradinho': 'SOB',
            'planaltina': 'PLA',
            'gama': 'GAM',
            'santa maria': 'SM',
            'recanto das emas': 'RDE',
            'riacho fundo': 'RF',
            'brazlândia': 'BRZ',
            'brazlandia': 'BRZ',
            'paranoá': 'PAR',
            'paranoa': 'PAR',
            'itapoã': 'ITA',
            'itapoa': 'ITA',
            'octogonal': 'OCT',
            'cruzeiro': 'CRZ',
            'park way': 'PKW',
            'jardim botânico': 'JB',
            'jardim botanico': 'JB',
            'são sebastião': 'SS',
            'sao sebastiao': 'SS',
            'arniqueiras': 'ARN'
        }
    
    def get_chrome_driver(self):
        """Configura Chrome driver para Windows"""
        options = Options()
        
        # Opções para evitar detecção
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # User agent real
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Modo headless opcional (comente para ver o navegador)
        # options.add_argument('--headless')
        
        # Tenta diferentes caminhos para o ChromeDriver
        chromedriver_paths = [
            r".\chromedriver.exe",  # Diretório atual
            r"C:\chromedriver\chromedriver.exe",  # Caminho comum
            r"C:\Program Files\Google\Chrome\Application\chromedriver.exe",
            os.path.join(os.environ.get('USERPROFILE', ''), 'Downloads', 'chromedriver.exe')
        ]
        
        driver = None
        for path in chromedriver_paths:
            if os.path.exists(path):
                try:
                    service = Service(path)
                    driver = webdriver.Chrome(service=service, options=options)
                    logging.info(f"ChromeDriver encontrado em: {path}")
                    break
                except Exception as e:
                    logging.error(f"Erro com ChromeDriver em {path}: {e}")
        
        if not driver:
            # Tenta sem especificar caminho (se estiver no PATH)
            try:
                driver = webdriver.Chrome(options=options)
                logging.info("ChromeDriver encontrado no PATH do sistema")
            except Exception as e:
                logging.error("ChromeDriver não encontrado. Baixe de: https://chromedriver.chromium.org/")
                raise
        
        # Scripts para evitar detecção
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def parse_endereco(self, endereco_completo):
        """Converte endereço completo em formato resumido"""
        if not endereco_completo:
            return "SEM_ENDERECO"
        
        endereco_lower = endereco_completo.lower()
        
        # Identifica o bairro
        bairro_sigla = None
        for bairro, sigla in self.siglas_bairros.items():
            if bairro in endereco_lower:
                bairro_sigla = sigla
                break
        
        if not bairro_sigla:
            if 'sqs' in endereco_lower or 'sqn' in endereco_lower:
                bairro_sigla = 'ASS' if 'sqs' in endereco_lower else 'ASN'
            elif 'qn' in endereco_lower or 'qi' in endereco_lower:
                if 'lago' in endereco_lower:
                    bairro_sigla = 'LN' if 'norte' in endereco_lower else 'LS'
                else:
                    bairro_sigla = 'BSB'
            else:
                bairro_sigla = 'BSB'
        
        # Extrai números
        numeros = re.findall(r'\d+', endereco_completo)
        
        # Quadra
        quadra = None
        quadra_patterns = [
            r'(?:quadra|qd|q\.?)\s*(\d+)',
            r'(?:sqs|sqn|qi|qn)\s*(\d+)',
            r'(?:rua|r\.?)\s*(\d+)'
        ]
        
        for pattern in quadra_patterns:
            match = re.search(pattern, endereco_lower)
            if match:
                quadra = match.group(1)
                break
        
        if not quadra and numeros:
            quadra = numeros[0]
        
        # Bloco
        bloco = None
        bloco_match = re.search(r'(?:bloco|bl|b\.?)\s*([a-z0-9]+)', endereco_lower)
        if bloco_match:
            bloco = bloco_match.group(1).upper()
        
        # Unidade
        unidade = None
        unidade_patterns = [
            r'(?:apartamento|apto|ap\.?)\s*(\d+)',
            r'(?:casa|cs)\s*(\d+)',
            r'(?:lote|lt)\s*(\d+)'
        ]
        
        for pattern in unidade_patterns:
            match = re.search(pattern, endereco_lower)
            if match:
                unidade = match.group(1)
                break
        
        # Monta endereço resumido
        partes = [bairro_sigla]
        if quadra:
            partes.append(quadra)
        if bloco:
            partes.append(bloco)
        if unidade:
            partes.append(unidade)
        
        return '_'.join(partes)
    
    def extract_number(self, text):
        """Extrai número do texto"""
        if not text:
            return None
        
        # Remove caracteres não numéricos
        clean_text = re.sub(r'[^\d,.]', '', str(text))
        
        # Converte formato brasileiro
        if '.' in clean_text and ',' in clean_text:
            clean_text = clean_text.replace('.', '').replace(',', '.')
        elif ',' in clean_text:
            clean_text = clean_text.replace(',', '.')
        
        try:
            return float(clean_text)
        except:
            return None
    
    def load_daily_data(self, date_str):
        """Carrega dados do dia"""
        filename = os.path.join(self.data_dir, f'imoveis_{date_str}.json')
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_daily_data(self, data, date_str):
        """Salva dados do dia"""
        filename = os.path.join(self.data_dir, f'imoveis_{date_str}.json')
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def scrape_imovelweb(self, max_pages=2):
        """Scraping do ImovelWeb"""
        logging.info("Iniciando scraping do ImovelWeb...")
        
        today = datetime.now().strftime('%Y-%m-%d')
        daily_data = self.load_daily_data(today)
        
        if today not in daily_data:
            daily_data[today] = {}
        
        driver = self.get_chrome_driver()
        
        try:
            for page in range(1, max_pages + 1):
                url = f"https://www.imovelweb.com.br/imoveis-venda-brasilia-df-pagina-{page}.html"
                logging.info(f"Acessando: {url}")
                
                driver.get(url)
                time.sleep(5)  # Aguarda carregamento
                
                # Scroll para carregar mais conteúdo
                for _ in range(3):
                    driver.execute_script("window.scrollBy(0, 500);")
                    time.sleep(1)
                
                # Espera elementos carregarem
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "postings-container"))
                    )
                except:
                    logging.warning("Timeout esperando conteúdo carregar")
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # Busca cards de imóveis - ImovelWeb usa estrutura diferente
                imoveis = soup.find_all(['div', 'article'], attrs={'data-qa': 'posting'})
                if not imoveis:
                    imoveis = soup.find_all('div', class_=re.compile('posting-card|property-card|CardContainer'))
                
                logging.info(f"Encontrados {len(imoveis)} imóveis na página {page}")
                
                for imovel in imoveis:
                    try:
                        # Título
                        titulo_elem = imovel.find(['h2', 'a'], class_=re.compile('card__title|posting-title'))
                        titulo = titulo_elem.text.strip() if titulo_elem else ''
                        
                        # Preço
                        preco_elem = imovel.find(['div', 'span'], class_=re.compile('price|card__price'))
                        preco = self.extract_number(preco_elem.text if preco_elem else None)
                        
                        # Endereço
                        endereco_elem = imovel.find(['div', 'span'], class_=re.compile('card__address|posting-location'))
                        endereco_completo = endereco_elem.text.strip() if endereco_elem else ''
                        
                        # Características
                        area = None
                        quartos = None
                        banheiros = None
                        vagas = None
                        
                        # Busca características
                        features = imovel.find_all(['span', 'li'], class_=re.compile('card__main-features|posting-features'))
                        for feature in features:
                            text = feature.text.lower()
                            if 'm²' in text or 'm2' in text:
                                area = self.extract_number(text)
                            elif 'quarto' in text or 'dorm' in text:
                                quartos = self.extract_number(text)
                            elif 'banheiro' in text:
                                banheiros = self.extract_number(text)
                            elif 'vaga' in text or 'garagem' in text:
                                vagas = self.extract_number(text)
                        
                        # URL
                        link_elem = imovel.find('a', href=True)
                        url_imovel = f"https://www.imovelweb.com.br{link_elem['href']}" if link_elem else ''
                        
                        endereco_resumido = self.parse_endereco(endereco_completo)
                        
                        imovel_data = {
                            'preco': preco,
                            'area': area,
                            'quartos': int(quartos) if quartos else None,
                            'banheiros': int(banheiros) if banheiros else None,
                            'vagas': int(vagas) if vagas else None,
                            'titulo': titulo,
                            'endereco_completo': endereco_completo,
                            'url': url_imovel,
                            'site': 'ImovelWeb',
                            'data_captura': datetime.now().isoformat()
                        }
                        
                        # Evita duplicatas
                        if endereco_resumido in daily_data[today]:
                            endereco_resumido = f"{endereco_resumido}_{hash(url_imovel) % 1000}"
                        
                        daily_data[today][endereco_resumido] = imovel_data
                        
                        if preco:
                            logging.info(f"Capturado: {endereco_resumido} - R$ {preco:,.2f}")
                    
                    except Exception as e:
                        logging.error(f"Erro ao processar imóvel: {e}")
                        continue
                
                time.sleep(3)  # Delay entre páginas
        
        except Exception as e:
            logging.error(f"Erro geral no scraping: {e}")
        
        finally:
            driver.quit()
            self.save_daily_data(daily_data, today)
            logging.info(f"Dados salvos em dados_imoveis/imoveis_{today}.json")
    
    def show_daily_summary(self):
        """Mostra resumo dos dados coletados"""
        today = datetime.now().strftime('%Y-%m-%d')
        daily_data = self.load_daily_data(today)
        
        if today in daily_data and daily_data[today]:
            total = len(daily_data[today])
            precos = [item['preco'] for item in daily_data[today].values() if item.get('preco')]
            
            print(f"\n=== RESUMO DO DIA {today} ===")
            print(f"Total de imóveis capturados: {total}")
            
            if precos:
                print(f"\nEstatísticas de preço:")
                print(f"  Média: R$ {sum(precos)/len(precos):,.2f}")
                print(f"  Mínimo: R$ {min(precos):,.2f}")
                print(f"  Máximo: R$ {max(precos):,.2f}")
            
            # Contagem por bairro
            bairros = {}
            for endereco in daily_data[today].keys():
                sigla = endereco.split('_')[0]
                bairros[sigla] = bairros.get(sigla, 0) + 1
            
            print("\nImóveis por região:")
            for bairro, count in sorted(bairros.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {bairro}: {count}")
        else:
            print(f"\nNenhum dado capturado para {today}")

if __name__ == "__main__":
    print("=== SCRAPER DE IMÓVEIS WINDOWS ===")
    print("\nCertifique-se de que:")
    print("1. O Google Chrome está instalado")
    print("2. O ChromeDriver está baixado e no diretório atual ou no PATH")
    print("   Download: https://chromedriver.chromium.org/")
    print("\nIniciando em 3 segundos...\n")
    
    time.sleep(3)
    
    try:
        scraper = ImoveisScraperWindows()
        scraper.scrape_imovelweb(max_pages=2)
        scraper.show_daily_summary()
    except Exception as e:
        print(f"\nErro: {e}")
        print("\nDicas:")
        print("1. Baixe o ChromeDriver da mesma versão do seu Chrome")
        print("2. Coloque o chromedriver.exe na mesma pasta deste script")
        print("3. Ou adicione o caminho do ChromeDriver ao PATH do Windows")