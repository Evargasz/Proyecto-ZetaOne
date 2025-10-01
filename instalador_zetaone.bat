@echo off
chcp 65001 >nul
title Instalador ZetaOne v1.4.0

echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    INSTALADOR ZETAONE v1.4.0                ║
echo ║                                                              ║
echo ║  Este instalador puede:                                      ║
echo ║  • Instalar ZetaOne por primera vez                         ║
echo ║  • Actualizar una instalación existente                     ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: Verificar si se ejecuta como administrador
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✓ Ejecutándose con permisos de administrador
) else (
    echo ⚠ ADVERTENCIA: Se recomienda ejecutar como administrador
    echo   para evitar problemas de permisos.
    echo.
    pause
)

:: Detectar instalación existente
set "INSTALL_PATH="
set "UPDATE_MODE=0"

:: Buscar en ubicaciones comunes
if exist "C:\ZetaOne\ZetaOne.exe" (
    set "INSTALL_PATH=C:\ZetaOne"
    set "UPDATE_MODE=1"
)
if exist "C:\Program Files\ZetaOne\ZetaOne.exe" (
    set "INSTALL_PATH=C:\Program Files\ZetaOne"
    set "UPDATE_MODE=1"
)
if exist "C:\Program Files (x86)\ZetaOne\ZetaOne.exe" (
    set "INSTALL_PATH=C:\Program Files (x86)\ZetaOne"
    set "UPDATE_MODE=1"
)

if %UPDATE_MODE%==1 (
    echo ✓ Instalación existente detectada en: %INSTALL_PATH%
    echo.
    echo ¿Desea actualizar la instalación existente? (S/N)
    set /p "choice=Respuesta: "
    if /i "%choice%"=="S" (
        goto :update_installation
    ) else (
        goto :new_installation
    )
) else (
    echo ℹ No se detectó instalación previa
    goto :new_installation
)

:new_installation
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    INSTALACIÓN NUEVA                         ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo Seleccione la ubicación de instalación:
echo 1. C:\ZetaOne (Recomendado)
echo 2. C:\Program Files\ZetaOne
echo 3. Ubicación personalizada
echo.
set /p "install_choice=Seleccione opción (1-3): "

if "%install_choice%"=="1" (
    set "INSTALL_PATH=C:\ZetaOne"
) else if "%install_choice%"=="2" (
    set "INSTALL_PATH=C:\Program Files\ZetaOne"
) else if "%install_choice%"=="3" (
    set /p "INSTALL_PATH=Ingrese la ruta completa: "
) else (
    echo Opción inválida. Usando ubicación por defecto.
    set "INSTALL_PATH=C:\ZetaOne"
)

echo.
echo Creando directorio de instalación...
if not exist "%INSTALL_PATH%" (
    mkdir "%INSTALL_PATH%" 2>nul
    if errorlevel 1 (
        echo ❌ Error: No se pudo crear el directorio %INSTALL_PATH%
        echo    Verifique los permisos o ejecute como administrador.
        pause
        exit /b 1
    )
)

goto :install_files

:update_installation
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                      ACTUALIZACIÓN                          ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo Creando respaldo de la versión actual...
set "BACKUP_PATH=%INSTALL_PATH%_backup_%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%"
set "BACKUP_PATH=%BACKUP_PATH: =0%"

if exist "%INSTALL_PATH%" (
    xcopy "%INSTALL_PATH%" "%BACKUP_PATH%" /E /I /H /Y >nul 2>&1
    if errorlevel 1 (
        echo ⚠ Advertencia: No se pudo crear respaldo completo
    ) else (
        echo ✓ Respaldo creado en: %BACKUP_PATH%
    )
)

:install_files
echo.
echo Instalando ZetaOne v1.4.0...
echo.

:: Copiar archivos del ejecutable
echo • Copiando ejecutable principal...
if exist "dist\ZetaOne_v1.4.0\ZetaOne_v1.4.0.exe" (
    copy "dist\ZetaOne_v1.4.0\ZetaOne_v1.4.0.exe" "%INSTALL_PATH%\ZetaOne.exe" >nul
    if errorlevel 1 (
        echo ❌ Error copiando ejecutable principal
        goto :error_exit
    )
) else (
    echo ❌ Error: No se encontró el ejecutable ZetaOne_v1.1.0.exe
    goto :error_exit
)

:: Copiar carpeta _internal
echo • Copiando archivos internos...
if exist "dist\ZetaOne_v1.4.0\_internal" (
    if exist "%INSTALL_PATH%\_internal" (
        rmdir /s /q "%INSTALL_PATH%\_internal" 2>nul
    )
    xcopy "dist\ZetaOne_v1.4.0\_internal" "%INSTALL_PATH%\_internal" /E /I /H /Y >nul
    if errorlevel 1 (
        echo ❌ Error copiando archivos internos
        goto :error_exit
    )
) else (
    echo ❌ Error: No se encontró la carpeta _internal
    goto :error_exit
)

