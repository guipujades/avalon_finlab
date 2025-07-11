"""
Benchmark Online Multi-label Corrigido - Baseado no Paper OSML-ELM
Corrige os problemas identificados na revisão crítica.
"""

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import hamming_loss
import time
from typing import Dict, List, Tuple, Optional
import copy
from abc import ABC, abstractmethod


class OnlineMultiLabelClassifier(BaseEstimator, ClassifierMixin, ABC):
    """Base class para classificadores online multi-label."""
    
    @abstractmethod
    def partial_fit(self, X, y, classes=None):
        """Atualização incremental com uma ou mais amostras."""
        pass
    
    @abstractmethod
    def predict(self, X):
        """Predizer labels."""
        pass
    
    def fit(self, X, y):
        """Treinar com batch inicial."""
        return self.partial_fit(X, y)


class OnlineOSMLELM(OnlineMultiLabelClassifier):
    """
    OSML-ELM corrigido com:
    - Atualização verdadeiramente online
    - Threshold adaptativo sem vazamento
    - RLS com dimensões corretas
    """
    
    def __init__(self, n_hidden=100, activation='sigmoid', 
                 threshold_window=100, random_state=None):
        self.n_hidden = n_hidden
        self.activation = activation
        self.threshold_window = threshold_window
        self.random_state = random_state
        
        # Parâmetros do modelo
        self.input_weights_ = None
        self.biases_ = None
        self.output_weights_ = None
        self.M_ = None
        
        # Para threshold adaptativo
        self.threshold_ = 0.0
        self.output_history_ = []
        self.label_history_ = []
        
        # Estatísticas online
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
        """Calcular saída da camada oculta."""
        # Garantir que X seja 2D
        X = np.atleast_2d(X)
        
        # H = activation(X * W^T + bias)
        linear = np.dot(X, self.input_weights_.T) + self.biases_
        return self._activation_function(linear)
    
    def _update_threshold(self, outputs, y):
        """Atualizar threshold adaptativo usando janela deslizante."""
        # Adicionar à história
        self.output_history_.extend(outputs.flatten())
        self.label_history_.extend(y.flatten())
        
        # Manter apenas janela recente
        if len(self.output_history_) > self.threshold_window * self.n_labels_:
            self.output_history_ = self.output_history_[-self.threshold_window * self.n_labels_:]
            self.label_history_ = self.label_history_[-self.threshold_window * self.n_labels_:]
        
        # Calcular threshold
        if len(self.output_history_) >= 10:
            outputs_array = np.array(self.output_history_)
            labels_array = np.array(self.label_history_)
            
            positive_outputs = outputs_array[labels_array == 1]
            negative_outputs = outputs_array[labels_array == 0]
            
            if len(positive_outputs) > 0 and len(negative_outputs) > 0:
                # Fórmula do paper: (min(Y_A) + max(Y_B)) / 2
                self.threshold_ = (np.min(positive_outputs) + np.max(negative_outputs)) / 2
            else:
                self.threshold_ = 0.0
    
    def partial_fit(self, X, y, classes=None):
        """Atualização online do OSML-ELM."""
        X = np.atleast_2d(X)
        y = np.atleast_2d(y)
        
        n_samples, n_features = X.shape
        self.n_labels_ = y.shape[1]
        
        # Inicialização na primeira chamada
        if self.input_weights_ is None:
            rng = np.random.RandomState(self.random_state)
            self.input_weights_ = rng.uniform(-1, 1, (self.n_hidden, n_features))
            self.biases_ = rng.uniform(-1, 1, self.n_hidden)
            
            # Calcular H inicial
            H = self._calculate_hidden_output(X)
            
            # Inicializar M e beta usando pseudo-inversa
            self.M_ = np.linalg.pinv(H.T @ H + 0.0001 * np.eye(self.n_hidden))
            self.output_weights_ = self.M_ @ H.T @ (2 * y - 1)  # Bipolar
            
        else:
            # Atualização RLS para cada amostra
            for i in range(n_samples):
                Xi = X[i:i+1]
                yi = y[i:i+1]
                
                # Calcular hidden output
                Hi = self._calculate_hidden_output(Xi)
                
                # RLS update (Sherman-Morrison formula)
                # M = M - (M @ H^T @ H @ M) / (1 + H @ M @ H^T)
                MH = self.M_ @ Hi.T
                HMH = Hi @ MH
                
                self.M_ = self.M_ - (MH @ MH.T) / (1 + HMH)
                
                # Update output weights
                # beta = beta + M @ H^T @ (y - H @ beta)
                error = (2 * yi - 1) - Hi @ self.output_weights_
                self.output_weights_ = self.output_weights_ + MH @ error.T
        
        # Atualizar threshold com as novas amostras
        outputs = self._calculate_hidden_output(X) @ self.output_weights_
        self._update_threshold(outputs, y)
        
        self.n_samples_seen_ += n_samples
        
        return self
    
    def predict(self, X):
        """Predizer labels."""
        X = np.atleast_2d(X)
        H = self._calculate_hidden_output(X)
        outputs = H @ self.output_weights_
        
        # Aplicar threshold
        predictions = (outputs > self.threshold_).astype(int)
        
        return predictions
    
    def predict_proba(self, X):
        """Probabilidades via sigmoid."""
        X = np.atleast_2d(X)
        H = self._calculate_hidden_output(X)
        outputs = H @ self.output_weights_
        
        # Sigmoid para probabilidades
        return 1 / (1 + np.exp(-outputs))


