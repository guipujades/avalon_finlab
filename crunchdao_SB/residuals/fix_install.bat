@echo off
echo ============================================================
echo CORRIGINDO INSTALACAO DO TSFRESH
echo ============================================================

echo.
echo Atualizando pip e setuptools...
python -m pip install --upgrade pip
pip install --upgrade setuptools wheel

echo.
echo Instalando TSFresh...
pip install tsfresh

echo.
echo Verificando...
python -c "import pkg_resources; print('pkg_resources OK')"
python -c "import tsfresh; print('TSFresh versao:', tsfresh.__version__)"

echo.
echo ============================================================
echo Pronto! Agora execute: python test_tsfresh.py
echo ============================================================
pause