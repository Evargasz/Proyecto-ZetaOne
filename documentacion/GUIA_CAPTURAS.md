# Guía para Capturar Imágenes - ZetaOne

Esta guía te indica exactamente qué capturas de pantalla necesitas tomar para completar la documentación.

---

## 📸 Preparativos

### Herramientas Recomendadas

1. **Recortes de Windows** (Win + Shift + S)
2. **Snipping Tool** (Herramienta de recortes)
3. **Greenshot** (software gratuito, más opciones)
4. **ShareX** (avanzado, gratis)

### Configuración Antes de Capturar

- Resolución: **1920x1080** (Full HD)
- Cerrar ventanas innecesarias
- Usar datos de ejemplo (no datos sensibles/reales)
- Asegurarse que la aplicación esté en modo claro (no oscuro)

---

## 📂 Estructura de Carpetas

Crear la siguiente estructura:

```
documentacion/
└── imagenes/
    ├── 01_pantalla_inicio/
    ├── 02_autenticacion/
    ├── 03_admin_principal/
    ├── 04_validacion/
    ├── 05_catalogacion/
    ├── 06_basico/
    └── 07_diagramas/
```

Comando PowerShell para crear:
```powershell
cd C:\Users\evargas\Documents\BAC\IA\ZetaOne2\documentacion
New-Item -ItemType Directory -Path imagenes\01_pantalla_inicio
New-Item -ItemType Directory -Path imagenes\02_autenticacion
New-Item -ItemType Directory -Path imagenes\03_admin_principal
New-Item -ItemType Directory -Path imagenes\04_validacion
New-Item -ItemType Directory -Path imagenes\05_catalogacion
New-Item -ItemType Directory -Path imagenes\06_basico
New-Item -ItemType Directory -Path imagenes\07_diagramas
```

---

## 📋 Lista de Capturas Necesarias

### 1. Pantalla de Inicio (01_pantalla_inicio/)

#### `pantalla_inicio.png`
- **Qué capturar:** Ventana completa de bienvenida
- **Cómo:**
  1. Ejecutar `ZetaOne.exe` o `python ZLauncher.py`
  2. Esperar a que cargue la pantalla de inicio
  3. Capturar ventana completa (Alt + Impr Pant)
- **Debe mostrar:**
  - Logo ZetaOne
  - Botones "Iniciar Sesión" y "Salir"
  - Imagen de fondo

---

### 2. Autenticación (02_autenticacion/)

#### `ventana_credenciales.png`
- **Qué capturar:** Ventana de login
- **Cómo:**
  1. Click en "Iniciar Sesión" desde pantalla de inicio
  2. Capturar ventana de credenciales
- **Debe mostrar:**
  - Campos Usuario y Contraseña
  - Botones "Iniciar sesión" y "Salir"

#### `credenciales_llenadas.png`
- **Qué capturar:** Formulario con datos ingresados
- **Cómo:**
  1. Ingresar usuario: `admin`
  2. Ingresar contraseña: `****` (oculta)
  3. NO hacer click en Iniciar sesión aún
  4. Capturar
- **Debe mostrar:**
  - Campo Usuario: "admin"
  - Campo Contraseña: "****"

---

### 3. Administrador - Pantalla Principal (03_admin_principal/)

#### `admin_pantalla_principal.png`
- **Qué capturar:** Interfaz completa de administrador
- **Cómo:**
  1. Iniciar sesión como admin
  2. Maximizar ventana
  3. Capturar pantalla completa
- **Debe mostrar:**
  - Panel izquierdo (Ambientes)
  - Panel derecho (Archivos)
  - Barra de título
  - Botones de acción

#### `panel_ambientes.png`
- **Qué capturar:** Solo el panel izquierdo
- **Cómo:**
  1. Usar herramienta de recorte
  2. Seleccionar solo la sección de ambientes
- **Debe mostrar:**
  - Lista de ambientes con checkboxes
  - Información de IP, puerto, usuario
  - Botones "Recargar Ambientes" y "Probar Conexión"

#### `panel_archivos_vacio.png`
- **Qué capturar:** Panel derecho sin archivos
- **Debe mostrar:**
  - Área de Drag & Drop vacía
  - Tabla vacía
  - Mensaje "Arrastra archivos aquí"

