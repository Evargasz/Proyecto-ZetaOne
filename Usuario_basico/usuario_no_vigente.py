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

        # Resolviendo rutas a los JSON
        self.proyecto_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.json_path_ambientes = os.path.join(self.proyecto_base, "json", "ambientes.json")
        self.json_path_rel = os.path.join(self.proyecto_base, "json", "ambientesrelacionados.json")

        self.ambientes = []
        self.ambientes_rel = {}
        try:
            with open(self.json_path_ambientes, "r", encoding="utf-8") as f:
                self.ambientes = json.load(f)
            with open(self.json_path_rel, "r", encoding="utf-8") as f:
                self.ambientes_rel = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los archivos JSON:\n{e}")
            self.destroy()
            return

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

        # Determinar ambientes afectados (principal y relacionados)
        ambientes_a_afectar = [ambiente_seleccionado]
        if ambiente_seleccionado in self.ambientes_rel:
            ambientes_a_afectar.extend(self.ambientes_rel[ambiente_seleccionado])

        # Obtener datos de conexión de cada ambiente
        ambientes_dic = {a["nombre"]: a for a in self.ambientes if a["nombre"] in ambientes_a_afectar}
        if not ambientes_dic:
            messagebox.showerror("Error", "No se encontró información de los ambientes seleccionados.")
            return

        # 1. Consulta previa: Muestra cuántos registros serán afectados
        consulta_resultados = self.consulta_resumen_ambientes(ambientes_a_afectar, ambientes_dic, usuario)
        if not consulta_resultados:
            messagebox.showerror("Sin conexión", "No se pudo consultar el estado de ningún ambiente. Verifique su conexión.")
            return

        resumen = ""
        total_afectados = 0
        for nombre_amb, res in consulta_resultados.items():
            if res['estado'] == "ok":
                resumen += f"{nombre_amb}: Encontrado(s) {res['no_vigentes']} usuario(s) no vigentes\n"
                total_afectados += res['no_vigentes']
            else:
                resumen += f"{nombre_amb}: {res['mensaje']}\n"

        if total_afectados == 0:
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

        # 2. Ejecutar los updates en hilo aparte
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
            try:
                driver = amb.get('driver', "")
                if driver == 'Sybase ASE ODBC Driver':
                    conn_str = (
                        f"DRIVER={{{driver}}};"
                        f"SERVER={amb['ip']};"
                        f"PORT={amb['puerto']};"
                        f"DATABASE={amb['base']};"
                        f"UID={amb['usuario']};"
                        f"PWD={amb['clave']};"
                    )
                else:
                    conn_str = (
                        f"DRIVER={{{driver}}};"
                        f"SERVER={amb['ip']},{amb['puerto']};"
                        f"DATABASE={amb['base']};"
                        f"UID={amb['usuario']};"
                        f"PWD={amb['clave']};"
                    )
                conn = pyodbc.connect(conn_str, timeout=5)
                cursor = conn.cursor()
                query_revisar = "SELECT COUNT(*) FROM cobis..ad_usuario WHERE us_login = ? AND us_estado <> 'V'"
                cursor.execute(query_revisar, usuario)
                count_no_vigente = cursor.fetchone()[0]
                cursor.close()
                conn.close()
                resultado[nombre_amb] = {"estado": "ok", "no_vigentes": count_no_vigente, "conn_str": conn_str}
            except Exception as e:
                resultado[nombre_amb] = {"estado": "error", "mensaje": "Revise la conexión al ambiente."}
        return resultado

    def _actualizar_multi_amb(self, ambientes_a_afectar, ambientes_dic, usuario, consulta_resultados):
        resultados = []
        for nombre_amb in ambientes_a_afectar:
            res = consulta_resultados.get(nombre_amb)
            if not res or res['estado'] != "ok" or res.get("no_vigentes", 0) == 0:
                # No hay nada que actualizar o hubo error en consulta
                if res and res['estado'] == "error":
                    resultados.append(f"{nombre_amb}: {res['mensaje']}")
                continue
            amb = ambientes_dic[nombre_amb]
            conn_str = res['conn_str']
            try:
                conn = pyodbc.connect(conn_str, timeout=5)
                cursor = conn.cursor()
                query = "UPDATE cobis..ad_usuario SET us_estado = 'V' WHERE us_login = ? AND us_estado <> 'V'"
                cursor.execute(query, usuario)
                conn.commit()
                cursor.close()
                conn.close()
                # USAMOS EL no_vigentes del SELECT correcto
                resultados.append(f"{nombre_amb}: Actualizado correctamente ({res.get('no_vigentes', 0)} usuario/s).")
            except Exception as e:
                resultados.append(f"{nombre_amb}: Revise la conexión al ambiente.")
        # Mostrar resultados y desbloquear UI
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