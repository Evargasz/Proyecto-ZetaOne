#Libreria
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, messagebox
from util_rutas import recurso_path

#importar estilos
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from styles import boton_creden, etiqueta_titulo, entrada_estandar

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
        
    #icono
        ruta = recurso_path("imagenes_iconos","Zeta99.ico")
        self.root.iconbitmap(ruta)

    #Imagen de fondo
        
        ruta_carpeta = os.path.dirname(__file__)
        ruta_imagen = os.path.join(ruta_carpeta, "imagenes_iconos", "ZetaOne_bg_op2.jpg")
        self.bg_image = Image.open(ruta_imagen)
        self.bg_image = self.bg_image.resize((250, 250))  # tamaño fijo
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        self.background_label = tk.Label(self.root, image=self.bg_photo)
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)

    
    #estos son los campos visibles de la ventana

        #titulo
        self.lbl_titulo = etiqueta_titulo(self.root, "CREDENCIALES", font=("Arial", 14, "bold"))
        self.lbl_titulo.place(relx=0.5, y=30, anchor="center")
        
        #Usuario
        self.entry_usuario = entrada_estandar(self.root)
        self.entry_usuario.place(relx=0.5, y=70, anchor="center", width=200, height=35)
        self.entry_usuario.insert(0, "Usuario")
        
        # --- CAMBIO: Posicionar el cursor en el campo de usuario al abrir ---
        self.entry_usuario.focus_set()

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
        self.entry_usuario.bind("<Return>", lambda event: self.iniciar_sesion())

        #contraseña
        self.entry_contraseña = entrada_estandar(self.root, show="", foreground='black')
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
        
        self.btn_iniciar = boton_creden(self.root, "Iniciar sesión", comando=self.iniciar_sesion, width=15)
        self.btn_iniciar.place(relx=0.68, y=167, anchor="center")

        self.btn_salir = boton_creden(self.root, "salir", comando=self.root.quit, width=9)
        self.btn_salir.place(x=61, y=167, anchor="center")

        self.btn_volver = boton_creden(self.root, "cancelar", comando=self.volver_inicio, width=30)
        self.btn_volver.place(x=124, y=212, anchor="center")

    
    #fin de los campos visibles
    
        #logica iniciar sesion
    def iniciar_sesion(self):
        usuario = self.entry_usuario.get()
        contraseña = self.entry_contraseña.get()

        if usuario in ["", "Usuario"] or contraseña in ["", "contraseña"]:
            messagebox.showwarning("campos incompletos","Por favor, complete todos los campos para poder acceder.")
            return
        
        if self.validar_usuario(usuario, contraseña):
            self.controlador.mostrar_admin()
            
        else: 
            messagebox.showerror(
                "Error de autenticación",
                "Usuario o contraseña incorrectos."
            )

    #esta funcion va a cambiar y sera conectada con una base de datos
    def validar_usuario(self, usuario, contraseña):
        import os
        from cryptography.fernet import Fernet
        ruta_carpeta = os.path.dirname(__file__)
        ruta_usuarios = os.path.join(ruta_carpeta, "json", "usuarios.json")
        ruta_clave = os.path.join(ruta_carpeta, "json", "clave.key")
        try:
            with open(ruta_clave, "rb") as key_file:
                clave = key_file.read()
            fernet = Fernet(clave)
            with open(ruta_usuarios, "r", encoding="utf-8") as f:
                datos = json.load(f)
                for user in datos["usuarios"]:
                    if user["usuario"] == usuario:
                        # Desencriptar el password guardado
                        try:
                            password_guardado = fernet.decrypt(user["password"].encode()).decode()
                        except Exception:
                            continue  # Si falla la desencriptación, pasa al siguiente usuario
                        if password_guardado == contraseña:
                            return True
        except Exception as e:
            print("Error al leer usuarios o la clave:", e)
        return False
    
    def volver_inicio(self):
        self.controlador.mostrar_pantalla_inicio()