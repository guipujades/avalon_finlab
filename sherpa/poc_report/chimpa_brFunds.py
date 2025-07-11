#!/usr/bin/env python3
"""
chimpa_brFunds - Análise de fundos brasileiros usando dados CVM locais
======================================================================

Este script utiliza os dados já baixados na pasta database para processar
carteiras de fundos brasileiros.

Uso:
    python chimpa_brFunds.py --cnpj "00.000.000/0001-00"
"""

import os
import re
import zipfile
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import pickle
from tqdm import tqdm
import argparse
import json


def limpar_cnpj(cnpj):
    """Remove formatação do CNPJ."""
    return re.sub(r'[^0-9]', '', cnpj)


def processar_arquivo_cda(arquivo_zip, cnpj_limpo):
    """
    Processa um arquivo ZIP de carteira CDA.
    
    Args:
        arquivo_zip (Path): Caminho do arquivo ZIP
        cnpj_limpo (str): CNPJ sem formatação
        
    Returns:
        DataFrame: Carteira processada ou None
    """
    # Extrair período do nome do arquivo
    nome = arquivo_zip.stem
    match = re.search(r'cda_fi_(\d{6})', nome)
    if match:
        periodo = match.group(1)
        data_formatada = f"{periodo[:4]}-{periodo[4:]}"
    else:
        match_anual = re.search(r'cda_fi_(\d{4})', nome)
        if match_anual:
            periodo = match_anual.group(1)
            data_formatada = periodo
        else:
            return None
    
    carteira_completa = []
    
    try:
        with zipfile.ZipFile(arquivo_zip, 'r') as zip_ref:
            # Listar arquivos no ZIP
            arquivos_no_zip = zip_ref.namelist()
            
            # Processar arquivos BLC
            for arquivo in arquivos_no_zip:
                if re.match(r'.*BLC_[1-8].*\.csv$', arquivo):
                    # Ler direto do ZIP
                    with zip_ref.open(arquivo) as f:
                        try:
                            df = pd.read_csv(f, sep=';', encoding='ISO-8859-1')
                            
                            # Filtrar pelo CNPJ (tentar ambos os formatos)
                            cnpj_formatado = f"{cnpj_limpo[:2]}.{cnpj_limpo[2:5]}.{cnpj_limpo[5:8]}/{cnpj_limpo[8:12]}-{cnpj_limpo[12:14]}"
                            
                            df_fundo = df[
                                (df['CNPJ_FUNDO'] == cnpj_limpo) | 
                                (df['CNPJ_FUNDO'] == cnpj_formatado)
                            ].copy()
                            
                            if not df_fundo.empty:
                                # Adicionar informações
                                tipo_blc = re.search(r'BLC_(\d)', arquivo).group(1)
                                df_fundo['TIPO_BLC'] = f'BLC_{tipo_blc}'
                                df_fundo['DATA_CARTEIRA'] = data_formatada
                                df_fundo['PERIODO'] = periodo
                                
                                carteira_completa.append(df_fundo)
                        except Exception as e:
                            continue
                            
        if carteira_completa:
            return pd.concat(carteira_completa, ignore_index=True)
            
    except Exception as e:
        print(f"⚠️ Erro ao processar {arquivo_zip.name}: {e}")
        
    return None


def categorizar_ativos(df_carteira):
    """Categoriza os ativos da carteira."""
    df_carteira['CATEGORIA'] = 'Outros'
    
    # Mapeamento de categorias por tipo BLC
    categorias = {
        'BLC_1': 'Ações',
        'BLC_2': 'Títulos Públicos',
        'BLC_3': 'Renda Fixa Privada',
        'BLC_4': 'Renda Fixa Privada',
        'BLC_5': 'Cotas de Fundos',
        'BLC_6': 'Derivativos',
        'BLC_7': 'Exterior',
        'BLC_8': 'Disponibilidades'
    }
    
    for blc, categoria in categorias.items():
        df_carteira.loc[df_carteira['TIPO_BLC'] == blc, 'CATEGORIA'] = categoria
        
    return df_carteira