class OnlineBinaryRelevance(OnlineMultiLabelClassifier):
    """Binary Relevance com SGDClassifier para streaming."""
    
    def __init__(self, base_estimator=None, random_state=None):
        from sklearn.linear_model import SGDClassifier
        
        self.base_estimator = base_estimator
        if self.base_estimator is None:
            self.base_estimator = SGDClassifier(
                loss='log', 
                learning_rate='constant',
                eta0=0.01,
                random_state=random_state
            )
        self.random_state = random_state
        self.estimators_ = None
        
    def partial_fit(self, X, y, classes=None):
        """Atualização incremental."""
        X = np.atleast_2d(X)
        y = np.atleast_2d(y)
        
        n_labels = y.shape[1]
        
        if self.estimators_ is None:
            self.estimators_ = []
            for i in range(n_labels):
                estimator = copy.deepcopy(self.base_estimator)
                self.estimators_.append(estimator)
        
        # Atualizar cada classificador binário
        for i in range(n_labels):
            self.estimators_[i].partial_fit(X, y[:, i], classes=[0, 1])
        
        return self
    
    def predict(self, X):
        """Predizer."""
        predictions = np.zeros((len(X), len(self.estimators_)))
        
        for i, estimator in enumerate(self.estimators_):
            predictions[:, i] = estimator.predict(X)
        
        return predictions.astype(int)


class PrequentialEvaluator:
    """
    Avaliador prequential (test-then-train) para streaming.
    Corrige vazamento de dados e implementa protocolo correto.
    """
    
    def __init__(self, metrics=['hamming_loss', 'subset_accuracy', 'f1_example'],
                 window_size=1000, update_frequency=100):
        self.metrics = metrics
        self.window_size = window_size
        self.update_frequency = update_frequency
        
        # Histórico de métricas
        self.metric_history = {m: [] for m in metrics}
        self.time_history = []
        self.throughput_history = []
        
        # Janela deslizante para métricas
        self.y_true_window = []
        self.y_pred_window = []
        
        # Scaler online
        self.scaler = StandardScaler()
        self.scaler_fitted = False
        
    def evaluate_online(self, model, X_stream, y_stream, 
                       initial_train_size=100, max_samples=None):
        """
        Avaliação prequential completa.
        
        Parameters
        ----------
        model : OnlineMultiLabelClassifier
            Modelo com partial_fit
        X_stream : array-like
            Features do stream
        y_stream : array-like  
            Labels do stream
        initial_train_size : int
            Tamanho do treino inicial
        max_samples : int
            Limite de amostras (None = todas)
        """
        n_samples = len(X_stream)
        if max_samples:
            n_samples = min(n_samples, max_samples)
        
        # Treino inicial
        print(f"Treinamento inicial com {initial_train_size} amostras...")
        X_init = X_stream[:initial_train_size]
        y_init = y_stream[:initial_train_size]
        
        # Fit inicial do scaler
        self.scaler.fit(X_init)
        self.scaler_fitted = True
        X_init_scaled = self.scaler.transform(X_init)
        
        # Treino inicial do modelo
        model.fit(X_init_scaled, y_init)
        
        # Métricas acumuladas
        cumulative_metrics = {m: 0.0 for m in self.metrics}
        samples_evaluated = 0
        
        # Loop prequential
        print(f"Iniciando avaliação prequential...")
        start_time = time.time()
        
        for i in range(initial_train_size, n_samples):
            # Test
            X_i = X_stream[i:i+1]
            y_i = y_stream[i:i+1]
            
            # Atualizar scaler incrementalmente
            self.scaler.partial_fit(X_i)
            X_i_scaled = self.scaler.transform(X_i)
            
            # Predizer ANTES de treinar
            y_pred = model.predict(X_i_scaled)
            
            # Adicionar à janela
            self.y_true_window.append(y_i[0])
            self.y_pred_window.append(y_pred[0])
            
            # Manter janela limitada
            if len(self.y_true_window) > self.window_size:
                self.y_true_window.pop(0)
                self.y_pred_window.pop(0)
            
            # Train
            model.partial_fit(X_i_scaled, y_i)
            
            samples_evaluated += 1
            
            # Calcular métricas periodicamente
            if i % self.update_frequency == 0 or i == n_samples - 1:
                # Converter janela para arrays
                y_true_w = np.array(self.y_true_window)
                y_pred_w = np.array(self.y_pred_window)
                
                # Calcular métricas na janela
                current_metrics = self._calculate_metrics(y_true_w, y_pred_w)
                
                # Throughput
                elapsed = time.time() - start_time
                throughput = samples_evaluated / elapsed
                
                # Armazenar
                for metric_name, value in current_metrics.items():
                    self.metric_history[metric_name].append(value)
                
                self.time_history.append(i)
                self.throughput_history.append(throughput)
                
                # Log
                print(f"Sample {i}/{n_samples} | "
                      f"Hamming: {current_metrics.get('hamming_loss', 0):.4f} | "
                      f"Throughput: {throughput:.1f} samples/s")
        
        return self._compile_results()
    
    def _calculate_metrics(self, y_true, y_pred):
        """Calcular métricas sem vazamento."""
        metrics = {}
        
        if len(y_true) == 0:
            return metrics
        
        # Hamming Loss
        if 'hamming_loss' in self.metrics:
            metrics['hamming_loss'] = hamming_loss(y_true, y_pred)
        
        # Subset Accuracy
        if 'subset_accuracy' in self.metrics:
            metrics['subset_accuracy'] = np.mean(
                np.all(y_true == y_pred, axis=1)
            )
        
        # Example-based F1
        if 'f1_example' in self.metrics:
            f1_scores = []
            for i in range(len(y_true)):
                true_i = y_true[i]
                pred_i = y_pred[i]
                
                if np.sum(true_i) == 0 and np.sum(pred_i) == 0:
                    f1_scores.append(1.0)
                else:
                    intersection = np.sum(true_i & pred_i)
                    precision = intersection / np.sum(pred_i) if np.sum(pred_i) > 0 else 0
                    recall = intersection / np.sum(true_i) if np.sum(true_i) > 0 else 0
                    
                    if precision + recall > 0:
                        f1 = 2 * precision * recall / (precision + recall)
                    else:
                        f1 = 0
                    
                    f1_scores.append(f1)
            
            metrics['f1_example'] = np.mean(f1_scores)
        
        return metrics
    
    def _compile_results(self):
        """Compilar resultados finais."""
        results = {
            'metrics': self.metric_history,
            'time_points': self.time_history,
            'throughput': self.throughput_history,
            'final_metrics': {
                m: self.metric_history[m][-1] 
                for m in self.metrics
            },
            'avg_throughput': np.mean(self.throughput_history)
        }
        
        return results


