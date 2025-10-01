# ZetaOne v1.1.0 - Changelog

## Nuevas Funcionalidades

### AutocompleteEntry Mejorado
- ✅ **Selección visual con mouse**: Ahora cuando haces clic en un elemento del listado, se marca visualmente antes de seleccionarse
- ✅ **Delay de confirmación**: 200ms de delay para confirmar visualmente la selección
- ✅ **Sin selección automática**: El primer elemento ya no se selecciona automáticamente
- ✅ **Mejor experiencia de usuario**: Feedback visual claro de qué elemento se está seleccionando

### Sistema de Captura (Nuevos Módulos)
- 📸 **Capturador de pantallas**: Funcionalidad para capturar screenshots
- 🎥 **Grabador de video**: Sistema de grabación de pantalla
- 🤖 **Asistente de captura**: Herramienta automatizada para captura de procesos
- 📱 **Interfaz principal**: Nueva ventana principal para gestión de capturas

### Mejoras Técnicas
- 🔧 **Código optimizado**: Refactorización del widget AutocompleteEntry
- 📦 **Nuevas dependencias**: Soporte para librerías de captura de pantalla
- 🛠️ **Instalador automático**: Script batch para instalar dependencias de captura

## Archivos Modificados
- `Usuario_basico/Migracion.py` - Widget AutocompleteEntry mejorado
- `Usuario_basico/migrar_grupo.py` - Optimizaciones menores
- `Usuario_basico/usu_basico_main.py` - Integración de nuevas funcionalidades
- `ZLauncher.py` - Actualizaciones del controlador principal

## Archivos Nuevos
- `Usuario_basico/asistente_captura.py`
- `Usuario_basico/capturador_pantallas.py`
- `Usuario_basico/grabador_video.py`
- `Usuario_basico/app_principal.py`
- `instalar_dependencias_captura.bat`
- `util_ventanas.py`

## Información de Versión
- **Versión**: 1.1.0
- **Fecha**: 29/09/2025
- **Ejecutable**: ZetaOne_v1.1.0.exe
- **Tamaño**: ~9.9 MB
- **Plataforma**: Windows 32-bit

## Instalación
1. Descargar `ZetaOne_v1.1.0.exe` de la carpeta `dist/ZetaOne_v1.1.0/`
2. Copiar toda la carpeta `ZetaOne_v1.1.0` al destino deseado
3. Ejecutar `ZetaOne_v1.1.0.exe`

## Notas Técnicas
- Compilado con PyInstaller 6.14.2
- Python 3.12.3
- Incluye información de versión en el ejecutable
- Ícono personalizado incluido