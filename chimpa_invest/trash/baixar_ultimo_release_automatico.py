#!/usr/bin/env python3
"""
Versão automatizada do script para baixar releases
Sem interações do usuário
"""
import requests
import pandas as pd
import zipfile
import io
from pathlib import Path
from datetime import datetime
import time
import json
import sys

# Mapeamento de tickers
TICKER_MAPPING = {
    'PETR3': 'PETRÓLEO BRASILEIRO  S.A.  - PETROBRAS',
    'PETR4': 'PETRÓLEO BRASILEIRO  S.A.  - PETROBRAS',
    'VALE3': 'VALE S.A.',
    'VALE': 'VALE S.A.',
    'BBAS3': 'BANCO DO BRASIL S.A.',
    'ITUB3': 'ITAUSA S.A.',
    'BBDC3': 'BANCO BRADESCO S.A.',
    'MGLU3': 'MAGAZINE LUIZA SA',
    'ABEV3': 'AMBEV S.A.',
}

def baixar_ultimo_release(ticker_ou_nome):
    """Baixa o último release de uma empresa"""
    
    # Determinar nome da empresa
    if ticker_ou_nome.upper() in TICKER_MAPPING:
        nome_empresa = TICKER_MAPPING[ticker_ou_nome.upper()]
        print(f"Ticker {ticker_ou_nome} → {nome_empresa}")
    else:
        nome_empresa = ticker_ou_nome
        print(f"Buscando por: {nome_empresa}")
    
    # Configurações
    ano_atual = datetime.now().year
    pasta_pending = Path("/mnt/c/Users/guilh/documents/github/chimpa_invest/documents/pending")
    pasta_pending.mkdir(parents=True, exist_ok=True)
    
    # Baixar dados IPE
    print(f"\nBaixando dados IPE de {ano_atual}...")
    url_ipe = f'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/ipe_cia_aberta_{ano_atual}.zip'
    
    try:
        response = requests.get(url_ipe, timeout=30)
        response.raise_for_status()
        
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
            df_ipe = pd.read_csv(
                zip_file.open(f'ipe_cia_aberta_{ano_atual}.csv'),
                sep=';',
                encoding='latin-1'
            )
        print(f"Dados carregados: {len(df_ipe)} registros")
    except Exception as e:
        print(f"Erro ao baixar dados IPE: {e}")
        return False
    
    # Filtrar empresa
    df_empresa = df_ipe[df_ipe['Nome_Companhia'] == nome_empresa].copy()
    
    if df_empresa.empty:
        print(f"Empresa '{nome_empresa}' não encontrada")
        
        # Buscar parcial
        palavras = nome_empresa.split()
        for palavra in palavras:
            if len(palavra) > 3:
                df_temp = df_ipe[df_ipe['Nome_Companhia'].str.contains(palavra, case=False, na=False)]
                if not df_temp.empty:
                    print(f"\nEmpresas com '{palavra}':")
                    for emp in df_temp['Nome_Companhia'].unique()[:5]:
                        print(f"  - {emp}")
                    break
        return False
    
    print(f"Encontradas {len(df_empresa)} entradas para {nome_empresa}")
    
    # Converter datas
    df_empresa['Data_Entrega'] = pd.to_datetime(df_empresa['Data_Entrega'], errors='coerce')
    
    # Filtrar APENAS releases de resultados trimestrais
    # Palavras-chave específicas para resultados trimestrais
    palavras_resultado = [
        'Desempenho',
        'Resultado',
        'Release de Resultado',
        'Informações Trimestrais',
        'ITR',
        '1T', '2T', '3T', '4T',  # Trimestres
        '1Q', '2Q', '3Q', '4Q',  # Quarters em inglês
        'Trimestre',
        'Trimestral',
        'Earnings'
    ]
    
    # Palavras que indicam que NÃO é resultado trimestral
    palavras_excluir = [
        'Ata', 'AGO', 'AGE', 'Assembl',
        'Eleição', 'Conselho',
        'Dividendo', 'JCP', 'Juros',
        'Aquisição', 'Venda',
        'Aprovação', 'Plano',
        'incorporadas em prospectos',  # Excluir anexos
        'arquivados na SEC',
        'Produção e Vendas'  # Não é resultado financeiro completo
    ]
    
    # Aplicar filtros
    mask_incluir = df_empresa['Assunto'].str.contains('|'.join(palavras_resultado), case=False, na=False)
    mask_excluir = df_empresa['Assunto'].str.contains('|'.join(palavras_excluir), case=False, na=False)
    
    # Também verificar o tipo de documento (incluir nan para Petrobras e outros)
    tipos_validos = ['Dados Econômico-Financeiros', 'Comunicado ao Mercado', 'Fato Relevante', 
                     'Press-release', 'Apresentações a analistas/agentes do mercado']
    mask_tipo = df_empresa['Tipo'].isin(tipos_validos) | df_empresa['Tipo'].isna()
    
    df_filtrado = df_empresa[mask_incluir & ~mask_excluir & mask_tipo]
    
    if df_filtrado.empty:
        print("Nenhum release de resultado trimestral encontrado!")
        print("\nÚltimos 5 documentos disponíveis:")
        for idx, row in df_empresa.head(5).iterrows():
            assunto = str(row['Assunto'])[:70] if pd.notna(row['Assunto']) else 'N/A'
        print(f"- {row['Data_Entrega'].strftime('%Y-%m-%d')}: {assunto}...")
        return False
    
    # Ordenar por data primeiro
    df_filtrado = df_filtrado.sort_values('Data_Entrega', ascending=False).copy()
    
    # Identificar o trimestre mais recente
    if not df_filtrado.empty:
        # Pegar data mais recente e buscar releases do mesmo período (7 dias)
        data_mais_recente = df_filtrado.iloc[0]['Data_Entrega']
        data_limite = data_mais_recente - pd.Timedelta(days=7)
        
        # Filtrar releases do mesmo período
        df_periodo = df_filtrado[df_filtrado['Data_Entrega'] >= data_limite].copy()
        
        # Dentro do mesmo período, priorizar releases principais
        if len(df_periodo) > 1:
            # Excluir apresentações e calls
            mask_nao_apresentacao = ~df_periodo['Assunto'].str.contains('Apresentação|Conference Call|Call', case=False, na=False)
            df_principal = df_periodo[mask_nao_apresentacao]
            
            if not df_principal.empty:
                df_filtrado = df_principal
            else:
                df_filtrado = df_periodo
        else:
            df_filtrado = df_periodo
    
    # Mostrar releases de resultados encontrados
    print(f"\nReleases de resultados encontrados: {len(df_filtrado)}")
    print("Últimos 5:")
    for idx, row in df_filtrado.head(5).iterrows():
        assunto = str(row['Assunto'])[:70] if pd.notna(row['Assunto']) else 'N/A'
        print(f"- {row['Data_Entrega'].strftime('%Y-%m-%d')}: {assunto}...")
    
    if df_filtrado.empty:
        print("Nenhum documento encontrado")
        return False
    
    ultimo_release = df_filtrado.iloc[0]
    
    # Mostrar informações
    print(f"\n=== Último Release ===")
    print(f"Data: {ultimo_release['Data_Entrega'].strftime('%Y-%m-%d')}")
    print(f"Assunto: {ultimo_release['Assunto']}")
    print(f"Tipo: {ultimo_release['Tipo']}")
    
    # Preparar nome do arquivo
    empresa_limpa = ''.join(c for c in nome_empresa if c.isalnum() or c in ' ')[:30].strip()
    data_str = ultimo_release['Data_Entrega'].strftime('%Y%m%d')
    assunto_limpo = ''.join(c for c in str(ultimo_release['Assunto']) if c.isalnum() or c in ' ')[:50].strip()
    nome_arquivo = f"{empresa_limpa}_{data_str}_{assunto_limpo}.pdf"
    
    # Baixar PDF
    url_download = ultimo_release['Link_Download']
    print(f"\nBaixando PDF...")
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url_download, headers=headers, timeout=60, stream=True)
        response.raise_for_status()
        
        caminho_arquivo = pasta_pending / nome_arquivo
        
        with open(caminho_arquivo, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        print(f"PDF salvo: {caminho_arquivo}")
        
        # Salvar metadados
        metadata = {
            "empresa": nome_empresa,
            "ticker": ticker_ou_nome if ticker_ou_nome.upper() in TICKER_MAPPING else None,
            "data_entrega": ultimo_release['Data_Entrega'].strftime('%Y-%m-%d'),
            "assunto": str(ultimo_release['Assunto']),
            "tipo": ultimo_release['Tipo'],
            "url_original": url_download,
            "arquivo": nome_arquivo,
            "download_em": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        metadata_file = pasta_pending / f"{nome_arquivo}.metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return True
        
    except Exception as e:
        print(f"Erro ao baixar PDF: {e}")
        return False

def main():
    """Função principal"""
    if len(sys.argv) < 2:
        print("Uso: python baixar_ultimo_release_automatico.py <TICKER ou NOME>")
        print("Exemplos:")
        print("  python baixar_ultimo_release_automatico.py PETR4")
        print("  python baixar_ultimo_release_automatico.py VALE3")
        print("  python baixar_ultimo_release_automatico.py 'BANCO DO BRASIL S.A.'")
        sys.exit(1)
    
    empresa = sys.argv[1]
    
    print(f"=== Baixar Último Release CVM ===")
    print(f"Empresa/Ticker: {empresa}")
    
    sucesso = baixar_ultimo_release(empresa)
    
    if sucesso:
        print("\n✓ Download concluído com sucesso!")
    else:
        print("\n✗ Falha no download")
        sys.exit(1)

if __name__ == "__main__":
    main()