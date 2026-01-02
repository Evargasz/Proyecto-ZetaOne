"""
Capturador Híbrido de Pantallas para Documentación ZetaOne
- Automático: Captura ventanas simples sin dependencias
- Manual Asistido: Abre cada ventana y espera que presiones tecla para capturar
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
from pathlib import Path
from PIL import ImageGrab, Image
import time
import subprocess

# Agregar ruta para importar módulos de ZetaOne
sys.path.insert(0, str(Path(__file__).parent.parent))


class CapturadorHibrido:
    """Captura pantallas automáticamente o con asistencia manual"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent / "imagenes"
        self.capturas_realizadas = []
        self.errores = []
        
    def crear_estructura_carpetas(self):
        """Crea la estructura de carpetas para las imágenes"""
        carpetas = [
            "01_pantalla_inicio",
            "02_autenticacion",
            "03_admin_principal",
            "04_validacion",
            "05_catalogacion",
            "06_basico",
            "07_diagramas"
        ]
        
        for carpeta in carpetas:
            (self.base_path / carpeta).mkdir(parents=True, exist_ok=True)
        
        print(f"✓ Estructura de carpetas creada en: {self.base_path}")
    
    def capturar_widget(self, widget, nombre_archivo, carpeta):
        """Captura un widget de tkinter y lo guarda como imagen"""
        try:
            widget.update_idletasks()
            widget.update()
            time.sleep(0.3)
            
            x = widget.winfo_rootx()
            y = widget.winfo_rooty()
            w = widget.winfo_width()
            h = widget.winfo_height()
            
            imagen = ImageGrab.grab(bbox=(x, y, x + w, y + h))
            
            ruta_completa = self.base_path / carpeta / nombre_archivo
            imagen.save(ruta_completa, "PNG")
            
            self.capturas_realizadas.append(str(ruta_completa))
            print(f"  ✓ Capturado: {nombre_archivo}")
            
            return True
            
        except Exception as e:
            error_msg = f"Error capturando {nombre_archivo}: {str(e)}"
            self.errores.append(error_msg)
            print(f"  ✗ {error_msg}")
            return False
    
    def capturar_ventana_manual_asistida(self, titulo_ventana, nombre_archivo, carpeta, instrucciones):
        """
        Abre una ventana y espera que el usuario presione una tecla para capturarla
        """
        print(f"\n{instrucciones}")
        print(f"  → Presiona ENTER cuando la ventana esté lista para capturar...")
        input()
        
        # Esperar un momento para que la consola se oculte
        time.sleep(0.5)
        
        # Capturar toda la pantalla y recortar si es necesario
        try:
            imagen = ImageGrab.grab()
            ruta_completa = self.base_path / carpeta / nombre_archivo
            imagen.save(ruta_completa, "PNG")
            
            self.capturas_realizadas.append(str(ruta_completa))
            print(f"  ✓ Capturado: {nombre_archivo}")
            return True
        except Exception as e:
            error_msg = f"Error capturando {nombre_archivo}: {str(e)}"
            self.errores.append(error_msg)
            print(f"  ✗ {error_msg}")
            return False
    
    def capturar_credenciales_auto(self):
        """Captura automática de credenciales"""
        print("\n[AUTO] Capturando Autenticación...")
        
        try:
            from ventana_credenciales import credenciales
            
            root = tk.Tk()
            ventana_cred = credenciales(root, None)
            root.update()
            time.sleep(0.5)
            
            # Captura 1: Vacía
            self.capturar_widget(root, "ventana_credenciales.png", "02_autenticacion")
            
            # Captura 2: Con datos
            if hasattr(ventana_cred, 'entry_usuario'):
                ventana_cred.entry_usuario.insert(0, "admin_usuario")
            if hasattr(ventana_cred, 'entry_password'):
                ventana_cred.entry_password.insert(0, "••••••••")
            root.update()
            time.sleep(0.3)
            
            self.capturar_widget(root, "credenciales_ingresadas.png", "02_autenticacion")
            
            root.quit()
            root.destroy()
            
        except Exception as e:
            self.errores.append(f"Error en autenticación: {str(e)}")
            print(f"  ✗ Error: {str(e)}")
    
    def generar_script_manual(self):
        """
        Genera instrucciones para capturas manuales
        """
        script_manual = """
╔══════════════════════════════════════════════════════════════════╗
║                   CAPTURAS MANUALES PENDIENTES                   ║
╚══════════════════════════════════════════════════════════════════╝

Para completar la documentación, necesitas capturar manualmente las
siguientes pantallas usando la aplicación ZetaOne:

📋 PASOS:

1. Ejecuta ZetaOne.exe (o python ZLauncher.py)

2. Para cada captura, usa: Win + Shift + S (Snipping Tool)

3. Guarda en la carpeta correspondiente con el nombre indicado


═══════════════════════════════════════════════════════════════════

[01] PANTALLA DE INICIO
────────────────────────────────────────────────────────────────────
📁 Carpeta: imagenes/01_pantalla_inicio/
📸 Nombre: pantalla_inicio.png

✓ Ejecuta: python ZLauncher.py
✓ Captura la pantalla con logo ZetaOne
✓ Guarda


═══════════════════════════════════════════════════════════════════

[02] VENTANA PRINCIPAL ADMINISTRADOR  
────────────────────────────────────────────────────────────────────
📁 Carpeta: imagenes/03_admin_principal/

📸 ventana_principal_admin.png
   → Inicia sesión como Administrador
   → Captura la ventana completa

📸 pestana_validar.png
   → Click en pestaña "Validar"
   → Captura

📸 pestana_catalogar.png
   → Click en pestaña "Catalogar"
   → Captura

📸 pestana_repetidos.png
   → Click en pestaña "Repetidos"
   → Captura


═══════════════════════════════════════════════════════════════════

[03] PROCESO DE VALIDACIÓN
────────────────────────────────────────────────────────────────────
📁 Carpeta: imagenes/04_validacion/

📸 dialogo_validacion_inicial.png
   → Selecciona archivos para validar
   → Captura el diálogo ANTES de iniciar

📸 validacion_en_progreso.png
   → Inicia validación
   → Captura con barra de progreso al 40-60%

📸 validacion_completada.png
   → Espera a que termine
   → Captura resultado final

📸 tabla_resultados_validacion.png
   → Captura la tabla de resultados


═══════════════════════════════════════════════════════════════════

[04] PROCESO DE CATALOGACIÓN
────────────────────────────────────────────────────────────────────
📁 Carpeta: imagenes/05_catalogacion/

📸 dialogo_catalogacion_inicial.png
   → Selecciona archivos para catalogar
   → Captura el diálogo ANTES de iniciar

📸 catalogacion_en_progreso.png
   → Inicia catalogación
   → Captura con barra de progreso

📸 catalogo_generado.png
   → Abre el archivo de catálogo generado
   → Captura parte del contenido


═══════════════════════════════════════════════════════════════════

[05] VENTANA PRINCIPAL USUARIO BÁSICO
────────────────────────────────────────────────────────────────────
📁 Carpeta: imagenes/06_basico/

📸 ventana_principal_basico.png
   → Inicia sesión como Usuario Básico
   → Captura la ventana completa

📸 pestana_migracion.png
   → Click en pestaña de Migración
   → Captura

📸 proceso_migracion.png
   → Inicia una migración de prueba
   → Captura con progreso


═══════════════════════════════════════════════════════════════════

VERIFICACIÓN FINAL:

Ejecuta este comando PowerShell para verificar todas las imágenes:

Get-ChildItem -Path "imagenes" -Recurse -Filter "*.png" | Select-Object Name, Directory | Format-Table -AutoSize

═══════════════════════════════════════════════════════════════════
"""
        
        # Guardar instrucciones
        ruta_instrucciones = self.base_path / "INSTRUCCIONES_CAPTURAS_MANUALES.txt"
        with open(ruta_instrucciones, 'w', encoding='utf-8') as f:
            f.write(script_manual)
        
        print(script_manual)
        print(f"\n✓ Instrucciones guardadas en: {ruta_instrucciones}")
    
    def ejecutar(self):
        """Ejecuta el proceso de captura híbrido"""
        print("=" * 70)
        print("CAPTURADOR HÍBRIDO DE PANTALLAS - ZetaOne")
        print("=" * 70)
        
        self.crear_estructura_carpetas()
        
        # Captura automática de lo que funciona
        print("\n" + "─" * 70)
        print("FASE 1: CAPTURAS AUTOMÁTICAS")
        print("─" * 70)
        
        self.capturar_credenciales_auto()
        
        # Generar instrucciones para el resto
        print("\n" + "─" * 70)
        print("FASE 2: CAPTURAS MANUALES")
        print("─" * 70)
        
        self.generar_script_manual()
        
        # Resumen
        print("\n" + "=" * 70)
        print("RESUMEN")
        print("=" * 70)
        print(f"✓ Capturas automáticas: {len(self.capturas_realizadas)}")
        print(f"⚠ Capturas manuales pendientes: ~15")
        print(f"✗ Errores: {len(self.errores)}")
        
        if self.capturas_realizadas:
            print("\nArchivos generados automáticamente:")
            for captura in self.capturas_realizadas:
                print(f"  • {Path(captura).name}")
        
        print("\n" + "=" * 70)
        print("SIGUIENTES PASOS:")
        print("=" * 70)
        print("1. Revisa: INSTRUCCIONES_CAPTURAS_MANUALES.txt")
        print("2. Ejecuta ZetaOne y captura las pantallas restantes")
        print("3. Usa Win + Shift + S para capturar")
        print("4. Guarda en las carpetas indicadas")
        print("5. Ejecuta la verificación final")
        print("=" * 70)


def main():
    """Función principal"""
    capturador = CapturadorHibrido()
    capturador.ejecutar()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
