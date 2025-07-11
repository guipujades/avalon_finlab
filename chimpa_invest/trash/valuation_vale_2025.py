#!/usr/bin/env python3
"""
Valuation VALE 2025
===================
Script para análise de múltiplos e histórico da VALE usando dados CVM.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json

# Configurações
CODIGO_CVM_VALE = '4170'
CNPJ_VALE = '33.592.510/0001-54'
TICKER_VALE = 'VALE3'

class ValuationVALE:
    """
    Classe para análise de valuation da VALE usando dados CVM.
    """
    
    def __init__(self):
        self.base_path = Path('documents/cvm_estruturados/ITR/itr_cia_aberta_2025')
        self.codigo_cvm = CODIGO_CVM_VALE
        self.cnpj = CNPJ_VALE
        self.ticker = TICKER_VALE
        
        # DataFrames principais
        self.bpa_con = None  # Balanço Patrimonial Ativo Consolidado
        self.bpp_con = None  # Balanço Patrimonial Passivo Consolidado
        self.dre_con = None  # DRE Consolidado
        self.dfc_con = None  # Demonstração Fluxo de Caixa Consolidado
        
    def carregar_dados(self):
        """
        Carrega os dados ITR da VALE.
        """
        print(f"📂 Carregando dados da VALE (CVM: {self.codigo_cvm})...")
        
        try:
            # Balanço Patrimonial Ativo
            self.bpa_con = pd.read_csv(
                self.base_path / 'itr_cia_aberta_BPA_con_2025.csv',
                encoding='latin-1',
                sep=';',
                decimal=','
            )
            self.bpa_con = self.bpa_con[self.bpa_con['CD_CVM'] == int(self.codigo_cvm)]
            
            # Balanço Patrimonial Passivo
            self.bpp_con = pd.read_csv(
                self.base_path / 'itr_cia_aberta_BPP_con_2025.csv',
                encoding='latin-1',
                sep=';',
                decimal=','
            )
            self.bpp_con = self.bpp_con[self.bpp_con['CD_CVM'] == int(self.codigo_cvm)]
            
            # DRE
            self.dre_con = pd.read_csv(
                self.base_path / 'itr_cia_aberta_DRE_con_2025.csv',
                encoding='latin-1',
                sep=';',
                decimal=','
            )
            self.dre_con = self.dre_con[self.dre_con['CD_CVM'] == int(self.codigo_cvm)]
            
            # DFC
            self.dfc_con = pd.read_csv(
                self.base_path / 'itr_cia_aberta_DFC_MD_con_2025.csv',
                encoding='latin-1',
                sep=';',
                decimal=','
            )
            self.dfc_con = self.dfc_con[self.dfc_con['CD_CVM'] == int(self.codigo_cvm)]
            
            print("✅ Dados carregados com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            return False
    
    def analisar_balanco(self):
        """
        Analisa o balanço patrimonial e calcula indicadores.
        """
        print("\n📊 ANÁLISE DO BALANÇO PATRIMONIAL")
        print("=" * 50)
        
        # Filtrar dados mais recentes
        ultima_data = self.bpa_con['DT_REFER'].max()
        
        # Ativo
        ativo_atual = self.bpa_con[self.bpa_con['DT_REFER'] == ultima_data]
        
        # Principais contas do Ativo
        ativo_total = ativo_atual[ativo_atual['CD_CONTA'] == '1'].iloc[0]['VL_CONTA'] if len(ativo_atual[ativo_atual['CD_CONTA'] == '1']) > 0 else 0
        ativo_circulante = ativo_atual[ativo_atual['CD_CONTA'] == '1.01'].iloc[0]['VL_CONTA'] if len(ativo_atual[ativo_atual['CD_CONTA'] == '1.01']) > 0 else 0
        ativo_nao_circulante = ativo_atual[ativo_atual['CD_CONTA'] == '1.02'].iloc[0]['VL_CONTA'] if len(ativo_atual[ativo_atual['CD_CONTA'] == '1.02']) > 0 else 0
        
        # Passivo
        passivo_atual = self.bpp_con[self.bpp_con['DT_REFER'] == ultima_data]
        
        passivo_circulante = passivo_atual[passivo_atual['CD_CONTA'] == '2.01'].iloc[0]['VL_CONTA'] if len(passivo_atual[passivo_atual['CD_CONTA'] == '2.01']) > 0 else 0
        passivo_nao_circulante = passivo_atual[passivo_atual['CD_CONTA'] == '2.02'].iloc[0]['VL_CONTA'] if len(passivo_atual[passivo_atual['CD_CONTA'] == '2.02']) > 0 else 0
        patrimonio_liquido = passivo_atual[passivo_atual['CD_CONTA'] == '2.03'].iloc[0]['VL_CONTA'] if len(passivo_atual[passivo_atual['CD_CONTA'] == '2.03']) > 0 else 0
        
        # Indicadores
        indicadores = {
            'data_referencia': ultima_data,
            'ativo_total': ativo_total,
            'ativo_circulante': ativo_circulante,
            'ativo_nao_circulante': ativo_nao_circulante,
            'passivo_circulante': passivo_circulante,
            'passivo_nao_circulante': passivo_nao_circulante,
            'patrimonio_liquido': patrimonio_liquido,
            'liquidez_corrente': ativo_circulante / passivo_circulante if passivo_circulante > 0 else 0,
            'capital_giro_liquido': ativo_circulante - passivo_circulante,
            'endividamento_geral': (passivo_circulante + passivo_nao_circulante) / ativo_total if ativo_total > 0 else 0,
            'multiplicador_capital': ativo_total / patrimonio_liquido if patrimonio_liquido > 0 else 0
        }
        
        # Exibir resultados
        print(f"📅 Data de Referência: {ultima_data}")
        print(f"\n💰 ESTRUTURA PATRIMONIAL (em milhares R$):")
        print(f"   Ativo Total: R$ {ativo_total:,.0f}")
        print(f"   - Circulante: R$ {ativo_circulante:,.0f} ({ativo_circulante/ativo_total*100:.1f}%)")
        print(f"   - Não Circulante: R$ {ativo_nao_circulante:,.0f} ({ativo_nao_circulante/ativo_total*100:.1f}%)")
        print(f"\n   Patrimônio Líquido: R$ {patrimonio_liquido:,.0f}")
        print(f"   Passivo Total: R$ {passivo_circulante + passivo_nao_circulante:,.0f}")
        
        print(f"\n📈 INDICADORES FINANCEIROS:")
        print(f"   Liquidez Corrente: {indicadores['liquidez_corrente']:.2f}")
        print(f"   Capital de Giro Líquido: R$ {indicadores['capital_giro_liquido']:,.0f}")
        print(f"   Endividamento Geral: {indicadores['endividamento_geral']*100:.1f}%")
        print(f"   Multiplicador de Capital: {indicadores['multiplicador_capital']:.2f}x")
        
        return indicadores
    
    def analisar_dre(self):
        """
        Analisa a DRE e calcula margens.
        """
        print("\n📊 ANÁLISE DA DRE")
        print("=" * 50)
        
        # Filtrar dados mais recentes
        ultima_data = self.dre_con['DT_REFER'].max()
        dre_atual = self.dre_con[self.dre_con['DT_REFER'] == ultima_data]
        
        # Principais linhas da DRE
        receita_liquida = dre_atual[dre_atual['CD_CONTA'] == '3.01'].iloc[0]['VL_CONTA'] if len(dre_atual[dre_atual['CD_CONTA'] == '3.01']) > 0 else 0
        lucro_bruto = dre_atual[dre_atual['CD_CONTA'] == '3.03'].iloc[0]['VL_CONTA'] if len(dre_atual[dre_atual['CD_CONTA'] == '3.03']) > 0 else 0
        lucro_operacional = dre_atual[dre_atual['CD_CONTA'] == '3.05'].iloc[0]['VL_CONTA'] if len(dre_atual[dre_atual['CD_CONTA'] == '3.05']) > 0 else 0
        lucro_liquido = dre_atual[dre_atual['CD_CONTA'] == '3.11'].iloc[0]['VL_CONTA'] if len(dre_atual[dre_atual['CD_CONTA'] == '3.11']) > 0 else 0
        
        # Margens
        margens = {
            'receita_liquida': receita_liquida,
            'lucro_bruto': lucro_bruto,
            'lucro_operacional': lucro_operacional,
            'lucro_liquido': lucro_liquido,
            'margem_bruta': lucro_bruto / receita_liquida * 100 if receita_liquida > 0 else 0,
            'margem_operacional': lucro_operacional / receita_liquida * 100 if receita_liquida > 0 else 0,
            'margem_liquida': lucro_liquido / receita_liquida * 100 if receita_liquida > 0 else 0
        }
        
        print(f"📅 Período: {ultima_data}")
        print(f"\n💵 DEMONSTRAÇÃO DE RESULTADOS (em milhares R$):")
        print(f"   Receita Líquida: R$ {receita_liquida:,.0f}")
        print(f"   Lucro Bruto: R$ {lucro_bruto:,.0f}")
        print(f"   Lucro Operacional: R$ {lucro_operacional:,.0f}")
        print(f"   Lucro Líquido: R$ {lucro_liquido:,.0f}")
        
        print(f"\n📊 MARGENS:")
        print(f"   Margem Bruta: {margens['margem_bruta']:.1f}%")
        print(f"   Margem Operacional: {margens['margem_operacional']:.1f}%")
        print(f"   Margem Líquida: {margens['margem_liquida']:.1f}%")
        
        return margens
    
    def calcular_multiplos(self):
        """
        Calcula múltiplos de valuation.
        """
        print("\n📊 MÚLTIPLOS DE VALUATION")
        print("=" * 50)
        
        # Dados do balanço
        balanco = self.analisar_balanco()
        dre = self.analisar_dre()
        
        # Para cálculo de múltiplos, precisaríamos de:
        # - Valor de mercado (market cap)
        # - Número de ações
        # - Cotação atual
        
        print("\n⚠️  Para calcular múltiplos completos (P/L, EV/EBITDA, etc.)")
        print("   precisamos de dados de mercado (cotação, número de ações).")
        print("   Por enquanto, temos apenas os dados fundamentais da CVM.")
        
        # ROE - Return on Equity
        roe = dre['lucro_liquido'] / balanco['patrimonio_liquido'] * 100 if balanco['patrimonio_liquido'] > 0 else 0
        
        # ROA - Return on Assets
        roa = dre['lucro_liquido'] / balanco['ativo_total'] * 100 if balanco['ativo_total'] > 0 else 0
        
        print(f"\n📈 INDICADORES DE RENTABILIDADE:")
        print(f"   ROE (Retorno sobre PL): {roe:.1f}%")
        print(f"   ROA (Retorno sobre Ativos): {roa:.1f}%")
        
        return {
            'roe': roe,
            'roa': roa
        }
    
    def gerar_relatorio(self):
        """
        Gera relatório completo em JSON.
        """
        relatorio = {
            'empresa': self.ticker,
            'codigo_cvm': self.codigo_cvm,
            'data_analise': datetime.now().isoformat(),
            'balanco': self.analisar_balanco(),
            'dre': self.analisar_dre(),
            'multiplos': self.calcular_multiplos()
        }
        
        # Salvar relatório
        output_path = Path(f'valuation_VALE_{datetime.now().strftime("%Y%m%d")}.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Relatório salvo em: {output_path}")
        
        return relatorio


def main():
    """
    Função principal.
    """
    print("🏭 ANÁLISE DE VALUATION - VALE S.A.")
    print("=" * 60)
    
    # Criar instância do analisador
    vale = ValuationVALE()
    
    # Carregar dados
    if vale.carregar_dados():
        # Executar análises
        vale.analisar_balanco()
        vale.analisar_dre()
        vale.calcular_multiplos()
        vale.gerar_relatorio()
        
        print("\n✅ Análise concluída com sucesso!")
    else:
        print("\n❌ Erro ao processar dados")


if __name__ == "__main__":
    main()