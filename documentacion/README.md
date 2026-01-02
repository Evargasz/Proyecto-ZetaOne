# Documentación del Proyecto ZetaOne

## Versión 1.4.0

---

## Índice de Documentación

Esta carpeta contiene la documentación completa del sistema ZetaOne para catalogación, validación y migración de procedimientos almacenados en ambientes Sybase ASE y SQL Server.

---

## Documentos Disponibles

### 1. [Manual de Usuario](Manual_Usuario.md)

**Audiencia:** Usuarios finales (administradores y usuarios básicos)

**Contenido:**
- Introducción al sistema
- Requisitos del sistema
- Autenticación y navegación
- Módulo de Administrador:
  - Gestión de ambientes
  - Carga de archivos (Drag & Drop)
  - Validación de archivos con búsqueda inteligente
  - Catalogación automática
  - Detección de SPs repetidos
  - Catalogación de frontend
- Módulo de Usuario Básico:
  - Migración de datos (tabla individual y grupos)
  - Modificaciones varias (UPDATEs controlados)
  - Otras funcionalidades (desbloqueo, autorizaciones, etc.)
- Gestión de archivos de resultado
- Solución de problemas
- Preguntas frecuentes

**Uso:** Guía paso a paso para operar el sistema

---

### 2. [Manual Técnico](Manual_Tecnico.md)

**Audiencia:** Desarrolladores, arquitectos y personal técnico

**Contenido:**
- Arquitectura del sistema (3 capas)
- Tecnologías utilizadas (Python 3.12, tkinter, pyodbc)
- Estructura del proyecto
- Módulos principales:
  - ZLauncher y orquestador
  - Usuario Administrador
  - Usuario Básico
  - Conectividad de datos
- Flujo de validación detallado
- Flujo de catalogación detallado
- Algoritmo de búsqueda inteligente de bases de datos
- Sistema de callbacks y progreso en tiempo real
- Manejo de errores y logging
- Configuración y archivos JSON
- API y funciones principales
- Extensión y personalización
- Testing y depuración

**Uso:** Referencia técnica para desarrollo y mantenimiento

---

### 3. [Guía de Instalación](Instalacion.md)

**Audiencia:** Administradores de sistemas y usuarios técnicos

**Contenido:**
- Requisitos del sistema (hardware y software)
- Instalación del ejecutable (instalador Windows y portable)
- Instalación desde código fuente:
  - Instalación de Python 3.12 (32-bit)
  - Clonación del repositorio
  - Creación de entorno virtual
  - Instalación de dependencias
- Configuración de drivers ODBC:
  - Sybase ASE ODBC Driver
  - SQL Server Native Client
- Configuración de ambientes (edición de JSON)
- Estructura de directorios
- Verificación de la instalación (checklist completo)
- Solución de problemas comunes
- Desinstalación y actualización

**Uso:** Guía completa para instalar y configurar el sistema

---

### 4. [Arquitectura del Sistema](Arquitectura.md)

**Audiencia:** Arquitectos de software, diseñadores de sistemas

**Contenido:**
- Visión general del sistema
- Arquitectura de alto nivel (diagrama de capas)
- Componentes del sistema:
  - Launcher y orquestador
  - Módulo de autenticación
  - Usuario Administrador
  - Usuario Básico
  - Conectividad de datos
- Patrones de diseño:
  - MVC (Modelo-Vista-Controlador)
  - Observer (Callbacks)
  - Strategy (Búsqueda de BD)
  - Template Method (Migración)
  - Singleton (Configuración)
- Flujo de datos (diagramas de secuencia)
- Modelo de datos (entidades y relaciones)
- Seguridad:
  - Autenticación
  - Conexiones de BD
  - Prevención de inyección SQL
  - Permisos de archivos
- Rendimiento y escalabilidad:
  - Threading
  - Búsqueda optimizada
  - Batch processing
  - Caché de conexiones
- Decisiones de diseño y justificaciones

**Uso:** Comprensión profunda del diseño y arquitectura

---

## Convenciones de Documentación

### Placeholders para Imágenes

Los documentos incluyen marcadores `[IMAGEN: descripción]` donde se deben insertar capturas de pantalla. Ejemplos:

```markdown
[IMAGEN: Pantalla de inicio con logo ZetaOne y botones]
[IMAGEN: Ventana de validación con barra de progreso]
[IMAGEN: Diagrama de componentes del sistema]
```

**Para agregar imágenes:**

1. Cree la carpeta `documentacion/imagenes/`
2. Guarde las capturas con nombres descriptivos:
   ```
   pantalla_inicio.png
   ventana_validacion.png
   diagrama_componentes.png
   ```
