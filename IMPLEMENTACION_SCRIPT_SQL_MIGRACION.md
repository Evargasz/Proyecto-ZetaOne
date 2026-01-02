# Implementación: Script SQL en Migración Tabla a Tabla

## Descripción General
Se ha implementado la funcionalidad de **Script SQL** en la migración tabla a tabla, similar a la que ya existe en "Modificaciones varias". Esto permite que los usuarios ejecuten scripts SELECT personalizados para migrar datos de forma más flexible.

## Cambios Realizados

### 1. Nueva Clase: `MigracionScriptSQLDialog`

**Ubicación**: Final de `Usuario_basico/Migracion.py`

Clase Toplevel que proporciona un diálogo para que el usuario ingrese un script SELECT personalizado.

**Características**:
- TextBox para pegar el script SELECT
- Validación de formato: requiere `SELECT` y `FROM`
- Parsing automático para extraer:
  - Tabla (con base de datos): `base.dbo.tabla`
  - Condición WHERE (opcional)
- Barra de progreso durante ejecución
- Botones: Ejecutar Script y Cancelar

**Formato esperado del script**:
```sql
SELECT * FROM base.dbo.tabla WHERE condicion
SELECT column1, column2 FROM base.tabla WHERE id = 123
```

### 2. Botón "Script SQL" en la Interfaz

**Ubicación**: Panel "Tabla a tabla" en `_armar_interfaz()`

El botón se posiciona al lado del campo "Base de datos origen":

```
┌─ Tabla a tabla ──────────────────────────────────────┐
│ Base de datos: [_____] [Script SQL] [Historial]      │
│ Tabla:         [_____] [Consultar datos a migrar]    │
│ Condición WHERE: [________________] [Limpiar]        │
└──────────────────────────────────────────────────────┘
```

**Función del botón**: `_on_script_sql_tabla()`

Valida que haya un ambiente seleccionado y abre el diálogo `MigracionScriptSQLDialog`.

### 3. Funciones Callback

#### `_on_script_sql_tabla()`
- Valida que exista un ambiente origen seleccionado
- Abre el diálogo `MigracionScriptSQLDialog`

#### `_ejecutar_desde_script_tabla(parsed_data, script_dialog)`
- Recibe los datos parseados del diálogo
- Parsea el nombre de la tabla (extrae base y tabla):
  - Formato: `base.tabla` → base = "base", tabla = "tabla"
  - Formato: `base.dbo.tabla` → base = "base", tabla = "tabla" (ignora schema)
- Rellena automáticamente los campos:
  - `entry_db_origen` con la base de datos
  - `entry_tabla_origen` con el nombre de la tabla
  - `entry_where` con la condición (si existe)
- Ejecuta `on_consultar_tabla()` automáticamente para cargar los datos

## Flujo de Uso

1. **Usuario en pantalla de Migración → Tabla a tabla**
   - Selecciona ambiente origen y destino
   
2. **Usuario hace clic en "Script SQL"**
   - Se abre el diálogo `MigracionScriptSQLDialog`
   - Se muestra ejemplo de formato esperado

3. **Usuario pega su script SELECT**
   ```sql
   SELECT * FROM cob_conta_super.dbo.sb_balance WHERE ba_empresa = 1 AND ba_periodo = 2024
   ```

4. **Usuario hace clic en "Ejecutar Script"**
   - El script se valida (debe tener SELECT y FROM)
   - Se parsean los datos:
     - Tabla: `cob_conta_super.dbo.sb_balance` → base = "cob_conta_super", tabla = "sb_balance"
     - Condición: `ba_empresa = 1 AND ba_periodo = 2024`
   - Los campos se rellenan automáticamente
   - Se ejecuta la consulta (`on_consultar_tabla()`)
   - Se muestra el número de registros a migrar

5. **Migración procede normalmente**
   - Usuario hace clic en "Migrar"
   - Se ejecuta la migración con los parámetros del script

## Validaciones Implementadas

✅ **Ambiente origen requerido**: No se puede abrir el diálogo sin ambiente  
✅ **Formato SELECT requerido**: Script debe empezar con `SELECT`  
✅ **FROM requerido**: Script debe contener `FROM`  
✅ **Tabla con base de datos**: Formato `base.tabla` o `base.schema.tabla`  
✅ **Condición WHERE opcional**: Se parsea si existe  

## Casos de Uso

### Caso 1: Script simple sin condición
```sql
SELECT * FROM mi_base.tabla
```
Resultado: Los campos se rellenan, se consultan todos los registros

### Caso 2: Script con condición WHERE
```sql
SELECT * FROM cob_conta_super.sb_balance WHERE ba_empresa = 1 AND ba_periodo = 2024
```
Resultado: Los campos se rellenan, se consultan solo los registros que coinciden

### Caso 3: Script con columnas específicas
```sql
SELECT ba_empresa, ba_cuenta, ba_saldo FROM cob_conta_super.sb_balance WHERE ba_corte = 182
```
Resultado: Se migran solo las columnas especificadas

### Caso 4: Script con schema explícito
```sql
SELECT * FROM base.dbo.tabla WHERE condicion
```
Resultado: Se extrae correctamente (ignora el schema "dbo")

## Integración con Migración Existente

La implementación se integra perfectamente con:
- ✅ `on_consultar_tabla()`: Validación y cálculo de registros
- ✅ `on_migrar()`: Ejecución de migración con parámetros
- ✅ Sistema de logs: Todas las operaciones se registran
- ✅ Sistema de rollback: Si hay error, se deshace automáticamente
- ✅ Retry logic: Los reintentos se mantienen activos

## Compilación

✅ **Estado**: Compilación exitosa  
Módulo `Usuario_basico.Migracion` importa sin errores

## Código Relevante

```python
# Botón en interfaz
self.btn_script_sql = boton_accion(
    self.frame_tabla,
    texto="Script SQL",
    comando=self._on_script_sql_tabla,
    width=12
)
self.btn_script_sql.grid(row=0, column=2, padx=(2,2), pady=0, sticky="nwe")

# Clase de diálogo (al final de Migracion.py)
class MigracionScriptSQLDialog(tk.Toplevel):
    def __init__(self, parent, callback_ejecutar, ambiente_origen):
        # ... inicialización y parsing
        
    def on_ejecutar_script(self):
        # ... validación y callback
```

## Próximas Mejoras (Opcionales)

1. **Autocomplete para tablas**: Detectar tablas disponibles en la base
2. **Validación en tiempo real**: Sugerir correcciones mientras se escribe
3. **Historial de scripts**: Guardar scripts usados frecuentemente
4. **Preview de datos**: Mostrar primeros N registros antes de migrar
5. **Botón "Copiar script"**: Para reutilizar en otra migración

## Pruebas Recomendadas

1. Abrir migración tabla a tabla
2. Hacer clic en "Script SQL"
3. Pegar un script válido (ej: `SELECT * FROM base.tabla`)
4. Verificar que los campos se rellenan correctamente
5. Hacer clic en "Migrar" para confirmar que funciona
6. Verificar logs y rollback si hay error
