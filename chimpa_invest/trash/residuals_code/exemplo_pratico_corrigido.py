#!/usr/bin/env python3
"""
Exemplo Prático Corrigido - Extrator CVM
========================================

Este exemplo mostra como usar o sistema completo de extração CVM
com os módulos corretos do pacote.
"""

# Importação corrigida
from cvm_extractor_complete import CVMCompleteDocumentExtractor
import json
import pandas as pd
from datetime import datetime

def exemplo_empresa_especifica():
    """
    Exemplo de extração de uma empresa específica.
    """
    print("=== EXEMPLO 1: EMPRESA ESPECÍFICA ===\n")
    
    # Inicializar extrator
    extractor = CVMCompleteDocumentExtractor()
    
    # Extrair documentos da Petrobras
    empresa = "PETROBRAS"
    print(f"Extraindo documentos de {empresa}...")
    
    documentos = extractor.extract_company_documents(empresa, year=2024)
    
    if documentos:
        print(f"\n✅ Resultados para {empresa}:")
        print(f"   📄 ITRs: {len(documentos['documentos_estruturados'])}")
        print(f"   🚨 Fatos relevantes: {len(documentos['fatos_relevantes'])}")
        print(f"   📢 Comunicados: {len(documentos['comunicados'])}")
        print(f"   🏛️ Assembleias: {len(documentos['assembleias'])}")
        
        # Mostrar últimos fatos relevantes
        if documentos['fatos_relevantes']:
            print(f"\n📰 Últimos 3 fatos relevantes:")
            for i, fato in enumerate(documentos['fatos_relevantes'][-3:], 1):
                print(f"   {i}. {fato['data_entrega']}: {fato['assunto']}")
        
        # Salvar resultados
        extractor.save_to_json({empresa: documentos}, f"{empresa.lower()}_exemplo.json")
        print(f"\n💾 Dados salvos em: {empresa.lower()}_exemplo.json")
        
        return documentos
    else:
        print(f"❌ Nenhum documento encontrado para {empresa}")
        return None

def exemplo_multiplas_empresas():
    """
    Exemplo de extração de múltiplas empresas.
    """
    print("\n=== EXEMPLO 2: MÚLTIPLAS EMPRESAS ===\n")
    
    extractor = CVMCompleteDocumentExtractor()
    
    # Lista de empresas para testar
    empresas = ["VALE", "B3", "ITAU"]
    
    print(f"Extraindo documentos de {len(empresas)} empresas...")
    
    resultados = {}
    
    for i, empresa in enumerate(empresas, 1):
        print(f"\n📊 {i}/{len(empresas)}: Processando {empresa}...")
        
        try:
            docs = extractor.extract_company_documents(empresa, year=2024)
            
            if docs:
                total_docs = sum(len(d) if isinstance(d, list) else 0 for d in docs.values())
                print(f"   ✅ {total_docs} documentos extraídos")
                
                resultados[empresa] = docs
            else:
                print(f"   ⚠️ Nenhum documento encontrado")
                
        except Exception as e:
            print(f"   ❌ Erro: {e}")
    
    if resultados:
        # Salvar resultados
        extractor.save_to_excel(resultados, "multiplas_empresas_exemplo.xlsx")
        extractor.save_to_json(resultados, "multiplas_empresas_exemplo.json")
        
        print(f"\n💾 Resultados salvos:")
        print(f"   📁 Excel: multiplas_empresas_exemplo.xlsx")
        print(f"   📁 JSON: multiplas_empresas_exemplo.json")
        
        # Estatísticas gerais
        total_geral = sum(
            sum(len(d) if isinstance(d, list) else 0 for d in empresa_docs.values())
            for empresa_docs in resultados.values()
        )
        print(f"\n📊 Total geral: {total_geral} documentos de {len(resultados)} empresas")
    
    return resultados

