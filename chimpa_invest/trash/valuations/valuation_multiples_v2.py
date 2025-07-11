import os
import sys
import pickle
import statistics
import numpy as np
import pandas as pd
import datetime as dt
from pathlib import Path
from datetime import date

from finance_module_class import CVMDataFetcher
pd.options.display.float_format = '{:.3f}'.format

# ABEV
# Caminho individual para ativo
home = Path.home()
abev_path = Path(home, 'Documents', 'Avalon', 'dfp_taee.xls')
dre_ex = pd.read_excel(abev_path, sheet_name='Dem. Result.')
bal_ex = pd.read_excel(abev_path, sheet_name='Bal. Patrim.')

# 1.GETTING DATA
# data CVM
start_date = date(2015, 1, 1)
cvm_codes_list = ['23264'] # Codigo CVM empresa ABEV

fetcher = CVMDataFetcher(start_date, cvm_codes_list)
data, df_dfc = fetcher.fetch_data()

# obs.: rode essa parte apenas se nao tiver os dados ja guardados e serializados
# organizar dados avulsos
def organize_data(df):
    df = df.rename(columns = {'0': 'Data'})
    # capturar nomes das colunas
    colnames = df.iloc[0,:]
    colnames.iloc[0] = "Data"
    # capturar nomes das linhas
    rownames = df.iloc[:,0]
    # deletar primeira linha
    df = df.drop(df.index[0])
    # deletar primeira coluna
    df = df.drop(df.columns[0], axis=1)
    # transpose
    df = df.T
    # definir nomes das colunas
    df.columns = rownames[1:]
    # definir nomes das linhas
    df.index = pd.to_datetime(colnames[1:],)
    return df

dre_ex = organize_data(dre_ex)
bal_ex = organize_data(bal_ex)


#----------------------DRE----------------------------------#
period_results = {}
dre_consolidado = pd.DataFrame()
for period in dre_ex.index:
    d_year = period.year
    dre_consolidado['Period'] = d_year
    period_results[d_year] = {}
    for col in list(dre_ex.columns):
        result = dre_ex[dre_ex.index.year == d_year]
        result = np.sum(result.loc[:,col])
        period_results[d_year][col] = result

dre_consolidado = pd.DataFrame(period_results)
dre_consolidado = dre_consolidado.T
dre = dre_consolidado.T


#----------------------BALANÇO(Ativo)--------------------------------------#
period_results = {}
for period in bal_ex.groupby([bal_ex.index]):
    d_trim = period[0][0]
    if d_trim.month == 12:
        period_results[d_trim.year] = {}
        balAtivo_consolidado = bal_ex[bal_ex.index == d_trim]
        balAtivo_consolidado.index = balAtivo_consolidado.index.year
        period_results[d_trim.year] = balAtivo_consolidado
        
balAtivo_consolidado = pd.concat(period_results, axis=0)
# retirar um nivel do multi-index
balAtivo_consolidado = balAtivo_consolidado.droplevel(1)
bal_visual = balAtivo_consolidado.T

# ajustes de tamanhos dos dfs
balAtivo_consolidado = balAtivo_consolidado[(balAtivo_consolidado.index>=2015) & (balAtivo_consolidado.index<=2023)]
dre_consolidado = dre_consolidado[(dre_consolidado.index>=2015) & (dre_consolidado.index<=2023)]


# adaptar dataframes para o caso de nao estarmos no fim de algum ano
if len(balAtivo_consolidado.index) != len(dre_consolidado.index):
    diff = [i for i in balAtivo_consolidado.index if i not in dre_consolidado.index] + [i for i in dre_consolidado.index if i not in balAtivo_consolidado.index]
    for year in diff:
        if year in balAtivo_consolidado.index:
            balAtivo_consolidado = balAtivo_consolidado.drop([year], axis=0)
        else:
            dre_consolidado = dre_consolidado.drop([year], axis=0)


# criar copia
df = df_dfc.copy()
df.set_index(['Conta', 'Descrição'], inplace=True)
filter_columns = [i for i in df.columns if pd.to_datetime(i, errors='coerce').month == 12]
df = df[filter_columns]

years_filter = df.index
df.columns = pd.to_datetime(df.columns, errors='coerce').year
df = df.loc[:, df.columns.isin(years_filter)]

index_ref = df[~df.index.get_level_values('Conta').duplicated(keep='first')].index
df = df.groupby(['Conta'], as_index=False).sum()
df.index = index_ref

# 2 CONTAS INDIVIDUAIS

# 2.1 DRE

