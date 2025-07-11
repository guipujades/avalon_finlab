@echo off
echo ============================================================
echo COMPETICAO JUSTA: TSFresh vs 10 Modelos Online
echo Todos processando series temporais brutas
echo ============================================================
echo.

call conda activate sb_2025
echo.

echo Executando benchmark com series brutas...
python benchmark2_raw_timeseries.py

echo.
echo ============================================================
echo COMPARACAO FINALIZADA
echo ============================================================
echo.
echo Verifique:
echo - benchmark_raw_timeseries_comparison.png
echo - Resultados no terminal
echo.
pause