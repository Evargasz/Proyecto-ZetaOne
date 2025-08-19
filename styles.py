#---------------colores y fuentes--------

FONDO_BTN_N="#e0e0e0"

HOVER_BTN_N = "#b4b4b4"

from ttkbootstrap.widgets import Button, Label, Frame, Entry

def configurar_estilos(style):
    #-------------------------confi ventana princial-------------------
        #botones
    style.configure(
        'PrincipalInicio.TButton', 
        foreground="black", 
        background=FONDO_BTN_N, 
        font=("Arial", 10, "bold"), 
        padding=10, 
        relief=FONDO_BTN_N,
        width=30
    )
    style.map(
        'PrincipalInicio.TButton',
        background=[('active', HOVER_BTN_N)],
        foreground=[('active', 'black')],
        bordercolor=[('active', HOVER_BTN_N)],
        relief=[('active', 'solid')]
    )
    #---------------------confi ventana credenciales----------------
        #botones
    style.configure(
        'Creden.TButton',
        foreground='black',  # <- corregido "foeground"
        background=FONDO_BTN_N,
        font=("Arial", 8, "bold"),
        padding=6,
        relief=FONDO_BTN_N,
        width=10
    )
    style.map(
        'Creden.TButton',
        background=[('active', HOVER_BTN_N)],
        foreground=[('active', 'black')],
        bordercolor=[('active', HOVER_BTN_N)],
        relief=[('active', 'solid')]
    )

    #------------------------Usuario basico -----------------------
        #botones 

#-------------------------------------------------------------------------------------------------------------------------

#acciones de botones y demas
def boton_principal(master, texto, comando=None, **kwargs):
    return Button(master, text=texto, command=comando, style='PrincipalInicio.TButton', **kwargs)

def boton_creden(master, texto, comando=None, **kwargs):
    return Button(master, text=texto, command=comando, style='Creden.TButton', **kwargs)

def boton_accion(master, texto, comando=None, **kwargs):
    return Button(master, text=texto, command=comando, bootstyle="dark", **kwargs)

def boton_exito(master, texto, comando=None, **kwargs):
    return Button(master, text=texto, command=comando, bootstyle="success", **kwargs)

def boton_rojo(master, texto, comando=None, **kwargs):
    return Button(master, text=texto, command=comando, bootstyle="danger", **kwargs)

def etiqueta_titulo(master, texto, **kwargs):
    return Label(master, text=texto, bootstyle="default", **kwargs)

def entrada_estandar(master, **kwargs):
    return Entry(master, bootstyle="default", **kwargs)

def img_boton(master, comando=None, **kwargs):
    return Button(master, command=comando, bootstyle="light-outline", **kwargs)

def label_img(master, **kwargs):
    return Button(master, bootstyle="light", **kwargs)

def boton_comun(master, texto, comando=None, **kwargs):
    return Button(master, text=texto, command=comando, bootstyle="dark-outline-button", **kwargs)




#-----------------------EJEMPLO DE COMO CAMBIAR LOS COLORES---------------------------------

# style.configure("primary.TButton", foreground="white", background="#8e44ad")

# btn = Button(root, text="Botón Morado (Primary)", bootstyle="primary")

# btn.pack(padx=10, pady=10)

#----------------------------ventana de usuario basico---------------------------------- 

#frame derecho: (panel principal)


