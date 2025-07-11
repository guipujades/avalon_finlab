import json
import pandas as pd



def process_account_data(account_data):
    account_summary = json.loads(account_data)
    
    # Inicializa os totais
    total_positions = 0.0
    total_equity = 0.0
    
    # DataFrames para armazenar os dados de cada categoria
    funds_df = pd.DataFrame(columns=['FundName', 'GrossAssetValue'])
    fixed_income_df = pd.DataFrame(columns=['Issuer', 'GrossValue'])
    coe_df = pd.DataFrame(columns=['Issuer', 'GrossValue'])
    equities_df = pd.DataFrame(columns=['Ticker', 'GrossValue'])
    derivatives_df = pd.DataFrame(columns=['Description', 'GrossValue'])
    commodities_df = pd.DataFrame(columns=['Ticker', 'GrossValue'])
    crypto_df = pd.DataFrame(columns=['AssetName', 'GrossValue'])
    cash_df = pd.DataFrame(columns=['Value'])
    pension_df = pd.DataFrame(columns=['FundName', 'GrossAssetValue'])
    credits_df = pd.DataFrame(columns=['ContractCode', 'GrossValue'])
    pending_settlements_df = pd.DataFrame(columns=['Description', 'FinancialValue'])

    # Fundos de Investimento
    investment_funds = account_summary.get('InvestmentFund', []) or []
    for fund in investment_funds:
        fund_name = fund.get('Fund', {}).get('FundName', '')
        acquisitions = fund.get('Acquisition', []) or []
        for acquisition in acquisitions:
            gross_asset_value = float(acquisition.get('GrossAssetValue', 0))
            funds_df = pd.concat([funds_df, pd.DataFrame({
                'FundName': [fund_name],
                'GrossAssetValue': [gross_asset_value]
            })], ignore_index=True)
            total_positions += gross_asset_value

    # Renda Fixa
    fixed_income = account_summary.get('FixedIncome', []) or []
    for bond in fixed_income:
        issuer = bond.get('Issuer', '')
        gross_value = float(bond.get('GrossValue', 0))
        fixed_income_df = pd.concat([fixed_income_df, pd.DataFrame({
            'Issuer': [issuer],
            'GrossValue': [gross_value]
        })], ignore_index=True)
        total_positions += gross_value

    # COEs
    coes = account_summary.get('FixedIncomeStructuredNote', []) or []
    for coe in coes:
        issuer = coe.get('Issuer', '')
        gross_value = float(coe.get('GrossValue', 0))
        coe_df = pd.concat([coe_df, pd.DataFrame({
            'Issuer': [issuer],
            'GrossValue': [gross_value]
        })], ignore_index=True)
        total_positions += gross_value

    # Acoes
    equities = account_summary.get('Equities', []) or []
    for equity in equities:
        stock_positions = equity.get('StockPositions', []) or []
        for stock in stock_positions:
            ticker = stock.get('Ticker', '')
            gross_value = float(stock.get('GrossValue', 0))
            equities_df = pd.concat([equities_df, pd.DataFrame({
                'Ticker': [ticker],
                'GrossValue': [gross_value]
            })], ignore_index=True)
            total_positions += gross_value

    # Derivativos
    derivatives = account_summary.get('Derivative', []) or []
    for derivative in derivatives:
        ndf_positions = derivative.get('NDFPosition', []) or []
        for ndf in ndf_positions:
            description = ndf.get('ReferencedSecurity', '')
            gross_value = float(ndf.get('GrossValue', 0))
            derivatives_df = pd.concat([derivatives_df, pd.DataFrame({
                'Description': [description],
                'GrossValue': [gross_value]
            })], ignore_index=True)
            total_positions += gross_value

    # Commodities
    commodities = account_summary.get('Commodity', []) or []
    for commodity in commodities:
        ticker = commodity.get('Ticker', '')
        gross_value = float(commodity.get('MarketValue', 0))  # Assumindo que usamos MarketValue aqui
        commodities_df = pd.concat([commodities_df, pd.DataFrame({
            'Ticker': [ticker],
            'GrossValue': [gross_value]
        })], ignore_index=True)
        total_positions += gross_value

    # Moedas Digitais
    cryptos = account_summary.get('CryptoCoins', []) or []
    for crypto in cryptos:
        asset_name = crypto.get('asset', {}).get('name', '')
        gross_value = float(crypto.get('grossFinancial', 0))
        crypto_df = pd.concat([crypto_df, pd.DataFrame({
            'AssetName': [asset_name],
            'GrossValue': [gross_value]
        })], ignore_index=True)
        total_positions += gross_value

    # Dinheiro em Conta
    cash = account_summary.get('Cash', []) or []
    for account in cash:
        current_account_value = float(account.get('CurrentAccount', {}).get('Value', 0))
        cash_df = pd.concat([cash_df, pd.DataFrame({
            'Value': [current_account_value]
        })], ignore_index=True)
        total_equity += current_account_value

    # Previ
    pensions = account_summary.get('PensionInformations', []) or []
    for pension in pensions:
        positions = pension.get('Positions', []) or []
        for position in positions:
            fund_name = position.get('FundName', '')
            gross_asset_value = float(position.get('GrossAssetValue', 0))
            pension_df = pd.concat([pension_df, pd.DataFrame({
                'FundName': [fund_name],
                'GrossAssetValue': [gross_asset_value]
            })], ignore_index=True)
            total_positions += gross_asset_value

    # Creditos
    credits_ = account_summary.get('Credits', []) or []
    for credit in credits_:
        loans = credit.get('Loan', []) or []
        for loan in loans:
            contract_code = loan.get('ContractCode', '')
            gross_value = float(loan.get('PrincipalAmount', 0))  # Usando PrincipalAmount se GrossValue não estiver presente
            credits_df = pd.concat([credits_df, pd.DataFrame({
                'ContractCode': [contract_code],
                'GrossValue': [gross_value]
            })], ignore_index=True)
            total_positions += gross_value
            
    # Valores em transito
    pending_settlements = account_summary.get('PendingSettlements', []) or []
    for settlement in pending_settlements:
        for category in ['FixedIncome', 'InvestmentFund', 'Equities', 'Derivative', 'Pension', 'Others']:
            transactions = settlement.get(category, []) or []
            for transaction in transactions:
                description = transaction.get('Description', '')
                financial_value = float(transaction.get('FinancialValue', 0))
                pending_settlements_df = pd.concat([pending_settlements_df, pd.DataFrame({
                    'Description': [description],
                    'FinancialValue': [financial_value]
                })], ignore_index=True)
                total_positions += financial_value

    # PL Total = Total das posicoes + Dinheiro em Conta
    total_equity += total_positions

    return (funds_df, fixed_income_df, coe_df, equities_df, derivatives_df,
            commodities_df, crypto_df, cash_df, pension_df, credits_df, pending_settlements_df, total_positions, total_equity)


def get_total_amount(account_data):
    # Carrega os dados da conta a partir da string JSON
    account_summary = json.loads(account_data)
    
    # Extrai o valor de TotalAmmount
    total_amount = float(account_summary.get('TotalAmmount', 0.0))
    
    return total_amount











