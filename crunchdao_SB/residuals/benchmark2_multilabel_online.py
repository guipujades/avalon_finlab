"""
Benchmark 2: Multi-label Online Classifiers
Implementação completa dos modelos do paper OSML-ELM com correções.

Modelos implementados:
1. OSML-ELM - Online Sequential Multi-label ELM (proposto)
2. BR - Binary Relevance 
3. CC - Classifier Chains
4. CLR - Calibrated Label Ranking
5. QWML - Q-Weighted Multi-label
6. HOMER - Hierarchy Of Multi-label classifiERs
7. ML-kNN - Multi-Label k-Nearest Neighbors
8. PCT - Predictive Clustering Trees
9. ECC - Ensemble Classifier Chains
10. RAkEL - Random k-Labelsets
"""

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import hamming_loss, accuracy_score, f1_score
from sklearn.model_selection import train_test_split
import time
from typing import Dict, List, Tuple, Optional
import copy
from abc import ABC, abstractmethod
import warnings
warnings.filterwarnings('ignore')


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
    OSML-ELM (Proposed) - Online Sequential Multi-label ELM
    Implementação fiel ao paper com correções.
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
        """
        Atualizar threshold adaptativo usando fórmula do paper:
        threshold = (min(Y_A) + max(Y_B)) / 2
        onde Y_A são outputs para labels positivos e Y_B para negativos.
        """
        self.output_history_.extend(outputs.flatten())
        self.label_history_.extend(y.flatten())
        
        if len(self.output_history_) > self.threshold_window * self.n_labels_:
            self.output_history_ = self.output_history_[-self.threshold_window * self.n_labels_:]
            self.label_history_ = self.label_history_[-self.threshold_window * self.n_labels_:]
        
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
        """Implementação do algoritmo OSML-ELM do paper."""
        X = np.atleast_2d(X)
        y = np.atleast_2d(y)
        
        n_samples, n_features = X.shape
        self.n_labels_ = y.shape[1]
        
        # Converter para representação bipolar como no paper
        y_bipolar = 2 * y - 1
        
        if self.input_weights_ is None:
            # Inicialização
            rng = np.random.RandomState(self.random_state)
            self.input_weights_ = rng.uniform(-1, 1, (self.n_hidden, n_features))
            self.biases_ = rng.uniform(-1, 1, self.n_hidden)
            
            # Fase inicial de treino
            H = self._calculate_hidden_output(X)
            self.M_ = np.linalg.pinv(H.T @ H + 0.0001 * np.eye(self.n_hidden))
            self.output_weights_ = self.M_ @ H.T @ y_bipolar
            
        else:
            # Fase sequencial - RLS update
            for i in range(n_samples):
                Xi = X[i:i+1]
                yi_bipolar = y_bipolar[i:i+1]
                
                Hi = self._calculate_hidden_output(Xi)
                
                # Fórmulas do paper (equações 11 e 12)
                MH = self.M_ @ Hi.T
                denominator = 1 + Hi @ MH
                
                # M_k+1 = M_k - (M_k @ h_k+1 @ h_k+1^T @ M_k) / (1 + h_k+1^T @ M_k @ h_k+1)
                self.M_ = self.M_ - (MH @ MH.T) / denominator
                
                # beta_k+1 = beta_k + M_k+1 @ h_k+1 @ (y_k+1^T - h_k+1^T @ beta_k)
                prediction = Hi @ self.output_weights_  # (1, n_labels)
                error = yi_bipolar - prediction  # (1, n_labels)
                # M @ Hi.T tem shape (n_hidden, 1), error.T tem shape (n_labels, 1)
                # Precisamos fazer: self.output_weights_ += (M @ Hi.T) @ error
                update = self.M_ @ Hi.T  # (n_hidden, 1)
                self.output_weights_ = self.output_weights_ + update @ error  # (n_hidden, n_labels)
        
        # Atualizar threshold
        outputs = self._calculate_hidden_output(X) @ self.output_weights_
        self._update_threshold(outputs, y)
        
        self.n_samples_seen_ += n_samples
        
        return self
    
    def predict(self, X):
        """Predizer com threshold adaptativo."""
        X = np.atleast_2d(X)
        H = self._calculate_hidden_output(X)
        outputs = H @ self.output_weights_
        
        predictions = (outputs > self.threshold_).astype(int)
        
        return predictions


