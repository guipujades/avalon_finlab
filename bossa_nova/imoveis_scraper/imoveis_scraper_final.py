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
import random

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ImoveisScraperFinal:
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
            'parkway': 'PKW',
            'park sul': 'PS',
            'jardim botânico': 'JB',
            'jardim botanico': 'JB',
            'são sebastião': 'SS',
            'sao sebastiao': 'SS',
            'arniqueiras': 'ARN',
            'vila planalto': 'VPL',
            'setor de mansões': 'SM',
            'mansoes': 'SM',
            'smpw': 'PKW',
            'smdb': 'LS'
        }
    
    def get_chrome_driver(self):
        """Configura Chrome driver com opções anti-detecção"""
        options = Options()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Para debug - deixa visível
        # options.add_argument('--headless')
        
        service = Service('./chromedriver.exe')
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def parse_endereco(self, endereco_completo, titulo=''):
        """Parse melhorado do endereço"""
        if not endereco_completo and not titulo:
            return "SEM_ENDERECO"
        
        texto = f"{endereco_completo} {titulo}".lower()
        texto = re.sub(r'[^\w\s-]', ' ', texto)
        texto = ' '.join(texto.split())  # Remove espaços extras
        
        # Identifica o bairro
        bairro_sigla = 'BSB'
        for bairro, sigla in self.siglas_bairros.items():
            if bairro in texto:
                bairro_sigla = sigla
                break
        
        # Padrões específicos
        if bairro_sigla == 'BSB':
            if 'sqs' in texto:
                bairro_sigla = 'ASS'
            elif 'sqn' in texto:
                bairro_sigla = 'ASN'
            elif 'sqsw' in texto:
                bairro_sigla = 'SW'
            elif 'sqnw' in texto:
                bairro_sigla = 'NW'
            elif 'shin' in texto or 'qi ' in texto:
                bairro_sigla = 'LN'
            elif 'shis' in texto or 'ql ' in texto:
                bairro_sigla = 'LS'
            elif 'smpw' in texto:
                bairro_sigla = 'PKW'
        
        # Extrai quadra
        quadra = None
        quadra_match = re.search(r'(?:quadra|qd?|sqs|sqn|sqsw|sqnw|shin|shis|smpw|qi|ql|qms|qnm|conjunto)\s*(\d+)', texto)
        if quadra_match:
            quadra = quadra_match.group(1)
        
        # Extrai bloco
        bloco = None
        bloco_match = re.search(r'(?:bloco|bl?)\s*([a-z0-9]+)', texto)
        if bloco_match:
            bloco = bloco_match.group(1).upper()
        
        # Extrai unidade
        unidade = None
        unidade_match = re.search(r'(?:apartamento|apto?|ap|casa|lote|sala|cobertura)\s*(\d+)', texto)
        if unidade_match:
            unidade = unidade_match.group(1)
        
        # Monta endereço
        partes = [bairro_sigla]
        if quadra:
            partes.append(quadra)
        if bloco:
            partes.append(bloco)
        if unidade:
            partes.append(unidade)
        elif len(partes) == 1:
            # Adiciona hash único se só tem bairro
            partes.append(str(abs(hash(texto)) % 10000))
        
        return '_'.join(partes)
    
    def extract_price(self, text):
        """Extrai preço com validação"""
        if not text:
            return None
        
        # Remove R$ e espaços
        text = text.replace('R$', '').strip()
        
        # Procura padrão brasileiro: 1.234.567,89
        match = re.search(r'([\d.]+)(?:,(\d+))?', text)
        if match:
            inteiro = match.group(1).replace('.', '')
            decimal = match.group(2) if match.group(2) else '00'
            try:
                valor = float(f"{inteiro}.{decimal}")
                # Valida se é um preço razoável (mais de 50 mil)
                if valor > 50000:
                    return valor
            except:
                pass
        
        return None
    
    def scrape_with_javascript(self, max_pages=2):
        """Scraping usando execução de JavaScript para pegar dados diretamente"""
        logging.info("Iniciando scraping com extração via JavaScript...")
        
        today = datetime.now().strftime('%Y-%m-%d')
        daily_data = {'2025-06-24': {}}  # Limpa dados anteriores ruins
        
        driver = self.get_chrome_driver()
        total_capturados = 0
        
        try:
            for page in range(1, max_pages + 1):
                url = f"https://www.imovelweb.com.br/imoveis-venda-brasilia-df-pagina-{page}.html"
                logging.info(f"\n🔍 Acessando página {page}...")
                
                driver.get(url)
                time.sleep(random.uniform(3, 5))
                
                # Scroll para carregar todos os imóveis
                last_height = driver.execute_script("return document.body.scrollHeight")
                while True:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
                
                # Extrai dados via JavaScript
                imoveis_data = driver.execute_script("""
                    const imoveis = [];
                    
                    // Tenta diferentes seletores
                    const cards = document.querySelectorAll('[data-qa="POSTING_CARD"], .postingCard, .CardContainer, [class*="posting-card"], [class*="property-card"]');
                    
                    cards.forEach(card => {
                        try {
                            // Título
                            const tituloElem = card.querySelector('h2, a[data-qa="POSTING_CARD_TITLE"], .postingCardTitle, [class*="title"]');
                            const titulo = tituloElem ? tituloElem.textContent.trim() : '';
                            
                            // Preço
                            const precoElem = card.querySelector('[data-qa="POSTING_CARD_PRICE"], .postingCardPrice, [class*="price"]');
                            const precoTexto = precoElem ? precoElem.textContent.trim() : '';
                            
                            // Endereço
                            const enderecoElem = card.querySelector('[data-qa="POSTING_CARD_LOCATION"], .postingCardLocationTitle, [class*="location"], [class*="address"]');
                            const endereco = enderecoElem ? enderecoElem.textContent.trim() : '';
                            
                            // Features (área, quartos, etc)
                            const featuresElem = card.querySelector('[data-qa="POSTING_CARD_FEATURES"], .postingCardFeatures, [class*="features"]');
                            const featuresText = featuresElem ? featuresElem.textContent : '';
                            
                            // URL
                            const linkElem = card.querySelector('a[href*="/propriedades/"]');
                            const url = linkElem ? linkElem.href : '';
                            
                            // Só adiciona se tem algum dado válido
                            if (titulo || precoTexto || endereco) {
                                imoveis.push({
                                    titulo: titulo,
                                    preco: precoTexto,
                                    endereco: endereco,
                                    features: featuresText,
                                    url: url
                                });
                            }
                        } catch (e) {
                            console.error('Erro ao processar card:', e);
                        }
                    });
                    
                    return imoveis;
                """)
                
                logging.info(f"📊 Encontrados {len(imoveis_data)} imóveis na página {page}")
                
                # Processa cada imóvel
                for idx, imovel in enumerate(imoveis_data[:30]):  # Limita a 30 por página
                    try:
                        # Extrai preço
                        preco = self.extract_price(imovel['preco'])
                        
                        # Extrai features
                        features_text = imovel.get('features', '')
                        area = None
                        quartos = None
                        banheiros = None
                        vagas = None
                        
                        if features_text:
                            # Área
                            area_match = re.search(r'(\d+)\s*m[²2]', features_text)
                            if area_match:
                                area = float(area_match.group(1))
                            
                            # Quartos
                            quartos_match = re.search(r'(\d+)\s*(?:quarto|dorm|suíte)', features_text)
                            if quartos_match:
                                quartos = int(quartos_match.group(1))
                            
                            # Banheiros
                            banheiros_match = re.search(r'(\d+)\s*banheiro', features_text)
                            if banheiros_match:
                                banheiros = int(banheiros_match.group(1))
                            
                            # Vagas
                            vagas_match = re.search(r'(\d+)\s*(?:vaga|garag)', features_text)
                            if vagas_match:
                                vagas = int(vagas_match.group(1))
                        
                        # Parse do endereço
                        endereco_resumido = self.parse_endereco(imovel['endereco'], imovel['titulo'])
                        
                        # Só salva se tem dados relevantes
                        if not imovel['titulo'] and not preco and not imovel['endereco']:
                            continue
                        
                        # Monta dados limpos
                        imovel_data = {
                            'titulo': imovel['titulo'],
                            'preco': preco,
                            'area': area,
                            'quartos': quartos,
                            'banheiros': banheiros,
                            'vagas': vagas,
                            'endereco_completo': imovel['endereco'],
                            'url': imovel['url'],
                            'site': 'ImovelWeb',
                            'data_captura': datetime.now().isoformat()
                        }
                        
                        # Chave única
                        if endereco_resumido in daily_data['2025-06-24']:
                            endereco_resumido = f"{endereco_resumido}_{idx}"
                        
                        daily_data['2025-06-24'][endereco_resumido] = imovel_data
                        total_capturados += 1
                        
                        # Log informativo
                        if preco:
                            logging.info(f"✅ {endereco_resumido}: R$ {preco:,.2f} - {imovel['titulo'][:50]}")
                        elif imovel['titulo']:
                            logging.info(f"✅ {endereco_resumido}: {imovel['titulo'][:50]}")
                    
                    except Exception as e:
                        logging.error(f"Erro ao processar imóvel {idx}: {e}")
                
                # Delay entre páginas
                time.sleep(random.uniform(2, 4))
        
        except Exception as e:
            logging.error(f"Erro durante scraping: {e}")
        
        finally:
            driver.quit()
            
            # Salva apenas se capturou dados válidos
            if total_capturados > 0:
                self.save_daily_data(daily_data, today)
                logging.info(f"\n✅ Total de {total_capturados} imóveis capturados e salvos!")
            else:
                logging.warning("\n⚠️ Nenhum imóvel válido foi capturado")
    
    def save_daily_data(self, data, date_str):
        """Salva dados limpos"""
        filename = os.path.join(self.data_dir, f'imoveis_{date_str}.json')
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def show_clean_summary(self):
        """Mostra resumo dos dados limpos"""
        today = datetime.now().strftime('%Y-%m-%d')
        filename = os.path.join(self.data_dir, f'imoveis_{today}.json')
        
        if not os.path.exists(filename):
            print("\nNenhum dado encontrado para hoje.")
            return
        
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if '2025-06-24' not in data or not data['2025-06-24']:
            print("\nNenhum imóvel válido capturado.")
            return
        
        imoveis = data['2025-06-24']
        total = len(imoveis)
        
        # Filtra apenas imóveis com dados
        imoveis_validos = {k: v for k, v in imoveis.items() 
                          if v.get('titulo') or v.get('preco') or v.get('endereco_completo')}
        
        com_preco = [i for i in imoveis_validos.values() if i.get('preco')]
        com_titulo = [i for i in imoveis_validos.values() if i.get('titulo')]
        com_endereco = [i for i in imoveis_validos.values() if i.get('endereco_completo')]
        
        print(f"\n{'='*70}")
        print(f"📊 RESUMO DOS IMÓVEIS CAPTURADOS - {today}")
        print(f"{'='*70}")
        print(f"Total de imóveis válidos: {len(imoveis_validos)}")
        print(f"Com título: {len(com_titulo)}")
        print(f"Com preço: {len(com_preco)}")
        print(f"Com endereço: {len(com_endereco)}")
        
        if com_preco:
            precos = [i['preco'] for i in com_preco]
            print(f"\n💰 ESTATÍSTICAS DE PREÇO:")
            print(f"  Média: R$ {sum(precos)/len(precos):,.2f}")
            print(f"  Mínimo: R$ {min(precos):,.2f}")
            print(f"  Máximo: R$ {max(precos):,.2f}")
        
        print(f"\n🏠 EXEMPLOS DE IMÓVEIS:")
        exemplos = list(imoveis_validos.items())[:5]
        for key, imovel in exemplos:
            if imovel.get('titulo') or imovel.get('preco') or imovel.get('endereco_completo'):
                print(f"\n📍 {key}:")
                if imovel.get('titulo'):
                    print(f"   Título: {imovel['titulo'][:80]}")
                if imovel.get('preco'):
                    print(f"   Preço: R$ {imovel['preco']:,.2f}")
                if imovel.get('endereco_completo'):
                    print(f"   Endereço: {imovel['endereco_completo'][:80]}")
                if imovel.get('area'):
                    print(f"   Área: {imovel['area']} m²")
                if imovel.get('quartos'):
                    print(f"   Quartos: {imovel['quartos']}")

if __name__ == "__main__":
    print("=== SCRAPER DE IMÓVEIS - VERSÃO FINAL ===")
    print("Extração via JavaScript para dados mais confiáveis\n")
    
    try:
        scraper = ImoveisScraperFinal()
        scraper.scrape_with_javascript(max_pages=2)
        scraper.show_clean_summary()
    except Exception as e:
        print(f"\nErro: {e}")
        import traceback
        traceback.print_exc()