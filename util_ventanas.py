# util_ventanas.py
import tkinter as tk
from tkinter import ttk

def centrar_ventana(ventana, ancho=None, alto=None, offset_y=0):
    """Centra una ventana Toplevel en la pantalla.
    
    Args:
        ventana: Ventana a centrar
        ancho: Ancho opcional (si None, usa el actual)
        alto: Alto opcional (si None, usa el actual)
        offset_y: Desplazamiento vertical en píxeles (negativo = arriba, positivo = abajo)
    """
    ventana.update_idletasks()
    
    # Si no se especifican dimensiones, se usan las del widget
    ancho_ventana = ancho if ancho is not None else ventana.winfo_width()
    alto_ventana = alto if alto is not None else ventana.winfo_height()
    
    x = (ventana.winfo_screenwidth() // 2) - (ancho_ventana // 2)
    y = (ventana.winfo_screenheight() // 2) - (alto_ventana // 2) + offset_y
    
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
        # Asegurar que el valor sea entero y válido para no mostrar decimales
        try:
            pct = int(round(float(value)))
        except Exception:
            pct = 0
        pct = max(0, min(100, pct))

        self.progress_bar['value'] = pct
        # Si `text` contiene el porcentaje, reemplazarlo por la versión sin decimales
        try:
            # Si el texto ya incluye un porcentaje numérico, reemplazar la parte numérica
            if isinstance(text, str) and '%' in text:
                # Reemplaza el primer número que aparezca seguido de '%' por el entero
                import re
                text = re.sub(r"\d+(?:[.,]\d+)?%", f"{pct}%", text, count=1)
        except Exception:
            pass

        self.progress_label.config(text=text)
        self.update_idletasks()