# styles.py

# Colores principales
FONDO_MAIN     = "#f8fafc"
FONDO_PANEL    = "#e2e8f0"
FONDO_PANEL2   = "#c7d2fe"
FONDO_WIDGET   = "#f1f5f9"
COLOR_ACCION   = "#2563eb"
COLOR_RESALTADO= "#22c55e"
COLOR_TEXTO    = "#172554"

# Fuentes principales
FUENTE_GENERAL = ("Segoe UI", 10)
FUENTE_BOTON   = ("Segoe UI", 11, "bold")
FUENTE_HEADING = ("Segoe UI", 10, "bold")

def configurar_estilos(style):
    style.theme_use("clam")
    style.configure("Panel.TFrame", background=FONDO_MAIN, relief="flat")
    style.configure("Panel2.TFrame", background=FONDO_PANEL)
    style.configure("SidePanel.TLabelframe", background=FONDO_PANEL2, font=(FUENTE_HEADING), borderwidth=2, relief="ridge")
    style.configure("MainPanel.TLabelframe", background=FONDO_PANEL, font=(FUENTE_HEADING), borderwidth=2, relief="ridge")
    style.configure("TLabel", font=FUENTE_GENERAL, background=FONDO_MAIN)
    style.configure("TButton", font=FUENTE_BOTON, padding=6)
    style.map("TButton", background=[("active", "#c7d2fe")])
    style.configure("Accion.TButton", background=COLOR_ACCION, foreground="white", font=FUENTE_BOTON, padding=6)
    style.configure("Salir.TButton", background="#ef4444", foreground="white", font=FUENTE_BOTON, padding=6)
    style.configure("Treeview.Heading", font=FUENTE_HEADING, background=FONDO_PANEL2)
    style.configure("Treeview", font=FUENTE_GENERAL, rowheight=27, background="white", fieldbackground=FONDO_PANEL, borderwidth=0, relief="flat")
    style.configure("Treeview.Fallido", background="#fecaca", foreground="#b91c1c")
    style.configure("Barra.TFrame", background=FONDO_WIDGET)

    # PROGRESO DELGADO, SIN BORDE, SIN TKINTER, SOLO TTK
    style.configure(
        "ProgressYellow.Horizontal.TProgressbar",
        troughcolor="#fffde8",     # canal claro
        background="#fde047",      # barra amarilla
        thickness=24,
        borderwidth=0,
        relief='flat'
    )
    style.configure(
        "ProgressGreen.Horizontal.TProgressbar",
        troughcolor='#f0fff4',
        background="#22c55e",
        thickness=18,
        borderwidth=0,
        relief='flat'
    )
    style.configure(
        "ProgressRed.Horizontal.TProgressbar",
        troughcolor='#fff2f2',
        background="#dc2626",
        thickness=18,
        borderwidth=0,
        relief='flat'
    )
    style.configure(
        "ProgressBlue.Horizontal.TProgressbar",
        troughcolor='#eaf4ff',
        background="#2563eb",
        thickness=18,
        borderwidth=0,
        relief='flat'
    )
    style.configure("ProgressFrame.TFrame", background="#fff")
    style.configure("Treeview.Fallido", background="#fecaca", foreground="#b91c1c")

def configurar_botones_personalizados(style):
    style.configure("BotonConectar.Amarillo.TButton", background="#fde047", foreground="#78350f", font=FUENTE_BOTON)
    style.configure("BotonConectar.Verde.TButton", background="#22c55e", foreground="white", font=FUENTE_BOTON)
    style.configure("BotonConectar.Rojo.TButton", background="#ef4444", foreground="white", font=FUENTE_BOTON)
    style.map("BotonConectar.Rojo.TButton",
              background=[("active", "#b91c1c")])   