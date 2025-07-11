#!/usr/bin/env python3
"""
Download de Releases de Resultados Trimestrais
==============================================
Script especializado para baixar apenas os releases de resultados trimestrais
das empresas listadas na CVM.
"""

from cvm_extractor_complete import CVMCompleteDocumentExtractor
from cvm_document_downloader import CVMDocumentDownloader
import json
import re
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd


class ReleasesTrimestralDownloader:
    """
    Classe especializada para download de releases de resultados trimestrais.
    """
    
    def __init__(self, pasta_destino: str = "releases_trimestrais"):
        self.extractor = CVMCompleteDocumentExtractor()
        self.downloader = CVMDocumentDownloader(pasta_destino)
        self.pasta_destino = pasta_destino
        
        # Padrões para identificar releases de resultados
        self.padroes_resultado = [
            r'resultado.*\d{1}t\d{2}',
            r'itr.*\d{1}t',
            r'release.*result',
            r'divulgação.*resultado',
            r'earnings.*release',
            r'\d{1}t\d{2}.*resultado',
            r'resultado.*trimestre',
            r'resultado.*trimestral',
            r'desempenho.*\d{1}t\d{2}',
            r'demonstrações.*\d{1}t\d{2}'
        ]
        
        # Palavras-chave adicionais
        self.palavras_chave = [
            'resultado', 'trimestre', 'itr', 'trimestral',
            '1t', '2t', '3t', '4t', 'release', 'earnings',
            'divulgação', 'desempenho', 'demonstrações'
        ]
    
    def identificar_release_resultado(self, documento: Dict) -> bool:
        """
        Identifica se um documento é um release de resultado trimestral.
        """
        assunto = documento.get('assunto', '')
        if not assunto or not isinstance(assunto, str):
            return False
        
        assunto = assunto.lower()
        
        # Verificar padrões regex
        for padrao in self.padroes_resultado:
            if re.search(padrao, assunto):
                return True
        
        # Verificar combinações de palavras-chave
        tem_resultado = any(palavra in assunto for palavra in ['resultado', 'result', 'earnings', 'desempenho'])
        tem_trimestre = any(palavra in assunto for palavra in ['1t', '2t', '3t', '4t', 'trimestre', 'trimestral', 'itr'])
        
        return tem_resultado and tem_trimestre
    
    def filtrar_releases_resultados(self, documentos: Dict) -> List[Dict]:
        """
        Filtra apenas os releases de resultados trimestrais.
        """
        releases_resultados = []
        
        # Verificar nos fatos relevantes
        for doc in documentos.get('fatos_relevantes', []):
            if self.identificar_release_resultado(doc):
                doc['origem'] = 'fato_relevante'
                releases_resultados.append(doc)
        
        # Verificar nos comunicados
        for doc in documentos.get('comunicados', []):
            if self.identificar_release_resultado(doc):
                doc['origem'] = 'comunicado'
                releases_resultados.append(doc)
        
        # Ordenar por data de entrega (mais recente primeiro)
        releases_resultados.sort(key=lambda x: x.get('data_entrega', ''), reverse=True)
        
        return releases_resultados
    
    def extrair_periodo_resultado(self, assunto: str) -> Optional[str]:
        """
        Extrai o período do resultado (1T24, 2T24, etc) do assunto.
        """
        if not assunto or not isinstance(assunto, str):
            return None
            
        # Padrões para encontrar períodos
        padroes_periodo = [
            r'(\d{1}t\d{2,4})',
            r'(\d{1}).*trimestre.*(\d{4})',
            r'trimestre.*(\d{4})'
        ]
        
        assunto_lower = assunto.lower()
        
        for padrao in padroes_periodo:
            match = re.search(padrao, assunto_lower)
            if match:
                return match.group(0)
        
        return None
    
    def baixar_releases_empresa(self, empresa: str, year: int = 2024, 
                               limite: Optional[int] = None) -> Dict:
        """
        Baixa os releases de resultados de uma empresa específica.
        """
        print(f"\n📊 Processando releases de {empresa} - {year}")
        print("=" * 50)
        
        # Extrair todos os documentos
        print("📥 Extraindo metadados...")
        documentos = self.extractor.extract_company_documents(empresa, year)
        
        if not documentos:
            print(f"❌ Nenhum documento encontrado para {empresa}")
            return {'empresa': empresa, 'releases': [], 'downloads': {}}
        
        # Filtrar apenas releases de resultados
        releases = self.filtrar_releases_resultados(documentos)
        
        print(f"✅ Encontrados {len(releases)} releases de resultados")
        
        if not releases:
            return {'empresa': empresa, 'releases': [], 'downloads': {}}
        
        # Mostrar releases encontrados
        print("\n📋 Releases identificados:")
        for i, release in enumerate(releases[:limite] if limite else releases):
            periodo = self.extrair_periodo_resultado(release['assunto']) or "N/A"
            print(f"   {i+1}. {release['data_entrega'][:10]} - {periodo}")
            print(f"      📄 {release['assunto'][:60]}...")
            print(f"      📍 Origem: {release['origem']}")
        
        # Preparar para download
        docs_para_download = {
            'releases_resultados': releases[:limite] if limite else releases
        }
        
        # Fazer download
        print(f"\n💾 Baixando {len(docs_para_download['releases_resultados'])} releases...")
        resultado_download = self.downloader.download_company_documents(
            docs_para_download,
            empresa,
            tipos_documento=['releases_resultados']
        )
        
        return {
            'empresa': empresa,
            'releases': releases,
            'downloads': resultado_download
        }
    
    def baixar_multiplas_empresas(self, empresas: List[str], 
                                 year: int = 2024, 
                                 limite_por_empresa: int = 4) -> Dict:
        """
        Baixa releases de múltiplas empresas.
        """
        print("🏭 DOWNLOAD DE RELEASES TRIMESTRAIS - MÚLTIPLAS EMPRESAS")
        print("=" * 60)
        
        resultados = {}
        total_downloads = 0
        total_erros = 0
        
        for i, empresa in enumerate(empresas, 1):
            print(f"\n[{i}/{len(empresas)}] Processando {empresa}")
            
            resultado = self.baixar_releases_empresa(empresa, year, limite_por_empresa)
            resultados[empresa] = resultado
            
            # Estatísticas
            if resultado['downloads']:
                stats = resultado['downloads'].get('estatisticas', {})
                total_downloads += stats.get('downloads_sucesso', 0)
                total_erros += stats.get('downloads_erro', 0)
        
        # Resumo final
        print("\n" + "=" * 60)
        print("📊 RESUMO FINAL")
        print(f"   🏢 Empresas processadas: {len(empresas)}")
        print(f"   ✅ Downloads bem-sucedidos: {total_downloads}")
        print(f"   ❌ Downloads com erro: {total_erros}")
        
        return resultados
    
    def gerar_relatorio_releases(self, resultados: Dict, arquivo: str = None):
        """
        Gera relatório detalhado dos releases baixados.
        """
        if not arquivo:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            arquivo = f"relatorio_releases_{timestamp}.json"
        
        relatorio = {
            'data_geracao': datetime.now().isoformat(),
            'empresas_processadas': len(resultados),
            'total_releases_identificados': sum(len(r['releases']) for r in resultados.values()),
            'detalhes_por_empresa': {}
        }
        
        for empresa, dados in resultados.items():
            relatorio['detalhes_por_empresa'][empresa] = {
                'releases_encontrados': len(dados['releases']),
                'releases': [
                    {
                        'data': r['data_entrega'],
                        'assunto': r['assunto'],
                        'periodo': self.extrair_periodo_resultado(r['assunto']),
                        'origem': r['origem'],
                        'link': r['link_download']
                    }
                    for r in dados['releases']
                ]
            }
        
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)
        
        print(f"\n📝 Relatório salvo em: {arquivo}")
        return arquivo


