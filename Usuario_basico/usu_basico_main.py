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
        # La geometría y el estado resizable ahora son manejados por ZLauncher.py
        self.root.minsize(900, 650)  # Tamaño mínimo ajustado para 2 columnas completas

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
            },
            {
                "titulo": "Asistente de captura y grabación",
                "desc": "Captura pantallas y graba videos de aplicaciones",
                "Favoritos": False,
                "accion": self.usar_asistente_captura
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

        # 1. SIDEBAR IZQUIERDA - Responsive
        self.sidebar = tb.Frame(self.root, bootstyle="light", width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        # Configurar peso para redimensionamiento
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.armar_sidebar()

        # 2. ÁREA PRINCIPAL DERECHA - Responsive
        self.main_frame = tk.Frame(self.root, bg="#F7F7F7")
        self.main_frame.pack(side="right", fill="both", expand=True)
        
        # Bind para ajustar contenido al redimensionar
        self.root.bind('<Configure>', self.on_window_resize)
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
        bienvenida_lbl.pack(pady=(0, 200))

        # Botones de navegación (Volver arriba, Salir abajo según mejores prácticas UX)
        self.btn_salir = boton_rojo(self.sidebar, "salir", comando=self.salir, width=15)
        self.btn_salir.pack(side="bottom", pady=(0, 20))
        
        self.btn_volver = boton_accion(self.sidebar, "volver", comando=self.volver, width=15)
        self.btn_volver.pack(side="bottom", pady=(0, 5))
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

        # Canvas con scrollbar para contenido dinámico
        canvas_frame = tk.Frame(self.main_frame, bg="#F7F7F7")
        canvas_frame.pack(fill="both", expand=True, padx=40, pady=(0, 20))
        
        self.canvas = tk.Canvas(canvas_frame, bg="#F7F7F7")
        self.scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#F7F7F7")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Frame para las cards dentro del scrollable
        self.cards_frame = tk.Frame(self.scrollable_frame, bg="#F7F7F7")
        self.cards_frame.pack(fill="both", expand=True)
        
        # Variable para controlar columnas dinámicas
        self.columnas_actuales = 2
        
        # Bind mousewheel al canvas
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)

        self.mostrar_funcionalidades()

    def mostrar_funcionalidades(self, filtro_favoritos=False):
        # Verificar que el widget existe antes de usarlo
        try:
            if not hasattr(self, 'cards_frame') or not self.cards_frame.winfo_exists():
                return
            
            for widget in self.cards_frame.winfo_children():
                widget.destroy()
        except tk.TclError:
            return  # Widget destruido, salir silenciosamente

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
                self.after_idle(lambda: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
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
            self.after_idle(lambda: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
            return

        # Detectar si la ventana está maximizada
        ventana_maximizada = self.root.state() == 'zoomed'
        
        if ventana_maximizada:
            # Solo si está maximizada, usar más columnas
            try:
                ancho_disponible = self.canvas.winfo_width() if hasattr(self, 'canvas') else self.main_frame.winfo_width()
                if ancho_disponible > 1200:  # Solo si hay mucho espacio
                    self.columnas_actuales = 3
                else:
                    self.columnas_actuales = 2
            except:
                self.columnas_actuales = 2
        else:
            # Ventana normal: siempre 2 columnas
            self.columnas_actuales = 2
        
        fila = 0
        columna = 0
        for func in funcionalidades_a_mostrar:
            card_frame = tk.Frame(self.cards_frame, bd=1, relief="solid", bg="#f9f9f9", width=280, height=120)
            card_frame.grid(row=fila, column=columna, padx=8, pady=8, sticky="nsew")
            card_frame.grid_propagate(False)  # Mantener tamaño fijo
            
            # Título más compacto
            etiqueta_titulo(card_frame, texto=func["titulo"], font=("Arial", 10, "bold")).pack(pady=(4, 2))
            # Descripción más compacta
            etiqueta_titulo(card_frame, texto=func["desc"], font=("Arial", 8)).pack(pady=(0, 4), padx=8)
            
            btn_acceso = tb.Button(
                card_frame,
                text="Añadir a favoritos" if not func.get("Favoritos") else "Quitar de favoritos",
                bootstyle="primary-outline" if not func.get("Favoritos") else "primary",
                command=lambda f=func: self.toggle_Favoritos(f))
            btn_acceso.pack(side="left", padx=(8, 4), pady=4)
            
            btn_usar = boton_accion(
                card_frame,
                "Usar",
                comando=func["accion"]
                )
            btn_usar.pack(side="right", padx=8, pady=4)

            columna += 1
            if columna >= self.columnas_actuales:
                columna = 0
                fila += 1
                
        # Configurar el grid para que las columnas se expandan uniformemente
        for i in range(self.columnas_actuales):
            self.cards_frame.columnconfigure(i, weight=1, minsize=280)
        
        # Configurar filas para tamaño uniforme
        for j in range(fila + 1):
            self.cards_frame.rowconfigure(j, weight=0, minsize=120)
        
        # Actualizar scroll region después de agregar cards
        self.after_idle(lambda: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

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

    def _on_mousewheel(self, event):
        """Permite scroll con rueda del mouse"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def on_window_resize(self, event):
        """Ajusta el layout cuando se redimensiona la ventana"""
        # Solo procesar eventos de la ventana principal
        if event.widget == self.root:
            # Verificar que los widgets existan antes de actualizar
            try:
                if hasattr(self, 'cards_frame') and self.cards_frame.winfo_exists():
                    self.after_idle(lambda: self.mostrar_funcionalidades(self.filtro_favoritos))
            except tk.TclError:
                pass  # Widget ya destruido, ignorar
    
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

    def usar_asistente_captura(self):
        """Abre el asistente de captura y grabación modular"""
        try:
            from Usuario_basico.asistente_captura_modular import abrir_asistente_captura_modular
            self.habilitar_sidebar(False)
            ventana_asistente = abrir_asistente_captura_modular(self.root)
            self.root.wait_window(ventana_asistente)
            self.habilitar_sidebar(True)
        except ImportError as e:
            respuesta = messagebox.askyesno(
                "Dependencias Faltantes", 
                "Esta funcionalidad requiere librerías adicionales.\n\n"
                "¿Deseas instalarlas automáticamente?\n\n"
                "(Alternativa: ejecuta instalar_dependencias_captura.bat)"
            )
            if respuesta:
                self.instalar_dependencias_captura()
        except Exception as e:
            messagebox.showerror(
                "Error", 
                f"Error inesperado al abrir el asistente.\n\nDetalle: {e}"
            )

    def instalar_dependencias_captura(self):
        """Instala las dependencias necesarias para el asistente de captura"""
        try:
            import subprocess
            import sys
            from tkinter import scrolledtext
            
            # Mostrar ventana de progreso
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Instalando Dependencias")
            progress_window.geometry("400x200")
            progress_window.resizable(False, False)
            
            # Centrar ventana
            x = (progress_window.winfo_screenwidth() // 2) - 200
            y = (progress_window.winfo_screenheight() // 2) - 100
            progress_window.geometry(f"400x200+{x}+{y}")
            
            etiqueta_titulo(progress_window, "Instalando dependencias...", font=("Arial", 12, "bold")).pack(pady=20)
            
            progress_text = scrolledtext.ScrolledText(progress_window, height=8, width=50)
            progress_text.pack(padx=20, pady=10, fill="both", expand=True)
            
            progress_window.update()
            
            # Lista de paquetes
            paquetes = [
                "pyautogui", "keyboard", "python-docx", "pywinauto", "pillow",
                "opencv-python", "mss", "pygetwindow", "pywin32", "paramiko"
            ]
            
            for paquete in paquetes:
                progress_text.insert(tk.END, f"Instalando {paquete}...\n")
                progress_text.see(tk.END)
                progress_window.update()
                
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", paquete], 
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    progress_text.insert(tk.END, f"✓ {paquete} instalado\n")
                except:
                    progress_text.insert(tk.END, f"✗ Error instalando {paquete}\n")
                
                progress_text.see(tk.END)
                progress_window.update()
            
            progress_text.insert(tk.END, "\n¡Instalación completada!\nReinicia ZetaOne para usar la funcionalidad.")
            progress_text.see(tk.END)
            
            boton_exito(progress_window, "Cerrar", comando=progress_window.destroy).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error instalando dependencias: {e}\n\nEjecuta manualmente: instalar_dependencias_captura.bat")

    def habilitar_sidebar(self, habilitar=True):
        estado = "normal" if habilitar else "disabled"
        self.btn_volver.config(state=estado)
        self.btn_salir.config(state=estado)

    #cuando la migracion este activa, los botones de la pagina principal deben bloquearse para evitar errores