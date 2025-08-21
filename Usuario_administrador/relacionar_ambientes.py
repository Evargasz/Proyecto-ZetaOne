import tkinter as tk
from tkinter import messagebox, ttk
import json
import os

#estilos
from styles import boton_accion, etiqueta_titulo, entrada_estandar, boton_comun, boton_exito
import ttkbootstrap as tb
from ttkbootstrap.constants import *

# Nueva: ruta base a la carpeta json/
CARPETA_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "json")
ARCHIVO_AMBIENTES = os.path.join(CARPETA_JSON, "ambientes.json")
ARCHIVO_RELACIONES = os.path.join(CARPETA_JSON, "ambientesrelacionados.json")

def cargar_ambientes():
    print("DEBUG ruta actual:", os.getcwd())
    print("DEBUG buscaré ambientes.json en:", ARCHIVO_AMBIENTES)
    if os.path.exists(ARCHIVO_AMBIENTES):
        with open(ARCHIVO_AMBIENTES, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        print("DEBUG - No se encontró ambientes.json")
        return []

def cargar_relaciones():
    if os.path.exists(ARCHIVO_RELACIONES):
        with open(ARCHIVO_RELACIONES, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {}

def guardar_relaciones(relaciones):
    with open(ARCHIVO_RELACIONES, 'w', encoding='utf-8') as f:
        json.dump(relaciones, f, indent=4, ensure_ascii=False)

def gestionar_ambientes_relacionados(ambiente, master=None):
    ambientes = cargar_ambientes()
    nombres_ambientes = [a['nombre'] for a in ambientes if 'nombre' in a]

    relaciones = cargar_relaciones()
    relacionados = set(relaciones.get(ambiente, []))

    win = tk.Toplevel(master)
    win.title(f"Ambientes relacionados para: {ambiente}")
    win.geometry("520x320")
    win.resizable(False, False)

    frame_main = tk.Frame(win, pady=12)
    frame_main.pack(fill=tk.BOTH, expand=True)

    lbl_principal = etiqueta_titulo(frame_main, texto=f"Ambiente seleccionado:")
    lbl_principal.grid(row=0, column=0, sticky='e', padx=(12,8), pady=(6,3))
    lbl_principal_value = etiqueta_titulo(frame_main, texto=ambiente)
    lbl_principal_value.grid(row=0, column=1, sticky='w', padx=(0,16), pady=(6,3))

    etiqueta_titulo(frame_main, texto="Ambiente a relacionar:").grid(row=1, column=0, sticky='e', padx=(12,8), pady=(2,3))
    combo_ambiente = ttk.Combobox(frame_main, state="readonly", width=26)
    combo_ambiente.grid(row=1, column=1, sticky='w', padx=(0,16), pady=(2,3))

    def agregar_relacion():
        seleccionado = combo_ambiente.get()
        if not seleccionado:
            messagebox.showinfo("Info", "Seleccione un ambiente para relacionar.")
            return
        if seleccionado in relacionados:
            messagebox.showwarning("Advertencia", "Este ambiente ya está relacionado.")
            return
        relacionados.add(seleccionado)
        actualizar_listas()
        guardar_en_archivo()
    btn_relacionar = tb.Button(frame_main, text="Relacionar", width=14, command=agregar_relacion, bootstyle="primary")
    btn_relacionar.grid(row=1, column=2, padx=(9,8), pady=2)

    etiqueta_titulo(frame_main, texto="Ambientes relacionados:").grid(row=2, column=0, sticky='ne', padx=(12,6), pady=(8,2))
    lb_relacionados = tk.Listbox(frame_main, height=10, width=35, exportselection=False)
    lb_relacionados.grid(row=2, column=1, sticky='w', padx=(0,0), pady=(8,2))

    def quitar_relacion():
        seleccion = lb_relacionados.curselection()
        if not seleccion:
            messagebox.showinfo("Info", "Seleccione un ambiente relacionado para quitar.")
            return
        seleccionado = lb_relacionados.get(seleccion[0])
        relacionados.discard(seleccionado)
        actualizar_listas()
        guardar_en_archivo()
    btn_quitar = tb.Button(frame_main, text="Quitar", width=14, command=quitar_relacion, bootstyle="danger")
    btn_quitar.grid(row=2, column=2, padx=(9,8), pady=(8,2), sticky='n')

    def regresar():
        win.destroy()

    frame_botones = tk.Frame(win, pady=20)
    frame_botones.pack()
    btn_regresar = boton_comun(frame_botones, texto="Regresar", width=14, comando=regresar)
    btn_regresar.grid(row=0, column=0, padx=(10,8))
    btn_cerrar = boton_comun(frame_botones, texto="Salir", width=10, comando=win.destroy)
    btn_cerrar.grid(row=0, column=1, padx=(4,12))

    def actualizar_listas():
        lb_relacionados.delete(0, tk.END)
        for amb in sorted(relacionados):
            lb_relacionados.insert(tk.END, amb)
        disponibles = [a for a in nombres_ambientes if a != ambiente and a not in relacionados]
        # ---- DEBUG PRINTS ----
        print("DEBUG - Ambiente principal:", ambiente)
        print("DEBUG - Nombres ambientes:", nombres_ambientes)
        print("DEBUG - Ya relacionados:", relacionados)
        print("DEBUG - Disponibles para relacionar:", disponibles)
        # ---------------------
        combo_ambiente['values'] = disponibles
        combo_ambiente.set('' if not disponibles else disponibles[0])

    def guardar_en_archivo():
        relaciones[ambiente] = sorted(list(relacionados))
        guardar_relaciones(relaciones)

    actualizar_listas()