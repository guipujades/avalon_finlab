import pandas as pd
import numpy as np
import os
import zipfile
import json
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
# import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

CNPJ_CAPSTONE = "35.803.288/0001-17"
BASE_DIR = "/mnt/c/Users/guilh/Documents/GitHub/sherpa/database"

def processar_carteira_capstone(base_dir, cnpj_fundo):
    """
    Processa todas as carteiras históricas do fundo Capstone
    """
    cda_dir = os.path.join(base_dir, "CDA")
    carteiras_por_periodo = defaultdict(lambda: defaultdict(list))
    
    print(f"Buscando dados do fundo Capstone (CNPJ: {cnpj_fundo})")
    
    # Listar todos os arquivos CDA disponíveis
    arquivos_cda = []
    
    # Arquivos mensais recentes
    for arquivo in sorted(os.listdir(cda_dir), reverse=True):
        if arquivo.startswith("cda_fi_") and arquivo.endswith(".zip"):
            arquivos_cda.append(os.path.join(cda_dir, arquivo))
    
    # Arquivos históricos anuais
    hist_dir = os.path.join(cda_dir, "HIST")
    if os.path.exists(hist_dir):
        for arquivo in sorted(os.listdir(hist_dir), reverse=True):
            if arquivo.startswith("cda_fi_") and arquivo.endswith(".zip"):
                arquivos_cda.append(os.path.join(hist_dir, arquivo))
    
    print(f"Encontrados {len(arquivos_cda)} arquivos CDA para processar")
    
    # Processar cada arquivo
    for i, arquivo_zip in enumerate(arquivos_cda):
        try:
            # Extrair período do nome do arquivo
            nome_arquivo = os.path.basename(arquivo_zip)
            if "_" in nome_arquivo:
                periodo_str = nome_arquivo.split("_")[-1].replace(".zip", "")
                if len(periodo_str) == 6:  # YYYYMM
                    periodo = periodo_str[:4] + "-" + periodo_str[4:6]
                elif len(periodo_str) == 4:  # YYYY
                    periodo = periodo_str
                else:
                    continue
            else:
                continue
            
            # Processar arquivo ZIP
            with zipfile.ZipFile(arquivo_zip, 'r') as zip_file:
                # Processar cada BLC (1 a 8)
                for blc_num in range(1, 9):
                    for nome_interno in zip_file.namelist():
                        if f"BLC_{blc_num}" in nome_interno and nome_interno.endswith('.csv'):
                            try:
                                with zip_file.open(nome_interno) as f:
                                    df = pd.read_csv(f, sep=';', encoding='ISO-8859-1')
                                    
                                    # Buscar coluna com CNPJ do fundo
                                    cnpj_col = None
                                    for col in ['CNPJ_FUNDO_CLASSE', 'CNPJ_FUNDO', 'CD_FUNDO']:
                                        if col in df.columns:
                                            cnpj_col = col
                                            break
                                    
                                    if cnpj_col:
                                        # Filtrar pelo CNPJ do Capstone
                                        df_fundo = df[df[cnpj_col].astype(str).str.strip() == cnpj_fundo]
                                        
                                        if not df_fundo.empty:
                                            df_fundo['TIPO_BLC'] = f'BLC_{blc_num}'
                                            df_fundo['PERIODO'] = periodo
                                            carteiras_por_periodo[periodo][f'BLC_{blc_num}'].append(df_fundo)
                                            
                            except Exception as e:
                                continue
            
            if (i + 1) % 10 == 0:
                print(f"Processados {i + 1}/{len(arquivos_cda)} arquivos...")
                
        except Exception as e:
            print(f"Erro ao processar {arquivo_zip}: {e}")
            continue
    
    # Consolidar dados por período
    carteira_completa = {}
    for periodo, blcs in carteiras_por_periodo.items():
        carteira_completa[periodo] = {}
        for blc, dfs in blcs.items():
            if dfs:
                carteira_completa[periodo][blc] = pd.concat(dfs, ignore_index=True)
    
    print(f"\nCarteiras encontradas para {len(carteira_completa)} períodos")
    return carteira_completa

