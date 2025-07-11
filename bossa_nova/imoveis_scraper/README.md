# Scraper de Imóveis - Brasília

Este projeto captura dados diários de imóveis à venda em Brasília, salvando em formato JSON estruturado.

## Situação Atual

Todos os principais sites de imóveis brasileiros (ZAP, VivaReal, ImovelWeb, OLX) estão usando Cloudflare para proteção contra bots, retornando erro 403 para requisições diretas.

## Soluções Implementadas

### 1. Script com Dados de Exemplo (FUNCIONANDO)
- `imoveis_scraper_simple.py` - Demonstra o formato de dados e estrutura
- Usa dados de exemplo para testar o parser de endereços
- Mostra como os dados são organizados no JSON

### 2. Script com Selenium (REQUER CHROME)
- `imoveis_scraper.py` - Versão original com Selenium básico
- `imoveis_scraper_v2.py` - Versão melhorada com undetected-chromedriver
- Requer Google Chrome instalado no sistema

## Instalação

### 1. Instalar Chrome no WSL:
```bash
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
sudo apt update
sudo apt install google-chrome-stable
```

### 2. Instalar dependências Python:
```bash
pip3 install --user requests beautifulsoup4 selenium undetected-chromedriver pandas lxml
```

### 3. Configurar ChromeDriver:
```bash
# Se você já baixou o chromedriver
unzip chromedriver_linux64.zip
chmod +x chromedriver
```

## Uso

### Testar com dados de exemplo:
```bash
python3 imoveis_scraper_simple.py
```

### Executar scraper completo (requer Chrome):
```bash
python3 imoveis_scraper_v2.py
```

## Formato dos Dados

Os dados são salvos em `dados_imoveis/imoveis_YYYY-MM-DD.json`:

```json
{
  "2025-06-24": {
    "ASS_308_A_201": {
      "preco": 850000,
      "area": 120,
      "quartos": 3,
      "banheiros": 2,
      "vagas": 2,
      "titulo": "Apartamento com 3 quartos à venda",
      "endereco_completo": "SQS 308 Bloco A Apartamento 201, Asa Sul",
      "url": "https://exemplo.com/imovel/123",
      "site": "ZAP Imóveis",
      "data_captura": "2025-06-24T15:02:45.578810"
    }
  }
}
```

### Formato do Endereço Resumido:
- `ASS_308_A_201` = Asa Sul, Quadra 308, Bloco A, Apartamento 201
- `LN_5_15` = Lago Norte, QI 5, Casa 15
- `TAG_25_B_302` = Taguatinga, Quadra 25, Bloco B, Apartamento 302

## Siglas dos Bairros

- ASS: Asa Sul
- ASN: Asa Norte
- LS: Lago Sul
- LN: Lago Norte
- SW: Sudoeste
- NW: Noroeste
- AC: Águas Claras
- TAG: Taguatinga
- CEI: Ceilândia
- SAM: Samambaia
- VP: Vicente Pires
- GUA: Guará
- SOB: Sobradinho
- PLA: Planaltina
- GAM: Gama
- SM: Santa Maria
- RDE: Recanto das Emas
- RF: Riacho Fundo
- BRZ: Brazlândia
- PAR: Paranoá
- ITA: Itapoã
- OCT: Octogonal
- CRZ: Cruzeiro
- PKW: Park Way
- JB: Jardim Botânico
- SS: São Sebastião
- ARN: Arniqueiras
- BSB: Brasília (genérico)

## Alternativas para Contornar Cloudflare

1. **Usar undetected-chromedriver** (implementado em `imoveis_scraper_v2.py`)
2. **Usar proxy residencial rotativo**
3. **Implementar delays e comportamento humano**
4. **Usar APIs não documentadas dos sites**
5. **Scraping via aplicativo mobile (APIs diferentes)**

## Estrutura do Projeto

```
imoveis_scraper/
├── dados_imoveis/          # JSONs diários
├── imoveis_scraper.py      # Scraper original
├── imoveis_scraper_v2.py   # Scraper com undetected-chromedriver
├── imoveis_scraper_simple.py # Exemplo funcional
├── test_simple_request.py  # Teste de acesso aos sites
├── requirements.txt        # Dependências Python
└── README.md              # Este arquivo
```