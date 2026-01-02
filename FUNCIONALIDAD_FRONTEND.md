# Nueva Funcionalidad: Detección de Carpetas Frontend

## Descripción
Se ha implementado una nueva funcionalidad en el módulo de catalogación que detecta automáticamente carpetas llamadas "frontend" (case-insensitive) dentro de las estructuras de SD seleccionadas.

## Características Implementadas

### 1. Detección Automática
- **Cuándo se activa**: Después de seleccionar un SD único o una carpeta con varios SD y validar archivos contra el .txt
- **Búsqueda**: Recursiva en todas las subcarpetas del SD seleccionado
- **Case-insensitive**: Detecta "frontend", "Frontend", "FRONTEND", "FrontEnd", etc.

### 2. Botón Frontend Dinámico
- **Ubicación**: Barra superior, columna 4 (después del botón "Catalogación de CTS")
- **Visibilidad**: Solo aparece cuando se detectan carpetas frontend
- **Animación**: Titila alternando entre estilos "info" y "warning" cada 500ms
- **Acción**: Al hacer clic, abre ventana con detalles de archivos frontend

### 3. Detección de Archivos
- **Tipos detectados**: Archivos .exe y .dll
- **Información capturada**:
  - Nombre del archivo
  - Ruta relativa desde el SD
  - Versión del archivo (leída de propiedades Windows)

### 4. Ventana de Visualización
- **Diseño**: Similar a la ventana "Archivos Detectados"
- **Columnas**:
  - **Nombre**: Nombre del archivo (.exe o .dll)
  - **Ruta**: Ruta relativa desde la carpeta SD
  - **Versión**: Versión leída desde las propiedades del archivo
- **Características**:
  - Scrollbars vertical y horizontal
  - Filas alternadas con colores (mejor legibilidad)
  - Botón "Exportar Lista" que guarda en C:\ZetaOne\Frontend\
  - Ventana centrada en pantalla
  - Transient (siempre sobre la ventana principal)

### 5. Lectura de Versiones
- **Librería utilizada**: win32api (pywin32)
- **Formato de versión**: Major.Minor.Build.Revision (ej: 1.0.0.0)
- **Manejo de errores**: 
  - Si win32api no está disponible: "N/A (win32api no disponible)"
  - Si hay error al leer: "Error: [mensaje]"

### 6. Exportación de Resultados
- **Carpeta destino**: C:\ZetaOne\Frontend\
- **Formato de nombre**: archivos_frontend_YYYYMMDD_HHMMSS.txt
- **Contenido del archivo**:
  - Encabezado con fecha y carpeta escaneada
  - Número de carpetas frontend encontradas
  - Lista detallada de cada archivo con nombre, ruta y versión

## Flujo de Operación

1. Usuario selecciona SD único o carpeta con varios SD
2. Sistema escanea archivos .sp, .sql, .tg
3. Sistema valida contra archivo .txt
4. **NUEVO**: Sistema busca carpetas "frontend"
5. Si encuentra carpetas frontend:
   - Escanea archivos .exe y .dll
   - Lee versiones de cada archivo
   - Muestra botón "Frontend" con animación titilante
6. Usuario hace clic en botón "Frontend"
7. Se abre ventana con lista de archivos y versiones
8. Usuario puede exportar la lista o simplemente consultar

## Variables de Estado Agregadas

```python
# Variables para funcionalidad Frontend
self.carpetas_frontend = []  # Lista de carpetas frontend encontradas
self.archivos_frontend = []  # Lista de archivos .exe y .dll encontrados
self.btn_frontend_visible = False  # Estado de visibilidad del botón
self.animacion_frontend_activa = False
self.animacion_frontend_estado = 0
self.animacion_frontend_id = None
```

## Funciones Principales Agregadas

1. `_detectar_carpetas_frontend()`: Busca carpetas y archivos frontend
2. `_obtener_version_archivo(filepath)`: Lee versión de .exe/.dll usando win32api
3. `_mostrar_boton_frontend()`: Muestra y anima el botón
4. `_ocultar_boton_frontend()`: Oculta y detiene animación del botón
5. `_iniciar_animacion_frontend()`: Inicia animación titilante
6. `_detener_animacion_frontend()`: Detiene animación
7. `_animar_boton_frontend()`: Alterna estilos para crear efecto titilante
8. `abrir_frontend()`: Abre ventana de visualización de archivos

## Dependencias

### Requeridas
- `tkinter` y `ttkbootstrap`: Ya estaban disponibles
- `os`, `datetime`: Ya estaban disponibles

### Opcionales
- `pywin32` (win32api): Para leer versiones de archivos
  - Si no está instalado, la funcionalidad sigue funcionando pero muestra "N/A" en versiones
  - Instalación: `pip install pywin32`

## Mensajes de Log Generados

```
[Archivos] Buscando carpetas frontend...
[Archivos] Carpeta frontend detectada: [ruta]
[Archivos] Se encontraron X carpeta(s) frontend con Y archivo(s) .exe/.dll
```

## Notas Técnicas

- La detección es **case-insensitive** para el nombre "frontend"
- La búsqueda es **recursiva** en toda la estructura del SD
- El botón solo aparece si hay al menos 1 carpeta frontend con archivos .exe o .dll
- La animación se detiene automáticamente al cerrar o cambiar de SD
- La exportación crea la carpeta C:\ZetaOne\Frontend\ si no existe
- El formato de archivo exportado es texto plano UTF-8

## Compatibilidad

- **Windows**: ✅ Totalmente compatible (lectura de versiones funciona)
- **Linux/Mac**: ⚠️ Funcional pero sin lectura de versiones (requiere win32api)

## Ubicación en el Código

**Archivo**: `Usuario_administrador/usu_admin_main.py`

**Líneas principales**:
- Imports: ~14-19 (win32api)
- Variables de estado: ~211-217
- Botón Frontend: ~140-142
- Funciones: ~320-560 (aproximadamente)
- Integración en flujo: ~685 (llamada a _detectar_carpetas_frontend)

## Próximas Mejoras Sugeridas

1. Filtro por tipo de archivo (.exe, .dll, o ambos)
2. Búsqueda de archivos de configuración adicionales (.config, .json)
3. Comparación de versiones entre múltiples SD
4. Exportación a formato Excel o CSV
5. Copiar archivos frontend a ubicación específica
6. Validación de firmas digitales de archivos