3. Reemplace los placeholders con referencias Markdown:
   ```markdown
   ![Pantalla de inicio](imagenes/pantalla_inicio.png)
   ```

### Formato de Código

Los bloques de código usan sintaxis Markdown con resaltado:

```python
def funcion_ejemplo():
    """Docstring"""
    return True
```

```json
{
  "nombre": "valor"
}
```

### Tablas

Las tablas usan formato Markdown estándar:

| Columna 1 | Columna 2 |
|-----------|-----------|
| Valor 1   | Valor 2   |

---

## Conversión a Word/PDF

### Usando Pandoc (Recomendado)

**Instalación:**

```powershell
# Instalar Pandoc
choco install pandoc

# Instalar LaTeX (para PDF)
choco install miktex
```

**Conversión a Word:**

```powershell
cd documentacion

# Convertir Manual de Usuario
pandoc Manual_Usuario.md -o Manual_Usuario.docx

# Convertir todos los documentos
pandoc Manual_Usuario.md -o Manual_Usuario.docx
pandoc Manual_Tecnico.md -o Manual_Tecnico.docx
pandoc Instalacion.md -o Instalacion.docx
pandoc Arquitectura.md -o Arquitectura.docx
```

**Conversión a PDF:**

```powershell
pandoc Manual_Usuario.md -o Manual_Usuario.pdf --pdf-engine=xelatex
```

**Con tabla de contenidos y numeración:**

```powershell
pandoc Manual_Usuario.md -o Manual_Usuario.docx --toc --number-sections
```

### Usando Visual Studio Code

**Extensiones:**

1. **Markdown PDF** (yzane.markdown-pdf)
2. **Markdown Preview Enhanced** (shd101wyy.markdown-preview-enhanced)

**Pasos:**

1. Abrir archivo `.md` en VS Code
2. Presionar `Ctrl+Shift+P`
3. Buscar "Markdown PDF: Export (pdf)"
4. Seleccionar destino

### Usando Microsoft Word

**Importación directa:**

1. Abrir Microsoft Word
2. **Archivo** → **Abrir**
3. Seleccionar archivo `.md`
4. Word convertirá automáticamente el formato
5. Guardar como `.docx`

**Nota:** Puede requerir ajustes manuales de formato

---

## Versionado de Documentación

### Control de Versiones

Cada documento incluye:

```markdown
## Versión 1.4.0
**Última Actualización:** Diciembre 2024
```

### Registro de Cambios

Al actualizar la documentación:

1. Incrementar número de versión
2. Actualizar fecha
3. Agregar sección "Historial de Cambios" (opcional):

```markdown
### Historial de Cambios

#### Versión 1.4.0 (Diciembre 2024)
- Agregado: Algoritmo de búsqueda inteligente de BD
- Agregado: Sistema de callbacks para progreso en tiempo real
- Modificado: Flujo de catalogación (sin re-búsqueda)
- Corregido: Validación de fase 2/2 con progreso correcto

#### Versión 1.3.0 (Noviembre 2024)
- Agregado: Detección de SPs repetidos
- Agregado: Catalogación de frontend
```

---

## Mantenimiento de la Documentación

### Responsabilidades

- **Desarrolladores:** Actualizar Manual Técnico tras cambios de código
- **QA/Testers:** Verificar Manual de Usuario con flujos reales
- **Administradores:** Actualizar Guía de Instalación con nuevos requisitos
- **Arquitectos:** Actualizar Arquitectura con decisiones de diseño

### Frecuencia de Actualización

- **Cada release mayor:** Revisión completa de todos los documentos
- **Cada release menor:** Actualización de secciones afectadas
- **Cada cambio crítico:** Actualización inmediata de documento relevante

---

## Estructura de la Carpeta

```
documentacion/
├── README.md                    # Este archivo (índice)
├── Manual_Usuario.md            # Guía para usuarios finales
├── Manual_Tecnico.md            # Referencia técnica
├── Instalacion.md               # Guía de instalación
├── Arquitectura.md              # Diseño del sistema
│
└── imagenes/                    # Capturas de pantalla (agregar)
    ├── pantalla_inicio.png
    ├── ventana_validacion.png
    ├── diagrama_componentes.png
    └── ...
```

---

## Contacto y Contribuciones

Para reportar errores en la documentación o sugerir mejoras:

- **Repositorio:** [URL del repositorio]
- **Issues:** [URL de issues]
- **Contacto:** [Email del equipo]

---

## Licencia

[Especificar licencia del proyecto]

---

**Generado por:** GitHub Copilot  
**Fecha de Generación:** Diciembre 2024  
**Versión del Sistema:** 1.4.0