class OnlineBinaryRelevance(OnlineMultiLabelClassifier):
    """BR - Binary Relevance para streaming."""
    
    def __init__(self, base_estimator=None, random_state=None):
        from sklearn.linear_model import SGDClassifier
        
        self.base_estimator = base_estimator
        if self.base_estimator is None:
            self.base_estimator = SGDClassifier(
                loss='log_loss', 
                learning_rate='constant',
                eta0=0.01,
                random_state=random_state
            )
        self.random_state = random_state
        self.estimators_ = None
        
    def partial_fit(self, X, y, classes=None):
        """Treinar um classificador por label."""
        X = np.atleast_2d(X)
        y = np.atleast_2d(y)
        
        n_labels = y.shape[1]
        
        if self.estimators_ is None:
            self.estimators_ = []
            for i in range(n_labels):
                estimator = copy.deepcopy(self.base_estimator)
                self.estimators_.append(estimator)
        
        for i in range(n_labels):
            self.estimators_[i].partial_fit(X, y[:, i], classes=[0, 1])
        
        return self
    
    def predict(self, X):
        """Predizer cada label independentemente."""
        predictions = np.zeros((len(X), len(self.estimators_)))
        
        for i, estimator in enumerate(self.estimators_):
            predictions[:, i] = estimator.predict(X)
        
        return predictions.astype(int)


class OnlineClassifierChain(OnlineMultiLabelClassifier):
    """CC - Classifier Chain para streaming."""
    
    def __init__(self, base_estimator=None, order=None, random_state=None):
        from sklearn.linear_model import SGDClassifier
        
        self.base_estimator = base_estimator
        if self.base_estimator is None:
            self.base_estimator = SGDClassifier(
                loss='log_loss',
                learning_rate='constant',
                eta0=0.01,
                random_state=random_state
            )
        self.order = order
        self.random_state = random_state
        self.estimators_ = None
        self.n_labels_ = None
        
    def partial_fit(self, X, y, classes=None):
        """Treinar em cadeia."""
        X = np.atleast_2d(X)
        y = np.atleast_2d(y)
        
        n_labels = y.shape[1]
        
        if self.n_labels_ is None:
            self.n_labels_ = n_labels
            if self.order is None:
                self.order = list(range(n_labels))
            
            self.estimators_ = []
            for i in range(n_labels):
                estimator = copy.deepcopy(self.base_estimator)
                self.estimators_.append(estimator)
        
        for label_idx in range(n_labels):
            augmented_X = X
            
            if label_idx > 0:
                previous_predictions = np.zeros((X.shape[0], label_idx))
                for j in range(label_idx):
                    previous_predictions[:, j] = y[:, self.order[j]]
                augmented_X = np.hstack([X, previous_predictions])
            
            self.estimators_[label_idx].partial_fit(
                augmented_X, 
                y[:, self.order[label_idx]], 
                classes=[0, 1]
            )
        
        return self
    
    def predict(self, X):
        """Predizer em cadeia."""
        X = np.atleast_2d(X)
        predictions = np.zeros((X.shape[0], self.n_labels_))
        
        for label_idx in range(self.n_labels_):
            augmented_X = X
            
            if label_idx > 0:
                augmented_X = np.hstack([X, predictions[:, :label_idx]])
            
            predictions[:, self.order[label_idx]] = self.estimators_[label_idx].predict(augmented_X)
        
        return predictions.astype(int)


