import os
import pandas as pd
from datetime import datetime
from pathlib import Path


from carteiras_analysis_utils import (
    serializar_resultados_carteira, processar_carteira_completa, categorizar_ativos, analisar_carteira_por_categoria,
    analisar_concentracao_emissores, salvar_dados_processados, gerar_relatorio_evolucao_carteira, executar_analise_carteira_completa,
    serializar_carteira, carregar_carteira_serializada, carregar_carteiras_multiplos_fundos, extrair_informacoes_por_fundo,
    plotar_evolucao_valor_fundos_empilhado, analisar_composicao_consolidada, plotar_composicao_por_fundo, 
    plotar_distribuicao_categoria_consolidada, gerar_relatorio_consolidado, consolidar_carteiras_fundos, 
    integrar_analise_consolidacao, classificar_produtos_por_objetivo, gerar_relatorio_classificacao_objetivos,
    gerar_grafico_evolucao_objetivos, histograma_objetivos_horizontal, gerar_histograma_alocacao_objetivos,
    extrair_retornos_fundos, processar_dados, criar_grafico, gerar_histogramas_objetivos_completo
)

from carteiras_analysis_utils import *

cnpj_fundo = '32.320.609/0001-34'
nome_fundo = "huayna"
base_dir = r"C:\Users\guilh\Documents\GitHub\flab\database"

# Relações entre fundos (exemplo para usar na consolidação)
relacoes_entre_fundos = {
    'alpamayo': {
        'investido_por': {
            'chimborazo': {
                '2024-10': 98000000,
                '2024-11': 97000000,
                '2024-12': 90000000,
                '2025-01': 94000000,
                '2025-02': 92750000
            }
        }
    }
}

resultados = executar_analise_carteira_completa(
        cnpj_fundo=cnpj_fundo,
        nome_fundo=nome_fundo,
        base_dir=base_dir,
        limite_arquivos=30,
        consolidar=True,  
        lista_fundos=['chimborazo', 'aconcagua', 'alpamayo', 'huayna'],
        relacoes_entre_fundos=relacoes_entre_fundos)

resultado = consolidar_carteiras_fundos(
    lista_fundos=['chimborazo', 'aconcagua', 'alpamayo', 'huayna'], 
    base_dir=base_dir, 
    relacoes_entre_fundos=relacoes_entre_fundos)

# Evolução das categorias no tempo
lista_cnpj_objetivo = [
    "Ganho\t41.535.122/0001-60",
    "Ganho\t32.311.914/0001-60",
    "Ganho\t12.138.862/0001-64",
    "Manutenção\t12.809.201/0001-13",
    "Manutenção\t29.993.554/0001-19",
    "Ganho\t24.546.223/0001-17",
    "Ganho\t28.260.530/0001-98",
    "Ganho\t14.096.710/0001-71",
    "Ganho\t33.019.558/0001-78",
    "Ganho\t38.000.887/0001-90",
    "Ganho\t43.551.227/0001-38",
    "Ganho\t17.329.489/0001-42",
    "Ganho\t26.324.227/0001-86",
    "Ganho\t16.478.741/0001-12",
    "Ganho\t42.317.906/0001-84",
    "Manutenção\t07.096.546/0001-37",
    "Manutenção\t55.419.784/0001-89",
    "Manutenção\t24.546.223/0001-17",
    "Ganho\t41.287.689/0001-64",
    "Ganho\t14.096.710/0001-71",
    "Ganho\t12.809.201/0001-13",
    "Ganho\t31.820.746/0001-75",
    "Ganho\t28.653.719/0001-40",
    "Ganho\t28.260.530/0001-98",
    "Ganho\t26.324.227/0001-86",
    "Ganho\t26.277.663/0001-41",
    "Preservação\t21.407.105/0001-30",
    "Ganho\t19.412.573/0001-50",
    "Ganho\t19.294.718/0001-66",
    "Ganho\t18.489.912/0001-34",
    "Preservação\t18.138.913/0001-34",

    
]


