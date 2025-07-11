@echo off
echo ====================================
echo Instalando dependencias para Levy
echo ====================================

echo.
echo Desinstalando scipy corrompido...
python -m pip uninstall scipy -y

echo.
echo Instalando dependencias necessarias...
python -m pip install numpy pandas matplotlib scikit-learn pyarrow tqdm

echo.
echo Reinstalando scipy...
python -m pip install scipy

echo.
echo Instalando seaborn...
python -m pip install seaborn

echo.
echo Instalando yfinance (opcional)...
python -m pip install yfinance

echo.
echo ====================================
echo Instalacao concluida!
echo ====================================
pause