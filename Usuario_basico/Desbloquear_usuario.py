import getpass
from tkinter import ttk, messagebox
import tkinter as tk
import os
import json

# 🔵 AGREGADO: Para importar 'styles' desde la carpeta superior
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# estilos
from styles import etiqueta_titulo, entrada_estandar, boton_accion
from ttkbootstrap.constants import *

class desbloquearUsuVentana(tk.Toplevel):
    def __init__(self, parent, ambientes_lista, callback_confirmar, master=None):
        # iniciadores
        super().__init__(parent)
        self.title("desbloquear usuario")
        self.protocol("WM_DELETE_WINDOW", self.on_salir)

        # configuracion de ventana
        ventana_ancho = 320
        ventana_alto = 200
        pantalla_ancho = self.winfo_screenwidth()
        pantalla_alto = self.winfo_screenheight()
        x = int((pantalla_ancho / 2) - (ventana_ancho / 2))
        y = int((pantalla_alto / 2) - (ventana_alto / 2))
        self.geometry(f"{ventana_ancho}x{ventana_alto}+{x}+{y}")
        self.resizable(False, False)
        print("esta funcion si abre")

        # Interfaz visual
        lbl_ambiente = etiqueta_titulo(self, texto="Ambiente:")
        lbl_ambiente.place(x=20, y=20)

        lista_nombres_ambiente = [amb['nombre'] for amb in ambientes_lista]
        self.entry_ambiente = ttk.Combobox(self, values=lista_nombres_ambiente, state='readonly')
        self.entry_ambiente.place(x=100, y=20, width=180)

        lbl_usuario = etiqueta_titulo(self, texto="Usuario:")
        lbl_usuario.place(x=20, y=60)
        self.entry_usuario = entrada_estandar(self)
        self.entry_usuario.place(x=100, y=60, width=180)
        self.entry_usuario.insert(0, getpass.getuser())

        self.btn_continuar = boton_accion(self, texto="Continuar", comando=self.on_continuar, width=12)
        self.btn_continuar.place(relx=1.0, rely=1.0, x=-200, y=-27, anchor='se')

        self.btn_salir = boton_accion(self, "Salir", comando=self.on_salir, width=12)
        self.btn_salir.place(relx=1.0, rely=1.0, x=-40, y=-27, anchor='se')

        # Progress bar (rueda de progreso, oculta inicialmente)
        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.place(x=60, y=110, width=200, height=14)
        self.progress.lower()  # queda invisible/trasera

        # referencias
        self.ambientes_lista = ambientes_lista
        self.callback_confirmar = callback_confirmar

    def bloquear_campos(self, bloquear=True):
        # Bloquea o desbloquea los widgets
        state = "disabled" if bloquear else "normal"
        self.entry_ambiente.config(state=state)
        self.entry_usuario.config(state=state)
        self.btn_continuar.config(state=state)
        self.btn_salir.config(state=state)

    def on_continuar(self):
        ambiente = self.entry_ambiente.get()
        usuario = self.entry_usuario.get()
        if not ambiente or not usuario: 
            messagebox.showwarning("Campo/s vacío/s", "Por favor complete ambos campos.")
            return
        ambiente_obj = next((a for a in self.ambientes_lista if a['nombre'] == ambiente), None)
        if ambiente_obj is None:
            messagebox.showerror("Ambiente no encontrado", "Por favor seleccione un ambiente válido.")
            return

        # BLOQUEAR y mostrar la rueda de progreso
        self.bloquear_campos(True)
        self.progress.lift()
        self.progress.start(10)

        # Ejecutar el desbloqueo en la cola de eventos (permite animación)
        self.after(200, lambda: self.desbloquear_y_terminar(usuario, ambiente_obj))

    def desbloquear_y_terminar(self, usuario, ambiente_obj):
        self.desbloquear_usuario_en_bd(usuario, ambiente_obj)
        self.progress.stop()
        self.progress.lower()
        self.bloquear_campos(False)
        # callback si quieres mantenerlo. Finalmente, cerrar
        if self.callback_confirmar:
            self.callback_confirmar(usuario, ambiente_obj)
        self.destroy()

    def on_salir(self):
        self.destroy()

    def desbloquear_usuario_en_bd(self, usuario, ambiente):
        import pyodbc
        resp = messagebox.askyesno(
            "Confirmar acción",
            f"¿Está seguro de borrar la sesión en '{ambiente['nombre']}' para el usuario '{usuario}'?"
        )
        if not resp:
            return messagebox.showinfo("Cancelado", "Acción cancelada por el usuario.")

        def ejecutar_borrado(amb, usuario):
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
            print(f"[DEBUG] Borrando en ambiente: {amb['nombre']} con cadena: {conn_str}")
            try:
                conn = pyodbc.connect(conn_str, timeout=5)
                cursor = conn.cursor()
                cursor.execute("delete cobis..in_login where lo_login = ?", usuario)
                conn.commit()
                conn.close()
                print(f"[DEBUG] Éxito en ambiente: {amb['nombre']}")
                return True, ""
            except Exception as e:
                print(f"[DEBUG] Error en ambiente: {amb['nombre']} -> {e}")
                return False, str(e)

        exito_p, error_p = ejecutar_borrado(ambiente, usuario)
        mensaje_final = ""

        if exito_p:
            mensaje_final += f"Sesión del usuario '{usuario}' borrada correctamente en el ambiente '{ambiente['nombre']}'.\n"
            # ruta absoluta a la carpeta json, suponiendo siempre bajo la raíz del proyecto
            proyecto_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            carpeta_json = os.path.join(proyecto_base, "json")
            ruta_rel = os.path.join(carpeta_json, "ambientesrelacionados.json")
            ruta_ambientes = os.path.join(carpeta_json, "ambientes.json")
            print(f"[DEBUG] cwd: {os.getcwd()}")
            print(f"[DEBUG] ruta_rel: {ruta_rel}")
            print(f"[DEBUG] ruta_ambientes: {ruta_ambientes}")
            print(f"[DEBUG] Existe ambientesrelacionados.json: {os.path.exists(ruta_rel)}")
            print(f"[DEBUG] Existe ambientes.json: {os.path.exists(ruta_ambientes)}")

            if os.path.exists(ruta_rel) and os.path.exists(ruta_ambientes):
                with open(ruta_rel, 'r', encoding='utf-8') as f:
                    relaciones = json.load(f)
                print(f"[DEBUG] JSON ambientesrelacionados.json: {relaciones}")

                ambiente_nombre = ambiente['nombre'].strip().casefold()
                print(f"[DEBUG] Ambiente principal: {ambiente['nombre']!r}")
                print(f"[DEBUG] Ambiente principal normalizado: {ambiente_nombre!r}")

                relaciones_norm = {k.strip().casefold(): v for k, v in relaciones.items()}
                print(f"[DEBUG] Llaves en relaciones_norm: {list(relaciones_norm.keys())}")
                print(f"[DEBUG] existe? --> {ambiente_nombre in relaciones_norm}")

                if ambiente_nombre in relaciones_norm and relaciones_norm[ambiente_nombre]:
                    with open(ruta_ambientes, 'r', encoding='utf-8') as f:
                        ambientes_todos = json.load(f)
                    ambientes_dict = {a['nombre'].strip().casefold(): a for a in ambientes_todos if 'nombre' in a}
                    for rel_nombre in relaciones_norm[ambiente_nombre]:
                        rel_nombre_norm = rel_nombre.strip().casefold()
                        print(f"[DEBUG] Procesando relacionado: '{rel_nombre}' (normalizado: '{rel_nombre_norm}')")
                        print(f"[DEBUG] Ambientes disponibles para relacionar: {list(ambientes_dict.keys())}")
                        if rel_nombre_norm in ambientes_dict:
                            rel_amb = ambientes_dict[rel_nombre_norm]
                            exito, error = ejecutar_borrado(rel_amb, usuario)
                            if exito:
                                mensaje_final += f"Sesión del usuario '{usuario}' también borrada en el ambiente relacionado '{rel_nombre.strip()}'.\n"
                            else:
                                mensaje_final += f"[ERROR] al eliminar en relacionado '{rel_nombre.strip()}': {error}\n"
                        else:
                            mensaje_final += f"[ADVERTENCIA] Ambiente relacionado '{rel_nombre.strip()}' no encontrado en ambientes.json\n"
                else:
                    print(f"[DEBUG] No hay relacionados para {ambiente_nombre}")
            else:
                print("[DEBUG] No existe ambientesrelacionados.json o ambientes.json")
        else:
            mensaje_final += f"[ERROR] en ambiente '{ambiente['nombre']}': {error_p}"

        messagebox.showinfo("Resultado", mensaje_final)