#### `panel_archivos_con_datos.png`
- **Qué capturar:** Panel derecho con archivos cargados
- **Cómo:**
  1. Cargar 3-5 archivos .sp
  2. Capturar
- **Debe mostrar:**
  - Lista de archivos en la tabla
  - Columnas: Nombre, Ruta, Estado
  - Botones: Validar, Catalogar, etc.

#### `probar_conexion_exito.png`
- **Qué capturar:** Mensaje de conexión exitosa
- **Cómo:**
  1. Seleccionar un ambiente
  2. Click en "Probar Conexión"
  3. Capturar el mensaje de éxito
- **Debe mostrar:**
  - Diálogo con mensaje "Conexión exitosa a SYBCOB28"

---

### 4. Validación (04_validacion/)

#### `ventana_validacion_inicial.png`
- **Qué capturar:** Ventana de validación recién abierta
- **Cómo:**
  1. Cargar archivos
  2. Seleccionar ambientes
  3. Click en "Validar"
  4. Capturar inmediatamente
- **Debe mostrar:**
  - Dos pestañas: "Pendientes" y "Validados"
  - Barra de progreso en 0%
  - Lista de archivos pendientes

#### `validacion_en_progreso.png`
- **Qué capturar:** Validación ejecutándose
- **Cómo:**
  1. Durante la validación (Fase 2)
  2. Esperar a que aparezca "Buscando en: ..."
  3. Capturar rápidamente
- **Debe mostrar:**
  - Barra de progreso al 40-60%
  - Texto: "Buscando en: cob_workflow" (o similar)
  - Archivos moviéndose de Pendientes a Validados

#### `validacion_busqueda_bd.png`
- **Qué capturar:** Progreso mostrando BD específica
- **Debe mostrar:**
  - Label: "[Fase 2/2] 'sp_consulta' (5/10) → Buscando en: cob_cartera"

#### `validacion_completada.png`
- **Qué capturar:** Validación finalizada
- **Cómo:**
  1. Esperar a que termine
  2. Cambiar a pestaña "Validados"
  3. Capturar
- **Debe mostrar:**
  - Pestaña "Validados" activa
  - Tabla con columnas: Archivo, SP Name, Base de Datos, Fecha Compilación, Estado
  - Archivos con ✓ Validado
  - Botones "Ejecutar Catalogación" y "Finalizar"

#### `validacion_error.png`
- **Qué capturar:** Archivo con error de validación
- **Cómo:**
  1. Incluir un archivo .sp que NO exista en la BD
  2. Validar
  3. Capturar fila con error
- **Debe mostrar:**
  - Fila con ✗ No encontrado
  - Estado de error

---

### 5. Catalogación (05_catalogacion/)

#### `catalogacion_progreso.png`
- **Qué capturar:** Ventana de progreso de catalogación
- **Cómo:**
  1. Después de validar, click en "Ejecutar Catalogación"
  2. Capturar mientras ejecuta
- **Debe mostrar:**
  - Barra de progreso
  - Archivo actual procesándose
  - Log de actividad

#### `catalogacion_resultado.png`
- **Qué capturar:** Ventana de resultados
- **Debe mostrar:**
  - Lista de archivos catalogados
  - Estado: ÉXITO / ERROR
  - Ruta de la carpeta de resultados

