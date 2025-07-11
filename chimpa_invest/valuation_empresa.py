#!/usr/bin/env python3
"""
Sistema de Valuation Genérico para Qualquer Empresa
===================================================
Análise completa de múltiplos, indicadores e rentabilidade
para qualquer empresa listada na CVM.

Uso:
    python valuation_empresa.py PETR4
    python valuation_empresa.py "PETROBRAS"
    python valuation_empresa.py 9512
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
    """Processa dados CVM baixados para formato compatível com análise"""
    
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
    
    def carregar_balanco_patrimonial(self):
        """Carrega e processa Balanço Patrimonial (Ativo e Passivo)"""
        # Tentar ITR primeiro, depois DFP
        for tipo in ['ITR', 'DFP']:
            if tipo in self.dados_disponiveis:
                base_path = self.dados_disponiveis[tipo]
                
                try:
                    # Carregar BPA (Ativo)
                    arquivo_bpa = base_path / f'{tipo.lower()}_cia_aberta_BPA_con_2025.csv'
                    if not arquivo_bpa.exists():
                        continue
                        
                    bpa = pd.read_csv(arquivo_bpa, encoding='latin-1', sep=';', decimal=',')
                    bpa = bpa[bpa['CD_CVM'] == self.codigo_cvm]
                    bpa['VL_CONTA'] = pd.to_numeric(bpa['VL_CONTA'], errors='coerce')
                    
                    # Carregar BPP (Passivo)
                    arquivo_bpp = base_path / f'{tipo.lower()}_cia_aberta_BPP_con_2025.csv'
                    bpp = pd.read_csv(arquivo_bpp, encoding='latin-1', sep=';', decimal=',')
                    bpp = bpp[bpp['CD_CVM'] == self.codigo_cvm]
                    bpp['VL_CONTA'] = pd.to_numeric(bpp['VL_CONTA'], errors='coerce')
                    
                    # Combinar e pivotar
                    bal_completo = pd.concat([bpa, bpp])
                    
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
                    continue
        
        return pd.DataFrame()
    
    def carregar_dre(self):
        """Carrega e processa DRE"""
        for tipo in ['ITR', 'DFP']:
            if tipo in self.dados_disponiveis:
                base_path = self.dados_disponiveis[tipo]
                
                try:
                    arquivo_dre = base_path / f'{tipo.lower()}_cia_aberta_DRE_con_2025.csv'
                    if not arquivo_dre.exists():
                        continue
                        
                    dre = pd.read_csv(arquivo_dre, encoding='latin-1', sep=';', decimal=',')
                    dre = dre[dre['CD_CVM'] == self.codigo_cvm]
                    dre['VL_CONTA'] = pd.to_numeric(dre['VL_CONTA'], errors='coerce')
                    
                    # Filtrar últimos 12 meses
                    dre_12m = dre[dre['ORDEM_EXERC'] == 'ÚLTIMO']
                    
                    dre_pivot = dre_12m.pivot_table(
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
                        dados_conta = dre_12m[dre_12m['CD_CONTA'] == codigo]
                        if not dados_conta.empty:
                            for _, row in dados_conta.iterrows():
                                dre_pivot.loc[pd.to_datetime(row['DT_REFER']), nome] = row['VL_CONTA']
                    
                    return dre_pivot
                    
                except Exception as e:
                    print(f"Erro ao carregar DRE de {tipo}: {e}")
                    continue
        
        return pd.DataFrame()
    
    def carregar_dfc(self):
        """Carrega e processa DFC"""
        for tipo in ['ITR', 'DFP']:
            if tipo in self.dados_disponiveis:
                base_path = self.dados_disponiveis[tipo]
                
                try:
                    arquivo_dfc = base_path / f'{tipo.lower()}_cia_aberta_DFC_MD_con_2025.csv'
                    if not arquivo_dfc.exists():
                        continue
                        
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
                    continue
        
        return pd.DataFrame()
    
    def carregar_serie_historica(self):
        """Carrega série histórica completa para análise temporal"""
        # Coletar dados de múltiplos períodos
        series = {
            'balanco': [],
            'dre': [],
            'dfc': []
        }
        
        # Processar múltiplos anos se disponível
        for tipo in ['DFP', 'ITR']:
            if tipo in self.dados_disponiveis:
                # Aqui poderiamos buscar múltiplos anos
                # Por ora, mantemos apenas o período atual
                pass
        
        return series


class ValuationAnalyzer:
    """Realiza análise de valuation completa"""
    
    def __init__(self, empresa_info, analise_temporal=False):
        self.empresa = empresa_info
        self.codigo_cvm = empresa_info['codigo_cvm']
        self.cnpj = empresa_info.get('cnpj', '')
        self.ticker = empresa_info.get('ticker', '')
        self.nome = empresa_info.get('nome_pregao', '')
        self.analise_temporal = analise_temporal
        
        # Processar dados CVM
        self.processor = CVMDataProcessor(self.codigo_cvm, self.cnpj)
        
        # Carregar dados
        self.bal = self.processor.carregar_balanco_patrimonial()
        self.dre = self.processor.carregar_dre()
        self.dfc = self.processor.carregar_dfc()
        
        # Resultados
        self.metricas = {}
        self.multiplos = {}
        self.indicadores_prazos = {}
        self.series_temporais = {}
        
    def calcular_metricas_financeiras(self):
        """Calcula métricas financeiras principais"""
        if self.bal.empty or self.dre.empty:
            print("Aviso: Dados insuficientes para calcular métricas")
            return
        
        # Pegar dados mais recentes
        try:
            ultimo_bal = self.bal.iloc[-1]
            ultimo_dre = self.dre.iloc[-1]
            
            # Métricas básicas
            self.metricas['receita_liquida'] = ultimo_dre.get('Receita Líquida', 0)
            self.metricas['custos'] = abs(ultimo_dre.get('Custos', 0))
            self.metricas['lucro_bruto'] = ultimo_dre.get('Lucro Bruto', 0)
            self.metricas['lucro_liquido'] = ultimo_dre.get('Lucro Líquido', 0)
            self.metricas['ebit'] = ultimo_dre.get('EBIT', 0)
            self.metricas['resultado_financeiro'] = ultimo_dre.get('Resultado Financeiro', 0)
            self.metricas['patrimonio_liquido'] = ultimo_bal.get('Patrimônio Líquido', 0)
            self.metricas['ativo_total'] = ultimo_bal.get('Ativo Total', 0)
            self.metricas['divida_bruta'] = ultimo_bal.get('Empréstimos e Financiamentos', 0)
            self.metricas['caixa'] = ultimo_bal.get('Caixa e Equivalentes de Caixa', 0)
            self.metricas['divida_liquida'] = self.metricas['divida_bruta'] - self.metricas['caixa']
            
            # Adicionar mais métricas do balanço
            self.metricas['ativo_circulante'] = ultimo_bal.get('Ativo Circulante', 0)
            self.metricas['passivo_circulante'] = ultimo_bal.get('Passivo Circulante', 0)
            self.metricas['estoques'] = ultimo_bal.get('Estoques', 0)
            self.metricas['contas_receber'] = ultimo_bal.get('Contas a Receber', 0)
            self.metricas['fornecedores'] = ultimo_bal.get('Fornecedores', 0)
            self.metricas['imobilizado'] = ultimo_bal.get('Imobilizado', 0)
            
            # Tentar obter EBITDA (se não disponível, estimar)
            self.metricas['ebitda'] = ultimo_dre.get('EBITDA', 0)
            if self.metricas['ebitda'] == 0:
                # Estimar EBITDA = EBIT + Depreciação
                depreciacao = ultimo_dre.get('Depreciação e Amortização', 0)
                if depreciacao == 0 and self.metricas['receita_liquida'] > 0:
                    # Estimativa: 5% da receita para empresas industriais
                    depreciacao = self.metricas['receita_liquida'] * 0.05
                self.metricas['ebitda'] = self.metricas['ebit'] + abs(depreciacao)
            
            # Capital de Giro
            self.metricas['capital_giro'] = self.metricas['ativo_circulante'] - self.metricas['passivo_circulante']
            self.metricas['ncg'] = (self.metricas['contas_receber'] + self.metricas['estoques']) - self.metricas['fornecedores']
            
            # ROIC - Return on Invested Capital
            capital_investido = self.metricas['patrimonio_liquido'] + self.metricas['divida_liquida']
            if capital_investido > 0:
                self.metricas['roic'] = (self.metricas['ebit'] * 0.66 / capital_investido) * 100  # Assumindo alíquota de 34%
            
            # Margens
            if self.metricas['receita_liquida'] > 0:
                self.metricas['margem_bruta'] = (self.metricas['lucro_bruto'] / self.metricas['receita_liquida']) * 100
                self.metricas['margem_liquida'] = (self.metricas['lucro_liquido'] / self.metricas['receita_liquida']) * 100
                self.metricas['margem_ebit'] = (self.metricas['ebit'] / self.metricas['receita_liquida']) * 100
                self.metricas['margem_ebitda'] = (self.metricas['ebitda'] / self.metricas['receita_liquida']) * 100
            
            # Rentabilidade
            if self.metricas['patrimonio_liquido'] > 0:
                self.metricas['roe'] = (self.metricas['lucro_liquido'] / self.metricas['patrimonio_liquido']) * 100
            
            if self.metricas['ativo_total'] > 0:
                self.metricas['roa'] = (self.metricas['lucro_liquido'] / self.metricas['ativo_total']) * 100
                self.metricas['roi'] = (self.metricas['ebit'] / self.metricas['ativo_total']) * 100
            
            # Liquidez
            if self.metricas['passivo_circulante'] > 0:
                self.metricas['liquidez_corrente'] = self.metricas['ativo_circulante'] / self.metricas['passivo_circulante']
                self.metricas['liquidez_seca'] = (self.metricas['ativo_circulante'] - self.metricas['estoques']) / self.metricas['passivo_circulante']
            
            # Alavancagem
            if self.metricas['patrimonio_liquido'] > 0:
                self.metricas['divida_pl'] = self.metricas['divida_liquida'] / self.metricas['patrimonio_liquido']
                self.metricas['pl_ativos'] = self.metricas['patrimonio_liquido'] / self.metricas['ativo_total']
            
            if self.metricas['ebit'] > 0:
                self.metricas['divida_ebit'] = self.metricas['divida_liquida'] / self.metricas['ebit']
                # ICJ - Índice de Cobertura de Juros
                if self.metricas['resultado_financeiro'] < 0:
                    self.metricas['icj'] = self.metricas['ebit'] / abs(self.metricas['resultado_financeiro'])
            
            if self.metricas['ebitda'] > 0:
                self.metricas['divida_ebitda'] = self.metricas['divida_liquida'] / self.metricas['ebitda']
            
            # Processar DFC se disponível
            if not self.dfc.empty:
                ultimo_dfc = self.dfc.iloc[-1]
                self.metricas['fluxo_caixa_operacional'] = ultimo_dfc.get('Caixa Líquido Atividades Operacionais', 0)
                self.metricas['capex'] = abs(ultimo_dfc.get('Aquisições de Ativo Imobilizado', 0))
                self.metricas['fcf'] = self.metricas['fluxo_caixa_operacional'] - self.metricas['capex']
                
        except Exception as e:
            print(f"Erro ao calcular métricas: {e}")
    
    def calcular_indicadores_prazos(self):
        """Calcula indicadores de prazos médios"""
        if self.metricas.get('receita_liquida', 0) == 0:
            return
        
        # PMR - Prazo Médio de Recebimento
        if self.metricas.get('contas_receber', 0) > 0:
            self.indicadores_prazos['pmr'] = (self.metricas['contas_receber'] / self.metricas['receita_liquida']) * 365
        
        # PME - Prazo Médio de Estocagem
        if self.metricas.get('estoques', 0) > 0 and self.metricas.get('custos', 0) > 0:
            self.indicadores_prazos['pme'] = (self.metricas['estoques'] / self.metricas['custos']) * 365
        
        # PMP - Prazo Médio de Pagamento
        if self.metricas.get('fornecedores', 0) > 0 and self.metricas.get('custos', 0) > 0:
            self.indicadores_prazos['pmp'] = (self.metricas['fornecedores'] / self.metricas['custos']) * 365
        
        # Ciclo Operacional e Ciclo de Caixa
        if 'pmr' in self.indicadores_prazos and 'pme' in self.indicadores_prazos:
            self.indicadores_prazos['ciclo_operacional'] = self.indicadores_prazos['pmr'] + self.indicadores_prazos['pme']
            
            if 'pmp' in self.indicadores_prazos:
                self.indicadores_prazos['ciclo_caixa'] = self.indicadores_prazos['ciclo_operacional'] - self.indicadores_prazos['pmp']
    
    def estimar_multiplos(self, preco_acao=None, num_acoes=None, dividendos_12m=None):
        """Estima múltiplos de mercado"""
        if not preco_acao:
            print("Aviso: Preço da ação não fornecido. Múltiplos de mercado não calculados.")
            return
        
        if not num_acoes:
            # Tentar estimar número de ações (simplificado)
            num_acoes = 1_000_000_000  # Placeholder - idealmente buscar o valor real
        
        market_cap = preco_acao * num_acoes
        ev = market_cap + self.metricas.get('divida_liquida', 0)
        
        # P/L (Price-to-Earnings)
        if self.metricas.get('lucro_liquido', 0) > 0:
            self.multiplos['P/L'] = market_cap / self.metricas['lucro_liquido']
        
        # P/S (Price-to-Sales)
        if self.metricas.get('receita_liquida', 0) > 0:
            self.multiplos['P/S'] = market_cap / self.metricas['receita_liquida']
        
        # P/VPA (Price-to-Book)
        if self.metricas.get('patrimonio_liquido', 0) > 0:
            self.multiplos['P/VPA'] = market_cap / self.metricas['patrimonio_liquido']
        
        # P/EBITDA
        if self.metricas.get('ebitda', 0) > 0:
            self.multiplos['P/EBITDA'] = market_cap / self.metricas['ebitda']
        
        # P/ATIVO
        if self.metricas.get('ativo_total', 0) > 0:
            self.multiplos['P/ATIVO'] = market_cap / self.metricas['ativo_total']
        
        # EV/EBIT
        if self.metricas.get('ebit', 0) > 0:
            self.multiplos['EV/EBIT'] = ev / self.metricas['ebit']
        
        # EV/EBITDA
        if self.metricas.get('ebitda', 0) > 0:
            self.multiplos['EV/EBITDA'] = ev / self.metricas['ebitda']
        
        # EV/Receita
        if self.metricas.get('receita_liquida', 0) > 0:
            self.multiplos['EV/Receita'] = ev / self.metricas['receita_liquida']
        
        # P/FCF (Price-to-Free-Cash-Flow)
        if self.metricas.get('fcf', 0) > 0:
            self.multiplos['P/FCF'] = market_cap / self.metricas['fcf']
        
        # EV/FCF
        if self.metricas.get('fcf', 0) > 0:
            self.multiplos['EV/FCF'] = ev / self.metricas['fcf']
        
        # Dividend Yield e Payout (se dividendos fornecidos)
        if dividendos_12m and dividendos_12m > 0:
            self.multiplos['Dividend_Yield'] = (dividendos_12m / preco_acao) * 100
            
            # Payout Ratio
            if self.metricas.get('lucro_liquido', 0) > 0:
                total_dividendos = dividendos_12m * num_acoes
                self.multiplos['Payout'] = (total_dividendos / self.metricas['lucro_liquido']) * 100
        
        # PEG Ratio (simplificado - assumindo crescimento de 10%)
        if self.multiplos.get('P/L', 0) > 0:
            crescimento_estimado = 10  # Placeholder - idealmente calcular CAGR histórico
            self.multiplos['PEG'] = self.multiplos['P/L'] / crescimento_estimado
    
    def calcular_series_temporais(self):
        """Calcula métricas para todos os períodos disponíveis"""
        if not self.analise_temporal or self.bal.empty or self.dre.empty:
            return
        
        print("Calculando séries temporais...")
        
        # Alinhar índices
        datas_comuns = self.bal.index.intersection(self.dre.index)
        
        series = []
        for data in datas_comuns:
            periodo = {
                'data': data,
                'receita_liquida': self.dre.loc[data].get('Receita Líquida', 0),
                'lucro_liquido': self.dre.loc[data].get('Lucro Líquido', 0),
                'ebit': self.dre.loc[data].get('EBIT', 0),
                'patrimonio_liquido': self.bal.loc[data].get('Patrimônio Líquido', 0),
                'ativo_total': self.bal.loc[data].get('Ativo Total', 0)
            }
            
            # Calcular ROE e ROA
            if periodo['patrimonio_liquido'] > 0:
                periodo['roe'] = (periodo['lucro_liquido'] / periodo['patrimonio_liquido']) * 100
            if periodo['ativo_total'] > 0:
                periodo['roa'] = (periodo['lucro_liquido'] / periodo['ativo_total']) * 100
            
            # Margens
            if periodo['receita_liquida'] > 0:
                periodo['margem_liquida'] = (periodo['lucro_liquido'] / periodo['receita_liquida']) * 100
                periodo['margem_ebit'] = (periodo['ebit'] / periodo['receita_liquida']) * 100
            
            series.append(periodo)
        
        self.series_temporais = pd.DataFrame(series).set_index('data').sort_index()
        print(f"Séries temporais calculadas para {len(self.series_temporais)} períodos")
    
    def gerar_relatorio(self, arquivo_saida=None):
        """Gera relatório completo de valuation"""
        # Calcular séries temporais se habilitado
        if self.analise_temporal:
            self.calcular_series_temporais()
        
        relatorio = {
            'empresa': {
                'nome': self.nome,
                'ticker': self.ticker,
                'codigo_cvm': self.codigo_cvm,
                'cnpj': self.cnpj
            },
            'data_analise': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'metricas_financeiras': self.metricas,
            'multiplos': self.multiplos,
            'indicadores_prazos': self.indicadores_prazos,
            'periodo_dados': {
                'inicio': str(self.bal.index.min()) if not self.bal.empty else 'N/A',
                'fim': str(self.bal.index.max()) if not self.bal.empty else 'N/A'
            }
        }
        
        # Adicionar séries temporais se disponível
        if self.analise_temporal and not self.series_temporais.empty:
            relatorio['series_temporais'] = self.series_temporais.to_dict('index')
        
        # Salvar JSON
        if not arquivo_saida:
            arquivo_saida = f"valuation_{self.ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(arquivo_saida, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, indent=2, ensure_ascii=False)
        
        # Exibir resumo
        print(f"\n{'='*60}")
        print(f"RELATÓRIO DE VALUATION - {self.nome} ({self.ticker})")
        print(f"{'='*60}")
        print(f"Código CVM: {self.codigo_cvm}")
        print(f"CNPJ: {self.cnpj}")
        
        # Organizar métricas por categoria
        print("\n[DEMONSTRAÇÕES FINANCEIRAS]")
        print("-" * 40)
        metricas_financeiras = ['receita_liquida', 'lucro_liquido', 'ebit', 'ebitda', 'fcf']
        for metrica in metricas_financeiras:
            if metrica in self.metricas and self.metricas[metrica] != 0:
                valor = self.metricas[metrica]
                nome = metrica.replace('_', ' ').upper()
                print(f"{nome}: R$ {valor/1_000_000:.1f}M")
        
        print("\n[MARGENS E RENTABILIDADE]")
        print("-" * 40)
        for metrica, valor in self.metricas.items():
            if isinstance(valor, (int, float)) and ('margem' in metrica or metrica in ['roe', 'roa', 'roi', 'roic']):
                print(f"{metrica.replace('_', ' ').title()}: {valor:.2f}%")
        
        print("\n[LIQUIDEZ E ENDIVIDAMENTO]")
        print("-" * 40)
        metricas_liquidez = ['liquidez_corrente', 'liquidez_seca', 'divida_pl', 'divida_ebitda', 'icj', 'pl_ativos']
        for metrica in metricas_liquidez:
            if metrica in self.metricas:
                valor = self.metricas[metrica]
                nome = metrica.replace('_', ' ').title()
                if metrica == 'pl_ativos':
                    print(f"{nome}: {valor:.2%}")
                else:
                    print(f"{nome}: {valor:.2f}x")
        
        print("\n[CAPITAL DE GIRO]")
        print("-" * 40)
        metricas_capital = ['capital_giro', 'ncg']
        for metrica in metricas_capital:
            if metrica in self.metricas:
                valor = self.metricas[metrica]
                nome = metrica.replace('_', ' ').upper()
                print(f"{nome}: R$ {valor/1_000_000:.1f}M")
        
        if self.indicadores_prazos:
            print("\n[INDICADORES DE PRAZOS]")
            print("-" * 40)
            for indicador, valor in self.indicadores_prazos.items():
                nome = indicador.replace('_', ' ').upper()
                print(f"{nome}: {valor:.1f} dias")
        
        if self.multiplos:
            print(f"\n[MÚLTIPLOS DE MERCADO]")
            print(f"{'='*40}")
            for multiplo, valor in self.multiplos.items():
                if multiplo in ['Dividend_Yield', 'Payout']:
                    print(f"{multiplo}: {valor:.2f}%")
                else:
                    print(f"{multiplo}: {valor:.2f}x")
        
        if self.analise_temporal and not self.series_temporais.empty:
            print(f"\n[EVOLUÇÃO TEMPORAL - ÚLTIMOS 3 PERÍODOS]")
            print(f"{'='*40}")
            ultimos = self.series_temporais.tail(3)
            
            print("\nReceita Líquida:")
            for data, valor in ultimos['receita_liquida'].items():
                print(f"  {data.strftime('%Y-%m')}: R$ {valor/1_000_000:.1f}M")
            
            if 'margem_liquida' in ultimos.columns:
                print("\nMargem Líquida:")
                for data, valor in ultimos['margem_liquida'].items():
                    print(f"  {data.strftime('%Y-%m')}: {valor:.1f}%")
            
            if 'roe' in ultimos.columns:
                print("\nROE:")
                for data, valor in ultimos['roe'].items():
                    print(f"  {data.strftime('%Y-%m')}: {valor:.1f}%")
        
        print(f"\nRelatório salvo em: {arquivo_saida}")
        
        return relatorio


def main():
    parser = argparse.ArgumentParser(
        description='Sistema de Valuation para Empresas CVM',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python valuation_empresa.py VALE3
  python valuation_empresa.py "VALE S.A."
  python valuation_empresa.py 4170
  python valuation_empresa.py PETR4 --preco 38.50
        """
    )
    
    parser.add_argument('empresa', help='Ticker, nome ou código CVM da empresa')
    parser.add_argument('--preco', type=float, help='Preço atual da ação')
    parser.add_argument('--acoes', type=float, help='Número de ações (em milhões)')
    parser.add_argument('--dividendo', type=float, help='Dividendo por ação (últimos 12 meses)')
    parser.add_argument('--output', help='Nome do arquivo de saída')
    parser.add_argument('--temporal', action='store_true', help='Incluir análise temporal dos indicadores')
    
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
    
    # Realizar análise
    analyzer = ValuationAnalyzer(empresa, analise_temporal=args.temporal)
    analyzer.calcular_metricas_financeiras()
    analyzer.calcular_indicadores_prazos()
    
    # Calcular múltiplos se preço fornecido
    if args.preco:
        num_acoes = args.acoes * 1_000_000 if args.acoes else None
        analyzer.estimar_multiplos(args.preco, num_acoes, args.dividendo)
    
    # Gerar relatório
    analyzer.gerar_relatorio(args.output)


if __name__ == "__main__":
    main()