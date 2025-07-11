import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import time
import re
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class OLXScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0'
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
    
    def parse_endereco(self, endereco_completo, titulo=''):
        """Parse do endereço usando informações do título também"""
        if not endereco_completo and not titulo:
            return "SEM_ENDERECO"
        
        # Combina endereço e título para melhor extração
        texto_completo = f"{endereco_completo} {titulo}".lower()
        
        # Identifica o bairro
        bairro_sigla = None
        for bairro, sigla in self.siglas_bairros.items():
            if bairro in texto_completo:
                bairro_sigla = sigla
                break
        
        if not bairro_sigla:
            # Tenta identificar por padrões
            if 'sqs' in texto_completo or 'sqn' in texto_completo:
                bairro_sigla = 'ASS' if 'sqs' in texto_completo else 'ASN'
            elif 'qn' in texto_completo or 'qi' in texto_completo:
                if 'lago' in texto_completo:
                    bairro_sigla = 'LN' if 'norte' in texto_completo else 'LS'
                else:
                    bairro_sigla = 'BSB'
            else:
                bairro_sigla = 'BSB'
        
        # Extrai números
        numeros = re.findall(r'\d+', endereco_completo + ' ' + titulo)
        
        # Identifica quadra
        quadra = None
        quadra_patterns = [
            r'(?:quadra|qd|q\.?)\s*(\d+)',
            r'(?:sqs|sqn|qi|qn)\s*(\d+)',
            r'(?:qms|qnm)\s*(\d+)',
            r'(?:conjunto|conj\.?)\s*(\d+)'
        ]
        
        for pattern in quadra_patterns:
            match = re.search(pattern, texto_completo)
            if match:
                quadra = match.group(1)
                break
        
        if not quadra and numeros:
            quadra = numeros[0]
        
        # Monta endereço básico
        partes = [bairro_sigla]
        if quadra:
            partes.append(quadra)
        
        # Adiciona hash único baseado no título para evitar colisões
        if len(partes) == 1:
            partes.append(str(abs(hash(titulo)) % 10000))
        
        return '_'.join(partes)
    
    def extract_number(self, text):
        """Extrai número do texto"""
        if not text:
            return None
        
        # Remove caracteres não numéricos exceto vírgula e ponto
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
    
    def extract_features_from_title(self, titulo):
        """Extrai características do título do anúncio"""
        titulo_lower = titulo.lower()
        
        # Quartos
        quartos = None
        quartos_match = re.search(r'(\d+)\s*(?:quartos?|qts?|dormitórios?)', titulo_lower)
        if quartos_match:
            quartos = int(quartos_match.group(1))
        
        # Área
        area = None
        area_match = re.search(r'(\d+)\s*m[²2]', titulo_lower)
        if area_match:
            area = float(area_match.group(1))
        
        # Vagas
        vagas = None
        vagas_match = re.search(r'(\d+)\s*(?:vagas?|garagens?)', titulo_lower)
        if vagas_match:
            vagas = int(vagas_match.group(1))
        
        # Tipo de imóvel
        tipo = 'Apartamento'
        if 'casa' in titulo_lower:
            tipo = 'Casa'
        elif 'kitnet' in titulo_lower or 'studio' in titulo_lower:
            tipo = 'Kitnet/Studio'
        elif 'cobertura' in titulo_lower:
            tipo = 'Cobertura'
        elif 'terreno' in titulo_lower or 'lote' in titulo_lower:
            tipo = 'Terreno'
        
        return {
            'quartos': quartos,
            'area': area,
            'vagas': vagas,
            'tipo': tipo
        }
    
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
    
    def scrape_olx(self, max_pages=3):
        """Scraping da OLX - geralmente tem menos proteção"""
        logging.info("Iniciando scraping da OLX...")
        
        today = datetime.now().strftime('%Y-%m-%d')
        daily_data = self.load_daily_data(today)
        
        if today not in daily_data:
            daily_data[today] = {}
        
        # URLs de teste para diferentes categorias
        urls = [
            "https://df.olx.com.br/distrito-federal-e-regiao/imoveis/venda",
            "https://df.olx.com.br/distrito-federal-e-regiao/imoveis/venda/apartamentos",
            "https://df.olx.com.br/distrito-federal-e-regiao/imoveis/venda/casas"
        ]
        
        total_capturados = 0
        
        for base_url in urls[:1]:  # Começa com apenas uma categoria
            logging.info(f"Tentando URL: {base_url}")
            
            for page in range(1, max_pages + 1):
                try:
                    url = f"{base_url}?o={page}"
                    
                    logging.info(f"Acessando página {page}...")
                    response = self.session.get(url, timeout=10)
                    
                    if response.status_code != 200:
                        logging.warning(f"Status code: {response.status_code}")
                        continue
                    
                    # Verifica se tem Cloudflare
                    if 'cloudflare' in response.text.lower() or 'cf-browser-verification' in response.text:
                        logging.error("Cloudflare detectado na OLX")
                        break
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Diferentes seletores para OLX
                    imoveis = []
                    
                    # Tenta diferentes estruturas
                    selectors = [
                        'div[data-testid="ad-card"]',
                        'li[data-aut-id="itemBox"]',
                        'div.sc-12rk7z2-0',
                        'a[data-lurker-detail="list_id"]',
                        'div[class*="adList"]',
                        'ul[id="ad-list"] li'
                    ]
                    
                    for selector in selectors:
                        if selector.startswith('div[') or selector.startswith('li['):
                            imoveis = soup.select(selector)
                        else:
                            imoveis = soup.find_all(selector.split('[')[0], class_=selector.split('.')[-1] if '.' in selector else None)
                        
                        if imoveis:
                            logging.info(f"Encontrados {len(imoveis)} imóveis com seletor: {selector}")
                            break
                    
                    if not imoveis:
                        # Tenta abordagem genérica
                        imoveis = soup.find_all('a', href=re.compile(r'/.*-\d+$'))
                        logging.info(f"Tentativa genérica: {len(imoveis)} links encontrados")
                    
                    for imovel in imoveis[:10]:  # Limita para teste
                        try:
                            # Extrai informações básicas
                            titulo = None
                            preco = None
                            endereco = None
                            link = None
                            
                            # Título
                            titulo_elem = imovel.find(['h2', 'h3', 'span'], class_=re.compile('title|name'))
                            if not titulo_elem:
                                titulo_elem = imovel.find(text=re.compile(r'(apartamento|casa|kitnet)', re.I))
                            
                            if titulo_elem:
                                titulo = titulo_elem.text.strip() if hasattr(titulo_elem, 'text') else str(titulo_elem).strip()
                            
                            # Preço
                            preco_elem = imovel.find(['span', 'p'], class_=re.compile('price|valor'))
                            if not preco_elem:
                                preco_elem = imovel.find(text=re.compile(r'R\$'))
                            
                            if preco_elem:
                                preco_text = preco_elem.text if hasattr(preco_elem, 'text') else str(preco_elem)
                                preco = self.extract_number(preco_text)
                            
                            # Link
                            if imovel.name == 'a':
                                link = imovel.get('href', '')
                            else:
                                link_elem = imovel.find('a')
                                if link_elem:
                                    link = link_elem.get('href', '')
                            
                            if link and not link.startswith('http'):
                                link = f"https://df.olx.com.br{link}"
                            
                            # Localização
                            loc_elem = imovel.find(['span', 'p'], class_=re.compile('location|local|bairro'))
                            if loc_elem:
                                endereco = loc_elem.text.strip()
                            
                            # Se não tem título, pula
                            if not titulo:
                                continue
                            
                            # Extrai features do título
                            features = self.extract_features_from_title(titulo)
                            
                            # Parse do endereço
                            endereco_resumido = self.parse_endereco(endereco or '', titulo)
                            
                            imovel_data = {
                                'preco': preco,
                                'area': features['area'],
                                'quartos': features['quartos'],
                                'banheiros': None,
                                'vagas': features['vagas'],
                                'tipo': features['tipo'],
                                'titulo': titulo,
                                'endereco_completo': endereco or 'Brasília - DF',
                                'url': link or f"https://df.olx.com.br/imovel/{abs(hash(titulo))}",
                                'site': 'OLX',
                                'data_captura': datetime.now().isoformat()
                            }
                            
                            # Evita duplicatas
                            if endereco_resumido in daily_data[today]:
                                endereco_resumido = f"{endereco_resumido}_{abs(hash(titulo)) % 1000}"
                            
                            daily_data[today][endereco_resumido] = imovel_data
                            total_capturados += 1
                            
                            if preco:
                                logging.info(f"Capturado: {endereco_resumido} - R$ {preco:,.2f} - {titulo[:50]}")
                            else:
                                logging.info(f"Capturado: {endereco_resumido} - {titulo[:50]}")
                        
                        except Exception as e:
                            logging.error(f"Erro ao processar imóvel individual: {e}")
                            continue
                    
                    time.sleep(2)  # Delay entre páginas
                    
                except Exception as e:
                    logging.error(f"Erro ao acessar página {page}: {e}")
                    continue
        
        self.save_daily_data(daily_data, today)
        logging.info(f"Total de imóveis capturados: {total_capturados}")
        logging.info(f"Dados salvos em imoveis_{today}.json")
        
        return total_capturados > 0
    
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
                print(f"\nEstatísticas de preço:")
                print(f"  Média: R$ {sum(precos)/len(precos):,.2f}")
                print(f"  Mínimo: R$ {min(precos):,.2f}")
                print(f"  Máximo: R$ {max(precos):,.2f}")
                print(f"  Com preço: {len(precos)} ({len(precos)/total*100:.1f}%)")
            
            # Tipos de imóveis
            tipos = {}
            for item in daily_data[today].values():
                tipo = item.get('tipo', 'Não especificado')
                tipos[tipo] = tipos.get(tipo, 0) + 1
            
            print("\nTipos de imóveis:")
            for tipo, count in sorted(tipos.items(), key=lambda x: x[1], reverse=True):
                print(f"  {tipo}: {count}")
            
            # Contagem por bairro
            bairros = {}
            for endereco in daily_data[today].keys():
                sigla = endereco.split('_')[0]
                bairros[sigla] = bairros.get(sigla, 0) + 1
            
            print("\nImóveis por região:")
            for bairro, count in sorted(bairros.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {bairro}: {count}")
        else:
            print(f"\nNenhum dado encontrado para {today}")

if __name__ == "__main__":
    scraper = OLXScraper()
    
    # Tenta scraping
    success = scraper.scrape_olx(max_pages=2)
    
    if success:
        scraper.show_daily_summary()
    else:
        print("\nNenhum dado foi capturado. Possíveis razões:")
        print("1. Sites com proteção anti-bot (Cloudflare)")
        print("2. Estrutura HTML diferente da esperada")
        print("3. Necessário usar Selenium com undetected-chromedriver")
        print("\nPara funcionar adequadamente, instale:")
        print("pip install undetected-chromedriver")