"""
Esse codigo faz a autenticacao BTG, captura dados principais do FIA Avalon
e esta preparado para a captura de dados de portfolio tanto em excel quanto em xml

Pontos de atencao:
    1. Por vezes a api nao retorna o dado esperado para a data de input (verificar essa falta de dados mais de perto)
"""


import os
import tempfile
import zipfile
import requests
import time
import json
import time
import pandas as pd
import xml.etree.ElementTree as ET


def auth_apiBTG(config):
    """
    Autentica-se com a API da BTG Pactual e obtem um token de acesso.

    Args:
        config (dict): Um dicionario contendo as seguintes chaves:
            - 'CLIENT_ID' ou 'client_id' (str): O ID do cliente para autenticacao da API.
            - 'CLIENT_SECRET' ou 'client_secret' (str): O segredo do cliente para autenticacao da API.
            - 'GRANT_TYPE' ou 'grant_type' (str): O tipo de concessao para autenticacao da API.

    Returns:
        tuple: Uma tupla contendo o token de acesso (str) e os dados (dict) usados para autenticacao.
    """
    
    # Credenciais - aceitar ambos os formatos (maiuscula e minuscula)
    client_id = config.get('CLIENT_ID') or config.get('client_id')
    client_secret = config.get('CLIENT_SECRET') or config.get('client_secret')
    grant_type = config.get('GRANT_TYPE') or config.get('grant_type') or 'client_credentials'

    # URL de autenticação e relatorios
    auth_url = 'https://funds.btgpactual.com/connect/token'
   
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    # Dados para a autenticacao
    data = {
        'grant_type': grant_type,
        'client_id': client_id,
        'client_secret': client_secret,
    }
    
    # Token
    time.sleep(10)
    response = requests.post(auth_url, headers=headers, data=data)
    
    # available_data = response.json()
    token = response.json().get('access_token')
    
    return token, data


def fia_main_info(token, data):
    """
    Recupera informacoes principais do FIA da API da BTG Pactual usando um token de acesso.

    Args:
        token (str): O token de acesso para autenticacao da API.
        data (dict): Os dados usados para autenticacao da API.

    Returns:
        dict: Um dicionario contendo as informacoes do FIA recuperadas da API.
    """
    
    # Info principais FIA
    report_url = 'https://funds.btgpactual.com/reports/Fund'
    ticket_base_url = 'https://funds.btgpactual.com/reports/Ticket'

    payload = json.dumps({
        "contract": {},
        "webhookEndpoint": "string"
    })
    
    # Headers
    report_headers = {
        'Content-Type': 'application/json',
        'X-SecureConnect-Token': token
    }
    
    # Requisicao relatorio
    response_report = requests.post(report_url, headers=report_headers, data=payload)
    ticket = response_report.json().get('ticket')
    ticket_url = f'{ticket_base_url}?ticketId={ticket}'
    
    # Headers para ticket
    ticket_headers = {
        'Content-Type': 'application/json',
        'X-SecureConnect-Token': token
    }
    
    # Dados FIA Avalon
    time.sleep(10)
    response_ticket = requests.get(ticket_url, headers=ticket_headers)
    info = response_ticket.json()
    
    return info


def get_position_by_partner_refresh(token, cnpj='47952345000109'):
    """
    Chama o endpoint get-position-by-partner-refresh para atualizar as posicoes do parceiro.
    Necessario apos 21/01 para garantir que as posicoes estejam atualizadas para D0.

    Args:
        token (str): O token de acesso para autenticacao da API.
        cnpj (str): CNPJ do parceiro (padrao: CNPJ da Avalon).

    Returns:
        dict: Resposta da API com status da atualizacao.
    """
    
    # URL do endpoint para refresh de posicoes - corrigida baseando-se no padrao da API BTG
    refresh_url = 'https://funds.btgpactual.com/reports/PositionByPartnerRefresh'
    
    headers = {
        'Content-Type': 'application/json',
        'X-SecureConnect-Token': token
    }
    
    payload = json.dumps({
        'contract': {
            'cnpj': cnpj
        },
        'webhookEndpoint': 'positions-by-partner'  # Webhook conforme documentacao
    })
    
    # Fazer a requisicao de refresh
    response = requests.post(refresh_url, headers=headers, data=payload)
    
    if response.status_code == 200:
        print(f"Refresh de posicoes iniciado com sucesso para CNPJ {cnpj}")
        return response.json()
    else:
        print(f"Erro ao iniciar refresh: {response.status_code} - {response.text}")
        return None


