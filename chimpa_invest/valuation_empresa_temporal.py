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
        self.empresas_path = Path('dados/empresas_cvm_completa.json')
        self.indice_path = Path('dados/indice_busca_empresas.json')
        self.empresas = {}
        self.indice = {}
        self._carregar_dados()
    
    def _carregar_dados(self):
        """Carrega dados das empresas"""
        if self.empresas_path.exists():
            with open(self.empresas_path, 'r', encoding='utf-8') as f:
                self.empresas = json.load(f)
        
        if self.indice_path.exists():
            with open(self.indice_path, 'r', encoding='utf-8') as f:
                self.indice = json.load(f)
    
    def buscar_empresa(self, termo):
        """
        Busca empresa por ticker, nome ou código CVM
        Retorna: dict com informações da empresa ou None
        """
        termo = str(termo).upper().strip()
        
        # Buscar por ticker
        if termo in self.indice.get('por_ticker', {}):
            codigo_cvm = self.indice['por_ticker'][termo]
            return self.empresas.get(str(codigo_cvm))
        
        # Buscar por código CVM
        if termo.isdigit() and termo in self.empresas:
            return self.empresas[termo]
        
        # Buscar por nome (parcial)
        for codigo, info in self.empresas.items():
            nome = info.get('nome_pregao', '').upper()
            if termo in nome or nome in termo:
                return info
        
        return None


class CVMDataProcessor:
    """Processa dados CVM baixados para formato compatível com análise temporal"""
    
    def __init__(self, codigo_cvm, cnpj):
        self.codigo_cvm = int(codigo_cvm)
        self.cnpj = cnpj
        self.dados_disponiveis = self._verificar_dados_disponiveis()
        
    def _verificar_dados_disponiveis(self):
        """Verifica quais tipos de dados estão disponíveis"""
        bases = {
            'ITR': Path('documents/cvm_estruturados/ITR/itr_cia_aberta_2025'),
            'DFP': Path('documents/cvm_estruturados/DFP/dfp_cia_aberta_2025'),
            'FRE': Path('documents/cvm_estruturados/FRE/fre_cia_aberta_2025'),
            'FCA': Path('documents/cvm_estruturados/FCA/fca_cia_aberta_2025')
        }
        
        disponiveis = {}
        for tipo, path in bases.items():
            if path.exists():
                disponiveis[tipo] = path
        
        return disponiveis
    
    def carregar_serie_temporal_completa(self):
        """Carrega série temporal completa de dados financeiros"""
        dados_completos = {
            'balanco': pd.DataFrame(),
            'dre': pd.DataFrame(),
            'dfc': pd.DataFrame()
        }
        
        # Tentar ITR primeiro (trimestral), depois DFP (anual)
        for tipo in ['ITR', 'DFP']:
            if tipo in self.dados_disponiveis:
                base_path = self.dados_disponiveis[tipo]
                
                # Carregar balanço patrimonial
                bal = self._carregar_balanco_temporal(base_path, tipo)
                if not bal.empty:
                    dados_completos['balanco'] = pd.concat([dados_completos['balanco'], bal])
                
                # Carregar DRE
                dre = self._carregar_dre_temporal(base_path, tipo)
                if not dre.empty:
                    dados_completos['dre'] = pd.concat([dados_completos['dre'], dre])
                
                # Carregar DFC
                dfc = self._carregar_dfc_temporal(base_path, tipo)
                if not dfc.empty:
                    dados_completos['dfc'] = pd.concat([dados_completos['dfc'], dfc])
        
        # Remover duplicatas e ordenar por data
        for key in dados_completos:
            if not dados_completos[key].empty:
                dados_completos[key] = dados_completos[key][~dados_completos[key].index.duplicated(keep='last')]
                dados_completos[key] = dados_completos[key].sort_index()
        
        return dados_completos
    
    def _carregar_balanco_temporal(self, base_path, tipo):
        """Carrega série temporal do balanço patrimonial"""
        try:
            # Carregar BPA (Ativo)
            arquivo_bpa = base_path / f'{tipo.lower()}_cia_aberta_BPA_con_2025.csv'
            if not arquivo_bpa.exists():
                return pd.DataFrame()
                
            bpa = pd.read_csv(arquivo_bpa, encoding='latin-1', sep=';', decimal=',')
            bpa = bpa[bpa['CD_CVM'] == self.codigo_cvm]
            bpa['VL_CONTA'] = pd.to_numeric(bpa['VL_CONTA'], errors='coerce')
            
            # Carregar BPP (Passivo)
            arquivo_bpp = base_path / f'{tipo.lower()}_cia_aberta_BPP_con_2025.csv'
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
    
    def _carregar_dre_temporal(self, base_path, tipo):
        """Carrega série temporal da DRE"""
        try:
            arquivo_dre = base_path / f'{tipo.lower()}_cia_aberta_DRE_con_2025.csv'
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
    
    def _carregar_dfc_temporal(self, base_path, tipo):
        """Carrega série temporal da DFC"""
        try:
            arquivo_dfc = base_path / f'{tipo.lower()}_cia_aberta_DFC_MD_con_2025.csv'
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
            
            # ROIC
            capital_investido = metricas_periodo['patrimonio_liquido'] + metricas_periodo['divida_liquida']
            if capital_investido > 0:
                metricas_periodo['roic'] = (metricas_periodo['ebit'] * 0.66 / capital_investido) * 100
            
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
                # PMR
                contas_receber = bal_periodo.get('Contas a Receber', 0)
                if contas_receber > 0:
                    indicadores_periodo['pmr'] = (contas_receber / receita) * 365
                
                # PME
                estoques = bal_periodo.get('Estoques', 0)
                if estoques > 0 and custos > 0:
                    indicadores_periodo['pme'] = (estoques / custos) * 365
                
                # PMP
                fornecedores = bal_periodo.get('Fornecedores', 0)
                if fornecedores > 0 and custos > 0:
                    indicadores_periodo['pmp'] = (fornecedores / custos) * 365
                
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
        
        # Criar diretório de saída
        if not output_dir:
            output_dir = f"analise_{self.ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(output_dir, exist_ok=True)
        
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
        plt.savefig(f'{output_dir}/receita_lucro_evolucao.png')
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
        plt.savefig(f'{output_dir}/margens_evolucao.png')
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
        plt.savefig(f'{output_dir}/rentabilidade_evolucao.png')
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
            plt.savefig(f'{output_dir}/divida_ebitda_evolucao.png')
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
        
        # Colunas de interesse
        colunas_analise = [
            'margem_bruta', 'margem_liquida', 'margem_ebitda',
            'roe', 'roa', 'roic',
            'divida_pl', 'divida_ebitda',
            'liquidez_corrente'
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
    
    def gerar_relatorio_temporal(self, arquivo_saida=None):
        """Gera relatório completo com análise temporal"""
        # Executar análises
        self.calcular_metricas_temporais()
        self.calcular_indicadores_prazos_temporais()
        
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
            'serie_temporal': {
                'metricas': self.metricas_temporais.to_dict('index') if not self.metricas_temporais.empty else {},
                'indicadores_prazos': self.indicadores_temporais.to_dict('index') if not self.indicadores_temporais.empty else {}
            }
        }
        
        # Converter tipos numpy para Python nativo
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
        
        relatorio = json.loads(json.dumps(relatorio, default=converter_numpy))
        
        # Salvar JSON
        if not arquivo_saida:
            arquivo_saida = f"valuation_temporal_{self.ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(arquivo_saida, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, indent=2, ensure_ascii=False)
        
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
        
        print(f"\nRelatório salvo em: {arquivo_saida}")
        
        return relatorio


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