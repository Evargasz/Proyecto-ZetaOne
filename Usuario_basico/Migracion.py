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

# --- NUEVO WIDGET DE AUTOCOMPLETADO PERSONALIZADO (VERSIÓN DEFINITIVA) ---
class AutocompleteEntry(tk.Frame):
    def __init__(self, parent, completion_list, **kwargs):
        super().__init__(parent)
        
        self._completion_list = sorted(completion_list, key=str.lower)
        
        self.entry = entrada_estandar(self, **kwargs)
        self.entry.pack(fill='both', expand=True)
        self.entry.bind('<KeyRelease>', self._on_keyrelease)
        self.entry.bind('<FocusOut>', self._on_focus_out)
        self.entry.bind('<Down>', self._on_arrow_down)
        self.entry.bind('<Up>', self._on_arrow_up)
        self.entry.bind('<Return>', self._on_enter)
        self.entry.bind('<Enter>', self._on_enter)
        
        # --- LÍNEA NUEVA: Añadimos el evento de clic ---
        self.entry.bind('<Button-1>', self._on_click)
        
        self._listbox = None
        self._listbox_toplevel = None

    def _create_listbox(self):
        if self._listbox:
            return
        
        # Crea una ventana flotante para la lista
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        width = self.entry.winfo_width()
        
        self._listbox_toplevel = tk.Toplevel(self)
        self._listbox_toplevel.wm_overrideredirect(True) # Sin bordes de ventana
        self._listbox_toplevel.wm_geometry(f"{width}x150+{x}+{y}")
        
        self._listbox = tk.Listbox(self._listbox_toplevel, exportselection=False)
        self._listbox.pack(fill='both', expand=True)
        self._listbox.bind('<Button-1>', self._on_listbox_click)

    def _destroy_listbox(self):
        if self._listbox_toplevel:
            self._listbox_toplevel.destroy()
            self._listbox_toplevel = None
            self._listbox = None

    def _on_keyrelease(self, event):
        if event.keysym in ("Up", "Down", "Return", "Enter"):
            return
            
        value = self.entry.get()
        if value:
            hits = [item for item in self._completion_list if item.lower().startswith(value.lower())]
        else:
            hits = self._completion_list
            
        self._update_listbox(hits)

    def _update_listbox(self, items):
        if not items:
            self._destroy_listbox()
            return
            
        self._create_listbox()
        self._listbox.delete(0, 'end')
        for item in items:
            self._listbox.insert('end', item)

    def _on_focus_out(self, event):
        # Cierra la lista si se pierde el foco
        self.after(200, self._destroy_listbox)

    def _on_listbox_click(self, event):
        # Capturar el índice y valor inmediatamente
        index = self._listbox.nearest(event.y)
        if 0 <= index < self._listbox.size():
            value = self._listbox.get(index)
            self._listbox.selection_clear(0, 'end')
            self._listbox.selection_set(index)
            self._listbox.activate(index)
            # Ejecutar la selección después del delay visual
            self.after(200, lambda: self._complete_selection(value))

    # --- FUNCIÓN NUEVA: Se ejecuta al hacer clic en el campo ---
    def _on_click(self, event):
        """Muestra la lista completa si el campo está vacío."""
        if not self.entry.get():
            self._update_listbox(self._completion_list)

    def _on_enter(self, event):
        if self._listbox:
            self._select_item()
        return "break"

    def _select_item(self):
        if self._listbox and self._listbox.curselection():
            value = self._listbox.get(self._listbox.curselection())
            self.entry.delete(0, 'end')
            self.entry.insert(0, value)
            self._destroy_listbox()
            self.entry.icursor('end')
            # --- CORRECCIÓN: Generar el evento para notificar a la ventana principal ---
            self.event_generate("<<ItemSelected>>")

    def _select_item_by_index(self, index):
        if self._listbox and 0 <= index < self._listbox.size():
            value = self._listbox.get(index)
            self.entry.delete(0, 'end')
            self.entry.insert(0, value)
            self._destroy_listbox()
            self.entry.icursor('end')
            self.event_generate("<<ItemSelected>>")

    def _complete_selection(self, value):
        self.entry.delete(0, 'end')
        self.entry.insert(0, value)
        self._destroy_listbox()
        self.entry.icursor('end')
        self.event_generate("<<ItemSelected>>")

    def _move_selection(self, direction):
        if not self._listbox:
            self._update_listbox(self._completion_list)
            return "break"
        
        current_selection = self._listbox.curselection()
        if current_selection:
            next_idx = current_selection[0] + direction
            if 0 <= next_idx < self._listbox.size():
                self._listbox.selection_clear(0, 'end')
                self._listbox.selection_set(next_idx)
                self._listbox.see(next_idx)
        return "break"

    def _on_arrow_down(self, event):
        return self._move_selection(1)

    def _on_arrow_up(self, event):
        return self._move_selection(-1)

    # --- Métodos para que se comporte como un widget normal ---
    def get(self):
        return self.entry.get()

    def set(self, text):
        self.entry.delete(0, 'end')
        self.entry.insert(0, text)
        
    def focus_set(self):
        self.entry.focus_set()
        
    def icursor(self, index):
        self.entry.icursor(index)


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
        
        # Centrar ventana
        from util_ventanas import centrar_ventana
        centrar_ventana(self, 900, 560)
        self.variables_inputs = {}
        self.tablas_con_errores = []
        self.info_tabla_origen = None
        self.cancelar_migracion = False
        self.migrando = False

        # --- CORRECCIÓN: Se usan rutas seguras con recurso_path ---
        from util_rutas import recurso_path # Importación local para claridad
        try:
            self.json_path_grupo = recurso_path("json", CATALOGO_FILE)
            # --- CORRECCIÓN: Cargar ambientes desde la función centralizada que lee el .dat ---
            from Usuario_administrador.handlers.ambientes import cargar_ambientes
            self.ambientes = cargar_ambientes()
        except Exception as e:
            messagebox.showerror("Error de Carga", f"No se pudieron cargar los archivos de configuración.\n{e}")
            self.destroy()
            return

        self.configurar_logging()
        self.catalogo = cargar_json(self.json_path_grupo)
        if self.catalogo is None:
            messagebox.showerror("Error", f"No se pudo cargar {CATALOGO_FILE}. Consulte el log.")
            self.destroy()
            return

        self.nombres_ambientes = [a["nombre"] for a in self.ambientes]
        self._armar_interfaz()

    def centrar_ventana(ventana):
        ventana.update_idletasks()
        ancho = ventana.winfo_width()
        alto = ventana.winfo_height()
        x = (ventana.winfo_screenwidth() // 2) - (ancho // 2)
        y = (ventana.winfo_screenheight() // 2) - (alto // 2)
        ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

    def is_cancelled(self):
        return self.cancelar_migracion

    def configurar_logging(self):
        logging.basicConfig(
            filename="log_migracion.txt",
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s'
        )

    def _log_thread_safe(self, mensaje, color):
        """Función interna para actualizar el log_box de forma segura desde cualquier hilo."""
        # --- MEJORA: Comprobar si el widget todavía existe antes de actualizar ---
        # Esto previene errores si la ventana se cierra mientras el hilo aún corre.
        if not self.log_box.winfo_exists():
            return
        self.log_box.config(state="normal")
        # Usamos el color directamente en lugar del nivel para simplificar
        self.log_box.insert(tk.END, mensaje + "\n", color)
        self.log_box.tag_config(color, foreground=color)
        self.log_box.see(tk.END)
        self.log_box.config(state="disabled")

    def log(self, msg, nivel="info"):
        """
        Añade un mensaje al log de la UI y al archivo de log.
        Es seguro llamarlo desde cualquier hilo.
        """
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mensaje = f"[{now}] {msg}"
        color = {"info": "black", "error": "red", "warning": "darkorange", "success": "green"}.get(nivel, "black")
        self.after(0, self._log_thread_safe, mensaje, color)
        getattr(logging, nivel if nivel in ["info", "error", "warning"] else "info")(msg)

    def _armar_interfaz(self):
        # --- CORRECCIÓN: El frame principal debe ser 'self', no 'tk.Frame(self)' ---
        # Esto asegura que los widgets se empaqueten directamente en la ventana Toplevel.
        # main_panel = tk.Frame(self) 
        # main_panel.pack(fill='x', padx=35, pady=(2, 0))

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

        # --- MEJORA: Excluir SYBREPOR de la lista de ambientes de destino ---
        nombres_ambientes_destino = [amb for amb in self.nombres_ambientes if amb.upper() != "SYBREPOR"]

        etiqueta_titulo(panel_superior, texto="Ambiente destino:").grid(row=2, column=0, sticky="e")
        self.combo_amb_destino = ttk.Combobox(panel_superior, values=nombres_ambientes_destino, state="readonly", width=28)
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
        # Usamos nuestro nuevo widget personalizado
        self.combo_grupo = AutocompleteEntry(self.frame_grupo, completion_list=[g["grupo"] for g in self.catalogo], width=25)
        self.combo_grupo.grid(row=0, column=1)
        # --- CORRECCIÓN: Se enlaza al evento correcto <<ItemSelected>> que sí se dispara ---
        self.combo_grupo.bind('<<ItemSelected>>', self.on_grupo_change)

        if "boton_rojo" in globals():
            self.btn_limpiar_grupo = boton_rojo(self.frame_grupo, texto="Limpiar",
            cursor='hand2', comando=self.limpiar_grupo, width=12)
        else:
            self.btn_limpiar_grupo = boton_rojo(self.frame_grupo, texto="Limpiar", cursor='hand2', comando=self.limpiar_grupo, width=12)
        self.btn_limpiar_grupo.grid(row=0, column=2, padx=(12,0), ipadx=12)

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

        # --- BOTÓN "SALIR" CON LA INDENTACIÓN CORRECTA ---
        self.btn_salir = boton_accion(
            frame_migrar, texto="Salir",
            comando=self.on_salir,
            width=18
        )
        self.btn_salir.pack(side="left", padx=(0,8))

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
        self.log_box = scrolledtext.ScrolledText(self, width=95, height=7, state="disabled", font=("Consolas", 9))
        self.log_box.pack(padx=30, pady=(4, 0), fill='x', expand=False)
        self.lbl_registros = etiqueta_titulo(self, texto="")
        self.lbl_registros.pack(pady=(2, 8))
        self.toggle_tipo()

    def actualizar_combos_ambientes(self, changed_combo):
        """
        Actualiza los combobox de origen y destino para evitar que sean iguales.
        Cuando se selecciona un ambiente, se elimina de la lista del otro y se reinicia su selección.
        """
        origen_sel = self.combo_amb_origen.get()
        destino_sel = self.combo_amb_destino.get()

        # Actualizar lista de destino
        if origen_sel and "Selecciona" not in origen_sel:
            # --- MEJORA: Excluir SYBREPOR de la lista de ambientes de destino ---
            self.combo_amb_destino["values"] = [amb for amb in self.nombres_ambientes if amb != origen_sel and amb.upper() != "SYBREPOR"]
            if destino_sel == origen_sel:
                self.combo_amb_destino.set("Selecciona un ambiente")

        # Actualizar lista de origen
        if destino_sel and "Selecciona" not in destino_sel:
            self.combo_amb_origen["values"] = [amb for amb in self.nombres_ambientes if amb != destino_sel]
            if origen_sel == destino_sel:
                self.combo_amb_origen.set("Selecciona un ambiente")

    def limpiar_tabla(self):
        self.entry_tabla_origen.delete(0, tk.END)
        self.entry_where.delete(0, tk.END)
        self.entry_db_origen.delete(0, tk.END)
        self.info_tabla_origen = None
        self.btn_migrar["state"] = "disabled"
        self.combo_amb_origen["state"] = "readonly"
        self.combo_amb_destino["state"] = "readonly"
        self.btn_cancelar["state"] = "disabled"
        # --- MEJORA: Reiniciar la barra de progreso ---
        self.progress['value'] = 0
        # --- MEJORA: Reiniciar color de la barra de progreso ---
        self.progress.config(bootstyle="success")
        self.progress_lbl['text'] = ""
        self.limpiar_consola()

    def limpiar_grupo(self):
        self.combo_grupo.set('')
        for entry in self.variables_inputs.values():
            entry.delete(0, tk.END)
        self.btn_migrar.config(state="normal")
        self.btn_cancelar.config(state="normal")
        # --- MEJORA: Reiniciar la barra de progreso ---
        self.progress['value'] = 0
        # --- MEJORA: Reiniciar color de la barra de progreso ---
        self.progress.config(bootstyle="success")
        self.progress_lbl['text'] = ""
        self.limpiar_consola()

    def limpiar_consola(self):
        self.log_box.config(state='normal')
        self.log_box.delete('1.0', tk.END)
        self.log_box.config(state='disabled')

    def open_admin_grupo(self):
        # Obtener el grupo actualmente seleccionado
        grupo_seleccionado = self.combo_grupo.get()
        
        # Pasar el grupo seleccionado a la nueva ventana
        app = MigracionGruposGUI(self, self.reload_catalogo, json_path=self.json_path_grupo, grupo_inicial=grupo_seleccionado)
        app.grab_set()

    def reload_catalogo(self):
        self.catalogo = cargar_json(self.json_path_grupo) or []
        grupos = [g["grupo"] for g in self.catalogo]
        self.combo_grupo._completion_list = sorted(grupos, key=str.lower) # Actualizamos la lista interna
        if self.combo_grupo.get() not in grupos and grupos:
            self.combo_grupo.set(grupos[0])
        self.on_grupo_change(None)

    def update_progress(self, percent):
        # --- MEJORA: Comprobar si los widgets existen antes de actualizar ---
        # Previene errores si la ventana se cierra durante la migración.
        if not self.progress.winfo_exists() or not self.progress_lbl.winfo_exists():
            return

        last = self.progress["value"]
        if percent > last or percent == 0 or percent == 100:
            self.progress["value"] = percent
            self.progress_lbl["text"] = f"{percent}%"
            self.update_idletasks()

    def error_migracion(self, msg):
        self.log(msg, nivel="error")
        messagebox.showerror("Error en migración", msg)
        # --- MEJORA: Cambiar color de la barra a rojo en caso de error ---
        self.progress.config(bootstyle="danger")
        self.progress["value"] = 0
        self.progress_lbl["text"] = ""
        self.habilitar_botones(True)
        self.migrando = False

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
            # --- LÍNEA NUEVA: Ponemos el foco en nuestro widget ---
            self.after(50, lambda: self.combo_grupo.focus_set())

        self.lbl_registros["text"] = ""
        self.progress["value"] = 0
        self.progress_lbl["text"] = ""
        self.limpiar_consola()
        self.info_tabla_origen = None

    def on_salir(self):
        """Maneja el cierre de la ventana, asegurando que los hilos terminen."""
        if self.migrando:
            resp = messagebox.askyesno(
                "Confirmar cierre",
                "Hay una migración en curso. ¿Deseas cancelarla y salir?",
                parent=self
            )
            if not resp:
                return
            
            # Iniciar cierre seguro en un hilo para no bloquear la UI
            self.log("Cierre solicitado. Cancelando migración en curso...", "warning")
            self.cancelar_migracion = True
            self.btn_cancelar.config(state="disabled")
            self.btn_migrar.config(state="disabled")
            self.btn_salir.config(state="disabled", text="Saliendo...")
            
            # Hilo que espera a que la migración termine
            threading.Thread(target=self._esperar_y_cerrar, daemon=True).start()
        else:
            self.destroy()

    def _esperar_y_cerrar(self):
        """
        (Worker Thread) Espera a que el flag 'migrando' sea False y luego cierra la ventana.
        """
        while self.migrando:
            # Pequeña pausa para no consumir CPU innecesariamente
            import time
            time.sleep(0.2)
        
        # Una vez que el hilo de migración ha terminado, cierra la ventana desde el hilo principal
        self.after(0, self.destroy)
        
    def mostrar_ven_historial(self):
        def rellenar_campos(base, tabla, where):
            self.entry_db_origen.delete(0, tk.END)
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
    
    def habilitar_controles_tabla(self, afectar_migrar_cancelar=True):
        self.btn_consultar.config(state="normal")
        self.btn_limpiar_tabla.config(state="normal")
        self.entry_db_origen.config(state="normal")
        self.entry_tabla_origen.config(state="normal")
        self.entry_where.config(state="normal")
        self.btn_historial.config(state="normal")
        self.ventana_tabla.config(state="normal")
        self.ventana_grupo.config(state="normal")
        if afectar_migrar_cancelar:
            self.btn_migrar.config(state="normal")
            self.btn_cancelar.config(state="normal")

    def cancelar_op(self):
        if not self.migrando:
            messagebox.showinfo("No hay nada que cancelar","No hay ninguna migración corriendo para cancelar.")
            return
        
        respuesta = messagebox.askyesno(
            "Confirmar Cancelación",
            "¿Seguro que quieres cancelar la migración en curso?\n\nSe detendrá inmediatamente y se harán rollback de los cambios pendientes."
        )
        if not respuesta:
            self.log("Cancelación abortada por el usuario.")
            return
        
        # FIX CRÍTICO: Activar cancelación real
        self.cancelar_migracion = True
        self.log("🛑 CANCELANDO migración... Deteniendo hilos y haciendo rollback.", "warning")
        
        # Deshabilitar botón para evitar múltiples clicks
        self.btn_cancelar.config(state="disabled")
        self.btn_migrar.config(state="disabled")

    def sanitizar_valor_sql(self, valor):
        """Sanitiza valores para prevenir inyección SQL básica"""
        if not valor:
            return valor
        # Remover caracteres peligrosos comunes
        caracteres_peligrosos = [';', '--', '/*', '*/', 'xp_', 'sp_', 'DROP', 'DELETE', 'TRUNCATE', 'ALTER']
        valor_limpio = str(valor).strip()
        for peligroso in caracteres_peligrosos:
            if peligroso.lower() in valor_limpio.lower():
                self.log(f"⚠️ Valor rechazado por contener '{peligroso}': {valor_limpio[:50]}", "warning")
                return ""
        return valor_limpio
    
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
                ToolTip(entry, f"Ingrese el valor para la variable '{variable}' en JOIN o condición WHERE. No usar: ; -- /* DROP DELETE")
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

    def habilitar_botones(self, enable=True, afectar_migrar=False):
        st = "normal" if enable else "disabled"
        if afectar_migrar:
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

    def validar_where_seguro(self, where_clause):
        """Valida que la cláusula WHERE no contenga SQL peligroso"""
        if not where_clause:
            return True, where_clause
        
        # Patrones peligrosos
        patrones_peligrosos = [
            r';\s*DROP\s+', r';\s*DELETE\s+', r';\s*TRUNCATE\s+', r';\s*ALTER\s+',
            r'--', r'/\*', r'\*/'
        ]
        
        for patron in patrones_peligrosos:
            if re.search(patron, where_clause, re.IGNORECASE):
                return False, f"Patrón peligroso detectado: {patron}"
        
        return True, where_clause
    
    def on_consultar_tabla(self):
        self.info_tabla_origen = None
        tabla = self.entry_tabla_origen.get().strip()
        base = self.entry_db_origen.get().strip()
        where = self.entry_where.get().strip()
        nombre_origen = self.combo_amb_origen.get()
        nombre_destino = self.combo_amb_destino.get()
        errores = []
        
        # SEGURIDAD: Validar WHERE clause
        if where:
            es_seguro, mensaje = self.validar_where_seguro(where)
            if not es_seguro:
                self.error_migracion(f"Condición WHERE no segura: {mensaje}")
                return

        # Validaciones
        if not tabla:
            self.entry_tabla_origen.config(bootstyle="danger")
            errores.append("Tabla (origen)")
        if not base:
            self.entry_db_origen.config(bootstyle="danger")
            errores.append("Base de datos (origen)")
        if not nombre_origen or not nombre_destino:
            errores.append("Ambientes")
        if not es_nombre_tabla_valido(tabla):
            self.entry_tabla_origen.config(bootstyle="danger")
            errores.append("Nombre de tabla no válido (solo A-Z, 0-9, _, .)")
        if not es_nombre_tabla_valido(base):
            self.entry_db_origen.config(bootstyle="danger")
            errores.append("Nombre de base no válido (solo A-Z, 0-9, _, .)")

        # BLOQUE DE CORRECCIÓN: deshabilitar ambos botones si hay errores
        if errores:
            self.error_migracion("❌ Errores encontrados: " + ", ".join(errores))
            self.btn_migrar["state"] = "disabled"
            self.btn_cancelar["state"] = "disabled"
            # Limpiar estilos de error después de 3 segundos
            self.after(3000, lambda: [
                self.entry_tabla_origen.config(bootstyle=""),
                self.entry_db_origen.config(bootstyle="")
            ])
            return

        amb_origen = next((a for a in self.ambientes if a["nombre"] == nombre_origen), None)
        if not amb_origen:
            self.error_migracion("Debes seleccionar un ambiente de origen válido.")
            self.btn_migrar["state"] = "disabled"
            self.btn_cancelar["state"] = "disabled"
            return
        amb_destino = next((a for a in self.ambientes if a["nombre"] == nombre_destino), None)
        if not amb_destino:
            self.error_migracion("Debes seleccionar un ambiente de destino válido.")
            self.btn_migrar["state"] = "disabled"
            self.btn_cancelar["state"] = "disabled"
            return

        # Mostrar indicador de progreso y deshabilitar controles
        self.btn_consultar.config(state="disabled", text="Consultando...")
        self.progress.config(mode="indeterminate")
        self.progress.start(10)
        self.progress_lbl.config(text="Consultando estructura y datos...")
        
        # Ejecutar consulta en hilo separado
        threading.Thread(
            target=self._consultar_en_hilo,
            args=(tabla, amb_origen, amb_destino, where, base),
            daemon=True
        ).start()
        
    def _consultar_en_hilo(self, tabla, amb_origen, amb_destino, where, base):
        """Ejecuta la consulta en un hilo separado para no bloquear la UI"""
        try:
            resultado = consultar_tabla_e_indice(
                tabla, amb_origen, amb_destino, self.log, self._error_consulta_hilo, where=where, base_usuario=base
            )
            # Actualizar UI en el hilo principal
            self.after(0, self._finalizar_consulta, resultado)
        except Exception as e:
            self.after(0, self._error_consulta_hilo, f"Error inesperado: {str(e)}")
    
    def _finalizar_consulta(self, resultado):
        """Finaliza la consulta y actualiza la UI"""
        # Detener progreso
        self.progress.stop()
        self.progress_lbl.config(text="")
        self.btn_consultar.config(state="normal", text="Consultar datos a migrar")
        
        if resultado:
            self.info_tabla_origen = resultado
            self.btn_migrar["state"] = "normal"
            self.btn_cancelar["state"] = "normal"
            self.combo_amb_origen["state"] = "disabled"
            self.combo_amb_destino["state"] = "disabled"
            self.log(
                f"Tabla lista para migrar. Clave primaria: {resultado['clave_primaria']}, "
                f"Total registros: {resultado['nregs']}", nivel="info"
            )
        else:
            self.btn_migrar["state"] = "disabled"
            self.btn_cancelar["state"] = "disabled"
    
    def _error_consulta_hilo(self, mensaje):
        """Maneja errores desde el hilo de consulta"""
        self.progress.stop()
        self.progress_lbl.config(text="")
        self.btn_consultar.config(state="normal", text="Consultar datos a migrar")
        self.error_migracion(mensaje)

    def on_migrar(self):
        # --- CORRECCIÓN #1: Se usan los nombres correctos para los combos de ambiente ---
        amb_origen_nombre = self.combo_amb_origen.get()
        amb_destino_nombre = self.combo_amb_destino.get()

        if not amb_origen_nombre or "Selecciona" in amb_origen_nombre or not amb_destino_nombre or "Selecciona" in amb_destino_nombre:
            messagebox.showwarning("Selección requerida", "Debe seleccionar un ambiente de origen y uno de destino.", parent=self)
            return
        if amb_origen_nombre == amb_destino_nombre:
            messagebox.showwarning("Selección inválida", "El ambiente de origen y destino no pueden ser el mismo.", parent=self)
            return

        amb_origen = next((a for a in self.ambientes if a['nombre'] == amb_origen_nombre), None)
        amb_destino = next((a for a in self.ambientes if a['nombre'] == amb_destino_nombre), None)

        if not amb_origen or not amb_destino:
            messagebox.showerror("Error", "No se encontró la configuración para los ambientes seleccionados.", parent=self)
            return

        # --- CORRECCIÓN #2: Se usa la variable del radio button (self.tipo_var) en lugar del notebook ---
        modo_seleccionado = self.tipo_var.get()
        
        # Lógica para migración por tabla
        if modo_seleccionado == "tabla":
            if not self.info_tabla_origen:
                self.error_migracion("Debe usar 'Consultar datos a migrar' antes de poder migrar.")
                return
            self.migrando = True
            self.deshabilitar_controles_tabla()
            self.btn_cancelar.config(state="normal")
            threading.Thread(target=self.do_migrar_tabla, daemon=True).start()

        # Lógica para migración por grupo
        elif modo_seleccionado == "grupo":
            errores = self.validar_campos_obligatorios()
            if errores:
                self.error_migracion("Debe completar los siguientes campos: " + ", ".join(errores))
                return

            # --- INICIO DE LA MEJORA: Añadir diálogo de confirmación ---
            confirmacion = messagebox.askyesno(
                "Confirmar Migración de Grupo",
                f"¿Estás seguro que quieres migrar desde '{amb_origen_nombre}' hacia '{amb_destino_nombre}'?",
                parent=self
            )
            if not confirmacion:
                self.log("Migración de grupo cancelada por el usuario.", "warning")
                return # Detiene la ejecución si el usuario presiona "No"
            # --- FIN DE LA MEJORA ---

            self.migrando = True
            self.habilitar_botones(False)
            self.habilitar_botones(False, afectar_migrar=True)
            self.btn_cancelar.config(state="normal")
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
            base_usuario=base, # type: ignore
            cancelar_func=self.is_cancelled,
            total_registros=self.info_tabla_origen['nregs']
        )
        try:
            # --- CORRECCIÓN: Se pasa la nueva consulta y el historial por separado a la función centralizada ---
            historial = cargar_historial()
            nuevo = {"base": base, "tabla": tabla_origen, "condicion (where)": where} # type: ignore
            guardar_historial(historial, nueva_consulta=nuevo) # guardar_historial ahora hace todo el trabajo
        except Exception as e:
            self.log(f"No se pudo guardar en el historial: {e}", nivel="warning")
        self.update_progress(100)
        
        # --- INICIO DE LA MEJORA: Feedback inteligente basado en el resultado ---
        if self.is_cancelled():
            # --- MEJORA: Cambiar a rojo en caso de cancelación ---
            self.progress.config(bootstyle="danger")
            self.log("La migración fue cancelada por el usuario.", "warning")
            messagebox.showwarning("Cancelado", "La migración fue cancelada por el usuario.", parent=self)
        elif resultado_migracion and resultado_migracion.get("insertados", 0) > 0:
            self.progress.config(bootstyle="success")
            insertados = resultado_migracion.get("insertados", 0)
            omitidos = resultado_migracion.get("omitidos", 0)
            self.log(f"Migración tabla a tabla finalizada. Insertados: {insertados}, Omitidos: {omitidos}", "success")
            messagebox.showinfo("Migración Finalizada", f"¡Migración finalizada con éxito!\n\nRegistros Insertados: {insertados:,}\nRegistros Omitidos: {omitidos:,}", parent=self)
        else:
            # --- MEJORA: Cambiar a rojo si no hubo inserciones ---
            self.progress.config(bootstyle="danger")
            omitidos = resultado_migracion.get("omitidos", 0) if resultado_migracion else 0
            self.log(f"Migración completada sin inserciones. Omitidos: {omitidos}", "warning")
            messagebox.showinfo("Sin Datos Migrados", f"No se insertaron nuevos registros.\n\nPosibles causas:\n- Todos los registros ya existían en el destino (Omitidos: {omitidos:,})\n- La tabla de origen estaba vacía o no cumplía la condición WHERE.", parent=self)
        # --- FIN DE LA MEJORA ---

        # Habilita los controles para una nueva consulta, pero mantiene deshabilitados Migrar y Cancelar.
        self.habilitar_controles_tabla(afectar_migrar_cancelar=False)
        self.btn_migrar.config(state="disabled")
        self.btn_cancelar.config(state="disabled")
        self.migrando = False

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
        # SEGURIDAD: Sanitizar variables antes de usar
        variables = {}
        if self.variables_inputs:
            for var, entry in self.variables_inputs.items():
                valor_original = entry.get().strip()
                valor_sanitizado = self.sanitizar_valor_sql(valor_original)
                if valor_original != valor_sanitizado:
                    self.log(f"⚠️ Variable ${var}$ sanitizada: '{valor_original}' -> '{valor_sanitizado}'", "warning")
                variables[var] = valor_sanitizado
        amb_origen = next((a for a in self.ambientes if a["nombre"] == nombre_origen), None)
        if not amb_origen:
            self.error_migracion("Debes seleccionar un ambiente de origen válido.")
            return
        amb_destino = next((a for a in self.ambientes if a["nombre"] == nombre_destino), None)
        if not amb_destino:
            self.error_migracion("Debes seleccionar un ambiente de destino válido.")
            return

        self.log(f"Iniciando migración de grupo '{grupo_nombre}' de {nombre_origen} a {nombre_destino}...", nivel="info")
        resultado_migracion = migrar_grupo(
            grupo_conf,
            variables,
            amb_origen,
            amb_destino,
            log_func=self.log,
            progress_func=self.update_progress,
            abort_func=self.error_migracion, # type: ignore
            cancelar_func=self.is_cancelled
        )
        self.update_progress(100)

        # Feedback basado en el resultado
        if self.is_cancelled():
            # --- MEJORA: Cambiar a rojo en caso de cancelación ---
            self.progress.config(bootstyle="danger")
            self.log("La migración de grupo fue cancelada por el usuario.", "warning")
            messagebox.showwarning("Cancelado", "La migración de grupo fue cancelada por el usuario.", parent=self)
        elif resultado_migracion and resultado_migracion.get('insertados', 0) > 0:
            self.log(f"Migración de grupo finalizada. Total insertados: {resultado_migracion['insertados']}", "success")
            messagebox.showinfo("Migración Finalizada", f"¡Migración de grupo finalizada con éxito!\n\nTotal de registros insertados: {resultado_migracion['insertados']:,}", parent=self)
        else:
            # --- MEJORA: Cambiar a rojo si no hubo inserciones ---
            self.progress.config(bootstyle="danger")
            self.log("Migración de grupo completada sin inserciones.", "warning")
            messagebox.showinfo("Sin Datos Migrados", "NO se insertaron nuevos registros durante la migración del grupo. Revisa el log para más detalles.", parent=self)
        

        self.habilitar_botones(True) # Habilitar todos los botones
        self.habilitar_botones(True, afectar_migrar=False) # Habilita controles, pero no el botón de migrar
        self.btn_migrar.config(state="disabled") # Deshabilita explícitamente el botón de migrar
        self.btn_cancelar.config(state="disabled") # Deshabilitar cancelar al final
        self.migrando = False # 
        
        # FIX: Cancelación ahora funciona correctamente