#### `archivos_generados.png`
- **Qué capturar:** Explorador de Windows con archivos generados
- **Cómo:**
  1. Abrir `C:\ZetaOne\Catalogaciones\cataloga<timestamp>\`
  2. Navegar a carpeta SYBCOB28/SD/
  3. Capturar
- **Debe mostrar:**
  - Archivos `sp_name_respaldo_<timestamp>.sp`
  - Archivos `sp_name_catalogado_<timestamp>.sp`
  - Estructura de carpetas

#### `archivo_resultado_txt.png`
- **Qué capturar:** Contenido del archivo resultado_catalogacion_<timestamp>.txt
- **Cómo:**
  1. Abrir el archivo .txt con Notepad
  2. Capturar contenido
- **Debe mostrar:**
  - Tabla con columnas: ESTADO | AMBIENTE | BASE DATOS | RUTA | DETALLE
  - Varias filas de resultados

---

### 6. Usuario Básico (06_basico/)

#### `basico_dashboard.png`
- **Qué capturar:** Dashboard principal de usuario básico
- **Cómo:**
  1. Cerrar sesión de admin
  2. Iniciar sesión con usuario: `user`, contraseña: `user123`
  3. Capturar dashboard
- **Debe mostrar:**
  - Cards de funcionalidades
  - Desbloquear Usuario, Autorizar Tabla, Migración, etc.

#### `migracion_tabla.png`
- **Qué capturar:** Ventana de migración - pestaña Tabla
- **Cómo:**
  1. Click en card "Migración de Datos"
  2. Asegurarse que pestaña "Tabla" esté activa
  3. Capturar
- **Debe mostrar:**
  - Campos: Ambiente Origen, Destino, Base, Tabla, Condición WHERE
  - Botón "Migrar"

#### `migracion_grupo.png`
- **Qué capturar:** Ventana de migración - pestaña Grupo
- **Cómo:**
  1. Click en pestaña "Grupo"
  2. Seleccionar un grupo del combo
  3. Capturar
- **Debe mostrar:**
  - Combo de grupos
  - Campos de variables (:cod_oficina, etc.)
  - Lista de tablas del grupo

#### `migracion_progreso.png`
- **Qué capturar:** Migración en progreso
- **Cómo:**
  1. Iniciar una migración pequeña
  2. Capturar durante ejecución
- **Debe mostrar:**
  - Barra de progreso
  - Log con mensajes "INSERT...", "Procesando..."
  - Contador de registros

#### `modificaciones_varias.png`
- **Qué capturar:** Ventana de modificaciones
- **Cómo:**
  1. Click en card "Modificaciones Varias"
  2. Llenar formulario con datos de ejemplo
  3. Capturar
- **Debe mostrar:**
  - Campos: Ambiente, Base, Tabla, Campo, Valor, Condición
  - Botones "Ejecutar" y "Generar Script SQL"

#### `confirmacion_update.png`
- **Qué capturar:** Diálogo de confirmación de UPDATE
- **Cómo:**
  1. Click en "Ejecutar"
  2. Capturar diálogo de confirmación
- **Debe mostrar:**
  - Sentencia SQL generada
  - Botones "Cancelar" y "Confirmar"

#### `script_sql_completo.png`
- **Qué capturar:** Editor de script SQL
- **Cómo:**
  1. Click en "Generar Script SQL"
  2. Capturar ventana del editor
- **Debe mostrar:**
  - 3 secciones: Pre-código, UPDATE, Post-código
  - Ejemplo de script con BEGIN TRANSACTION, SELECT, UPDATE, COMMIT

---

### 7. Diagramas (07_diagramas/)

**IMPORTANTE:** Usa los diagramas Mermaid del archivo `DIAGRAMAS.md`

#### Conversión de Diagramas Mermaid:

1. **Opción Online:**
   - Visita https://mermaid.live/
   - Copia cada diagrama de `DIAGRAMAS.md`
   - Pega en el editor
   - Click en botón "PNG" o "SVG"
   - Guardar con el nombre indicado

2. **Opción VS Code:**
   - Instalar extensión "Markdown Preview Mermaid Support"
   - Abrir `DIAGRAMAS.md`
   - Click derecho en diagrama → "Export to PNG"

**Diagramas a generar:**

- `arquitectura_alto_nivel.png`
- `flujo_validacion.png`
- `flujo_catalogacion.png`
- `algoritmo_busqueda_inteligente.png`
- `componentes_sistema.png`
- `flujo_migracion_grupo.png`
- `modelo_datos.png`
- `arquitectura_3_capas.png`
- `patrones_diseno.png`

---

## 🔧 Script Automatizado para Organizar

Después de capturar todas las imágenes, usa este script para verificar:

```powershell
# Verificar que todas las imágenes estén presentes