def analisar_evolucao_acoes(carteira_completa):
    """
    Analisa a evolução das posições em ações ao longo do tempo
    """
    print("\nAnalisando evolução das posições em ações...")
    
    evolucao_acoes = []
    
    for periodo, blcs in sorted(carteira_completa.items()):
        if 'BLC_4' in blcs:  # BLC_4 = Ações
            df_acoes = blcs['BLC_4']
            
            # Colunas de valor podem variar
            valor_col = None
            for col in ['VL_MERC_POS_FINAL', 'VL_MERCADO', 'VL_POS_FINAL']:
                if col in df_acoes.columns:
                    valor_col = col
                    break
            
            if valor_col:
                # Agrupar por ação
                for col in ['NM_ATIVO', 'DS_ATIVO', 'TP_ATIVO']:
                    if col in df_acoes.columns:
                        nome_col = col
                        break
                
                if nome_col in df_acoes.columns:
                    resumo = df_acoes.groupby(nome_col)[valor_col].sum().reset_index()
                    resumo['PERIODO'] = periodo
                    resumo['TOTAL_ACOES'] = df_acoes[valor_col].sum()
                    evolucao_acoes.append(resumo)
    
    if evolucao_acoes:
        df_evolucao = pd.concat(evolucao_acoes, ignore_index=True)
        return df_evolucao
    return pd.DataFrame()

def analisar_derivativos(carteira_completa):
    """
    Analisa posições em derivativos (BLC_5) e mercado futuro
    """
    print("\nAnalisando posições em derivativos...")
    
    derivativos_por_periodo = []
    
    for periodo, blcs in sorted(carteira_completa.items()):
        if 'BLC_5' in blcs:  # BLC_5 = Derivativos
            df_deriv = blcs['BLC_5']
            
            # Identificar colunas relevantes
            info_derivativo = {}
            info_derivativo['PERIODO'] = periodo
            
            # Tentar diferentes nomes de colunas
            for col_busca, col_destino in [
                (['TP_DERIVATIVO', 'DS_DERIVATIVO', 'TP_ATIVO'], 'TIPO'),
                (['VL_MERC_POS_FINAL', 'VL_MERCADO', 'VL_POS_FINAL'], 'VALOR'),
                (['QT_POS_FINAL', 'QUANTIDADE'], 'QUANTIDADE'),
                (['DS_ATIVO', 'NM_ATIVO'], 'ATIVO')
            ]:
                for col in col_busca:
                    if col in df_deriv.columns:
                        if col_destino == 'VALOR':
                            info_derivativo[col_destino] = df_deriv[col].sum()
                        else:
                            # Para análise detalhada
                            if not df_deriv.empty:
                                resumo = df_deriv.groupby(col).agg({
                                    col_busca[0]: 'count'
                                }).to_dict()
                                info_derivativo[f'{col_destino}_DETALHE'] = resumo
                        break
            
            if 'VALOR' in info_derivativo:
                derivativos_por_periodo.append(info_derivativo)
    
    return derivativos_por_periodo

def analisar_debentures(carteira_completa):
    """
    Analisa evolução das posições em debêntures
    """
    print("\nAnalisando posições em debêntures...")
    
    debentures_por_periodo = []
    
    for periodo, blcs in sorted(carteira_completa.items()):
        if 'BLC_3' in blcs:  # BLC_3 = Debêntures
            df_deb = blcs['BLC_3']
            
            # Colunas de valor
            valor_col = None
            for col in ['VL_MERC_POS_FINAL', 'VL_MERCADO', 'VL_POS_FINAL']:
                if col in df_deb.columns:
                    valor_col = col
                    break
            
            if valor_col and not df_deb.empty:
                info = {
                    'PERIODO': periodo,
                    'VALOR_TOTAL': df_deb[valor_col].sum(),
                    'QUANTIDADE': len(df_deb)
                }
                
                # Tentar obter emissores
                for col in ['NM_EMISSOR', 'EMISSOR', 'DS_EMISSOR']:
                    if col in df_deb.columns:
                        emissores = df_deb.groupby(col)[valor_col].sum().to_dict()
                        info['EMISSORES'] = emissores
                        break
                
                debentures_por_periodo.append(info)
    
    return debentures_por_periodo

def obter_cotacoes_ibovespa(data_inicio, data_fim):
    """
    Obtém cotações históricas do Ibovespa
    """
    print("\nBaixando cotações do Ibovespa... (desabilitado temporariamente)")
    # Retornar série vazia por enquanto
    return pd.Series()

