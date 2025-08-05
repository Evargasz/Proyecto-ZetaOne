#Libreria
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, messagebox

#Importar estilos 
from Usuario_administrador.styles import configurar_estilos

#manipulacion de archivos del sistema operativo
import os #os = Operative System?

#Importar credenciales validas
import json

#importar linkeos



class credenciales:
    def __init__(self, root, controlador):
        self.root = root
        self.controlador = controlador
        self.root.title("ZetaOne")
        ventana_ancho = 250
        ventana_alto = 250
        pantalla_ancho = self.root.winfo_screenwidth()
        pantalla_alto = self.root.winfo_screenheight()
        x = int((pantalla_ancho / 2) - (ventana_ancho / 2 ))
        y = int((pantalla_alto / 2) - (ventana_alto / 2))
        self.root.geometry(f"{ventana_ancho}x{ventana_alto}+{x}+{y}")
        root.resizable(False, False)
    #icono
        ruta = os.path.join(os.path.dirname(__file__), "imagenes_iconos", "Zeta99.ico")
        self.root.iconbitmap(ruta)

    #Imagen de fondo
        
        ruta_carpeta = os.path.dirname(__file__)
        ruta_imagen = os.path.join(ruta_carpeta, "imagenes_iconos", "ZetaOne_img_bg.jpg")
        self.bg_image = Image.open(ruta_imagen)
        self.bg_image = self.bg_image.resize((250, 250))  # ajusta al tamaño de la ventana
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        self.background_label = tk.Label(self.root, image=self.bg_photo)
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)

    #estos son los campos visibles de la ventana

        #titulo
        self.lbl_titulo = tk.Label(self.root, text="CREDENCIALES", font=("Arial", 14, "bold"), bg="#EBF0F1")
        self.lbl_titulo.place(relx=0.5, y=30, anchor="center")
        
        #Usuario
        self.entry_usuario = ttk.Entry(self.root, font=("Arial", 12))
        self.entry_usuario.place(relx=0.5, y=70, anchor="center", width=200, height=35)
        self.entry_usuario.insert(0, "Usuario")

        def clear_placeholder_usu(event):
            if self.entry_usuario.get() == "Usuario":
                self.entry_usuario.delete(0, tk.END)
                self.entry_usuario.config(foreground='black')
        
        def add_placeholder_usu(event):
            if self.entry_usuario.get() == "":
                self.entry_usuario.insert(0, "Usuario")
                self.entry_usuario.config(foreground='black')

        self.entry_usuario.bind("<FocusIn>", clear_placeholder_usu)
        self.entry_usuario.bind("<FocusOut>", add_placeholder_usu)

        #contraseña
        self.entry_contraseña = ttk.Entry(self.root, font=("Arial", 12), show="", foreground='black')
        self.entry_contraseña.place(relx=0.5, y=120, anchor="center", width=200, height=35)
        self.entry_contraseña.insert(0, "contraseña")

        def clear_placeholder_psw(event):
            if self.entry_contraseña.get() == "contraseña":
                self.entry_contraseña.delete(0, tk.END)
                self.entry_contraseña.config(foreground='black', show="*")

        def add_placeholder_psw(event):
            if self.entry_contraseña.get() == "":
                self.entry_contraseña.insert(0, "contraseña")
                self.entry_contraseña.config(foreground='black', show="")
        
        self.entry_contraseña.bind("<FocusIn>", clear_placeholder_psw)
        self.entry_contraseña.bind("<FocusOut>", add_placeholder_psw)
        self.entry_contraseña.bind("<Return>", lambda event: self.iniciar_sesion()) 

        #botones
        self.btn_iniciar = tk.Button(self.root, text="Iniciar sesión", command=self.iniciar_sesion, bg="#FAF1F0", fg="black", font=("Arial", 11), borderwidth=3, width=12, height=1)
        self.btn_iniciar.place(relx=0.66, y=170, anchor="center")

        self.btn_salir = tk.Button(self.root, text="salir", command=self.root.quit, bg="#FAF1F0", fg="black", font=("Arial", 11), borderwidth=3, width=6, height=1)
        self.btn_salir.place(x=55, y=170, anchor="center")

        self.btn_volver = tk.Button(self.root, text="cancelar", command=self.volver_inicio, bg="#FAF1F0", fg="black", font=("Arial", 11), borderwidth=3, width=21, height=1)
        self.btn_volver.place(x=122, y=215, anchor="center")
    
    #fin de los campos visibles
    
        #logica iniciar sesion
    def iniciar_sesion(self):
        usuario = self.entry_usuario.get()
        contraseña = self.entry_contraseña.get()

        if self.validar_usuario(usuario, contraseña):
            self.controlador.mostrar_admin()
            
        else: 
            messagebox.showerror(
                "Error de autenticación",
                "Usuario o contraseña incorrectos."
            )

    #esta funcion va a cambiar y sera conectada con una base de datos
    def validar_usuario(self, usuario, contraseña):
        ruta_carpeta = os.path.dirname(__file__)
        ruta_usuarios = os.path.join(ruta_carpeta, "json", "usuarios.json")
        try:
            with open(ruta_usuarios, "r", encoding="utf-8") as f:
                datos = json.load(f)
                for user in datos["usuarios"]:
                    if user["usuario"] == usuario and user["password"] == contraseña:
                        return True
        except Exception as e:
            print("Error al leer usuarios:", e)
        return False
    
    def volver_inicio(self):
        self.controlador.mostrar_pantalla_inicio()