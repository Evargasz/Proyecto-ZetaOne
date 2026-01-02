# Especificaciones Funcionales - ZetaOne

**Proyecto:** Sistema de Homologación y Migración de Datos Sybase  
**Versión:** 1.4.0  
**Fecha:** Diciembre 2025  
**Product Owner:** Equipo de Desarrollo ZetaOne  
**Metodología:** Agile/Scrum  

---

## Índice

1. [Epic 1: Gestión de Autenticación y Acceso](#epic-1-gestión-de-autenticación-y-acceso)
2. [Epic 2: Validación de Stored Procedures (Admin)](#epic-2-validación-de-stored-procedures-admin)
3. [Epic 3: Catalogación de Stored Procedures (Admin)](#epic-3-catalogación-de-stored-procedures-admin)
4. [Epic 4: Migración de Datos (Usuario Básico)](#epic-4-migración-de-datos-usuario-básico)
5. [Epic 5: Operaciones Administrativas de Base de Datos](#epic-5-operaciones-administrativas-de-base-de-datos)
6. [Epic 6: Gestión de Configuración y Ambientes](#epic-6-gestión-de-configuración-y-ambientes)

---

## Epic 1: Gestión de Autenticación y Acceso

### US-001: Inicio de Sesión con Control de Roles

**Como** usuario del sistema  
**Quiero** autenticarme con credenciales válidas y que el sistema reconozca mi rol  
**Para** acceder a las funcionalidades correspondientes a mi perfil (Administrador o Usuario Básico)

#### Criterios de Aceptación

- **Dado** que soy un usuario registrado en el sistema
- **Cuando** ingreso mi usuario y contraseña en la pantalla de login
- **Entonces** el sistema:
  - Valida las credenciales contra `json/usuarios.json`
  - Identifica mi rol (Administrador/Basico)
  - Redirige a la interfaz correspondiente según el rol
  - Muestra mensaje de error si las credenciales son inválidas

#### Reglas de Negocio

- **RN-001.1:** Las credenciales deben estar almacenadas en `json/usuarios.json` con estructura:
  ```json
  {
    "usuario": "nombre_usuario",
    "password": "contraseña_encriptada",
    "rol": "Administrador" | "Basico"
  }
  ```
- **RN-001.2:** Máximo 3 intentos fallidos antes de bloquear temporalmente (opcional)
- **RN-001.3:** El sistema debe registrar usuario logueado y timestamp del login

#### Definición de Terminado (DoD)

- [ ] Validación de credenciales funcional
- [ ] Redirección correcta según rol
- [ ] Manejo de errores con mensajes claros
- [ ] Log de accesos registrado
- [ ] Pruebas unitarias pasadas (cobertura > 80%)
- [ ] Code review aprobado
- [ ] Documentación técnica actualizada

#### Estimación

**Story Points:** 3  
**Prioridad:** Crítica  
**Sprint:** 1

#### Dependencias

- Archivo `json/usuarios.json` debe existir
- `ventana_credenciales.py` implementado

#### Notas Técnicas

```python
# Componentes involucrados:
# - ZLauncher.py (controlador principal)
# - ventana_credenciales.py (UI de login)
# - json/usuarios.json (persistencia)

# Flujo:
# 1. Usuario ingresa credenciales
# 2. Sistema valida contra JSON
# 3. Si válido → cargar interfaz según rol
# 4. Si inválido → mostrar error y limpiar campos
```

---

### US-002: Pantalla de Bienvenida con Selección de Perfil

**Como** usuario del sistema  
**Quiero** ver una pantalla de bienvenida con acceso directo a mi perfil  
**Para** navegar rápidamente a la funcionalidad que necesito

#### Criterios de Aceptación

- **Dado** que ejecuto la aplicación ZetaOne
- **Cuando** se carga la pantalla inicial
- **Entonces** veo:
  - Logo de ZetaOne
  - Botón "Administrador" que abre pantalla de login
  - Botón "Usuario Básico" que abre pantalla de login
  - Información de versión de la aplicación

#### Reglas de Negocio

- **RN-002.1:** La pantalla debe tener dimensiones fijas de 400x350px
- **RN-002.2:** Debe mostrar imagen de fondo `ZetaOne_bg_op2.jpg`
- **RN-002.3:** Ambos botones conducen al mismo login (diferenciación por credenciales)

#### Definición de Terminado

- [ ] Pantalla renderizada correctamente con imagen de fondo
- [ ] Botones funcionales
- [ ] Navegación a login operativa
- [ ] Ventana centrada en pantalla
- [ ] Pruebas de UI pasadas

#### Estimación

**Story Points:** 2  
**Prioridad:** Alta  
**Sprint:** 1

---

### US-003: Cierre de Sesión Seguro

**Como** usuario autenticado  
**Quiero** poder cerrar sesión de forma segura  
**Para** proteger mi cuenta y permitir que otro usuario acceda

#### Criterios de Aceptación

- **Dado** que estoy autenticado en el sistema
- **Cuando** hago clic en "Cerrar Sesión" o cierro la ventana principal
- **Entonces** el sistema:
  - Limpia los datos de sesión actual
  - Cierra todas las ventanas abiertas
  - Regresa a la pantalla de inicio o termina la aplicación

#### Reglas de Negocio

- **RN-003.1:** Debe solicitar confirmación si hay operaciones en progreso
- **RN-003.2:** Debe guardar estado de favoritos antes de cerrar (Usuario Básico)
- **RN-003.3:** Debe liberar conexiones de base de datos activas

#### Estimación

**Story Points:** 2  
**Prioridad:** Media  
**Sprint:** 1

---

## Epic 2: Validación de Stored Procedures (Admin)

### US-004: Validación Automatizada de SP en Múltiples Ambientes

**Como** administrador del sistema  
**Quiero** validar que un Stored Procedure existe en uno o varios ambientes destino  
**Para** asegurar que el código está sincronizado antes de implementar en producción

#### Criterios de Aceptación

- **Dado** que tengo un archivo `.sp` seleccionado y ambientes configurados
- **Cuando** ejecuto la validación automatizada
- **Entonces** el sistema:
  - **Fase 1 - Preparación:**
    - Extrae nombre de BD desde encabezado (`/* Base de datos: xxx */`)
    - Extrae nombre de SP desde encabezado (`/* Stored procedure: xxx */`)
    - Valida que la información extraída no sea `None`
    - Si falta información, intenta extraer de líneas `use <db>` y `create procedure <sp>`
  
  - **Fase 2 - Búsqueda Inteligente:**
    - **Estrategia Directa:** Busca SP en la BD del encabezado
    - **Estrategia Smart (si falla directa):** Busca en BDs relacionadas según `ambientesrelacionados.json`
    - **Estrategia Exhaustiva (último recurso):** Busca en todas las BDs del ambiente
    - Ejecuta `sp_help <sp_name>` en cada BD candidata
    - Extrae `crdate` (fecha de creación) del resultado
  
  - **Resultado:**
    - Marca ambiente como ✅ ENCONTRADO (con fecha) o ❌ NO ENCONTRADO
    - Genera archivo de resultado en `output/<timestamp>_validacion.txt`
    - Muestra resumen en pantalla con progreso por archivo y ambiente

#### Reglas de Negocio

- **RN-004.1:** La validación debe ejecutarse en **thread separado** para no bloquear UI
- **RN-004.2:** Debe permitir **cancelación** en cualquier momento
- **RN-004.3:** Debe mostrar **progreso en tiempo real** (% completado, archivo actual, ambiente actual)
- **RN-004.4:** Si un ambiente falla (timeout, error de conexión), debe continuar con los siguientes
- **RN-004.5:** El archivo de salida debe incluir:
  ```
  ARCHIVO: nombre_archivo.sp
  ════════════════════════════════════════════════
  
  Ambiente: PRU
  Base de datos: cob_atm (Directa)
  Stored Procedure: sp_consulta_asigna_tc
  Fecha de creación: 2024-11-15 10:30:45
  Estado: ✅ ENCONTRADO
  
  Ambiente: DES
  Estado: ❌ NO ENCONTRADO (Búsqueda exhaustiva completada)
  ```
- **RN-004.6:** Debe usar `db_override` de catalogación previa si existe (evita re-búsqueda)

#### Casos de Uso Extendidos

**Flujo Principal:**
1. Admin selecciona 1+ archivos `.sp`
2. Admin selecciona ambiente origen
3. Admin selecciona 1+ ambientes destino
4. Admin hace clic en "Validar"
5. Sistema muestra diálogo de confirmación con plan de ejecución
6. Admin confirma
7. Sistema ejecuta validación en background thread
8. Sistema actualiza progreso en UI
9. Sistema genera archivo de resultado
10. Sistema muestra resumen final

**Flujos Alternativos:**

- **FA-1:** Si archivo no tiene encabezados → Sistema intenta parsing de `use` y `create procedure`
- **FA-2:** Si falla parsing → Admin puede editar manualmente BD/SP en diálogo
- **FA-3:** Si ambiente no conecta → Sistema marca como ERROR y continúa
- **FA-4:** Si Admin cancela → Sistema detiene thread, genera archivo parcial y muestra resultados hasta el momento

#### Definición de Terminado

- [ ] Fase 1 (Preparación) extrae correctamente BD y SP
- [ ] Fase 2 (Búsqueda) implementa 3 estrategias (Directa/Smart/Exhaustiva)
- [ ] Threading funcional sin bloquear UI
- [ ] Callback de progreso actualiza barra y labels
- [ ] Cancelación detiene thread correctamente
- [ ] Archivo de resultado generado con formato correcto
- [ ] Manejo de errores de conexión robusto
- [ ] Pruebas unitarias > 85% cobertura
- [ ] Pruebas de integración con BD mock pasadas
- [ ] Documentación técnica completa

#### Estimación

**Story Points:** 13  
**Prioridad:** Crítica  
**Sprint:** 2-3

#### Dependencias

- `validacion_dialog.py` (UI de validación)
- `handlers/validacion.py` (lógica de negocio)
- `sybase_utils.py` (conexiones BD)
- `ambientesrelacionados.json` (relaciones entre ambientes)

#### Notas Técnicas

```python
# Algoritmo de Búsqueda Inteligente:

def buscar_sp_inteligente(ambiente, sp_name, db_encabezado, db_override=None):
    """
    Estrategia de 3 niveles para encontrar SP
    """
    if db_override:
        # OPTIMIZACIÓN: Usar BD de catalogación previa
        return buscar_en_bd(ambiente, db_override, sp_name)
    
    # NIVEL 1: Búsqueda directa en BD del encabezado
    resultado = buscar_en_bd(ambiente, db_encabezado, sp_name)
    if resultado:
        return resultado
    
    # NIVEL 2: Búsqueda en BDs relacionadas (smart)
    bds_relacionadas = obtener_bds_relacionadas(ambiente, db_encabezado)
    for bd in bds_relacionadas:
        resultado = buscar_en_bd(ambiente, bd, sp_name)
        if resultado:
            return resultado
    
    # NIVEL 3: Búsqueda exhaustiva en todas las BDs
    todas_las_bds = listar_todas_las_bds(ambiente)
    for bd in todas_las_bds:
        resultado = buscar_en_bd(ambiente, bd, sp_name)
        if resultado:
            return resultado
    
    return None  # No encontrado

# Threading pattern:
def ejecutar_validacion_thread():
    thread = threading.Thread(
        target=validar_archivos,
        args=(archivos, origen, destinos, callback_progreso, callback_finalizado),
        daemon=True
    )
    thread.start()
```

---

### US-005: Edición Manual de Información de Validación

**Como** administrador  
**Quiero** editar manualmente la información de BD y SP durante la validación  
**Para** corregir errores de parsing o manejar casos especiales

#### Criterios de Aceptación

- **Dado** que estoy en el diálogo de validación
- **Cuando** veo el plan de ejecución antes de confirmar
- **Entonces** puedo:
  - Hacer doble clic en una tarea para editarla
  - Modificar el nombre de la base de datos
  - Modificar el nombre del stored procedure
  - Guardar cambios y que se reflejen en el plan

#### Reglas de Negocio

- **RN-005.1:** Los cambios solo afectan la sesión actual (no modifican el archivo `.sp`)
- **RN-005.2:** Debe validar que BD y SP no estén vacíos
- **RN-005.3:** Debe actualizar el tree view con los nuevos valores

#### Estimación

**Story Points:** 3  
**Prioridad:** Media  
**Sprint:** 2

---

### US-006: Generación de Reporte de Validación

**Como** administrador  
**Quiero** que el sistema genere un reporte detallado de la validación  
**Para** documentar el estado de sincronización de los SPs en los ambientes

#### Criterios de Aceptación

- **Dado** que completé una validación
- **Cuando** finaliza el proceso
- **Entonces** el sistema genera un archivo `.txt` con:
  - Timestamp de ejecución
  - Lista de archivos validados
  - Estado por ambiente (Encontrado/No encontrado/Error)
  - Fecha de creación del SP (si se encontró)
  - Estrategia de búsqueda usada (Directa/Smart/Exhaustiva)
  - Resumen global (X de Y encontrados)

#### Reglas de Negocio

- **RN-006.1:** Archivo debe guardarse en `output/<timestamp>_validacion.txt`
- **RN-006.2:** Debe abrirse automáticamente al finalizar
- **RN-006.3:** Formato debe ser legible y estructurado

#### Estimación

**Story Points:** 2  
**Prioridad:** Alta  
**Sprint:** 2

---

## Epic 3: Catalogación de Stored Procedures (Admin)

### US-007: Catalogación Automatizada Sin Re-búsqueda

**Como** administrador  
**Quiero** catalogar Stored Procedures utilizando la información de validación previa  
**Para** generar catálogos precisos sin duplicar búsquedas en las bases de datos

#### Criterios de Aceptación

- **Dado** que tengo archivos validados previamente
- **Cuando** ejecuto la catalogación
- **Entonces** el sistema:
  - **NO** realiza nueva búsqueda de BDs (usa `db_override` de validación)
  - Lee el contenido completo del archivo `.sp`
  - Extrae dependencias (tablas, stored procedures referenciados)
  - Genera archivo de catálogo con formato estructurado
  - Guarda en `output/<timestamp>_catalogo_<archivo>.txt`

#### Reglas de Negocio

- **RN-007.1:** **OPTIMIZACIÓN CRÍTICA:** Si existe `db_override` de validación → NO buscar BD nuevamente
- **RN-007.2:** El catálogo debe incluir:
  ```
  ════════════════════════════════════════════════
  CATÁLOGO DE STORED PROCEDURE
  ════════════════════════════════════════════════
  
  Archivo: sp_consulta_asigna_tc.sp
  Base de datos: cob_atm
  Stored Procedure: sp_consulta_asigna_tc
  Fecha de catalogación: 2025-12-17 14:30:00
  Usuario: admin_user
  
  ════════════════════════════════════════════════
  CONTENIDO DEL ARCHIVO
  ════════════════════════════════════════════════
  
  /* Base de datos: cob_atm */
  /* Stored procedure: sp_consulta_asigna_tc */
  
  use cob_atm
  go
  
  create procedure sp_consulta_asigna_tc
  ...
  
  ════════════════════════════════════════════════
  ANÁLISIS DE DEPENDENCIAS
  ════════════════════════════════════════════════
  
  Tablas referenciadas:
    - ca_transaccion
    - ca_usuario
  
  Stored Procedures llamados:
    - sp_valida_usuario
    - sp_log_operacion
  ```
- **RN-007.3:** Debe ejecutarse en thread separado
- **RN-007.4:** Debe mostrar progreso en tiempo real

#### Casos de Uso Extendidos

**Flujo Principal:**
1. Admin selecciona archivos validados
2. Admin hace clic en "Catalogar"
3. Sistema muestra diálogo de confirmación
4. Sistema ejecuta catalogación en background
5. Sistema lee contenido de cada archivo
6. Sistema analiza dependencias (tablas, SPs)
7. Sistema genera archivo de catálogo
8. Sistema muestra resumen final

**Flujos Alternativos:**

- **FA-1:** Si archivo no fue validado → Sistema ejecuta búsqueda de BD (fallback)
- **FA-2:** Si archivo no se puede leer → Sistema marca ERROR y continúa
- **FA-3:** Si Admin cancela → Sistema detiene y guarda catálogos parciales

#### Definición de Terminado

- [ ] Usa `db_override` cuando está disponible
- [ ] No realiza búsqueda duplicada de BD
- [ ] Lee contenido completo del archivo
- [ ] Analiza dependencias correctamente (regex parsing)
- [ ] Genera archivo con formato correcto
- [ ] Threading no bloquea UI
- [ ] Cancelación funcional
- [ ] Pruebas unitarias > 80% cobertura
- [ ] Documentación actualizada

#### Estimación

**Story Points:** 8  
**Prioridad:** Crítica  
**Sprint:** 3

#### Dependencias

- US-004 (Validación) debe estar completa
- `catalogacion_dialog.py` (UI)
- `handlers/catalogacion.py` (lógica)

#### Notas Técnicas

```python
# OPTIMIZACIÓN CLAVE:

def catalogar_archivo(archivo, db_override=None):
    """
    Catalogación optimizada con db_override
    """
    if db_override:
        # ✅ USAR BD DE VALIDACIÓN - NO RE-BUSCAR
        base_datos = db_override
    else:
        # ⚠️ FALLBACK: Solo si no hay validación previa
        base_datos = buscar_bd_inteligente(archivo)
    
    # Leer contenido del archivo
    with open(archivo, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Analizar dependencias
    tablas = extraer_tablas_referenciadas(contenido)
    sps = extraer_sps_llamados(contenido)
    
    # Generar catálogo
    catalogo = generar_catalogo_estructurado(
        archivo, base_datos, contenido, tablas, sps
    )
    
    return catalogo
```

---

### US-008: Análisis de Dependencias en Catalogación

**Como** administrador  
**Quiero** que el catálogo identifique automáticamente las dependencias del SP  
**Para** entender el impacto de cambios y planificar migraciones

#### Criterios de Aceptación

- **Dado** que estoy catalogando un SP
- **Cuando** se genera el catálogo
- **Entonces** el sistema identifica:
  - **Tablas:** Nombres de tablas en cláusulas `FROM`, `JOIN`, `UPDATE`, `INSERT INTO`
  - **SPs llamados:** Nombres de SPs en cláusulas `EXEC`, `EXECUTE`
  - **Variables:** Declaraciones de variables (`@variable`)
  - **Parámetros:** Parámetros del SP (`@param tipo`)

#### Reglas de Negocio

- **RN-008.1:** Usar expresiones regulares para parsing
- **RN-008.2:** Ignorar comentarios al analizar
- **RN-008.3:** Eliminar duplicados en listas de dependencias

#### Estimación

**Story Points:** 5  
**Prioridad:** Media  
**Sprint:** 3

---

### US-009: Detección y Eliminación de Archivos Repetidos

**Como** administrador  
**Quiero** detectar archivos duplicados antes de validar/catalogar  
**Para** evitar trabajo redundante y mantener el workspace limpio

#### Criterios de Aceptación

- **Dado** que tengo archivos seleccionados
- **Cuando** ejecuto "Quitar Repetidos"
- **Entonces** el sistema:
  - Compara nombres de archivos
  - Identifica duplicados exactos
  - Muestra lista de duplicados
  - Permite eliminar los duplicados seleccionados

#### Reglas de Negocio

- **RN-009.1:** Comparación debe ser case-insensitive
- **RN-009.2:** Debe solicitar confirmación antes de eliminar
- **RN-009.3:** Debe actualizar el tree view después de eliminar

#### Estimación

**Story Points:** 3  
**Prioridad:** Baja  
**Sprint:** 4

---

## Epic 4: Migración de Datos (Usuario Básico)

### US-010: Migración de Tabla Individual con Preview

**Como** usuario básico  
**Quiero** migrar datos de una tabla entre ambientes con vista previa  
**Para** asegurar que estoy migrando los datos correctos antes de confirmar

#### Criterios de Aceptación

- **Dado** que tengo una tabla origen y destino configurados
- **Cuando** ingreso una consulta SQL y presiono "Consultar"
- **Entonces** el sistema:
  - Ejecuta el SELECT en el ambiente origen
  - Muestra preview de los primeros 100 registros
  - Muestra total de registros a migrar
  - Muestra las columnas de la tabla
  - Habilita el botón "Migrar"

- **Cuando** presiono "Migrar" después del preview
- **Entonces** el sistema:
  - Deshabilita triggers en tabla destino (`_manage_trigger`)
  - Extrae datos del origen en lotes de 5000 registros
  - Inserta en destino usando `INSERT` batch
  - Actualiza barra de progreso cada lote
  - Re-habilita triggers al finalizar
  - Muestra resumen (insertados, omitidos, errores)
  - Guarda registro en `HistorialModificaciones.json`

#### Reglas de Negocio

- **RN-010.1:** **Manejo de Triggers:**
  ```python
  # ANTES de migrar:
  _manage_trigger(cursor, tabla, "DISABLE", log_func)
  
  # DESPUÉS de migrar (SIEMPRE, incluso si falla):
  try:
      # ... migración ...
  finally:
      _manage_trigger(cursor, tabla, "ENABLE", log_func)
  ```
- **RN-010.2:** **Batch Processing:** Lotes de 5000 registros para optimizar memoria
- **RN-010.3:** **Manejo de Duplicados:** Usar `INSERT` sin validación previa (dejar que BD rechace duplicados)
- **RN-010.4:** **Cancelación:** Debe permitir cancelar en cualquier momento con rollback
- **RN-010.5:** **Threading:** Migración en thread separado, consulta preview también en thread
- **RN-010.6:** **Logging:** Registrar cada operación en consola con timestamp
- **RN-010.7:** **Progreso:** Actualizar cada 5000 registros o cada 5 segundos

#### Casos de Uso Extendidos

**Flujo Principal - Consulta:**
1. Usuario ingresa nombre de tabla
2. Usuario ingresa condición WHERE (opcional)
3. Usuario selecciona ambientes origen/destino
4. Usuario presiona "Consultar datos a migrar"
5. Sistema ejecuta SELECT en thread
6. Sistema muestra datos en grid (primeros 100)
7. Sistema muestra total de registros
8. Sistema habilita botón "Migrar"

**Flujo Principal - Migración:**
1. Usuario presiona "Migrar"
2. Sistema solicita confirmación
3. Usuario confirma
4. Sistema inicia thread de migración
5. Sistema deshabilita triggers
6. Sistema extrae datos en lotes
7. Sistema inserta cada lote
8. Sistema actualiza progreso
9. Sistema re-habilita triggers
10. Sistema muestra resumen
11. Sistema guarda en historial

**Flujos Alternativos:**

- **FA-1:** Si consulta falla (tabla no existe) → Mostrar error, no habilitar Migrar
- **FA-2:** Si conexión se pierde → Rollback, re-habilitar triggers, mostrar error
- **FA-3:** Si usuario cancela → Detener extracción, rollback lo insertado, re-habilitar triggers
- **FA-4:** Si hay errores de inserción → Continuar con siguiente lote, contar como omitidos
- **FA-5:** Si 0 registros insertados → Mostrar advertencia sobre posibles duplicados o desconexión

#### Definición de Terminado

- [ ] Consulta preview funcional en thread
- [ ] Grid muestra primeros 100 registros correctamente
- [ ] Migración en thread no bloquea UI
- [ ] Triggers se deshabilitan/habilitan correctamente
- [ ] Batch processing de 5000 registros funcional
- [ ] Progreso se actualiza en tiempo real
- [ ] Cancelación detiene thread y hace rollback
- [ ] Manejo de errores robusto (red, duplicados, permisos)
- [ ] Historial se guarda correctamente
- [ ] Pruebas unitarias > 85% cobertura
- [ ] Pruebas de integración con BD mock

#### Estimación

**Story Points:** 13  
**Prioridad:** Crítica  
**Sprint:** 4-5

#### Dependencias

- `Migracion.py` (UI principal)
- `migrar_tabla.py` (lógica de migración)
- `ambientes.json` (configuración de ambientes)

#### Notas Técnicas

```python
# Función principal de migración:

def migrar_tabla(tabla, where, amb_origen, amb_destino, 
                 log, progress, abort, columnas, cancelar_func):
    """
    Migración secuencial con manejo de triggers y batch processing
    """
    try:
        # Conectar a destino
        conn_dest = conectar_ambiente(amb_destino)
        cursor_dest = conn_dest.cursor()
        
        # CRÍTICO: Deshabilitar triggers
        _manage_trigger(cursor_dest, tabla, "DISABLE", log)
        
        # Conectar a origen y extraer datos
        conn_orig = conectar_ambiente(amb_origen)
        cursor_orig = conn_orig.cursor()
        
        query = f"SELECT * FROM {tabla}"
        if where:
            query += f" WHERE {where}"
        
        cursor_orig.execute(query)
        
        # Migrar en lotes
        insertados = 0
        omitidos = 0
        
        while True:
            if cancelar_func():
                log("⚠️ Migración cancelada por usuario")
                conn_dest.rollback()
                break
            
            lote = cursor_orig.fetchmany(5000)
            if not lote:
                break
            
            # Insertar lote
            for registro in lote:
                try:
                    cursor_dest.execute(
                        f"INSERT INTO {tabla} VALUES ({','.join(['?']*len(registro))})",
                        registro
                    )
                    insertados += 1
                except Exception as e:
                    omitidos += 1
            
            # Commit cada lote
            conn_dest.commit()
            
            # Actualizar progreso
            progress(insertados, total_registros)
        
        # Commit final
        conn_dest.commit()
        log(f"✅ Migración completada: {insertados} insertados, {omitidos} omitidos")
        
    except Exception as e:
        log(f"❌ Error: {str(e)}")
        conn_dest.rollback()
    
    finally:
        # CRÍTICO: Siempre re-habilitar triggers
        _manage_trigger(cursor_dest, tabla, "ENABLE", log)
        cursor_dest.close()
        conn_dest.close()

def _manage_trigger(cursor, tabla, accion, log_func=None):
    """
    Deshabilita/habilita triggers en una tabla
    
    Args:
        cursor: Cursor de BD activo
        tabla: Nombre de la tabla
        accion: "DISABLE" o "ENABLE"
        log_func: Función de logging (opcional)
    """
    if not tabla:
        return
    
    try:
        sql = f"ALTER TABLE {tabla} {accion} TRIGGER ALL"
        cursor.execute(sql)
        if log_func:
            log_func(f"🔧 Triggers {accion}D en {tabla}")
    except Exception as e:
        if log_func:
            log_func(f"⚠️ No se pudieron {accion} triggers: {str(e)}")
```

---

### US-011: Migración de Grupo de Tablas con Catálogo

**Como** usuario básico  
**Quiero** migrar múltiples tablas relacionadas como un grupo  
**Para** automatizar migraciones complejas y asegurar consistencia de datos

#### Criterios de Aceptación

- **Dado** que tengo un grupo de tablas configurado en `catalogo_migracion.json`
- **Cuando** selecciono el grupo y presiono "Migrar Grupo"
- **Entonces** el sistema:
  - Muestra las tablas del grupo con sus condiciones WHERE
  - Solicita valores para variables dinámicas (${variable})
  - Ejecuta migración de cada tabla secuencialmente
  - Muestra progreso global y por tabla
  - Permite cancelar en cualquier momento
  - Genera log consolidado de todo el grupo

#### Reglas de Negocio

- **RN-011.1:** **Catálogo JSON debe tener estructura:**
  ```json
  {
    "grupo": "Migración Transacciones ATM",
    "tablas": [
      {
        "tabla": "ca_transaccion",
        "where": "tr_fecha = '${fecha}' AND tr_estado = 'P'"
      },
      {
        "tabla": "ca_detalle",
        "where": "tr_fecha = '${fecha}'"
      }
    ],
    "variables": ["fecha"]
  }
  ```
- **RN-011.2:** **Variables dinámicas:**
  - Se solicitan al usuario antes de iniciar
  - Se reemplazan en todas las condiciones WHERE
  - Se validan para prevenir SQL injection (sanitización)
- **RN-011.3:** **Ejecución secuencial:** Tablas se migran una por una en el orden del catálogo
- **RN-011.4:** **Rollback parcial:** Si una tabla falla, se detiene el grupo (no continúa con siguientes)
- **RN-011.5:** **Threading:** Migración en thread separado

#### Casos de Uso Extendidos

**Flujo Principal:**
1. Usuario selecciona grupo del combo
2. Sistema muestra tablas del grupo en tree view
3. Sistema muestra campos para variables (si existen)
4. Usuario ingresa valores de variables
5. Usuario selecciona ambientes origen/destino
6. Usuario presiona "Migrar Grupo"
7. Sistema valida variables (sanitización)
8. Sistema solicita confirmación con preview
9. Usuario confirma
10. Sistema inicia thread de migración
11. Para cada tabla del grupo:
    - Reemplaza variables en WHERE
    - Ejecuta migración individual (US-010)
    - Actualiza progreso global
12. Sistema muestra resumen consolidado
13. Sistema guarda en historial

**Flujos Alternativos:**

- **FA-1:** Si variable está vacía → Mostrar error, no permitir migración
- **FA-2:** Si variable contiene caracteres peligrosos (`;`, `--`, `'`) → Sanitizar o rechazar
- **FA-3:** Si tabla del grupo falla → Detener migración, mostrar error, no continuar con siguientes
- **FA-4:** Si usuario cancela → Detener en tabla actual, no iniciar siguientes

#### Definición de Terminado

- [ ] Carga catálogo JSON correctamente
- [ ] Muestra tablas del grupo en UI
- [ ] Solicita variables dinámicas
- [ ] Reemplaza variables en WHERE
- [ ] Sanitiza variables (prevención SQL injection)
- [ ] Ejecuta migraciones secuencialmente
- [ ] Progreso global funcional
- [ ] Cancelación detiene en tabla actual
- [ ] Log consolidado generado
- [ ] Historial guardado
- [ ] Pruebas unitarias > 80%
- [ ] Pruebas de integración

#### Estimación

**Story Points:** 13  
**Prioridad:** Alta  
**Sprint:** 5-6

#### Dependencias

- US-010 (Migración de tabla) debe estar completa
- `migrar_grupo.py` (lógica)
- `json/catalogo_migracion.json` (configuración)

#### Notas Técnicas

```python
# Estrategia PEC (Preparar-Extraer-Cargar):

def migrar_grupo(grupo_conf, variables, amb_origen, amb_destino, 
                 log, progress, abort, cancelar_func):
    """
    Migración de grupo con variables dinámicas
    """
    # PREPARAR: Reemplazar variables
    tablas_preparadas = []
    for tabla_conf in grupo_conf['tablas']:
        where = tabla_conf['where']
        
        # Reemplazar cada variable
        for var_name, var_value in variables.items():
            # SEGURIDAD: Sanitizar valor
            var_value_safe = sanitizar_valor_sql(var_value)
            where = where.replace(f"${{{var_name}}}", var_value_safe)
        
        tablas_preparadas.append({
            'tabla': tabla_conf['tabla'],
            'where': where
        })
    
    # EXTRAER Y CARGAR: Migrar cada tabla
    total_tablas = len(tablas_preparadas)
    for i, tabla_prep in enumerate(tablas_preparadas):
        if cancelar_func():
            log("⚠️ Migración de grupo cancelada")
            break
        
        log(f"\n📊 Migrando tabla {i+1}/{total_tablas}: {tabla_prep['tabla']}")
        
        # Delegar a migración individual
        resultado = migrar_tabla_del_grupo(
            tabla_prep['tabla'],
            tabla_prep['where'],
            amb_origen,
            amb_destino,
            log,
            lambda p: progress((i/total_tablas)*100 + (p/total_tablas)),
            abort,
            cancelar_func
        )
        
        if not resultado['exito']:
            log(f"❌ Error en {tabla_prep['tabla']}, deteniendo grupo")
            break
    
    log("\n✅ Migración de grupo completada")

def sanitizar_valor_sql(valor):
    """
    Previene SQL injection eliminando caracteres peligrosos
    """
    # Eliminar caracteres peligrosos
    peligrosos = [';', '--', '/*', '*/', 'xp_', 'sp_', 'DROP', 'DELETE', 'TRUNCATE']
    valor_limpio = valor
    
    for char in peligrosos:
        valor_limpio = valor_limpio.replace(char, '')
    
    # Escapar comillas simples
    valor_limpio = valor_limpio.replace("'", "''")
    
    return valor_limpio
```

---

### US-012: Administrador de Grupos de Migración

**Como** usuario básico  
**Quiero** crear, editar y eliminar grupos de migración  
**Para** personalizar mis flujos de trabajo sin editar JSON manualmente

#### Criterios de Aceptación

- **Dado** que abro el administrador de grupos
- **Cuando** interactúo con la interfaz
- **Entonces** puedo:
  - **Crear nuevo grupo:** Ingresar nombre, agregar tablas, definir variables
  - **Editar grupo existente:** Modificar nombre, agregar/eliminar tablas, cambiar WHERE
  - **Eliminar grupo:** Borrar grupo completo del catálogo
  - **Guardar cambios:** Persistir en `catalogo_migracion.json`

#### Reglas de Negocio

- **RN-012.1:** Nombre de grupo debe ser único
- **RN-012.2:** Cada tabla debe tener nombre y WHERE (puede ser vacío)
- **RN-012.3:** Variables se detectan automáticamente buscando `${...}` en WHERE
- **RN-012.4:** Cambios se guardan inmediatamente al cerrar el administrador

#### Estimación

**Story Points:** 8  
**Prioridad:** Media  
**Sprint:** 6

---

### US-013: Ejecución de Scripts SQL Personalizados

**Como** usuario básico  
**Quiero** ejecutar un script SELECT personalizado para migración  
**Para** tener control total sobre la consulta de extracción

#### Criterios de Aceptación

- **Dado** que tengo un script SQL complejo
- **Cuando** selecciono "Migrar con Script SQL personalizado"
- **Entonces** puedo:
  - Ingresar script SELECT completo
  - Especificar tabla destino manualmente
  - Ejecutar preview de datos
  - Migrar con el script personalizado

#### Reglas de Negocio

- **RN-013.1:** Script debe comenzar con `SELECT`
- **RN-013.2:** No se permite `DELETE`, `UPDATE`, `DROP` en script
- **RN-013.3:** Columnas del script deben coincidir con tabla destino

#### Estimación

**Story Points:** 5  
**Prioridad:** Baja  
**Sprint:** 7

---

## Epic 5: Operaciones Administrativas de Base de Datos

### US-014: Desbloqueo de Usuario en Base de Datos

**Como** usuario básico  
**Quiero** liberar la sesión de un usuario bloqueado en la BD  
**Para** permitir que vuelva a acceder sin intervención del DBA

#### Criterios de Aceptación

- **Dado** que un usuario está bloqueado en la base de datos
- **Cuando** ingreso su nombre de usuario y presiono "Desbloquear"
- **Entonces** el sistema:
  - Ejecuta `sp_killsession` o equivalente
  - Libera la sesión del usuario
  - Muestra confirmación de éxito
  - Registra la operación en log

#### Reglas de Negocio

- **RN-014.1:** Debe validar que el usuario existe antes de ejecutar
- **RN-014.2:** Debe solicitar confirmación antes de ejecutar
- **RN-014.3:** Debe registrar quién realizó el desbloqueo y cuándo

#### Estimación

**Story Points:** 3  
**Prioridad:** Media  
**Sprint:** 5

---

### US-015: Autorización de Acceso a Tablas

**Como** usuario básico  
**Quiero** otorgar permisos de SELECT en una tabla a un usuario  
**Para** habilitar acceso a consultas sin involucrar al DBA

#### Criterios de Aceptación

- **Dado** que tengo una tabla y un usuario
- **Cuando** ejecuto "Autorizar Tabla"
- **Entonces** el sistema:
  - Ejecuta `GRANT SELECT ON <tabla> TO <usuario>`
  - Muestra confirmación de éxito
  - Registra la operación

#### Reglas de Negocio

- **RN-015.1:** Solo permisos de SELECT (no INSERT/UPDATE/DELETE)
- **RN-015.2:** Debe validar que tabla y usuario existen
- **RN-015.3:** Debe solicitar confirmación

#### Estimación

**Story Points:** 3  
**Prioridad:** Media  
**Sprint:** 5

---

### US-016: Actualización de Fecha de Contabilidad

**Como** usuario básico  
**Quiero** actualizar la fecha de contabilidad en una tabla de configuración  
**Para** sincronizar parámetros de procesamiento batch

#### Criterios de Aceptación

- **Dado** que tengo una nueva fecha de contabilidad
- **Cuando** ingreso la fecha y presiono "Actualizar"
- **Entonces** el sistema:
  - Valida formato de fecha (YYYY-MM-DD)
  - Ejecuta UPDATE en tabla de configuración
  - Muestra confirmación de éxito
  - Registra la operación

#### Reglas de Negocio

- **RN-016.1:** Fecha debe ser válida y no futura
- **RN-016.2:** Debe solicitar confirmación antes de actualizar
- **RN-016.3:** Debe mostrar fecha actual antes de cambiar

#### Estimación

**Story Points:** 3  
**Prioridad:** Baja  
**Sprint:** 6

---

### US-017: Verificación de Usuario No Vigente

**Como** usuario básico  
**Quiero** consultar el estado de vigencia de un usuario  
**Para** identificar usuarios inactivos o bloqueados

#### Criterios de Aceptación

- **Dado** que tengo un nombre de usuario
- **Cuando** consulto su estado
- **Entonces** el sistema:
  - Ejecuta query de estado
  - Muestra si está vigente, bloqueado o inactivo
  - Muestra fecha de último acceso
  - Muestra motivo de bloqueo (si aplica)

#### Reglas de Negocio

- **RN-017.1:** Debe consultar tabla de usuarios del sistema
- **RN-017.2:** Debe mostrar información clara y legible

#### Estimación

**Story Points:** 2  
**Prioridad:** Baja  
**Sprint:** 6

---

### US-018: Modificaciones Varias con Generación de Scripts

**Como** usuario básico  
**Quiero** generar scripts SQL de UPDATE/INSERT/DELETE  
**Para** preparar modificaciones que serán revisadas antes de ejecutar

#### Criterios de Aceptación

- **Dado** que tengo una operación de modificación (UPDATE/INSERT/DELETE)
- **Cuando** ingreso los parámetros y presiono "Generar Script"
- **Entonces** el sistema:
  - Genera el script SQL correspondiente
  - Muestra preview del script
  - Permite copiar al portapapeles
  - Opcionalmente permite ejecutar directamente

#### Reglas de Negocio

- **RN-018.1:** Script debe incluir comentarios con metadatos (fecha, usuario, propósito)
- **RN-018.2:** Debe validar sintaxis antes de generar
- **RN-018.3:** Debe solicitar confirmación doble para ejecutar DELETE

#### Estimación

**Story Points:** 5  
**Prioridad:** Media  
**Sprint:** 7

---

## Epic 6: Gestión de Configuración y Ambientes

### US-019: Configuración de Ambientes de Base de Datos

**Como** administrador  
**Quiero** configurar las conexiones a diferentes ambientes (PRU, DES, PRO)  
**Para** que el sistema pueda conectarse a las bases de datos correctas

#### Criterios de Aceptación

- **Dado** que abro el panel de ambientes
- **Cuando** agrego o edito un ambiente
- **Entonces** puedo ingresar:
  - Nombre del ambiente (PRU, DES, PRO)
  - Host/IP del servidor
  - Puerto
  - Tipo de BD (Sybase, SQL Server)
  - Usuario
  - Contraseña (encriptada)
  - Lista de bases de datos disponibles

#### Reglas de Negocio

- **RN-019.1:** Contraseñas deben almacenarse encriptadas en `ambientes.json`
- **RN-019.2:** Debe validar conexión antes de guardar ("Probar Conexión")
- **RN-019.3:** Debe permitir configurar drivers ODBC personalizados
- **RN-019.4:** Debe guardar cambios inmediatamente

#### Estimación

**Story Points:** 5  
**Prioridad:** Crítica  
**Sprint:** 1

---

### US-020: Relacionamiento de Ambientes para Búsqueda Inteligente

**Como** administrador  
**Quiero** configurar relaciones entre ambientes (ej: PRU relacionado con DES)  
**Para** optimizar la búsqueda inteligente de SPs en validación

#### Criterios de Aceptación

- **Dado** que tengo múltiples ambientes configurados
- **Cuando** abro el gestor de relaciones
- **Entonces** puedo:
  - Seleccionar un ambiente padre
  - Seleccionar ambientes hijos relacionados
  - Guardar relaciones en `ambientesrelacionados.json`
  - Usar estas relaciones en validación para búsqueda smart

#### Reglas de Negocio

- **RN-020.1:** Estructura JSON:
  ```json
  {
    "PRU": ["DES", "QA"],
    "DES": ["PRU"],
    "PRO": []
  }
  ```
- **RN-020.2:** Relaciones se usan en Fase 2 de validación (búsqueda smart)
- **RN-020.3:** Debe prevenir relaciones circulares

#### Estimación

**Story Points:** 5  
**Prioridad:** Alta  
**Sprint:** 2

---

### US-021: Gestión de Favoritos en Usuario Básico

**Como** usuario básico  
**Quiero** marcar funcionalidades como favoritas  
**Para** acceder rápidamente a las operaciones que uso frecuentemente

#### Criterios de Aceptación

- **Dado** que estoy en el dashboard de usuario básico
- **Cuando** hago clic en la estrella de una funcionalidad
- **Entonces** el sistema:
  - Marca la funcionalidad como favorita
  - Mueve la card al inicio del dashboard
  - Guarda preferencia en `Favoritos.json`
  - Restaura favoritos al iniciar sesión

#### Reglas de Negocio

- **RN-021.1:** Favoritos se guardan por usuario
- **RN-021.2:** Favoritos persisten entre sesiones
- **RN-021.3:** Debe permitir desmarcar favorito

#### Estimación

**Story Points:** 3  
**Prioridad:** Baja  
**Sprint:** 7

---

### US-022: Comparador de Archivos de Texto

**Como** usuario básico  
**Quiero** comparar dos archivos de texto lado a lado  
**Para** identificar diferencias en scripts o resultados

#### Criterios de Aceptación

- **Dado** que tengo dos archivos de texto
- **Cuando** abro el comparador
- **Entonces** veo:
  - Contenido de ambos archivos lado a lado
  - Líneas diferentes resaltadas
  - Contador de diferencias
  - Opción de exportar reporte de diferencias

#### Reglas de Negocio

- **RN-022.1:** Debe soportar archivos grandes (> 10MB)
- **RN-022.2:** Debe resaltar diferencias línea por línea
- **RN-022.3:** Debe mostrar números de línea

#### Estimación

**Story Points:** 5  
**Prioridad:** Baja  
**Sprint:** 8

---

### US-023: Historial de Consultas y Modificaciones

**Como** usuario básico  
**Quiero** ver el historial de mis operaciones  
**Para** auditar cambios y repetir operaciones exitosas

#### Criterios de Aceptación

- **Dado** que he realizado operaciones en el sistema
- **Cuando** abro el historial
- **Entonces** veo:
  - Lista de operaciones ordenadas por fecha (más reciente primero)
  - Tipo de operación (Migración, Consulta, Modificación)
  - Parámetros usados
  - Resultado (éxito/error)
  - Timestamp
  - Usuario que ejecutó

#### Reglas de Negocio

- **RN-023.1:** Historial se guarda en `HistorialConsultas.json` y `HistorialModificaciones.json`
- **RN-023.2:** Debe permitir filtrar por tipo y fecha
- **RN-023.3:** Debe permitir repetir operación desde historial

#### Estimación

**Story Points:** 5  
**Prioridad:** Media  
**Sprint:** 8

---

## Resumen de Priorización

### Sprint 1 (Crítico - Fundación)
- US-001: Login con roles
- US-002: Pantalla de bienvenida
- US-003: Cierre de sesión
- US-019: Configuración de ambientes

**Total: 12 Story Points**

### Sprint 2-3 (Crítico - Validación)
- US-004: Validación automatizada (13 SP)
- US-005: Edición manual de validación (3 SP)
- US-006: Reporte de validación (2 SP)
- US-020: Relacionamiento de ambientes (5 SP)

**Total: 23 Story Points**

### Sprint 3-4 (Crítico - Catalogación)
- US-007: Catalogación sin re-búsqueda (8 SP)
- US-008: Análisis de dependencias (5 SP)
- US-009: Detección de repetidos (3 SP)

**Total: 16 Story Points**

### Sprint 4-6 (Crítico - Migración)
- US-010: Migración de tabla (13 SP)
- US-011: Migración de grupo (13 SP)
- US-012: Administrador de grupos (8 SP)
- US-014: Desbloqueo de usuario (3 SP)
- US-015: Autorización de tablas (3 SP)

**Total: 40 Story Points**

### Sprint 7-8 (Media-Baja Prioridad)
- US-013: Scripts SQL personalizados (5 SP)
- US-016: Actualización fecha contabilidad (3 SP)
- US-017: Usuario no vigente (2 SP)
- US-018: Modificaciones varias (5 SP)
- US-021: Favoritos (3 SP)
- US-022: Comparador de archivos (5 SP)
- US-023: Historial (5 SP)

**Total: 28 Story Points**

---

## Métricas y KPIs

### Métricas de Producto

1. **Tiempo de Validación:** < 2 minutos para 50 archivos en 5 ambientes
2. **Tiempo de Catalogación:** < 1 minuto para 50 archivos
3. **Velocidad de Migración:** > 5000 registros/segundo
4. **Tasa de Éxito:** > 95% de migraciones sin errores
5. **Disponibilidad:** 99% uptime durante horarios laborales

### Métricas de Calidad

1. **Cobertura de Pruebas:** > 80% en código crítico
2. **Bugs en Producción:** < 5 bugs críticos por release
3. **Tiempo de Resolución:** < 24 horas para bugs críticos
4. **Satisfacción de Usuario:** > 4/5 en encuestas

---

## Glosario de Términos

- **SP:** Stored Procedure (procedimiento almacenado)
- **BD:** Base de Datos
- **db_override:** Base de datos detectada en validación, reutilizada en catalogación
- **Ambiente:** Entorno de base de datos (PRU, DES, PRO)
- **Trigger:** Disparador automático en base de datos
- **Batch Processing:** Procesamiento por lotes
- **Thread:** Hilo de ejecución paralelo
- **Callback:** Función de retorno para actualizar progreso

---

## Notas de Implementación

### Arquitectura Técnica

- **Framework UI:** tkinter + ttkbootstrap
- **BD:** pyodbc (Sybase ASE, SQL Server)
- **Threading:** threading.Thread para operaciones asíncronas
- **Persistencia:** JSON (configuración, historial, catálogos)
- **Logging:** Consola en tiempo real + archivos de salida

### Convenciones de Código

- **Naming:** snake_case para funciones, PascalCase para clases
- **Documentación:** Docstrings en todas las funciones públicas
- **Manejo de Errores:** try-except con logging detallado
- **Threading:** Siempre usar daemon=True y manejo de cancelación

### Seguridad

- **SQL Injection:** Sanitización de todas las entradas de usuario
- **Credenciales:** Encriptación de contraseñas en JSON
- **Validación:** Input validation en todos los formularios
- **Permisos:** Control de acceso basado en roles

---

**Fin del Documento de Especificaciones Funcionales**

*Última actualización: 17 de diciembre de 2025*
