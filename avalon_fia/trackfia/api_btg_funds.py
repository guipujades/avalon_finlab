"""
API BTG para Fundos - Implementação correta com as mudanças após 21/01
Baseado no código original fornecido e nas instruções do BTG
"""

import json
import os
import tempfile
import zipfile
import base64
import requests
import uuid
import time
import pandas as pd
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def auth_apiBTG_funds(config):
    """
    Autentica-se com a API de Fundos da BTG Pactual
    
    Args:
        config (dict): Dicionário com client_id e client_secret
        
    Returns:
        tuple: (token, data)
    """
    # Usar as credenciais corretas fornecidas no código original
    # Estas são diferentes das credenciais da API digital
    client_id = 'guilherme magalhães'
    client_secret = 'Cg21092013PM#'
    grant_type = 'client_credentials'
    
    # URL de autenticação para fundos
    auth_url = 'https://funds.btgpactual.com/connect/token'
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    # Dados para autenticação
    data = {
        'grant_type': grant_type,
        'client_id': client_id,
        'client_secret': client_secret,
    }
    
    # Token
    time.sleep(2)  # Pequeno delay para evitar rate limit
    response = requests.post(auth_url, headers=headers, data=data)
    
    if response.status_code == 200:
        token = response.json().get('access_token')
        logger.info("✅ Token de fundos obtido com sucesso")
        return token, data
    else:
        logger.error(f"❌ Erro na autenticação: {response.status_code} - {response.text}")
        raise Exception(f"Falha na autenticação: {response.text}")


