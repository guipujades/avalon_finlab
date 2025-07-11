import requests
import pandas as pd
import zipfile
import io
from pathlib import Path
from datetime import datetime
import time
import json

# Configurações
EMPRESA_NOME = "PETROBRAS"  # Nome da empresa para buscar
ANO_ATUAL = datetime.now().year
PASTA_PENDING = Path("/mnt/c/Users/guilh/documents/github/chimpa_invest/documents/pending")

# URL base da CVM
URL_IPE = f'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/ipe_cia_aberta_{ANO_ATUAL}.zip'

def baixar_dados_ipe():
    """Baixa dados IPE do ano atual"""
    print(f"Baixando dados IPE de {ANO_ATUAL}...")
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
    print(f"\nProcurando releases de {nome_empresa}...")
    
    # Filtrar por nome da empresa
    df_empresa = df[df['Nome_Companhia'].str.contains(nome_empresa, case=False, na=False)].copy()
    
    if df_empresa.empty:
        # Tentar busca alternativa
        print(f"Nenhum resultado para '{nome_empresa}'. Tentando variações...")
        # Tentar PETRO ou PETROLEO BRASILEIRO
        if nome_empresa.upper() == "PETROBRAS":
            df_empresa = df[
                (df['Nome_Companhia'].str.contains('PETRO', case=False, na=False)) |
                (df['Nome_Companhia'].str.contains('PETROLEO BRASILEIRO', case=False, na=False))
            ].copy()
    
    if df_empresa.empty:
        return None
    
    print(f"Encontradas {len(df_empresa)} entradas")
    
    # Converter data para datetime
    df_empresa['Data_Entrega'] = pd.to_datetime(df_empresa['Data_Entrega'], format='%Y-%m-%d', errors='coerce')
    
    # Filtrar apenas releases com assuntos relevantes
    assuntos_relevantes = ['Desempenho', 'Resultado', 'Release', 'Demonstrações Financeiras', 'ITR', 'DFP']
    mask = df_empresa['Assunto'].str.contains('|'.join(assuntos_relevantes), case=False, na=False)
    df_filtrado = df_empresa[mask]
    
    if df_filtrado.empty:
        print("Nenhum release financeiro encontrado. Pegando documento mais recente...")
        df_filtrado = df_empresa
    
    # Ordenar por data e pegar o mais recente
    df_filtrado = df_filtrado.sort_values('Data_Entrega', ascending=False)
    
    # Mostrar os 5 mais recentes
    print("\nÚltimos 5 documentos encontrados:")
    for idx, row in df_filtrado.head(5).iterrows():
        print(f"- {row['Data_Entrega'].strftime('%Y-%m-%d')}: {row['Assunto'][:80]}...")
    
    return df_filtrado.iloc[0] if not df_filtrado.empty else None

def baixar_pdf_direto(url, nome_arquivo):
    """Baixa PDF diretamente usando requests"""
    print(f"\nBaixando PDF...")
    print(f"URL: {url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Fazer download com stream
        response = requests.get(url, headers=headers, timeout=60, stream=True)
        response.raise_for_status()
        
        # Verificar se é um PDF
        content_type = response.headers.get('Content-Type', '')
        if 'pdf' not in content_type.lower() and not nome_arquivo.endswith('.pdf'):
            print(f"Aviso: Content-Type é {content_type}")
        
        # Salvar arquivo
        caminho_arquivo = PASTA_PENDING / nome_arquivo
        
        total_size = int(response.headers.get('Content-Length', 0))
        
        with open(caminho_arquivo, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rProgresso: {percent:.1f}%", end='')
        
        print(f"\nArquivo salvo: {caminho_arquivo}")
        print(f"Tamanho: {downloaded / (1024*1024):.2f} MB")
        return True
        
    except Exception as e:
        print(f"Erro ao baixar PDF: {str(e)}")
        return False

def main():
    """Função principal para baixar último release"""
    print(f"=== Baixar Último Release CVM ===")
    print(f"Empresa: {EMPRESA_NOME}")
    print(f"Ano: {ANO_ATUAL}")
    
    # Criar pasta pending se não existir
    PASTA_PENDING.mkdir(parents=True, exist_ok=True)
    
    # Baixar dados IPE
    df_ipe = baixar_dados_ipe()
    
    if df_ipe is None:
        print("Erro ao baixar dados IPE")
        return
    
    # Mostrar empresas únicas para debug
    empresas_unicas = df_ipe['Nome_Companhia'].unique()
    empresas_petro = [emp for emp in empresas_unicas if 'PETRO' in emp.upper()]
    if empresas_petro:
        print(f"\nEmpresas relacionadas encontradas:")
        for emp in empresas_petro[:5]:
            print(f"  - {emp}")
    
    # Filtrar último release
    ultimo_release = filtrar_ultimo_release(df_ipe, EMPRESA_NOME)
    
    if ultimo_release is None:
        print(f"\nNenhum release encontrado para {EMPRESA_NOME}")
        return
    
    # Exibir informações do release
    print("\n=== Último Release Encontrado ===")
    print(f"Empresa: {ultimo_release['Nome_Companhia']}")
    print(f"Data: {ultimo_release['Data_Entrega']}")
    print(f"Assunto: {ultimo_release['Assunto']}")
    print(f"Tipo: {ultimo_release['Tipo']}")
    print(f"Categoria: {ultimo_release.get('Categoria', 'N/A')}")
    
    # Preparar nome do arquivo
    data_str = ultimo_release['Data_Entrega'].strftime('%Y%m%d')
    assunto_limpo = ''.join(c for c in ultimo_release['Assunto'] if c.isalnum() or c in ' -_')[:60]
    nome_arquivo = f"{EMPRESA_NOME}_{data_str}_{assunto_limpo}.pdf"
    
    # Verificar se já existe
    caminho_arquivo = PASTA_PENDING / nome_arquivo
    if caminho_arquivo.exists():
        print(f"\nArquivo já existe: {caminho_arquivo}")
        return
    
    # Baixar PDF
    url_download = ultimo_release['Link_Download']
    
    sucesso = baixar_pdf_direto(url_download, nome_arquivo)
    
    if sucesso:
        print(f"\nPDF baixado com sucesso!")
        
        # Salvar metadados
        metadata = {
            "empresa": ultimo_release['Nome_Companhia'],
            "cnpj": ultimo_release.get('CNPJ_Companhia', ''),
            "data_entrega": ultimo_release['Data_Entrega'].strftime('%Y-%m-%d'),
            "assunto": ultimo_release['Assunto'],
            "tipo": ultimo_release['Tipo'],
            "categoria": ultimo_release.get('Categoria', ''),
            "url_original": url_download,
            "arquivo": nome_arquivo,
            "download_em": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        metadata_file = PASTA_PENDING / f"{nome_arquivo}.metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"Metadados salvos em: {metadata_file}")
    else:
        print("\nErro ao baixar PDF")

if __name__ == "__main__":
    main()