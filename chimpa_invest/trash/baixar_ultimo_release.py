import requests
import pandas as pd
import zipfile
import io
from pathlib import Path
from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm
import json
import sys

# Mapeamento de tickers para nomes de empresas
TICKER_MAPPING = {
    # Petrobras
    'PETR3': 'PETRÓLEO BRASILEIRO  S.A.  - PETROBRAS',
    'PETR4': 'PETRÓLEO BRASILEIRO  S.A.  - PETROBRAS',
    'PETROBRAS': 'PETRÓLEO BRASILEIRO  S.A.  - PETROBRAS',
    
    # Vale
    'VALE3': 'VALE S.A.',
    'VALE': 'VALE S.A.',
    
    # Bancos
    'ITUB3': 'ITAUSA S.A.',
    'ITUB4': 'ITAUSA S.A.',
    'BBAS3': 'BANCO DO BRASIL S.A.',
    'BBDC3': 'BANCO BRADESCO S.A.',
    'BBDC4': 'BANCO BRADESCO S.A.',
    'SANB3': 'SANTANDER',
    'SANB4': 'SANTANDER',
    'SANB11': 'SANTANDER',
    
    # Varejo
    'MGLU3': 'MAGAZINE LUIZA SA',
    'LREN3': 'LOJAS RENNER S.A.',
    'AMER3': 'AMERICANAS S.A.',
    'PETZ3': 'PET CENTER COMÉRCIO E PARTICIPAÇÕES S.A.',
    
    # Energia
    'ELET3': 'ELETROBRAS',
    'ELET6': 'ELETROBRAS',
    'CMIG3': 'CEMIG',
    'CMIG4': 'CEMIG',
    'CPFE3': 'CPFL ENERGIA',
    'ENBR3': 'EDP BRASIL',
    
    # Telecomunicações
    'VIVT3': 'VIVO',
    'TIMS3': 'TIM',
    
    # Outros
    'ABEV3': 'AMBEV S.A.',
    'WEGE3': 'WEG S.A.',
    'SUZB3': 'SUZANO S.A.',
    'RENT3': 'LOCALIZA',
    'RAIL3': 'RUMO',
    'EMBR3': 'EMBRAER',
    'AZUL4': 'AZUL',
    'GOLL4': 'GOL',
    'BEEF3': 'MINERVA',
    'JBSS3': 'JBS',
    'MRFG3': 'MARFRIG',
}

def obter_nome_empresa():
    """Obtém o nome da empresa do usuário"""
    print("\n=== Seleção de Empresa ===")
    print("Digite o ticker (ex: PETR4) ou nome da empresa (ex: PETROBRAS)")
    print("Exemplos de tickers: PETR4, VALE3, ITUB4, BBAS3, MGLU3")
    
    entrada = input("\nEmpresa/Ticker: ").strip().upper()
    
    if not entrada:
        print("Usando PETROBRAS como padrão")
        return "PETROLEO BRASILEIRO"
    
    # Verificar se é um ticker conhecido
    if entrada in TICKER_MAPPING:
        nome_empresa = TICKER_MAPPING[entrada]
        print(f"Ticker {entrada} → {nome_empresa}")
        return nome_empresa
    
    # Tentar variações do ticker
    ticker_base = entrada.rstrip('34567890')  # Remove números do final
    for ticker, nome in TICKER_MAPPING.items():
        if ticker.startswith(ticker_base):
            print(f"Ticker similar encontrado: {ticker} → {nome}")
            confirma = input("Usar esta empresa? (S/n): ").strip().lower()
            if confirma != 'n':
                return nome
    
    # Se não for ticker, usar como nome
    print(f"Buscando por: {entrada}")
    return entrada

# Configurações
ANO_ATUAL = datetime.now().year
PASTA_PENDING = Path("/mnt/c/Users/guilh/documents/github/chimpa_invest/documents/pending")

# URL base da CVM
URL_IPE = f'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/ipe_cia_aberta_{ANO_ATUAL}.zip'

