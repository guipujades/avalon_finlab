import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ImoveisScraperJSON:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.data_dir = 'dados_imoveis'
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.siglas_bairros = {
            'asa sul': 'ASS',
            'asa norte': 'ASN',
            'lago sul': 'LS',
            'lago norte': 'LN',
            'sudoeste': 'SW',
            'noroeste': 'NW',
            'aguas claras': 'AC',
            'taguatinga': 'TAG',
            'ceilandia': 'CEI',
            'samambaia': 'SAM',
            'vicente pires': 'VP',
            'guara': 'GUA',
            'sobradinho': 'SOB',
            'planaltina': 'PLA',
            'gama': 'GAM',
            'santa maria': 'SM',
            'recanto das emas': 'RDE',
            'riacho fundo': 'RF',
            'brazlandia': 'BRZ',
            'paranoa': 'PAR',
            'itapoa': 'ITA',
            'sia': 'SIA',
            'saan': 'SAAN',
            'octogonal': 'OCT',
            'cruzeiro': 'CRZ',
            'park way': 'PKW',
            'jardim botanico': 'JB',
            'sao sebastiao': 'SS',
            'arniqueiras': 'ARN'
        }
    
    def get_selenium_driver(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Tenta usar ChromeDriver local primeiro
        try:
            if os.path.exists('./chromedriver'):
                service = Service('./chromedriver')
                return webdriver.Chrome(service=service, options=chrome_options)
            else:
                return webdriver.Chrome(options=chrome_options)
        except Exception as e:
            logging.error(f"Erro ao iniciar ChromeDriver: {e}")
            logging.error("Certifique-se de que o Google Chrome está instalado")
            raise
    
    def parse_endereco(self, endereco_completo):
        """
        Converte endereço completo em formato resumido
        Ex: "SQS 308 Bloco A Apartamento 201" -> "ASS_308_A_201"
        """
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
            # Tenta identificar por padrões conhecidos
            if 'sqs' in endereco_lower or 'sqn' in endereco_lower:
                bairro_sigla = 'ASS' if 'sqs' in endereco_lower else 'ASN'
            elif 'qn' in endereco_lower or 'qi' in endereco_lower:
                # Pode ser Lago Norte, Lago Sul, etc
                if 'lago' in endereco_lower:
                    bairro_sigla = 'LN' if 'norte' in endereco_lower else 'LS'
                else:
                    bairro_sigla = 'BSB'  # Brasília genérico
            else:
                bairro_sigla = 'BSB'
        
        # Extrai números e identificadores
        numeros = re.findall(r'\d+', endereco_completo)
        
        # Identifica quadra
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
        
        # Identifica bloco
        bloco = None
        bloco_match = re.search(r'(?:bloco|bl|b\.?)\s*([a-z0-9]+)', endereco_lower)
        if bloco_match:
            bloco = bloco_match.group(1).upper()
        
        # Identifica apartamento/casa
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
        
        # Monta o endereço resumido
        partes = [bairro_sigla]
        if quadra:
            partes.append(quadra)
        if bloco:
            partes.append(bloco)
        if unidade:
            partes.append(unidade)
        
        return '_'.join(partes)
    
    def extract_number(self, text):
        if not text:
            return None
        clean_text = re.sub(r'[^\d,.]', '', str(text))
        clean_text = clean_text.replace('.', '').replace(',', '.')
        try:
            return float(clean_text)
        except:
            return None
    
    def load_daily_data(self, date_str):
        """Carrega dados do dia ou cria estrutura vazia"""
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
    
    def scrape_zapimoveis(self, max_pages=3):
        logging.info("Iniciando scraping do ZAP Imóveis...")
        base_url = "https://www.zapimoveis.com.br/venda/imoveis/df+brasilia/"
        
        today = datetime.now().strftime('%Y-%m-%d')
        daily_data = self.load_daily_data(today)
        
        driver = self.get_selenium_driver()
        
        try:
            for page in range(1, max_pages + 1):
                url = f"{base_url}?pagina={page}"
                driver.get(url)
                time.sleep(3)
                
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "result-card"))
                    )
                except:
                    logging.warning("Timeout esperando cards de imóveis")
                    continue
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                imoveis = soup.find_all('div', class_='result-card')
                
                for imovel in imoveis:
                    try:
                        link = imovel.find('a', class_='result-card__header')
                        if not link:
                            continue
                        
                        imovel_url = urljoin(base_url, link.get('href', ''))
                        titulo = link.get('title', '').strip()
                        
                        preco_elem = imovel.find('p', class_='simple-card__price')
                        preco = self.extract_number(preco_elem.text if preco_elem else None)
                        
                        area_elem = imovel.find('span', class_='feature__item--area')
                        area = self.extract_number(area_elem.text if area_elem else None)
                        
                        quartos_elem = imovel.find('span', class_='feature__item--bedroom')
                        quartos = self.extract_number(quartos_elem.text if quartos_elem else None)
                        
                        banheiros_elem = imovel.find('span', class_='feature__item--bathroom')
                        banheiros = self.extract_number(banheiros_elem.text if banheiros_elem else None)
                        
                        vagas_elem = imovel.find('span', class_='feature__item--parking')
                        vagas = self.extract_number(vagas_elem.text if vagas_elem else None)
                        
                        endereco_elem = imovel.find('p', class_='simple-card__address')
                        endereco_completo = endereco_elem.text.strip() if endereco_elem else ''
                        
                        # Parse do endereço
                        endereco_resumido = self.parse_endereco(endereco_completo)
                        
                        # Estrutura dos dados
                        imovel_data = {
                            'preco': preco,
                            'area': area,
                            'quartos': int(quartos) if quartos else None,
                            'banheiros': int(banheiros) if banheiros else None,
                            'vagas': int(vagas) if vagas else None,
                            'titulo': titulo,
                            'endereco_completo': endereco_completo,
                            'url': imovel_url,
                            'site': 'ZAP Imóveis',
                            'data_captura': datetime.now().isoformat()
                        }
                        
                        # Salva no formato: data -> endereco -> dados
                        if today not in daily_data:
                            daily_data[today] = {}
                        
                        # Usa URL como identificador único se houver conflito de endereço
                        if endereco_resumido in daily_data[today]:
                            endereco_resumido = f"{endereco_resumido}_{hash(imovel_url) % 1000}"
                        
                        daily_data[today][endereco_resumido] = imovel_data
                        
                        logging.info(f"Imóvel capturado: {endereco_resumido} - R$ {preco:,.2f}" if preco else f"Imóvel capturado: {endereco_resumido}")
                        
                    except Exception as e:
                        logging.error(f"Erro ao processar imóvel: {e}")
                        continue
                
                time.sleep(2)
        
        finally:
            driver.quit()
            self.save_daily_data(daily_data, today)
            logging.info(f"Dados salvos em imoveis_{today}.json")
    
    def scrape_vivareal(self, max_pages=3):
        logging.info("Iniciando scraping do Viva Real...")
        base_url = "https://www.vivareal.com.br/venda/distrito-federal/brasilia/"
        
        today = datetime.now().strftime('%Y-%m-%d')
        daily_data = self.load_daily_data(today)
        
        for page in range(1, max_pages + 1):
            try:
                url = f"{base_url}?pagina={page}"
                response = self.session.get(url)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                imoveis = soup.find_all('article', class_='property-card')
                
                for imovel in imoveis:
                    try:
                        link = imovel.find('a', class_='property-card__content-link')
                        if not link:
                            continue
                        
                        imovel_url = urljoin(base_url, link.get('href', ''))
                        
                        titulo_elem = imovel.find('span', class_='property-card__title')
                        titulo = titulo_elem.text.strip() if titulo_elem else ''
                        
                        preco_elem = imovel.find('div', class_='property-card__price')
                        preco = self.extract_number(preco_elem.text if preco_elem else None)
                        
                        area_elem = imovel.find('span', class_='property-card__detail-area')
                        area = self.extract_number(area_elem.text if area_elem else None)
                        
                        quartos_elem = imovel.find('li', class_='property-card__detail-room')
                        quartos = self.extract_number(quartos_elem.text if quartos_elem else None)
                        
                        banheiros_elem = imovel.find('li', class_='property-card__detail-bathroom')
                        banheiros = self.extract_number(banheiros_elem.text if banheiros_elem else None)
                        
                        vagas_elem = imovel.find('li', class_='property-card__detail-garage')
                        vagas = self.extract_number(vagas_elem.text if vagas_elem else None)
                        
                        endereco_elem = imovel.find('span', class_='property-card__address')
                        endereco_completo = endereco_elem.text.strip() if endereco_elem else ''
                        
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
                            'site': 'Viva Real',
                            'data_captura': datetime.now().isoformat()
                        }
                        
                        if today not in daily_data:
                            daily_data[today] = {}
                        
                        if endereco_resumido in daily_data[today]:
                            endereco_resumido = f"{endereco_resumido}_{hash(imovel_url) % 1000}"
                        
                        daily_data[today][endereco_resumido] = imovel_data
                        
                        logging.info(f"Imóvel Viva Real: {endereco_resumido}")
                        
                    except Exception as e:
                        logging.error(f"Erro ao processar imóvel Viva Real: {e}")
                        continue
                
                time.sleep(2)
                
            except Exception as e:
                logging.error(f"Erro ao acessar página {page} do Viva Real: {e}")
        
        self.save_daily_data(daily_data, today)
    
    def run_daily_scraping(self):
        """Executa scraping diário de todos os sites"""
        logging.info("Iniciando scraping diário...")
        
        # ZAP Imóveis
        try:
            self.scrape_zapimoveis(max_pages=2)
        except Exception as e:
            logging.error(f"Erro no scraping ZAP: {e}")
        
        # Viva Real
        try:
            self.scrape_vivareal(max_pages=2)
        except Exception as e:
            logging.error(f"Erro no scraping Viva Real: {e}")
        
        logging.info("Scraping diário concluído!")
        
        # Mostra resumo
        self.show_daily_summary()
    
    def show_daily_summary(self):
        """Mostra resumo dos dados coletados hoje"""
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
            for bairro, count in sorted(bairros.items(), key=lambda x: x[1], reverse=True):
                print(f"  {bairro}: {count}")

if __name__ == "__main__":
    scraper = ImoveisScraperJSON()
    scraper.run_daily_scraping()