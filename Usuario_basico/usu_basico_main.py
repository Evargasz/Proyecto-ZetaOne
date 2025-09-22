#librerias
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import getpass


#Base de datos
import json

#ventanas modales (importes absolutos de Usuario_basico)
from Usuario_basico.Autorizar_tabla import AutorizarTablaVentana
from Usuario_basico.usuario_no_vigente import UsuarioNoVigenteVentana
from Usuario_basico.Desbloquear_usuario import desbloquearUsuVentana
from Usuario_basico.Migracion import MigracionVentana
from Usuario_basico.Modificaciones_varias import ModificacionesVariasVentana
from Usuario_basico.Actualizafechaconta import ActualizaFechaContabilidadVentana
from util_rutas import recurso_path

#estilos (styles.py está en la raíz)
from styles import etiqueta_titulo, entrada_estandar, boton_rojo, img_boton, boton_comun, boton_accion
import ttkbootstrap as tb
from ttkbootstrap.constants import *

FAVORITOS_FILE = 'Favoritos.json'

#--------------------Precargar favoritos guardados-------------------

# --- SECCIÓN CORREGIDA: Rutas de archivos JSON ---
# Se define la ruta de forma segura y reutilizable
RUTA_FAVORITOS = recurso_path("json", "Favoritos.json")

def cargar_favoritos():
    """Carga los favoritos desde un archivo JSON usando la ruta correcta."""
    if not os.path.exists(RUTA_FAVORITOS):
        return []
    try:
        with open(RUTA_FAVORITOS, 'r', encoding='utf-8') as fav:
            return json.load(fav)
    except Exception as err:
        print(f"Error al leer favoritos: {err}")
        return []

def guardar_favoritos(favoritos):
    """Guarda los favoritos en un archivo JSON usando la ruta correcta."""
    try:
        with open(RUTA_FAVORITOS, 'w', encoding='utf-8') as fav:
            json.dump(favoritos, fav, indent=4)
    except Exception as err:
        print(f"Error al guardar favoritos: {err}")

