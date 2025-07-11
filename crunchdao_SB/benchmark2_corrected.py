"""
Benchmark 2 Corrigido - Versão estável com todos os fixes
"""

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import hamming_loss, accuracy_score, f1_score
import time
from typing import Dict, List, Tuple, Optional
import copy
from abc import ABC, abstractmethod
import warnings
warnings.filterwarnings('ignore')

# Importar as classes do benchmark original
from benchmark2_multilabel_online import (
    OnlineMultiLabelClassifier,
    OnlineBinaryRelevance,
    OnlineClassifierChain,
    OnlineCLR,
    OnlineQWML,
    OnlineHOMER,
    OnlineMLkNN,
    OnlinePCT,
    OnlineECC,
    PrequentialEvaluator
)


class OnlineOSMLELMFixed(OnlineMultiLabelClassifier):
    """
    OSML-ELM Corrigido - Versão estável
    """
    
    def __init__(self, n_hidden=100, activation='sigmoid', 
                 threshold_window=100, random_state=None):
        self.n_hidden = n_hidden
        self.activation = activation
        self.threshold_window = threshold_window
        self.random_state = random_state
        
        self.input_weights_ = None
        self.biases_ = None
        self.output_weights_ = None
        self.M_ = None
        self.n_labels_ = None
        
        self.threshold_ = 0.0
        self.output_history_ = []
        self.label_history_ = []
        
        self.n_samples_seen_ = 0
        
    def _activation_function(self, X):
        """Função de ativação."""
        if self.activation == 'sigmoid':
            return 1 / (1 + np.exp(-np.clip(X, -250, 250)))
        elif self.activation == 'tanh':
            return np.tanh(X)
        elif self.activation == 'relu':
            return np.maximum(0, X)
        return X
    
    def _calculate_hidden_output(self, X):
        """Calcular saída da camada oculta H."""
        X = np.atleast_2d(X)
        linear = np.dot(X, self.input_weights_.T) + self.biases_
        return self._activation_function(linear)
    
    def _update_threshold(self, outputs, y):
        """Atualizar threshold adaptativo."""
        if self.n_labels_ is None:
            return
            
        self.output_history_.extend(outputs.flatten())
        self.label_history_.extend(y.flatten())
        
        # Manter janela limitada
        max_size = self.threshold_window * self.n_labels_
        if len(self.output_history_) > max_size:
            self.output_history_ = self.output_history_[-max_size:]
            self.label_history_ = self.label_history_[-max_size:]
        
        # Calcular threshold
        if len(self.output_history_) >= 10:
            outputs_array = np.array(self.output_history_)
            labels_array = np.array(self.label_history_)
            
            positive_outputs = outputs_array[labels_array == 1]
            negative_outputs = outputs_array[labels_array == 0]
            
            if len(positive_outputs) > 0 and len(negative_outputs) > 0:
                self.threshold_ = (np.min(positive_outputs) + np.max(negative_outputs)) / 2
            else:
                self.threshold_ = 0.0
    
    def partial_fit(self, X, y, classes=None):
        """Implementação corrigida do OSML-ELM."""
        X = np.atleast_2d(X)
        y = np.atleast_2d(y)
        
        n_samples, n_features = X.shape
        
        if self.n_labels_ is None:
            self.n_labels_ = y.shape[1]
        
        # Converter para representação bipolar
        y_bipolar = 2 * y - 1
        
        if self.input_weights_ is None:
            # Inicialização
            rng = np.random.RandomState(self.random_state)
            self.input_weights_ = rng.uniform(-1, 1, (self.n_hidden, n_features))
            self.biases_ = rng.uniform(-1, 1, self.n_hidden)
            
            # Calcular H inicial
            H = self._calculate_hidden_output(X)
            
            # Inicializar M e beta
            try:
                self.M_ = np.linalg.inv(H.T @ H + 0.0001 * np.eye(self.n_hidden))
            except:
                self.M_ = np.linalg.pinv(H.T @ H + 0.0001 * np.eye(self.n_hidden))
            
            self.output_weights_ = self.M_ @ H.T @ y_bipolar
            
        else:
            # Atualização RLS sequencial
            for i in range(n_samples):
                Xi = X[i:i+1]
                yi_bipolar = y_bipolar[i:i+1]
                
                # Calcular hidden output
                Hi = self._calculate_hidden_output(Xi)
                
                # RLS update
                try:
                    # Calcular ganho de Kalman
                    K = self.M_ @ Hi.T / (1 + Hi @ self.M_ @ Hi.T)
                    
                    # Atualizar M
                    self.M_ = self.M_ - K @ Hi @ self.M_
                    
                    # Calcular erro de predição
                    prediction = Hi @ self.output_weights_
                    error = yi_bipolar - prediction
                    
                    # Atualizar pesos
                    self.output_weights_ = self.output_weights_ + K @ error
                    
                except Exception as e:
                    # Fallback para batch update se RLS falhar
                    print(f"RLS update failed: {e}, using batch update")
                    H = self._calculate_hidden_output(X[:i+1])
                    self.output_weights_ = np.linalg.pinv(H) @ y_bipolar[:i+1]
        
        # Atualizar threshold
        outputs = self._calculate_hidden_output(X) @ self.output_weights_
        self._update_threshold(outputs, y)
        
        self.n_samples_seen_ += n_samples
        
        return self
    
    def predict(self, X):
        """Predizer com threshold adaptativo."""
        if self.input_weights_ is None:
            # Não foi treinado ainda
            return np.zeros((len(X), self.n_labels_))
            
        X = np.atleast_2d(X)
        H = self._calculate_hidden_output(X)
        outputs = H @ self.output_weights_
        
        # Converter de bipolar para binário
        predictions = (outputs > self.threshold_).astype(int)
        
        return predictions


