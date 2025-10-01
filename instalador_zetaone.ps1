# Instalador ZetaOne v1.1.0
# PowerShell Script para instalación y actualización

param(
    [string]$InstallPath = "",
    [switch]$Silent = $false,
    [switch]$Update = $false
)

# Configuración
$AppName = "ZetaOne"
$AppVersion = "1.4.0"
$AppDisplayName = "$AppName v$AppVersion"
$DefaultInstallPath = "C:\ZetaOne"

# Funciones auxiliares
function Write-ColorText {
    param([string]$Text, [string]$Color = "White")
    Write-Host $Text -ForegroundColor $Color
}

function Show-Header {
    Clear-Host
    Write-ColorText "╔══════════════════════════════════════════════════════════════╗" "Cyan"
    Write-ColorText "║                    INSTALADOR ZETAONE v1.4.0                ║" "Cyan"
    Write-ColorText "║                                                              ║" "Cyan"
    Write-ColorText "║  • Instalación nueva o actualización automática             ║" "White"
    Write-ColorText "║  • Respaldo automático de versión anterior                  ║" "White"
    Write-ColorText "║  • Creación de accesos directos                             ║" "White"
    Write-ColorText "║                                                              ║" "Cyan"
    Write-ColorText "╚══════════════════════════════════════════════════════════════╝" "Cyan"
    Write-Host ""
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Find-ExistingInstallation {
    $possiblePaths = @(
        "C:\ZetaOne",
        "C:\Program Files\ZetaOne",
        "C:\Program Files (x86)\ZetaOne",
        "$env:LOCALAPPDATA\ZetaOne",
        "$env:APPDATA\ZetaOne"
    )
    
    foreach ($path in $possiblePaths) {
        if (Test-Path "$path\ZetaOne.exe") {
            return $path
        }
    }
    return $null
}

function Create-Backup {
    param([string]$SourcePath)
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupPath = "${SourcePath}_backup_$timestamp"
    
    try {
        Write-ColorText "Creando respaldo en: $backupPath" "Yellow"
        Copy-Item -Path $SourcePath -Destination $backupPath -Recurse -Force
        Write-ColorText "✓ Respaldo creado exitosamente" "Green"
        return $backupPath
    }
    catch {
        Write-ColorText "⚠ Advertencia: No se pudo crear respaldo completo" "Yellow"
        return $null
    }
}

function Install-Files {
    param([string]$TargetPath)
    
    Write-ColorText "Instalando archivos en: $TargetPath" "White"
    
    # Crear directorio si no existe
    if (!(Test-Path $TargetPath)) {
        New-Item -ItemType Directory -Path $TargetPath -Force | Out-Null
    }
    
    # Copiar ejecutable principal
    $exePath = "dist\ZetaOne_v1.4.0\ZetaOne_v1.4.0.exe"
    if (Test-Path $exePath) {
        Write-ColorText "• Copiando ejecutable principal..." "Gray"
        Copy-Item -Path $exePath -Destination "$TargetPath\ZetaOne.exe" -Force
    } else {
        throw "No se encontró el ejecutable principal: $exePath"
    }
    
    # Copiar carpeta _internal
    $internalPath = "dist\ZetaOne_v1.4.0\_internal"
    if (Test-Path $internalPath) {
        Write-ColorText "• Copiando archivos internos..." "Gray"
        $targetInternal = "$TargetPath\_internal"
        if (Test-Path $targetInternal) {
            Remove-Item -Path $targetInternal -Recurse -Force
        }
        Copy-Item -Path $internalPath -Destination $targetInternal -Recurse -Force
    } else {
        throw "No se encontró la carpeta _internal: $internalPath"
    }
    
    # Copiar archivos de configuración
    Write-ColorText "• Copiando archivos de configuración..." "Gray"
    
    $configFolders = @("json", "imagenes_iconos", "ODBC")
    foreach ($folder in $configFolders) {
        if (Test-Path $folder) {
            $targetFolder = "$TargetPath\$folder"
            if (!(Test-Path $targetFolder)) {
                New-Item -ItemType Directory -Path $targetFolder -Force | Out-Null
            }
            Copy-Item -Path "$folder\*" -Destination $targetFolder -Recurse -Force
        }
    }
    
    # Copiar documentación
    if (Test-Path "CHANGELOG_v1.1.0.md") {
        Copy-Item -Path "CHANGELOG_v1.1.0.md" -Destination $TargetPath -Force
    }
}

function Create-Shortcuts {
    param([string]$InstallPath)
    
    Write-ColorText "• Creando accesos directos..." "Gray"
    
    $WshShell = New-Object -comObject WScript.Shell
    
    # Acceso directo en escritorio
    $desktopPath = [Environment]::GetFolderPath("Desktop")
    $shortcut = $WshShell.CreateShortcut("$desktopPath\$AppDisplayName.lnk")
    $shortcut.TargetPath = "$InstallPath\ZetaOne.exe"
    $shortcut.WorkingDirectory = $InstallPath
    $shortcut.Description = "$AppDisplayName - Sistema de Migración de Datos"
    $shortcut.Save()
    
    # Acceso directo en menú inicio
    $startMenuPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\ZetaOne"
    if (!(Test-Path $startMenuPath)) {
        New-Item -ItemType Directory -Path $startMenuPath -Force | Out-Null
    }
    $shortcut = $WshShell.CreateShortcut("$startMenuPath\$AppDisplayName.lnk")
    $shortcut.TargetPath = "$InstallPath\ZetaOne.exe"
    $shortcut.WorkingDirectory = $InstallPath
    $shortcut.Description = "$AppDisplayName - Sistema de Migración de Datos"
    $shortcut.Save()
}

function Create-Uninstaller {
    param([string]$InstallPath)
    
    $uninstallerContent = @"
@echo off
title Desinstalador $AppDisplayName
echo Desinstalando $AppDisplayName...
echo.
set /p "confirm=¿Está seguro que desea desinstalar ZetaOne? (S/N): "
if /i "%confirm%"=="S" (
    echo Eliminando archivos...
    cd /d "%~dp0.."
    timeout /t 2 /nobreak >nul
    rmdir /s /q "$InstallPath" 2>nul
    del "$env:USERPROFILE\Desktop\$AppDisplayName.lnk" 2>nul
    rmdir /s /q "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\ZetaOne" 2>nul
    echo ✓ ZetaOne ha sido desinstalado correctamente.
) else (
    echo Desinstalación cancelada.
)
pause
"@
    
    $uninstallerContent | Out-File -FilePath "$InstallPath\Desinstalar.bat" -Encoding ASCII
}

function Register-Application {
    param([string]$InstallPath)
    
    try {
        $regPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\ZetaOne"
        
        if (!(Test-Path $regPath)) {
            New-Item -Path $regPath -Force | Out-Null
        }
        
        Set-ItemProperty -Path $regPath -Name "DisplayName" -Value $AppDisplayName
        Set-ItemProperty -Path $regPath -Name "DisplayVersion" -Value $AppVersion
        Set-ItemProperty -Path $regPath -Name "Publisher" -Value "BAC Credomatic"
        Set-ItemProperty -Path $regPath -Name "InstallLocation" -Value $InstallPath
        Set-ItemProperty -Path $regPath -Name "UninstallString" -Value "$InstallPath\Desinstalar.bat"
        Set-ItemProperty -Path $regPath -Name "DisplayIcon" -Value "$InstallPath\ZetaOne.exe"
        
        Write-ColorText "✓ Aplicación registrada en el sistema" "Green"
    }
    catch {
        Write-ColorText "⚠ No se pudo registrar en el sistema (requiere permisos de administrador)" "Yellow"
    }
}

# Script principal
try {
    Show-Header
    
    # Verificar permisos de administrador
    if (Test-Administrator) {
        Write-ColorText "✓ Ejecutándose con permisos de administrador" "Green"
    } else {
        Write-ColorText "⚠ ADVERTENCIA: Se recomienda ejecutar como administrador" "Yellow"
        Write-ColorText "  para registrar la aplicación en el sistema." "Yellow"
        Write-Host ""
    }
    
    # Detectar instalación existente
    $existingPath = Find-ExistingInstallation
    $isUpdate = $existingPath -ne $null
    
    if ($isUpdate) {
        Write-ColorText "✓ Instalación existente detectada en: $existingPath" "Green"
        Write-Host ""
        
        if (!$Silent) {
            $updateChoice = Read-Host "¿Desea actualizar la instalación existente? (S/N)"
            if ($updateChoice -notmatch '^[SsYy]') {
                $isUpdate = $false
            }
        }
        
        if ($isUpdate) {
            $InstallPath = $existingPath
            Write-ColorText "╔══════════════════════════════════════════════════════════════╗" "Yellow"
            Write-ColorText "║                      ACTUALIZACIÓN                          ║" "Yellow"
            Write-ColorText "╚══════════════════════════════════════════════════════════════╝" "Yellow"
            Write-Host ""
            
            # Crear respaldo
            $backupPath = Create-Backup -SourcePath $InstallPath
        }
    }
    
    if (!$isUpdate) {
        Write-ColorText "ℹ Realizando instalación nueva" "Cyan"
        Write-ColorText "╔══════════════════════════════════════════════════════════════╗" "Cyan"
        Write-ColorText "║                    INSTALACIÓN NUEVA                         ║" "Cyan"
        Write-ColorText "╚══════════════════════════════════════════════════════════════╝" "Cyan"
        Write-Host ""
        
        if ([string]::IsNullOrEmpty($InstallPath)) {
            if (!$Silent) {
                Write-Host "Seleccione la ubicación de instalación:"
                Write-Host "1. C:\ZetaOne (Recomendado)"
                Write-Host "2. C:\Program Files\ZetaOne"
                Write-Host "3. Ubicación personalizada"
                Write-Host ""
                
                $choice = Read-Host "Seleccione opción (1-3)"
                
                switch ($choice) {
                    "1" { $InstallPath = "C:\ZetaOne" }
                    "2" { $InstallPath = "C:\Program Files\ZetaOne" }
                    "3" { $InstallPath = Read-Host "Ingrese la ruta completa" }
                    default { $InstallPath = $DefaultInstallPath }
                }
            } else {
                $InstallPath = $DefaultInstallPath
            }
        }
    }
    
    # Instalar archivos
    Write-Host ""
    Write-ColorText "Instalando $AppDisplayName..." "White"
    Write-Host ""
    
    Install-Files -TargetPath $InstallPath
    Create-Shortcuts -InstallPath $InstallPath
    Create-Uninstaller -InstallPath $InstallPath
    
    if (Test-Administrator) {
        Register-Application -InstallPath $InstallPath
    }
    
    # Mostrar resultado
    Write-Host ""
    Write-ColorText "╔══════════════════════════════════════════════════════════════╗" "Green"
    Write-ColorText "║                   INSTALACIÓN COMPLETADA                    ║" "Green"
    Write-ColorText "╚══════════════════════════════════════════════════════════════╝" "Green"
    Write-Host ""
    Write-ColorText "✓ $AppDisplayName se ha instalado correctamente en:" "Green"
    Write-ColorText "  $InstallPath" "White"
    Write-Host ""
    Write-ColorText "✓ Accesos directos creados:" "Green"
    Write-ColorText "  • Escritorio: $AppDisplayName" "White"
    Write-ColorText "  • Menú Inicio: Programas > ZetaOne > $AppDisplayName" "White"
    Write-Host ""
    
    if ($isUpdate -and $backupPath) {
        Write-ColorText "✓ Respaldo de versión anterior disponible en:" "Green"
        Write-ColorText "  $backupPath" "White"
        Write-Host ""
    }
    
    if (!$Silent) {
        $runChoice = Read-Host "¿Desea ejecutar ZetaOne ahora? (S/N)"
        if ($runChoice -match '^[SsYy]') {
            Start-Process -FilePath "$InstallPath\ZetaOne.exe"
        }
    }
    
    Write-ColorText "Instalación finalizada exitosamente." "Green"
}
catch {
    Write-Host ""
    Write-ColorText "❌ Error durante la instalación:" "Red"
    Write-ColorText $_.Exception.Message "Red"
    Write-Host ""
    
    if ($isUpdate -and $backupPath) {
        Write-ColorText "Para restaurar la versión anterior:" "Yellow"
        Write-ColorText "Copy-Item -Path '$backupPath\*' -Destination '$InstallPath' -Recurse -Force" "White"
    }
    
    exit 1
}