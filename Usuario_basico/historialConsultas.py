import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import os
import json
import re

#importacion de estilos
from styles import etiqueta_titulo, boton_accion
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from textwrap import wrap

#-----------Historial de consultas
HISTORIAL_FILE = 'json/HistorialConsultas.json'
def cargar_historial():
    if os.path.exists(HISTORIAL_FILE):
        try:
            with open(HISTORIAL_FILE, 'r', encoding='utf-8') as hfile:
                return json.load(hfile)
        except Exception as error:
            print(f"Error al leer historial: {error}")
            return []
    return []

def guardar_historial(historial_existente, nueva_consulta=None):
    """
    Guarda el historial de consultas asegurándose de eliminar duplicados
    y mantener solo los 10 más recientes.
    """
    # --- CORRECCIÓN: Se procesa la nueva consulta por separado ---
    if nueva_consulta:
        historial_existente.insert(0, nueva_consulta)

    historial_limpio = []
    vistos = set()

    for consulta in historial_existente:
        # Normalizar cada consulta para una comparación robusta.
        base_norm = consulta.get("base", "").strip().lower()
        tabla_norm = consulta.get("tabla", "").strip().lower()
        
        # --- CORRECCIÓN EXPERTA: Leer la condición WHERE de forma retrocompatible ---
        # Intenta leer la clave correcta, y si no, las antiguas incorrectas.
        where_str = consulta.get("condicion (where)", consulta.get("condicion(where)", consulta.get("where", "")))
        where_norm = "".join(where_str.strip().lower().split())
        
        identificador_unico = (base_norm, tabla_norm, where_norm)
        
        if identificador_unico not in vistos:
            vistos.add(identificador_unico)
            historial_limpio.append(consulta)

    try:
        with open(HISTORIAL_FILE, 'w', encoding='utf-8') as hfile:
            # Guardar solo los 10 más recientes de la lista limpia.
            json.dump(historial_limpio[:10], hfile, ensure_ascii=False, indent=4)
    except Exception as error:
        print(f"Error al guardar historial: {error}")

class HistorialConsultasVen(tk.Toplevel):
    def __init__(self, master=None, callback_usar=None):
        super().__init__(master)
        self.callback_usar = callback_usar
        self.title("historial de consultas")
        self.geometry("400x400")
        self.resizable(False,False)

        etiqueta_titulo(self, texto="Historial de consultas recientes").pack(pady=10)


        historial_bruto = cargar_historial()

        # --- OPTIMIZACIÓN EXPERTA: Filtrar duplicados en memoria antes de mostrar ---
        # Esto garantiza una vista limpia sin importar el estado del archivo JSON.
        historial_limpio = []
        vistos = set()
        for consulta in historial_bruto:
            base_norm = consulta.get("base", "").strip().lower()
            tabla_norm = consulta.get("tabla", "").strip().lower()
            
            # Lógica retrocompatible para leer la condición WHERE
            where_str = consulta.get("condicion (where)", consulta.get("condicion(where)", consulta.get("where", "")))
            where_norm = "".join(where_str.strip().lower().split())
            
            identificador_unico = (base_norm, tabla_norm, where_norm)
            if identificador_unico not in vistos:
                vistos.add(identificador_unico)
                historial_limpio.append(consulta)

        if not historial_limpio:
            etiqueta_titulo(self, texto="No hay historial todavía", font=("Arial", 12, "italic")).pack(pady=30)
            return
        
#------------------------------------------------------------------------------------

        # scrollbar
        canvas = tk.Canvas(self, borderwidth=0, height=180)  # Puedes ajustar el height
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=(0,0), pady=(0,10))
        scrollbar.pack(side="right", fill="y")

    #logica de carga de consultas 
        for i, consulta in enumerate(historial_limpio):
            frame = tk.Frame(scrollable_frame, bd=1, relief="solid", pady=4, padx=6)

            # --- CORRECCIÓN: Añadir la condición WHERE a la vista del historial ---
            where_str = consulta.get("condicion (where)", consulta.get("condicion(where)", consulta.get("where", "")))
            
            texto_consuta = f"Base: {consulta.get('base', '')}\nTabla: {consulta.get('tabla', '')}"
            if where_str:
                # Ajusta el texto de la condición si es muy largo para que quepa en la ventana
                condicion_ajustada = '\n'.join(wrap(f"Condición: {where_str}", width=40))
                texto_consuta += f"\n{condicion_ajustada}"

            consutla = etiqueta_titulo(frame, texto=texto_consuta)
            consutla.grid(row=0, column=0, sticky="w")
            
            btn_usar = tb.Button(frame, text="Usar consulta",
                                 command=lambda c=consulta: self.usar_consulta(c), bootstyle="dark", width=14)
            btn_usar.grid(row=0, column=1, padx=20, pady=30, sticky="n")

            frame.pack(fill="x", pady=5, padx=18)

    def usar_consulta(self, consulta):
        if self.callback_usar:
            self.callback_usar(
                consulta.get("base",""),
                consulta.get("tabla",""),
                # --- CORRECCIÓN EXPERTA: Leer la condición WHERE de forma retrocompatible al usarla ---
                consulta.get("condicion (where)", consulta.get("condicion(where)", consulta.get("where", "")))
            )
        self.destroy()  