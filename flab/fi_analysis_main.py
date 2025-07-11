import os
import pandas as pd

from fi_analysis_utils import (
    processar_carteiras, adicionar_taxas_administracao, extrair_cnpjs_sem_taxa,
    adicionar_taxas_manuais, calcular_custos_taxas, analisar_evolucao_custos,
    analisar_fundos_sem_taxa, calcular_taxa_efetiva_fundos_zero_taxa, combinar_taxas_efetivas,
    extrair_pl_taxas, taxas_niveis, plotar_pl_custos_niveis, salvar_variaveis_serial,
    carregar_todos_fundos, plotar_pl_custos_niveis_multi_fundos,
    plotar_pl_custos_niveis_multi_fundos_alterado
)

# Config inicial
nome_fundo = 'aconcagua'
cnpj_fundo = '54.195.596/0001-51'
base_dir = r"C:\Users\guilh\Documents\GitHub\flab\database"  
limite_arquivos = 30
consolidar = False
relacoes_entre_fundos = {
    'alpamayo': {
        'investido_por': {
            'chimborazo': {
                # O Chimborazo diminuiu sua participação no Alpamayo com o tempo
                '2024-10': 98000000,  # Início: participação alta do Chimborazo (quase 100%)
                '2024-11': 97000000,
                '2024-12': 90000000,
                '2025-01': 94000000,
                '2025-02': 92750000   # Final: participação menor do Chimborazo (≈96.6%)
            }
        }
    }
}

# Processar carteiras
carteiras = processar_carteiras(cnpj_fundo, base_dir, limite_arquivos)

# Carregar cadastro de fundos
arquivo_local = os.path.join(base_dir, 'CAD', 'cad_fi.csv')
fund_info = pd.read_csv(arquivo_local, sep=';', encoding='ISO-8859-1', low_memory=False)

# Adicionar taxas de administração
carteiras_com_taxas = adicionar_taxas_administracao(carteiras, fund_info)

# Extrai CNPJs de fundos sem taxa
cnpjs_sem_taxa = extrair_cnpjs_sem_taxa(carteiras_com_taxas)

# Adicionar taxas manuais
carteiras_com_taxas_manuais = adicionar_taxas_manuais(carteiras_com_taxas, fund_info)

# Calcular custos
dir_analises = os.path.join(base_dir, 'analises_custos_taxas')
resultados = calcular_custos_taxas(carteiras_com_taxas_manuais, dir_analises)

# Analisar evolução dos custos
analisar_evolucao_custos(resultados, dir_analises)

# Analisar fundos sem taxa
dir_analises = os.path.join(base_dir, 'analises_fundos_sem_taxa')
fundos_sem_taxa = analisar_fundos_sem_taxa(carteiras_com_taxas_manuais, dir_analises)

# Calcular a taxa efetiva para esses fundos
cnpjs_sem_taxa = list(fundos_sem_taxa.keys())
dir_analises = os.path.join(base_dir, 'analises_taxas_efetivas')
taxas_efetivas = calcular_taxa_efetiva_fundos_zero_taxa(
    carteiras_com_taxas_manuais, 
    cnpjs_sem_taxa, 
    dir_analises,
    base_dir=base_dir,
    limite_arquivos=limite_arquivos
)

# Ajustar carteiras com taxas efetivas
carteiras_finais = combinar_taxas_efetivas(carteiras_com_taxas_manuais, taxas_efetivas)

# Custos por niveis
serie_custos, media_custos = taxas_niveis(cnpj_fundo, base_dir, resultados, carteiras_finais)
valor_investido = {k: v['valor_total_investido'] for k,v in resultados.items()}
dir_graficos = os.path.join(base_dir, 'graficos_fundos_exclusivos')
os.makedirs(dir_graficos, exist_ok=True)
plotar_pl_custos_niveis(serie_custos, valor_investido, f"Fundo {nome_fundo}", os.path.join(dir_graficos, f"pl_custos_{nome_fundo}.png"))

# Serializar
salvar_variaveis_serial(base_dir, serie_custos, media_custos, valor_investido, nome=f'{nome_fundo}')


# Consolidar dados (apenas quando rorando o ultimo FE disponivel)
if consolidar:
    
    lista_fundos = ['chimborazo', 'aconcagua', 'alpamayo']
    serie_custos_consolidado, valor_investido_consolidado = carregar_todos_fundos(base_dir, lista_fundos)
    
    # Criar diretório para os gráficos
    dir_graficos = os.path.join(base_dir, 'graficos_fundos_consolidados')
    os.makedirs(dir_graficos, exist_ok=True)
    
    # Gerar o gráfico
    fig = plotar_pl_custos_niveis_multi_fundos_alterado(
        serie_custos_consolidado,
        valor_investido_consolidado, 
        relacoes_entre_fundos=relacoes_entre_fundos,
        titulo="Fundos Consolidados (Chimborazo, Aconcagua e Alpamayo)", 
        caminho_saida=os.path.join(dir_graficos, "pl_custos_consolidados.png")
    )

