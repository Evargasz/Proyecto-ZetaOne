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
        self.geometry("320x320")
        self.resizable(False,False)

        etiqueta_titulo(self, texto="Historial de consultas recientes").pack(pady=10)


        historial = cargar_historial()
        if not historial:
            etiqueta_titulo(self, texto="No hay historial todavía", font=("Arial", 12, "italic")).pack(pady=30)
            return

        main_frame = tk.Frame(self)
        main_frame.pack(fill="both", expand=True)
        for i, consulta in enumerate(historial):
            frame = tk.Frame(main_frame, bd=1, relief="solid", pady=4, padx=6)
            frame.pack(fill="x", pady=5, padx=18)
            etiqueta_titulo(frame, texto=f"Base: {consulta['base']}").grid(row=0, column=0, sticky="w")
            etiqueta_titulo(frame, texto=f"Tabla: {consulta['tabla']}").grid(row=1, column=0, sticky="w")
            etiqueta_titulo(
                frame, 
                texto=f"Where: {consulta.get('where', consulta.get('condicion (where)', ''))}"
            ).grid(row=2, column=0, sticky="w")
            btn_usar = tb.Button(frame, text="Usar esta consulta", command=lambda c=consulta: self.usar_consulta(c), bootstyle="dark")
            btn_usar.grid(row=0, column=2, rowspan=3, padx=10)

    def usar_consulta(self, consulta):
        if self.callback_usar:
            self.callback_usar(
                consulta.get("base",""),
                consulta.get("tabla",""),
                consulta.get("where", consulta.get("condicion(where)",""))
            )
        self.destroy()


   #asda   