import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import json
import getpass
import pyodbc

# --- Imports corregidos y optimizados ---
# Se importa directamente desde la raíz del proyecto
from styles import etiqueta_titulo, entrada_estandar, boton_accion
from util_rutas import recurso_path
import ttkbootstrap as tb
from ttkbootstrap.constants import *

class desbloquearUsuVentana(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Desbloquear Usuario")
        self.protocol("WM_DELETE_WINDOW", self.on_salir)
        
        # Configuración de la ventana
        ventana_ancho = 400
        ventana_alto = 200
        pantalla_ancho = self.winfo_screenwidth()
        pantalla_alto = self.winfo_screenheight()
        x = int((pantalla_ancho / 2) - (ventana_ancho / 2))
        y = int((pantalla_alto / 2) - (ventana_alto / 2))
        self.geometry(f"{ventana_ancho}x{ventana_alto}+{x}+{y}")
        self.resizable(False, False)

        # --- SECCIÓN CORREGIDA: Carga de archivos JSON con recurso_path ---
        self.ambientes = []
        self.ambientes_rel = {}
        try:
            # Usamos recurso_path para encontrar las rutas correctas
            ruta_ambientes = recurso_path("json", "ambientes.json")
            ruta_relaciones = recurso_path("json", "ambientesrelacionados.json")

            with open(ruta_ambientes, "r", encoding="utf-8") as f:
                self.ambientes = json.load(f)
            
            # El archivo de relaciones es opcional, no debe detener la app si no existe
            if os.path.exists(ruta_relaciones):
                with open(ruta_relaciones, "r", encoding="utf-8") as f:
                    self.ambientes_rel = json.load(f)
            else:
                 self.ambientes_rel = {}

        except FileNotFoundError as e:
            messagebox.showerror("Error de Archivo", f"No se pudo encontrar el archivo de configuración 'ambientes.json':\n{e}")
            self.destroy()
            return
        except Exception as e:
            messagebox.showerror("Error de Carga", f"No se pudieron cargar los archivos JSON:\n{e}")
            self.destroy()
            return
        # --- FIN DE SECCIÓN CORREGIDA ---

        self._armar_interfaz()

    def _armar_interfaz(self):
        lbl_amb = etiqueta_titulo(self, texto="Ambiente:")
        lbl_amb.place(x=30, y=20)
        
        nombres_ambiente = [a['nombre'] for a in self.ambientes]
        self.cmb_ambiente = ttk.Combobox(self, values=nombres_ambiente, state="readonly")
        self.cmb_ambiente.place(x=120, y=20, width=200)
        if nombres_ambiente:
            self.cmb_ambiente.current(0)

        lbl_usuario = etiqueta_titulo(self, texto="Usuario:")
        lbl_usuario.place(x=30, y=60)
        
        self.ent_usuario = entrada_estandar(self)
        self.ent_usuario.place(x=120, y=60, width=200)
        self.ent_usuario.insert(0, getpass.getuser())

        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.place(x=30, y=110, width=340)

        self.btn_actualizar = boton_accion(self, "Desbloquear", comando=self.on_continuar)
        self.btn_actualizar.place(x=70, y=145, width=120)
        
        self.btn_salir = boton_accion(self, "Salir", comando=self.on_salir)
        self.btn_salir.place(x=210, y=145, width=120)

    def on_salir(self):
        self.destroy()

    def on_continuar(self):
        ambiente_seleccionado = self.cmb_ambiente.get()
        usuario = self.ent_usuario.get().strip()
        
        if not ambiente_seleccionado or not usuario:
            messagebox.showwarning("Campos requeridos", "Elija un ambiente e ingrese un usuario.")
            return

        ambientes_a_afectar = [ambiente_seleccionado]
        if ambiente_seleccionado in self.ambientes_rel:
            ambientes_a_afectar.extend(self.ambientes_rel[ambiente_seleccionado])

        ambientes_dic = {a["nombre"]: a for a in self.ambientes if a["nombre"] in ambientes_a_afectar}
        if not ambientes_dic:
            messagebox.showerror("Error", "No se encontró información de los ambientes seleccionados.")
            return

        confirmar = messagebox.askyesno(
            "Confirmar Desbloqueo",
            f"Se intentará desbloquear al usuario '{usuario}' en los siguientes ambientes:\n\n- " + 
            "\n- ".join(ambientes_a_afectar) + 
            "\n\n¿Desea continuar?"
        )
        if not confirmar:
            return
            
        self._deshabilitar_ui(True)
        self.progress.start(10)
        
        # Ejecutar la lógica de base de datos en un hilo para no congelar la interfaz
        threading.Thread(
            target=self._actualizar_multi_amb,
            args=(ambientes_a_afectar, ambientes_dic, usuario),
            daemon=True
        ).start()

    def _ejecutar_borrado_en_amb(self, amb, usuario):
        """Función aislada para ejecutar el borrado en un solo ambiente."""
        try:
            driver = amb.get('driver', 'SQL Server')
            if driver == 'Sybase ASE ODBC Driver':
                conn_str = f"DRIVER={{{driver}}};SERVER={amb['ip']};PORT={amb['puerto']};DATABASE={amb['base']};UID={amb['usuario']};PWD={amb['clave']};"
            else:
                conn_str = f"DRIVER={{{driver}}};SERVER={amb['ip']},{amb['puerto']};DATABASE={amb['base']};UID={amb['usuario']};PWD={amb['clave']};"
            
            with pyodbc.connect(conn_str, timeout=5) as conn:
                with conn.cursor() as cursor:
                    # Se usa la consulta correcta para desbloquear sesión
                    query = "DELETE FROM cobis..ts_session WHERE ss_login = ?"
                    cursor.execute(query, usuario)
                    conn.commit()
            return f"{amb['nombre']}: Sesión de '{usuario}' eliminada correctamente."

        except Exception as e:
            return f"{amb['nombre']}: Error - {e}"

    def _actualizar_multi_amb(self, ambientes_a_afectar, ambientes_dic, usuario):
        resultados = []
        for nombre_amb in ambientes_a_afectar:
            amb = ambientes_dic.get(nombre_amb)
            if not amb:
                resultados.append(f"{nombre_amb}: No se encontró información del ambiente.")
                continue
            
            resultado_msg = self._ejecutar_borrado_en_amb(amb, usuario)
            resultados.append(resultado_msg)

        resumen = "\n".join(resultados)
        
        # Actualizar la interfaz gráfica desde el hilo principal
        self.after(0, self.progress.stop)
        self.after(0, self._deshabilitar_ui, False) # Llama a _deshabilitar_ui con False
        self.after(0, lambda: messagebox.showinfo("Resultado del Desbloqueo", resumen))

    def _deshabilitar_ui(self, deshabilitar):
        estado = "disabled" if deshabilitar else "normal"
        self.cmb_ambiente.config(state=estado if deshabilitar else "readonly")
        self.ent_usuario.config(state=estado)
        self.btn_actualizar.config(state=estado)
        self.btn_salir.config(state=estado)