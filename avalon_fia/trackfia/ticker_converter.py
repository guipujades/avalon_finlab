#!/usr/bin/env python3
"""
Conversor de códigos de fundos para tickers padrão
"""

def convert_to_standard_ticker(codigo):
    """
    Converte códigos do tipo MSFTBDR00 para tickers padrão como MSFT34
    """
    # Mapeamento de códigos especiais
    ticker_map = {
        # BDRs - Ações americanas
        'MSFTBDR00': 'MSFT34',
        'AURABDR00': 'AURA33', 
        'DISBBDR00': 'DISB34',
        'NFLXBDR00': 'NFLX34',
        'TSMCBDR00': 'TSMC34',
        'BABABDR00': 'BABA34',
        'MELIBDR00': 'MELI34',
        'GOGLBDR00': 'GOGL34',
        
        # Ações brasileiras - ON
        'CMIGACNOR': 'CMIG4',
        'PSSAACNOR': 'PSSA3',
        'PORTACNOR': 'PORT3',
        'AGROACNOR': 'AGRO3',
        'VIVTACNOR': 'VIVT3',
        'LEVEACNOR': 'LEVE3',
        'CSMGACNOR': 'CSMG3',
        'VLIDACNOR': 'VLID3',
        'BBASACNOR': 'BBAS3',
        'BBSEACNOR': 'BBSE3',
        'CPFEACNOR': 'CPFE3',
        'EGIEACNOR': 'EGIE3',
        'MYPKACNOR': 'MYPK3',
        'ODPVACNOR': 'ODPV3',
        'PETRACNOR': 'PETR4',
        'RADLACNOR': 'RADL3',
        'SBSPACNOR': 'SBSP3',
        'SLCEACNOR': 'SLCE3',
        'TIMSACNOR': 'TIMS3',
        'WEGEACNOR': 'WEGE3',
        
        # Ações preferenciais
        'SAPRACNPR': 'SAPR4'
    }
    
    # Se está no mapeamento, usar conversão
    if codigo in ticker_map:
        return ticker_map[codigo]
    
    # Tentar conversão automática para padrões conhecidos
    codigo_upper = codigo.upper()
    
    # BDRs (terminam com BDR00)
    if codigo_upper.endswith('BDR00'):
        base = codigo_upper.replace('BDR00', '')
        return f"{base}34"
    
    # Ações ON (terminam com ACNOR)
    if codigo_upper.endswith('ACNOR'):
        base = codigo_upper.replace('ACNOR', '')
        return f"{base}3"
    
    # Ações PN (terminam com ACNPR)
    if codigo_upper.endswith('ACNPR'):
        base = codigo_upper.replace('ACNPR', '')
        return f"{base}4"
    
    # Se não conseguir converter, retorna o código original
    return codigo

def get_company_name(ticker):
    """
    Retorna o nome da empresa baseado no ticker
    """
    company_names = {
        'MSFT34': 'Microsoft',
        'AURA33': 'Aura Minerals', 
        'DISB34': 'Discovery',
        'NFLX34': 'Netflix',
        'TSMC34': 'Taiwan Semi',
        'BABA34': 'Alibaba',
        'MELI34': 'MercadoLibre',
        'GOGL34': 'Alphabet',
        'CMIG4': 'Cemig',
        'PSSA3': 'Porto Seguro',
        'PORT3': 'Wilson Sons',
        'AGRO3': 'BrasilAgro',
        'VIVT3': 'Telefônica',
        'LEVE3': 'Metal Leve',
        'CSMG3': 'Copasa',
        'VLID3': 'Valid',
        'BBAS3': 'Banco Brasil',
        'BBSE3': 'BB Seguridade',
        'CPFE3': 'CPFL Energia',
        'EGIE3': 'Engie Brasil',
        'MYPK3': 'Iochpe-Maxion',
        'ODPV3': 'Odontoprev',
        'PETR4': 'Petrobras',
        'RADL3': 'Raia Drogasil',
        'SAPR4': 'Sanepar',
        'SBSP3': 'Sabesp',
        'SLCE3': 'SLC Agrícola',
        'TIMS3': 'TIM',
        'WEGE3': 'WEG'
    }
    
    return company_names.get(ticker, ticker)

def test_converter():
    """Testar o conversor"""
    test_codes = [
        'MSFTBDR00', 'CMIGACNOR', 'PSSAACNOR', 'PORTACNOR',
        'AURABDR00', 'SAPRACNPR', 'PETRACNOR'
    ]
    
    print("🔄 Testando Conversor de Tickers")
    print("=" * 50)
    
    for code in test_codes:
        ticker = convert_to_standard_ticker(code)
        company = get_company_name(ticker)
        print(f"{code} → {ticker} ({company})")

if __name__ == '__main__':
    test_converter()