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

def extrair_produtos_direto(df, fundo):
    """Extrai produtos diretamente do DataFrame bruto, sem agrupamentos"""
    produtos = []
    
    # Para huayna: usar códigos das debêntures
    if fundo == 'huayna' and 'CD_ATIVO' in df.columns:
        debentures = df[df['CD_ATIVO'].notna() & (df['CD_ATIVO'] != '')]
        for _, row in debentures.iterrows():
            produtos.append({
                'nome': row['CD_ATIVO'],
                'valor': row['VL_MERC_POS_FINAL']
            })
    
    # Títulos públicos: tratar individualmente
    if 'TP_TITPUB' in df.columns:
        titulos = df[df['TP_TITPUB'].notna() & (df['TP_TITPUB'] != '')]
        for _, row in titulos.iterrows():
            produtos.append({
                'nome': row['TP_TITPUB'],
                'valor': row['VL_MERC_POS_FINAL']
            })
    
    # Fundos de investimento: tratar individualmente
    if 'NM_FUNDO_CLASSE_SUBCLASSE_COTA' in df.columns:
        fundos_inv = df[df['NM_FUNDO_CLASSE_SUBCLASSE_COTA'].notna() & (df['NM_FUNDO_CLASSE_SUBCLASSE_COTA'] != '')]
        for _, row in fundos_inv.iterrows():
            nome = str(row['NM_FUNDO_CLASSE_SUBCLASSE_COTA'])
            nome = re.sub(r'FUNDO DE INVESTIMENTO FINANCEIRO|FUNDO DE INVESTIMENTO|RESPONSABILIDADE LIMITADA', '', nome).strip()
            nome = nome[:40] + '...' if len(nome) > 40 else nome
            
            produtos.append({
                'nome': nome,
                'valor': row['VL_MERC_POS_FINAL']
            })
    
    # Renda Fixa - Bancário: incluir individualmente
    if 'CATEGORIA_ATIVO' in df.columns:
        bancario = df[df['CATEGORIA_ATIVO'] == 'Renda Fixa - Bancário']
        if not bancario.empty:
            produtos.append({
                'nome': 'Renda Fixa - Bancário',
                'valor': bancario['VL_MERC_POS_FINAL'].sum()
            })
    
    # Operações Compromissadas
    if 'TP_APLIC' in df.columns:
        compromissadas = df[df['TP_APLIC'] == 'Operações Compromissadas']
        if not compromissadas.empty:
            produtos.append({
                'nome': 'Operações Compromissadas',
                'valor': compromissadas['VL_MERC_POS_FINAL'].sum()
            })
    
    # Mercado Futuro e outros produtos específicos
    if 'DS_ATIVO' in df.columns:
        outros = df[(df['DS_ATIVO'] == 'DISPONIBILIDADES') | 
                   (df['DS_ATIVO'] == 'VALORES A RECEBER') | 
                   (df['DS_ATIVO'] == 'VALORES A PAGAR') |
                   (df['DS_ATIVO'] == 'Futuro de Cupom de IPCA - FUT DAP')]
        
        for descricao, grupo in outros.groupby('DS_ATIVO'):
            if descricao == 'DISPONIBILIDADES':
                nome = 'Caixa e Disponibilidades'
            elif descricao == 'Futuro de Cupom de IPCA - FUT DAP':
                # Verificar se é posição comprada ou vendida
                if 'TP_APLIC' in grupo.columns:
                    posicoes_compradas = grupo[grupo['TP_APLIC'] == 'Mercado Futuro - Posições compradas']
                    posicoes_vendidas = grupo[grupo['TP_APLIC'] == 'Mercado Futuro - Posições vendidas']
                    
                    if not posicoes_compradas.empty:
                        produtos.append({
                            'nome': 'Mercado Futuro - Posições compradas',
                            'valor': posicoes_compradas['VL_MERC_POS_FINAL'].sum()
                        })
                    
                    if not posicoes_vendidas.empty:
                        produtos.append({
                            'nome': 'Mercado Futuro - Posições vendidas',
                            'valor': posicoes_vendidas['VL_MERC_POS_FINAL'].sum()
                        })
                else:
                    produtos.append({
                        'nome': 'Mercado Futuro',
                        'valor': grupo['VL_MERC_POS_FINAL'].sum()
                    })
            else:
                nome = descricao.title()
                
            # Adicionar apenas se não foi adicionado nas categorias específicas acima
            if descricao != 'Futuro de Cupom de IPCA - FUT DAP':
                produtos.append({
                    'nome': nome,
                    'valor': grupo['VL_MERC_POS_FINAL'].sum()
                })
    
    # Produtos não capturados acima
    produtos_nomes = [p['nome'] for p in produtos]
    valores_capturados = sum(p['valor'] for p in produtos)
    valor_total = df['VL_MERC_POS_FINAL'].sum()
    
    if valor_total - valores_capturados > 0.01 * valor_total:  # Mais de 1% não capturado
        produtos.append({
            'nome': 'Outros',
            'valor': valor_total - valores_capturados
        })
    
    return produtos

