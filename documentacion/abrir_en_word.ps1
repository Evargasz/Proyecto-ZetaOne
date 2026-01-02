# Conversión Rápida con Microsoft Word
# Este script abre cada documento .md en Word para conversión manual

$documentos = @(
    "Manual_Usuario.md",
    "Manual_Tecnico.md", 
    "Instalacion.md",
    "Arquitectura.md",
    "ESPECIFICACIONES_FUNCIONALES.md"
)

Write-Host "`n════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  CONVERSIÓN CON MICROSOFT WORD" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════`n" -ForegroundColor Cyan

Write-Host "INSTRUCCIONES:" -ForegroundColor Yellow
Write-Host "1. Se abrirá cada documento en Word" -ForegroundColor White
Write-Host "2. En Word: Archivo > Guardar Como" -ForegroundColor White
Write-Host "3. Selecciona formato: .docx o .pdf" -ForegroundColor White
Write-Host "4. Guarda en: documentacion\output_docs\`n" -ForegroundColor White

# Crear carpeta de salida
$carpetaSalida = "output_docs"
if (!(Test-Path $carpetaSalida)) {
    New-Item -ItemType Directory -Path $carpetaSalida | Out-Null
    Write-Host "✓ Carpeta creada: documentacion\output_docs`n" -ForegroundColor Green
}

foreach ($doc in $documentos) {
    if (Test-Path $doc) {
        Write-Host "Abriendo: $doc" -ForegroundColor Cyan
        Start-Process "winword.exe" $doc
        Start-Sleep -Seconds 2
    }
}

Write-Host "`n✓ Documentos abiertos en Word" -ForegroundColor Green
Write-Host "Guarda cada uno como .docx o .pdf en: output_docs\`n" -ForegroundColor Yellow
