import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
import sys

# Estilos e importaciones
from styles import etiqueta_titulo, boton_comun
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from util_rutas import recurso_path

# --- Lógica de Rutas Corregida ---

def obtener_ruta_guardado(*partes_ruta):
    """
    Obtiene la ruta correcta para guardar archivos de datos.
    Funciona tanto en desarrollo como en el ejecutable.
    """
    if getattr(sys, 'frozen', False):
        # Si es un ejecutable, la base es el directorio del .exe
        base_path = os.path.dirname(sys.executable)
    else:
        # Si es un script de Python, la base es el directorio del proyecto
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, *partes_ruta)

# Se definen las rutas de lectura y escritura
RUTA_LECTURA_AMBIENTES = recurso_path("json", "ambientes.json")
RUTA_LECTURA_RELACIONES = recurso_path("json", "ambientesrelacionados.json")
RUTA_ESCRITURA_RELACIONES = obtener_ruta_guardado("json", "ambientesrelacionados.json")

# --- Funciones de Carga y Guardado ---

def cargar_ambientes_rel():
    """Carga los ambientes desde el archivo JSON de forma segura."""
    try:
        with open(RUTA_LECTURA_AMBIENTES, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def cargar_relaciones():
    """Carga las relaciones de ambientes. Si no existe, devuelve un diccionario vacío."""
    if os.path.exists(RUTA_LECTURA_RELACIONES):
        try:
            with open(RUTA_LECTURA_RELACIONES, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def guardar_relaciones_final(data):
    """Guarda las relaciones en la ruta de escritura correcta."""
    try:
        # Asegurarse de que la carpeta 'json' exista
        os.makedirs(os.path.dirname(RUTA_ESCRITURA_RELACIONES), exist_ok=True)
        with open(RUTA_ESCRITURA_RELACIONES, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        messagebox.showerror("Error al Guardar", f"No se pudo guardar el archivo de relaciones:\n{e}")

# --- Interfaz Gráfica (Sin cambios en el diseño) ---

def gestionar_ambientes_relacionados(ambiente, master=None):
    win = tk.Toplevel(master)
    win.title(f"Relacionar ambientes para: {ambiente}")
    win.grab_set()
    win.resizable(False, False)

    ambientes_data = cargar_ambientes_rel()
    nombres_ambientes = [a['nombre'] for a in ambientes_data]
    relaciones_data = cargar_relaciones()
    relacionados_actuales = relaciones_data.get(ambiente, [])

    def guardar_y_cerrar():
        relaciones_data[ambiente] = relacionados_actuales
        guardar_relaciones_final(relaciones_data)
        win.destroy()

    frame_main = tk.Frame(win, padx=20, pady=15)
    frame_main.pack()

    etiqueta_titulo(frame_main, texto="Ambientes Relacionados:").grid(row=0, column=0, sticky="w")
    etiqueta_titulo(frame_main, texto="Ambientes Disponibles:").grid(row=0, column=1, sticky="w", padx=(60, 0))

    lb_relacionados = tk.Listbox(frame_main, height=10, width=30)
    lb_relacionados.grid(row=1, column=0)
    lb_disponibles = tk.Listbox(frame_main, height=10, width=30)
    lb_disponibles.grid(row=1, column=1, padx=(60, 0))

    def agregar_relacion():
        seleccion = lb_disponibles.curselection()
        if not seleccion: return
        amb_a_agregar = lb_disponibles.get(seleccion[0])
        if amb_a_agregar not in relacionados_actuales:
            relacionados_actuales.append(amb_a_agregar)
        actualizar_listas()

    btn_agregar = tb.Button(frame_main, text="<< Agregar", width=14, command=agregar_relacion, bootstyle="success")
    btn_agregar.grid(row=2, column=0, pady=(10, 0))

    def quitar_relacion():
        seleccion = lb_relacionados.curselection()
        if not seleccion: return
        amb_a_quitar = lb_relacionados.get(seleccion[0])
        if amb_a_quitar in relacionados_actuales:
            relacionados_actuales.remove(amb_a_quitar)
        actualizar_listas()

    btn_quitar = tb.Button(frame_main, text="Quitar >>", width=14, command=quitar_relacion, bootstyle="danger")
    btn_quitar.grid(row=2, column=1, padx=(60, 0), pady=(10, 0))

    frame_botones = tk.Frame(win, pady=15)
    frame_botones.pack()
    btn_guardar = boton_comun(frame_botones, texto="Guardar y Cerrar", width=20, comando=guardar_y_cerrar)
    btn_guardar.pack()

    def actualizar_listas():
        lb_relacionados.delete(0, tk.END)
        for amb in sorted(relacionados_actuales):
            lb_relacionados.insert(tk.END, amb)

        lb_disponibles.delete(0, tk.END)
        disponibles = [a for a in nombres_ambientes if a != ambiente and a not in relacionados_actuales]
        for amb in sorted(disponibles):
            lb_disponibles.insert(tk.END, amb)

    actualizar_listas()