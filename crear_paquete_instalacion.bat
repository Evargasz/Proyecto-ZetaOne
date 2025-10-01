@echo off
chcp 65001 >nul
title Creador de Paquete de Instalación ZetaOne v1.4.0

echo ╔══════════════════════════════════════════════════════════════╗
echo ║              CREADOR DE PAQUETE DE INSTALACIÓN               ║
echo ║                     ZetaOne v1.4.0                          ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: Verificar que existe el ejecutable
if not exist "dist\ZetaOne_v1.4.0\ZetaOne_v1.4.0.exe" (
    echo ❌ Error: No se encontró el ejecutable compilado.
    echo    Ejecute primero: pyinstaller ZetaOne.spec --clean
    pause
    exit /b 1
)

:: Crear directorio del paquete
set "PACKAGE_DIR=ZetaOne_v1.4.0_Instalador"
if exist "%PACKAGE_DIR%" (
    echo Eliminando paquete anterior...
    rmdir /s /q "%PACKAGE_DIR%"
)

echo Creando estructura del paquete...
mkdir "%PACKAGE_DIR%"
mkdir "%PACKAGE_DIR%\dist"
mkdir "%PACKAGE_DIR%\dist\ZetaOne_v1.4.0"

:: Copiar ejecutable y archivos internos
echo • Copiando ejecutable y dependencias...
xcopy "dist\ZetaOne_v1.4.0" "%PACKAGE_DIR%\dist\ZetaOne_v1.4.0" /E /I /H /Y >nul

:: Copiar archivos de configuración
echo • Copiando archivos de configuración...
if exist "json" (
    xcopy "json" "%PACKAGE_DIR%\json" /E /I /Y >nul
)
if exist "imagenes_iconos" (
    xcopy "imagenes_iconos" "%PACKAGE_DIR%\imagenes_iconos" /E /I /Y >nul
)
if exist "ODBC" (
    xcopy "ODBC" "%PACKAGE_DIR%\ODBC" /E /I /Y >nul
)

:: Copiar instaladores
echo • Copiando instaladores...
copy "instalador_zetaone.bat" "%PACKAGE_DIR%\" >nul
copy "instalador_zetaone.ps1" "%PACKAGE_DIR%\" >nul

:: Copiar documentación
echo • Copiando documentación...
if exist "CHANGELOG_v1.1.0.md" (
    copy "CHANGELOG_v1.1.0.md" "%PACKAGE_DIR%\" >nul
)

:: Crear archivo README para el paquete
echo • Creando documentación del instalador...
(
echo # ZetaOne v1.1.0 - Paquete de Instalación
echo.
echo ## Contenido del Paquete
echo.
echo - `instalador_zetaone.bat` - Instalador principal ^(Windows Batch^)
echo - `instalador_zetaone.ps1` - Instalador avanzado ^(PowerShell^)
echo - `dist/ZetaOne_v1.1.0/` - Ejecutable y dependencias
echo - `json/` - Archivos de configuración
echo - `imagenes_iconos/` - Iconos de la aplicación
echo - `ODBC/` - Scripts y configuraciones de base de datos
echo - `CHANGELOG_v1.1.0.md` - Lista de cambios de esta versión
echo.
echo ## Instrucciones de Instalación
echo.
echo ### Opción 1: Instalador Batch ^(Recomendado^)
echo 1. Haga clic derecho en `instalador_zetaone.bat`
echo 2. Seleccione "Ejecutar como administrador"
echo 3. Siga las instrucciones en pantalla
echo.
echo ### Opción 2: Instalador PowerShell ^(Avanzado^)
echo 1. Abra PowerShell como administrador
echo 2. Ejecute: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
echo 3. Ejecute: `.\instalador_zetaone.ps1`
echo.
echo ### Instalación Silenciosa
echo ```
echo .\instalador_zetaone.ps1 -InstallPath "C:\ZetaOne" -Silent
echo ```
echo.
echo ## Características del Instalador
echo.
echo - ✅ **Detección automática** de instalaciones previas
echo - ✅ **Actualización inteligente** con respaldo automático
echo - ✅ **Instalación nueva** con selección de ubicación
echo - ✅ **Creación de accesos directos** en escritorio y menú inicio
echo - ✅ **Registro en el sistema** para desinstalación desde Panel de Control
echo - ✅ **Desinstalador incluido**
echo.
echo ## Requisitos del Sistema
echo.
echo - Windows 7 SP1 o superior
echo - .NET Framework 4.5 o superior ^(generalmente ya instalado^)
echo - 50 MB de espacio libre en disco
echo - Permisos de administrador ^(recomendado^)
echo.
echo ## Soporte
echo.
echo Para soporte técnico, contacte al equipo de desarrollo.
echo.
echo ---
echo **Versión:** 1.1.0  
echo **Fecha:** %date%  
echo **Compilado con:** PyInstaller 6.14.2, Python 3.12.3
) > "%PACKAGE_DIR%\README.md"

:: Crear script de instalación rápida
echo • Creando instalación rápida...
(
echo @echo off
echo title Instalación Rápida ZetaOne v1.1.0
echo echo Iniciando instalación rápida de ZetaOne v1.1.0...
echo echo.
echo call instalador_zetaone.bat
) > "%PACKAGE_DIR%\INSTALAR_RAPIDO.bat"

:: Crear información del paquete
echo • Creando información del paquete...
(
echo Paquete de Instalación ZetaOne v1.1.0
echo =====================================
echo.
echo Fecha de creación: %date% %time%
echo Tamaño del ejecutable: 
dir "dist\ZetaOne_v1.1.0\ZetaOne_v1.1.0.exe" | find "ZetaOne_v1.1.0.exe"
echo.
echo Archivos incluidos:
echo - Ejecutable principal y dependencias
echo - Archivos de configuración JSON
echo - Iconos e imágenes
echo - Scripts de base de datos ODBC
echo - Instaladores ^(Batch y PowerShell^)
echo - Documentación y changelog
echo.
echo Para instalar, ejecute instalador_zetaone.bat como administrador.
) > "%PACKAGE_DIR%\INFO_PAQUETE.txt"

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                  PAQUETE CREADO EXITOSAMENTE                 ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo ✓ Paquete de instalación creado en: %PACKAGE_DIR%
echo.
echo Contenido del paquete:
dir /b "%PACKAGE_DIR%"
echo.
echo Para distribuir:
echo 1. Comprima la carpeta "%PACKAGE_DIR%" en un archivo ZIP
echo 2. Distribuya el archivo ZIP a los usuarios
echo 3. Los usuarios deben extraer y ejecutar INSTALAR_RAPIDO.bat
echo.
echo ¿Desea abrir la carpeta del paquete? (S/N)
set /p "open_choice=Respuesta: "
if /i "%open_choice%"=="S" (
    explorer "%PACKAGE_DIR%"
)

echo.
echo Paquete listo para distribución.
pause