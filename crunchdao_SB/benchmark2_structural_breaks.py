"""
Benchmark 2 Adaptado para Structural Breaks
Compara modelos multi-label adaptados para classificação binária
Métricas compatíveis com TSFresh (ROC AUC)
"""

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score, precision_recall_curve
from sklearn.model_selection import cross_val_score, StratifiedKFold
import time
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Importar modelos do benchmark2
from benchmark2_corrected import (
    OnlineOSMLELMFixed,
    OnlineBinaryRelevance,
    OnlineClassifierChain,
    OnlineCLR,
    OnlineQWML,
    OnlineHOMER,
    OnlineMLkNN,
    OnlinePCT,
    OnlineECC,
    OnlineRAkELFixed
)


class BinaryAdapter(BaseEstimator, ClassifierMixin):
    """Adapta modelos multi-label para classificação binária."""
    
    def __init__(self, base_model, aggregation='mean'):
        self.base_model = base_model
        self.aggregation = aggregation
        
    def fit(self, X, y):
        # Converter para multi-label (1 label)
        y_multi = y.reshape(-1, 1)
        self.base_model.fit(X, y_multi)
        return self
        
    def partial_fit(self, X, y, classes=None):
        y_multi = y.reshape(-1, 1)
        self.base_model.partial_fit(X, y_multi)
        return self
        
    def predict(self, X):
        y_multi = self.base_model.predict(X)
        return y_multi.ravel()
        
    def predict_proba(self, X):
        # Para modelos que não têm predict_proba
        if hasattr(self.base_model, 'predict_proba'):
            proba = self.base_model.predict_proba(X)
            if len(proba.shape) > 1:
                proba = proba[:, 0]
        else:
            # Usar predict e converter para probabilidade
            pred = self.predict(X)
            proba = np.column_stack([1 - pred, pred])
        
        return proba


class StreamingEvaluator:
    """Avaliador para streaming com ROC AUC."""
    
    def __init__(self, window_size=1000):
        self.window_size = window_size
        self.reset()
        
    def reset(self):
        self.y_true_window = []
        self.y_pred_window = []
        self.y_proba_window = []
        self.metrics_history = {
            'roc_auc': [],
            'accuracy': [],
            'f1': [],
            'time_points': []
        }
        
    def update(self, y_true, y_pred, y_proba=None):
        """Atualiza janela de avaliação."""
        self.y_true_window.extend(y_true)
        self.y_pred_window.extend(y_pred)
        
        if y_proba is not None:
            self.y_proba_window.extend(y_proba)
        else:
            self.y_proba_window.extend(y_pred)
        
        # Manter janela limitada
        if len(self.y_true_window) > self.window_size:
            self.y_true_window = self.y_true_window[-self.window_size:]
            self.y_pred_window = self.y_pred_window[-self.window_size:]
            self.y_proba_window = self.y_proba_window[-self.window_size:]
    
    def compute_metrics(self, sample_idx):
        """Calcula métricas na janela atual."""
        if len(self.y_true_window) < 10:
            return None
            
        y_true = np.array(self.y_true_window)
        y_pred = np.array(self.y_pred_window)
        y_proba = np.array(self.y_proba_window)
        
        # Verificar se há variação nas classes
        if len(np.unique(y_true)) < 2:
            return None
            
        metrics = {
            'roc_auc': roc_auc_score(y_true, y_proba),
            'accuracy': accuracy_score(y_true, y_pred),
            'f1': f1_score(y_true, y_pred),
            'sample': sample_idx
        }
        
        # Armazenar histórico
        for key in ['roc_auc', 'accuracy', 'f1']:
            self.metrics_history[key].append(metrics[key])
        self.metrics_history['time_points'].append(sample_idx)
        
        return metrics


