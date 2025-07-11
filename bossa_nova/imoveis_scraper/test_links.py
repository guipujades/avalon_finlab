from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

def test_imovelweb_links():
    """Testa se consegue encontrar links de imóveis"""
    
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    service = Service('./chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        url = "https://www.imovelweb.com.br/imoveis-venda-brasilia-df.html"
        print(f"Acessando: {url}")
        driver.get(url)
        time.sleep(5)
        
        # Tira screenshot para debug
        driver.save_screenshot("debug_screenshot.png")
        print("Screenshot salvo como debug_screenshot.png")
        
        # Testa diferentes formas de encontrar links
        print("\n=== TESTANDO SELETORES ===")
        
        # 1. Links gerais
        all_links = driver.find_elements(By.TAG_NAME, 'a')
        print(f"Total de links na página: {len(all_links)}")
        
        # 2. Procura padrões nos links
        property_links = []
        patterns = ['propriedades', 'imovel', 'apartamento', 'casa']
        
        for link in all_links[:50]:  # Verifica os primeiros 50 links
            try:
                href = link.get_attribute('href')
                text = link.text
                
                if href:
                    for pattern in patterns:
                        if pattern in href.lower():
                            print(f"\nLink encontrado:")
                            print(f"  URL: {href[:100]}")
                            print(f"  Texto: {text[:50]}")
                            property_links.append(href)
                            break
            except:
                continue
        
        print(f"\n\nTotal de links de imóveis encontrados: {len(property_links)}")
        
        # 3. Mostra estrutura HTML
        print("\n=== ESTRUTURA HTML ===")
        # Procura por elementos que parecem cards de imóveis
        potential_cards = [
            ('div[class*="card"]', "Cards com 'card' na classe"),
            ('article', "Elementos <article>"),
            ('div[class*="listing"]', "Divs com 'listing'"),
            ('div[class*="property"]', "Divs com 'property'"),
            ('div[data-qa]', "Divs com atributo data-qa"),
            ('[class*="posting"]', "Elementos com 'posting' na classe")
        ]
        
        for selector, description in potential_cards:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"\n{description}: {len(elements)} encontrados")
                # Mostra classes do primeiro elemento
                if elements[0].get_attribute('class'):
                    print(f"  Classes: {elements[0].get_attribute('class')}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_imovelweb_links()