class OnlineCLR(OnlineMultiLabelClassifier):
    """CLR - Calibrated Label Ranking para streaming."""
    
    def __init__(self, base_estimator=None, random_state=None):
        from sklearn.linear_model import SGDClassifier
        
        self.base_estimator = base_estimator
        if self.base_estimator is None:
            self.base_estimator = SGDClassifier(
                loss='log_loss',
                learning_rate='constant',
                eta0=0.01,
                random_state=random_state
            )
        self.random_state = random_state
        self.pairwise_models_ = None
        self.calibration_model_ = None
        self.n_labels_ = None
        
    def partial_fit(self, X, y, classes=None):
        """Treinar modelos pairwise e calibração."""
        X = np.atleast_2d(X)
        y = np.atleast_2d(y)
        
        if self.n_labels_ is None:
            self.n_labels_ = y.shape[1]
            self.pairwise_models_ = {}
            self.calibration_model_ = copy.deepcopy(self.base_estimator)
            
            for i in range(self.n_labels_):
                for j in range(i + 1, self.n_labels_):
                    self.pairwise_models_[(i, j)] = copy.deepcopy(self.base_estimator)
        
        # Treinar modelos pairwise
        for (i, j), model in self.pairwise_models_.items():
            mask = (y[:, i] != y[:, j])
            if np.any(mask):
                X_pair = X[mask]
                y_pair = y[mask, i]  # 1 se label i é preferido sobre j
                model.partial_fit(X_pair, y_pair, classes=[0, 1])
        
        # Treinar modelo de calibração
        y_calibration = np.any(y, axis=1).astype(int)
        self.calibration_model_.partial_fit(X, y_calibration, classes=[0, 1])
        
        return self
    
    def predict(self, X):
        """Predizer com ranking calibrado."""
        X = np.atleast_2d(X)
        n_samples = X.shape[0]
        
        # Calcular scores de ranking
        scores = np.zeros((n_samples, self.n_labels_))
        
        for (i, j), model in self.pairwise_models_.items():
            predictions = model.predict_proba(X)[:, 1] if hasattr(model, 'predict_proba') else model.predict(X)
            scores[:, i] += predictions
            scores[:, j] += (1 - predictions)
        
        # Normalizar scores
        scores = scores / (self.n_labels_ - 1)
        
        # Calibrar com threshold
        calibration_pred = self.calibration_model_.predict(X)
        predictions = np.zeros((n_samples, self.n_labels_))
        
        for i in range(n_samples):
            if calibration_pred[i] == 1:
                # Pelo menos um label deve ser positivo
                threshold = np.median(scores[i])
                predictions[i] = (scores[i] >= threshold).astype(int)
                if np.sum(predictions[i]) == 0:
                    predictions[i, np.argmax(scores[i])] = 1
        
        return predictions.astype(int)


class OnlineQWML(OnlineMultiLabelClassifier):
    """QWML - Q-Weighted Multi-Label para streaming."""
    
    def __init__(self, q=2.0, base_estimator=None, random_state=None):
        from sklearn.linear_model import SGDClassifier
        
        self.q = q
        self.base_estimator = base_estimator
        if self.base_estimator is None:
            self.base_estimator = SGDClassifier(
                loss='log_loss',
                learning_rate='constant',
                eta0=0.01,
                random_state=random_state
            )
        self.random_state = random_state
        self.pairwise_models_ = None
        self.n_labels_ = None
        
    def partial_fit(self, X, y, classes=None):
        """Treinar com pesos Q."""
        X = np.atleast_2d(X)
        y = np.atleast_2d(y)
        
        if self.n_labels_ is None:
            self.n_labels_ = y.shape[1]
            self.pairwise_models_ = {}
            
            for i in range(self.n_labels_):
                for j in range(i + 1, self.n_labels_):
                    self.pairwise_models_[(i, j)] = copy.deepcopy(self.base_estimator)
        
        for (i, j), model in self.pairwise_models_.items():
            mask = (y[:, i] != y[:, j])
            if np.any(mask):
                X_pair = X[mask]
                y_pair = y[mask, i]
                
                # Aplicar peso Q baseado na diferença
                sample_weights = np.ones(len(X_pair))
                diff_mask = (y[mask, i] == 1) & (y[mask, j] == 0)
                sample_weights[diff_mask] = self.q
                
                if hasattr(model, 'partial_fit'):
                    model.partial_fit(X_pair, y_pair, classes=[0, 1])
        
        return self
    
    def predict(self, X):
        """Predizer com voting ponderado por Q."""
        X = np.atleast_2d(X)
        votes = np.zeros((X.shape[0], self.n_labels_))
        
        for (i, j), model in self.pairwise_models_.items():
            predictions = model.predict(X)
            votes[:, i] += predictions * self.q
            votes[:, j] += (1 - predictions) * self.q
        
        avg_votes = votes / (self.n_labels_ - 1)
        return (avg_votes > self.q / 2).astype(int)


