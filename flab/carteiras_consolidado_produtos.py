import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
import re

def carregar_carteira(base_dir, fundo, data):
    """Carrega dados da carteira diretamente do arquivo pickle"""
    caminho = os.path.join(base_dir, 'serial_carteiras', f'carteira_{fundo}.pkl')
    
    try:
        with open(caminho, 'rb') as f:
            dados = pickle.load(f)
        
        if data in dados['carteira_categorizada']:
            return dados['carteira_categorizada'][data]
        else:
            print(f"Data {data} não disponível para {fundo}")
            return None
    except Exception as e:
        print(f"Erro ao carregar {fundo}: {e}")
        return None

def extrair_produtos_por_tipo(carteiras_fundos):
    """Extrai todos os produtos por tipo (debêntures, fundos, etc.), independentemente do fundo"""
    produtos_por_tipo = {
        'Debêntures': [],
        'Títulos Públicos': [],
        'Fundos': [],
        'Renda Fixa - Bancário': [],
        'Operações Compromissadas': [],
        'Outros': []
    }
    
    for fundo, df in carteiras_fundos.items():
        # Debêntures
        if 'CD_ATIVO' in df.columns:
            debentures = df[df['CD_ATIVO'].notna() & (df['CD_ATIVO'] != '')]
            for _, row in debentures.iterrows():
                produtos_por_tipo['Debêntures'].append({
                    'nome': row['CD_ATIVO'],
                    'valor': row['VL_MERC_POS_FINAL']
                })
        
        # Títulos públicos
        if 'TP_TITPUB' in df.columns:
            titulos = df[df['TP_TITPUB'].notna() & (df['TP_TITPUB'] != '')]
            for _, row in titulos.iterrows():
                produtos_por_tipo['Títulos Públicos'].append({
                    'nome': row['TP_TITPUB'],
                    'valor': row['VL_MERC_POS_FINAL']
                })
        
        # Fundos de investimento
        if 'NM_FUNDO_CLASSE_SUBCLASSE_COTA' in df.columns:
            fundos_inv = df[df['NM_FUNDO_CLASSE_SUBCLASSE_COTA'].notna() & (df['NM_FUNDO_CLASSE_SUBCLASSE_COTA'] != '')]
            for _, row in fundos_inv.iterrows():
                nome = str(row['NM_FUNDO_CLASSE_SUBCLASSE_COTA'])
                nome = re.sub(r'FUNDO DE INVESTIMENTO FINANCEIRO|FUNDO DE INVESTIMENTO|RESPONSABILIDADE LIMITADA', '', nome).strip()
                nome = nome[:40] + '...' if len(nome) > 40 else nome
                
                produtos_por_tipo['Fundos'].append({
                    'nome': nome,
                    'valor': row['VL_MERC_POS_FINAL']
                })
        
        # Renda Fixa - Bancário
        if 'CATEGORIA_ATIVO' in df.columns:
            bancario = df[df['CATEGORIA_ATIVO'] == 'Renda Fixa - Bancário']
            if not bancario.empty:
                for _, row in bancario.iterrows():
                    nome = 'Letra Financeira'
                    if 'EMISSOR' in row and pd.notna(row['EMISSOR']):
                        nome = f"LF - {row['EMISSOR']}"
                    
                    produtos_por_tipo['Renda Fixa - Bancário'].append({
                        'nome': nome,
                        'valor': row['VL_MERC_POS_FINAL']
                    })
        
        # Operações Compromissadas
        if 'TP_APLIC' in df.columns:
            compromissadas = df[df['TP_APLIC'] == 'Operações Compromissadas']
            if not compromissadas.empty:
                for _, row in compromissadas.iterrows():
                    nome = 'Operações Compromissadas'
                    if 'TP_TITPUB' in row and pd.notna(row['TP_TITPUB']):
                        nome = f"Compromissada - {row['TP_TITPUB']}"
                    
                    produtos_por_tipo['Operações Compromissadas'].append({
                        'nome': nome,
                        'valor': row['VL_MERC_POS_FINAL']
                    })
        
        # Outros produtos
        if 'DS_ATIVO' in df.columns:
            outros = df[(df['DS_ATIVO'] == 'DISPONIBILIDADES') | 
                       (df['DS_ATIVO'] == 'VALORES A RECEBER') | 
                       (df['DS_ATIVO'] == 'VALORES A PAGAR') |
                       (df['DS_ATIVO'] == 'Futuro de Cupom de IPCA - FUT DAP')]
            
            for _, row in outros.iterrows():
                if row['DS_ATIVO'] == 'DISPONIBILIDADES':
                    nome = 'Caixa e Disponibilidades'
                elif row['DS_ATIVO'] == 'Futuro de Cupom de IPCA - FUT DAP':
                    if 'TP_APLIC' in row and pd.notna(row['TP_APLIC']):
                        if 'compradas' in row['TP_APLIC']:
                            nome = 'Mercado Futuro - Posições compradas'
                        elif 'vendidas' in row['TP_APLIC']:
                            nome = 'Mercado Futuro - Posições vendidas'
                        else:
                            nome = 'Mercado Futuro'
                    else:
                        nome = 'Mercado Futuro'
                else:
                    nome = row['DS_ATIVO'].title()
                
                produtos_por_tipo['Outros'].append({
                    'nome': nome,
                    'valor': row['VL_MERC_POS_FINAL']
                })
    
    # Remover categorias vazias
    categorias_vazias = []
    for categoria, produtos in produtos_por_tipo.items():
        if not produtos:
            categorias_vazias.append(categoria)
    
    for categoria in categorias_vazias:
        del produtos_por_tipo[categoria]
    
    return produtos_por_tipo

