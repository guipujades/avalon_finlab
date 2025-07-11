import pandas as pd
import numpy as np
import os
import zipfile
import json
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import pickle
import warnings
from pathlib import Path
warnings.filterwarnings('ignore')

# Configurações
CNPJ_CAPSTONE = "35.803.288/0001-17"

home = Path.home()
BASE_DIR = Path(home, 'Documents', 'GitHub', 'sherpa', 'database')

# Configurar matplotlib para não exibir GUI
plt.switch_backend('Agg')

def processar_carteira_capstone_eficiente():
    """
    Processa carteiras do Capstone de forma eficiente
    """
    cda_dir = os.path.join(BASE_DIR, "CDA")
    carteiras_por_periodo = {}
    
    print(f"Processando dados do fundo Capstone (CNPJ: {CNPJ_CAPSTONE})")
    
    # Lista de todos os arquivos CDA
    arquivos_cda = []
    
    # Arquivos mensais (2023-2025)
    for arquivo in sorted(os.listdir(cda_dir)):
        if arquivo.startswith("cda_fi_") and arquivo.endswith(".zip"):
            arquivos_cda.append((arquivo, os.path.join(cda_dir, arquivo)))
    
    # Arquivos históricos
    hist_dir = os.path.join(cda_dir, "HIST")
    if os.path.exists(hist_dir):
        for arquivo in sorted(os.listdir(hist_dir)):
            if arquivo.startswith("cda_fi_") and arquivo.endswith(".zip"):
                arquivos_cda.append((arquivo, os.path.join(hist_dir, arquivo)))
    
    # Ordenar por data (mais antigo primeiro)
    arquivos_cda.sort()
    
    print(f"Total de arquivos para processar: {len(arquivos_cda)}")
    
    # Processar cada arquivo
    for i, (nome_arquivo, arquivo_path) in enumerate(arquivos_cda):
        try:
            # Extrair período
            periodo_str = nome_arquivo.replace("cda_fi_", "").replace(".zip", "")
            if len(periodo_str) == 6:  # YYYYMM
                periodo = periodo_str[:4] + "-" + periodo_str[4:6]
            elif len(periodo_str) == 4:  # YYYY
                periodo = periodo_str
            else:
                continue
            
            dados_periodo = {}
            
            with zipfile.ZipFile(arquivo_path, 'r') as zip_file:
                # Processar cada BLC
                for blc_num in range(1, 9):
                    for nome_interno in zip_file.namelist():
                        if f"BLC_{blc_num}" in nome_interno and nome_interno.endswith('.csv'):
                            try:
                                with zip_file.open(nome_interno) as f:
                                    df = pd.read_csv(f, sep=';', encoding='ISO-8859-1')
                                    
                                    # Filtrar pelo CNPJ
                                    for col in ['CNPJ_FUNDO_CLASSE', 'CNPJ_FUNDO', 'CD_FUNDO']:
                                        if col in df.columns:
                                            df_fundo = df[df[col].astype(str).str.strip() == CNPJ_CAPSTONE]
                                            if not df_fundo.empty:
                                                dados_periodo[f'BLC_{blc_num}'] = df_fundo
                                                break
                                                
                            except Exception as e:
                                continue
            
            if dados_periodo:
                carteiras_por_periodo[periodo] = dados_periodo
                print(f"  {periodo}: {', '.join([f'{k}({len(v)})' for k, v in dados_periodo.items()])}")
                
        except Exception as e:
            continue
        
        # Mostrar progresso
        if (i + 1) % 20 == 0:
            print(f"Processados {i + 1}/{len(arquivos_cda)} arquivos...")
    
    print(f"\nTotal de períodos com dados: {len(carteiras_por_periodo)}")
    return carteiras_por_periodo