:: Copiar archivos de configuración y datos
echo • Copiando archivos de configuración...
if exist "json" (
    if not exist "%INSTALL_PATH%\json" mkdir "%INSTALL_PATH%\json"
    xcopy "json\*" "%INSTALL_PATH%\json\" /Y >nul 2>&1
)

if exist "imagenes_iconos" (
    if not exist "%INSTALL_PATH%\imagenes_iconos" mkdir "%INSTALL_PATH%\imagenes_iconos"
    xcopy "imagenes_iconos\*" "%INSTALL_PATH%\imagenes_iconos\" /Y >nul 2>&1
)

if exist "ODBC" (
    if not exist "%INSTALL_PATH%\ODBC" mkdir "%INSTALL_PATH%\ODBC"
    xcopy "ODBC\*" "%INSTALL_PATH%\ODBC\" /E /I /Y >nul 2>&1
)

:: Copiar documentación
echo • Copiando documentación...
if exist "CHANGELOG_v1.1.0.md" (
    copy "CHANGELOG_v1.1.0.md" "%INSTALL_PATH%\" >nul 2>&1
)

:: Crear acceso directo en el escritorio
echo • Creando acceso directo en el escritorio...
powershell -Command "& {$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\ZetaOne v1.1.0.lnk'); $Shortcut.TargetPath = '%INSTALL_PATH%\ZetaOne.exe'; $Shortcut.WorkingDirectory = '%INSTALL_PATH%'; $Shortcut.Description = 'ZetaOne v1.1.0 - Sistema de Migración de Datos'; $Shortcut.Save()}" 2>nul

:: Crear entrada en el menú inicio
echo • Creando entrada en menú inicio...
if not exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\ZetaOne" (
    mkdir "%APPDATA%\Microsoft\Windows\Start Menu\Programs\ZetaOne" 2>nul
)
powershell -Command "& {$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%APPDATA%\Microsoft\Windows\Start Menu\Programs\ZetaOne\ZetaOne v1.1.0.lnk'); $Shortcut.TargetPath = '%INSTALL_PATH%\ZetaOne.exe'; $Shortcut.WorkingDirectory = '%INSTALL_PATH%'; $Shortcut.Description = 'ZetaOne v1.1.0 - Sistema de Migración de Datos'; $Shortcut.Save()}" 2>nul

:: Crear desinstalador
echo • Creando desinstalador...
(
echo @echo off
echo title Desinstalador ZetaOne v1.1.0
echo echo Desinstalando ZetaOne v1.1.0...
echo echo.
echo set /p "confirm=¿Está seguro que desea desinstalar ZetaOne? (S/N): "
echo if /i "%%confirm%%"=="S" (
echo     echo Eliminando archivos...
echo     cd /d "%%~dp0.."
echo     timeout /t 2 /nobreak ^>nul
echo     rmdir /s /q "%INSTALL_PATH%" 2^>nul
echo     del "%USERPROFILE%\Desktop\ZetaOne v1.1.0.lnk" 2^>nul
echo     rmdir /s /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\ZetaOne" 2^>nul
echo     echo ✓ ZetaOne ha sido desinstalado correctamente.
echo ^) else (
echo     echo Desinstalación cancelada.
echo ^)
echo pause
) > "%INSTALL_PATH%\Desinstalar.bat"

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                   INSTALACIÓN COMPLETADA                    ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo ✓ ZetaOne v1.1.0 se ha instalado correctamente en:
echo   %INSTALL_PATH%
echo.
echo ✓ Accesos directos creados:
echo   • Escritorio: ZetaOne v1.1.0
echo   • Menú Inicio: Programas ^> ZetaOne ^> ZetaOne v1.1.0
echo.
if %UPDATE_MODE%==1 (
    echo ✓ Respaldo de versión anterior disponible en:
    echo   %BACKUP_PATH%
    echo.
)
echo ¿Desea ejecutar ZetaOne ahora? (S/N)
set /p "run_choice=Respuesta: "
if /i "%run_choice%"=="S" (
    start "" "%INSTALL_PATH%\ZetaOne.exe"
)

echo.
echo Instalación finalizada. Presione cualquier tecla para salir.
pause >nul
exit /b 0

:error_exit
echo.
echo ❌ La instalación no se pudo completar debido a errores.
echo    Verifique los permisos y que todos los archivos estén presentes.
echo.
if %UPDATE_MODE%==1 (
    echo Para restaurar la versión anterior, ejecute:
    echo xcopy "%BACKUP_PATH%" "%INSTALL_PATH%" /E /I /H /Y
    echo.
)
pause
exit /b 1