# util_ventanas.py
import tkinter as tk
from tkinter import ttk

def centrar_ventana(ventana, ancho=None, alto=None):
    """Centra una ventana Toplevel en la pantalla."""
    ventana.update_idletasks()
    
    # Si no se especifican dimensiones, se usan las del widget
    ancho_ventana = ancho if ancho is not None else ventana.winfo_width()
    alto_ventana = alto if alto is not None else ventana.winfo_height()
    
    x = (ventana.winfo_screenwidth() // 2) - (ancho_ventana // 2)
    y = (ventana.winfo_screenheight() // 2) - (alto_ventana // 2)
    
    ventana.geometry(f'{ancho_ventana}x{alto_ventana}+{x}+{y}')

class ProgressWindow(tk.Toplevel):
    """Una ventana de progreso genérica para tareas en segundo plano."""
    def __init__(self, parent, titulo="Procesando..."):
        super().__init__(parent)
        self.title(titulo)
        self.geometry("400x150")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        centrar_ventana(self)

        ttk.Label(self, text=titulo, font=("Segoe UI", 12, "bold")).pack(pady=(15, 10))

        self.progress_label = ttk.Label(self, text="Iniciando...")
        self.progress_label.pack(pady=5, padx=20, anchor="w")

        self.progress_bar = ttk.Progressbar(self, mode='determinate', length=360)
        self.progress_bar.pack(pady=10, padx=20)

    def update_progress(self, value, text):
        """Actualiza la barra de progreso y el texto de estado."""
        self.progress_bar['value'] = value
        self.progress_label.config(text=text)
        self.update_idletasks()