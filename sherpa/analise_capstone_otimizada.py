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
warnings.filterwarnings('ignore')

# Configurações
CNPJ_CAPSTONE = "35.803.288/0001-17"
BASE_DIR = "/mnt/c/Users/guilh/Documents/GitHub/sherpa/database"

# Configurar matplotlib para não exibir GUI
plt.switch_backend('Agg')

def processar_ultimos_24_meses():
    """
    Processa apenas os últimos 24 meses de dados
    """
    cda_dir = os.path.join(BASE_DIR, "CDA")
    carteiras_por_periodo = {}
    
    print(f"Processando últimos 24 meses do fundo Capstone (CNPJ: {CNPJ_CAPSTONE})")
    
    # Lista de arquivos dos últimos 24 meses
    arquivos_processar = [
        "cda_fi_202412.zip", "cda_fi_202411.zip", "cda_fi_202410.zip",
        "cda_fi_202409.zip", "cda_fi_202408.zip", "cda_fi_202407.zip",
        "cda_fi_202406.zip", "cda_fi_202405.zip", "cda_fi_202404.zip",
        "cda_fi_202403.zip", "cda_fi_202402.zip", "cda_fi_202401.zip",
        "cda_fi_202312.zip", "cda_fi_202311.zip", "cda_fi_202310.zip",
        "cda_fi_202309.zip", "cda_fi_202308.zip", "cda_fi_202307.zip",
        "cda_fi_202306.zip", "cda_fi_202305.zip", "cda_fi_202304.zip",
        "cda_fi_202303.zip", "cda_fi_202302.zip", "cda_fi_202301.zip"
    ]
    
    for arquivo in arquivos_processar:
        arquivo_path = os.path.join(cda_dir, arquivo)
        if not os.path.exists(arquivo_path):
            continue
            
        try:
            # Extrair período
            periodo_str = arquivo.replace("cda_fi_", "").replace(".zip", "")
            periodo = periodo_str[:4] + "-" + periodo_str[4:6]
            
            print(f"Processando {periodo}...", end="")
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
                print(f" ✓ {', '.join([f'{k}({len(v)})' for k, v in dados_periodo.items()])}")
            else:
                print(" ✗ Sem dados")
                
        except Exception as e:
            print(f" Erro: {e}")
    
    print(f"\nTotal de períodos com dados: {len(carteiras_por_periodo)}")
    return carteiras_por_periodo

def analisar_dados_rapido(carteiras):
    """
    Análise rápida dos dados principais
    """
    # Evolução patrimonial
    evolucao = []
    
    for periodo in sorted(carteiras.keys()):
        dados = {
            'periodo': periodo,
            'total': 0,
            'acoes': 0,
            'derivativos': 0,
            'debentures': 0,
            'outros': 0
        }
        
        # BLC_4 = Ações
        if 'BLC_4' in carteiras[periodo]:
            df = carteiras[periodo]['BLC_4']
            for col in ['VL_MERC_POS_FINAL', 'VL_MERCADO', 'VL_POS_FINAL']:
                if col in df.columns:
                    dados['acoes'] = df[col].sum()
                    dados['total'] += dados['acoes']
                    break
        
        # BLC_5 = Derivativos
        if 'BLC_5' in carteiras[periodo]:
            df = carteiras[periodo]['BLC_5']
            for col in ['VL_MERC_POS_FINAL', 'VL_MERCADO', 'VL_POS_FINAL']:
                if col in df.columns:
                    dados['derivativos'] = df[col].sum()
                    dados['total'] += dados['derivativos']
                    break
        
        # BLC_3 = Debêntures
        if 'BLC_3' in carteiras[periodo]:
            df = carteiras[periodo]['BLC_3']
            for col in ['VL_MERC_POS_FINAL', 'VL_MERCADO', 'VL_POS_FINAL']:
                if col in df.columns:
                    dados['debentures'] = df[col].sum()
                    dados['total'] += dados['debentures']
                    break
        
        # Outros BLCs
        for blc in ['BLC_1', 'BLC_2', 'BLC_6', 'BLC_7', 'BLC_8']:
            if blc in carteiras[periodo]:
                df = carteiras[periodo][blc]
                for col in ['VL_MERC_POS_FINAL', 'VL_MERCADO', 'VL_POS_FINAL']:
                    if col in df.columns:
                        valor = df[col].sum()
                        dados['outros'] += valor
                        dados['total'] += valor
                        break
        
        if dados['total'] > 0:
            evolucao.append(dados)
    
    return pd.DataFrame(evolucao)