def get_partner_position(token, cnpj='47952345000109'):
    """
    Recupera as posicoes do parceiro usando o endpoint get-partner-position.
    Deve ser chamado apos get-position-by-partner-refresh.

    Args:
        token (str): O token de acesso para autenticacao da API.
        cnpj (str): CNPJ do parceiro (padrao: CNPJ da Avalon).

    Returns:
        requests.Response: O objeto de resposta HTTP contendo os dados ZIP das posicoes.
    """
    
    # URL do endpoint para obter posicoes - seguindo padrao de tickets
    position_url = 'https://funds.btgpactual.com/reports/PartnerPosition'
    ticket_base_url = 'https://funds.btgpactual.com/reports/Ticket'
    
    headers = {
        'Content-Type': 'application/json',
        'X-SecureConnect-Token': token
    }
    
    payload = json.dumps({
        'contract': {
            'cnpj': cnpj
        }
    })
    
    # Fazer a requisicao das posicoes
    response = requests.post(position_url, headers=headers, data=payload)
    
    if response.status_code == 200:
        # Obter ticket da resposta
        ticket = response.json().get('ticket')
        if ticket:
            # Aguardar processamento
            time.sleep(5)
            
            # Buscar resultado com o ticket
            ticket_url = f'{ticket_base_url}?ticketId={ticket}'
            ticket_response = requests.get(ticket_url, headers={'X-SecureConnect-Token': token})
            
            if ticket_response.status_code == 200:
                print(f"Posicoes recuperadas com sucesso para CNPJ {cnpj}")
                return ticket_response
            else:
                print(f"Erro ao recuperar resultado do ticket: {ticket_response.status_code}")
                return None
        else:
            print("Resposta sem ticket")
            return response
    else:
        print(f"Erro ao recuperar posicoes: {response.status_code} - {response.text}")
        return None


def portfolio_api(token, data, start_date, end_date, type_report, page_size):
    """
    Recupera informacoes de portfolio da API da BTG Pactual usando um token de acesso e parametros especificados.

    Args:
        token (str): O token de acesso para autenticacao da API.
        data (dict): Os dados usados para autenticacao da API.
        start_date (str): A data de início para o relatorio de portfolio (formato: YYYY-MM-DD).
        end_date (str): A data de termino para o relatorio de portfolio (formato: YYYY-MM-DD).
        type_report (str): O tipo de relatorio solicitado.
        page_size (int): O numero de resultados por pagina.

    Returns:
        requests.Response: O objeto de resposta HTTP contendo os dados do portfolio.
    """
    
    # Portfolio
    report_url = 'https://funds.btgpactual.com/reports/Portfolio'
    ticket_base_url = 'https://funds.btgpactual.com/reports/Ticket'
    scope = 'reports.position'
    
    data['scope'] = scope
    payload = json.dumps({
        'contract': {
            'startDate': start_date,
            'endDate': end_date,
            'typeReport': type_report,
            'fundName': 'AVALON FIA'
        },
        
        'pageSize': page_size,
        'webhookEndpoint': 'string'
    })
    
    # Headers 
    report_headers = {
        'Content-Type': 'application/json',
        'X-SecureConnect-Token': token
    }
    
    # Requisicao 
    response_report = requests.post(report_url, headers=report_headers, data=payload)
    
    # Requisicao de relatorio
    ticket = response_report.json().get('ticket')
    ticket_url = f'{ticket_base_url}?ticketId={ticket}'
    
    # Headers
    ticket_headers = {
        'Content-Type': 'application/json',
        'X-SecureConnect-Token': token
    }
    
    # Carteira Avalon
    time.sleep(10)
    response_ticket = requests.get(ticket_url, headers=ticket_headers)
    
    return response_ticket


