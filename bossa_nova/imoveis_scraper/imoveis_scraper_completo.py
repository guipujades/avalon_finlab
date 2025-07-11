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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import random

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ImoveisScraperCompleto:
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
        """Configura Chrome driver"""
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
        texto = ' '.join(texto.split())
        
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
            partes.append(str(abs(hash(texto)) % 10000))
        
        return '_'.join(partes)
    
    def extract_price(self, text):
        """Extrai preço com validação"""
        if not text:
            return None
        
        text = text.replace('R$', '').strip()
        match = re.search(r'([\d.]+)(?:,(\d+))?', text)
        if match:
            inteiro = match.group(1).replace('.', '')
            decimal = match.group(2) if match.group(2) else '00'
            try:
                valor = float(f"{inteiro}.{decimal}")
                if valor > 50000:  # Filtra preços muito baixos
                    return valor
            except:
                pass
        
        return None
    
    def extract_number(self, text):
        """Extrai número genérico"""
        if not text:
            return None
        numbers = re.findall(r'\d+', str(text))
        return int(numbers[0]) if numbers else None
    
    def get_property_details(self, driver, url):
        """Acessa a página do imóvel e extrai TODOS os detalhes"""
        try:
            logging.info(f"📄 Acessando detalhes: {url}")
            driver.get(url)
            time.sleep(random.uniform(2, 4))
            
            # Espera página carregar
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            details = {}
            
            # 1. INFORMAÇÕES BÁSICAS
            # Título principal
            try:
                titulo_elem = driver.find_element(By.CSS_SELECTOR, 'h1, [class*="title"], [class*="heading"]')
                details['titulo_completo'] = titulo_elem.text.strip()
            except:
                details['titulo_completo'] = None
            
            # Preço
            try:
                preco_elem = driver.find_element(By.CSS_SELECTOR, '[class*="price"], [data-qa*="PRICE"]')
                details['preco'] = self.extract_price(preco_elem.text)
            except:
                details['preco'] = None
            
            # Endereço completo
            try:
                endereco_elem = driver.find_element(By.CSS_SELECTOR, '[class*="location"], [class*="address"], [data-qa*="LOCATION"]')
                details['endereco_completo'] = endereco_elem.text.strip()
            except:
                details['endereco_completo'] = None
            
            # 2. CARACTERÍSTICAS PRINCIPAIS
            caracteristicas = {}
            
            # Área útil e total
            area_selectors = ['[class*="area"]', '[class*="size"]', 'span:contains("m²")', 'span:contains("m2")']
            for selector in area_selectors:
                try:
                    areas = driver.find_elements(By.CSS_SELECTOR, selector)
                    for area in areas:
                        texto = area.text.lower()
                        if 'útil' in texto:
                            caracteristicas['area_util'] = self.extract_number(texto)
                        elif 'total' in texto:
                            caracteristicas['area_total'] = self.extract_number(texto)
                        elif 'm²' in texto or 'm2' in texto:
                            if 'area_util' not in caracteristicas:
                                caracteristicas['area_util'] = self.extract_number(texto)
                except:
                    pass
            
            # Quartos, suítes, banheiros, vagas
            feature_patterns = {
                'quartos': ['quarto', 'dormitório', 'bedroom'],
                'suites': ['suíte', 'suite'],
                'banheiros': ['banheiro', 'bathroom'],
                'vagas': ['vaga', 'garagem', 'parking'],
                'salas': ['sala'],
                'cozinhas': ['cozinha'],
                'lavabos': ['lavabo'],
                'piscinas': ['piscina'],
                'churrasqueiras': ['churrasqueira'],
                'areas_servico': ['área de serviço', 'area de servico']
            }
            
            features_container = driver.find_elements(By.CSS_SELECTOR, '[class*="feature"], [class*="amenity"], [data-qa*="FEATURES"]')
            for container in features_container:
                texto = container.text.lower()
                for feature, patterns in feature_patterns.items():
                    for pattern in patterns:
                        if pattern in texto:
                            numero = self.extract_number(texto)
                            if numero:
                                caracteristicas[feature] = numero
            
            details['caracteristicas_principais'] = caracteristicas
            
            # 3. VALORES ADICIONAIS
            valores = {}
            
            # Condomínio, IPTU, etc
            valor_patterns = {
                'condominio': ['condomínio', 'condominio', 'taxa condominial'],
                'iptu': ['iptu', 'imposto'],
                'preco_m2': ['preço por m²', 'valor do m²', 'r$/m²']
            }
            
            valores_elems = driver.find_elements(By.CSS_SELECTOR, '[class*="fee"], [class*="cost"], [class*="expense"]')
            for elem in valores_elems:
                texto = elem.text.lower()
                for valor_tipo, patterns in valor_patterns.items():
                    for pattern in patterns:
                        if pattern in texto:
                            valores[valor_tipo] = self.extract_price(elem.text)
            
            details['valores_adicionais'] = valores
            
            # 4. DESCRIÇÃO COMPLETA
            try:
                desc_elem = driver.find_element(By.CSS_SELECTOR, '[class*="description"], [data-qa*="DESCRIPTION"]')
                details['descricao_completa'] = desc_elem.text.strip()
            except:
                details['descricao_completa'] = None
            
            # 5. COMODIDADES E CARACTERÍSTICAS
            comodidades = []
            
            # Lista de amenidades
            amenity_selectors = [
                '[class*="amenity"] li',
                '[class*="feature"] li', 
                '[data-qa*="AMENITIES"] li',
                '[class*="characteristics"] li'
            ]
            
            for selector in amenity_selectors:
                try:
                    items = driver.find_elements(By.CSS_SELECTOR, selector)
                    for item in items:
                        texto = item.text.strip()
                        if texto and texto not in comodidades:
                            comodidades.append(texto)
                except:
                    pass
            
            details['comodidades'] = comodidades
            
            # 6. INFORMAÇÕES DO EDIFÍCIO/CONDOMÍNIO
            edificio = {}
            
            # Procura informações sobre o prédio/condomínio
            building_patterns = {
                'andares': ['andares', 'pavimentos'],
                'unidades_por_andar': ['unidades por andar', 'apartamentos por andar'],
                'total_unidades': ['total de unidades', 'unidades'],
                'ano_construcao': ['ano de construção', 'construído em', 'ano:']
            }
            
            all_text = driver.find_element(By.TAG_NAME, 'body').text.lower()
            for info, patterns in building_patterns.items():
                for pattern in patterns:
                    match = re.search(f'{pattern}[:\\s]*(\\d+)', all_text)
                    if match:
                        edificio[info] = int(match.group(1))
            
            details['informacoes_edificio'] = edificio
            
            # 7. LOCALIZAÇÃO E PROXIMIDADES
            localizacao = {}
            
            # Coordenadas (se disponível)
            try:
                map_elem = driver.find_element(By.CSS_SELECTOR, '[class*="map"], [data-lat], [data-lng]')
                lat = map_elem.get_attribute('data-lat')
                lng = map_elem.get_attribute('data-lng')
                if lat and lng:
                    localizacao['coordenadas'] = {
                        'latitude': float(lat),
                        'longitude': float(lng)
                    }
            except:
                pass
            
            # Pontos de interesse próximos
            proximidades = []
            proximity_selectors = ['[class*="nearby"]', '[class*="proximity"]', '[class*="poi"]']
            for selector in proximity_selectors:
                try:
                    items = driver.find_elements(By.CSS_SELECTOR, selector)
                    for item in items:
                        texto = item.text.strip()
                        if texto:
                            proximidades.append(texto)
                except:
                    pass
            
            localizacao['proximidades'] = proximidades
            details['localizacao'] = localizacao
            
            # 8. INFORMAÇÕES DO ANUNCIANTE
            anunciante = {}
            
            try:
                # Nome
                nome_elem = driver.find_element(By.CSS_SELECTOR, '[class*="advertiser"], [class*="seller"], [class*="agent"]')
                anunciante['nome'] = nome_elem.text.strip()
            except:
                pass
            
            try:
                # Tipo (imobiliária, corretor, proprietário)
                tipo_elem = driver.find_element(By.CSS_SELECTOR, '[class*="advertiser-type"], [class*="seller-type"]')
                anunciante['tipo'] = tipo_elem.text.strip()
            except:
                pass
            
            try:
                # CRECI
                creci_match = re.search(r'CRECI[:\s]*([A-Z0-9\-/]+)', driver.page_source)
                if creci_match:
                    anunciante['creci'] = creci_match.group(1)
            except:
                pass
            
            details['anunciante'] = anunciante
            
            # 9. FOTOS
            fotos = []
            foto_selectors = ['img[class*="gallery"]', 'img[class*="photo"]', '[class*="image-container"] img']
            for selector in foto_selectors:
                try:
                    imgs = driver.find_elements(By.CSS_SELECTOR, selector)
                    for img in imgs[:10]:  # Limita a 10 fotos
                        src = img.get_attribute('src')
                        if src and 'placeholder' not in src.lower():
                            fotos.append(src)
                except:
                    pass
            
            details['fotos'] = fotos
            
            # 10. DATA E CÓDIGO DO ANÚNCIO
            try:
                # Código do imóvel
                codigo_match = re.search(r'(?:código|code|id)[:\s]*([A-Z0-9\-]+)', driver.page_source, re.I)
                if codigo_match:
                    details['codigo_imovel'] = codigo_match.group(1)
            except:
                pass
            
            try:
                # Data de publicação
                data_match = re.search(r'(?:publicado|published|atualizado)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', driver.page_source, re.I)
                if data_match:
                    details['data_publicacao'] = data_match.group(1)
            except:
                pass
            
            # 11. TIPO E CATEGORIA DO IMÓVEL
            tipo_patterns = {
                'tipo_imovel': ['apartamento', 'casa', 'cobertura', 'flat', 'kitnet', 'studio', 'loft', 'sobrado', 'terreno', 'sala comercial'],
                'tipo_negocio': ['venda', 'aluguel', 'temporada'],
                'situacao': ['novo', 'usado', 'em construção', 'na planta', 'pronto para morar']
            }
            
            for categoria, patterns in tipo_patterns.items():
                for pattern in patterns:
                    if pattern in all_text:
                        details[categoria] = pattern.capitalize()
                        break
            
            return details
            
        except Exception as e:
            logging.error(f"Erro ao extrair detalhes: {e}")
            return None
    
    def scrape_with_full_details(self, max_pages=1, max_properties_per_page=5):
        """Scraping com captura completa de detalhes"""
        logging.info("🚀 Iniciando scraping COMPLETO com todos os detalhes...")
        
        today = datetime.now().strftime('%Y-%m-%d')
        daily_data = {today: {}}
        
        driver = self.get_chrome_driver()
        total_capturados = 0
        
        try:
            for page in range(1, max_pages + 1):
                url = f"https://www.imovelweb.com.br/imoveis-venda-brasilia-df-pagina-{page}.html"
                logging.info(f"\n📑 Acessando página {page}...")
                
                driver.get(url)
                time.sleep(random.uniform(3, 5))
                
                # Scroll para carregar
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Coleta URLs dos imóveis
                property_links = []
                
                # Tenta múltiplos seletores
                selectors = [
                    'a[href*="/propriedades/"]',
                    'a.go-to-posting',
                    '[data-qa="POSTING_CARD"] a',
                    '.postingCard a',
                    '.posting-card a',
                    'article a[href*="imovelweb"]',
                    'div[class*="card"] a[href*="/propriedades/"]'
                ]
                
                for selector in selectors:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        logging.info(f"Seletor '{selector}' encontrou {len(elements)} elementos")
                        
                        for elem in elements:
                            try:
                                href = elem.get_attribute('href')
                                if href and 'propriedades' in href and href not in property_links:
                                    property_links.append(href)
                                    if len(property_links) >= max_properties_per_page:
                                        break
                            except:
                                continue
                        
                        if property_links:
                            break
                    except Exception as e:
                        logging.debug(f"Erro com seletor {selector}: {e}")
                
                # Se ainda não encontrou, tenta método alternativo
                if not property_links:
                    logging.info("Tentando método alternativo para encontrar links...")
                    all_links = driver.find_elements(By.TAG_NAME, 'a')
                    logging.info(f"Total de links na página: {len(all_links)}")
                    
                    for link in all_links:
                        try:
                            href = link.get_attribute('href')
                            if href and 'propriedades' in href and 'imovelweb.com.br' in href:
                                property_links.append(href)
                                logging.info(f"Link encontrado: {href[:80]}...")
                                if len(property_links) >= max_properties_per_page:
                                    break
                        except:
                            continue
                
                logging.info(f"📌 Encontrados {len(property_links)} imóveis para análise detalhada")
                
                # Visita cada imóvel
                for idx, property_url in enumerate(property_links):
                    try:
                        # Extrai detalhes completos
                        details = self.get_property_details(driver, property_url)
                        
                        if details:
                            # Parse do endereço
                            endereco_resumido = self.parse_endereco(
                                details.get('endereco_completo', ''),
                                details.get('titulo_completo', '')
                            )
                            
                            # Adiciona metadados
                            details['url'] = property_url
                            details['site'] = 'ImovelWeb'
                            details['data_captura'] = datetime.now().isoformat()
                            details['endereco_resumido'] = endereco_resumido
                            
                            # Salva no JSON
                            chave = f"{endereco_resumido}_{idx}"
                            daily_data[today][chave] = details
                            total_capturados += 1
                            
                            logging.info(f"✅ Capturado com sucesso: {endereco_resumido}")
                            
                            # Mostra preview dos dados
                            if details.get('preco'):
                                logging.info(f"   💰 Preço: R$ {details['preco']:,.2f}")
                            if details.get('caracteristicas_principais'):
                                logging.info(f"   🏠 Características: {details['caracteristicas_principais']}")
                            if details.get('comodidades'):
                                logging.info(f"   ✨ {len(details['comodidades'])} comodidades")
                        
                        # Delay entre imóveis
                        time.sleep(random.uniform(2, 4))
                        
                    except Exception as e:
                        logging.error(f"❌ Erro ao processar {property_url}: {e}")
                        continue
                
                # Salva progresso após cada página
                self.save_daily_data(daily_data, today)
                logging.info(f"💾 Progresso salvo: {total_capturados} imóveis")
        
        except Exception as e:
            logging.error(f"Erro durante scraping: {e}")
        
        finally:
            driver.quit()
            
            if total_capturados > 0:
                self.save_daily_data(daily_data, today)
                logging.info(f"\n✅ Scraping completo! {total_capturados} imóveis capturados com detalhes completos!")
                self.show_detailed_summary(today)
            else:
                logging.warning("\n⚠️ Nenhum imóvel foi capturado")
    
    def save_daily_data(self, data, date_str):
        """Salva dados completos"""
        filename = os.path.join(self.data_dir, f'imoveis_completos_{date_str}.json')
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def show_detailed_summary(self, date_str):
        """Mostra resumo dos dados completos capturados"""
        filename = os.path.join(self.data_dir, f'imoveis_completos_{date_str}.json')
        
        if not os.path.exists(filename):
            return
        
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if date_str not in data:
            return
        
        imoveis = data[date_str]
        total = len(imoveis)
        
        print(f"\n{'='*70}")
        print(f"📊 RESUMO DOS IMÓVEIS CAPTURADOS COM DETALHES COMPLETOS")
        print(f"{'='*70}")
        print(f"Data: {date_str}")
        print(f"Total de imóveis: {total}")
        
        # Estatísticas de completude
        com_preco = sum(1 for i in imoveis.values() if i.get('preco'))
        com_area = sum(1 for i in imoveis.values() if i.get('caracteristicas_principais', {}).get('area_util'))
        com_descricao = sum(1 for i in imoveis.values() if i.get('descricao_completa'))
        com_comodidades = sum(1 for i in imoveis.values() if i.get('comodidades'))
        com_fotos = sum(1 for i in imoveis.values() if i.get('fotos'))
        
        print(f"\n📈 COMPLETUDE DOS DADOS:")
        print(f"  Com preço: {com_preco} ({com_preco/total*100:.1f}%)")
        print(f"  Com área: {com_area} ({com_area/total*100:.1f}%)")
        print(f"  Com descrição: {com_descricao} ({com_descricao/total*100:.1f}%)")
        print(f"  Com lista de comodidades: {com_comodidades} ({com_comodidades/total*100:.1f}%)")
        print(f"  Com fotos: {com_fotos} ({com_fotos/total*100:.1f}%)")
        
        # Exemplo de imóvel completo
        print(f"\n🏠 EXEMPLO DE IMÓVEL COM DADOS COMPLETOS:")
        for key, imovel in list(imoveis.items())[:1]:
            print(f"\n{key}:")
            print(f"  Título: {imovel.get('titulo_completo', 'N/A')}")
            print(f"  Preço: R$ {imovel.get('preco', 0):,.2f}")
            print(f"  Endereço: {imovel.get('endereco_completo', 'N/A')}")
            
            if imovel.get('caracteristicas_principais'):
                print(f"  Características principais:")
                for k, v in imovel['caracteristicas_principais'].items():
                    print(f"    - {k}: {v}")
            
            if imovel.get('valores_adicionais'):
                print(f"  Valores adicionais:")
                for k, v in imovel['valores_adicionais'].items():
                    print(f"    - {k}: R$ {v:,.2f}")
            
            if imovel.get('comodidades'):
                print(f"  Comodidades ({len(imovel['comodidades'])}):")
                for com in imovel['comodidades'][:5]:
                    print(f"    - {com}")
                if len(imovel['comodidades']) > 5:
                    print(f"    ... e mais {len(imovel['comodidades'])-5} comodidades")
            
            if imovel.get('descricao_completa'):
                print(f"  Descrição: {imovel['descricao_completa'][:200]}...")

if __name__ == "__main__":
    print("=== SCRAPER DE IMÓVEIS - CAPTURA COMPLETA DE DETALHES ===")
    print("Este scraper captura TODOS os detalhes disponíveis de cada imóvel\n")
    
    try:
        scraper = ImoveisScraperCompleto()
        # Limita para teste: 1 página, 5 imóveis por página
        scraper.scrape_with_full_details(max_pages=1, max_properties_per_page=5)
    except Exception as e:
        print(f"\nErro: {e}")
        import traceback
        traceback.print_exc()