def create_stream_generator(X, y, chunk_size=1, shuffle=True, random_state=None):
    """
    Gerador de stream para simular dados chegando.
    
    Parameters
    ----------
    X : array-like
        Features
    y : array-like
        Labels
    chunk_size : int
        Tamanho de cada chunk
    shuffle : bool
        Se deve embaralhar
    random_state : int
        Seed para reprodutibilidade
    """
    n_samples = len(X)
    indices = np.arange(n_samples)
    
    if shuffle:
        rng = np.random.RandomState(random_state)
        rng.shuffle(indices)
    
    for i in range(0, n_samples, chunk_size):
        idx = indices[i:i+chunk_size]
        yield X[idx], y[idx]


def run_corrected_benchmark():
    """Executar benchmark corrigido."""
    
    # Criar dataset sintético multi-label
    print("Criando dataset sintético...")
    n_samples = 5000
    n_features = 100
    n_labels = 10
    
    # Gerar dados com dependências entre labels
    rng = np.random.RandomState(42)
    X = rng.randn(n_samples, n_features)
    
    # Criar matriz de pesos para gerar labels correlacionados
    W = rng.randn(n_features, n_labels)
    logits = X @ W
    y = (logits > rng.randn(n_samples, n_labels)).astype(int)
    
    print(f"Dataset: {n_samples} amostras, {n_features} features, {n_labels} labels")
    print(f"Label cardinality: {np.mean(np.sum(y, axis=1)):.2f}")
    
    # Modelos para testar
    models = {
        'OSML-ELM': OnlineOSMLELM(n_hidden=50, random_state=42),
        'OBR': OnlineBinaryRelevance(random_state=42)
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
        print(f"\nAvaliando {model_name}...")
        
        model_results = evaluator.evaluate_online(
            model=copy.deepcopy(model),
            X_stream=X,
            y_stream=y,
            initial_train_size=100,
            max_samples=2000  # Limitar para teste rápido
        )
        
        results[model_name] = model_results
        
        # Imprimir resultados finais
        print(f"\nResultados finais - {model_name}:")
        for metric, value in model_results['final_metrics'].items():
            print(f"  {metric}: {value:.4f}")
        print(f"  Throughput médio: {model_results['avg_throughput']:.1f} samples/s")
    
    return results


if __name__ == "__main__":
    print("="*60)
    print("BENCHMARK ONLINE MULTI-LABEL CORRIGIDO")
    print("="*60)
    
    results = run_corrected_benchmark()
    
    print("\n" + "="*60)
    print("BENCHMARK CONCLUÍDO")
    print("="*60)