classificacao_cnpj = criar_mapeamento_cnpj_objetivo(lista_cnpj_objetivo)
carteiras_consolidadas = resultado['carteiras_consolidadas']
# carteiras_consolidadas['2025-02'] = carteiras_consolidadas['2025-01']


# Por objetivos
base_dir = r"C:\Users\guilh\Documents\GitHub\flab\database"
datas_disponiveis = sorted(list(resultado['carteiras_consolidadas'].keys()))

datas_analise = []
data_atual = None

for data in datas_disponiveis:
    try:
        data_dt = datetime.strptime(data, '%Y-%m')
        
        # Se é a primeira data ou se passou pelo menos 6 meses desde a última data
        if data_atual is None or (data_dt.year - data_atual.year) * 12 + data_dt.month - data_atual.month >= 6:
            datas_analise.append(data)
            data_atual = data_dt
    except ValueError:
        continue


carteiras_classificadas = {}
for data, df in carteiras_consolidadas.items():
    # Classificar cada carteira usando a função original
    carteira_classificada = classificar_produtos_por_objetivo(
        df, 
        periodo=data, 
        classificacao_cnpj=classificacao_cnpj, 
        solicitar_input=False  # Desativar input para processamento em lote
    )
    carteiras_classificadas[data] = carteira_classificada


### necessario gerar uma funcao de gerar curvas que captura essas carteiras classificadas nesse formato. A atual nao faz isso
















# results = gerar_grafico_evolucao_objetivos_separado(resultados_por_data, datas_analise=datas_analise, 
#                                                     base_dir=base_dir, nome_arquivo="evolucao_objetivos.png",  
#                                                     titulo="Evolução da Alocação por Objetivo")


caminho_grafico, percentuais_preservacao, percentuais_manutencao, percentuais_ganho = gerar_grafico_evolucao_objetivos(
    carteiras_classificadas, 
    base_dir, 
    classificacao_cnpj,
    datas_analise=datas_analise,
    nome_arquivo="evolucao_objetivos_cnpj.png", 
    titulo="Evolução da Alocação por Objetivo")


# Histograma horizontal para ultimo periodo
resultados = gerar_histograma_alocacao_objetivos(
    carteiras_consolidadas=carteiras_consolidadas,
    classificacao_cnpj=classificacao_cnpj,
    data_analise="2025-01",  # ou None para usar a data mais recente
    mostrar_grafico=True,
    salvar_arquivo="alocacao_objetivos.png"
)




resultados_objetivos = gerar_histogramas_objetivos_completo(
    df_carteira=carteiras_classificadas['2025-01'],               # Seu DataFrame original
    classificacao_cnpj=classificacao_cnpj, # Sua classificação de CNPJs
    periodo="2025-02")




print(f"Datas selecionadas para análise: {datas_analise}")
caminho_grafico = gerar_grafico_evolucao_objetivos(
    resultado['carteiras_consolidadas'],
    base_dir,
    datas_analise=datas_analise,
    titulo="Evolução da Alocação por Objetivo de Investimento"
)


# Período para análise
base_dir = r"C:\Users\guilh\Documents\GitHub\flab\database"
lista_objetivos = []
for periodo,_ in resultado['carteiras_consolidadas'].items():

    carteiras_consolidadas = resultado['carteiras_consolidadas'][periodo]

    df_classificado = classificar_produtos_por_objetivo(carteiras_consolidadas, periodo=periodo)
    lista_objetivos.append(df_classificado)
    
df_analysis = pd.concat(lista_objetivos)
df_analysis.to_excel(Path(Path.home(), 'Desktop', 'carteiras_consolidadas.xlsx'))


periodos = sorted(list(resultado['carteiras_consolidadas'].keys()))
ultimo_periodo = periodos[-1]

print(f"Gerando histograma horizontal para o período: {ultimo_periodo}")