$imagenesRequeridas = @(
    "01_pantalla_inicio\pantalla_inicio.png",
    "02_autenticacion\ventana_credenciales.png",
    "02_autenticacion\credenciales_llenadas.png",
    "03_admin_principal\admin_pantalla_principal.png",
    "03_admin_principal\panel_ambientes.png",
    "03_admin_principal\panel_archivos_vacio.png",
    "03_admin_principal\panel_archivos_con_datos.png",
    "03_admin_principal\probar_conexion_exito.png",
    "04_validacion\ventana_validacion_inicial.png",
    "04_validacion\validacion_en_progreso.png",
    "04_validacion\validacion_busqueda_bd.png",
    "04_validacion\validacion_completada.png",
    "04_validacion\validacion_error.png",
    "05_catalogacion\catalogacion_progreso.png",
    "05_catalogacion\catalogacion_resultado.png",
    "05_catalogacion\archivos_generados.png",
    "05_catalogacion\archivo_resultado_txt.png",
    "06_basico\basico_dashboard.png",
    "06_basico\migracion_tabla.png",
    "06_basico\migracion_grupo.png",
    "06_basico\migracion_progreso.png",
    "06_basico\modificaciones_varias.png",
    "06_basico\confirmacion_update.png",
    "06_basico\script_sql_completo.png",
    "07_diagramas\arquitectura_alto_nivel.png",
    "07_diagramas\flujo_validacion.png",
    "07_diagramas\flujo_catalogacion.png",
    "07_diagramas\algoritmo_busqueda_inteligente.png",
    "07_diagramas\componentes_sistema.png",
    "07_diagramas\flujo_migracion_grupo.png",
    "07_diagramas\modelo_datos.png",
    "07_diagramas\arquitectura_3_capas.png",
    "07_diagramas\patrones_diseno.png"
)

$faltantes = @()

foreach ($img in $imagenesRequeridas) {
    $ruta = "C:\Users\evargas\Documents\BAC\IA\ZetaOne2\documentacion\imagenes\$img"
    if (-not (Test-Path $ruta)) {
        $faltantes += $img
    }
}

if ($faltantes.Count -eq 0) {
    Write-Host "✓ Todas las imágenes están presentes!" -ForegroundColor Green
} else {
    Write-Host "✗ Faltan las siguientes imágenes:" -ForegroundColor Red
    $faltantes | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
}

Write-Host "`nTotal requeridas: $($imagenesRequeridas.Count)" -ForegroundColor Cyan
Write-Host "Total presentes: $($imagenesRequeridas.Count - $faltantes.Count)" -ForegroundColor Cyan
Write-Host "Faltantes: $($faltantes.Count)" -ForegroundColor Cyan
```

---

## 📝 Checklist de Progreso

Marca cada captura completada:

### Pantalla de Inicio
- [ ] pantalla_inicio.png

### Autenticación
- [ ] ventana_credenciales.png
- [ ] credenciales_llenadas.png

### Admin Principal
- [ ] admin_pantalla_principal.png
- [ ] panel_ambientes.png
- [ ] panel_archivos_vacio.png
- [ ] panel_archivos_con_datos.png
- [ ] probar_conexion_exito.png

### Validación
- [ ] ventana_validacion_inicial.png
- [ ] validacion_en_progreso.png
- [ ] validacion_busqueda_bd.png
- [ ] validacion_completada.png
- [ ] validacion_error.png

### Catalogación
- [ ] catalogacion_progreso.png
- [ ] catalogacion_resultado.png
- [ ] archivos_generados.png
- [ ] archivo_resultado_txt.png

### Usuario Básico
- [ ] basico_dashboard.png
- [ ] migracion_tabla.png
- [ ] migracion_grupo.png
- [ ] migracion_progreso.png
- [ ] modificaciones_varias.png
- [ ] confirmacion_update.png
- [ ] script_sql_completo.png

### Diagramas
- [ ] arquitectura_alto_nivel.png
- [ ] flujo_validacion.png
- [ ] flujo_catalogacion.png
- [ ] algoritmo_busqueda_inteligente.png
- [ ] componentes_sistema.png
- [ ] flujo_migracion_grupo.png
- [ ] modelo_datos.png
- [ ] arquitectura_3_capas.png
- [ ] patrones_diseno.png

---

## 🎨 Consejos para Mejores Capturas

1. **Resolución consistente:** Todas las capturas en 1920x1080
2. **Datos de ejemplo:** Usar nombres genéricos (sp_consulta_saldos, no datos reales)
3. **Contraste:** Modo claro de la aplicación
4. **Recorte preciso:** Eliminar espacios innecesarios
5. **Formato PNG:** Mejor calidad que JPG
6. **Nombre descriptivo:** Seguir exactamente los nombres de esta guía

---

**Total de imágenes a capturar: 32**

¡Éxito con las capturas! 📸
