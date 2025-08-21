import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import json
import pyodbc

#estilos
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

        btn_actualizar = boton_accion(self, "Actualizar", comando=self.enviar_update_usuario)
        btn_actualizar.place(x=70, y=145, width=100)
        btn_salir = boton_accion(self, "Salir", comando=self.on_salir)
        btn_salir.place(x=220, y=145, width=100)

    def on_salir(self):
        self.destroy()

    def enviar_update_usuario(self):
        ambiente_seleccionado = self.cmb_ambiente.get()
        usuario = self.ent_usuario.get().strip()
        if not ambiente_seleccionado or not usuario:
            messagebox.showwarning("Campos requeridos", "Elija un ambiente e ingrese un usuario.")
            return

        ambientes_a_afectar = [ambiente_seleccionado]
        # Incluye ambientes relacionados si existen
        if ambiente_seleccionado in self.ambientes_rel:
            ambientes_a_afectar.extend(self.ambientes_rel[ambiente_seleccionado])

        # Obtiene los diccionarios de cada ambiente
        ambientes_dic = {}
        for a in self.ambientes:
            if a["nombre"] in ambientes_a_afectar:
                ambientes_dic[a["nombre"]] = a

        self.progress.start()
        threading.Thread(
            target=self._actualizar_multi_amb,
            args=(ambientes_a_afectar, ambientes_dic, usuario),
            daemon=True
        ).start()

    def _actualizar_multi_amb(self, ambientes_a_afectar, ambientes_dic, usuario):
        estados_por_ambiente = {}
        try:
            # 1. Consultar en todos los ambientes primero
            for nombre_amb in ambientes_a_afectar:
                amb = ambientes_dic.get(nombre_amb)
                if not amb:
                    estados_por_ambiente[nombre_amb] = ("info_ambiente", 0, None)
                    continue
                try:
                    driver = amb['driver']
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
                    # Conteo de registros a modificar
                    query_revisar = "SELECT COUNT(*) FROM cobis..ad_usuario WHERE us_login = ? AND us_estado <> 'V'"
                    cursor.execute(query_revisar, usuario)
                    count_no_vigente = cursor.fetchone()[0]
                    estados_por_ambiente[nombre_amb] = ("ok", count_no_vigente, conn_str)
                    cursor.close()
                    conn.close()
                except Exception as e:
                    estados_por_ambiente[nombre_amb] = ("error_conexion", 0, str(e))
            # 2. Verificar si se pudo conectar al menos a un ambiente
            hay_conexion = any(
                estados_por_ambiente[amb][0] == "ok"
                for amb in ambientes_a_afectar
            )
            if not hay_conexion:
                self.after(0, lambda: messagebox.showerror(
                    "Sin conexión",
                    "No se pudo conectar a ningún ambiente. Verifique su VPN o la disponibilidad de los ambientes."
                ))
                self.after(0, self.progress.stop)
                return
            # 3. Analizar si en al menos uno hay registros a actualizar
            existe_para_actualizar = any(
                estados_por_ambiente[amb][0] == "ok" and estados_por_ambiente[amb][1] > 0
                for amb in ambientes_a_afectar
            )
            if not existe_para_actualizar:
                self.after(0, lambda: messagebox.showinfo(
                    "Sin registros", "No hay registros para actualizar en ningún ambiente disponible."
                ))
                self.after(0, self.progress.stop)
                return
            # 4. Hacer UPDATE solo en los ambientes donde la consulta fue exitosa
            resultados = []
            for nombre_amb in ambientes_a_afectar:
                estado, reg_a_afectar, conn_info = estados_por_ambiente[nombre_amb]
                if estado == "info_ambiente":
                    resultados.append(f"{nombre_amb}: No se encontró información del ambiente.")
                    continue
                if estado == "error_conexion":
                    resultados.append(f"{nombre_amb}: Error de conexión -> {conn_info}")
                    continue
                try:
                    conn = pyodbc.connect(conn_info, timeout=5)
                    cursor = conn.cursor()
                    query = "UPDATE cobis..ad_usuario SET us_estado = 'V' WHERE us_login = ? AND us_estado <> 'V'"
                    cursor.execute(query, usuario)
                    conn.commit()
                    cursor.close()
                    conn.close()
                    resultados.append(f"{nombre_amb}: Ok (Filas actualizadas: {reg_a_afectar})")
                except Exception as e:
                    resultados.append(f"{nombre_amb}: Error al actualizar -> {e}")
            result_msg = "\n".join(resultados)
            self.after(0, lambda: messagebox.showinfo("Resultados", result_msg))
            self.after(0, self.progress.stop)
        except Exception as e:
            self.after(0, self.progress.stop)
            self.after(0, lambda: messagebox.showerror("Error grave", f"Ocurrió un error inesperado:\n{e}"))

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    UsuarioNoVigenteVentana(root)
    root.mainloop()