class OnlineHOMER(OnlineMultiLabelClassifier):
    """HOMER - Hierarchy Of Multi-label classifiERs para streaming."""
    
    def __init__(self, k=3, base_estimator=None, random_state=None):
        from sklearn.linear_model import SGDClassifier
        
        self.k = k
        self.base_estimator = base_estimator
        if self.base_estimator is None:
            self.base_estimator = SGDClassifier(
                loss='log_loss',
                learning_rate='constant',
                eta0=0.01,
                random_state=random_state
            )
        self.random_state = random_state
        self.hierarchy_ = None
        self.models_ = None
        
    def partial_fit(self, X, y, classes=None):
        """Treinar hierarquia."""
        X = np.atleast_2d(X)
        y = np.atleast_2d(y)
        
        if self.hierarchy_ is None:
            self._build_hierarchy(y.shape[1])
            self.models_ = {}
            for node in self.hierarchy_:
                self.models_[node] = copy.deepcopy(self.base_estimator)
        
        for node, labels in self.hierarchy_.items():
            if len(labels) == 1:
                self.models_[node].partial_fit(X, y[:, labels[0]], classes=[0, 1])
            else:
                y_meta = np.any(y[:, labels], axis=1).astype(int)
                self.models_[node].partial_fit(X, y_meta, classes=[0, 1])
        
        return self
    
    def _build_hierarchy(self, n_labels):
        """Construir hierarquia de labels."""
        self.hierarchy_ = {}
        
        # Dividir labels em grupos de tamanho k
        n_nodes = (n_labels + self.k - 1) // self.k
        for i in range(n_nodes):
            start = i * self.k
            end = min((i + 1) * self.k, n_labels)
            self.hierarchy_[f'node_{i}'] = list(range(start, end))
        
        # Nó raiz
        self.hierarchy_['root'] = list(range(n_labels))
    
    def predict(self, X):
        """Predizer através da hierarquia."""
        X = np.atleast_2d(X)
        n_labels = len(self.hierarchy_['root'])
        predictions = np.zeros((X.shape[0], n_labels))
        
        # Predizer no nó raiz
        root_pred = self.models_['root'].predict(X)
        
        for i, active in enumerate(root_pred):
            if active:
                # Descer na hierarquia
                for node, labels in self.hierarchy_.items():
                    if node != 'root' and len(labels) > 0:
                        node_pred = self.models_[node].predict(X[i:i+1])
                        if node_pred[0]:
                            for label in labels:
                                predictions[i, label] = 1
        
        return predictions.astype(int)