def exemplo_uso_basico():
    """
    Exemplo básico de uso do downloader de releases.
    """
    print("🎯 EXEMPLO: Download de Releases Trimestrais")
    print("=" * 45)
    
    # Criar instância do downloader
    downloader = ReleasesTrimestralDownloader("documents/releases_trimestrais")
    
    # Baixar releases de uma empresa
    empresa = "PETROBRAS"
    print(f"\n📊 Baixando releases de {empresa}...")
    
    resultado = downloader.baixar_releases_empresa(
        empresa=empresa,
        year=2024,
        limite=4  # Últimos 4 releases (geralmente 1 ano)
    )
    
    # Gerar relatório
    downloader.gerar_relatorio_releases({empresa: resultado})
    
    return resultado


def exemplo_multiplas_empresas():
    """
    Exemplo com múltiplas empresas.
    """
    print("🏭 EXEMPLO: Múltiplas Empresas")
    print("=" * 35)
    
    # Lista de empresas
    empresas = ["VALE", "PETROBRAS", "ITAU", "AMBEV"]
    
    downloader = ReleasesTrimestralDownloader("documents/releases_trimestrais")
    
    # Baixar releases
    resultados = downloader.baixar_multiplas_empresas(
        empresas=empresas,
        year=2024,
        limite_por_empresa=2  # 2 últimos releases de cada
    )
    
    # Gerar relatório consolidado
    downloader.gerar_relatorio_releases(resultados)
    
    return resultados


