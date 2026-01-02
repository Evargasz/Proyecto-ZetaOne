# Script de Conversión de Documentación a PDF y Word
# Requiere: Pandoc instalado

$documentos = @(
    "Manual_Usuario.md",
    "Manual_Tecnico.md",
    "Instalacion.md",
    "Arquitectura.md",
    "ESPECIFICACIONES_FUNCIONALES.md"
)

$carpetaDoc = "documentacion"
$carpetaSalida = "documentacion\output_docs"

# Crear carpeta de salida
if (!(Test-Path $carpetaSalida)) {
    New-Item -ItemType Directory -Path $carpetaSalida | Out-Null
    Write-Host "✓ Carpeta de salida creada: $carpetaSalida" -ForegroundColor Green
}

Write-Host "`n════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "    CONVERSIÓN DE DOCUMENTACIÓN ZETAONE A PDF/WORD" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════`n" -ForegroundColor Cyan

# Verificar si Pandoc está instalado
try {
    $pandocVersion = pandoc --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Pandoc detectado" -ForegroundColor Green
        $usarPandoc = $true
    } else {
        throw "Pandoc no encontrado"
    }
} catch {
    Write-Host "✗ Pandoc no está instalado" -ForegroundColor Red
    Write-Host "`nInstalando Pandoc..." -ForegroundColor Yellow
    Write-Host "Ejecuta: winget install --id JohnMacFarlane.Pandoc" -ForegroundColor Yellow
    Write-Host "O descarga desde: https://pandoc.org/installing.html`n" -ForegroundColor Yellow
    $usarPandoc = $false
}

if ($usarPandoc) {
    Write-Host "`n[1/2] Convirtiendo a Word (.docx)...`n" -ForegroundColor Yellow
    
    foreach ($doc in $documentos) {
        $rutaEntrada = Join-Path $carpetaDoc $doc
        $nombreSalida = [System.IO.Path]::GetFileNameWithoutExtension($doc)
        $rutaSalidaWord = Join-Path $carpetaSalida "$nombreSalida.docx"
        
        if (Test-Path $rutaEntrada) {
            Write-Host "  Procesando: $doc" -ForegroundColor Cyan
            
            # Convertir a Word con tabla de contenidos y numeración
            pandoc $rutaEntrada `
                -o $rutaSalidaWord `
                --toc `
                --toc-depth=3 `
                --number-sections `
                --highlight-style=tango `
                --reference-doc="$carpetaDoc\plantilla_word.docx" `
                2>$null
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "    ✓ Word generado: $nombreSalida.docx" -ForegroundColor Green
            } else {
                # Si falla con plantilla, intentar sin ella
                pandoc $rutaEntrada `
                    -o $rutaSalidaWord `
                    --toc `
                    --toc-depth=3 `
                    --number-sections `
                    --highlight-style=tango `
                    2>$null
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "    ✓ Word generado: $nombreSalida.docx" -ForegroundColor Green
                } else {
                    Write-Host "    ✗ Error al generar Word" -ForegroundColor Red
                }
            }
        } else {
            Write-Host "  ⚠ No encontrado: $doc" -ForegroundColor Yellow
        }
    }
    
    Write-Host "`n[2/2] Convirtiendo a PDF...`n" -ForegroundColor Yellow
    
    foreach ($doc in $documentos) {
        $rutaEntrada = Join-Path $carpetaDoc $doc
        $nombreSalida = [System.IO.Path]::GetFileNameWithoutExtension($doc)
        $rutaSalidaPDF = Join-Path $carpetaSalida "$nombreSalida.pdf"
        
        if (Test-Path $rutaEntrada) {
            Write-Host "  Procesando: $doc" -ForegroundColor Cyan
            
            # Convertir a PDF (requiere LaTeX o wkhtmltopdf)
            pandoc $rutaEntrada `
                -o $rutaSalidaPDF `
                --toc `
                --toc-depth=3 `
                --number-sections `
                --pdf-engine=xelatex `
                -V geometry:margin=1in `
                -V fontsize=11pt `
                2>$null
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "    ✓ PDF generado: $nombreSalida.pdf" -ForegroundColor Green
            } else {
                Write-Host "    ⚠ PDF requiere LaTeX. Intentando método alternativo..." -ForegroundColor Yellow
                
                # Método alternativo: HTML -> PDF (requiere wkhtmltopdf)
                $htmlTemp = Join-Path $carpetaSalida "$nombreSalida.html"
                
                pandoc $rutaEntrada -o $htmlTemp --standalone --self-contained 2>$null
                
                if (Test-Path $htmlTemp) {
                    Write-Host "    ✓ HTML generado: $nombreSalida.html (puedes imprimir a PDF desde navegador)" -ForegroundColor Green
                } else {
                    Write-Host "    ✗ No se pudo generar PDF ni HTML" -ForegroundColor Red
                    Write-Host "      Instala MiKTeX para PDF: https://miktex.org/download" -ForegroundColor Yellow
                }
            }
        }
    }
    
    Write-Host "`n════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "    RESUMEN" -ForegroundColor Cyan
    Write-Host "════════════════════════════════════════════════════════`n" -ForegroundColor Cyan
    
    $archivosGenerados = Get-ChildItem -Path $carpetaSalida -File
    Write-Host "Archivos generados: $($archivosGenerados.Count)" -ForegroundColor Green
    
    foreach ($archivo in $archivosGenerados) {
        $tamanoKB = [math]::Round($archivo.Length / 1KB, 1)
        Write-Host "  • $($archivo.Name) ($tamanoKB KB)" -ForegroundColor White
    }
    
    Write-Host "`nUbicación: $carpetaSalida" -ForegroundColor Cyan
    Write-Host "`n✓ Proceso completado!" -ForegroundColor Green
    
    # Abrir carpeta de salida
    Write-Host "`nAbriendo carpeta de salida..." -ForegroundColor Yellow
    Start-Process explorer.exe $carpetaSalida
    
} else {
    Write-Host "`n════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "    MÉTODO ALTERNATIVO SIN PANDOC" -ForegroundColor Cyan
    Write-Host "════════════════════════════════════════════════════════`n" -ForegroundColor Cyan
    
    Write-Host "Opción 1: Abrir con Microsoft Word" -ForegroundColor Yellow
    Write-Host "  1. Abre Word" -ForegroundColor White
    Write-Host "  2. Archivo > Abrir > Selecciona el archivo .md" -ForegroundColor White
    Write-Host "  3. Word lo importará automáticamente" -ForegroundColor White
    Write-Host "  4. Guarda como .docx o .pdf`n" -ForegroundColor White
    
    Write-Host "Opción 2: Usar VS Code con extensiones" -ForegroundColor Yellow
    Write-Host "  1. code --install-extension yzane.markdown-pdf" -ForegroundColor White
    Write-Host "  2. Abre el archivo .md en VS Code" -ForegroundColor White
    Write-Host "  3. Ctrl+Shift+P > 'Markdown PDF: Export (pdf)'" -ForegroundColor White
    
    Write-Host "`nOpción 3: Convertidor online" -ForegroundColor Yellow
    Write-Host "  https://cloudconvert.com/md-to-pdf" -ForegroundColor White
    Write-Host "  https://convertio.co/es/md-docx/" -ForegroundColor White
}

Write-Host "`n════════════════════════════════════════════════════════`n" -ForegroundColor Cyan
