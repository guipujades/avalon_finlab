#!/usr/bin/env python3
"""
Script unificado para coletar dados estruturados da CVM
Funciona em Windows, Linux e macOS
Permite escolha de período de dados
"""
import requests
import pandas as pd
import zipfile
import io
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import time
import platform
import json
import sys

# URLs base da CVM
URLS_CVM = {
    'ITR': 'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/',
    'DFP': 'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/'
}

def get_output_path():
    """
    Determina o caminho de saída baseado no sistema operacional
    e estrutura de pastas existente
    """
    # Primeiro, tenta encontrar a pasta database/chimpa relativa ao script
    script_dir = Path(__file__).parent.absolute()
    
    # Sobe dois níveis (poc -> chimpa_invest -> github)
    github_dir = script_dir.parent.parent
    
    # Caminho preferencial: database/chimpa
    database_path = github_dir / "database" / "chimpa"
    
    # Se não existir, cria dentro do próprio projeto
    if not database_path.exists():
        print(f"Pasta database/chimpa não encontrada em {github_dir}")
        print("Criando pasta de dados dentro do projeto...")
        database_path = script_dir.parent / "dados_cvm" / "chimpa"
    
    return database_path

def get_date_range():
    """
    Obtém o intervalo de datas do usuário ou usa padrão
    """
    print("\n=== Configuração do Período de Dados ===")
    print("Pressione ENTER para usar o período padrão (2015-2025)")
    print("Ou digite o período desejado")
    print()
    
    try:
        ano_inicial = input("Ano inicial (ex: 2015): ").strip()
        if not ano_inicial:
            ano_inicial = 2015
            ano_final = 2025
            print(f"Usando período padrão: {ano_inicial}-{ano_final}")
        else:
            ano_inicial = int(ano_inicial)
            ano_final = input("Ano final (ex: 2025): ").strip()
            ano_final = int(ano_final) if ano_final else datetime.now().year
            
        # Validações
        if ano_inicial < 2010:
            print("Aviso: Dados anteriores a 2010 podem não estar disponíveis")
        if ano_final > datetime.now().year:
            ano_final = datetime.now().year
            print(f"Ajustado ano final para {ano_final}")
        if ano_inicial > ano_final:
            ano_inicial, ano_final = ano_final, ano_inicial
            print(f"Anos invertidos. Usando: {ano_inicial}-{ano_final}")
            
        return list(range(ano_inicial, ano_final + 1))
        
    except ValueError:
        print("Entrada inválida. Usando período padrão: 2015-2025")
        return list(range(2015, 2026))

def get_document_types():
    """
    Permite escolher quais tipos de documentos baixar
    """
    print("\n=== Tipos de Documentos ===")
    print("1. ITR - Informações Trimestrais")
    print("2. DFP - Demonstrações Financeiras Padronizadas (Anuais)")
    print("3. Ambos (padrão)")
    
    escolha = input("\nEscolha (1/2/3 ou ENTER para ambos): ").strip()
    
    if escolha == '1':
        return ['ITR']
    elif escolha == '2':
        return ['DFP']
    else:
        return ['ITR', 'DFP']

def criar_estrutura_pastas(output_path, tipos_documentos, anos):
    """Cria estrutura de pastas para salvar os dados"""
    output_path.mkdir(parents=True, exist_ok=True)
    
    for tipo in tipos_documentos:
        pasta_tipo = output_path / tipo
        pasta_tipo.mkdir(exist_ok=True)
        for ano in anos:
            pasta_ano = pasta_tipo / str(ano)
            pasta_ano.mkdir(exist_ok=True)

def baixar_arquivo_cvm(tipo_doc, ano, output_path):
    """Baixa arquivo ZIP da CVM e extrai CSVs relevantes"""
    url = f"{URLS_CVM[tipo_doc]}{tipo_doc.lower()}_cia_aberta_{ano}.zip"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Processar ZIP em memória
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
            # Arquivos que contém balanço e DRE
            arquivos_interesse = [
                f'{tipo_doc.lower()}_cia_aberta_BPA_con_{ano}.csv',  # Balanço Patrimonial Ativo consolidado
                f'{tipo_doc.lower()}_cia_aberta_BPP_con_{ano}.csv',  # Balanço Patrimonial Passivo consolidado
                f'{tipo_doc.lower()}_cia_aberta_DRE_con_{ano}.csv',  # DRE consolidado
                f'{tipo_doc.lower()}_cia_aberta_BPA_ind_{ano}.csv',  # Balanço Patrimonial Ativo individual
                f'{tipo_doc.lower()}_cia_aberta_BPP_ind_{ano}.csv',  # Balanço Patrimonial Passivo individual
                f'{tipo_doc.lower()}_cia_aberta_DRE_ind_{ano}.csv',  # DRE individual
                f'{tipo_doc.lower()}_cia_aberta_{ano}.csv'          # Dados gerais
            ]
            
            for arquivo in arquivos_interesse:
                if arquivo in zip_file.namelist():
                    # Ler e salvar CSV
                    df = pd.read_csv(
                        zip_file.open(arquivo),
                        sep=';',
                        encoding='latin-1',
                        decimal=',',
                        low_memory=False
                    )
                    
                    # Salvar localmente
                    caminho_saida = output_path / tipo_doc / str(ano) / arquivo
                    df.to_csv(caminho_saida, index=False, sep=';', encoding='utf-8')
                    
        return True
    except requests.exceptions.RequestException as e:
        return False
    except Exception as e:
        print(f"Erro ao processar {tipo_doc} {ano}: {str(e)}")
        return False

