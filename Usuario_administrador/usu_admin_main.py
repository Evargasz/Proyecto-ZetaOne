# |================================================================================================================================|
# | IMPORTANTE: Ejecurar ventana desde powersherll (para pruebas) con este comando: python -m Usuario_administrador.usu_admin_main |
# |================================================================================================================================|

#importaciones generales
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, PhotoImage

#importaciones frame derecha (panel de archivos)
from .handlers.explorador import explorar_sd_folder
from .util_repetidos import quitar_repetidos
from .styles import FUENTE_GENERAL, COLOR_ACCION
from .widgets.tooltip import ToolTip
from .validacion_dialog import lanzar_validacion
from .catalogacion_dialog import CatalogacionDialog

#importaciones frame izquierdo (panel de ambientes)
import os
from .handlers.ambientes import cargar_ambientes, guardar_ambientes, probar_conexion_amb
from .styles import COLOR_ACCION, COLOR_RESALTADO, FONDO_PANEL2, FUENTE_GENERAL, configurar_estilos, configurar_botones_personalizados

class usuAdminMain:
        
    #-----------------------configuracion de ventana--------------------------
    
    class iniciar_ventana:
        def __init__(self, root, controlador):
            self.root = root
            self.root.title("Homologador Sybase SD - Multiambiente Validación/Catalogación")
            style = ttk.Style()
            
            #tamaño de la ventana
            ventana_ancho = 1366
            ventana_alto = 780
            pantalla_ancho = self.root.winfo_screenwidth()
            pantalla_alto = self.root.winfo_screenheight()
            x = int((pantalla_ancho / 2) - (ventana_ancho / 2 ))
            y = int((pantalla_alto / 2) - (ventana_alto / 2))
            self.root.geometry(f"{ventana_ancho}x{ventana_alto}+{x}+{y}")
            root.resizable(False, False)

            #icono de la ventana
            self.root.iconbitmap("imagenes_iconos/Zeta99.ico")

            #llamado a los estilos de la ventana
            style.theme_use("clam")  # Fuerza el tema clam antes de aplicar estilos personalizados
            configurar_estilos(style)
            configurar_botones_personalizados(style)

            main_frame = ttk.Frame(root, padding=12, style="Panel.TFrame")
            main_frame.pack(fill="both", expand=True)

            main_frame.columnconfigure(0, weight=0, minsize=400)
            main_frame.columnconfigure(1, weight=7)
            main_frame.rowconfigure(0, weight=1)
            main_frame.rowconfigure(1, weight=0)

            # Panel de Ambientes (izquierda)
            self.amb_panel = usuAdminMain.AmbientesPanel(main_frame)
            self.amb_panel.frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 8))

            # Panel de Archivos (derecha)
            self.arch_panel = usuAdminMain.ArchivosPanel(main_frame, self.amb_panel, toggle_log_callback=self.toggle_log)
            self.arch_panel.frame.grid(row=0, column=1, sticky="nsew", padx=(0, 0), pady=(0, 8))

            # Zona de log
            self.logtxt = scrolledtext.ScrolledText(
                main_frame, height=7, font=("Segoe UI", 9), background="#f9fafb",
                foreground="#1e293b", relief="flat", wrap="word"
            )
            self.logtxt.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
            self.logtxt.grid_remove()   # Oculta el log al inicio
            self.log_visible = False    # Marca el estado como oculto

            # Referencia cruzada para accionar desde paneles
            self.amb_panel.master = self
            self.arch_panel.master = self
            self.arch_panel.logtxt = self.logtxt

        def toggle_log(self):
            if self.log_visible:
                self.logtxt.grid_remove()
                self.log_visible = False
            else:
                self.logtxt.grid()
                self.log_visible = True

    #-------------------------panel de archivos-------------------------------

    class ArchivosPanel:
        def __init__(self, parent, ambientes_panel, toggle_log_callback=None):
            self.frame = ttk.Frame(parent, style="Panel2.TFrame", padding=(3, 3))
            self.ambientes_panel = ambientes_panel
            self.toggle_log_callback = toggle_log_callback
            self.logtxt = None  # Se asigna desde el main

            # Barra superior
            barra_sd = ttk.Frame(self.frame, style="Barra.TFrame", padding=(8, 6))
            barra_sd.grid(row=0, column=0, sticky="ew", pady=(0, 8))
            barra_sd.columnconfigure(0, weight=1, minsize=180)
            barra_sd.columnconfigure(1, weight=1, minsize=230)
            barra_sd.columnconfigure(2, weight=5)
            barra_sd.columnconfigure(3, weight=2, minsize=240)
            self.single_sd_btn = ttk.Button(
                barra_sd, text="SD Único", command=self.single_sd, style="Accion.TButton", width=14
            )
            self.multi_sd_btn = ttk.Button(
                barra_sd, text="Carpeta con varios SD", command=self.multi_sd, style="Accion.TButton", width=22
            )
            self.single_sd_btn.grid(row=0, column=0, padx=10, sticky="ew")
            self.multi_sd_btn.grid(row=0, column=1, padx=10, sticky="ew")
            self.sd_label = ttk.Label(barra_sd, text="", foreground=COLOR_ACCION, font=FUENTE_GENERAL)
            self.sd_label.grid(row=0, column=2, sticky="w", padx=(16, 0))
            self.btn_repetidos = ttk.Button(
                barra_sd, text="Programas Repetidos", command=self.ver_repetidos, width=31, style="TButton"
            )
            self.btn_repetidos.grid(row=0, column=3, padx=(6, 6), sticky="e")

            archivos_frame = ttk.LabelFrame(
                self.frame, text="Archivos Detectados",
                padding=(16, 8, 12, 8), style="MainPanel.TLabelframe"
            )
            archivos_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
            archivos_frame.rowconfigure(0, weight=1)
            archivos_frame.columnconfigure(0, weight=1)
            columns = ("Nombre", "Ruta", "Fecha Modif.")
            self.tree = ttk.Treeview(
                archivos_frame,
                columns=columns, show="headings", selectmode="extended", style="Treeview"
            )
            self.tree.heading("Nombre", text="Nombre")
            self.tree.column("Nombre", width=200, anchor="w")
            self.tree.heading("Ruta", text="Ruta SD")
            self.tree.column("Ruta", width=500, anchor="w")
            self.tree.heading("Fecha Modif.", text="Fecha Modificación")
            self.tree.column("Fecha Modif.", width=170, anchor="center")
            self.tree.grid(row=0, column=0, sticky="nsew")
            tree_vscroll = ttk.Scrollbar(archivos_frame, orient="vertical", command=self.tree.yview)
            tree_vscroll.grid(row=0, column=1, sticky="ns")
            tree_hscroll = ttk.Scrollbar(archivos_frame, orient="horizontal", command=self.tree.xview)
            tree_hscroll.grid(row=1, column=0, sticky="ew")
            self.tree.configure(yscrollcommand=tree_vscroll.set, xscrollcommand=tree_hscroll.set)
            ToolTip(self.tree, self.get_tooltip_for_row)

            barra_accion = ttk.Frame(self.frame, style="Barra.TFrame", padding=(7, 7, 12, 7))
            barra_accion.grid(row=2, column=0, sticky="ew", pady=(14, 6))
            ttk.Button(barra_accion, text="Seleccionar Todos", command=self.seleccionar_todos, style="Accion.TButton").pack(side="left", padx=8)
            ttk.Button(barra_accion, text="Deseleccionar", command=self.deseleccionar_todos, style="TButton").pack(side="left", padx=7)
            ttk.Button(barra_accion, text="Validar Seleccionados", command=self.validar_seleccionados, style="Accion.TButton").pack(side="left", padx=18)
            ttk.Button(barra_accion, text="Log de Operaciones 📝", command=self.toggle_log, style="TButton").pack(side="left", padx=18)
            ttk.Button(barra_accion, text="Salir", command=self.salir, style="Salir.TButton").pack(side="right", padx=18)

            self.frame.columnconfigure(0, weight=1)
            self.frame.rowconfigure(1, weight=1)

            self.archivos_unicos = []
            self.selected_sd_folder = ""
            self.multi_sd_flag = False
            self.repetidos_log = []

        def toggle_log(self):
            if self.toggle_log_callback:
                self.toggle_log_callback()

        def logear_panel(self, msg):
            if self.logtxt:
                self.logtxt.insert(tk.END, "[Archivos] " + msg + "\n")
                self.logtxt.see(tk.END)

        def seleccionar_todos(self):
            for iid in self.tree.get_children():
                self.tree.selection_add(iid)
            self.logear_panel("Seleccionados todos los archivos en el listado.")

        def deseleccionar_todos(self):
            for iid in self.tree.selection():
                self.tree.selection_remove(iid)
            self.logear_panel("Deseleccionados todos los archivos.")

        def salir(self):
            self.logear_panel("Aplicación finalizada a solicitud del usuario.")
            self.frame.quit()
            self.frame.winfo_toplevel().quit()
            print("aplicacion cerrada correctamente")

        def single_sd(self):
            carpeta = filedialog.askdirectory(title="Seleccionar carpeta SD única")
            if carpeta:
                self.selected_sd_folder = carpeta
                self.multi_sd_flag = False
                self.sd_label.config(text="SD único: " + carpeta)
                self.logear_panel(f"Seleccionado SD único: {carpeta}")
                self.escanear_archivos_inner()
        def multi_sd(self):
            carpeta = filedialog.askdirectory(title="Seleccionar carpeta con varios SDs")
            if carpeta:
                self.selected_sd_folder = carpeta
                self.multi_sd_flag = True
                self.sd_label.config(text="Carpeta con varios SDs: " + carpeta)
                self.logear_panel(f"Seleccionada carpeta multi-SD: {carpeta}")
                self.escanear_archivos_inner()

        def escanear_archivos_inner(self):
            carpeta = self.selected_sd_folder
            multi = self.multi_sd_flag
            if not carpeta:
                messagebox.showwarning("Advertencia", "Seleccione una carpeta válida.", parent=self.frame)
                self.repetidos_log = []
                self.logear_panel("Intento de escaneo con carpeta inválida.")
                return
            archivos_candidatos = explorar_sd_folder(carpeta, multi_sd=multi)
            if not archivos_candidatos:
                self.tree.delete(*self.tree.get_children())
                self.archivos_unicos = []
                self.repetidos_log = []
                self.logear_panel("No se detectaron archivos candidatos en la carpeta.")
                return
            self.archivos_unicos, self.repetidos_log = quitar_repetidos(archivos_candidatos)
            self.tree.delete(*self.tree.get_children())
            for idx, a in enumerate(self.archivos_unicos):
                import datetime
                fecha = datetime.datetime.fromtimestamp(a['fecha_mod']).strftime('%Y-%m-%d %H:%M:%S')
                ruta_corta = a['rel_path']
                tag = "alt" if idx % 2 == 1 else ""
                self.tree.insert("", "end", iid=idx, values=(a['nombre_archivo'], ruta_corta, fecha), tags=(tag,))
            self.tree.tag_configure('alt', background="#f3f9fb")
            self.logear_panel(f"Escaneados {len(self.archivos_unicos)} archivos únicos. Repetidos: {len(self.repetidos_log)}.")

        def get_tooltip_for_row(self, iid):
            if iid and iid.isdigit() and int(iid)<len(self.archivos_unicos):
                return self.archivos_unicos[int(iid)]['rel_path']
            return ""

        def ver_repetidos(self):
            import datetime
            
            if not hasattr(self, "repetidos_log"):
                self.repetidos_log = []
            if not self.repetidos_log:
                messagebox.showinfo("Sin repetidos", "No se detectaron repeticiones en el último escaneo.", parent=self.frame)
                self.logear_panel("Se consultaron repetidos pero no había repeticiones.")
                return

            win = tk.Toplevel(self.frame)
            win.title("Fuentes repetidos")
            st = scrolledtext.ScrolledText(win, width=130, height=18, font=FUENTE_GENERAL, bg="white")
            st.pack(fill="both", expand=True)
            for entry in self.repetidos_log:
                key = entry['nombre_ext']
                escog = entry['escogido']
                st.insert(tk.END, f"Archivo: {key[0]} ({key[1]})\n")
                st.insert(tk.END, f"  Elegido:     {escog['rel_path']}  [Fecha: {datetime.datetime.fromtimestamp(escog['fecha_mod']).strftime('%Y-%m-%d %H:%M:%S')}]\n")
                for desc in entry['descartados']:
                    st.insert(tk.END, f"  Descartado:  {desc['rel_path']}  [Fecha: {datetime.datetime.fromtimestamp(desc['fecha_mod']).strftime('%Y-%m-%d %H:%M:%S')}]\n")
                st.insert(tk.END, "-"*110+"\n")
            st.configure(state="disabled")
            self.logear_panel("Mostrada ventana de fuentes repetidos.")

        def validar_seleccionados(self):
            seleccionados_archivos = [int(iid) for iid in self.tree.selection()]
            if not seleccionados_archivos:
                messagebox.showwarning("Validación", "Seleccione uno o más archivos de la lista.", parent=self.frame)
                self.logear_panel("Intento de validar sin selección de archivos.")
                return

            ambientes_panel = self.ambientes_panel

            selamb_idx = ambientes_panel.lbamb.curselection()
            if not selamb_idx:
                messagebox.showwarning("Validación", "No ha seleccionado ambientes para validar.", parent=self.frame)
                self.logear_panel("Intento de validar sin selección de ambientes.")
                return

            no_conectados = [idx for idx in selamb_idx if ambientes_panel.estado_conex_ambs[idx] is not True]
            if no_conectados:
                nombres = [ambientes_panel.ambientes[i]['nombre'] for i in no_conectados]
                msg = "Debe seleccionar solo ambientes con CONEXIÓN exitosa (verde) antes de validar.\n" \
                    "Los siguientes ambientes no tienen conexión exitosa:\n" + \
                    "\n".join(f"- {n}" for n in nombres)
                messagebox.showwarning("Ambiente", msg, parent=self.frame)
                self.logear_panel("Intento de validar ambientes sin conexión OK.")
                return

            self.logear_panel("Validando seleccionados contra multiambiente (detalle en log).")
            lanzar_validacion(self.frame, self.archivos_unicos, seleccionados_archivos, ambientes_panel)

        def lanzar_catalogacion(self):
            def aceptar(nombre, descripcion):
                messagebox.showinfo("Catalogado", f"Archivo '{nombre}' catalogado.\nDescripción: {descripcion}")
                self.logear_panel(f"Archivo '{nombre}' catalogado con descripción '{descripcion}'.")
            CatalogacionDialog(self.frame, aceptar_callback=aceptar)

    #--------------------------panel de ambientes-------------------------------------

    class AmbientesPanel:
        
        def __init__(self, parent, logtxt=None):
            self.frame = ttk.LabelFrame(parent, text="Ambientes Configurados", padding=(12, 8), style="SidePanel.TLabelframe")
            self.ambientes = cargar_ambientes()
            self.estado_conex_ambs = [None] * len(self.ambientes)  # None: sin testear, True: OK, False: fallido

            # Permitir asignar el widget del log externo (compartido con archivos_panel.py, por ejemplo)
            self.logtxt = logtxt

            icon_path = os.path.join(os.path.dirname(__file__), "imagenes_iconos/zeta99.png")
            if os.path.exists(icon_path):
                self.zeta_icon = PhotoImage(file=icon_path)
            else:
                self.zeta_icon = None

            self.btn_testamb = ttk.Button(
                self.frame,
                text="Probar Conexión",
                image=self.zeta_icon,
                compound="left" if self.zeta_icon else None,
                command=self.test_ambs,
                style="BotonConectar.Amarillo.TButton"
            )
            self.btn_testamb.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12), padx=(5,5))

            self.lbamb = tk.Listbox(
                self.frame, selectmode=tk.MULTIPLE, exportselection=0, height=9,
                font=FUENTE_GENERAL, bg="white"
            )
            self.lbamb.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, 8), padx=(0, 0))
            self.refresh_amb_list([])

            self.frame.rowconfigure(1, weight=1)
            self.frame.columnconfigure(0, weight=1)

            botones_amb = ttk.Frame(self.frame, style="Panel2.TFrame")
            botones_amb.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10,0))
            ttk.Button(botones_amb, text="➕ Agregar", command=self.add_amb).grid(row=0, column=0, padx=2, pady=2, sticky='ew')
            ttk.Button(botones_amb, text="✏️ Editar", command=self.edit_amb).grid(row=1, column=0, padx=2, pady=2, sticky='ew')
            ttk.Button(botones_amb, text="🗑️ Eliminar", command=self.del_amb).grid(row=2, column=0, padx=2, pady=2, sticky='ew')

            self.amb_estado = tk.Label(self.frame, text="", fg=COLOR_ACCION, anchor="w", bg=FONDO_PANEL2, font=FUENTE_GENERAL)
            self.amb_estado.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))

            self.progressbar_amb = ttk.Progressbar(
                self.frame,
                orient="horizontal",
                length=220,
                style="ProgressYellow.Horizontal.TProgressbar",
                mode="determinate"
            )
            self.progressbar_amb.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 0))
            self.progressbar_amb.grid_remove()

        def logear_panel(self, msg):
            if self.logtxt is not None:
                self.logtxt.insert(tk.END, "[Ambientes] " + msg + "\n")
                self.logtxt.see(tk.END)

        def refresh_amb_list(self, keep_selection):
            self.lbamb.delete(0, tk.END)
            for amb in self.ambientes:
                self.lbamb.insert(
                    tk.END,
                    f"{amb['nombre']} | {amb['ip']} | {amb['puerto']} | {amb['usuario']}"
                )
            for idx in keep_selection:
                self.lbamb.select_set(idx)
            self.colorear_lbamb()

        def add_amb(self):
            self.editar_amb_dialog(nuevo=True)

        def edit_amb(self):
            sel = self.lbamb.curselection()
            if not sel:
                messagebox.showinfo("Editar ambiente", "Seleccione uno", parent=self.frame)
                return
            idx = sel[0]
            self.editar_amb_dialog(nuevo=False, editar_idx=idx)

        def del_amb(self):
            sel = self.lbamb.curselection()
            if not sel:
                return
            idx = sel[0]
            ok = messagebox.askyesno("Confirma", "¿Eliminar el ambiente seleccionado?", parent=self.frame)
            if ok:
                self.logear_panel(f"Eliminado ambiente: {self.ambientes[idx]['nombre']}")
                self.ambientes.pop(idx)
                self.estado_conex_ambs.pop(idx)
                guardar_ambientes(self.ambientes)
                self.refresh_amb_list([])

        def editar_amb_dialog(self, nuevo=True, editar_idx=None):
            window = tk.Toplevel(self.frame)
            window.title("Nuevo ambiente" if nuevo else "Editar ambiente")
            fields = [
                ("Nombre","nombre"),("IP/HOST","ip"),("Puerto","puerto"),
                ("Usuario","usuario"),("Clave","clave"),("Base de datos","base"),
                ("Driver ODBC","driver")
            ]
            default = {'driver':'Sybase ASE ODBC Driver', 'puerto':'7028'}
            vals = {}
            for i, (lbl, key) in enumerate(fields):
                tk.Label(window, text=lbl+":", font=FUENTE_GENERAL).grid(row=i, column=0, sticky="w", padx=8, pady=3)
                ent = tk.Entry(window, width=32, show="*" if key=="clave" else None, font=FUENTE_GENERAL)
                ent.grid(row=i, column=1, padx=8, pady=3)
                vals[key] = ent
            if not nuevo and editar_idx is not None:
                amb = self.ambientes[editar_idx]
                for key in vals:
                    if key in amb:
                        vals[key].insert(0, amb[key])
            else:
                for key in vals:
                    if key in default:
                        vals[key].insert(0, default[key])
            def snd():
                data = {key: vals[key].get() for key in vals}
                if not all(data[x] for x in ['nombre', 'ip', 'puerto', 'usuario', 'clave', 'base', 'driver']):
                    messagebox.showwarning("Error", "Faltan datos obligatorios", parent=window)
                    return
                if nuevo:
                    self.ambientes.append(data)
                    self.estado_conex_ambs.append(None)
                    self.logear_panel(f"Agregado nuevo ambiente: {data['nombre']}")
                else:
                    self.logear_panel(f"Editado ambiente: {data['nombre']} (Anterior: {self.ambientes[editar_idx]['nombre']})")
                    self.ambientes[editar_idx] = data
                guardar_ambientes(self.ambientes)
                self.refresh_amb_list([])
                window.destroy()
            tk.Button(window, text="Guardar", command=snd, font=FUENTE_GENERAL).grid(row=len(fields), column=0, pady=6)
            tk.Button(window, text="Cancelar", command=window.destroy, font=FUENTE_GENERAL).grid(row=len(fields), column=1, pady=6)

        def test_ambs(self):
            sel = self.lbamb.curselection()
            if not sel:
                messagebox.showinfo("Conexión", "Seleccione al menos un ambiente para probar.", parent=self.frame)
                return

            self.btn_testamb.config(style="BotonConectar.Amarillo.TButton")
            self.frame.update()

            total = len(sel)
            self.progressbar_amb.config(style="ProgressYellow.Horizontal.TProgressbar")
            self.progressbar_amb['maximum'] = total
            self.progressbar_amb['value'] = 0
            self.progressbar_amb.grid()
            hay_exito = False
            hay_fallo = False

            for idx in sel:
                self.estado_conex_ambs[idx] = None

            for i, idx in enumerate(sel):
                amb = self.ambientes[idx]
                self.progressbar_amb['value'] = i
                self.amb_estado.config(
                    text=f"Probando ambiente {amb['nombre']}...",
                    fg=COLOR_ACCION
                )
                # MODIFICACIÓN: pasamos self.logear_panel a probar_conexion_amb
                self.logear_panel(f"Intentando conexión al ambiente '{amb['nombre']}'")
                self.frame.update()
                ok, msg = probar_conexion_amb(amb, log_func=self.logear_panel)
                self.progressbar_amb['value'] = i + 1

                self.estado_conex_ambs[idx] = ok

                if ok:
                    self.progressbar_amb.config(style="ProgressGreen.Horizontal.TProgressbar")
                    self.amb_estado.config(
                        text=f"Ambiente {amb['nombre']}: Conexión exitosa",
                        fg=COLOR_RESALTADO
                    )
                    hay_exito = True
                    self.logear_panel(f"Conexión exitosa a '{amb['nombre']}': {msg}")
                else:
                    self.progressbar_amb.config(style="ProgressRed.Horizontal.TProgressbar")
                    self.amb_estado.config(
                        text=f"Ambiente {amb['nombre']}: Conexión fallida",
                        fg="#dc2626"
                    )
                    hay_fallo = True
                    self.logear_panel(f"Conexión *fallida* a '{amb['nombre']}': {msg}")
                self.frame.update()

            self.progressbar_amb.grid_remove()
            self.colorear_lbamb()
            self.lbamb.selection_clear(0, tk.END)

            if hay_exito and not hay_fallo:
                self.btn_testamb.config(style="BotonConectar.Verde.TButton")
                self.amb_estado.config(text="Todas las conexiones exitosas", fg=COLOR_RESALTADO)
                self.logear_panel("Prueba de ambientes: ¡todas las conexiones exitosas!")
            elif hay_exito and hay_fallo:
                self.btn_testamb.config(style="BotonConectar.Verde.TButton")
                self.amb_estado.config(text="Al menos un ambiente OK", fg=COLOR_RESALTADO)
                self.logear_panel("Prueba de ambientes: al menos un ambiente OK, alguno fallido.")
            else:
                self.btn_testamb.config(style="BotonConectar.Rojo.TButton")
                self.amb_estado.config(text="Todas las conexiones fallidas", fg="#dc2626")
                self.logear_panel("Prueba de ambientes: todas las conexiones fallidas.")

        def colorear_lbamb(self):
            for idx in range(self.lbamb.size()):
                estado = self.estado_conex_ambs[idx] if idx < len(self.estado_conex_ambs) else None
                if estado is True:
                    self.lbamb.itemconfig(idx, {'bg': '#22c55e', 'fg': 'white'})
                elif estado is False:
                    self.lbamb.itemconfig(idx, {'bg': '#ef4444', 'fg': 'white'})
                else:
                    self.lbamb.itemconfig(idx, {'bg': 'white'})