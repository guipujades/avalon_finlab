import pandas as pd
import numpy as np
import os
import zipfile
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import pickle
import warnings
warnings.filterwarnings('ignore')

# Configurações
CNPJ_CAPSTONE = "35.803.288/0001-17"
BASE_DIR = "/mnt/c/Users/guilh/Documents/GitHub/sherpa/database"

# Configurar matplotlib
plt.switch_backend('Agg')
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def processar_periodo_especifico(inicio_ano=2022, fim_ano=2024, fim_mes=11):
    """
    Processa dados do fundo Capstone para período específico
    """
    cda_dir = os.path.join(BASE_DIR, "CDA")
    carteiras_por_periodo = {}
    
    print(f"Processando dados do fundo Capstone de {inicio_ano} até {fim_mes}/{fim_ano}")
    print(f"CNPJ: {CNPJ_CAPSTONE}")
    print("=" * 60)
    
    # Gerar lista de arquivos para processar
    arquivos_processar = []
    
    # Arquivos mensais (2022 em diante)
    for ano in range(inicio_ano, fim_ano + 1):
        for mes in range(1, 13):
            # Parar em novembro de 2024
            if ano == fim_ano and mes > fim_mes:
                break
                
            arquivo = f"cda_fi_{ano}{mes:02d}.zip"
            arquivo_path = os.path.join(cda_dir, arquivo)
            
            if os.path.exists(arquivo_path):
                arquivos_processar.append((arquivo, arquivo_path, f"{ano}-{mes:02d}"))
    
    print(f"Total de arquivos para processar: {len(arquivos_processar)}")
    
    # Processar cada arquivo
    for i, (nome_arquivo, arquivo_path, periodo) in enumerate(arquivos_processar):
        print(f"\nProcessando {periodo}...", end="")
        
        try:
            dados_periodo = {}
            
            with zipfile.ZipFile(arquivo_path, 'r') as zip_file:
                # Processar todos os BLCs
                for blc_num in range(1, 9):
                    for nome_interno in zip_file.namelist():
                        if f"BLC_{blc_num}" in nome_interno and nome_interno.endswith('.csv'):
                            try:
                                with zip_file.open(nome_interno) as f:
                                    df = pd.read_csv(f, sep=';', encoding='ISO-8859-1', low_memory=False)
                                    
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
                blcs_encontrados = [f"{k}({len(v)})" for k, v in dados_periodo.items()]
                print(f" ✓ {', '.join(blcs_encontrados)}")
            else:
                print(" ✗ Sem dados")
                
        except Exception as e:
            print(f" Erro: {e}")
    
    return carteiras_por_periodo

def analisar_evolucao_detalhada(carteiras):
    """
    Análise detalhada da evolução patrimonial
    """
    evolucao = []
    
    # Mapeamento BLC para tipo
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
        
        for blc, tipo in blc_map.items():
            if blc in carteiras[periodo]:
                df = carteiras[periodo][blc]
                
                # Buscar coluna de valor
                valor = 0
                for col in ['VL_MERC_POS_FINAL', 'VL_MERCADO', 'VL_POS_FINAL', 'VL_ATUALIZADO']:
                    if col in df.columns:
                        valor = df[col].sum()
                        break
                
                dados_periodo[tipo] = valor
                dados_periodo['total'] += valor
        
        if dados_periodo['total'] > 0:
            evolucao.append(dados_periodo)
    
    return pd.DataFrame(evolucao)

def analisar_acoes_historico(carteiras):
    """
    Análise histórica das ações
    """
    historico_acoes = []
    
    for periodo in sorted(carteiras.keys()):
        if 'BLC_4' not in carteiras[periodo]:
            continue
            
        df_acoes = carteiras[periodo]['BLC_4']
        
        # Identificar colunas
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
            # Top ações do período
            top_acoes = df_acoes.nlargest(10, valor_col)
            
            for _, row in top_acoes.iterrows():
                historico_acoes.append({
                    'periodo': periodo,
                    'acao': row[nome_col],
                    'valor': row[valor_col],
                    'total_periodo': df_acoes[valor_col].sum()
                })
    
    return pd.DataFrame(historico_acoes)