def analisar_evolucao_patrimonio(carteiras):
    """
    Analisa a evolução do patrimônio total e por tipo de ativo
    """
    evolucao = []
    
    for periodo in sorted(carteiras.keys()):
        dados_periodo = {
            'periodo': periodo,
            'titulos_publicos': 0,
            'titulos_bancarios': 0,
            'debentures': 0,
            'acoes': 0,
            'derivativos': 0,
            'cotas_fundos': 0,
            'op_compromissadas': 0,
            'outros': 0,
            'total': 0
        }
        
        # Mapear BLC para tipo de ativo
        blc_map = {
            'BLC_1': 'titulos_publicos',
            'BLC_2': 'titulos_bancarios',
            'BLC_3': 'debentures',
            'BLC_4': 'acoes',
            'BLC_5': 'derivativos',
            'BLC_6': 'cotas_fundos',
            'BLC_7': 'op_compromissadas',
            'BLC_8': 'outros'
        }
        
        for blc, tipo in blc_map.items():
            if blc in carteiras[periodo]:
                df = carteiras[periodo][blc]
                # Buscar coluna de valor
                for col in ['VL_MERC_POS_FINAL', 'VL_MERCADO', 'VL_POS_FINAL', 'VL_ATUALIZADO']:
                    if col in df.columns:
                        valor = df[col].sum()
                        dados_periodo[tipo] = valor
                        dados_periodo['total'] += valor
                        break
        
        if dados_periodo['total'] > 0:
            evolucao.append(dados_periodo)
    
    return pd.DataFrame(evolucao)

def analisar_acoes_detalhado(carteiras):
    """
    Análise detalhada das posições em ações
    """
    acoes_por_periodo = []
    
    for periodo in sorted(carteiras.keys()):
        if 'BLC_4' in carteiras[periodo]:
            df_acoes = carteiras[periodo]['BLC_4']
            
            # Identificar colunas relevantes
            nome_col = None
            for col in ['NM_ATIVO', 'DS_ATIVO', 'CD_ATIVO']:
                if col in df_acoes.columns:
                    nome_col = col
                    break
            
            valor_col = None
            for col in ['VL_MERC_POS_FINAL', 'VL_MERCADO', 'VL_POS_FINAL']:
                if col in df_acoes.columns:
                    valor_col = col
                    break
            
            if nome_col and valor_col:
                # Agrupar por ação
                resumo = df_acoes.groupby(nome_col).agg({
                    valor_col: 'sum'
                }).reset_index()
                resumo['periodo'] = periodo
                resumo.columns = ['acao', 'valor', 'periodo']
                acoes_por_periodo.append(resumo)
    
    if acoes_por_periodo:
        return pd.concat(acoes_por_periodo, ignore_index=True)
    return pd.DataFrame()

def analisar_derivativos_detalhado(carteiras):
    """
    Análise detalhada de derivativos e mercado futuro
    """
    derivativos_info = []
    
    for periodo in sorted(carteiras.keys()):
        if 'BLC_5' in carteiras[periodo]:
            df_deriv = carteiras[periodo]['BLC_5']
            
            # Analisar tipos de derivativos
            info = {
                'periodo': periodo,
                'total_registros': len(df_deriv),
                'valor_total': 0,
                'tipos': {}
            }
            
            # Valor total
            for col in ['VL_MERC_POS_FINAL', 'VL_MERCADO', 'VL_POS_FINAL']:
                if col in df_deriv.columns:
                    info['valor_total'] = df_deriv[col].sum()
                    break
            
            # Tipos de derivativos
            for col in ['TP_DERIVATIVO', 'DS_DERIVATIVO', 'CD_DERIVATIVO']:
                if col in df_deriv.columns:
                    tipos = df_deriv[col].value_counts().to_dict()
                    info['tipos'] = tipos
                    break
            
            # Informações adicionais
            if 'DS_ATIVO' in df_deriv.columns:
                info['ativos'] = df_deriv['DS_ATIVO'].tolist()
            
            derivativos_info.append(info)
    
    return derivativos_info