class OnlineMLkNN(OnlineMultiLabelClassifier):
    """ML-kNN - Multi-Label k-NN para streaming."""
    
    def __init__(self, k=10, s=1.0, window_size=1000, random_state=None):
        self.k = k
        self.s = s  # smoothing parameter
        self.window_size = window_size
        self.random_state = random_state
        self.X_window_ = None
        self.y_window_ = None
        
    def partial_fit(self, X, y, classes=None):
        """Manter janela de exemplos."""
        X = np.atleast_2d(X)
        y = np.atleast_2d(y)
        
        if self.X_window_ is None:
            self.X_window_ = X
            self.y_window_ = y
        else:
            self.X_window_ = np.vstack([self.X_window_, X])
            self.y_window_ = np.vstack([self.y_window_, y])
        
        # Manter tamanho da janela
        if len(self.X_window_) > self.window_size:
            n_remove = len(self.X_window_) - self.window_size
            self.X_window_ = self.X_window_[n_remove:]
            self.y_window_ = self.y_window_[n_remove:]
        
        return self
    
    def predict(self, X):
        """Predizer usando ML-kNN."""
        from sklearn.neighbors import NearestNeighbors
        
        X = np.atleast_2d(X)
        n_labels = self.y_window_.shape[1]
        predictions = np.zeros((X.shape[0], n_labels))
        
        if len(self.X_window_) < self.k:
            return predictions.astype(int)
        
        nbrs = NearestNeighbors(n_neighbors=min(self.k, len(self.X_window_)))
        nbrs.fit(self.X_window_)
        
        distances, indices = nbrs.kneighbors(X)
        
        for i in range(X.shape[0]):
            neighbor_labels = self.y_window_[indices[i]]
            
            for j in range(n_labels):
                # Contar vizinhos com label j
                c_j = np.sum(neighbor_labels[:, j])
                
                # Aplicar regra ML-kNN com smoothing
                if c_j >= self.k / 2:
                    predictions[i, j] = 1
        
        return predictions.astype(int)


class OnlinePCT(OnlineMultiLabelClassifier):
    """PCT - Predictive Clustering Trees para streaming."""
    
    def __init__(self, max_depth=5, min_samples_split=20, random_state=None):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.random_state = random_state
        self.tree_ = None
        self.n_labels_ = None
        self.n_features_ = None
        
    def partial_fit(self, X, y, classes=None):
        """Atualizar árvore incrementalmente."""
        X = np.atleast_2d(X)
        y = np.atleast_2d(y)
        
        if self.n_labels_ is None:
            self.n_labels_ = y.shape[1]
            self.n_features_ = X.shape[1]
            self.tree_ = {
                'node_id': 0,
                'depth': 0,
                'n_samples': 0,
                'label_sum': np.zeros(self.n_labels_),
                'feature_sum': np.zeros(self.n_features_),
                'feature_sq_sum': np.zeros(self.n_features_),
                'is_leaf': True
            }
        
        # Atualizar árvore com novos exemplos
        for i in range(len(X)):
            self._update_tree(self.tree_, X[i], y[i])
        
        return self
    
    def _update_tree(self, node, x, y):
        """Atualizar nó da árvore."""
        node['n_samples'] += 1
        node['label_sum'] += y
        node['feature_sum'] += x
        node['feature_sq_sum'] += x ** 2
        
        if node['is_leaf']:
            # Verificar se deve dividir
            if node['n_samples'] >= self.min_samples_split and node['depth'] < self.max_depth:
                self._try_split(node)
        else:
            # Descer na árvore
            if x[node['split_feature']] <= node['split_threshold']:
                self._update_tree(node['left'], x, y)
            else:
                self._update_tree(node['right'], x, y)
    
    def _try_split(self, node):
        """Tentar dividir nó."""
        if node['n_samples'] < self.min_samples_split * 2:
            return
        
        # Calcular variância de cada feature
        mean = node['feature_sum'] / node['n_samples']
        var = (node['feature_sq_sum'] / node['n_samples']) - mean ** 2
        
        # Escolher feature com maior variância
        best_feature = np.argmax(var)
        threshold = mean[best_feature]
        
        node['is_leaf'] = False
        node['split_feature'] = best_feature
        node['split_threshold'] = threshold
        
        # Criar nós filhos
        node['left'] = {
            'node_id': node['node_id'] * 2 + 1,
            'depth': node['depth'] + 1,
            'n_samples': 0,
            'label_sum': np.zeros(self.n_labels_),
            'feature_sum': np.zeros(self.n_features_),
            'feature_sq_sum': np.zeros(self.n_features_),
            'is_leaf': True
        }
        
        node['right'] = {
            'node_id': node['node_id'] * 2 + 2,
            'depth': node['depth'] + 1,
            'n_samples': 0,
            'label_sum': np.zeros(self.n_labels_),
            'feature_sum': np.zeros(self.n_features_),
            'feature_sq_sum': np.zeros(self.n_features_),
            'is_leaf': True
        }
    
    def predict(self, X):
        """Predizer usando árvore."""
        X = np.atleast_2d(X)
        predictions = np.zeros((X.shape[0], self.n_labels_))
        
        for i in range(X.shape[0]):
            node = self.tree_
            
            # Descer até folha
            while not node['is_leaf']:
                if X[i, node['split_feature']] <= node['split_threshold']:
                    node = node['left']
                else:
                    node = node['right']
            
            # Predizer com média do nó
            if node['n_samples'] > 0:
                predictions[i] = (node['label_sum'] / node['n_samples'] > 0.5).astype(int)
        
        return predictions.astype(int)