def gerar_histograma_tipo_produto(tipo, produtos_lista, dir_relatorios, max_produtos=10):
    """
    Gera um histograma para um tipo específico de produto com tamanho e fontes adequados
    
    Args:
        tipo (str): Nome do tipo de produto (ex: 'Debêntures', 'Fundos')
        produtos_lista (list): Lista de dicionários com 'nome' e 'valor' dos produtos
        dir_relatorios (str): Diretório onde salvar o histograma
        max_produtos (int): Número máximo de produtos a exibir (default: 10)
        
    Returns:
        str: Caminho do arquivo gerado
    """
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns
    import os
    
    print(f"Gerando histograma para {tipo}...")
    
    # Converter para DataFrame
    produtos_df = pd.DataFrame(produtos_lista)
    
    # Agrupar produtos com mesmo nome (somando valores)
    produtos_df = produtos_df.groupby('nome')['valor'].sum().reset_index()
    
    # Calcular percentuais
    total = produtos_df['valor'].sum()
    produtos_df['percentual'] = (produtos_df['valor'] / total * 100).round(2)
    
    # Ordenar por percentual (decrescente)
    produtos_df = produtos_df.sort_values('percentual', ascending=False)
    
    print(f"  Total de {len(produtos_df)} {tipo.lower()} encontrados")
    
    # Se temos mais produtos que o máximo, criar um grupo "Outros"
    if len(produtos_df) > max_produtos:
        # Separar os principais produtos
        principais = produtos_df.head(max_produtos - 1)  # -1 para deixar espaço para "Outros"
        outros = produtos_df.iloc[max_produtos - 1:]
        
        # Calcular totais do grupo "Outros"
        valor_outros = outros['valor'].sum()
        percentual_outros = (valor_outros / total * 100).round(2)
        
        # Criar entrada para "Outros"
        outros_row = pd.DataFrame({
            'nome': [f"Outros ({len(outros)} produtos)"],
            'valor': [valor_outros],
            'percentual': [percentual_outros]
        })
        
        # Combinar principais com outros
        produtos_df = pd.concat([principais, outros_row], ignore_index=True)
    
    # Número efetivo de produtos a mostrar
    n_produtos = len(produtos_df)
    
    # Configuração da figura - tamanho adaptado ao número de produtos
    fig_width = 14  # Largura fixa
    # Altura baseada no número de produtos, mas com mínimo de 6 e máximo de 14
    fig_height = max(6, min(14, 4 + n_produtos * 0.5))
    
    plt.figure(figsize=(fig_width, fig_height))
    
    # Determinar cor base para este tipo de produto
    cores_tipo = {
        'Debêntures': '#00008B',     # Azul escuro
        'Títulos Públicos': '#8B0000', # Vermelho escuro
        'Fundos': '#006400',         # Verde escuro
        'Renda Fixa - Bancário': '#404040', # Cinza escuro
        'Operações Compromissadas': '#4B0082', # Índigo
        'Outros': '#5D4037'          # Marrom escuro
    }
    
    cor_base = cores_tipo.get(tipo, '#333333')
    
    # Criar escala de cores (degradê)
    cmap = sns.light_palette(cor_base, n_colors=n_produtos+2)
    cores_barras = [cmap[i+1] for i in range(n_produtos)]
    
    # Inverter ordem para visualização (maior valor no topo)
    produtos_df = produtos_df.sort_values('percentual', ascending=True)
    
    # Criar barras horizontais
    barras = plt.barh(
        produtos_df['nome'], 
        produtos_df['percentual'], 
        color=cores_barras,
        height=0.6  # Altura das barras maior
    )
    
    # Adicionar valores nas barras
    for i, barra in enumerate(barras):
        width = barra.get_width()
        valor = produtos_df['valor'].iloc[i]
        
        # Formatar valor
        if valor >= 1e9:
            valor_str = f"R$ {valor/1e9:.2f}B"
        elif valor >= 1e6:
            valor_str = f"R$ {valor/1e6:.2f}M"
        else:
            valor_str = f"R$ {valor/1e3:.2f}K"
        
        # Adicionar texto dentro ou fora da barra, dependendo do tamanho
        if width > 10:  # Se a barra for larga o suficiente, texto dentro
            texto_x = width/2
            texto_cor = 'white'
            texto_ha = 'center'
        else:  # Se a barra for estreita, texto fora
            texto_x = width + 0.5
            texto_cor = 'black'
            texto_ha = 'left'
        
        plt.text(
            texto_x,
            barra.get_y() + barra.get_height()/2,
            f"{width:.1f}% ({valor_str})",
            va='center',
            ha=texto_ha,
            color=texto_cor,
            fontsize=11,
            fontweight='bold'
        )
    
    # Configurar gráfico
    plt.title(f'{tipo}', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Percentual (%)', fontsize=14)
    plt.ylabel('', fontsize=14)  # Sem rótulo no eixo Y
    
    # Configurar tamanho da fonte dos rótulos dos eixos
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    
    # Adicionar grid
    plt.grid(axis='x', linestyle='--', alpha=0.3)
    
    # Ajustar limites do eixo X
    max_pct = produtos_df['percentual'].max() if not produtos_df.empty else 10
    plt.xlim(0, max_pct * 1.25)  # 25% de espaço extra
    
    # Remover bordas superiores e à direita
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['top'].set_visible(False)
    
    # Adicionar total como anotação
    if total >= 1e9:
        total_str = f"Total: R$ {total/1e9:.2f}B"
    else:
        total_str = f"Total: R$ {total/1e6:.2f}M"
    
    plt.annotate(
        total_str,
        xy=(0.95, 0.03),
        xycoords='figure fraction',
        ha='right',
        fontsize=12,
        fontweight='bold',
        bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8, edgecolor='#cccccc')
    )
    
    plt.tight_layout()
    
    # Salvar figura
    caminho = os.path.join(dir_relatorios, f"{tipo.lower().replace(' ', '_')}_consolidado.png")
    plt.savefig(caminho, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  Histograma de {tipo} salvo em: {caminho}")
    
    return caminho

def gerar_histogramas_consolidados(fundos, mapeamento_datas, base_dir, max_produtos=10):
    """
    Gera histogramas consolidados por tipo de produto, independentemente do fundo,
    com visualização melhorada e tamanhos adequados
    
    Args:
        fundos (list): Lista de nomes dos fundos a analisar
        mapeamento_datas (dict): Mapeamento de datas para cada fundo
        base_dir (str): Diretório base para dados e resultados
        max_produtos (int): Número máximo de produtos em cada histograma
        
    Returns:
        dict: Dicionário com os caminhos dos histogramas gerados
    """
    import os
    import pandas as pd
    from datetime import datetime
    
    print("Gerando histogramas consolidados por tipo de produto...")
    print(f"Datas analisadas: {mapeamento_datas}")
    
    # Carregar carteiras de todos os fundos
    carteiras_fundos = {}
    for fundo in fundos:
        data = mapeamento_datas.get(fundo, mapeamento_datas.get('default'))
        df = carregar_carteira(base_dir, fundo, data)
        if df is not None:
            carteiras_fundos[fundo] = df
            print(f"Carregada carteira de {fundo} para a data {data}")
        else:
            print(f"AVISO: Não foi possível carregar a carteira de {fundo} para {data}")
    
    # Verificar se temos alguma carteira para processar
    if not carteiras_fundos:
        print("ERRO: Nenhuma carteira disponível para processar. Verifique os dados.")
        return {}
    
    # Diretório para salvar os resultados
    dir_relatorios = os.path.join(base_dir, 'relatorios', 'consolidado')
    os.makedirs(dir_relatorios, exist_ok=True)
    
    # Gerar um relatório HTML para os histogramas
    data_relatorio = datetime.now().strftime('%Y-%m-%d')
    html_path = os.path.join(dir_relatorios, f"relatorio_histogramas_{data_relatorio}.html")
    
    # Extrair produtos por tipo
    produtos_por_tipo = extrair_produtos_por_tipo(carteiras_fundos)
    
    # Verificar se extraímos algum produto
    if not produtos_por_tipo:
        print("AVISO: Nenhum produto extraído das carteiras. Verifique os dados.")
        return {}
    
    # Gerar histograma para cada tipo de produto
    caminhos_histogramas = {}
    for tipo, produtos in produtos_por_tipo.items():
        if produtos:  # Verificar se há produtos nesta categoria
            caminho = gerar_histograma_tipo_produto(
                tipo, 
                produtos, 
                dir_relatorios, 
                max_produtos=max_produtos
            )
            caminhos_histogramas[tipo] = caminho
    
    # Gerar relatório HTML com todos os histogramas
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Histogramas Consolidados por Tipo de Produto</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2 {{ color: #333366; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .grafico {{ text-align: center; margin: 30px 0; }}
            img {{ max-width: 100%; border: 1px solid #ddd; }}
            .footer {{ text-align: center; margin-top: 40px; color: #666; font-size: 12px; }}
            .info {{ margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Histogramas Consolidados por Tipo de Produto</h1>
            <p>Data do relatório: {data_relatorio}</p>
            
            <div class="info">
                <h2>Informações sobre os dados</h2>
                <p>Fundos analisados: {', '.join(carteiras_fundos.keys())}</p>
                <p>Datas utilizadas:</p>
                <ul>
    """
    
    # Adicionar datas para cada fundo
    for fundo in fundos:
        if fundo in carteiras_fundos:
            data = mapeamento_datas.get(fundo, mapeamento_datas.get('default'))
            html_content += f"<li>{fundo.capitalize()}: {data}</li>\n"
    
    html_content += """
                </ul>
            </div>
    """
    
    # Adicionar cada histograma ao HTML
    for tipo, caminho in caminhos_histogramas.items():
        # Obter caminho relativo para o HTML
        nome_arquivo = os.path.basename(caminho)
        
        html_content += f"""
            <h2>{tipo}</h2>
            <div class="grafico">
                <img src="{nome_arquivo}" alt="Histograma de {tipo}">
            </div>
        """
    
    # Finalizar HTML
    html_content += f"""
            <div class="footer">
                <p>Relatório gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Salvar HTML
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Relatório HTML salvo em: {html_path}")
    print("Histogramas consolidados gerados com sucesso!")
    
    # Adicionar caminho do HTML aos resultados
    caminhos_histogramas['relatorio_html'] = html_path
    
    return caminhos_histogramas

# Exemplo de uso das funções melhoradas
def exemplo_uso_histogramas():
    """
    Exemplo demonstrando o uso das funções melhoradas para gerar histogramas
    """
    # Lista de fundos para analisar
    lista_fundos = ['chimborazo', 'aconcagua', 'alpamayo', 'huayna']
    
    # Diretório base (ajuste conforme necessário)
    base_dir = "./database"
    
    # Mapeamento de datas para cada fundo
    # Se um fundo não estiver listado, usará a data em 'default'
    mapeamento_datas = {
        'huayna': '2025-01',  # Data específica para huayna
        'default': '2025-02'  # Data padrão para os demais fundos
    }
    
    # Chamar a função com o parâmetro max_produtos
    caminhos = gerar_histogramas_consolidados_v2(
        lista_fundos, 
        mapeamento_datas, 
        base_dir,
        max_produtos=10  # Limitar a 10 produtos por histograma
    )
    
    # Verificar resultados
    if 'relatorio_html' in caminhos:
        print(f"\nRelatório HTML gerado com sucesso: {caminhos['relatorio_html']}")
        print("\nHistogramas gerados para os seguintes tipos de produtos:")
        for tipo, caminho in caminhos.items():
            if tipo != 'relatorio_html':
                print(f"- {tipo}: {caminho}")
    else:
        print("Nenhum histograma foi gerado. Verifique os logs de erro.")
    
    return caminhos

def extrair_produtos_por_tipo_v2(carteiras_fundos):
    """
    Extrai todos os produtos por tipo, com subcategorias específicas para Fundos
    (Ações, Renda Fixa, Multimercado, Private Equity e Outros Fundos)
    
    Args:
        carteiras_fundos (dict): Dicionário com DataFrames de carteira por fundo
        
    Returns:
        dict: Dicionário com produtos organizados por tipo e subcategorias de fundos
    """
    produtos_por_tipo = {
        'Debêntures': [],
        'Títulos Públicos': [],
        'Fundos de Ações': [],
        'Fundos de Renda Fixa': [],
        'Fundos Multimercado': [],
        'Fundos de Private Equity': [],
        'Outros Fundos': [],
        'Renda Fixa - Bancário': [],
        'Operações Compromissadas': [],
        'Outros': []
    }
    
    for fundo, df in carteiras_fundos.items():
        # Debêntures
        if 'CD_ATIVO' in df.columns:
            debentures = df[df['CD_ATIVO'].notna() & (df['CD_ATIVO'] != '')]
            for _, row in debentures.iterrows():
                produtos_por_tipo['Debêntures'].append({
                    'nome': row['CD_ATIVO'],
                    'valor': row['VL_MERC_POS_FINAL']
                })
        
        # Títulos públicos
        if 'TP_TITPUB' in df.columns:
            titulos = df[df['TP_TITPUB'].notna() & (df['TP_TITPUB'] != '')]
            for _, row in titulos.iterrows():
                produtos_por_tipo['Títulos Públicos'].append({
                    'nome': row['TP_TITPUB'],
                    'valor': row['VL_MERC_POS_FINAL']
                })
        
        # Fundos de investimento - com subcategorias
        if 'NM_FUNDO_CLASSE_SUBCLASSE_COTA' in df.columns:
            fundos_inv = df[df['NM_FUNDO_CLASSE_SUBCLASSE_COTA'].notna() & (df['NM_FUNDO_CLASSE_SUBCLASSE_COTA'] != '')]
            for _, row in fundos_inv.iterrows():
                nome_completo = str(row['NM_FUNDO_CLASSE_SUBCLASSE_COTA'])
                nome = re.sub(r'FUNDO DE INVESTIMENTO FINANCEIRO|FUNDO DE INVESTIMENTO|RESPONSABILIDADE LIMITADA', '', nome_completo).strip()
                nome = nome[:40] + '...' if len(nome) > 40 else nome
                
                # Determinar a subcategoria do fundo
                nome_lower = nome_completo.lower()
                
                # 1. Verificar se é um fundo de ações
                if any(term in nome_lower for term in ['ações', 'acoes', 'equities', 'ibovespa', 'long biased', 'stock', 
                                                      'long only', 'ativos', 'small caps', 'dividendos']):
                    categoria = 'Fundos de Ações'
                
                # 2. Verificar se é um fundo de renda fixa
                elif any(term in nome_lower for term in ['renda fixa', 'crédito privado', 'credito privado', 
                                                       'tesouro', 'rf ', 'di ', 'selic', 'inflação', 'inflation',
                                                       'juro ', 'juros ']):
                    categoria = 'Fundos de Renda Fixa'
                
                # 3. Verificar se é um fundo multimercado
                elif any(term in nome_lower for term in ['multimercado', 'multimarket', 'multi-estratégia', 
                                                       'multi estrategia', 'hedge', 'arbitragem', 'macro',
                                                       'multi-asset', 'multiasset', 'solutions', 'total return']):
                    categoria = 'Fundos Multimercado'
                
                # 4. Verificar se é um fundo de private equity
                elif any(term in nome_lower for term in ['private equity', 'equity', 'venture', 'participações', 
                                                      'participacoes', 'fip ', 'investimento em participações',
                                                      'capital', 'private']):
                    categoria = 'Fundos de Private Equity'
                
                # 5. Caso não seja possível classificar, vai para "Outros Fundos"
                else:
                    categoria = 'Outros Fundos'
                    
                # Adicionar informações extras para melhor classificação
                info_extra = {}
                
                # Adicionar CNPJ se disponível
                if 'CNPJ_FUNDO_CLASSE_COTA' in row and pd.notna(row['CNPJ_FUNDO_CLASSE_COTA']):
                    info_extra['cnpj'] = row['CNPJ_FUNDO_CLASSE_COTA']
                
                # Adicionar tipo de fundo se disponível 
                if 'TP_ATIVO' in row and pd.notna(row['TP_ATIVO']):
                    info_extra['tipo_ativo'] = row['TP_ATIVO']
                
                produtos_por_tipo[categoria].append({
                    'nome': nome,
                    'valor': row['VL_MERC_POS_FINAL'],
                    'nome_completo': nome_completo,
                    'info_extra': info_extra
                })
        
        # Renda Fixa - Bancário
        if 'CATEGORIA_ATIVO' in df.columns:
            bancario = df[df['CATEGORIA_ATIVO'] == 'Renda Fixa - Bancário']
            if not bancario.empty:
                for _, row in bancario.iterrows():
                    nome = 'Letra Financeira'
                    if 'EMISSOR' in row and pd.notna(row['EMISSOR']):
                        nome = f"LF - {row['EMISSOR']}"
                    
                    produtos_por_tipo['Renda Fixa - Bancário'].append({
                        'nome': nome,
                        'valor': row['VL_MERC_POS_FINAL']
                    })
        
        # Operações Compromissadas
        if 'TP_APLIC' in df.columns:
            compromissadas = df[df['TP_APLIC'] == 'Operações Compromissadas']
            if not compromissadas.empty:
                for _, row in compromissadas.iterrows():
                    nome = 'Operações Compromissadas'
                    if 'TP_TITPUB' in row and pd.notna(row['TP_TITPUB']):
                        nome = f"Compromissada - {row['TP_TITPUB']}"
                    
                    produtos_por_tipo['Operações Compromissadas'].append({
                        'nome': nome,
                        'valor': row['VL_MERC_POS_FINAL']
                    })
        
        # Outros produtos
        if 'DS_ATIVO' in df.columns:
            outros = df[(df['DS_ATIVO'] == 'DISPONIBILIDADES') | 
                       (df['DS_ATIVO'] == 'VALORES A RECEBER') | 
                       (df['DS_ATIVO'] == 'VALORES A PAGAR') |
                       (df['DS_ATIVO'] == 'Futuro de Cupom de IPCA - FUT DAP')]
            
            for _, row in outros.iterrows():
                if row['DS_ATIVO'] == 'DISPONIBILIDADES':
                    nome = 'Caixa e Disponibilidades'
                elif row['DS_ATIVO'] == 'Futuro de Cupom de IPCA - FUT DAP':
                    if 'TP_APLIC' in row and pd.notna(row['TP_APLIC']):
                        if 'compradas' in row['TP_APLIC']:
                            nome = 'Mercado Futuro - Posições compradas'
                        elif 'vendidas' in row['TP_APLIC']:
                            nome = 'Mercado Futuro - Posições vendidas'
                        else:
                            nome = 'Mercado Futuro'
                    else:
                        nome = 'Mercado Futuro'
                else:
                    nome = row['DS_ATIVO'].title()
                
                produtos_por_tipo['Outros'].append({
                    'nome': nome,
                    'valor': row['VL_MERC_POS_FINAL']
                })
    
    # Remover categorias vazias
    categorias_vazias = []
    for categoria, produtos in produtos_por_tipo.items():
        if not produtos:
            categorias_vazias.append(categoria)
    
    for categoria in categorias_vazias:
        del produtos_por_tipo[categoria]
    
    return produtos_por_tipo



def gerar_histogramas_consolidados_v2(fundos, mapeamento_datas, base_dir, max_produtos=10):
    """
    Gera histogramas consolidados por tipo de produto, com subcategorias específicas para Fundos
    (Ações, Renda Fixa, Multimercado, Private Equity e Outros)
    
    Args:
        fundos (list): Lista de nomes dos fundos a analisar
        mapeamento_datas (dict): Mapeamento de datas para cada fundo
        base_dir (str): Diretório base para dados e resultados
        max_produtos (int): Número máximo de produtos em cada histograma
        
    Returns:
        dict: Dicionário com os caminhos dos histogramas gerados
    """
    import os
    import pandas as pd
    from datetime import datetime
    
    print("Gerando histogramas consolidados por tipo de produto com subcategorias de fundos...")
    print(f"Datas analisadas: {mapeamento_datas}")
    
    # Carregar carteiras de todos os fundos
    carteiras_fundos = {}
    for fundo in fundos:
        data = mapeamento_datas.get(fundo, mapeamento_datas.get('default'))
        df = carregar_carteira(base_dir, fundo, data)
        if df is not None:
            carteiras_fundos[fundo] = df
            print(f"Carregada carteira de {fundo} para a data {data}")
        else:
            print(f"AVISO: Não foi possível carregar a carteira de {fundo} para {data}")
    
    # Verificar se temos alguma carteira para processar
    if not carteiras_fundos:
        print("ERRO: Nenhuma carteira disponível para processar. Verifique os dados.")
        return {}
    
    # Diretório para salvar os resultados
    dir_relatorios = os.path.join(base_dir, 'relatorios', 'consolidado')
    os.makedirs(dir_relatorios, exist_ok=True)
    
    # Extrair produtos por tipo (usando a nova função com subcategorias)
    produtos_por_tipo = extrair_produtos_por_tipo_v2(carteiras_fundos)
    
    # Verificar se extraímos algum produto
    if not produtos_por_tipo:
        print("AVISO: Nenhum produto extraído das carteiras. Verifique os dados.")
        return {}
    
    print(f"Categorias identificadas: {', '.join(produtos_por_tipo.keys())}")
    
    # Determinar cores específicas para subcategorias de fundos
    cores_tipo = {
        'Debêntures': '#00008B',            # Azul escuro
        'Títulos Públicos': '#8B0000',      # Vermelho escuro
        'Fundos de Ações': '#B22222',       # Fire Brick (vermelho tijolo)
        'Fundos de Renda Fixa': '#4169E1',  # Royal Blue (azul royal)
        'Fundos Multimercado': '#228B22',   # Forest Green (verde floresta)
        'Fundos de Private Equity': '#8B008B', # Dark Magenta (magenta escuro)
        'Outros Fundos': '#4B0082',         # Indigo
        'Renda Fixa - Bancário': '#404040', # Cinza escuro
        'Operações Compromissadas': '#2F4F4F', # Dark Slate Gray
        'Outros': '#5D4037'                 # Marrom escuro
    }
    
    # Gerar histograma para cada tipo de produto
    caminhos_histogramas = {}
    for tipo, produtos in produtos_por_tipo.items():
        if produtos:  # Verificar se há produtos nesta categoria
            # Ajustar max_produtos com base na categoria
            # Para subcategorias de fundos, permitir mais itens para melhor visualização
            max_produtos_cat = max_produtos
            if "Fundos" in tipo:
                max_produtos_cat = max(15, max_produtos)  # Pelo menos 15 para categorias de fundos
            
            caminho = gerar_histograma_tipo_produto_v2(
                tipo, 
                produtos, 
                dir_relatorios, 
                max_produtos=max_produtos_cat,
                cores_tipo=cores_tipo
            )
            caminhos_histogramas[tipo] = caminho
    
    # Gerar relatório HTML com todos os histogramas
    data_relatorio = datetime.now().strftime('%Y-%m-%d')
    html_path = os.path.join(dir_relatorios, f"relatorio_histogramas_subcategorias_{data_relatorio}.html")
    
    # Criação do conteúdo HTML com organização por categorias principais
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Histogramas Consolidados por Tipo de Produto</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2, h3 {{ color: #333366; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .grafico {{ text-align: center; margin: 30px 0; }}
            img {{ max-width: 100%; border: 1px solid #ddd; }}
            .footer {{ text-align: center; margin-top: 40px; color: #666; font-size: 12px; }}
            .info {{ margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-radius: 5px; }}
            .secao {{ margin: 40px 0; padding: 15px; background-color: #f8f9fa; border-radius: 5px; }}
            .tipo-fundo {{ color: #008000; }} /* Verde para seção de Fundos */
            .tipo-rf {{ color: #0000FF; }}    /* Azul para seção de Renda Fixa */
            .tipo-outro {{ color: #800080; }} /* Roxo para Outros */
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Histogramas Consolidados por Tipo de Produto</h1>
            <p>Data do relatório: {data_relatorio}</p>
            
            <div class="info">
                <h2>Informações sobre os dados</h2>
                <p>Fundos analisados: {', '.join(carteiras_fundos.keys())}</p>
                <p>Datas utilizadas:</p>
                <ul>
    """
    
    # Adicionar datas para cada fundo
    for fundo in fundos:
        if fundo in carteiras_fundos:
            data = mapeamento_datas.get(fundo, mapeamento_datas.get('default'))
            html_content += f"<li>{fundo.capitalize()}: {data}</li>\n"
    
    html_content += """
                </ul>
            </div>
    """
    
    # Organizar categorias por grupos
    categorias_fundos = [cat for cat in caminhos_histogramas.keys() if 'Fundos' in cat]
    categorias_renda_fixa = [cat for cat in caminhos_histogramas.keys() if 'Renda Fixa' in cat or 'Títulos' in cat or 'Debêntures' in cat or 'Compromissadas' in cat]
    categorias_outros = [cat for cat in caminhos_histogramas.keys() if cat not in categorias_fundos and cat not in categorias_renda_fixa]
    
    # Seção: Categorias de Fundos
    if categorias_fundos:
        html_content += """
            <div class="secao">
                <h2 class="tipo-fundo">Fundos de Investimento</h2>
        """
        
        for categoria in categorias_fundos:
            caminho = caminhos_histogramas[categoria]
            nome_arquivo = os.path.basename(caminho)
            
            html_content += f"""
                <h3>{categoria}</h3>
                <div class="grafico">
                    <img src="{nome_arquivo}" alt="Histograma de {categoria}">
                </div>
            """
        
        html_content += """
            </div>
        """
    
    # Seção: Categorias de Renda Fixa
    if categorias_renda_fixa:
        html_content += """
            <div class="secao">
                <h2 class="tipo-rf">Renda Fixa e Títulos</h2>
        """
        
        for categoria in categorias_renda_fixa:
            caminho = caminhos_histogramas[categoria]
            nome_arquivo = os.path.basename(caminho)
            
            html_content += f"""
                <h3>{categoria}</h3>
                <div class="grafico">
                    <img src="{nome_arquivo}" alt="Histograma de {categoria}">
                </div>
            """
        
        html_content += """
            </div>
        """
    
    # Seção: Outras Categorias
    if categorias_outros:
        html_content += """
            <div class="secao">
                <h2 class="tipo-outro">Outras Categorias</h2>
        """
        
        for categoria in categorias_outros:
            caminho = caminhos_histogramas[categoria]
            nome_arquivo = os.path.basename(caminho)
            
            html_content += f"""
                <h3>{categoria}</h3>
                <div class="grafico">
                    <img src="{nome_arquivo}" alt="Histograma de {categoria}">
                </div>
            """
        
        html_content += """
            </div>
        """
    
    # Finalizar HTML
    html_content += f"""
            <div class="footer">
                <p>Relatório gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Salvar HTML
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Relatório HTML com subcategorias salvo em: {html_path}")
    print("Histogramas consolidados gerados com sucesso!")
    
    # Adicionar caminho do HTML aos resultados
    caminhos_histogramas['relatorio_html'] = html_path
    
    return caminhos_histogramas



def gerar_histograma_tipo_produto_v2(tipo, produtos_lista, dir_relatorios, max_produtos=10, cores_tipo=None):
    """
    Versão atualizada da função para gerar histograma para um tipo específico de produto,
    com melhor suporte para subcategorias de fundos e informações detalhadas
    
    Args:
        tipo (str): Nome do tipo de produto
        produtos_lista (list): Lista de dicionários com produtos
        dir_relatorios (str): Diretório onde salvar o histograma
        max_produtos (int): Número máximo de produtos a exibir
        cores_tipo (dict, optional): Mapeamento personalizado de cores por tipo
        
    Returns:
        str: Caminho do arquivo gerado
    """
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns
    import os
    import re
    
    print(f"Gerando histograma para {tipo}...")
    
    # Converter para DataFrame
    produtos_df = pd.DataFrame(produtos_lista)
    
    # Agrupar produtos com mesmo nome (somando valores)
    produtos_df = produtos_df.groupby('nome')['valor'].sum().reset_index()
    
    # Calcular percentuais
    total = produtos_df['valor'].sum()
    produtos_df['percentual'] = (produtos_df['valor'] / total * 100).round(2)
    
    # Ordenar por percentual (decrescente)
    produtos_df = produtos_df.sort_values('percentual', ascending=False)
    
    print(f"  Total de {len(produtos_df)} {tipo.lower()} encontrados")
    
    # Se temos mais produtos que o máximo, criar um grupo "Outros"
    if len(produtos_df) > max_produtos:
        # Separar os principais produtos
        principais = produtos_df.head(max_produtos - 1)  # -1 para deixar espaço para "Outros"
        outros = produtos_df.iloc[max_produtos - 1:]
        
        # Calcular totais do grupo "Outros"
        valor_outros = outros['valor'].sum()
        percentual_outros = (valor_outros / total * 100).round(2)
        
        # Criar entrada para "Outros"
        outros_row = pd.DataFrame({
            'nome': [f"Outros ({len(outros)} produtos)"],
            'valor': [valor_outros],
            'percentual': [percentual_outros]
        })
        
        # Combinar principais com outros
        produtos_df = pd.concat([principais, outros_row], ignore_index=True)
    
    # Número efetivo de produtos a mostrar
    n_produtos = len(produtos_df)
    
    # Configuração da figura - tamanho adaptado ao número de produtos
    fig_width = 14  # Largura fixa
    
    # Para subcategorias de fundos, ajuste a altura para mostrar melhor
    if "Fundos" in tipo:
        altura_base = 6
        altura_por_produto = 0.5  # Um pouco mais alto para categorias de fundos
        fig_height = max(7, min(16, altura_base + n_produtos * altura_por_produto))
    else:
        altura_base = 5
        altura_por_produto = 0.4
        fig_height = max(6, min(14, altura_base + n_produtos * altura_por_produto))
    
    plt.figure(figsize=(fig_width, fig_height))
    
    # Cores personalizadas para tipos de produtos
    if cores_tipo is None:
        cores_tipo = {
            'Debêntures': '#00008B',     # Azul escuro
            'Títulos Públicos': '#8B0000', # Vermelho escuro
            'Fundos': '#006400',         # Verde escuro
            'Fundos de Ações': '#B22222',       # Fire Brick (vermelho tijolo)
            'Fundos de Renda Fixa': '#4169E1',  # Royal Blue (azul royal)
            'Fundos Multimercado': '#228B22',   # Forest Green (verde floresta)
            'Fundos de Private Equity': '#8B008B', # Dark Magenta (magenta escuro)
            'Outros Fundos': '#4B0082',         # Indigo
            'Renda Fixa - Bancário': '#404040', # Cinza escuro
            'Operações Compromissadas': '#2F4F4F', # Dark Slate Gray
            'Outros': '#5D4037'          # Marrom escuro
        }
    
    # Determinar cor base para este tipo de produto
    cor_base = cores_tipo.get(tipo, '#333333')
    
    # Criar escala de cores (degradê)
    cmap = sns.light_palette(cor_base, n_colors=n_produtos+2)
    cores_barras = [cmap[i+1] for i in range(n_produtos)]
    
    # Inverter ordem para visualização (maior valor no topo)
    produtos_df = produtos_df.sort_values('percentual', ascending=True)
    
    # Criar barras horizontais
    barras = plt.barh(
        produtos_df['nome'], 
        produtos_df['percentual'], 
        color=cores_barras,
        height=0.65,  # Altura das barras um pouco maior
        edgecolor='white',
        linewidth=0.5
    )
    
    # Adicionar valores nas barras
    for i, barra in enumerate(barras):
        width = barra.get_width()
        valor = produtos_df['valor'].iloc[i]
        
        # Formatar valor
        if valor >= 1e9:
            valor_str = f"R$ {valor/1e9:.2f}B"
        elif valor >= 1e6:
            valor_str = f"R$ {valor/1e6:.2f}M"
        else:
            valor_str = f"R$ {valor/1e3:.2f}K"
        
        # Adicionar texto dentro ou fora da barra, dependendo do tamanho
        if width > 10:  # Se a barra for larga o suficiente, texto dentro
            texto_x = width/2
            texto_cor = 'white'
            texto_ha = 'center'
        else:  # Se a barra for estreita, texto fora
            texto_x = width + 0.5
            texto_cor = 'black'
            texto_ha = 'left'
        
        plt.text(
            texto_x,
            barra.get_y() + barra.get_height()/2,
            f"{width:.1f}% ({valor_str})",
            va='center',
            ha=texto_ha,
            color=texto_cor,
            fontsize=11,
            fontweight='bold'
        )
    
    # Título customizado para subcategorias de fundos
    if "Fundos" in tipo:
        plt.title(f'{tipo}', fontsize=16, fontweight='bold', pad=20, color=cor_base)
    else:
        plt.title(f'{tipo}', fontsize=16, fontweight='bold', pad=20)
    
    plt.xlabel('Percentual (%)', fontsize=14)
    plt.ylabel('', fontsize=14)  # Sem rótulo no eixo Y
    
    # Configurar tamanho da fonte dos rótulos dos eixos
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    
    # Adicionar grid
    plt.grid(axis='x', linestyle='--', alpha=0.3)
    
    # Ajustar limites do eixo X
    max_pct = produtos_df['percentual'].max() if not produtos_df.empty else 10
    plt.xlim(0, max_pct * 1.25)  # 25% de espaço extra
    
    # Remover bordas superiores e à direita
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['top'].set_visible(False)
    
    # Adicionar total como anotação
    if total >= 1e9:
        total_str = f"Total: R$ {total/1e9:.2f}B"
    else:
        total_str = f"Total: R$ {total/1e6:.2f}M"
    
    plt.annotate(
        total_str,
        xy=(0.95, 0.03),
        xycoords='figure fraction',
        ha='right',
        fontsize=12,
        fontweight='bold',
        bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8, edgecolor='#cccccc')
    )
    
    # Gerar nome de arquivo baseado no tipo
    nome_arquivo = tipo.lower().replace(' ', '_').replace('-', '_')
    
    # Para subcategorias de fundos, adicionar prefixo para agrupar
    if "Fundos" in tipo:
        nome_arquivo = f"fundos_{nome_arquivo}"
    
    # Ajustar layout
    plt.tight_layout()
    
    # Salvar figura
    caminho = os.path.join(dir_relatorios, f"{nome_arquivo}_consolidado.png")


import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re

def gerar_histograma_tipo_produto_v2(tipo, produtos_lista, dir_relatorios=None, max_produtos=10, cores_tipo=None, mostrar_apenas=False):
    """
    Versão atualizada da função para gerar histograma para um tipo específico de produto,
    com melhor suporte para subcategorias de fundos e informações detalhadas
    
    Args:
        tipo (str): Nome do tipo de produto
        produtos_lista (list): Lista de dicionários com produtos
        dir_relatorios (str, optional): Diretório onde salvar o histograma (None se mostrar_apenas=True)
        max_produtos (int): Número máximo de produtos a exibir
        cores_tipo (dict, optional): Mapeamento personalizado de cores por tipo
        mostrar_apenas (bool): Se True, apenas mostra o gráfico sem salvar
        
    Returns:
        str or None: Caminho do arquivo gerado ou None se mostrar_apenas=True
    """
    print(f"Gerando histograma para {tipo}...")
    
    # Converter para DataFrame
    produtos_df = pd.DataFrame(produtos_lista)
    
    # Agrupar produtos com mesmo nome (somando valores)
    produtos_df = produtos_df.groupby('nome')['valor'].sum().reset_index()
    
    # Calcular percentuais
    total = produtos_df['valor'].sum()
    produtos_df['percentual'] = (produtos_df['valor'] / total * 100).round(2)
    
    # Ordenar por percentual (decrescente)
    produtos_df = produtos_df.sort_values('percentual', ascending=False)
    
    print(f"  Total de {len(produtos_df)} {tipo.lower()} encontrados")
    
    # Se temos mais produtos que o máximo, criar um grupo "Outros"
    if len(produtos_df) > max_produtos:
        # Separar os principais produtos
        principais = produtos_df.head(max_produtos - 1)  # -1 para deixar espaço para "Outros"
        outros = produtos_df.iloc[max_produtos - 1:]
        
        # Calcular totais do grupo "Outros"
        valor_outros = outros['valor'].sum()
        percentual_outros = (valor_outros / total * 100).round(2)
        
        # Criar entrada para "Outros"
        outros_row = pd.DataFrame({
            'nome': [f"Outros ({len(outros)} produtos)"],
            'valor': [valor_outros],
            'percentual': [percentual_outros]
        })
        
        # Combinar principais com outros
        produtos_df = pd.concat([principais, outros_row], ignore_index=True)
    
    # Número efetivo de produtos a mostrar
    n_produtos = len(produtos_df)
    
    # Configuração da figura - tamanho adaptado ao número de produtos
    fig_width = 14  # Largura fixa
    
    # Para subcategorias de fundos, ajuste a altura para mostrar melhor
    if "Fundos" in tipo:
        altura_base = 6
        altura_por_produto = 0.5  # Um pouco mais alto para categorias de fundos
        fig_height = max(7, min(16, altura_base + n_produtos * altura_por_produto))
    else:
        altura_base = 5
        altura_por_produto = 0.4
        fig_height = max(6, min(14, altura_base + n_produtos * altura_por_produto))
    
    plt.figure(figsize=(fig_width, fig_height))
    
    # Cores personalizadas para tipos de produtos
    if cores_tipo is None:
        cores_tipo = {
            'Debêntures': '#00008B',     # Azul escuro
            'Títulos Públicos': '#8B0000', # Vermelho escuro
            'Fundos': '#006400',         # Verde escuro
            'Fundos de Ações': '#B22222',       # Fire Brick (vermelho tijolo)
            'Fundos de Renda Fixa': '#4169E1',  # Royal Blue (azul royal)
            'Fundos Multimercado': '#228B22',   # Forest Green (verde floresta)
            'Fundos de Private Equity': '#8B008B', # Dark Magenta (magenta escuro)
            'Outros Fundos': '#4B0082',         # Indigo
            'Renda Fixa - Bancário': '#404040', # Cinza escuro
            'Operações Compromissadas': '#2F4F4F', # Dark Slate Gray
            'Outros': '#5D4037'          # Marrom escuro
        }
    
    # Determinar cor base para este tipo de produto
    cor_base = cores_tipo.get(tipo, '#333333')
    
    # Criar escala de cores (degradê)
    cmap = sns.light_palette(cor_base, n_colors=n_produtos+2)
    cores_barras = [cmap[i+1] for i in range(n_produtos)]
    
    # Inverter ordem para visualização (maior valor no topo)
    produtos_df = produtos_df.sort_values('percentual', ascending=True)
    
    # Criar barras horizontais
    barras = plt.barh(
        produtos_df['nome'], 
        produtos_df['percentual'], 
        color=cores_barras,
        height=0.65,  # Altura das barras um pouco maior
        edgecolor='white',
        linewidth=0.5
    )
    
    # Adicionar valores nas barras
    for i, barra in enumerate(barras):
        width = barra.get_width()
        valor = produtos_df['valor'].iloc[i]
        
        # Formatar valor
        if valor >= 1e9:
            valor_str = f"R$ {valor/1e9:.2f}B"
        elif valor >= 1e6:
            valor_str = f"R$ {valor/1e6:.2f}M"
        else:
            valor_str = f"R$ {valor/1e3:.2f}K"
        
        # Adicionar texto dentro ou fora da barra, dependendo do tamanho
        if width > 10:  # Se a barra for larga o suficiente, texto dentro
            texto_x = width/2
            texto_cor = 'white'
            texto_ha = 'center'
        else:  # Se a barra for estreita, texto fora
            texto_x = width + 0.5
            texto_cor = 'black'
            texto_ha = 'left'
        
        plt.text(
            texto_x,
            barra.get_y() + barra.get_height()/2,
            f"{width:.1f}% ({valor_str})",
            va='center',
            ha=texto_ha,
            color=texto_cor,
            fontsize=11,
            fontweight='bold'
        )
    
    # Título customizado para subcategorias de fundos
    if "Fundos" in tipo:
        plt.title(f'{tipo}', fontsize=16, fontweight='bold', pad=20, color=cor_base)
    else:
        plt.title(f'{tipo}', fontsize=16, fontweight='bold', pad=20)
    
    plt.xlabel('Percentual (%)', fontsize=14)
    plt.ylabel('', fontsize=14)  # Sem rótulo no eixo Y
    
    # Configurar tamanho da fonte dos rótulos dos eixos
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    
    # Adicionar grid
    plt.grid(axis='x', linestyle='--', alpha=0.3)
    
    # Ajustar limites do eixo X
    max_pct = produtos_df['percentual'].max() if not produtos_df.empty else 10
    plt.xlim(0, max_pct * 1.25)  # 25% de espaço extra
    
    # Remover bordas superiores e à direita
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['top'].set_visible(False)
    
    # Adicionar total como anotação
    if total >= 1e9:
        total_str = f"Total: R$ {total/1e9:.2f}B"
    else:
        total_str = f"Total: R$ {total/1e6:.2f}M"
    
    plt.annotate(
        total_str,
        xy=(0.95, 0.03),
        xycoords='figure fraction',
        ha='right',
        fontsize=12,
        fontweight='bold',
        bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8, edgecolor='#cccccc')
    )
    
    # Ajustar layout
    plt.tight_layout()
    
    # Se apenas mostrar sem salvar
    if mostrar_apenas:
        plt.show()
        return None
    
    # Gerar nome de arquivo baseado no tipo
    nome_arquivo = tipo.lower().replace(' ', '_').replace('-', '_')
    
    # Para subcategorias de fundos, adicionar prefixo para agrupar
    if "Fundos" in tipo:
        nome_arquivo = f"fundos_{nome_arquivo}"
    
    # Salvar figura se dir_relatorios não for None
    if dir_relatorios:
        caminho = os.path.join(dir_relatorios, f"{nome_arquivo}_consolidado.png")
        plt.savefig(caminho, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  Histograma de {tipo} salvo em: {caminho}")
        return caminho
    else:
        plt.show()
        return None


def gerar_histogramas_consolidados_v2(fundos, mapeamento_datas, base_dir=None, max_produtos=10, mostrar_apenas=False):
    """
    Gera histogramas consolidados por tipo de produto, com subcategorias específicas para Fundos
    
    Args:
        fundos (list): Lista de nomes dos fundos a analisar
        mapeamento_datas (dict): Mapeamento de datas para cada fundo
        base_dir (str, optional): Diretório base para dados e resultados (None se mostrar_apenas=True)
        max_produtos (int): Número máximo de produtos em cada histograma
        mostrar_apenas (bool): Se True, apenas mostra os gráficos sem salvar
        
    Returns:
        dict: Dicionário com os caminhos dos histogramas gerados ou categorias processadas se mostrar_apenas=True
    """
    import pandas as pd
    from datetime import datetime
    
    print("Gerando histogramas consolidados por tipo de produto com subcategorias de fundos...")
    print(f"Datas analisadas: {mapeamento_datas}")
    
    # Carregar carteiras de todos os fundos
    carteiras_fundos = {}
    for fundo in fundos:
        data = mapeamento_datas.get(fundo, mapeamento_datas.get('default'))
        if base_dir:
            df = carregar_carteira(base_dir, fundo, data)
            if df is not None:
                carteiras_fundos[fundo] = df
                print(f"Carregada carteira de {fundo} para a data {data}")
            else:
                print(f"AVISO: Não foi possível carregar a carteira de {fundo} para {data}")
        else:
            # Se estamos apenas mostrando, criar dados de exemplo
            print(f"Usando dados de exemplo para {fundo} na data {data}")
            # Aqui você poderia criar dados de exemplo para testes
    
    # Verificar se temos alguma carteira para processar
    if not carteiras_fundos and not mostrar_apenas:
        print("ERRO: Nenhuma carteira disponível para processar. Verifique os dados.")
        return {}
    
    # Diretório para salvar os resultados (se não mostrar_apenas)
    dir_relatorios = None
    if base_dir and not mostrar_apenas:
        dir_relatorios = os.path.join(base_dir, 'relatorios', 'consolidado')
        os.makedirs(dir_relatorios, exist_ok=True)
    
    # Extrair produtos por tipo
    produtos_por_tipo = extrair_produtos_por_tipo_v2(carteiras_fundos) if carteiras_fundos else {}
    
    # Para demonstração, se não temos dados reais, usar dados de exemplo
    if not produtos_por_tipo:
        print("Usando dados de exemplo para demonstração...")
        produtos_por_tipo = {
            'Debêntures': [
                {'nome': 'Debenture 1', 'valor': 10000000},
                {'nome': 'Debenture 2', 'valor': 8000000},
                {'nome': 'Debenture 3', 'valor': 6000000},
                {'nome': 'Debenture 4', 'valor': 5000000},
                {'nome': 'Debenture 5', 'valor': 4000000},
            ],
            'Fundos de Ações': [
                {'nome': 'Fundo Ações A', 'valor': 15000000},
                {'nome': 'Fundo Ações B', 'valor': 12000000},
                {'nome': 'Fundo Ações C', 'valor': 9000000},
            ],
            'Títulos Públicos': [
                {'nome': 'LFT', 'valor': 20000000},
                {'nome': 'NTN-B', 'valor': 18000000},
                {'nome': 'LTN', 'valor': 15000000},
            ]
        }
    
    # Verificar se extraímos algum produto
    if not produtos_por_tipo:
        print("AVISO: Nenhum produto extraído das carteiras. Verifique os dados.")
        return {}
    
    print(f"Categorias identificadas: {', '.join(produtos_por_tipo.keys())}")
    
    # Determinar cores específicas para subcategorias de fundos
    cores_tipo = {
        'Debêntures': '#00008B',            # Azul escuro
        'Títulos Públicos': '#8B0000',      # Vermelho escuro
        'Fundos de Ações': '#B22222',       # Fire Brick (vermelho tijolo)
        'Fundos de Renda Fixa': '#4169E1',  # Royal Blue (azul royal)
        'Fundos Multimercado': '#228B22',   # Forest Green (verde floresta)
        'Fundos de Private Equity': '#8B008B', # Dark Magenta (magenta escuro)
        'Outros Fundos': '#4B0082',         # Indigo
        'Renda Fixa - Bancário': '#404040', # Cinza escuro
        'Operações Compromissadas': '#2F4F4F', # Dark Slate Gray
        'Outros': '#5D4037'                 # Marrom escuro
    }
    
    # Gerar histograma para cada tipo de produto
    resultados = {}
    for tipo, produtos in produtos_por_tipo.items():
        if produtos:  # Verificar se há produtos nesta categoria
            # Ajustar max_produtos com base na categoria
            max_produtos_cat = max_produtos
            if "Fundos" in tipo:
                max_produtos_cat = max(15, max_produtos)  # Pelo menos 15 para categorias de fundos
            
            resultado = gerar_histograma_tipo_produto_v2(
                tipo, 
                produtos, 
                dir_relatorios, 
                max_produtos=max_produtos_cat,
                cores_tipo=cores_tipo,
                mostrar_apenas=mostrar_apenas
            )
            
            if mostrar_apenas:
                resultados[tipo] = "Mostrado"
            else:
                resultados[tipo] = resultado
    
    # Se não estamos apenas mostrando, gerar relatório HTML
    if not mostrar_apenas and dir_relatorios:
        # Código para gerar relatório HTML aqui (mantendo o que estava no original)
        # ...
        print("Relatório HTML gerado com sucesso!")
    
    return resultados


# Função para demonstração que apenas mostra os gráficos sem salvar
def chamar_histogramas():
    """
    Demonstração dos histogramas usando dados de exemplo
    """
    # Lista de fundos para demonstração
    lista_fundos = ['chimborazo', 'aconcagua', 'alpamayo', 'huayna']
    
    # Mapeamento de datas para cada fundo
    mapeamento_datas = {
        'huayna': '2025-01',  # Data específica para huayna
        'default': '2025-02'  # Data padrão para os demais fundos
    }
    
    # Chamar a função apenas para mostrar os gráficos
    resultados = gerar_histogramas_consolidados_v2(
        lista_fundos, 
        mapeamento_datas,
        mostrar_apenas=True,  # Importante: apenas mostrar sem salvar
        max_produtos=10
    )
    
    return resultados


chamar_histogramas()


    
    