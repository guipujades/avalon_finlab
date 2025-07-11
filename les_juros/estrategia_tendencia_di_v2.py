import numpy as np
import pandas as pd
import pickle as pkl
from pathlib import Path
import matplotlib.pyplot as plt

def PU_DI(i_m=None, i_pre=None, d=None, dtf=252, formato='VPA') -> float:
    if formato == 'VPA':
        vpa = (1 + i_pre) ** (d/252) - 1
        pu = (vpa * (1 + i_m * d)) / (1 + (dtf * i_m))
    elif formato == 'VPL':
        pu = 100_000 / (1 + i_pre)**(d/252)
    return pu

def compute_long_only_signal(group):
    # Shift das SMA's para obter o valor do período anterior
    group['Prev_SMA_short'] = group['SMA_short'].shift(1)
    group['Prev_SMA_long'] = group['SMA_long'].shift(1)
    
    # Sinal de compra: SMA_short atual > SMA_long atual E SMA_short anterior <= SMA_long anterior
    group['Buy_Signal'] = np.where((group['SMA_short'] < group['SMA_long']) & 
                                   (group['Prev_SMA_short'] >= group['Prev_SMA_long']), -1, 0)
    
    # Sinal de zeramento: quando SMA_short cruza SMA_long para baixo
    group['Exit_Signal'] = np.where((group['SMA_short'] > group['SMA_long']) & 
                                   (group['Prev_SMA_short'] <= group['Prev_SMA_long']), 0, np.nan)
    
    # Combinar sinais
    group['Signal'] = group['Buy_Signal']
    group['Signal'] = np.where(group['Exit_Signal'] == 0, 0, group['Signal'])
    
    # Limpar colunas temporárias
    group.drop(columns=['Prev_SMA_short', 'Prev_SMA_long', 'Buy_Signal'], inplace=True)
    
    return group

# Carregar e preparar dados
futures_data = pkl.load(open(Path(Path.home(), 'Desktop', 'futures_v2.pkl'), 'rb'))
dis = pd.DataFrame()

for contract, df_ in futures_data.items():
    if contract.startswith('DI'):
        df_.columns = ['Data', 'Contrato', 'Venc', 'Venc_Data', 'Preço Ajuste', 'Preço Ajuste D-1',
               'Ajuste por Contrato (Calc)', 'Número de Negócios',
               'Contratos em aberto', 'pregoes', 'du', 'dc',
               'Ajuste por Contrato (Pub)', 'Taxa']
        dis = pd.concat([dis, df_], ignore_index=True)

# Preparação dos dados
dis.Venc_Data = pd.to_datetime(dis.Venc_Data, format='%d/%m/%Y')
dis['Data'] = pd.to_datetime(dis['Data'])
dis = dis[dis['Venc'].apply(lambda x: x.startswith('F'))]
dis.sort_values(by='Data', inplace=True)

# Cálculos
dis['price_calc'] = dis.apply(lambda row: PU_DI(i_pre=row['Taxa']/100, d=row['du'], dtf=252, formato='VPL'), axis=1)
dis['SMA_long'] = dis.groupby(['Venc'])['Taxa'].rolling(window=21).mean().reset_index(0, drop=True)
dis['SMA_short'] = dis.groupby(['Venc'])['Taxa'].rolling(window=9).mean().reset_index(0, drop=True)

# Computar sinais apenas de compra
dis = dis.groupby('Venc').apply(compute_long_only_signal).reset_index(drop=True)
dis['Position'] = dis.groupby('Venc')['Signal'].shift(1)

# Preencher posições
dis['Position'] = dis['Position'].replace(0, np.nan)
dis['Position'].ffill(inplace=True)

# Filtro de tempo
six_months = pd.Timedelta(days=360)
two_years = pd.Timedelta(days=10000)

def in_date_range(row):
    time_diff = row['Venc_Data'] - row['Data']
    return 1 if six_months <= time_diff <= two_years else 0

dis['confirm'] = dis.apply(in_date_range, axis=1)
dis['Position'] = dis['Position'] * dis['confirm']

# Cálculo dos retornos
dis['Strategy_Returns'] = dis['Ajuste por Contrato (Calc)'] * dis['Position']
dis.sort_values(by='Data', inplace=True)
dis['Cumulative_Returns'] = dis['Strategy_Returns'].cumsum()

# Visualização
plt.figure(figsize=(14, 7))
plt.plot(dis['Data'], dis['Cumulative_Returns'], label='Performance da Estratégia Long-Only')
plt.title('Curva de Performance - Estratégia Long-Only')
plt.xlabel('Data')
plt.ylabel('Retorno Acumulado')
plt.legend()
plt.grid(True)
plt.show()