def load_structural_breaks_data(n_samples=2000):
    """Carrega dados de structural breaks e features TSFresh."""
    
    print("Carregando dados de structural breaks...")
    
    # Tentar carregar features TSFresh primeiro
    try:
        # Usar top 100 features do TSFresh
        tsfresh_data = pd.read_parquet('tsfresh_top100_features.parquet')
        X = tsfresh_data.drop('label', axis=1).values
        y = tsfresh_data['label'].values
        
        print(f"Usando top 100 features TSFresh: {X.shape}")
        
    except:
        print("Features TSFresh não encontradas. Carregando dados brutos...")
        
        # Carregar dados originais
        X_train = pd.read_parquet('database/X_train.parquet').reset_index()
        y_train = pd.read_parquet('database/y_train.parquet')
        
        # Criar features básicas
        feature_list = []
        labels = []
        
        unique_ids = X_train['id'].unique()[:n_samples]
        
        for series_id in unique_ids:
            series_data = X_train[X_train['id'] == series_id]
            
            # Features básicas por período
            features = []
            for period in [0, 1]:
                period_data = series_data[series_data['period'] == period]['value'].values
                if len(period_data) > 0:
                    features.extend([
                        np.mean(period_data),
                        np.std(period_data),
                        np.max(period_data),
                        np.min(period_data),
                        np.median(period_data)
                    ])
                else:
                    features.extend([0, 0, 0, 0, 0])
            
            # Adicionar diferenças
            for i in range(5):
                features.append(features[i+5] - features[i])  # after - before
            
            feature_list.append(features)
            labels.append(y_train.loc[series_id, 'structural_breakpoint'])
        
        X = np.array(feature_list)
        y = np.array(labels)
        
        print(f"Features básicas criadas: {X.shape}")
    
    return X, y


def evaluate_online_models(X, y, models_dict, initial_train_size=100):
    """Avalia modelos em modo streaming com ROC AUC."""
    
    print("\n" + "="*60)
    print("AVALIAÇÃO ONLINE COM ROC AUC")
    print("="*60)
    
    # Normalizar dados
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    results = {}
    
    for model_name, base_model in models_dict.items():
        print(f"\n{model_name}:")
        
        # Adaptar para binário
        model = BinaryAdapter(base_model)
        
        # Avaliador
        evaluator = StreamingEvaluator(window_size=500)
        
        # Treino inicial
        model.fit(X_scaled[:initial_train_size], y[:initial_train_size])
        
        # Streaming evaluation
        start_time = time.time()
        
        for i in range(initial_train_size, len(X)):
            # Predict
            X_i = X_scaled[i:i+1]
            y_i = y[i:i+1]
            
            y_pred = model.predict(X_i)
            
            # Tentar obter probabilidade
            try:
                if hasattr(model.base_model, 'predict_proba'):
                    y_proba = model.base_model.predict_proba(X_i)
                    if len(y_proba.shape) > 1:
                        y_proba = y_proba[:, -1]
                else:
                    y_proba = y_pred
            except:
                y_proba = y_pred
            
            # Update evaluator
            evaluator.update(y_i, y_pred, y_proba)
            
            # Train (after predict)
            model.partial_fit(X_i, y_i)
            
            # Compute metrics periodicamente
            if i % 100 == 0 or i == len(X) - 1:
                metrics = evaluator.compute_metrics(i)
                if metrics and i % 500 == 0:
                    print(f"  Sample {i}: ROC AUC = {metrics['roc_auc']:.3f}")
        
        elapsed = time.time() - start_time
        throughput = (len(X) - initial_train_size) / elapsed
        
        # Resultados finais
        final_metrics = evaluator.compute_metrics(len(X))
        
        results[model_name] = {
            'roc_auc': final_metrics['roc_auc'] if final_metrics else 0,
            'accuracy': final_metrics['accuracy'] if final_metrics else 0,
            'f1': final_metrics['f1'] if final_metrics else 0,
            'throughput': throughput,
            'history': evaluator.metrics_history
        }
        
        print(f"  ROC AUC Final: {results[model_name]['roc_auc']:.3f}")
        print(f"  Throughput: {throughput:.1f} samples/s")
    
    return results


def evaluate_batch_models(X, y, models_dict):
    """Avalia modelos em modo batch com cross-validation."""
    
    print("\n" + "="*60)
    print("AVALIAÇÃO BATCH (CROSS-VALIDATION)")
    print("="*60)
    
    # Normalizar
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    results = {}
    
    for model_name, base_model in models_dict.items():
        print(f"\n{model_name}:")
        
        # Adaptar para binário
        model = BinaryAdapter(base_model)
        
        # Cross-validation
        scores = cross_val_score(model, X_scaled, y, cv=cv, scoring='roc_auc', n_jobs=-1)
        
        results[model_name] = {
            'roc_auc_mean': np.mean(scores),
            'roc_auc_std': np.std(scores),
            'scores': scores
        }
        
        print(f"  ROC AUC: {results[model_name]['roc_auc_mean']:.3f} "
              f"(+/- {results[model_name]['roc_auc_std']:.3f})")
    
    return results


