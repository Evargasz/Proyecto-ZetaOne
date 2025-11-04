# 🔍 Comparador de Archivos Profesional

Una aplicación moderna con interfaz gráfica para comparar múltiples archivos y generar reportes detallados de diferencias.

## ✨ Características

- **Interfaz gráfica moderna** con diseño profesional
- **Comparación múltiple** de archivos simultáneamente
- **Opciones avanzadas** de comparación (ignorar espacios, mayúsculas, etc.)
- **Reportes detallados** en formato texto
- **Visualización en tiempo real** de diferencias con colores
- **Soporte para múltiples formatos** de archivo

## 🚀 Instalación y Uso

### Requisitos
- Python 3.7 a 3.11 (recomendado para compatibilidad completa con Drag & Drop)
- Sistema operativo Windows (optimizado para Windows)

### Ejecución Rápida
1. Hacer doble clic en `ejecutar_comparador.bat`
2. O ejecutar desde línea de comandos: `python file_comparator.py`

### Uso de la Aplicación

#### 1. Seleccionar Archivos
- Clic en "➕ Agregar Archivos" para seleccionar archivos
- **Arrastrar y Soltar (Drag & Drop)**: Arrastra archivos directamente al área de la lista de archivos.
- Selecciona 2 o más archivos para comparar
- Usa "🗑️ Eliminar Seleccionado" para quitar archivos
- Usa "🧹 Limpiar Todo" para empezar de nuevo

#### 2. Configurar Opciones
- **Ignorar espacios en blanco**: No considera diferencias en espaciado
- **Ignorar mayúsculas/minúsculas**: Comparación insensible a mayúsculas
- **Mostrar contexto**: Incluye líneas de contexto alrededor de diferencias

#### 3. Ejecutar Comparación
- Clic en "🔍 Comparar Archivos"
- Los resultados aparecen en tiempo real
- Las diferencias se muestran con colores:
  - 🟢 Verde: Líneas agregadas
  - 🔴 Rojo: Líneas eliminadas
  - 🔵 Azul: Encabezados e información

#### 4. Guardar Reporte
- Clic en "💾 Guardar Reporte" para generar un informe detallado en `C:\comparador`.
- Selecciona ubicación y nombre del archivo
- El reporte incluye:
  - Resumen de comparaciones
  - Opciones utilizadas
  - Diferencias detalladas
  - Estadísticas finales

## 📁 Tipos de Archivos Soportados

- **Archivos de texto**: .txt, .log, .csv
- **Archivos de configuración**: .properties, .xml, .json
- **Archivos de código**: .py, .java, .js, .html, .css, .sql
- **Cualquier archivo de texto plano**

## 🎨 Características de la Interfaz

- **Diseño moderno** con colores profesionales
- **Iconos intuitivos** para cada función
- **Área de resultados** con scroll y colores
- **Ventana redimensionable** y centrada
- **Feedback visual** durante el procesamiento

## 📊 Funcionalidades Avanzadas

### Comparación Inteligente
- Compara todos los archivos entre sí (comparación de pares)
- Detecta archivos idénticos automáticamente
- Muestra estadísticas de diferencias

### Reportes Detallados
- Formato unificado de diferencias
- **Informe estructurado** en `C:\comparador\resCompara_<nombre_primer_archivo>.txt`
- Información de contexto configurable
- Resumen ejecutivo con estadísticas
- Marca de tiempo de generación

### Procesamiento Eficiente
- Procesamiento en segundo plano
- Interfaz responsiva durante comparaciones
- Manejo de errores robusto
- Soporte para archivos grandes

## 🛠️ Solución de Problemas

### Error: "Python no está instalado"
- Instalar Python desde https://python.org
- Asegurarse de agregar Python al PATH durante la instalación

### Error: "tkinterdnd2 no está instalado"
- Para la funcionalidad de Drag & Drop, instala `tkinterdnd2`: `pip install tkinterdnd2`
### Error al leer archivos
- Verificar que los archivos no estén en uso por otra aplicación
- Comprobar permisos de lectura
- Asegurarse de que los archivos sean de texto plano

### Interfaz no responde
- La aplicación procesa en segundo plano
- Esperar a que termine la comparación
- Para archivos muy grandes, el proceso puede tomar tiempo

## 📝 Ejemplos de Uso

### Caso 1: Comparar archivos de configuración
1. Seleccionar `config1.properties` y `config2.properties`
2. Activar "Ignorar espacios en blanco"
3. Ejecutar comparación
4. Guardar reporte como `diferencias_config.txt`

### Caso 2: Comparar logs de aplicación
1. Seleccionar múltiples archivos `.log`
2. Activar "Mostrar contexto"
3. Ejecutar comparación para ver diferencias entre logs
4. Analizar patrones en el reporte generado

### Caso 3: Validar versiones de código
1. Seleccionar archivos de código fuente
2. Configurar opciones según necesidades
3. Generar reporte para documentar cambios
4. Usar reporte para revisión de código

## 🔧 Personalización

El código está diseñado para ser fácilmente personalizable:
- Modificar colores en `setup_styles()`
- Agregar nuevos formatos de archivo
- Personalizar opciones de comparación
- Modificar formato de reportes

## 📞 Soporte

Para problemas o mejoras, revisar el código fuente en `file_comparator.py`.
La aplicación está completamente documentada y es fácil de modificar.

---

**Desarrollado como herramienta profesional para comparación de archivos**
*Versión 1.0 - Interfaz gráfica moderna con funcionalidad completa*