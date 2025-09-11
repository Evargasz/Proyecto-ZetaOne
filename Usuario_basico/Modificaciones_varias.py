import tkinter as tk
from tkinter import ttk, messagebox
import os
import json
import re
import datetime
import getpass
import threading
import pyodbc

# --- Imports Corregidos y Optimizados ---
from styles import etiqueta_titulo, entrada_estandar, boton_accion
from util_rutas import recurso_path
from ttkbootstrap.constants import *

class ModificacionesVariasVentana(tk.Toplevel):
    def __init__(self, parent, ambientes_lista, master=None):
        super().__init__(parent)
        self.title("Modificaciones varias")
        self.protocol("WM_DELETE_WINDOW", self.on_salir)

        # --- Tu diseño de ventana original, sin cambios ---
        ventana_ancho = 400
        ventana_alto = 380
        pantalla_ancho = self.winfo_screenwidth()
        pantalla_alto = self.winfo_screenheight()
        x = int((pantalla_ancho / 2) - (ventana_ancho / 2))
        y = int((pantalla_alto / 2) - (ventana_alto / 2))
        self.geometry(f"{ventana_ancho}x{ventana_alto}+{x}+{y}")
        self.resizable(False, False)

        y_step = 35
        y_now = 20

        etiqueta_titulo(self, texto="Ambiente:").place(x=20, y=y_now)
        self.entry_ambiente = ttk.Combobox(self, values=[amb['nombre'] for amb in ambientes_lista], state='readonly')
        self.entry_ambiente.place(x=150, y=y_now, width=200)
        y_now += y_step

        etiqueta_titulo(self, texto="Base de Datos:").place(x=20, y=y_now)
        self.entry_base = entrada_estandar(self)
        self.entry_base.place(x=150, y=y_now, width=200)
        y_now += y_step

        etiqueta_titulo(self, texto="Tabla:").place(x=20, y=y_now)
        self.entry_tabla = entrada_estandar(self)
        self.entry_tabla.place(x=150, y=y_now, width=200)
        y_now += y_step

        etiqueta_titulo(self, texto="Campo a modificar:").place(x=20, y=y_now)
        self.entry_campo = entrada_estandar(self)
        self.entry_campo.place(x=150, y=y_now, width=200)
        y_now += y_step

        etiqueta_titulo(self, texto="Nuevo valor:").place(x=20, y=y_now)
        self.entry_valor = entrada_estandar(self)
        self.entry_valor.place(x=150, y=y_now, width=200)
        y_now += y_step

        etiqueta_titulo(self, texto="Condición (sin WHERE):").place(x=20, y=y_now)
        self.entry_condicion = entrada_estandar(self)
        self.entry_condicion.place(x=150, y=y_now, width=200)

        self.btn_continuar = boton_accion(self, texto="Ejecutar modificación", comando=self.on_ejecutar, width=20)
        self.btn_continuar.place(relx=1.0, rely=1.0, x=-230, y=-22, anchor='se')
        self.btn_salir = boton_accion(self, "Salir", comando=self.on_salir, width=10)
        self.btn_salir.place(relx=1.0, rely=1.0, x=-40, y=-22, anchor='se')

        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.place(x=75, y=y_now+40, width=250, height=15)
        self.progress.lower()

        self.ambientes_lista = ambientes_lista
        
        # --- Carga segura de ambientes relacionados ---
        self.ambientes_rel = {}
        try:
            ruta_relaciones = recurso_path("json", "ambientesrelacionados.json")
            if os.path.exists(ruta_relaciones):
                with open(ruta_relaciones, "r", encoding="utf-8") as f:
                    self.ambientes_rel = json.load(f)
        except Exception as e:
            print(f"ADVERTENCIA: No se pudo cargar 'ambientesrelacionados.json': {e}")

    def bloquear_campos(self, bloquear=True):
        state = "disabled" if bloquear else "normal"
        # Para el combobox, el estado normal es 'readonly'
        self.entry_ambiente.config(state="disabled" if bloquear else "readonly")
        self.entry_base.config(state=state)
        self.entry_tabla.config(state=state)
        self.entry_campo.config(state=state)
        self.entry_valor.config(state=state)
        self.entry_condicion.config(state=state)
        self.btn_continuar.config(state=state)
        self.btn_salir.config(state=state)

    def on_ejecutar(self):
        ambiente = self.entry_ambiente.get().strip()
        base = self.entry_base.get().strip()
        tabla = self.entry_tabla.get().strip()
        campo = self.entry_campo.get().strip()
        valor = self.entry_valor.get().strip()
        condicion = self.entry_condicion.get().strip()

        if not all([ambiente, base, tabla, campo, valor, condicion]):
            messagebox.showerror("Error de validación", "Todos los campos son obligatorios.")
            return
        if re.search(r'\bwhere\b', condicion, re.I):
            messagebox.showerror("Error de validación", "No incluya la palabra 'WHERE' en la condición.")
            return

        # --- Lógica mejorada para incluir ambientes relacionados ---
        ambientes_a_afectar_nombres = [ambiente]
        if ambiente in self.ambientes_rel:
            ambientes_a_afectar_nombres.extend(self.ambientes_rel[ambiente])
        
        ambientes_dic = {a['nombre']: a for a in self.ambientes_lista}
        ambientes_obj_a_afectar = [ambientes_dic.get(nombre) for nombre in ambientes_a_afectar_nombres if ambientes_dic.get(nombre)]

        confirm_msg = (
            f"Se intentará ejecutar la modificación en los siguientes ambientes:\n\n"
            f"- {chr(10).join(ambientes_a_afectar_nombres)}\n\n"
            "Esta acción puede ser irreversible. ¿Desea continuar?"
        )
        if not messagebox.askyesno("Confirmar Modificación", confirm_msg):
            return

        self.bloquear_campos(True)
        self.progress.lift()
        self.progress.start(10)

        params = {"base": base, "tabla": tabla, "campo": campo, "valor": valor, "condicion": condicion}
        
        threading.Thread(
            target=self.proceso_de_modificacion,
            args=(ambientes_obj_a_afectar, params),
            daemon=True
        ).start()

    def proceso_de_modificacion(self, ambientes_a_modificar, params):
        resultados = []
        for amb in ambientes_a_modificar:
            try:
                conn_str = self._cadena_conexion(amb, params['base'])
                with pyodbc.connect(conn_str, timeout=5) as conn:
                    with conn.cursor() as cursor:
                        # 1. Respaldo (SELECT)
                        select_sql = f"SELECT * FROM {params['tabla']} WHERE {params['condicion']}"
                        cursor.execute(select_sql)
                        columnas = [column[0] for column in cursor.description]
                        filas = cursor.fetchall()

                        if not filas:
                            resultados.append(f"[{amb['nombre']}] - INFO: No se encontraron registros que cumplan la condición.")
                            continue
                        
                        self._respaldar_registros(columnas, filas, params, amb['nombre'])
                        
                        # 2. Modificación (UPDATE)
                        update_sql = f"UPDATE {params['tabla']} SET {params['campo']} = ? WHERE {params['condicion']}"
                        cursor.execute(update_sql, params['valor'])
                        filas_afectadas = cursor.rowcount
                        conn.commit()
                        resultados.append(f"[{amb['nombre']}] - ÉXITO: {filas_afectadas} fila(s) modificada(s).")

            except Exception as e:
                resultados.append(f"[{amb['nombre']}] - ERROR: {e}")

        resumen_final = "\n".join(resultados)
        self.after(0, self._finalizar, resumen_final)

    def _finalizar(self, mensaje):
        self.progress.stop()
        self.progress.lower()
        self.bloquear_campos(False)
        messagebox.showinfo("Resultado", mensaje)

    def _cadena_conexion(self, ambiente, base):
        driver = ambiente.get('driver', 'SQL Server')
        if driver == 'Sybase ASE ODBC Driver':
            return (
                f"DRIVER={{{driver}}};"
                f"SERVER={ambiente['ip']};"
                f"PORT={ambiente['puerto']};"
                f"DATABASE={base};"
                f"UID={ambiente['usuario']};"
                f"PWD={ambiente['clave']};"
            )
        else:
            return (
                f"DRIVER={{{driver}}};"
                f"SERVER={ambiente['ip']},{ambiente['puerto']};"
                f"DATABASE={base};"
                f"UID={ambiente['usuario']};"
                f"PWD={ambiente['clave']};"
            )

    def _respaldar_registros(self, columnas, filas, params, ambiente_nombre):
        # --- Ruta de respaldo mejorada y segura ---
        try:
            folder = os.path.join(os.path.expanduser("~"), "Documents", "ZetaOne_Respaldos")
            os.makedirs(folder, exist_ok=True)
            fecha = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre = f"{params['tabla']}_{ambiente_nombre}_{fecha}.txt"
            path = os.path.join(folder, nombre)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"--- Respaldo previo a modificación ---\n")
                f.write(f"Tabla: {params['tabla']}\nAmbiente: {ambiente_nombre}\nCondición: {params['condicion']}\nFecha: {fecha}\n\n")
                f.write('\t'.join(columnas) + '\n')
                for fila in filas:
                    f.write('\t'.join([str(campo) for campo in fila]) + '\n')
        except Exception as e:
            print(f"ADVERTENCIA: No se pudo crear el archivo de respaldo: {e}")

    def on_salir(self):
        self.destroy()