def analisar_top_acoes(carteiras):
    """
    Analisa as principais ações do fundo
    """
    ultimo_periodo = max(carteiras.keys())
    
    if 'BLC_4' not in carteiras[ultimo_periodo]:
        return pd.DataFrame()
    
    df_acoes = carteiras[ultimo_periodo]['BLC_4']
    
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
        return df_acoes[[nome_col, valor_col]].rename(columns={
            nome_col: 'acao',
            valor_col: 'valor'
        }).sort_values('valor', ascending=False)
    
    return pd.DataFrame()

def gerar_graficos_simples(df_evolucao, df_top_acoes):
    """
    Gera visualizações principais
    """
    print("\nGerando visualizações...")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Análise do Fundo Capstone - Últimos 24 Meses', fontsize=16)
    
    # 1. Evolução do patrimônio
    ax1 = axes[0, 0]
    ax1.plot(df_evolucao['periodo'], df_evolucao['total'], 
            marker='o', linewidth=2, markersize=8)
    ax1.set_title('Evolução do Patrimônio Total')
    ax1.set_xlabel('Período')
    ax1.set_ylabel('Valor (R$ milhões)')
    ax1.tick_params(axis='x', rotation=45)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}'))
    ax1.grid(True, alpha=0.3)
    
    # 2. Composição da carteira
    ax2 = axes[0, 1]
    if not df_evolucao.empty:
        ultimo = df_evolucao.iloc[-1]
        valores = []
        labels = []
        
        if ultimo['acoes'] > 0:
            valores.append(ultimo['acoes'])
            labels.append(f"Ações\n{ultimo['acoes']/ultimo['total']*100:.1f}%")
        if ultimo['derivativos'] > 0:
            valores.append(ultimo['derivativos'])
            labels.append(f"Derivativos\n{ultimo['derivativos']/ultimo['total']*100:.1f}%")
        if ultimo['debentures'] > 0:
            valores.append(ultimo['debentures'])
            labels.append(f"Debêntures\n{ultimo['debentures']/ultimo['total']*100:.1f}%")
        if ultimo['outros'] > 0:
            valores.append(ultimo['outros'])
            labels.append(f"Outros\n{ultimo['outros']/ultimo['total']*100:.1f}%")
        
        ax2.pie(valores, labels=labels, autopct='R$ %.0fM', startangle=90,
                pctdistance=0.85, labeldistance=1.1)
        ax2.set_title(f"Composição da Carteira - {ultimo['periodo']}")
    
    # 3. Evolução das ações
    ax3 = axes[1, 0]
    df_com_acoes = df_evolucao[df_evolucao['acoes'] > 0]
    if not df_com_acoes.empty:
        ax3.bar(df_com_acoes['periodo'], df_com_acoes['acoes']/1e6, 
               alpha=0.7, color='green')
        ax3.set_title('Evolução das Posições em Ações')
        ax3.set_xlabel('Período')
        ax3.set_ylabel('Valor (R$ milhões)')
        ax3.tick_params(axis='x', rotation=45)
        ax3.grid(True, alpha=0.3)
    
    # 4. Top 10 ações
    ax4 = axes[1, 1]
    if not df_top_acoes.empty:
        top10 = df_top_acoes.head(10)
        y_pos = np.arange(len(top10))
        ax4.barh(y_pos, top10['valor']/1e6)
        ax4.set_yticks(y_pos)
        ax4.set_yticklabels(top10['acao'], fontsize=8)
        ax4.set_xlabel('Valor (R$ milhões)')
        ax4.set_title('Top 10 Ações - Último Período')
        ax4.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    plt.savefig('capstone_analise.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print("Gráficos salvos em 'capstone_analise.png'")

def gerar_html_simples(carteiras, df_evolucao, df_top_acoes):
    """
    Gera relatório HTML simplificado
    """
    print("\nGerando relatório HTML...")
    
    periodo_inicial = min(carteiras.keys()) if carteiras else "N/A"
    periodo_final = max(carteiras.keys()) if carteiras else "N/A"
    
    patrimonio_atual = df_evolucao.iloc[-1]['total'] if not df_evolucao.empty else 0
    patrimonio_inicial = df_evolucao.iloc[0]['total'] if not df_evolucao.empty else 0
    evolucao_pct = ((patrimonio_atual / patrimonio_inicial - 1) * 100) if patrimonio_inicial > 0 else 0
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Análise Fundo Capstone</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
            h1, h2 {{ color: #2c3e50; }}
            .info {{ background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
            .stat-card {{ background: #3498db; color: white; padding: 20px; border-radius: 5px; text-align: center; }}
            .stat-value {{ font-size: 28px; font-weight: bold; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background: #34495e; color: white; }}
            tr:hover {{ background: #f5f5f5; }}
            .chart {{ text-align: center; margin: 30px 0; }}
            img {{ max-width: 100%; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Análise do Fundo Capstone</h1>
            <div class="info">
                <p><strong>CNPJ:</strong> 35.803.288/0001-17</p>
                <p><strong>Período Analisado:</strong> {periodo_inicial} a {periodo_final}</p>
                <p><strong>Observação:</strong> Fundo não encontrado no cadastro CVM, mas com dados de carteira disponíveis.</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div>Patrimônio Atual</div>
                    <div class="stat-value">R$ {patrimonio_atual/1e6:.1f}M</div>
                </div>
                <div class="stat-card">
                    <div>Evolução</div>
                    <div class="stat-value">{evolucao_pct:+.1f}%</div>
                </div>
                <div class="stat-card">
                    <div>Posição em Ações</div>
                    <div class="stat-value">R$ {df_evolucao.iloc[-1]['acoes']/1e6:.1f}M</div>
                </div>
            </div>
            
            <h2>Visualizações</h2>
            <div class="chart">
                <img src="capstone_analise.png" alt="Análise Gráfica">
            </div>
    """
    
    # Tabela de evolução
    if not df_evolucao.empty:
        html += """
            <h2>Evolução Mensal</h2>
            <table>
                <tr>
                    <th>Período</th>
                    <th>Patrimônio Total</th>
                    <th>Ações</th>
                    <th>Derivativos</th>
                    <th>Outros</th>
                </tr>
        """
        
        for _, row in df_evolucao.iterrows():
            html += f"""
                <tr>
                    <td>{row['periodo']}</td>
                    <td>R$ {row['total']/1e6:.1f}M</td>
                    <td>R$ {row['acoes']/1e6:.1f}M</td>
                    <td>R$ {row['derivativos']/1e6:.1f}M</td>
                    <td>R$ {(row['debentures'] + row['outros'])/1e6:.1f}M</td>
                </tr>
            """
        
        html += "</table>"
    
    # Top ações
    if not df_top_acoes.empty:
        html += """
            <h2>Top 20 Ações - Último Período</h2>
            <table>
                <tr>
                    <th>Posição</th>
                    <th>Ação</th>
                    <th>Valor</th>
                    <th>% do Total</th>
                </tr>
        """
        
        total_acoes = df_top_acoes['valor'].sum()
        for i, (_, row) in enumerate(df_top_acoes.head(20).iterrows(), 1):
            pct = (row['valor'] / total_acoes * 100) if total_acoes > 0 else 0
            html += f"""
                <tr>
                    <td>{i}</td>
                    <td>{row['acao']}</td>
                    <td>R$ {row['valor']/1e6:.2f}M</td>
                    <td>{pct:.1f}%</td>
                </tr>
            """
        
        html += "</table>"
    
    html += """
        </div>
    </body>
    </html>
    """
    
    with open('capstone.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("Relatório salvo em 'capstone.html'")

def main():
    """
    Função principal otimizada
    """
    print("=" * 60)
    print("ANÁLISE OTIMIZADA - FUNDO CAPSTONE")
    print("=" * 60)
    
    # 1. Processar últimos 24 meses
    carteiras = processar_ultimos_24_meses()
    
    if not carteiras:
        print("\nNenhum dado encontrado!")
        return
    
    # 2. Análise rápida
    print("\nAnalisando dados...")
    df_evolucao = analisar_dados_rapido(carteiras)
    df_top_acoes = analisar_top_acoes(carteiras)
    
    # 3. Gerar visualizações
    gerar_graficos_simples(df_evolucao, df_top_acoes)
    
    # 4. Gerar HTML
    gerar_html_simples(carteiras, df_evolucao, df_top_acoes)
    
    # 5. Salvar dados
    print("\nSalvando dados...")
    dados = {
        'carteiras': carteiras,
        'evolucao': df_evolucao,
        'top_acoes': df_top_acoes,
        'processamento': datetime.now().isoformat()
    }
    
    with open('capstone_dados.pkl', 'wb') as f:
        pickle.dump(dados, f)
    
    print("\n" + "=" * 60)
    print("ANÁLISE CONCLUÍDA!")
    print("Arquivos gerados:")
    print("- capstone_analise.png")
    print("- capstone.html")
    print("- capstone_dados.pkl")
    print("=" * 60)

if __name__ == "__main__":
    main()