# # Gerar o histograma
# resultados = histograma_objetivos_horizontal(
#     carteiras_consolidadas=resultado['carteiras_consolidadas'],
#     periodo=ultimo_periodo,
#     mostrar_grafico=True,
#     salvar_arquivo="histograma_objetivos_horizontal.png"
# )



# BlOCO PARA RETORNOS COMPARADOS


# MÉTODO SEM BENCHMARK



caminho_base = Path(Path.home(), 'Documents', 'GitHub', 'flab', 'database', 'INF_DIARIO')
periodo_inicial = '2021-01'
periodo_final = '2025-02'
find_cnpjs = ['05.849.352/0001-30', '54.195.596/0001-51', '56.430.872/0001-44', '32.320.609/0001-34']

# Extrair retornos
returns_f, total_returns, pl = extrair_retornos_fundos(
    caminho_base=caminho_base,
    periodo_inicial=periodo_inicial,
    periodo_final=periodo_final,
    filtro_cnpj=find_cnpjs
)

df = returns_f.copy()
df_normalizado, estatisticas, colunas = processar_dados(df)
plt_obj = criar_grafico(df_normalizado, estatisticas, colunas)





nomes_fundos = {
    '05.849.352/0001-30': 'Aconcagua',
    '32.320.609/0001-34': 'Huayna',
    '54.195.596/0001-51': 'Chimborazo',
    '56.430.872/0001-44': 'Alpamayo'
}


relacoes_entre_fundos = {
    '56.430.872/0001-44': {  # Alpamayo
        'investido_por': {
            '54.195.596/0001-51': {  # Chimborazo
                '2024-10': 98000000,
                '2024-11': 97000000,
                '2024-12': 90000000,
                '2025-01': 94000000,
                '2025-02': 92750000
            }
        }
    }
}


def calcular_retorno_ponderado(df):
    # Convertemos a data para datetime caso não esteja
    df['Data'] = pd.to_datetime(df['Data'])
    
    # Ordenamos o DataFrame por data
    df = df.sort_values('Data')
    
    # Criamos um DataFrame para armazenar os resultados
    resultados = []
    
    # Processamos cada fundo separadamente
    for cnpj in df['CNPJ_FUNDO'].unique():
        fundo_df = df[df['CNPJ_FUNDO'] == cnpj].copy()
        
        # Adicionamos colunas para calcular o retorno
        fundo_df['PL_Anterior'] = fundo_df['PL'].shift(1)
        
        # Calculamos o retorno diário ajustado por fluxos (captações e resgates)
        fundo_df['Retorno_Diario'] = (fundo_df['PL'] - fundo_df['PL_Anterior'] - 
                                      fundo_df['Captacao'] + fundo_df['Resgate']) / fundo_df['PL_Anterior']
        
        # Substituímos NaN (primeiro dia) por 0
        fundo_df['Retorno_Diario'] = fundo_df['Retorno_Diario'].fillna(0)
        
        # Calculamos o retorno acumulado
        fundo_df['Retorno_Acumulado'] = (1 + fundo_df['Retorno_Diario']).cumprod() - 1
        
        # Adicionamos o nome do fundo
        fundo_df['Nome_Fundo'] = nomes_fundos.get(cnpj, cnpj)
        
        # Adicionamos ao resultado
        resultados.append(fundo_df)
    
    # Combinamos todos os resultados
    resultado_combinado = pd.concat(resultados)
    
    # Ajustamos o PL para considerar as relações entre fundos
    resultado_combinado = ajustar_pl_por_relacoes(resultado_combinado)
    
    # Calculamos o PL consolidado por data
    pl_consolidado = resultado_combinado.groupby('Data')['PL_Ajustado'].sum().reset_index()
    pl_consolidado.rename(columns={'PL_Ajustado': 'PL_Total'}, inplace=True)
    
    # Unimos o PL consolidado com os dados originais
    resultado_final = pd.merge(resultado_combinado, pl_consolidado, on='Data')
    
    # Calculamos o peso de cada fundo no PL total
    resultado_final['Peso'] = resultado_final['PL_Ajustado'] / resultado_final['PL_Total']
    
    # Calculamos a contribuição ponderada de cada fundo
    resultado_final['Contribuicao'] = resultado_final['Retorno_Diario'] * resultado_final['Peso']
    
    # Calculamos o retorno consolidado diário
    retorno_consolidado = resultado_final.groupby('Data')['Contribuicao'].sum().reset_index()
    retorno_consolidado.rename(columns={'Contribuicao': 'Retorno_Diario_Consolidado'}, inplace=True)
    
    # Calculamos o retorno acumulado consolidado
    retorno_consolidado['Retorno_Acumulado_Consolidado'] = (1 + retorno_consolidado['Retorno_Diario_Consolidado']).cumprod() - 1
    
    return resultado_final, retorno_consolidado