def exemplo_analise_releases():
    """
    Exemplo de análise de releases sem download.
    """
    print("📊 EXEMPLO: Análise de Releases (sem download)")
    print("=" * 45)
    
    downloader = ReleasesTrimestralDownloader()
    empresa = "B3"
    
    # Extrair documentos
    print(f"\n🔍 Analisando releases de {empresa}...")
    documentos = downloader.extractor.extract_company_documents(empresa, 2024)
    
    if documentos:
        # Filtrar releases
        releases = downloader.filtrar_releases_resultados(documentos)
        
        print(f"\n✅ Encontrados {len(releases)} releases de resultados")
        
        # Criar DataFrame para análise
        if releases:
            df_releases = pd.DataFrame(releases)
            
            print("\n📈 Análise dos releases:")
            print(f"   Período: {df_releases['data_entrega'].min()[:10]} a {df_releases['data_entrega'].max()[:10]}")
            print(f"   Origem: {df_releases['origem'].value_counts().to_dict()}")
            
            # Extrair períodos
            df_releases['periodo'] = df_releases['assunto'].apply(
                downloader.extrair_periodo_resultado
            )
            
            print("\n📅 Períodos identificados:")
            for _, row in df_releases.iterrows():
                print(f"   {row['data_entrega'][:10]} - {row['periodo'] or 'N/A'}")
                print(f"      {row['assunto'][:70]}...")
    
    return releases if 'releases' in locals() else []