def parse_xml(root):
    """
    Analisa uma arvore XML para extrair dados financeiros em formatos estruturados.

    Args:
        root (xml.etree.ElementTree.Element): O elemento raiz da arvore XML a ser analisado.

    Returns:
        tuple: Uma tupla contendo:
            - df (pandas.DataFrame): Um DataFrame contendo os dados XML analisados.
            - data_xml (list): Uma lista de dicionarios representando os dados XML extraidos.
            - header_data (dict): Um dicionarios contendo informacoes do cabeçalho.
    """

    data_xml = []

    fundo = root.find('fundo')
    header = fundo.find('header')

    # Extrair dados do header
    header_data = {
        'isin': header.find('isin').text,
        'cnpj': header.find('cnpj').text,
        'nome': header.find('nome').text,
        'dtposicao': header.find('dtposicao').text,
        'nomeadm': header.find('nomeadm').text,
        'cnpjadm': header.find('cnpjadm').text,
        'nomegestor': header.find('nomegestor').text,
        'cnpjgestor': header.find('cnpjgestor').text,
        'nomecustodiante': header.find('nomecustodiante').text,
        'cnpjcustodiante': header.find('cnpjcustodiante').text,
        'valorcota': float(header.find('valorcota').text),
        'quantidade': float(header.find('quantidade').text),
        'patliq': float(header.find('patliq').text),
        'valorativos': float(header.find('valorativos').text),
        'valorreceber': float(header.find('valorreceber').text),
        'valorpagar': float(header.find('valorpagar').text),
        'vlcotasemitir': float(header.find('vlcotasemitir').text),
        'vlcotasresgatar': float(header.find('vlcotasresgatar').text),
        'codanbid': header.find('codanbid').text,
        'tipofundo': header.find('tipofundo').text,
        'nivelrsc': header.find('nivelrsc').text
    }
    
    # Extrair dados dos títulos públicos
    for titpublico in fundo.findall('titpublico'):
        data_xml.append({
            'tipo': 'titpublico',
            'isin': titpublico.find('isin').text,
            'codativo': titpublico.find('codativo').text,
            'cusip': titpublico.find('cusip').text,
            'dtemissao': titpublico.find('dtemissao').text,
            'dtoperacao': titpublico.find('dtoperacao').text,
            'dtvencimento': titpublico.find('dtvencimento').text,
            'qtdisponivel': int(titpublico.find('qtdisponivel').text),
            'qtgarantia': int(titpublico.find('qtgarantia').text),
            'depgar': int(titpublico.find('depgar').text),
            'pucompra': float(titpublico.find('pucompra').text),
            'puvencimento': float(titpublico.find('puvencimento').text),
            'puposicao': float(titpublico.find('puposicao').text),
            'puemissao': float(titpublico.find('puemissao').text),
            'principal': float(titpublico.find('principal').text),
            'tributos': float(titpublico.find('tributos').text),
            'valorfindisp': float(titpublico.find('valorfindisp').text),
            'valorfinemgar': float(titpublico.find('valorfinemgar').text),
            'coupom': float(titpublico.find('coupom').text),
            'indexador': titpublico.find('indexador').text,
            'percindex': int(titpublico.find('percindex').text),
            'caracteristica': titpublico.find('caracteristica').text,
            'percprovcred': int(titpublico.find('percprovcred').text),
            'classeoperacao': titpublico.find('classeoperacao').text,
            'idinternoativo': titpublico.find('idinternoativo').text,
            'nivelrsc': titpublico.find('nivelrsc').text
        })

    # Extrair dados das ações
    for acao in fundo.findall('acoes'):
        data_xml.append({
            'tipo': 'acoes',
            'isin': acao.find('isin').text,
            'cusip': acao.find('cusip').text,
            'codativo': acao.find('codativo').text,
            'qtdisponivel': int(acao.find('qtdisponivel').text),
            'lote': int(acao.find('lote').text),
            'qtgarantia': int(acao.find('qtgarantia').text),
            'valorfindisp': float(acao.find('valorfindisp').text),
            'valorfinemgar': float(acao.find('valorfinemgar').text),
            'tributos': float(acao.find('tributos').text),
            'puposicao': float(acao.find('puposicao').text),
            'percprovcred': int(acao.find('percprovcred').text),
            'tpconta': int(acao.find('tpconta').text),
            'classeoperacao': acao.find('classeoperacao').text,
            'dtvencalug': acao.find('dtvencalug').text,
            'txalug': float(acao.find('txalug').text),
            'cnpjinter': acao.find('cnpjinter').text
        })

    # Extrair dados das provisões
    for provisao in fundo.findall('provisao'):
        data_xml.append({
            'tipo': 'provisao',
            'codprov': provisao.find('codprov').text,
            'credeb': provisao.find('credeb').text,
            'dt': provisao.find('dt').text,
            'valor': float(provisao.find('valor').text)
        })

    df = pd.DataFrame(data_xml)

    return df, data_xml, header_data


