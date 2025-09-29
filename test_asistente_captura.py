#!/usr/bin/env python3
"""
Script de prueba para el Asistente de Captura y Grabación
Ejecuta este archivo para probar la funcionalidad de forma independiente
"""

import tkinter as tk
import sys
import os

# Añadir el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Función principal de prueba"""
    try:
        # Importar y crear la ventana de prueba
        from Usuario_basico.asistente_captura import AsistenteCapturaVentana
        
        # Crear ventana principal temporal
        root = tk.Tk()
        root.withdraw()  # Ocultar la ventana principal
        
        # Crear y mostrar el asistente
        asistente = AsistenteCapturaVentana(root)
        
        # Ejecutar el bucle principal
        root.mainloop()
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("\n🔧 Soluciones posibles:")
        print("1. Ejecuta 'instalar_dependencias_captura.bat'")
        print("2. Instala manualmente: pip install pyautogui keyboard python-docx pywinauto pillow opencv-python mss pygetwindow pywin32")
        input("\nPresiona Enter para salir...")
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    print("🧪 PRUEBA DEL ASISTENTE DE CAPTURA Y GRABACIÓN")
    print("=" * 50)
    print("Este script prueba la funcionalidad de forma independiente")
    print("Presiona Ctrl+C para salir en cualquier momento")
    print("=" * 50)
    print()
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 ¡Prueba cancelada por el usuario!")
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        input("Presiona Enter para salir...")