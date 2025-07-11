import pandas as pd
import requests, datetime as dt
import pickle, pathlib as Path
from tqdm import tqdm
import xml.etree.ElementTree as ET
import re
from newspaper import Article
import browser_cookie3, requests


NS = {
    "sm":  "http://www.sitemaps.org/schemas/sitemap/0.9",
    "img": "http://www.google.com/schemas/sitemap-image/1.1",
}

def parse_sitemap(xml_text: str):
    """Converte XML de sitemap em lista de dicionários seguros contra campos ausentes."""
    root = ET.fromstring(xml_text)
    dados = []

    for node in root.findall("sm:url", NS):
        # Sempre existe <loc>; se não existir, pulamos a entrada
        loc_tag = node.find("sm:loc", NS)
        if loc_tag is None:
            continue

        # <lastmod> pode faltar (tag opcional segundo o protocolo)
        lastmod_tag = node.find("sm:lastmod", NS)
        lastmod = lastmod_tag.text if lastmod_tag is not None else None

        # Primeiro tenta <image:image>/<image:loc>; se não achar, fica None
        img_loc_tag = node.find("img:image/img:loc", NS)
        if img_loc_tag is None:                      # cobertura para Sitemap sem child <loc>
            img_loc_tag = node.find("img:image", NS)
        image_url = img_loc_tag.text if img_loc_tag is not None else None

        dados.append({
            "url":     loc_tag.text,
            "lastmod": lastmod,
            "image":   image_url,
        })
    return dados



dates = pd.date_range("2024-06-01", "2025-04-25", freq="D")

BASE = "https://valor.globo.com/sitemap/valor/{:%Y/%m/%d}_1.xml"
raw_xml = {}                     # dicionário <data: str> → <xml: str>

for day in tqdm(dates):
    url = BASE.format(day)
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()     # lança exceção se não for 200
        raw_xml[str(day.date())] = r.text
    except requests.exceptions.HTTPError as e:
        print(f"{url} → {e}")
        
        
        
sitemap_data = {}
for date, xml in raw_xml.items():        # raw_xml veio da etapa anterior
    sitemap_data[date] = parse_sitemap(xml)

# salvar apenas urls
all_urls_dates = {}
for k,v in sitemap_data.items():
    all_urls_dates[k] = [i['url'] for i in v]
all_urls = [url 
            for urls in all_urls_dates.values() 
            for url  in urls]


pattern = re.compile(r"india", re.IGNORECASE)

cookies = browser_cookie3.chrome(domain_name='valor.globo.com')
sess = requests.Session(); sess.cookies.update(cookies)
store_text = {}
tema = 'india'

from tqdm import tqdm
for link in all_urls:
    # filtra toda URL que contenha 'mexico' (maiúscula ou minúscula)
    if not pattern.search(link):
        continue

    html = sess.get(link, timeout=20).text
    art = Article(link, language='pt')
    art.set_html(html)
    art.parse()

    # Se quiser armazenar várias notícias, use lista em vez de sobrescrever
    store_text.setdefault(tema, []).append(
        (art.title, art.text, art.authors, art.publish_date, link)
    )

output_path = Path(Path.home(), 'Desktop', "india_articles.txt")

with output_path.open("w", encoding="utf8") as f:
    for title, text, authors, pub_date, link in store_text.get(tema, []):
        f.write(f"Título: {title}\n")
        f.write(f"Data de publicação: {pub_date}\n")
        f.write(f"Autores: {', '.join(authors) if authors else 'N/D'}\n")
        f.write(f"URL: {link}\n\n")
        f.write(text.strip() + "\n\n")
        f.write("=" * 100 + "\n\n")

print(f"Salvo em {output_path.resolve()}")
    