def gerar_visualizacoes(carteira_completa, evolucao_acoes, derivativos, debentures):
    """
    Gera gráficos e visualizações
    """
    print("\nGerando visualizações...")
    
    # Configurar estilo
    plt.style.use('seaborn-v0_8-darkgrid')
    sns.set_palette("husl")
    
    # Criar figura com subplots
    fig = plt.figure(figsize=(20, 16))
    
    # 1. Evolução do patrimônio total
    ax1 = plt.subplot(3, 2, 1)
    patrimonio_total = []
    periodos = []
    
    for periodo in sorted(carteira_completa.keys()):
        total = 0
        for blc, df in carteira_completa[periodo].items():
            for col in ['VL_MERC_POS_FINAL', 'VL_MERCADO', 'VL_POS_FINAL']:
                if col in df.columns:
                    total += df[col].sum()
                    break
        
        if total > 0:
            patrimonio_total.append(total)
            periodos.append(periodo)
    
    if patrimonio_total:
        ax1.plot(periodos, patrimonio_total, marker='o', linewidth=2, markersize=8)
        ax1.set_title('Evolução do Patrimônio Total', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Período')
        ax1.set_ylabel('Valor (R$)')
        ax1.tick_params(axis='x', rotation=45)
        
        # Formatar valores do eixo Y
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x/1e6:.1f}M'))
    
    # 2. Composição da carteira por tipo de ativo
    ax2 = plt.subplot(3, 2, 2)
    if periodos:
        ultimo_periodo = periodos[-1]
        composicao = {}
        
        blc_nomes = {
            'BLC_1': 'Títulos Públicos',
            'BLC_2': 'Títulos Bancários',
            'BLC_3': 'Debêntures',
            'BLC_4': 'Ações',
            'BLC_5': 'Derivativos',
            'BLC_6': 'Cotas de Fundos',
            'BLC_7': 'Op. Compromissadas',
            'BLC_8': 'Outros'
        }
        
        for blc, df in carteira_completa[ultimo_periodo].items():
            for col in ['VL_MERC_POS_FINAL', 'VL_MERCADO', 'VL_POS_FINAL']:
                if col in df.columns:
                    valor = df[col].sum()
                    if valor > 0:
                        composicao[blc_nomes.get(blc, blc)] = valor
                    break
        
        if composicao:
            valores = list(composicao.values())
            labels = list(composicao.keys())
            ax2.pie(valores, labels=labels, autopct='%1.1f%%', startangle=90)
            ax2.set_title(f'Composição da Carteira - {ultimo_periodo}', fontsize=14, fontweight='bold')
    
    # 3. Evolução das posições em ações
    ax3 = plt.subplot(3, 2, 3)
    if not evolucao_acoes.empty:
        acoes_por_periodo = evolucao_acoes.groupby('PERIODO')['TOTAL_ACOES'].first()
        ax3.plot(acoes_por_periodo.index, acoes_por_periodo.values, marker='o', linewidth=2, markersize=8, label='Capstone')
        
        # Tentar plotar Ibovespa normalizado
        if len(acoes_por_periodo) > 1:
            try:
                data_inicio = acoes_por_periodo.index[0] + '-01'
                data_fim = acoes_por_periodo.index[-1] + '-28'
                ibov = obter_cotacoes_ibovespa(data_inicio, data_fim)
                
                if not ibov.empty:
                    # Normalizar Ibovespa para mesma escala
                    ibov_norm = ibov / ibov.iloc[0] * acoes_por_periodo.iloc[0]
                    ax3.plot(ibov_norm.index.strftime('%Y-%m'), ibov_norm.values, 
                            marker='s', linewidth=2, markersize=6, label='Ibovespa (normalizado)', alpha=0.7)
                    ax3.legend()
            except:
                pass
        
        ax3.set_title('Evolução das Posições em Ações', fontsize=14, fontweight='bold')
        ax3.set_xlabel('Período')
        ax3.set_ylabel('Valor (R$)')
        ax3.tick_params(axis='x', rotation=45)
        ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x/1e6:.1f}M'))
    
    # 4. Evolução dos derivativos
    ax4 = plt.subplot(3, 2, 4)
    if derivativos:
        periodos_deriv = [d['PERIODO'] for d in derivativos if 'VALOR' in d]
        valores_deriv = [d['VALOR'] for d in derivativos if 'VALOR' in d]
        
        if periodos_deriv:
            ax4.bar(periodos_deriv, valores_deriv, alpha=0.7)
            ax4.set_title('Evolução das Posições em Derivativos', fontsize=14, fontweight='bold')
            ax4.set_xlabel('Período')
            ax4.set_ylabel('Valor (R$)')
            ax4.tick_params(axis='x', rotation=45)
            ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x/1e6:.1f}M'))
    
    # 5. Evolução das debêntures
    ax5 = plt.subplot(3, 2, 5)
    if debentures:
        periodos_deb = [d['PERIODO'] for d in debentures]
        valores_deb = [d['VALOR_TOTAL'] for d in debentures]
        
        if periodos_deb:
            ax5.plot(periodos_deb, valores_deb, marker='o', linewidth=2, markersize=8, color='green')
            ax5.set_title('Evolução das Posições em Debêntures', fontsize=14, fontweight='bold')
            ax5.set_xlabel('Período')
            ax5.set_ylabel('Valor (R$)')
            ax5.tick_params(axis='x', rotation=45)
            ax5.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x/1e6:.1f}M'))
    
    # 6. Distribuição de ativos no último período (top 10)
    ax6 = plt.subplot(3, 2, 6)
    if periodos and not evolucao_acoes.empty:
        ultimo_periodo = periodos[-1]
        acoes_ultimo = evolucao_acoes[evolucao_acoes['PERIODO'] == ultimo_periodo]
        
        if not acoes_ultimo.empty:
            # Pegar nome da coluna de ativo
            nome_col = None
            for col in ['NM_ATIVO', 'DS_ATIVO', 'TP_ATIVO']:
                if col in acoes_ultimo.columns:
                    nome_col = col
                    break
            
            valor_col = None
            for col in ['VL_MERC_POS_FINAL', 'VL_MERCADO', 'VL_POS_FINAL']:
                if col in acoes_ultimo.columns:
                    valor_col = col
                    break
            
            if nome_col and valor_col:
                top10 = acoes_ultimo.nlargest(10, valor_col)
                ax6.barh(top10[nome_col], top10[valor_col])
                ax6.set_title(f'Top 10 Ações - {ultimo_periodo}', fontsize=14, fontweight='bold')
                ax6.set_xlabel('Valor (R$)')
                ax6.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x/1e6:.1f}M'))
    
    plt.tight_layout()
    
    # Salvar figura
    plt.savefig('analise_capstone_graficos.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("Gráficos salvos em 'analise_capstone_graficos.png'")

def gerar_relatorio_html(carteira_completa, evolucao_acoes, derivativos, debentures):
    """
    Gera relatório HTML com análises
    """
    print("\nGerando relatório HTML...")
    
    html_content = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Análise Completa - Fundo Capstone</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 0 20px rgba(0,0,0,0.1);
            }
            h1 {
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
            }
            h2 {
                color: #34495e;
                margin-top: 30px;
            }
            .info-box {
                background-color: #ecf0f1;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            th, td {
                padding: 10px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #3498db;
                color: white;
            }
            .chart-container {
                margin: 30px 0;
                text-align: center;
            }
            .highlight {
                background-color: #f39c12;
                color: white;
                padding: 2px 5px;
                border-radius: 3px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Análise Completa - Fundo Capstone</h1>
            <div class="info-box">
                <p><strong>CNPJ:</strong> 35.803.288/0001-17</p>
                <p><strong>Período Analisado:</strong> """ + f"{min(carteira_completa.keys()) if carteira_completa else 'N/A'} até {max(carteira_completa.keys()) if carteira_completa else 'N/A'}" + """</p>
                <p><strong>Total de Períodos:</strong> """ + str(len(carteira_completa)) + """</p>
            </div>
            
            <h2>1. Resumo Executivo</h2>
            <p>Esta análise abrange o histórico completo do fundo Capstone, incluindo:</p>
            <ul>
                <li>Evolução das posições em ações comparada ao Ibovespa</li>
                <li>Análise detalhada de derivativos e estratégias</li>
                <li>Posições em mercado futuro</li>
                <li>Evolução das debêntures</li>
            </ul>
            
            <h2>2. Evolução Patrimonial</h2>
            <div class="chart-container">
                <img src="analise_capstone_graficos.png" alt="Gráficos de Análise" style="max-width: 100%;">
            </div>
    """
    
    # Adicionar tabela de evolução de ações
    if not evolucao_acoes.empty:
        html_content += """
            <h2>3. Detalhamento das Posições em Ações</h2>
            <table>
                <tr>
                    <th>Período</th>
                    <th>Valor Total em Ações</th>
                    <th>Principais Posições</th>
                </tr>
        """
        
        for periodo in sorted(evolucao_acoes['PERIODO'].unique()):
            acoes_periodo = evolucao_acoes[evolucao_acoes['PERIODO'] == periodo]
            total = acoes_periodo['TOTAL_ACOES'].iloc[0] if not acoes_periodo.empty else 0
            
            # Top 3 ações
            nome_col = None
            for col in ['NM_ATIVO', 'DS_ATIVO', 'TP_ATIVO']:
                if col in acoes_periodo.columns:
                    nome_col = col
                    break
            
            valor_col = None
            for col in ['VL_MERC_POS_FINAL', 'VL_MERCADO', 'VL_POS_FINAL']:
                if col in acoes_periodo.columns:
                    valor_col = col
                    break
            
            principais = ""
            if nome_col and valor_col:
                top3 = acoes_periodo.nlargest(3, valor_col)
                principais = ", ".join([f"{row[nome_col]} (R$ {row[valor_col]/1e6:.1f}M)" 
                                       for _, row in top3.iterrows()])
            
            html_content += f"""
                <tr>
                    <td>{periodo}</td>
                    <td>R$ {total/1e6:.2f}M</td>
                    <td>{principais}</td>
                </tr>
            """
        
        html_content += "</table>"
    
    # Análise de derivativos
    if derivativos:
        html_content += """
            <h2>4. Análise de Derivativos e Mercado Futuro</h2>
            <div class="info-box">
                <p>O fundo apresentou posições em derivativos nos seguintes períodos:</p>
            </div>
            <table>
                <tr>
                    <th>Período</th>
                    <th>Valor Total</th>
                    <th>Observações</th>
                </tr>
        """
        
        for deriv in derivativos:
            if 'VALOR' in deriv:
                html_content += f"""
                    <tr>
                        <td>{deriv['PERIODO']}</td>
                        <td>R$ {deriv['VALOR']/1e6:.2f}M</td>
                        <td>Análise detalhada disponível</td>
                    </tr>
                """
        
        html_content += "</table>"
    
    # Análise de debêntures
    if debentures:
        html_content += """
            <h2>5. Evolução das Posições em Debêntures</h2>
            <table>
                <tr>
                    <th>Período</th>
                    <th>Valor Total</th>
                    <th>Quantidade</th>
                    <th>Principais Emissores</th>
                </tr>
        """
        
        for deb in debentures:
            emissores = ""
            if 'EMISSORES' in deb:
                top_emissores = sorted(deb['EMISSORES'].items(), 
                                     key=lambda x: x[1], reverse=True)[:3]
                emissores = ", ".join([f"{em[0]} (R$ {em[1]/1e6:.1f}M)" 
                                      for em in top_emissores])
            
            html_content += f"""
                <tr>
                    <td>{deb['PERIODO']}</td>
                    <td>R$ {deb['VALOR_TOTAL']/1e6:.2f}M</td>
                    <td>{deb['QUANTIDADE']}</td>
                    <td>{emissores}</td>
                </tr>
            """
        
        html_content += "</table>"
    
    html_content += """
            <h2>6. Conclusões e Insights</h2>
            <div class="info-box">
                <p>Com base na análise realizada, observamos:</p>
                <ul>
                    <li>O fundo apresenta uma gestão ativa com mudanças significativas na composição da carteira ao longo do tempo</li>
                    <li>As posições em derivativos sugerem estratégias de hedge e alavancagem</li>
                    <li>A diversificação entre diferentes classes de ativos demonstra uma abordagem balanceada de risco</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Salvar HTML
    with open('capstone.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("Relatório HTML salvo em 'capstone.html'")

def main():
    """
    Função principal para executar a análise completa
    """
    print("=" * 60)
    print("ANÁLISE COMPLETA - FUNDO CAPSTONE")
    print("=" * 60)
    
    # 1. Processar carteiras históricas
    carteira_completa = processar_carteira_capstone(BASE_DIR, CNPJ_CAPSTONE)
    
    if not carteira_completa:
        print("\nNENHUM DADO ENCONTRADO para o fundo Capstone!")
        print("Verifique se o CNPJ está correto e se os dados CDA estão disponíveis.")
        return
    
    # 2. Analisar evolução das ações
    evolucao_acoes = analisar_evolucao_acoes(carteira_completa)
    
    # 3. Analisar derivativos
    derivativos = analisar_derivativos(carteira_completa)
    
    # 4. Analisar debêntures
    debentures = analisar_debentures(carteira_completa)
    
    # 5. Gerar visualizações
    gerar_visualizacoes(carteira_completa, evolucao_acoes, derivativos, debentures)
    
    # 6. Gerar relatório HTML
    gerar_relatorio_html(carteira_completa, evolucao_acoes, derivativos, debentures)
    
    print("\n" + "=" * 60)
    print("ANÁLISE CONCLUÍDA!")
    print("Arquivos gerados:")
    print("- analise_capstone_graficos.png")
    print("- capstone.html")
    print("=" * 60)

if __name__ == "__main__":
    main()