def exemplo_apenas_fatos_relevantes():
    """
    Exemplo focado apenas em fatos relevantes.
    """
    print("\n=== EXEMPLO 3: APENAS FATOS RELEVANTES ===\n")
    
    extractor = CVMCompleteDocumentExtractor()
    
    # Extrair apenas fatos relevantes da Vale
    empresa = "VALE"
    print(f"Extraindo apenas fatos relevantes de {empresa}...")
    
    # Usar o método direto para ter mais controle
    documentos = extractor.extract_company_documents(empresa, year=2024)
    
    if documentos and documentos['fatos_relevantes']:
        fatos = documentos['fatos_relevantes']
        print(f"\n✅ {len(fatos)} fatos relevantes encontrados")
        
        # Criar DataFrame para análise
        df_fatos = pd.DataFrame(fatos)
        
        # Análise por mês
        if not df_fatos.empty:
            df_fatos['mes'] = pd.to_datetime(df_fatos['data_entrega']).dt.strftime('%Y-%m')
            fatos_por_mes = df_fatos['mes'].value_counts().sort_index()
            
            print(f"\n📊 Fatos relevantes por mês:")
            for mes, count in fatos_por_mes.items():
                print(f"   {mes}: {count} fatos")
            
            # Salvar apenas fatos relevantes
            fatos_data = {
                'empresa': empresa,
                'total_fatos': len(fatos),
                'periodo': '2024',
                'fatos_por_mes': fatos_por_mes.to_dict(),
                'fatos_relevantes': fatos
            }
            
            with open(f"fatos_relevantes_{empresa.lower()}.json", 'w', encoding='utf-8') as f:
                json.dump(fatos_data, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"\n💾 Fatos relevantes salvos em: fatos_relevantes_{empresa.lower()}.json")
            
            # Mostrar alguns exemplos
            print(f"\n📰 Exemplos de fatos relevantes:")
            for i, fato in enumerate(fatos[:3], 1):
                print(f"   {i}. {fato['data_entrega']}: {fato['assunto'][:60]}...")
        
        return fatos
    else:
        print(f"❌ Nenhum fato relevante encontrado para {empresa}")
        return []

def exemplo_busca_com_lista():
    """
    Exemplo usando a lista de empresas para busca.
    """
    print("\n=== EXEMPLO 4: BUSCA COM LISTA DE EMPRESAS ===\n")
    
    try:
        # Tentar carregar lista de empresas
        with open('dados/empresas_cvm_completa.json', 'r', encoding='utf-8') as f:
            empresas_lista = json.load(f)
        
        print(f"✅ Lista carregada: {len(empresas_lista)} empresas")
        
        # Buscar empresas do setor bancário
        bancos = [emp for emp in empresas_lista if 'BANCO' in emp['nome_completo'].upper()]
        
        print(f"\n🏦 Encontrados {len(bancos)} bancos:")
        for i, banco in enumerate(bancos[:5], 1):
            print(f"   {i}. {banco['nome_completo']}")
            print(f"      CNPJ: {banco['cnpj']}, CVM: {banco['codigo_cvm']}")
            print(f"      Documentos: {banco['total_documentos_ipe']} IPE")
            print(f"      Fatos relevantes: {'✅' if banco['tem_fatos_relevantes'] else '❌'}")
        
        # Extrair documentos do primeiro banco com fatos relevantes
        bancos_com_fatos = [b for b in bancos if b['tem_fatos_relevantes']]
        
        if bancos_com_fatos:
            banco_escolhido = bancos_com_fatos[0]
            nome_busca = banco_escolhido['nome_busca']
            
            print(f"\n📊 Extraindo documentos de: {banco_escolhido['nome_completo']}")
            
            extractor = CVMCompleteDocumentExtractor()
            docs = extractor.extract_company_documents(nome_busca, year=2024)
            
            if docs:
                print(f"   ✅ Fatos relevantes: {len(docs['fatos_relevantes'])}")
                print(f"   ✅ Comunicados: {len(docs['comunicados'])}")
                
                return docs
        
    except FileNotFoundError:
        print("❌ Arquivo de lista de empresas não encontrado")
        print("Execute primeiro: python gerador_lista_empresas.py")
        return None
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