def baixar_dados_ipe():
    """Baixa dados IPE do ano atual"""
    print(f"\nBaixando dados IPE de {ANO_ATUAL}...")
    try:
        response = requests.get(URL_IPE, timeout=30)
        response.raise_for_status()
        
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
            arquivo_csv = f'ipe_cia_aberta_{ANO_ATUAL}.csv'
            if arquivo_csv in zip_file.namelist():
                df = pd.read_csv(
                    zip_file.open(arquivo_csv),
                    sep=';',
                    encoding='latin-1'
                )
                print(f"Dados IPE carregados: {len(df)} registros")
                return df
    except Exception as e:
        print(f"Erro ao baixar dados IPE: {str(e)}")
        return None

def filtrar_ultimo_release(df, nome_empresa):
    """Filtra e retorna o último release da empresa"""
    print(f"\nProcurando releases de '{nome_empresa}'...")
    
    # Filtrar por nome da empresa
    df_empresa = df[df['Nome_Companhia'].str.contains(nome_empresa, case=False, na=False)].copy()
    
    if df_empresa.empty:
        # Tentar busca parcial
        print(f"Nenhum resultado exato. Tentando busca parcial...")
        palavras = nome_empresa.split()
        for palavra in palavras:
            if len(palavra) > 3:  # Ignorar palavras muito curtas
                df_temp = df[df['Nome_Companhia'].str.contains(palavra, case=False, na=False)]
                if not df_temp.empty:
                    print(f"Encontradas empresas com '{palavra}':")
                    empresas_unicas = df_temp['Nome_Companhia'].unique()[:5]
                    for i, emp in enumerate(empresas_unicas):
                        print(f"  {i+1}. {emp}")
                    
                    escolha = input("\nEscolha o número da empresa ou ENTER para continuar: ").strip()
                    if escolha.isdigit() and 1 <= int(escolha) <= len(empresas_unicas):
                        df_empresa = df_temp[df_temp['Nome_Companhia'] == empresas_unicas[int(escolha)-1]]
                        break
    
    if df_empresa.empty:
        return None
    
    print(f"Encontradas {len(df_empresa)} entradas")
    
    # Converter data para datetime
    df_empresa['Data_Entrega'] = pd.to_datetime(df_empresa['Data_Entrega'], format='%Y-%m-%d', errors='coerce')
    
    # Filtrar APENAS releases de resultados trimestrais
    palavras_resultado = [
        'Desempenho', 'Resultado', 'Release de Resultado',
        'Informações Trimestrais', 'ITR',
        '1T', '2T', '3T', '4T', '1Q', '2Q', '3Q', '4Q',
        'Trimestre', 'Trimestral', 'Earnings'
    ]
    
    palavras_excluir = [
        'Ata', 'AGO', 'AGE', 'Assembl', 'Eleição', 'Conselho',
        'Dividendo', 'JCP', 'Juros', 'Aquisição', 'Venda',
        'Aprovação', 'Plano', 'incorporadas em prospectos',
        'arquivados na SEC', 'Produção e Vendas'
    ]
    
    mask_incluir = df_empresa['Assunto'].str.contains('|'.join(palavras_resultado), case=False, na=False)
    mask_excluir = df_empresa['Assunto'].str.contains('|'.join(palavras_excluir), case=False, na=False)
    
    tipos_validos = ['Dados Econômico-Financeiros', 'Comunicado ao Mercado', 'Fato Relevante', 
                     'Press-release', 'Apresentações a analistas/agentes do mercado']
    mask_tipo = df_empresa['Tipo'].isin(tipos_validos) | df_empresa['Tipo'].isna()
    
    df_filtrado = df_empresa[mask_incluir & ~mask_excluir & mask_tipo]
    
    if df_filtrado.empty:
        print("Nenhum release financeiro encontrado. Pegando documento mais recente...")
        df_filtrado = df_empresa
    
    # Ordenar por data e pegar o mais recente
    df_filtrado = df_filtrado.sort_values('Data_Entrega', ascending=False)
    
    # Mostrar os 5 mais recentes
    print("\nÚltimos 5 documentos encontrados:")
    for idx, row in df_filtrado.head(5).iterrows():
        print(f"- {row['Data_Entrega'].strftime('%Y-%m-%d')}: {row['Assunto'][:70]}...")
    
    return df_filtrado.iloc[0] if not df_filtrado.empty else None

