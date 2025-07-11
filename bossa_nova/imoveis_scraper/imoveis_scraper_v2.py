import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import time
import re
import random
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ImoveisScraperV2:
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
            'arniqueiras': 'ARN',
            'sol nascente': 'SN',
            'pôr do sol': 'PS',
            'por do sol': 'PS'
        }
    
    def get_driver(self):
        """Cria driver usando undetected-chromedriver para evitar detecção"""
        options = uc.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        driver = uc.Chrome(options=options, version_main=120)
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
        
        # Extrai componentes do endereço
        numeros = re.findall(r'\d+', endereco_completo)
        
        # Quadra
        quadra = None
        quadra_patterns = [
            r'(?:quadra|qd|q\.?)\s*(\d+)',
            r'(?:sqs|sqn|qi|qn)\s*(\d+)',
            r'(?:rua|r\.?)\s*(\d+)',
            r'(?:qms|qnm)\s*(\d+)'
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
            r'(?:lote|lt)\s*(\d+)',
            r'(?:sala)\s*(\d+)'
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
        """Extrai número de string com formato brasileiro"""
        if not text:
            return None
        
        # Remove tudo exceto números, vírgula e ponto
        clean_text = re.sub(r'[^\d,.]', '', str(text))
        
        # Converte formato brasileiro para float
        if ',' in clean_text and '.' in clean_text:
            # Formato: 1.234.567,89
            clean_text = clean_text.replace('.', '').replace(',', '.')
        elif ',' in clean_text:
            # Formato: 1234,56
            clean_text = clean_text.replace(',', '.')
        
        try:
            return float(clean_text)
        except:
            return None
    
    def random_delay(self, min_seconds=1, max_seconds=3):
        """Delay aleatório para parecer humano"""
        time.sleep(random.uniform(min_seconds, max_seconds))
    
    def scroll_slowly(self, driver, pixels=300):
        """Scroll suave para parecer humano"""
        driver.execute_script(f"window.scrollBy(0, {pixels});")
        self.random_delay(0.5, 1)
    
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
        """Scraper para ImovelWeb - mais fácil de acessar"""
        logging.info("Iniciando scraping do ImovelWeb...")
        
        today = datetime.now().strftime('%Y-%m-%d')
        daily_data = self.load_daily_data(today)
        
        if today not in daily_data:
            daily_data[today] = {}
        
        driver = self.get_driver()
        
        try:
            for page in range(1, max_pages + 1):
                url = f"https://www.imovelweb.com.br/imoveis-venda-brasilia-df-pagina-{page}.html"
                logging.info(f"Acessando página {page}...")
                
                driver.get(url)
                self.random_delay(3, 5)
                
                # Espera carregar
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "posting-card"))
                    )
                except:
                    logging.warning(f"Timeout na página {page}")
                    continue
                
                # Scroll para carregar todos os imóveis
                for _ in range(5):
                    self.scroll_slowly(driver)
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # Busca cards de imóveis
                imoveis = soup.find_all('div', class_='posting-card')
                
                logging.info(f"Encontrados {len(imoveis)} imóveis na página {page}")
                
                for imovel in imoveis:
                    try:
                        # URL
                        link_elem = imovel.find('a', class_='go-to-posting')
                        if not link_elem:
                            continue
                        
                        imovel_url = "https://www.imovelweb.com.br" + link_elem.get('href', '')
                        
                        # Preço
                        preco_elem = imovel.find('div', class_='first-price')
                        if not preco_elem:
                            preco_elem = imovel.find('span', class_='first-price')
                        preco = self.extract_number(preco_elem.text if preco_elem else None)
                        
                        # Título
                        titulo_elem = imovel.find('h2', class_='posting-title')
                        titulo = titulo_elem.text.strip() if titulo_elem else ''
                        
                        # Endereço
                        endereco_elem = imovel.find('div', class_='posting-location')
                        endereco_completo = endereco_elem.text.strip() if endereco_elem else ''
                        
                        # Features (área, quartos, etc)
                        features = imovel.find_all('li', class_='posting-features__item')
                        
                        area = None
                        quartos = None
                        banheiros = None
                        vagas = None
                        
                        for feature in features:
                            text = feature.text.lower()
                            if 'm²' in text:
                                area = self.extract_number(text)
                            elif 'quarto' in text or 'dormitório' in text:
                                quartos = self.extract_number(text)
                            elif 'banheiro' in text:
                                banheiros = self.extract_number(text)
                            elif 'vaga' in text or 'garagem' in text:
                                vagas = self.extract_number(text)
                        
                        endereco_resumido = self.parse_endereco(endereco_completo)
                        
                        imovel_data = {
                            'preco': preco,
                            'area': area,
                            'quartos': int(quartos) if quartos else None,
                            'banheiros': int(banheiros) if banheiros else None,
                            'vagas': int(vagas) if vagas else None,
                            'titulo': titulo,
                            'endereco_completo': endereco_completo,
                            'url': imovel_url,
                            'site': 'ImovelWeb',
                            'data_captura': datetime.now().isoformat()
                        }
                        
                        # Evita duplicatas
                        if endereco_resumido in daily_data[today]:
                            endereco_resumido = f"{endereco_resumido}_{hash(imovel_url) % 1000}"
                        
                        daily_data[today][endereco_resumido] = imovel_data
                        
                        if preco:
                            logging.info(f"Capturado: {endereco_resumido} - R$ {preco:,.2f}")
                        else:
                            logging.info(f"Capturado: {endereco_resumido} - Preço sob consulta")
                    
                    except Exception as e:
                        logging.error(f"Erro ao processar imóvel: {e}")
                        continue
                
                self.random_delay(2, 4)
        
        finally:
            driver.quit()
            self.save_daily_data(daily_data, today)
            logging.info(f"Dados salvos em imoveis_{today}.json")
    
    def run_daily_scraping(self):
        """Executa scraping diário"""
        logging.info("Iniciando scraping diário...")
        
        try:
            self.scrape_imovelweb(max_pages=3)
        except Exception as e:
            logging.error(f"Erro no scraping: {e}")
        
        self.show_daily_summary()
    
    def show_daily_summary(self):
        """Mostra resumo dos dados coletados"""
        today = datetime.now().strftime('%Y-%m-%d')
        daily_data = self.load_daily_data(today)
        
        if today in daily_data:
            total = len(daily_data[today])
            precos = [item['preco'] for item in daily_data[today].values() if item.get('preco')]
            
            print(f"\n=== RESUMO DO DIA {today} ===")
            print(f"Total de imóveis capturados: {total}")
            
            if precos:
                print(f"Preço médio: R$ {sum(precos)/len(precos):,.2f}")
                print(f"Preço mínimo: R$ {min(precos):,.2f}")
                print(f"Preço máximo: R$ {max(precos):,.2f}")
            
            # Contagem por bairro
            bairros = {}
            for endereco in daily_data[today].keys():
                sigla = endereco.split('_')[0]
                bairros[sigla] = bairros.get(sigla, 0) + 1
            
            print("\nImóveis por região:")
            for bairro, count in sorted(bairros.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {bairro}: {count}")

if __name__ == "__main__":
    # Primeiro instale: pip install undetected-chromedriver
    scraper = ImoveisScraperV2()
    scraper.run_daily_scraping()