import os
import time
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np
from fund_report_utils import (
    initialize_mt5, 
    fund_data,
    run_manager_xml,
    calculate_pnl,
    calculate_var,
    calculate_daily_change,
    calculate_portfolio_change_pm,
    calculate_weekly_change,
    calculate_weeklyAssets_change,
    calculate_monthlyAssets_change,
    get_real_time_prices,
    get_real_time_prices_options_stocks,
    id_options,
    save_pickle,
    load_pickle,
    find_invalid_floats,
    clean_data_for_json,
    convert_timestamps_to_strings,
    dataframe_to_dict,
    dataframe_to_dict_ts,
    generate_html_report,
)
from scipy.stats import norm

def generate_portfolio_report(manual_insert=None):
    """
    Gera um relatório detalhado do portfólio e salva em HTML
    
    Args:
        manual_insert (DataFrame, optional): Operações manuais para incluir. Defaults to None.
    
    Returns:
        dict: Dados do portfólio processados
    """
    # Datas
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Diretório para os arquivos pickle
    pickle_dir = Path(Path.home(), 'Documents', 'GitHub', 'database', 'dados_api')
    os.makedirs(pickle_dir, exist_ok=True)
    
    df_xml_path = os.path.join(pickle_dir, f'df_xml_{current_date}.pkl')
    data_xml_path = os.path.join(pickle_dir, f'data_xml_{current_date}.pkl')
    header_path = os.path.join(pickle_dir, f'header_{current_date}.pkl')
    
    # Verifica se os arquivos pickle do dia já existem
    if os.path.exists(df_xml_path) and os.path.exists(data_xml_path) and os.path.exists(header_path):
        df_xml = load_pickle(df_xml_path)
        data_xml = load_pickle(data_xml_path)
        header = load_pickle(header_path)
        print('Dados carregados dos arquivos serializados.')
    
    else:
        # Capturar dados da API
        df_xml, data_xml, header = fund_data(find_type='xml')
        save_pickle(df_xml, df_xml_path)
        save_pickle(data_xml, data_xml_path)
        save_pickle(header, header_path)
        print('Dados capturados da API e salvos em arquivos serializados.')
    
    data_api = header['dtposicao']
    print(f'Data dos dados capturados da API: {data_api}')
    
    pl_fundo = header['patliq']
    data_dados = pd.to_datetime(header['dtposicao']).strftime('%d/%m/%Y')
    cota_fia = header['valorcota']
    a_receber = header['valorreceber']
    a_pagar = header['valorpagar']
    
    # Puxar dados locais
    portfolio, df_original_table = run_manager_xml()
    
    # Comparação com dados de carteira
    try:
        df_comp = pd.read_excel(Path(Path.home(), 'Documents', 'GitHub', 'database', 'carteira_comp', 'Carteira_AVALON_FIA_31_10_2024.xlsx'))
        df_comp.iloc[:, 0] = df_comp.iloc[:, 0].str.strip()
        df_comp.iloc[:,3] = df_comp.iloc[:,3].str.strip()
        
        find_cols1 = df_comp[(df_comp.iloc[:,0] == 'AVALONCAP')].iloc[0]
        find_cols1 = int(float(find_cols1.name) - 1)
        find_cols2 = df_comp[(df_comp.iloc[:,0] == 'SB')].iloc[-1]
        find_cols2 = int(float(find_cols2.name) + 1)

        df_comp = df_comp.iloc[find_cols1:find_cols2, :]
        df_comp.reset_index(inplace=True, drop=True)
        df_comp.columns = list(df_comp.iloc[0,:])
        df_comp = df_comp.drop(index=0).reset_index(drop=True)
        
        # Verificar símbolos que não constam no portfólio
        for symbol in list(df_comp.iloc[:,3]):
            if symbol not in list(portfolio.keys()):
                print(f"{symbol} not in portfolio")
    except Exception as e:
        print(f"Erro ao processar arquivo de comparação: {e}")
    
    # Alterar dados para inclusão de operações manuais
    if manual_insert is not None and len(manual_insert) > 0:
        from fund_report_utils import calculate_PnL_averagePrices
        df_original_table = pd.concat([df_original_table, manual_insert], axis=0)
        portfolio, df_original_table = calculate_PnL_averagePrices(df_original_table)
    
    # Obter preços em tempo real
    counter = 0
    last_prices = {}
    prices = {}
    
    while len(last_prices) == 0 and counter < 5:
        last_prices, prices = get_real_time_prices(portfolio)
        counter += 1
        if len(last_prices) == 0:
            time.sleep(2)
    
    pnl = calculate_pnl(portfolio, last_prices)

    # Base cálculos posições
    df = pd.DataFrame.from_dict(pnl, orient='index')
    df['pcts_port'] = (df['current_value'] / np.sum(df['current_value'])) * 100
    df['percentage_change'] = df['percentage_change'] * 100
    df['impact'] = df['percentage_change'] * df['pcts_port'] / 100

    # PROCESSO 1: Lidar com ações em carteira
    df_stocks = df[df.index.str.len() < 7]
    weights = df_stocks['pcts_port'].values / 100
    
    # Variação de preços
    df_var = pd.DataFrame({k: v['Fechamento'] for k,v in prices.items() if k in list(df_stocks.index)}, 
                        columns=[i for i in prices.keys() if i in list(df_stocks.index)])
    df_var.index = pd.to_datetime(df_var.index)
    
    # Calcular VaR
    portfolio_var_1_week = calculate_var(df_var, weights, 5)
    portfolio_var_1_month = calculate_var(df_var, weights, 21)
    
    # VaR individual
    VaR_1_week = []
    VaR_1_month = []
    tickers = list(df_stocks.index)
    for ticker in tickers:
        individual_returns = np.log(1 + df_var[ticker].pct_change(fill_method=None))
        individual_std_dev = individual_returns.std() * np.sqrt(252)
        var_1_week = individual_std_dev * norm.ppf(0.95) * np.sqrt(5 / 252)
        var_1_month = individual_std_dev * norm.ppf(0.95) * np.sqrt(21 / 252)
        VaR_1_week.append(var_1_week * 100)  # Convertendo para porcentagem
        VaR_1_month.append(var_1_month * 100)
 
    df_stocks['VaR 1 semana'] = VaR_1_week
    df_stocks['VaR 1 mês'] = VaR_1_month
    
    # Variação dos ativos
    daily_change = calculate_daily_change(df_var).dropna()
    weekly_change = calculate_weeklyAssets_change(df_var).dropna()
    monthly_change = calculate_monthlyAssets_change(df_var).dropna()
    
    # Combinar dados de variações em um DataFrame
    change_df = pd.DataFrame({
        'Retorno Diário (%)': daily_change,
        'Retorno Semanal (%)': weekly_change,
        'Retorno Mensal (%)': monthly_change
    })

    # Dataframe para variação do portfólio
    df_var_port = pd.DataFrame({k: v['Fechamento'] for k,v in prices.items()}, columns=df.index)
    df_var_port.index = pd.to_datetime(df_var_port.index)
    weights_total = df['pcts_port'].values / 100
    
    # Variação portfólio
    portfolio_change = calculate_portfolio_change_pm(df)
    portfolio_change_stocks = calculate_portfolio_change_pm(df_stocks)

    portfolio_daily_change = calculate_weekly_change(df_var_port, weights_total, days=1)
    portfolio_weekly_change = calculate_weekly_change(df_var_port, weights_total)
    
    # DataFrame para uso em gráficos
    df_chart_usage = df_stocks.copy()
    df_chart_usage.columns = ['Preço', 'Quantidade', 'PM', 'Financeiro', 'PnL', 'Variação', 'Peso', 'Variação ponderada',
                  'VaR semanal', 'VaR mensal']
    df_chart_usage = df_chart_usage.apply(lambda x: round(x,2))
    df_chart_usage = df_chart_usage.sort_values(by='PnL', ascending=False)

    # Enquadramento do fundo
    enquadramento = df['current_value'].sum() / pl_fundo
    
    # Base tabela opções
    opts_df = df[df.index.str.len() >= 7]
    impact_by_date = {}
    
    # Lidar com opções se houverem
    limits_der = 0.0
    df_opts_table_dict = {}
    
    if len(opts_df) > 0:
        # Lidar com dados de opções
        opts_id = list(opts_df.index)
        opts_database = id_options(opts_id)
        
        if not opts_database.empty:
            opts_database_find_data = opts_database[opts_database.ticker.isin(list(opts_df.index))]
            opts_database = opts_database[['stock', 'ticker', 'tipo', 'vencimento', 'strike']]
        
            # Base preços opções
            opts_df.index.name = 'ticker'
            df_opts = pd.merge(opts_df.reset_index(), opts_database, on='ticker', how='inner')
            
            if not df_opts.empty:
                today = datetime.today()
                today = datetime.strftime(today, format='%Y-%m-%d')
                
                df_opts = df_opts[df_opts.vencimento > today]
                
                if not df_opts.empty:
                    prices_assets_opts = get_real_time_prices_options_stocks(df_opts)
                    
                    # Preço atual dos ativos subjacentes
                    df_opts['current_price_stock'] = df_opts['stock'].map(prices_assets_opts)
                
                    # Limites derivativos
                    limits_der = np.sum(abs(df_opts['current_value'])) / pl_fundo
                
                    # Valor financeiro das ações
                    financial_sum = df_chart_usage['Financeiro'].sum()
                    
                    # Calcula o impacto financeiro para cada data de vencimento
                    for _, row in df_opts.iterrows():
                        expiry_date = row['vencimento']
                        tipo = row['tipo']
                        quantity = row['quantity']
                        strike = row['strike']
                        
                        if expiry_date not in impact_by_date:
                            impact_by_date[expiry_date] = 0
                    
                        if tipo == 'p':  # Put
                            if quantity < 0:  # Vendendo Put
                                impact_by_date[expiry_date] += abs(quantity) * strike
                            else:  # Comprando Put
                                impact_by_date[expiry_date] -= abs(quantity) * strike
                        elif tipo == 'c':  # Call
                            if quantity < 0:  # Vendendo Call
                                impact_by_date[expiry_date] -= abs(quantity) * strike
                            else:  # Comprando Call
                                impact_by_date[expiry_date] += abs(quantity) * strike
                    
                    # Adiciona o impacto financeiro ao valor financeiro das ações
                    impact_by_date = {date: financial_sum + impact for date, impact in impact_by_date.items()}
                    
                    # Tabela de operações com opções
                    df_opts.set_index('ticker', inplace=True)
                    df_opts = df_opts.sort_values(by='profit_loss', ascending=False)
                    df_opts.columns = ['Preço Atual', 'Quantidade', 'PM', 'Valor Atual', 'PnL', 'Variação', 'Peso', 
                                      'Variação ponderada', 'Ativo Subjacente', 'Tipo', 'Vencimento', 'Strike', 'Preço Atual Ativo']
                    
                    numeric_cols = df_opts.select_dtypes(include=[np.number]).columns
                    df_opts[numeric_cols] = df_opts[numeric_cols].round(2)
                    
                    df_opts_table = df_opts.copy()
                    df_opts_table['Vencimento'] = df_opts_table['Vencimento'].astype(str)
                    df_opts_table_dict = dataframe_to_dict(df_opts_table)

    # Converter dados para o relatório
    df_dict = dataframe_to_dict_ts(df_original_table)
    df_stocks_dict = dataframe_to_dict(df_stocks)
    change_df_dict = dataframe_to_dict(change_df)
    impact_by_date_str_keys = convert_timestamps_to_strings(impact_by_date)
    df_chart_usage_dict = dataframe_to_dict(df_chart_usage)
    
    # Preparar dados para o relatório
    portfolio_data = {
        'current_time': current_time,
        'data': data_dados,
        'current_pl': pl_fundo,
        'cota': cota_fia,
        'receber': a_receber,
        'pagar': a_pagar,
        'enquadramento': enquadramento,
        'limits_der': limits_der,
        'portfolio_change': portfolio_change,
        'portfolio_change_stocks': portfolio_change_stocks,
        'portfolio_daily_change': portfolio_daily_change,
        'portfolio_weekly_change': portfolio_weekly_change,
        'portfolio_var_1_week': portfolio_var_1_week,
        'portfolio_var_1_month': portfolio_var_1_month,
        'df_stocks_dict': df_stocks_dict,
        'change_df_dict': change_df_dict,
        'impact_by_date': impact_by_date_str_keys,
        'df_chart_usage': df_chart_usage_dict,
        'df_opts_table': df_opts_table_dict,
        'portfolio': portfolio,
        'df': df_dict
    }
    
    # Verificar valores inválidos
    invalid_floats = find_invalid_floats(portfolio_data)
    if invalid_floats:
        print("Found invalid float values at the following paths:")
        for path, value in invalid_floats:
            print(f"Path: {path}, Value: {value}")
            
    # Limpar dados para o relatório
    portfolio_data = clean_data_for_json(portfolio_data)
    
    # Gerar o relatório HTML
    report_path = generate_html_report(portfolio_data)
    
    return portfolio_data, report_path


if __name__ == "__main__":
    # Iniciar o MT5
    initialize_mt5()
    
    # Gerar relatório
    portfolio_data, report_path = generate_portfolio_report()
    
    print(f"Relatório gerado com sucesso em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Arquivo salvo em: {report_path}")



    