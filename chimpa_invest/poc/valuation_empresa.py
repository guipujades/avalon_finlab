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
    """Processa dados CVM baixados para formato compatível com análise"""
    
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
    
    def carregar_balanco_patrimonial(self):
        """Carrega e processa Balanço Patrimonial (Ativo e Passivo)"""
        # Tentar ITR primeiro, depois DFP
        for tipo in ['ITR', 'DFP']:
            if tipo in self.dados_disponiveis:
                base_path = self.dados_disponiveis[tipo]
                
                try:
                    # Extrair ano do caminho
                    ano = base_path.name
                    
                    # Carregar BPA (Ativo)
                    arquivo_bpa = base_path / f'{tipo.lower()}_cia_aberta_BPA_con_{ano}.csv'
                    if not arquivo_bpa.exists():
                        continue
                        
                    bpa = pd.read_csv(arquivo_bpa, encoding='latin-1', sep=';', decimal=',')
                    bpa = bpa[bpa['CD_CVM'] == self.codigo_cvm]
                    bpa['VL_CONTA'] = pd.to_numeric(bpa['VL_CONTA'], errors='coerce')
                    
                    # Carregar BPP (Passivo)
                    arquivo_bpp = base_path / f'{tipo.lower()}_cia_aberta_BPP_con_{ano}.csv'
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
                    # Extrair ano do caminho
                    ano = base_path.name
                    arquivo_dre = base_path / f'{tipo.lower()}_cia_aberta_DRE_con_{ano}.csv'
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
                    # Extrair ano do caminho
                    ano = base_path.name
                    arquivo_dfc = base_path / f'{tipo.lower()}_cia_aberta_DFC_MD_con_{ano}.csv'
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
            self.metricas['passivo_nao_circulante'] = ultimo_bal.get('Passivo Não Circulante', 0)
            self.metricas['estoques'] = ultimo_bal.get('Estoques', 0)
            self.metricas['contas_receber'] = ultimo_bal.get('Contas a Receber', 0)
            self.metricas['fornecedores'] = ultimo_bal.get('Fornecedores', 0)
            self.metricas['imobilizado'] = ultimo_bal.get('Imobilizado', 0)
            
            # Métricas específicas metodologia Insper
            self.metricas['passivo_total'] = self.metricas['passivo_circulante'] + self.metricas['passivo_nao_circulante']
            self.metricas['passivo_financeiro'] = self.metricas['divida_bruta']
            self.metricas['passivo_operacional'] = self.metricas['passivo_total'] - self.metricas['passivo_financeiro']
            self.metricas['ativo_liquido'] = self.metricas['ativo_total'] - self.metricas['passivo_operacional']
            
            # Lucro ativo (metodologia Insper)
            self.metricas['despesas_financeiras'] = abs(self.metricas['resultado_financeiro']) if self.metricas['resultado_financeiro'] < 0 else 0
            self.metricas['lucro_ativo'] = self.metricas['lucro_liquido'] + self.metricas['despesas_financeiras']
            
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
            
            # ROIC - Return on Invested Capital (metodologia Insper: sem ajuste de IR)
            capital_investido = self.metricas['patrimonio_liquido'] + self.metricas['divida_liquida']
            if capital_investido > 0:
                self.metricas['roic'] = (self.metricas['ebit'] / capital_investido) * 100
            
            # Margens
            if self.metricas['receita_liquida'] > 0:
                self.metricas['margem_bruta'] = (self.metricas['lucro_bruto'] / self.metricas['receita_liquida']) * 100
                self.metricas['margem_liquida'] = (self.metricas['lucro_liquido'] / self.metricas['receita_liquida']) * 100
                self.metricas['margem_ebit'] = (self.metricas['ebit'] / self.metricas['receita_liquida']) * 100
                self.metricas['margem_ebitda'] = (self.metricas['ebitda'] / self.metricas['receita_liquida']) * 100
            
            # Rentabilidade (metodologia Insper)
            if self.metricas['patrimonio_liquido'] > 0:
                self.metricas['roe'] = (self.metricas['lucro_liquido'] / self.metricas['patrimonio_liquido']) * 100
            
            if self.metricas['ativo_total'] > 0:
                self.metricas['roa'] = (self.metricas['lucro_liquido'] / self.metricas['ativo_total']) * 100
            
            # ROI específico Insper: lucro_ativo / ativo_liquido
            if self.metricas['ativo_liquido'] > 0:
                self.metricas['roi'] = (self.metricas['lucro_ativo'] / self.metricas['ativo_liquido']) * 100
            
            # Liquidez
            if self.metricas['passivo_circulante'] > 0:
                self.metricas['liquidez_corrente'] = self.metricas['ativo_circulante'] / self.metricas['passivo_circulante']
                self.metricas['liquidez_seca'] = (self.metricas['ativo_circulante'] - self.metricas['estoques']) / self.metricas['passivo_circulante']
            
            # Alavancagem (metodologia Insper)
            if self.metricas['patrimonio_liquido'] > 0:
                self.metricas['divida_pl'] = self.metricas['divida_liquida'] / self.metricas['patrimonio_liquido']
                self.metricas['pl_ativos'] = self.metricas['patrimonio_liquido'] / self.metricas['ativo_total']
            
            # Passivos/Ativos (específico Insper)
            if self.metricas['ativo_total'] > 0:
                self.metricas['passivos_ativos'] = self.metricas['passivo_total'] / self.metricas['ativo_total']
            
            if self.metricas['ebit'] > 0:
                self.metricas['divida_ebit'] = self.metricas['divida_liquida'] / self.metricas['ebit']
                # ICJ - Índice de Cobertura de Juros (metodologia Insper)
                if self.metricas['despesas_financeiras'] > 0:
                    self.metricas['icj'] = self.metricas['ebit'] / self.metricas['despesas_financeiras']
            
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
        """Calcula indicadores de prazos médios seguindo metodologia Insper"""
        if self.metricas.get('receita_liquida', 0) == 0:
            return
        
        # PMR - Prazo Médio de Recebimento (metodologia Insper: 360 dias)
        if self.metricas.get('contas_receber', 0) > 0:
            self.indicadores_prazos['pmr'] = (self.metricas['contas_receber'] * 360) / self.metricas['receita_liquida']
        
        # PME - Prazo Médio de Estocagem (metodologia Insper: 360 dias)
        if self.metricas.get('estoques', 0) > 0 and self.metricas.get('custos', 0) > 0:
            self.indicadores_prazos['pme'] = (self.metricas['estoques'] * 360) / self.metricas['custos']
        
        # PMP - Prazo Médio de Pagamento (metodologia Insper: 360 dias)
        if self.metricas.get('fornecedores', 0) > 0 and self.metricas.get('custos', 0) > 0:
            self.indicadores_prazos['pmp'] = (self.metricas['fornecedores'] * 360) / self.metricas['custos']
        
        # Ciclo Operacional e Ciclo de Caixa (metodologia Insper)
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
    
    def buscar_dados_mercado_perplexity(self):
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
                'multiplos_setor': f"Quais os múltiplos P/L e EV/EBITDA médios do setor de {self.nome} no Brasil em 2024?",
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
                    resposta = input(f"\n Ações: [E]nviar / [M]odificar / [P]ular (E/M/P): ").upper().strip()
                    
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
                                print(f"\n[FONTES] FONTES ({len(response_data['citations'])}):")
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
            
            print(f"\n📊 RESUMO FINAL:")
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
    
    def gerar_relatorio(self, arquivo_saida=None, incluir_mercado=False):
        """Gera relatório completo de valuation"""
        # Calcular séries temporais se habilitado
        if self.analise_temporal:
            self.calcular_series_temporais()
        
        # Buscar dados de mercado se solicitado
        dados_mercado = {}
        if incluir_mercado:
            dados_mercado = self.buscar_dados_mercado_perplexity()
        
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
            'dados_mercado': dados_mercado,  # NOVO: Dados do Perplexity
            'periodo_dados': {
                'inicio': str(self.bal.index.min()) if not self.bal.empty else 'N/A',
                'fim': str(self.bal.index.max()) if not self.bal.empty else 'N/A'
            }
        }
        
        # Adicionar séries temporais se disponível
        if self.analise_temporal and not self.series_temporais.empty:
            relatorio['series_temporais'] = self.series_temporais.to_dict('index')
        
        # Criar pasta data se não existir
        script_dir = Path(__file__).parent
        data_dir = script_dir / 'data'
        data_dir.mkdir(exist_ok=True)
        
        # Salvar JSON
        if not arquivo_saida:
            arquivo_saida = data_dir / f"valuation_{self.ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
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
        
        print("\n[LIQUIDEZ E ENDIVIDAMENTO - METODOLOGIA INSPER]")
        print("-" * 40)
        metricas_liquidez = ['liquidez_corrente', 'liquidez_seca', 'divida_pl', 'divida_ebitda', 'icj', 'pl_ativos', 'passivos_ativos']
        for metrica in metricas_liquidez:
            if metrica in self.metricas:
                valor = self.metricas[metrica]
                nome = metrica.replace('_', ' ').title()
                if metrica in ['pl_ativos', 'passivos_ativos']:
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
        
        print("\n[MÉTRICAS ESPECÍFICAS INSPER]")
        print("-" * 40)
        metricas_insper = ['ativo_liquido', 'passivo_operacional', 'passivo_financeiro', 'lucro_ativo', 'despesas_financeiras']
        for metrica in metricas_insper:
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
    parser.add_argument('--mercado', action='store_true', help='Incluir dados de mercado via Perplexity (interativo)')
    
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
    analyzer.gerar_relatorio(args.output, incluir_mercado=args.mercado)


if __name__ == "__main__":
    main()