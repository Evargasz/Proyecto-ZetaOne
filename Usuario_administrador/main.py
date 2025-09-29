# main.py
import tkinter as tk
import ttkbootstrap as tb
from gui.ventana_principal import VentanaPrincipal

if __name__ == "__main__":
    # Usamos el tema 'litera' de ttkbootstrap que es limpio y profesional
    app = tb.Window(themename="litera")
    
    # Instanciamos nuestra ventana principal
    ventana = VentanaPrincipal(app)
    
    # Iniciamos el bucle principal de la aplicación
    app.mainloop()