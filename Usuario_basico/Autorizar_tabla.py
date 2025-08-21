import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import json
from styles import etiqueta_titulo, entrada_estandar, boton_rojo, boton_accion
import ttkbootstrap as tb
from ttkbootstrap.constants import *

class AutorizarTablaVentana(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Autorizar SELECT en Tabla")
        self.protocol("WM_DELETE_WINDOW", self.on_salir)
        ventana_ancho = 400
        ventana_alto = 222
        pantalla_ancho = self.winfo_screenwidth()
        pantalla_alto = self.winfo_screenheight()
        x = int((pantalla_ancho / 2) - (ventana_ancho / 2))
        y = int((pantalla_alto / 2) - (ventana_alto / 2))
        self.geometry(f"{ventana_ancho}x{ventana_alto}+{x}+{y}")
        self.resizable(False, False)


        self.btn_continuar = None  # Para tener referencia al botón de continuar
        self.btn_salir = None

        # Resolviendo ruta a la carpeta json a partir de la ubicación del módulo
        self.proyecto_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.json_path = os.path.join(self.proyecto_base, "json", "ambientes.json")
        self.ambientes = []
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                self.ambientes = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar ambientes.json:\n{e}")
            self.destroy()
            return

        self._armar_interfaz()

    def _armar_interfaz(self):
        lbl_amb = etiqueta_titulo(self, texto="Ambiente:")
        lbl_amb.place(x=30, y=20)
        nombres_ambiente = [a['nombre'] for a in self.ambientes]
        self.combo_ambiente = ttk.Combobox(self, values=nombres_ambiente, state="readonly", width=23)
        self.combo_ambiente.place(x=120, y=20)
        if nombres_ambiente:
            self.combo_ambiente.set(nombres_ambiente[0])

        lbl_base = etiqueta_titulo(self, texto="Base de Datos:")
        lbl_base.place(x=30, y=60)
        self.entry_base = entrada_estandar(self, width=26)
        self.entry_base.place(x=120, y=60)

        lbl_tabla = etiqueta_titulo(self, texto="Tabla (con esquema):")
        lbl_tabla.place(x=30, y=100)
        self.entry_tabla = entrada_estandar(self, width=26)
        self.entry_tabla.place(x=160, y=100)

        self.progress = ttk.Progressbar(self, orient='horizontal', length=320, mode='indeterminate')
        self.progress.place(x=40, y=140)

        self.btn_continuar = boton_accion(self, "Continuar", comando=self.on_continuar, width=12)
        self.btn_continuar.place(x=170, y=167)

        self.btn_salir = boton_accion(self, "Salir", comando=self.on_salir, width=10)
        self.btn_salir.place(x=290, y=167)

    def on_salir(self):
        self.destroy()

    def on_continuar(self):
        ambiente_nombre = self.combo_ambiente.get()
        base = self.entry_base.get().strip()
        tabla = self.entry_tabla.get().strip()
        if not ambiente_nombre or not base or not tabla:
            messagebox.showwarning("Campos vacíos", "Por favor complete todos los campos.")
            return
        ambiente = next((a for a in self.ambientes if a['nombre'] == ambiente_nombre), None)
        if not ambiente:
            messagebox.showerror("Ambiente no encontrado", "Por favor seleccione un ambiente válido.")
            return

        self._deshabilitar_ui(True)
        self.progress.start()
        threading.Thread(
            target=self._grant_select, args=(base, tabla, ambiente),
            daemon=True
        ).start()

    def _grant_select(self, base, tabla, ambiente):
        import pyodbc
        try:
            # Confirmación en thread UI
            self.after(0, lambda: self._confirm_grant_and_execute(base, tabla, ambiente))
        except Exception as e:
            self.after(0, self._habilitar_ui)
            self.after(0, self.progress.stop)
            self.after(0, lambda: messagebox.showerror("Error", f"Ocurrió un error inesperado: {e}"))

    def _confirm_grant_and_execute(self, base, tabla, ambiente):
        resp = messagebox.askyesno(
            "Confirmar acción",
            f"¿Conceder SELECT en '{base}..{tabla}' al usuario 'consulta'\nen ambiente '{ambiente['nombre']}'?"
        )
        if resp:
            threading.Thread(
                target=self._do_grant_select, args=(base, tabla, ambiente),
                daemon=True
            ).start()
        else:
            self.progress.stop()
            self._habilitar_ui()

    def _do_grant_select(self, base, tabla, ambiente):
        import pyodbc
        try:
            driver = ambiente['driver']
            if driver == 'Sybase ASE ODBC Driver':
                conn_str = (
                    f"DRIVER={{{driver}}};"
                    f"SERVER={ambiente['ip']};"
                    f"PORT={ambiente['puerto']};"
                    f"DATABASE={base};"
                    f"UID={ambiente['usuario']};"
                    f"PWD={ambiente['clave']};"
                )
            else:
                conn_str = (
                    f"DRIVER={{{driver}}};"
                    f"SERVER={ambiente['ip']},{ambiente['puerto']};"
                    f"DATABASE={base};"
                    f"UID={ambiente['usuario']};"
                    f"PWD={ambiente['clave']};"
                )
            comando = f"GRANT SELECT ON {tabla} TO consulta"
            print(f"[DEBUG] Ejecutando: {comando} en {conn_str}")
            try:
                conn = pyodbc.connect(conn_str, timeout=8)
            except Exception as e:
                self.after(0, self._habilitar_ui)
                self.after(0, self.progress.stop)
                self.after(0, lambda: messagebox.showerror(
                    "Error de conexión",
                    f"No se pudo conectar al ambiente '{ambiente['nombre']}'.\n"
                    f"Revise su VPN o la disponibilidad del ambiente.\n\nDetalle: {e}"
                ))
                return
            cursor = conn.cursor()
            try:
                cursor.execute(comando)
                conn.commit()
                conn.close()
                self.after(0, lambda: messagebox.showinfo(
                    "Éxito",
                    f"Permiso SELECT concedido en '{base}..{tabla}' a 'consulta' en '{ambiente['nombre']}'."
                ))
            except Exception as e:
                conn.close()
                self.after(0, lambda: messagebox.showerror(
                    "Error SQL",
                    f"Ocurrió un error al ejecutar el GRANT:\n{e}"
                ))
            self.after(0, self.progress.stop)
            self.after(0, self._habilitar_ui)
        except Exception as e:
            self.after(0, self.progress.stop)
            self.after(0, self._habilitar_ui)
            self.after(0, lambda: messagebox.showerror("Error inesperado", f"{e}"))

    def _deshabilitar_ui(self, state):
        widget_state = 'disabled' if state else 'normal'
        for w in (self.combo_ambiente, self.entry_base, self.entry_tabla, self.btn_continuar, self.btn_salir):
            w.configure(state=widget_state)

    def _habilitar_ui(self):
        self._deshabilitar_ui(False)

