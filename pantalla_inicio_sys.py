from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, messagebox
from ventana_credenciales import credenciales
from Usuario_basico.usu_basico_main import usuBasicoMain
import os
from styles import boton_principal, etiqueta_titulo
from util_rutas import recurso_path

class PantallaInicio: 
    def __init__(self, root, controlador=None):
        self.root = root
        self.controlador = controlador
        self.root.title("ZetaOne")

        # Icono
        ruta = recurso_path("imagenes_iconos", "Zeta99.ico")
        self.root.iconbitmap(ruta)

        # Imagen de fondo fija 400x350
        ruta_carpeta = os.path.dirname(__file__)
        ruta_imagen = os.path.join(ruta_carpeta, "imagenes_iconos", "ZetaOne_bg_op2.jpg")
        self.bg_image = Image.open(ruta_imagen)
        self.bg_image = self.bg_image.resize((400, 350))
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        self.background_label = tk.Label(self.root, image=self.bg_photo)
        self.background_label.image = self.bg_photo  # IMPORTANTE
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)   

        # Botones grandes con fuente grande
        
        btn_usuario = boton_principal(
            root,
            "Usuario básico",
            comando=self.usuario_normal,
        )
        btn_usuario.pack(pady=(120, 15))

        btn_admin = boton_principal(
            root,
            "Administrador / catalogador",
            comando=self.ir_credenciales, width=30
        )
        btn_admin.pack(pady=15)

        btn_salir = boton_principal(
            root,
            "salir",
            comando=self.root.quit, width=10
        )
        btn_salir.pack(pady=15)

    def ir_credenciales(self):
        if self.controlador:
            self.controlador.mostrar_credenciales()

    def usuario_normal(self):
        if self.controlador:
            self.controlador.mostrar_basico()

