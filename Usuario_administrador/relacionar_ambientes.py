import tkinter as tk
from tkinter import messagebox, ttk
import json
import os

# Estilos
from styles import etiqueta_titulo, boton_comun
import ttkbootstrap as tb
from ttkbootstrap.constants import *

# Import clave para que las rutas funcionen en el .exe
from util_rutas import recurso_path

# --- SECCIÓN CORREGIDA: Carga de archivos JSON ---

def cargar_ambientes():
    """Carga los ambientes desde el archivo JSON usando la ruta correcta."""
    try:
        # Usamos recurso_path para encontrar el archivo de forma segura
        ruta_json = recurso_path("json", "ambientes.json")
        with open(ruta_json, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        messagebox.showerror("Error Crítico", "No se encontró el archivo 'ambientes.json'. La aplicación no puede continuar.")
        return []
    except Exception as e:
        messagebox.showerror("Error Crítico", f"Error al cargar 'ambientes.json':\n{e}")
        return []

def cargar_relaciones():
    """Carga las relaciones de ambientes desde el archivo JSON."""
    try:
        # Usamos recurso_path para encontrar el archivo de forma segura
        ruta_json = recurso_path("json", "ambientesrelacionados.json")
        with open(ruta_json, "r", encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Si el archivo no existe, es normal, se creará después.
        return {}
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar 'ambientesrelacionados.json':\n{e}")
        return {}


# --- Interfaz Gráfica ---

def gestionar_ambientes_relacionados(ambiente, master=None):
    win = tk.Toplevel(master)
    win.title(f"Relacionar ambientes para: {ambiente}")
    win.grab_set()
    win.resizable(False, False)

    # Cargar datos
    ambientes_data = cargar_ambientes()
    nombres_ambientes = [a['nombre'] for a in ambientes_data]
    relaciones_data = cargar_relaciones()
    relacionados = relaciones_data.get(ambiente, [])

    # --- SECCIÓN CORREGIDA: Guardado de archivo JSON ---
    def guardar_en_archivo():
        """Guarda el archivo de relaciones usando la ruta correcta."""
        relaciones_data[ambiente] = relacionados
        try:
            # Usamos recurso_path para obtener la ruta de guardado correcta
            ruta_json = recurso_path("json", "ambientesrelacionados.json")
            with open(ruta_json, 'w', encoding='utf-8') as f:
                json.dump(relaciones_data, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error al Guardar", f"No se pudo guardar el archivo de relaciones:\n{e}")

    # Interfaz
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
        if not seleccion:
            return
        amb_a_agregar = lb_disponibles.get(seleccion[0])
        if amb_a_agregar not in relacionados:
            relacionados.append(amb_a_agregar)
        actualizar_listas()
        guardar_en_archivo() # Guardar al agregar

    btn_agregar = tb.Button(frame_main, text="Agregar", width=14, command=agregar_relacion, bootstyle="success")
    btn_agregar.grid(row=2, column=0, padx=(8,0), pady=(8,2), sticky='n')

    def quitar_relacion():
        seleccion = lb_relacionados.curselection()
        if not seleccion:
            return
        amb_a_quitar = lb_relacionados.get(seleccion[0])
        if amb_a_quitar in relacionados:
            relacionados.remove(amb_a_quitar)
        actualizar_listas()
        guardar_en_archivo() # Guardar al quitar

    btn_quitar = tb.Button(frame_main, text="Quitar", width=14, command=quitar_relacion, bootstyle="danger")
    btn_quitar.grid(row=2, column=1, padx=(60,0), pady=(8,2), sticky='n')

    def regresar():
        guardar_en_archivo() # Aseguramos guardar antes de salir
        win.destroy()

    frame_botones = tk.Frame(win, pady=15)
    frame_botones.pack()
    btn_regresar = boton_comun(frame_botones, texto="Cerrar", width=14, comando=regresar)
    btn_regresar.pack()

    def actualizar_listas():
        lb_relacionados.delete(0, tk.END)
        for amb in sorted(relacionados):
            lb_relacionados.insert(tk.END, amb)

        lb_disponibles.delete(0, tk.END)
        disponibles = [a for a in nombres_ambientes if a != ambiente and a not in relacionados]
        for amb in sorted(disponibles):
            lb_disponibles.insert(tk.END, amb)

    actualizar_listas()