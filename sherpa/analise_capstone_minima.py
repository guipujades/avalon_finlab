import pandas as pd
import numpy as np
import os
import zipfile
from datetime import datetime
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

CNPJ_CAPSTONE = "35.803.288/0001-17"
BASE_DIR = "/mnt/c/Users/guilh/Documents/GitHub/sherpa/database"
plt.switch_backend('Agg')

def processar_arquivo_rapido(arquivo_path, periodo):
    """Processa um único arquivo de forma rápida"""
    dados = {}
    
    try:
        with zipfile.ZipFile(arquivo_path, 'r') as zip_file:
            # Processar apenas BLC_4 (ações) e BLC_5 (derivativos) inicialmente
            for blc_num in [4, 5]:
                for nome in zip_file.namelist():
                    if f"BLC_{blc_num}" in nome and nome.endswith('.csv'):
                        with zip_file.open(nome) as f:
                            df = pd.read_csv(f, sep=';', encoding='ISO-8859-1', low_memory=False)
                            
                            # Buscar CNPJ
                            for col in ['CNPJ_FUNDO_CLASSE', 'CNPJ_FUNDO']:
                                if col in df.columns:
                                    mask = df[col].astype(str).str.strip() == CNPJ_CAPSTONE
                                    df_fundo = df[mask]
                                    if not df_fundo.empty:
                                        dados[f'BLC_{blc_num}'] = df_fundo
                                        print(f"  ✓ BLC_{blc_num}: {len(df_fundo)} registros")
                                    break
                        break
    except Exception as e:
        print(f"  Erro: {e}")
    
    return dados

def main():
    print("ANÁLISE RÁPIDA - FUNDO CAPSTONE")
    print("=" * 50)
    
    cda_dir = os.path.join(BASE_DIR, "CDA")
    
    # Processar apenas 3 arquivos mais recentes
    arquivos = ["cda_fi_202412.zip", "cda_fi_202411.zip", "cda_fi_202410.zip"]
    
    resultados = {}
    
    for arquivo in arquivos:
        arquivo_path = os.path.join(cda_dir, arquivo)
        if os.path.exists(arquivo_path):
            periodo = arquivo.replace("cda_fi_", "").replace(".zip", "")
            periodo_fmt = f"{periodo[:4]}-{periodo[4:6]}"
            
            print(f"\nProcessando {periodo_fmt}...")
            dados = processar_arquivo_rapido(arquivo_path, periodo_fmt)
            
            if dados:
                resultados[periodo_fmt] = dados
    
    # Análise simples
    print("\n" + "=" * 50)
    print("RESUMO DA ANÁLISE")
    print("=" * 50)
    
    for periodo, dados in sorted(resultados.items(), reverse=True):
        print(f"\nPeríodo: {periodo}")
        
        # Ações (BLC_4)
        if 'BLC_4' in dados:
            df_acoes = dados['BLC_4']
            
            # Buscar coluna de valor
            valor_col = None
            for col in ['VL_MERC_POS_FINAL', 'VL_MERCADO', 'VL_POS_FINAL']:
                if col in df_acoes.columns:
                    valor_col = col
                    break
            
            if valor_col:
                total_acoes = df_acoes[valor_col].sum()
                print(f"  Ações: R$ {total_acoes/1e6:.1f}M em {len(df_acoes)} posições")
                
                # Top 5 ações
                nome_col = None
                for col in ['NM_ATIVO', 'DS_ATIVO']:
                    if col in df_acoes.columns:
                        nome_col = col
                        break
                
                if nome_col:
                    top5 = df_acoes.nlargest(5, valor_col)
                    print("  Top 5 ações:")
                    for _, row in top5.iterrows():
                        print(f"    - {row[nome_col]}: R$ {row[valor_col]/1e6:.1f}M")
        
        # Derivativos (BLC_5)
        if 'BLC_5' in dados:
            df_deriv = dados['BLC_5']
            
            valor_col = None
            for col in ['VL_MERC_POS_FINAL', 'VL_MERCADO', 'VL_POS_FINAL']:
                if col in df_deriv.columns:
                    valor_col = col
                    break
            
            if valor_col:
                total_deriv = df_deriv[valor_col].sum()
                print(f"  Derivativos: R$ {total_deriv/1e6:.1f}M em {len(df_deriv)} posições")
    
    # Gerar gráfico simples
    if resultados:
        periodos = sorted(resultados.keys())
        valores_acoes = []
        valores_deriv = []
        
        for periodo in periodos:
            valor_acao = 0
            valor_deriv = 0
            
            if 'BLC_4' in resultados[periodo]:
                df = resultados[periodo]['BLC_4']
                for col in ['VL_MERC_POS_FINAL', 'VL_MERCADO', 'VL_POS_FINAL']:
                    if col in df.columns:
                        valor_acao = df[col].sum()
                        break
            
            if 'BLC_5' in resultados[periodo]:
                df = resultados[periodo]['BLC_5']
                for col in ['VL_MERC_POS_FINAL', 'VL_MERCADO', 'VL_POS_FINAL']:
                    if col in df.columns:
                        valor_deriv = df[col].sum()
                        break
            
            valores_acoes.append(valor_acao/1e6)
            valores_deriv.append(valor_deriv/1e6)
        
        # Criar gráfico
        fig, ax = plt.subplots(figsize=(10, 6))
        
        x = np.arange(len(periodos))
        width = 0.35
        
        ax.bar(x - width/2, valores_acoes, width, label='Ações', color='green', alpha=0.8)
        ax.bar(x + width/2, valores_deriv, width, label='Derivativos', color='orange', alpha=0.8)
        
        ax.set_xlabel('Período')
        ax.set_ylabel('Valor (R$ milhões)')
        ax.set_title('Fundo Capstone - Evolução de Ações e Derivativos')
        ax.set_xticks(x)
        ax.set_xticklabels(periodos)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('capstone_rapido.png', dpi=150)
        plt.close()
        
        print("\nGráfico salvo em 'capstone_rapido.png'")
    
    # Gerar HTML mínimo
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Análise Rápida - Fundo Capstone</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            h1 {{ color: #2c3e50; }}
            .info {{ background: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            img {{ max-width: 100%; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Análise Rápida - Fundo Capstone</h1>
            <div class="info">
                <p><strong>CNPJ:</strong> 35.803.288/0001-17</p>
                <p><strong>Períodos Analisados:</strong> {len(resultados)} meses</p>
                <p><strong>Observação:</strong> Análise focada em ações e derivativos</p>
            </div>
            <h2>Gráfico de Evolução</h2>
            <img src="capstone_rapido.png" alt="Evolução">
        </div>
    </body>
    </html>
    """
    
    with open('capstone.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("HTML salvo em 'capstone.html'")
    print("\nAnálise concluída!")

if __name__ == "__main__":
    main()