import tkinter as tk
from tkinter import ttk
import os
import json
from textwrap import wrap

from styles import etiqueta_titulo, boton_accion
import ttkbootstrap as tb

HISTORIAL_FILE = 'json/HistorialModificaciones.json'

def cargar_historial():
    """Carga el historial de modificaciones desde un archivo JSON."""
    if os.path.exists(HISTORIAL_FILE):
        try:
            with open(HISTORIAL_FILE, 'r', encoding='utf-8') as hfile:
                return json.load(hfile)
        except Exception as error:
            print(f"Error al leer historial de modificaciones: {error}")
            return []
    return []

def guardar_historial(historial_existente, nueva_consulta=None):
    """
    Guarda el historial de modificaciones, eliminando duplicados
    y manteniendo solo los 10 más recientes.
    """
    if nueva_consulta:
        historial_existente.insert(0, nueva_consulta)

    historial_limpio = []
    vistos = set()

    for consulta in historial_existente:
        # Normalizar para una comparación robusta
        ambiente_norm = consulta.get("ambiente", "").strip().lower()
        base_norm = consulta.get("base", "").strip().lower()
        tabla_norm = consulta.get("tabla", "").strip().lower()
        campo_norm = consulta.get("campo", "").strip().lower()
        condicion_norm = "".join(consulta.get("condicion", "").strip().lower().split())
        
        identificador_unico = (ambiente_norm, base_norm, tabla_norm, campo_norm, condicion_norm)
        
        if identificador_unico not in vistos:
            vistos.add(identificador_unico)
            historial_limpio.append(consulta)

    try:
        with open(HISTORIAL_FILE, 'w', encoding='utf-8') as hfile:
            json.dump(historial_limpio[:10], hfile, ensure_ascii=False, indent=4)
    except Exception as error:
        print(f"Error al guardar historial de modificaciones: {error}")

class HistorialModificacionesVen(tk.Toplevel):
    def __init__(self, master=None, callback_usar=None):
        super().__init__(master)
        self.callback_usar = callback_usar
        self.title("Historial de Modificaciones")
        self.geometry("450x450")
        self.resizable(False, False)

        etiqueta_titulo(self, texto="Historial de modificaciones recientes").pack(pady=10)

        historial_bruto = cargar_historial()

        # Filtro de duplicados en memoria
        historial_limpio = []
        vistos = set()
        for consulta in historial_bruto:
            ambiente_norm = consulta.get("ambiente", "").strip().lower()
            base_norm = consulta.get("base", "").strip().lower()
            tabla_norm = consulta.get("tabla", "").strip().lower()
            campo_norm = consulta.get("campo", "").strip().lower()
            condicion_norm = "".join(consulta.get("condicion", "").strip().lower().split())
            
            identificador_unico = (ambiente_norm, base_norm, tabla_norm, campo_norm, condicion_norm)
            if identificador_unico not in vistos:
                vistos.add(identificador_unico)
                historial_limpio.append(consulta)

        if not historial_limpio:
            etiqueta_titulo(self, texto="No hay historial todavía", font=("Arial", 12, "italic")).pack(pady=30)
            return

        canvas = tk.Canvas(self, borderwidth=0, height=300)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=(10,0), pady=(0,10))
        scrollbar.pack(side="right", fill="y", padx=(0,10))

        for i, consulta in enumerate(historial_limpio):
            frame = tk.Frame(scrollable_frame, bd=1, relief="solid", pady=4, padx=6)
            texto_consulta = (
                f"Ambiente: {consulta.get('ambiente', 'N/A')}\n"
                f"Base: {consulta.get('base', 'N/A')}\n"
                f"Tabla: {consulta.get('tabla', 'N/A')}\n"
                f"Campo: {consulta.get('campo', 'N/A')}"
            )
            condicion_str = consulta.get("condicion", "")
            if condicion_str:
                condicion_ajustada = '\n'.join(wrap(f"Condición: {condicion_str}", width=45))
                texto_consulta += f"\n{condicion_ajustada}"
            label_consulta = etiqueta_titulo(frame, texto=texto_consulta)
            label_consulta.grid(row=0, column=0, sticky="w")
            btn_usar = tb.Button(frame, text="Usar", command=lambda c=consulta: self.usar_consulta(c), bootstyle="dark", width=10)
            btn_usar.grid(row=0, column=1, padx=20, pady=10, sticky="e")
            frame.pack(fill="x", pady=5, padx=10)

    def usar_consulta(self, consulta):
        if self.callback_usar:
            self.callback_usar(consulta.get("ambiente", ""), consulta.get("base", ""), consulta.get("tabla", ""), consulta.get("campo", ""), consulta.get("condicion", ""))
        self.destroy()