def compare_with_tsfresh(online_results, batch_results):
    """Compara resultados com TSFresh."""
    
    print("\n" + "="*60)
    print("COMPARAÇÃO COM TSFRESH")
    print("="*60)
    
    # Resultados TSFresh (do experimento anterior)
    tsfresh_roc_auc = 0.607
    tsfresh_std = 0.047
    
    print(f"\nTSFresh (RandomForest):")
    print(f"  ROC AUC: {tsfresh_roc_auc:.3f} (+/- {tsfresh_std:.3f})")
    
    print("\nModelos Online (Streaming):")
    online_df = pd.DataFrame({
        model: {
            'ROC_AUC': res['roc_auc'],
            'Throughput': res['throughput']
        }
        for model, res in online_results.items()
    }).T.sort_values('ROC_AUC', ascending=False)
    
    print(online_df.round(3))
    
    print("\nModelos Batch (Cross-Validation):")
    batch_df = pd.DataFrame({
        model: {
            'ROC_AUC': res['roc_auc_mean'],
            'Std': res['roc_auc_std']
        }
        for model, res in batch_results.items()
    }).T.sort_values('ROC_AUC', ascending=False)
    
    print(batch_df.round(3))
    
    # Visualização
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # 1. Comparação ROC AUC - Online
    ax = axes[0, 0]
    models = list(online_results.keys())
    roc_aucs_online = [online_results[m]['roc_auc'] for m in models]
    
    bars = ax.bar(range(len(models)), roc_aucs_online, alpha=0.7)
    ax.axhline(tsfresh_roc_auc, color='red', linestyle='--', 
               label=f'TSFresh ({tsfresh_roc_auc:.3f})')
    ax.axhline(0.5, color='gray', linestyle=':', alpha=0.5, label='Baseline')
    
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels([m.split('.')[-1] for m in models], rotation=45, ha='right')
    ax.set_ylabel('ROC AUC')
    ax.set_title('Comparação ROC AUC - Online')
    ax.legend()
    ax.set_ylim(0.4, 0.8)
    
    # 2. Streaming Performance Evolution
    ax = axes[0, 1]
    for model_name, res in online_results.items():
        if 'history' in res and res['history']['roc_auc']:
            ax.plot(res['history']['time_points'], 
                   res['history']['roc_auc'], 
                   label=model_name.split('.')[-1], alpha=0.7)
    
    ax.axhline(tsfresh_roc_auc, color='red', linestyle='--', alpha=0.5)
    ax.axhline(0.5, color='gray', linestyle=':', alpha=0.5)
    ax.set_xlabel('Samples')
    ax.set_ylabel('ROC AUC')
    ax.set_title('Evolução ROC AUC - Streaming')
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, alpha=0.3)
    
    # 3. Trade-off Performance vs Speed
    ax = axes[1, 0]
    for model_name, res in online_results.items():
        ax.scatter(res['throughput'], res['roc_auc'], 
                  s=100, alpha=0.7, label=model_name.split('.')[-1])
    
    ax.axhline(tsfresh_roc_auc, color='red', linestyle='--', alpha=0.5)
    ax.axhline(0.5, color='gray', linestyle=':', alpha=0.5)
    ax.set_xlabel('Throughput (samples/s)')
    ax.set_ylabel('ROC AUC')
    ax.set_title('Trade-off: Performance vs Velocidade')
    ax.legend()
    ax.set_xscale('log')
    ax.grid(True, alpha=0.3)
    
    # 4. Comparação direta
    ax = axes[1, 1]
    model_names = [m.split('.')[-1] for m in online_results.keys()]
    online_aucs = [online_results[m]['roc_auc'] for m in online_results.keys()]
    
    # Adicionar TSFresh
    model_names.append('TSFresh')
    online_aucs.append(tsfresh_roc_auc)
    
    # Ordenar por performance
    sorted_idx = np.argsort(online_aucs)[::-1]
    model_names_sorted = [model_names[i] for i in sorted_idx]
    online_aucs_sorted = [online_aucs[i] for i in sorted_idx]
    
    bars = ax.barh(range(len(model_names_sorted)), online_aucs_sorted)
    # Colorir TSFresh diferente
    for i, name in enumerate(model_names_sorted):
        if name == 'TSFresh':
            bars[i].set_color('red')
            bars[i].set_alpha(0.8)
    
    ax.axvline(0.5, color='gray', linestyle=':', alpha=0.5)
    ax.set_yticks(range(len(model_names_sorted)))
    ax.set_yticklabels(model_names_sorted)
    ax.set_xlabel('ROC AUC')
    ax.set_title('Ranking Final - ROC AUC')
    ax.set_xlim(0.4, 0.7)
    
    plt.tight_layout()
    plt.savefig('benchmark2_vs_tsfresh.png', dpi=150, bbox_inches='tight')
    print("\nVisualização salva: benchmark2_vs_tsfresh.png")
    
    # Ranking final
    print("\n" + "="*60)
    print("RANKING FINAL POR ROC AUC (ONLINE)")
    print("="*60)
    
    all_results = [('TSFresh-RF', tsfresh_roc_auc)]
    all_results.extend([(m, r['roc_auc']) for m, r in online_results.items()])
    all_results.sort(key=lambda x: x[1], reverse=True)
    
    for i, (model, auc) in enumerate(all_results, 1):
        print(f"{i}. {model}: {auc:.3f}")


