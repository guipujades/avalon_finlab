@echo off
echo ============================================================
echo INSTALANDO TSFRESH E DEPENDENCIAS
echo ============================================================

echo.
echo Instalando TSFresh...
pip install tsfresh

echo.
echo Verificando instalacao...
python -c "import tsfresh; print('TSFresh versao:', tsfresh.__version__)"

echo.
echo ============================================================
echo INSTALACAO CONCLUIDA
echo ============================================================
echo.
echo Agora execute: python test_tsfresh.py
echo.
pause