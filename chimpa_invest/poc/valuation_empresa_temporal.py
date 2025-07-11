#!/usr/bin/env python3
"""
Sistema de Valuation Genérico com Análise Temporal
==================================================
Análise completa de múltiplos, indicadores e rentabilidade
para qualquer empresa listada na CVM com evolução temporal.

Uso:
    python valuation_empresa_temporal.py PETR4
    python valuation_empresa_temporal.py "PETROBRAS"
    python valuation_empresa_temporal.py 9512
"""

import os
import sys
import pickle
import statistics
import numpy as np
import pandas as pd
import datetime as dt
from pathlib import Path
from datetime import date, datetime
import json
import argparse
import matplotlib.pyplot as plt
try:
    plt.style.use('seaborn-v0_8-darkgrid')
except:
    plt.style.use('ggplot')

pd.options.display.float_format = '{:.3f}'.format


class EmpresaInfo:
    """Gerencia informações das empresas disponíveis"""
    
    def __init__(self):
        # Ajustar caminhos para poc
        script_dir = Path(__file__).parent
        self.empresas_path = script_dir / 'empresas_cvm_completa.json'
        self.indice_path = script_dir / 'indice_busca_empresas.json'
        self.empresas = {}
        self.indice = {}
        self._carregar_dados()
    
    def _carregar_dados(self):
        """Carrega dados das empresas"""
        if self.empresas_path.exists():
            with open(self.empresas_path, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                # Converter lista para dicionário indexado por código CVM
                if isinstance(dados, list):
                    self.empresas = {str(emp['codigo_cvm']): emp for emp in dados}
                else:
                    self.empresas = dados
        
        if self.indice_path.exists():
            with open(self.indice_path, 'r', encoding='utf-8') as f:
                self.indice = json.load(f)
    
    def buscar_empresa(self, termo):
        """
        Busca empresa por ticker, nome ou código CVM
        Retorna: dict com informações da empresa ou None
        """
        termo = str(termo).upper().strip()
        
        # Usar o sistema de busca inteligente
        from buscar_empresa_cvm import BuscadorEmpresasCVM
        
        try:
            buscador = BuscadorEmpresasCVM()
            resultados = buscador.buscar(termo)
            
            if resultados:
                # Se encontrou múltiplos, pegar o com mais documentos
                if len(resultados) > 1:
                    resultados.sort(key=lambda x: x.get('total_documentos_ipe', 0), reverse=True)
                
                # Converter formato para compatibilidade
                empresa = resultados[0]
                return {
                    'codigo_cvm': empresa['codigo_cvm'],
                    'cnpj': empresa['cnpj'],
                    'nome_pregao': empresa['nome_completo'],
                    'ticker': termo if termo in ['BBAS3', 'PETR4', 'VALE3', 'ITUB4'] else None
                }
        except:
            pass
        
        # Fallback: busca manual
        for codigo, info in self.empresas.items():
            nome = info.get('nome_completo', '').upper()
            if termo in nome or nome in termo:
                return {
                    'codigo_cvm': info['codigo_cvm'],
                    'cnpj': info['cnpj'],
                    'nome_pregao': info['nome_completo'],
                    'ticker': termo
                }
        
        return None


class CVMDataProcessor:
    """Processa dados CVM baixados para formato compatível com análise temporal"""
    
    def __init__(self, codigo_cvm, cnpj):
        self.codigo_cvm = int(codigo_cvm)
        self.cnpj = cnpj
        self.dados_disponiveis = self._verificar_dados_disponiveis()
        
    def _verificar_dados_disponiveis(self):
        """Verifica quais tipos de dados estão disponíveis"""
        # Ajustar caminhos para usar database global - buscar em múltiplos anos
        base_dir = Path('/mnt/c/Users/guilh/documents/github/database/chimpa')
        disponiveis = {}
        
        # Buscar por tipo de documento (ITR, DFP)
        for tipo in ['ITR', 'DFP']:
            tipo_dir = base_dir / tipo
            if tipo_dir.exists():
                # Buscar o ano mais recente que tem dados
                anos = sorted([d.name for d in tipo_dir.iterdir() if d.is_dir()], reverse=True)
                for ano in anos:
                    ano_dir = tipo_dir / ano
                    # Verificar se tem os arquivos necessários
                    arquivo_teste = ano_dir / f'{tipo.lower()}_cia_aberta_BPA_con_{ano}.csv'
                    if arquivo_teste.exists():
                        disponiveis[tipo] = ano_dir
                        break
        
        return disponiveis
    
    def carregar_serie_temporal_completa(self):
        """Carrega série temporal completa de dados financeiros de múltiplos anos"""
        dados_completos = {
            'balanco': pd.DataFrame(),
            'dre': pd.DataFrame(),
            'dfc': pd.DataFrame()
        }
        
        # Buscar dados em todos os anos disponíveis
        base_dir = Path('/mnt/c/Users/guilh/documents/github/database/chimpa')
        
        for tipo in ['DFP', 'ITR']:  # DFP primeiro (anual), depois ITR (trimestral)
            tipo_dir = base_dir / tipo
            if not tipo_dir.exists():
                continue
                
            # Processar todos os anos disponíveis
            anos = sorted([d.name for d in tipo_dir.iterdir() if d.is_dir()])
            
            for ano in anos:
                ano_dir = tipo_dir / ano
                
                # Carregar dados do ano
                bal = self._carregar_balanco_temporal(ano_dir, tipo, ano)
                if not bal.empty:
                    dados_completos['balanco'] = pd.concat([dados_completos['balanco'], bal])
                
                dre = self._carregar_dre_temporal(ano_dir, tipo, ano)
                if not dre.empty:
                    dados_completos['dre'] = pd.concat([dados_completos['dre'], dre])
                
                dfc = self._carregar_dfc_temporal(ano_dir, tipo, ano)
                if not dfc.empty:
                    dados_completos['dfc'] = pd.concat([dados_completos['dfc'], dfc])
        
        # Remover duplicatas e ordenar por data
        for key in dados_completos:
            if not dados_completos[key].empty:
                dados_completos[key] = dados_completos[key][~dados_completos[key].index.duplicated(keep='last')]
                dados_completos[key] = dados_completos[key].sort_index()
        
        return dados_completos
    
    def _carregar_balanco_temporal(self, base_path, tipo, ano):
        """Carrega série temporal do balanço patrimonial"""
        try:
            # Carregar BPA (Ativo)
            arquivo_bpa = base_path / f'{tipo.lower()}_cia_aberta_BPA_con_{ano}.csv'
            if not arquivo_bpa.exists():
                return pd.DataFrame()
                
            bpa = pd.read_csv(arquivo_bpa, encoding='latin-1', sep=';', decimal=',')
            bpa = bpa[bpa['CD_CVM'] == self.codigo_cvm]
            bpa['VL_CONTA'] = pd.to_numeric(bpa['VL_CONTA'], errors='coerce')
            
            # Carregar BPP (Passivo)
            arquivo_bpp = base_path / f'{tipo.lower()}_cia_aberta_BPP_con_{ano}.csv'
            bpp = pd.read_csv(arquivo_bpp, encoding='latin-1', sep=';', decimal=',')
            bpp = bpp[bpp['CD_CVM'] == self.codigo_cvm]
            bpp['VL_CONTA'] = pd.to_numeric(bpp['VL_CONTA'], errors='coerce')
            
            # Combinar
            bal_completo = pd.concat([bpa, bpp])
            
            # Pivotar por data
            bal_pivot = bal_completo.pivot_table(
                index='DT_REFER',
                columns='DS_CONTA',
                values='VL_CONTA',
                aggfunc='first'
            )
            
            bal_pivot.index = pd.to_datetime(bal_pivot.index)
            
            # Mapear contas essenciais
            colunas_essenciais = {
                'Ativo Total': '1',
                'Ativo Circulante': '1.01',
                'Ativo Não Circulante': '1.02',
                'Passivo Total': '2',
                'Passivo Circulante': '2.01',
                'Passivo Não Circulante': '2.02',
                'Patrimônio Líquido': '2.03',
                'Caixa e Equivalentes de Caixa': '1.01.01',
                'Contas a Receber': '1.01.03',
                'Estoques': '1.01.04',
                'Imobilizado': '1.02.03',
                'Empréstimos e Financiamentos': '2.01.04',
                'Fornecedores': '2.01.02'
            }
            
            for nome, codigo in colunas_essenciais.items():
                dados_conta = bal_completo[bal_completo['CD_CONTA'] == codigo]
                if not dados_conta.empty:
                    for _, row in dados_conta.iterrows():
                        bal_pivot.loc[pd.to_datetime(row['DT_REFER']), nome] = row['VL_CONTA']
            
            return bal_pivot
            
        except Exception as e:
            print(f"Erro ao carregar balanço de {tipo}: {e}")
            return pd.DataFrame()
    
    def _carregar_dre_temporal(self, base_path, tipo, ano):
        """Carrega série temporal da DRE"""
        try:
            arquivo_dre = base_path / f'{tipo.lower()}_cia_aberta_DRE_con_{ano}.csv'
            if not arquivo_dre.exists():
                return pd.DataFrame()
                
            dre = pd.read_csv(arquivo_dre, encoding='latin-1', sep=';', decimal=',')
            dre = dre[dre['CD_CVM'] == self.codigo_cvm]
            dre['VL_CONTA'] = pd.to_numeric(dre['VL_CONTA'], errors='coerce')
            
            # Para ITR, pegar apenas últimos 12 meses
            if tipo == 'ITR':
                dre = dre[dre['ORDEM_EXERC'] == 'ÚLTIMO']
            
            dre_pivot = dre.pivot_table(
                index='DT_REFER',
                columns='DS_CONTA',
                values='VL_CONTA',
                aggfunc='first'
            )
            
            dre_pivot.index = pd.to_datetime(dre_pivot.index)
            
            # Mapear contas essenciais
            colunas_essenciais = {
                'Receita Líquida': '3.01',
                'Custos': '3.02',
                'Lucro Bruto': '3.03',
                'Despesas Operacionais': '3.04',
                'EBIT': '3.05',
                'Resultado Financeiro': '3.06',
                'EBT': '3.07',
                'Lucro Líquido': '3.11',
                'Depreciação e Amortização': '3.04.02'
            }
            
            for nome, codigo in colunas_essenciais.items():
                dados_conta = dre[dre['CD_CONTA'] == codigo]
                if not dados_conta.empty:
                    for _, row in dados_conta.iterrows():
                        dre_pivot.loc[pd.to_datetime(row['DT_REFER']), nome] = row['VL_CONTA']
            
            return dre_pivot
            
        except Exception as e:
            print(f"Erro ao carregar DRE de {tipo}: {e}")
            return pd.DataFrame()
    
    def _carregar_dfc_temporal(self, base_path, tipo, ano):
        """Carrega série temporal da DFC"""
        try:
            arquivo_dfc = base_path / f'{tipo.lower()}_cia_aberta_DFC_MD_con_{ano}.csv'
            if not arquivo_dfc.exists():
                return pd.DataFrame()
                
            dfc = pd.read_csv(arquivo_dfc, encoding='latin-1', sep=';', decimal=',')
            dfc = dfc[dfc['CD_CVM'] == self.codigo_cvm]
            dfc['VL_CONTA'] = pd.to_numeric(dfc['VL_CONTA'], errors='coerce')
            
            dfc_pivot = dfc.pivot_table(
                index='DT_REFER',
                columns='DS_CONTA',
                values='VL_CONTA',
                aggfunc='first'
            )
            
            dfc_pivot.index = pd.to_datetime(dfc_pivot.index)
            
            return dfc_pivot
            
        except Exception as e:
            print(f"Erro ao carregar DFC de {tipo}: {e}")
            return pd.DataFrame()


class ValuationTemporalAnalyzer:
    """Realiza análise de valuation com série temporal completa"""
    
    def __init__(self, empresa_info):
        self.empresa = empresa_info
        self.codigo_cvm = empresa_info['codigo_cvm']
        self.cnpj = empresa_info.get('cnpj', '')
        self.ticker = empresa_info.get('ticker', '')
        self.nome = empresa_info.get('nome_pregao', '')
        
        # Processar dados CVM
        self.processor = CVMDataProcessor(self.codigo_cvm, self.cnpj)
        
        # Carregar dados temporais
        self.dados_temporais = self.processor.carregar_serie_temporal_completa()
        self.bal = self.dados_temporais['balanco']
        self.dre = self.dados_temporais['dre']
        self.dfc = self.dados_temporais['dfc']
        
        # DataFrames de resultados temporais
        self.metricas_temporais = pd.DataFrame()
        self.indicadores_temporais = pd.DataFrame()
        self.multiplos_temporais = pd.DataFrame()
        
    def calcular_metricas_temporais(self):
        """Calcula todas as métricas para cada período disponível"""
        if self.bal.empty or self.dre.empty:
            print("Aviso: Dados insuficientes para análise temporal")
            return
        
        # Alinhar índices de balanço e DRE
        datas_comuns = self.bal.index.intersection(self.dre.index)
        
        metricas_lista = []
        
        for data in datas_comuns:
            metricas_periodo = {}
            metricas_periodo['data'] = data
            
            # Dados do período
            bal_periodo = self.bal.loc[data]
            dre_periodo = self.dre.loc[data]
            
            # Métricas básicas
            metricas_periodo['receita_liquida'] = dre_periodo.get('Receita Líquida', 0)
            metricas_periodo['custos'] = abs(dre_periodo.get('Custos', 0))
            metricas_periodo['lucro_bruto'] = dre_periodo.get('Lucro Bruto', 0)
            metricas_periodo['lucro_liquido'] = dre_periodo.get('Lucro Líquido', 0)
            metricas_periodo['ebit'] = dre_periodo.get('EBIT', 0)
            metricas_periodo['patrimonio_liquido'] = bal_periodo.get('Patrimônio Líquido', 0)
            metricas_periodo['ativo_total'] = bal_periodo.get('Ativo Total', 0)
            metricas_periodo['ativo_circulante'] = bal_periodo.get('Ativo Circulante', 0)
            metricas_periodo['passivo_circulante'] = bal_periodo.get('Passivo Circulante', 0)
            
            # Dívida
            divida_bruta = bal_periodo.get('Empréstimos e Financiamentos', 0)
            caixa = bal_periodo.get('Caixa e Equivalentes de Caixa', 0)
            metricas_periodo['divida_liquida'] = divida_bruta - caixa
            
            # EBITDA
            ebitda = metricas_periodo['ebit']
            depreciacao = dre_periodo.get('Depreciação e Amortização', 0)
            if depreciacao == 0 and metricas_periodo['receita_liquida'] > 0:
                depreciacao = metricas_periodo['receita_liquida'] * 0.05
            metricas_periodo['ebitda'] = ebitda + abs(depreciacao)
            
            # Margens
            if metricas_periodo['receita_liquida'] > 0:
                metricas_periodo['margem_bruta'] = (metricas_periodo['lucro_bruto'] / metricas_periodo['receita_liquida']) * 100
                metricas_periodo['margem_liquida'] = (metricas_periodo['lucro_liquido'] / metricas_periodo['receita_liquida']) * 100
                metricas_periodo['margem_ebit'] = (metricas_periodo['ebit'] / metricas_periodo['receita_liquida']) * 100
                metricas_periodo['margem_ebitda'] = (metricas_periodo['ebitda'] / metricas_periodo['receita_liquida']) * 100
            
            # Rentabilidade
            if metricas_periodo['patrimonio_liquido'] > 0:
                metricas_periodo['roe'] = (metricas_periodo['lucro_liquido'] / metricas_periodo['patrimonio_liquido']) * 100
            
            if metricas_periodo['ativo_total'] > 0:
                metricas_periodo['roa'] = (metricas_periodo['lucro_liquido'] / metricas_periodo['ativo_total']) * 100
                metricas_periodo['roi'] = (metricas_periodo['ebit'] / metricas_periodo['ativo_total']) * 100
            
            # ROIC (metodologia Insper: sem ajuste de IR)
            capital_investido = metricas_periodo['patrimonio_liquido'] + metricas_periodo['divida_liquida']
            if capital_investido > 0:
                metricas_periodo['roic'] = (metricas_periodo['ebit'] / capital_investido) * 100
            
            # Liquidez
            if metricas_periodo['passivo_circulante'] > 0:
                metricas_periodo['liquidez_corrente'] = metricas_periodo['ativo_circulante'] / metricas_periodo['passivo_circulante']
            
            # Alavancagem
            if metricas_periodo['patrimonio_liquido'] > 0:
                metricas_periodo['divida_pl'] = metricas_periodo['divida_liquida'] / metricas_periodo['patrimonio_liquido']
            
            if metricas_periodo['ebitda'] > 0:
                metricas_periodo['divida_ebitda'] = metricas_periodo['divida_liquida'] / metricas_periodo['ebitda']
            
            metricas_lista.append(metricas_periodo)
        
        # Criar DataFrame temporal
        self.metricas_temporais = pd.DataFrame(metricas_lista)
        if not self.metricas_temporais.empty:
            self.metricas_temporais.set_index('data', inplace=True)
            self.metricas_temporais = self.metricas_temporais.sort_index()
        
        print(f"Métricas calculadas para {len(self.metricas_temporais)} períodos")
    
    def calcular_indicadores_prazos_temporais(self):
        """Calcula indicadores de prazos para todos os períodos"""
        if self.bal.empty or self.dre.empty:
            return
        
        datas_comuns = self.bal.index.intersection(self.dre.index)
        indicadores_lista = []
        
        for data in datas_comuns:
            indicadores_periodo = {}
            indicadores_periodo['data'] = data
            
            bal_periodo = self.bal.loc[data]
            dre_periodo = self.dre.loc[data]
            
            receita = dre_periodo.get('Receita Líquida', 0)
            custos = abs(dre_periodo.get('Custos', 0))
            
            if receita > 0:
                # PMR (metodologia Insper: 360 dias)
                contas_receber = bal_periodo.get('Contas a Receber', 0)
                if contas_receber > 0:
                    indicadores_periodo['pmr'] = (contas_receber * 360) / receita
                
                # PME (metodologia Insper: 360 dias)
                estoques = bal_periodo.get('Estoques', 0)
                if estoques > 0 and custos > 0:
                    indicadores_periodo['pme'] = (estoques * 360) / custos
                
                # PMP (metodologia Insper: 360 dias)
                fornecedores = bal_periodo.get('Fornecedores', 0)
                if fornecedores > 0 and custos > 0:
                    indicadores_periodo['pmp'] = (fornecedores * 360) / custos
                
                # Ciclos
                if 'pmr' in indicadores_periodo and 'pme' in indicadores_periodo:
                    indicadores_periodo['ciclo_operacional'] = indicadores_periodo['pmr'] + indicadores_periodo['pme']
                    
                    if 'pmp' in indicadores_periodo:
                        indicadores_periodo['ciclo_caixa'] = indicadores_periodo['ciclo_operacional'] - indicadores_periodo['pmp']
            
            if indicadores_periodo:
                indicadores_lista.append(indicadores_periodo)
        
        # Criar DataFrame temporal
        self.indicadores_temporais = pd.DataFrame(indicadores_lista)
        if not self.indicadores_temporais.empty:
            self.indicadores_temporais.set_index('data', inplace=True)
            self.indicadores_temporais = self.indicadores_temporais.sort_index()
    
    def plotar_evolucao_indicadores(self, output_dir=None):
        """Gera gráficos da evolução dos principais indicadores"""
        if self.metricas_temporais.empty:
            print("Sem dados para plotar")
            return
        
        # Criar diretório de saída dentro de data
        script_dir = Path(__file__).parent
        data_dir = script_dir / 'data'
        data_dir.mkdir(exist_ok=True)
        
        if not output_dir:
            output_dir = data_dir / f"graficos_{self.ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_dir.mkdir(exist_ok=True)
        
        # Definir períodos para análise
        anos = self.metricas_temporais.index.year.unique()
        
        # 1. Evolução da Receita e Lucro
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        receita_anual = self.metricas_temporais.groupby(self.metricas_temporais.index.year)['receita_liquida'].sum()
        lucro_anual = self.metricas_temporais.groupby(self.metricas_temporais.index.year)['lucro_liquido'].sum()
        
        receita_anual.plot(kind='bar', ax=ax1, color='steelblue')
        ax1.set_title(f'{self.nome} - Evolução da Receita Líquida')
        ax1.set_ylabel('R$ Milhões')
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:,.0f}'))
        
        lucro_anual.plot(kind='bar', ax=ax2, color='darkgreen')
        ax2.set_title('Evolução do Lucro Líquido')
        ax2.set_ylabel('R$ Milhões')
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:,.0f}'))
        
        plt.tight_layout()
        plt.savefig(output_dir / 'receita_lucro_evolucao.png')
        plt.close()
        
        # 2. Evolução das Margens
        fig, ax = plt.subplots(figsize=(12, 6))
        
        margens = ['margem_bruta', 'margem_ebit', 'margem_ebitda', 'margem_liquida']
        margens_existentes = [m for m in margens if m in self.metricas_temporais.columns]
        
        for margem in margens_existentes:
            self.metricas_temporais[margem].plot(ax=ax, marker='o', label=margem.replace('_', ' ').title())
        
        ax.set_title(f'{self.nome} - Evolução das Margens')
        ax.set_ylabel('%')
        ax.legend()
        ax.grid(True)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'margens_evolucao.png')
        plt.close()
        
        # 3. Evolução da Rentabilidade
        fig, ax = plt.subplots(figsize=(12, 6))
        
        rentabilidade = ['roe', 'roa', 'roic']
        rent_existentes = [r for r in rentabilidade if r in self.metricas_temporais.columns]
        
        for rent in rent_existentes:
            self.metricas_temporais[rent].plot(ax=ax, marker='o', label=rent.upper())
        
        ax.set_title(f'{self.nome} - Evolução da Rentabilidade')
        ax.set_ylabel('%')
        ax.legend()
        ax.grid(True)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'rentabilidade_evolucao.png')
        plt.close()
        
        # 4. Evolução do Endividamento
        if 'divida_ebitda' in self.metricas_temporais.columns:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            self.metricas_temporais['divida_ebitda'].plot(ax=ax, marker='o', color='red')
            ax.set_title(f'{self.nome} - Evolução Dívida Líquida/EBITDA')
            ax.set_ylabel('x')
            ax.axhline(y=3, color='orange', linestyle='--', label='Limite saudável (3x)')
            ax.legend()
            ax.grid(True)
            
            plt.tight_layout()
            plt.savefig(output_dir / 'divida_ebitda_evolucao.png')
            plt.close()
        
        print(f"Gráficos salvos em: {output_dir}")
    
    def calcular_estatisticas_periodo(self, anos=5):
        """Calcula estatísticas dos indicadores para um período"""
        # Filtrar últimos N anos
        data_corte = datetime.now() - pd.Timedelta(days=365*anos)
        metricas_periodo = self.metricas_temporais[self.metricas_temporais.index >= data_corte]
        
        if metricas_periodo.empty:
            return {}
        
        estatisticas = {}
        
        # Colunas de interesse - TODAS as métricas calculadas
        colunas_analise = [
            # Demonstrações Financeiras
            'receita_liquida', 'lucro_liquido', 'ebit', 'ebitda', 'lucro_bruto', 'custos',
            
            # Margens
            'margem_bruta', 'margem_liquida', 'margem_ebit', 'margem_ebitda',
            
            # Rentabilidade
            'roe', 'roa', 'roi', 'roic',
            
            # Liquidez e Endividamento
            'liquidez_corrente', 'divida_pl', 'divida_ebitda', 'divida_ebit', 'pl_ativos',
            
            # Estrutura Patrimonial
            'ativo_total', 'patrimonio_liquido', 'ativo_circulante', 'passivo_circulante',
            'divida_liquida', 'caixa', 'capital_giro', 'divida_bruta',
            
            # Outras métricas importantes
            'passivo_total', 'ativo_nao_circulante', 'passivo_nao_circulante'
        ]
        
        for coluna in colunas_analise:
            if coluna in metricas_periodo.columns:
                valores = metricas_periodo[coluna].dropna()
                if len(valores) > 0:
                    estatisticas[coluna] = {
                        'media': valores.mean(),
                        'mediana': valores.median(),
                        'desvio_padrao': valores.std(),
                        'minimo': valores.min(),
                        'maximo': valores.max(),
                        'ultimo': valores.iloc[-1] if len(valores) > 0 else None
                    }
        
        return estatisticas
    
    def _buscar_dados_mercado_perplexity(self):
        """Busca dados de mercado usando Perplexity com interação do usuário"""
        try:
            import asyncio
            from perplexity_client import PerplexityClient
            import os
            from dotenv import load_dotenv
            
            load_dotenv()
            api_key = os.getenv("PERPLEXITY_API_KEY")
            
            if not api_key:
                print("[AVISO] PERPLEXITY_API_KEY não encontrada no .env")
                return {}
            
            print(f"\n BUSCA DE DADOS DE MERCADO PARA {self.nome} ({self.ticker})")
            print("=" * 70)
            
            # Queries para buscar dados específicos
            queries = {
                'preco_atual': f"Qual o preço atual da ação {self.ticker} {self.nome} na bolsa brasileira hoje?",
                'multiplos_setor': f"Quais os múltiplos P/L e EV/EBITDA médios do setor bancário brasileiro em 2024?",
                'análise_recente': f"Qual a análise mais recente sobre as ações do {self.nome} {self.ticker}? Perspectivas e recomendações?",
                'numero_acoes': f"Quantas ações o {self.nome} possui em circulação atualmente? Capital social?",
                'dividend_yield': f"Qual o dividend yield atual do {self.nome} {self.ticker}? Histórico de dividendos?"
            }
            
            resultados = {}
            client = PerplexityClient(api_key)
            
            # Processar cada pergunta interativamente
            for i, (categoria, query_original) in enumerate(queries.items(), 1):
                print(f"\n PERGUNTA {i}/5: {categoria.upper()}")
                print(f" Pergunta proposta:")
                print(f"   {query_original}")
                
                # Solicitar autorização do usuário
                while True:
                    resposta = input(f"\n Ações: [E]nvoar / [M]odificar / [P]ular (E/M/P): ").upper().strip()
                    
                    if resposta == 'E':
                        query_final = query_original
                        break
                    elif resposta == 'M':
                        print(" Digite a nova pergunta:")
                        query_final = input("   ").strip()
                        if not query_final:
                            print("[ERRO] Pergunta vazia! Usando pergunta original.")
                            query_final = query_original
                        break
                    elif resposta == 'P':
                        print(" Pergunta pulada.")
                        resultados[categoria] = {'pulado': True, 'motivo': 'Usuário optou por pular'}
                        continue
                    else:
                        print("[ERRO] Opção inválida! Use E (Enviar), M (Modificar) ou P (Pular)")
                        continue
                
                # Se chegou aqui, deve fazer a busca
                if categoria not in resultados:
                    print(f" Enviando pergunta: {query_final}")
                    
                    try:
                        # Executar busca assíncrona
                        async def buscar_single():
                            return await client.search(query_final, max_tokens=1500, return_related_questions=False)
                        
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        resultado = loop.run_until_complete(buscar_single())
                        loop.close()
                        
                        if resultado["status"] == "success":
                            response_data = resultado["response"]
                            
                            # Mostrar resposta para aprovação
                            print(f"\n RESPOSTA RECEBIDA:")
                            print("=" * 50)
                            print(response_data["content"][:800] + "..." if len(response_data["content"]) > 800 else response_data["content"])
                            
                            if response_data["citations"]:
                                print(f"\n FONTES ({len(response_data['citations'])}):")
                                for j, fonte in enumerate(response_data["citations"][:3], 1):
                                    print(f"   {j}. {fonte.get('title', 'Sem título')} - {fonte.get('url', 'Sem URL')}")
                            
                            # Solicitar aprovação
                            while True:
                                aprovacao = input(f"\n Aceitar essa resposta? [S]im / [N]ão (S/N): ").upper().strip()
                                if aprovacao == 'S':
                                    resultados[categoria] = {
                                        'pergunta_enviada': query_final,
                                        'conteudo': response_data["content"],
                                        'fontes': response_data["citations"][:3],
                                        'insights': response_data["key_insights"][:5],
                                        'aprovado': True
                                    }
                                    print(" Resposta aprovada e salva!")
                                    break
                                elif aprovacao == 'N':
                                    print("[ERRO] Resposta rejeitada.")
                                    
                                    # Oferecer opção de fornecer resposta manual
                                    while True:
                                        opcao_manual = input("\n Opções: [F]ornecer resposta correta / [D]esconsiderar análise (F/D): ").upper().strip()
                                        
                                        if opcao_manual == 'F':
                                            print(f" Digite a resposta correta para {categoria.upper()}:")
                                            resposta_manual = input("   ").strip()
                                            
                                            if resposta_manual:
                                                resultados[categoria] = {
                                                    'pergunta_enviada': query_final,
                                                    'conteudo': resposta_manual,
                                                    'fontes': [{'title': 'Fornecido pelo usuário', 'url': '', 'snippet': 'Resposta manual'}],
                                                    'insights': [resposta_manual],
                                                    'aprovado': True,
                                                    'fonte': 'manual'
                                                }
                                                print(" Resposta manual salva!")
                                            else:
                                                print("[ERRO] Resposta vazia. Desconsiderando análise.")
                                                resultados[categoria] = {
                                                    'pergunta_enviada': query_final,
                                                    'desconsiderado': True,
                                                    'motivo': 'Usuário optou por descartar - sem resposta manual'
                                                }
                                            break
                                            
                                        elif opcao_manual == 'D':
                                            resultados[categoria] = {
                                                'pergunta_enviada': query_final,
                                                'desconsiderado': True,
                                                'motivo': 'Usuário optou por descartar a análise'
                                            }
                                            print("[AVISO] Análise desconsiderada. Cálculos dependentes serão ajustados.")
                                            break
                                            
                                        else:
                                            print("[ERRO] Opção inválida! Use F (Fornecer resposta) ou D (Desconsiderar)")
                                    break
                                else:
                                    print("[ERRO] Opção inválida! Use S (Sim) ou N (Não)")
                        else:
                            print(f"[ERRO] Erro na busca: {resultado.get('error', 'Erro desconhecido')}")
                            resultados[categoria] = {'erro': resultado.get('error', 'Erro desconhecido')}
                            
                    except Exception as e:
                        print(f"[ERRO] Erro ao processar pergunta: {e}")
                        resultados[categoria] = {'erro': str(e)}
            
            # Resumo final
            aprovados = len([r for r in resultados.values() if r.get('aprovado')])
            manuais = len([r for r in resultados.values() if r.get('fonte') == 'manual'])
            desconsiderados = len([r for r in resultados.values() if r.get('desconsiderado')])
            pulados = len([r for r in resultados.values() if r.get('pulado')])
            erros = len([r for r in resultados.values() if 'erro' in r])
            
            print(f"\n RESUMO FINAL:")
            print(f"    Respostas aprovadas (Perplexity): {aprovados - manuais}")
            print(f"    Respostas manuais (usuário): {manuais}")
            print(f"   [AVISO] Análises desconsideradas: {desconsiderados}")
            print(f"    Perguntas puladas: {pulados}")
            print(f"   [ERRO] Erros: {erros}")
            print(f"    Total processado: {len(resultados)}")
            
            # Alertas para análises que podem ser impactadas
            if desconsiderados > 0:
                print(f"\n[AVISO] ALERTAS:")
                categorias_desconsideradas = [cat for cat, res in resultados.items() if res.get('desconsiderado')]
                if 'preco_atual' in categorias_desconsideradas:
                    print(f"   - Múltiplos de mercado não serão calculados (sem preço atual)")
                if 'numero_acoes' in categorias_desconsideradas:
                    print(f"   - Market cap não será calculado (sem número de ações)")
                if 'multiplos_setor' in categorias_desconsideradas:
                    print(f"   - Comparação setorial limitada")
                if 'dividend_yield' in categorias_desconsideradas:
                    print(f"   - Análise de dividendos não disponível")
            
            return resultados
            
        except Exception as e:
            print(f"[ERRO] Erro ao buscar dados de mercado: {e}")
            return {}
    
    def gerar_relatorio_temporal(self, arquivo_saida=None):
        """Gera relatório completo com análise temporal"""
        # Executar análises
        self.calcular_metricas_temporais()
        self.calcular_indicadores_prazos_temporais()
        
        # NOVO: Buscar dados de mercado com Perplexity
        dados_mercado = self._buscar_dados_mercado_perplexity()
        
        # Estatísticas dos últimos 5 anos
        stats_5anos = self.calcular_estatisticas_periodo(5)
        
        relatorio = {
            'empresa': {
                'nome': self.nome,
                'ticker': self.ticker,
                'codigo_cvm': self.codigo_cvm,
                'cnpj': self.cnpj
            },
            'data_analise': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'periodo_dados': {
                'inicio': str(self.metricas_temporais.index.min()) if not self.metricas_temporais.empty else 'N/A',
                'fim': str(self.metricas_temporais.index.max()) if not self.metricas_temporais.empty else 'N/A',
                'total_periodos': len(self.metricas_temporais)
            },
            'estatisticas_5anos': stats_5anos,
            'dados_mercado': dados_mercado,  # NOVO: Dados do Perplexity
            'serie_temporal': {
                'metricas': self.metricas_temporais.to_dict('index') if not self.metricas_temporais.empty else {},
                'indicadores_prazos': self.indicadores_temporais.to_dict('index') if not self.indicadores_temporais.empty else {}
            } if not self.metricas_temporais.empty else {}
        }
        
        # Converter tipos numpy e pandas para Python nativo
        def converter_numpy(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, pd.Timestamp):
                return obj.strftime('%Y-%m-%d')
            return obj
        
        # Converter as chaves Timestamp para string antes do JSON
        if 'serie_temporal' in relatorio and relatorio['serie_temporal']:
            if 'metricas' in relatorio['serie_temporal']:
                metricas_convertidas = {}
                for timestamp, dados in relatorio['serie_temporal']['metricas'].items():
                    if isinstance(timestamp, pd.Timestamp):
                        chave_str = timestamp.strftime('%Y-%m-%d')
                    else:
                        chave_str = str(timestamp)
                    metricas_convertidas[chave_str] = dados
                relatorio['serie_temporal']['metricas'] = metricas_convertidas
            
            if 'indicadores_prazos' in relatorio['serie_temporal']:
                indicadores_convertidos = {}
                for timestamp, dados in relatorio['serie_temporal']['indicadores_prazos'].items():
                    if isinstance(timestamp, pd.Timestamp):
                        chave_str = timestamp.strftime('%Y-%m-%d')
                    else:
                        chave_str = str(timestamp)
                    indicadores_convertidos[chave_str] = dados
                relatorio['serie_temporal']['indicadores_prazos'] = indicadores_convertidos
        
        relatorio = json.loads(json.dumps(relatorio, default=converter_numpy))
        
        # Criar pasta data se não existir
        script_dir = Path(__file__).parent
        data_dir = script_dir / 'data'
        data_dir.mkdir(exist_ok=True)
        
        # Salvar JSON
        if not arquivo_saida:
            arquivo_saida = data_dir / f"valuation_temporal_{self.ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(arquivo_saida, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, indent=2, ensure_ascii=False)
        
        # NOVO: Gerar relatório TXT COMPLETO com TODAS as estatísticas
        arquivo_txt = str(arquivo_saida).replace('.json', '_COMPLETO.txt')
        self._gerar_relatorio_txt_completo(relatorio, arquivo_txt)
        
        # Exibir resumo
        print(f"\n{'='*60}")
        print(f"ANÁLISE TEMPORAL DE VALUATION - {self.nome} ({self.ticker})")
        print(f"{'='*60}")
        print(f"Código CVM: {self.codigo_cvm}")
        print(f"CNPJ: {self.cnpj}")
        print(f"\nPeríodo analisado: {relatorio['periodo_dados']['inicio']} a {relatorio['periodo_dados']['fim']}")
        print(f"Total de períodos: {relatorio['periodo_dados']['total_periodos']}")
        
        if stats_5anos:
            print("\n[ESTATÍSTICAS DOS ÚLTIMOS 5 ANOS]")
            print("-" * 40)
            
            # Margens
            print("\nMARGENS (%):")
            for margem in ['margem_bruta', 'margem_liquida', 'margem_ebitda']:
                if margem in stats_5anos:
                    stats = stats_5anos[margem]
                    nome = margem.replace('_', ' ').title()
                    print(f"{nome}:")
                    print(f"  Média: {stats['media']:.1f}% | Último: {stats['ultimo']:.1f}%")
                    print(f"  Min-Max: [{stats['minimo']:.1f}% - {stats['maximo']:.1f}%]")
            
            # Rentabilidade
            print("\nRENTABILIDADE (%):")
            for rent in ['roe', 'roa', 'roic']:
                if rent in stats_5anos:
                    stats = stats_5anos[rent]
                    print(f"{rent.upper()}:")
                    print(f"  Média: {stats['media']:.1f}% | Último: {stats['ultimo']:.1f}%")
            
            # Endividamento
            print("\nENDIVIDAMENTO:")
            if 'divida_ebitda' in stats_5anos:
                stats = stats_5anos['divida_ebitda']
                print(f"Dívida/EBITDA:")
                print(f"  Média: {stats['media']:.2f}x | Último: {stats['ultimo']:.2f}x")
        
        # Plotar gráficos
        self.plotar_evolucao_indicadores()
        
        print(f"\nRelatório JSON salvo em: {arquivo_saida}")
        print(f"Relatório TXT COMPLETO salvo em: {arquivo_txt}")
        
        return relatorio
    
    def _gerar_relatorio_txt_completo(self, relatorio, arquivo_txt):
        """Gera relatório TXT COMPLETO com TODAS as estatísticas temporais"""
        with open(arquivo_txt, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write(f"RELATÓRIO COMPLETO DE VALUATION TEMPORAL - {self.nome} ({self.ticker})\n")
            f.write("="*80 + "\n")
            f.write(f"Data da Análise: {relatorio['data_analise']}\n")
            f.write(f"Código CVM: {self.codigo_cvm}\n")
            f.write(f"CNPJ: {self.cnpj}\n")
            f.write(f"Período: {relatorio['periodo_dados']['inicio']} a {relatorio['periodo_dados']['fim']}\n")
            f.write(f"Total de Períodos: {relatorio['periodo_dados']['total_periodos']}\n\n")
            
            # 0. DADOS DE MERCADO (PERPLEXITY)
            dados_mercado = relatorio.get('dados_mercado', {})
            if dados_mercado:
                f.write("0. DADOS DE MERCADO ATUALIZADOS (PERPLEXITY)\n")
                f.write("-"*60 + "\n\n")
                
                categorias_mercado = {
                    'preco_atual': 'PREÇO ATUAL DA AÇÃO',
                    'numero_acoes': 'NÚMERO DE AÇÕES EM CIRCULAÇÃO',
                    'dividend_yield': 'DIVIDEND YIELD E DIVIDENDOS',
                    'multiplos_setor': 'MÚLTIPLOS DO SETOR BANCÁRIO',
                    'análise_recente': 'ANÁLISE E PERSPECTIVAS RECENTES'
                }
                
                for categoria, titulo in categorias_mercado.items():
                    if categoria in dados_mercado:
                        resultado = dados_mercado[categoria]
                        
                        f.write(f"{titulo}\n")
                        f.write("-" * len(titulo) + "\n")
                        
                        # Verificar status da resposta
                        if resultado.get('desconsiderado'):
                            f.write("[AVISO] ANÁLISE DESCONSIDERADA PELO USUÁRIO\n")
                            f.write(f"Motivo: {resultado.get('motivo', 'Não especificado')}\n\n")
                            
                        elif resultado.get('pulado'):
                            f.write(" PERGUNTA PULADA PELO USUÁRIO\n")
                            f.write(f"Motivo: {resultado.get('motivo', 'Não especificado')}\n\n")
                            
                        elif 'erro' in resultado:
                            f.write("[ERRO] ERRO NA BUSCA\n")
                            f.write(f"Erro: {resultado['erro']}\n\n")
                            
                        elif 'conteudo' in resultado:
                            # Indicar se é resposta manual ou do Perplexity
                            if resultado.get('fonte') == 'manual':
                                f.write(" RESPOSTA FORNECIDA MANUALMENTE PELO USUÁRIO\n\n")
                            else:
                                f.write(" RESPOSTA DO PERPLEXITY (APROVADA)\n\n")
                            
                            # Conteúdo principal
                            conteudo = resultado['conteudo']
                            f.write(f"{conteudo}\n\n")
                            
                            # Insights principais
                            insights = resultado.get('insights', [])
                            if insights:
                                f.write("PRINCIPAIS INSIGHTS:\n")
                                for i, insight in enumerate(insights, 1):
                                    f.write(f"  {i}. {insight}\n")
                                f.write("\n")
                            
                            # Fontes
                            fontes = resultado.get('fontes', [])
                            if fontes:
                                f.write("FONTES:\n")
                                for i, fonte in enumerate(fontes, 1):
                                    titulo_fonte = fonte.get('title', 'Fonte')
                                    url = fonte.get('url', '')
                                    f.write(f"  {i}. {titulo_fonte}")
                                    if url:
                                        f.write(f" - {url}")
                                    f.write("\n")
                        
                        f.write("\n" + "="*50 + "\n\n")
            
            # 1. ESTATÍSTICAS RESUMO DOS ÚLTIMOS 5 ANOS
            stats_5anos = relatorio.get('estatisticas_5anos', {})
            if stats_5anos:
                f.write("1. ESTATÍSTICAS DOS ÚLTIMOS 5 ANOS\n")
                f.write("-"*50 + "\n\n")
                
                # Organizar por categorias
                categorias = {
                    'DEMONSTRAÇÕES FINANCEIRAS (Milhões R$)': [
                        'receita_liquida', 'lucro_liquido', 'ebit', 'ebitda', 'lucro_bruto'
                    ],
                    'MARGENS (%)': [
                        'margem_bruta', 'margem_liquida', 'margem_ebit', 'margem_ebitda'
                    ],
                    'RENTABILIDADE (%)': [
                        'roe', 'roa', 'roi', 'roic'
                    ],
                    'LIQUIDEZ E ENDIVIDAMENTO': [
                        'liquidez_corrente', 'divida_pl', 'divida_ebitda', 'divida_ebit', 'pl_ativos'
                    ],
                    'ESTRUTURA PATRIMONIAL (Milhões R$)': [
                        'ativo_total', 'patrimonio_liquido', 'ativo_circulante', 'passivo_circulante',
                        'divida_liquida', 'caixa', 'capital_giro'
                    ]
                }
                
                for categoria, metricas in categorias.items():
                    f.write(f"{categoria}\n")
                    f.write("-" * len(categoria) + "\n")
                    
                    for metrica in metricas:
                        if metrica in stats_5anos:
                            stats = stats_5anos[metrica]
                            nome = metrica.replace('_', ' ').title()
                            
                            # Formatação baseada no tipo de métrica
                            if 'milhões' in categoria.lower():
                                f.write(f"{nome}:\n")
                                f.write(f"  Média: R$ {stats['media']/1_000_000:.1f}M | Último: R$ {stats['ultimo']/1_000_000:.1f}M\n")
                                f.write(f"  Mínimo: R$ {stats['minimo']/1_000_000:.1f}M | Máximo: R$ {stats['maximo']/1_000_000:.1f}M\n")
                                f.write(f"  Desvio Padrão: R$ {stats['desvio_padrao']/1_000_000:.1f}M | Mediana: R$ {stats['mediana']/1_000_000:.1f}M\n\n")
                            elif '%' in categoria:
                                f.write(f"{nome}:\n")
                                f.write(f"  Média: {stats['media']:.2f}% | Último: {stats['ultimo']:.2f}%\n")
                                f.write(f"  Mínimo: {stats['minimo']:.2f}% | Máximo: {stats['maximo']:.2f}%\n")
                                f.write(f"  Desvio Padrão: {stats['desvio_padrao']:.2f}% | Mediana: {stats['mediana']:.2f}%\n\n")
                            else:  # Múltiplos e índices
                                f.write(f"{nome}:\n")
                                f.write(f"  Média: {stats['media']:.2f}x | Último: {stats['ultimo']:.2f}x\n")
                                f.write(f"  Mínimo: {stats['minimo']:.2f}x | Máximo: {stats['maximo']:.2f}x\n")
                                f.write(f"  Desvio Padrão: {stats['desvio_padrao']:.2f}x | Mediana: {stats['mediana']:.2f}x\n\n")
                    
                    f.write("\n")
            
            # 2. SÉRIE TEMPORAL COMPLETA (TODOS OS PERÍODOS)
            serie_temporal = relatorio.get('serie_temporal', {})
            metricas_temporais = serie_temporal.get('metricas', {})
            
            if metricas_temporais:
                f.write("2. SÉRIE TEMPORAL COMPLETA - TODAS AS MÉTRICAS\n")
                f.write("-"*50 + "\n\n")
                
                # Converter para DataFrame para facilitar análise
                df_temporal = pd.DataFrame.from_dict(metricas_temporais, orient='index')
                df_temporal.index = pd.to_datetime(df_temporal.index)
                df_temporal = df_temporal.sort_index()
                
                # Listar todas as colunas disponíveis
                f.write(f"Períodos disponíveis: {len(df_temporal)} trimestres/anos\n")
                f.write(f"De {df_temporal.index.min().strftime('%Y-%m-%d')} até {df_temporal.index.max().strftime('%Y-%m-%d')}\n\n")
                
                # Para cada métrica, mostrar evolução temporal
                for coluna in df_temporal.columns:
                    serie = df_temporal[coluna].dropna()
                    if len(serie) > 0:
                        f.write(f"{coluna.replace('_', ' ').upper()}\n")
                        f.write("-" * len(coluna) + "\n")
                        
                        # Estatísticas da série
                        f.write(f"Total de períodos: {len(serie)}\n")
                        
                        if 'margem' in coluna or 'roe' in coluna or 'roa' in coluna or 'roic' in coluna:
                            f.write(f"Média histórica: {serie.mean():.2f}%\n")
                            f.write(f"Último valor: {serie.iloc[-1]:.2f}%\n")
                            f.write(f"Variação total: {((serie.iloc[-1] / serie.iloc[0]) - 1) * 100:.1f}%\n")
                        elif any(x in coluna for x in ['receita', 'lucro', 'ebit', 'ativo', 'patrimonio', 'caixa']):
                            f.write(f"Média histórica: R$ {serie.mean()/1_000_000:.1f}M\n")
                            f.write(f"Último valor: R$ {serie.iloc[-1]/1_000_000:.1f}M\n")
                            f.write(f"CAGR (crescimento anual): {((serie.iloc[-1] / serie.iloc[0]) ** (1/len(serie)) - 1) * 100:.1f}%\n")
                        else:
                            f.write(f"Média histórica: {serie.mean():.2f}x\n")
                            f.write(f"Último valor: {serie.iloc[-1]:.2f}x\n")
                        
                        # Evolução período a período (últimos 8 períodos)
                        f.write("\nEvolução (últimos 8 períodos):\n")
                        ultimos = serie.tail(8)
                        for data, valor in ultimos.items():
                            if 'margem' in coluna or 'roe' in coluna or 'roa' in coluna or 'roic' in coluna:
                                f.write(f"  {data.strftime('%Y-%m')}: {valor:.2f}%\n")
                            elif any(x in coluna for x in ['receita', 'lucro', 'ebit', 'ativo', 'patrimonio', 'caixa']):
                                f.write(f"  {data.strftime('%Y-%m')}: R$ {valor/1_000_000:.1f}M\n")
                            else:
                                f.write(f"  {data.strftime('%Y-%m')}: {valor:.2f}x\n")
                        
                        f.write("\n" + "="*40 + "\n\n")
            
            # 3. INDICADORES DE PRAZOS (se disponível)
            indicadores_prazos = serie_temporal.get('indicadores_prazos', {})
            if indicadores_prazos:
                f.write("3. INDICADORES DE PRAZOS TEMPORAIS\n")
                f.write("-"*50 + "\n\n")
                
                df_prazos = pd.DataFrame.from_dict(indicadores_prazos, orient='index')
                df_prazos.index = pd.to_datetime(df_prazos.index)
                df_prazos = df_prazos.sort_index()
                
                for coluna in df_prazos.columns:
                    serie = df_prazos[coluna].dropna()
                    if len(serie) > 0:
                        f.write(f"{coluna.replace('_', ' ').upper()} (dias)\n")
                        f.write(f"Média histórica: {serie.mean():.1f} dias\n")
                        f.write(f"Último valor: {serie.iloc[-1]:.1f} dias\n")
                        f.write(f"Mínimo: {serie.min():.1f} | Máximo: {serie.max():.1f} dias\n")
                        
                        # Últimos 4 períodos
                        f.write("Últimos períodos:\n")
                        for data, valor in serie.tail(4).items():
                            f.write(f"  {data.strftime('%Y-%m')}: {valor:.1f} dias\n")
                        f.write("\n")
            
            f.write("="*80 + "\n")
            f.write("RELATÓRIO GERADO AUTOMATICAMENTE PELO SISTEMA DE VALUATION CHIMPA INVEST\n")
            f.write("="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Sistema de Valuation Temporal para Empresas CVM',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python valuation_empresa_temporal.py VALE3
  python valuation_empresa_temporal.py "VALE S.A."
  python valuation_empresa_temporal.py 4170
  python valuation_empresa_temporal.py PETR4 --anos 3
        """
    )
    
    parser.add_argument('empresa', help='Ticker, nome ou código CVM da empresa')
    parser.add_argument('--anos', type=int, default=5, help='Anos para análise estatística (padrão: 5)')
    parser.add_argument('--output', help='Nome do arquivo de saída')
    parser.add_argument('--graficos', action='store_true', help='Gerar gráficos de evolução')
    
    args = parser.parse_args()
    
    # Buscar empresa
    print(f"Buscando empresa: {args.empresa}")
    
    empresa_info = EmpresaInfo()
    empresa = empresa_info.buscar_empresa(args.empresa)
    
    if not empresa:
        print(f"Erro: Empresa '{args.empresa}' não encontrada!")
        print("\nDica: Tente usar o ticker (ex: VALE3) ou código CVM (ex: 4170)")
        sys.exit(1)
    
    print(f"Empresa encontrada: {empresa['nome_pregao']} ({empresa.get('ticker', 'N/A')})")
    
    # Realizar análise temporal
    analyzer = ValuationTemporalAnalyzer(empresa)
    
    # Gerar relatório
    analyzer.gerar_relatorio_temporal(args.output)


if __name__ == "__main__":
    main()