def read_xml(response_portfolio):
    """
    Le e analisa o conteudo XML de uma resposta de portfolio, salvando-o temporariamente e extraindo dados relevantes.

    Args:
        response_portfolio (requests.Response): O objeto de resposta HTTP contendo o conteudo XML.

    Returns:
        tuple: Uma tupla contendo:
            - df_ (pandas.DataFrame): Um DataFrame contendo dados XML analisados.
            - data_xml (list): Uma lista de dicionarios representando dados XML.
            - header (dict): Um dicionario contendo informacoes do cabeçalho.
    """
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.bin')
    temp_file.write(response_portfolio.content)
    temp_file.close()
    print(f"Conteúdo salvo como {temp_file.name}")
    
    try:
        tree = ET.parse(temp_file.name)
        root = tree.getroot()
        df_, data_xml, header = parse_xml(root)
        return df_, data_xml, header
        
    except ET.ParseError:
        print("Erro ao analisar o arquivo XML.")
        return pd.DataFrame(), None, None


def process_partner_position_zip(response_portfolio):
    """
    Processa o arquivo ZIP retornado pelo endpoint get-partner-position.
    
    Args:
        response_portfolio (requests.Response): O objeto de resposta HTTP contendo o arquivo ZIP.
    
    Returns:
        tuple: Uma tupla contendo os DataFrames e dados processados.
    """
    
    content_type = response_portfolio.headers.get('Content-Type')
    
    if 'application/zip' in content_type or 'application/octet-stream' in content_type:
        # Salvar o ZIP em arquivo temporario
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_zip.write(response_portfolio.content)
        temp_zip.close()
        print(f"Arquivo ZIP de posicoes salvo como {temp_zip.name}")
        
        try:
            # Extrair o ZIP
            with zipfile.ZipFile(temp_zip.name, 'r') as zip_ref:
                extracted_files = zip_ref.namelist()
                extract_dir = tempfile.mkdtemp()
                zip_ref.extractall(extract_dir)
                
                # Procurar por arquivos XML dentro do ZIP
                for file in extracted_files:
                    if file.endswith('.xml'):
                        xml_path = os.path.join(extract_dir, file)
                        print(f"Processando arquivo XML: {file}")
                        
                        # Analisar o XML
                        tree = ET.parse(xml_path)
                        root = tree.getroot()
                        df_, data_xml, header = parse_xml(root)
                        
                        # Limpar arquivos temporarios
                        os.unlink(temp_zip.name)
                        
                        return df_, data_xml, header
                
                # Se nao encontrou XML, tentar outros formatos
                print("Nenhum arquivo XML encontrado no ZIP")
                return pd.DataFrame(), None, None
                
        except Exception as e:
            print(f"Erro ao processar arquivo ZIP: {e}")
            return pd.DataFrame(), None, None
    else:
        print(f"Formato de resposta inesperado: {content_type}")
        return pd.DataFrame(), None, None
    

def read_xls(response_portfolio):
    """
    Le e analisa o conteudo Excel de uma resposta de portfolio, salvando-o temporariamente e extraindo dados relevantes.

    Args:
        response_portfolio (requests.Response): O objeto de resposta HTTP contendo o conteudo Excel.

    Returns:
        pandas.DataFrame: Um DataFrame contendo os dados do arquivo Excel extraido e analisado.
    """
    
    content_type = response_portfolio.headers.get('Content-Type')
    if 'application/octet-stream' in content_type or 'application/zip' in content_type:
        # Salvar conteúdo binário em um arquivo temporário
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_zip.write(response_portfolio.content)
        temp_zip.close()
        print(f"Conteúdo salvo como {temp_zip.name}")
    
        # Descompactar o arquivo ZIP e identificar o arquivo Excel
        with zipfile.ZipFile(temp_zip.name, 'r') as zip_ref:
            extracted_files = zip_ref.namelist()
            zip_ref.extractall(tempfile.gettempdir())
    
            # Procurar o arquivo Excel principal
            excel_file_path = None
            for file in extracted_files:
                if file.endswith('xl/worksheets/sheet1.xml'):
                    excel_file_path = os.path.join(tempfile.gettempdir(), 'xl', 'worksheets', 'sheet1.xml')
                    break
    
            if excel_file_path:
                # Reconstruir o caminho do arquivo Excel
                reconstructed_excel_path = os.path.join(tempfile.gettempdir(), 'reconstructed.xlsx')
                with zipfile.ZipFile(reconstructed_excel_path, 'w') as new_zip:
                    for file in extracted_files:
                        new_zip.write(os.path.join(tempfile.gettempdir(), file), file)
                # Ler o arquivo Excel com pandas
                df = pd.read_excel(reconstructed_excel_path, engine='openpyxl')

            else:
                print('Arquivo Excel não encontrado...')
                
            return df
    
    else:
        print('Resposta não condizente com captura... Conteúdo:')
        # print(response_portfolio.text)
        return pd.DataFrame()
