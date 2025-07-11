#!/usr/bin/env python3
"""
CVM Download Documentos Estruturados
====================================
Baixa ITR, DFP e outros documentos estruturados da CVM.
Organiza por tipo de documento para fácil acesso.
"""

import requests
import pandas as pd
from pathlib import Path
import zipfile
import logging
from datetime import datetime
from typing import List, Dict, Optional
import json
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CVMDocumentosEstruturados:
    """
    Baixa e organiza documentos estruturados da CVM.
    """
    
    # URLs base da CVM para diferentes tipos de documentos
    URLS_CVM = {
        'ITR': 'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/',
        'DFP': 'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/',
        'FCA': 'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/',
        'FRE': 'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/DADOS/',
        'IPE': 'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/'
    }
    
    def __init__(self, pasta_base: str = "documents/cvm_estruturados"):
        self.pasta_base = Path(pasta_base)
        self.pasta_base.mkdir(parents=True, exist_ok=True)
        
        # Criar subpastas por tipo
        for tipo in self.URLS_CVM.keys():
            (self.pasta_base / tipo).mkdir(exist_ok=True)
    
    def listar_arquivos_disponiveis(self, tipo_doc: str) -> List[str]:
        """
        Lista arquivos disponíveis para download de um tipo específico.
        """
        url_base = self.URLS_CVM.get(tipo_doc)
        if not url_base:
            logger.error(f"Tipo de documento inválido: {tipo_doc}")
            return []
        
        try:
            response = requests.get(url_base, timeout=30)
            response.raise_for_status()
            
            # Extrair links de arquivos ZIP
            arquivos = []
            linhas = response.text.split('\n')
            
            for linha in linhas:
                if '.zip' in linha and 'href=' in linha:
                    # Extrair nome do arquivo
                    inicio = linha.find('href="') + 6
                    fim = linha.find('.zip', inicio) + 4
                    if inicio > 5 and fim > inicio:
                        arquivo = linha[inicio:fim]
                        arquivos.append(arquivo)
            
            logger.info(f"Encontrados {len(arquivos)} arquivos {tipo_doc}")
            return arquivos
            
        except Exception as e:
            logger.error(f"[ERRO] Erro ao listar arquivos {tipo_doc}: {e}")
            return []
    
    def baixar_arquivo(self, tipo_doc: str, nome_arquivo: str) -> bool:
        """
        Baixa um arquivo específico da CVM.
        """
        url_completa = self.URLS_CVM[tipo_doc] + nome_arquivo
        caminho_destino = self.pasta_base / tipo_doc / nome_arquivo
        
        # Verificar se já existe
        if caminho_destino.exists():
            logger.info(f"Arquivo já existe: {nome_arquivo}")
            return True
        
        try:
            logger.info(f"Baixando {tipo_doc}/{nome_arquivo}...")
            
            response = requests.get(url_completa, stream=True, timeout=60)
            response.raise_for_status()
            
            # Salvar arquivo
            with open(caminho_destino, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            tamanho_mb = caminho_destino.stat().st_size / (1024 * 1024)
            logger.info(f"Download concluído: {nome_arquivo} ({tamanho_mb:.1f} MB)")
            
            # Descompactar automaticamente
            self.descompactar_arquivo(tipo_doc, nome_arquivo)
            
            return True
            
        except Exception as e:
            logger.error(f"[ERRO] Erro ao baixar {nome_arquivo}: {e}")
            if caminho_destino.exists():
                caminho_destino.unlink()
            return False
    
    def descompactar_arquivo(self, tipo_doc: str, nome_arquivo: str):
        """
        Descompacta arquivo ZIP baixado.
        """
        caminho_zip = self.pasta_base / tipo_doc / nome_arquivo
        pasta_extracao = self.pasta_base / tipo_doc / nome_arquivo.replace('.zip', '')
        
        if not caminho_zip.exists():
            return
        
        try:
            logger.info(f"Descompactando {nome_arquivo}...")
            
            pasta_extracao.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
                zip_ref.extractall(pasta_extracao)
            
            # Listar conteúdo extraído
            arquivos_extraidos = list(pasta_extracao.glob('*'))
            logger.info(f"Extraídos {len(arquivos_extraidos)} arquivos")
            
        except Exception as e:
            logger.error(f"[ERRO] Erro ao descompactar {nome_arquivo}: {e}")
    
    def baixar_documentos_periodo(self, tipos_doc: List[str], anos: List[int]):
        """
        Baixa documentos de tipos específicos para anos específicos.
        """
        print("\nDOWNLOAD DOCUMENTOS ESTRUTURADOS CVM")
        print("=" * 60)
        
        estatisticas = {
            'total_baixados': 0,
            'total_existentes': 0,
            'total_erros': 0,
            'por_tipo': {}
        }
        
        for tipo in tipos_doc:
            if tipo not in self.URLS_CVM:
                logger.warning(f"Tipo inválido: {tipo}")
                continue
            
            print(f"\nProcessando {tipo}...")
            print("-" * 40)
            
            # Listar arquivos disponíveis
            arquivos_disponiveis = self.listar_arquivos_disponiveis(tipo)
            
            # Filtrar por anos solicitados
            arquivos_filtrados = []
            for arquivo in arquivos_disponiveis:
                for ano in anos:
                    if str(ano) in arquivo:
                        arquivos_filtrados.append(arquivo)
                        break
            
            print(f"{len(arquivos_filtrados)} arquivos para baixar")
            
            # Baixar cada arquivo
            baixados = 0
            existentes = 0
            erros = 0
            
            for arquivo in arquivos_filtrados:
                if self.baixar_arquivo(tipo, arquivo):
                    if (self.pasta_base / tipo / arquivo).exists():
                        baixados += 1
                    else:
                        existentes += 1
                else:
                    erros += 1
                
                # Pequena pausa entre downloads
                time.sleep(1)
            
            # Atualizar estatísticas
            estatisticas['total_baixados'] += baixados
            estatisticas['total_existentes'] += existentes
            estatisticas['total_erros'] += erros
            estatisticas['por_tipo'][tipo] = {
                'baixados': baixados,
                'existentes': existentes,
                'erros': erros,
                'total': len(arquivos_filtrados)
            }
            
            print(f"\n{tipo} concluído: {baixados} baixados, {existentes} já existentes, {erros} erros")
        
        # Salvar relatório
        relatorio = {
            'data_execucao': datetime.now().isoformat(),
            'tipos_documentos': tipos_doc,
            'anos_solicitados': anos,
            'estatisticas': estatisticas,
            'pasta_destino': str(self.pasta_base)
        }
        
        relatorio_path = self.pasta_base / f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(relatorio_path, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)
        
        # Resumo final
        print(f"\n{'='*60}")
        print("RESUMO FINAL")
        print(f"   Total baixados: {estatisticas['total_baixados']}")
        print(f"   Já existentes: {estatisticas['total_existentes']}")
        print(f"   Erros: {estatisticas['total_erros']}")
        print(f"   Pasta destino: {self.pasta_base}")
        print(f"   Relatório: {relatorio_path}")
        
        return relatorio
    
    def extrair_dados_empresa(self, cnpj: str, tipo_doc: str = 'ITR') -> pd.DataFrame:
        """
        Extrai dados de uma empresa específica dos arquivos baixados.
        """
        pasta_tipo = self.pasta_base / tipo_doc
        dados_empresa = []
        
        # Procurar em todos os arquivos extraídos
        for pasta_arquivo in pasta_tipo.glob('*/'):
            if not pasta_arquivo.is_dir():
                continue
            
            # Procurar arquivos CSV dentro
            for arquivo_csv in pasta_arquivo.glob('*.csv'):
                try:
                    df = pd.read_csv(arquivo_csv, encoding='latin-1', sep=';')
                    
                    # Filtrar por CNPJ se a coluna existir
                    if 'CNPJ_CIA' in df.columns:
                        df_empresa = df[df['CNPJ_CIA'] == cnpj]
                        if not df_empresa.empty:
                            dados_empresa.append(df_empresa)
                    
                except Exception as e:
                    logger.debug(f"Erro ao ler {arquivo_csv}: {e}")
        
        if dados_empresa:
            return pd.concat(dados_empresa, ignore_index=True)
        else:
            return pd.DataFrame()


def main():
    """
    Interface para download de documentos estruturados.
    """
    print("CVM DOWNLOAD - DOCUMENTOS ESTRUTURADOS")
    print("=" * 60)
    print("\nEste script baixa:")
    print("   ITR - Informações Trimestrais")
    print("   DFP - Demonstrações Financeiras Padronizadas")
    print("   FCA - Formulário Cadastral")
    print("   FRE - Formulário de Referência")
    print("   IPE - Informe de Eventos")
    
    # Tipos de documento
    print("\nCONFIGURAÇÃO:")
    print("\nTipos disponíveis: ITR, DFP, FCA, FRE, IPE")
    print("Digite os tipos separados por vírgula (Enter = ITR,DFP)")
    tipos_input = input("Tipos de documento: ").strip()
    
    if tipos_input:
        tipos = [t.strip().upper() for t in tipos_input.split(',')]
    else:
        tipos = ['ITR', 'DFP']
    
    print(f"\nTipos selecionados: {', '.join(tipos)}")
    
    # Anos
    anos_input = input("\nAnos (ex: 2023,2024,2025) [2024,2025]: ").strip()
    if anos_input:
        anos = [int(a.strip()) for a in anos_input.split(',')]
    else:
        anos = [2024, 2025]
    
    print(f"Anos: {', '.join(map(str, anos))}")
    
    # Confirmar
    print(f"\nRESUMO:")
    print(f"   Tipos: {', '.join(tipos)}")
    print(f"   Anos: {', '.join(map(str, anos))}")
    print(f"   Pasta destino: documents/cvm_estruturados/")
    
    confirmar = input("\nIniciar download? (S/n): ").strip().lower()
    if confirmar == 'n':
        print("[ERRO] Operação cancelada")
        return
    
    # Executar
    downloader = CVMDocumentosEstruturados()
    
    try:
        downloader.baixar_documentos_periodo(
            tipos_doc=tipos,
            anos=anos
        )
        
        print("\nDownload concluído!")
        print("\nDICA: Os arquivos estão organizados em:")
        print("   documents/cvm_estruturados/ITR/")
        print("   documents/cvm_estruturados/DFP/")
        print("   etc...")
        
    except KeyboardInterrupt:
        print("\n\nDownload interrompido pelo usuário")
    except Exception as e:
        print(f"\n[ERRO] Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()