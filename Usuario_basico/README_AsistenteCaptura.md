# 📸 Asistente de Captura y Grabación - ZetaOne

## 🎯 Descripción
El **Asistente de Captura y Grabación** es una funcionalidad integrada en ZetaOne que permite capturar pantallas y grabar videos de aplicaciones específicas de forma automatizada.

## ✨ Características Principales

### 📸 Capturador de Pantallas
- **Captura selectiva** de ventanas específicas
- **Captura combinada** de múltiples aplicaciones
- **Captura de pantalla completa**
- **Generación automática** de documentos Word con las capturas
- **Activación con tecla F8**
- **Organización automática** en carpetas por aplicación

### 🎥 Grabador de Video
- **Grabación de ventanas específicas**
- **Grabación de pantalla completa**
- **Pausa automática** cuando la aplicación pierde el foco
- **Activación con tecla F9**
- **Formato MP4** con compresión optimizada

### ⚙️ Editor de Objetivos
- **Configuración personalizable** de aplicaciones objetivo
- **Títulos de ventana exactos** para mejor detección
- **Guardado automático** en config.json
- **Interfaz intuitiva** de edición

## 🔧 Instalación de Dependencias

### Opción 1: Script Automático
Ejecuta el archivo `instalar_dependencias_captura.bat` desde la carpeta raíz del proyecto.

### Opción 2: Manual
```bash
# Para captura de pantallas
pip install pyautogui keyboard python-docx pywinauto pillow

# Para grabación de video
pip install opencv-python mss pygetwindow pywin32
```

## 🚀 Uso

### Acceso
1. Abre ZetaOne como **Usuario Básico**
2. Busca la card **"Asistente de captura y grabación"**
3. Haz clic en **"Usar"**

### Captura de Pantallas
1. Selecciona el **objetivo** en el dropdown
2. Haz clic en **"Activar Capturador (F8)"**
3. Presiona **F8** para tomar capturas
4. Presiona **ESC** para desactivar el capturador

### Grabación de Video
1. Selecciona el **objetivo** en el dropdown
2. Haz clic en **"Iniciar Grabación (F9)"**
3. Presiona **F9** nuevamente para detener
4. El video se guarda automáticamente en la carpeta `grabaciones/`

### Editar Objetivos
1. Haz clic en **"Editar Objetivos"**
2. Añade o modifica los títulos de ventana (uno por línea)
3. Haz clic en **"Guardar"**

## 📁 Estructura de Archivos Generados

```
ZetaOne/
├── capturas_sistema_de_cartera/
│   ├── captura_001.png
│   ├── captura_002.png
│   └── ...
├── pantallazos_sistema_de_cartera.docx
├── grabaciones/
│   ├── grabacion_2024-01-15_14-30-25.mp4
│   └── ...
└── json/
    └── config.json (objetivos configurados)
```

## ⚡ Teclas de Acceso Rápido

| Tecla | Función |
|-------|---------|
| **F8** | Tomar captura de pantalla |
| **F9** | Iniciar/Detener grabación de video |
| **ESC** | Desactivar capturador (solo en modo captura) |

## 🎛️ Configuración Avanzada

### Objetivos Predeterminados
- Sistema de Cartera
- C O B I S  Clientes  
- C.O.B.I.S TERMINAL ADMINISTRATIVA

### Personalización
Puedes añadir cualquier aplicación editando los objetivos. El título debe coincidir **exactamente** con el título de la ventana.

**Ejemplos de títulos válidos:**
- `Sistema de Cartera`
- `Google Chrome`
- `Microsoft Word - Documento1`
- `Calculadora`

## 🔍 Solución de Problemas

### "Funcionalidad no disponible. Faltan dependencias"
- Ejecuta `instalar_dependencias_captura.bat`
- O instala manualmente las librerías requeridas

### "No se encontró la ventana"
- Verifica que la aplicación esté abierta
- Comprueba que el título en "Objetivos" sea exacto
- La ventana no debe estar minimizada

### "Error en captura/grabación"
- Cierra y vuelve a abrir la aplicación objetivo
- Verifica que tengas permisos de escritura en la carpeta
- Comprueba que no haya otro software de captura activo

## 🔒 Consideraciones de Seguridad

- Las capturas se guardan **localmente** en tu equipo
- No se envía información a servidores externos
- Los archivos generados quedan bajo tu control total
- Respeta las políticas de privacidad de tu organización

## 🆘 Soporte

Si encuentras problemas:
1. Verifica que todas las dependencias estén instaladas
2. Comprueba el log de actividad en la ventana del asistente
3. Asegúrate de que las aplicaciones objetivo estén abiertas y visibles

---
*Integrado en ZetaOne v1.3+ | Desarrollado para optimizar la documentación de procesos bancarios*