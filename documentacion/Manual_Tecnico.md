# Manual Técnico - ZetaOne

## Versión 1.4.0

---

## Tabla de Contenidos

1. [Arquitectura del Sistema](#arquitectura-del-sistema)
2. [Tecnologías Utilizadas](#tecnologías-utilizadas)
3. [Estructura del Proyecto](#estructura-del-proyecto)
4. [Módulos Principales](#módulos-principales)
5. [Flujo de Validación](#flujo-de-validación)
6. [Flujo de Catalogación](#flujo-de-catalogación)
7. [Algoritmo de Búsqueda Inteligente](#algoritmo-de-búsqueda-inteligente)
8. [Conexiones a Bases de Datos](#conexiones-a-bases-de-datos)
9. [Sistema de Callbacks y Progreso](#sistema-de-callbacks-y-progreso)
10. [Manejo de Errores](#manejo-de-errores)
11. [Configuración y Archivos JSON](#configuración-y-archivos-json)
12. [API y Funciones Principales](#api-y-funciones-principales)
13. [Extensión y Personalización](#extensión-y-personalización)
14. [Testing y Depuración](#testing-y-depuración)

---

## Arquitectura del Sistema

### Diseño General

ZetaOne sigue una arquitectura de **3 capas**:

```
┌─────────────────────────────────────────┐
│         CAPA DE PRESENTACIÓN            │
│   (tkinter, ttkbootstrap - GUI)         │
├─────────────────────────────────────────┤
│         CAPA DE LÓGICA DE NEGOCIO       │
│   (handlers, validaciones, catalogación)│
├─────────────────────────────────────────┤
│         CAPA DE DATOS                   │
│   (pyodbc, JSON, archivos .sp/.sql)     │
└─────────────────────────────────────────┘
```

### Patrón MVC Adaptado

- **Modelo**: Archivos JSON (ambientes, usuarios, configuración)
- **Vista**: Interfaces tkinter (ventanas, diálogos)
- **Controlador**: `controladorVentanas`, handlers especializados

### Componentes Principales

[IMAGEN: Diagrama de componentes con ZLauncher, usuarios, handlers, BD]

```
ZLauncher.py (Punto de entrada)
    │
    ├─► PantallaInicio (Bienvenida)
    ├─► Credenciales (Autenticación)
    │
    ├─► Usuario Administrador
    │   ├─► usu_admin_main.py (Ventana principal)
    │   ├─► handlers/
    │   │   ├─► catalogacion.py (Lógica de catalogación)
    │   │   ├─► validacion.py (Lógica de validación)
    │   │   └─► repetidos.py (Detección duplicados)
    │   └─► validacion_dialog.py (UI validación)
    │
    └─► Usuario Básico
        ├─► usu_basico_main.py (Dashboard)
        ├─► Migracion.py (Migración de datos)
        ├─► Modificaciones_varias.py (Updates)
        └─► migrar_grupo.py (Migración grupal)
```

---

## Tecnologías Utilizadas

### Lenguaje y Framework

- **Python 3.12 (32-bit)**
  - Versión 32-bit requerida para compatibilidad con drivers ODBC legacy
  - Instalación: [Python.org](https://www.python.org/downloads/)

### Librerías Principales

| Librería | Versión | Propósito |
|----------|---------|-----------|
| tkinter | (built-in) | GUI framework base |
| ttkbootstrap | 1.10.1 | Temas modernos para tkinter |
| pyodbc | 5.0.1 | Conectividad a Sybase/SQL Server |
| tkinterdnd2 | 0.4.3 | Drag & Drop de archivos |
| Pillow | 10.1.0 | Procesamiento de imágenes |

### Drivers de Base de Datos

- **Sybase ASE ODBC Driver** (32-bit)
  - Ubicación: `ODBC/dll/`
  - Configuración: DSN-less connection strings
  
- **SQL Server Native Client 11.0** (Opcional)
  - Para conexiones a SQL Server
  - Descarga: Microsoft Download Center

### Herramientas de Desarrollo

- **PyInstaller**: Empaquetado de ejecutables
- **Inno Setup**: Generador de instaladores Windows
- **Git**: Control de versiones

---

## Estructura del Proyecto

### Árbol de Directorios

```
ZetaOne2/
│
├── ZLauncher.py                    # Punto de entrada principal
├── pantalla_inicio_sys.py          # Pantalla de bienvenida
├── ventana_credenciales.py         # Login
├── styles.py                       # Estilos globales
├── util_rutas.py                   # Utilidades de rutas
├── util_ventanas.py                # Utilidades de UI
│
├── Usuario_administrador/          # Módulo de administrador
│   ├── __init__.py
│   ├── usu_admin_main.py          # Ventana principal
│   ├── validacion_dialog.py       # Diálogo de validación
│   ├── catalogacion_dialog.py     # Diálogo de catalogación
│   ├── config.py                  # Configuración
│   ├── sybase_utils.py            # Utilidades Sybase
│   │
│   ├── handlers/                  # Lógica de negocio
│   │   ├── __init__.py
│   │   ├── catalogacion.py        # Handler de catalogación
│   │   ├── validacion.py          # Handler de validación
│   │   ├── repetidos.py           # Detección de duplicados
│   │   └── frontend.py            # Catalogación frontend
│   │
│   └── widgets/                   # Widgets personalizados
│       ├── __init__.py
│       ├── archivo_tree.py        # Treeview de archivos
│       └── ambiente_list.py       # Lista de ambientes
│
├── Usuario_basico/                # Módulo de usuario básico
│   ├── __init__.py
│   ├── usu_basico_main.py        # Dashboard
│   ├── Migracion.py              # Ventana de migración
│   ├── migrar_tabla.py           # Migración individual
│   ├── migrar_grupo.py           # Migración grupal
│   ├── Modificaciones_varias.py  # Updates
│   ├── Desbloquear_usuario.py    # Desbloqueo
│   ├── Autorizar_tabla.py        # Permisos
│   └── historialConsultas.py     # Historial
│
├── json/                          # Archivos de configuración
│   ├── ambientes.json            # Definición de ambientes
│   ├── usuarios.json             # Usuarios del sistema
│   ├── config.json               # Configuración global
│   ├── catalogo_migracion.json   # Catálogos de migración
│   ├── historial_migraciones.json
│   └── HistorialModificaciones.json
│
├── ODBC/                          # Drivers de base de datos
│   ├── dll/                      # DLLs del driver Sybase
│   └── include/                  # Headers
│
├── imagenes_iconos/              # Recursos gráficos
│   ├── Zeta99.ico
│   ├── ZetaOne_bg_op2.jpg
│   └── ...
│
├── output/                        # Salidas generadas
│   ├── migration_progress/
│   └── ZLauncher/
│
├── build/                         # Archivos de build (PyInstaller)
├── instalador_generado/          # Instalador Windows
│
└── documentacion/                # Documentación del proyecto
    ├── Manual_Usuario.md
    ├── Manual_Tecnico.md
    ├── Instalacion.md
    └── Arquitectura.md
```

### Archivos de Configuración Importantes

- **ZetaOne.spec**: Configuración de PyInstaller
- **ZetaOne_installer.iss**: Script de Inno Setup
- **version.rc**: Información de versión del ejecutable

---

## Módulos Principales

### 1. ZLauncher.py

**Responsabilidad:** Punto de entrada y orquestador de ventanas

**Clase Principal:**
```python
class controladorVentanas:
    def __init__(self, root):
        self.root = root
        self.style = Style(theme="litera")
        self.usuario_logueado = None
        self.mostrar_pantalla_inicio()
    
    def mostrar_pantalla_inicio(self):
        # Muestra la pantalla de bienvenida
        
    def mostrar_credenciales(self):
        # Muestra la ventana de login
        
    def mostrar_admin(self):
        # Carga interfaz de administrador
        
    def mostrar_basico(self):
        # Carga interfaz de usuario básico
```

**Funciones Clave:**
- `limpiar_root()`: Destruye widgets y resetea geometría
- `_configurar_y_centrar_ventana()`: Centra ventanas en pantalla

---

### 2. Usuario_administrador/usu_admin_main.py

**Responsabilidad:** Interfaz principal del administrador

**Estructura de Clases:**
```python
class usuAdminMain:
    class iniciar_ventana:
        # Configuración de la ventana principal
        
    class AmbientesPanel:
        # Panel izquierdo: gestión de ambientes
        
    class ArchivosPanel:
        # Panel derecho: gestión de archivos
```

**Panel de Archivos - Métodos Principales:**

```python
def cargar_archivos_drag_drop(self, event):
    """Maneja eventos de drag & drop"""
    
def seleccionar_archivos_manual(self):
    """Abre diálogo de selección de archivos"""
    
def validar_archivos(self):
    """Inicia proceso de validación"""
    
def ejecutar_catalogacion(self):
    """Inicia proceso de catalogación"""
    
def detectar_repetidos(self):
    """Busca SPs duplicados"""
```

---

### 3. Usuario_administrador/handlers/catalogacion.py

**Responsabilidad:** Lógica de catalogación y búsqueda de SPs

**Funciones Principales:**

#### obtener_fecha_desde_sp_help()

```python
def obtener_fecha_desde_sp_help(
    sp_name, 
    base_datos_inicial, 
    ambiente, 
    progress_callback=None
):
    """
    Busca un SP en la BD y obtiene su fecha de compilación.
    
    Args:
        sp_name: Nombre del procedimiento almacenado
        base_datos_inicial: BD donde buscar primero
        ambiente: Dict con datos de conexión
        progress_callback: Función para reportar progreso
        
    Returns:
        tuple: (fecha_str, bd_real) o (None, None)
        
    Algoritmo:
        1. Búsqueda directa en base_datos_inicial
        2. Búsqueda en combinaciones inteligentes
        3. Búsqueda exhaustiva en todas las BDs
    """
```

**Búsqueda Inteligente:**

```python
# Fase 1: Búsqueda directa
if base_datos_inicial:
    fecha = _ejecutar_sp_help(sp_name, base_datos_inicial, conn)
    if fecha:
        return (fecha, None)  # Encontrado en BD original

# Fase 2: Combinaciones inteligentes
bases_a_probar = _generar_combinaciones_inteligentes(base_datos_inicial)
# Ejemplo: "COBIS WORKFLOW" → ["cob_cobis", "cob_workflow", "cob_cobis_workflow"]

for bd in bases_a_probar:
    if progress_callback:
        progress_callback(bd)  # Notificar UI
    
    fecha = _ejecutar_sp_help(sp_name, bd, conn)
    if fecha:
        return (fecha, bd)  # Encontrado en otra BD

# Fase 3: Búsqueda exhaustiva
todas_las_bases = _obtener_todas_las_bases_de_datos(conn, tipo_servidor)
for bd in todas_las_bases:
    if progress_callback:
        progress_callback(bd)
    
    fecha = _ejecutar_sp_help(sp_name, bd, conn)
    if fecha:
        return (fecha, bd)

return (None, None)  # No encontrado
```

#### _catalogar_una_tarea()

```python
def _catalogar_una_tarea(archivo, ambiente, directorio_salida):
    """
    Cataloga un único archivo .sp
    
    Args:
        archivo: Dict con datos del archivo
        ambiente: Dict con conexión
        directorio_salida: Ruta donde guardar
        
    Returns:
        tuple: (success_bool, message_str, bd_used_str)
        
    Proceso:
        1. Leer encabezado original
        2. Obtener código compilado (sp_helptext)
        3. Generar archivo respaldo
        4. Generar archivo catalogado
        5. Combinar encabezado + código compilado
    """
```

#### generar_archivo_respaldo()

```python
def generar_archivo_respaldo(
    ruta_archivo_original,
    tipo_archivo='catalogado',  # 'respaldo' o 'catalogado'
    directorio_salida=None
):
    """
    Genera archivo con timestamp
    
    Formato: sp_name_catalogado_20251217165729.sp
    
    Args:
        ruta_archivo_original: Ruta del archivo fuente
        tipo_archivo: Sufijo a usar
        directorio_salida: Directorio destino
        
    Returns:
        str: Ruta del archivo generado
    """
```

---

### 4. Usuario_administrador/validacion_dialog.py

**Responsabilidad:** UI y lógica de validación

**Clase Principal:**

```python
class ValidacionDialog(tk.Toplevel):
    def __init__(self, parent, archivos, ambientes):
        self.archivos = archivos
        self.ambientes = ambientes
        self.validacion_cancelada = False
        
        self._crear_interfaz()
        self._iniciar_validacion()
```

**Flujo de Validación:**

```python
def worker_validacion(self):
    """
    Thread worker que ejecuta la validación en segundo plano
    
    Fase 1: Preparación (rápida)
        - Extraer nombre SP de cada archivo
        - Extraer BD del encabezado
        - Aplicar corrección de BD
        
    Fase 2: Validación (lenta)
        - Para cada archivo:
            - Conectar a cada ambiente
            - Buscar SP usando búsqueda inteligente
            - Actualizar progreso en tiempo real
            - Actualizar Treeview con resultado
    """
    
    total = len(self.archivos)
    
    # FASE 1: Preparación
    self.actualizar_progreso(0, "[Fase 1/2] Preparación...")
    for archivo in self.archivos:
        sp_name = _extraer_sp_name_de_sp(archivo['ruta'])
        bd_from_file = _extraer_db_de_sp(archivo['ruta'])
        archivo['sp_name'] = sp_name
        archivo['bd_original'] = bd_from_file
    
    # FASE 2: Validación
    for idx, archivo in enumerate(self.archivos):
        if self.validacion_cancelada:
            break
        
        progreso_actual = idx + 1
        sp = archivo['sp_name']
        bd = archivo['bd_original']
        
        # Corregir BD antes de mostrar
        bd_corregida = _validar_y_corregir_base_datos(bd, ambiente)
        
        # Mostrar en UI
        self.actualizar_progreso(
            progreso_actual, 
            f"[Fase 2/2] '{sp}' ({progreso_actual}/{total}) → Buscando en: {bd_corregida}"
        )
        
        # Callback para actualizar BD en tiempo real
        def callback_bd_actual(bd_nombre):
            self.after(0, self.actualizar_progreso, progreso_actual, 
                      f"[Fase 2/2] '{sp}' ({progreso_actual}/{total}) → Buscando en: {bd_nombre}")
        
        # Buscar SP
        fecha, bd_real = obtener_fecha_desde_sp_help(
            sp, bd_corregida, ambiente, callback_bd_actual
        )
        
        # Actualizar Treeview
        if fecha:
            self.actualizar_archivo_en_treeview(archivo, fecha, bd_real or bd_corregida)
        
    # Completar
    self.actualizar_progreso(total, "[Completado] 100%")
```

**Métodos de Actualización UI:**

```python
def actualizar_progreso(self, valor, texto):
    """Actualiza barra de progreso y label"""
    self.progress_bar['value'] = (valor / total) * 100
    self.lbl_progreso.config(text=texto)
    
def actualizar_archivo_en_treeview(self, archivo, fecha, bd):
    """Actualiza fila en Treeview con resultado"""
    iid = archivo['tree_id']
    tree.set(iid, "Fecha Compilación", fecha)
    tree.set(iid, "Base de Datos", bd)
    tree.set(iid, "Estado", "✓ Validado")
    
def actualizar_columna_bd(self, archivo, nueva_bd):
    """Actualiza solo la columna Base de Datos"""
    iid = archivo['tree_id']
    tree.set(iid, "Base de Datos", nueva_bd)
```

**Ejecución de Catalogación:**

```python
def ejecutar_catalogacion(self):
    """
    Lee archivos validados y ejecuta catalogación
    Usa db_override para evitar re-búsqueda
    """
    archivos_plan = []
    
    # Leer archivos de Treeview validados
    for iid in active_tree.get_children():
        archivo = {
            'ruta': active_tree.set(iid, "Ruta"),
            'sp_name': active_tree.set(iid, "SP Name"),
            'db_override': active_tree.set(iid, "Base de Datos"),  # ← BD validada
        }
        archivos_plan.append(archivo)
    
    # Ejecutar catalogación
    from .handlers.catalogacion import catalogar_plan_ejecucion
    catalogar_plan_ejecucion(archivos_plan, self.ambientes, directorio_salida)
```

---

### 5. Usuario_basico/Migracion.py

**Responsabilidad:** Interfaz de migración de datos

**Clase Principal:**

```python
class MigracionVentana(tk.Toplevel):
    def __init__(self, parent):
        self.migrando = False
        self.cancelar_migracion = False
        
        self._crear_interfaz()
        self._configurar_eventos()
```

**Migración de Tabla:**

```python
def migrar_tabla_unica(self):
    """
    Migra una tabla individual
    
    Proceso:
        1. Leer datos del formulario
        2. Construir query SELECT con WHERE
        3. Conectar a origen
        4. Ejecutar SELECT
        5. Construir INSERT
        6. Conectar a destino
        7. Insertar datos en lotes
        8. Commit
    """
    # Validar campos
    if not self._validar_campos():
        return
    
    # Construir query
    query = f"SELECT * FROM {base}..{tabla}"
    if condicion:
        query += f" WHERE {condicion}"
    
    # Ejecutar en thread
    thread = threading.Thread(
        target=self._ejecutar_migracion,
        args=(query, tabla, amb_origen, amb_destino)
    )
    thread.start()
```

**Migración de Grupo:**

```python
def migrar_grupo_tablas(self):
    """
    Migra múltiples tablas según catálogo
    
    Proceso:
        1. Leer grupo del catálogo
        2. Solicitar valores de variables (:cod_oficina)
        3. Reemplazar placeholders en WHERE
        4. Para cada tabla:
            - Ejecutar SELECT
            - Insertar en destino
            - Actualizar progreso
    """
    grupo = self.combo_grupo.get()
    catalogo = self._cargar_catalogo(grupo)
    
    for tabla_config in catalogo['tablas']:
        base = tabla_config['base']
        tabla = tabla_config['tabla']
        where = tabla_config['where']
        
        # Reemplazar variables
        where = where.replace(':cod_oficina', self.valores_vars['cod_oficina'])
        
        # Migrar
        self._migrar_una_tabla(base, tabla, where)
```

---

### 6. Usuario_basico/Modificaciones_varias.py

**Responsabilidad:** Ejecución controlada de UPDATEs

**Validación de Tipo de Dato:**

```python
def _get_column_type(self, amb, base, tabla, campo):
    """
    Consulta el tipo de dato de una columna en Sybase
    
    Query:
        SELECT c.type 
        FROM syscolumns c, sysobjects o
        WHERE o.name = 'tabla' AND c.id = o.id AND c.name = 'campo'
    
    Returns:
        int: Tipo de dato (Sybase type code)
    """
    
def _adaptar_valor_por_tipo(self, valor_bruto, tipo_dato):
    """
    Convierte el valor según el tipo de dato
    
    Tipos numéricos (int, decimal, money): valor sin comillas
    Tipos string (char, varchar): 'valor' con comillas
    Tipos fecha (datetime): CONVERT(datetime, 'valor')
    """
```

**Generación de Script:**

```python
def generar_script_completo(self):
    """
    Abre editor de script con 3 secciones:
        - Pre-código
        - UPDATE (generado automáticamente)
        - Post-código
    """
    dialog = UpdateCompletoDialog(self)
    dialog.set_update_statement(self._generar_update())
    dialog.wait_window()
```

---

## Flujo de Validación

### Diagrama de Secuencia

```
Usuario → UI → Dialog → Worker Thread → Handler → BD → Handler → Thread → Dialog → UI
```

### Paso a Paso

1. **Usuario hace clic en "Validar"**
   - `usu_admin_main.py`: `validar_archivos()`
   
2. **Se abre ValidacionDialog**
   - `validacion_dialog.py`: `__init__()`
   - Crea interfaz con Treeview, ProgressBar
   
3. **Inicia worker thread**
   - `validacion_dialog.py`: `_iniciar_validacion()`
   - Thread separado para no bloquear UI
   
4. **Fase 1: Preparación**
   - Extrae SP name de cada archivo
   - Extrae BD del encabezado
   - Corrige BD (mayúsculas/minúsculas)
   
5. **Fase 2: Validación**
   - Para cada archivo:
     - Conecta a ambiente
     - Llama `obtener_fecha_desde_sp_help()`
     - Recibe callback con BD siendo probada
     - Actualiza UI vía `self.after()`
     
6. **Búsqueda inteligente en BD**
   - `catalogacion.py`: `obtener_fecha_desde_sp_help()`
   - Prueba BD original
   - Prueba combinaciones
   - Búsqueda exhaustiva
   - Cada BD probada dispara `progress_callback(bd_nombre)`
   
7. **Actualización de UI en tiempo real**
   - `validacion_dialog.py`: `actualizar_progreso()`
   - Label muestra: "Buscando en: cob_workflow"
   - ProgressBar incrementa
   
8. **Resultado encontrado**
   - `obtener_fecha_desde_sp_help()` retorna `(fecha, bd_real)`
   - Thread actualiza Treeview
   - Mueve archivo a pestaña "Validados"
   
9. **Completado**
   - ProgressBar → 100%
   - Label → "Completado"
   - Botón "Finalizar" habilitado

---

## Flujo de Catalogación

### Diagrama de Flujo

```
[Archivos Validados] 
    ↓
[ejecutar_catalogacion()]
    ↓
[Leer BD de Treeview]
    ↓
[Asignar db_override]
    ↓
[catalogar_plan_ejecucion()]
    ↓
[Para cada archivo]
    ↓
[_catalogar_una_tarea()]
    ├─► [Leer encabezado original]
    ├─► [Obtener código compilado: sp_helptext]
    ├─► [Generar archivo respaldo]
    ├─► [Generar archivo catalogado]
    └─► [Combinar y guardar]
    ↓
[Generar resultado_catalogacion.txt]
    ↓
[Mostrar ventana de resultados]
```

### Código Detallado

**1. Inicio de Catalogación**

```python
# validacion_dialog.py
def ejecutar_catalogacion(self):
    archivos_plan = []
    active_tree = self.tree_validados
    
    for iid in active_tree.get_children():
        archivo = {
            'ruta': active_tree.set(iid, "Ruta"),
            'sp_name': active_tree.set(iid, "SP Name"),
            'db_override': active_tree.set(iid, "Base de Datos"),  # ← BD validada
        }
        archivos_plan.append(archivo)
    
    # Ejecutar
    from .handlers.catalogacion import catalogar_plan_ejecucion
    resultados = catalogar_plan_ejecucion(
        archivos_plan, 
        self.ambientes, 
        directorio_salida
    )
```

**2. Catalogación de un Archivo**

```python
# catalogacion.py
def _catalogar_una_tarea(archivo, ambiente, directorio_salida):
    # 1. Leer encabezado original
    encabezado_original = extraer_comentarios_iniciales(archivo['ruta'])
    
    # 2. Obtener BD a usar (ya validada, no re-buscar)
    base_datos_a_usar = archivo.get('db_override') or \
                        _extraer_db_de_sp(archivo['ruta']) or \
                        ambiente['base']
    
    # Corregir BD
    base_datos_a_usar = _validar_y_corregir_base_datos(base_datos_a_usar, ambiente)
    
    # 3. Conectar y obtener código compilado
    codigo_compilado = _obtener_codigo_sp_helptext(
        archivo['sp_name'], 
        base_datos_a_usar, 
        ambiente
    )
    
    if not codigo_compilado:
        return (False, f"SP {archivo['sp_name']} no encontrado", None)
    
    # 4. Generar archivo respaldo (antes)
    ruta_respaldo = generar_archivo_respaldo(
        archivo['ruta'], 
        tipo_archivo='respaldo',
        directorio_salida
    )
    
    # Copiar archivo original
    shutil.copy(archivo['ruta'], ruta_respaldo)
    
    # 5. Generar archivo catalogado (después)
    ruta_catalogado = generar_archivo_respaldo(
        archivo['ruta'], 
        tipo_archivo='catalogado',
        directorio_salida
    )
    
    # 6. Combinar encabezado + código compilado
    contenido_final = f"{encabezado_original}\n"
    contenido_final += f"--@last-modified-date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    contenido_final += codigo_compilado
    
    # 7. Guardar
    with open(ruta_catalogado, 'w', encoding='utf-8') as f:
        f.write(contenido_final)
    
    return (True, f"Catalogado exitosamente en {base_datos_a_usar}", base_datos_a_usar)
```

**3. Generación de Resultado**

```python
# usu_admin_main.py
def _guardar_resultado_catalogacion_en_archivo(resultados, directorio):
    ruta_resultado = os.path.join(directorio, f"resultado_catalogacion_{timestamp}.txt")
    
    with open(ruta_resultado, 'w', encoding='utf-8') as f:
        # Encabezado
        f.write("ESTADO     | AMBIENTE        | BASE DATOS      | RUTA RELATIVA     | DETALLE\n")
        f.write("---------- | --------------- | --------------- | ----------------- | --------\n")
        
        # Resultados
        for res in resultados:
            estado = "ÉXITO" if res['exito'] else "ERROR"
            ambiente = res['ambiente']
            bd = res.get('base_datos', 'N/A')
            ruta = res['ruta_relativa']
            detalle = res['mensaje']
            
            f.write(f"{estado:<10} | {ambiente:<15} | {bd:<15} | {ruta:<17} | {detalle}\n")
```

---

## Algoritmo de Búsqueda Inteligente

### Objetivo

Encontrar un SP en la base de datos correcta incluso cuando:
- El archivo tiene el nombre de BD incorrecto
- El SP existe en múltiples BDs
- La BD cambió de nombre entre versiones

### Fases del Algoritmo

```python
def obtener_fecha_desde_sp_help(sp_name, base_datos_inicial, ambiente, progress_callback=None):
    """
    Fase 1: Búsqueda Directa
        - Prueba la BD especificada en el archivo
        - Si encuentra → retorna (fecha, None)
        
    Fase 2: Búsqueda Inteligente
        - Genera combinaciones basadas en el nombre de BD
        - Ejemplo: "COBIS WORKFLOW" → ["cob_cobis", "cob_workflow", "cob_cobis_workflow"]
        - Prueba cada combinación
        - Si encuentra → retorna (fecha, bd_real)
        
    Fase 3: Búsqueda Exhaustiva
        - Obtiene TODAS las bases del servidor
        - Prueba cada una secuencialmente
        - Muestra progreso en UI
        - Si encuentra → retorna (fecha, bd_real)
        
    Fase 4: No Encontrado
        - Retorna (None, None)
    """
```

### Implementación Detallada

**Fase 1: Búsqueda Directa**

```python
# Intentar en la BD original primero
if base_datos_inicial:
    if progress_callback:
        progress_callback(base_datos_inicial)
    
    fecha = _ejecutar_sp_help(sp_name, base_datos_inicial, conn)
    if fecha:
        return (fecha, None)  # Encontrado en BD original
```

**Fase 2: Combinaciones Inteligentes**

```python
def _generar_combinaciones_inteligentes(nombre_bd):
    """
    Genera variaciones del nombre de BD
    
    Ejemplos:
        "COBIS" → ["cob_cobis", "cobis", "COBIS"]
        "COBIS WORKFLOW" → ["cob_cobis", "cob_workflow", "cob_cobis_workflow"]
        "COB_CARTERA" → ["cob_cartera", "cartera"]
    """
    combinaciones = set()
    
    # Normalizar
    nombre_limpio = nombre_bd.strip().lower()
    
    # Split por espacios
    palabras = nombre_limpio.split()
    
    # Agregar cada palabra con prefijo "cob_"
    for palabra in palabras:
        combinaciones.add(f"cob_{palabra}")
        combinaciones.add(palabra)
    
    # Combinar todas las palabras
    if len(palabras) > 1:
        combinaciones.add(f"cob_{'_'.join(palabras)}")
    
    # Remover BD original para no duplicar
    combinaciones.discard(nombre_limpio)
    
    return list(combinaciones)

# Usar combinaciones
bases_inteligentes = _generar_combinaciones_inteligentes(base_datos_inicial)
for bd in bases_inteligentes:
    if progress_callback:
        progress_callback(bd)
    
    fecha = _ejecutar_sp_help(sp_name, bd, conn)
    if fecha:
        return (fecha, bd)
```

**Fase 3: Búsqueda Exhaustiva**

```python
# Obtener todas las BDs del servidor
if tipo_servidor == 'sybase':
    query = "SELECT name FROM master.dbo.sysdatabases WHERE name NOT IN ('master', 'model', 'tempdb', 'sybsystemprocs')"
else:  # SQL Server
    query = "SELECT name FROM sys.databases WHERE name NOT IN ('master', 'model', 'msdb', 'tempdb')"

cursor = conn.cursor()
cursor.execute(query)
todas_las_bases = [row.name for row in cursor.fetchall()]

# Remover BDs ya probadas
bases_no_probadas = [bd for bd in todas_las_bases if bd not in bases_ya_probadas]

# Buscar en todas
for bd in bases_no_probadas:
    if progress_callback:
        progress_callback(bd)
    
    fecha = _ejecutar_sp_help(sp_name, bd, conn)
    if fecha:
        return (fecha, bd)

# No encontrado
return (None, None)
```

**Ejecución de sp_helptext**

```python
def _ejecutar_sp_help(sp_name, base_datos, conn):
    """
    Ejecuta sp_helptext en una BD específica
    
    Returns:
        str: Fecha de compilación o None
    """
    try:
        cursor = conn.cursor()
        
        # Cambiar contexto a la BD
        cursor.execute(f"USE {base_datos}")
        
        # Buscar objeto en sysobjects
        query = f"""
        SELECT CONVERT(varchar(30), crdate, 109) as fecha
        FROM {base_datos}..sysobjects 
        WHERE name = ?
        AND type = 'P'
        """
        
        cursor.execute(query, sp_name)
        row = cursor.fetchone()
        
        if row:
            return row.fecha
        
        return None
        
    except pyodbc.Error as e:
        # Errores esperados: objeto no existe, BD no existe
        return None
```

### Ejemplo de Ejecución

**Archivo:** `SD/sp_consulta_saldos.sp`  
**BD en encabezado:** `"COBIS WORKFLOW"`

```
1. Búsqueda Directa
   → Prueba: "COBIS WORKFLOW" → No existe (error: BD no válida)

2. Búsqueda Inteligente
   → Genera combinaciones: ["cob_cobis", "cob_workflow", "cobis", "workflow", "cob_cobis_workflow"]
   
   → Prueba: "cob_cobis"
      ↳ UI: "Buscando en: cob_cobis"
      ↳ Resultado: SP no encontrado
   
   → Prueba: "cob_workflow"
      ↳ UI: "Buscando en: cob_workflow"
      ↳ Resultado: ✓ SP encontrado! Fecha: 2024-01-15 10:30:00
      ↳ Retorna: ("2024-01-15 10:30:00", "cob_workflow")

3. Actualiza Treeview
   → Columna "Base de Datos": "cob_workflow" (corregida)
   → Columna "Fecha Compilación": "2024-01-15 10:30:00"
```

---

## Conexiones a Bases de Datos

### Cadenas de Conexión

**Sybase ASE:**

```python
def conectar_sybase(ambiente):
    """
    Conecta a Sybase ASE usando ODBC
    
    Connection String:
        DRIVER={Sybase ASE ODBC Driver};
        SERVER=192.168.36.51;
        PORT=7028;
        UID=sa_cobis;
        PWD=4dm1Nc0b1S;
        DATABASE=cobis;
        CHARSET=utf8
    """
    conn_str = (
        f"DRIVER={{{ambiente['driver']}}};"
        f"SERVER={ambiente['ip']};"
        f"PORT={ambiente['puerto']};"
        f"UID={ambiente['usuario']};"
        f"PWD={ambiente['clave']};"
        f"DATABASE={ambiente['base']};"
        f"CHARSET=utf8"
    )
    
    conn = pyodbc.connect(conn_str, timeout=10)
    return conn
```

**SQL Server:**

```python
def conectar_sqlserver(ambiente):
    """
    Conecta a SQL Server
    
    Connection String:
        DRIVER={SQL Server Native Client 11.0};
        SERVER=192.168.1.100,1433;
        UID=sa;
        PWD=password;
        DATABASE=master;
        TrustServerCertificate=yes
    """
    conn_str = (
        f"DRIVER={{SQL Server Native Client 11.0}};"
        f"SERVER={ambiente['ip']},{ambiente['puerto']};"
        f"UID={ambiente['usuario']};"
        f"PWD={ambiente['clave']};"
        f"DATABASE={ambiente['base']};"
        f"TrustServerCertificate=yes"
    )
    
    conn = pyodbc.connect(conn_str, timeout=10)
    return conn
```

### Manejo de Contexto

```python
def ejecutar_con_conexion(ambiente, funcion):
    """
    Context manager para conexiones
    
    Garantiza:
        - Conexión se abre
        - Se ejecuta función
        - Conexión se cierra (incluso si hay error)
    """
    conn = None
    try:
        conn = conectar_sybase(ambiente) if ambiente['driver'] == 'Sybase ASE ODBC Driver' else conectar_sqlserver(ambiente)
        resultado = funcion(conn)
        return resultado
    except Exception as e:
        logging.error(f"Error en conexión: {e}")
        raise
    finally:
        if conn:
            conn.close()
```

---

## Sistema de Callbacks y Progreso

### Patrón Observer para Progreso

**Definición:**

Un **callback** es una función pasada como argumento que se ejecuta cuando ocurre un evento específico.

**Implementación en ZetaOne:**

```python
# Handler (Modelo)
def obtener_fecha_desde_sp_help(sp_name, bd, ambiente, progress_callback=None):
    """
    progress_callback: Función que recibe el nombre de la BD siendo probada
    """
    for bd_actual in lista_bases:
        # Notificar progreso
        if progress_callback:
            progress_callback(bd_actual)  # ← Llamada al callback
        
        # Buscar SP
        fecha = _ejecutar_sp_help(sp_name, bd_actual, conn)
        if fecha:
            return (fecha, bd_actual)

# UI (Vista)
class ValidacionDialog:
    def worker_validacion(self):
        # Definir callback
        def callback_bd_actual(bd_nombre):
            # Actualizar UI desde thread secundario
            self.after(0, self.actualizar_progreso, idx, f"Buscando en: {bd_nombre}")
        
        # Pasar callback al handler
        fecha, bd = obtener_fecha_desde_sp_help(sp, bd_inicial, amb, callback_bd_actual)
```

### Sincronización de Threads

**Problema:** Las operaciones de búsqueda son lentas y bloquearían la UI.

**Solución:** Worker threads + `self.after()` para actualizar UI.

```python
# Thread seguro: Actualizar UI desde worker thread
def worker_validacion(self):
    for archivo in self.archivos:
        # Este código corre en thread secundario
        
        def callback(bd_nombre):
            # Programar actualización en thread principal
            self.after(0, self.actualizar_label, f"Buscando en: {bd_nombre}")
        
        fecha, bd = obtener_fecha_desde_sp_help(sp, bd, amb, callback)

# Thread principal: Actualizar widgets
def actualizar_label(self, texto):
    self.lbl_progreso.config(text=texto)
    self.update_idletasks()
```

### Progreso con ProgressBar

```python
def actualizar_progreso(self, valor, texto):
    """
    Actualiza barra de progreso y label
    
    Args:
        valor: Índice actual (1 a N)
        texto: Descripción de la operación
    """
    porcentaje = (valor / self.total_archivos) * 100
    self.progress_bar['value'] = porcentaje
    self.lbl_progreso.config(text=texto)
    self.update()
```

---

## Manejo de Errores

### Clasificación de Errores

**1. Errores de Conexión**

```python
# Códigos de error ODBC
ERRORES_CONEXION = ['08001', '08S01', 'HYT00']

try:
    conn = pyodbc.connect(conn_str)
except pyodbc.Error as e:
    sqlstate = e.args[0] if e.args else None
    if sqlstate in ERRORES_CONEXION:
        raise ConexionError(f"No se puede conectar a {ambiente['ip']}")
```

**2. Errores de BD**

```python
# Códigos de error de BD no existente
ERRORES_BD = ['42S02', '42000']

try:
    cursor.execute(f"USE {base_datos}")
except pyodbc.Error as e:
    sqlstate = e.args[0]
    if sqlstate in ERRORES_BD:
        raise BDNoExisteError(f"Base de datos {base_datos} no existe")
```

**3. Errores de Objeto**

```python
# SP no existe
try:
    cursor.execute(f"sp_helptext '{sp_name}'")
    rows = cursor.fetchall()
    if not rows:
        raise SPNoExisteError(f"SP {sp_name} no encontrado")
except pyodbc.Error as e:
    raise SPNoExisteError(f"SP {sp_name} no existe o sin permisos")
```

### Logging

```python
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('zetaone.log'),
        logging.StreamHandler()
    ]
)

# Usar en código
logger = logging.getLogger(__name__)

try:
    resultado = operacion_riesgosa()
    logger.info(f"Operación exitosa: {resultado}")
except Exception as e:
    logger.error(f"Error en operación: {e}", exc_info=True)
```

---

## Configuración y Archivos JSON

### json/ambientes.json

```json
[
  {
    "nombre": "SYBCOB28",
    "ip": "192.168.36.51",
    "puerto": "7028",
    "usuario": "sa_cobis",
    "clave": "4dm1Nc0b1S",
    "base": "cobis",
    "driver": "Sybase ASE ODBC Driver"
  }
]
```

### json/usuarios.json

```json
[
  {
    "usuario": "admin",
    "contrasena": "admin123",
    "rol": "administrador"
  },
  {
    "usuario": "user",
    "contrasena": "user123",
    "rol": "basico"
  }
]
```

### json/catalogo_migracion.json

```json
[
  {
    "nombre": "Cartera",
    "descripcion": "Migración de operaciones de cartera",
    "variables": ["cod_oficina"],
    "tablas": [
      {
        "base": "cob_cartera",
        "tabla": "ca_operacion",
        "where": "op_oficina = :cod_oficina"
      },
      {
        "base": "cob_cartera",
        "tabla": "ca_dividendo",
        "where": "di_operacion IN (SELECT op_operacion FROM ca_operacion WHERE op_oficina = :cod_oficina)"
      }
    ]
  }
]
```

---

## API y Funciones Principales

### Módulo: catalogacion.py

```python
# Función principal de catalogación
def catalogar_plan_ejecucion(archivos, ambientes, directorio_salida):
    """
    Ejecuta plan de catalogación para múltiples archivos
    
    Args:
        archivos: Lista de dicts con archivos a catalogar
        ambientes: Lista de ambientes donde catalogar
        directorio_salida: Directorio donde guardar resultados
        
    Returns:
        list: Lista de resultados con éxito/error
    """

# Búsqueda de SP
def obtener_fecha_desde_sp_help(sp_name, base_datos_inicial, ambiente, progress_callback=None):
    """Ver sección de Algoritmo de Búsqueda Inteligente"""

# Generación de archivos
def generar_archivo_respaldo(ruta_original, tipo_archivo='catalogado', directorio_salida=None):
    """
    Genera archivo con timestamp
    
    Returns:
        str: Ruta del archivo generado
    """
```

### Módulo: validacion_dialog.py

```python
class ValidacionDialog(tk.Toplevel):
    """
    Diálogo de validación de archivos
    
    Métodos públicos:
        - __init__(parent, archivos, ambientes)
        - ejecutar_catalogacion()
        - cancelar_validacion()
    """
    
    def worker_validacion(self):
        """Worker thread para validación en segundo plano"""
        
    def actualizar_progreso(self, valor, texto):
        """Actualiza UI con progreso"""
        
    def actualizar_archivo_en_treeview(self, archivo, fecha, bd):
        """Actualiza resultado en Treeview"""
```

### Módulo: sybase_utils.py

```python
def conectar_ambiente(ambiente):
    """
    Conecta a un ambiente (Sybase o SQL Server)
    
    Returns:
        pyodbc.Connection: Conexión activa
    """

def _validar_y_corregir_base_datos(bd_nombre, ambiente):
    """
    Valida y corrige nombre de BD
    
    Normaliza mayúsculas/minúsculas
    Verifica existencia en servidor
    
    Returns:
        str: Nombre de BD corregido
    """
```

---

## Extensión y Personalización

### Agregar Nuevo Ambiente

1. Editar `json/ambientes.json`:

```json
{
  "nombre": "NUEVO_SERVIDOR",
  "ip": "192.168.1.200",
  "puerto": "5000",
  "usuario": "sa",
  "clave": "MiPassword123",
  "base": "master",
  "driver": "Sybase ASE ODBC Driver"
}
```

2. Recargar ambientes en la UI

### Agregar Nuevo Catálogo de Migración

1. Editar `json/catalogo_migracion.json`:

```json
{
  "nombre": "Nuevo Grupo",
  "descripcion": "Descripción del grupo",
  "variables": ["var1", "var2"],
  "tablas": [
    {
      "base": "cob_database",
      "tabla": "mi_tabla",
      "where": "campo = :var1 AND otro_campo = :var2"
    }
  ]
}
```

2. La UI detectará automáticamente el nuevo grupo

### Crear Nuevo Handler

```python
# Usuario_administrador/handlers/mi_handler.py

def mi_nueva_funcionalidad(datos, ambiente):
    """
    Nueva funcionalidad personalizada
    
    Args:
        datos: Información necesaria
        ambiente: Ambiente donde ejecutar
        
    Returns:
        bool: Éxito/fallo
    """
    try:
        conn = conectar_ambiente(ambiente)
        cursor = conn.cursor()
        
        # Tu lógica aquí
        cursor.execute("SELECT ...")
        
        conn.commit()
        return True
    except Exception as e:
        logging.error(f"Error en mi_nueva_funcionalidad: {e}")
        return False
    finally:
        conn.close()
```

---

## Testing y Depuración

### Tests Unitarios

```python
# test_catalogacion.py
import unittest
from Usuario_administrador.handlers.catalogacion import obtener_fecha_desde_sp_help

class TestCatalogacion(unittest.TestCase):
    def test_busqueda_directa(self):
        """Prueba búsqueda directa en BD correcta"""
        ambiente = {
            'ip': '192.168.36.51',
            'puerto': '7028',
            'usuario': 'sa_cobis',
            'clave': '4dm1Nc0b1S',
            'driver': 'Sybase ASE ODBC Driver'
        }
        
        fecha, bd = obtener_fecha_desde_sp_help('sp_login', 'cobis', ambiente)
        
        self.assertIsNotNone(fecha)
        self.assertIsNone(bd)  # Encontrado en BD original
    
    def test_busqueda_inteligente(self):
        """Prueba búsqueda con BD incorrecta"""
        ambiente = {...}
        
        # BD incorrecta: "COBIS" en lugar de "cobis"
        fecha, bd = obtener_fecha_desde_sp_help('sp_login', 'COBIS', ambiente)
        
        self.assertIsNotNone(fecha)
        self.assertEqual(bd, 'cobis')  # Corregido automáticamente

if __name__ == '__main__':
    unittest.main()
```

### Debug con Logging

```python
import logging

# Habilitar debug
logging.basicConfig(level=logging.DEBUG)

# En funciones críticas
logger.debug(f"Probando BD: {bd_nombre}")
logger.debug(f"Query: {query}")
logger.debug(f"Resultado: {resultado}")
```

### Herramientas de Depuración

- **VS Code Debugger**: Breakpoints en Python
- **PyCharm Debugger**: Inspección de variables
- **print() statements**: Para debugging rápido
- **logging**: Para debugging permanente

---

**Fin del Manual Técnico**

**Versión:** 1.4.0  
**Última Actualización:** Diciembre 2024
