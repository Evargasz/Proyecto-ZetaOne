from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, messagebox
from ventana_credenciales import credenciales
from Usuario_basico.usu_basico_main import usuBasicoMain
import os

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

        # Título (etiqueta más grande)
        label_bienvenida = tk.Label(
            root,
            text="Bienvenido a ZetaOne",
            font=("Arial", 28, "bold"),    # Fuente más grande y negrita
            bg="#EBF0F1"
        )
        label_bienvenida.pack(pady=48)     # Más espacio arriba

        # Botones grandes con fuente grande
        boton_font = ("Arial", 12, "bold")    # Cambia este valor para ajustar tamaño

        btn_usuario = tk.Button(
            root,
            text="Usuario básico",
            width=22,
            height=1,
            font=boton_font,
            command=self.usuario_normal
        )
        btn_usuario.pack(pady=15)

        btn_admin = tk.Button(
            root,
            text="Administrador / catalogador",
            width=22,
            height=1,
            font=boton_font,
            command=self.ir_credenciales
        )
        btn_admin.pack(pady=15)

        btn_salir = tk.Button(
            root,
            text="salir",
            width=22,
            height=1,
            font=boton_font,
            command=self.root.quit
        )
        btn_salir.pack(pady=15)

    def ir_credenciales(self):
        if self.controlador:
            self.controlador.mostrar_credenciales()

    def usuario_normal(self):
        if self.controlador:
            self.controlador.mostrar_basico()

# Código para iniciar la ventana principal
if __name__ == "__main__":
    root = tk.Tk()
    app = PantallaInicio(root)
    root.mainloop()