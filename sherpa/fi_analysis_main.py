import os
import pandas as pd
from datetime import datetime

from fi_analysis_utils import (
    processar_carteiras, adicionar_taxas_administracao, extrair_cnpjs_sem_taxa,
    adicionar_taxas_manuais, calcular_custos_taxas, analisar_evolucao_custos,
    analisar_fundos_sem_taxa, calcular_taxa_efetiva_fundos_zero_taxa, combinar_taxas_efetivas,
    extrair_pl_taxas, taxas_niveis, plotar_pl_custos_niveis, salvar_variaveis_serial,
    carregar_todos_fundos, plotar_pl_custos_niveis_multi_fundos,
    plotar_pl_custos_niveis_multi_fundos_alterado, calcular_estatisticas_custos,
    gerar_visualizacoes_custos, gerar_tabela_resumo, calcular_estatisticas_fundo,
    gerar_recomendacoes_fundo, gerar_relatorio_fundo, calcular_taxas_efetivas_fundo,
    analisar_taxas_efetivas, gerar_visualizacoes_taxas, integrar_taxas_efetivas,
    analisar_carteira_combinada
)

from fi_analysis_utils import *


def main():
    """
    Função principal que executa a análise completa de fundos.
    
    Esta função coordena todo o processo de análise, desde o carregamento dos dados
    até a geração de relatórios e visualizações.
    """
    try:
        # Configuração inicial
        config = {
            'nome_fundo': 'chimborazo',
            'cnpj_fundo': '54.195.596/0001-51',
            'base_dir': r"C:\Users\guilh\Documents\GitHub\flab\database",
            'limite_arquivos': 30,
            'consolidar': False
        }
        
        # Relações entre fundos
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
        
        # Criar diretórios de saída
        dir_analises = os.path.join(config['base_dir'], 'analises_custos_taxas')
        dir_fundos_sem_taxa = os.path.join(config['base_dir'], 'analises_fundos_sem_taxa')
        dir_taxas_efetivas = os.path.join(config['base_dir'], 'analises_taxas_efetivas')
        dir_graficos = os.path.join(config['base_dir'], 'graficos_fundos_exclusivos')
        
        for dir_path in [dir_analises, dir_fundos_sem_taxa, dir_taxas_efetivas, dir_graficos]:
            os.makedirs(dir_path, exist_ok=True)
        
        # 1. Processar carteiras
        print("Processando carteiras...")
        carteiras = processar_carteiras(
            config['cnpj_fundo'], 
            config['base_dir'], 
            config['limite_arquivos']
        )
        
        if carteiras is None:
            raise ValueError("Falha ao processar carteiras")
        
        # 2. Carregar cadastro de fundos
        print("Carregando cadastro de fundos...")
        arquivo_local = os.path.join(config['base_dir'], 'CAD', 'cad_fi.csv')
        fund_info = pd.read_csv(arquivo_local, sep=';', encoding='ISO-8859-1', low_memory=False)
        
        # 3. Adicionar taxas de administração
        print("Adicionando taxas de administração...")
        carteiras_com_taxas = adicionar_taxas_administracao(carteiras, fund_info)
        
        # 4. Extrair CNPJs de fundos sem taxa
        print("Extraindo CNPJs de fundos sem taxa...")
        cnpjs_sem_taxa = extrair_cnpjs_sem_taxa(carteiras_com_taxas)
        
        # 5. Adicionar taxas manuais
        print("Adicionando taxas manuais...")
        carteiras_com_taxas_manuais = adicionar_taxas_manuais(carteiras_com_taxas, fund_info)
        
        # 6. Calcular custos
        print("Calculando custos...")
        resultados = calcular_custos_taxas(carteiras_com_taxas_manuais, dir_analises)
        
        # 7. Analisar evolução dos custos
        print("Analisando evolução dos custos...")
        analise_custos = analisar_evolucao_custos(resultados, dir_analises)
        
        # 8. Analisar fundos sem taxa
        print("Analisando fundos sem taxa...")
        fundos_sem_taxa = analisar_fundos_sem_taxa(carteiras_com_taxas_manuais, dir_fundos_sem_taxa)
        
        # 9. Calcular taxas efetivas
        print("Calculando taxas efetivas...")
        cnpjs_sem_taxa = list(fundos_sem_taxa.keys())
        taxas_efetivas = calcular_taxa_efetiva_fundos_zero_taxa(
            carteiras_com_taxas_manuais,
            cnpjs_sem_taxa,
            dir_taxas_efetivas,
            base_dir=config['base_dir'],
            limite_arquivos=config['limite_arquivos']
        )
        
        # 10. Ajustar carteiras com taxas efetivas
        print("Ajustando carteiras com taxas efetivas...")
        carteiras_finais = combinar_taxas_efetivas(carteiras_com_taxas_manuais, taxas_efetivas)
        
        # 11. Calcular custos por níveis
        print("Calculando custos por níveis...")
        serie_custos, media_custos = taxas_niveis(
            config['cnpj_fundo'],
            config['base_dir'],
            resultados,
            carteiras_finais
        )
        
        # 12. Preparar dados para visualização
        valor_investido = {k: v['valor_total_investido'] for k, v in resultados.items()}
        
        # 13. Gerar visualizações
        print("Gerando visualizações...")
        plotar_pl_custos_niveis(
            serie_custos,
            valor_investido,
            f"Fundo {config['nome_fundo']}",
            os.path.join(dir_graficos, f"pl_custos_{config['nome_fundo']}.png")
        )
        
        # 14. Serializar resultados
        print("Serializando resultados...")
        salvar_variaveis_serial(
            config['base_dir'],
            serie_custos,
            media_custos,
            valor_investido,
            nome=config['nome_fundo']
        )
        
        # 15. Consolidar dados (opcional)
        if config['consolidar']:
            print("Consolidando dados...")
            lista_fundos = ['chimborazo', 'aconcagua', 'alpamayo']
            serie_custos_consolidado, valor_investido_consolidado = carregar_todos_fundos(
                config['base_dir'],
                lista_fundos
            )
            
            dir_graficos_consolidados = os.path.join(config['base_dir'], 'graficos_fundos_consolidados')
            os.makedirs(dir_graficos_consolidados, exist_ok=True)
            
            plotar_pl_custos_niveis_multi_fundos_alterado(
                serie_custos_consolidado,
                valor_investido_consolidado,
                relacoes_entre_fundos=relacoes_entre_fundos,
                titulo="Fundos Consolidados (Chimborazo, Aconcagua e Alpamayo)",
                caminho_saida=os.path.join(dir_graficos_consolidados, "pl_custos_consolidados.png")
            )
        
        print("Análise concluída com sucesso!")
        
    except Exception as e:
        print(f"Erro durante a execução da análise: {str(e)}")
        raise

if __name__ == "__main__":
    main()

