import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import json

def investigate_with_requests(url, site_name):
    """Try to fetch page with requests library"""
    print(f"\n{'='*50}")
    print(f"Investigating {site_name} with requests")
    print(f"URL: {url}")
    print(f"{'='*50}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            print(f"Page Title: {soup.title.string if soup.title else 'No title found'}")
            
            # Look for property listing containers
            possible_containers = [
                'property-card', 'listing-card', 'card-listing',
                'imovel-card', 'property-item', 'result-item',
                'card', 'listing', 'property'
            ]
            
            for container in possible_containers:
                # Try class
                elements = soup.find_all(class_=lambda x: x and container in x.lower() if x else False)
                if elements:
                    print(f"\nFound {len(elements)} elements with class containing '{container}'")
                    if elements:
                        print(f"Sample element: {elements[0].get('class')}")
                
                # Try id
                elements = soup.find_all(id=lambda x: x and container in x.lower() if x else False)
                if elements:
                    print(f"\nFound {len(elements)} elements with id containing '{container}'")
            
            # Look for price elements
            price_indicators = ['preço', 'preco', 'price', 'valor', 'R$']
            for indicator in price_indicators:
                elements = soup.find_all(text=lambda x: x and indicator in str(x))
                if elements:
                    print(f"\nFound {len(elements)} text elements containing '{indicator}'")
                    
        elif response.status_code == 403:
            print("\n⚠️  403 Forbidden - Site has anti-scraping measures")
            # Check for Cloudflare
            if 'cloudflare' in response.text.lower() or 'cf-ray' in str(response.headers).lower():
                print("Detected: Cloudflare protection")
                
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return False

def investigate_with_selenium(url, site_name):
    """Try to fetch page with Selenium"""
    print(f"\n{'='*50}")
    print(f"Investigating {site_name} with Selenium")
    print(f"URL: {url}")
    print(f"{'='*50}")
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        
        # Wait for page to load
        time.sleep(5)
        
        print(f"Page Title: {driver.title}")
        print(f"Current URL: {driver.current_url}")
        
        # Check for Cloudflare challenge
        if "challenge" in driver.current_url or "cloudflare" in driver.page_source.lower():
            print("\n⚠️  Detected Cloudflare challenge page")
            
        # Try to find property listings
        selectors_to_try = {
            'Zap': [
                "[data-testid='card-container']",
                ".card-container",
                ".listing-card",
                ".property-card",
                "[class*='Card']",
                "[class*='card']"
            ],
            'VivaReal': [
                "[data-testid='card']",
                ".property-card",
                ".js-card-selector",
                "[class*='Card']",
                ".results-list article"
            ],
            'ImovelWeb': [
                ".aviso",
                ".posting-card",
                ".card-aviso",
                "[class*='posting']",
                ".item-listing"
            ]
        }
        
        site_key = 'Zap' if 'zap' in site_name.lower() else 'VivaReal' if 'viva' in site_name.lower() else 'ImovelWeb'
        
        for selector in selectors_to_try.get(site_key, []):
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"\n✓ Found {len(elements)} elements with selector: {selector}")
                    
                    # Analyze first element structure
                    if elements:
                        element = elements[0]
                        print(f"\nAnalyzing first property card:")
                        
                        # Try to find price
                        price_selectors = ["[class*='price']", "[class*='valor']", "[class*='preco']"]
                        for price_sel in price_selectors:
                            price_elem = element.find_elements(By.CSS_SELECTOR, price_sel)
                            if price_elem:
                                print(f"  Price selector: {price_sel}")
                                print(f"  Price text: {price_elem[0].text[:50]}")
                                break
                        
                        # Try to find area
                        area_selectors = ["[class*='area']", "[class*='m2']", "[class*='metros']"]
                        for area_sel in area_selectors:
                            area_elem = element.find_elements(By.CSS_SELECTOR, area_sel)
                            if area_elem:
                                print(f"  Area selector: {area_sel}")
                                print(f"  Area text: {area_elem[0].text[:50]}")
                                break
                        
                        # Try to find bedrooms
                        bedroom_selectors = ["[class*='bedroom']", "[class*='quarto']", "[class*='dorm']"]
                        for bed_sel in bedroom_selectors:
                            bed_elem = element.find_elements(By.CSS_SELECTOR, bed_sel)
                            if bed_elem:
                                print(f"  Bedroom selector: {bed_sel}")
                                print(f"  Bedroom text: {bed_elem[0].text[:50]}")
                                break
                                
            except Exception as e:
                continue
        
        # Check if content is dynamically loaded
        initial_height = driver.execute_script("return document.body.scrollHeight")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        if new_height > initial_height:
            print("\n📜 Content appears to be dynamically loaded (infinite scroll detected)")
        
        return True
        
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return False
    finally:
        if driver:
            driver.quit()

def main():
    sites = [
        ("https://www.zapimoveis.com.br/venda/imoveis/df+brasilia/", "Zap Imóveis"),
        ("https://www.vivareal.com.br/venda/distrito-federal/brasilia/", "VivaReal"),
        ("https://www.imovelweb.com.br/imoveis-venda-brasilia-df.html", "ImovelWeb")
    ]
    
    results = {}
    
    for url, name in sites:
        results[name] = {
            'url': url,
            'requests_success': investigate_with_requests(url, name),
            'selenium_needed': False
        }
        
        if not results[name]['requests_success']:
            print(f"\n🔄 Trying Selenium for {name}...")
            results[name]['selenium_needed'] = True
            investigate_with_selenium(url, name)
    
    print(f"\n\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    
    for site, info in results.items():
        print(f"\n{site}:")
        print(f"  - Requests success: {info['requests_success']}")
        print(f"  - Selenium needed: {info['selenium_needed']}")

if __name__ == "__main__":
    main()