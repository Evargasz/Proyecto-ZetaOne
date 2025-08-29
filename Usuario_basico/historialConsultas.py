import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import os
import json
import re

#importacion de estilos
from styles import etiqueta_titulo, entrada_estandar, boton_accion, boton_exito, boton_rojo
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
        self.geometry("470x320")
        self.resizable(False,False)

        etiqueta_titulo(self, texto="Historial de consultas recientes").pack(pady=10)


        historial = cargar_historial()
        if not historial:
            tk.Label(self, text="No hay historial todavía", font=("Arial", 12, "italic")).pack(pady=30)
            return

        main_frame = tk.Frame(self)
        main_frame.pack(fill="both", expand=True)
        for i, consulta in enumerate(historial):
            frame = tk.Frame(main_frame, bd=1, relief="solid", pady=4, padx=6)
            frame.pack(fill="x", pady=5, padx=18)
            tk.Label(frame, text=f"Base: {consulta['base']}", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w")
            tk.Label(frame, text=f"Tabla: {consulta['tabla']}", font=("Arial", 10)).grid(row=1, column=0, sticky="w")
            tk.Label(frame, text=f"Where: {consulta['where']}", font=("Arial", 10)).grid(row=2, column=0, sticky="w")
            btn_usar = tk.Button(frame, text="Usar esta consulta", command=lambda c=consulta: self.usar_consulta(c))
            btn_usar.grid(row=0, column=1, rowspan=3, padx=10)

    def usar_consulta(self, consulta):
        if self.callback_usar:
            self.callback_usar(
                consulta.get("base",""),
                consulta.get("tabla",""),
                consulta.get("where","")
            )
        self.destroy()