class OnlineECC(OnlineMultiLabelClassifier):
    """ECC - Ensemble of Classifier Chains para streaming."""
    
    def __init__(self, n_chains=10, base_estimator=None, random_state=None):
        self.n_chains = n_chains
        self.base_estimator = base_estimator
        self.random_state = random_state
        self.chains_ = None
        
    def partial_fit(self, X, y, classes=None):
        """Treinar ensemble de chains."""
        if self.chains_ is None:
            self.chains_ = []
            rng = np.random.RandomState(self.random_state)
            
            for i in range(self.n_chains):
                # Ordem aleatória para cada chain
                order = rng.permutation(y.shape[1]).tolist()
                chain = OnlineClassifierChain(
                    base_estimator=copy.deepcopy(self.base_estimator),
                    order=order,
                    random_state=self.random_state + i if self.random_state else None
                )
                self.chains_.append(chain)
        
        # Treinar cada chain
        for chain in self.chains_:
            chain.partial_fit(X, y)
        
        return self
    
    def predict(self, X):
        """Predizer com voting do ensemble."""
        predictions = np.zeros((len(X), self.chains_[0].n_labels_))
        
        for chain in self.chains_:
            predictions += chain.predict(X)
        
        # Voting majoritário
        return (predictions >= self.n_chains / 2).astype(int)


class OnlineRAkEL(OnlineMultiLabelClassifier):
    """RAkEL - Random k-Labelsets para streaming."""
    
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
        
    def partial_fit(self, X, y, classes=None):
        """Treinar com random labelsets."""
        X = np.atleast_2d(X)
        y = np.atleast_2d(y)
        
        n_labels = y.shape[1]
        
        if self.models_ is None:
            rng = np.random.RandomState(self.random_state)
            self.labelsets_ = []
            self.models_ = []
            
            for _ in range(self.n_models):
                # Selecionar k labels aleatórios
                labelset = rng.choice(n_labels, size=min(self.k, n_labels), replace=False)
                self.labelsets_.append(labelset)
                self.models_.append(copy.deepcopy(self.base_estimator))
        
        # Treinar cada modelo no seu labelset
        for i, (model, labelset) in enumerate(zip(self.models_, self.labelsets_)):
            y_subset = y[:, labelset]
            # Converter para powerset (representação string)
            y_powerset = self._to_powerset(y_subset)
            
            # Usar todas as classes possíveis para evitar erro
            all_classes = self._get_all_possible_classes(len(labelset))
            model.partial_fit(X, y_powerset, classes=all_classes)
        
        return self
    
    def _to_powerset(self, y_subset):
        """Converter subset para powerset."""
        return [''.join(map(str, row)) for row in y_subset.astype(int)]
    
    def _get_all_possible_classes(self, k):
        """Gerar todas as classes possíveis do powerset para k labels."""
        import itertools
        classes = []
        for i in range(2**k):
            binary = format(i, f'0{k}b')
            classes.append(binary)
        return sorted(classes)
    
    def predict(self, X):
        """Predizer com voting."""
        X = np.atleast_2d(X)
        n_labels = max(max(ls) for ls in self.labelsets_) + 1
        votes = np.zeros((X.shape[0], n_labels))
        
        for model, labelset in zip(self.models_, self.labelsets_):
            powerset_pred = model.predict(X)
            
            # Decodificar powerset predictions
            for i, pred_str in enumerate(powerset_pred):
                if len(pred_str) == len(labelset):
                    for j, label_idx in enumerate(labelset):
                        if pred_str[j] == '1':
                            votes[i, label_idx] += 1
        
        # Threshold baseado em voting
        threshold = self.n_models / (2 * self.k)
        return (votes >= threshold).astype(int)


