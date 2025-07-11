import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

class ReplicadorFundoMeta:
    def __init__(self, cnpj_meta="38.351.476/0001-40", janela_meses=6, min_ativos=15):
        self.cnpj_meta = cnpj_meta
        self.janela_meses = janela_meses
        self.min_ativos = min_ativos
        self.data_dir = Path("C:/Users/guilh/Documents/GitHub/database/chimpa")
        
        # DataFrames
        self.retornos_fundos = None
        self.retornos_acoes = None
        self.serie_meta = None
        self.universo_ativos = None
        
        # Resultados
        self.historico_carteiras = []
        self.curva_replicada = []
        self.datas_rebalanceamento = []
        
    def carregar_dados(self):
        """Carrega todos os dados necessários"""
        print("Carregando dados...")
        
        # Retornos dos fundos (acumulados)
        fundos_path = self.data_dir / "retornos_fundos_cvm.csv"
        self.retornos_fundos = pd.read_csv(fundos_path, index_col=0, parse_dates=True)
        
        # Carregar ações usando o método que funciona (baseado no código do usuário)
        acoes_path = self.data_dir / "data_stocks.txt"
        self.retornos_acoes = None
        
        try:
            print("Carregando dados de ações...")
            # Usar utf-16 como especificado no código do usuário
            df_acoes = pd.read_csv(acoes_path, encoding='utf-16', sep=';', header=None)
            print(f"✅ Dados carregados: {df_acoes.shape}")
            self._processar_dados_acoes(df_acoes)
        except Exception as e:
            print(f"❌ Erro ao carregar dados de ações: {e}")
            self.retornos_acoes = pd.DataFrame()
        
        if self.retornos_acoes is None:
            print("❌ Não foi possível carregar dados de ações")
            print("Usando apenas fundos para replicação...")
            # Usar apenas fundos
            self.retornos_acoes = pd.DataFrame()
        
        # Série do fundo meta
        self.serie_meta = self.retornos_fundos[self.cnpj_meta].dropna()
        
        print(f"Fundos carregados: {len(self.retornos_fundos.columns)}")
        print(f"Ações carregadas: {len(self.retornos_acoes.columns) if self.retornos_acoes is not None else 0}")
        
    def _processar_dados_acoes(self, df_raw):
        """Processa dados brutos de ações usando método baseado no seu código"""
        try:
            print(f"Debug: DataFrame shape inicial: {df_raw.shape}")
            
            # Definir colunas conforme seu código original
            cols = ['Ticker', 'Data', 'Abertura', 'Fechamento', 'Maxima', 'Minima', 'Negocios', 'Volume']
            df_raw.columns = cols
            
            print(f"Debug: Tickers únicos: {df_raw['Ticker'].nunique()}")
            print(f"Debug: Primeiro ticker: {df_raw['Ticker'].iloc[0] if len(df_raw) > 0 else 'N/A'}")
            
            # Calcular volume financeiro
            df_raw['Volume_Financeiro'] = ((df_raw['Maxima'] + df_raw['Minima']) / 2) * df_raw['Volume']
            
            # Usar apenas colunas necessárias
            df_raw = df_raw[['Ticker', 'Data', 'Fechamento']]
            df_raw['Data'] = pd.to_datetime(df_raw['Data'], errors='coerce')
            df_raw['Fechamento'] = pd.to_numeric(df_raw['Fechamento'], errors='coerce')
            
            # Remover dados inválidos
            df_raw = df_raw.dropna(subset=['Data', 'Fechamento'])
            
            if len(df_raw) == 0:
                print("❌ Nenhuma linha válida após conversão")
                self.retornos_acoes = pd.DataFrame()
                return
            
            # Filtrar data
            df_raw.set_index('Data', inplace=True)
            
            # Criar dicionário de preços por ativo (como no seu código)
            assets_prices = {}
            for ticker, group in df_raw.groupby('Ticker'):
                df_ticker = group[['Fechamento']].copy()
                df_ticker.columns = ['Fechamento']
                assets_prices[ticker] = df_ticker
            
            # Criar DataFrame de preços (ticker como coluna, data como índice)
            all_prices = pd.DataFrame({ticker: data['Fechamento'] for ticker, data in assets_prices.items()})
            
            # Calcular retornos diários
            self.retornos_acoes = all_prices.pct_change().fillna(0)
            
            print(f"✅ Processadas {len(self.retornos_acoes.columns)} ações")
            print(f"✅ Período: {self.retornos_acoes.index[0]} a {self.retornos_acoes.index[-1]}")
            
        except Exception as e:
            print(f"❌ Erro ao processar ações: {e}")
            import traceback
            traceback.print_exc()
            self.retornos_acoes = pd.DataFrame()
        
    def alinhar_dados(self):
        """Alinha as datas entre fundos e ações"""
        print("Alinhando dados...")
        
        # Converter retornos de fundos para retornos diários
        self.retornos_fundos_diarios = self.retornos_fundos.pct_change().fillna(0)
        
        # Remover o fundo meta do universo
        fundos_sem_meta = self.retornos_fundos_diarios.drop(columns=[self.cnpj_meta])
        
        # Se temos ações, combinar. Se não, usar apenas fundos
        if self.retornos_acoes is not None and len(self.retornos_acoes.columns) > 0:
            print(f"Combinando {len(self.retornos_acoes.columns)} ações com {len(fundos_sem_meta.columns)} fundos")
            
            # Encontrar período comum
            inicio_comum = max(self.retornos_fundos.index[0], self.retornos_acoes.index[0])
            fim_comum = min(self.retornos_fundos.index[-1], self.retornos_acoes.index[-1])
            
            # Filtrar período comum
            self.retornos_fundos = self.retornos_fundos.loc[inicio_comum:fim_comum]
            self.retornos_acoes = self.retornos_acoes.loc[inicio_comum:fim_comum]
            fundos_sem_meta = fundos_sem_meta.loc[inicio_comum:fim_comum]
            self.serie_meta = self.serie_meta.loc[inicio_comum:fim_comum]
            
            # Combinar universo (ações + outros fundos)
            self.universo_ativos = pd.concat([self.retornos_acoes, fundos_sem_meta], axis=1)
            
        else:
            print(f"Usando apenas {len(fundos_sem_meta.columns)} fundos (sem ações)")
            
            # Usar apenas período dos fundos
            inicio_comum = self.retornos_fundos.index[0]
            fim_comum = self.retornos_fundos.index[-1]
            self.serie_meta = self.serie_meta.loc[inicio_comum:fim_comum]
            
            # Universo = apenas outros fundos
            self.universo_ativos = fundos_sem_meta
        
        self.universo_ativos = self.universo_ativos.fillna(0)
        
        print(f"✅ Universo total de ativos: {len(self.universo_ativos.columns)}")
        print(f"✅ Período alinhado: {inicio_comum} até {fim_comum}")
        
    def calcular_retorno_meta_diario(self):
        """Calcula retornos diários do fundo meta"""
        self.retornos_meta_diarios = self.serie_meta.pct_change().fillna(0)
        
    def otimizar_carteira(self, periodo_inicio, periodo_fim):
        """
        ESTRATÉGIA PARA BETA = 1:
        
        1. Período de calibração (6 meses): Encontrar carteira que replique o fundo meta
        2. Objetivo: Beta da carteira vs fundo meta = 1 (sensibilidade 1:1)
        3. Método: Regressão com restrições + seleção por correlação
        4. Validação: Testar no mês seguinte
        
        Beta = Cov(Carteira, Meta) / Var(Meta)
        Se Beta = 1, então 1% de retorno do meta = 1% de retorno da carteira
        """
        
        # Dados do período de calibração
        retornos_periodo = self.universo_ativos.loc[periodo_inicio:periodo_fim]
        meta_periodo = self.retornos_meta_diarios.loc[periodo_inicio:periodo_fim]
        
        # Remover ativos com poucos dados (80% de cobertura mínima)
        coverage_threshold = len(retornos_periodo) * 0.8
        ativos_validos = retornos_periodo.columns[retornos_periodo.count() >= coverage_threshold]
        retornos_periodo = retornos_periodo[ativos_validos].fillna(0)
        
        n_ativos = len(ativos_validos)
        print(f"Período {periodo_inicio.strftime('%Y-%m')} a {periodo_fim.strftime('%Y-%m')}: {n_ativos} ativos válidos")
        
        if n_ativos < self.min_ativos:
            return None, None, None
        
        # PASSO 1: Calcular correlações e selecionar candidatos
        correlacoes = []
        betas_individuais = []
        
        for ativo in ativos_validos:
            try:
                ret_ativo = retornos_periodo[ativo]
                
                # Correlação
                corr = np.corrcoef(ret_ativo, meta_periodo)[0, 1]
                if np.isnan(corr):
                    corr = 0
                correlacoes.append(abs(corr))
                
                # Beta individual
                if meta_periodo.var() > 0:
                    beta = np.cov(ret_ativo, meta_periodo)[0, 1] / meta_periodo.var()
                    if np.isnan(beta):
                        beta = 0
                else:
                    beta = 0
                betas_individuais.append(beta)
                
            except:
                correlacoes.append(0)
                betas_individuais.append(0)
        
        # PASSO 2: Selecionar top ativos por correlação
        correlacoes = np.array(correlacoes)
        indices_top = np.argsort(correlacoes)[::-1]
        
        n_candidatos = min(100, max(self.min_ativos * 3, n_ativos // 2))
        ativos_candidatos = ativos_validos[indices_top[:n_candidatos]]
        
        print(f"Selecionados {len(ativos_candidatos)} candidatos (correlação média: {np.mean(correlacoes[indices_top[:n_candidatos]]):.3f})")
        
        # PASSO 3: Otimização para Beta ≈ 1
        X = retornos_periodo[ativos_candidatos].values
        y = meta_periodo.values
        
        try:
            # Método 1: Regressão com restrição de soma
            from scipy.optimize import minimize
            
            def objetivo_beta(weights):
                # Retorno da carteira
                retorno_cart = X @ weights
                
                # Calcular beta
                if meta_periodo.var() > 0:
                    beta_cart = np.cov(retorno_cart, y)[0, 1] / meta_periodo.var()
                else:
                    beta_cart = 0
                
                # Tracking error
                tracking_err = np.mean((retorno_cart - y) ** 2)
                
                # Função objetivo: minimizar desvio do beta=1 + tracking error
                erro_beta = (beta_cart - 1.0) ** 2
                
                # Penalizar muitos ativos (esparsidade)
                penalidade_esparsidade = 0.001 * np.sum(weights > 0.01)
                
                return 100 * erro_beta + tracking_err + penalidade_esparsidade
            
            # Restrições
            constraints = [
                {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0},  # Soma = 1
            ]
            
            # Limites: 0.5% a 15% por ativo
            bounds = [(0.005, 0.15) for _ in range(len(ativos_candidatos))]
            
            # Chute inicial: peso igual para todos
            w0 = np.ones(len(ativos_candidatos)) / len(ativos_candidatos)
            
            # Otimizar
            result = minimize(
                objetivo_beta, w0,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints,
                options={'maxiter': 2000, 'ftol': 1e-8}
            )
            
            if result.success and result.fun < 10:  # Função objetivo razoável
                weights_otimos = result.x
                
                # Filtrar pesos significativos
                mask_significativo = weights_otimos >= 0.01  # 1% mínimo
                
                if np.sum(mask_significativo) >= self.min_ativos:
                    weights_finais = weights_otimos[mask_significativo]
                    ativos_finais = ativos_candidatos[mask_significativo]
                    
                    # Renormalizar
                    weights_finais = weights_finais / weights_finais.sum()
                    
                    # Verificar beta resultante
                    retorno_final = X[:, mask_significativo] @ weights_finais
                    beta_final = np.cov(retorno_final, y)[0, 1] / meta_periodo.var() if meta_periodo.var() > 0 else 0
                    tracking_error_final = np.mean((retorno_final - y) ** 2)
                    
                    print(f"✅ Carteira otimizada: {len(ativos_finais)} ativos, Beta={beta_final:.3f}, Tracking Error={tracking_error_final:.6f}")
                    
                    return ativos_finais, weights_finais, {
                        'beta': beta_final,
                        'tracking_error': tracking_error_final,
                        'correlacao_media': np.mean([correlacoes[indices_top[i]] for i in range(len(ativos_finais))])
                    }
            
            print(f"❌ Otimização falhou: success={result.success}, fun={result.fun}")
            
        except Exception as e:
            print(f"❌ Erro na otimização: {e}")
        
        # FALLBACK: Método simples baseado em correlação
        print("Usando método fallback...")
        indices_simples = indices_top[:self.min_ativos]
        ativos_simples = ativos_validos[indices_simples]
        weights_simples = np.ones(len(ativos_simples)) / len(ativos_simples)
        
        retorno_simples = (retornos_periodo[ativos_simples] * weights_simples).sum(axis=1)
        beta_simples = np.cov(retorno_simples, meta_periodo)[0, 1] / meta_periodo.var() if meta_periodo.var() > 0 else 0
        
        print(f"🔄 Fallback: {len(ativos_simples)} ativos, Beta={beta_simples:.3f}")
        
        return ativos_simples, weights_simples, {
            'beta': beta_simples,
            'tracking_error': np.mean((retorno_simples - meta_periodo) ** 2),
            'correlacao_media': np.mean(correlacoes[indices_simples])
        }
    
    def executar_backtest(self):
        """Executa o backtest com janela móvel"""
        print("Executando backtest com janela móvel...")
        
        # Preparar dados
        self.carregar_dados()
        self.alinhar_dados()
        self.calcular_retorno_meta_diario()
        
        # Datas para rebalanceamento (mensais)
        datas_inicio = pd.date_range(
            start=self.universo_ativos.index[0],
            end=self.universo_ativos.index[-1] - pd.DateOffset(months=self.janela_meses),
            freq='MS'
        )
        
        print(f"Períodos de rebalanceamento: {len(datas_inicio)}")
        
        for i, data_inicio in enumerate(tqdm(datas_inicio, desc="Rebalanceamento")):
            # Período de calibração (6 meses)
            data_fim_calib = data_inicio + pd.DateOffset(months=self.janela_meses)
            
            # Período de teste (1 mês seguinte)
            data_inicio_teste = data_fim_calib
            data_fim_teste = data_inicio_teste + pd.DateOffset(months=1)
            
            # Verificar se temos dados suficientes
            if data_fim_teste > self.universo_ativos.index[-1]:
                break
                
            # Otimizar carteira no período de calibração
            resultado_otimizacao = self.otimizar_carteira(data_inicio, data_fim_calib)
            
            if resultado_otimizacao[0] is not None:
                ativos, weights, stats = resultado_otimizacao
                
                # Calcular performance no período de teste
                retornos_teste = self.universo_ativos.loc[data_inicio_teste:data_fim_teste]
                meta_teste = self.retornos_meta_diarios.loc[data_inicio_teste:data_fim_teste]
                
                # Retorno da carteira no período de teste
                retorno_carteira_teste = (retornos_teste[ativos] * weights).sum(axis=1)
                
                # Calcular beta no período de teste
                beta_teste = np.cov(retorno_carteira_teste, meta_teste)[0, 1] / meta_teste.var() if meta_teste.var() > 0 else 0
                
                # Armazenar resultados
                self.historico_carteiras.append({
                    'data_rebalanceamento': data_inicio,
                    'periodo_calibracao': f"{data_inicio.strftime('%Y-%m-%d')} a {data_fim_calib.strftime('%Y-%m-%d')}",
                    'periodo_teste': f"{data_inicio_teste.strftime('%Y-%m-%d')} a {data_fim_teste.strftime('%Y-%m-%d')}",
                    'ativos': list(ativos),
                    'weights': list(weights),
                    'beta_calibracao': stats.get('beta', 0),
                    'beta_teste': beta_teste,
                    'tracking_error_calibracao': stats.get('tracking_error', 0),
                    'correlacao_media': stats.get('correlacao_media', 0),
                    'retorno_carteira_teste': retorno_carteira_teste.sum(),
                    'retorno_meta_teste': meta_teste.sum(),
                    'tracking_error_teste': np.mean((retorno_carteira_teste - meta_teste) ** 2)
                })
                
                # Adicionar à curva replicada
                for data, retorno in retorno_carteira_teste.items():
                    self.curva_replicada.append({
                        'data': data,
                        'retorno_carteira': retorno,
                        'retorno_meta': meta_teste.loc[data] if data in meta_teste.index else 0
                    })
                    
        print(f"Backtest concluído! {len(self.historico_carteiras)} rebalanceamentos realizados")
        
    def salvar_resultados(self):
        """Salva todos os resultados"""
        output_dir = self.data_dir
        
        # Histórico de carteiras
        df_carteiras = pd.DataFrame(self.historico_carteiras)
        df_carteiras.to_csv(output_dir / "historico_carteiras_replicacao.csv", index=False)
        
        # Curva replicada
        df_curva = pd.DataFrame(self.curva_replicada)
        df_curva.to_csv(output_dir / "curva_replicada_vs_meta.csv", index=False)
        
        # Estatísticas resumo
        if len(self.historico_carteiras) > 0:
            stats = {
                'total_rebalanceamentos': len(self.historico_carteiras),
                'tracking_error_medio': np.mean([h['tracking_error_teste'] for h in self.historico_carteiras]),
                'retorno_total_carteira': sum([h['retorno_carteira_teste'] for h in self.historico_carteiras]),
                'retorno_total_meta': sum([h['retorno_meta_teste'] for h in self.historico_carteiras]),
                'ativos_mais_utilizados': self._analisar_ativos_utilizados()
            }
            
            with open(output_dir / "estatisticas_replicacao.json", 'w') as f:
                import json
                json.dump(stats, f, indent=2, default=str)
        
        print(f"Resultados salvos em: {output_dir}")
        
    def _analisar_ativos_utilizados(self):
        """Analisa quais ativos foram mais utilizados"""
        contador_ativos = {}
        for carteira in self.historico_carteiras:
            for ativo, peso in zip(carteira['ativos'], carteira['weights']):
                if ativo not in contador_ativos:
                    contador_ativos[ativo] = []
                contador_ativos[ativo].append(peso)
        
        # Peso médio por ativo
        peso_medio = {ativo: np.mean(pesos) for ativo, pesos in contador_ativos.items()}
        
        # Top 20 ativos mais utilizados
        top_ativos = sorted(peso_medio.items(), key=lambda x: x[1], reverse=True)[:20]
        
        return dict(top_ativos)


def main():
    # Executar replicação
    replicador = ReplicadorFundoMeta(
        cnpj_meta="38.351.476/0001-40",
        janela_meses=6,
        min_ativos=15
    )
    
    replicador.executar_backtest()
    replicador.salvar_resultados()
    
    print("\n🎯 Replicação concluída!")
    print("Arquivos gerados:")
    print("  - historico_carteiras_replicacao.csv")
    print("  - curva_replicada_vs_meta.csv") 
    print("  - estatisticas_replicacao.json")


if __name__ == "__main__":
    main()