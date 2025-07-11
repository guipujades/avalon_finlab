import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Definir o período de análise
end_date = datetime.now()
start_date = end_date - timedelta(days=5*365)

# Baixar todos os dados de uma vez
tickers = ['VUAA.L', '^SP500TR']
data = yf.download(tickers, start=start_date, end=end_date)

# Analisar a estrutura do MultiIndex
print("Estrutura do DataFrame:")
print(f"Nomes dos níveis: {data.columns.names}")
print(f"Níveis: {data.columns.levels}")
print("\nColunas disponíveis:")
print(data.columns)

# Método correto para extrair os dados de fechamento
# O MultiIndex tem níveis ['Price', 'Ticker'], então precisamos acessar corretamente
if 'Price' in data.columns.names:
    # Se o nível é 'Price', usamos esse nome
    comparison_df = data.xs('Close', axis=1, level='Price')
else:
    # Se não, acessamos diretamente
    comparison_df = data['Close']

# Renomear as colunas para nomes mais simples
renaming_dict = {
    'VUAA.L': 'VUAA',
    '^GSPC': 'S&P 500',
    '^SP500TR': 'S&P 500 TR'
}
comparison_df.columns = [renaming_dict[col] if col in renaming_dict else col for col in comparison_df.columns]

print("\nDataFrame simplificado:")
print(comparison_df.head())
print(f"Colunas: {comparison_df.columns}")

# Remover linhas com valores ausentes
comparison_df = comparison_df.dropna()

# Normalizar os dados para base 100
comparison_normalized = comparison_df.copy()
for col in comparison_normalized.columns:
    comparison_normalized[col] = (comparison_normalized[col] / comparison_normalized[col].iloc[0]) * 100

# Plotar o gráfico comparativo
plt.figure(figsize=(12, 8))
for col in comparison_normalized.columns:
    plt.plot(comparison_normalized.index, comparison_normalized[col], label=col, linewidth=2)

plt.title('Comparação de Performance: VUAA ETF vs S&P 500 vs S&P 500 TR (Base 100)', fontsize=14)
plt.xlabel('Data', fontsize=12)
plt.ylabel('Valor Indexado (Base 100)', fontsize=12)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# Calcular retornos e métricas
print("\n=== Análise de Performance ===")
for col in comparison_df.columns:
    if len(comparison_df[col]) > 0:
        # Retorno total
        total_return = (comparison_df[col].iloc[-1] / comparison_df[col].iloc[0] - 1) * 100
        
        # Período em anos
        years = (comparison_df.index[-1] - comparison_df.index[0]).days / 365.25
        
        # Retorno anualizado
        annual_return = ((1 + total_return/100) ** (1/years) - 1) * 100
        
        # Volatilidade
        daily_returns = comparison_df[col].pct_change().dropna()
        volatility = daily_returns.std() * (252 ** 0.5) * 100
        
        print(f"\n{col}:")
        print(f"Retorno Total: {total_return:.2f}%")
        print(f"Retorno Anualizado: {annual_return:.2f}%")
        print(f"Volatilidade Anualizada: {volatility:.2f}%")


# Criar DataFrame de retornos mensais
monthly_prices = comparison_df.resample('M').last()
monthly_returns = monthly_prices.pct_change().dropna()

monthly_returns_cum = monthly_returns.add(1).cumprod()-1

print("\n=== Retornos Mensais ===")
print(monthly_returns)

# Visualizar retornos mensais
plt.figure(figsize=(12, 8))
for col in monthly_returns.columns:
    plt.plot(monthly_returns.index, monthly_returns[col] * 100, label=col, linewidth=2)

plt.title('Retornos Mensais: VUAA ETF vs S&P 500 vs S&P 500 TR', fontsize=14)
plt.xlabel('Data', fontsize=12)
plt.ylabel('Retorno Mensal (%)', fontsize=12)
plt.legend()
plt.grid(True, alpha=0.3)
plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
plt.tight_layout()
plt.show()

# Estatísticas básicas dos retornos mensais
print("\n=== Estatísticas dos Retornos Mensais ===")
for col in monthly_returns.columns:
    print(f"\n{col}:")
    print(f"Média mensal: {monthly_returns[col].mean() * 100:.2f}%")
    print(f"Desvio padrão mensal: {monthly_returns[col].std() * 100:.2f}%")
    
    
    