def processar_fundo(cnpj, base_dir="/mnt/c/Users/guilh/Documents/GitHub/sherpa/database", anos=10):
    """
    Processa as carteiras de um fundo usando dados locais.
    
    Args:
        cnpj (str): CNPJ do fundo
        base_dir (str): Diretório base dos dados
        anos (int): Número de anos para processar
        
    Returns:
        dict: Carteiras processadas por período
    """
    cnpj_limpo = limpar_cnpj(cnpj)
    base_path = Path(base_dir)
    cda_path = base_path / "CDA"
    
    print(f"\n🔍 Processando fundo CNPJ: {cnpj}")
    print(f"📂 Buscando dados em: {cda_path}")
    
    if not cda_path.exists():
        print(f"❌ Diretório CDA não encontrado: {cda_path}")
        return None
        
    # Encontrar todos os arquivos CDA
    arquivos_cda = []
    for arquivo in cda_path.glob("cda_fi_*.zip"):
        arquivos_cda.append(arquivo)
        
    # Ordenar por data (mais recente primeiro)
    arquivos_cda.sort(reverse=True)
    
    # Limitar por período se necessário
    data_limite = datetime.now().year - anos
    arquivos_filtrados = []
    
    for arquivo in arquivos_cda:
        # Extrair ano do arquivo
        match = re.search(r'cda_fi_(\d{4})', arquivo.stem)
        if match:
            ano = int(match.group(1))
            if ano >= data_limite:
                arquivos_filtrados.append(arquivo)
        else:
            match = re.search(r'cda_fi_(\d{6})', arquivo.stem)
            if match:
                ano = int(match.group(1)[:4])
                if ano >= data_limite:
                    arquivos_filtrados.append(arquivo)
                    
    print(f"📊 {len(arquivos_filtrados)} arquivos encontrados no período")
    
    # Processar arquivos
    carteiras_por_periodo = {}
    arquivos_com_dados = 0
    
    print("\n⏳ Processando carteiras...")
    for arquivo in tqdm(arquivos_filtrados, desc="Arquivos"):
        df_carteira = processar_arquivo_cda(arquivo, cnpj_limpo)
        
        if df_carteira is not None and not df_carteira.empty:
            # Categorizar ativos
            df_carteira = categorizar_ativos(df_carteira)
            
            # Adicionar ao dicionário
            periodo = df_carteira['PERIODO'].iloc[0]
            carteiras_por_periodo[periodo] = df_carteira
            arquivos_com_dados += 1
            
    print(f"\n✅ {arquivos_com_dados} carteiras encontradas para o fundo")
    
    if not carteiras_por_periodo:
        print("❌ Nenhuma carteira encontrada para este CNPJ")
        return None
        
    # Gerar relatório
    gerar_relatorio_resumido(cnpj, carteiras_por_periodo)
    
    return carteiras_por_periodo


def gerar_relatorio_resumido(cnpj, carteiras):
    """Gera um relatório resumido das carteiras."""
    cnpj_limpo = limpar_cnpj(cnpj)
    
    print("\n" + "="*60)
    print("RESUMO DAS CARTEIRAS")
    print("="*60)
    print(f"CNPJ: {cnpj}")
    print(f"Períodos disponíveis: {len(carteiras)}")
    
    if carteiras:
        periodos = sorted(carteiras.keys())
        print(f"Primeiro período: {periodos[0][:4]}-{periodos[0][4:]}")
        print(f"Último período: {periodos[-1][:4]}-{periodos[-1][4:]}")
        
        # Analisar última carteira
        ultimo_periodo = periodos[-1]
        df_ultimo = carteiras[ultimo_periodo]
        
        print(f"\n📊 Composição da última carteira ({ultimo_periodo[:4]}-{ultimo_periodo[4:]}):")
        print("-" * 40)
        
        # Agrupar por categoria
        if 'VL_MERC_POS_FINAL' in df_ultimo.columns:
            resumo = df_ultimo.groupby('CATEGORIA')['VL_MERC_POS_FINAL'].sum().sort_values(ascending=False)
            total = resumo.sum()
            
            for categoria, valor in resumo.items():
                percentual = (valor / total) * 100 if total > 0 else 0
                print(f"{categoria:.<25} R$ {valor:>15,.2f} ({percentual:>5.1f}%)")
                
            print("-" * 40)
            print(f"{'TOTAL':.<25} R$ {total:>15,.2f}")
            
        # Salvar resumo em CSV
        output_file = f"resumo_carteiras_{cnpj_limpo}.csv"
        
        # Criar DataFrame consolidado
        consolidado = []
        for periodo, df in carteiras.items():
            if 'VL_MERC_POS_FINAL' in df.columns:
                resumo_periodo = df.groupby('CATEGORIA')['VL_MERC_POS_FINAL'].sum().reset_index()
                resumo_periodo['PERIODO'] = f"{periodo[:4]}-{periodo[4:]}"
                resumo_periodo['PERCENTUAL'] = resumo_periodo['VL_MERC_POS_FINAL'] / resumo_periodo['VL_MERC_POS_FINAL'].sum() * 100
                consolidado.append(resumo_periodo)
                
        if consolidado:
            df_consolidado = pd.concat(consolidado, ignore_index=True)
            df_consolidado.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"\n💾 Resumo salvo em: {output_file}")


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description='Análise de fundos brasileiros usando dados CVM locais'
    )
    parser.add_argument('--cnpj', type=str, required=True, 
                       help='CNPJ do fundo (formato: 00.000.000/0001-00)')
    parser.add_argument('--anos', type=int, default=10,
                       help='Número de anos para análise (padrão: 10)')
    parser.add_argument('--base-dir', type=str, 
                       default="/mnt/c/Users/guilh/Documents/GitHub/sherpa/database",
                       help='Diretório base dos dados')
    
    args = parser.parse_args()
    
    print(f"\n🚀 CHIMPA BR FUNDS - Análise de Fundos")
    print("=" * 50)
    
    # Processar fundo
    carteiras = processar_fundo(args.cnpj, args.base_dir, args.anos)
    
    if carteiras:
        print("\n✅ Processamento concluído!")
        
        # Salvar carteiras em pickle para uso posterior
        cnpj_limpo = limpar_cnpj(args.cnpj)
        with open(f"carteiras_{cnpj_limpo}.pkl", 'wb') as f:
            pickle.dump(carteiras, f)
            print(f"💾 Carteiras salvas em: carteiras_{cnpj_limpo}.pkl")
    else:
        print("\n❌ Nenhum dado encontrado para o fundo")
        

if __name__ == "__main__":
    main()