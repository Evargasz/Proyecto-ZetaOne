import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from handlers.explorador import explorar_sd_folder
from util_repetidos import quitar_repetidos
from styles import FUENTE_GENERAL, COLOR_ACCION
from widgets.tooltip import ToolTip
from validacion_dialog import lanzar_validacion
from catalogacion_dialog import CatalogacionDialog
from styles import FUENTE_GENERAL



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
        from tkinter import scrolledtext

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
    
    