# Calcular retornos anuais
yearly_data = {}

# Agrupar por ano
for year in comparison_df.index.year.unique():
    year_df = comparison_df[comparison_df.index.year == year]
    
    if len(year_df) > 0:
        # Calcular retorno anual usando primeiro e último valor do ano
        returns = {}
        
        for col in ['VUAA', 'S&P 500 TR']:
            if col in year_df.columns:
                first_value = year_df[col].iloc[0]
                last_value = year_df[col].iloc[-1]
                yearly_return = (last_value / first_value - 1) * 100
                returns[col] = yearly_return
            else:
                returns[col] = None
        
        if returns['VUAA'] is not None and returns['S&P 500 TR'] is not None:
            difference = returns['VUAA'] - returns['S&P 500 TR']
            yearly_data[year] = {
                'VUAA': returns['VUAA'],
                'S&P 500 TR': returns['S&P 500 TR'],
                'Diferença': difference
            }

# Criar DataFrame dos retornos anuais
yearly_returns = pd.DataFrame.from_dict(yearly_data, orient='index')
yearly_returns.sort_index(ascending=False, inplace=True)

# Calcular YTD (Year-to-date) para 2025
current_year = datetime.now().year
if current_year in comparison_df.index.year:
    ytd_df = comparison_df[comparison_df.index.year == current_year]
    if len(ytd_df) > 0:
        ytd_returns = {}
        for col in ['VUAA', 'S&P 500 TR']:
            if col in ytd_df.columns:
                first_value = ytd_df[col].iloc[0]
                last_value = ytd_df[col].iloc[-1]
                ytd_return = (last_value / first_value - 1) * 100
                ytd_returns[col] = ytd_return
        
        if ytd_returns['VUAA'] is not None and ytd_returns['S&P 500 TR'] is not None:
            ytd_difference = ytd_returns['VUAA'] - ytd_returns['S&P 500 TR']
            yearly_returns.loc[f'YTD ({current_year})'] = {
                'VUAA': ytd_returns['VUAA'],
                'S&P 500 TR': ytd_returns['S&P 500 TR'],
                'Diferença': ytd_difference
            }

# Formatar a tabela para exibição
print("\n=== Comparação Anual: VUAA vs S&P 500 TR ===")
print("Período         VUAA        S&P 500 TR    Diferença")
print("-" * 50)

# Ordenar para ter YTD primeiro, depois anos em ordem decrescente
index_order = []
for idx in yearly_returns.index:
    if 'YTD' in str(idx):
        index_order.insert(0, idx)
    else:
        index_order.append(idx)

ordered_returns = yearly_returns.loc[index_order]

for idx, row in ordered_returns.iterrows():
    if pd.notna(row['VUAA']) and pd.notna(row['S&P 500 TR']):
        print(f"{str(idx):<12} {row['VUAA']:>8.2f}%   {row['S&P 500 TR']:>8.2f}%   {row['Diferença']:>8.2f}%")
    else:
        print(f"{str(idx):<12}     —           —           —")

# Calcular médias
if len(yearly_returns) > 0:
    mean_vuaa = yearly_returns['VUAA'].mean()
    mean_sp500tr = yearly_returns['S&P 500 TR'].mean()
    mean_diff = yearly_returns['Diferença'].mean()
    
    print("-" * 50)
    print(f"{'Média':<12} {mean_vuaa:>8.2f}%   {mean_sp500tr:>8.2f}%   {mean_diff:>8.2f}%")

# Verificar dados disponíveis por ano
print("\n=== Dados disponíveis por ano ===")
for year in sorted(comparison_df.index.year.unique()):
    year_df = comparison_df[comparison_df.index.year == year]
    print(f"{year}: {len(year_df)} dias (de {year_df.index[0].strftime('%d/%m')} a {year_df.index[-1].strftime('%d/%m')})")
    

import numpy as np
# Adicionar após o código existente

print("\n=== Cálculo do Tracking Error (TE) ===")

# Calcular retornos diários
daily_returns = comparison_df.pct_change().dropna()

# Calcular a diferença entre os retornos diários do VUAA e S&P 500 TR
tracking_difference = daily_returns['VUAA'] - daily_returns['S&P 500 TR']

# Calcular o Tracking Error (desvio padrão das diferenças, anualizado)
tracking_error_daily = tracking_difference.std()
tracking_error_annual = tracking_error_daily * np.sqrt(252)  # Anualizar usando 252 dias úteis