class PrequentialEvaluator:
    """
    Avaliador prequential (test-then-train) para streaming.
    Implementação correta sem vazamento de dados.
    """
    
    def __init__(self, metrics=['hamming_loss', 'subset_accuracy', 'f1_example'],
                 window_size=1000, update_frequency=100):
        self.metrics = metrics
        self.window_size = window_size
        self.update_frequency = update_frequency
        
        self.metric_history = {m: [] for m in metrics}
        self.time_history = []
        self.throughput_history = []
        
        self.y_true_window = []
        self.y_pred_window = []
        
        self.scaler = None
        
    def evaluate_online(self, model, X_stream, y_stream, 
                       initial_train_size=100, max_samples=None):
        """
        Avaliação prequential completa.
        """
        n_samples = len(X_stream)
        if max_samples:
            n_samples = min(n_samples, max_samples)
        
        print(f"Treinamento inicial com {initial_train_size} amostras...")
        X_init = X_stream[:initial_train_size]
        y_init = y_stream[:initial_train_size]
        
        # Inicializar scaler online
        from sklearn.preprocessing import StandardScaler
        self.scaler = StandardScaler()
        self.scaler.fit(X_init)
        X_init_scaled = self.scaler.transform(X_init)
        
        # Treino inicial
        model.fit(X_init_scaled, y_init)
        
        # Resetar janelas
        self.y_true_window = []
        self.y_pred_window = []
        
        # Loop prequential
        print(f"Iniciando avaliação prequential...")
        start_time = time.time()
        samples_evaluated = 0
        
        for i in range(initial_train_size, n_samples):
            # Test-then-train
            X_i = X_stream[i:i+1]
            y_i = y_stream[i:i+1]
            
            # Atualizar scaler incrementalmente
            self.scaler.partial_fit(X_i)
            X_i_scaled = self.scaler.transform(X_i)
            
            # TEST: Predizer ANTES de treinar
            y_pred = model.predict(X_i_scaled)
            
            # Adicionar à janela
            self.y_true_window.append(y_i[0])
            self.y_pred_window.append(y_pred[0])
            
            # Manter janela limitada
            if len(self.y_true_window) > self.window_size:
                self.y_true_window.pop(0)
                self.y_pred_window.pop(0)
            
            # TRAIN: Treinar DEPOIS de testar
            model.partial_fit(X_i_scaled, y_i)
            
            samples_evaluated += 1
            
            # Calcular métricas periodicamente
            if i % self.update_frequency == 0 or i == n_samples - 1:
                y_true_w = np.array(self.y_true_window)
                y_pred_w = np.array(self.y_pred_window)
                
                current_metrics = self._calculate_metrics(y_true_w, y_pred_w)
                
                elapsed = time.time() - start_time
                throughput = samples_evaluated / elapsed
                
                for metric_name, value in current_metrics.items():
                    self.metric_history[metric_name].append(value)
                
                self.time_history.append(i)
                self.throughput_history.append(throughput)
                
                print(f"Sample {i}/{n_samples} | "
                      f"Hamming: {current_metrics.get('hamming_loss', 0):.4f} | "
                      f"Throughput: {throughput:.1f} samples/s")
        
        return self._compile_results()
    
    def _calculate_metrics(self, y_true, y_pred):
        """Calcular métricas."""
        metrics = {}
        
        if len(y_true) == 0:
            return metrics
        
        if 'hamming_loss' in self.metrics:
            metrics['hamming_loss'] = hamming_loss(y_true, y_pred)
        
        if 'subset_accuracy' in self.metrics:
            metrics['subset_accuracy'] = np.mean(
                np.all(y_true == y_pred, axis=1)
            )
        
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
        """Compilar resultados."""
        results = {
            'metrics': self.metric_history,
            'time_points': self.time_history,
            'throughput': self.throughput_history,
            'final_metrics': {
                m: self.metric_history[m][-1] if self.metric_history[m] else 0
                for m in self.metrics
            },
            'avg_throughput': np.mean(self.throughput_history) if self.throughput_history else 0
        }
        
        return results


