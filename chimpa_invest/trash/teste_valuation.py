#!/usr/bin/env python3
"""
Teste de Valuation - Verificação de Dados
=========================================
Script para testar se os dados CVM estão corretos antes de rodar a análise completa.
"""

import pandas as pd
from pathlib import Path
import sys

def verificar_estrutura_pastas():
    """Verifica se as pastas necessárias existem."""
    print("🔍 VERIFICANDO ESTRUTURA DE PASTAS...")
    print("=" * 60)
    
    pastas_necessarias = [
        'documents',
        'documents/cvm_estruturados',
        'documents/cvm_estruturados/ITR',
        'documents/cvm_estruturados/ITR/itr_cia_aberta_2025'
    ]
    
    todas_existem = True
    for pasta in pastas_necessarias:
        path = Path(pasta)
        if path.exists():
            print(f"✅ {pasta}")
        else:
            print(f"❌ {pasta} - NÃO EXISTE")
            todas_existem = False
    
    return todas_existem

def verificar_arquivos_csv():
    """Verifica se os arquivos CSV necessários existem."""
    print("\n🔍 VERIFICANDO ARQUIVOS CSV...")
    print("=" * 60)
    
    base_path = Path('documents/cvm_estruturados/ITR/itr_cia_aberta_2025')
    
    arquivos_necessarios = {
        'BPA': 'itr_cia_aberta_BPA_con_2025.csv',
        'BPP': 'itr_cia_aberta_BPP_con_2025.csv',
        'DRE': 'itr_cia_aberta_DRE_con_2025.csv',
        'DFC': 'itr_cia_aberta_DFC_MD_con_2025.csv'
    }
    
    arquivos_encontrados = {}
    
    for tipo, arquivo in arquivos_necessarios.items():
        caminho_completo = base_path / arquivo
        if caminho_completo.exists():
            tamanho = caminho_completo.stat().st_size / 1024  # KB
            print(f"✅ {tipo}: {arquivo} ({tamanho:.1f} KB)")
            arquivos_encontrados[tipo] = caminho_completo
        else:
            print(f"❌ {tipo}: {arquivo} - NÃO ENCONTRADO")
    
    return arquivos_encontrados

def verificar_dados_vale(arquivos):
    """Verifica se existem dados da VALE nos arquivos."""
    print("\n🔍 VERIFICANDO DADOS DA VALE (CVM: 4170)...")
    print("=" * 60)
    
    CODIGO_CVM_VALE = 4170
    dados_vale = {}
    
    for tipo, caminho in arquivos.items():
        try:
            # Ler primeiras linhas para verificar estrutura
            df = pd.read_csv(caminho, encoding='latin-1', sep=';', nrows=1000)
            
            print(f"\n📄 {tipo}:")
            print(f"   Total de linhas (amostra): {len(df)}")
            print(f"   Colunas: {', '.join(df.columns[:5])}...")
            
            # Verificar dados da VALE
            if 'CD_CVM' in df.columns:
                vale_data = df[df['CD_CVM'] == CODIGO_CVM_VALE]
                if not vale_data.empty:
                    print(f"   ✅ Dados da VALE encontrados: {len(vale_data)} registros")
                    
                    # Mostrar datas disponíveis
                    if 'DT_REFER' in vale_data.columns:
                        datas = vale_data['DT_REFER'].unique()
                        print(f"   📅 Datas: {', '.join(sorted(datas)[:3])}...")
                    
                    dados_vale[tipo] = True
                else:
                    print(f"   ❌ Nenhum dado da VALE encontrado")
                    dados_vale[tipo] = False
            else:
                print(f"   ❌ Coluna CD_CVM não encontrada")
                dados_vale[tipo] = False
                
        except Exception as e:
            print(f"   ❌ Erro ao ler arquivo: {e}")
            dados_vale[tipo] = False
    
    return dados_vale

def testar_analise_simples():
    """Tenta fazer uma análise simples com os dados."""
    print("\n🔍 TESTE DE ANÁLISE SIMPLES...")
    print("=" * 60)
    
    try:
        # Tentar carregar balanço patrimonial
        bpa_path = Path('documents/cvm_estruturados/ITR/itr_cia_aberta_2025/itr_cia_aberta_BPA_con_2025.csv')
        
        if bpa_path.exists():
            df_bpa = pd.read_csv(bpa_path, encoding='latin-1', sep=';', decimal=',')
            vale_bpa = df_bpa[df_bpa['CD_CVM'] == 4170]
            
            if not vale_bpa.empty:
                # Pegar ativo total
                ativo_total = vale_bpa[vale_bpa['CD_CONTA'] == '1']
                if not ativo_total.empty:
                    ultima_data = ativo_total['DT_REFER'].max()
                    valor = ativo_total[ativo_total['DT_REFER'] == ultima_data]['VL_CONTA'].iloc[0]
                    print(f"✅ Ativo Total VALE em {ultima_data}: R$ {valor/1000000:,.1f} milhões")
                else:
                    print("❌ Não encontrou conta do Ativo Total")
            else:
                print("❌ Sem dados da VALE no balanço")
        
    except Exception as e:
        print(f"❌ Erro no teste de análise: {e}")

def main():
    """Função principal de teste."""
    print("🧪 TESTE DO SISTEMA DE VALUATION - VALE")
    print("=" * 60)
    
    # 1. Verificar estrutura
    if not verificar_estrutura_pastas():
        print("\n❌ ERRO: Estrutura de pastas incompleta!")
        print("Execute primeiro: python cvm_download_principal.py")
        return
    
    # 2. Verificar arquivos
    arquivos = verificar_arquivos_csv()
    if not arquivos:
        print("\n❌ ERRO: Arquivos CSV não encontrados!")
        print("Execute primeiro o download de ITR no menu principal")
        return
    
    # 3. Verificar dados da VALE
    dados_vale = verificar_dados_vale(arquivos)
    if not any(dados_vale.values()):
        print("\n❌ ERRO: Nenhum dado da VALE encontrado!")
        print("Possível causa: ITR 2025 ainda não tem dados")
        return
    
    # 4. Teste simples
    testar_analise_simples()
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📊 RESUMO DO TESTE:")
    
    if all(dados_vale.values()):
        print("✅ TODOS OS DADOS NECESSÁRIOS ESTÃO DISPONÍVEIS!")
        print("\nPróximo passo:")
        print("   python valuation_vale_completo.py")
    else:
        print("⚠️  ALGUNS DADOS ESTÃO FALTANDO")
        print("\nDados encontrados:")
        for tipo, encontrado in dados_vale.items():
            status = "✅" if encontrado else "❌"
            print(f"   {status} {tipo}")
        
        print("\nPossíveis soluções:")
        print("1. Tente baixar ITR de 2024 ao invés de 2025")
        print("2. Verifique se a VALE tem dados publicados para o período")

if __name__ == "__main__":
    main()