def download_interativo():
    """
    Download interativo com escolha de empresa e período.
    """
    print("📊 DOWNLOAD INTERATIVO DE RELEASES TRIMESTRAIS")
    print("=" * 50)
    
    # Escolher empresa
    empresa = input("\n🏢 Digite o nome ou código da empresa (ex: PETROBRAS, VALE, ITAU): ").strip().upper()
    if not empresa:
        print("❌ Nome da empresa é obrigatório")
        return
    
    # Escolher ano
    ano_atual = datetime.now().year
    print(f"\n📅 Escolha o ano (Enter para {ano_atual}):")
    ano_str = input(f"   Ano [{ano_atual}]: ").strip()
    ano = int(ano_str) if ano_str.isdigit() else ano_atual
    
    # Escolher período específico
    print("\n📆 Escolha o período:")
    print("   1. Ano completo (todos os trimestres)")
    print("   2. Trimestre específico")
    print("   3. Últimos N releases")
    
    opcao_periodo = input("👉 Opção (1-3): ").strip()
    
    trimestres_filtro = None
    limite = None
    
    if opcao_periodo == "2":
        print("\n🗓️  Escolha o(s) trimestre(s):")
        print("   1. 1T (primeiro trimestre)")
        print("   2. 2T (segundo trimestre)")
        print("   3. 3T (terceiro trimestre)")
        print("   4. 4T (quarto trimestre)")
        print("   Múltiplos: separe por vírgula (ex: 1,3)")
        
        trimestres_input = input("👉 Trimestre(s): ").strip()
        trimestres_selecionados = [f"{t.strip()}T" for t in trimestres_input.split(",") if t.strip()]
        trimestres_filtro = trimestres_selecionados
    
    elif opcao_periodo == "3":
        limite_str = input("📊 Quantos releases baixar? [4]: ").strip()
        limite = int(limite_str) if limite_str.isdigit() else 4
    
    # Criar downloader
    downloader = ReleasesTrimestralDownloader("documents/releases_trimestrais")
    
    # Processar
    print(f"\n🔍 Buscando releases de {empresa} - {ano}")
    print("Por favor aguarde...")
    
    # Extrair documentos
    documentos = downloader.extractor.extract_company_documents(empresa, ano)
    
    if not documentos:
        print(f"❌ Nenhum documento encontrado para {empresa}")
        return
    
    # Filtrar releases
    releases = downloader.filtrar_releases_resultados(documentos)
    
    if not releases:
        print(f"❌ Nenhum release de resultado encontrado para {empresa} em {ano}")
        return
    
    # Aplicar filtro de trimestres se especificado
    if trimestres_filtro:
        releases_filtrados = []
        for release in releases:
            assunto_lower = release['assunto'].lower()
            for trimestre in trimestres_filtro:
                if trimestre.lower() in assunto_lower:
                    releases_filtrados.append(release)
                    break
        releases = releases_filtrados
    
    # Aplicar limite se especificado
    if limite:
        releases = releases[:limite]
    
    print(f"\n✅ Encontrados {len(releases)} releases para download")
    
    if not releases:
        print("❌ Nenhum release corresponde aos critérios selecionados")
        return
    
    # Mostrar releases que serão baixados
    print("\n📋 Releases a serem baixados:")
    for i, release in enumerate(releases, 1):
        periodo = downloader.extrair_periodo_resultado(release['assunto']) or "N/A"
        print(f"   {i}. {release['data_entrega'][:10]} - {periodo}")
        print(f"      📄 {release['assunto'][:60]}...")
    
    # Confirmar download
    confirma = input("\n💾 Confirma o download? (S/n): ").strip().lower()
    if confirma == 'n':
        print("❌ Download cancelado")
        return
    
    # Preparar para download
    docs_para_download = {'releases_resultados': releases}
    
    # Fazer download
    print(f"\n💾 Baixando {len(releases)} releases...")
    resultado_download = downloader.downloader.download_company_documents(
        docs_para_download,
        empresa,
        tipos_documento=['releases_resultados']
    )
    
    # Estatísticas
    if resultado_download:
        stats = resultado_download.get('estatisticas', {})
        print(f"\n✅ Downloads concluídos:")
        print(f"   📥 Sucesso: {stats.get('downloads_sucesso', 0)}")
        print(f"   ❌ Erros: {stats.get('downloads_erro', 0)}")
        print(f"   📁 Já existentes: {stats.get('arquivos_existentes', 0)}")
    
    # Gerar relatório
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    relatorio_arquivo = f"relatorio_{empresa}_{timestamp}.json"
    downloader.gerar_relatorio_releases({empresa: {'releases': releases, 'downloads': resultado_download}}, relatorio_arquivo)
    
    print(f"\n📁 Arquivos salvos em: documents/releases_trimestrais/{empresa}/")
    
    return resultado_download


def main():
    """
    Menu principal.
    """
    print("📊 SISTEMA DE DOWNLOAD DE RELEASES TRIMESTRAIS")
    print("=" * 50)
    print("\nEscolha uma opção:")
    print("1. 📥 Download interativo (escolha empresa e período)")
    print("2. 📊 Apenas análise (sem download)")
    print("3. ❌ Sair")
    
    opcao = input("\n👉 Escolha (1-3): ").strip()
    
    if opcao == "1":
        download_interativo()
    elif opcao == "2":
        exemplo_analise_releases()
    elif opcao == "3":
        print("👋 Até logo!")
    else:
        print("❌ Opção inválida")


if __name__ == "__main__":
    main()