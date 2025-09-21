import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import json
import pyodbc

# estilos
from styles import etiqueta_titulo, entrada_estandar, boton_accion
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from util_rutas import recurso_path

class UsuarioNoVigenteVentana(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Usuario no vigente")
        self.protocol("WM_DELETE_WINDOW", self.on_salir)
        ventana_ancho = 400
        ventana_alto = 200
        pantalla_ancho = self.winfo_screenwidth()
        pantalla_alto = self.winfo_screenheight()
        x = int((pantalla_ancho / 2) - (ventana_ancho / 2))
        y = int((pantalla_alto / 2) - (ventana_alto / 2))
        self.geometry(f"{ventana_ancho}x{ventana_alto}+{x}+{y}")
        self.resizable(False, False)

        # --- SECCIÓN CORREGIDA Y ROBUSTA ---
        self.ambientes = []
        self.ambientes_rel = {}
        try:
            # Carga el archivo de ambientes (este es obligatorio)
            ruta_ambientes = recurso_path("json", "ambientes.json")
            with open(ruta_ambientes, "r", encoding="utf-8") as f:
                self.ambientes = json.load(f)

            # Carga el archivo de relaciones (este es opcional)
            ruta_relaciones = recurso_path("json", "ambientesrelacionados.json")
            if os.path.exists(ruta_relaciones):
                with open(ruta_relaciones, "r", encoding="utf-8") as f:
                    self.ambientes_rel = json.load(f)
            else:
                # Si el archivo no existe, simplemente continuamos con un diccionario vacío
                print("ADVERTENCIA: No se encontró 'ambientesrelacionados.json'. Se continuará sin relaciones.")
                self.ambientes_rel = {}

        except FileNotFoundError as e:
            # Este error solo saltará si 'ambientes.json' no se encuentra
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
        self.cmb_ambiente.place(x=120, y=20)
        if nombres_ambiente:
            self.cmb_ambiente.current(0)

        lbl_usuario = etiqueta_titulo(self, texto="Usuario:")
        lbl_usuario.place(x=30, y=60)
        self.ent_usuario = entrada_estandar(self)
        self.ent_usuario.place(x=120, y=60, width=180)

        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.place(x=30, y=110, width=340)

        self.btn_actualizar = boton_accion(self, "Actualizar", comando=self.enviar_update_usuario)
        self.btn_actualizar.place(x=70, y=145, width=100)
        self.btn_salir = boton_accion(self, "Salir", comando=self.on_salir)
        self.btn_salir.place(x=220, y=145, width=100)

    def on_salir(self):
        self.destroy()

    def enviar_update_usuario(self):
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

        consulta_resultados = self.consulta_resumen_ambientes(ambientes_a_afectar, ambientes_dic, usuario)

        resumen = ""
        total_afectados = 0
        hubo_errores = False
        for nombre_amb, res in consulta_resultados.items():
            if res['estado'] == "ok":
                resumen += f"{nombre_amb}: Encontrado(s) {res['no_vigentes']} usuario(s) no vigentes\n"
                total_afectados += res['no_vigentes']
            else:
                resumen += f"{nombre_amb}: {res['mensaje']}\n"
                hubo_errores = True

        # --- LÓGICA CORREGIDA PARA MANEJO DE ERRORES ---
        # Si no hay nada que actualizar...
        if total_afectados == 0:
            # ...y además hubo errores, muestra el resumen de errores.
            if hubo_errores:
                messagebox.showerror(
                    "Error de Conexión",
                    f"No se pudo consultar uno o más ambientes. Verifique su conexión (VPN).\n\nDetalle:\n{resumen}"
                )
            # ...y no hubo errores, entonces sí informa que no hay cambios.
            else:
                messagebox.showinfo(
                    "No hay cambios",
                    "No se encontraron usuarios no vigentes para actualizar en los ambientes seleccionados."
                )
            return

        if not messagebox.askyesno(
            "Confirmar actualización",
            f"Se actualizarán los siguientes ambientes para usuario '{usuario}':\n\n{resumen}\n¿Desea continuar?"
        ):
            return

        self.progress.start()
        self._deshabilitar_ui(True)
        threading.Thread(
            target=self._actualizar_multi_amb,
            args=(ambientes_a_afectar, ambientes_dic, usuario, consulta_resultados),
            daemon=True
        ).start()

    def consulta_resumen_ambientes(self, ambientes_a_afectar, ambientes_dic, usuario):
        resultado = {}
        for nombre_amb in ambientes_a_afectar:
            amb = ambientes_dic.get(nombre_amb)
            if not amb:
                resultado[nombre_amb] = {"estado": "error", "mensaje": "No hay info del ambiente."}
                continue
            
            # REFACTOR: Centralizar la creación de la cadena de conexión
            # Se podría mover esta lógica a un archivo de utilidades (p. ej. util_db.py)
            # def crear_cadena_conexion(amb, base=None): ...
            driver = amb.get('driver', 'SQL Server')
            conn_str_parts = [
                f"DRIVER={{{driver}}}",
                f"SERVER={amb['ip']},{amb['puerto']}" if 'sql server' in driver.lower() else f"SERVER={amb['ip']};PORT={amb['puerto']}",
                f"DATABASE={amb['base']}",
                f"UID={amb['usuario']}",
                f"PWD={amb['clave']}",
            ]
            conn_str = ";".join(conn_str_parts) + ";"

            try:
                conn = pyodbc.connect(conn_str, timeout=5)
                cursor = conn.cursor()
                query_revisar = "SELECT COUNT(*) FROM cobis..ad_usuario WHERE us_login = ? AND us_estado <> 'V'"
                cursor.execute(query_revisar, usuario)
                count_no_vigente = cursor.fetchone()[0]
                cursor.close()
                conn.close()
                resultado[nombre_amb] = {"estado": "ok", "no_vigentes": count_no_vigente, "conn_str": conn_str}
            except Exception as e:
                # --- Mensaje de error más específico ---
                mensaje_error = "Error de conexión."
                if "timeout" in str(e).lower():
                    mensaje_error = "Tiempo de espera agotado (verifique VPN)."
                elif "login failed" in str(e).lower():
                    mensaje_error = "Credenciales incorrectas."
                resultado[nombre_amb] = {"estado": "error", "mensaje": mensaje_error}
        return resultado

    def _actualizar_multi_amb(self, ambientes_a_afectar, ambientes_dic, usuario, consulta_resultados):
        resultados = []
        for nombre_amb in ambientes_a_afectar:
            res = consulta_resultados.get(nombre_amb)
            if not res or res['estado'] != "ok" or res.get("no_vigentes", 0) == 0:
                if res and res['estado'] == "error":
                    resultados.append(f"{nombre_amb}: {res['mensaje']}")
                continue
            
            conn_str = res['conn_str']
            try:
                conn = pyodbc.connect(conn_str, timeout=5)
                cursor = conn.cursor()
                query = "UPDATE cobis..ad_usuario SET us_estado = 'V' WHERE us_login = ? AND us_estado <> 'V'"
                cursor.execute(query, usuario)
                conn.commit()
                cursor.close()
                conn.close()
                resultados.append(f"{nombre_amb}: Actualizado correctamente ({res.get('no_vigentes', 0)} usuario/s).")
            except Exception as e:
                resultados.append(f"{nombre_amb}: Revise la conexión al ambiente.")

        resumen = "\n".join(resultados) or "No hubo cambios."
        self.after(0, self.progress.stop)
        self.after(0, self._habilitar_ui)
        if any("Actualizado correctamente" in line for line in resultados):
            self.after(0, lambda: messagebox.showinfo("Resultado", resumen))
        else:
            self.after(0, lambda: messagebox.showerror("Resultado", resumen))

    def _deshabilitar_ui(self, state):
        state_str = "disabled" if state else "normal"
        self.cmb_ambiente.configure(state=state_str)
        self.ent_usuario.configure(state=state_str)
        self.btn_actualizar.configure(state=state_str)
        self.btn_salir.configure(state=state_str)

    def _habilitar_ui(self):
        self._deshabilitar_ui(False)

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    UsuarioNoVigenteVentana(root)
    root.mainloop()