def verificar_bibliotecas():
    """Verifica se as bibliotecas necessárias estão instaladas"""
    bibliotecas_faltando = []
    
    try:
        import requests
    except ImportError:
        bibliotecas_faltando.append('requests')
    
    try:
        import pandas
    except ImportError:
        bibliotecas_faltando.append('pandas')
    
    try:
        from tqdm import tqdm
    except ImportError:
        bibliotecas_faltando.append('tqdm')
    
    if bibliotecas_faltando:
        print("ERRO: Bibliotecas necessárias não encontradas!")
        print("Por favor, instale as seguintes bibliotecas:")
        print(f"\npip install {' '.join(bibliotecas_faltando)}")
        print("\nOu execute:")
        print("pip install pandas requests tqdm")
        sys.exit(1)

def main():
    """Função principal"""
    # Verificar bibliotecas
    verificar_bibliotecas()
    
    print("=== Coletor de Dados CVM ===")
    print(f"Sistema Operacional: {platform.system()}")
    print(f"Python: {sys.version.split()[0]}")
    
    # Obter configurações
    output_path = get_output_path()
    anos = get_date_range()
    tipos_documentos = get_document_types()
    
    print(f"\n=== Resumo da Coleta ===")
    print(f"Destino: {output_path}")
    print(f"Anos: {anos[0]} a {anos[-1]} ({len(anos)} anos)")
    print(f"Tipos: {', '.join(tipos_documentos)}")
    
    confirmar = input("\nIniciar download? (S/n): ").strip().lower()
    if confirmar == 'n':
        print("Download cancelado.")
        return
    
    # Criar estrutura de pastas
    criar_estrutura_pastas(output_path, tipos_documentos, anos)
    
    # Estatísticas
    total_downloads = len(tipos_documentos) * len(anos)
    sucesso = 0
    falhas = []
    
    print("\nIniciando downloads...")
    
    with tqdm(total=total_downloads, desc="Progresso geral") as pbar:
        for tipo_doc in tipos_documentos:
            for ano in anos:
                pbar.set_description(f"Baixando {tipo_doc} {ano}")
                
                if baixar_arquivo_cvm(tipo_doc, ano, output_path):
                    sucesso += 1
                else:
                    falhas.append(f"{tipo_doc} {ano}")
                
                pbar.update(1)
                
                # Pequena pausa entre requisições
                time.sleep(0.5)
    
    # Salvar log
    log = {
        "data_execucao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sistema_operacional": platform.system(),
        "python_version": sys.version.split()[0],
        "caminho_dados": str(output_path),
        "total": total_downloads,
        "sucesso": sucesso,
        "falhas": falhas,
        "anos": anos,
        "tipos": tipos_documentos
    }
    
    log_path = output_path / f"log_coleta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
    
    # Resumo final
    print(f"\n{'='*50}")
    print("=== RESUMO FINAL ===")
    print(f"{'='*50}")
    print(f"Total de downloads: {total_downloads}")
    print(f"Sucesso: {sucesso} ({sucesso/total_downloads*100:.1f}%)")
    print(f"Falhas: {len(falhas)} ({len(falhas)/total_downloads*100:.1f}%)")
    
    if falhas:
        print("\nArquivos não baixados:")
        for falha in falhas:
            print(f"  - {falha}")
    
    # Calcular tamanho total
    try:
        tamanho_total = sum(f.stat().st_size for f in output_path.rglob('*.csv'))
        print(f"\nTamanho total dos dados: {tamanho_total / (1024**3):.2f} GB")
    except:
        pass
    
    print(f"\nLog salvo em: {log_path}")
    print(f"Dados salvos em: {output_path}")
    print("\nColeta concluída!")

if __name__ == "__main__":
    main()