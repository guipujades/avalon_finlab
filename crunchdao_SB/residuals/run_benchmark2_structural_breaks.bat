@echo off
echo ============================================================
echo BENCHMARK 2: STRUCTURAL BREAKS - DADOS REAIS
echo ============================================================
echo.

call conda activate sb_2025
echo Ambiente ativado: sb_2025
echo.

echo Executando benchmark com dados reais de structural breaks...
echo.

python benchmark2_structural_breaks.py

echo.
echo ============================================================
echo BENCHMARK FINALIZADO
echo ============================================================
echo.
echo Resultados salvos em:
echo - benchmark2_roc_auc_results.csv
echo - benchmark2_vs_tsfresh.png
echo.
pause