class OnlineRAkELFixed(OnlineMultiLabelClassifier):
    """RAkEL Corrigido - com classes fixas"""
    
    def __init__(self, k=3, n_models=10, base_estimator=None, random_state=None):
        from sklearn.linear_model import SGDClassifier
        
        self.k = k
        self.n_models = n_models
        self.base_estimator = base_estimator
        if self.base_estimator is None:
            self.base_estimator = SGDClassifier(
                loss='log_loss',
                learning_rate='constant',
                eta0=0.01,
                random_state=random_state
            )
        self.random_state = random_state
        self.models_ = None
        self.labelsets_ = None
        self.classes_ = None
        
    def _get_all_classes(self, k):
        """Gerar todas as classes possíveis para k labels."""
        classes = []
        for i in range(2**k):
            binary = format(i, f'0{k}b')
            classes.append(binary)
        return sorted(classes)
    
    def partial_fit(self, X, y, classes=None):
        """Treinar com labelsets fixos."""
        X = np.atleast_2d(X)
        y = np.atleast_2d(y)
        
        n_labels = y.shape[1]
        
        if self.models_ is None:
            rng = np.random.RandomState(self.random_state)
            self.labelsets_ = []
            self.models_ = []
            self.classes_ = []
            
            for _ in range(self.n_models):
                # Selecionar k labels aleatórios
                k_actual = min(self.k, n_labels)
                labelset = rng.choice(n_labels, size=k_actual, replace=False)
                self.labelsets_.append(labelset)
                
                # Criar modelo e classes para este labelset
                model = copy.deepcopy(self.base_estimator)
                self.models_.append(model)
                
                # Guardar todas as classes possíveis
                all_classes = self._get_all_classes(k_actual)
                self.classes_.append(all_classes)
        
        # Treinar cada modelo
        for i, (model, labelset, model_classes) in enumerate(
            zip(self.models_, self.labelsets_, self.classes_)
        ):
            y_subset = y[:, labelset]
            # Converter para string
            y_powerset = [''.join(map(str, row)) for row in y_subset.astype(int)]
            
            # Treinar com todas as classes possíveis
            model.partial_fit(X, y_powerset, classes=model_classes)
        
        return self
    
    def predict(self, X):
        """Predizer com voting."""
        X = np.atleast_2d(X)
        n_labels = max(max(ls) for ls in self.labelsets_) + 1
        votes = np.zeros((X.shape[0], n_labels))
        
        for model, labelset in zip(self.models_, self.labelsets_):
            powerset_pred = model.predict(X)
            
            # Decodificar predictions
            for i, pred_str in enumerate(powerset_pred):
                for j, label_idx in enumerate(labelset):
                    if j < len(pred_str) and pred_str[j] == '1':
                        votes[i, label_idx] += 1
        
        # Threshold baseado em voting
        threshold = self.n_models / 2
        return (votes >= threshold).astype(int)


