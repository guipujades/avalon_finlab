import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

def test_simple_scraping():
    """Testa acesso direto aos sites para verificar proteções"""
    
    sites = [
        {
            'nome': 'ImovelWeb',
            'url': 'https://www.imovelweb.com.br/imoveis-venda-brasilia-df.html'
        },
        {
            'nome': 'ZAP Imóveis',
            'url': 'https://www.zapimoveis.com.br/venda/imoveis/df+brasilia/'
        },
        {
            'nome': 'Viva Real',
            'url': 'https://www.vivareal.com.br/venda/distrito-federal/brasilia/'
        }
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    for site in sites:
        print(f"\n=== Testando {site['nome']} ===")
        try:
            response = requests.get(site['url'], headers=headers, timeout=10)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                print(f"Título da página: {soup.title.string if soup.title else 'Sem título'}")
                
                # Verifica se tem conteúdo de imóveis
                if 'cloudflare' in response.text.lower():
                    print("⚠️  Cloudflare detectado")
                
                # Procura por indicadores de imóveis
                indicators = ['apartamento', 'casa', 'imóvel', 'quarto', 'venda', 'R$']
                found = sum(1 for ind in indicators if ind.lower() in response.text.lower())
                print(f"Indicadores de conteúdo encontrados: {found}/6")
                
            elif response.status_code == 403:
                print("❌ Acesso bloqueado (403 Forbidden) - Provável proteção anti-bot")
                
            else:
                print(f"❌ Erro: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erro na requisição: {e}")

if __name__ == "__main__":
    test_simple_scraping()