import ttkbootstrap as tb
from ttkbootstrap.constants import *
import tkinter as tk
import os
from Usuario_administrador.handlers.ambientes import cargar_ambientes, guardar_ambientes, probar_conexion_amb


class AmbientesPanel:
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
            
    def __init__(self, parent, logtxt=None):
        # Panel principal de ambientes, usando LabelFrame de bootstrap
        self.frame = tb.LabelFrame(parent, text="Ambientes Configurados", bootstyle="primary", padding=(12, 8))
        
        self.ambientes = cargar_ambientes()
        self.estado_conex_ambs = [None] * len(self.ambientes)  # Estado de conexión de cada ambiente

        self.logtxt = logtxt

        # Icono para el botón de "Probar Conexión"
        icon_path = os.path.join(os.path.dirname(__file__), "imagenes_iconos/zeta99.png")
        if os.path.exists(icon_path):
            self.zeta_icon = tk.PhotoImage(file=icon_path)
        else:
            self.zeta_icon = None

        # Botón para probar conexión, con estilo 'warning outline'
        self.btn_testamb = tb.Button(
            self.frame,
            text="Probar Conexión",
            image=self.zeta_icon,
            compound="left" if self.zeta_icon else None,
            command=self.test_ambs,
            bootstyle="warning-outline"
        )
        self.btn_testamb.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12), padx=(5,5))

        # Frame para los ambientes (los checkbuttons)
        self.ambientes_vars = []
        self.check_frame = tb.Frame(self.frame)
        self.check_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0,8), padx=(0, 0))
        self.refresh_amb_list()

        self.frame.rowconfigure(1, weight=1)
        self.frame.columnconfigure(0, weight=1)

        # Botones de Agregar, Editar, Eliminar con estilos bootstrap
        botones_amb = tb.Frame(self.frame)
        botones_amb.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10,0))
        tb.Button(botones_amb, text="➕ Agregar", command=self.add_amb, bootstyle="success-outline").grid(row=0, column=0, padx=2, pady=2, sticky='ew')
        tb.Button(botones_amb, text="✏️ Editar", command=self.edit_amb, bootstyle="info-outline").grid(row=1, column=0, padx=2, pady=2, sticky='ew')
        tb.Button(botones_amb, text="🗑️ Eliminar", command=self.del_amb, bootstyle="danger-outline").grid(row=2, column=0, padx=2, pady=2, sticky='ew')

        # Estado, label elegante
        self.amb_estado = tb.Label(self.frame, text="", anchor="w", bootstyle="inverse-info", font=("Segoe UI", 10, "bold"))
        self.amb_estado.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        # Progressbar elegante
        self.progressbar_amb = tb.Progressbar(
            self.frame,
            orient="horizontal",
            length=220,
            bootstyle="warning-striped",
            mode="determinate"
        )
        self.progressbar_amb.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self.progressbar_amb.grid_remove()

    def logear_panel(self, msg):
        # Log externo
        if self.logtxt is not None:
            self.logtxt.insert(tk.END, "[Ambientes] " + msg + "\n")
            self.logtxt.see(tk.END)

    def refresh_amb_list(self):
        # Borra y vuelve a crear los checkbutton con el nuevo estado
        for widget in self.check_frame.winfo_children():
            widget.destroy()
        self.ambientes_vars.clear()
        for idx, amb in enumerate(self.ambientes):
            var = tk.BooleanVar()
            self.ambientes_vars.append(var)
            label = f"{amb['nombre']} | {amb['ip']} | {amb['puerto']} | {amb['usuario']}"

            # Determina el estilo del checkbutton según el estado de conexión
            estado = self.estado_conex_ambs[idx]
            if estado is True:
                bootstyle = "success-round-toggle"
            elif estado is False:
                bootstyle = "danger-round-toggle"
            else:
                bootstyle = "secondary-round-toggle"

            chk = tb.Checkbutton(self.check_frame, text=label, variable=var,
                                 bootstyle=bootstyle, font=("Segoe UI", 10))
            chk.grid(row=idx, sticky='w', padx=2, pady=1)

    def add_amb(self):
        self.editar_amb_dialog(nuevo=True)

    def edit_amb(self):
        sel = [i for i, v in enumerate(self.ambientes_vars) if v.get()]
        if not sel:
            tb.Messagebox.show_info("Editar ambiente", "Seleccione uno", parent=self.frame)
            return
        idx = sel[0]
        self.editar_amb_dialog(nuevo=False, editar_idx=idx)

    def del_amb(self):
        sel = [i for i, v in enumerate(self.ambientes_vars) if v.get()]
        if not sel:
            return
        idx = sel[0]
        ok = tb.Messagebox.yesno("Confirma", "¿Eliminar el ambiente seleccionado?", parent=self.frame)
        if ok:
            self.logear_panel(f"Eliminado ambiente: {self.ambientes[idx]['nombre']}")
            self.ambientes.pop(idx)
            self.estado_conex_ambs.pop(idx)
            guardar_ambientes(self.ambientes)
            self.refresh_amb_list()

    # Los métodos editar_amb_dialog, test_ambs, etc, pueden mantenerse tal y como los tienes, 
    # solo actualiza los messagebox/showinfo por los tb.Messagebox equivalentes.
import ttkbootstrap as tb

if __name__ == "__main__":
    root = tb.Window(themename="litera")
    panel = AmbientesPanel(root)
    panel.frame.pack(fill="both", expand=True)
    root.mainloop()