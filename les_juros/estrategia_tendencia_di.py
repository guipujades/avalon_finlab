import numpy as np
import pandas as pd
import pickle as pkl
from pathlib import Path
from tqdm import tqdm
import matplotlib.pyplot as plt

import xlrd
from datetime import date
from urllib.request import urlretrieve


def PU_DI(i_m=None, i_pre=None, d=None, dtf=252, formato='VPA') -> float:
    
    if formato == 'VPA':
        vpa = (1 + i_pre) ** (d/252) - 1
        pu = (vpa * (1 + i_m * d)) / (1 + (dtf * i_m))
        
    elif formato == 'VPL':
        pu = 100_000 / (1 + i_pre)**(d/252)
    
    return pu


futures_data = pkl.load(open(Path(Path.home(), 'Desktop', 'futures_v2.pkl'), 'rb'))
dis = pd.DataFrame()
other_futures = pd.DataFrame()
for contract, df_ in futures_data.items():
    
    if contract.startswith('DI'):
        df_.columns = ['Data', 'Contrato', 'Venc', 'Venc_Data', 'Preço Ajuste', 'Preço Ajuste D-1',
               'Ajuste por Contrato (Calc)', 'Número de Negócios',
               'Contratos em aberto', 'pregoes', 'du', 'dc',
               'Ajuste por Contrato (Pub)', 'Taxa']
        dis = pd.concat([dis, df_], ignore_index=True)
    else:
        df_.columns = ['Data', 'Contrato', 'Venc', 'Venc_Data', 'Preço Ajuste', 'Preço Ajuste D-1',
               'Ajuste por Contrato (Calc)', 'Número de Negócios',
               'Contratos em aberto', 'pregoes', 'du', 'dc',
               'Ajuste por Contrato (Pub)']
        other_futures = pd.concat([other_futures, df_], ignore_index=True)

dis.Venc_Data = pd.to_datetime(dis.Venc_Data, format='%d/%m/%Y')
dis.sort_values(by='Data', inplace=True)
other_futures.Venc_Data = pd.to_datetime(other_futures.Venc_Data, format='%d/%m/%Y')
other_futures.sort_values(by='Data', inplace=True)

dis['Data'] = pd.to_datetime(dis['Data'])
dis = dis[dis['Venc'].apply(lambda x: x.startswith('F'))]

# Teste de sinal
# dis = dis[dis.Data >= '2020-01-01']

dis['price_calc'] = dis.apply(lambda row: PU_DI(i_pre=row['Taxa']/100, d=row['du'], dtf=252, formato='VPL'), axis=1)

dis['SMA_long'] = dis.groupby(['Venc'])['Taxa'].rolling(window=21).mean().reset_index(0, drop=True)
dis['SMA_short'] = dis.groupby(['Venc'])['Taxa'].rolling(window=9).mean().reset_index(0, drop=True)


def compute_signal(group):
    # Shift das SMA's para obter o valor do período anterior
    group['Prev_SMA_short'] = group['SMA_short'].shift(1)
    group['Prev_SMA_long'] = group['SMA_long'].shift(1)
    
    # Sinal de compra: SMA_short atual > SMA_long atual E SMA_short anterior <= SMA_long anterior
    group['Buy_Signal'] = np.where((group['SMA_short'] > group['SMA_long']) & 
                                   (group['Prev_SMA_short'] <= group['Prev_SMA_long']), 1, 0)
    
    # Sinal de venda: SMA_short atual < SMA_long atual E SMA_short anterior >= SMA_long anterior
    group['Sell_Signal'] = np.where((group['SMA_short'] < group['SMA_long']) & 
                                    (group['Prev_SMA_short'] >= group['Prev_SMA_long']), -1, 0)
    
    # Compilar os sinais de compra e venda em uma única coluna 'Signal'
    group['Signal'] = group['Buy_Signal'] + group['Sell_Signal']
    
    # Limpar colunas temporárias
    group.drop(columns=['Prev_SMA_short', 'Prev_SMA_long', 'Buy_Signal', 'Sell_Signal'], inplace=True)
    
    return group


dis = dis.groupby('Venc').apply(compute_signal).reset_index(drop=True)
dis['Position'] = dis.groupby('Venc')['Signal'].shift(1) # .diff()

dis['Position'] = dis['Position'].replace(0, np.nan)
dis['Position'].ffill(inplace=True)

# Liquidez
# dis['exec_auth'] = dis['Número de Negócios'] * 0.2
# dis['confirm'] = np.where(dis['exec_auth'] >= 1, 1, 0) # numero de negocios realizados nao significa presenca ou ausencia de book
# dis['Position'] = dis['Position'] * dis['confirm']

six_months = pd.Timedelta(days=360)
two_years = pd.Timedelta(days=10000)

# Função para aplicar na DataFrame e verificar o intervalo de tempo
def in_date_range(row):
    time_diff = row['Venc_Data'] - row['Data']
    return 1 if six_months <= time_diff <= two_years else 0

# Aplicar a função no DataFrame
dis['confirm'] = dis.apply(in_date_range, axis=1)
dis['Position'] = dis['Position'] * dis['confirm']

dis['Strategy_Returns'] = dis['Ajuste por Contrato (Calc)'] * dis['Position'] # no dia mesmo, por conta do delay das medias

dis.sort_values(by='Data', inplace=True)
dis['Cumulative_Returns'] = dis['Strategy_Returns'].cumsum()


plt.figure(figsize=(14, 7))
plt.plot(dis['Data'], dis['Cumulative_Returns'], label='Performance da Estratégia')

# Formatar o gráfico
plt.title('Curva de Performance')
plt.show()



###################################################################

dis = result
dis['Cumulative_Returns'] = dis['Strategy_Returns'].cumsum()

df = dis.copy()
target_days = 360

# Cria lista para armazenar os contratos selecionados
selected_rows = []

# Para cada data única no DataFrame
for date in df['Data'].unique():
    # Filtra contratos dessa data
    daily_contracts = df[df['Data'] == date].copy()
    
    # Calcula dias até o vencimento para cada contrato
    daily_contracts['dias_ate_venc'] = (daily_contracts['Venc_Data'] - daily_contracts['Data']).dt.days
    
    # Calcula distância até o prazo alvo
    daily_contracts['dist_to_target'] = abs(daily_contracts['dias_ate_venc'] - target_days)
    
    # Seleciona o contrato mais próximo do prazo alvo
    selected_contract = daily_contracts.nsmallest(1, 'dist_to_target')
    
    # Adiciona à lista de selecionados
    selected_rows.append(selected_contract)

# Combina todos os contratos selecionados
result = pd.concat(selected_rows)

# Remove colunas temporárias
result = result.drop(['dias_ate_venc', 'dist_to_target'], axis=1)

# Ordena por data
result = result.sort_values('Data')

# Reseta o índice
result = result.reset_index(drop=True)



test = dis.iloc[-500:,:]


################################################## 

