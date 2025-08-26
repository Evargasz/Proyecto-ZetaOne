#librerias
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import getpass

#Base de datos
import json

#ventanas modales
from .Autorizar_tabla import AutorizarTablaVentana
from .usuario_no_vigente import UsuarioNoVigenteVentana
from .Desbloquear_usuario import desbloquearUsuVentana
from .Migracion import MigracionVentana

#estilos
from styles import etiqueta_titulo, entrada_estandar, boton_rojo, img_boton, boton_comun, boton_accion
import ttkbootstrap as tb
from ttkbootstrap.constants import *

FAVORITOS_FILE = 'Favoritos.json'

#--------------------Precargar favoritos guardados-------------------
def cargar_favoritos():
    if os.path.exists(FAVORITOS_FILE):
        try:
            with open(FAVORITOS_FILE, 'r', encoding='utf-8') as fav:
                return json.load(fav)
        except Exception as err:
            print(f"Error al leer favoritos: {err}")
            return[]
    return []

def guardar_favoritos(favoritos):
    try:
        with open(FAVORITOS_FILE, 'w', encoding='utf-8') as fav:
            json.dump(favoritos, fav, ensure_ascii=False, indent=4)
    except Exception as err:
        print(f"Error al guardar favoritos: {err}")

class usuBasicoMain(tb.Frame):
    def __init__(self, master, controlador):
        super().__init__(master)
        self.root = master
        self.master = master
        self.controlador = controlador

        # Configuración de ventana
        self.root.title("ZetaOne || Usuraio Basico")
        ventana_ancho = 790
        ventana_alto = 600
        pantalla_ancho = self.root.winfo_screenwidth()
        pantalla_alto = self.root.winfo_screenheight()
        x = int((pantalla_ancho / 2) - (ventana_ancho / 2))
        y = int((pantalla_alto / 2) - (ventana_alto / 2))
        self.root.geometry(f"{ventana_ancho}x{ventana_alto}+{x}+{y}")
        self.root.resizable(False, False)

        #icono
        self.root.iconbitmap("imagenes_iconos/Zeta99.ico")

        # funcionalidades Y contenido de las cards
        self.funcionalidades = [
            {
                "titulo": "Desbloquear usuario",
                "desc": "Borrar usuario de un ambiente...",
                "Favoritos": False,
                "accion": self.usar_desbloquear_usuario
            },
            {
                "titulo": "Autorizar tablas",
                "desc": "Autoriza ciertas tablas en BD.",
                "Favoritos": False,
                "accion": self.usar_autorizar_tablas
            },
            {
                "titulo": "Actualizar fecha de contabilidad",
                "desc": "Descripción...",
                "Favoritos": False,
                "accion": self.usar_actualizar_fecha_cont
            },
            {
                "titulo": "Usuario no Vigente",
                "desc": "nose aun",
                "Favoritos": False,
                "accion": self.usar_usu_no_vigente
            },
            {
                "titulo": "Migracion de datos",
                "desc": "Migrar datos",
                "Favoritos": False,
                "accion": self.usar_migracion_de_datos
            }
        ]

        self.favoritos = cargar_favoritos()
        for func in self.funcionalidades:
            func["Favoritos"] = func["titulo"] in self.favoritos
    
        #variables de la barra de busqueda
        self.texto_busqueda = ""
        self.placeholder_text = "¿Qué deseas hacer?"
    
       

        # Variables de control del filtro
        self.filtro_favoritos = False
        self.color_boton_activo = "#20ABFC"
        self.color_boton_default = "#F2F2F2"

        # 1. SIDEBAR IZQUIERDA
        self.sidebar = tb.Frame(self.root, bootstyle="light", width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self.armar_sidebar()

        # 2. ÁREA PRINCIPAL DERECHA
        self.main_frame = tk.Frame(self.root, bg="#F7F7F7")
        self.main_frame.pack(side="right", fill="both", expand=True)
        self.armar_area_principal()

    #-------------------------------------------frame de la izquierda------------------------------------------
    def armar_sidebar(self):
        usuario_img = Image.open("imagenes_iconos/userico.png")
        usuario_img = usuario_img.resize((120, 120))
        self.usuario_icon = ImageTk.PhotoImage(usuario_img)
        tb.Label(self.sidebar, image=self.usuario_icon, bootstyle="light").pack(pady=(30, 10))

        nombre_usuario = getpass.getuser()
        bienvenida_lbl = etiqueta_titulo(self.sidebar, f"BIENVENIDO\n  {nombre_usuario}", font=("Arial", 12))
        bienvenida_lbl.pack(pady=(0, 300))

        btn_volver = boton_accion(self.sidebar, "volver", comando=self.volver,
                                width=15)
        btn_volver.pack(side="top", pady=(0, 0))

        btn_salir = boton_rojo(self.sidebar, "salir", comando=self.salir, width=15)
        btn_salir.pack(side="bottom", pady=(0, 30))
        
    #------------------------------------------frame de la derecha---------------------------------------------
    def armar_area_principal(self): #frame derecha
        barra_superior = tb.Frame(self.main_frame)
        barra_superior.pack(fill="x", padx=40, pady=20)

            #Buscador
        self.entry_busqueda = entrada_estandar(barra_superior, font=("Arial", 14))
        self.entry_busqueda.insert(0, self.placeholder_text)
        self.entry_busqueda.pack(side="left", fill="x", expand=True, padx=(0, 0), ipady=4)

        def clear_placeholder_busqueda(event):
            if self.entry_busqueda.get() == self.placeholder_text:
                self.entry_busqueda.delete(0, tk.END)
                self.entry_busqueda.config(foreground='black', show="")

        def add_placeholder_busqueda(event):
            if self.entry_busqueda.get() == "":
                self.entry_busqueda.insert(0, self.placeholder_text)
                self.entry_busqueda.config(foreground='black', show="")

        self.entry_busqueda.bind("<FocusIn>", clear_placeholder_busqueda)
        self.entry_busqueda.bind("<FocusOut>", add_placeholder_busqueda)
        self.entry_busqueda.bind("<Return>", lambda event: self.accion_busqueda())

        lupa_img = Image.open("imagenes_iconos/lupa.png")
        lupa_img = lupa_img.resize((28, 30))
        self.lupa_icon = ImageTk.PhotoImage(lupa_img)

        btn_lupa = img_boton(barra_superior, image=self.lupa_icon,
                             comando=self.accion_busqueda)
        btn_lupa.pack(side="left")

        #-----------------------filtrado de contenido---------------------------------

        filtros_frame = tb.Frame(self.main_frame)
        filtros_frame.pack(anchor="w", padx=56, pady=(5, 10))

        self.filtro_todos = boton_comun(filtros_frame, "Todos", comando=self.mostrar_todos)
        self.filtro_todos.pack(side="left", padx=(0, 10))

        self.boton_filtro_favoritos = tb.Button(
            filtros_frame, text="Favoritos",
            command=self.toggle_filtro_favoritos, bootstyle="primary-outline",
            width=12
        )
        self.boton_filtro_favoritos.pack(side="left", padx=5)
        
        self.boton_recargar = boton_comun(
            filtros_frame, "Recargar",
            comando=self.recargar_cards,
            width=12
        )
        self.boton_recargar.pack(side="left", padx=5)

        self.cards_frame = tb.Frame(self.main_frame)
        self.cards_frame.pack(fill="both", expand=True, padx=40, pady=(0, 20))

        self.mostrar_funcionalidades()

        #------------------------------------------cards---------------------------------------------------------- 
    def mostrar_funcionalidades(self, filtro_favoritos=False):
                
        for widget in self.cards_frame.winfo_children():
            widget.destroy()

        if filtro_favoritos:
            funcionalidades_a_mostrar = [f for f in self.funcionalidades if f.get("Favoritos")]
            if not funcionalidades_a_mostrar:
                mensaje = etiqueta_titulo(
                    self.cards_frame,
                    texto="no tienes ningun favorito activo.\nMarca alguno y aparecera aqui",
                    font=("Arial", 12, "italic"),
                    justify="center"
                )
                mensaje.pack(expand=True, pady=50)
                return
        else:
            funcionalidades_a_mostrar = self.funcionalidades

        texto = getattr(self, "texto_busqueda", "")
        if texto:
            funcionalidades_a_mostrar = [
                f for f in funcionalidades_a_mostrar
                if texto in f["titulo"].lower() or texto in f["desc"].lower()
            ]

        if not funcionalidades_a_mostrar:
            mensaje = etiqueta_titulo(
                self.cards_frame,
                texto="No se encontraron funcionalidades con relacion a la busqueda",
                font=("Arial", 12, "italic"),
                justify="center"
            )
            mensaje.pack(expand=True, pady=50)
            return

        columnas = 2
        fila = 0
        columna = 0
        for func in funcionalidades_a_mostrar:
            card_frame = tk.Frame(self.cards_frame, bd=1, relief="solid", bg="#f9f9f9")
            card_frame.grid(row=fila, column=columna, padx=10, pady=10, sticky="nsew")
            etiqueta_titulo(card_frame, texto=func["titulo"], font=("Arial", 11, "bold")).pack(pady=(6, 3))
            etiqueta_titulo(card_frame, texto=func["desc"], font=("Arial", 9)).pack(pady=(0, 7), padx=11)
            es_fav = func.get("Favoritos", False)
            btn_acceso = tb.Button(
                card_frame,
                text="Añadir a favoritos" if not func.get("Favoritos") else "Quitar de favoritos",
                bootstyle="primary-outline" if not func.get("Favoritos") else "primary",
                command=lambda f=func: self.toggle_Favoritos(f))
            btn_acceso.pack(side="left", padx=(14, 8), pady=6)
            
            btn_usar = boton_accion(
                card_frame,
                "Usar",
                comando=func["accion"]
                )
            btn_usar.pack(side="right", padx=10, pady=6)

            columna += 1
            if columna >= columnas:
                columna = 0
                fila += 1

        #---------------------------------Funciones de botones------------------------------------
    #Navegacion
    def salir(self):
        self.root.destroy()

    def volver(self):
        self.controlador.mostrar_pantalla_inicio()
    
    #Botondes de Barra de busqueda
    def accion_busqueda(self):
        txt = self.entry_busqueda.get()
        if txt == self.placeholder_text or txt.strip() == "":
            self.texto_busqueda = ""
        else:
            self.texto_busqueda = txt.strip().lower()
        self.mostrar_funcionalidades(filtro_favoritos=self.filtro_favoritos)

    def toggle_filtro_favoritos(self):
        self.filtro_favoritos = not self.filtro_favoritos

        if self.filtro_favoritos:
            self.boton_filtro_favoritos.config()
            self.mostrar_funcionalidades(filtro_favoritos=True)
            print("favoritos funciona")
        else:
            self.boton_filtro_favoritos.config()
            self.mostrar_funcionalidades(filtro_favoritos=False)
            print("deseleccion de favoritos funciona")

    def toggle_Favoritos(self, funcionalidad):
        funcionalidad["Favoritos"] = not funcionalidad.get("Favoritos", False)
        self.favoritos = [f["titulo"] for f in self.funcionalidades if f.get("Favoritos", False)]
        guardar_favoritos(self.favoritos)
        self.mostrar_funcionalidades(self.filtro_favoritos)
            
    def mostrar_todos(self):
        self.filtro_favoritos = False
        self.boton_filtro_favoritos.config()
        self.mostrar_funcionalidades(filtro_favoritos=False)
        print("este boton funciona correctamente")

    def recargar_cards(self):
        self.entry_busqueda.delete(0, tk.END)
        self.entry_busqueda.insert(0, self.placeholder_text)
        self.entry_busqueda.config(foreground='black')
        self.texto_busqueda = ""
        self.filtro_favoritos = False
        self.boton_filtro_favoritos.config()
        self.mostrar_funcionalidades(filtro_favoritos=False)
        self.entry_busqueda.focus_set()
        self.entry_busqueda.icursor(0)
        self.root.focus()
        print("este boton funciona correctamente")

    #-------------------------------------------Ventanas Modales (contenido de las cards)---------------------------------------------
    def usar_desbloquear_usuario(self):
        try:
            with open('json/ambientes.json', 'r', encoding='utf-8') as f:
                ambientes_lista = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar ambientes.json\n{e}")
            return

        def callback_confirmar(usuario, ambiente_obj):
            # Aquí tu código cuando confirmen en la modal
            print("Usuario a desbloquear:", usuario, "Ambiente:", ambiente_obj)

        ventana_desbloquear_usu = desbloquearUsuVentana(self.root, ambientes_lista, callback_confirmar)
        ventana_desbloquear_usu.grab_set()
        ventana_desbloquear_usu.wait_window()

    def usar_autorizar_tablas(self):
        ventana_autorizar = AutorizarTablaVentana(master=self.root)
        ventana_autorizar.grab_set()
        ventana_autorizar.wait_window

    def usar_actualizar_fecha_cont(self):
        messagebox.showinfo("funcion no implementada", "esta funcion estara disponible en breve")
    
    def usar_usu_no_vigente (self):
        ventana_usu_no_vig = UsuarioNoVigenteVentana(master=self.root)
        ventana_usu_no_vig.grab_set()
        ventana_usu_no_vig.wait_window

    def usar_migracion_de_datos(self):
        ventana_mig_datos = MigracionVentana(master= self.root)
        ventana_mig_datos.grab_set()
        ventana_mig_datos.wait_window