def baixar_pdf_com_requests(url, nome_arquivo):
    """Tenta baixar PDF usando requests"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()
        
        caminho_arquivo = PASTA_PENDING / nome_arquivo
        
        with open(caminho_arquivo, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True
    except:
        return False

def baixar_pdf_com_selenium(url, nome_arquivo):
    """Baixa PDF usando Selenium como fallback"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    prefs = {
        "download.default_directory": str(PASTA_PENDING),
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True
    }
    options.add_experimental_option("prefs", prefs)
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        
        # Aguardar download
        time.sleep(5)
        
        driver.quit()
        return True
    except Exception as e:
        print(f"Erro Selenium: {str(e)}")
        return False

def main():
    """Função principal para baixar último release"""
    print("=== Baixar Último Release CVM ===")
    
    # Verificar se foi passado argumento de linha de comando
    if len(sys.argv) > 1:
        entrada = sys.argv[1].upper()
        if entrada in TICKER_MAPPING:
            nome_empresa = TICKER_MAPPING[entrada]
            print(f"Usando ticker: {entrada} → {nome_empresa}")
        else:
            nome_empresa = entrada
            print(f"Buscando por: {nome_empresa}")
    else:
        # Obter empresa interativamente
        nome_empresa = obter_nome_empresa()
    
    print(f"\nBuscando releases para: {nome_empresa}")
    print(f"Ano: {ANO_ATUAL}")
    
    # Criar pasta pending se não existir
    PASTA_PENDING.mkdir(parents=True, exist_ok=True)
    
    # Baixar dados IPE
    df_ipe = baixar_dados_ipe()
    
    if df_ipe is None:
        print("Erro ao baixar dados IPE")
        return
    
    # Filtrar último release
    ultimo_release = filtrar_ultimo_release(df_ipe, nome_empresa)
    
    if ultimo_release is None:
        print(f"\nNenhum release encontrado para {nome_empresa}")
        
        # Sugerir empresas similares
        print("\nEmpresas disponíveis no sistema:")
        empresas_unicas = sorted(df_ipe['Nome_Companhia'].unique())
        
        # Filtrar empresas que contenham parte do nome buscado
        sugestoes = [emp for emp in empresas_unicas if any(palavra in emp.upper() for palavra in nome_empresa.split())]
        
        if sugestoes:
            print("\nSugestões:")
            for sug in sugestoes[:10]:
                print(f"  - {sug}")
        
        return
    
    # Exibir informações do release
    print("\n=== Último Release Encontrado ===")
    print(f"Empresa: {ultimo_release['Nome_Companhia']}")
    print(f"Data: {ultimo_release['Data_Entrega']}")
    print(f"Assunto: {ultimo_release['Assunto']}")
    print(f"Tipo: {ultimo_release['Tipo']}")
    
    # Preparar nome do arquivo
    empresa_limpa = ''.join(c for c in ultimo_release['Nome_Companhia'] if c.isalnum() or c in ' -_')[:30]
    data_str = ultimo_release['Data_Entrega'].strftime('%Y%m%d')
    assunto_limpo = ''.join(c for c in ultimo_release['Assunto'] if c.isalnum() or c in ' -_')[:50]
    nome_arquivo = f"{empresa_limpa}_{data_str}_{assunto_limpo}.pdf"
    
    # Baixar PDF
    url_download = ultimo_release['Link_Download']
    print(f"\nBaixando PDF...")
    
    # Tentar primeiro com requests
    sucesso = baixar_pdf_com_requests(url_download, nome_arquivo)
    
    if not sucesso:
        print("Tentando método alternativo...")
        sucesso = baixar_pdf_com_selenium(url_download, nome_arquivo)
    
    if sucesso:
        print(f"\nPDF baixado com sucesso!")
        print(f"Arquivo: {PASTA_PENDING / nome_arquivo}")
        
        # Salvar metadados
        metadata = {
            "empresa": ultimo_release['Nome_Companhia'],
            "data_entrega": ultimo_release['Data_Entrega'].strftime('%Y-%m-%d'),
            "assunto": ultimo_release['Assunto'],
            "tipo": ultimo_release['Tipo'],
            "url_original": url_download,
            "arquivo": nome_arquivo,
            "download_em": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        metadata_file = PASTA_PENDING / f"{nome_arquivo}.metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
    else:
        print("\nErro ao baixar PDF")

if __name__ == "__main__":
    main()