import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import os
import json
import re
import logging

# Importación de estilos personalizados
from styles import etiqueta_titulo, entrada_estandar, boton_accion, boton_exito, boton_rojo
import ttkbootstrap as tb
from ttkbootstrap.constants import *

#Linkeo de ventanas
from Usuario_basico.migrar_tabla import migrar_tabla, consultar_tabla_e_indice
from Usuario_basico.migrar_grupo import migrar_grupo, MigracionGruposGUI
from Usuario_basico.historialConsultas import HistorialConsultasVen, cargar_historial, guardar_historial

CATALOGO_FILE = "catalogo_migracion.json"

def es_nombre_tabla_valido(nombre):
    return bool(re.match(r'^[A-Za-z0-9_.]+$', nombre.strip()))

def cargar_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.exception(f"Error leyendo {path}: {e}")
        return None

def guardar_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.exception(f"Error guardando {path}: {e}")

class ToolTip:
    """Tooltip simple para widgets de Tkinter."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        widget.bind("<Enter>", self.show_tooltip)
        widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 30
        y = y + self.widget.winfo_rooty() + 20
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.geometry(f"+{x}+{y}")
        label = etiqueta_titulo(
            tw, texto=self.text,
            font=("Arial", 10)
        )
        label.pack(ipadx=3)

    def hide_tooltip(self, event=None):
        tw = self.tooltip_window
        if tw:
            tw.destroy()
            self.tooltip_window = None

class MigracionVentana(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Migración de tablas ||  grupos")
        self.resizable(False, False)
        self.geometry("900x560")
        self.protocol("WM_DELETE_WINDOW", self.on_salir)
        self.variables_inputs = {}
        self.tablas_con_errores = []
        self.info_tabla_origen = None
        self.cancelar_migracion = False
        self.migrando = False

        base_script = os.path.dirname(os.path.abspath(__file__))
        base_raiz = os.path.dirname(base_script)
        json_dir = os.path.join(base_raiz, "json")

        self.json_path_grupo = os.path.join(json_dir, CATALOGO_FILE)
        self.json_ambientes = os.path.join(json_dir, "ambientes.json")

        self.configurar_logging()
        self.catalogo = cargar_json(self.json_path_grupo)
        if self.catalogo is None:
            messagebox.showerror("Error", f"No se pudo cargar {CATALOGO_FILE}. Consulte el log.")
            self.destroy()
            return

        self.ambientes = cargar_json(self.json_ambientes)
        if self.ambientes is None:
            messagebox.showerror("Error", f"No se pudo cargar ambientes.json. Consulte el log.")
            self.destroy()
            return

        self.nombres_ambientes = [a["nombre"] for a in self.ambientes]
        self._armar_interfaz()

    def is_cancelled(self):
        return self.cancelar_migracion

    def configurar_logging(self):
        logging.basicConfig(
            filename="log_migracion.txt",
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s'
        )

    def log(self, msg, nivel="info"):
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mensaje = f"[{now}] {msg}"
        color = {"info": "black", "error": "red", "warning": "darkorange", "success": "green"}.get(nivel, "black")
        if hasattr(self, "log_box"):
            self.log_box.config(state="normal")
            self.log_box.insert(tk.END, mensaje + "\n", nivel)
            self.log_box.tag_config(nivel, foreground=color)
            self.log_box.see(tk.END)
            self.log_box.config(state="disabled")
        getattr(logging, nivel if nivel in ["info", "error", "warning"] else "info")(msg)

    def _armar_interfaz(self):
        panel_superior = tk.Frame(self)
        panel_superior.pack(fill='x', padx=18, pady=8)

        self.tipo_var = tk.StringVar(value="tabla")
        self.ventana_tabla = tk.Radiobutton(panel_superior, text="Tabla a tabla", variable=self.tipo_var, value="tabla", command=self.toggle_tipo)
        self.ventana_tabla.grid(row=0, column=0, sticky="w")
        
        self.ventana_grupo = tk.Radiobutton(panel_superior, text="Grupo de selección", variable=self.tipo_var, value="grupo", command=self.toggle_tipo)
        self.ventana_grupo.grid(row=0, column=1, sticky="w", padx=15)

        etiqueta_titulo(panel_superior, texto="Ambiente origen:").grid(row=1, column=0, sticky="e", pady=8)
        self.combo_amb_origen = ttk.Combobox(panel_superior, values=self.nombres_ambientes, state="readonly", width=28)
        self.combo_amb_origen.grid(row=1, column=1, pady=8, sticky="w")
        self.combo_amb_origen.set("Selecciona un ambiente")

        etiqueta_titulo(panel_superior, texto="Ambiente destino:").grid(row=2, column=0, sticky="e")
        self.combo_amb_destino = ttk.Combobox(panel_superior, values=self.nombres_ambientes, state="readonly", width=28)
        self.combo_amb_destino.grid(row=2, column=1, pady=2, sticky="w")
        self.combo_amb_destino.set("Selecciona un ambiente")

        self.combo_amb_origen.bind("<<ComboboxSelected>>", lambda e: self.actualizar_combos_ambientes("origen"))
        self.combo_amb_destino.bind("<<ComboboxSelected>>", lambda e: self.actualizar_combos_ambientes("destino"))
        self.actualizar_combos_ambientes("origen")

        main_panel = tk.Frame(self)
        main_panel.pack(fill='x', padx=35, pady=(2, 0))

        # --- Bloque TABLA ---
        self.frame_tabla = tk.LabelFrame(main_panel, text="Tabla a tabla", padx=10, pady=10)
        self.frame_tabla.pack(fill='x')
        self.frame_tabla.grid_columnconfigure(1, weight=1)
        self.frame_tabla.grid_columnconfigure(2, weight=0)

        # --- Usa widgets personalizados si los tienes, sino pon los de Tkinter ---
        if "entrada_estandar" in globals():
            etiqueta_titulo(self.frame_tabla, texto="Base de datos:").grid(row=0, column=0, sticky="e")
            self.entry_db_origen = entrada_estandar(self.frame_tabla, width=24)
            self.entry_db_origen.grid(row=0, column=1, sticky="w", padx=(4, 20), pady=4)
        else:
            etiqueta_titulo(self.frame_tabla, texto="Base de datos:").grid(row=0, column=0, sticky="e")
            self.entry_db_origen = entrada_estandar(self.frame_tabla, width=24)
            self.entry_db_origen.grid(row=0, column=1, sticky="w", padx=(2, 20))

        # Historial botón
        if "boton_accion" in globals():
            self.btn_historial = boton_accion(
                self.frame_tabla,
                texto="Historial",
                comando=self.mostrar_ven_historial,
                width=22
            )
            self.btn_historial.grid(row=0, column=2, padx=(8,2), pady=0, sticky="nwe")

        if "entrada_estandar" in globals():
            etiqueta_titulo(self.frame_tabla, texto="Tabla:").grid(row=1, column=0, sticky="e")
            self.entry_tabla_origen = entrada_estandar(self.frame_tabla, width=24)
            self.entry_tabla_origen.grid(row=1, column=1, sticky="w", padx=(4, 20), pady=4)
        else:
            etiqueta_titulo(self.frame_tabla, text="Tabla:").grid(row=1, column=0, sticky="e")
            self.entry_tabla_origen = entrada_estandar(self.frame_tabla, width=24)
            self.entry_tabla_origen.grid(row=1, column=1, sticky="w", padx=(2, 20))

        self.entry_tabla_origen.configure(
            validate='key',
            validatecommand=(self.register(lambda s: re.match(r'^[A-Za-z0-9_.]*$', s) is not None), '%P')
        )

        etiqueta_titulo(self.frame_tabla, texto="Condición WHERE (opcional):").grid(row=2, column=0, sticky="e")
        self.entry_where = entrada_estandar(self.frame_tabla, width=50)
        self.entry_where.grid(row=2, column=1, padx=5, sticky="w")

        # Consultar datos
        if "boton_accion" in globals():
            self.btn_consultar = boton_accion(
                self.frame_tabla,
                texto="Consultar datos a migrar",
                comando=self.on_consultar_tabla,
                width=22
            )
        else:
            self.btn_consultar = boton_accion(
                self.frame_tabla,
                texto="Consultar datos a migrar",
                comando=self.on_consultar_tabla,
                width=22
            )
        self.btn_consultar.grid(row=1, column=2, padx=(8, 2), pady=0, sticky="nwe")

        self.btn_limpiar_tabla = boton_rojo(
            self.frame_tabla, texto="Limpiar",
            cursor='hand2', comando=self.limpiar_tabla, width=12
        )
        self.btn_limpiar_tabla.grid(row=2, column=2, padx=(8,2), pady=(2,0), sticky="we")

        # --- Bloque GRUPO ---
        self.frame_grupo = tk.LabelFrame(main_panel, text="Grupo de migración", padx=10, pady=10)
        etiqueta_titulo(self.frame_grupo, texto="Grupo:").grid(row=0, column=0, sticky="e")
        self.combo_grupo = ttk.Combobox(self.frame_grupo, values=[g["grupo"] for g in self.catalogo], width=33, state="readonly")
        self.combo_grupo.grid(row=0, column=1)
        self.combo_grupo.bind('<<ComboboxSelected>>', self.on_grupo_change)

        if "boton_rojo" in globals():
            self.btn_limpiar_grupo = boton_rojo(self.frame_grupo, texto="Limpiar",
            cursor='hand2', comando=self.limpiar_grupo, width=12)
        else:
            self.btn_limpiar_grupo = boton_rojo(self.frame_grupo, texto="Limpiar", cursor='hand2', comando=self.limpiar_grupo, width=12)
        self.btn_limpiar_grupo.grid(row=0, column=2, padx=(12,0), ipadx=12, ipady=5)

        self.btn_editar_grupos = boton_accion(
            self.frame_grupo, texto="Administrar grupos...", 
            comando=self.open_admin_grupo,
            width=15
        )
        self.btn_editar_grupos.grid(row=0,column=3,padx=(18,0),ipadx=10)
        self.var_frame = tk.Frame(self.frame_grupo)
        self.var_frame.grid(row=1, column=0, columnspan=4, pady=8, sticky="w")

        #--- Botones inferiores y barra progreso ---
        frame_migrar = tk.Frame(self)
        frame_migrar.pack(pady=(13,0), anchor="center")

        if "boton_exito" in globals():
            self.btn_migrar = boton_exito(
                frame_migrar, texto="Migrar",
                comando=self.on_migrar,
                state="disabled",
                width=18
            )
        else:
            self.btn_migrar = boton_accion(
                frame_migrar, texto="Migrar",
                comando=self.on_migrar,
                state="disabled"
            )
        self.btn_migrar.pack(side="left", padx=(0,8))

        if "boton_rojo" in globals():
            self.btn_cancelar = boton_rojo(
                frame_migrar, texto="Cancelar",
                comando=self.cancelar_op,
                state="disabled",
                width=18
            )
        else:
            self.btn_cancelar = boton_rojo(
                frame_migrar, texto="Cancelar",
                comando=self.cancelar_op,
                state="disabled"
            )
        self.btn_cancelar.pack(side="left", padx=(0,8))

        # Barra progreso
        # Si tienes ttkbootstrap/tb.Progressbar úsala. Sino usa ttk.Progressbar normal
        try:
            import ttkbootstrap as tb
            self.progress = tb.Progressbar(
                self,
                bootstyle="success",
                orient="horizontal",
                length=840,
                mode="determinate"
            )
        except ImportError:
            self.progress = ttk.Progressbar(self, orient='horizontal', length=840, mode='determinate')

        self.progress['maximum'] = 100
        self.progress['value'] = 0
        self.progress.pack(padx=25, pady=(15,7))
        self.progress_lbl = etiqueta_titulo(self, texto="")
        self.progress_lbl.pack()
        log_label = etiqueta_titulo(self, texto="Log de migración:", anchor='w')
        log_label.pack(fill='x', padx=38, pady=(14, 0))
        self.log_box = scrolledtext.ScrolledText(self, width=95, height=7, state="disabled")
        self.log_box.pack(padx=30, pady=(4, 0), fill='x', expand=False)
        self.lbl_registros = etiqueta_titulo(self, texto="")
        self.lbl_registros.pack(pady=(2, 8))
        self.toggle_tipo()

    def actualizar_combos_ambientes(self, changed_combo):
        origen_sel = self.combo_amb_origen.get()
        destino_sel = self.combo_amb_destino.get()
        if changed_combo == "origen":
            values_dest = [amb for amb in self.nombres_ambientes if amb != origen_sel] 
            if destino_sel == origen_sel:
                self.combo_amb_destino.set(values_dest[0] if values_dest else '')
            self.combo_amb_destino["values"] = values_dest

        elif changed_combo == "destino":
            values_ori = [amb for amb in self.nombres_ambientes if amb != destino_sel]
            if origen_sel == destino_sel:
                self.combo_amb_origen.set(values_ori[0] if values_ori else '')
            self.combo_amb_origen["values"] = values_ori

    def limpiar_tabla(self):
        self.entry_tabla_origen.delete(0, tk.END)
        self.entry_where.delete(0, tk.END)
        self.entry_db_origen.delete(0, tk.END)
        self.info_tabla_origen = None
        self.btn_migrar["state"] = "disabled"
        self.combo_amb_origen["state"] = "readonly"
        self.combo_amb_destino["state"] = "readonly"
        self.btn_cancelar["state"] = "disabled"
        self.limpiar_consola()

    def limpiar_grupo(self):
        self.combo_grupo.set('')
        for entry in self.variables_inputs.values():
            entry.delete(0, tk.END)

    def limpiar_consola(self):
        self.log_box.config(state='normal')
        self.log_box.delete('1.0', tk.END)
        self.log_box.config(state='disabled')

    def open_admin_grupo(self):
        app = MigracionGruposGUI(self, self.reload_catalogo, json_path=self.json_path_grupo)
        app.grab_set()

    def reload_catalogo(self):
        self.catalogo = cargar_json(self.json_path_grupo) or []
        self.combo_grupo['values'] = [g["grupo"] for g in self.catalogo]
        if self.combo_grupo.get() not in self.combo_grupo['values'] and self.combo_grupo['values']:
            self.combo_grupo.set(self.combo_grupo['values'][0])
        self.on_grupo_change(None)

    def update_progress(self, percent):
        last = self.progress["value"]
        if percent > last or percent == 0 or percent == 100:
            self.progress["value"] = percent
            self.progress_lbl["text"] = f"{percent}%"
            self.update_idletasks()

    def error_migracion(self, msg):
        self.log(msg, nivel="error")
        messagebox.showerror("Error en migración", msg)
        self.progress["value"] = 0
        self.progress_lbl["text"] = ""
        self.habilitar_botones(True)

    def toggle_tipo(self):
        if self.tipo_var.get() == "tabla":
            self.frame_tabla.pack(fill='x')
            self.frame_grupo.pack_forget()
            self.btn_migrar["state"] = "disabled"
            self.btn_cancelar["state"] = "disabled"

        else:
            self.frame_grupo.pack(fill='x')
            self.frame_tabla.pack_forget()
            self.btn_migrar["state"] = "normal"
            self.btn_cancelar["state"] = "normal"

        self.lbl_registros["text"] = ""
        self.progress["value"] = 0
        self.progress_lbl["text"] = ""
        self.limpiar_consola()
        self.info_tabla_origen = None

    def on_salir(self):
        self.destroy()

    def mostrar_ven_historial(self):
        def rellenar_campos(base, tabla, where):
            self.entry_db_origen.delete(0, tk.END)
            self.entry_db_origen.insert(0, base)
            self.entry_tabla_origen.delete(0, tk.END)
            self.entry_tabla_origen.insert(0, tabla)
            self.entry_where.delete(0, tk.END)
            self.entry_where.insert(0, where)
        HistorialConsultasVen(self, callback_usar=rellenar_campos)

    def deshabilitar_controles_tabla(self):
        self.btn_consultar.config(state="disabled")
        self.btn_limpiar_tabla.config(state="disabled")
        self.btn_migrar.config(state="disabled")
        self.entry_db_origen.config(state="disabled")
        self.entry_tabla_origen.config(state="disabled")
        self.entry_where.config(state="disabled")
        self.btn_cancelar.config(state="disabled")
        self.btn_historial.config(state="disabled")
        self.ventana_tabla.config(state="disabled")
        self.ventana_grupo.config(state="disabled")
    
    def habilitar_controles_tabla(self):
        self.btn_consultar.config(state="normal")
        self.btn_limpiar_tabla.config(state="normal")
        self.btn_migrar.config(state="normal")
        self.entry_db_origen.config(state="normal")
        self.entry_tabla_origen.config(state="normal")
        self.entry_where.config(state="normal")
        self.btn_cancelar.config(state="normal")
        self.btn_historial.config(state="normal")
        self.ventana_tabla.config(state="normal")
        self.ventana_grupo.config(state="normal")

    def cancelar_op(self):
        if not self.migrando:
            messagebox.showinfo("No hay nada que cancelar","No hay ninguna migración corriendo para cancelar.")
            return
        
        respuesta = messagebox.askyesno(
            "confirmar",
            "¿Seguro que quieres cancelar la migracion en curso?\n Se perderan TODOS los datos"
        )
        if not respuesta:
            self.log("Cancelación abortada por el usuario.")
            return
        
        self.cancelar_migracion = True
        self.log("Cancelando migracion. Espera un momento...")
        self.btn_cancelar.config(state="normal")

    def on_grupo_change(self, event):
        for widget in self.var_frame.winfo_children():
            widget.destroy()
        self.variables_inputs.clear()
        grupo_nombre = self.combo_grupo.get()
        grupo_conf = next((g for g in self.catalogo if g["grupo"] == grupo_nombre), None)
        if not grupo_conf:
            return
        variables_set = set()
        regex = re.compile(r"\$(.+?)\$")
        for tabla in grupo_conf["tablas"]:
            for campo in [tabla.get("join", ""), tabla.get("condicion", "")]:
                if campo:
                    matches = regex.findall(campo)
                    variables_set.update(matches)
        if not variables_set:
            etiqueta_titulo(self.var_frame, texto="Este grupo no requiere variables de filtro.").grid(row=0, column=0)
        else:
            for idx, variable in enumerate(sorted(variables_set)):
                etiqueta_titulo(self.var_frame, texto=f"Valor para ${variable}$:").grid(row=idx, column=0, sticky="e")
                entry = entrada_estandar(self.var_frame, width=30)
                entry.grid(row=idx, column=1, padx=10)
                ToolTip(entry, f"Ingrese el valor para la variable '{variable}' en JOIN o condición WHERE.")
                self.variables_inputs[variable] = entry

    def validar_campos_obligatorios(self):
        errores = []
        if self.tipo_var.get() == "tabla":
            if not self.entry_db_origen.get().strip():
                errores.append("Base de datos (origen)")
            if not self.entry_tabla_origen.get().strip():
                errores.append("Tabla (origen)")
            if not es_nombre_tabla_valido(self.entry_tabla_origen.get().strip()):
                errores.append("Nombre de tabla inválido")
            if not es_nombre_tabla_valido(self.entry_db_origen.get().strip()):
                errores.append("Nombre de base inválido")
        else:
            if not self.combo_grupo.get().strip():
                errores.append("Grupo")
            for var, entry in self.variables_inputs.items():
                if not entry.get().strip():
                    errores.append(f"Valor para variable ${var}$")
        return errores

    def habilitar_botones(self, enable=True):
        st = "normal" if enable else "disabled"
        self.btn_migrar["state"] = st
        self.combo_amb_origen["state"] = "readonly" if enable else "disabled"
        self.combo_amb_destino["state"] = "readonly" if enable else "disabled"
        self.btn_editar_grupos["state"] = st
        self.btn_limpiar_grupo["state"] = st
        self.btn_consultar["state"] = st
        self.btn_limpiar_tabla["state"] = st
        self.btn_cancelar["state"] = st
        self.btn_historial["state"] = st
        self.ventana_tabla["state"] = st
        self.ventana_grupo["state"] = st

    def on_consultar_tabla(self):
        self.info_tabla_origen = None
        tabla = self.entry_tabla_origen.get().strip()
        base = self.entry_db_origen.get().strip()
        where = self.entry_where.get().strip()
        nombre_origen = self.combo_amb_origen.get()
        nombre_destino = self.combo_amb_destino.get()
        errores = []
        if not tabla:
            self.entry_tabla_origen.config(bootstyle="light")
            errores.append("Tabla (origen)")
        if not base:
            self.entry_db_origen.config(bootstyle="light")
            errores.append("Base de datos (origen)")
        if not nombre_origen or not nombre_destino:
            errores.append("Ambientes")
        if not es_nombre_tabla_valido(tabla):
            self.entry_tabla_origen.config(bootstyle="light")
            errores.append("Nombre de tabla no válido")
        if not es_nombre_tabla_valido(base):
            self.entry_db_origen.config(bootstyle="light")
            errores.append("Nombre de base no válido")
        if errores:
            self.error_migracion("Debe ingresar: " + ", ".join(errores))
            return
        amb_origen = next((a for a in self.ambientes if a["nombre"] == nombre_origen), None)
        if not amb_origen:
            self.error_migracion("Debes seleccionar un ambiente de origen válido.")
            return
        amb_destino = next((a for a in self.ambientes if a["nombre"] == nombre_destino), None)
        if not amb_destino:
            self.error_migracion("Debes seleccionar un ambiente de destino válido.")
            return
        resultado = consultar_tabla_e_indice(
            tabla, amb_origen, amb_destino, self.log, self.error_migracion, where=where, base_usuario=base
        )
        if resultado:
            self.info_tabla_origen = resultado
            self.btn_migrar["state"] = "normal"
            self.combo_amb_origen["state"] = "disabled"
            self.combo_amb_destino["state"] = "disabled"
            self.log(
                f"Tabla lista para migrar. Clave primaria: {resultado['clave_primaria']}, "
                f"Total registros: {resultado['nregs']}", nivel="info"
            )
        else:
            self.btn_migrar["state"] = "disabled"
            # self.btn_migrar["bootstyle"] = "success"
            self.btn_cancelar["state"] = "disabled"


    def on_migrar(self):
        # ventana modal de confirmacion de migración
        def dialogo_confirmacion_migracion(parent, titulo, encabezado, pares):
            win = tk.Toplevel(parent)
            win.title(titulo)
            win.grab_set()
            win.resizable(False, False)
            frame = ttk.Frame(win, padding=18)
            frame.pack()

            etiqueta_titulo(frame, texto=encabezado).pack(anchor="w", pady=(0,12))
            for clave, valor in pares:
                fila = tk.Frame(frame)
                fila.pack(anchor="w", pady=2)
                etiqueta_titulo(fila, texto=clave+":").pack(side="left")
                tb.Label(fila,
                        text=valor,
                        font=("Arial", 15, "bold"),
                        bootstyle="warning"
                    ).pack(side="left", padx=5)

            resp = {"ok": False}
            botones = tk.Frame(frame)
            botones.pack(pady=(14,0))
            def ok(): resp["ok"] = True; win.destroy()
            def canc(): win.destroy()
            boton_accion(botones, texto="si, migrar", comando=ok).pack(side="left", padx=5)
            boton_accion(botones, texto="cancelar", comando=canc). pack(side="left")
            parent.update_idletasks()
            x = parent.winfo_rootx() + 50
            y = parent.winfo_rooty() + 70
            win.geometry(f"+{x}+{y}")
            win.wait_window()
            return resp["ok"]

        errores = self.validar_campos_obligatorios()
        if self.tipo_var.get() == "tabla":
            self.entry_tabla_origen.config(bootstyle="light" if not self.entry_tabla_origen.get().strip() else "white")
            self.entry_db_origen.config(bootstyle="light" if not self.entry_db_origen.get().strip() else "white")
        else:
            for var, entry in self.variables_inputs.items():
                entry.config(bootstyle="light" if not entry.get().strip() else "white")
        if errores:
            messagebox.showerror("Campos requeridos", "Debes completar:\n- " + "\n- ".join(errores))
            return

        if self.tipo_var.get() == "tabla":
            pares = [
                ("Ambiente origen", self.combo_amb_origen.get()),
                ("Ambiente destino", self.combo_amb_destino.get()),
                ("Base de datos", self.entry_db_origen.get().strip()),
                ("Tabla", self.entry_tabla_origen.get().strip())
            ]
            encabezado = "¿Estas seguro de iniciar la migracion?\n"

        respuesta = dialogo_confirmacion_migracion(
            self,
            titulo="confirmar migracion",
            encabezado=encabezado,
            pares=pares
        )

        if not respuesta:
            return

        self.cancelar_migracion = False   # <--- reinicia el flag siempre ANTES de migrar
        self.migrando = True              # <--- indica que una migración está en curso

        self.btn_migrar["state"] = "disabled"
        self.progress["value"] = 0
        self.progress_lbl["text"] = "0%"
        self.habilitar_botones(False)

        def restaurar():
            self.cancelar_migracion = False
            self.migrando = False
            self.habilitar_controles_tabla()
            self.btn_migrar["state"] = "normal"
            self.btn_cancelar["state"] = "normal"

        if self.tipo_var.get() == "tabla":
            self.deshabilitar_controles_tabla()
            self.btn_cancelar["state"] = "normal"
            threading.Thread(target=lambda: [self.do_migrar_tabla(), restaurar()], daemon=True).start()
        else:
            self.deshabilitar_controles_tabla()
            self.btn_cancelar["state"] = "normal"
            threading.Thread(target=lambda: [self.do_migrar_grupo(), restaurar()], daemon=True).start()    
    
    
    def do_migrar_tabla(self):
        self.update_progress(5)
        tabla_origen = self.entry_tabla_origen.get().strip()
        where = self.entry_where.get().strip()
        base = self.entry_db_origen.get().strip()
        nombre_origen = self.combo_amb_origen.get()
        nombre_destino = self.combo_amb_destino.get()
        if not tabla_origen or not base or not nombre_origen or not nombre_destino:
            self.update_progress(10)
            self.error_migracion("Debe ingresar todos los campos requeridos.")
            return
        if not es_nombre_tabla_valido(tabla_origen) or not es_nombre_tabla_valido(base):
            self.error_migracion('Nombre de tabla o base no válido.')
            return
        self.update_progress(15)
        amb_origen = next((a for a in self.ambientes if a["nombre"] == nombre_origen), None)
        if not amb_origen:
            self.error_migracion("Debes seleccionar un ambiente de origen válido.")
            return
        amb_destino = next(a for a in self.ambientes if a["nombre"] == nombre_destino)
        if not self.info_tabla_origen:
            self.update_progress(25)
            self.error_migracion("Debe consultar primero la estructura y clave primaria de la tabla.")
            return
        self.log(f"Iniciando migración tabla '{base}..{tabla_origen}' de {nombre_origen} a {nombre_destino}...", nivel="info")
        self.update_progress(25)
        def progress_fase(p):
            self.update_progress(25 + (p * 0.7))
        resultado_migracion = migrar_tabla(
            tabla_origen,
            where,
            amb_origen,
            amb_destino,
            log_func=self.log,
            progress_func=progress_fase,
            abort_func=self.error_migracion,
            columnas=self.info_tabla_origen['columnas'],
            clave_primaria=self.info_tabla_origen['clave_primaria'],
            base_usuario=base,
            cancelar_func=self.is_cancelled
        )
        try:
            historial = cargar_historial()
            nuevo = {"base": base, "tabla": tabla_origen, "condicion (where)": where}
            if nuevo not in historial:
                historial.insert(0, nuevo)
                historial = historial[:10]
                guardar_historial(historial)
        except Exception as e:
            self.log(f"No se pudo guardar en el historial: {e}", nivel="warning")
        self.update_progress(100)
        if resultado_migracion and resultado_migracion.get("insertados", 0) == 0:
            messagebox.showinfo("Sin migración", "No existen datos para migrar (todos duplicados o sin registros).")
            self.log("No existen datos para migrar (todo estaba duplicado o tabla vacía).", nivel="warning")
        else:
            self.log("Migración tabla a tabla finalizada.", nivel="success")
            messagebox.showinfo("Migración finalizada", "¡Migración finalizada con éxito!")
        self.habilitar_controles_tabla()
        self.btn_cancelar.config(state="normal")

    def do_migrar_grupo(self):
        grupo_nombre = self.combo_grupo.get()
        nombre_origen = self.combo_amb_origen.get()
        nombre_destino = self.combo_amb_destino.get()
        if not grupo_nombre or not nombre_origen or not nombre_destino:
            self.error_migracion("Debe escoger grupo y ambientes.")
            return
        grupo_conf = next((g for g in self.catalogo if g["grupo"] == grupo_nombre), None)
        if not grupo_conf:
            self.error_migracion("No se encontró el grupo seleccionado en el catálogo.")
            return
        variables = {var: entry.get().strip() for var, entry in self.variables_inputs.items()} if self.variables_inputs else {}
        amb_origen = next((a for a in self.ambientes if a["nombre"] == nombre_origen), None)
        if not amb_origen:
            self.error_migracion("Debes seleccionar un ambiente de origen válido.")
            return
        amb_destino = next(a for a in self.ambientes if a["nombre"] == nombre_destino)
        self.log(f"Iniciando migración de grupo '{grupo_nombre}' de {nombre_origen} a {nombre_destino}...", nivel="info")
        migrar_grupo(
            grupo_conf,
            variables,
            amb_origen,
            amb_destino,
            log_func=self.log,
            progress_func=self.update_progress,
            abort_func=self.error_migracion,
            cancelar_func=self.is_cancelled
        )
        self.update_progress(100)
        self.log("Migración de grupo finalizada.", nivel="success")
        messagebox.showinfo("Migración finalizada", "¡Migración finalizada con éxito!")
        
        #el boton cancelar sigue sin ejecutar la operacion de cancelacion, sin embargo ejecuta la accion del boton (manda el mensaje de info)
        #en conclusion no cancela la operacion de migracion