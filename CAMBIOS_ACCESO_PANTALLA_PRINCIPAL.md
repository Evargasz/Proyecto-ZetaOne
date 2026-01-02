# Cambios: Acceso a Pantalla Principal Durante Migraciones

## Problema Original
Cuando se ejecutaba una migración (o "Modificaciones varias"), la aplicación bloqueaba completamente la pantalla principal usando `.grab_set()` y `.wait_window()`, impidiendo acceder a otras funcionalidades.

## Solución Implementada

### Cambios en `Usuario_basico/usu_basico_main.py`

#### 1. **Función `usar_migracion_de_datos()`**
- **Antes**: Usaba `.grab_set()` y `.wait_window()` para bloquear la UI
- **Después**: Usa callback con `.bind('<Destroy>', ...)` para reactibar el sidebar cuando se cierra

```python
# ANTES
def usar_migracion_de_datos(self):
    self.habilitar_sidebar(False)
    ventana_mig_datos = MigracionVentana(master=self.root)
    ventana_mig_datos.grab_set()
    ventana_mig_datos.wait_window()  # ❌ Bloquea la UI
    self.habilitar_sidebar(True)

# DESPUÉS
def usar_migracion_de_datos(self):
    self.habilitar_sidebar(False)
    ventana_mig_datos = MigracionVentana(master=self.root)
    # Configurar callback para cuando se cierre la ventana
    ventana_mig_datos.bind('<Destroy>', lambda e: self.habilitar_sidebar(True))
    # ✅ No bloquea, permite acceso a otras funciones
```

#### 2. **Función `usar_modificaciones_varias()`**
Cambio idéntico al anterior.

```python
# DESPUÉS
ventana_modificaciones = ModificacionesVariasVentana(self.root, ambientes_lista)
ventana_modificaciones.bind('<Destroy>', lambda e: self.habilitar_sidebar(True))
```

#### 3. **Función `usar_asistente_captura()`**
Cambio idéntico al anterior.

```python
# DESPUÉS
ventana_asistente = abrir_asistente_captura_modular(self.root)
ventana_asistente.bind('<Destroy>', lambda e: self.habilitar_sidebar(True))
```

### Cambios en `Usuario_basico/Migracion.py`

#### Función de Migración de Grupos
- **Antes**: `app.grab_set()` bloqueaba la ventana secundaria
- **Después**: Removido para permitir navegación

```python
# ANTES
app = MigracionGruposGUI(...)
app.grab_set()  # ❌ Bloquea

# DESPUÉS
app = MigracionGruposGUI(...)
# Removido grab_set() para permitir acceso a otras ventanas durante la migración
```

## Cómo Funciona Ahora

### Flujo de Uso

1. **Usuario hace clic en "Migración de datos"**
   - Se abre la ventana de migración
   - El sidebar se deshabilita (pero no bloquea la ventana)
   
2. **Durante la migración en ejecución**
   - El usuario puede hacer clic en "Pantalla Principal" u otras opciones del sidebar
   - La migración continúa en background
   - El usuario puede acceder a otras funcionalidades (como "Modificaciones varias")

3. **Al cerrar la ventana de migración**
   - El evento `<Destroy>` se dispara automáticamente
   - Se ejecuta el callback: `self.habilitar_sidebar(True)`
   - El sidebar se reactiva

### Navegación de Ventanas

**Importante**: Cada ventana de migración/modificación es independiente:
- Puedes abrir múltiples ventanas de migración simultáneamente
- Puedes cambiar entre ellas libremente
- Al cerrar cualquiera, vuelve a la pantalla principal (no a otra ventana abierta)

### Comportamiento del Cierre

Cuando una migración está en ejecución y intentas cerrar la ventana:

1. Se muestra un diálogo: **"Hay una migración en curso. ¿Deseas cancelarla y salir?"**
2. Si aceptas:
   - Se cancela la migración
   - Se espera a que los hilos terminen
   - Se cierra la ventana
3. Si rechazas:
   - La ventana permanece abierta
   - La migración continúa

## Ventajas de este Cambio

✅ **Mejor experiencia de usuario**: Acceso a pantalla principal sin bloqueos  
✅ **Migraciones paralelas**: Puedes hacer múltiples migraciones simultáneamente  
✅ **Flexibilidad**: Cambiar entre funcionalidades mientras se ejecutan tareas largas  
✅ **Sin pérdida de funcionalidad**: El cierre sigue siendo seguro y controlado  
✅ **Compatible**: No requiere cambios en la lógica de migración o base de datos

## Cambios Compilados

✅ `Usuario_basico/usu_basico_main.py` - Compilación exitosa  
✅ `Usuario_basico/Migracion.py` - Compilación exitosa  

## Próximos Pasos (Opcionales)

1. **Indicador visual**: Mostrar un pequeño badge en el sidebar indicando migraciones activas
2. **Tabla de tareas**: Mostrar lista de migraciones en ejecución en la pantalla principal
3. **Notificaciones**: Alertar cuando una migración se completa