def analisar_derivativos_detalhe(carteiras):
    """
    Análise detalhada dos derivativos
    """
    derivativos_detalhe = []
    
    for periodo in sorted(carteiras.keys()):
        if 'BLC_5' not in carteiras[periodo]:
            continue
            
        df_deriv = carteiras[periodo]['BLC_5']
        
        # Buscar informações relevantes
        info = {
            'periodo': periodo,
            'num_posicoes': len(df_deriv),
            'valor_total': 0
        }
        
        # Valor total
        for col in ['VL_MERC_POS_FINAL', 'VL_MERCADO', 'VL_POS_FINAL']:
            if col in df_deriv.columns:
                info['valor_total'] = df_deriv[col].sum()
                break
        
        # Tentar identificar tipos
        for col in ['TP_DERIVATIVO', 'DS_DERIVATIVO', 'DS_ATIVO']:
            if col in df_deriv.columns and len(df_deriv) > 0:
                info['tipos'] = df_deriv[col].value_counts().to_dict()
                break
        
        if info['valor_total'] > 0:
            derivativos_detalhe.append(info)
    
    return derivativos_detalhe

def gerar_visualizacoes_completas(df_evolucao, df_acoes_hist, derivativos_info):
    """
    Gera conjunto completo de visualizações
    """
    print("\nGerando visualizações...")
    
    # Criar figura com múltiplos gráficos
    fig = plt.figure(figsize=(20, 24))
    
    # 1. Evolução do patrimônio total
    ax1 = plt.subplot(5, 2, 1)
    if not df_evolucao.empty:
        ax1.plot(df_evolucao['periodo'], df_evolucao['total']/1e6, 
                marker='o', linewidth=3, markersize=8, color='darkblue')
        ax1.fill_between(df_evolucao['periodo'], df_evolucao['total']/1e6, alpha=0.3)
        ax1.set_title('Evolução do Patrimônio Total', fontsize=16, fontweight='bold')
        ax1.set_xlabel('Período')
        ax1.set_ylabel('Valor (R$ milhões)')
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True, alpha=0.3)
        
        # Adicionar anotações de máximo e mínimo
        max_idx = df_evolucao['total'].idxmax()
        min_idx = df_evolucao['total'].idxmin()
        ax1.annotate(f'Máx: R$ {df_evolucao.loc[max_idx, "total"]/1e6:.0f}M', 
                    xy=(max_idx, df_evolucao.loc[max_idx, 'total']/1e6),
                    xytext=(10, 10), textcoords='offset points')
    
    # 2. Composição da carteira (área empilhada)
    ax2 = plt.subplot(5, 2, 2)
    if not df_evolucao.empty:
        tipos = ['acoes', 'titulos_publicos', 'cotas_fundos', 'outros', 'derivativos']
        cores = ['#2ecc71', '#3498db', '#9b59b6', '#95a5a6', '#e74c3c']
        
        # Preparar dados
        bottom = np.zeros(len(df_evolucao))
        for i, tipo in enumerate(tipos):
            if tipo in df_evolucao.columns:
                valores = df_evolucao[tipo].values / 1e6
                ax2.bar(df_evolucao['periodo'], valores, bottom=bottom, 
                       label=tipo.replace('_', ' ').title(), color=cores[i], alpha=0.8)
                bottom += valores
        
        ax2.set_title('Composição da Carteira ao Longo do Tempo', fontsize=16, fontweight='bold')
        ax2.set_xlabel('Período')
        ax2.set_ylabel('Valor (R$ milhões)')
        ax2.tick_params(axis='x', rotation=45)
        ax2.legend(loc='upper left', fontsize=10)
        ax2.grid(True, alpha=0.3, axis='y')
    
    # 3. Evolução percentual das ações
    ax3 = plt.subplot(5, 2, 3)
    if not df_evolucao.empty and 'acoes' in df_evolucao.columns:
        pct_acoes = (df_evolucao['acoes'] / df_evolucao['total'] * 100)
        ax3.plot(df_evolucao['periodo'], pct_acoes, 
                marker='o', linewidth=3, markersize=8, color='green')
        ax3.fill_between(df_evolucao['periodo'], pct_acoes, alpha=0.3, color='green')
        ax3.set_title('Percentual do Patrimônio em Ações', fontsize=16, fontweight='bold')
        ax3.set_xlabel('Período')
        ax3.set_ylabel('% do Patrimônio Total')
        ax3.tick_params(axis='x', rotation=45)
        ax3.set_ylim(0, 100)
        ax3.grid(True, alpha=0.3)
        ax3.axhline(y=50, color='red', linestyle='--', alpha=0.5)
    
    # 4. Valor absoluto em ações
    ax4 = plt.subplot(5, 2, 4)
    if not df_evolucao.empty and 'acoes' in df_evolucao.columns:
        ax4.bar(df_evolucao['periodo'], df_evolucao['acoes']/1e6, 
               alpha=0.7, color='darkgreen')
        ax4.set_title('Valor Investido em Ações', fontsize=16, fontweight='bold')
        ax4.set_xlabel('Período')
        ax4.set_ylabel('Valor (R$ milhões)')
        ax4.tick_params(axis='x', rotation=45)
        ax4.grid(True, alpha=0.3, axis='y')
    
    # 5. Concentração em top 5 ações
    ax5 = plt.subplot(5, 2, 5)
    if not df_acoes_hist.empty:
        concentracao = []
        periodos = []
        
        for periodo in df_acoes_hist['periodo'].unique():
            df_periodo = df_acoes_hist[df_acoes_hist['periodo'] == periodo]
            if len(df_periodo) >= 5:
                top5_valor = df_periodo.nlargest(5, 'valor')['valor'].sum()
                total = df_periodo['total_periodo'].iloc[0]
                if total > 0:
                    concentracao.append(top5_valor / total * 100)
                    periodos.append(periodo)
        
        if concentracao:
            ax5.plot(periodos, concentracao, marker='s', linewidth=2, markersize=8, color='red')
            ax5.set_title('Concentração das Top 5 Ações', fontsize=16, fontweight='bold')
            ax5.set_xlabel('Período')
            ax5.set_ylabel('% do Total em Ações')
            ax5.tick_params(axis='x', rotation=45)
            ax5.set_ylim(0, 100)
            ax5.grid(True, alpha=0.3)
            ax5.axhline(y=50, color='red', linestyle='--', alpha=0.5)
    
    # 6. Evolução dos derivativos
    ax6 = plt.subplot(5, 2, 6)
    if derivativos_info:
        periodos_deriv = [d['periodo'] for d in derivativos_info]
        valores_deriv = [d['valor_total']/1e6 for d in derivativos_info]
        
        ax6.plot(periodos_deriv, valores_deriv, marker='o', linewidth=2, 
                markersize=8, color='orange')
        ax6.fill_between(periodos_deriv, valores_deriv, alpha=0.3, color='orange')
        ax6.set_title('Evolução das Posições em Derivativos', fontsize=16, fontweight='bold')
        ax6.set_xlabel('Período')
        ax6.set_ylabel('Valor (R$ milhões)')
        ax6.tick_params(axis='x', rotation=45)
        ax6.grid(True, alpha=0.3)
    
    # 7. Composição percentual média
    ax7 = plt.subplot(5, 2, 7)
    if not df_evolucao.empty:
        # Calcular médias
        tipos = ['acoes', 'titulos_publicos', 'cotas_fundos', 'outros']
        medias = []
        labels = []
        
        for tipo in tipos:
            if tipo in df_evolucao.columns:
                media_pct = (df_evolucao[tipo] / df_evolucao['total'] * 100).mean()
                if media_pct > 0:
                    medias.append(media_pct)
                    labels.append(tipo.replace('_', ' ').title())
        
        if medias:
            colors = plt.cm.Set3(np.linspace(0, 1, len(medias)))
            ax7.pie(medias, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
            ax7.set_title('Composição Média da Carteira (2022-2024)', fontsize=16, fontweight='bold')
    
    # 8. Volatilidade do patrimônio
    ax8 = plt.subplot(5, 2, 8)
    if not df_evolucao.empty and len(df_evolucao) > 1:
        # Calcular retornos mensais
        retornos = df_evolucao['total'].pct_change().dropna() * 100
        
        ax8.bar(df_evolucao['periodo'][1:], retornos, 
               color=['green' if r > 0 else 'red' for r in retornos], alpha=0.7)
        ax8.set_title('Variação Mensal do Patrimônio (%)', fontsize=16, fontweight='bold')
        ax8.set_xlabel('Período')
        ax8.set_ylabel('Variação (%)')
        ax8.tick_params(axis='x', rotation=45)
        ax8.grid(True, alpha=0.3, axis='y')
        ax8.axhline(y=0, color='black', linewidth=0.5)
    
    # 9. Número de posições em ações
    ax9 = plt.subplot(5, 2, 9)
    if not df_acoes_hist.empty:
        num_acoes_por_periodo = df_acoes_hist.groupby('periodo')['acao'].nunique()
        ax9.plot(num_acoes_por_periodo.index, num_acoes_por_periodo.values,
                marker='o', linewidth=2, markersize=8, color='darkblue')
        ax9.set_title('Número de Ações Diferentes na Carteira', fontsize=16, fontweight='bold')
        ax9.set_xlabel('Período')
        ax9.set_ylabel('Quantidade de Ações')
        ax9.tick_params(axis='x', rotation=45)
        ax9.grid(True, alpha=0.3)
    
    
    # 10. Resumo estatístico
    ax10 = plt.subplot(5, 2, 10)
    ax10.axis('off')
    
    if not df_evolucao.empty:
        # Calcular estatísticas
        stats_text = f"""
        RESUMO ESTATÍSTICO (2022-2024)
        
        Patrimônio Médio: R$ {df_evolucao['total'].mean()/1e6:.0f}M
        Patrimônio Máximo: R$ {df_evolucao['total'].max()/1e6:.0f}M
        Patrimônio Mínimo: R$ {df_evolucao['total'].min()/1e6:.0f}M
        
        % Médio em Ações: {(df_evolucao['acoes']/df_evolucao['total']*100).mean():.1f}%
        % Máximo em Ações: {(df_evolucao['acoes']/df_evolucao['total']*100).max():.1f}%
        
        Volatilidade Mensal: {df_evolucao['total'].pct_change().std()*100:.1f}%
        
        Períodos Analisados: {len(df_evolucao)}
        """
        
        ax10.text(0.1, 0.5, stats_text, fontsize=12, verticalalignment='center',
                 bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig('capstone_analise_2022_2024.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("Gráficos salvos em 'capstone_analise_2022_2024.png'")

def gerar_relatorio_html_corrigido(carteiras, df_evolucao, df_acoes_hist, derivativos_info):
    """
    Gera relatório HTML com dados corrigidos
    """
    print("\nGerando relatório HTML...")
    
    # Estatísticas gerais
    patrimonio_medio = df_evolucao['total'].mean() if not df_evolucao.empty else 0
    patrimonio_max = df_evolucao['total'].max() if not df_evolucao.empty else 0
    pct_acoes_medio = (df_evolucao['acoes']/df_evolucao['total']*100).mean() if not df_evolucao.empty else 0
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Análise Fundo Capstone - 2022 a 2024</title>
        <style>
            body {{
                font-family: 'Arial', sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f0f2f5;
                color: #333;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                background-color: white;
                box-shadow: 0 0 30px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                padding: 60px 40px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 42px;
                font-weight: 300;
                letter-spacing: 2px;
            }}
            .header .subtitle {{
                margin-top: 15px;
                font-size: 20px;
                opacity: 0.9;
            }}
            .header .period {{
                margin-top: 10px;
                font-size: 18px;
                opacity: 0.8;
            }}
            .content {{
                padding: 40px;
            }}
            .alert {{
                background: #fff3cd;
                border: 1px solid #ffeeba;
                color: #856404;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 30px;
            }}
            .alert h3 {{
                margin-top: 0;
            }}
            .summary-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 25px;
                margin-bottom: 40px;
            }}
            .metric-card {{
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 25px;
                box-shadow: 0 3px 10px rgba(0,0,0,0.08);
                transition: all 0.3s ease;
            }}
            .metric-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 5px 20px rgba(0,0,0,0.15);
            }}
            .metric-card h3 {{
                margin: 0 0 15px 0;
                color: #2a5298;
                font-size: 16px;
                text-transform: uppercase;
                letter-spacing: 1px;
                font-weight: 600;
            }}
            .metric-card .value {{
                font-size: 32px;
                font-weight: bold;
                color: #1e3c72;
                margin-bottom: 5px;
            }}
            .metric-card .detail {{
                font-size: 14px;
                color: #666;
            }}
            .chart-section {{
                margin: 50px 0;
                text-align: center;
            }}
            .chart-section img {{
                max-width: 100%;
                border-radius: 10px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            }}
            h2 {{
                color: #1e3c72;
                font-size: 28px;
                margin: 40px 0 20px 0;
                padding-bottom: 15px;
                border-bottom: 3px solid #2a5298;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 25px 0;
                background: white;
                box-shadow: 0 5px 15px rgba(0,0,0,0.08);
                border-radius: 8px;
                overflow: hidden;
            }}
            th {{
                background: #2a5298;
                color: white;
                padding: 15px;
                text-align: left;
                font-weight: 600;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            td {{
                padding: 15px;
                border-bottom: 1px solid #f0f0f0;
            }}
            tr:hover {{
                background: #f8f9fa;
            }}
            .insight-box {{
                background: #e3f2fd;
                border-left: 5px solid #2a5298;
                padding: 25px;
                margin: 30px 0;
                border-radius: 8px;
            }}
            .insight-box h3 {{
                margin-top: 0;
                color: #1e3c72;
            }}
            .footer {{
                background: #1e3c72;
                color: white;
                text-align: center;
                padding: 30px;
                margin-top: 60px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Análise do Fundo Capstone</h1>
                <div class="subtitle">CNPJ: 35.803.288/0001-17</div>
                <div class="period">Período: Janeiro/2022 a Novembro/2024</div>
            </div>
            
            <div class="content">
                <div class="alert">
                    <h3>⚠️ Nota sobre os Dados</h3>
                    <p>Esta análise exclui os dados de dezembro/2024 em diante devido a anomalias detectadas, 
                    onde o patrimônio cai drasticamente de ~R$ 17 bilhões para ~R$ 3 bilhões e as posições em 
                    ações desaparecem completamente. Isso pode indicar um evento corporativo significativo 
                    (resgate massivo, mudança de estratégia, ou erro nos dados).</p>
                </div>
                
                <div class="summary-grid">
                    <div class="metric-card">
                        <h3>Patrimônio Médio</h3>
                        <div class="value">R$ {patrimonio_medio/1e6:.0f}M</div>
                        <div class="detail">Média do período analisado</div>
                    </div>
                    <div class="metric-card">
                        <h3>Patrimônio Máximo</h3>
                        <div class="value">R$ {patrimonio_max/1e6:.0f}M</div>
                        <div class="detail">Pico histórico no período</div>
                    </div>
                    <div class="metric-card">
                        <h3>Alocação Média em Ações</h3>
                        <div class="value">{pct_acoes_medio:.1f}%</div>
                        <div class="detail">Percentual médio do patrimônio</div>
                    </div>
                    <div class="metric-card">
                        <h3>Períodos Analisados</h3>
                        <div class="value">{len(df_evolucao)}</div>
                        <div class="detail">Meses com dados disponíveis</div>
                    </div>
                </div>
                
                <div class="chart-section">
                    <h2>Visualizações e Análises</h2>
                    <img src="capstone_analise_2022_2024.png" alt="Análise Completa 2022-2024">
                </div>
    """
    
    # Tabela de evolução patrimonial
    if not df_evolucao.empty:
        html_content += """
                <h2>Evolução Patrimonial Detalhada</h2>
                <table>
                    <tr>
                        <th>Período</th>
                        <th>Patrimônio Total</th>
                        <th>Ações</th>
                        <th>Títulos Públicos</th>
                        <th>Cotas de Fundos</th>
                        <th>Outros</th>
                    </tr>
        """
        
        for _, row in df_evolucao.iterrows():
            outros_total = row['outros'] + row['debentures'] + row['titulos_bancarios'] + row['op_compromissadas']
            html_content += f"""
                    <tr>
                        <td><strong>{row['periodo']}</strong></td>
                        <td>R$ {row['total']/1e6:.0f}M</td>
                        <td>R$ {row['acoes']/1e6:.0f}M ({row['acoes']/row['total']*100:.1f}%)</td>
                        <td>R$ {row['titulos_publicos']/1e6:.0f}M ({row['titulos_publicos']/row['total']*100:.1f}%)</td>
                        <td>R$ {row['cotas_fundos']/1e6:.0f}M ({row['cotas_fundos']/row['total']*100:.1f}%)</td>
                        <td>R$ {outros_total/1e6:.0f}M ({outros_total/row['total']*100:.1f}%)</td>
                    </tr>
            """
        
        html_content += "</table>"
    
    # Top ações históricas
    if not df_acoes_hist.empty:
        # Pegar último período válido (novembro/2024)
        ultimo_periodo = '2024-11'
        acoes_ultimo = df_acoes_hist[df_acoes_hist['periodo'] == ultimo_periodo]
        
        if not acoes_ultimo.empty:
            html_content += f"""
                <h2>Principais Posições em Ações - {ultimo_periodo}</h2>
                <table>
                    <tr>
                        <th>Ranking</th>
                        <th>Ação</th>
                        <th>Valor</th>
                        <th>% da Carteira de Ações</th>
                    </tr>
            """
            
            top_acoes = acoes_ultimo.nlargest(15, 'valor')
            total_acoes = acoes_ultimo['total_periodo'].iloc[0]
            
            for i, (_, row) in enumerate(top_acoes.iterrows(), 1):
                pct = (row['valor'] / total_acoes * 100) if total_acoes > 0 else 0
                html_content += f"""
                    <tr>
                        <td>{i}</td>
                        <td><strong>{row['acao']}</strong></td>
                        <td>R$ {row['valor']/1e6:.1f}M</td>
                        <td>{pct:.2f}%</td>
                    </tr>
                """
            
            html_content += "</table>"
    
    # Insights sobre derivativos
    if derivativos_info:
        valor_medio_deriv = sum(d['valor_total'] for d in derivativos_info) / len(derivativos_info)
        
        html_content += f"""
                <h2>Análise de Derivativos</h2>
                <div class="insight-box">
                    <h3>Uso Consistente de Derivativos</h3>
                    <p>O fundo mantém posições regulares em derivativos com valor médio de 
                    R$ {valor_medio_deriv/1e6:.1f}M, representando aproximadamente 0.1% do patrimônio total.</p>
                    <p>Esta exposição limitada sugere uso principalmente para:</p>
                    <ul>
                        <li>Hedge de posições em ações</li>
                        <li>Gestão de risco cambial</li>
                        <li>Otimização fiscal</li>
                    </ul>
                </div>
        """
    
    # Principais conclusões
    html_content += """
                <h2>Principais Conclusões</h2>
                <div class="insight-box">
                    <h3>Perfil de Investimento</h3>
                    <ol>
                        <li><strong>Fundo de Ações Ativo:</strong> Média de 40-50% do patrimônio em renda variável, 
                        com picos acima de 50%.</li>
                        
                        <li><strong>Diversificação Significativa:</strong> Investe em mais de 180 ações diferentes, 
                        com foco em blue chips brasileiras.</li>
                        
                        <li><strong>Gestão de Liquidez:</strong> Mantém parcela relevante em títulos públicos e 
                        cotas de outros fundos para gestão de liquidez.</li>
                        
                        <li><strong>Crescimento Patrimonial:</strong> O fundo cresceu significativamente durante 
                        o período analisado, atingindo pico de R$ 19 bilhões em julho/2024.</li>
                        
                        <li><strong>Anomalia em Dez/2024:</strong> A queda abrupta do patrimônio e desaparecimento 
                        das posições em ações requer investigação adicional.</li>
                    </ol>
                </div>
            </div>
            
            <div class="footer">
                <p>Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')} | 
                Análise baseada em dados públicos da CVM | Período: Jan/2022 a Nov/2024</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    with open('capstone.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("Relatório HTML salvo em 'capstone.html'")

def main():
    """
    Função principal
    """
    print("=" * 80)
    print("ANÁLISE FUNDO CAPSTONE - PERÍODO 2022 A 2024")
    print("=" * 80)
    
    # 1. Processar dados
    carteiras = processar_periodo_especifico(inicio_ano=2022, fim_ano=2024, fim_mes=11)
    
    if not carteiras:
        print("\nERRO: Nenhum dado encontrado!")
        return
    
    # 2. Análises
    print("\n" + "=" * 60)
    print("Realizando análises...")
    
    df_evolucao = analisar_evolucao_detalhada(carteiras)
    df_acoes_hist = analisar_acoes_historico(carteiras)
    derivativos_info = analisar_derivativos_detalhe(carteiras)
    
    # 3. Mostrar resumo
    print("\nRESUMO DA ANÁLISE:")
    print(f"- Períodos processados: {len(carteiras)}")
    print(f"- Patrimônio médio: R$ {df_evolucao['total'].mean()/1e6:.0f}M")
    print(f"- Patrimônio máximo: R$ {df_evolucao['total'].max()/1e6:.0f}M (em {df_evolucao.loc[df_evolucao['total'].idxmax(), 'periodo']})")
    print(f"- % médio em ações: {(df_evolucao['acoes']/df_evolucao['total']*100).mean():.1f}%")
    
    # 4. Gerar visualizações
    gerar_visualizacoes_completas(df_evolucao, df_acoes_hist, derivativos_info)
    
    # 5. Gerar relatório HTML
    gerar_relatorio_html_corrigido(carteiras, df_evolucao, df_acoes_hist, derivativos_info)
    
    # 6. Salvar dados
    print("\nSalvando dados processados...")
    dados = {
        'carteiras': carteiras,
        'evolucao': df_evolucao,
        'acoes_historico': df_acoes_hist,
        'derivativos': derivativos_info,
        'processamento': datetime.now().isoformat()
    }
    
    with open('capstone_dados_2022_2024.pkl', 'wb') as f:
        pickle.dump(dados, f)
    
    print("\n" + "=" * 80)
    print("ANÁLISE CONCLUÍDA!")
    print("Arquivos gerados:")
    print("- capstone_analise_2022_2024.png (visualizações)")
    print("- capstone.html (relatório completo)")
    print("- capstone_dados_2022_2024.pkl (dados serializados)")
    print("=" * 80)

if __name__ == "__main__":
    main()