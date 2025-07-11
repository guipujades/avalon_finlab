import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import time
import re
from urllib.parse import urljoin
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ImoveisScraperSimple:
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
    
    def scrape_vivareal_simple(self, max_pages=2):
        """Scraping simplificado do Viva Real usando apenas requests"""
        logging.info("Iniciando scraping simplificado do Viva Real...")
        base_url = "https://www.vivareal.com.br/venda/distrito-federal/brasilia/"
        
        today = datetime.now().strftime('%Y-%m-%d')
        daily_data = self.load_daily_data(today)
        
        if today not in daily_data:
            daily_data[today] = {}
        
        # Dados de exemplo para teste
        exemplos = [
            {
                'endereco': 'SQS 308 Bloco A Apartamento 201, Asa Sul',
                'preco': 850000,
                'area': 120,
                'quartos': 3,
                'banheiros': 2,
                'vagas': 2,
                'titulo': 'Apartamento com 3 quartos à venda'
            },
            {
                'endereco': 'SQN 208 Bloco B Apartamento 304, Asa Norte',
                'preco': 650000,
                'area': 90,
                'quartos': 2,
                'banheiros': 1,
                'vagas': 1,
                'titulo': 'Apartamento 2 quartos reformado'
            },
            {
                'endereco': 'QI 5 Conjunto 12 Casa 15, Lago Norte',
                'preco': 2500000,
                'area': 400,
                'quartos': 4,
                'banheiros': 4,
                'vagas': 4,
                'titulo': 'Casa em condomínio fechado'
            }
        ]
        
        for idx, exemplo in enumerate(exemplos):
            endereco_resumido = self.parse_endereco(exemplo['endereco'])
            
            imovel_data = {
                'preco': exemplo['preco'],
                'area': exemplo['area'],
                'quartos': exemplo['quartos'],
                'banheiros': exemplo['banheiros'],
                'vagas': exemplo['vagas'],
                'titulo': exemplo['titulo'],
                'endereco_completo': exemplo['endereco'],
                'url': f"https://exemplo.com/imovel/{idx}",
                'site': 'Viva Real (Exemplo)',
                'data_captura': datetime.now().isoformat()
            }
            
            daily_data[today][endereco_resumido] = imovel_data
            logging.info(f"Exemplo capturado: {endereco_resumido} - R$ {exemplo['preco']:,.2f}")
        
        self.save_daily_data(daily_data, today)
        logging.info(f"Dados de exemplo salvos em imoveis_{today}.json")
        
        return True
    
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
            
            print("\nExemplos de endereços processados:")
            for endereco, dados in list(daily_data[today].items())[:3]:
                print(f"  {endereco} -> {dados['endereco_completo']}")

if __name__ == "__main__":
    scraper = ImoveisScraperSimple()
    
    print("=== TESTE DO SCRAPER DE IMÓVEIS ===")
    print("Executando com dados de exemplo...")
    
    scraper.scrape_vivareal_simple()
    scraper.show_daily_summary()