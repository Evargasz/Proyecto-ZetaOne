# Guía de Instalación - ZetaOne

## Versión 1.4.0

---

## Tabla de Contenidos

1. [Requisitos del Sistema](#requisitos-del-sistema)
2. [Instalación del Ejecutable](#instalación-del-ejecutable)
3. [Instalación desde Código Fuente](#instalación-desde-código-fuente)
4. [Configuración de Drivers ODBC](#configuración-de-drivers-odbc)
5. [Configuración de Ambientes](#configuración-de-ambientes)
6. [Estructura de Directorios](#estructura-de-directorios)
7. [Verificación de la Instalación](#verificación-de-la-instalación)
8. [Solución de Problemas](#solución-de-problemas)
9. [Desinstalación](#desinstalación)

---

## Requisitos del Sistema

### Hardware

- **Procesador:** Intel Core i3 o superior (32-bit o 64-bit)
- **RAM:** Mínimo 4 GB (recomendado 8 GB)
- **Disco Duro:** 
  - 500 MB para la aplicación
  - 2 GB adicionales para archivos de catalogación
- **Pantalla:** Resolución mínima 1280x720
- **Red:** Conexión a red corporativa con acceso a servidores Sybase/SQL Server

### Software

- **Sistema Operativo:** Windows 10 (build 1803 o superior) o Windows 11
- **Framework:** .NET Framework 4.7.2 o superior (usualmente incluido en Windows 10)
- **Permisos:** Derechos de administrador para instalación de drivers

### Dependencias de Red

- Acceso de red a servidores Sybase ASE
- Puertos abiertos (por defecto 7025, 7026, 7028, etc.)
- Conectividad ODBC funcional

---

## Instalación del Ejecutable

### Opción 1: Instalador Windows (Recomendado)

1. **Descargar el Instalador**
   
   Obtenga el archivo `ZetaOne_Setup_v1.4.0.exe` del repositorio o servidor de distribución.

2. **Ejecutar el Instalador**
   
   [IMAGEN: Inicio del instalador de ZetaOne]
   
   - Haga doble clic en `ZetaOne_Setup_v1.4.0.exe`
   - Si aparece advertencia de Windows Defender, haga clic en **Más información** → **Ejecutar de todas formas**

3. **Asistente de Instalación**
   
   [IMAGEN: Pantalla de bienvenida del asistente]
   
   - Haga clic en **Siguiente**
   - Acepte los términos de la licencia
   - Seleccione la carpeta de destino (por defecto: `C:\Program Files (x86)\ZetaOne`)
   - Haga clic en **Instalar**

4. **Progreso de Instalación**
   
   [IMAGEN: Barra de progreso de instalación]
   
   El instalador copiará:
   - Archivos ejecutables
   - Librerías Python
   - Drivers ODBC
   - Archivos de configuración
   - Iconos y recursos

5. **Finalización**
   
   [IMAGEN: Pantalla de finalización]
   
   - Marque **Crear acceso directo en el Escritorio**
   - Marque **Ejecutar ZetaOne ahora**
   - Haga clic en **Finalizar**

### Opción 2: Ejecutable Portable

1. **Descargar el Archivo ZIP**
   
   Descargue `ZetaOne_Portable_v1.4.0.zip`

2. **Extraer Archivos**
   
   - Extraiga el contenido a una carpeta (ej: `C:\ZetaOne`)
   - **No ejecute desde una unidad de red** (puede causar problemas de rendimiento)

3. **Ejecutar la Aplicación**
   
   - Navegue a la carpeta extraída
   - Ejecute `ZetaOne.exe`

---

## Instalación desde Código Fuente

### Para Desarrolladores y Personalizaciones Avanzadas

### Paso 1: Instalar Python

1. **Descargar Python 3.12 (32-bit)**
   
   - Visite [https://www.python.org/downloads/](https://www.python.org/downloads/)
   - Descargue **Python 3.12.x (32-bit)** → Windows installer (32-bit)
   
   > **IMPORTANTE:** Debe ser 32-bit para compatibilidad con drivers ODBC legacy

2. **Instalar Python**
   
   [IMAGEN: Instalador de Python con checkbox "Add to PATH"]
   
   - Ejecute el instalador
   - ✅ Marque **"Add Python 3.12 to PATH"**
   - Haga clic en **Install Now**
   - Espere a que finalice la instalación

3. **Verificar Instalación**
   
   Abra PowerShell y ejecute:
   
   ```powershell
   python --version
   ```
   
   Debe mostrar: `Python 3.12.x`

### Paso 2: Clonar el Repositorio

1. **Instalar Git** (si no está instalado)
   
   - Descargue desde [https://git-scm.com/download/win](https://git-scm.com/download/win)
   - Ejecute el instalador con opciones por defecto

2. **Clonar el Proyecto**
   
   ```powershell
   cd C:\Users\evargas\Documents\BAC\IA
   git clone <URL_DEL_REPOSITORIO> ZetaOne2
   cd ZetaOne2
   ```

### Paso 3: Crear Entorno Virtual

```powershell
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Si aparece error de ejecución de scripts:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Paso 4: Instalar Dependencias

```powershell
# Actualizar pip
python -m pip install --upgrade pip

# Instalar dependencias del proyecto
pip install -r requirements.txt
```

**Archivo requirements.txt:**

```
pyodbc==5.0.1
ttkbootstrap==1.10.1
Pillow==10.1.0
tkinterdnd2==0.4.3
cryptography==41.0.7
pyinstaller==6.3.0
```

### Paso 5: Configurar Drivers ODBC

Ver sección [Configuración de Drivers ODBC](#configuración-de-drivers-odbc)

### Paso 6: Ejecutar la Aplicación

```powershell
# Ejecutar desde código fuente
python ZLauncher.py
```

---

## Configuración de Drivers ODBC

### Driver de Sybase ASE (Incluido en el Proyecto)

El proyecto incluye el driver Sybase ASE ODBC en la carpeta `ODBC/`.

#### Instalación Manual del Driver

1. **Navegar a la Carpeta del Driver**
   
   ```
   C:\Users\evargas\Documents\BAC\IA\ZetaOne2\ODBC
   ```

2. **Ejecutar el Instalador** (si existe)
   
   Si existe un archivo `setup.exe` en la carpeta ODBC:
   
   - Ejecute `setup.exe` como Administrador
   - Siga el asistente de instalación
   - Seleccione instalación típica

3. **Verificar Instalación del Driver**
   
   [IMAGEN: Administrador de orígenes de datos ODBC]
   
   - Presione `Win + R`
   - Ejecute `odbcad32.exe`
   - Vaya a la pestaña **Drivers**
   - Busque **"Sybase ASE ODBC Driver"**
   
   [IMAGEN: Lista de drivers con Sybase ASE ODBC Driver resaltado]

#### Configuración Alternativa: Agregar Driver Manualmente

Si el driver no aparece automáticamente:

1. **Abrir Registro de Windows**
   
   ```powershell
   regedit
   ```

2. **Navegar a la Clave de Drivers**
   
   ```
   HKEY_LOCAL_MACHINE\SOFTWARE\ODBC\ODBCINST.INI\ODBC Drivers
   ```

3. **Agregar Entrada**
   
   - Clic derecho → Nuevo → Valor de cadena
   - Nombre: `Sybase ASE ODBC Driver`
   - Valor: `Installed`

4. **Configurar Parámetros del Driver**
   
   Crear clave:
   ```
   HKEY_LOCAL_MACHINE\SOFTWARE\ODBC\ODBCINST.INI\Sybase ASE ODBC Driver
   ```
   
   Agregar valores:
   - `Driver` (REG_SZ): `C:\ZetaOne\ODBC\dll\sybdrvodb.dll`
   - `Setup` (REG_SZ): `C:\ZetaOne\ODBC\dll\sybdrvodb.dll`

### Driver de SQL Server (Opcional)

Para conexiones a SQL Server:

1. **Descargar SQL Server Native Client 11.0**
   
   - Visite [Microsoft Download Center](https://www.microsoft.com/en-us/download/)
   - Busque "SQL Server Native Client 11.0"
   - Descargue el instalador correspondiente a su arquitectura (32-bit o 64-bit)

2. **Instalar**
   
   - Ejecute `sqlncli.msi`
   - Acepte los términos
   - Instalación completa

3. **Verificar**
   
   - Ejecute `odbcad32.exe`
   - Pestaña **Drivers**
   - Busque **"SQL Server Native Client 11.0"**

---

## Configuración de Ambientes

### Estructura del Archivo ambientes.json

1. **Navegar a la Carpeta JSON**
   
   ```
   C:\Users\evargas\Documents\BAC\IA\ZetaOne2\json\
   ```

2. **Editar ambientes.json**
   
   Abra con un editor de texto (Notepad++, VS Code, etc.):
   
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
     },
     {
       "nombre": "NUEVO_AMBIENTE",
       "ip": "192.168.1.100",
       "puerto": "5000",
       "usuario": "usuario_db",
       "clave": "password123",
       "base": "master",
       "driver": "Sybase ASE ODBC Driver"
     }
   ]
   ```

### Parámetros de Configuración

| Parámetro | Descripción | Ejemplo |
|-----------|-------------|---------|
| nombre | Identificador único del ambiente | "SYBCOB28" |
| ip | Dirección IP del servidor | "192.168.36.51" |
| puerto | Puerto de conexión | "7028" |
| usuario | Usuario de base de datos | "sa_cobis" |
| clave | Contraseña del usuario | "4dm1Nc0b1S" |
| base | Base de datos inicial | "cobis" |
| driver | Driver ODBC a usar | "Sybase ASE ODBC Driver" |

### Probar Conexión

1. **Ejecutar ZetaOne**
2. **Iniciar sesión como Administrador**
3. **Hacer clic en "Recargar Ambientes"**
4. **Seleccionar el nuevo ambiente**
5. **Hacer clic en "Probar Conexión"**

[IMAGEN: Mensaje de conexión exitosa]

---

## Estructura de Directorios

### Directorios del Sistema

El sistema creará automáticamente las siguientes carpetas:

```
C:\ZetaOne\
├── Catalogaciones\           # Resultados de catalogación
│   ├── cataloga20251217165729\
│   │   ├── SYBCOB28\
│   │   │   ├── AC\
│   │   │   └── SD\
│   │   └── resultado_catalogacion_20251217165729.txt
│   └── ...
│
└── Migraciones\              # Logs de migraciones
    ├── migracion20251217165729.log
    └── ...
```

### Directorios del Proyecto

```
C:\Users\evargas\Documents\BAC\IA\ZetaOne2\
├── json\                     # Configuración (EDITABLE)
│   ├── ambientes.json       # ← Configurar aquí
│   ├── usuarios.json
│   ├── config.json
│   └── catalogo_migracion.json
│
├── ODBC\                     # Drivers de BD (NO MODIFICAR)
│   └── dll\
│
├── imagenes_iconos\          # Recursos gráficos
│   └── ...
│
├── output\                   # Salidas temporales
│   └── ...
│
└── documentacion\            # Manuales
    ├── Manual_Usuario.md
    ├── Manual_Tecnico.md
    └── Instalacion.md
```

### Permisos Requeridos

- **Lectura/Escritura** en `C:\ZetaOne\`
- **Lectura** en la carpeta de instalación del proyecto
- **Ejecución** en `ZetaOne.exe`

---

## Verificación de la Instalación

### Checklist de Verificación

#### 1. Verificar Python (Solo para instalación desde código)

```powershell
python --version
# Debe mostrar: Python 3.12.x
```

#### 2. Verificar Dependencias

```powershell
pip list
# Debe incluir:
# - pyodbc
# - ttkbootstrap
# - tkinterdnd2
# - Pillow
```

#### 3. Verificar Driver ODBC

- Ejecutar `odbcad32.exe`
- Pestaña **Drivers**
- Buscar **"Sybase ASE ODBC Driver"**

[IMAGEN: Driver verificado en lista]

#### 4. Verificar Conectividad de Red

```powershell
# Probar ping al servidor
ping 192.168.36.51

# Probar puerto abierto (requiere telnet)
telnet 192.168.36.51 7028
```

#### 5. Ejecutar la Aplicación

- Ejecutar `ZetaOne.exe` (o `python ZLauncher.py`)
- Debe aparecer la pantalla de inicio

[IMAGEN: Pantalla de inicio de ZetaOne]

#### 6. Iniciar Sesión

- Usuario: `admin`
- Contraseña: `admin123`
- Debe cargar la interfaz de administrador

[IMAGEN: Interfaz de administrador]

#### 7. Probar Conexión a Ambiente

- Seleccionar un ambiente
- Hacer clic en **Probar Conexión**
- Debe mostrar mensaje de éxito

[IMAGEN: Mensaje "Conexión exitosa a SYBCOB28"]

### Registro de Errores

Si encuentra problemas, revise:

- **Consola de Python** (si ejecuta desde código)
- **Archivo zetaone.log** (en la carpeta del proyecto)
- **Visor de Eventos de Windows** → Registro de Aplicaciones

---

## Solución de Problemas

### Problema: Driver ODBC no encontrado

**Síntoma:**
```
pyodbc.Error: ('IM002', '[IM002] [Microsoft][ODBC Driver Manager] Data source name not found...')
```

**Solución:**

1. Verifique que el driver esté instalado:
   ```powershell
   odbcad32.exe
   ```

2. Si falta, instale manualmente desde `ODBC/dll/`

3. Agregue al PATH de Windows:
   ```powershell
   $env:PATH += ";C:\ZetaOne\ODBC\dll"
   ```

### Problema: Error de conexión a la base de datos

**Síntoma:**
```
Error de conexión: [08001] Unable to connect...
```

**Solución:**

1. Verifique credenciales en `json/ambientes.json`
2. Pruebe conectividad de red:
   ```powershell
   ping 192.168.36.51
   telnet 192.168.36.51 7028
   ```
3. Verifique que el usuario tenga permisos en la BD
4. Revise firewall de Windows

### Problema: tkinterdnd2 no funciona (Drag & Drop)

**Síntoma:**
- No se pueden arrastrar archivos a la interfaz

**Solución:**

```powershell
pip uninstall tkinterdnd2
pip install tkinterdnd2
```

Si persiste, use el método de selección manual de archivos.

### Problema: DLL no encontrada al ejecutar desde código

**Síntoma:**
```
ImportError: DLL load failed while importing _tkinter
```

**Solución:**

1. Reinstale Python 3.12 (32-bit)
2. Durante la instalación, marque **"tcl/tk and IDLE"**
3. Reinstale dependencias:
   ```powershell
   pip install --force-reinstall --no-cache-dir -r requirements.txt
   ```

### Problema: Aplicación se congela durante validación

**Síntoma:**
- La interfaz no responde
- Progreso se detiene

**Solución:**

1. Espere al menos 2 minutos (búsqueda exhaustiva puede ser lenta)
2. Si persiste, cierre la aplicación con `Ctrl+Alt+Supr`
3. Verifique la red (puede estar lenta)
4. Reduzca cantidad de archivos a validar

### Problema: Permisos insuficientes en C:\ZetaOne

**Síntoma:**
```
PermissionError: [Errno 13] Permission denied: 'C:\\ZetaOne\\...'
```

**Solución:**

1. Ejecute ZetaOne como Administrador:
   - Clic derecho en `ZetaOne.exe`
   - **Ejecutar como administrador**

2. Cambie permisos de la carpeta:
   - Clic derecho en `C:\ZetaOne`
   - **Propiedades** → **Seguridad**
   - **Editar** → Agregar permisos de escritura para su usuario

### Problema: Error de encoding UTF-8

**Síntoma:**
```
UnicodeDecodeError: 'utf-8' codec can't decode byte...
```

**Solución:**

1. Asegúrese de que los archivos .sp estén en UTF-8
2. Si tiene archivos en ANSI/Latin-1:
   - Ábralos con Notepad++
   - **Codificación** → **Convertir a UTF-8**
   - Guarde

---

## Desinstalación

### Método 1: Desinstalador Windows

1. **Panel de Control**
   
   - Abra **Panel de Control**
   - Vaya a **Programas** → **Programas y características**
   - Busque **ZetaOne**
   - Haga clic derecho → **Desinstalar**

2. **Seguir el Asistente**
   
   [IMAGEN: Asistente de desinstalación]
   
   - Confirme la desinstalación
   - Espere a que finalice

### Método 2: Eliminación Manual

1. **Eliminar Carpeta del Programa**
   
   ```powershell
   Remove-Item -Recurse -Force "C:\Program Files (x86)\ZetaOne"
   ```

2. **Eliminar Datos de Usuario**
   
   ```powershell
   Remove-Item -Recurse -Force "C:\ZetaOne"
   ```

3. **Eliminar Accesos Directos**
   
   - Escritorio: `C:\Users\<usuario>\Desktop\ZetaOne.lnk`
   - Menú Inicio: `C:\ProgramData\Microsoft\Windows\Start Menu\Programs\ZetaOne`

4. **Eliminar Configuración de Usuario** (Opcional)
   
   ```powershell
   Remove-Item -Recurse -Force "$env:APPDATA\ZetaOne"
   ```

### Limpieza de Registro (Opcional)

```powershell
# Abrir Editor de Registro
regedit
```

Eliminar claves:
```
HKEY_LOCAL_MACHINE\SOFTWARE\ZetaOne
HKEY_CURRENT_USER\SOFTWARE\ZetaOne
```

---

## Actualización de Versiones

### Actualizar desde Ejecutable

1. **Desinstalar versión anterior** (conservar datos en `C:\ZetaOne`)
2. **Instalar nueva versión** desde el instalador
3. **Verificar configuración** en `json/ambientes.json`

### Actualizar desde Código Fuente

```powershell
# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Actualizar código
git pull origin main

# Actualizar dependencias
pip install --upgrade -r requirements.txt

# Ejecutar
python ZLauncher.py
```

---

## Notas de Seguridad

### Protección de Credenciales

El archivo `json/ambientes.json` contiene credenciales en texto plano. Recomendaciones:

1. **Restringir permisos del archivo**
   ```powershell
   icacls "C:\ZetaOne2\json\ambientes.json" /grant:r "$env:USERNAME:(R)"
   ```

2. **Cifrar el disco** (BitLocker)

3. **No compartir el archivo** por correo o redes públicas

### Firewall

Configure excepciones de firewall para:
- `ZetaOne.exe`
- `python.exe` (si ejecuta desde código)

---

## Soporte Técnico

Para asistencia adicional:

- **Documentación:** Consulte los manuales en `documentacion/`
- **Logs:** Revise `zetaone.log` en la carpeta del proyecto
- **Contacto:** [contacto del equipo de desarrollo]

---

**Fin de la Guía de Instalación**

**Versión:** 1.4.0  
**Última Actualización:** Diciembre 2024