print(f"Tracking Error (diário): {tracking_error_daily * 100:.3f}%")
print(f"Tracking Error (anualizado): {tracking_error_annual * 100:.3f}%")

# Calcular o Tracking Error por ano
print("\n=== Tracking Error por Ano ===")
te_by_year = {}

for year in daily_returns.index.year.unique():
    year_returns = daily_returns[daily_returns.index.year == year]
    
    if len(year_returns) > 10:  # Garantir um número mínimo de observações
        year_tracking_diff = year_returns['VUAA'] - year_returns['S&P 500 TR']
        year_te = year_tracking_diff.std() * np.sqrt(252)
        te_by_year[year] = year_te * 100

# Ordenar por ano
te_series = pd.Series(te_by_year).sort_index()
for year, te in te_series.items():
    print(f"{year}: {te:.3f}%")

# Visualizar Tracking Error ao longo do tempo
plt.figure(figsize=(12, 8))

# Calcular TE rolling (janela de 60 dias)
rolling_te = tracking_difference.rolling(window=60).std() * np.sqrt(252) * 100

plt.plot(rolling_te.index, rolling_te, label='TE Rolling (60 dias)', linewidth=2)
plt.axhline(y=tracking_error_annual*100, color='r', linestyle='--', label=f'TE Médio ({tracking_error_annual*100:.2f}%)')

plt.title('Tracking Error ao Longo do Tempo (VUAA vs S&P 500 TR)', fontsize=14)
plt.xlabel('Data', fontsize=12)
plt.ylabel('Tracking Error Anualizado (%)', fontsize=12)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# Histograma das diferenças de retorno
plt.figure(figsize=(10, 6))
plt.hist(tracking_difference * 100, bins=50, alpha=0.75, color='skyblue', edgecolor='black')
plt.axvline(x=0, color='red', linestyle='--', linewidth=2)
plt.title('Distribuição das Diferenças de Retorno Diário (VUAA - S&P 500 TR)', fontsize=14)
plt.xlabel('Diferença de Retorno Diário (%)', fontsize=12)
plt.ylabel('Frequência', fontsize=12)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# Estatísticas adicionais
print("\n=== Estatísticas das Diferenças de Retorno ===")
print(f"Média da diferença: {tracking_difference.mean() * 100:.3f}%")
print(f"Mediana da diferença: {tracking_difference.median() * 100:.3f}%")
print(f"Máximo da diferença: {tracking_difference.max() * 100:.3f}%")
print(f"Mínimo da diferença: {tracking_difference.min() * 100:.3f}%")
print(f"Skewness: {tracking_difference.skew():.3f}")
print(f"Kurtosis: {tracking_difference.kurtosis():.3f}")

# Calcular Information Ratio
excess_return = daily_returns['VUAA'].mean() - daily_returns['S&P 500 TR'].mean()
information_ratio = (excess_return / tracking_difference.std()) * np.sqrt(252)
print(f"\nInformation Ratio (anualizado): {information_ratio:.3f}")

def convert_european_number(text):
    if isinstance(text, str):
        # Replace comma with period for decimal point
        text = text.replace(',', '.')
        # Check if there are multiple periods (thousands separators)
        if text.count('.') > 1:
            # Keep only the last period (the decimal point)
            parts = text.split('.')
            return float(''.join(parts[:-1]) + '.' + parts[-1])
        return float(text)
    return text


from pathlib import Path
home = Path.home()
data = Path(home, 'Desktop', 'sherpa_dados.xlsx')

df = pd.read_excel(data, sheet_name='StocksUS - Vontobel')
df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
col_interest = ['Date', 'Close']
df_filter = df[col_interest]
df_filter['Date'] = pd.to_datetime(df_filter['Date'], dayfirst=True)
df_filter.set_index('Date', inplace=True)

df_filter = df_filter[::-1]
df_filter = df_filter.resample('M').last()

df_filter = df_filter[(df_filter.index>='2011-01-01') & (df_filter.index<='2011-01-31')]

# Or alternatively
df_filter['Close'] = df_filter['Close'].apply(convert_european_number).astype(float)


returns = df_filter.pct_change()
returns = returns.add(1).cumprod()-1


# returns = df_filter.pct_change()
# returns = returns[returns.index>='2018-01-01']

# returns = returns.add(1).cumprod()-1