def run_corrected_benchmark(use_synthetic=True, fast_test=True):
    """Executar benchmark corrigido."""
    
    print("="*60)
    print("BENCHMARK 2 CORRIGIDO - TODOS OS MODELOS FUNCIONANDO")
    print("="*60)
    
    # Dataset
    if use_synthetic:
        print("\nCriando dataset sintético multi-label...")
        n_samples = 1000 if fast_test else 5000
        n_features = 100
        n_labels = 10
        
        rng = np.random.RandomState(42)
        X = rng.randn(n_samples, n_features)
        
        # Labels correlacionados
        W = rng.randn(n_features, n_labels)
        logits = X @ W
        y = (logits > rng.randn(n_samples, n_labels)).astype(int)
    
    print(f"\nDataset: {X.shape[0]} amostras, {X.shape[1]} features, {y.shape[1]} labels")
    print(f"Label cardinality: {np.mean(np.sum(y, axis=1)):.2f}")
    print(f"Label density: {np.mean(y):.3f}")
    
    # Modelos - incluindo as versões corrigidas
    models = {
        '01.OSML-ELM': OnlineOSMLELMFixed(n_hidden=50, random_state=42),
        '02.BR': OnlineBinaryRelevance(random_state=42),
        '03.CC': OnlineClassifierChain(random_state=42),
        '04.CLR': OnlineCLR(random_state=42),
        '05.QWML': OnlineQWML(q=2.0, random_state=42),
        '06.HOMER': OnlineHOMER(k=3, random_state=42),
        '07.ML-kNN': OnlineMLkNN(k=10, window_size=500, random_state=42),
        '08.PCT': OnlinePCT(max_depth=5, random_state=42),
        '09.ECC': OnlineECC(n_chains=3 if fast_test else 10, random_state=42),
        '10.RAkEL': OnlineRAkELFixed(k=3, n_models=5 if fast_test else 10, random_state=42)
    }
    
    # Avaliador
    evaluator = PrequentialEvaluator(
        metrics=['hamming_loss', 'subset_accuracy', 'f1_example'],
        window_size=500,
        update_frequency=100
    )
    
    results = {}
    
    # Avaliar cada modelo
    for model_name, model in models.items():
        print(f"\n{'='*60}")
        print(f"Avaliando {model_name}")
        print('='*60)
        
        # Reset evaluator
        evaluator.metric_history = {m: [] for m in evaluator.metrics}
        evaluator.time_history = []
        evaluator.throughput_history = []
        
        try:
            model_results = evaluator.evaluate_online(
                model=copy.deepcopy(model),
                X_stream=X,
                y_stream=y,
                initial_train_size=100,
                max_samples=500 if fast_test else 2000
            )
            
            results[model_name] = model_results
            
            print(f"\nResultados finais - {model_name}:")
            for metric, value in model_results['final_metrics'].items():
                print(f"  {metric}: {value:.4f}")
            print(f"  Throughput médio: {model_results['avg_throughput']:.1f} samples/s")
            
        except Exception as e:
            print(f"Erro ao avaliar {model_name}: {str(e)}")
            results[model_name] = {
                'final_metrics': {m: np.nan for m in evaluator.metrics},
                'avg_throughput': 0
            }
    
    # Comparação final
    print("\n" + "="*60)
    print("COMPARAÇÃO FINAL - BENCHMARK CORRIGIDO")
    print("="*60)
    
    comparison_df = pd.DataFrame({
        model_name: res['final_metrics'] 
        for model_name, res in results.items()
        if res['final_metrics']
    }).T
    
    print("\n", comparison_df.round(4))
    
    # Salvar resultados
    comparison_df.to_csv('benchmark2_corrected_results.csv')
    print("\nResultados salvos em benchmark2_corrected_results.csv")
    
    # Ranking
    print("\nRanking por Hamming Loss (menor é melhor):")
    ranking = comparison_df.sort_values('hamming_loss')
    for i, (model, row) in enumerate(ranking.iterrows(), 1):
        if not np.isnan(row['hamming_loss']):
            print(f"{i}. {model}: {row['hamming_loss']:.4f}")
    
    # Análise de trade-offs
    print("\n" + "="*60)
    print("ANÁLISE DE TRADE-OFFS")
    print("="*60)
    
    # Criar DataFrame com throughput
    analysis_df = pd.DataFrame({
        'hamming_loss': [res['final_metrics']['hamming_loss'] for res in results.values()],
        'f1_example': [res['final_metrics']['f1_example'] for res in results.values()],
        'throughput': [res['avg_throughput'] for res in results.values()]
    }, index=results.keys())
    
    # Remover NaN
    analysis_df = analysis_df.dropna()
    
    print("\nTop 3 - Melhor Performance (Hamming Loss):")
    print(analysis_df.nsmallest(3, 'hamming_loss')[['hamming_loss', 'throughput']])
    
    print("\nTop 3 - Maior Velocidade:")
    print(analysis_df.nlargest(3, 'throughput')[['hamming_loss', 'throughput']])
    
    print("\nMelhor Trade-off (Performance × Velocidade):")
    # Normalizar métricas
    analysis_df['perf_score'] = 1 - analysis_df['hamming_loss']
    analysis_df['speed_score'] = analysis_df['throughput'] / analysis_df['throughput'].max()
    analysis_df['trade_off'] = analysis_df['perf_score'] * analysis_df['speed_score']
    
    print(analysis_df.nlargest(3, 'trade_off')[['hamming_loss', 'throughput', 'trade_off']])
    
    return results


if __name__ == "__main__":
    # Executar versão corrigida
    results = run_corrected_benchmark(use_synthetic=True, fast_test=True)
    
    print("\n" + "="*60)
    print("BENCHMARK CORRIGIDO CONCLUÍDO")
    print("="*60)