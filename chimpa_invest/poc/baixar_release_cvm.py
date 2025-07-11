#!/usr/bin/env python3
"""
Script unificado para baixar releases CVM com busca inteligente
Aceita: ticker, nome, código CVM ou CNPJ
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

# Importar o buscador
try:
    from buscar_empresa_cvm import buscar_empresa_interativo, obter_nome_cvm
except ImportError:
    print("Erro: arquivo buscar_empresa_cvm.py não encontrado")
    sys.exit(1)

def baixar_ultimo_release(termo_busca):
    """Baixa o último release de uma empresa"""
    
    # Buscar empresa no sistema
    print(f"Buscando empresa: {termo_busca}")
    nome_empresa = obter_nome_cvm(termo_busca)
    
    if not nome_empresa:
        print(f"\nEmpresa não encontrada para: {termo_busca}")
        print("\nDicas:")
        print("- Para tickers, use sem o F (ex: PETR4, não PETR4F)")
        print("- Tente o nome parcial (ex: PETROBRAS)")
        print("- Use o código CVM se souber")
        print("- Para busca interativa, execute sem argumentos")
        return False
    
    print(f"Empresa encontrada: {nome_empresa}")
    
    # Configurações
    ano_atual = datetime.now().year
    pasta_pending = Path(__file__).parent.parent / "documents" / "pending"
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
        print(f"Nenhum documento encontrado para {nome_empresa} em {ano_atual}")
        return False
    
    print(f"Encontrados {len(df_empresa)} documentos")
    
    # Converter datas
    df_empresa['Data_Entrega'] = pd.to_datetime(df_empresa['Data_Entrega'], errors='coerce')
    
    # Filtrar APENAS releases de resultados trimestrais
    palavras_resultado = [
        'Desempenho', 'Resultado', 'Release de Resultado',
        'Informações Trimestrais', 'ITR',
        '1T', '2T', '3T', '4T', '1Q', '2Q', '3Q', '4Q',
        'Trimestre', 'Trimestral', 'Earnings',
        'Demonstrações Financeiras'
    ]
    
    palavras_excluir = [
        'Ata', 'AGO', 'AGE', 'Assembl', 'Eleição', 'Conselho',
        'Dividendo', 'JCP', 'Juros', 'Aquisição', 'Venda',
        'Aprovação', 'Plano', 'incorporadas em prospectos',
        'arquivados na SEC', 'Produção e Vendas'
    ]
    
    mask_incluir = df_empresa['Assunto'].str.contains('|'.join(palavras_resultado), case=False, na=False)
    mask_excluir = df_empresa['Assunto'].str.contains('|'.join(palavras_excluir), case=False, na=False)
    
    tipos_validos = ['Dados Econômico-Financeiros', 'Comunicado ao Mercado', 'Fato Relevante', 
                     'Press-release', 'Apresentações a analistas/agentes do mercado',
                     'Demonstrações Financeiras Anuais Completas', 'Demonstrações Financeiras Intermediárias']
    mask_tipo = df_empresa['Tipo'].isin(tipos_validos) | df_empresa['Tipo'].isna()
    
    df_filtrado = df_empresa[mask_incluir & ~mask_excluir & mask_tipo]
    
    if df_filtrado.empty:
        print("\nNenhum release de resultado encontrado!")
        print("\nÚltimos 5 documentos disponíveis:")
        df_recentes = df_empresa.sort_values('Data_Entrega', ascending=False).head(5)
        for idx, row in df_recentes.iterrows():
            assunto = str(row['Assunto'])[:70] if pd.notna(row['Assunto']) else 'N/A'
            print(f"- {row['Data_Entrega'].strftime('%Y-%m-%d')}: {assunto}...")
        return False
    
    # Ordenar e priorizar releases principais
    df_filtrado = df_filtrado.sort_values('Data_Entrega', ascending=False).copy()
    
    # Pegar releases do mesmo período (7 dias)
    if not df_filtrado.empty:
        data_mais_recente = df_filtrado.iloc[0]['Data_Entrega']
        data_limite = data_mais_recente - pd.Timedelta(days=7)
        df_periodo = df_filtrado[df_filtrado['Data_Entrega'] >= data_limite].copy()
        
        # Priorizar releases principais sobre apresentações
        if len(df_periodo) > 1:
            mask_nao_apresentacao = ~df_periodo['Assunto'].str.contains('Apresentação|Conference Call|Call', case=False, na=False)
            df_principal = df_periodo[mask_nao_apresentacao]
            
            if not df_principal.empty:
                df_filtrado = df_principal
            else:
                df_filtrado = df_periodo
        else:
            df_filtrado = df_periodo
    
    # Mostrar opções encontradas
    print(f"\nReleases de resultados encontrados: {len(df_filtrado)}")
    print("Últimos 3:")
    for idx, row in df_filtrado.head(3).iterrows():
        assunto = str(row['Assunto'])[:70] if pd.notna(row['Assunto']) else 'N/A'
        print(f"- {row['Data_Entrega'].strftime('%Y-%m-%d')}: {assunto}...")
    
    # Pegar o mais recente
    ultimo_release = df_filtrado.iloc[0]
    
    # Mostrar informações
    print(f"\n=== Release Selecionado ===")
    print(f"Data: {ultimo_release['Data_Entrega'].strftime('%Y-%m-%d')}")
    print(f"Assunto: {ultimo_release['Assunto']}")
    print(f"Tipo: {ultimo_release['Tipo']}")
    
    # Preparar nome do arquivo
    empresa_limpa = ''.join(c for c in nome_empresa if c.isalnum() or c in ' ')[:50].strip()
    data_str = ultimo_release['Data_Entrega'].strftime('%Y%m%d')
    assunto_limpo = ''.join(c for c in str(ultimo_release['Assunto']) if c.isalnum() or c in ' ')[:60].strip()
    nome_arquivo = f"{empresa_limpa}_{data_str}_{assunto_limpo}.pdf"
    nome_arquivo = nome_arquivo.replace('  ', ' ').replace(' ', '_')
    
    # Verificar se já existe
    caminho_arquivo = pasta_pending / nome_arquivo
    if caminho_arquivo.exists():
        print(f"\nArquivo já existe: {nome_arquivo}")
        return True
    
    # Baixar PDF
    url_download = ultimo_release['Link_Download']
    print(f"\nBaixando PDF...")
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url_download, headers=headers, timeout=60, stream=True)
        response.raise_for_status()
        
        # Salvar arquivo
        total_size = int(response.headers.get('Content-Length', 0))
        downloaded = 0
        
        with open(caminho_arquivo, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rProgresso: {percent:.1f}%", end='')
        
        print(f"\n\nPDF salvo: {nome_arquivo}")
        print(f"Tamanho: {downloaded / (1024*1024):.2f} MB")
        
        # Salvar metadados
        metadata = {
            "empresa": nome_empresa,
            "ticker_busca": termo_busca,
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
        print(f"\nErro ao baixar PDF: {e}")
        return False


def main():
    """Função principal"""
    print("=== Download de Releases CVM ===")
    
    if len(sys.argv) > 1:
        # Modo direto com argumento
        termo = ' '.join(sys.argv[1:])
        sucesso = baixar_ultimo_release(termo)
    else:
        # Modo interativo
        print("\nModo interativo - busca avançada de empresas")
        empresa = buscar_empresa_interativo()
        
        if empresa:
            print(f"\nBaixando release de: {empresa['nome_completo']}")
            sucesso = baixar_ultimo_release(empresa['nome_completo'])
        else:
            print("\nNenhuma empresa selecionada")
            sucesso = False
    
    if sucesso:
        print("\n✓ Download concluído com sucesso!")
    else:
        print("\n✗ Falha no download")
        sys.exit(1)


if __name__ == "__main__":
    main()