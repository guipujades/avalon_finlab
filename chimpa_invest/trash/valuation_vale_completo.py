#!/usr/bin/env python3
"""
Valuation VALE - Versão Completa
================================
Adaptação do valuation_multiples_2.0.py para usar dados CVM baixados.
Análise completa de múltiplos, indicadores e rentabilidade.
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

pd.options.display.float_format = '{:.3f}'.format

# Configurações VALE
CODIGO_CVM_VALE = 4170
CNPJ_VALE = '33.592.510/0001-54'
TICKER_VALE = 'VALE3'


class CVMDataProcessor:
    """
    Processa dados CVM baixados para formato compatível com análise.
    """
    
    def __init__(self, codigo_cvm, base_path='documents/cvm_estruturados/ITR/itr_cia_aberta_2025'):
        self.codigo_cvm = int(codigo_cvm)
        self.base_path = Path(base_path)
        
    def carregar_balanco_patrimonial(self):
        """
        Carrega e processa Balanço Patrimonial (Ativo e Passivo).
        """
        # Carregar BPA (Ativo)
        bpa = pd.read_csv(
            self.base_path / 'itr_cia_aberta_BPA_con_2025.csv',
            encoding='latin-1', sep=';', decimal=','
        )
        bpa = bpa[bpa['CD_CVM'] == self.codigo_cvm]
        # Converter VL_CONTA para numérico
        bpa['VL_CONTA'] = pd.to_numeric(bpa['VL_CONTA'], errors='coerce')
        
        # Carregar BPP (Passivo)
        bpp = pd.read_csv(
            self.base_path / 'itr_cia_aberta_BPP_con_2025.csv',
            encoding='latin-1', sep=';', decimal=','
        )
        bpp = bpp[bpp['CD_CVM'] == self.codigo_cvm]
        # Converter VL_CONTA para numérico
        bpp['VL_CONTA'] = pd.to_numeric(bpp['VL_CONTA'], errors='coerce')
        
        # Combinar e pivotar para formato de análise
        bal_completo = pd.concat([bpa, bpp])
        
        # Criar DataFrame estruturado por data e conta
        bal_pivot = bal_completo.pivot_table(
            index='DT_REFER',
            columns='DS_CONTA',
            values='VL_CONTA',
            aggfunc='first'
        )
        
        # Converter índice para datetime
        bal_pivot.index = pd.to_datetime(bal_pivot.index)
        
        # Adicionar colunas essenciais se não existirem
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
        
        # Mapear contas por código
        for nome, codigo in colunas_essenciais.items():
            dados_conta = bal_completo[bal_completo['CD_CONTA'] == codigo]
            if not dados_conta.empty:
                for _, row in dados_conta.iterrows():
                    bal_pivot.loc[pd.to_datetime(row['DT_REFER']), nome] = row['VL_CONTA']
        
        return bal_pivot
    
    def carregar_dre(self):
        """
        Carrega e processa DRE.
        """
        dre = pd.read_csv(
            self.base_path / 'itr_cia_aberta_DRE_con_2025.csv',
            encoding='latin-1', sep=';', decimal=','
        )
        dre = dre[dre['CD_CVM'] == self.codigo_cvm]
        # Converter VL_CONTA para numérico
        dre['VL_CONTA'] = pd.to_numeric(dre['VL_CONTA'], errors='coerce')
        
        # Pivotar para formato de análise
        dre_pivot = dre.pivot_table(
            index='DT_REFER',
            columns='DS_CONTA',
            values='VL_CONTA',
            aggfunc='first'
        )
        
        dre_pivot.index = pd.to_datetime(dre_pivot.index)
        
        # Mapear contas essenciais
        colunas_dre = {
            'Receita Líquida de Vendas e/ou Serviços': '3.01',
            'Custo de Bens e/ou Serviços Vendidos': '3.02',
            'Resultado Bruto': '3.03',
            'Despesas/Receitas Operacionais': '3.04',
            'Resultado Antes do Resultado Financeiro e dos Tributos': '3.05',
            'Resultado Financeiro': '3.06',
            'Despesas Financeiras': '3.06.02',
            'Resultado Antes dos Tributos sobre o Lucro': '3.07',
            'Lucro/Prejuízo do Período': '3.11'
        }
        
        for nome, codigo in colunas_dre.items():
            dados_conta = dre[dre['CD_CONTA'] == codigo]
            if not dados_conta.empty:
                for _, row in dados_conta.iterrows():
                    dre_pivot.loc[pd.to_datetime(row['DT_REFER']), nome] = row['VL_CONTA']
        
        return dre_pivot
    
    def carregar_dfc(self):
        """
        Carrega Demonstração de Fluxo de Caixa.
        """
        try:
            dfc = pd.read_csv(
                self.base_path / 'itr_cia_aberta_DFC_MD_con_2025.csv',
                encoding='latin-1', sep=';', decimal=','
            )
            dfc = dfc[dfc['CD_CVM'] == self.codigo_cvm]
            # Converter VL_CONTA para numérico
            dfc['VL_CONTA'] = pd.to_numeric(dfc['VL_CONTA'], errors='coerce')
            
            dfc_pivot = dfc.pivot_table(
                index='DT_REFER',
                columns='DS_CONTA',
                values='VL_CONTA',
                aggfunc='first'
            )
            
            dfc_pivot.index = pd.to_datetime(dfc_pivot.index)
            return dfc_pivot
        except:
            return pd.DataFrame()


class ValuationAnalysis:
    """
    Análise completa de valuation baseada no código original.
    """
    
    def __init__(self, ticker='VALE3', codigo_cvm=4170):
        self.ticker = ticker
        self.codigo_cvm = codigo_cvm
        self.processor = CVMDataProcessor(codigo_cvm)
        
        # DataFrames principais
        self.bal_consolidado = None
        self.dre_consolidado = None
        self.dfc_consolidado = None
        
        # Resultados
        self.indicadores = {}
        
    def carregar_dados(self):
        """
        Carrega todos os dados necessários.
        """
        print(f"📂 Carregando dados CVM para {self.ticker}...")
        
        self.bal_consolidado = self.processor.carregar_balanco_patrimonial()
        self.dre_consolidado = self.processor.carregar_dre()
        self.dfc_consolidado = self.processor.carregar_dfc()
        
        # Consolidar por ano (usar último trimestre)
        self.bal_anual = self.bal_consolidado.groupby(self.bal_consolidado.index.year).last()
        self.dre_anual = self.dre_consolidado.groupby(self.dre_consolidado.index.year).sum()
        
        print(f"✅ Dados carregados: {len(self.bal_anual)} anos")
        
    def analise_estrutura_capital(self):
        """
        Análise da estrutura de capital e liquidez.
        """
        print("\n📊 ANÁLISE DA ESTRUTURA DE CAPITAL")
        print("=" * 60)
        
        # Magnitude de investimentos
        investimentos = self.bal_anual['Ativo Total']
        crescimento = investimentos.pct_change()
        
        print(f"\n💼 Evolução do Ativo Total:")
        for ano in investimentos.index[-3:]:
            print(f"   {ano}: R$ {investimentos[ano]/1000000:,.1f} bilhões")
        
        # Análise vertical dos ativos
        ativo_circulante_pct = self.bal_anual['Ativo Circulante'] / self.bal_anual['Ativo Total']
        ativo_nao_circulante_pct = self.bal_anual['Ativo Não Circulante'] / self.bal_anual['Ativo Total']
        
        print(f"\n📊 Composição do Ativo (último ano):")
        print(f"   Circulante: {ativo_circulante_pct.iloc[-1]*100:.1f}%")
        print(f"   Não Circulante: {ativo_nao_circulante_pct.iloc[-1]*100:.1f}%")
        
        # Capital de Giro Líquido
        cgl = self.bal_anual['Ativo Circulante'] - self.bal_anual['Passivo Circulante']
        
        # Índice de Liquidez Corrente
        ilc = self.bal_anual['Ativo Circulante'] / self.bal_anual['Passivo Circulante']
        
        print(f"\n💧 Indicadores de Liquidez:")
        print(f"   Liquidez Corrente: {ilc.iloc[-1]:.2f}")
        print(f"   Capital de Giro: R$ {cgl.iloc[-1]/1000000:,.1f} bilhões")
        
        # Índice de Endividamento
        if 'Empréstimos e Financiamentos' in self.bal_anual.columns:
            divida_total = self.bal_anual['Empréstimos e Financiamentos']
            ind_endividamento = divida_total / self.bal_anual['Ativo Total']
            print(f"\n💰 Endividamento:")
            print(f"   Dívida/Ativo Total: {ind_endividamento.iloc[-1]*100:.1f}%")
        
        # Multiplicador de Capital Próprio
        mult_k_proprio = self.bal_anual['Ativo Total'] / self.bal_anual['Patrimônio Líquido']
        print(f"   Alavancagem: {mult_k_proprio.iloc[-1]:.2f}x")
        
        self.indicadores['estrutura_capital'] = {
            'crescimento_ativo': crescimento.iloc[-1] if len(crescimento) > 0 else 0,
            'liquidez_corrente': ilc.iloc[-1],
            'capital_giro': cgl.iloc[-1],
            'multiplicador_capital': mult_k_proprio.iloc[-1]
        }
        
    def analise_rentabilidade(self):
        """
        Análise de rentabilidade e margens.
        """
        print("\n📊 ANÁLISE DE RENTABILIDADE")
        print("=" * 60)
        
        # Receita Líquida
        receita = self.dre_anual.get('Receita Líquida de Vendas e/ou Serviços', pd.Series())
        if receita.empty:
            print("⚠️  Dados de receita não encontrados")
            return
        
        # Crescimento da Receita
        cresc_receita = receita.pct_change()
        
        print(f"\n💵 Evolução da Receita:")
        for ano in receita.index[-3:]:
            print(f"   {ano}: R$ {receita[ano]/1000000:,.1f} bilhões", end='')
            if ano > receita.index[0]:
                print(f" ({cresc_receita[ano]*100:+.1f}%)")
            else:
                print()
        
        # Lucro Bruto e Margem Bruta
        lucro_bruto = self.dre_anual.get('Resultado Bruto', pd.Series())
        if not lucro_bruto.empty:
            margem_bruta = lucro_bruto / receita
            print(f"\n📈 Margem Bruta:")
            for ano in margem_bruta.index[-3:]:
                print(f"   {ano}: {margem_bruta[ano]*100:.1f}%")
        
        # EBIT (Resultado Operacional)
        ebit = self.dre_anual.get('Resultado Antes do Resultado Financeiro e dos Tributos', pd.Series())
        if not ebit.empty:
            margem_operacional = ebit / receita
            print(f"\n📈 Margem Operacional (EBIT):")
            for ano in margem_operacional.index[-3:]:
                print(f"   {ano}: {margem_operacional[ano]*100:.1f}%")
        
        # Lucro Líquido
        lucro_liquido = self.dre_anual.get('Lucro/Prejuízo do Período', pd.Series())
        if not lucro_liquido.empty:
            margem_liquida = lucro_liquido / receita
            print(f"\n📈 Margem Líquida:")
            for ano in margem_liquida.index[-3:]:
                print(f"   {ano}: {margem_liquida[ano]*100:.1f}%")
        
        # ROE - Return on Equity
        roe = lucro_liquido / self.bal_anual['Patrimônio Líquido']
        print(f"\n💎 ROE (Retorno sobre PL):")
        for ano in roe.index[-3:]:
            print(f"   {ano}: {roe[ano]*100:.1f}%")
        
        # ROA - Return on Assets
        roa = lucro_liquido / self.bal_anual['Ativo Total']
        print(f"\n💰 ROA (Retorno sobre Ativos):")
        for ano in roa.index[-3:]:
            print(f"   {ano}: {roa[ano]*100:.1f}%")
        
        # ROIC - Return on Invested Capital
        if not ebit.empty and 'Empréstimos e Financiamentos' in self.bal_anual.columns:
            capital_investido = self.bal_anual['Patrimônio Líquido'] + self.bal_anual['Empréstimos e Financiamentos']
            roic = ebit * (1 - 0.34) / capital_investido  # Assumindo 34% de imposto
            print(f"\n🎯 ROIC (Retorno sobre Capital Investido):")
            for ano in roic.index[-3:]:
                print(f"   {ano}: {roic[ano]*100:.1f}%")
        
        self.indicadores['rentabilidade'] = {
            'margem_bruta': margem_bruta.iloc[-1] if 'margem_bruta' in locals() else 0,
            'margem_operacional': margem_operacional.iloc[-1] if 'margem_operacional' in locals() else 0,
            'margem_liquida': margem_liquida.iloc[-1] if 'margem_liquida' in locals() else 0,
            'roe': roe.iloc[-1],
            'roa': roa.iloc[-1],
            'roic': roic.iloc[-1] if 'roic' in locals() else 0
        }
    
    def analise_dupont(self):
        """
        Análise DuPont do ROE.
        """
        print("\n📊 ANÁLISE DUPONT")
        print("=" * 60)
        
        # Componentes DuPont
        receita = self.dre_anual.get('Receita Líquida de Vendas e/ou Serviços', pd.Series())
        lucro_liquido = self.dre_anual.get('Lucro/Prejuízo do Período', pd.Series())
        
        if not receita.empty and not lucro_liquido.empty:
            # Margem Líquida
            margem_liquida = lucro_liquido / receita
            
            # Giro do Ativo
            giro_ativo = receita / self.bal_anual['Ativo Total']
            
            # Multiplicador de Alavancagem
            alavancagem = self.bal_anual['Ativo Total'] / self.bal_anual['Patrimônio Líquido']
            
            # ROE = Margem × Giro × Alavancagem
            roe_dupont = margem_liquida * giro_ativo * alavancagem
            
            ano = self.bal_anual.index[-1]
            print(f"\n📅 Decomposição do ROE ({ano}):")
            print(f"   Margem Líquida: {margem_liquida.iloc[-1]*100:.1f}%")
            print(f"   × Giro do Ativo: {giro_ativo.iloc[-1]:.2f}x")
            print(f"   × Alavancagem: {alavancagem.iloc[-1]:.2f}x")
            print(f"   = ROE: {roe_dupont.iloc[-1]*100:.1f}%")
    
    def analise_ciclo_operacional(self):
        """
        Análise de prazos e ciclo operacional.
        """
        print("\n📊 ANÁLISE DO CICLO OPERACIONAL")
        print("=" * 60)
        
        receita = self.dre_anual.get('Receita Líquida de Vendas e/ou Serviços', pd.Series())
        custo_vendas = abs(self.dre_anual.get('Custo de Bens e/ou Serviços Vendidos', pd.Series()))
        
        if not receita.empty and not custo_vendas.empty:
            # PMR - Prazo Médio de Recebimento
            if 'Contas a Receber' in self.bal_anual.columns:
                contas_receber = self.bal_anual['Contas a Receber']
                pmr = (contas_receber * 360) / receita
                print(f"\n📅 Prazo Médio de Recebimento:")
                for ano in pmr.index[-3:]:
                    print(f"   {ano}: {pmr[ano]:.0f} dias")
            
            # PME - Prazo Médio de Estocagem
            if 'Estoques' in self.bal_anual.columns:
                estoques = self.bal_anual['Estoques']
                pme = (estoques * 360) / custo_vendas
                print(f"\n📦 Prazo Médio de Estocagem:")
                for ano in pme.index[-3:]:
                    print(f"   {ano}: {pme[ano]:.0f} dias")
            
            # PMP - Prazo Médio de Pagamento
            if 'Fornecedores' in self.bal_anual.columns:
                fornecedores = self.bal_anual['Fornecedores']
                pmp = (fornecedores * 360) / custo_vendas
                print(f"\n💳 Prazo Médio de Pagamento:")
                for ano in pmp.index[-3:]:
                    print(f"   {ano}: {pmp[ano]:.0f} dias")
                
                # Ciclo de Caixa
                if 'pmr' in locals() and 'pme' in locals():
                    ciclo_caixa = pmr + pme - pmp
                    print(f"\n🔄 Ciclo de Caixa:")
                    for ano in ciclo_caixa.index[-3:]:
                        print(f"   {ano}: {ciclo_caixa[ano]:.0f} dias")
    
    def analise_fluxo_caixa(self):
        """
        Análise completa de fluxo de caixa e geração de valor.
        """
        print("\n📊 ANÁLISE DE FLUXO DE CAIXA E GERAÇÃO DE VALOR")
        print("=" * 60)
        
        # EBITDA
        ebit = self.dre_anual.get('Resultado Antes do Resultado Financeiro e dos Tributos', pd.Series())
        
        # Tentar encontrar depreciação na DFC
        if not self.dfc_consolidado.empty:
            # Procurar depreciação/amortização
            depreciacao = pd.Series(index=ebit.index, data=0)
            for col in self.dfc_consolidado.columns:
                if 'deprecia' in col.lower() or 'amortiza' in col.lower():
                    depreciacao = self.dfc_consolidado.groupby(self.dfc_consolidado.index.year)[col].sum()
                    break
        else:
            # Estimativa: 5% do ativo imobilizado
            if 'Imobilizado' in self.bal_anual.columns:
                depreciacao = self.bal_anual['Imobilizado'] * 0.05
            else:
                depreciacao = pd.Series(index=ebit.index, data=0)
        
        # EBITDA = EBIT + Depreciação
        ebitda = ebit + depreciacao
        
        # Margem EBITDA
        receita = self.dre_anual.get('Receita Líquida de Vendas e/ou Serviços', pd.Series())
        margem_ebitda = ebitda / receita
        
        print(f"\n💰 EBITDA:")
        for ano in ebitda.index[-3:]:
            print(f"   {ano}: R$ {ebitda[ano]/1000000:,.1f} bilhões (Margem: {margem_ebitda[ano]*100:.1f}%)")
        
        # NOPAT (Net Operating Profit After Tax)
        taxa_imposto = 0.34
        nopat = ebit * (1 - taxa_imposto)
        
        print(f"\n📊 NOPAT (Lucro Operacional Após Impostos):")
        for ano in nopat.index[-3:]:
            print(f"   {ano}: R$ {nopat[ano]/1000000:,.1f} bilhões")
        
        # Free Cash Flow to Firm (FCFF)
        # FCFF = NOPAT + Depreciação - CAPEX - ΔCapital de Giro
        
        # CAPEX (estimativa baseada na variação do imobilizado)
        if 'Imobilizado' in self.bal_anual.columns:
            capex = -self.bal_anual['Imobilizado'].diff()
            capex.iloc[0] = 0
        else:
            capex = pd.Series(index=nopat.index, data=0)
        
        # Variação do Capital de Giro
        capital_giro = self.bal_anual['Ativo Circulante'] - self.bal_anual['Passivo Circulante']
        var_capital_giro = -capital_giro.diff()
        var_capital_giro.iloc[0] = 0
        
        # FCFF
        fcff = nopat + depreciacao + capex + var_capital_giro
        
        print(f"\n💸 Free Cash Flow to Firm (FCFF):")
        for ano in fcff.index[-3:]:
            print(f"   {ano}: R$ {fcff[ano]/1000000:,.1f} bilhões")
        
        # Taxa de Conversão EBITDA -> Caixa
        if not ebitda.empty:
            conversao_caixa = fcff / ebitda
            print(f"\n🔄 Taxa de Conversão EBITDA -> FCFF:")
            for ano in conversao_caixa.index[-3:]:
                if not pd.isna(conversao_caixa[ano]) and not np.isinf(conversao_caixa[ano]):
                    print(f"   {ano}: {conversao_caixa[ano]*100:.1f}%")
        
        # Análise de Reinvestimento
        lucro_liquido = self.dre_anual.get('Lucro/Prejuízo do Período', pd.Series())
        
        # Taxa de Reinvestimento = (CAPEX - Depreciação + ΔCG) / NOPAT
        reinvestimento = (-capex + depreciacao - var_capital_giro) / nopat
        
        # Taxa de Crescimento Sustentável = ROE x Taxa de Retenção
        roe = lucro_liquido / self.bal_anual['Patrimônio Líquido']
        
        # Estimativa de payout (seria ideal ter dados reais de dividendos)
        payout_estimado = 0.4  # 40% de payout médio
        taxa_retencao = 1 - payout_estimado
        
        taxa_crescimento_sustentavel = roe * taxa_retencao
        
        print(f"\n📈 Taxa de Crescimento Sustentável:")
        for ano in taxa_crescimento_sustentavel.index[-3:]:
            print(f"   {ano}: {taxa_crescimento_sustentavel[ano]*100:.1f}%")
        
        self.indicadores['fluxo_caixa'] = {
            'ebitda': float(ebitda.iloc[-1]) if not ebitda.empty else 0,
            'margem_ebitda': float(margem_ebitda.iloc[-1]) if not margem_ebitda.empty else 0,
            'nopat': float(nopat.iloc[-1]) if not nopat.empty else 0,
            'fcff': float(fcff.iloc[-1]) if not fcff.empty else 0,
            'taxa_crescimento_sustentavel': float(taxa_crescimento_sustentavel.iloc[-1]) if not taxa_crescimento_sustentavel.empty else 0
        }
    
    def calcular_multiplos_valuation(self):
        """
        Calcula múltiplos de valuation (sem dados de mercado).
        """
        print("\n📊 MÚLTIPLOS DE VALUATION")
        print("=" * 60)
        
        # Dados necessários
        ebitda = self.indicadores.get('fluxo_caixa', {}).get('ebitda', 0)
        lucro_liquido = float(self.dre_anual.get('Lucro/Prejuízo do Período', pd.Series()).iloc[-1]) if 'Lucro/Prejuízo do Período' in self.dre_anual.columns else 0
        patrimonio_liquido = float(self.bal_anual['Patrimônio Líquido'].iloc[-1])
        
        # Dívida Líquida
        caixa = float(self.bal_anual.get('Caixa e Equivalentes de Caixa', pd.Series()).iloc[-1]) if 'Caixa e Equivalentes de Caixa' in self.bal_anual.columns else 0
        divida_bruta = float(self.bal_anual.get('Empréstimos e Financiamentos', pd.Series()).iloc[-1]) if 'Empréstimos e Financiamentos' in self.bal_anual.columns else 0
        divida_liquida = divida_bruta - caixa
        
        print("\n🎯 DADOS PARA CÁLCULO DE MÚLTIPLOS:")
        print(f"   EBITDA: R$ {ebitda/1000000:,.1f} bilhões")
        print(f"   Lucro Líquido: R$ {lucro_liquido/1000000:,.1f} bilhões")
        print(f"   Dívida Líquida: R$ {divida_liquida/1000000:,.1f} bilhões")
        print(f"   Patrimônio Líquido: R$ {patrimonio_liquido/1000000:,.1f} bilhões")
        
        print("\n⚠️  Para calcular múltiplos completos precisamos de:")
        print("   - Valor de Mercado (Market Cap)")
        print("   - Número de ações")
        print("   - Cotação atual")
        
        print("\n📊 Múltiplos que PODERÍAMOS calcular com dados de mercado:")
        print("   - P/L (Preço/Lucro)")
        print("   - EV/EBITDA (Enterprise Value/EBITDA)")
        print("   - P/VPA (Preço/Valor Patrimonial)")
        print("   - EV/Receita")
        print("   - Dividend Yield")
        
        # Preparar dados para quando tivermos cotação
        self.indicadores['dados_para_multiplos'] = {
            'ebitda': ebitda,
            'lucro_liquido': lucro_liquido,
            'divida_liquida': divida_liquida,
            'patrimonio_liquido': patrimonio_liquido,
            'receita_liquida': float(self.dre_anual.get('Receita Líquida de Vendas e/ou Serviços', pd.Series()).iloc[-1]) if 'Receita Líquida de Vendas e/ou Serviços' in self.dre_anual.columns else 0
        }
    
    def gerar_relatorio_completo(self):
        """
        Gera relatório completo em JSON.
        """
        # Executar todas as análises
        self.analise_estrutura_capital()
        self.analise_rentabilidade()
        self.analise_dupont()
        self.analise_ciclo_operacional()
        self.analise_fluxo_caixa()
        self.calcular_multiplos_valuation()
        
        # Compilar relatório
        relatorio = {
            'empresa': self.ticker,
            'codigo_cvm': self.codigo_cvm,
            'data_analise': datetime.now().isoformat(),
            'periodo_analisado': {
                'inicio': str(self.bal_anual.index.min()),
                'fim': str(self.bal_anual.index.max())
            },
            'indicadores': self.indicadores,
            'dados_recentes': {
                'ativo_total': float(self.bal_anual['Ativo Total'].iloc[-1]),
                'patrimonio_liquido': float(self.bal_anual['Patrimônio Líquido'].iloc[-1]),
                'receita_liquida': float(self.dre_anual.get('Receita Líquida de Vendas e/ou Serviços', pd.Series()).iloc[-1]) if 'Receita Líquida de Vendas e/ou Serviços' in self.dre_anual.columns else 0,
                'lucro_liquido': float(self.dre_anual.get('Lucro/Prejuízo do Período', pd.Series()).iloc[-1]) if 'Lucro/Prejuízo do Período' in self.dre_anual.columns else 0
            }
        }
        
        # Salvar
        output_path = Path(f'valuation_completo_VALE_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Relatório completo salvo em: {output_path}")
        
        return relatorio


def main():
    """
    Função principal.
    """
    print("🏭 ANÁLISE COMPLETA DE VALUATION - VALE S.A.")
    print("=" * 70)
    print("Baseado em valuation_multiples_2.0.py")
    print("=" * 70)
    
    # Criar analisador
    vale = ValuationAnalysis(ticker='VALE3', codigo_cvm=4170)
    
    # Carregar dados
    try:
        vale.carregar_dados()
        
        # Gerar relatório completo
        relatorio = vale.gerar_relatorio_completo()
        
        print("\n✅ Análise concluída com sucesso!")
        print("\n📋 RESUMO EXECUTIVO:")
        print(f"   Período analisado: {relatorio['periodo_analisado']['inicio']} a {relatorio['periodo_analisado']['fim']}")
        print(f"   Ativo Total: R$ {relatorio['dados_recentes']['ativo_total']/1000000:,.1f} bilhões")
        print(f"   Patrimônio Líquido: R$ {relatorio['dados_recentes']['patrimonio_liquido']/1000000:,.1f} bilhões")
        
        if relatorio['dados_recentes']['receita_liquida'] > 0:
            print(f"   Receita Líquida: R$ {relatorio['dados_recentes']['receita_liquida']/1000000:,.1f} bilhões")
            print(f"   Lucro Líquido: R$ {relatorio['dados_recentes']['lucro_liquido']/1000000:,.1f} bilhões")
        
    except Exception as e:
        print(f"\n❌ Erro durante análise: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()