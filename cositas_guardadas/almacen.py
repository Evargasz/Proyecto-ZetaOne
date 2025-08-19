from PIL import Image, ImageTk
import tkinter as tk
from ventana_credenciales import credenciales
from Usuario_basico.usu_basico_main import usuBasicoMain
import os
from styles import boton_principal, boton_accion, boton_exito, boton_rojo

class PantallaInicio: 
    def __init__(self, root, controlador=None):
        self.root = root
        self.controlador = controlador
        self.root.title("ZetaOne")
        ventana_ancho = 500
        ventana_alto = 450
        pantalla_ancho = self.root.winfo_screenwidth()
        pantalla_alto = self.root.winfo_screenheight()
        x = int((pantalla_ancho / 2) - (ventana_ancho / 2 ))
        y = int((pantalla_alto / 2) - (ventana_alto / 2))
        self.root.geometry(f"{ventana_ancho}x{ventana_alto}+{x}+{y}")
        root.resizable(False, False)

        # Icono
        ruta = os.path.join(os.path.dirname(__file__), "imagenes_iconos", "Zeta99.ico")
        self.root.iconbitmap(ruta)

        # Imagen de fondo ajustada al nuevo tamaño
        ruta_carpeta = os.path.dirname(__file__)
        ruta_imagen = os.path.join(ruta_carpeta, "imagenes_iconos", "ZetaOne_img_bg.jpg")
        self.bg_image = Image.open(ruta_imagen)
        self.bg_image = self.bg_image.resize((ventana_ancho, ventana_alto))
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        self.background_label = tk.Label(self.root, image=self.bg_photo)
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)
        self.background_label.image = self.bg_photo  # Esto lo "amarra" incluso si tu clase cambia

        # Título (etiqueta más grande)
        label_bienvenida = tk.Label(
            root,
            "Bienvenido a ZetaOne",
            font=("Arial", 28, "bold"),    # Fuente más grande y negrita
            
        )
        label_bienvenida.pack(pady=48)     # Más espacio arriba

        # Botones grandes con fuente grande
        # boton_font = ("Arial", 12, "bold")    # Cambia este valor para ajustar tamaño

        btn_usuario = boton_principal(
            root,
            "Usuario básico",
            comando=self.usuario_normal
        )
        btn_usuario.pack()

        btn_admin = boton_principal(
            root,
            "Administrador / catalogador",
            comando=self.ir_credenciales
        )
        btn_admin.pack()

        btn_salir = boton_rojo(
            root,
            "salir",
            comando=self.root.quit
        )
        btn_salir.pack()

    def ir_credenciales(self):
        if self.controlador:
            self.controlador.mostrar_credenciales()

    def usuario_normal(self):
        if self.controlador:
            self.controlador.mostrar_basico()