def exemplo_analise_dados():
    """
    Exemplo de análise dos dados extraídos.
    """
    print("\n=== EXEMPLO 5: ANÁLISE DE DADOS ===\n")
    
    # Tentar carregar dados já extraídos
    try:
        with open('petrobras_exemplo.json', 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        petrobras_docs = dados['PETROBRAS']
        
        print("📊 Análise dos dados da Petrobras:")
        
        # Análise de fatos relevantes
        fatos = petrobras_docs['fatos_relevantes']
        if fatos:
            df_fatos = pd.DataFrame(fatos)
            
            # Análise temporal
            df_fatos['data'] = pd.to_datetime(df_fatos['data_entrega'])
            df_fatos['mes'] = df_fatos['data'].dt.strftime('%Y-%m')
            
            print(f"\n📰 Fatos relevantes por mês:")
            fatos_mes = df_fatos['mes'].value_counts().sort_index()
            for mes, count in fatos_mes.items():
                print(f"   {mes}: {count} fatos")
            
            # Palavras-chave mais comuns nos assuntos
            assuntos = ' '.join(df_fatos['assunto'].fillna(''))
            palavras_comuns = ['dividendos', 'pagamento', 'resultado', 'produção', 'vendas']
            
            print(f"\n🔍 Análise de palavras-chave:")
            for palavra in palavras_comuns:
                count = assuntos.lower().count(palavra.lower())
                if count > 0:
                    print(f"   '{palavra}': {count} menções")
        
        # Análise de comunicados
        comunicados = petrobras_docs['comunicados']
        if comunicados:
            df_com = pd.DataFrame(comunicados)
            
            # Tipos de comunicados mais comuns
            if 'tipo_doc' in df_com.columns:
                tipos = df_com['tipo_doc'].value_counts()
                print(f"\n📢 Tipos de comunicados:")
                for tipo, count in tipos.head().items():
                    print(f"   {tipo}: {count}")
        
        print(f"\n✅ Análise concluída!")
        
    except FileNotFoundError:
        print("❌ Dados não encontrados. Execute primeiro o exemplo 1.")
    except Exception as e:
        print(f"❌ Erro na análise: {e}")

def main():
    """
    Função principal que executa todos os exemplos.
    """
    print("🚀 EXEMPLOS PRÁTICOS - EXTRATOR CVM")
    print("=" * 50)
    
    try:
        # Exemplo 1: Empresa específica
        docs_petrobras = exemplo_empresa_especifica()
        
        # Exemplo 2: Múltiplas empresas
        docs_multiplas = exemplo_multiplas_empresas()
        
        # Exemplo 3: Apenas fatos relevantes
        fatos_vale = exemplo_apenas_fatos_relevantes()
        
        # Exemplo 4: Busca com lista
        docs_banco = exemplo_busca_com_lista()
        
        # Exemplo 5: Análise de dados
        exemplo_analise_dados()
        
        print("\n" + "=" * 50)
        print("🎉 TODOS OS EXEMPLOS EXECUTADOS COM SUCESSO!")
        print("\n📁 Arquivos gerados:")
        print("   - petrobras_exemplo.json")
        print("   - multiplas_empresas_exemplo.xlsx")
        print("   - multiplas_empresas_exemplo.json")
        print("   - fatos_relevantes_vale.json")
        print("\n💡 Dica: Verifique os arquivos gerados para ver os dados extraídos!")
        
    except KeyboardInterrupt:
        print("\n\n👋 Exemplos interrompidos pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        print("Verifique se todos os arquivos estão no diretório correto.")

if __name__ == "__main__":
    main()

