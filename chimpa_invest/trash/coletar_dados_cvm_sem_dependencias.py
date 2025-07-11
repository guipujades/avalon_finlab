#!/usr/bin/env python3
"""
Script para coletar dados estruturados da CVM
Versão sem dependências externas - funciona com Python puro
Compatível com Windows, Linux e macOS
"""
import urllib.request
import urllib.error
import zipfile
import io
import csv
from pathlib import Path
from datetime import datetime
import time
import json
import sys
import platform

# URLs base da CVM
URLS_CVM = {
    'ITR': 'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/',
    'DFP': 'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/'
}

class SimpleProgressBar:
    """Barra de progresso simples sem dependências"""
    def __init__(self, total, desc=""):
        self.total = total
        self.current = 0
        self.desc = desc
        self.start_time = time.time()
        
    def update(self, n=1):
        self.current += n
        self._display()
        
    def _display(self):
        percent = (self.current / self.total) * 100
        filled = int(percent / 2)
        bar = '█' * filled + '░' * (50 - filled)
        elapsed = time.time() - self.start_time
        
        sys.stdout.write(f'\r{self.desc}: [{bar}] {percent:.1f}% ({self.current}/{self.total}) - {elapsed:.1f}s')
        sys.stdout.flush()
        
        if self.current >= self.total:
            print()  # Nova linha ao completar

def get_output_path():
    """Determina o caminho de saída multiplataforma"""
    script_dir = Path(__file__).parent.absolute()
    github_dir = script_dir.parent.parent
    database_path = github_dir / "database" / "chimpa"
    
    if not database_path.exists():
        print(f"Pasta database/chimpa não encontrada")
        print("Criando pasta de dados dentro do projeto...")
        database_path = script_dir.parent / "dados_cvm" / "chimpa"
    
    return database_path

def get_date_range():
    """Obtém o intervalo de datas do usuário"""
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
    """Permite escolher quais tipos de documentos baixar"""
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
    """Cria estrutura de pastas"""
    output_path.mkdir(parents=True, exist_ok=True)
    
    for tipo in tipos_documentos:
        pasta_tipo = output_path / tipo
        pasta_tipo.mkdir(exist_ok=True)
        for ano in anos:
            pasta_ano = pasta_tipo / str(ano)
            pasta_ano.mkdir(exist_ok=True)

def baixar_arquivo_cvm(tipo_doc, ano, output_path):
    """Baixa e extrai arquivos da CVM"""
    url = f"{URLS_CVM[tipo_doc]}{tipo_doc.lower()}_cia_aberta_{ano}.zip"
    
    try:
        # Download do arquivo
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=60) as response:
            data = response.read()
        
        # Processar ZIP
        with zipfile.ZipFile(io.BytesIO(data)) as zip_file:
            arquivos_interesse = [
                f'{tipo_doc.lower()}_cia_aberta_BPA_con_{ano}.csv',
                f'{tipo_doc.lower()}_cia_aberta_BPP_con_{ano}.csv',
                f'{tipo_doc.lower()}_cia_aberta_DRE_con_{ano}.csv',
                f'{tipo_doc.lower()}_cia_aberta_BPA_ind_{ano}.csv',
                f'{tipo_doc.lower()}_cia_aberta_BPP_ind_{ano}.csv',
                f'{tipo_doc.lower()}_cia_aberta_DRE_ind_{ano}.csv',
                f'{tipo_doc.lower()}_cia_aberta_{ano}.csv'
            ]
            
            for arquivo in arquivos_interesse:
                if arquivo in zip_file.namelist():
                    caminho_saida = output_path / tipo_doc / str(ano) / arquivo
                    
                    with zip_file.open(arquivo) as f_in:
                        conteudo = f_in.read()
                        with open(caminho_saida, 'wb') as f_out:
                            f_out.write(conteudo)
        
        return True
        
    except urllib.error.URLError as e:
        print(f"\nErro de rede ao baixar {tipo_doc} {ano}: {str(e)}")
        return False
    except Exception as e:
        print(f"\nErro ao processar {tipo_doc} {ano}: {str(e)}")
        return False

def calcular_tamanho_pasta(path):
    """Calcula o tamanho total de uma pasta"""
    total = 0
    try:
        for arquivo in path.rglob('*'):
            if arquivo.is_file():
                total += arquivo.stat().st_size
    except:
        pass
    return total

def main():
    """Função principal"""
    print("=== Coletor de Dados CVM (Sem Dependências) ===")
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
    
    # Criar estrutura
    criar_estrutura_pastas(output_path, tipos_documentos, anos)
    
    # Estatísticas
    total_downloads = len(tipos_documentos) * len(anos)
    sucesso = 0
    falhas = []
    
    print("\nIniciando downloads...")
    print("(Isso pode demorar alguns minutos)\n")
    
    # Barra de progresso
    progress = SimpleProgressBar(total_downloads, "Progresso")
    
    for tipo_doc in tipos_documentos:
        for ano in anos:
            progress.desc = f"Baixando {tipo_doc} {ano}"
            
            if baixar_arquivo_cvm(tipo_doc, ano, output_path):
                sucesso += 1
            else:
                falhas.append(f"{tipo_doc} {ano}")
            
            progress.update()
            time.sleep(0.5)  # Pausa entre requisições
    
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
    print(f"\n{'='*60}")
    print("=== RESUMO FINAL ===")
    print(f"{'='*60}")
    print(f"Total de downloads: {total_downloads}")
    print(f"Sucesso: {sucesso} ({sucesso/total_downloads*100:.1f}%)")
    print(f"Falhas: {len(falhas)} ({len(falhas)/total_downloads*100:.1f}%)")
    
    if falhas:
        print("\nArquivos não baixados:")
        for falha in falhas:
            print(f"  - {falha}")
    
    # Tamanho total
    tamanho_total = calcular_tamanho_pasta(output_path)
    if tamanho_total > 0:
        print(f"\nTamanho total dos dados: {tamanho_total / (1024**3):.2f} GB")
    
    print(f"\nLog salvo em: {log_path}")
    print(f"Dados salvos em: {output_path}")
    print("\nColeta concluída!")

if __name__ == "__main__":
    main()