def ajustar_pl_por_relacoes(df):
    # Adicionamos uma coluna para armazenar o PL ajustado
    df['PL_Ajustado'] = df['PL']
    
    # Para cada relação entre fundos
    for fundo_investido, info in relacoes_entre_fundos.items():
        for relacao_tipo, relacionamentos in info.items():
            if relacao_tipo == 'investido_por':
                for fundo_investidor, valores_mensais in relacionamentos.items():
                    # Para cada mês, ajustamos o PL
                    for mes, valor in valores_mensais.items():
                        # Convertemos o mês para um formato que possamos usar
                        ano, mes = mes.split('-')
                        
                        # Filtramos as datas no mês específico
                        mascara_mes = (df['Data'].dt.year == int(ano)) & (df['Data'].dt.month == int(mes))
                        
                        # Ajustamos o PL do fundo investidor
                        mascara_investidor = (df['CNPJ_FUNDO'] == fundo_investidor) & mascara_mes
                        df.loc[mascara_investidor, 'PL_Ajustado'] = df.loc[mascara_investidor, 'PL'] - valor
                        
                        # O fundo investido já tem seu próprio PL, então não precisamos adicionar
    
    return df

def plotar_retorno_ponderado(resultado_final, retorno_consolidado):
    # Amostragem mensal para melhor visualização
    retorno_consolidado['Mes'] = retorno_consolidado['Data'].dt.to_period('M')
    retorno_mensal = retorno_consolidado.groupby('Mes').last().reset_index()
    retorno_mensal['Data'] = retorno_mensal['Mes'].dt.to_timestamp()
    
    # Calculamos o PL mensal
    resultado_final['Mes'] = resultado_final['Data'].dt.to_period('M')
    pl_mensal = resultado_final.groupby(['Mes', 'Nome_Fundo'])['PL_Ajustado'].last().reset_index()
    pl_mensal_total = pl_mensal.groupby('Mes')['PL_Ajustado'].sum().reset_index()
    pl_mensal_total['Data'] = pl_mensal_total['Mes'].dt.to_timestamp()
    
    # Criamos o gráfico
    fig, ax1 = plt.subplots(figsize=(14, 8))
    
    # Barras para o PL total
    ax1.bar(pl_mensal_total['Data'], pl_mensal_total['PL_Ajustado'], 
            width=20, color='#404040', alpha=0.6, label='PL Total Ajustado')
    
    # Configuração do eixo Y esquerdo (PL)
    ax1.set_xlabel('Data', fontsize=12)
    ax1.set_ylabel('PL Total (R$)', fontsize=12, color='#404040')
    ax1.tick_params(axis='y', labelcolor='#404040')
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'R$ {x/1e6:.1f}M'))
    
    # Eixo Y direito para o retorno acumulado
    ax2 = ax1.twinx()
    ax2.plot(retorno_mensal['Data'], retorno_mensal['Retorno_Acumulado_Consolidado'], 
              color='#003366', linewidth=3, label='Retorno Acumulado Consolidado')
    
    # Configuração do eixo Y direito (Retorno)
    ax2.set_ylabel('Retorno Acumulado (%)', fontsize=12, color='#0D47A1')
    ax2.tick_params(axis='y', labelcolor='#0D47A1')
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x*100:.1f}%'))
    
    # Ajustamos o eixo X
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%Y'))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=45)
    
    # Título e linha de referência
    plt.title('Evolução do PL Total e Retorno Acumulado Consolidado', fontsize=16)
    ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.3)
    
    # Legenda combinada
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    # Estatísticas
    primeiro_dia = retorno_consolidado['Data'].min()
    ultimo_dia = retorno_consolidado['Data'].max()
    pl_inicial = resultado_final[resultado_final['Data'] == primeiro_dia]['PL_Ajustado'].sum()
    pl_final = resultado_final[resultado_final['Data'] == ultimo_dia]['PL_Ajustado'].sum()
    retorno_total = retorno_consolidado.loc[retorno_consolidado['Data'] == ultimo_dia, 'Retorno_Acumulado_Consolidado'].values[0]
    
    # Cálculo do retorno anualizado
    dias_totais = (ultimo_dia - primeiro_dia).days
    dias_uteis_estimados = dias_totais * (251 / 365.25)
    anos_uteis = dias_uteis_estimados / 251
    retorno_anualizado = ((1 + retorno_total) ** (1/anos_uteis)) - 1
    
    # Adicionamos as estatísticas como texto
    stats_text = f"Estatísticas:\n"
    stats_text += f"Período: {primeiro_dia.strftime('%d/%m/%Y')} a {ultimo_dia.strftime('%d/%m/%Y')}\n"
    stats_text += f"Retorno Acumulado: {retorno_total*100:.2f}%\n"
    stats_text += f"Retorno Anualizado: {retorno_anualizado*100:.2f}%\n"
    
    # Texto explicativo sobre o ajuste
    adj_text = f"Nota: Os valores de PL foram ajustados para evitar dupla contagem.\n"
    
    plt.figtext(0.25, 0.7, stats_text + "\n" + adj_text, fontsize=10, 
                bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.5'))
    
    plt.tight_layout()
    plt.show()
    return fig

# Função principal
def analisar_retorno_ponderado(df, arquivo_saida=None):
    # Calculamos o retorno ponderado
    resultado_final, retorno_consolidado = calcular_retorno_ponderado(df)
    
    # Plotamos o gráfico
    fig = plotar_retorno_ponderado(resultado_final, retorno_consolidado)
    
    # Salvamos ou mostramos a figura
    if arquivo_saida:
        fig.savefig(arquivo_saida, dpi=300, bbox_inches='tight')
        print(f"Gráfico salvo em {arquivo_saida}")
    else:
        plt.show()
    
    return resultado_final, retorno_consolidado

# Para usar a função:
resultado_final, retorno_consolidado = analisar_retorno_ponderado(pl, "retorno_ponderado.png")




### MÉTODO COM BENCHMARK


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Definição dos nomes dos fundos
nomes_fundos = {
    '05.849.352/0001-30': 'Aconcagua',
    '32.320.609/0001-34': 'Huayna',
    '54.195.596/0001-51': 'Chimborazo',
    '56.430.872/0001-44': 'Alpamayo'
}

# Definição das relações entre fundos
relacoes_entre_fundos = {
    '56.430.872/0001-44': {  # Alpamayo
        'investido_por': {
            '54.195.596/0001-51': {  # Chimborazo
                '2024-10': 98000000,
                '2024-11': 97000000,
                '2024-12': 90000000,
                '2025-01': 94000000,
                '2025-02': 92750000
            }
        }
    }
}

def calcular_retorno_ponderado(df):
    """
    Calcula o retorno ponderado dos fundos.
    
    Args:
        df: DataFrame com os dados dos fundos
        
    Returns:
        Tuple contendo (resultado_final, retorno_consolidado)
    """
    # Convertemos a data para datetime caso não esteja
    df['Data'] = pd.to_datetime(df['Data'])
    
    # Ordenamos o DataFrame por data
    df = df.sort_values('Data')
    
    # Criamos um DataFrame para armazenar os resultados
    resultados = []
    
    # Processamos cada fundo separadamente
    for cnpj in df['CNPJ_FUNDO'].unique():
        fundo_df = df[df['CNPJ_FUNDO'] == cnpj].copy()
        
        # Adicionamos colunas para calcular o retorno
        fundo_df['PL_Anterior'] = fundo_df['PL'].shift(1)
        
        # Calculamos o retorno diário ajustado por fluxos (captações e resgates)
        fundo_df['Retorno_Diario'] = (fundo_df['PL'] - fundo_df['PL_Anterior'] - 
                                      fundo_df['Captacao'] + fundo_df['Resgate']) / fundo_df['PL_Anterior']
        
        # Substituímos NaN (primeiro dia) por 0
        fundo_df['Retorno_Diario'] = fundo_df['Retorno_Diario'].fillna(0)
        
        # Calculamos o retorno acumulado
        fundo_df['Retorno_Acumulado'] = (1 + fundo_df['Retorno_Diario']).cumprod() - 1
        
        # Adicionamos o nome do fundo
        fundo_df['Nome_Fundo'] = nomes_fundos.get(cnpj, cnpj)
        
        # Adicionamos ao resultado
        resultados.append(fundo_df)
    
    # Combinamos todos os resultados
    resultado_combinado = pd.concat(resultados)
    
    # Ajustamos o PL para considerar as relações entre fundos
    resultado_combinado = ajustar_pl_por_relacoes(resultado_combinado)
    
    # Calculamos o PL consolidado por data
    pl_consolidado = resultado_combinado.groupby('Data')['PL_Ajustado'].sum().reset_index()
    pl_consolidado.rename(columns={'PL_Ajustado': 'PL_Total'}, inplace=True)
    
    # Unimos o PL consolidado com os dados originais
    resultado_final = pd.merge(resultado_combinado, pl_consolidado, on='Data')
    
    # Calculamos o peso de cada fundo no PL total
    resultado_final['Peso'] = resultado_final['PL_Ajustado'] / resultado_final['PL_Total']
    
    # Calculamos a contribuição ponderada de cada fundo
    resultado_final['Contribuicao'] = resultado_final['Retorno_Diario'] * resultado_final['Peso']
    
    # Calculamos o retorno consolidado diário
    retorno_consolidado = resultado_final.groupby('Data')['Contribuicao'].sum().reset_index()
    retorno_consolidado.rename(columns={'Contribuicao': 'Retorno_Diario_Consolidado'}, inplace=True)
    
    # Calculamos o retorno acumulado consolidado
    retorno_consolidado['Retorno_Acumulado_Consolidado'] = (1 + retorno_consolidado['Retorno_Diario_Consolidado']).cumprod() - 1
    
    return resultado_final, retorno_consolidado

def ajustar_pl_por_relacoes(df):
    """
    Ajusta o PL para evitar dupla contagem entre fundos relacionados.
    
    Args:
        df: DataFrame com os dados dos fundos
        
    Returns:
        DataFrame com o PL ajustado
    """
    # Adicionamos uma coluna para armazenar o PL ajustado
    df['PL_Ajustado'] = df['PL']
    
    # Para cada relação entre fundos
    for fundo_investido, info in relacoes_entre_fundos.items():
        for relacao_tipo, relacionamentos in info.items():
            if relacao_tipo == 'investido_por':
                for fundo_investidor, valores_mensais in relacionamentos.items():
                    # Para cada mês, ajustamos o PL
                    for mes, valor in valores_mensais.items():
                        # Convertemos o mês para um formato que possamos usar
                        ano, mes = mes.split('-')
                        
                        # Filtramos as datas no mês específico
                        mascara_mes = (df['Data'].dt.year == int(ano)) & (df['Data'].dt.month == int(mes))
                        
                        # Ajustamos o PL do fundo investidor
                        mascara_investidor = (df['CNPJ_FUNDO'] == fundo_investidor) & mascara_mes
                        df.loc[mascara_investidor, 'PL_Ajustado'] = df.loc[mascara_investidor, 'PL'] - valor
    
    return df

def plotar_retorno_ponderado_com_benchmarks(resultado_final, retorno_consolidado, benchmarks_df):
    """
    Plota o gráfico de retorno ponderado incluindo benchmarks para comparação.
    
    Args:
        resultado_final: DataFrame com os resultados finais dos fundos
        retorno_consolidado: DataFrame com o retorno consolidado
        benchmarks_df: DataFrame com os benchmarks
        
    Returns:
        Figura matplotlib com o gráfico
    """
    # Garantir que a data está no formato datetime
    retorno_consolidado['Data'] = pd.to_datetime(retorno_consolidado['Data'])
    resultado_final['Data'] = pd.to_datetime(resultado_final['Data'])
    benchmarks_df.index = pd.to_datetime(benchmarks_df.index)
    
    # Amostragem mensal para melhor visualização
    retorno_consolidado['Mes'] = retorno_consolidado['Data'].dt.to_period('M')
    retorno_mensal = retorno_consolidado.groupby('Mes').last().reset_index()
    retorno_mensal['Data'] = retorno_mensal['Mes'].dt.to_timestamp()
    
    # Calculamos o PL mensal
    resultado_final['Mes'] = resultado_final['Data'].dt.to_period('M')
    pl_mensal = resultado_final.groupby(['Mes', 'Nome_Fundo'])['PL_Ajustado'].last().reset_index()
    pl_mensal_total = pl_mensal.groupby('Mes')['PL_Ajustado'].sum().reset_index()
    pl_mensal_total['Data'] = pl_mensal_total['Mes'].dt.to_timestamp()
    
    # Criamos o gráfico
    fig, ax1 = plt.subplots(figsize=(14, 8))
    
    # Barras para o PL total
    ax1.bar(pl_mensal_total['Data'], pl_mensal_total['PL_Ajustado'], 
            width=20, color='#404040', alpha=0.6, label='PL Total Ajustado')
    
    # Configuração do eixo Y esquerdo (PL)
    ax1.set_xlabel('Data', fontsize=12)
    ax1.set_ylabel('PL Total (R$)', fontsize=12, color='#404040')
    ax1.tick_params(axis='y', labelcolor='#404040')
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'R$ {x/1e6:.1f}M'))
    
    # Eixo Y direito para o retorno acumulado e benchmarks
    ax2 = ax1.twinx()
    
    # Plotando o retorno acumulado consolidado
    ax2.plot(retorno_mensal['Data'], retorno_mensal['Retorno_Acumulado_Consolidado'], 
             color='black', linewidth=2.5, linestyle='--', label='Retorno Acumulado Consolidado')
    
    # Cores para os benchmarks conforme especificadas
    cores_benchmarks = {
        'cdi': '#104E8B',    # Azul oceano
        'ibov': '#8B0000',   # Vermelho escuro
        'imab': '#8B4500'    # Laranja escuro
    }
    
    # Para cada benchmark, plotamos no gráfico
    for benchmark, cor in cores_benchmarks.items():
        if benchmark in benchmarks_df.columns:
            # Criar série de datas mensais para o benchmark
            bench_monthly = benchmarks_df[benchmark].resample('M').last()
            
            # Plotar o benchmark (já está acumulado)
            ax2.plot(bench_monthly.index, bench_monthly.values, 
                    color=cor, linewidth=2, label=benchmark.upper())
    
    # Configuração do eixo Y direito (Retorno)
    ax2.set_ylabel('Retorno Acumulado (%)', fontsize=12, color='#0D47A1')
    ax2.tick_params(axis='y', labelcolor='#0D47A1')
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x*100:.1f}%'))
    
    # Ajustamos o eixo X
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%Y'))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=45)
    
    # Título e linha de referência
    plt.title('Evolução do PL Total e Retorno Acumulado vs Benchmarks', fontsize=16)
    ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.3)
    
    # Legenda combinada
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    # Estatísticas
    primeiro_dia = retorno_consolidado['Data'].min()
    ultimo_dia = retorno_consolidado['Data'].max()
    retorno_total = retorno_consolidado.loc[retorno_consolidado['Data'] == ultimo_dia, 'Retorno_Acumulado_Consolidado'].values[0]
    
    # Cálculo do retorno anualizado
    dias_totais = (ultimo_dia - primeiro_dia).days
    dias_uteis_estimados = dias_totais * (251 / 365.25)
    anos_uteis = dias_uteis_estimados / 251
    retorno_anualizado = ((1 + retorno_total) ** (1/anos_uteis)) - 1
    
    # Estatísticas de comparação com benchmarks
    stats_text = f"Estatísticas:\n"
    stats_text += f"Período: {primeiro_dia.strftime('%d/%m/%Y')} a {ultimo_dia.strftime('%d/%m/%Y')}\n"
    stats_text += f"Retorno Acumulado: {retorno_total*100:.2f}%\n"
    stats_text += f"Retorno Anualizado: {retorno_anualizado*100:.2f}%\n\n"
    
    # Texto explicativo sobre o ajuste
    adj_text = f"Nota: Os valores de PL foram ajustados para evitar dupla contagem.\n"
    
    plt.figtext(0.25, 0.7, stats_text + "\n" + adj_text, fontsize=10, 
                bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.5'))
    
    plt.tight_layout()
    return fig

def analisar_retorno_ponderado_com_benchmarks(df, benchmarks_df, arquivo_saida=None):
    """
    Analisa o retorno ponderado e compara com benchmarks.
    
    Args:
        df: DataFrame com os dados dos fundos
        benchmarks_df: DataFrame com os benchmarks
        arquivo_saida: Caminho para salvar o gráfico (opcional)
        
    Returns:
        Tuple contendo (resultado_final, retorno_consolidado)
    """
    # Calculamos o retorno ponderado
    resultado_final, retorno_consolidado = calcular_retorno_ponderado(df)
    
    # Plotamos o gráfico com benchmarks
    fig = plotar_retorno_ponderado_com_benchmarks(resultado_final, retorno_consolidado, benchmarks_df)
    
    # Salvamos ou mostramos a figura
    if arquivo_saida:
        fig.savefig(arquivo_saida, dpi=300, bbox_inches='tight')
        print(f"Gráfico salvo em {arquivo_saida}")
    else:
        plt.show()
    
    return resultado_final, retorno_consolidado

# Exemplo de uso
def executar_analise(pl_df, test_df):
    """
    Executa a análise de retorno ponderado com benchmarks.
    
    Args:
        pl_df: DataFrame com os dados dos fundos
        test_df: DataFrame com os benchmarks
        
    Returns:
        Tuple contendo (resultado_final, retorno_consolidado)
    """
    # Chamar a função principal de análise
    resultado_final, retorno_consolidado = analisar_retorno_ponderado_com_benchmarks(
        pl_df, 
        test_df, 
        "retorno_ponderado_com_benchmarks.png"
    )
    
    return resultado_final, retorno_consolidado




path_selic = Path(Path.home(), 'Desktop', 'selic.pkl')
# pickle.dump(selic, open(path_selic, 'wb'))
selic = pickle.load(open(path_selic, 'rb'))

cdi = pd.DataFrame(selic[selic.index>='2021-01-04'])
# cdi = pd.DataFrame(cdi.add(1).cumprod()-1)
cdi.reset_index(inplace=True)
cdi.columns = ['Data', 'cdi']


data_e = Path(Path.home(), 'Desktop', 'benchmark.xlsx')
data_ed = pd.read_excel(data_e)
data_ed.set_index('Data', inplace=True)
data_ed = data_ed.pct_change()
data_ed.reset_index(inplace=True)

test = pd.merge(data_ed, cdi, on='Data')

test.set_index('Data', inplace=True)
test = test.add(1).cumprod()-1

# Para usar na prática, basta chamar a função executar_analise com os DataFrames fornecidos:
resultado_final, retorno_consolidado = executar_analise(pl, test)


