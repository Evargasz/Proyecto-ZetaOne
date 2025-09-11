import tkinter as tk
from tkinter import ttk, messagebox, PhotoImage
import os
from handlers.ambientes import cargar_ambientes, guardar_ambientes, probar_conexion_amb
from styles import COLOR_ACCION, COLOR_RESALTADO, FONDO_PANEL2, FUENTE_GENERAL

class AmbientesPanel:
    def __init__(self, parent, logtxt=None):
        self.frame = ttk.LabelFrame(parent, text="Ambientes Configurados", padding=(12, 8), style="SidePanel.TLabelframe")
        self.ambientes = cargar_ambientes()
        self.estado_conex_ambs = [None] * len(self.ambientes)  # None: sin testear, True: OK, False: fallido

        # Permitir asignar el widget del log externo (compartido con archivos_panel.py, por ejemplo)
        self.logtxt = logtxt

        icon_path = os.path.join(os.path.dirname(__file__), "zeta99.png")
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