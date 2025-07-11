# CrunchDAO Structural Breaks Detection

Projeto para o desafio ADIA Lab Structural Break Challenge no CrunchDAO.

## Estrutura do Projeto

### Arquivos Principais

- `benchmark2_structural_breaks.py` - Benchmark comparando 10 modelos online com TSFresh em dados reais
- `test_tsfresh_comprehensive.py` - Análise completa usando TSFresh (783 features)
- `analise_final_benchmark.py` - Análise consolidada e relatório final

### Diretórios

- `src/` - Código fonte principal
  - `features/` - Extratores de features (cumulants, robust_stats, distribution, noise, temporal)
  - `classification/` - Classificadores (gravitational, constellation)
- `database/` - Dados de treino (X_train.parquet, y_train.parquet)
- `documents/` - Papers e documentação processada
- `residuals/` - Scripts antigos e testes não utilizados
- `utils/` - Scripts auxiliares que podem ser úteis

### Resultados

- `tsfresh_top100_features.parquet` - Top 100 features do TSFresh
- `relatorio_final_benchmark.txt` - Relatório final com ranking dos modelos
- Visualizações: `*.png`

## Melhores Resultados (ROC AUC)

1. **TSFresh + RandomForest**: 0.607 (baseline batch, 783 features)
2. **ML-kNN Online**: 0.550 (streaming, 127.9 samples/s)
3. **ECC**: 0.536 (streaming, 140.6 samples/s)

## Execução

### Análise TSFresh Completa
```bash
python test_tsfresh_comprehensive.py
```

### Benchmark Modelos Online
```bash
python benchmark2_structural_breaks.py
```

### Análise Final
```bash
python analise_final_benchmark.py
```

## Próximos Passos

1. Implementar ensemble TSFresh + ML-kNN
2. Otimizar hiperparâmetros do ML-kNN
3. Testar em dados de validação do desafio
4. Submeter predições finais