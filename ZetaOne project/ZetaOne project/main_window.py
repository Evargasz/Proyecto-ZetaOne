from tkinter import ttk, scrolledtext
from styles import configurar_estilos, configurar_botones_personalizados
from ambientes_panel import AmbientesPanel
from archivos_panel import ArchivosPanel

class mainWindow:
    def __init__(self, root):
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
        self.root.iconbitmap("Zeta99.ico")

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
        self.amb_panel = AmbientesPanel(main_frame)
        self.amb_panel.frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 8))

        # Panel de Archivos (derecha)
        self.arch_panel = ArchivosPanel(main_frame, self.amb_panel, toggle_log_callback=self.toggle_log)
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

        # Si quieres que el foco vaya al log cuando se muestre, puedes dejar esta línea:
        # self.logtxt.focus_set()

    def toggle_log(self):
        if self.log_visible:
            self.logtxt.grid_remove()
            self.log_visible = False
        else:
            self.logtxt.grid()
            self.log_visible = True