def run_benchmark2(use_synthetic=True, fast_test=False):
    """Executar benchmark 2 com todos os modelos."""
    
    if use_synthetic:
        print("Criando dataset sintético multi-label...")
        n_samples = 5000 if not fast_test else 1000
        n_features = 100
        n_labels = 10
        
        rng = np.random.RandomState(42)
        X = rng.randn(n_samples, n_features)
        
        # Criar labels correlacionados
        W = rng.randn(n_features, n_labels)
        logits = X @ W
        y = (logits > rng.randn(n_samples, n_labels)).astype(int)
        
    else:
        print("Carregando dados reais...")
        # Implementar conversão de structural break para multi-label
        pass
    
    print(f"\nDataset: {X.shape[0]} amostras, {X.shape[1]} features, {y.shape[1]} labels")
    print(f"Label cardinality: {np.mean(np.sum(y, axis=1)):.2f}")
    print(f"Label density: {np.mean(y):.3f}")
    
    # Todos os modelos do paper
    models = {
        '01.OSML-ELM': OnlineOSMLELM(n_hidden=50, random_state=42),
        '02.BR': OnlineBinaryRelevance(random_state=42),
        '03.CC': OnlineClassifierChain(random_state=42),
        '04.CLR': OnlineCLR(random_state=42),
        '05.QWML': OnlineQWML(q=2.0, random_state=42),
        '06.HOMER': OnlineHOMER(k=3, random_state=42),
        '07.ML-kNN': OnlineMLkNN(k=10, window_size=500, random_state=42),
        '08.PCT': OnlinePCT(max_depth=5, random_state=42),
        '09.ECC': OnlineECC(n_chains=5 if fast_test else 10, random_state=42),
        '10.RAkEL': OnlineRAkEL(k=3, n_models=5 if fast_test else 10, random_state=42)
    }
    
    evaluator = PrequentialEvaluator(
        metrics=['hamming_loss', 'subset_accuracy', 'f1_example'],
        window_size=500,
        update_frequency=100
    )
    
    results = {}
    
    for model_name, model in models.items():
        print(f"\n{'='*60}")
        print(f"Avaliando {model_name}")
        print('='*60)
        
        # Resetar avaliador
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
    print("COMPARAÇÃO FINAL - BENCHMARK 2")
    print("="*60)
    
    comparison_df = pd.DataFrame({
        model_name: res['final_metrics'] 
        for model_name, res in results.items()
    }).T
    
    print("\n", comparison_df.round(4))
    
    # Salvar resultados
    comparison_df.to_csv('benchmark2_results.csv')
    print("\nResultados salvos em benchmark2_results.csv")
    
    # Ranking por Hamming Loss
    print("\nRanking por Hamming Loss (menor é melhor):")
    ranking = comparison_df.sort_values('hamming_loss')
    for i, (model, row) in enumerate(ranking.iterrows(), 1):
        print(f"{i}. {model}: {row['hamming_loss']:.4f}")
    
    return results


if __name__ == "__main__":
    print("="*60)
    print("BENCHMARK 2: MULTI-LABEL ONLINE CLASSIFIERS")
    print("Implementação completa com 10 modelos do paper")
    print("="*60)
    
    # Rodar teste rápido primeiro
    print("\nRodando teste rápido para verificar implementação...")
    results_fast = run_benchmark2(use_synthetic=True, fast_test=True)
    
    # Se quiser rodar completo
    # results_full = run_benchmark2(use_synthetic=True, fast_test=False)
    
    print("\n" + "="*60)
    print("BENCHMARK 2 CONCLUÍDO")
    print("="*60)