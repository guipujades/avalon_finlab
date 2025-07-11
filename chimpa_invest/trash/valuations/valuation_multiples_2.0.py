"""
De tempos em tempos e preciso renovar os codigos das empresas: https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/

"""

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

def get_dre(codigo_cvm):
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
    dre = dre_consolidado[(dre_consolidado.index>=2015) & (dre_consolidado.index<=2023)]
    return dre

# Baixar dados
database_path = Path(Path.home(), 'Documents', 'GitHub', 'database')
bal_path = Path(database_path, 'fundamentus_bal.pkl')
df_bal_results = pickle.load(open(bal_path, 'rb'))
dre_path = Path(database_path, 'fundamentus_DRE.pkl')
df_dre_results = pickle.load(open(dre_path, 'rb'))

open_cvm_codes_path = Path(database_path, 'dados_ciasabertas_cvm.csv')
open_cvm_codes = pd.read_csv(open_cvm_codes_path, encoding='ISO-8859-1', sep=';')
                           

ticker_value_df = []
ticker_value_info = {}
start_date = date(2015, 1, 1)
for n, code in enumerate(open_cvm_codes.CD_CVM):
    codigo_cvm = code
    
    print(open_cvm_codes.loc[n, 'LINK_DOC'])
    print('Digite o ticker da empresa na B3:')
    ticker = input()
    
    # data CVM
    cvm_codes_list = [codigo_cvm] # Codigo CVM empresa
    
    fetcher = CVMDataFetcher(start_date, cvm_codes_list)
    data, df_dfc = fetcher.fetch_data()

    dre_ex = df_dre_results[ticker]
    bal_ex = df_bal_results[ticker]
    
    # Analise comeca aqui
    # DRE consolidada
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


    # magnitude de investimentos
    investimentos = balAtivo_consolidado.loc[:, 'Ativo Total']
    data = []
    for year in list(investimentos.index):
        if year+1 in list(investimentos.index):
            crescimento = investimentos[year+1] / investimentos[year]
            data.append(crescimento)
    crescimento = pd.DataFrame(data, index=list(investimentos.index)[1:], columns=['crescimento'])
    
    # analise vertical dos ativos de curto e longo prazo
    ativo_circulanteabs = balAtivo_consolidado.loc[:, 'Ativo Circulante']
    ativo_naocirculante = investimentos - ativo_circulanteabs
    ativo_circulante_pct = ativo_circulanteabs/investimentos
    ativo_naocirculante_pct = ativo_naocirculante/investimentos
    
    # capital de giro liquido
    CGL = ativo_circulanteabs - balAtivo_consolidado.loc[:, 'Passivo Circulante']
    
    # equilibrio AC/PC
    AC = balAtivo_consolidado.loc[:, 'Ativo Circulante']
    PC = balAtivo_consolidado.loc[:, 'Passivo Circulante']
    
    # ILC: indice de liquidez corrente
    # quanto maior for o risco dos ativos circulantes da empresa (concentracao do contas, estoques de baixo giro), maior deve ser o indice
    # premissa de descontinuidade das operacoes
    # -- capacidade da empresa de pagar suas dívidas de curto prazo com seus ativos de curto prazo
    # ILS: indice de liquidez seca (nao considera o estoque)
    il_corrente = AC / PC
    
    # indice de envividamento
    ind_endividamento = np.sum(balAtivo_consolidado.loc[:, 'Empréstimos e Financiamentos'], axis=1) / balAtivo_consolidado.loc[:, 'Ativo Total'] 
    # indice de solvencia
    # IS = AT / PC + ELP (quanto maior, menor o risco da empresa)
    # -- capacidade da empresa de cumprir suas obrigações de longo prazo
    is_ind = pd.DataFrame(balAtivo_consolidado.loc[:, 'Ativo Total'] / (PC+balAtivo_consolidado.loc[:, 'Passivo Não Circulante']))
    is_ind = is_ind.rename(columns={is_ind.columns[0]:'IS'})
    
    # multiplicador de capital proprio: total dos ativos / PL
    # indica quanto a empresa está utilizando de recursos próprios versus recursos de terceiros
    mult_Kproprio = balAtivo_consolidado.loc[:, 'Ativo Total'] / balAtivo_consolidado.loc[:, 'Patrimônio Líquido']
    
    # diferenca capital proprio / capital de terceiros
    k_proprio = balAtivo_consolidado.loc[:, 'Patrimônio Líquido'] / balAtivo_consolidado.loc[:, 'Passivo Total'] 
    k_terceiros = (balAtivo_consolidado.loc[:, 'Passivo Total'] - balAtivo_consolidado.loc[:, 'Patrimônio Líquido']) / balAtivo_consolidado.loc[:, 'Passivo Total'] 
    k_proprio = k_proprio.apply(lambda x: str(round(x*100,2))+'%')
    k_terceiros = k_terceiros.apply(lambda x: str(round(x*100,2))+'%')
    pd_verfinanc = pd.DataFrame(k_proprio, columns=['% Capital Próprio'])
    pd_verfinanc['% Capital Terceiros'] = k_terceiros
    
    # total de financiamentos onerosos captados pela empresa
    k_oneroso = np.sum(balAtivo_consolidado.loc[:, 'Empréstimos e Financiamentos'], axis=1) / balAtivo_consolidado.loc[:, 'Passivo Total'] 
    k_oneroso = k_oneroso.apply(lambda x: str(round(x*100,2))+'%')
    pd_verfinanc['% Capital Oneroso de 3os'] = k_oneroso
    media_emprOn = statistics.mean(list(np.sum(balAtivo_consolidado.loc[:, 'Empréstimos e Financiamentos'], axis=1)))
    mediana_emprOn = statistics.median(list(np.sum(balAtivo_consolidado.loc[:, 'Empréstimos e Financiamentos'], axis=1)))
    # pd_verfinanc.to_excel(Path(home, 'Desktop', 'totus_proprioTerceiros.xlsx'))
    
    # analise vertical ano a ano das linhas do balanço (ativo total)
    an_vertical = balAtivo_consolidado.loc[:,'Ativo Total':'Diferido']
    counter = 0
    pd_verticalAtivo = pd.DataFrame(columns=list(an_vertical.columns)[1:])
    while counter < len(an_vertical.iloc[0,:])-1:
        ref_values = {}
        counter+=1
        for year in an_vertical.index:
            # participacao de cada item do ativo no total
            col = list(an_vertical.columns)[counter]
            values = np.sum(an_vertical.loc[year, col])/an_vertical.loc[year, 'Ativo Total']
            values = round(values*100, 2)
            values = str(values)+'%'
            ref_values[year] = values
        if counter == 1:
            pd_verticalAtivo = pd.DataFrame.from_dict(ref_values, orient='index', columns=[col])
        else:
            pd_verticalAtivo[col] = pd.DataFrame.from_dict(ref_values, orient='index')
    
    # analise vertical ano a ano das linhas do balanço (composicao percentual de cada item no passivo total)
    an_vertical = balAtivo_consolidado.loc[:,'Passivo Total':'Lucros e Receitas a Apropriar']
    counter = 0
    pd_verticalPassivo = pd.DataFrame(columns=list(an_vertical.columns)[1:])
    while counter < len(an_vertical.iloc[0,:])-1:
        ref_values = {}
        counter+=1
        for year in an_vertical.index:
            # participacao de cada item do ativo no total
            col = list(an_vertical.columns)[counter]
            values = np.sum(an_vertical.loc[year, col])/an_vertical.loc[year, 'Passivo Total']
            values = round(values*100, 2)
            values = str(values)+'%'
            ref_values[year] = values
        if counter == 1:
            pd_verticalPassivo = pd.DataFrame.from_dict(ref_values, orient='index', columns=[col])
        else:
            pd_verticalPassivo[col] = pd.DataFrame.from_dict(ref_values, orient='index')
       
    # variacoes percentuais das linhas entre anos (analise horizontal)
    num = len(balAtivo_consolidado.iloc[:,0])
    first_year = list(balAtivo_consolidado.index)[0]
    last_year = list(balAtivo_consolidado.index)[-1]
    count = 0
    var_years = {}
    for n in range(num+1):
        year = first_year + count
        ref_year = year + 1
        if year == last_year:
            break
        year_df = balAtivo_consolidado.iloc[count,:]
        next_year_df = balAtivo_consolidado.iloc[count+1,:]
        all_var = {}
        count_index = -1
        for value1,value2 in zip(year_df, next_year_df):
            count_index += 1
            if value1 != 0:
                var = round((float(value2/value1)-1)*100, 2)
                var = str(var)+'%'
                all_var[next_year_df.index[count_index]] = var
        
        count +=1
        pd_final = pd.DataFrame.from_dict(all_var, orient='index')
        pd_final = pd_final.rename(columns={0:str(ref_year)})
        var_years[ref_year] = pd_final
    
    pd_VarAno = pd.concat(var_years.values(), axis=1)
    
    
    # INDICADORES DE ATIVIDADE E SOLVÊNCIA
    receita = dre_consolidado.loc[:,'Receita Líquida de Vendas e/ou Serviços']
    data = []
    for year in list(receita.index):
        if year+1 in list(receita.index):
            comp = receita[year+1] / receita[year]
            data.append(comp)
    comparacao_RL = pd.DataFrame(data, index=list(receita.index)[1:])
    comparacao_RL = comparacao_RL.rename(columns={comparacao_RL.columns[0]:'Receita Líquida Vertical'})
    
    
    # indice de cobertura de juros: EBIT / despesas de juros (capacidade de pagar juros do financiamento) -> menor que 1 diz que resultado op nao e suficiente para pagar juros
    # INDICADORES DE ALAVANCAGEM E RENTABILIDADE
    # resultado operacional / margem operacional
    # lucro operacional = Ebit: metrica de viabilidade e competitividade 
    ebit = dre_consolidado.iloc[:, 4:11]
    ebit["sum"] = ebit.sum(axis=1)
    
    # obs.: nao necessariamente as despesas financeiras serao juros (proxy)
    # O que temos aqui e um indice de cobertura de despesas financeiras
    icj = ebit["sum"] / abs(dre_consolidado['Despesas Financeiras'])
    
    margem_op = ebit["sum"] / dre_consolidado.iloc[:,2]
    margem_opMedia = statistics.mean(margem_op)
    margem_opMedian = statistics.median(margem_op)
    
    # calculos de indicadores fundamentalistas
    receita_media = statistics.mean(dre_consolidado.iloc[0:10,2])
    
    # lucro bruto: reflete a capacidade da empresa de agregar valor
    lucro_bruto = dre_consolidado.iloc[:,4] # resultado bruto
    df_LB = pd.DataFrame(lucro_bruto)
    df_LB = df_LB.rename(columns={df_LB.columns[0]:'Lucro Bruto'})
    
    data = []
    for year in list(lucro_bruto.index):
        if year+1 in list(lucro_bruto.index):
            comp = lucro_bruto[year+1] / receita[year]
            data.append(comp)
    comparacao_LB = pd.DataFrame(data, index=list(lucro_bruto.index)[1:])
    comparacao_LB = comparacao_LB.rename(columns={comparacao_LB.columns[0]:'Lucro Bruto Vertical'})
    
    # receita liquida
    receita_liq = dre_consolidado.iloc[:,2]
    df_RL = pd.DataFrame(receita_liq)
    df_RL = df_RL.rename(columns={df_RL.columns[0]:'Receita Líquida'})
    
    # margem bruta: indicador de forca e competitividade
    margem_bruta = pd.DataFrame(dre_consolidado.iloc[:,4] / receita_liq)
    margem_bruta = margem_bruta.rename(columns={margem_bruta.columns[0]:'Margem Bruta'})
    mrgem_brutaMedia = statistics.mean(margem_bruta.iloc[:,0])
    margem_brutaMedian = statistics.median(margem_bruta.iloc[:,0])
    
    # lucro liquido
    LL =  dre_consolidado.iloc[:,-1] - dre_consolidado.iloc[:,-2]
    df_LL = pd.DataFrame(LL)
    df_LL = df_LL.rename(columns={df_LL.columns[0]:'Lucro Líquido'})
    
    # margem liquida
    margem_liq = LL/receita_liq.iloc[:]
    
    data = []
    for year in list(LL.index):
        if year+1 in list(LL.index):
            comp = LL[year+1] / receita[year]
            data.append(comp)
    comparacao_LL = pd.DataFrame(data, index=list(LL.index)[1:])
    comparacao_LL = comparacao_LL.rename(columns={comparacao_LL.columns[0]:'Lucro Líquido Vertical'})
    
    # dataframe para evolucao de RL e LL
    evolucao_RLL = pd.concat([comparacao_LB, comparacao_RL, comparacao_LL], axis=1)
    
    # dataframe de valores absolutos
    df_abs = pd.concat([df_LB, df_RL, df_LL], axis=1)
    
    
    # RENTABILIDADE PATRIMONIAL
    # passivo total: soma passivo circulante e nao circulante
    passivo_total = balAtivo_consolidado.loc[:, 'Passivo Circulante'] + balAtivo_consolidado.loc[:, 'Passivo Não Circulante']
    passivo_financeiro = np.sum(balAtivo_consolidado.loc[:, 'Empréstimos e Financiamentos'], axis=1)
    passivo_operacional = passivo_total - passivo_financeiro
    ativo_liquido = balAtivo_consolidado.loc[:, 'Ativo Total'] - passivo_operacional
    # despesa financeira líquida = despesa financeira * (1 -0,34)
    despfin = dre_consolidado.loc[:,'Despesas Financeiras'] * (1 -0.34)
    # Kd Custo da dívida = Despesa financeira líquida em módulo/Passivo financeiro
    Kd = abs(despfin) / passivo_financeiro
    # lucro dos Ativos = Lucro líquido - Despesa financeira líquida 
    lucro_ativo = LL - despfin
    # Retorno sobre o investimento (ROI) = Lucro do Ativo/ Ativo líquido
    roi_calc = lucro_ativo / ativo_liquido
    # ROE: Retorno sobre o PL = Lucro líquido/ PL
    roe_calc = LL / balAtivo_consolidado.loc[:, 'Patrimônio Líquido']
    # Spread = ROI - Kd
    spread = roi_calc - Kd # indica a capacidade da empresa de gerar valor acima do custo da dívida
    # proporção Passivo Financeiro/PL = Passivo financeiro/PL
    propPF_PL = passivo_financeiro / balAtivo_consolidado.loc[:, 'Patrimônio Líquido']
    # Contribuição da alavancagem = Spread * Proporção PF/PL
    contr_alav = spread * propPF_PL
    # grau de alavancagem financeira = ROE/ROI
    # Valores proximos a 1 indicam que a alavancagem financeira tem um impacto neutro na rentabilidade da 
    # empresa. Isso significa que o retorno gerado pelo uso de divida e aproximadamente igual ao retorno 
    # gerado pelo uso de capital proprio. Quando o grau de alavancagem e menor que 1, isso indica que o retorno 
    # sobre o patrimônio liquido (ROE) e menor do que o retorno sobre o investimento total (ROI). 
    # Isso pode ocorrer quando a empresa nao esta conseguindo gerar um retorno suficiente para compensar 
    # o custo adicional de alavancar-se com dividas.
    grau_alav = roe_calc / roi_calc
    
    # MODELO DUPONT
    # Margem Líquida (Lucro líquido/Receita líquida)
    mLiq = LL / receita_liq
    # Giro (Receita líquida/ Ativo total)
    giro = receita_liq / investimentos
    # Alavancagem (Ativo total/Patrimônio líquido)
    alav = investimentos / balAtivo_consolidado.loc[:, 'Patrimônio Líquido']
    # ROE (Lucro líquido/Patrimônio Líquido)
    ROE_dupont = LL / balAtivo_consolidado.loc[:, 'Patrimônio Líquido']
    
    rentabilidade_patr = pd.concat([
        passivo_total, passivo_financeiro, passivo_operacional, ativo_liquido, despfin, Kd, lucro_ativo, roi_calc, roe_calc,
        spread, propPF_PL, contr_alav, grau_alav, mLiq, giro, alav, ROE_dupont
        ], axis=1)
    cols = [
            'Passivo Total', 'Passivo Financeiro', 'Passivo Operacional', 'Ativo Líquido', 'Despesa Fin Líquida', 'Custo Dívida',
            'Lucro Ativo', 'ROI', 'ROE', 'Spread', 'Passivo Fin / PL', 'Contr Alavancagem', 'Grau Alavancagem',
            'DP_Margem Líquida', 'DP_Giro', 'DP_Alavancagem', 'DP_ROE'
            ]
    cols_dict = {}
    count = 0
    for i in cols:
        cols_dict[rentabilidade_patr.columns[count]] = i
        count+=1
    rentabilidade_patr = rentabilidade_patr.rename(columns=cols_dict)
    
    # PRAZOS
    # Ciclo de caixa = PME + PMR - PMP
    # PMR = Prazo medio de recebimento de vendas (Contas a receber x 360 / Receita Liquida) -> do ativo circulante operacional
    PMR = (balAtivo_consolidado.iloc[:, 4] * 360) / receita_liq
    # PME - Prazo medio de estocagem (Estoques x 360	 / Custo das vendas ou servico) -> do ativo circulante operacional 
    # ** o ideal seria observar o core da empresa e fazer o calculo apenas sobre o custo do bem ou do servico
    PME = (balAtivo_consolidado.iloc[:, 5] * 360) / abs(dre_consolidado.loc[:,'Custo de Bens e/ou Serviços Vendidos'])
    # PMP - Prazo medio de pagamento (Fornecedores x 360 / Custo do produto vendido) ** por aproximacao
    PMP = (balAtivo_consolidado.loc[:, 'Fornecedores'] * 360) / abs(dre_consolidado.loc[:,'Custo de Bens e/ou Serviços Vendidos'])
    
    # ciclo operacional
    ciclo_op = PME + PMR
    # ciclo de caixa
    # ABEV possui um ciclo de caixa negativo, o que significa que Ela financia suas atividades com recursos dos fornecedores 
    # e ainda pode utilizar este recurso aplicando-o no mercado financeiro por um período 
    # antes de realizar o pagamento aos fornecedores
    ciclo_cx = ciclo_op - PMP
    
    # dataframe de prazos
    df_prazos = pd.concat([PMR, PME, PMP, ciclo_op, ciclo_cx], axis=1)
    cols = [
            'PM Recebimento Vendas', 'PM Estocagem', 'PM Pagamento', 'Ciclo Operacional', 'Ciclo Caixa'
            ]
    cols_dict = {}
    count = 0
    for i in cols:
        cols_dict[df_prazos.columns[count]] = i
        count+=1
    df_prazos = df_prazos.rename(columns=cols_dict)
    
    # ROA bruto direto
    roa_brutoDireto = ebit["sum"] / balAtivo_consolidado.loc[:, 'Ativo Total']
    
    # ROA: retorno sobre o ativo total (usado muito em bancos) -> sobre todos os ativos da empresa
    # ROA bruto: EBIT / ativo total (medio)
    result_roaBruto = pd.DataFrame(columns=['pcts', 'ano'])
    roa_bruto_list = []
    for year in list(LL.index):
        if year+1 in list(LL.index):
            x = balAtivo_consolidado.loc[year+1, 'Ativo Total']
            y = balAtivo_consolidado.loc[year, 'Ativo Total']
            roa_bruto = ebit["sum"].loc[year] / (x+y/2)
            roa_bruto_list.append(roa_bruto)
            
    result_roaBruto = pd.DataFrame(roa_bruto_list, index=list(LL.index)[1:])
    result_roaBruto.index.name = 'ano'
    result_roaBruto.columns = ['pcts']
    
    # ROA liquido direto
    roa_liquidoDireto = LL / balAtivo_consolidado.loc[:, 'Ativo Total']
    # ROA liquido: LL / ativo total (medio)
    roa_liquido_list = []
    for year in list(LL.index):
        if year+1 in list(LL.index):
            x = balAtivo_consolidado.loc[year+1, 'Ativo Total']
            y = balAtivo_consolidado.loc[year, 'Ativo Total']
            roa_liquido = LL.loc[year] / (x+y/2)
            roa_liquido_list.append(roa_liquido)
            
    result_roaLiq = pd.DataFrame(roa_liquido_list, index=list(LL.index)[1:])
    result_roaLiq.index.name = 'ano'
    result_roaLiq.columns = ['pcts']
    
    # ROE = net profit (lucro líquido) / net worth (patrimônio líquido) (medio)
    # esse retorno e o que comparamos com o preco da acao
    # usar o LL medio em virtude do fato de o lucro ser formado ao longo do ano
    # metodo direto
    roeDireto = LL / balAtivo_consolidado.loc[:, 'Patrimônio Líquido']
    # metodo com PL medio
    roe_list = []
    for year in list(LL.index):
        if year+1 in list(LL.index):
            x = balAtivo_consolidado.loc[year+1, 'Patrimônio Líquido']
            y = balAtivo_consolidado.loc[year, 'Patrimônio Líquido']
            roe = LL.loc[year] / (x+y/2)
            roe_list.append(roe)
            
    result_roe = pd.DataFrame(roe_list, index=list(LL.index)[1:])
    result_roe.index.name = 'ano'
    result_roe.columns = ['pcts']
    
    # ROIC: EBIT / capital investido (pegar o capital investido = capital proprio + capital de terceiros)
    # importante principalmente para empresas muito alavancadas
    # o ideal e que o ROIC fique acima da SELIC (e o que mede as dividas)
    # capital proprio = PL || capital de terceiros = dividas
    # obs.: um resultado maior que o roe mostra como e importante para a empresa pegar dividas
    # e importante calcular o ROIC se a divida for muito alta, porque nesse caso o ROE pode enganar
    roic = ebit["sum"] / (balAtivo_consolidado.loc[:, 'Patrimônio Líquido'] + np.sum(balAtivo_consolidado.loc[:, 'Empréstimos e Financiamentos'], axis=1))
    
    # calculo do ROIC com valores medios
    roic_list = []
    for year in list(ebit["sum"].index):
        if year+1 in list(LL.index):
            x = balAtivo_consolidado.loc[year+1, 'Patrimônio Líquido'] + np.sum(balAtivo_consolidado.loc[year+1, 'Empréstimos e Financiamentos'])
            y = balAtivo_consolidado.loc[year, 'Patrimônio Líquido'] + np.sum(balAtivo_consolidado.loc[year, 'Empréstimos e Financiamentos'])
            roic = ebit["sum"].loc[year] / (x+y/2)
            roic_list.append(roic)
            
    result_roic = pd.DataFrame(roic_list, index=list(LL.index)[1:])
    result_roic.index.name = 'ano'
    result_roic.columns = ['pcts']
    
    # payout = dividendos / LL
    payout = balAtivo_consolidado.loc[:, 'Dividendos e JCP a Pagar'] / LL 
    # indice de retencao = 1 - payout
    ind_retencao = 1 - payout
    ind_retencao = ind_retencao.reset_index()
    ind_retencao = ind_retencao.rename(columns={'index':'ano', 0:'pcts'})
    ind_retencao = ind_retencao.set_index('ano') # taxa de reinvestimento
    # taxa de crescimento sustentavel = ROE * indice de retencao
    tx_crescimentoSus = result_roe.values * ind_retencao.iloc[1:].values
    tx_crescimentoSus = pd.DataFrame(tx_crescimentoSus, index=result_roe.index) # Damodaran
    
    # NOPAT e Expectativa de geracao de caixa livre para a empresa (EGCL)
    nopat = ebit["sum"] * (1 -0.34)
    # gcle = nopat.values * (1 + tx_crescimentoSus).values - ind_retencao * LL

    # -----------------------------------------------------------------------------------------------------
    # ANALISE DE DFC INDIVIDUAL
    
    # criar copia
    df = df_dfc.copy()
    df.set_index(['Conta', 'Descrição'], inplace=True)
    filter_columns = [i for i in df.columns if pd.to_datetime(i, errors='coerce').month == 12]
    df = df[filter_columns]
    
    years_filter = ebit.index
    df.columns = pd.to_datetime(df.columns, errors='coerce').year
    df = df.loc[:, df.columns.isin(years_filter)]
    
    index_ref = df[~df.index.get_level_values('Conta').duplicated(keep='first')].index
    df = df.groupby(['Conta'], as_index=False).sum()
    df.index = index_ref
    
    # indices
    caixaliquido_op = '6.01'
    caixaliquido_inv = '6.02'
    caixaliquido_fin = '6.03'
    deprec_amortID = '6.01.01.02'
    caixagerado_op = '6.01.01'
    geracao_caixa = '6.05'
    aquis_imob = '6.02.02'
    aquis_imob_ = '6.02.03' # -> AMBEV
    
    # caixa liquido de atividades operacionais e EBITDA
    FCO = df.loc[caixaliquido_op, :]
    depreciacao_ano = df.loc[deprec_amortID, :]
    ebitda = ebit['sum'].values + depreciacao_ano.values
    ebitda_df = pd.DataFrame(ebitda[0], index=df.columns)
    ebitda_df = ebitda_df.rename(columns={ebitda_df.columns[0]:'Ebitda'})
    
    # capacidade de conversao de EBITDA (caixa potencial) em FCO (caixa efetivo)
    # FCO antes de juros e impostos
    # ABEV -> caixa gerado nas operacoes
    FCO_info = df.loc[caixagerado_op, :]
    FCO_info = FCO_info.T
    ger_cx = pd.DataFrame(FCO_info.values/ebitda_df.values)
    ger_cx = ger_cx.rename(columns={ger_cx.columns[0]:'Conversão'})
    ger_cx.index = FCO_info.index
    
    # margem EBITDA
    margem_ebitda = pd.DataFrame(ebitda_df.values.flatten()/receita_liq.values, index=margem_bruta.index)
    
    # variacao de caixa no decurso dos anos
    FCI = df.loc[caixaliquido_inv, :]
    fci_df = pd.DataFrame(FCI.values[0], index=ger_cx.index)
    fci_df = fci_df.rename(columns={fci_df.columns[0]:'FCI'})
    FCF = df.loc[caixaliquido_fin, :]
    fcf_df = pd.DataFrame(FCF.values[0], index=ger_cx.index)
    fcf_df = fcf_df.rename(columns={fcf_df.columns[0]:'FCF'})
    
    var_cx = pd.DataFrame(FCO.T.values + FCI.T.values + FCF.T.values)
    var_cx = var_cx.rename(columns={var_cx.columns[0]:'Geração Caixa'})
    var_cx.index = FCO_info.index
    
    # calculo do FCO restrito e amplo
    # FCOR: lucro liquido + depreciacao (+-) outros resultados nao operacionais, (+-) resultado equiv patrim (+-) Rec/Desp fin
    # (+-) reversao de provisoes e outras despesas ou receitas nao monetarias, sem relacao com a operacao
    # temos LL e depreciacao_ano
    # equivalencia patrimonial
    equiv_patr = dre_consolidado.loc[:, 'Resultado da Equivalência Patrimonial']*-1
    desp_fin = dre_consolidado.loc[:, 'Despesas Financeiras']*-1
    rec_fin = dre_consolidado.loc[:, 'Receitas Financeiras']*-1
    
    FCOR = LL.values + depreciacao_ano.values[0] + equiv_patr + desp_fin.values + rec_fin.values
    FCOR_df = pd.DataFrame(FCOR, index=FCO_info.index)
    FCOR_df.columns = ['FCOR']
    
    # geracao liquida de caixa (nao e a mesma coisa que FCOR)
    ger_liqCx = df.loc[geracao_caixa, :]
    FCOR_ = pd.DataFrame(df.loc[caixagerado_op, :])
    FCOR_ = FCOR_.T
    FCOR_ = FCOR_.rename(columns={FCOR_.columns[0]:'FCOR'})
    
    fco_AMPLO = FCO.T
    fco_AMPLO.columns = ['FCO Amplo']
    
    # comparativo FCOR e FCO (organizar indice para constar como str)
    df1 = pd.DataFrame(fco_AMPLO)
    df1.columns = ['FCO']
    df2 = pd.DataFrame(FCOR.values, index=fco_AMPLO.index)
    df2.columns = ['FCOR']
    
    compFCO_FCOR = pd.concat([df2, df1], axis=1)
    
    # diferenca FCOR/Ebit
    diff = pd.DataFrame(FCOR.values[0] - ebit['sum'].values, index=fco_AMPLO.index)
    result = pd.DataFrame(depreciacao_ano.values[0] / diff.values[0], index=fco_AMPLO.index)
    
    # analises comparativas
    # espera-se ver um FCOR maior que o LL
    saude_operacao = pd.DataFrame(FCOR.values[0] / LL.values, index=fco_AMPLO.index)
    saude_operacao = saude_operacao.rename(columns={saude_operacao.columns[0]:'FCOR/LL'})
    
    # adequacao dos investimentos realizados
    # relacao FCI / depreciacao amortizacao
    rel_FCIAmort = pd.DataFrame(abs(FCI.values[0]) / depreciacao_ano.values[0], index=fco_AMPLO.index)
    rel_FCIAmort = rel_FCIAmort.rename(columns={rel_FCIAmort.columns[0]:'rel_FCI/Depreciação'})
    # quanto foi investido no operacional da empresa (ativo permanente e realizavel de longo prazo)
    imobil_int = balAtivo_consolidado.loc[:, 'Imobilizado'] + balAtivo_consolidado.loc[:, 'Intangível'] 
    RLP_op = balAtivo_consolidado.loc[:, 'Ativo Realizável a Longo Prazo']
    dir_gastos = imobil_int + RLP_op
    rel_FCI = pd.DataFrame(abs(FCI.values[0]) / dir_gastos.values, index=imobil_int.index)
    
    # computar apenas imobilizado e intangivel
    # analise de aquisicao de imobilizado e intangivel a partir da DFC
    i1 = df.loc[aquis_imob, :]
    i2 = df.loc[aquis_imob_, :]
    capex = i1 + i2
    
    rel_FCI_imob = pd.DataFrame(abs(FCI.values[0]) / capex.values[0], index=fco_AMPLO.index)
    rel_FCI_imob = rel_FCI_imob.rename(columns={rel_FCI_imob.columns[0]:'FCI/Ativo Permanente'})
    
    # free cash flow
    cash_fromOP = df.loc[caixaliquido_op, :]
    interest_andTaxshield = dre_consolidado.loc[:, 'Despesas Financeiras'] * (1-0.34)
    freeCash_flow = cash_fromOP.values + interest_andTaxshield.values + capex.values
    freeCash_flow = pd.DataFrame(freeCash_flow[0], index=fco_AMPLO.index)
    freeCash_flow = freeCash_flow.rename(columns={freeCash_flow.columns[0]: 'Free Cash Flow'})


    # df resumo de DFC
    dfc_df = pd.concat([FCO_info, FCOR, fci_df, fcf_df, var_cx, ebitda_df, ger_cx, saude_operacao, rel_FCIAmort, rel_FCI_imob, freeCash_flow], axis=1)
    cols = [
            'FCO', 'FCOR', 'FCI', 'FCF', 'Variação Caixa', 'Ebitda', 'Conversão FCO/Ebtida', 'FCOR/LL', 'FCI/Depreciação', 
            'FCI/Ativo Permanente', 'Free Cash Flow'
            ]
    dfc_df.columns = cols

    # df de margens
    margens_ano = pd.concat([margem_bruta, margem_liq, margem_ebitda], axis=1)
    margens_ano = margens_ano.rename(columns={
        list(margens_ano.columns)[0]:'Margem Bruta', list(margens_ano.columns)[1]:'Margem Líquida', 
        list(margens_ano.columns)[2]:'Margem Ebitda'
        })
    margens_ano.index = dfc_df.index

    analise_ampla = pd.concat([investimentos, crescimento, AC, PC, il_corrente, is_ind, CGL, ind_endividamento, mult_Kproprio], axis=1)
    cols = [
           'Investimentos', 'Crescimento', 'Ativo Circulante', 'Passivo Circulante', 'Liquidez Corrente (AC/PC)', 'Índice de Solvência', 'Capital de Giro Líquido',
           'Índice de Endividamento', 'Multiplicador de K Próprio'
            ]
    analise_ampla.columns = cols


    final_list = [
        analise_ampla, pd_verfinanc, df_abs, evolucao_RLL, pd_verticalPassivo, pd_verticalAtivo, pd_VarAno,
        margens_ano, df_prazos, dfc_df, rentabilidade_patr
        ]

    ticker_value_info[ticker] = final_list
    
    # Certifique-se de que todos os DataFrames têm as mesmas datas como índice
    ebitda_df.index = pd.to_datetime(ebitda_df.index, format='%Y')
    FCO_info.index = pd.to_datetime(FCO_info.index, format='%Y')
    ger_cx.index = pd.to_datetime(ger_cx.index, format='%Y')
    fcf_df.index = pd.to_datetime(fcf_df.index, format='%Y')
    margens_ano.index = pd.to_datetime(margens_ano.index, format='%Y')
    analise_ampla.index = pd.to_datetime(analise_ampla.index, format='%Y')
    pd_verfinanc.index = pd.to_datetime(pd_verfinanc.index, format='%Y')
    df_abs.index = pd.to_datetime(df_abs.index, format='%Y')
    evolucao_RLL.index = pd.to_datetime(evolucao_RLL.index, format='%Y')
    pd_verticalPassivo.index = pd.to_datetime(pd_verticalPassivo.index, format='%Y')
    pd_verticalAtivo.index = pd.to_datetime(pd_verticalAtivo.index, format='%Y')
    df_prazos.index = pd.to_datetime(df_prazos.index, format='%Y')
    dfc_df.index = pd.to_datetime(dfc_df.index, format='%Y')
    rentabilidade_patr.index = pd.to_datetime(rentabilidade_patr.index, format='%Y')
    
    # Concatenate all DataFrames along the columns
    final_df = pd.concat([analise_ampla, pd_verfinanc, df_abs, evolucao_RLL, 
                          pd_verticalPassivo, pd_verticalAtivo,
                          margens_ano, df_prazos, dfc_df, rentabilidade_patr], axis=1)
    final_df['Ativo'] = ticker
    ticker_value_df.append(final_df)
    
    

"""
counter = 0
with pd.ExcelWriter(Path(home, 'Desktop', 'abev.xlsx')) as writer:  
    for i in final_list:
        i.to_excel(writer, sheet_name=str(counter))
        counter+=1
        
# dre_consolidado.to_csv(Path(Path.home(), 'Desktop', 'dreabev.csv'))
df = pd.DataFrame(final_list)
file_json = Path(Path.home(), 'Desktop', 'multiplos_abev.json')
dados_teste = final_list.to_json(orient="split")
with open(file_json, 'w', encoding='utf-8') as f:
    f.write(dados_teste)


counter = 0
for i in final_list:
    counter+=1
    df_ = pd.DataFrame(i)
    json_ = df_.to_json(orient='split')
    
    str_save = 'doc' + str(counter)
    file_json = str(Path(Path.home(), 'Desktop', f'{str_save}.json'))
    # Salvar JSON em arquivos
    with open(file_json, 'w', encoding='utf-8') as f:
        f.write(json_)
           """ 
