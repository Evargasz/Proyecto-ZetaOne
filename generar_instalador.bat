@echo off
chcp 65001 >nul
title Generador de Instalador ZetaOne v1.4.0

echo ╔══════════════════════════════════════════════════════════════╗
echo ║              GENERADOR DE INSTALADOR ZETAONE v1.4.0         ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: Verificar que existe el ejecutable compilado
if not exist "dist\ZetaOne_v1.4.0\ZetaOne_v1.4.0.exe" (
    echo ❌ Error: No se encontró el ejecutable compilado.
    echo    Ejecute primero: pyinstaller ZetaOne.spec --clean
    echo.
    pause
    exit /b 1
)

:: Verificar que existe Inno Setup
set "INNO_PATH="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "INNO_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
) else (
    echo ❌ Error: No se encontró Inno Setup 6.
    echo    Descargue e instale desde: https://jrsoftware.org/isinfo.php
    echo.
    pause
    exit /b 1
)

echo ✓ Ejecutable encontrado: dist\ZetaOne_v1.4.0\ZetaOne_v1.4.0.exe
echo ✓ Inno Setup encontrado: %INNO_PATH%
echo.

:: Crear directorio de salida si no existe
if not exist "instalador_generado" (
    mkdir "instalador_generado"
    echo ✓ Directorio de salida creado: instalador_generado
)

echo Generando instalador con Inno Setup...
echo.

:: Ejecutar Inno Setup
"%INNO_PATH%" "instalador_zetaone.iss"

if errorlevel 1 (
    echo.
    echo ❌ Error al generar el instalador.
    echo    Revise el archivo instalador_zetaone.iss para errores.
    echo.
    pause
    exit /b 1
)

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                INSTALADOR GENERADO EXITOSAMENTE              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: Mostrar información del instalador generado
if exist "instalador_generado\ZetaOne_Setup_v1.4.0.exe" (
    echo ✓ Instalador creado: instalador_generado\ZetaOne_Setup_v1.4.0.exe
    
    :: Obtener tamaño del archivo
    for %%A in ("instalador_generado\ZetaOne_Setup_v1.4.0.exe") do (
        set "size=%%~zA"
        set /a "sizeMB=!size! / 1048576"
    )
    
    echo ✓ Tamaño: %sizeMB% MB aproximadamente
    echo.
    echo CARACTERÍSTICAS DEL INSTALADOR:
    echo • Detecta automáticamente versiones anteriores
    echo • Preserva configuraciones de usuario
    echo • Instala drivers ODBC necesarios
    echo • Compatible con instalaciones nuevas y actualizaciones
    echo • Incluye nuevas funcionalidades de captura y grabación
    echo.
    echo DISTRIBUCIÓN:
    echo 1. Copie ZetaOne_Setup_v1.4.0.exe a los equipos destino
    echo 2. Ejecute como administrador para instalación completa
    echo 3. El instalador detectará automáticamente si es actualización
    echo.
    
    set /p "open_folder=¿Desea abrir la carpeta del instalador? (S/N): "
    if /i "%open_folder%"=="S" (
        explorer "instalador_generado"
    )
    
    set /p "test_install=¿Desea probar el instalador ahora? (S/N): "
    if /i "%test_install%"=="S" (
        echo.
        echo ⚠ ADVERTENCIA: Esto instalará/actualizará ZetaOne en este equipo.
        set /p "confirm=¿Está seguro? (S/N): "
        if /i "!confirm!"=="S" (
            start "" "instalador_generado\ZetaOne_Setup_v1.4.0.exe"
        )
    )
) else (
    echo ❌ No se encontró el instalador generado.
    echo    Revise los mensajes de error anteriores.
)

echo.
echo Proceso completado.
pause