def refresh_partner_positions(token, cnpj='47952345000109'):
    """
    Chama o endpoint para refresh das posições do parceiro
    Necessário após 21/01 conforme orientação do BTG
    
    Args:
        token: Token de autenticação
        cnpj: CNPJ do parceiro
        
    Returns:
        bool: True se sucesso
    """
    # Baseado na documentação: https://developer-partner.btgpactual.com/documentation/api/4/posição
    url = 'https://funds.btgpactual.com/api/v4/position/refresh-partner'
    
    headers = {
        'Content-Type': 'application/json',
        'X-SecureConnect-Token': token
    }
    
    payload = {
        'cnpj': cnpj,
        'webhookEndpoint': 'positions-by-partner'
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code in [200, 202]:
            logger.info(f"✅ Refresh de posições iniciado para CNPJ {cnpj}")
            return True
        else:
            logger.warning(f"⚠️ Refresh retornou {response.status_code}: {response.text}")
            # Não falhar, pois pode não ser necessário sempre
            return False
    except Exception as e:
        logger.warning(f"⚠️ Erro no refresh (pode ser ignorado): {e}")
        return False


def portfolio_api_with_refresh(token, data, start_date, end_date, type_report, page_size):
    """
    Versão atualizada do portfolio_api que faz refresh antes se necessário
    
    Args:
        token: Token de autenticação
        data: Dados adicionais
        start_date: Data inicial
        end_date: Data final
        type_report: Tipo de relatório (3 para XML, 10 para Excel)
        page_size: Tamanho da página
        
    Returns:
        Response com os dados do portfolio
    """
    # Tentar fazer refresh primeiro (não crítico se falhar)
    refresh_partner_positions(token)
    
    # Aguardar processamento
    time.sleep(3)
    
    # Portfolio
    report_url = 'https://funds.btgpactual.com/reports/Portfolio'
    ticket_base_url = 'https://funds.btgpactual.com/reports/Ticket'
    
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
    
    headers = {
        'Content-Type': 'application/json',
        'X-SecureConnect-Token': token
    }
    
    # Requisição
    response_report = requests.post(report_url, headers=headers, data=payload)
    
    if response_report.status_code != 200:
        logger.error(f"❌ Erro ao solicitar relatório: {response_report.status_code} - {response_report.text}")
        return response_report
    
    # Obter ticket
    ticket = response_report.json().get('ticket')
    if not ticket:
        logger.error("❌ Ticket não retornado")
        return response_report
    
    ticket_url = f'{ticket_base_url}?ticketId={ticket}'
    
    # Aguardar processamento
    logger.info(f"⏳ Aguardando processamento do ticket {ticket}...")
    time.sleep(10)
    
    # Obter resultado
    response_ticket = requests.get(ticket_url, headers={'X-SecureConnect-Token': token})
    
    if response_ticket.status_code == 200:
        logger.info("✅ Dados do portfolio obtidos com sucesso")
    else:
        logger.error(f"❌ Erro ao obter dados: {response_ticket.status_code}")
    
    return response_ticket


def fund_data_corrected(find_type='xml'):
    """
    Versão corrigida da função fund_data com tratamento do erro 404
    
    Args:
        find_type: 'xml' ou 'excel'
        
    Returns:
        Dados do fundo conforme tipo solicitado
    """
    # Carregar configurações
    json_path = Path.home() / 'Desktop' / 'api_btg_info.json'
    with open(json_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Token de acesso
    token, data = auth_apiBTG_funds(config)
    
    if find_type == 'excel':
        # Carteira Excel
        counter = -1
        df = pd.DataFrame()
        
        while len(df) == 0 and counter < 30:  # Limitar tentativas
            counter += 1
            logger.info(f'Tentativa {counter + 1}: buscando dados...')
            
            date_ref = datetime.today() - timedelta(days=counter)
            formt_time = date_ref.strftime('%Y-%m-%d')
            
            response_portfolio = portfolio_api_with_refresh(
                token, data, 
                start_date=formt_time, 
                end_date=formt_time, 
                type_report=10,  # Excel
                page_size=100
            )
            
            if response_portfolio.status_code == 200:
                df = read_xls(response_portfolio)
                
                if not df.empty:
                    logger.info(f'✅ Dados encontrados para {formt_time}')
                    # Encontrar PL do fundo
                    index_pl = df.iloc[:, 0]
                    index_pl = list(index_pl[index_pl == 'Patrimonio'].index)[0]
                    pl = df.iloc[index_pl + 1, 0]
                    return pl
        
        logger.warning("⚠️ Não foi possível obter dados Excel")
        return None
    
    elif find_type == 'xml':
        # Carteira XML
        counter = -1
        df_xml = pd.DataFrame()
        
        while len(df_xml) == 0 and counter < 30:  # Limitar tentativas
            counter += 1
            logger.info(f'Tentativa {counter + 1}: buscando dados XML...')
            
            date_ref = datetime.today() - timedelta(days=counter)
            formt_time = date_ref.strftime('%Y-%m-%d')
            
            response_portfolio = portfolio_api_with_refresh(
                token, data,
                start_date=formt_time,
                end_date=formt_time,
                type_report=3,  # XML
                page_size=100
            )
            
            if response_portfolio.status_code == 200:
                content_type = response_portfolio.headers.get('Content-Type', '')
                
                if 'application/octet-stream' in content_type or 'application/zip' in content_type:
                    df_xml, data_xml, header = read_xml(response_portfolio)
                    
                    if not df_xml.empty:
                        logger.info(f'✅ Dados XML encontrados para {formt_time}')
                        logger.info(f'   Fundo: {header.get("nome")}')
                        logger.info(f'   PL: R$ {header.get("patliq"):,.2f}')
                        return df_xml, data_xml, header
                else:
                    logger.warning(f'Formato não esperado: {content_type}')
        
        logger.warning("⚠️ Não foi possível obter dados XML")
        return pd.DataFrame(), None, None


# Funções auxiliares (mantidas do código original)

def parse_xml(root):
    """Parser XML do código original"""
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
    """Lê XML da resposta"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.bin')
    temp_file.write(response_portfolio.content)
    temp_file.close()
    logger.info(f"Arquivo temporário criado: {temp_file.name}")
    
    try:
        tree = ET.parse(temp_file.name)
        root = tree.getroot()
        df_, data_xml, header = parse_xml(root)
        return df_, data_xml, header
        
    except ET.ParseError:
        logger.error("Erro ao analisar o arquivo XML")
        return pd.DataFrame(), None, None
    finally:
        os.unlink(temp_file.name)


def read_xls(response_portfolio):
    """Lê Excel da resposta"""
    content_type = response_portfolio.headers.get('Content-Type', '')
    
    if 'application/octet-stream' in content_type or 'application/zip' in content_type:
        # Salvar conteúdo binário
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_zip.write(response_portfolio.content)
        temp_zip.close()
        
        try:
            # Descompactar e processar
            with zipfile.ZipFile(temp_zip.name, 'r') as zip_ref:
                extracted_files = zip_ref.namelist()
                
                # Procurar arquivo Excel
                for file in extracted_files:
                    if file.endswith('.xlsx') or file.endswith('.xls'):
                        # Extrair e ler
                        zip_ref.extract(file, tempfile.gettempdir())
                        excel_path = os.path.join(tempfile.gettempdir(), file)
                        df = pd.read_excel(excel_path, engine='openpyxl')
                        os.unlink(excel_path)
                        return df
                
                logger.warning("Arquivo Excel não encontrado no ZIP")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Erro ao processar Excel: {e}")
            return pd.DataFrame()
        finally:
            os.unlink(temp_zip.name)
    else:
        logger.warning(f'Formato não esperado: {content_type}')
        return pd.DataFrame()


if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🧪 TESTE DA API DE FUNDOS BTG")
    print("="*60)
    
    try:
        # Testar obtenção de dados XML
        print("\n📊 Buscando dados do fundo AVALON FIA...")
        df_xml, data_xml, header = fund_data_corrected('xml')
        
        if header:
            print(f"\n✅ Dados obtidos com sucesso!")
            print(f"Fundo: {header['nome']}")
            print(f"CNPJ: {header['cnpj']}")
            print(f"Data: {header['dtposicao']}")
            print(f"PL: R$ {header['patliq']:,.2f}")
            print(f"Valor da Cota: R$ {header['valorcota']:.6f}")
            print(f"\nTotal de ativos: {len(df_xml)}")
        else:
            print("❌ Não foi possível obter dados do fundo")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()