def main():
    """Executa benchmark completo com ROC AUC."""
    
    print("="*60)
    print("BENCHMARK 2 - STRUCTURAL BREAKS")
    print("Avaliação com ROC AUC para comparação com TSFresh")
    print("="*60)
    
    # Carregar dados
    X, y = load_structural_breaks_data(n_samples=2000)
    
    print(f"\nDataset: {X.shape[0]} amostras, {X.shape[1]} features")
    print(f"Taxa de quebra: {y.mean():.1%}")
    
    # Definir modelos
    models = {
        '01.OSML-ELM': OnlineOSMLELMFixed(n_hidden=50, random_state=42),
        '02.BR': OnlineBinaryRelevance(random_state=42),
        '03.CC': OnlineClassifierChain(random_state=42),
        '04.CLR': OnlineCLR(random_state=42),
        '05.QWML': OnlineQWML(q=2.0, random_state=42),
        '06.HOMER': OnlineHOMER(k=3, random_state=42),
        '07.ML-kNN': OnlineMLkNN(k=10, window_size=500, random_state=42),
        '08.PCT': OnlinePCT(max_depth=5, random_state=42),
        '09.ECC': OnlineECC(n_chains=5, random_state=42),
        '10.RAkEL': OnlineRAkELFixed(k=3, n_models=5, random_state=42)
    }
    
    # Avaliar online
    online_results = evaluate_online_models(X, y, models, initial_train_size=200)
    
    # Skip batch evaluation por causa de problemas com adaptação
    batch_results = {}
    for model_name in models.keys():
        batch_results[model_name] = {
            'roc_auc_mean': np.nan,
            'roc_auc_std': np.nan,
            'scores': []
        }
    
    # Comparar com TSFresh
    compare_with_tsfresh(online_results, batch_results)
    
    # Salvar resultados
    results_df = pd.DataFrame({
        'Model': list(batch_results.keys()),
        'ROC_AUC_Online': [online_results[m]['roc_auc'] for m in batch_results.keys()],
        'ROC_AUC_Batch': [batch_results[m]['roc_auc_mean'] for m in batch_results.keys()],
        'ROC_AUC_Std': [batch_results[m]['roc_auc_std'] for m in batch_results.keys()],
        'Throughput': [online_results[m]['throughput'] for m in batch_results.keys()]
    })
    
    results_df = results_df.sort_values('ROC_AUC_Batch', ascending=False)
    results_df.to_csv('benchmark2_roc_auc_results.csv', index=False)
    print("\nResultados salvos: benchmark2_roc_auc_results.csv")
    
    print("\n" + "="*60)
    print("BENCHMARK CONCLUÍDO")
    print("="*60)


if __name__ == "__main__":
    main()