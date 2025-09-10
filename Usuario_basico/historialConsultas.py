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

def guardar_historial(historial):
    try:
        with open(HISTORIAL_FILE, 'w', encoding='utf-8') as hfile:
            json.dump(historial, hfile, ensure_ascii=False, indent=4)
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


        historial = cargar_historial()
        if not historial:
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
        for i, consulta in enumerate(historial):
            frame = tk.Frame(scrollable_frame, bd=1, relief="solid", pady=4, padx=6)

            texto_consuta = f"Base: {consulta['base']}\nTabla: {consulta['tabla']}"    

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
                consulta.get("where", consulta.get("condicion(where)",""))
            )
        self.destroy()  