class usuBasicoMain(tb.Frame):
    def __init__(self, master, controlador):
        super().__init__(master)
        self.root = master
        self.master = master
        self.controlador = controlador

        # Configuración de ventana
        self.root.title("ZetaOne || Usuario Basico")
        ventana_ancho = 820
        ventana_alto = 600
        pantalla_ancho = self.root.winfo_screenwidth()
        pantalla_alto = self.root.winfo_screenheight()
        x = int((pantalla_ancho / 2) - (ventana_ancho / 2))
        y = int((pantalla_alto / 2) - (ventana_alto / 2))
        self.root.geometry(f"{ventana_ancho}x{ventana_alto}+{x}+{y}")
        self.root.resizable(False, False)

        #icono
        ruta_icono = recurso_path("imagenes_iconos", "Zeta99.ico")
        self.root.iconbitmap(ruta_icono)

        # funcionalidades Y contenido de las cards
        self.funcionalidades = [
            {
                "titulo": "Borrar sesion de usuario",
                "desc": "Libera sesion usuario registrado anteriormente",
                "Favoritos": False,
                "accion": self.usar_desbloquear_usuario
            },
            {
                "titulo": "Autorizar tablas",
                "desc": "Autoriza tabla a usuario consulta.",
                "Favoritos": False,
                "accion": self.usar_autorizar_tablas
            },
            {
                "titulo": "Actualizar fecha de contabilidad",
                "desc": "Actualiza estado de corte contable",
                "Favoritos": False,
                "accion": self.usar_actualizar_fecha_cont
            },
            {
                "titulo": "Usuario no Vigente",
                "desc": "Cambia estado de usuario a V",
                "Favoritos": False,
                "accion": self.usar_usu_no_vigente
            },
            {
                "titulo": "Migracion de datos",
                "desc": "Migrar datos",
                "Favoritos": False,
                "accion": self.usar_migracion_de_datos
            },
            {
                "titulo": "Modificaciones varias",
                "desc": "Modificar datos básicos",
                "Favoritos": False,
                "accion": self.usar_modificaciones_varias
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
        try:
            # Carga la imagen del usuario y la muestra en la barra lateral
            ruta_user_ico = recurso_path("imagenes_iconos", "userico.png")
            usuario_img = Image.open(ruta_user_ico)
            usuario_img = usuario_img.resize((120, 120))
            self.usuario_icon = ImageTk.PhotoImage(usuario_img)
            tb.Label(self.sidebar, image=self.usuario_icon, bootstyle="light").pack(pady=(30, 10))
        except Exception as e:
            print(f"ADVERTENCIA: No se pudo cargar la imagen de usuario 'userico.png': {e}")
            # Si la imagen falla, se crea una etiqueta de texto como alternativa
            tb.Label(self.sidebar, text="(Imagen no disponible)", bootstyle="secondary").pack(pady=(30, 10))

        # Muestra el mensaje de bienvenida
        nombre_usuario = getpass.getuser()
        bienvenida_lbl = etiqueta_titulo(self.sidebar, f"BIENVENIDO\n  {nombre_usuario}", font=("Arial", 12))
        bienvenida_lbl.pack(pady=(0, 300))

        # Botón para volver
        self.btn_volver = boton_accion(self.sidebar, "volver", comando=self.volver,
                                    width=15)
        self.btn_volver.pack(side="top", pady=(0, 0))

        # Botón para salir
        self.btn_salir = boton_rojo(self.sidebar, "salir", comando=self.salir, width=15)
        self.btn_salir.pack(side="bottom", pady=(0, 30))
    #------------------------------------------frame de la derecha---------------------------------------------
    def armar_area_principal(self): #frame derecha
        barra_superior = tb.Frame(self.main_frame)
        barra_superior.pack(fill="x", padx=40, pady=20)

        # --- Buscador ---
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

        # --- Bloque de Carga de Imagen de Lupa (CORREGIDO) ---
        try:
            # 1. Obtenemos la ruta correcta de la imagen
            ruta_lupa = recurso_path("imagenes_iconos", "lupa.png")
            
            # 2. Abrimos, redimensionamos y preparamos la imagen
            lupa_img = Image.open(ruta_lupa)
            lupa_img = lupa_img.resize((28, 30))
            self.lupa_icon = ImageTk.PhotoImage(lupa_img)

            # 3. Creamos el botón con la imagen
            btn_lupa = img_boton(barra_superior, image=self.lupa_icon,
                                comando=self.accion_busqueda)
        except Exception as e:
            # Si la imagen falla, se crea un botón de texto como alternativa
            print(f"ADVERTENCIA: No se pudo cargar la imagen 'lupa.png': {e}")
            btn_lupa = boton_comun(barra_superior, "Buscar",
                                    comando=self.accion_busqueda)

        btn_lupa.pack(side="left")

        # --- Filtrado de contenido ---
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
        else:
            self.boton_filtro_favoritos.config()
            self.mostrar_funcionalidades(filtro_favoritos=False)

    def toggle_Favoritos(self, funcionalidad):
        funcionalidad["Favoritos"] = not funcionalidad.get("Favoritos", False)
        self.favoritos = [f["titulo"] for f in self.funcionalidades if f.get("Favoritos", False)]
        guardar_favoritos(self.favoritos)
        self.mostrar_funcionalidades(self.filtro_favoritos)
            
    def mostrar_todos(self):
        self.filtro_favoritos = False
        self.boton_filtro_favoritos.config()
        self.mostrar_funcionalidades(filtro_favoritos=False)

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

    #-------------------------------------------Ventanas Modales (contenido de las cards)---------------------------------------------
    def usar_desbloquear_usuario(self):
        # Estandarizamos la apertura de la ventana
        self.habilitar_sidebar(False)
        
        # Se llama a la ventana de la forma nueva y simplificada
        ventana_desbloqueo = desbloquearUsuVentana(master=self.root)
        
        # Se hace la ventana modal y se espera a que se cierre
        ventana_desbloqueo.grab_set()
        self.root.wait_window(ventana_desbloqueo)
        
        # Se rehabilita la ventana principal al terminar
        self.habilitar_sidebar(True)
        
    def usar_autorizar_tablas(self):
        ventana_autorizar = AutorizarTablaVentana(master=self.root)
        ventana_autorizar.grab_set()
        ventana_autorizar.wait_window()

    def usar_actualizar_fecha_cont(self):
        ventana_actualiza = ActualizaFechaContabilidadVentana(master=self.root)
        ventana_actualiza.grab_set()
        ventana_actualiza.wait_window()
    
    def usar_usu_no_vigente(self):
        self.habilitar_sidebar(False)
        
        # Creamos la ventana y la guardamos en una variable
        ventana_no_vigente = UsuarioNoVigenteVentana(master=self.root)
        
        # Hacemos que la nueva ventana sea modal (bloquea la anterior)
        ventana_no_vigente.grab_set()
        
        # Esperamos a que la nueva ventana se cierre
        self.root.wait_window(ventana_no_vigente)
        
        # Cuando se cierra, rehabilitamos la ventana principal
        self.habilitar_sidebar(True)

    def usar_migracion_de_datos(self):
        self.habilitar_sidebar(False)
        ventana_mig_datos = MigracionVentana(master= self.root)
        ventana_mig_datos.grab_set()
        ventana_mig_datos.wait_window()
        self.habilitar_sidebar(True)

    def usar_modificaciones_varias(self):
        try:
            # --- CORRECCIÓN: Cargar ambientes desde la función centralizada que lee el .dat ---
            from Usuario_administrador.handlers.ambientes import cargar_ambientes
            ambientes_lista = cargar_ambientes()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar 'ambientes.json'.\nLa ventana no puede abrirse.\n\nDetalle: {e}")
            return

        # Estandarizamos la apertura de la ventana
        self.habilitar_sidebar(False)
        ventana_modificaciones = ModificacionesVariasVentana(self.root, ambientes_lista)
        ventana_modificaciones.grab_set()
        self.root.wait_window(ventana_modificaciones)
        self.habilitar_sidebar(True)

    def habilitar_sidebar(self, habilitar=True):
        estado = "normal" if habilitar else "disabled"
        self.btn_volver.config(state=estado)
        self.btn_salir.config(state=estado)

    #cuando la migracion este activa, los botones de la pagina principal deben bloquearse para evitar errores