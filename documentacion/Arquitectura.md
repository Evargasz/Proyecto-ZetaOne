# Arquitectura del Sistema - ZetaOne

## Versión 1.4.0

---

## Tabla de Contenidos

1. [Visión General](#visión-general)
2. [Arquitectura de Alto Nivel](#arquitectura-de-alto-nivel)
3. [Componentes del Sistema](#componentes-del-sistema)
4. [Patrones de Diseño](#patrones-de-diseño)
5. [Flujo de Datos](#flujo-de-datos)
6. [Modelo de Datos](#modelo-de-datos)
7. [Seguridad](#seguridad)
8. [Rendimiento y Escalabilidad](#rendimiento-y-escalabilidad)
9. [Decisiones de Diseño](#decisiones-de-diseño)

---

## Visión General

### Propósito del Sistema

ZetaOne es un sistema de escritorio para **catalogación, validación y migración** de procedimientos almacenados (Stored Procedures) en ambientes Sybase ASE y SQL Server. Facilita:

- **Catalogación automatizada**: Extrae código compilado de múltiples ambientes
- **Validación inteligente**: Busca SPs en bases de datos usando algoritmos adaptativos
- **Migración de datos**: Transfiere datos entre ambientes de forma controlada
- **Auditoría**: Registra historial de modificaciones y consultas

### Características Principales

- Interfaz gráfica moderna (tkinter/ttkbootstrap)
- Conexión multiambiente simultánea
- Búsqueda inteligente de bases de datos
- Procesamiento asíncrono con progreso en tiempo real
- Generación automática de archivos de respaldo
- Detección de SPs duplicados
- Sistema de logs y auditoría

---

## Arquitectura de Alto Nivel

### Diagrama de Capas

```
┌─────────────────────────────────────────────────────────────────┐
│                     CAPA DE PRESENTACIÓN                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ PantallaInicio│  │ Credenciales │  │ Dashboard    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Validación UI│  │Catalogación UI│ │ Migración UI │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
├─────────────────────────────────────────────────────────────────┤
│                  CAPA DE LÓGICA DE NEGOCIO                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Orquestador de Ventanas                     │  │
│  │            (controladorVentanas)                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Catalogación │  │ Validación   │  │  Migración   │          │
│  │   Handler    │  │   Handler    │  │   Handler    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Sybase      │  │  SQL Server  │  │   Archivos   │          │
│  │  Utils       │  │   Utils      │  │   Utils      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
├─────────────────────────────────────────────────────────────────┤
│                      CAPA DE DATOS                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Sybase     │  │  SQL Server  │  │  Archivos    │          │
│  │   ASE DB     │  │     DB       │  │  JSON/SP     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │        pyodbc (Conectividad ODBC)                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Flujo de Control General

```
Usuario → UI (tkinter) → Controlador → Handler → Utilidades → BD/Archivos
                ↑                                                    │
                └────────────────────────────────────────────────────┘
                           Callbacks / Resultados
```

---

## Componentes del Sistema

### Componente 1: Launcher y Orquestador

[IMAGEN: Diagrama de ZLauncher con flujo de navegación]

```python
ZLauncher.py
    │
    ├─► controladorVentanas
    │   ├─► mostrar_pantalla_inicio()
    │   ├─► mostrar_credenciales()
    │   ├─► mostrar_admin()
    │   └─► mostrar_basico()
    │
    └─► Gestión de ventanas
        ├─► limpiar_root()
        ├─► _configurar_y_centrar_ventana()
        └─► Manejo de temas (ttkbootstrap)
```

**Responsabilidades:**
- Punto de entrada único de la aplicación
- Gestión del ciclo de vida de ventanas
- Navegación entre módulos
- Aplicación de temas visuales

**Tecnologías:**
- tkinter.Tk (raíz de la aplicación)
- ttkbootstrap.Style (temas modernos)
- TkinterDnD (Drag & Drop)

---

### Componente 2: Módulo de Autenticación

```python
ventana_credenciales.py
    │
    └─► class credenciales
        ├─► iniciar_sesion()
        ├─► validar_usuario()
        └─► volver_inicio()
```

**Flujo de Autenticación:**

```
[Usuario ingresa credenciales]
         ↓
[validar_usuario(usuario, contraseña)]
         ↓
[Leer json/usuarios.json]
         ↓
[Comparar credenciales]
         ├─► ✓ Usuario válido → Determinar rol
         │                      ├─► administrador → mostrar_admin()
         │                      └─► basico → mostrar_basico()
         │
         └─► ✗ Credenciales incorrectas → Mostrar error
```

**Archivo de Usuarios:**

```json
[
  {
    "usuario": "admin",
    "contrasena": "admin123",
    "rol": "administrador"
  }
]
```

---

### Componente 3: Usuario Administrador

[IMAGEN: Diagrama de componentes del módulo administrador]

```python
Usuario_administrador/
    │
    ├─► usu_admin_main.py
    │   ├─► class iniciar_ventana
    │   ├─► class AmbientesPanel
    │   └─► class ArchivosPanel
    │
    ├─► validacion_dialog.py
    │   └─► class ValidacionDialog
    │       ├─► worker_validacion() [Thread]
    │       ├─► actualizar_progreso()
    │       └─► ejecutar_catalogacion()
    │
    ├─► handlers/
    │   ├─► catalogacion.py
    │   │   ├─► obtener_fecha_desde_sp_help()
    │   │   ├─► catalogar_plan_ejecucion()
    │   │   └─► generar_archivo_respaldo()
    │   │
    │   ├─► validacion.py
    │   │   ├─► _extraer_sp_name_de_sp()
    │   │   ├─► _extraer_db_de_sp()
    │   │   └─► _validar_y_corregir_base_datos()
    │   │
    │   └─► repetidos.py
    │       └─► detectar_sps_repetidos()
    │
    └─► widgets/
        ├─► archivo_tree.py (Treeview personalizado)
        └─► ambiente_list.py (Lista de ambientes)
```

**Flujo Principal:**

```
[Carga de Archivos]
       ↓
[Selección de Ambientes]
       ↓
[Validación]
   ├─► Fase 1: Preparación (extracción de metadata)
   └─► Fase 2: Búsqueda en BD (algoritmo inteligente)
       ↓
[Resultado en Treeview]
       ↓
[Catalogación]
   ├─► Leer BD validada
   ├─► Obtener código compilado (sp_helptext)
   ├─► Generar archivo respaldo
   ├─► Generar archivo catalogado
   └─► Guardar resultado.txt
```

---

### Componente 4: Usuario Básico

```python
Usuario_basico/
    │
    ├─► usu_basico_main.py
    │   └─► Dashboard con cards
    │
    ├─► Migracion.py
    │   └─► class MigracionVentana
    │       ├─► migrar_tabla_unica()
    │       └─► migrar_grupo_tablas()
    │
    ├─► Modificaciones_varias.py
    │   └─► class ModificacionesVariasVentana
    │       ├─► ejecutar_update()
    │       └─► generar_script_completo()
    │
    ├─► migrar_tabla.py
    │   └─► migrar_tabla(query, tabla, origen, destino)
    │
    └─► migrar_grupo.py
        └─► migrar_grupo(grupo_conf, variables, origen, destino)
```

**Flujo de Migración:**

```
[Configuración]
   ├─► Seleccionar tabla/grupo
   ├─► Definir origen/destino
   └─► Ingresar condiciones WHERE
       ↓
[Ejecución]
   ├─► Conectar a origen
   ├─► SELECT datos
   ├─► Conectar a destino
   ├─► INSERT en lotes
   └─► Actualizar progreso
       ↓
[Resultado]
   ├─► Log en pantalla
   ├─► Guardar en historial
   └─► Mostrar resumen
```

---

### Componente 5: Conectividad de Datos

```python
sybase_utils.py / Handlers
    │
    ├─► conectar_ambiente(ambiente)
    │   ├─► Sybase ASE → pyodbc.connect(sybase_conn_str)
    │   └─► SQL Server → pyodbc.connect(sqlserver_conn_str)
    │
    ├─► _ejecutar_sp_help(sp_name, bd, conn)
    │   └─► SELECT crdate FROM sysobjects WHERE name = ?
    │
    ├─► _obtener_codigo_sp_helptext(sp_name, bd, ambiente)
    │   └─► EXEC sp_helptext 'sp_name'
    │
    └─► _obtener_todas_las_bases_de_datos(conn, tipo)
        ├─► Sybase: SELECT name FROM master.dbo.sysdatabases
        └─► SQL: SELECT name FROM sys.databases
```

**Cadena de Conexión Sybase:**

```python
conn_str = (
    f"DRIVER={{Sybase ASE ODBC Driver}};"
    f"SERVER={ambiente['ip']};"
    f"PORT={ambiente['puerto']};"
    f"UID={ambiente['usuario']};"
    f"PWD={ambiente['clave']};"
    f"DATABASE={ambiente['base']};"
    f"CHARSET=utf8"
)
```

---

## Patrones de Diseño

### 1. Patrón MVC (Modelo-Vista-Controlador)

**Implementación en ZetaOne:**

```
Modelo:
  - Archivos JSON (ambientes, usuarios, catálogos)
  - Base de datos Sybase/SQL Server
  - Archivos .sp en disco

Vista:
  - Ventanas tkinter (PantallaInicio, Credenciales, etc.)
  - Widgets personalizados (Treeview, Listbox)
  - Diálogos modales

Controlador:
  - controladorVentanas (navegación)
  - Handlers (catalogacion.py, validacion.py)
  - Utilidades (sybase_utils.py)
```

**Ejemplo:**

```python
# Modelo: Archivo JSON
ambientes = cargar_json("json/ambientes.json")

# Vista: Interfaz gráfica
class AmbientesPanel:
    def __init__(self):
        self.listbox = tk.Listbox(...)
        self.cargar_ambientes()

# Controlador: Lógica de negocio
def cargar_ambientes(self):
    ambientes = cargar_json("json/ambientes.json")
    for amb in ambientes:
        self.listbox.insert(tk.END, amb['nombre'])
```

---

### 2. Patrón Observer (Callbacks)

**Uso:** Notificación de progreso desde handlers a UI

```python
# Handler (Sujeto Observable)
def obtener_fecha_desde_sp_help(sp_name, bd, ambiente, progress_callback=None):
    for bd_actual in lista_bds:
        # Notificar observador
        if progress_callback:
            progress_callback(bd_actual)
        
        resultado = buscar_sp(bd_actual)

# UI (Observador)
class ValidacionDialog:
    def worker_validacion(self):
        # Definir callback (observador)
        def on_bd_change(bd_nombre):
            self.after(0, self.actualizar_label, f"Buscando en: {bd_nombre}")
        
        # Suscribirse al sujeto
        obtener_fecha_desde_sp_help(sp, bd, amb, on_bd_change)
```

**Beneficio:** Desacopla la lógica de negocio (handler) de la UI (dialog)

---

### 3. Patrón Strategy (Búsqueda de BD)

**Estrategias de Búsqueda:**

1. **Búsqueda Directa**: Usar BD especificada
2. **Búsqueda Inteligente**: Generar combinaciones
3. **Búsqueda Exhaustiva**: Probar todas las BDs

```python
def obtener_fecha_desde_sp_help(sp_name, bd_inicial, ambiente, callback):
    # Estrategia 1: Directa
    fecha = estrategia_directa(sp_name, bd_inicial, conn)
    if fecha:
        return (fecha, None)
    
    # Estrategia 2: Inteligente
    fecha, bd = estrategia_inteligente(sp_name, bd_inicial, conn, callback)
    if fecha:
        return (fecha, bd)
    
    # Estrategia 3: Exhaustiva
    fecha, bd = estrategia_exhaustiva(sp_name, conn, callback)
    return (fecha, bd)
```

---

### 4. Patrón Template Method (Migración)

```python
class MigracionBase:
    def migrar(self):
        self.preparar()
        self.extraer_datos()
        self.transformar_datos()
        self.cargar_datos()
        self.finalizar()
    
    # Métodos abstractos (implementados por subclases)
    def extraer_datos(self):
        raise NotImplementedError
    
    def transformar_datos(self):
        raise NotImplementedError

class MigracionTabla(MigracionBase):
    def extraer_datos(self):
        # Lógica específica para tabla única
        ...

class MigracionGrupo(MigracionBase):
    def extraer_datos(self):
        # Lógica específica para grupo de tablas
        ...
```

---

### 5. Patrón Singleton (Configuración)

```python
class Config:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.cargar_configuracion()
        return cls._instance
    
    def cargar_configuracion(self):
        with open('json/config.json', 'r') as f:
            self.datos = json.load(f)

# Uso
config = Config()  # Primera llamada: carga JSON
config2 = Config()  # Segunda llamada: reutiliza instancia
assert config is config2  # True
```

---

## Flujo de Datos

### Diagrama de Secuencia: Validación

```
Usuario   UI          Thread        Handler         BD
  │       │            │              │             │
  │──────►│ Click      │              │             │
  │       │ Validar    │              │             │
  │       │            │              │             │
  │       │───────────►│ Iniciar      │             │
  │       │            │ worker       │             │
  │       │            │              │             │
  │       │            │──────────────►│ obtener    │
  │       │            │              │ fecha       │
  │       │            │              │             │
  │       │            │              │─────────────►│ SELECT
  │       │            │              │             │ crdate
  │       │            │              │             │
  │       │            │              │◄─────────────│ Fecha
  │       │            │              │             │
  │       │            │◄──────────────│ (fecha,bd) │
  │       │            │              │             │
  │       │◄───────────│ Callback     │             │
  │       │            │              │             │
  │◄──────│ Actualizar │              │             │
  │       │ UI         │              │             │
```

### Diagrama de Secuencia: Catalogación

```
Usuario   UI       Handler      BD         Archivo
  │       │          │           │            │
  │──────►│ Catalogar│           │            │
  │       │          │           │            │
  │       │─────────►│ catalogar │            │
  │       │          │ plan      │            │
  │       │          │           │            │
  │       │          │──────────►│ sp_helptext│
  │       │          │           │            │
  │       │          │◄──────────│ Código     │
  │       │          │           │            │
  │       │          │───────────────────────►│ Leer
  │       │          │                        │ encabezado
  │       │          │                        │
  │       │          │◄───────────────────────│ Encabezado
  │       │          │                        │
  │       │          │───────────────────────►│ Guardar
  │       │          │                        │ respaldo
  │       │          │                        │
  │       │          │───────────────────────►│ Guardar
  │       │          │                        │ catalogado
  │       │          │                        │
  │       │◄─────────│ Resultado              │
  │◄──────│ Mostrar  │                        │
  │       │ ventana  │                        │
```

### Flujo de Datos: Migración de Grupo

```
[Catálogo JSON]
     ↓
[Leer grupo + tablas]
     ↓
[Solicitar variables]
     ↓
[Usuario ingresa: cod_oficina=100]
     ↓
[Para cada tabla:]
     ├─► Reemplazar :cod_oficina → 100
     ├─► Construir SELECT con WHERE
     │      ↓
     │   [Conectar a BD Origen]
     │      ↓
     │   [Ejecutar SELECT]
     │      ↓
     │   [Fetch resultados en lotes]
     │      ↓
     │   [Conectar a BD Destino]
     │      ↓
     │   [Ejecutar INSERT por lote]
     │      ↓
     │   [COMMIT]
     └──► [Siguiente tabla]
           ↓
[Guardar historial]
     ↓
[Mostrar resumen]
```

---

## Modelo de Datos

### Entidad: Ambiente

```json
{
  "nombre": "SYBCOB28",
  "ip": "192.168.36.51",
  "puerto": "7028",
  "usuario": "sa_cobis",
  "clave": "4dm1Nc0b1S",
  "base": "cobis",
  "driver": "Sybase ASE ODBC Driver"
}
```

**Atributos:**
- `nombre` (PK): Identificador único
- `ip`: Dirección del servidor
- `puerto`: Puerto de conexión
- `usuario`: Credencial de BD
- `clave`: Contraseña
- `base`: BD inicial
- `driver`: Driver ODBC

### Entidad: Archivo SP

```python
archivo = {
    'ruta': 'C:/path/to/file.sp',
    'nombre': 'sp_consulta_saldos',
    'sp_name': 'sp_consulta_saldos',
    'bd_original': 'COBIS WORKFLOW',
    'db_override': 'cob_workflow',  # BD validada
    'fecha_compilacion': '2024-01-15 10:30:00',
    'estado': 'Validado',
    'tree_id': 'I001'  # ID en Treeview
}
```

### Entidad: Usuario

```json
{
  "usuario": "admin",
  "contrasena": "admin123",
  "rol": "administrador"
}
```

**Roles:**
- `administrador`: Acceso completo
- `basico`: Acceso a migración y modificaciones

### Entidad: Catálogo de Migración

```json
{
  "nombre": "Cartera",
  "descripcion": "Migración de operaciones de cartera",
  "variables": ["cod_oficina"],
  "tablas": [
    {
      "base": "cob_cartera",
      "tabla": "ca_operacion",
      "where": "op_oficina = :cod_oficina"
    }
  ]
}
```

### Diagrama E-R (Simplificado)

```
┌──────────────┐         ┌──────────────┐
│   Usuario    │         │   Ambiente   │
├──────────────┤         ├──────────────┤
│ usuario (PK) │         │ nombre (PK)  │
│ contrasena   │         │ ip           │
│ rol          │         │ puerto       │
└──────────────┘         │ usuario      │
                         │ clave        │
                         │ base         │
                         │ driver       │
                         └──────────────┘
       │                        │
       │                        │
       │                        │
       └────────┬───────────────┘
                │
                │ usa
                │
                ▼
       ┌──────────────┐
       │   Archivo    │
       ├──────────────┤
       │ ruta (PK)    │
       │ sp_name      │
       │ bd_original  │
       │ db_override  │
       │ estado       │
       └──────────────┘
                │
                │ pertenece a
                │
                ▼
       ┌──────────────┐
       │  Catálogo    │
       ├──────────────┤
       │ nombre (PK)  │
       │ descripcion  │
       │ variables[]  │
       │ tablas[]     │
       └──────────────┘
```

---

## Seguridad

### 1. Autenticación

**Método Actual:** Archivo JSON con credenciales en texto plano

```python
def validar_usuario(self, usuario, contraseña):
    with open('json/usuarios.json', 'r') as f:
        usuarios = json.load(f)
    
    for u in usuarios:
        if u['usuario'] == usuario and u['contrasena'] == contraseña:
            return u['rol']
    
    return None
```

**Mejoras Recomendadas:**

1. **Hash de Contraseñas:**
   ```python
   import hashlib
   
   # Almacenar
   hash_password = hashlib.sha256(password.encode()).hexdigest()
   
   # Validar
   if hash_password == stored_hash:
       # Autenticado
   ```

2. **Cifrado del Archivo JSON:**
   ```python
   from cryptography.fernet import Fernet
   
   # Cifrar
   cipher = Fernet(key)
   encrypted = cipher.encrypt(json.dumps(usuarios).encode())
   
   # Descifrar
   decrypted = cipher.decrypt(encrypted)
   usuarios = json.loads(decrypted)
   ```

### 2. Conexiones de Base de Datos

**Cadena de Conexión Segura:**

```python
# ✗ NO: Contraseña en texto plano
conn_str = f"...;PWD={ambiente['clave']};..."

# ✓ SÍ: Usar variables de entorno
import os
clave = os.getenv('SYBASE_PASSWORD')
conn_str = f"...;PWD={clave};..."
```

**Timeout de Conexión:**

```python
conn = pyodbc.connect(conn_str, timeout=10)
# Evita bloqueos indefinidos
```

### 3. Prevención de Inyección SQL

**Uso de Parámetros:**

```python
# ✗ NO: Concatenación directa
query = f"SELECT * FROM {tabla} WHERE {campo} = '{valor}'"

# ✓ SÍ: Parámetros preparados
query = f"SELECT * FROM {tabla} WHERE {campo} = ?"
cursor.execute(query, (valor,))
```

**Sanitización:**

```python
def sanitizar_valor_sql(self, valor):
    """Sanitiza valores para prevenir inyección SQL básica"""
    if isinstance(valor, str):
        valor = valor.replace("'", "''")
    return valor
```

### 4. Permisos de Archivos

**Restricción de Permisos:**

```powershell
# Solo lectura para usuarios normales
icacls "C:\ZetaOne\json\ambientes.json" /grant:r "Usuarios:(R)"

# Lectura/escritura solo para administradores
icacls "C:\ZetaOne\json\ambientes.json" /grant:r "Administradores:(F)"
```

---

## Rendimiento y Escalabilidad

### 1. Threading para Operaciones Lentas

**Problema:** Búsqueda en BD bloquea UI

**Solución:** Worker threads

```python
def validar_archivos(self):
    # Thread secundario para no bloquear UI
    thread = threading.Thread(target=self.worker_validacion)
    thread.daemon = True
    thread.start()

def worker_validacion(self):
    for archivo in self.archivos:
        # Operación lenta
        fecha, bd = obtener_fecha_desde_sp_help(...)
        
        # Actualizar UI desde thread principal
        self.after(0, self.actualizar_treeview, archivo, fecha, bd)
```

### 2. Búsqueda Optimizada

**Algoritmo Inteligente:**

1. **Búsqueda Directa** (O(1)): 
   - Prueba BD especificada primero
   - Evita búsquedas innecesarias en 90% de casos

2. **Combinaciones Inteligentes** (O(n)):
   - n = número de palabras en el nombre de BD
   - Reduce búsqueda exhaustiva

3. **Búsqueda Exhaustiva** (O(m)):
   - m = número total de BDs
   - Solo como último recurso

**Comparación:**

```
Sin optimización:
  - 100 BDs × 100 archivos = 10,000 consultas

Con optimización:
  - Directa: 90 archivos × 1 consulta = 90
  - Inteligente: 8 archivos × 3 consultas = 24
  - Exhaustiva: 2 archivos × 100 consultas = 200
  Total: 314 consultas (97% reducción)
```

### 3. Batch Processing en Migraciones

```python
def migrar_tabla(query, tabla, origen, destino):
    BATCH_SIZE = 1000
    
    # Leer datos
    cursor_origen.execute(query)
    
    while True:
        # Procesar en lotes
        batch = cursor_origen.fetchmany(BATCH_SIZE)
        if not batch:
            break
        
        # Insertar lote
        cursor_destino.executemany(insert_query, batch)
        conn_destino.commit()
        
        # Actualizar progreso
        actualizar_progreso(len(batch))
```

**Beneficio:** 
- Reduce commits (1 cada 1000 filas vs 1 por fila)
- Mejora rendimiento 10x-100x

### 4. Caché de Conexiones

```python
class ConnectionPool:
    def __init__(self):
        self.connections = {}
    
    def get_connection(self, ambiente):
        key = f"{ambiente['ip']}:{ambiente['puerto']}"
        
        if key not in self.connections:
            self.connections[key] = pyodbc.connect(...)
        
        return self.connections[key]
    
    def close_all(self):
        for conn in self.connections.values():
            conn.close()
```

### 5. Escalabilidad

**Limitaciones Actuales:**

- **Desktop Application**: No soporta múltiples usuarios concurrentes
- **Single-threaded UI**: tkinter no es thread-safe
- **File-based Config**: No usa BD para configuración

**Posibles Mejoras:**

1. **Arquitectura Cliente-Servidor:**
   ```
   [ZetaOne Client] ──HTTP/REST──► [ZetaOne Server] ──ODBC──► [Sybase DB]
   ```

2. **Queue de Tareas:**
   ```python
   from queue import Queue
   import threading
   
   task_queue = Queue()
   
   def worker():
       while True:
           task = task_queue.get()
           procesar_tarea(task)
           task_queue.task_done()
   
   # Iniciar workers
   for i in range(5):
       t = threading.Thread(target=worker)
       t.daemon = True
       t.start()
   ```

3. **Base de Datos de Configuración:**
   - Reemplazar JSON por SQLite/PostgreSQL
   - Permite auditoría y concurrencia

---

## Decisiones de Diseño

### 1. Python 32-bit vs 64-bit

**Decisión:** Usar Python 32-bit

**Razón:**
- Drivers ODBC legacy de Sybase son 32-bit
- Mayor compatibilidad con ambientes antiguos
- Los servidores Sybase ASE en producción usan drivers 32-bit

**Trade-off:**
- Limitación de memoria (4 GB max)
- No afecta el uso normal (archivos .sp son pequeños)

### 2. tkinter vs Qt/Electron

**Decisión:** Usar tkinter + ttkbootstrap

**Razón:**
- tkinter incluido en Python (sin dependencias extra)
- Ligero y rápido
- ttkbootstrap proporciona temas modernos
- Suficiente para aplicación de escritorio interna

**Trade-off:**
- No tan moderno como Electron
- Menos componentes prediseñados que Qt

### 3. JSON vs Base de Datos

**Decisión:** Archivos JSON para configuración

**Razón:**
- Simplicidad: fácil de editar manualmente
- Portabilidad: copiar carpeta = copiar config
- No requiere servidor de BD adicional
- Suficiente para aplicación desktop single-user

**Trade-off:**
- No soporta concurrencia
- Sin validación de esquema
- Sin auditoría automática

### 4. Threading vs Asyncio

**Decisión:** Usar threading para operaciones de BD

**Razón:**
- pyodbc no es async-compatible
- threading.Thread más simple que asyncio
- tkinter se integra mejor con threads

**Implementación:**
```python
# Worker thread para operaciones lentas
thread = threading.Thread(target=self.worker_validacion)
thread.daemon = True
thread.start()

# Actualizar UI desde thread principal
self.after(0, self.actualizar_progreso, valor)
```

### 5. Catalogación con db_override

**Decisión:** Guardar BD validada y reutilizarla en catalogación

**Razón:**
- Evita búsqueda duplicada (ya se hizo en validación)
- Mejora rendimiento (catalogación instantánea)
- Garantiza consistencia (usa misma BD)

**Flujo:**
```
Validación:
  - Buscar SP en BDs
  - Guardar BD encontrada en Treeview columna "Base de Datos"

Catalogación:
  - Leer BD desde Treeview
  - Asignar a archivo['db_override']
  - Usar directamente sin buscar
```

### 6. Archivo de Respaldo + Catalogado

**Decisión:** Generar dos archivos (respaldo y catalogado)

**Razón:**
- **Respaldo**: Preserva archivo original sin modificar
- **Catalogado**: Contiene código actualizado de la BD
- Permite comparar diferencias (diff)
- Auditoría: qué cambió entre versiones

**Nomenclatura:**
```
sp_name_respaldo_20251217165729.sp
sp_name_catalogado_20251217165729.sp
```

---

**Fin de Arquitectura del Sistema**

**Versión:** 1.4.0  
**Última Actualización:** Diciembre 2024
