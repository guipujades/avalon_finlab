import pandas as pd
import numpy as np
import os
import zipfile
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from collections import defaultdict
import pickle
import warnings
from pathlib import Path
from typing import Dict, List, Tuple, Optional
warnings.filterwarnings('ignore')

BASE_DIR = Path("C:/Users/guilh/Documents/GitHub/database/funds_cvm")

plt.switch_backend('Agg')

class AnalisadorTemporalFundos:
    def __init__(self, cnpj_fundo: str, nome_fundo: str = "Fundo", periodo_minimo_anos: int = 5):
        self.cnpj_fundo = cnpj_fundo
        self.nome_fundo = nome_fundo
        self.periodo_minimo_anos = periodo_minimo_anos
        self.carteiras_por_periodo = {}
        self.df_evolucao = pd.DataFrame()
        self.df_acoes = pd.DataFrame()
        self.derivativos_info = []
        self.df_cotas = pd.DataFrame()
        self.df_retornos = pd.DataFrame()
        self.output_dir = self._criar_diretorio_saida()
        self.formato_exportacao = 'todos'
    
    def _criar_diretorio_saida(self) -> str:
        """Cria diretório padrão para salvar os dados"""
        cnpj_limpo = self.cnpj_fundo.replace('.', '').replace('/', '').replace('-', '')
        dir_saida = os.path.join('dados', cnpj_limpo)
        os.makedirs(dir_saida, exist_ok=True)
        return dir_saida
        
    def processar_carteiras(self) -> Dict:
        """Processa carteiras do fundo de forma eficiente"""
        cda_dir = os.path.join(BASE_DIR, "CDA")
        
        print(f"Processando dados do fundo {self.nome_fundo} (CNPJ: {self.cnpj_fundo})")
        print(f"Buscando histórico mínimo de {self.periodo_minimo_anos} anos...")
        
        arquivos_cda = []
        
        for arquivo in sorted(os.listdir(cda_dir)):
            if arquivo.startswith("cda_fi_") and arquivo.endswith(".zip"):
                arquivos_cda.append((arquivo, os.path.join(cda_dir, arquivo)))
        
        hist_dir = os.path.join(cda_dir, "HIST")
        if os.path.exists(hist_dir):
            for arquivo in sorted(os.listdir(hist_dir)):
                if arquivo.startswith("cda_fi_") and arquivo.endswith(".zip"):
                    arquivos_cda.append((arquivo, os.path.join(hist_dir, arquivo)))
        
        arquivos_cda.sort()
        
        print(f"Total de arquivos para processar: {len(arquivos_cda)}")
        
        for i, (nome_arquivo, arquivo_path) in enumerate(arquivos_cda):
            try:
                periodo_str = nome_arquivo.replace("cda_fi_", "").replace(".zip", "")
                if len(periodo_str) == 6:
                    periodo = periodo_str[:4] + "-" + periodo_str[4:6]
                elif len(periodo_str) == 4:
                    periodo = periodo_str
                else:
                    continue
                
                dados_periodo = {}
                
                with zipfile.ZipFile(arquivo_path, 'r') as zip_file:
                    for blc_num in range(1, 9):
                        for nome_interno in zip_file.namelist():
                            if f"BLC_{blc_num}" in nome_interno and nome_interno.endswith('.csv'):
                                try:
                                    with zip_file.open(nome_interno) as f:
                                        df = pd.read_csv(f, sep=';', encoding='ISO-8859-1')
                                        
                                        for col in ['CNPJ_FUNDO_CLASSE', 'CNPJ_FUNDO', 'CD_FUNDO']:
                                            if col in df.columns:
                                                df_fundo = df[df[col].astype(str).str.strip() == self.cnpj_fundo]
                                                if not df_fundo.empty:
                                                    dados_periodo[f'BLC_{blc_num}'] = df_fundo
                                                    break
                                                    
                                except Exception as e:
                                    continue
                
                if dados_periodo:
                    self.carteiras_por_periodo[periodo] = dados_periodo
                    
            except Exception as e:
                continue
            
            if (i + 1) % 20 == 0:
                print(f"Processados {i + 1}/{len(arquivos_cda)} arquivos...")
        
        self._filtrar_periodo_minimo()
        
        print(f"\nTotal de períodos com dados: {len(self.carteiras_por_periodo)}")
        return self.carteiras_por_periodo
    
    def _filtrar_periodo_minimo(self):
        """Filtra apenas períodos que atendem ao critério mínimo de anos"""
        if not self.carteiras_por_periodo:
            return
        
        periodos_ordenados = sorted(self.carteiras_por_periodo.keys())
        
        try:
            primeiro_periodo = periodos_ordenados[0]
            ultimo_periodo = periodos_ordenados[-1]
            
            if '-' in primeiro_periodo:
                ano_inicial = int(primeiro_periodo.split('-')[0])
            else:
                ano_inicial = int(primeiro_periodo)
                
            if '-' in ultimo_periodo:
                ano_final = int(ultimo_periodo.split('-')[0])
            else:
                ano_final = int(ultimo_periodo)
            
            anos_disponiveis = ano_final - ano_inicial + 1
            
            if anos_disponiveis < self.periodo_minimo_anos:
                print(f"Aviso: Apenas {anos_disponiveis} anos de dados disponíveis (mínimo solicitado: {self.periodo_minimo_anos})")
            else:
                data_corte = datetime.now() - timedelta(days=365 * self.periodo_minimo_anos)
                ano_corte = data_corte.year
                
                carteiras_filtradas = {}
                for periodo, dados in self.carteiras_por_periodo.items():
                    if '-' in periodo:
                        ano = int(periodo.split('-')[0])
                    else:
                        ano = int(periodo)
                    
                    if ano >= ano_corte:
                        carteiras_filtradas[periodo] = dados
                
                self.carteiras_por_periodo = carteiras_filtradas
                print(f"✓ Dados filtrados para os últimos {self.periodo_minimo_anos} anos")
                
        except Exception as e:
            print(f"Erro ao filtrar períodos: {e}")
    
    def analisar_evolucao_patrimonio(self) -> pd.DataFrame:
        """Analisa a evolução do patrimônio total e por tipo de ativo"""
        evolucao = []
        
        for periodo in sorted(self.carteiras_por_periodo.keys()):
            dados_periodo = {
                'periodo': periodo,
                'titulos_publicos': 0,
                'titulos_bancarios': 0,
                'debentures': 0,
                'acoes': 0,
                'derivativos': 0,
                'cotas_fundos': 0,
                'op_compromissadas': 0,
                'outros': 0,
                'total': 0
            }
            
            blc_map = {
                'BLC_1': 'titulos_publicos',
                'BLC_2': 'titulos_bancarios',
                'BLC_3': 'debentures',
                'BLC_4': 'acoes',
                'BLC_5': 'derivativos',
                'BLC_6': 'cotas_fundos',
                'BLC_7': 'op_compromissadas',
                'BLC_8': 'outros'
            }
            
            for blc, tipo in blc_map.items():
                if blc in self.carteiras_por_periodo[periodo]:
                    df = self.carteiras_por_periodo[periodo][blc]
                    for col in ['VL_MERC_POS_FINAL', 'VL_MERCADO', 'VL_POS_FINAL', 'VL_ATUALIZADO']:
                        if col in df.columns:
                            valor = df[col].sum()
                            dados_periodo[tipo] = valor
                            dados_periodo['total'] += valor
                            break
            
            if dados_periodo['total'] > 0:
                evolucao.append(dados_periodo)
        
        self.df_evolucao = pd.DataFrame(evolucao)
        return self.df_evolucao
    
    def analisar_acoes_detalhado(self) -> pd.DataFrame:
        """Análise detalhada das posições em ações"""
        acoes_por_periodo = []
        
        for periodo in sorted(self.carteiras_por_periodo.keys()):
            if 'BLC_4' in self.carteiras_por_periodo[periodo]:
                df_acoes = self.carteiras_por_periodo[periodo]['BLC_4']
                
                nome_col = None
                for col in ['NM_ATIVO', 'DS_ATIVO', 'CD_ATIVO']:
                    if col in df_acoes.columns:
                        nome_col = col
                        break
                
                valor_col = None
                for col in ['VL_MERC_POS_FINAL', 'VL_MERCADO', 'VL_POS_FINAL']:
                    if col in df_acoes.columns:
                        valor_col = col
                        break
                
                if nome_col and valor_col:
                    resumo = df_acoes.groupby(nome_col).agg({
                        valor_col: 'sum'
                    }).reset_index()
                    resumo['periodo'] = periodo
                    resumo.columns = ['acao', 'valor', 'periodo']
                    acoes_por_periodo.append(resumo)
        
        if acoes_por_periodo:
            return pd.concat(acoes_por_periodo, ignore_index=True)
        return pd.DataFrame()
    
    def analisar_derivativos_detalhado(self) -> List[Dict]:
        """Análise detalhada de derivativos e mercado futuro"""
        derivativos_info = []
        
        for periodo in sorted(self.carteiras_por_periodo.keys()):
            if 'BLC_5' in self.carteiras_por_periodo[periodo]:
                df_deriv = self.carteiras_por_periodo[periodo]['BLC_5']
                
                info = {
                    'periodo': periodo,
                    'total_registros': len(df_deriv),
                    'valor_total': 0,
                    'tipos': {}
                }
                
                for col in ['VL_MERC_POS_FINAL', 'VL_MERCADO', 'VL_POS_FINAL']:
                    if col in df_deriv.columns:
                        info['valor_total'] = df_deriv[col].sum()
                        break
                
                for col in ['TP_DERIVATIVO', 'DS_DERIVATIVO', 'CD_DERIVATIVO']:
                    if col in df_deriv.columns:
                        tipos = df_deriv[col].value_counts().to_dict()
                        info['tipos'] = tipos
                        break
                
                if 'DS_ATIVO' in df_deriv.columns:
                    info['ativos'] = df_deriv['DS_ATIVO'].tolist()
                
                derivativos_info.append(info)
        
        return derivativos_info
    
    def calcular_indicadores_performance(self) -> Dict:
        """Calcula indicadores de performance ao longo do tempo"""
        if self.df_evolucao.empty:
            return {}
        
        indicadores = {
            'retorno_total': 0,
            'retorno_anualizado': 0,
            'volatilidade_anualizada': 0,
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'periodos_analisados': len(self.df_evolucao),
            'valor_inicial': 0,
            'valor_final': 0,
            'evolucao_por_ano': {}
        }
        
        if len(self.df_evolucao) < 2:
            return indicadores
        
        valores = self.df_evolucao['total'].values
        indicadores['valor_inicial'] = valores[0]
        indicadores['valor_final'] = valores[-1]
        
        retornos = np.diff(valores) / valores[:-1]
        retornos = retornos[~np.isnan(retornos)]
        
        if len(retornos) > 0:
            indicadores['retorno_total'] = (valores[-1] / valores[0] - 1) * 100
            
            n_periodos = len(self.df_evolucao)
            periodos_por_ano = 12
            anos = n_periodos / periodos_por_ano
            
            if anos > 0:
                indicadores['retorno_anualizado'] = ((valores[-1] / valores[0]) ** (1/anos) - 1) * 100
            
            indicadores['volatilidade_anualizada'] = np.std(retornos) * np.sqrt(periodos_por_ano) * 100
            
            if indicadores['volatilidade_anualizada'] > 0:
                taxa_livre_risco = 0.1
                retorno_excesso = indicadores['retorno_anualizado'] - taxa_livre_risco * 100
                indicadores['sharpe_ratio'] = retorno_excesso / indicadores['volatilidade_anualizada']
            
            cumulative = (1 + retornos).cumprod()
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max) / running_max
            indicadores['max_drawdown'] = np.min(drawdown) * 100
        
        for _, row in self.df_evolucao.iterrows():
            periodo = row['periodo']
            if '-' in periodo:
                ano = periodo.split('-')[0]
            else:
                ano = periodo
            
            if ano not in indicadores['evolucao_por_ano']:
                indicadores['evolucao_por_ano'][ano] = {
                    'valor_inicial': row['total'],
                    'valor_final': row['total'],
                    'periodos': 1
                }
            else:
                indicadores['evolucao_por_ano'][ano]['valor_final'] = row['total']
                indicadores['evolucao_por_ano'][ano]['periodos'] += 1
        
        for ano, dados in indicadores['evolucao_por_ano'].items():
            if dados['valor_inicial'] > 0:
                dados['retorno'] = (dados['valor_final'] / dados['valor_inicial'] - 1) * 100
        
        return indicadores
    
    def analisar_composicao_detalhada(self) -> Dict:
        """Análise detalhada da composição da carteira ao longo do tempo"""
        composicao = {
            'media_alocacao': {},
            'volatilidade_alocacao': {},
            'tendencia_alocacao': {},
            'periodos_com_posicao': {}
        }
        
        tipos_ativos = ['titulos_publicos', 'titulos_bancarios', 'debentures', 
                       'acoes', 'derivativos', 'cotas_fundos', 'op_compromissadas', 'outros']
        
        for tipo in tipos_ativos:
            if tipo in self.df_evolucao.columns:
                valores = self.df_evolucao[tipo].values
                totais = self.df_evolucao['total'].values
                
                percentuais = np.where(totais > 0, valores / totais * 100, 0)
                
                composicao['media_alocacao'][tipo] = np.mean(percentuais)
                composicao['volatilidade_alocacao'][tipo] = np.std(percentuais)
                composicao['periodos_com_posicao'][tipo] = np.sum(valores > 0)
                
                if len(percentuais) > 1:
                    x = np.arange(len(percentuais))
                    coef = np.polyfit(x, percentuais, 1)
                    composicao['tendencia_alocacao'][tipo] = coef[0]
        
        return composicao
    
    def gerar_visualizacoes_temporais(self):
        """Gera visualizações completas para análise temporal"""
        print("\nGerando visualizações temporais...")
        
        try:
            plt.style.use('seaborn-v0_8-darkgrid')
        except:
            plt.style.use('ggplot')
        
        fig = plt.figure(figsize=(20, 24))
        
        ax1 = plt.subplot(5, 2, 1)
        if not self.df_evolucao.empty:
            ax1.plot(self.df_evolucao['periodo'], self.df_evolucao['total'], 
                    marker='o', linewidth=3, markersize=6)
            ax1.set_title(f'Evolução do Patrimônio Total - {self.nome_fundo}', fontsize=14, fontweight='bold')
            ax1.set_xlabel('Período')
            ax1.set_ylabel('Valor (R$)')
            ax1.tick_params(axis='x', rotation=45)
            ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x/1e6:.1f}M'))
            ax1.grid(True, alpha=0.3)
        
        ax2 = plt.subplot(5, 2, 2)
        if not self.df_evolucao.empty:
            retornos = self.df_evolucao['total'].pct_change() * 100
            retornos_positivos = retornos[retornos > 0]
            retornos_negativos = retornos[retornos <= 0]
            
            x = np.arange(len(retornos))
            colors = ['green' if r > 0 else 'red' for r in retornos]
            
            ax2.bar(x[1:], retornos[1:], color=colors[1:], alpha=0.7)
            ax2.set_title('Retornos Mensais (%)', fontsize=14, fontweight='bold')
            ax2.set_xlabel('Período')
            ax2.set_ylabel('Retorno (%)')
            ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            ax2.grid(True, alpha=0.3)
        
        ax3 = plt.subplot(5, 2, 3)
        if not self.df_evolucao.empty:
            indicadores = self.calcular_indicadores_performance()
            texto_indicadores = f"""
            Retorno Total: {indicadores['retorno_total']:.1f}%
            Retorno Anualizado: {indicadores['retorno_anualizado']:.1f}%
            Volatilidade Anual: {indicadores['volatilidade_anualizada']:.1f}%
            Sharpe Ratio: {indicadores['sharpe_ratio']:.2f}
            Max Drawdown: {indicadores['max_drawdown']:.1f}%
            
            Períodos Analisados: {indicadores['periodos_analisados']}
            Valor Inicial: R$ {indicadores['valor_inicial']/1e6:.1f}M
            Valor Final: R$ {indicadores['valor_final']/1e6:.1f}M
            """
            ax3.text(0.1, 0.5, texto_indicadores, transform=ax3.transAxes, 
                    fontsize=12, verticalalignment='center',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            ax3.set_title('Indicadores de Performance', fontsize=14, fontweight='bold')
            ax3.axis('off')
        
        ax4 = plt.subplot(5, 2, 4)
        if not self.df_evolucao.empty:
            composicao = self.analisar_composicao_detalhada()
            tipos = list(composicao['media_alocacao'].keys())
            medias = list(composicao['media_alocacao'].values())
            
            tipos_filtrados = [(t, m) for t, m in zip(tipos, medias) if m > 0.1]
            if tipos_filtrados:
                tipos, medias = zip(*tipos_filtrados)
                
                y_pos = np.arange(len(tipos))
                ax4.barh(y_pos, medias, alpha=0.7)
                ax4.set_yticks(y_pos)
                ax4.set_yticklabels([t.replace('_', ' ').title() for t in tipos])
                ax4.set_xlabel('Alocação Média (%)')
                ax4.set_title('Composição Média da Carteira', fontsize=14, fontweight='bold')
                ax4.grid(True, alpha=0.3, axis='x')
        
        ax5 = plt.subplot(5, 2, 5)
        if not self.df_evolucao.empty:
            tipos_ativos = ['acoes', 'titulos_publicos', 'derivativos', 'debentures']
            for tipo in tipos_ativos:
                if tipo in self.df_evolucao.columns:
                    valores = self.df_evolucao[tipo]
                    if valores.sum() > 0:
                        ax5.plot(self.df_evolucao['periodo'], valores/1e6, 
                                marker='o', label=tipo.replace('_', ' ').title(), 
                                linewidth=2, markersize=4)
            
            ax5.set_title('Evolução por Tipo de Ativo', fontsize=14, fontweight='bold')
            ax5.set_xlabel('Período')
            ax5.set_ylabel('Valor (R$ Milhões)')
            ax5.legend(loc='best', fontsize=10)
            ax5.tick_params(axis='x', rotation=45)
            ax5.grid(True, alpha=0.3)
        
        ax6 = plt.subplot(5, 2, 6)
        if not self.df_evolucao.empty and len(self.df_evolucao) > 12:
            retornos_acum = (1 + self.df_evolucao['total'].pct_change()).cumprod()
            retornos_acum_12m = retornos_acum.rolling(window=12).apply(lambda x: (x.iloc[-1]/x.iloc[0] - 1) * 100 if len(x) >= 12 else None)
            
            ax6.plot(self.df_evolucao['periodo'], retornos_acum_12m, 
                    marker='o', linewidth=2, markersize=4, color='darkblue')
            ax6.set_title('Retorno Acumulado 12 Meses (%)', fontsize=14, fontweight='bold')
            ax6.set_xlabel('Período')
            ax6.set_ylabel('Retorno 12M (%)')
            ax6.tick_params(axis='x', rotation=45)
            ax6.axhline(y=0, color='red', linestyle='--', alpha=0.5)
            ax6.grid(True, alpha=0.3)
        
        ax7 = plt.subplot(5, 2, 7)
        if not self.df_evolucao.empty:
            indicadores = self.calcular_indicadores_performance()
            if indicadores['evolucao_por_ano']:
                anos = list(indicadores['evolucao_por_ano'].keys())
                retornos = [indicadores['evolucao_por_ano'][ano].get('retorno', 0) 
                           for ano in anos]
                
                colors = ['green' if r > 0 else 'red' for r in retornos]
                ax7.bar(anos, retornos, color=colors, alpha=0.7)
                ax7.set_title('Retorno por Ano (%)', fontsize=14, fontweight='bold')
                ax7.set_xlabel('Ano')
                ax7.set_ylabel('Retorno (%)')
                ax7.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
                ax7.grid(True, alpha=0.3)
        
        ax8 = plt.subplot(5, 2, 8)
        if not self.df_evolucao.empty:
            valores = self.df_evolucao['total'].values
            if len(valores) > 1:
                cumulative = valores / valores[0]
                running_max = np.maximum.accumulate(cumulative)
                drawdown = (cumulative - running_max) / running_max * 100
                
                ax8.fill_between(range(len(drawdown)), 0, drawdown, 
                                color='red', alpha=0.3)
                ax8.plot(drawdown, color='darkred', linewidth=2)
                ax8.set_title('Drawdown ao Longo do Tempo', fontsize=14, fontweight='bold')
                ax8.set_xlabel('Período')
                ax8.set_ylabel('Drawdown (%)')
                ax8.grid(True, alpha=0.3)
        
        ax9 = plt.subplot(5, 2, 9)
        if not self.df_evolucao.empty:
            ultimo_ano = self.df_evolucao.iloc[-12:] if len(self.df_evolucao) >= 12 else self.df_evolucao
            
            tipos_pie = []
            valores_pie = []
            for tipo in ['titulos_publicos', 'titulos_bancarios', 'debentures', 
                        'acoes', 'derivativos', 'cotas_fundos', 'op_compromissadas', 'outros']:
                if tipo in ultimo_ano.columns:
                    valor_medio = ultimo_ano[tipo].mean()
                    if valor_medio > 0:
                        tipos_pie.append(tipo.replace('_', ' ').title())
                        valores_pie.append(valor_medio)
            
            if valores_pie:
                ax9.pie(valores_pie, labels=tipos_pie, autopct='%1.1f%%', startangle=90)
                ax9.set_title('Composição Média - Último Ano', fontsize=14, fontweight='bold')
        
        ax10 = plt.subplot(5, 2, 10)
        if not self.df_evolucao.empty:
            box_data = []
            labels_box = []
            
            for tipo in ['acoes', 'titulos_publicos', 'derivativos']:
                if tipo in self.df_evolucao.columns:
                    totais = self.df_evolucao['total'].values
                    valores = self.df_evolucao[tipo].values
                    percentuais = np.where(totais > 0, valores / totais * 100, 0)
                    if percentuais.sum() > 0:
                        box_data.append(percentuais[percentuais > 0])
                        labels_box.append(tipo.replace('_', ' ').title())
            
            if box_data:
                ax10.boxplot(box_data, labels=labels_box)
                ax10.set_title('Distribuição de Alocações', fontsize=14, fontweight='bold')
                ax10.set_ylabel('Alocação (%)')
                ax10.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        filename = os.path.join(self.output_dir, 'analise_temporal.png')
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Visualizações salvas em '{filename}'")
        return filename
    
    def gerar_relatorio_temporal(self):
        """Gera relatório HTML com análise temporal completa"""
        print("\nGerando relatório temporal...")
        
        indicadores = self.calcular_indicadores_performance()
        composicao = self.analisar_composicao_detalhada()
        
        periodo_inicial = min(self.carteiras_por_periodo.keys()) if self.carteiras_por_periodo else "N/A"
        periodo_final = max(self.carteiras_por_periodo.keys()) if self.carteiras_por_periodo else "N/A"
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Análise Temporal - {self.nome_fundo}</title>
            <style>
                body {{
                    font-family: 'Arial', sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f0f2f5;
                }}
                .container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    background-color: white;
                    box-shadow: 0 0 30px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                    color: white;
                    padding: 40px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 36px;
                    font-weight: 300;
                }}
                .header .subtitle {{
                    margin-top: 10px;
                    font-size: 18px;
                    opacity: 0.9;
                }}
                .content {{
                    padding: 40px;
                }}
                .metric-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-bottom: 40px;
                }}
                .metric-card {{
                    background: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 10px;
                    padding: 20px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                    transition: transform 0.2s;
                }}
                .metric-card:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
                }}
                .metric-card h3 {{
                    margin: 0 0 10px 0;
                    color: #34495e;
                    font-size: 14px;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}
                .metric-card .value {{
                    font-size: 28px;
                    font-weight: bold;
                    color: #2c3e50;
                }}
                .metric-card .change {{
                    font-size: 14px;
                    margin-top: 5px;
                }}
                .positive {{
                    color: #27ae60;
                }}
                .negative {{
                    color: #e74c3c;
                }}
                .neutral {{
                    color: #95a5a6;
                }}
                section {{
                    margin-bottom: 40px;
                }}
                h2 {{
                    color: #2c3e50;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                    margin-bottom: 20px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                }}
                th, td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #e0e0e0;
                }}
                th {{
                    background-color: #f8f9fa;
                    font-weight: 600;
                    color: #2c3e50;
                }}
                tr:hover {{
                    background-color: #f8f9fa;
                }}
                .chart-container {{
                    margin: 30px 0;
                    text-align: center;
                    padding: 20px;
                    background: #f8f9fa;
                    border-radius: 10px;
                }}
                .chart-container img {{
                    max-width: 100%;
                    border-radius: 5px;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                }}
                .insight-box {{
                    background: #e8f4f8;
                    border-left: 4px solid #3498db;
                    padding: 20px;
                    margin: 20px 0;
                    border-radius: 5px;
                }}
                .footer {{
                    background: #2c3e50;
                    color: white;
                    text-align: center;
                    padding: 20px;
                    margin-top: 40px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Análise Temporal - {self.nome_fundo}</h1>
                    <div class="subtitle">CNPJ: {self.cnpj_fundo} | Período: {periodo_inicial} a {periodo_final}</div>
                </div>
                
                <div class="content">
                    <div class="metric-grid">
                        <div class="metric-card">
                            <h3>Retorno Total</h3>
                            <div class="value">{indicadores['retorno_total']:.1f}%</div>
                            <div class="change {self._get_color_class(indicadores['retorno_total'])}">
                                Período completo
                            </div>
                        </div>
                        <div class="metric-card">
                            <h3>Retorno Anualizado</h3>
                            <div class="value">{indicadores['retorno_anualizado']:.1f}%</div>
                            <div class="change neutral">Por ano</div>
                        </div>
                        <div class="metric-card">
                            <h3>Volatilidade Anual</h3>
                            <div class="value">{indicadores['volatilidade_anualizada']:.1f}%</div>
                            <div class="change neutral">Desvio padrão</div>
                        </div>
                        <div class="metric-card">
                            <h3>Sharpe Ratio</h3>
                            <div class="value">{indicadores['sharpe_ratio']:.2f}</div>
                            <div class="change {self._get_sharpe_class(indicadores['sharpe_ratio'])}">
                                Retorno ajustado ao risco
                            </div>
                        </div>
                        <div class="metric-card">
                            <h3>Máximo Drawdown</h3>
                            <div class="value">{indicadores['max_drawdown']:.1f}%</div>
                            <div class="change negative">Maior queda do pico</div>
                        </div>
                        <div class="metric-card">
                            <h3>Patrimônio Atual</h3>
                            <div class="value">R$ {indicadores['valor_final']/1e6:.1f}M</div>
                            <div class="change neutral">Último período</div>
                        </div>
                    </div>
                    
                    <section>
                        <h2>1. Análise Gráfica Temporal</h2>
                        <div class="chart-container">
                            <img src="analise_temporal.png" 
                                 alt="Análise Temporal do Fundo">
                        </div>
                    </section>
                    
                    <section>
                        <h2>2. Composição Média da Carteira</h2>
                        <table>
                            <tr>
                                <th>Tipo de Ativo</th>
                                <th>Alocação Média</th>
                                <th>Volatilidade</th>
                                <th>Períodos com Posição</th>
                                <th>Tendência</th>
                            </tr>
        """
        
        for tipo, media in composicao['media_alocacao'].items():
            if media > 0.1:
                volatilidade = composicao['volatilidade_alocacao'].get(tipo, 0)
                periodos = composicao['periodos_com_posicao'].get(tipo, 0)
                tendencia = composicao['tendencia_alocacao'].get(tipo, 0)
                
                tendencia_texto = "↑ Crescente" if tendencia > 0.1 else "↓ Decrescente" if tendencia < -0.1 else "→ Estável"
                
                html_content += f"""
                            <tr>
                                <td>{tipo.replace('_', ' ').title()}</td>
                                <td>{media:.1f}%</td>
                                <td>{volatilidade:.1f}%</td>
                                <td>{periodos}</td>
                                <td>{tendencia_texto}</td>
                            </tr>
                """
        
        html_content += """
                        </table>
                    </section>
                    
                    <section>
                        <h2>3. Performance por Ano</h2>
                        <table>
                            <tr>
                                <th>Ano</th>
                                <th>Valor Inicial</th>
                                <th>Valor Final</th>
                                <th>Retorno</th>
                                <th>Períodos</th>
                            </tr>
        """
        
        for ano in sorted(indicadores['evolucao_por_ano'].keys(), reverse=True):
            dados_ano = indicadores['evolucao_por_ano'][ano]
            retorno = dados_ano.get('retorno', 0)
            color_class = self._get_color_class(retorno)
            
            html_content += f"""
                            <tr>
                                <td>{ano}</td>
                                <td>R$ {dados_ano['valor_inicial']/1e6:.1f}M</td>
                                <td>R$ {dados_ano['valor_final']/1e6:.1f}M</td>
                                <td class="{color_class}">{retorno:.1f}%</td>
                                <td>{dados_ano['periodos']}</td>
                            </tr>
            """
        
        html_content += f"""
                        </table>
                    </section>
                    
                    <section>
                        <h2>4. Insights e Conclusões</h2>
                        <div class="insight-box">
                            <strong>Principais Observações:</strong>
                            <ul>
                                <li>O fundo apresentou um retorno total de {indicadores['retorno_total']:.1f}% no período analisado</li>
                                <li>A volatilidade anualizada de {indicadores['volatilidade_anualizada']:.1f}% indica um nível de risco {self._classificar_volatilidade(indicadores['volatilidade_anualizada'])}</li>
                                <li>O Sharpe Ratio de {indicadores['sharpe_ratio']:.2f} sugere uma relação retorno/risco {self._classificar_sharpe(indicadores['sharpe_ratio'])}</li>
                                <li>O drawdown máximo de {indicadores['max_drawdown']:.1f}% mostra a maior perda potencial do período</li>
                            </ul>
                        </div>
                    </section>
                </div>
                
                <div class="footer">
                    <p>Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')} | Análise baseada em dados públicos da CVM</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        filename = os.path.join(self.output_dir, 'relatorio_temporal.html')
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Relatório salvo em '{filename}'")
        return filename
    
    def _get_color_class(self, value):
        """Retorna classe CSS baseada no valor"""
        return 'positive' if value > 0 else 'negative' if value < 0 else 'neutral'
    
    def _get_sharpe_class(self, sharpe):
        """Retorna classe CSS para Sharpe Ratio"""
        return 'positive' if sharpe > 1 else 'neutral' if sharpe > 0 else 'negative'
    
    def _classificar_volatilidade(self, vol):
        """Classifica nível de volatilidade"""
        if vol < 10:
            return "baixo"
        elif vol < 20:
            return "moderado"
        elif vol < 30:
            return "alto"
        else:
            return "muito alto"
    
    def _classificar_sharpe(self, sharpe):
        """Classifica Sharpe Ratio"""
        if sharpe > 2:
            return "excelente"
        elif sharpe > 1:
            return "boa"
        elif sharpe > 0.5:
            return "adequada"
        elif sharpe > 0:
            return "baixa"
        else:
            return "inadequada"
    
    def executar_analise_completa(self):
        """Executa análise completa do fundo"""
        print(f"\n{'='*60}")
        print(f"ANÁLISE TEMPORAL - {self.nome_fundo}")
        print(f"{'='*60}\n")
        
        self.processar_carteiras()
        
        if not self.carteiras_por_periodo:
            print(f"\nERRO: Nenhum dado encontrado para o fundo {self.nome_fundo}!")
            return False
        
        print("\nAnalisando evolução patrimonial...")
        self.analisar_evolucao_patrimonio()
        
        if self.df_evolucao.empty:
            print("\nERRO: Não foi possível calcular a evolução patrimonial!")
            return False
        
        print("\nAnalisando posições em ações...")
        self.df_acoes = self.analisar_acoes_detalhado()
        
        print("Analisando derivativos...")
        self.derivativos_info = self.analisar_derivativos_detalhado()
        
        self.processar_cotas_fundo()
        
        indicadores = self.calcular_indicadores_performance()
        composicao = self.analisar_composicao_detalhada()
        
        self.gerar_visualizacoes_temporais()
        self.gerar_relatorio_temporal()
        
        print(f"\n{'='*60}")
        print("ANÁLISE CONCLUÍDA COM SUCESSO!")
        print(f"{'='*60}")
        
        return True
    
    def processar_cotas_fundo(self):
        """Processa as cotas do fundo para calcular retornos"""
        print("\nProcessando cotas do fundo...")
        
        # Tentar diferentes nomes possíveis para o diretório
        possiveis_dirs = ["INF_DIARIO_FI", "INF_DIARIO", "INFORME_DIARIO"]
        inf_diario_dir = None
        
        for dir_name in possiveis_dirs:
            temp_dir = os.path.join(BASE_DIR, dir_name)
            if os.path.exists(temp_dir):
                inf_diario_dir = temp_dir
                break
        
        if not inf_diario_dir:
            print("Diretório de cotas não encontrado. Pulando análise de cotas...")
            return self.df_cotas
        
        cotas_list = []
        
        arquivos_inf = []
        for arquivo in sorted(os.listdir(inf_diario_dir)):
            if arquivo.startswith("inf_diario_fi_") and arquivo.endswith(".zip"):
                arquivos_inf.append((arquivo, os.path.join(inf_diario_dir, arquivo)))
        
        hist_dir = os.path.join(inf_diario_dir, "HIST")
        if os.path.exists(hist_dir):
            for arquivo in sorted(os.listdir(hist_dir)):
                if arquivo.startswith("inf_diario_fi_") and arquivo.endswith(".zip"):
                    arquivos_inf.append((arquivo, os.path.join(hist_dir, arquivo)))
        
        arquivos_inf.sort()
        print(f"Total de arquivos de cotas para processar: {len(arquivos_inf)}")
        
        for i, (nome_arquivo, arquivo_path) in enumerate(arquivos_inf):
            try:
                with zipfile.ZipFile(arquivo_path, 'r') as zip_file:
                    for nome_interno in zip_file.namelist():
                        if nome_interno.endswith('.csv'):
                            try:
                                with zip_file.open(nome_interno) as f:
                                    df = pd.read_csv(f, sep=';', encoding='ISO-8859-1')
                                    
                                    for col in ['CNPJ_FUNDO', 'CD_FUNDO']:
                                        if col in df.columns:
                                            df_fundo = df[df[col].astype(str).str.strip() == self.cnpj_fundo]
                                            if not df_fundo.empty:
                                                cotas_list.append(df_fundo)
                                                break
                            except Exception as e:
                                continue
                
                if (i + 1) % 20 == 0:
                    print(f"Processados {i + 1}/{len(arquivos_inf)} arquivos de cotas...")
                    
            except Exception as e:
                continue
        
        if cotas_list:
            self.df_cotas = pd.concat(cotas_list, ignore_index=True)
            
            if 'DT_COMPTC' in self.df_cotas.columns:
                self.df_cotas['DT_COMPTC'] = pd.to_datetime(self.df_cotas['DT_COMPTC'])
                self.df_cotas = self.df_cotas.sort_values('DT_COMPTC')
            
            self._calcular_retornos()
            
            print(f"✓ Cotas processadas: {len(self.df_cotas)} registros")
        else:
            print("Nenhuma cota encontrada para o fundo")
        
        return self.df_cotas
    
    def _calcular_retornos(self):
        """Calcula retornos baseados nas cotas"""
        if self.df_cotas.empty:
            return
        
        cota_col = None
        for col in ['VL_QUOTA', 'VL_COTA', 'VALOR_QUOTA', 'VALOR_COTA']:
            if col in self.df_cotas.columns:
                cota_col = col
                break
        
        if cota_col:
            self.df_cotas = self.df_cotas[self.df_cotas[cota_col] > 0].copy()
            
            self.df_cotas['retorno_diario'] = self.df_cotas[cota_col].pct_change()
            self.df_cotas['retorno_acumulado'] = (1 + self.df_cotas['retorno_diario']).cumprod() - 1
            
            if 'DT_COMPTC' in self.df_cotas.columns:
                retornos_mensais = self.df_cotas.set_index('DT_COMPTC').resample('M').agg({
                    cota_col: 'last',
                    'retorno_diario': lambda x: (1 + x).prod() - 1,
                    'retorno_acumulado': 'last'
                }).reset_index()
                
                retornos_mensais['ano'] = retornos_mensais['DT_COMPTC'].dt.year
                retornos_mensais['mes'] = retornos_mensais['DT_COMPTC'].dt.month
                retornos_mensais['periodo'] = retornos_mensais['DT_COMPTC'].dt.strftime('%Y-%m')
                
                self.df_retornos = retornos_mensais
                
                print(f"✓ Retornos calculados: {len(self.df_retornos)} períodos mensais")
    
    def exportar_dados_completos(self):
        """Exporta todos os dados processados para arquivos"""
        base_filename = "dados_fundo"
        
        dados_completos = {
            'cnpj': self.cnpj_fundo,
            'nome': self.nome_fundo,
            'periodo_analise': self.periodo_minimo_anos,
            'data_processamento': datetime.now().isoformat(),
            'carteiras_por_periodo': self.carteiras_por_periodo,
            'evolucao_patrimonio': self.df_evolucao,
            'posicoes_acoes': self.df_acoes,
            'info_derivativos': self.derivativos_info,
            'serie_cotas': self.df_cotas,
            'retornos_mensais': self.df_retornos,
            'indicadores': self.calcular_indicadores_performance(),
            'composicao': self.analisar_composicao_detalhada()
        }
        
        if self.formato_exportacao in ['pickle', 'todos']:
            filename = os.path.join(self.output_dir, f"{base_filename}.pkl")
            with open(filename, 'wb') as f:
                pickle.dump(dados_completos, f)
            print(f"✓ Dados salvos em formato pickle: {filename}")
        
        if self.formato_exportacao in ['json', 'todos']:
            filename = os.path.join(self.output_dir, f"{base_filename}.json")
            
            dados_json = dados_completos.copy()
            for key, value in dados_json.items():
                if isinstance(value, pd.DataFrame):
                    dados_json[key] = value.to_dict('records')
                elif isinstance(value, dict):
                    for k, v in value.items():
                        if isinstance(v, pd.DataFrame):
                            value[k] = v.to_dict('records')
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(dados_json, f, indent=2, default=str, ensure_ascii=False)
            print(f"✓ Dados salvos em formato JSON: {filename}")
        
        if self.formato_exportacao in ['csv', 'todos']:
            csv_dir = os.path.join(self.output_dir, "csv")
            os.makedirs(csv_dir, exist_ok=True)
            
            if not self.df_evolucao.empty:
                filename = os.path.join(csv_dir, "evolucao_patrimonio.csv")
                self.df_evolucao.to_csv(filename, index=False)
                print(f"✓ Evolução patrimonial salva em: {filename}")
            
            if not self.df_acoes.empty:
                filename = os.path.join(csv_dir, "posicoes_acoes.csv")
                self.df_acoes.to_csv(filename, index=False)
                print(f"✓ Posições em ações salvas em: {filename}")
            
            if not self.df_cotas.empty:
                filename = os.path.join(csv_dir, "serie_cotas.csv")
                self.df_cotas.to_csv(filename, index=False)
                print(f"✓ Série de cotas salva em: {filename}")
            
            if not self.df_retornos.empty:
                filename = os.path.join(csv_dir, "retornos_mensais.csv")
                self.df_retornos.to_csv(filename, index=False)
                print(f"✓ Retornos mensais salvos em: {filename}")
            
            filename = os.path.join(csv_dir, "indicadores.csv")
            indicadores_df = pd.DataFrame([self.calcular_indicadores_performance()])
            indicadores_df.to_csv(filename, index=False)
            print(f"✓ Indicadores salvos em: {filename}")
            
            carteiras_resumo = []
            for periodo, carteira in self.carteiras_por_periodo.items():
                resumo = {'periodo': periodo}
                for blc, df in carteira.items():
                    resumo[f'{blc}_registros'] = len(df)
                    for col in ['VL_MERC_POS_FINAL', 'VL_MERCADO', 'VL_POS_FINAL']:
                        if col in df.columns:
                            resumo[f'{blc}_valor'] = df[col].sum()
                            break
                carteiras_resumo.append(resumo)
            
            if carteiras_resumo:
                filename = os.path.join(csv_dir, "carteiras_resumo.csv")
                pd.DataFrame(carteiras_resumo).to_csv(filename, index=False)
                print(f"✓ Resumo das carteiras salvo em: {filename}")
        
        return True


def main():
    """Função principal com suporte a linha de comando"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Análise temporal de fundos de investimento brasileiros',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python analise_temporal_fundos.py 35.803.288/0001-17
  python analise_temporal_fundos.py 35.803.288/0001-17 --nome "Capstone" --anos 5
  python analise_temporal_fundos.py 35.803.288/0001-17 --formato csv
        """
    )
    
    parser.add_argument('cnpj', 
                       help='CNPJ do fundo (formato: XX.XXX.XXX/XXXX-XX)')
    
    parser.add_argument('--nome', '-n',
                       default='Fundo',
                       help='Nome do fundo (padrão: "Fundo")')
    
    parser.add_argument('--anos', '-a',
                       type=int,
                       default=5,
                       help='Período mínimo em anos para análise (padrão: 5)')
    
    parser.add_argument('--formato', '-f',
                       choices=['pickle', 'csv', 'json', 'todos'],
                       default='todos',
                       help='Formato de exportação dos dados (padrão: todos)')
    
    
    args = parser.parse_args()
    
    print(f"\nIniciando análise do fundo CNPJ: {args.cnpj}")
    print(f"Nome: {args.nome}")
    print(f"Período mínimo: {args.anos} anos")
    print(f"Formato de exportação: {args.formato}")
    
    analisador = AnalisadorTemporalFundos(args.cnpj, args.nome, periodo_minimo_anos=args.anos)
    analisador.formato_exportacao = args.formato
    
    print(f"Diretório de saída: {analisador.output_dir}\n")
    
    sucesso = analisador.executar_analise_completa()
    
    if sucesso:
        analisador.exportar_dados_completos()
        print(f"\n✓ Análise concluída com sucesso!")
        print(f"✓ Arquivos salvos no diretório: {analisador.output_dir}")
    else:
        print(f"\n✗ Erro na análise do fundo {args.cnpj}")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()