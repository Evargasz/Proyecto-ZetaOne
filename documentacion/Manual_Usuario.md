# Manual de Usuario - ZetaOne

## Versión 1.4.0

---

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [Requisitos del Sistema](#requisitos-del-sistema)
3. [Pantalla de Inicio](#pantalla-de-inicio)
4. [Autenticación de Usuarios](#autenticación-de-usuarios)
5. [Usuario Administrador](#usuario-administrador)
   - 5.1 [Pantalla Principal](#51-pantalla-principal)
   - 5.2 [Gestión de Ambientes](#52-gestión-de-ambientes)
   - 5.3 [Carga de Archivos](#53-carga-de-archivos)
   - 5.4 [Validación de Archivos](#54-validación-de-archivos)
   - 5.5 [Catalogación](#55-catalogación)
   - 5.6 [Detección de Repetidos](#56-detección-de-repetidos)
   - 5.7 [Catalogación de Frontend](#57-catalogación-de-frontend)
6. [Usuario Básico](#usuario-básico)
   - 6.1 [Pantalla Principal](#61-pantalla-principal)
   - 6.2 [Migración de Datos](#62-migración-de-datos)
   - 6.3 [Modificaciones Varias](#63-modificaciones-varias)
   - 6.4 [Otras Funcionalidades](#64-otras-funcionalidades)
7. [Gestión de Archivos de Resultado](#gestión-de-archivos-de-resultado)
8. [Solución de Problemas](#solución-de-problemas)
9. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## Introducción

**ZetaOne** es un sistema integral para la catalogación, validación y migración de procedimientos almacenados (Stored Procedures) de Sybase ASE y SQL Server. La aplicación proporciona dos perfiles de usuario:

- **Usuario Administrador**: Acceso completo a funciones de catalogación, validación y gestión de ambientes.
- **Usuario Básico**: Acceso a funciones de migración de datos, modificaciones y consultas.

### Objetivos del Sistema

- Catalogar SDs de forma automática en múltiples ambientes
- Validar la existencia de SDs en bases de datos
- Detectar SDs repetidos entre diferentes carpetas
- Facilitar la migración de datos entre ambientes
- Registrar historial de modificaciones y consultas

---

## Requisitos del Sistema

### Hardware Mínimo

- **Procesador**: Intel Core i3 o equivalente
- **RAM**: 4 GB
- **Disco**: 500 MB de espacio libre
- **Pantalla**: Resolución mínima 1280x720

### Software

- **Sistema Operativo**: Windows 10 o superior (32-bit o 64-bit)
- **Python**: 3.12 (32-bit recomendado para compatibilidad con ODBC)
- **Conectividad**: Acceso de red a servidores Sybase ASE y/o SQL Server

### Drivers de Base de Datos

- **Sybase ASE ODBC Driver** (incluido en la carpeta ODBC del proyecto)
- **SQL Server Native Client** (opcional, para conexiones SQL Server)

---

## Pantalla de Inicio

Al ejecutar **ZetaOne.exe** o **ZLauncher.py**, se muestra la pantalla de inicio del sistema.

[IMAGEN: Pantalla de inicio con logo ZetaOne y botones]

### Opciones Disponibles

1. **Iniciar Sesión**: Abre la ventana de credenciales
2. **Salir**: Cierra la aplicación

---

## Autenticación de Usuarios

La ventana de credenciales solicita:

[IMAGEN: Ventana de credenciales con campos Usuario y Contraseña]

### Campos

- **Usuario**: Nombre de usuario registrado
- **Contraseña**: Clave de acceso (se muestra con asteriscos)

### Usuarios Predefinidos

El sistema cuenta con usuarios de prueba (archivo `json/usuarios.json`):

| Usuario | Contraseña | Rol |
|---------|-----------|-----|
| admin | admin123 | Administrador |
| user | user123 | Básico |

### Proceso de Inicio de Sesión

1. Ingrese su **usuario** en el campo correspondiente
2. Ingrese su **contraseña**
3. Haga clic en **Iniciar sesión** o presione **Enter**
4. El sistema validará sus credenciales y lo redirigirá a la interfaz correspondiente

### Opciones Adicionales

- **Salir**: Cierra la ventana y vuelve a la pantalla de inicio
- **Volver**: Regresa a la pantalla de inicio sin cerrar la aplicación

---

## Usuario Administrador

### 5.1 Pantalla Principal

La interfaz del administrador está dividida en dos paneles principales:

[IMAGEN: Pantalla principal de administrador con panel de ambientes (izquierda) y archivos (derecha)]

#### Panel Izquierdo: Gestión de Ambientes
- Lista de ambientes disponibles
- Checkboxes para selección múltiple
- Información de conexión (IP, puerto, usuario)

#### Panel Derecho: Gestión de Archivos
- Área de carga de archivos (Drag & Drop)
- Lista de archivos cargados
- Botones de acción (Validar, Catalogar, Detectar Repetidos, etc.)

---

### 5.2 Gestión de Ambientes

Los ambientes representan conexiones a diferentes servidores de base de datos.

[IMAGEN: Panel de ambientes con checkboxes y botones de acción]

#### Cargar Ambientes

1. Haga clic en **Recargar Ambientes**
2. El sistema lee el archivo `json/ambientes.json`
3. Los ambientes aparecen en la lista con checkboxes

#### Seleccionar Ambientes

- **Marcar individual**: Click en el checkbox de cada ambiente
- **Seleccionar todos**: Click en el checkbox "Todos"
- **Deseleccionar todos**: Click nuevamente en "Todos"

#### Información Mostrada

Cada ambiente muestra:
- **Nombre**: Identificador del ambiente (ej: SYBCOB28)
- **IP**: Dirección del servidor
- **Puerto**: Puerto de conexión
- **Usuario**: Usuario de base de datos
- **Base**: Base de datos inicial

#### Probar Conexión

1. Seleccione uno o más ambientes
2. Haga clic en **Probar Conexión**
3. El sistema intenta conectarse a cada ambiente seleccionado
4. Se muestra un mensaje con el resultado (éxito/fallo)

[IMAGEN: Mensaje de resultado de prueba de conexión]

---

### 5.3 Carga de Archivos

ZetaOne permite cargar archivos de procedimientos almacenados (.sp, .sql) de dos formas:

#### Método 1: Drag & Drop (Arrastrar y Soltar)

[IMAGEN: Área de carga con mensaje "Arrastra archivos aquí"]

1. Seleccione los archivos .sp o .sql desde el explorador de Windows
2. Arrástrelos al área de carga (zona gris)
3. Suelte los archivos
4. Los archivos aparecerán en la lista inferior

#### Método 2: Selección Manual

1. Haga clic en **Seleccionar Archivos**
2. Navegue a la carpeta que contiene los archivos
3. Seleccione uno o más archivos .sp o .sql
4. Haga clic en **Abrir**

#### Lista de Archivos Cargados

[IMAGEN: Tabla con archivos cargados mostrando nombre, ruta y estado]

La tabla muestra:
- **Nombre**: Nombre del archivo
- **Ruta Relativa**: Ubicación del archivo
- **Estado**: Pendiente / Validado / Catalogado

#### Eliminar Archivos

- **Eliminar individual**: Seleccione el archivo y presione **Suprimir**
- **Limpiar todos**: Haga clic en **Limpiar Lista**

---

### 5.4 Validación de Archivos

La validación verifica la existencia de los SDs en las bases de datos seleccionadas.

[IMAGEN: Ventana de validación con barra de progreso]

#### Proceso de Validación

1. **Cargar archivos** en la lista
2. **Seleccionar ambientes** donde validar
3. Haga clic en **Validar**
4. Se abre la ventana de validación

#### Ventana de Validación

[IMAGEN: Ventana de validación con dos pestañas (Pendientes y Validados)]

**Fase 1: Preparación**
- Extrae información de los archivos (nombre SD, base de datos)
- Muy rápida, no requiere conexión

**Fase 2: Validación**
- Conecta a cada ambiente seleccionado
- Busca cada SD en las bases de datos
- Muestra progreso en tiempo real: "Buscando en: cob_cartera"
- Actualiza la columna "Base de Datos" con el resultado

#### Búsqueda Inteligente de Bases de Datos

El sistema usa un algoritmo inteligente que:

1. **Verifica la BD original**: Si el archivo indica "cob_workflow", busca allí primero
2. **Busca combinaciones**: Si no encuentra, prueba variaciones como:
   - "cob_cobis", "cob_workflow", "cob_cobis_workflow"
3. **Búsqueda exhaustiva**: Si falla, busca en TODAS las bases de datos del servidor

[IMAGEN: Progreso mostrando "Buscando en: cob_workflow"]

#### Resultados

**Pestaña "Pendientes"**
- Archivos que aún no se han validado

**Pestaña "Validados"**
- Archivos que ya tienen resultado
- Muestra la fecha de compilación (crdate)
- Muestra la base de datos donde se encontró

[IMAGEN: Tabla de validados con columnas: Archivo, SP Name, Base de Datos, Fecha Compilación, Estado]

#### Interpretación de Resultados

| Estado | Significado | Acción Recomendada |
|--------|-------------|-------------------|
| ✓ Validado | SD encontrado en la BD | Listo para catalogar |
| ✗ No encontrado | SD no existe en ninguna BD | Revisar nombre o crear SD |
| ⚠ Error conexión | No se pudo conectar al ambiente | Verificar credenciales |

#### Cancelar Validación

- Haga clic en **Cancelar** durante el proceso
- El sistema detiene la búsqueda en curso
- Los archivos procesados hasta ese momento se conservan

#### Finalizar Validación

- Haga clic en **Finalizar**
- La ventana se cierra
- Los archivos validados vuelven a la lista principal con su estado actualizado

---

### 5.5 Catalogación

La catalogación extrae el código compilado de los SDs desde la base de datos y genera archivos actualizados.

[IMAGEN: Botón "Ejecutar Catalogación" en la interfaz principal]

#### Pre-requisitos

- Los archivos deben estar **validados** correctamente
- La columna "Base de Datos" debe mostrar la BD correcta
- Al menos un ambiente debe estar seleccionado

#### Proceso de Catalogación

1. Asegúrese de que los archivos estén validados
2. Verifique que los ambientes correctos estén seleccionados
3. Haga clic en **Ejecutar Catalogación**

#### Ventana de Progreso

[IMAGEN: Ventana de progreso de catalogación con barra y log]

La ventana muestra:
- **Barra de progreso**: Porcentaje completado
- **Archivo actual**: Nombre del archivo procesándose
- **Log de actividad**: Mensajes detallados de cada operación

#### ¿Qué Hace la Catalogación?

Para cada archivo:

1. **Lee el encabezado original**: Extrae comentarios iniciales del archivo
2. **Obtiene código compilado**: Ejecuta `sp_helptext` en la BD
3. **Genera archivo de respaldo**: `sp_name_respaldo_20251217165729.sp`
4. **Genera archivo catalogado**: `sp_name_catalogado_20251217165729.sp`
5. **Combina contenido**: 
   - Encabezado original
   - Línea @last-modified-date actualizada
   - Código compilado de la BD

#### Archivos Generados

Todos los archivos se guardan en:
```
C:\ZetaOne\Catalogaciones\cataloga20251217165729\
```

**Estructura de carpetas:**
```
cataloga20251217165729/
├── SYBCOB28/
│   ├── AC/
│   │   ├── sp_archivo1_respaldo_20251217165729.sp
│   │   ├── sp_archivo1_catalogado_20251217165729.sp
│   │   └── ...
│   └── SD/
│       ├── sp_archivo2_respaldo_20251217165729.sp
│       ├── sp_archivo2_catalogado_20251217165729.sp
│       └── ...
└── resultado_catalogacion_20251217165729.txt
```

#### Archivo de Resultado

El archivo `resultado_catalogacion_YYYYMMDDHHMMSS.txt` contiene un resumen:

[IMAGEN: Contenido del archivo de resultado]

```
ESTADO     | AMBIENTE        | BASE DATOS      | RUTA RELATIVA     | DETALLE
---------- | --------------- | --------------- | ----------------- | --------
ÉXITO      | SYBCOB28       | cob_workflow    | SD/sp_file.sp     | Deployed
ÉXITO      | SYBCOB28       | cob_cartera     | AC/sp_otro.sp     | Deployed
ERROR      | SYBCOB28       | N/A             | SD/sp_fail.sp     | SP not found
```

Columnas:
- **ESTADO**: ÉXITO o ERROR
- **AMBIENTE**: Nombre del servidor
- **BASE DATOS**: BD donde se encontró el SP
- **RUTA RELATIVA**: Ubicación del archivo original
- **DETALLE**: Descripción del resultado o error

#### Beneficios de la Catalogación

- **Código actualizado**: Obtiene la última versión de la BD
- **Trazabilidad**: Mantiene respaldo del archivo original
- **Fecha actualizada**: Marca @last-modified-date con timestamp actual
- **Organización**: Estructura de carpetas por ambiente y tipo (AC/SD)

---

### 5.6 Detección de Repetidos

Esta función identifica SDs duplicados entre diferentes carpetas.

[IMAGEN: Ventana de detección de repetidos]

#### Proceso

1. Cargue archivos de **múltiples carpetas** en la lista
2. Haga clic en **Detectar Repetidos**
3. El sistema analiza todos los archivos

#### Criterios de Detección

Dos archivos se consideran repetidos si:
- Tienen el **mismo nombre de SP** (extraído del código)
- Están en **carpetas diferentes** (ej: SD/sp_file.sp y AC/sp_file.sp)

#### Resultados

[IMAGEN: Lista de SPs repetidos agrupados por nombre]

La ventana muestra:
- **Nombre del SP**: Procedimiento duplicado
- **Ubicaciones**: Lista de rutas donde aparece
- **Cantidad**: Número de duplicados

#### Acciones Disponibles

- **Ver detalles**: Muestra el contenido de cada archivo
- **Generar reporte**: Exporta lista de repetidos a archivo .txt
- **Cerrar**: Vuelve a la pantalla principal

---

### 5.7 Catalogación de Frontend

Catalogación especializada para archivos de frontend (archivos .sp sin código compilado en BD).

[IMAGEN: Botón "Catalogar Frontend" en interfaz]

#### ¿Cuándo Usar?

Use esta función cuando:
- Los archivos .sp son de frontend (no existen en la BD)
- Necesita actualizar solo la fecha @last-modified-date
- No requiere obtener código de sp_helptext

#### Proceso

1. Cargue archivos de frontend en la lista
2. Seleccione los archivos a catalogar
3. Haga clic en **Catalogar Frontend**
4. El sistema genera archivos con fecha actualizada

#### Diferencias con Catalogación Normal

| Característica | Catalogación Normal | Frontend |
|---------------|---------------------|----------|
| Consulta BD | Sí (sp_helptext) | No |
| Actualiza código | Sí (de la BD) | No (usa el original) |
| Actualiza fecha | Sí | Sí |
| Requiere validación | Sí | No |

---

## Usuario Básico

### 6.1 Pantalla Principal

La interfaz de usuario básico presenta un dashboard con tarjetas de acceso a diferentes funcionalidades.

[IMAGEN: Dashboard de usuario básico con cards]

#### Tarjetas Disponibles

1. **Desbloquear Usuario**: Desbloquea usuarios en Sybase
2. **Autorizar Tabla**: Autoriza acceso a tablas
3. **Actualizar Fecha Contable**: Modifica fecha de contabilidad
4. **Usuario No Vigente**: Gestiona usuarios no vigentes
5. **Migración de Datos**: Herramienta principal de migración
6. **Modificaciones Varias**: Actualizaciones de datos
7. **Asistente de Captura**: Grabación de pantalla

---

### 6.2 Migración de Datos

Herramienta para migrar datos entre diferentes ambientes de Sybase.

[IMAGEN: Ventana de migración de datos]

#### Tipos de Migración

**1. Migración de Tabla Individual**

Migra datos de una tabla específica.

[IMAGEN: Pestaña "Tabla" en ventana de migración]

**Campos:**
- **Ambiente Origen**: Servidor de donde se extraen los datos
- **Ambiente Destino**: Servidor donde se insertan los datos
- **Base de Datos**: Base de datos a consultar
- **Tabla**: Nombre de la tabla a migrar
- **Condición WHERE**: Filtro SQL (opcional)
- **Índice**: Índice para búsqueda (opcional)

**Proceso:**
1. Seleccione ambiente de origen
2. Ingrese base de datos y tabla
3. (Opcional) Agregue condición WHERE: `fecha > '2024-01-01'`
4. Seleccione ambiente de destino
5. Haga clic en **Migrar**

**2. Migración de Grupo**

Migra múltiples tablas según un catálogo predefinido.

[IMAGEN: Pestaña "Grupo" en ventana de migración]

**Campos:**
- **Grupo**: Seleccione un grupo del catálogo (ej: "Cartera", "Pasivas")
- **Valores Variables**: Ingrese valores para placeholders (:cod_oficina, :cod_cliente)
- **Ambiente Origen y Destino**

**Catálogo de Grupos:**

El archivo `json/catalogo_migracion.json` define grupos de tablas:

```json
{
  "nombre": "Cartera",
  "descripcion": "Migración de datos de cartera",
  "tablas": [
    {
      "base": "cob_cartera",
      "tabla": "ca_operacion",
      "where": "op_oficina = :cod_oficina"
    },
    {
      "base": "cob_cartera",
      "tabla": "ca_dividendo",
      "where": "di_operacion in (select op_operacion from ca_operacion where op_oficina = :cod_oficina)"
    }
  ]
}
```

**Proceso:**
1. Seleccione un **Grupo** del catálogo
2. El sistema muestra las **variables requeridas** (ej: cod_oficina)
3. Ingrese valores para cada variable
4. Seleccione ambientes origen y destino
5. Haga clic en **Migrar Grupo**

#### Progreso de Migración

[IMAGEN: Ventana mostrando progreso de migración con log]

La ventana muestra:
- **Barra de progreso**: Porcentaje completado
- **Tabla actual**: Nombre de la tabla procesándose
- **Registros procesados**: Contador de filas migradas
- **Log de actividad**: Mensajes detallados (INSERT, errores, etc.)

#### Cancelar Migración

- Haga clic en **Cancelar** durante el proceso
- El sistema detiene la migración
- Los datos ya insertados se mantienen (commit por lote)

#### Historial de Migraciones

- Haga clic en **Historial** para ver migraciones anteriores
- El sistema guarda registro de todas las operaciones
- Archivo: `json/historial_migraciones.json`

[IMAGEN: Ventana de historial con tabla de migraciones]

---

### 6.3 Modificaciones Varias

Permite ejecutar sentencias UPDATE en bases de datos de forma controlada.

[IMAGEN: Ventana de modificaciones varias]

#### Campos del Formulario

- **Ambiente**: Seleccione el servidor
- **Base de Datos**: Nombre de la BD
- **Tabla**: Tabla a modificar
- **Campo**: Campo a actualizar
- **Nuevo Valor**: Valor a asignar
- **Condición WHERE**: Filtro para el UPDATE

#### Proceso de Modificación

1. **Seleccione ambiente**: Al seleccionar, se habilitan los campos
2. **Complete datos**:
   ```
   Base: cob_cartera
   Tabla: ca_operacion
   Campo: op_estado
   Valor: 0
   Condición: op_operacion = 123456
   ```
3. El sistema **valida el tipo de dato** del campo automáticamente
4. Haga clic en **Ejecutar**

#### Confirmación

[IMAGEN: Diálogo de confirmación con sentencia SQL]

El sistema muestra:
```sql
UPDATE cob_cartera..ca_operacion
SET op_estado = 0
WHERE op_operacion = 123456
```

- **Cancelar**: Aborta la operación
- **Confirmar**: Ejecuta el UPDATE

#### Script SQL Completo

Puede generar un script SQL con comandos adicionales:

1. Haga clic en **Generar Script SQL**
2. Se abre un editor avanzado

[IMAGEN: Editor de script SQL con pre-código y post-código]

**Secciones del Script:**

- **Pre-código**: Sentencias ANTES del UPDATE (ej: BEGIN TRANSACTION)
- **Sentencia UPDATE**: Generada automáticamente
- **Post-código**: Sentencias DESPUÉS del UPDATE (ej: COMMIT TRANSACTION)

**Ejemplo:**
```sql
-- Pre-código
BEGIN TRANSACTION
SELECT * FROM ca_operacion WHERE op_operacion = 123456

-- Sentencia UPDATE
UPDATE cob_cartera..ca_operacion
SET op_estado = 0
WHERE op_operacion = 123456

-- Post-código
SELECT * FROM ca_operacion WHERE op_operacion = 123456
COMMIT TRANSACTION
```

3. Haga clic en **Ejecutar Script Completo**

#### Historial de Modificaciones

- Todas las modificaciones se guardan en `json/historial_modificaciones.json`
- Acceda al historial haciendo clic en **Historial**

[IMAGEN: Ventana de historial de modificaciones]

El historial muestra:
- Fecha y hora
- Usuario
- Ambiente
- Base de datos
- Sentencia SQL ejecutada
- Resultado (éxito/error)

---

### 6.4 Otras Funcionalidades

#### Desbloquear Usuario

[IMAGEN: Ventana de desbloquear usuario]

Desbloquea cuentas de usuario en Sybase.

**Proceso:**
1. Seleccione **Ambiente**
2. Ingrese **Usuario** a desbloquear
3. Haga clic en **Desbloquear**

El sistema ejecuta:
```sql
sp_locklogin 'usuario', 'unlock'
```

#### Autorizar Tabla

[IMAGEN: Ventana de autorizar tabla]

Otorga permisos sobre tablas a usuarios.

**Proceso:**
1. Seleccione **Ambiente**
2. Ingrese **Base de Datos**
3. Ingrese **Tabla**
4. Ingrese **Usuario** a autorizar
5. Seleccione **Permisos** (SELECT, INSERT, UPDATE, DELETE)
6. Haga clic en **Autorizar**

#### Actualizar Fecha Contable

[IMAGEN: Ventana de actualizar fecha contable]

Modifica la fecha de contabilidad del sistema.

**Proceso:**
1. Seleccione **Ambiente**
2. Ingrese **Nueva Fecha** (formato: YYYY-MM-DD)
3. Haga clic en **Actualizar**

El sistema actualiza la tabla `ba_fecha_cierre`.

#### Asistente de Captura

[IMAGEN: Ventana del asistente de captura]

Graba capturas de pantalla o videos.

**Funciones:**
- Captura de pantalla completa
- Captura de región seleccionada
- Grabación de video con audio
- Semáforo de grabación (indicador visual)

**Proceso:**
1. Haga clic en **Iniciar Grabación**
2. Realice las acciones a grabar
3. Haga clic en **Detener Grabación**
4. El archivo se guarda en `output/capturas/`

---

## Gestión de Archivos de Resultado

### Ubicación de Archivos

Todos los archivos generados se guardan en:

```
C:\ZetaOne\
├── Catalogaciones\
│   └── cataloga20251217165729\
│       ├── SYBCOB28\
│       │   ├── AC\
│       │   │   ├── sp_file_respaldo_20251217165729.sp
│       │   │   └── sp_file_catalogado_20251217165729.sp
│       │   └── SD\
│       └── resultado_catalogacion_20251217165729.txt
└── Migraciones\
    └── migracion20251217165729.log
```

### Convención de Nombres

- **Respaldo**: `sp_name_respaldo_YYYYMMDDHHMMSS.sp`
- **Catalogado**: `sp_name_catalogado_YYYYMMDDHHMMSS.sp`
- **Resultado**: `resultado_catalogacion_YYYYMMDDHHMMSS.txt`

### Limpieza de Archivos

**Recomendación:** 
- Conserve las carpetas de catalogación al menos 30 días
- Archive los resultados importantes
- Elimine carpetas antiguas manualmente desde el explorador de Windows

---

## Solución de Problemas

### Problema: Error de Conexión a la Base de Datos

**Síntoma:**
```
Error de conexión: [HY000] The driver did not supply an error!
```

**Solución:**
1. Verifique las credenciales en `json/ambientes.json`
2. Confirme que el servidor esté accesible (ping a la IP)
3. Verifique que el puerto esté correcto
4. Asegúrese de que el driver ODBC esté instalado

### Problema: SP No Encontrado en Validación

**Síntoma:**
```
Estado: No encontrado
```

**Solución:**
1. Verifique que el nombre del SP sea correcto
2. Confirme que el SP exista en la base de datos:
   ```sql
   SELECT name FROM sysobjects WHERE name LIKE '%sp_name%'
   ```
3. Verifique que el encabezado del archivo tenga el formato correcto
4. Intente con búsqueda exhaustiva (el sistema lo hace automáticamente)

### Problema: Catalogación Falla con Error

**Síntoma:**
```
ERROR: Objeto no encontrado
```

**Solución:**
1. Asegúrese de que el archivo esté **validado** correctamente
2. Verifique que la columna "Base de Datos" tenga la BD correcta
3. Re-ejecute la validación antes de catalogar
4. Verifique permisos del usuario en la BD

### Problema: Migración Muy Lenta

**Síntoma:**
- Progreso muy lento
- Se queda en 0%

**Solución:**
1. Verifique la velocidad de red entre servidores
2. Reduzca el tamaño de lote (batch size)
3. Agregue índices en tablas grandes
4. Divida la migración en rangos más pequeños

### Problema: Archivos No Se Cargan con Drag & Drop

**Síntoma:**
- No funciona arrastrar y soltar

**Solución:**
1. Verifique que los archivos sean .sp o .sql
2. Reinstale la librería tkinterdnd2:
   ```powershell
   pip install tkinterdnd2
   ```
3. Use el método de selección manual como alternativa

---

## Preguntas Frecuentes

### ¿Puedo catalogar sin validar?

No. La validación es necesaria para determinar en qué base de datos existe cada SP. Sin validación, la catalogación no sabría dónde buscar el código compilado.

### ¿Los archivos originales se modifican?

No. Los archivos originales nunca se modifican. El sistema genera archivos nuevos con sufijos `_respaldo` y `_catalogado`.

### ¿Puedo catalogar en múltiples ambientes a la vez?

Sí. Seleccione múltiples ambientes antes de hacer clic en "Ejecutar Catalogación". El sistema procesará cada ambiente por separado y generará carpetas para cada uno.

### ¿Qué formato debe tener el encabezado de los archivos?

El encabezado debe incluir la línea `@last-modified-date` que separa los comentarios del código compilado:

```sql
-- Comentarios iniciales
-- Descripción: Este es un SP de ejemplo
--@last-modified-date: 2024-01-15 10:30:00
CREATE PROCEDURE sp_example
AS
...
```

### ¿Cómo sé si un SP está en la carpeta correcta (AC vs SD)?

El sistema preserva la estructura de carpetas del archivo original. Si el archivo está en `AC/sp_file.sp`, el resultado también estará en la carpeta `AC`.

### ¿Puedo editar el archivo de resultado?

Sí. El archivo `resultado_catalogacion_YYYYMMDDHHMMSS.txt` es un archivo de texto plano. Puede abrirlo con cualquier editor.

### ¿Se pueden personalizar los ambientes?

Sí. Edite el archivo `json/ambientes.json` con cualquier editor de texto. Agregue nuevos objetos JSON con la estructura:

```json
{
  "nombre": "NUEVO_AMB",
  "ip": "192.168.1.100",
  "puerto": "5000",
  "usuario": "sa",
  "clave": "password",
  "base": "master",
  "driver": "Sybase ASE ODBC Driver"
}
```

Luego haga clic en **Recargar Ambientes**.

### ¿Cómo funciona la búsqueda inteligente de bases de datos?

El algoritmo sigue esta secuencia:

1. **Búsqueda directa**: Prueba la BD especificada en el archivo
2. **Combinaciones inteligentes**: Si el archivo dice "COBIS WORKFLOW", prueba:
   - cob_cobis
   - cob_workflow
   - cob_cobis_workflow
3. **Búsqueda exhaustiva**: Si falla, busca en TODAS las bases del servidor
4. **Actualización**: Si encuentra en otra BD, actualiza la columna "Base de Datos"

### ¿Qué hacer si el sistema se congela?

1. Presione **Ctrl+C** en la consola (si ejecuta desde Python)
2. Cierre la ventana modal actual
3. Reinicie la aplicación
4. Verifique que no haya procesos huérfanos en el Administrador de Tareas

### ¿Se guardan logs de las operaciones?

Sí. Dependiendo de la operación:
- **Catalogación**: `resultado_catalogacion_YYYYMMDDHHMMSS.txt`
- **Migración**: `json/historial_migraciones.json`
- **Modificaciones**: `json/historial_modificaciones.json`
- **Consultas**: `json/HistorialConsultas.json`

---

## Contacto y Soporte

Para reportar errores o solicitar nuevas funcionalidades, contacte al equipo de desarrollo.

**Versión del Manual:** 1.4.0  
**Última Actualización:** Diciembre 2024  

---

**Fin del Manual de Usuario**