def gerar_histograma_completo(fundo, data, base_dir):
    """Gera histograma com todos os produtos, sem limitação"""
    print(f"Processando {fundo} para data {data}...")
    
    # Cores base por fundo
    cores = {
        'alpamayo': '#404040',    # Cinza escuro
        'huayna': '#00008B',      # Azul escuro
        'chimborazo': '#006400',  # Verde escuro
        'aconcagua': '#8B0000'    # Vermelho escuro
    }
    
    # Carregar dados
    df = carregar_carteira(base_dir, fundo, data)
    if df is None:
        return
    
    # Extrair produtos
    produtos_lista = extrair_produtos_direto(df, fundo)
    
    # Converter para DataFrame
    produtos_df = pd.DataFrame(produtos_lista)
    
    # Agrupar produtos com mesmo nome (somando valores)
    if not produtos_df.empty:
        produtos_df = produtos_df.groupby('nome')['valor'].sum().reset_index()
    
    # Calcular percentuais
    valor_total = produtos_df['valor'].sum()
    produtos_df['percentual'] = (produtos_df['valor'] / valor_total * 100).round(2)
    
    # Verificação da soma dos percentuais
    soma_percentuais = produtos_df['percentual'].sum()
    print(f"Soma dos percentuais para {fundo}: {soma_percentuais:.2f}%")
    
    # Verificar se está próximo de 100%
    if abs(soma_percentuais - 100) > 1:
        print(f"AVISO: Soma dos percentuais ({soma_percentuais:.2f}%) difere significativamente de 100%!")
        
        # Ajustar percentuais para somar exatamente 100%
        fator_correcao = 100 / soma_percentuais
        produtos_df['percentual'] = (produtos_df['percentual'] * fator_correcao).round(2)
        print(f"Percentuais ajustados. Nova soma: {produtos_df['percentual'].sum():.2f}%")
    
    # Ordenar por percentual (sem limitar o número de produtos)
    produtos_df = produtos_df.sort_values('percentual', ascending=False)
    
    print(f"Total de produtos encontrados para {fundo}: {len(produtos_df)}")
    
    # Ajustar tamanho da figura com base no número de produtos
    altura_base = 10
    altura_por_produto = 0.3
    altura = max(altura_base, min(40, altura_base + len(produtos_df) * altura_por_produto))
    
    # Inverter ordem para visualização (maior valor no topo)
    produtos_df = produtos_df.sort_values('percentual', ascending=True)
    
    # Configurar figura com altura adaptativa
    plt.figure(figsize=(14, altura))
    
    # Criar escala de cores (degradê)
    cor_base = cores.get(fundo, '#333333')
    n_produtos = len(produtos_df)
    cmap = sns.light_palette(cor_base, n_colors=n_produtos+2)
    cores_barras = [cmap[i] for i in range(n_produtos)]
    
    # Criar barras horizontais
    bars = plt.barh(produtos_df['nome'], produtos_df['percentual'], color=cores_barras)
    
    # Adicionar valores nas barras
    for i, bar in enumerate(bars):
        width = bar.get_width()
        valor = produtos_df['valor'].iloc[i]
        
        # Formatar valor
        if valor >= 1e9:
            valor_str = f"R$ {valor/1e9:.2f}B"
        elif valor >= 1e6:
            valor_str = f"R$ {valor/1e6:.2f}M"
        else:
            valor_str = f"R$ {valor/1e3:.2f}K"
        
        plt.text(
            width + 0.05,  # Reduzir distância para caber mais texto
            bar.get_y() + bar.get_height()/2,
            f"{width:.1f}% ({valor_str})",
            va='center',
            fontsize=8,  # Fonte menor para não sobrepor
            fontweight='bold'
        )
    
    # Configurar gráfico - apenas nome do fundo no título (capitalizado)
    plt.title(f'{fundo.capitalize()}', fontsize=16, fontweight='bold')
    plt.xlabel('Percentual da Carteira (%)', fontsize=12)
    plt.ylabel('Produto', fontsize=12)
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    
    # Ajustar limites do eixo X
    max_pct = produtos_df['percentual'].max() if not produtos_df.empty else 10
    plt.xlim(0, max_pct * 1.1)  # Reduzir margem para acomodar mais informações
    
    plt.tight_layout()
    
    # Diretório para salvar
    dir_relatorios = os.path.join(base_dir, 'relatorios')
    os.makedirs(dir_relatorios, exist_ok=True)
    
    # Salvar figura
    caminho = os.path.join(dir_relatorios, f"{fundo}_produtos_completo.png")
    plt.savefig(caminho, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Histograma completo de {fundo} salvo em: {caminho}")
    
    return caminho

def processar_todos_fundos(fundos, mapeamento_datas, base_dir):
    """Processa todos os fundos com as datas especificadas, mostrando todos os produtos"""
    resultados = {}
    
    for fundo in fundos:
        data = mapeamento_datas.get(fundo, mapeamento_datas.get('default'))
        caminho = gerar_histograma_completo(fundo, data, base_dir)
        resultados[fundo] = caminho
    
    return resultados



# Executar
if __name__ == "__main__":
    lista_fundos = ['chimborazo', 'aconcagua', 'alpamayo', 'huayna']
    base_dir = "C:/Users/guilh/Documents/GitHub/flab/database"
    mapeamento_datas = {
        'huayna': '2025-01',
        'default': '2025-02'
    }
    
    resultados = processar_todos_fundos(lista_fundos, mapeamento_datas, base_dir)
    print("Histogramas completos gerados com sucesso.")
    
    
    