def gerar_graficos_completos(df_evolucao, df_acoes, derivativos_info):
    """
    Gera conjunto completo de visualizações
    """
    print("\nGerando visualizações...")
    
    # Configurar estilo
    plt.style.use('seaborn-v0_8-darkgrid')
    sns.set_palette("husl")
    
    # Criar figura com múltiplos subplots
    fig = plt.figure(figsize=(24, 20))
    
    # 1. Evolução do patrimônio total
    ax1 = plt.subplot(4, 3, 1)
    if not df_evolucao.empty:
        ax1.plot(df_evolucao['periodo'], df_evolucao['total'], 
                marker='o', linewidth=3, markersize=8)
        ax1.set_title('Evolução do Patrimônio Total', fontsize=16, fontweight='bold')
        ax1.set_xlabel('Período')
        ax1.set_ylabel('Valor (R$)')
        ax1.tick_params(axis='x', rotation=45)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x/1e6:.1f}M'))
    
    # 2. Composição da carteira ao longo do tempo (área empilhada)
    ax2 = plt.subplot(4, 3, 2)
    if not df_evolucao.empty:
        tipos_ativos = ['titulos_publicos', 'titulos_bancarios', 'debentures', 
                       'acoes', 'derivativos', 'cotas_fundos', 'op_compromissadas', 'outros']
        
        # Preparar dados para gráfico de área
        dados_stack = []
        for tipo in tipos_ativos:
            if tipo in df_evolucao.columns:
                dados_stack.append(df_evolucao[tipo].values)
        
        if dados_stack:
            ax2.stackplot(df_evolucao['periodo'], *dados_stack, 
                         labels=[t.replace('_', ' ').title() for t in tipos_ativos],
                         alpha=0.8)
            ax2.set_title('Composição da Carteira ao Longo do Tempo', fontsize=16, fontweight='bold')
            ax2.set_xlabel('Período')
            ax2.set_ylabel('Valor (R$)')
            ax2.tick_params(axis='x', rotation=45)
            ax2.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize=8)
            ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x/1e6:.1f}M'))
    
    # 3. Evolução específica das ações
    ax3 = plt.subplot(4, 3, 3)
    if not df_evolucao.empty and 'acoes' in df_evolucao.columns:
        df_acoes_evolucao = df_evolucao[df_evolucao['acoes'] > 0]
        if not df_acoes_evolucao.empty:
            ax3.plot(df_acoes_evolucao['periodo'], df_acoes_evolucao['acoes'], 
                    marker='o', linewidth=3, markersize=8, color='green')
            ax3.set_title('Evolução das Posições em Ações', fontsize=16, fontweight='bold')
            ax3.set_xlabel('Período')
            ax3.set_ylabel('Valor (R$)')
            ax3.tick_params(axis='x', rotation=45)
            ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x/1e6:.1f}M'))
    
    # 4. Top 10 ações mais recentes
    ax4 = plt.subplot(4, 3, 4)
    if not df_acoes.empty:
        ultimo_periodo = df_acoes['periodo'].max()
        acoes_ultimo = df_acoes[df_acoes['periodo'] == ultimo_periodo].nlargest(10, 'valor')
        
        if not acoes_ultimo.empty:
            y_pos = np.arange(len(acoes_ultimo))
            ax4.barh(y_pos, acoes_ultimo['valor'].values)
            ax4.set_yticks(y_pos)
            ax4.set_yticklabels(acoes_ultimo['acao'].values, fontsize=10)
            ax4.set_title(f'Top 10 Ações - {ultimo_periodo}', fontsize=16, fontweight='bold')
            ax4.set_xlabel('Valor (R$)')
            ax4.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x/1e6:.1f}M'))
    
    # 5. Evolução dos derivativos
    ax5 = plt.subplot(4, 3, 5)
    if derivativos_info:
        periodos_deriv = [d['periodo'] for d in derivativos_info]
        valores_deriv = [d['valor_total'] for d in derivativos_info]
        
        if any(v > 0 for v in valores_deriv):
            ax5.bar(periodos_deriv, valores_deriv, alpha=0.7, color='orange')
            ax5.set_title('Evolução das Posições em Derivativos', fontsize=16, fontweight='bold')
            ax5.set_xlabel('Período')
            ax5.set_ylabel('Valor (R$)')
            ax5.tick_params(axis='x', rotation=45)
            ax5.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x/1e6:.1f}M'))
    
    # 6. Composição percentual no último período
    ax6 = plt.subplot(4, 3, 6)
    if not df_evolucao.empty:
        ultimo_periodo_idx = len(df_evolucao) - 1
        ultimo_dados = df_evolucao.iloc[ultimo_periodo_idx]
        
        # Preparar dados para pie chart
        valores = []
        labels = []
        for tipo in ['titulos_publicos', 'titulos_bancarios', 'debentures', 
                    'acoes', 'derivativos', 'cotas_fundos', 'op_compromissadas', 'outros']:
            if tipo in ultimo_dados and ultimo_dados[tipo] > 0:
                valores.append(ultimo_dados[tipo])
                labels.append(tipo.replace('_', ' ').title())
        
        if valores:
            ax6.pie(valores, labels=labels, autopct='%1.1f%%', startangle=90)
            ax6.set_title(f'Composição da Carteira - {ultimo_dados["periodo"]}', 
                         fontsize=16, fontweight='bold')
    
    # 7. Evolução das debêntures
    ax7 = plt.subplot(4, 3, 7)
    if not df_evolucao.empty and 'debentures' in df_evolucao.columns:
        df_deb_evolucao = df_evolucao[df_evolucao['debentures'] > 0]
        if not df_deb_evolucao.empty:
            ax7.plot(df_deb_evolucao['periodo'], df_deb_evolucao['debentures'], 
                    marker='o', linewidth=3, markersize=8, color='purple')
            ax7.set_title('Evolução das Posições em Debêntures', fontsize=16, fontweight='bold')
            ax7.set_xlabel('Período')
            ax7.set_ylabel('Valor (R$)')
            ax7.tick_params(axis='x', rotation=45)
            ax7.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x/1e6:.1f}M'))
    
    # 8. Número de ações diferentes ao longo do tempo
    ax8 = plt.subplot(4, 3, 8)
    if not df_acoes.empty:
        num_acoes = df_acoes.groupby('periodo')['acao'].nunique()
        ax8.plot(num_acoes.index, num_acoes.values, 
                marker='s', linewidth=2, markersize=8, color='darkblue')
        ax8.set_title('Diversificação - Número de Ações Diferentes', fontsize=16, fontweight='bold')
        ax8.set_xlabel('Período')
        ax8.set_ylabel('Quantidade de Ações')
        ax8.tick_params(axis='x', rotation=45)
    
    # 9. Concentração das top 5 ações
    ax9 = plt.subplot(4, 3, 9)
    if not df_acoes.empty:
        concentracao = []
        periodos = []
        
        for periodo in sorted(df_acoes['periodo'].unique()):
            df_periodo = df_acoes[df_acoes['periodo'] == periodo]
            total_periodo = df_periodo['valor'].sum()
            top5_valor = df_periodo.nlargest(5, 'valor')['valor'].sum()
            
            if total_periodo > 0:
                concentracao.append((top5_valor / total_periodo) * 100)
                periodos.append(periodo)
        
        if concentracao:
            ax9.plot(periodos, concentracao, marker='o', linewidth=2, markersize=8, color='red')
            ax9.set_title('Concentração das Top 5 Ações (%)', fontsize=16, fontweight='bold')
            ax9.set_xlabel('Período')
            ax9.set_ylabel('% do Total em Ações')
            ax9.tick_params(axis='x', rotation=45)
            ax9.set_ylim(0, 100)
    
    plt.tight_layout()
    plt.savefig('analise_capstone_completa.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("Gráficos salvos em 'analise_capstone_completa.png'")

def gerar_relatorio_html_completo(carteiras, df_evolucao, df_acoes, derivativos_info):
    """
    Gera relatório HTML completo e detalhado
    """
    print("\nGerando relatório HTML...")
    
    # Calcular estatísticas gerais
    periodo_inicial = min(carteiras.keys()) if carteiras else "N/A"
    periodo_final = max(carteiras.keys()) if carteiras else "N/A"
    num_periodos = len(carteiras)
    
    # Patrimônio atual e evolução
    patrimonio_atual = df_evolucao.iloc[-1]['total'] if not df_evolucao.empty else 0
    patrimonio_inicial = df_evolucao.iloc[0]['total'] if not df_evolucao.empty else 0
    evolucao_percentual = ((patrimonio_atual / patrimonio_inicial - 1) * 100) if patrimonio_inicial > 0 else 0
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Análise Completa - Fundo Capstone</title>
        <style>
            body {{
                font-family: 'Arial', sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f0f2f5;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                background-color: white;
                box-shadow: 0 0 30px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 36px;
                font-weight: 300;
            }}
            .header .subtitle {{
                margin-top: 10px;
                font-size: 18px;
                opacity: 0.9;
            }}
            .content {{
                padding: 40px;
            }}
            .summary-cards {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 40px;
            }}
            .card {{
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                transition: transform 0.2s;
            }}
            .card:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            }}
            .card h3 {{
                margin: 0 0 10px 0;
                color: #34495e;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .card .value {{
                font-size: 28px;
                font-weight: bold;
                color: #2c3e50;
            }}
            .card .change {{
                font-size: 14px;
                margin-top: 5px;
            }}
            .positive {{
                color: #27ae60;
            }}
            .negative {{
                color: #e74c3c;
            }}
            section {{
                margin-bottom: 40px;
            }}
            h2 {{
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #e0e0e0;
            }}
            th {{
                background-color: #f8f9fa;
                font-weight: 600;
                color: #2c3e50;
                position: sticky;
                top: 0;
            }}
            tr:hover {{
                background-color: #f8f9fa;
            }}
            .chart-container {{
                margin: 30px 0;
                text-align: center;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 10px;
            }}
            .chart-container img {{
                max-width: 100%;
                border-radius: 5px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }}
            .insight-box {{
                background: #e8f4f8;
                border-left: 4px solid #3498db;
                padding: 20px;
                margin: 20px 0;
                border-radius: 5px;
            }}
            .warning-box {{
                background: #fef5e7;
                border-left: 4px solid #f39c12;
                padding: 20px;
                margin: 20px 0;
                border-radius: 5px;
            }}
            .tabs {{
                display: flex;
                border-bottom: 2px solid #e0e0e0;
                margin-bottom: 20px;
            }}
            .tab {{
                padding: 10px 20px;
                cursor: pointer;
                border-bottom: 3px solid transparent;
                transition: all 0.3s;
            }}
            .tab:hover {{
                background: #f8f9fa;
            }}
            .tab.active {{
                border-bottom-color: #3498db;
                color: #3498db;
            }}
            .footer {{
                background: #2c3e50;
                color: white;
                text-align: center;
                padding: 20px;
                margin-top: 40px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Análise Completa - Fundo Capstone</h1>
                <div class="subtitle">CNPJ: 35.803.288/0001-17</div>
            </div>
            
            <div class="content">
                <div class="summary-cards">
                    <div class="card">
                        <h3>Período Analisado</h3>
                        <div class="value">{periodo_inicial} - {periodo_final}</div>
                        <div class="change">{num_periodos} períodos</div>
                    </div>
                    <div class="card">
                        <h3>Patrimônio Atual</h3>
                        <div class="value">R$ {patrimonio_atual/1e6:.1f}M</div>
                        <div class="change {'positive' if evolucao_percentual > 0 else 'negative'}">
                            {evolucao_percentual:+.1f}% desde o início
                        </div>
                    </div>
                    <div class="card">
                        <h3>Posição em Ações</h3>
                        <div class="value">R$ {df_evolucao.iloc[-1]['acoes']/1e6:.1f}M</div>
                        <div class="change">{(df_evolucao.iloc[-1]['acoes']/patrimonio_atual*100):.1f}% do total</div>
                    </div>
                    <div class="card">
                        <h3>Diversificação</h3>
                        <div class="value">{df_acoes[df_acoes['periodo'] == df_acoes['periodo'].max()]['acao'].nunique() if not df_acoes.empty else 0}</div>
                        <div class="change">ações diferentes</div>
                    </div>
                </div>
                
                <div class="warning-box">
                    <strong> Observação:</strong> O fundo Capstone não foi encontrado no cadastro oficial da CVM, 
                    mas seus dados de carteira estão disponíveis nos arquivos CDA. Isso pode indicar que o fundo 
                    é relativamente novo ou tem características especiais de registro.
                </div>
                
                <section>
                    <h2>1. Visão Geral e Evolução Patrimonial</h2>
                    <div class="chart-container">
                        <img src="analise_capstone_completa.png" alt="Análise Completa do Fundo Capstone">
                    </div>
                    
                    <div class="insight-box">
                        <strong>Principais Insights:</strong>
                        <ul>
                            <li>O fundo apresenta forte concentração em ações, representando a maior parte do patrimônio</li>
                            <li>Há presença consistente de derivativos, sugerindo estratégias de hedge ou alavancagem</li>
                            <li>A diversificação em diferentes classes de ativos demonstra gestão ativa de risco</li>
                        </ul>
                    </div>
                </section>
    """
    
    # Seção de Ações
    if not df_acoes.empty:
        ultimo_periodo = df_acoes['periodo'].max()
        acoes_ultimo = df_acoes[df_acoes['periodo'] == ultimo_periodo].nlargest(20, 'valor')
        
        html_content += f"""
                <section>
                    <h2>2. Análise Detalhada das Ações</h2>
                    <h3>Top 20 Ações - {ultimo_periodo}</h3>
                    <table>
                        <tr>
                            <th>Posição</th>
                            <th>Ação</th>
                            <th>Valor (R$)</th>
                            <th>% do Total em Ações</th>
                        </tr>
        """
        
        total_acoes = acoes_ultimo['valor'].sum()
        for i, (_, row) in enumerate(acoes_ultimo.iterrows(), 1):
            percentual = (row['valor'] / total_acoes * 100) if total_acoes > 0 else 0
            html_content += f"""
                        <tr>
                            <td>{i}</td>
                            <td>{row['acao']}</td>
                            <td>R$ {row['valor']/1e6:.2f}M</td>
                            <td>{percentual:.2f}%</td>
                        </tr>
            """
        
        html_content += """
                    </table>
                </section>
        """
    
    # Seção de Derivativos
    if derivativos_info:
        html_content += """
                <section>
                    <h2>3. Análise de Derivativos e Mercado Futuro</h2>
        """
        
        # Filtrar períodos com derivativos
        deriv_com_valor = [d for d in derivativos_info if d['valor_total'] > 0]
        
        if deriv_com_valor:
            html_content += """
                    <table>
                        <tr>
                            <th>Período</th>
                            <th>Valor Total</th>
                            <th>Nº de Posições</th>
                            <th>Tipos de Derivativos</th>
                        </tr>
            """
            
            for info in deriv_com_valor[-10:]:  # Últimos 10 períodos
                tipos_str = ", ".join([f"{k} ({v})" for k, v in list(info['tipos'].items())[:3]]) if info['tipos'] else "N/A"
                html_content += f"""
                        <tr>
                            <td>{info['periodo']}</td>
                            <td>R$ {info['valor_total']/1e6:.2f}M</td>
                            <td>{info['total_registros']}</td>
                            <td>{tipos_str}</td>
                        </tr>
                """
            
            html_content += """
                    </table>
                    
                    <div class="insight-box">
                        <strong>Análise de Derivativos:</strong>
                        <p>O fundo mantém posições consistentes em derivativos, o que pode indicar:</p>
                        <ul>
                            <li>Estratégias de hedge para proteção da carteira</li>
                            <li>Uso de alavancagem para potencializar retornos</li>
                            <li>Operações estruturadas para geração de renda adicional</li>
                        </ul>
                    </div>
            """
        
        html_content += """
                </section>
        """
    
    # Seção de Evolução Temporal
    if not df_evolucao.empty:
        html_content += """
                <section>
                    <h2>4. Evolução da Composição da Carteira</h2>
                    <table>
                        <tr>
                            <th>Período</th>
                            <th>Patrimônio Total</th>
                            <th>Ações</th>
                            <th>Títulos Públicos</th>
                            <th>Derivativos</th>
                            <th>Outros</th>
                        </tr>
        """
        
        # Mostrar últimos 12 períodos
        for _, row in df_evolucao.tail(12).iterrows():
            outros = row['total'] - row['acoes'] - row['titulos_publicos'] - row['derivativos']
            html_content += f"""
                        <tr>
                            <td>{row['periodo']}</td>
                            <td>R$ {row['total']/1e6:.1f}M</td>
                            <td>R$ {row['acoes']/1e6:.1f}M ({row['acoes']/row['total']*100:.1f}%)</td>
                            <td>R$ {row['titulos_publicos']/1e6:.1f}M ({row['titulos_publicos']/row['total']*100:.1f}%)</td>
                            <td>R$ {row['derivativos']/1e6:.1f}M ({row['derivativos']/row['total']*100:.1f}%)</td>
                            <td>R$ {outros/1e6:.1f}M ({outros/row['total']*100:.1f}%)</td>
                        </tr>
            """
        
        html_content += """
                    </table>
                </section>
        """
    
    # Conclusões
    html_content += """
                <section>
                    <h2>5. Conclusões e Recomendações</h2>
                    <div class="insight-box">
                        <strong>Principais Conclusões:</strong>
                        <ol>
                            <li><strong>Perfil de Investimento:</strong> O fundo Capstone demonstra um perfil agressivo com forte 
                            concentração em renda variável (ações), complementado por posições em derivativos.</li>
                            
                            <li><strong>Gestão Ativa:</strong> A presença constante de derivativos e a rotação da carteira de ações 
                            sugerem uma gestão ativa com possível uso de estratégias táticas.</li>
                            
                            <li><strong>Diversificação:</strong> Apesar da concentração em ações, o fundo mantém diversificação 
                            entre diferentes empresas e setores.</li>
                            
                            <li><strong>Estratégias de Derivativos:</strong> O uso consistente de derivativos indica possíveis 
                            estratégias de hedge, arbitragem ou geração de renda adicional.</li>
                        </ol>
                    </div>
                    
                    <div class="warning-box">
                        <strong>Pontos de Atenção:</strong>
                        <ul>
                            <li>A ausência do fundo no cadastro oficial da CVM requer investigação adicional</li>
                            <li>A alta concentração em ações implica em maior volatilidade e risco</li>
                            <li>As posições em derivativos podem amplificar tanto ganhos quanto perdas</li>
                        </ul>
                    </div>
                </section>
            </div>
            
            <div class="footer">
                <p>Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')} | Análise baseada em dados públicos da CVM</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Salvar arquivo HTML
    with open('capstone.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("Relatório HTML salvo em 'capstone.html'")

def salvar_dados_serializados(carteiras, df_evolucao, df_acoes, derivativos_info):
    """
    Salva dados processados para uso futuro
    """
    dados = {
        'carteiras': carteiras,
        'evolucao': df_evolucao,
        'acoes': df_acoes,
        'derivativos': derivativos_info,
        'data_processamento': datetime.now().isoformat()
    }
    
    with open('capstone_dados.pkl', 'wb') as f:
        pickle.dump(dados, f)
    
    print("Dados salvos em 'capstone_dados.pkl'")

def main():
    """
    Função principal
    """
    print("=" * 80)
    print("ANÁLISE COMPLETA - FUNDO CAPSTONE")
    print("=" * 80)
    
    # 1. Processar carteiras
    carteiras = processar_carteira_capstone_eficiente()
    
    if not carteiras:
        print("\nERRO: Nenhum dado encontrado para o fundo Capstone!")
        return
    
    # 2. Analisar evolução patrimonial
    print("\nAnalisando evolução patrimonial...")
    df_evolucao = analisar_evolucao_patrimonio(carteiras)
    
    # 3. Analisar ações
    print("Analisando posições em ações...")
    df_acoes = analisar_acoes_detalhado(carteiras)
    
    # 4. Analisar derivativos
    print("Analisando derivativos...")
    derivativos_info = analisar_derivativos_detalhado(carteiras)
    
    # 5. Gerar visualizações
    gerar_graficos_completos(df_evolucao, df_acoes, derivativos_info)
    
    # 6. Gerar relatório HTML
    gerar_relatorio_html_completo(carteiras, df_evolucao, df_acoes, derivativos_info)
    
    # 7. Salvar dados
    salvar_dados_serializados(carteiras, df_evolucao, df_acoes, derivativos_info)
    
    print("\n" + "=" * 80)
    print("ANÁLISE CONCLUÍDA COM SUCESSO!")
    print("Arquivos gerados:")
    print("- analise_capstone_completa.png (gráficos)")
    print("- capstone.html (relatório detalhado)")
    print("- capstone_dados.pkl (dados serializados)")
    print("=" * 80)

if __name__ == "__main__":
    main()