import os
import requests
from bs4 import BeautifulSoup
import re
from pathlib import Path
from datetime import datetime
import time
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("cvm_download.log"),
        logging.StreamHandler()
    ]
)

BASE_URL = "https://dados.cvm.gov.br/dados/FI/DOC/"
DEST_DIR = r"C:\Users\guilh\Documents\GitHub\sherpa\database"
CATEGORIES = [
    "BALANCETE",
    "CDA",
    "COMPL",
    "EVENTUAL",
    "EXTRATO",
    "INF_DIARIO",
    "LAMINA",
    "PERFIL_MENSAL"
]

def ensure_dir_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        logging.info(f"Diretório criado: {directory}")

def download_file(url, destination):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # exc para codigos de erro HTTP

        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        file_size = os.path.getsize(destination) / (1024 * 1024)  # tamanho em MB
        logging.info(f"Arquivo baixado: {destination} ({file_size:.2f} MB)")
        return True
    except Exception as e:
        logging.error(f"Erro ao baixar {url}: {str(e)}")
        return False

def get_file_list(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        files = []
        
        # Encontra todos os links para arquivos (exclui dir)
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and not href.endswith('/') and href != '../':
                # Ignora os links de nav e dir
                if href.lower().endswith(('.zip', '.csv')):
                    file_url = url + href if url.endswith('/') else url + '/' + href
                    files.append((href, file_url))
        
        return files
    except Exception as e:
        logging.error(f"Erro ao obter lista de arquivos de {url}: {str(e)}")
        return []

def get_subdirectories(url):

    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        subdirs = []
        
        # Encontra todos os links para dirs (terminados com /)
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and href.endswith('/') and href != '../':
                subdir_url = url + href if url.endswith('/') else url + '/' + href
                subdirs.append(subdir_url)
        
        return subdirs
    except Exception as e:
        logging.error(f"Erro ao obter subdiretórios de {url}: {str(e)}")
        return []

def download_category(category):
    """
    Baixa todos os arquivos de uma categoria específica.
    """
    category_url = f"{BASE_URL}{category}/DADOS/"
    category_dir = os.path.join(DEST_DIR, category)
    ensure_dir_exists(category_dir)
    
    logging.info(f"Processando categoria: {category}")
    
    # Verifica se ha subidrs
    subdirs = get_subdirectories(category_url)
    
    if subdirs:
        # Se houver subdirs, processa cada um
        for subdir in subdirs:
            subdir_name = subdir.split('/')[-2]  # nome do subdir
            subdir_path = os.path.join(category_dir, subdir_name)
            ensure_dir_exists(subdir_path)
            
            files = get_file_list(subdir)
            for filename, file_url in files:
                dest_file = os.path.join(subdir_path, filename)
                
                # Verifica se o arquivo ja existe e se tem o mesmo tamanho
                if os.path.exists(dest_file):
                    logging.info(f"Arquivo já existe: {dest_file} - Pulando.")
                    continue
                
                download_file(file_url, dest_file)
                # Atraso para nao sobrecarregar o servidor
                time.sleep(0.5)
    else:
        # Se nao houver subdirs, obtem os arquivos diretamente
        files = get_file_list(category_url)
        for filename, file_url in files:
            dest_file = os.path.join(category_dir, filename)
            
            # Verifica se o arquivo ja existe
            if os.path.exists(dest_file):
                logging.info(f"Arquivo já existe: {dest_file} - Pulando.")
                continue
            
            download_file(file_url, dest_file)
            # Atraso para nao sobrecarregar o servidor
            time.sleep(0.5)

def download_direct_files():
    root_url = "https://dados.cvm.gov.br/dados/FI/CAD/DADOS/"
    root_dir = os.path.join(DEST_DIR, "CAD")
    ensure_dir_exists(root_dir)
    
    logging.info("Baixando arquivos principais do cadastro de fundos...")
    
    files = get_file_list(root_url)
    for filename, file_url in files:
        dest_file = os.path.join(root_dir, filename)
        
        # Verifica se o arquivo ja existe
        if os.path.exists(dest_file):
            logging.info(f"Arquivo já existe: {dest_file} - Pulando.")
            continue
        
        download_file(file_url, dest_file)
        # Atraso para nao sobrecarregar o servidor
        time.sleep(0.5)

def main():
    """Função principal que coordena o download de todas as categorias."""
    start_time = datetime.now()
    logging.info(f"Iniciando download de dados da CVM em {start_time}")
    
    # Garante que o dir principal existe
    ensure_dir_exists(DEST_DIR)
    
    # Baixa os arquivos de cadastro geral
    download_direct_files()
    
    # Baixa cada categoria
    for category in CATEGORIES:
        download_category(category)
    
    end_time = datetime.now()
    duration = end_time - start_time
    logging.info(f"Download concluído em {duration}")
    logging.info(f"Os arquivos foram salvos em: {DEST_DIR}")


if __name__ == "__main__":
    main()
