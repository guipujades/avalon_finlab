#!/usr/bin/env python3
"""
SISTEMA COMPLETO CVM - EXTRAÇÃO + DOWNLOAD
==========================================

Sistema unificado que:
1. Extrai metadados dos documentos
2. Baixa os arquivos reais (PDFs) para sua máquina
3. Organiza tudo em pastas estruturadas

Interface interativa completa com download automático.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import json

# Importar módulos necessários
try:
    from cvm_extractor_complete import CVMCompleteDocumentExtractor
    from cvm_document_downloader import CVMDocumentDownloader
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    print("Verifique se todos os arquivos estão no mesmo diretório")
    sys.exit(1)

class CVMCompleteSystem:
    """
    Sistema completo CVM: Extração + Download
    """
    
    def __init__(self, download_dir: str = "documentos_cvm_completos"):
        """
        Inicializa o sistema completo.
        """
        self.extractor = CVMCompleteDocumentExtractor()
        self.downloader = CVMDocumentDownloader(download_dir)
        self.download_dir = Path(download_dir)
        
        print(f"🚀 Sistema CVM Completo inicializado")
        print(f"📁 Documentos serão salvos em: {self.download_dir.absolute()}")
    
    def extract_and_download_company(self, empresa: str, year: int = 2024,
                                   tipos_documento: list = None,
                                   limite_por_tipo: int = None,
                                   baixar_arquivos: bool = True) -> dict:
        """
        Extrai metadados E baixa documentos de uma empresa.
        
        Args:
            empresa: Nome da empresa
            year: Ano dos documentos
            tipos_documento: Tipos a processar
            limite_por_tipo: Limite por tipo
            baixar_arquivos: Se deve baixar os arquivos
            
        Returns:
            Dict com metadados e resultados de download
        """
        print(f"\n🔍 PROCESSANDO: {empresa} ({year})")
        print("=" * 50)
        
        # 1. Extrair metadados
        print("📊 Fase 1: Extraindo metadados...")
        docs = self.extractor.extract_company_documents(empresa, year=year)
        
        if not docs:
            print(f"❌ Nenhum documento encontrado para {empresa}")
            return None
        
        # Estatísticas dos metadados
        total_docs = sum(len(d) if isinstance(d, list) else 0 for d in docs.values())
        print(f"✅ Metadados extraídos: {total_docs} documentos")
        print(f"   📄 ITRs: {len(docs['documentos_estruturados'])}")
        print(f"   🚨 Fatos relevantes: {len(docs['fatos_relevantes'])}")
        print(f"   📢 Comunicados: {len(docs['comunicados'])}")
        print(f"   🏛️ Assembleias: {len(docs['assembleias'])}")
        
        resultado = {
            'empresa': empresa,
            'ano': year,
            'metadados': docs,
            'downloads': None
        }
        
        # 2. Baixar arquivos se solicitado
        if baixar_arquivos and total_docs > 0:
            print(f"\n📥 Fase 2: Baixando arquivos...")
            
            download_result = self.downloader.download_company_documents(
                docs, empresa, tipos_documento, limite_por_tipo
            )
            
            resultado['downloads'] = download_result
            
            # Salvar relatório
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"relatorio_{empresa.lower()}_{timestamp}.json"
            self.downloader.save_download_report(download_result, report_file)
        
        return resultado
    
    def extract_and_download_multiple(self, empresas: list, year: int = 2024,
                                    tipos_documento: list = None,
                                    limite_por_empresa: int = None,
                                    baixar_arquivos: bool = True) -> dict:
        """
        Processa múltiplas empresas com extração e download.
        """
        print(f"\n🏭 PROCESSAMENTO EM LOTE: {len(empresas)} empresas")
        print("=" * 60)
        
        resultados = {
            'inicio': datetime.now().isoformat(),
            'empresas': {},
            'estatisticas': {
                'total_empresas': len(empresas),
                'processadas_sucesso': 0,
                'processadas_erro': 0,
                'total_documentos': 0,
                'total_downloads': 0
            }
        }
        
        for i, empresa in enumerate(empresas, 1):
            print(f"\n📊 Empresa {i}/{len(empresas)}: {empresa}")
            print("-" * 40)
            
            try:
                resultado = self.extract_and_download_company(
                    empresa, year, tipos_documento, limite_por_empresa, baixar_arquivos
                )
                
                if resultado:
                    resultados['empresas'][empresa] = resultado
                    resultados['estatisticas']['processadas_sucesso'] += 1
                    
                    # Contar documentos
                    total_docs = sum(len(d) if isinstance(d, list) else 0 
                                   for d in resultado['metadados'].values())
                    resultados['estatisticas']['total_documentos'] += total_docs
                    
                    # Contar downloads se houver
                    if resultado['downloads']:
                        downloads = resultado['downloads']['estatisticas']['downloads_sucesso']
                        resultados['estatisticas']['total_downloads'] += downloads
                else:
                    resultados['estatisticas']['processadas_erro'] += 1
                    
            except Exception as e:
                print(f"❌ Erro ao processar {empresa}: {e}")
                resultados['empresas'][empresa] = {'erro': str(e)}
                resultados['estatisticas']['processadas_erro'] += 1
        
        resultados['fim'] = datetime.now().isoformat()
        
        # Relatório final
        print(f"\n{'='*60}")
        print(f"📊 RELATÓRIO FINAL DO PROCESSAMENTO")
        print(f"{'='*60}")
        print(f"🏢 Empresas processadas: {resultados['estatisticas']['processadas_sucesso']}/{len(empresas)}")
        print(f"📄 Total de documentos: {resultados['estatisticas']['total_documentos']}")
        print(f"📥 Total de downloads: {resultados['estatisticas']['total_downloads']}")
        
        # Salvar relatório geral
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.download_dir / f"relatorio_geral_{timestamp}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"📄 Relatório geral salvo: {report_path}")
        
        return resultados
    
    def interface_interativa(self):
        """
        Interface interativa para o sistema completo.
        """
        print("\n" + "="*70)
        print("🚀 SISTEMA COMPLETO CVM - EXTRAÇÃO + DOWNLOAD AUTOMÁTICO")
        print("="*70)
        print("Extrai metadados E baixa os arquivos reais (PDFs) para sua máquina")
        print("="*70)
        
        while True:
            print("\n📋 OPÇÕES DISPONÍVEIS:")
            print("1. 🏢 Processar empresa específica (metadados + download)")
            print("2. 🏭 Processar múltiplas empresas")
            print("3. 📊 Apenas extrair metadados (sem download)")
            print("4. 📥 Apenas baixar de metadados existentes")
            print("5. 📁 Listar arquivos baixados")
            print("6. 📈 Estatísticas de downloads")
            print("7. ⚙️ Configurações")
            print("8. ❌ Sair")
            
            try:
                opcao = input("\n👉 Escolha uma opção (1-8): ").strip()
                
                if opcao == "1":
                    self._interface_empresa_completa()
                elif opcao == "2":
                    self._interface_multiplas_completa()
                elif opcao == "3":
                    self._interface_apenas_metadados()
                elif opcao == "4":
                    self._interface_apenas_download()
                elif opcao == "5":
                    self._interface_listar_arquivos()
                elif opcao == "6":
                    self._interface_estatisticas()
                elif opcao == "7":
                    self._interface_configuracoes()
                elif opcao == "8":
                    print("\n👋 Obrigado por usar o Sistema CVM Completo!")
                    break
                else:
                    print("❌ Opção inválida. Tente novamente.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Saindo...")
                break
            except Exception as e:
                print(f"\n❌ Erro: {e}")
    
    def _interface_empresa_completa(self):
        """Interface para processar empresa específica completa"""
        print("\n🏢 PROCESSAMENTO COMPLETO - EMPRESA ESPECÍFICA")
        print("-" * 50)
        
        empresa = input("Digite o nome da empresa: ").strip()
        if not empresa:
            print("❌ Nome da empresa é obrigatório")
            return
        
        try:
            ano = int(input("Ano dos documentos (2024): ") or "2024")
        except ValueError:
            ano = 2024
        
        # Configurar tipos de documento
        print("\n📄 Tipos de documento a processar:")
        print("1. Todos os tipos")
        print("2. Apenas fatos relevantes")
        print("3. Apenas comunicados")
        print("4. Apenas ITRs")
        print("5. Personalizado")
        
        tipo_opcao = input("Escolha (1-5): ").strip()
        
        tipos_documento = None
        if tipo_opcao == "2":
            tipos_documento = ['fatos_relevantes']
        elif tipo_opcao == "3":
            tipos_documento = ['comunicados']
        elif tipo_opcao == "4":
            tipos_documento = ['documentos_estruturados']
        elif tipo_opcao == "5":
            tipos_documento = []
            if input("Incluir fatos relevantes? (s/N): ").lower().startswith('s'):
                tipos_documento.append('fatos_relevantes')
            if input("Incluir comunicados? (s/N): ").lower().startswith('s'):
                tipos_documento.append('comunicados')
            if input("Incluir ITRs? (s/N): ").lower().startswith('s'):
                tipos_documento.append('documentos_estruturados')
            if input("Incluir assembleias? (s/N): ").lower().startswith('s'):
                tipos_documento.append('assembleias')
        
        # Limite de documentos
        limite_str = input("Limite de documentos por tipo (ENTER = sem limite): ").strip()
        limite_por_tipo = int(limite_str) if limite_str.isdigit() else None
        
        # Confirmar download
        baixar = input("Baixar arquivos reais (PDFs)? (S/n): ").lower() != 'n'
        
        # Processar
        resultado = self.extract_and_download_company(
            empresa, ano, tipos_documento, limite_por_tipo, baixar
        )
        
        if resultado:
            print(f"\n✅ Processamento concluído para {empresa}!")
            if baixar:
                downloads = resultado['downloads']['estatisticas']
                print(f"📥 Downloads: {downloads['downloads_sucesso']} sucessos, {downloads['downloads_erro']} erros")
    
    def _interface_multiplas_completa(self):
        """Interface para múltiplas empresas"""
        print("\n🏭 PROCESSAMENTO COMPLETO - MÚLTIPLAS EMPRESAS")
        print("-" * 50)
        
        print("Digite os nomes das empresas (uma por linha).")
        print("Digite 'FIM' quando terminar:")
        
        empresas = []
        while True:
            empresa = input(f"Empresa {len(empresas)+1}: ").strip()
            if empresa.upper() == 'FIM':
                break
            if empresa:
                empresas.append(empresa)
        
        if not empresas:
            print("❌ Nenhuma empresa informada")
            return
        
        # Configurações
        try:
            ano = int(input("Ano dos documentos (2024): ") or "2024")
        except ValueError:
            ano = 2024
        
        limite_str = input("Limite de documentos por empresa (ENTER = sem limite): ").strip()
        limite_por_empresa = int(limite_str) if limite_str.isdigit() else None
        
        baixar = input("Baixar arquivos reais (PDFs)? (S/n): ").lower() != 'n'
        
        # Processar
        self.extract_and_download_multiple(empresas, ano, None, limite_por_empresa, baixar)
    
    def _interface_apenas_metadados(self):
        """Interface para apenas extrair metadados"""
        print("\n📊 APENAS EXTRAÇÃO DE METADADOS")
        print("-" * 40)
        
        empresa = input("Digite o nome da empresa: ").strip()
        if not empresa:
            return
        
        resultado = self.extract_and_download_company(empresa, baixar_arquivos=False)
        
        if resultado:
            # Salvar metadados
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            meta_file = self.download_dir / f"metadados_{empresa.lower()}_{timestamp}.json"
            
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(resultado['metadados'], f, ensure_ascii=False, indent=2, default=str)
            
            print(f"💾 Metadados salvos: {meta_file}")
    
    def _interface_apenas_download(self):
        """Interface para baixar de metadados existentes"""
        print("\n📥 DOWNLOAD DE METADADOS EXISTENTES")
        print("-" * 40)
        
        # Listar arquivos de metadados disponíveis
        meta_files = list(self.download_dir.glob("metadados_*.json"))
        
        if not meta_files:
            print("❌ Nenhum arquivo de metadados encontrado")
            print("Execute primeiro a extração de metadados")
            return
        
        print("Arquivos de metadados disponíveis:")
        for i, file in enumerate(meta_files, 1):
            print(f"{i}. {file.name}")
        
        try:
            escolha = int(input(f"Escolha um arquivo (1-{len(meta_files)}): ")) - 1
            meta_file = meta_files[escolha]
            
            with open(meta_file, 'r', encoding='utf-8') as f:
                docs = json.load(f)
            
            empresa = input("Nome da empresa para organização: ").strip() or "empresa"
            
            resultado = self.downloader.download_company_documents(docs, empresa)
            self.downloader.save_download_report(resultado)
            
        except (ValueError, IndexError, FileNotFoundError) as e:
            print(f"❌ Erro: {e}")
    
    def _interface_listar_arquivos(self):
        """Interface para listar arquivos baixados"""
        print("\n📁 ARQUIVOS BAIXADOS")
        print("-" * 30)
        
        empresa = input("Filtrar por empresa (ENTER = todas): ").strip() or None
        
        arquivos = self.downloader.list_downloaded_files(empresa)
        
        print(f"\n📊 Total: {arquivos['total_arquivos']} arquivos")
        print(f"💾 Tamanho: {arquivos['total_tamanho']:,} bytes ({arquivos['total_tamanho']/1024/1024:.1f} MB)")
        
        if arquivos['arquivos']:
            print(f"\n📋 Últimos 10 arquivos:")
            for arquivo in arquivos['arquivos'][:10]:
                nome = Path(arquivo['arquivo']).name
                tamanho = arquivo['tamanho'] / 1024  # KB
                print(f"   📄 {nome} ({tamanho:.1f} KB) - {arquivo['empresa']}")
    
    def _interface_estatisticas(self):
        """Interface para mostrar estatísticas"""
        print("\n📈 ESTATÍSTICAS DE DOWNLOADS")
        print("-" * 40)
        
        stats = self.downloader.stats
        
        print(f"📊 Estatísticas gerais:")
        print(f"   🎯 Total de tentativas: {stats['total_tentativas']}")
        print(f"   ✅ Downloads bem-sucedidos: {stats['downloads_sucesso']}")
        print(f"   ❌ Downloads com erro: {stats['downloads_erro']}")
        print(f"   📁 Arquivos já existentes: {stats['arquivos_existentes']}")
        print(f"   💾 Total baixado: {stats['bytes_baixados']:,} bytes ({stats['bytes_baixados']/1024/1024:.1f} MB)")
        
        if stats['total_tentativas'] > 0:
            taxa_sucesso = (stats['downloads_sucesso'] / stats['total_tentativas']) * 100
            print(f"   📈 Taxa de sucesso: {taxa_sucesso:.1f}%")
    
    def _interface_configuracoes(self):
        """Interface de configurações"""
        print("\n⚙️ CONFIGURAÇÕES")
        print("-" * 20)
        
        print(f"📁 Diretório de download: {self.download_dir.absolute()}")
        print(f"⏱️ Timeout: {self.downloader.timeout}s")
        print(f"🔄 Max retries: {self.downloader.max_retries}")
        print(f"⏳ Delay entre downloads: {self.downloader.delay_between_downloads}s")
        
        print("\nOpções:")
        print("1. Alterar delay entre downloads")
        print("2. Alterar timeout")
        print("3. Limpar estatísticas")
        print("4. Voltar")
        
        opcao = input("Escolha: ").strip()
        
        if opcao == "1":
            try:
                novo_delay = float(input(f"Novo delay em segundos ({self.downloader.delay_between_downloads}): "))
                self.downloader.delay_between_downloads = novo_delay
                print(f"✅ Delay alterado para {novo_delay}s")
            except ValueError:
                print("❌ Valor inválido")
        elif opcao == "2":
            try:
                novo_timeout = int(input(f"Novo timeout em segundos ({self.downloader.timeout}): "))
                self.downloader.timeout = novo_timeout
                print(f"✅ Timeout alterado para {novo_timeout}s")
            except ValueError:
                print("❌ Valor inválido")
        elif opcao == "3":
            self.downloader.stats = {
                'total_tentativas': 0,
                'downloads_sucesso': 0,
                'downloads_erro': 0,
                'arquivos_existentes': 0,
                'bytes_baixados': 0
            }
            print("✅ Estatísticas limpas")


def main():
    """
    Função principal do sistema completo.
    """
    try:
        # Verificar diretório personalizado
        download_dir = "documentos_cvm_completos"
        if len(sys.argv) > 1:
            download_dir = sys.argv[1]
        
        # Inicializar sistema
        sistema = CVMCompleteSystem(download_dir)
        
        # Executar interface
        sistema.interface_interativa()
        
    except KeyboardInterrupt:
        print("\n\n👋 Sistema interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")


if __name__ == "__main__":
    main()

