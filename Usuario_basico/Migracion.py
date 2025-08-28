import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import os
import json
import re

# Importación de estilos personalizados
from styles import etiqueta_titulo, entrada_estandar, boton_accion, boton_exito, boton_rojo
import ttkbootstrap as tb
from ttkbootstrap.constants import *

from Usuario_basico.migrar_tabla import migrar_tabla, consultar_tabla_e_indice
from Usuario_basico.migrar_grupo import migrar_grupo

class MigracionVentana(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Migración de tablas o grupos")
        self.resizable(False, False)
        self.geometry("900x560")
        self.protocol("WM_DELETE_WINDOW", self.on_salir)
        self.variables_inputs = {}
        self.tablas_con_errores = []
        self.info_tabla_origen = None

        self.cancelar_migracion = False

        base_script = os.path.dirname(os.path.abspath(__file__))
        base_raiz = os.path.dirname(base_script)
        json_dir = os.path.join(base_raiz, "json")
        self.json_path_grupo = os.path.join(json_dir, "catalogo_migracion.json")
        self.json_ambientes = os.path.join(json_dir, "ambientes.json")

        try:
            with open(self.json_path_grupo, "r", encoding="utf-8") as f:
                self.catalogo = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar catalogo_migracion.json:\n{e}")
            self.destroy()
            return

        try:
            with open(self.json_ambientes, "r", encoding="utf-8") as f:
                self.ambientes = json.load(f)
            self.nombres_ambientes = [a["nombre"] for a in self.ambientes]
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar ambientes.json:\n{e}")
            self.destroy()
            return

        self._armar_interfaz()
    

    # --- NUEVOS MÉTODOS AUXILIARES ---
    def reset_inputs(self, *entries):
        """Limpia los campos de entrada recibidos como argumento."""
        for entry in entries:
            entry.delete(0, tk.END)

    def set_widgets_state(self, state_map):
        """
        Recibe un diccionario: {widget: {'state': valor, 'bootstyle': valor, ...}}
        y aplica los cambios a los widgets correspondientes,
        ignorando opciones que el widget no reconoce.
            """
        for widget, props in state_map.items():
            for attr, valor in props.items():
                try:
                    widget[attr] = valor
                except tk.TclError:
                    # La opción no es válida para este widget, la ignoramos
                    pass

    def _armar_interfaz(self):
        panel_superior = tk.Frame(self)
        panel_superior.pack(fill='x', padx=18, pady=8)

        self.tipo_var = tk.StringVar(value="tabla")
        tk.Radiobutton(panel_superior, text="Tabla a tabla", variable=self.tipo_var, value="tabla", command=self.toggle_tipo).grid(row=0, column=0, sticky="w")
        tk.Radiobutton(panel_superior, text="Grupo de selección", variable=self.tipo_var, value="grupo", command=self.toggle_tipo).grid(row=0, column=1, sticky="w", padx=15)

        etiqueta_titulo(panel_superior, texto="Ambiente origen:").grid(row=1, column=0, sticky="e", pady=8)
        self.combo_amb_origen = ttk.Combobox(panel_superior, values=self.nombres_ambientes, state="readonly", width=28)
        self.combo_amb_origen.grid(row=1, column=1, pady=8, sticky="w")
        self.combo_amb_origen.set("Selecciona un ambiente")

        etiqueta_titulo(panel_superior, texto="Ambiente destino:").grid(row=2, column=0, sticky="e")
        self.combo_amb_destino = ttk.Combobox(panel_superior, values=self.nombres_ambientes, state="readonly", width=28)
        self.combo_amb_destino.grid(row=2, column=1, pady=2, sticky="w")
        self.combo_amb_destino.set("Selecciona un ambiente")
        

        main_panel = tk.Frame(self)
        main_panel.pack(fill='x', padx=35, pady=(2, 0))

        self.frame_tabla = tk.LabelFrame(main_panel, text="Tabla a tabla", padx=10, pady=10)
        self.frame_tabla.pack(fill='x')

        self.frame_tabla.grid_columnconfigure(1, weight=1)
        self.frame_tabla.grid_columnconfigure(2, weight=0)

        etiqueta_titulo(self.frame_tabla, texto="Base de datos:").grid(row=0, column=0, sticky="e")
        self.entry_db_origen = entrada_estandar(self.frame_tabla, width=24)
        self.entry_db_origen.grid(row=0, column=1, sticky="w", padx=(4, 20), pady=4)

        etiqueta_titulo(self.frame_tabla, texto="Tabla:").grid(row=1, column=0, sticky="e")
        self.entry_tabla_origen = entrada_estandar(self.frame_tabla, width=24)
        self.entry_tabla_origen.grid(row=1, column=1, sticky="w", padx=(4, 20), pady=4)

        self.btn_consultar = boton_accion(
            self.frame_tabla,
            texto="Consultar datos a migrar",
            comando=self.on_consultar_tabla,
            width=22
        )
        self.btn_consultar.grid(row=1, column=2, padx=(8, 2), pady=0, sticky="nwe")

        etiqueta_titulo(self.frame_tabla, texto="Condición WHERE (opcional):").grid(row=2, column=0, sticky="e")
        self.entry_where = entrada_estandar(self.frame_tabla, width=50)
        self.entry_where.grid(row=2, column=1, padx=4, sticky="w", pady=4)

        self.btn_limpiar_tabla = boton_rojo(
            self.frame_tabla, texto="Limpiar",
            cursor='hand2', comando=self.limpiar_tabla,
            width=12
        )
        self.btn_limpiar_tabla.grid(row=2, column=2, padx=(8,2), pady=(2,0), sticky="we")

        self.frame_grupo = tk.LabelFrame(main_panel, text="Grupo de migración", padx=10, pady=10)
        etiqueta_titulo(self.frame_grupo, texto="Grupo:").grid(row=0, column=0, sticky="e")
        self.combo_grupo = ttk.Combobox(self.frame_grupo, values=[g["grupo"] for g in self.catalogo], width=33, state="readonly")
        self.combo_grupo.grid(row=0, column=1)
        self.combo_grupo.bind('<<ComboboxSelected>>', self.on_grupo_change)
        self.btn_limpiar_grupo = boton_rojo(self.frame_grupo, texto="Limpiar", cursor='hand2', comando=self.limpiar_grupo)
        self.btn_limpiar_grupo.grid(row=0, column=2, padx=(12,0), ipadx=12, ipady=5)

        self.var_frame = tk.Frame(self.frame_grupo)
        self.var_frame.grid(row=1, column=0, columnspan=3, pady=8, sticky="w")


        #APARTADO DE OPCIONES MIGRAR

        frame_migrar = tk.Frame(self)
        frame_migrar.pack(pady=(13,0), anchor="center")

        self.btn_migrar = boton_exito(
            frame_migrar, texto="Migrar",
            comando=self.on_migrar,
            state="disabled",
            width=18
        )
        self.btn_migrar.pack(side="left", padx=(0, 8))

        self.btn_cancelar = boton_rojo(
            frame_migrar, texto="Cancelar",
            comando=self.cancelar_op,
            state="disabled",
            width=18
        )
        self.btn_cancelar.pack(side="left", padx=(0, 8))

        self.progress = tb.Progressbar(
            self,
            bootstyle="success",
            orient="horizontal",
            length=1200,
            mode="determinate"
            )
        self.progress['maximum'] = 100
        self.progress['value'] = 0
        self.progress.pack(padx=25, pady=(20,2))
        self.progress_lbl = etiqueta_titulo(self, texto="")
        self.progress_lbl.pack()

        log_label = etiqueta_titulo(self, texto="Log de migración:", anchor='w')
        log_label.pack(fill='x', padx=38, pady=(14, 0))
        self.log_box = scrolledtext.ScrolledText(self, width=95, height=7, state="disabled")
        self.log_box.pack(padx=30, pady=(4, 0), fill='x', expand=False)

        self.lbl_registros = tk.Label(self, text="", fg="blue")
        self.lbl_registros.pack(pady=(2, 8))

        self.toggle_tipo()

        self.combo_amb_origen.bind("<<ComboboxSelected>>", lambda e: self.actualizar_combos_ambientes("origen"))
        self.combo_amb_destino.bind("<<ComboboxSelected>>", lambda e: self.actualizar_combos_ambientes("destino"))

        self.actualizar_combos_ambientes("origen")

    def actualizar_combos_ambientes(self, changed_combo):
        origen_sel = self.combo_amb_origen.get()
        destino_sel = self.combo_amb_destino.get()

        #actualizar combo destino si cambio origen
        if changed_combo == "origen":
            values_dest = [amb for amb in self.nombres_ambientes if amb != origen_sel] 
            
            if destino_sel == "origen":
                self.combo_amb_destino.set(values_dest[0] if values_dest else '')
            self.combo_amb_destino["values"] = values_dest

        elif changed_combo == "destino":
            values_ori = [amb for amb in self.nombres_ambientes if amb != destino_sel]
            if origen_sel == destino_sel:
                self.combo_amb_origen.set(values_ori [0] if values_ori else '')
            self.combo_amb_origen["values"] = values_ori
                
    def limpiar_tabla(self):
        self.reset_inputs(self.entry_tabla_origen, self.entry_where, self.entry_db_origen)
        self.info_tabla_origen = None
        self.set_widgets_state({
            self.btn_migrar: {"state": "disabled", "bootstyle": "dark"},
            self.combo_amb_origen: {"state": "readonly"},
            self.combo_amb_destino: {"state": "readonly"},
        })
        self.limpiar_consola()

    def limpiar_grupo(self):
        self.combo_grupo.set('')
        for entry in self.variables_inputs.values():
            entry.delete(0, tk.END)
    
    def limpiar_consola(self):
        self.log_box.config(state='normal')
        self.log_box.delete('1.0', tk.END)
        self.log_box.config(state='disabled')

    def log(self, msg):
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mensaje = f"[{now}] {msg}\n"
        self.log_box.config(state="normal")
        self.log_box.insert(tk.END, mensaje)
        self.log_box.see(tk.END)
        self.log_box.config(state="disabled")
        # Guarda logs en archivo (puedes cambiar la ruta si lo deseas)
        with open("log_migracion.txt", "a", encoding="utf-8") as f:
            f.write(mensaje)

    def update_progress(self, percent):
        #evitar que baje el progreso si el valor nuevo es menor
        last = self.progress["value"]
        if percent > last or percent == 0 or percent == 100:
            self.progress["value"] = percent
            self.progress_lbl["text"] = f"{percent}%"
            self.update_idletasks()

    def error_migracion(self, msg):
        messagebox.showerror("Error en migración", msg)
        self.progress["value"] = 0
        self.progress_lbl["text"] = ""

    def toggle_tipo(self):
        if self.tipo_var.get() == "tabla":
            self.frame_tabla.pack(fill='x')
            self.frame_grupo.pack_forget()
            self.set_widgets_state({
                self.btn_migrar: {"state": "disabled", "bootstyle": "dark"},
            })
        else:
            self.frame_grupo.pack(fill='x')
            self.frame_tabla.pack_forget()
            self.set_widgets_state({
                self.btn_migrar: {"state": "normal", "bootstyle": "success"},
            })
        self.lbl_registros["text"] = ""
        self.progress["value"] = 0
        self.progress_lbl["text"] = ""
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", tk.END)
        self.log_box.config(state="disabled")
        self.info_tabla_origen = None

    def on_salir(self):
        self.destroy()

    # DESHABILITAR BOTONES DURANTE LA MIGRACION
    def deshabilitar_controles_tabla(self):
        #botones
        self.btn_consultar.config(state="disabled")
        self.btn_limpiar_tabla.config(state="disabled")
        self.btn_migrar.config(state="disabled")

        #inputs:
        self.entry_db_origen.config(state="disabled")
        self.entry_tabla_origen.config(state="disabled")
        self.entry_where.config(state="disabled")
    
    #HABILITAR
    def habilitar_controles_tabla(self):
        #botones
        self.btn_consultar.config(state="normal")
        self.btn_limpiar_tabla.config(state="normal")
        self.btn_migrar.config(state="normal")

        #inputs:
        self.entry_db_origen.config(state="normal")
        self.entry_tabla_origen.config(state="normal")
        self.entry_where.config(state="normal")

    #boton cancelar
    def cancelar_op(self):
        self.cancelar_migracion = True
        self.log("Cancelando migracion. Espera un momento...")
        self.btn_cancelar.config(state="disabled")

    def on_grupo_change(self, event):
        for widget in self.var_frame.winfo_children():
            widget.destroy()
        self.variables_inputs.clear()
        grupo_nombre = self.combo_grupo.get()
        grupo_conf = next((g for g in self.catalogo if g["grupo"] == grupo_nombre), None)
        if not grupo_conf:
            etiqueta_titulo(self.var_frame, texto="Grupo no encontrado.").grid(row=0, column=0)
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
                self.variables_inputs[variable] = entry

    def on_consultar_tabla(self):
        self.info_tabla_origen = None
        tabla = self.entry_tabla_origen.get().strip()
        base = self.entry_db_origen.get().strip()
        where = self.entry_where.get().strip()
        nombre_origen = self.combo_amb_origen.get()
        nombre_destino = self.combo_amb_destino.get()
        if not tabla or not base or not nombre_origen or not nombre_destino:
            self.error_migracion('Debe ingresar la base, el nombre de la tabla y los ambientes.')
            return
        amb_origen = next((a for a in self.ambientes if a["nombre"] == nombre_origen), None)
        amb_destino = next((a for a in self.ambientes if a["nombre"] == nombre_destino), None)
        if not amb_origen or not amb_destino:
            self.error_migracion('No se encontró el ambiente seleccionado.')
            return
        resultado = consultar_tabla_e_indice(
            tabla, amb_origen, amb_destino, self.log, self.error_migracion, where=where, base_usuario=base
        )
        if resultado:
            self.info_tabla_origen = resultado
            self.set_widgets_state({
                self.btn_migrar: {"state": "normal", "bootstyle": "primary"},
                self.combo_amb_origen: {"state": "disabled"},
                self.combo_amb_destino: {"state": "disabled"},
            })
            self.log(
                f"Tabla lista para migrar. Clave primaria: {resultado['clave_primaria']}, "
                f"Total registros: {resultado['nregs']}"
            )
        else:
            self.set_widgets_state({
                self.btn_migrar: {"state": "disabled", "bootstyle": "dark"},
            })

        #----------------ACCIÓN DE MIGRAR-------------------

    def on_migrar(self):
        #deshabilitar botones
        self.deshabilitar_controles_tabla()
        self.btn_cancelar.config(state="normal")
        self.cancelar_migracion = False

        tabla = self.entry_tabla_origen.get().strip()
        base = self.entry_db_origen.get().strip()
        amb_ori = self.combo_amb_origen.get()
        amb_dest = self.combo_amb_destino.get()
        mensaje = (
            f"¿Está seguro de iniciar la migración?\n\n"
            f"Ambiente origen: {amb_ori}\n"
            f"Ambiente destino: {amb_dest}\n"
            f"Base de datos: {base}\n"
            f"Tabla: {tabla}\n"
        )
        respuesta = messagebox.askyesno("Confirmar migración", mensaje)
        if not respuesta:
            return
        self.set_widgets_state({
            self.btn_migrar: {"state": "disabled", "bootstyle": "dark"},
        })
        self.progress["value"] = 0
        self.progress_lbl["text"] = "0%"
        if self.tipo_var.get() == "tabla":
            threading.Thread(target=self.do_migrar_tabla, daemon=True).start()
        else:
            threading.Thread(target=self.do_migrar_grupo, daemon=True).start()

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

        self.update_progress(15)
        amb_origen = next((a for a in self.ambientes if a["nombre"] == nombre_origen), None)
        amb_destino = next((a for a in self.ambientes if a["nombre"] == nombre_destino), None)
        if not amb_origen or not amb_destino:
            self.update_progress(20)
            self.error_migracion('No se encontró el ambiente seleccionado.')
            return

        if not self.info_tabla_origen:
            self.update_progress(25)
            self.error_migracion("Debe consultar primero la estructura y clave primaria de la tabla.")
            return

        self.update_progress(25)

        self.log(f"Iniciando migración tabla '{base}..{tabla_origen}' de {nombre_origen} a {nombre_destino}...")

        def progress_fase_migracion(p):
            self.update_progress(25 + (p*0.7))

        resultado_migracion = migrar_tabla(
            tabla_origen,
            where,
            amb_origen,
            amb_destino,
            log_func=self.log,
            progress_func=progress_fase_migracion,
            abort_func=self.error_migracion,
            columnas=self.info_tabla_origen['columnas'],
            clave_primaria=self.info_tabla_origen['clave_primaria'],
            base_usuario=base
        )

        self.update_progress(100)

        if resultado_migracion and resultado_migracion.get("insertados", 0) == 0:
            messagebox.showinfo("Sin migración", "No existen datos para migrar (todos duplicados o sin registros).")
            self.log("No existen datos para migrar (todo estaba duplicado o tabla vacía).\n")
        else:
            self.log("Migración tabla a tabla finalizada.\n")
            messagebox.showinfo("Migración finalizada", "¡Migración finalizada con éxito!")
        
        self.habilitar_controles_tabla()
        self.btn_cancelar.config(state="disabled")
      
    def do_migrar_grupo(self):
        grupo_nombre = self.combo_grupo.get()
        nombre_origen = self.combo_amb_origen.get()
        nombre_destino = self.combo_amb_destino.get()
        if not grupo_nombre or not nombre_origen or not nombre_destino:
            self.error_migracion("Debe escoger grupo y ambientes.")
            return

        grupo_conf = next((g for g in self.catalogo if g["grupo"] == grupo_nombre), None)
        if not grupo_conf:
            self.error_migracion("No se encontró la configuración del grupo.")
            return
        variables = {var: entry.get().strip() for var, entry in self.variables_inputs.items()} if self.variables_inputs else {}
        amb_origen = next((a for a in self.ambientes if a["nombre"] == nombre_origen), None)
        amb_destino = next((a for a in self.ambientes if a["nombre"] == nombre_destino), None)
        if not amb_origen or not amb_destino:
            self.error_migracion('No se encontró el ambiente seleccionado.')
            return
        self.log(f"Iniciando migración de grupo '{grupo_nombre}' de {nombre_origen} a {nombre_destino}...")
        migrar_grupo(
            grupo_conf,
            variables,
            amb_origen,
            amb_destino,
            log_func=self.log,
            progress_func=self.update_progress,
            abort_func=self.error_migracion
        )
        self.update_progress(100)
        self.log("Migración de grupo finalizada.\n")
        messagebox.showinfo("Migración finalizada", "¡Migración finalizada con éxito!")
