@echo off
echo ========================================
echo  INSTALADOR DE DEPENDENCIAS - ZETAONE
echo  Asistente de Captura y Grabacion
echo ========================================
echo.

echo Detectando entorno Python...
python --version
echo.

echo Verificando pip...
pip --version
echo.

echo Instalando dependencias para captura de pantallas...
pip install --upgrade pyautogui keyboard python-docx pywinauto pillow

echo.
echo Instalando dependencias para grabacion de video...
pip install --upgrade opencv-python mss pygetwindow pywin32

echo.
echo Instalando dependencias adicionales del sistema...
pip install --upgrade paramiko

echo.
echo Verificando instalacion...
python -c "import pyautogui, keyboard, docx, pywinauto, PIL; print('Captura: OK')"
python -c "import cv2, mss, pygetwindow, win32process; print('Video: OK')"
python -c "import paramiko; print('SSH: OK')" 2>nul || echo "SSH: Opcional (paramiko no instalado)"

echo.
echo ========================================
echo  INSTALACION COMPLETADA
echo ========================================
echo.
echo Las siguientes funcionalidades ya estan disponibles:
echo - Captura de pantallas con F8
echo - Grabacion de video con F9
echo - Generacion automatica de documentos Word
echo - Editor de objetivos personalizable
echo.
echo IMPORTANTE: Si usas un entorno virtual, activalo antes
echo de ejecutar ZetaOne para que detecte las dependencias.
echo.
pause