#contas_dre = []
#for years in dre_consolidado:
    years = list(balAtivo_consolidado.index)
    # 2.1.1 RECEITA LIQUIDA
    receita_liquida = dre_consolidado.iloc[:,2]
    # 2.1.2 CUSTO DOS PRODUTOS VENDIDOS (CPV)
    CPV = dre_consolidado.iloc[:,3]
    # 2.1.3 LUCRO BRUTO
    lucro_bruto = dre_consolidado.iloc[:,4]
    # 2.1.4 SG&A
    #sga = dre_consolidado.iloc
    # 2.1.5 DEPRECIACAO & AMORTIZACAO
    deprec_amortID = '6.01.01.02'
    depreciacao_ano = df.loc[deprec_amortID, :]
    depreciacao_ano = depreciacao_ano.T
    # 2.1.6 TOTAL DESPESAS
    #despesas_total = SGA+D&A+
    # 2.1.7 EBIT
    ebit = dre_consolidado.iloc[:, 4:11]
    ebit["sum"] = ebit.sum(axis=1)
    # 2.1.8 EBITDA
    ebitda_df = pd.concat([ebit["sum"], depreciacao_ano], axis=1)
    ebitda_df = ebitda_df.dropna()
    ebitda_df["sum"] = ebitda_df.sum(axis=1)
    # 2.1.9 DESPESAS FINANCEIRAS (JUROS)
    despesas_financeiras = dre_consolidado.loc[:, 'Despesas Financeiras']*-1
    receitas_financeiras = dre_consolidado.loc[:, 'Receitas Financeiras']*-1
    equiv_patr = dre_consolidado.loc[:, 'Resultado da Equivalência Patrimonial']*-1
    # 2.1.10 LUCRO ANTES DOS IMPOSTOS
    lucro_antes_impostos = ebit - despesas_financeiras
    # 2.1.11 IMPOSTO DE RENDA
    IR = dre_consolidado.iloc[:, ]
    # 2.1.12 LUCRO LIQUIDO
    lucro_liquido = dre_consolidado.iloc[:,-1] - dre_consolidado.iloc[:,-2]
    #2.1.13 LUCRO ATIVO
    lucro_ativo = lucro_liquido - despesas_financeiras
    contas_dre.append()
    
result_contas_dre = pd.DataFrame(multiplos, index=list(balAtivo_consolidado.index)[1:])
result_contas_dre.index.name = 'ano'


# 2.2 BALANÇO (ATIVO)

