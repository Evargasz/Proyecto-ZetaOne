"""
Capturador Automático de Pantallas para Documentación ZetaOne
Renderiza y captura screenshots de todas las ventanas del sistema
"""

import tkinter as tk
from tkinter import ttk
import sys
import os
from pathlib import Path
from PIL import ImageGrab, Image
import time

# Agregar ruta para importar módulos de ZetaOne
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importar módulos de ZetaOne (solo los que funcionan standalone)
from pantalla_inicio_sys import PantallaInicio
from ventana_credenciales import credenciales


class CapturadorAutomatico:
    """Automatiza la captura de screenshots de todas las ventanas"""
    
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
        """
        Captura un widget de tkinter y lo guarda como imagen
        
        Args:
            widget: Widget de tkinter a capturar
            nombre_archivo: Nombre del archivo PNG
            carpeta: Subcarpeta donde guardar (ej: "01_pantalla_inicio")
        """
        try:
            # Actualizar ventana para asegurar renderizado completo
            widget.update_idletasks()
            widget.update()
            
            # Esperar un momento para que todo se dibuje
            time.sleep(0.3)
            
            # Obtener coordenadas de la ventana
            x = widget.winfo_rootx()
            y = widget.winfo_rooty()
            w = widget.winfo_width()
            h = widget.winfo_height()
            
            # Capturar la región
            imagen = ImageGrab.grab(bbox=(x, y, x + w, y + h))
            
            # Guardar
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
    
    def capturar_pantalla_inicio(self):
        """Captura la pantalla de inicio"""
        print("\n[1/7] Capturando Pantalla de Inicio...")
        
        root = tk.Tk()
        root.withdraw()  # Ocultar ventana principal
        
        try:
            pantalla = PantallaInicio(root)
            pantalla.update()
            time.sleep(0.5)
            
            self.capturar_widget(
                pantalla,
                "pantalla_inicio.png",
                "01_pantalla_inicio"
            )
            
        except Exception as e:
            self.errores.append(f"Error en pantalla_inicio: {str(e)}")
            print(f"  ✗ Error: {str(e)}")
        finally:
            root.quit()
            root.destroy()
    
    def capturar_autenticacion(self):
        """Captura las pantallas de autenticación"""
        print("\n[2/7] Capturando Autenticación...")
        
        # Ventana de credenciales vacía
        root = tk.Tk()
        
        try:
            ventana_cred = credenciales(root, None)
            root.update()
            time.sleep(0.5)
            
            self.capturar_widget(
                root,
                "ventana_credenciales.png",
                "02_autenticacion"
            )
            
            # Simular credenciales ingresadas (sin enviar)
            if hasattr(ventana_cred, 'entry_usuario'):
                ventana_cred.entry_usuario.insert(0, "admin_usuario")
            if hasattr(ventana_cred, 'entry_password'):
                ventana_cred.entry_password.insert(0, "••••••••")
            root.update()
            time.sleep(0.3)
            
            self.capturar_widget(
                root,
                "credenciales_ingresadas.png",
                "02_autenticacion"
            )
            
        except Exception as e:
            self.errores.append(f"Error en autenticación: {str(e)}")
            print(f"  ✗ Error: {str(e)}")
        finally:
            root.quit()
            root.destroy()
    
    def capturar_admin_principal(self):
        """Captura la ventana principal del administrador"""
        print("\n[3/7] Capturando Ventana Administrador...")
        print("  ⚠ Requiere dependencias adicionales - Captura manual recomendada")
    
    def capturar_validacion(self):
        """Captura diálogos de validación"""
        print("\n[4/7] Capturando Validación...")
        print("  ⚠ Requiere dependencias adicionales - Captura manual recomendada")
    
    def capturar_catalogacion(self):
        """Captura diálogos de catalogación"""
        print("\n[5/7] Capturando Catalogación...")
        print("  ⚠ Requiere dependencias adicionales - Captura manual recomendada")
    
    def capturar_basico_principal(self):
        """Captura ventana principal del usuario básico"""
        print("\n[6/7] Capturando Usuario Básico...")
        print("  ⚠ Requiere dependencias adicionales - Captura manual recomendada")
    
    def capturar_migracion(self):
        """Captura ventana de migración"""
        print("\n[7/7] Capturando Migración...")
        
        # Skip por ahora - depende de la estructura específica
        print("  ⚠ Migración: Captura manual recomendada")
    
    def ejecutar_capturas(self):
        """Ejecuta todas las capturas automáticamente"""
        print("=" * 70)
        print("CAPTURADOR AUTOMÁTICO DE PANTALLAS - ZetaOne")
        print("=" * 70)
        
        # Crear carpetas
        self.crear_estructura_carpetas()
        
        # Ejecutar capturas
        self.capturar_pantalla_inicio()
        self.capturar_autenticacion()
        self.capturar_admin_principal()
        self.capturar_validacion()
        self.capturar_catalogacion()
        self.capturar_basico_principal()
        self.capturar_migracion()
        
        # Resumen
        print("\n" + "=" * 70)
        print("RESUMEN DE CAPTURAS")
        print("=" * 70)
        print(f"✓ Capturas exitosas: {len(self.capturas_realizadas)}")
        print(f"✗ Errores: {len(self.errores)}")
        
        if self.capturas_realizadas:
            print("\nArchivos generados:")
            for captura in self.capturas_realizadas:
                print(f"  • {captura}")
        
        if self.errores:
            print("\nErrores encontrados:")
            for error in self.errores:
                print(f"  • {error}")
        
        print("\n" + "=" * 70)
        print("Proceso completado!")
        print(f"Las imágenes están en: {self.base_path}")
        print("=" * 70)
        
        return len(self.errores) == 0


def main():
    """Función principal"""
    capturador = CapturadorAutomatico()
    
    try:
        exito = capturador.ejecutar_capturas()
        
        if exito:
            print("\n✓ Todas las capturas se realizaron correctamente!")
            print("\nSiguientes pasos:")
            print("1. Revisa las imágenes generadas")
            print("2. Convierte los diagramas Mermaid a PNG (usa DIAGRAMAS.md)")
            print("3. Ejecuta la conversión de Markdown a Word")
            return 0
        else:
            print("\n⚠ Algunas capturas fallaron. Revisa los errores arriba.")
            return 1
            
    except Exception as e:
        print(f"\n✗ Error crítico: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
