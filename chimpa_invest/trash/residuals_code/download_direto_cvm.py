#!/usr/bin/env python3
"""
Download Direto CVM - Solução Alternativa
=========================================
Acessa diretamente os PDFs usando padrões conhecidos da CVM.
"""

import requests
import pandas as pd
from pathlib import Path
import re
import time
import json
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import subprocess
import webbrowser


class DownloadDiretoCVM:
    """
    Downloader que usa métodos alternativos para acessar PDFs da CVM.
    """
    
    def __init__(self, pasta_destino: str = "documents/releases_direto"):
        self.pasta_destino = Path(pasta_destino)
        self.pasta_destino.mkdir(parents=True, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def extrair_parametros_url(self, url: str) -> dict:
        """
        Extrai parâmetros da URL da CVM.
        """
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        return {
            'protocolo': params.get('numProtocolo', [''])[0],
            'sequencia': params.get('numSequencia', [''])[0],
            'versao': params.get('numVersao', [''])[0]
        }
    
    def gerar_url_alternativa(self, protocolo: str, sequencia: str) -> list:
        """
        Gera URLs alternativas para tentar acessar o PDF.
        """
        urls = [
            # URL padrão do sistema ENET
            f"https://www.rad.cvm.gov.br/ENET/frmGeraPDF.aspx?NumeroProtocoloEntrega={protocolo}",
            
            # URL alternativa com sequência
            f"https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?numProtocolo={protocolo}&numSequencia={sequencia}",
            
            # URL do sistema empresas.net
            f"https://sistemas.cvm.gov.br/asp/cvmwww/InvNet/Downloads/{protocolo}.pdf",
            
            # URL antiga do sistema
            f"https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/CPublica/CiaAb/FormBuscaCiaAb.aspx?NumeroSequencialDocumento={sequencia}"
        ]
        
        return urls
    
    def baixar_via_wget(self, url: str, arquivo_destino: Path) -> bool:
        """
        Tenta baixar usando wget (mais robusto para alguns sites).
        """
        try:
            cmd = [
                'wget',
                '--user-agent=Mozilla/5.0',
                '--tries=3',
                '--timeout=30',
                '-O', str(arquivo_destino),
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and arquivo_destino.exists():
                tamanho = arquivo_destino.stat().st_size
                if tamanho > 1000:  # Arquivo maior que 1KB
                    return True
                else:
                    arquivo_destino.unlink()
            
            return False
            
        except Exception as e:
            print(f"Erro com wget: {e}")
            return False
    
    def baixar_via_curl(self, url: str, arquivo_destino: Path) -> bool:
        """
        Tenta baixar usando curl.
        """
        try:
            cmd = [
                'curl',
                '-L',  # Seguir redirecionamentos
                '-s',  # Silencioso
                '--user-agent', 'Mozilla/5.0',
                '--max-redirs', '5',
                '-o', str(arquivo_destino),
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and arquivo_destino.exists():
                tamanho = arquivo_destino.stat().st_size
                if tamanho > 1000:
                    return True
                else:
                    arquivo_destino.unlink()
            
            return False
            
        except Exception as e:
            print(f"Erro com curl: {e}")
            return False
    
    def abrir_no_navegador(self, url: str, assunto: str):
        """
        Abre o link no navegador para download manual.
        """
        print(f"\n🌐 Abrindo no navegador: {assunto[:50]}...")
        print(f"   URL: {url}")
        webbrowser.open(url)
        time.sleep(2)
    
    def processar_releases(self, empresa: str, ano: int = 2025, modo: str = "auto"):
        """
        Processa releases de uma empresa.
        
        Modos:
        - auto: tenta baixar automaticamente
        - manual: abre links no navegador
        - lista: apenas lista os releases
        """
        print(f"\n🏢 Processando releases de {empresa} - {ano}")
        print("=" * 50)
        
        # Ler arquivo IPE
        ipe_file = f"ipe_cia_aberta_{ano}.csv"
        if not Path(ipe_file).exists():
            print(f"❌ Arquivo {ipe_file} não encontrado")
            return
        
        df = pd.read_csv(ipe_file, sep=';', encoding='latin-1')
        
        # Filtrar empresa
        df_empresa = df[df['Nome_Companhia'].str.contains(empresa.upper(), case=False, na=False)]
        
        # Filtrar releases de resultados
        palavras = ['resultado', 'trimestre', 'itr', '1t', '2t', '3t', '4t', 'release', 'earnings']
        mask = df_empresa['Assunto'].str.lower().str.contains('|'.join(palavras), na=False)
        releases = df_empresa[mask]
        
        if releases.empty:
            print(f"❌ Nenhum release encontrado para {empresa}")
            return
        
        print(f"✅ Encontrados {len(releases)} releases")
        
        # Criar pasta da empresa
        empresa_dir = self.pasta_destino / empresa.upper()
        empresa_dir.mkdir(exist_ok=True)
        
        # Processar cada release
        resultados = []
        
        for idx, row in releases.iterrows():
            assunto = row['Assunto']
            data = row['Data_Entrega']
            url = row['Link_Download']
            
            print(f"\n📄 {data[:10]} - {assunto[:60]}...")
            
            if modo == "lista":
                print(f"   URL: {url}")
                resultados.append({
                    'data': data,
                    'assunto': assunto,
                    'url': url
                })
                continue
            
            elif modo == "manual":
                self.abrir_no_navegador(url, assunto)
                resultados.append({
                    'data': data,
                    'assunto': assunto,
                    'url': url,
                    'status': 'aberto_navegador'
                })
                continue
            
            # Modo automático
            params = self.extrair_parametros_url(url)
            
            # Gerar nome do arquivo
            data_clean = data.replace('-', '')[:8]
            assunto_clean = re.sub(r'[^\w\s-]', '', assunto)[:50]
            nome_arquivo = f"{data_clean}_{assunto_clean}.pdf"
            arquivo_destino = empresa_dir / nome_arquivo
            
            if arquivo_destino.exists():
                print(f"   ✅ Arquivo já existe")
                resultados.append({
                    'data': data,
                    'assunto': assunto,
                    'arquivo': str(arquivo_destino),
                    'status': 'existe'
                })
                continue
            
            # Tentar diferentes métodos
            sucesso = False
            
            # Método 1: wget
            if not sucesso:
                print("   Tentando com wget...")
                sucesso = self.baixar_via_wget(url, arquivo_destino)
            
            # Método 2: curl
            if not sucesso:
                print("   Tentando com curl...")
                sucesso = self.baixar_via_curl(url, arquivo_destino)
            
            # Método 3: URLs alternativas
            if not sucesso and params['protocolo']:
                urls_alt = self.gerar_url_alternativa(params['protocolo'], params['sequencia'])
                for url_alt in urls_alt:
                    print(f"   Tentando URL alternativa...")
                    sucesso = self.baixar_via_wget(url_alt, arquivo_destino)
                    if sucesso:
                        break
            
            if sucesso:
                print(f"   ✅ Download concluído: {arquivo_destino.name}")
                resultados.append({
                    'data': data,
                    'assunto': assunto,
                    'arquivo': str(arquivo_destino),
                    'status': 'baixado'
                })
            else:
                print(f"   ❌ Falha no download automático")
                if input("   Abrir no navegador? (s/N): ").lower() == 's':
                    self.abrir_no_navegador(url, assunto)
                
                resultados.append({
                    'data': data,
                    'assunto': assunto,
                    'url': url,
                    'status': 'falha'
                })
        
        # Salvar relatório
        relatorio = {
            'empresa': empresa,
            'data_execucao': datetime.now().isoformat(),
            'modo': modo,
            'total_releases': len(releases),
            'resultados': resultados
        }
        
        relatorio_file = empresa_dir / f"relatorio_{modo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(relatorio_file, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)
        
        print(f"\n📝 Relatório salvo: {relatorio_file}")
        
        # Resumo
        if modo == "auto":
            baixados = len([r for r in resultados if r.get('status') == 'baixado'])
            existentes = len([r for r in resultados if r.get('status') == 'existe'])
            falhas = len([r for r in resultados if r.get('status') == 'falha'])
            
            print(f"\n📊 RESUMO:")
            print(f"   ✅ Baixados: {baixados}")
            print(f"   📁 Já existentes: {existentes}")
            print(f"   ❌ Falhas: {falhas}")


def main():
    """
    Menu principal.
    """
    print("💾 DOWNLOAD DIRETO CVM - RELEASES TRIMESTRAIS")
    print("=" * 50)
    
    downloader = DownloadDiretoCVM()
    
    # Verificar ferramentas disponíveis
    print("\n🔧 Verificando ferramentas...")
    tem_wget = subprocess.run(['which', 'wget'], capture_output=True).returncode == 0
    tem_curl = subprocess.run(['which', 'curl'], capture_output=True).returncode == 0
    
    print(f"   wget: {'✅ Disponível' if tem_wget else '❌ Não encontrado'}")
    print(f"   curl: {'✅ Disponível' if tem_curl else '❌ Não encontrado'}")
    
    if not tem_wget and not tem_curl:
        print("\n⚠️  Nenhuma ferramenta de download encontrada!")
        print("   Instale wget ou curl para melhor funcionamento")
    
    # Menu
    print("\n📊 OPÇÕES:")
    print("1. Download automático (tenta baixar PDFs)")
    print("2. Abrir no navegador (download manual)")
    print("3. Apenas listar releases")
    
    opcao = input("\n👉 Escolha (1-3): ").strip()
    
    if opcao not in ['1', '2', '3']:
        print("❌ Opção inválida")
        return
    
    modo = {'1': 'auto', '2': 'manual', '3': 'lista'}[opcao]
    
    # Empresa
    empresa = input("\n🏢 Nome da empresa: ").strip().upper()
    if not empresa:
        print("❌ Nome obrigatório")
        return
    
    # Executar
    downloader.processar_releases(empresa, 2025, modo)


if __name__ == "__main__":
    main()