contas_bp_a = []
for years in balAtivo_consolidado:
    years = list(balAtivo_consolidado.index)
    #2.2.1 ATIVO_TOTAL
    ativo_total = balAtivo_consolidado.loc[:, 'Ativo Total']
    #2.2.2 ATIVO CIRCULANTE
    ativo_circulante = balAtivo_consolidado.loc[:, 'Ativo Circulante']
    #2.2.4 ATIVO LIQUIDO
    ativo_liquido = balAtivo_consolidado.loc[:, 'Ativo Total'] - passivo_operacional
    #2.2.3 CAIXA
    caixa = balAtivo_consolidado.loc[:,'Caixa e Equivalentes de Caixa']
    #2.2.3 CONTAS A RECEBER
    contas_receber = balAtivo_consolidado.loc[:, 'Contas a receber']
    #2.2.4 ESTOQUES
    estoques = (balAtivo_consolidado.loc[:, 'Estoques']
    #2.2.5 IMOBILIZADO & INTANGIVEL
    imobilizado_intangivel = balAtivo_consolidado.loc[:, 'Imobilizado'] + balAtivo_consolidado.loc[:, 'Intangível'] 
    #2.2.6 Ativo Líquido
    ativo_liquido = balAtivo_consolidado.loc[:, 'Ativo Total'] - passivo_operacional
    contas_bp.append()

result_contas_bp = pd.DataFrame(contas_bp, index=list(balAtivo_consolidado.index)[1:])
result_contas_bp.index.name = 'ano'


# 2.3 BALANCO (PASSIVO)

contas_bp_p = []
for years in balAtivo_consolidado:
    years = list(balAtivo_consolidado.index)
    #2.3.1 Passivo Total
    passivo_total = balAtivo_consolidado.loc[:, 'Passivo Circulante'] + balAtivo_consolidado.loc[:, 'Passivo Não Circulante']
    #2.3.2 PASSIVO CIRCULANTE
    passivo_circulante = balAtivo_consolidado.loc[:, 'Passivo Circulante']
    # PASSIVO FINANCEIRO
    passivo_financeiro = np.sum(balAtivo_consolidado.loc[:, 'Empréstimos e Financiamentos'], axis=1)
    # 2.3.3 PASSIVO OPERACIONAL
    passivo_operacional = passivo_total - passivo_financeiro
    #2.3.2 FORNECEDORES
    fornecedores = balAtivo_consolidado.loc[:, 'Fornecedores']
    #2.3.3 DIVIDA 
    divida = balAtivo_consolidado.loc[:, 'Empréstimos e Financiamentos']
    #2.3.4 PASSIVO FINANCEIRO
    passivo_financeiro = np.sum(balAtivo_consolidado.loc[:, 'Empréstimos e Financiamentos'], axis=1)
    #2.3.5 PASSIVO OPERACIONAL
    passivo_operacional = passivo_total - passivo_financeiro
    contas_bp_p.append()

result_contas_bp_p = pd.DataFrame(contas_bp, index=list(balAtivo_consolidado.index)[1:])
result_contas_bp_p.index.name = 'ano'


# 2.4 BALANCO PL

#2.4.1
patrimonio_liquido = balAtivo_consolidado.loc[:, 'Patrimônio Líquido']

# 2.5 DEMONSTRATIVO DE FLUXO DE CAIXA

#2.5.1 FCO


#2.5.2 FCI


#2.5.3 FCF


#2.5.4 POSIÇÃO FINAL DE CAIXA


# 2.6 APOIO ADICIONAL

#2.6.1 CAPITAL DE GIRO
#NCG = 
#NCG% = 

#2.6.2 DEPRECIACAO


#2.6.3 ENDIVIDAMENTO


# 2.7 MODELO DCF

#2.7.1 IR


#2.7.2 TAXA DE DESCONTO


#2.7.3 CRESCIMENTO NA PERPETUIDADE


#2.7.4 MULTIPLO EV/EBITDA


#2.7.5 DATA DO VALUATION


#2.7.6 DATA FINAL DO ANO


#2.7.7 PREÇO ATUAL


#2.7.8 ACOES NEGOCIADAS


#2.7.9 GORDON


# 3 PREMISSAS

#%receita = 
#%CMV = 
#%SGA = 
#%depreciacao = 
#%juros = 
#%IR = 


#PRAZOS

PMR = (balAtivo_consolidado.iloc[:, 4] * 360) / receita_liquida

PME = (balAtivo_consolidado.iloc[:, 5] * 360) / abs(dre_consolidado.loc[:,'Custo de Bens e/ou Serviços Vendidos'])

PMP = (balAtivo_consolidado.loc[:, 'Fornecedores'] * 360) / abs(dre_consolidado.loc[:,'Custo de Bens e/ou Serviços Vendidos'])

ciclo_operacional = PME + PMR

ciclo_caixa = ciclo_operacional - PMP

df_prazos = pd.concat([PMR, PME, PMP, ciclo_operacional, ciclo_caixa], axis=1)
cols = [
        'PM Recebimento Vendas', 'PM Estocagem', 'PM Pagamento', 'Ciclo Operacional', 'Ciclo Caixa'
        ]
cols_dict = {}
count = 0
for i in cols:
    cols_dict[df_prazos.columns[count]] = i
    count+=1
df_prazos = df_prazos.rename(columns=cols_dict)


#----------------MULTIPLOS/INDICADORES---------------#

preço = 11.39 # Automatizar"
numero_acoes = 15757657 # "Automatizar"
ev = (preço*numero_acoes)+divida-caixa
LPA = lucro_liquido/numero_acoes
vpa = patrimonio_liquido/numero_acoes
div_liq = balAtivo_consolidado.loc[:, 'Empréstimos e Financiamentos'] - balAtivo_consolidado.loc[:,'Caixa e Equivalentes de Caixa']

multiplos = []
for years in balAtivo_consolidado:
    years = list(balAtivo_consolidado.index)
    # Indicadores de valuation
    PL = preço/LPA
    PVP = preço/vpa
    EV/EBITDA = ev/ebitda
    P/EBITDA = preço/ebitda
    P/ATIVO = preço/ativo_total
    # Margens
    margem_bruta = lucro_bruto / receita_liquida
    margem_operacional = ebit / receita_liquida
    margem_ebitda = ebitda/receita_liquida
    margem_liquida = lucro_liquido / receita_liquida
    #Rentabilidade
    roi = lucro_ativo / ativo_liquido
    roe = lucro_liquido / balAtivo_consolidado.loc[:, 'Patrimônio Líquido']
    roa = lucro_liquido / balAtivo_consolidado.loc[:, 'Ativo Total']
    roic = ebit / (balAtivo_consolidado.loc[:, 'Patrimônio Líquido'] + np.sum(balAtivo_consolidado.loc[:, 'Empréstimos e Financiamentos'], axis=1))
    payout = balAtivo_consolidado.loc[:, 'Dividendos e JCP a Pagar'] / LL 
    #Endividamento
    DIV_LIQUIDA/PL = div_liq/patrimonio_liquido
    DIV_LIQUIDA/EBITDA = div_liq/ebitda
    PL/ATIVOS = patrimonio_liquido/ativo_total
    PASSIVOS/ATIVOS = passivo_total/ativo_total
    LIQUIDEZ_CORRENTE = ativo_circulante/passivo_circulante
    # Indice de cobertura de despesas financeiras
    icj = ebit["sum"] / abs(dre_consolidado['Despesas Financeiras'])
    multiplos.append()
    
result_multiplos = pd.DataFrame(multiplos, index=list(lucro_liquido.index)[1:])
result_multiplos.index.name = 'ano'
