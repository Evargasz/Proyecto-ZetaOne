#importaciones generales
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, simpledialog
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import os
import datetime # <-- CORRECCIÓN: Se añade import faltante
import traceback
import json
import threading # <-- SOLUCIÓN: Se añade el import que faltaba
import re
import getpass # <-- CAMBIO: Importar para obtener el usuario del PC

# Importar win32api para leer versiones de archivos
try:
    import win32api
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

# --- Import clave para que las rutas funcionen en el .exe ---
from util_rutas import recurso_path

#importaciones frame derecha (panel de archivos)
from .handlers.explorador import explorar_sd_folder
from .util_repetidos import quitar_repetidos

#Importacion de estilos
from .handlers.catalogacion import catalogar_plan_ejecucion, mostrar_resultado_catalogacion, VentanaResultadosCatalogacion
from .catalogacion_dialog import CatalogacionDialog
from .widgets.tooltip import ToolTip
from util_ventanas import ProgressWindow # <-- AÑADIDO: Importar la nueva ventana de progreso

from .validacion_dialog import ValidacionAutomatizadaDialog
try:
    from .Catalogacion_CTS import CatalogacionCTS
except ImportError:
    CatalogacionCTS = None

#importaciones frame izquierdo (panel de ambientes)
from .handlers.ambientes import cargar_ambientes, guardar_ambientes, probar_conexion_amb
from .relacionar_ambientes import gestionar_ambientes_relacionados  
# 

class usuAdminMain:
        
    #-----------------------configuracion de ventana--------------------------
    
    class iniciar_ventana:
        def __init__(self, root, controlador):
            self.root = root
            self.root.title("Homologador Sybase SD - Multiambiente Validación/Catalogación")
            # La geometría y el estado resizable ahora son manejados por ZLauncher.py.
            # Esto evita conflictos y centraliza el control de la ventana principal.

            # --- REQUERIMIENTO: Establecer un tamaño mínimo para la ventana ---
            self.root.minsize(1250, 650)

            # --- CORRECCIÓN: Carga de ícono de ventana de forma segura ---
            try:
                ruta_icono = recurso_path("imagenes_iconos", "Zeta99.ico")
                self.root.iconbitmap(ruta_icono)
            except Exception as e:
                print(f"ADVERTENCIA: No se pudo cargar el icono de la ventana: {e}")

            # Fuerza el tema clam antes de aplicar estilos personalizados
            main_frame = tb.Frame(root, padding=12, bootstyle="light")
            main_frame.pack(fill="both", expand=True)

            main_frame.columnconfigure(0, weight=0, minsize=400)
            main_frame.columnconfigure(1, weight=7)
            main_frame.rowconfigure(0, weight=1)
            main_frame.rowconfigure(1, weight=0)

            # Panel de Ambientes (izquierda)
            self.amb_panel = usuAdminMain.AmbientesPanel(main_frame)
            self.amb_panel.frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 8))

            # Panel de Archivos (derecha)
            self.arch_panel = usuAdminMain.ArchivosPanel(main_frame, controlador, self.amb_panel, toggle_log_callback=self.toggle_log, app_root=root)
            self.arch_panel.frame.grid(row=0, column=1, sticky="nsew", padx=(0, 0), pady=(0, 8))

            # Zona de log
            self.logtxt = scrolledtext.ScrolledText(
                main_frame, height=7, font=("Segoe UI", 9), background="#f9fafb",
                foreground="#1e293b", relief="flat", wrap="word"
            )
            self.logtxt.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
            self.logtxt.grid_remove()   # Oculta el log al inicio
            self.log_visible = False    # Marca el estado como oculto

            # Referencia cruzada para accionar desde paneles
            self.amb_panel.logtxt = self.logtxt
            self.arch_panel.logtxt = self.logtxt

        def toggle_log(self):
            if self.log_visible:
                self.logtxt.grid_remove()
                self.log_visible = False
            else:
                self.logtxt.grid()
                self.log_visible = True

    #-------------------------panel de archivos-------------------------------

    class ArchivosPanel:
        def __init__(self, parent, controlador, ambientes_panel, toggle_log_callback=None, app_root=None ):
            self.frame = tb.Frame(parent, bootstyle="light", padding=(3, 3))
            self.ambientes_panel = ambientes_panel
            self.toggle_log_callback = toggle_log_callback
            self.logtxt = None  # Se asigna desde el main
            self.controlador = controlador
            self.app_root = app_root

            # Barra superior
            barra_sd = tb.Frame(self.frame, bootstyle="secondary", padding=(8, 6))
            barra_sd.grid(row=0, column=0, sticky="ew", pady=(0, 8))
            barra_sd.columnconfigure(0, weight=1, minsize=110)
            barra_sd.columnconfigure(1, weight=1, minsize=170)
            barra_sd.columnconfigure(2, weight=1, minsize=150)
            barra_sd.columnconfigure(3, weight=1, minsize=170)
            barra_sd.columnconfigure(4, weight=1, minsize=100)  # Frontend

            #botones de seleccion
            self.single_sd_btn = tb.Button(
                barra_sd, text="SD Único", command=self.single_sd, bootstyle="primary-outline", width=10
            )
            self.multi_sd_btn = tb.Button(
                barra_sd, text="Carpeta varios SD", command=self.multi_sd, bootstyle="primary-outline", width=17
            )
            self.single_sd_btn.grid(row=0, column=0, padx=(6, 3), sticky="ew")
            self.multi_sd_btn.grid(row=0, column=1, padx=(3, 3), sticky="ew")

            # self.sd_label = tb.Label(barra_sd, text="")
            # self.sd_label.grid(row=0, column=2, sticky="w", padx=(16, 0))

            self.btn_cata_cts = tb.Button(barra_sd, text="CTS", command=self.abrir_Catalog_CTS, bootstyle="dark-outline-button", width=14)
            self.btn_cata_cts.grid(row=0, column=2, padx=(3, 3), sticky="ew")

            self.btn_repetidos = tb.Button(
                barra_sd, text="Repetidos", command=self.ver_repetidos, width=16, bootstyle="dark-outline-button"
            )
            self.btn_repetidos.grid(row=0, column=3, padx=(3, 3), sticky="ew")
            
            # Botón Frontend (inicialmente oculto)
            self.btn_frontend = tb.Button(barra_sd, text="Frontend", command=self.abrir_frontend, bootstyle="info-outline", width=10)
            # No se hace grid inicialmente, se mostrará solo cuando se detecte carpeta frontend

            #parte principal
            archivos_frame = tb.LabelFrame(
                self.frame, text="Archivos Detectados",
                padding=(16, 8, 12, 8)
            )
            archivos_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
            archivos_frame.rowconfigure(0, weight=1)
            archivos_frame.columnconfigure(0, weight=1)

            columns = ("Nombre", "Ruta", "Fecha Modif.")
            self.tree = tb.Treeview(
                archivos_frame,
                columns=columns, show="headings", selectmode="extended",
                bootstyle="primary"
            )
            self.tree.heading("Nombre", text="Nombre")
            self.tree.column("Nombre", width=200, anchor="w")
            # --- CAMBIO: Unificar el nombre de la columna para que coincida con la ventana de validación ---
            self.tree.heading("Ruta", text="Ruta")
            self.tree.column("Ruta", width=500, anchor="w")
            self.tree.heading("Fecha Modif.", text="Fecha Modificación")
            self.tree.column("Fecha Modif.", width=170, anchor="center")
            self.tree.grid(row=0, column=0, sticky="nsew")

            tree_vscroll = tb.Scrollbar(archivos_frame, orient="vertical", command=self.tree.yview, bootstyle="info-round")
            tree_vscroll.grid(row=0, column=1, sticky="ns")
            tree_hscroll = tb.Scrollbar(archivos_frame, orient="horizontal", command=self.tree.xview, bootstyle="info-round")
            tree_hscroll.grid(row=1, column=0, sticky="ew")
            self.tree.configure(yscrollcommand=tree_vscroll.set, xscrollcommand=tree_hscroll.set)
            
            ToolTip(self.tree, self.get_tooltip_for_row)

            #barra de accion
            barra_accion = tb.Frame(self.frame, bootstyle="Barra.TFrame", padding=(7, 7, 12, 7))
            barra_accion.grid(row=2, column=0, sticky="ew", pady=(14, 6))
            
            #botones
            tb.Button(barra_accion, text="Seleccionar Todos", command=self.seleccionar_todos, bootstyle="success-outline").pack(side="left", padx=8) #verder borde
            tb.Button(barra_accion, text="Deseleccionar", command=self.deseleccionar_todos, bootstyle="secondary-outline").pack(side="left", padx=7) #gris borde
            self.btn_validar_auto = tb.Button(barra_accion, text="Validar", command=self.validar_seleccionados, bootstyle="secondary-outline", state="disabled")
            self.btn_validar_auto.pack(side="left", padx=18)
            tb.Button(barra_accion, text="Log de Operaciones 📝", command=self.toggle_log, bootstyle="TButton").pack(side="left", padx=18) #azul
            tb.Button(barra_accion, text="Salir", command=self.salir, bootstyle="danger", width=10).pack(side="right", padx=18) #Rojo
            tb.Button(barra_accion, text="volver", command=self.volver_creden, bootstyle="dark", width=10).pack(side="right", padx=18) #gris
            
            # Vincular evento de selección del treeview para activar animación
            self.tree.bind("<<TreeviewSelect>>", lambda e: self._verificar_seleccion_para_animacion_validar())

            self.frame.columnconfigure(0, weight=1)
            self.frame.rowconfigure(1, weight=1)

            self.archivos_unicos = []
            self.selected_sd_folder = ""
            self.multi_sd_flag = False
            self.repetidos_log = []
            self.btn_repetidos_animacion_activa = False
            self.btn_repetidos_animacion_estado = 0  # 0 o 1 para alternar colores
            self.archivos_no_referenciados = []  # Archivos físicos no referenciados en ningún .txt
            
            # Variables para animación del botón validar
            self.animacion_validar_activa = False
            self.animacion_validar_estado = 0  # 0 o 1 para alternar colores
            self.animacion_validar_id = None  # ID del after() para poder cancelarlo
            
            # Variables para funcionalidad Frontend
            self.carpetas_frontend = []  # Lista de carpetas frontend encontradas
            self.archivos_frontend = []  # Lista de archivos .exe y .dll encontrados
            self.btn_frontend_visible = False  # Estado de visibilidad del botón
            self.animacion_frontend_activa = False
            self.animacion_frontend_estado = 0
            self.animacion_frontend_id = None

        def abrir_Catalog_CTS(self):
            if CatalogacionCTS:
                CatalogacionCTS(self.app_root)
            else:
                messagebox.showerror("Error", "Funcionalidad no disponible.\nFalta instalar: pip install paramiko")
         
        def toggle_log(self):
            if self.toggle_log_callback:
                self.toggle_log_callback()

        def logear_panel(self, msg):
            if self.logtxt:
                self.logtxt.insert(tk.END, "[Archivos] " + msg + "\n")
                self.logtxt.see(tk.END)

        def seleccionar_todos(self):
            for iid in self.tree.get_children():
                self.tree.selection_add(iid)
            self.logear_panel("Seleccionados todos los archivos en el listado.")
            self._verificar_seleccion_para_animacion_validar()

        def deseleccionar_todos(self):
            for iid in self.tree.selection():
                self.tree.selection_remove(iid)
            self.logear_panel("Deseleccionados todos los archivos.")
            self._verificar_seleccion_para_animacion_validar()

        def salir(self):
            self.logear_panel("Aplicación finalizada a solicitud del usuario.")
            self.frame.quit()
            self.frame.winfo_toplevel().quit()

        def volver_creden(self):
            self.controlador.mostrar_pantalla_inicio()
        
        def _verificar_seleccion_para_animacion_validar(self):
            """Verifica si hay archivos seleccionados y activa/desactiva la animación del botón validar."""
            items_seleccionados = len(self.tree.selection())
            
            # Solo animar si el botón está habilitado (state="normal") y hay archivos seleccionados
            estado_boton = str(self.btn_validar_auto['state'])
            
            if items_seleccionados > 0 and estado_boton == "normal":
                # Hay archivos seleccionados y el botón está habilitado - activar animación
                if not self.animacion_validar_activa:
                    self._iniciar_animacion_validar()
            else:
                # No hay archivos seleccionados o botón deshabilitado - detener animación
                if self.animacion_validar_activa:
                    self._detener_animacion_validar()
        
        def _iniciar_animacion_validar(self):
            """Inicia la animación de parpadeo del botón Validar."""
            if self.animacion_validar_activa:
                return  # Ya está activa
            
            self.animacion_validar_activa = True
            self._animar_boton_validar()
        
        def _detener_animacion_validar(self):
            """Detiene la animación del botón y lo restaura a su estado normal."""
            self.animacion_validar_activa = False
            
            # Cancelar el after() pendiente si existe
            if self.animacion_validar_id is not None:
                try:
                    self.app_root.after_cancel(self.animacion_validar_id)
                except:
                    pass
                self.animacion_validar_id = None
            
            # Restaurar el botón a su estilo normal solo si sigue existiendo
            try:
                if self.btn_validar_auto.winfo_exists():
                    estado_actual = str(self.btn_validar_auto['state'])
                    if estado_actual == "normal":
                        self.btn_validar_auto.configure(bootstyle="secondary-outline")
                    # Si está disabled, mantener el estilo que tenga
            except:
                pass
        
        def _animar_boton_validar(self):
            """Alterna el color del botón para crear efecto de parpadeo."""
            if not self.animacion_validar_activa:
                return
            
            try:
                if not self.btn_validar_auto.winfo_exists():
                    self.animacion_validar_activa = False
                    return
                
                # Alternar entre dos estilos
                if self.animacion_validar_estado == 0:
                    nuevo_estilo = "success"
                    self.animacion_validar_estado = 1
                else:
                    nuevo_estilo = "success-outline"
                    self.animacion_validar_estado = 0
                
                self.btn_validar_auto.config(bootstyle=nuevo_estilo)
                
                # Llamar nuevamente después de 500ms
                self.animacion_validar_id = self.app_root.after(500, self._animar_boton_validar)
            except Exception as e:
                self.animacion_validar_activa = False
        
        def _detectar_carpetas_frontend(self):
            """Detecta carpetas llamadas 'frontend' (case-insensitive) en las subcarpetas del SD seleccionado."""
            self.carpetas_frontend = []
            self.archivos_frontend = []
            
            if not self.selected_sd_folder or not os.path.exists(self.selected_sd_folder):
                self.logear_panel("⚠️ No hay carpeta seleccionada o no existe")
                return
            
            self.logear_panel(f"🔍 Buscando carpetas 'frontend' en: {self.selected_sd_folder}")
            carpetas_totales_revisadas = 0
            
            # Buscar recursivamente carpetas llamadas 'frontend'
            for root, dirs, files in os.walk(self.selected_sd_folder):
                carpetas_totales_revisadas += len(dirs)
                for dir_name in dirs:
                    # Log de todas las carpetas encontradas para debug
                    if 'front' in dir_name.lower():
                        self.logear_panel(f"  📁 Carpeta con 'front': {dir_name} en {root}")
                    
                    if dir_name.lower() == 'frontend':
                        frontend_path = os.path.join(root, dir_name)
                        self.carpetas_frontend.append(frontend_path)
                        self.logear_panel(f"✅ Carpeta frontend detectada: {frontend_path}")
                        
                        # Buscar archivos .exe y .dll en esta carpeta frontend
                        for fe_root, _, fe_files in os.walk(frontend_path):
                            for fe_file in fe_files:
                                if fe_file.lower().endswith(('.exe', '.dll')):
                                    file_path = os.path.join(fe_root, fe_file)
                                    rel_path = os.path.relpath(file_path, self.selected_sd_folder)
                                    version = self._obtener_version_archivo(file_path)
                                    
                                    self.archivos_frontend.append({
                                        'nombre': fe_file,
                                        'ruta': rel_path,
                                        'ruta_completa': file_path,
                                        'version': version
                                    })
            
            self.logear_panel(f"📊 Total de carpetas revisadas: {carpetas_totales_revisadas}")
            
            # Mostrar/ocultar botón Frontend según detección
            if self.carpetas_frontend:
                self.logear_panel(f"✅ Se encontraron {len(self.carpetas_frontend)} carpeta(s) frontend con {len(self.archivos_frontend)} archivo(s) .exe/.dll")
                self._mostrar_boton_frontend()
            else:
                self.logear_panel(f"❌ No se encontraron carpetas 'frontend' (revisadas {carpetas_totales_revisadas} carpetas)")
                self._ocultar_boton_frontend()
        
        def _obtener_version_archivo(self, filepath):
            """Obtiene la versión de un archivo .exe o .dll usando win32api."""
            if not WIN32_AVAILABLE:
                return "N/A (win32api no disponible)"
            
            try:
                # Obtener información de versión del archivo
                info = win32api.GetFileVersionInfo(filepath, "\\")
                
                # Verificar que info sea un diccionario
                if not isinstance(info, dict):
                    return "N/A (formato no válido)"
                
                # Extraer los números de versión
                ms = info.get('FileVersionMS', 0)
                ls = info.get('FileVersionLS', 0)
                
                # Construir versión en formato X.X.X.X
                version = f"{win32api.HIWORD(ms)}.{win32api.LOWORD(ms)}.{win32api.HIWORD(ls)}.{win32api.LOWORD(ls)}"
                return version
            except Exception as e:
                return f"N/A ({str(e)[:25]})"
        
        def _mostrar_boton_frontend(self):
            """Muestra el botón Frontend en la barra superior y activa su animación."""
            self.logear_panel(f"🔧 Intentando mostrar botón Frontend (visible actual: {self.btn_frontend_visible})")
            if not self.btn_frontend_visible:
                # Ajustar el grid para que quepa el botón Frontend
                # Columna 4 para el botón Frontend (al final de la barra)
                self.btn_frontend.grid(row=0, column=4, padx=(3, 6), sticky="ew")
                self.btn_frontend_visible = True
                self.logear_panel(f"✅ Botón Frontend mostrado en columna 4")
                self._iniciar_animacion_frontend()
            else:
                self.logear_panel(f"ℹ️ Botón Frontend ya estaba visible")
        
        def _ocultar_boton_frontend(self):
            """Oculta el botón Frontend y detiene su animación."""
            if self.btn_frontend_visible:
                self.btn_frontend.grid_remove()
                self.btn_frontend_visible = False
                self._detener_animacion_frontend()
        
        def _iniciar_animacion_frontend(self):
            """Inicia la animación del botón Frontend."""
            self.logear_panel(f"🎬 Iniciando animación del botón Frontend")
            if not self.animacion_frontend_activa:
                self.animacion_frontend_activa = True
                self._animar_boton_frontend()
            else:
                self.logear_panel(f"ℹ️ Animación ya estaba activa")
        
        def _detener_animacion_frontend(self):
            """Detiene la animación del botón Frontend."""
            if self.animacion_frontend_activa:
                self.animacion_frontend_activa = False
                if self.animacion_frontend_id:
                    self.app_root.after_cancel(self.animacion_frontend_id)
                    self.animacion_frontend_id = None
                self.btn_frontend.config(bootstyle="info-outline")
        
        def _animar_boton_frontend(self):
            """Alterna el color del botón Frontend para crear efecto titilante."""
            if not self.animacion_frontend_activa:
                return
            
            # Alternar entre dos estilos llamativos
            if self.animacion_frontend_estado == 0:
                nuevo_estilo = "info"
                self.animacion_frontend_estado = 1
            else:
                nuevo_estilo = "warning"
                self.animacion_frontend_estado = 0
            
            self.btn_frontend.config(bootstyle=nuevo_estilo)
            
            # Llamar nuevamente después de 500ms
            self.animacion_frontend_id = self.app_root.after(500, self._animar_boton_frontend)
        
        def abrir_frontend(self):
            """Abre una ventana mostrando los archivos frontend detectados."""
            if not self.archivos_frontend:
                messagebox.showinfo(
                    "Sin archivos Frontend",
                    "No se encontraron archivos .exe o .dll en las carpetas frontend.",
                    parent=self.frame
                )
                return
            
            # Crear ventana de visualización
            ventana = tb.Toplevel(self.frame)
            ventana.title(f"Archivos Frontend - {len(self.archivos_frontend)} archivo(s)")
            ventana.geometry("900x500")
            ventana.transient(self.frame)
            
            # Frame principal
            main_frame = tb.Frame(ventana, padding=10)
            main_frame.pack(fill="both", expand=True)
            
            # Label informativo
            info_label = tb.Label(
                main_frame,
                text=f"Se encontraron {len(self.carpetas_frontend)} carpeta(s) frontend con {len(self.archivos_frontend)} archivo(s)",
                font=("Segoe UI", 10, "bold")
            )
            info_label.pack(pady=(0, 10))
            
            # Frame para el Treeview
            tree_frame = tb.Frame(main_frame)
            tree_frame.pack(fill="both", expand=True)
            
            # Treeview con columnas
            columns = ("Nombre", "Ruta", "Versión")
            tree = tb.Treeview(
                tree_frame,
                columns=columns,
                show="headings",
                bootstyle="primary"
            )
            
            tree.heading("Nombre", text="Nombre")
            tree.column("Nombre", width=200, anchor="w")
            tree.heading("Ruta", text="Ruta")
            tree.column("Ruta", width=450, anchor="w")
            tree.heading("Versión", text="Versión")
            tree.column("Versión", width=150, anchor="center")
            
            tree.pack(side="left", fill="both", expand=True)
            
            # Scrollbars
            tree_vscroll = tb.Scrollbar(tree_frame, orient="vertical", command=tree.yview, bootstyle="info-round")
            tree_vscroll.pack(side="right", fill="y")
            tree.configure(yscrollcommand=tree_vscroll.set)
            
            # Llenar el Treeview con los archivos
            for idx, archivo in enumerate(self.archivos_frontend):
                tag = "alt" if idx % 2 == 1 else ""
                tree.insert(
                    "",
                    "end",
                    values=(archivo['nombre'], archivo['ruta'], archivo['version']),
                    tags=(tag,)
                )
            
            tree.tag_configure('alt', background="#f3f9fb")
            
            # Frame para botones
            button_frame = tb.Frame(main_frame)
            button_frame.pack(fill="x", pady=(10, 0))
            
            # Botón para exportar a archivo
            def exportar_lista():
                try:
                    carpeta_frontend = r"C:\ZetaOne\Frontend"
                    os.makedirs(carpeta_frontend, exist_ok=True)
                    
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    nombre_archivo = f"archivos_frontend_{timestamp}.txt"
                    ruta_archivo = os.path.join(carpeta_frontend, nombre_archivo)
                    
                    with open(ruta_archivo, 'w', encoding='utf-8') as f:
                        f.write(f"--- Archivos Frontend Detectados ---\\n")
                        f.write(f"Fecha: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
                        f.write(f"Carpeta Escaneada: {self.selected_sd_folder}\\n")
                        f.write(f"Carpetas frontend encontradas: {len(self.carpetas_frontend)}\\n")
                        f.write("-" * 80 + "\\n\\n")
                        
                        for archivo in self.archivos_frontend:
                            f.write(f"Nombre: {archivo['nombre']}\\n")
                            f.write(f"Ruta: {archivo['ruta']}\\n")
                            f.write(f"Versión: {archivo['version']}\\n")
                            f.write("-" * 80 + "\\n")
                    
                    messagebox.showinfo(
                        "Exportación exitosa",
                        f"Lista exportada a:\\n{ruta_archivo}",
                        parent=ventana
                    )
                except Exception as e:
                    messagebox.showerror(
                        "Error al exportar",
                        f"No se pudo exportar la lista:\\n{str(e)}",
                        parent=ventana
                    )
            
            btn_exportar = tb.Button(
                button_frame,
                text="📄 Exportar Lista",
                command=exportar_lista,
                bootstyle="success-outline"
            )
            btn_exportar.pack(side="left", padx=5)
            
            btn_cerrar = tb.Button(
                button_frame,
                text="Cerrar",
                command=ventana.destroy,
                bootstyle="secondary"
            )
            btn_cerrar.pack(side="right", padx=5)
            
            # Centrar ventana
            ventana.update_idletasks()
            x = (ventana.winfo_screenwidth() // 2) - (ventana.winfo_width() // 2)
            y = (ventana.winfo_screenheight() // 2) - (ventana.winfo_height() // 2)
            ventana.geometry(f"+{x}+{y}")

        def single_sd(self):
            carpeta = filedialog.askdirectory(title="Seleccionar carpeta SD única")
            if carpeta:
                self.selected_sd_folder = carpeta
                self.multi_sd_flag = False
                # self.sd_label.config(text="SD único: " + carpeta)
                self.logear_panel(f"Seleccionado SD único: {carpeta}")
                self.escanear_archivos_inner()

        def multi_sd(self):
            carpeta = filedialog.askdirectory(title="Seleccionar carpeta con varios SDs")
            if carpeta:
                self.selected_sd_folder = carpeta
                self.multi_sd_flag = True
                # self.sd_label.config(text="Carpeta con varios SDs: " + carpeta)
                self.logear_panel(f"Seleccionada carpeta multi-SD: {carpeta}")
                self.escanear_archivos_inner()

        def escanear_archivos_inner(self):
            # --- INICIO: Resetear estado del flujo ---
            self.btn_validar_auto.config(state="disabled")
            self._detener_animacion_validar()  # Detener animación al resetear
            self.ambientes_panel.set_bloqueo_ambientes_hijos(bloqueado=False)
            self.archivos_del_txt = []
            self.archivos_no_referenciados = []  # Resetear archivos no referenciados
            
            # --- CORRECCIÓN: Limpiar la grilla antes de agregar nuevos elementos ---
            self.tree.delete(*self.tree.get_children())
            # --- FIN: Resetear estado del flujo ---

            carpeta = self.selected_sd_folder
            multi = self.multi_sd_flag
            if not carpeta:
                messagebox.showwarning("Advertencia", "Seleccione una carpeta válida.", parent=self.frame)
                self.repetidos_log = []
                self.logear_panel("Intento de escaneo con carpeta inválida.")
                return

            archivos_candidatos = explorar_sd_folder(carpeta, multi_sd=multi)

            # --- CAMBIO: Excluir archivos .sqr de la lista de candidatos ---
            archivos_candidatos = [a for a in archivos_candidatos if not a.get('nombre_archivo', '').lower().endswith('.sqr')]
            self.logear_panel("Filtrando y excluyendo archivos .sqr.")

            if not archivos_candidatos:
                self.archivos_unicos = []
                self.repetidos_log = []
                self.logear_panel("No se detectaron archivos candidatos en la carpeta.")
                return

            # --- CAMBIO: Lógica de ordenamiento según el archivo .txt ---

            # 1. Obtener archivos únicos sin ordenar
            # --- CORRECCIÓN: La función quitar_repetidos devuelve una tupla (lista, lista) ---
            archivos_unicos_lista, self.repetidos_log = quitar_repetidos(archivos_candidatos)
            archivos_unicos_map = {a['nombre_archivo']: a for a in archivos_unicos_lista}

            # 2. Leer el orden del archivo .txt
            orden_del_txt = []
            txt_files = [os.path.join(r, f) for r, _, fs in os.walk(carpeta) for f in fs if f.lower().endswith('.txt')]
            
            # --- SUGERENCIA: Mapa para almacenar datos extra del TXT ---
            datos_extra_txt = {}

            if txt_files:
                for txt_file in txt_files:
                    with open(txt_file, 'r', encoding='utf-8', errors='ignore') as f:
                        next(f, None) # Omitir cabecera
                        for line in f:
                            nombre_archivo = os.path.basename(line.strip().replace('\\', '/'))
                            if nombre_archivo and not nombre_archivo.lower().endswith('.sqr'):
                                orden_del_txt.append(nombre_archivo)

                            # --- SUGERENCIA: Procesar la línea para datos extra ---
                            parts = [p.strip() for p in line.strip().split(';')]
                            if len(parts) >= 3:
                                ruta_relativa, db, sp_logico = parts[0], parts[1], parts[2]
                                nombre_archivo_extra = os.path.basename(ruta_relativa.replace('\\', '/'))
                                if nombre_archivo_extra:
                                    datos_extra_txt[nombre_archivo_extra] = {
                                        "db_override": db if db else None,
                                        "sp_name_override": sp_logico if sp_logico else None
                                    }


            # --- CAMBIO: Lógica de ordenamiento multi-nivel (SD -> orden .txt) ---
            def get_sd_number(path):
                # Extrae el número de una carpeta SD (ej: 'SD12345' -> 12345)
                match = re.search(r'SD(\d+)', path, re.IGNORECASE)
                return int(match.group(1)) if match else float('inf')

            # Crear un mapa para obtener el índice de orden del .txt rápidamente
            orden_txt_map = {nombre: i for i, nombre in enumerate(orden_del_txt)}

            # 3. Reordenar la lista de archivos únicos
            self.logear_panel("Ordenando archivos por SD y manifiesto .txt.")
            
            # Se aplica una clave de ordenamiento con múltiples criterios:
            # 1. Número de SD (ascendente).
            # 2. Posición en el archivo .txt (los no listados van al final).
            # 3. Nombre del archivo (alfabético, como desempate).
            self.archivos_unicos = sorted(
                archivos_unicos_map.values(),
                key=lambda archivo: (
                    get_sd_number(archivo['rel_path']),
                    orden_txt_map.get(archivo['nombre_archivo'], float('inf')),
                    archivo['nombre_archivo']
                )
            )
            # --- FIN DEL CAMBIO ---
            
            for idx, a in enumerate(self.archivos_unicos):
                # --- SUGERENCIA: Añadir los datos extra al diccionario del archivo ---
                if a['nombre_archivo'] in datos_extra_txt:
                    a.update(datos_extra_txt[a['nombre_archivo']])
                else:
                    a.update({"db_override": None, "sp_name_override": None})

                fecha = datetime.datetime.fromtimestamp(a['fecha_mod']).strftime('%Y-%m-%d %H:%M:%S')
                ruta_corta = a['rel_path']
                tag = "alt" if idx % 2 == 1 else ""
                self.tree.insert("", "end", iid=str(idx), values=(a['nombre_archivo'], ruta_corta, fecha), tags=(tag,))
            self.tree.tag_configure('alt', background="#f3f9fb")
            self.tree.tag_configure('no_referenciado', background="#ffcccc")  # Rojo claro para no referenciados
            self.logear_panel(f"Escaneados {len(self.archivos_unicos)} archivos únicos. Repetidos: {len(self.repetidos_log)}.")

            # --- CAMBIO: Activar animación del botón si hay repetidos ---
            if len(self.repetidos_log) > 0:
                self._activar_animacion_boton_repetidos()
            else:
                self._desactivar_animacion_boton_repetidos()
            # --- FIN DEL CAMBIO ---

            # --- CORRECCIÓN: Se restaura la validación automática contra el .txt ---
            self.logear_panel("Iniciando validación automática de archivos .txt...")
            threading.Thread(target=self._validacion_txt_thread, daemon=True).start()
            # --- FIN DE LA CORRECCIÓN ---
            
            # --- NUEVO: Detectar carpetas frontend después de cargar archivos ---
            self.logear_panel("Buscando carpetas frontend...")
            self._detectar_carpetas_frontend()
            # --- FIN NUEVO ---
            
            # --- CAMBIO: Activar animación del botón si hay repetidos ---
            if len(self.repetidos_log) > 0:
                self._activar_animacion_boton_repetidos()
            else:
                self._desactivar_animacion_boton_repetidos()
            # --- FIN DEL CAMBIO ---

        def get_tooltip_for_row(self, iid):
            try:
                if iid and int(iid)<len(self.archivos_unicos):
                    return self.archivos_unicos[int(iid)]['rel_path']
            except (ValueError, IndexError):
                return ""
            return ""
        
        def _activar_animacion_boton_repetidos(self):
            """Activa la animación (titilante) del botón de repetidos."""
            if not self.btn_repetidos_animacion_activa:
                self.btn_repetidos_animacion_activa = True
                self._animar_boton_repetidos()
        
        def _desactivar_animacion_boton_repetidos(self):
            """Desactiva la animación del botón de repetidos."""
            self.btn_repetidos_animacion_activa = False
            self.btn_repetidos.config(bootstyle="dark-outline-button")
        
        def _animar_boton_repetidos(self):
            """Alterna el estilo del botón entre warning y danger para crear efecto titilante."""
            if not self.btn_repetidos_animacion_activa:
                return
            
            # Alternar entre dos estilos llamativos usando variable de estado
            if self.btn_repetidos_animacion_estado == 0:
                nuevo_estilo = "warning"
                self.btn_repetidos_animacion_estado = 1
            else:
                nuevo_estilo = "danger"
                self.btn_repetidos_animacion_estado = 0
            
            self.btn_repetidos.config(bootstyle=nuevo_estilo)
            
            # Llamar nuevamente después de 500ms para crear efecto titilante
            self.app_root.after(500, self._animar_boton_repetidos)
        
        def _activar_animacion_boton_repetidos(self):
            """Activa la animación (titilante) del botón de repetidos."""
            if not self.btn_repetidos_animacion_activa:
                self.btn_repetidos_animacion_activa = True
                self._animar_boton_repetidos()
        
        def _desactivar_animacion_boton_repetidos(self):
            """Desactiva la animación del botón de repetidos."""
            self.btn_repetidos_animacion_activa = False
            self.btn_repetidos.config(bootstyle="dark-outline-button")

        def ver_repetidos(self):
            if not hasattr(self, "repetidos_log") or not self.repetidos_log:
                messagebox.showinfo("Sin repetidos", "No se detectaron repeticiones en el último escaneo.", parent=self.frame)
                self.logear_panel("Se consultaron repetidos pero no había repeticiones.")
                return

            win = tb.Toplevel(self.frame)
            win.title("Fuentes repetidos")
            st = scrolledtext.ScrolledText(win, width=130, height=18)
            st.pack(fill="both", expand=True)
            for entry in self.repetidos_log:
                key = entry['nombre_ext']
                escog = entry['escogido']
                st.insert(tk.END, f"Archivo: {key[0]} ({key[1]})\n")
                st.insert(tk.END, f"  Elegido:     {escog['rel_path']}  [Fecha: {datetime.datetime.fromtimestamp(escog['fecha_mod']).strftime('%Y-%m-%d %H:%M:%S')}]\n")
                for desc in entry['descartados']:
                    st.insert(tk.END, f"  Descartado:  {desc['rel_path']}  [Fecha: {datetime.datetime.fromtimestamp(desc['fecha_mod']).strftime('%Y-%m-%d %H:%M:%S')}]\n")
                st.insert(tk.END, "--------------------------------------------------------------------------------------------------------------\n")
            st.configure(state="disabled")
            self.logear_panel("Mostrada ventana de fuentes repetidos.")
        
        def _validacion_txt_thread(self):
            """
            (Worker Thread) Busca archivos .txt, los cruza con la grilla y prepara el resumen.
            """
            try:
                # 1. Encontrar todos los archivos .txt
                txt_files = []
                for root, _, files in os.walk(self.selected_sd_folder):
                    for file in files:
                        if file.lower().endswith(".txt"):
                            txt_files.append(os.path.join(root, file))

                if not txt_files:
                    # No hay .txt, el flujo no puede continuar como automático
                    self.app_root.after(0, self._finalizar_validacion_txt, "No se encontraron archivos .txt. No se puede realizar la validación automática.", True, False, None)
                    return

                # 2. Procesar cada .txt individualmente para detectar discrepancias
                # Obtener nombres de archivo de la grilla en ORDEN (archivos .sp, .sql, .tg)
                archivos_grid_ordenados = [a for a in self.archivos_unicos if a['nombre_archivo'].lower().endswith(('.sp', '.sql', '.tg'))]
                nombres_en_grid_orden = [a['nombre_archivo'] for a in archivos_grid_ordenados]
                nombres_en_grid = set(nombres_en_grid_orden)
                # Crear diccionario que mapea nombre de archivo a ruta relativa
                archivo_a_ruta = {a['nombre_archivo']: a.get('rel_path', a['nombre_archivo']) for a in archivos_grid_ordenados}
                
                # Diccionario para almacenar archivos de cada txt
                archivos_por_txt = {}
                todos_archivos_txt = []
                
                for txt_file in txt_files:
                    archivos_este_txt = []
                    with open(txt_file, 'r', encoding='utf-8', errors='ignore') as f:
                        # --- CAMBIO: Omitir la primera línea del archivo .txt ---
                        try:
                            next(f)  # Salta la primera línea que es el título.
                        except StopIteration:
                            continue # Si el archivo está vacío o solo tiene el título, pasa al siguiente.

                        for line in f:
                            cleaned_line = line.strip()
                            if not cleaned_line:
                                continue
                            
                            # --- VALIDACIÓN INTELIGENTE: Solo procesar líneas que sean rutas de archivos válidas ---
                            # Verificar que termine en extensiones válidas (.sp, .sql, .tg)
                            if not cleaned_line.lower().endswith(('.sp', '.sql', '.tg', '.sqr')):
                                # No es una ruta de archivo válida, ignorar
                                continue
                            
                            # Ignorar archivos .sqr
                            if cleaned_line.lower().endswith('.sqr'):
                                continue
                            
                            # Extraer el nombre del archivo de la ruta (puede tener \ o /)
                            nombre_archivo = os.path.basename(cleaned_line)
                            
                            # Validar que el nombre extraído sea válido (no vacío y con extensión)
                            if not nombre_archivo or '.' not in nombre_archivo:
                                continue
                            
                            # Validación adicional: verificar que contenga caracteres típicos de nombres de archivo
                            if not any(c.isalnum() for c in nombre_archivo):
                                continue

                            # Agregar solo el NOMBRE del archivo
                            archivos_este_txt.append(nombre_archivo)
                            todos_archivos_txt.append(nombre_archivo)
                    
                    archivos_por_txt[txt_file] = archivos_este_txt
                
                self.archivos_del_txt = todos_archivos_txt # Guardar para el procesamiento final

                # 3. Analizar discrepancias por cada .txt
                txt_con_discrepancias = []
                nombres_en_grid_restantes = set(nombres_en_grid)
                
                for txt_file, archivos_txt in archivos_por_txt.items():
                    archivos_txt_set = set(archivos_txt)
                    # Archivos en este txt que NO están en la carpeta
                    faltantes = list(archivos_txt_set - nombres_en_grid)
                    
                    # Validar ORDEN: comparar el orden del txt con el orden de la grilla
                    # Filtrar solo archivos que están en ambos
                    archivos_comunes_txt = [a for a in archivos_txt if a in nombres_en_grid]
                    archivos_comunes_grid = [a for a in nombres_en_grid_orden if a in archivos_txt_set]
                    
                    orden_incorrecto = []
                    if archivos_comunes_txt != archivos_comunes_grid:
                        # El orden no coincide
                        for idx, archivo in enumerate(archivos_comunes_txt):
                            if idx >= len(archivos_comunes_grid) or archivo != archivos_comunes_grid[idx]:
                                posicion_txt = idx + 1
                                if archivo in archivos_comunes_grid:
                                    posicion_grid = archivos_comunes_grid.index(archivo) + 1
                                    orden_incorrecto.append(f"{archivo} (en .txt: posición {posicion_txt}, en carpeta: posición {posicion_grid})")
                    
                    if faltantes or orden_incorrecto:
                        txt_con_discrepancias.append({
                            'ruta': txt_file,
                            'faltantes': faltantes,
                            'orden_incorrecto': orden_incorrecto
                        })
                    
                    # Quitar los archivos que sí están en este txt
                    nombres_en_grid_restantes -= archivos_txt_set

                # 4. Preparar mensaje de resumen
                # Convertir los archivos no referenciados a lista con rutas
                en_grid_no_en_txt = [{'nombre': nombre, 'ruta': archivo_a_ruta.get(nombre, nombre)} 
                                     for nombre in nombres_en_grid_restantes]
                hay_discrepancias = bool(txt_con_discrepancias or en_grid_no_en_txt)
                
                # Guardar la lista de nombres de archivos no referenciados para marcarlos en rojo
                self.archivos_no_referenciados = list(nombres_en_grid_restantes)
                
                if not hay_discrepancias:
                    resumen = "Todos los archivos detectados en la carpeta coinciden exactamente con los listados en el archivo .txt."
                else:
                    resumen_partes = ["Validación completada con discrepancias.\n"]
                    
                    # Mostrar archivos en carpeta NO referenciados en ningún .txt
                    if en_grid_no_en_txt:
                        resumen_partes.append("Archivos en carpeta NO referenciados en ningún .txt:")
                        for archivo_info in en_grid_no_en_txt:
                            resumen_partes.append(f"-  {archivo_info['nombre']}")
                            resumen_partes.append(f"   Ruta: {archivo_info['ruta']}")
                        resumen_partes.append("")
                    
                    # Mostrar discrepancias por cada .txt
                    if txt_con_discrepancias:
                        for txt_info in txt_con_discrepancias:
                            resumen_partes.append(f"Archivo .txt: {txt_info['ruta']}")
                            
                            if txt_info.get('orden_incorrecto'):
                                resumen_partes.append("Archivos en ORDEN INCORRECTO:")
                                resumen_partes.extend([f'-  {f}' for f in txt_info['orden_incorrecto']])
                            
                            if txt_info.get('faltantes'):
                                resumen_partes.append("Archivos en el .txt NO encontrados físicamente en la carpeta:")
                                resumen_partes.extend([f'-  {f}' for f in txt_info['faltantes']])
                            
                            resumen_partes.append("")
                    
                    resumen = "\n".join(resumen_partes).rstrip()
                
                # 5. Marcar visualmente los archivos no referenciados en el Treeview
                if self.archivos_no_referenciados:
                    self.app_root.after(0, self._marcar_archivos_no_referenciados)
                
                # 6. Enviar el resultado al hilo principal
                self.app_root.after(0, self._finalizar_validacion_txt, resumen, hay_discrepancias, True, txt_files)

            except Exception as e:
                error_msg = f"Ocurrió un error inesperado durante la validación de archivos .txt: {e}"
                self.app_root.after(0, self._finalizar_validacion_txt, error_msg, True, False, None)

        def _marcar_archivos_no_referenciados(self):
            """Marca visualmente en rojo los archivos no referenciados en el Treeview."""
            for iid in self.tree.get_children():
                idx = int(iid)
                if idx < len(self.archivos_unicos):
                    archivo = self.archivos_unicos[idx]
                    if archivo['nombre_archivo'] in self.archivos_no_referenciados:
                        # Obtener tags actuales y agregar 'no_referenciado'
                        tags_actuales = list(self.tree.item(iid, 'tags'))
                        if 'no_referenciado' not in tags_actuales:
                            tags_actuales.append('no_referenciado')
                            self.tree.item(iid, tags=tuple(tags_actuales))
            self.logear_panel(f"Marcados {len(self.archivos_no_referenciados)} archivos no referenciados en rojo.")
        
        def _finalizar_validacion_txt(self, resumen: str, hay_discrepancias: bool, exito: bool, txt_files=None):
            """
            (Main Thread) Muestra el resumen, bloquea ambientes y habilita el botón final.
            """
            log_resumen = resumen.replace('\n', ' | ') # Log sin saltos de línea para que sea más legible
            self.logear_panel(log_resumen)

            # --- CAMBIO: Guardar el resultado en un archivo de texto ---
            try:
                carpeta_validaciones = r"C:\ZetaOne\Validaciones"
                os.makedirs(carpeta_validaciones, exist_ok=True)
                
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                nombre_archivo = f"resultado_validacion_{timestamp}.txt"
                ruta_archivo = os.path.join(carpeta_validaciones, nombre_archivo)
                
                with open(ruta_archivo, 'w', encoding='utf-8') as f:
                    f.write(f"--- Resultado de Validación Automática ---\n")
                    f.write(f"Fecha: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Carpeta Escaneada: {self.selected_sd_folder}\n")
                    f.write("-" * 40 + "\n\n")
                    f.write(resumen)
                
                self.logear_panel(f"Resultado de la validación guardado en: {ruta_archivo}")
            except Exception as e:
                error_msg = f"No se pudo guardar el archivo de resultado de validación: {e}"
                self.logear_panel(error_msg)
            # --- FIN DEL CAMBIO ---
            
            # Mostrar mensaje de resultado de validación
            if exito:
                if hay_discrepancias:
                    # Mostrar mensaje con diferencias detalladas
                    messagebox.showwarning(
                        "Validación con Diferencias",
                        f"Se validaron los archivos listados con el/los archivo(s) .txt encontrados.\n\n{resumen}",
                        parent=self.frame
                    )
                else:
                    # Validación exitosa sin diferencias
                    messagebox.showinfo(
                        "Validación Exitosa",
                        f"Se validaron los archivos listados con el/los archivo(s) .txt encontrados exitosamente.\n\nTodos los archivos coinciden.",
                        parent=self.frame
                    )

            # --- CAMBIO: Habilitar botón y bloquear ambientes solo si la validación fue exitosa ---
            if exito:
                self.ambientes_panel.set_bloqueo_ambientes_hijos(bloqueado=True)
                self.btn_validar_auto.config(state="normal")
                self.logear_panel("Botón 'Validar' habilitado.")
                # Verificar si hay archivos seleccionados para activar animación
                self._verificar_seleccion_para_animacion_validar()
            else:
                # Si hubo un error (ej. no se encontró .txt), mantener el botón deshabilitado
                self.btn_validar_auto.config(state="disabled")
                self.logear_panel("La validación no fue exitosa. El flujo automático se detiene.")
                # Asegurar que la animación esté detenida
                self._detener_animacion_validar()

        def validar_seleccionados(self):
            # Ahora esta función es el punto de entrada para el procesamiento final
            print(">>> [main] 1. validar_seleccionados() INICIADO")
            
            # Detener la animación del botón al hacer clic
            self._detener_animacion_validar()
            
            # 1. Obtener macroambientes seleccionados
            ambientes_seleccionados_idx = self.ambientes_panel.get_seleccionados()
            if not ambientes_seleccionados_idx:
                messagebox.showwarning("Sin Ambientes", "Debe seleccionar al menos un macroambiente para continuar.", parent=self.frame)
                return
            print(">>> [main] 2. Obtenidos ambientes seleccionados.")
            macros_seleccionados = [self.ambientes_panel.ambientes[i] for i in ambientes_seleccionados_idx]

            # 2. Obtener archivos seleccionados
            # --- CAMBIO: Obtener los archivos seleccionados en el orden en que se muestran en la grilla ---
            items_en_orden = self.tree.get_children('')
            items_seleccionados_en_orden = [item for item in items_en_orden if item in self.tree.selection()]
            if not items_seleccionados_en_orden:
                messagebox.showwarning("Sin Archivos", "Debe seleccionar al menos un archivo de la lista para continuar.", parent=self.frame)
                return
            print(">>> [main] 3. Obtenidos archivos seleccionados.")
            archivos_seleccionados = [self.archivos_unicos[int(iid)] for iid in items_seleccionados_en_orden]

            # 3. Construir el plan de ejecución con la lógica inteligente
            print(">>> [main] 4. Construyendo plan de ejecución...")
            plan_ejecucion = self.construir_plan_ejecucion(archivos_seleccionados, macros_seleccionados)
            print(">>> [main] 5. Plan construido. Abriendo diálogo de validación...")

            # 4. Mostrar diálogo de confirmación y ejecutar si se acepta
            # --- REQUERIMIENTO: Reabrir la ventana de validación después de catalogar ---
            # Guardamos el plan y los macros para poder reutilizarlos en el callback.
            self.plan_para_reabrir = plan_ejecucion
            self.macros_para_reabrir = macros_seleccionados

            # Llamamos a la función que abre el diálogo por primera vez.
            print(">>> [main] 5.1. Abriendo diálogo de validación por primera vez...")
            self._abrir_dialogo_validacion()

        def _abrir_dialogo_validacion(self):
            """Abre el diálogo de validación con callback para ejecutar catalogación."""
            self.dialogo_validacion = ValidacionAutomatizadaDialog(
                self.frame, 
                self.plan_para_reabrir, 
                self.macros_para_reabrir,
                on_ejecutar_callback=self._iniciar_catalogacion_desde_dialogo
            )
            # No esperamos que se cierre, el diálogo llama al callback cuando se ejecuta
            print(f">>> [main] 6. Diálogo de validación abierto con callback.")

        def _iniciar_catalogacion_desde_dialogo(self, plan_ejecutar):
            """Callback que se ejecuta cuando el usuario hace clic en Ejecutar Catalogación."""
            print(">>> [main] 7. Callback de catalogación recibido.")
            self.logear_panel("Confirmación de catalogación aceptada. Iniciando proceso...")
            
            descripcion = simpledialog.askstring(
                "Descripción de Cambios", 
                "Ingrese una breve descripción para este lote de catalogación:",
                parent=self.frame
            )
            if descripcion is None:
                self.logear_panel("Catalogación cancelada.")
                return

            # Crear carpeta de catalogaciones (para pasar a la ventana de resultados)
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            carpeta_catalogaciones = os.path.join("C:\\ZetaOne\\Catalogaciones", f"cataloga{timestamp}")
            os.makedirs(carpeta_catalogaciones, exist_ok=True)

            # Crear y mostrar la ventana de resultados ANTES de catalogar
            # Usar dialogo_validacion como padre si existe, sino usar self.frame
            parent_ventana = self.dialogo_validacion if hasattr(self, 'dialogo_validacion') else self.frame
            ventana_resultados = VentanaResultadosCatalogacion(parent_ventana, carpeta_catalogaciones)
            # Guardar referencia a la ventana de resultados
            self.ventana_resultados_catalogacion = ventana_resultados
            
            # Crear y mostrar la ventana de progreso
            progress_dialog = ProgressWindow(parent_ventana, "Catalogando...")
            progress_dialog.progress_bar.config(mode='indeterminate')
            progress_dialog.progress_bar.start()

            def update_progress_callback(current, total, filename):
                progress_dialog.update_progress(current, f"({current}/{total}) Catalogando: {filename}...")

            print(">>> [main] 9. Lanzando hilo de catalogación (_worker_catalogacion)...")
            threading.Thread(target=self._worker_catalogacion, 
                           args=(plan_ejecutar, descripcion, update_progress_callback, 
                                progress_dialog, ventana_resultados, carpeta_catalogaciones), 
                           daemon=True).start()

        def construir_plan_ejecucion(self, archivos, macros_seleccionados):
            """
            Aplica la lógica inteligente para asignar cada archivo a sus ambientes de destino.
            """
            # --- LÓGICA COMPLETAMENTE REESTRUCTURADA SEGÚN NUEVAS REGLAS ---
            plan = []
            todos_ambientes_map = {a['nombre']: a for a in self.ambientes_panel.ambientes}
            
            for archivo in archivos:
                ruta = archivo['rel_path'].lower()
                ambientes_destino_nombres = set()
                regla_aplicada = "Regla por defecto" # Valor inicial

                # Las reglas se evalúan en orden de prioridad
                if 'central' in ruta:
                    # REGLA 1: Contiene "central" -> Asignar a macros
                    for macro in macros_seleccionados:
                        ambientes_destino_nombres.add(macro['nombre'])
                    regla_aplicada = "Ruta contiene 'central'"
                
                elif 'local' in ruta:
                    # --- LÓGICA REESTRUCTURADA CON PRIORIDADES ---
                    # REGLA 2: "local" + "ATMcompensa..."
                    if any(segmento.startswith('atmcompensa') for segmento in ruta.replace('\\', '/').split('/')):
                        for macro in macros_seleccionados:
                            for nombre_hijo in self.ambientes_panel.ambientes_relacionados.get(macro['nombre'], []):
                                hijo_obj = todos_ambientes_map.get(nombre_hijo)
                                # Asigna a hijo SQL Server cuyo nombre contenga "CMP"
                                if hijo_obj and 'sql server' in hijo_obj.get('driver', '').lower() and 'cmp' in nombre_hijo.lower():
                                    ambientes_destino_nombres.add(nombre_hijo)
                        regla_aplicada = "Ruta contiene 'local' y segmento 'ATMcompensa...'"

                    # REGLA 3: "local" + "atm" (pero no la anterior)
                    elif 'atm' in ruta:
                        for macro in macros_seleccionados:
                            for nombre_hijo in self.ambientes_panel.ambientes_relacionados.get(macro['nombre'], []):
                                hijo_obj = todos_ambientes_map.get(nombre_hijo)
                                if hijo_obj and 'sql server' in hijo_obj.get('driver', '').lower() and 'atm' in nombre_hijo.lower():
                                    ambientes_destino_nombres.add(nombre_hijo)
                        regla_aplicada = "Ruta contiene 'local' y 'atm'"
                    
                    # REGLA 4: "local" (pero no las anteriores)
                    else:
                        for macro in macros_seleccionados:
                            for nombre_hijo in self.ambientes_panel.ambientes_relacionados.get(macro['nombre'], []):
                                hijo_obj = todos_ambientes_map.get(nombre_hijo)
                                if hijo_obj and 'sybase' in hijo_obj.get('driver', '').lower():
                                    ambientes_destino_nombres.add(nombre_hijo)
                        regla_aplicada = "Ruta contiene 'local' (Sybase)"
                
                # REGLA FINAL: Si ninguna regla anterior asignó ambientes, se aplica la regla por defecto
                if not ambientes_destino_nombres:
                    for macro in macros_seleccionados:
                        ambientes_destino_nombres.add(macro['nombre'])
                    # Si la regla por defecto se aplica, es porque no hubo coincidencia con las reglas anteriores
                    if regla_aplicada == "Regla por defecto":
                        regla_aplicada = "Regla por defecto (no hubo coincidencia)"

                # Loguear la decisión tomada
                self.logear_panel(f"Archivo '{archivo['nombre_archivo']}' -> {regla_aplicada}. Ambientes: {', '.join(ambientes_destino_nombres) or 'Ninguno'}")

                # Advertir si se encontraron múltiples coincidencias para una regla de hijo
                if len(ambientes_destino_nombres) > len(macros_seleccionados) and 'central' not in ruta and 'local' not in regla_aplicada:
                    self.logear_panel(f"  ADVERTENCIA: Se encontraron múltiples ambientes hijos para la regla '{regla_aplicada}'. Se asignarán a todos los encontrados.")

                # Convertir nombres a objetos de ambiente
                ambientes_finales = [todos_ambientes_map[nombre] for nombre in ambientes_destino_nombres if nombre in todos_ambientes_map]

                if ambientes_finales:
                    plan.append({
                        "archivo": archivo,
                        "ambientes": ambientes_finales
                    })
                else:
                    self.logear_panel(f"  ADVERTENCIA: El archivo '{archivo['nombre_archivo']}' no fue asignado a ningún ambiente válido tras aplicar la regla '{regla_aplicada}'.")
            
            return plan
        
        def _worker_catalogacion(self, plan, descripcion, progress_callback, progress_dialog, ventana_resultados=None, carpeta_catalogaciones=None):
            """
            (Worker Thread) Ejecuta el plan de catalogación y muestra los resultados.
            """
            print(">>> [worker] 10. Hilo _worker_catalogacion INICIADO.")
            # --- SOLUCIÓN: Crear una función de log segura para hilos ---
            # Esta función asegura que cualquier actualización del log se ejecute en el hilo principal de Tkinter.
            def log_thread_safe(msg):
                if self.app_root and self.app_root.winfo_exists():
                    # self.logear_panel se ejecutará en el hilo principal, evitando el crash.
                    self.app_root.after(0, self.logear_panel, msg)
            # --- FIN DE LA SOLUCIÓN ---
            
            # Callback para agregar resultados progresivamente
            def agregar_resultado_callback(resultado):
                if ventana_resultados:
                    self.app_root.after(0, ventana_resultados.agregar_resultado, resultado)
            
            try: # <--- ADDED TRY BLOCK
                # Bloquear UI
                self.app_root.after(0, self.btn_validar_auto.config, {"state": "disabled"})
                
                # --- CORRECCIÓN: Pasar la función de log segura en lugar de la directa ---
                print(">>> [worker] 11. Llamando a catalogar_plan_ejecucion...")
                # --- CAMBIO: Pasar la función de progreso y el callback de resultados ---
                resultados, carpeta_cat = catalogar_plan_ejecucion(plan, descripcion, 
                                                                    log_func=log_thread_safe, 
                                                                    progress_func=progress_callback,
                                                                    resultado_callback=agregar_resultado_callback,
                                                                    carpeta_destino=carpeta_catalogaciones)
                
                # --- REQUERIMIENTO: Guardar el resultado en un archivo de texto ---
                # --- CAMBIO: Pasar el nombre de usuario logueado y la carpeta de catalogación ---
                self._guardar_resultado_catalogacion_en_archivo(resultados, descripcion, self.controlador.usuario_logueado, log_thread_safe, carpeta_cat)
                
                print(">>> [worker] 12. catalogar_plan_ejecucion finalizado.")
                # --- CAMBIO: Solo cerrar la ventana de progreso, la de resultados ya está visible ---
                self.app_root.after(0, self._on_catalogacion_finalizada, progress_dialog)


            except Exception as e: # <--- ADDED EXCEPT BLOCK
                print(f">>> [worker] ERROR CRÍTICO: {e}\n{traceback.format_exc()}")
                error_msg = f"ERROR CRÍTICO EN HILO DE CATALOGACIÓN: {str(e)}\n{traceback.format_exc()}"
                log_thread_safe(error_msg)
                # --- CAMBIO: Asegurarse de cerrar ambas ventanas si hay un error ---
                if progress_dialog:
                    self.app_root.after(0, progress_dialog.destroy)
                if ventana_resultados:
                    self.app_root.after(0, ventana_resultados.destroy)
                self.app_root.after(0, lambda: messagebox.showerror("Error Crítico", "La catalogación falló inesperadamente. Revise el log de operaciones.", parent=self.frame))
                self.app_root.after(0, self.btn_validar_auto.config, {"state": "normal"}) # Asegurarse de que el botón se re-habilite
        
        def _on_catalogacion_finalizada(self, progress_dialog):
            """Callback que se ejecuta en el hilo principal después de la catalogación."""
            # --- CAMBIO: Solo cerrar la ventana de progreso ---
            if progress_dialog:
                # --- CAMBIO: Detener la animación de la barra antes de cerrar ---
                progress_dialog.progress_bar.stop()
                progress_dialog.destroy()

            self.btn_validar_auto.config(state="normal")
            self.logear_panel("Catalogación finalizada. Revise los resultados.")
            print(">>> [main] 13. Catalogación completada.")
            
            # Mostrar mensaje de catalogación finalizada automáticamente
            if hasattr(self, 'ventana_resultados_catalogacion') and self.ventana_resultados_catalogacion:
                self.ventana_resultados_catalogacion.mostrar_mensaje_finalizado()


        def _guardar_resultado_catalogacion_en_archivo(self, resultados, descripcion, usuario_app, log_func, carpeta_catalogaciones):
            """
            (Worker Thread) Guarda el resumen de la catalogación en un archivo de texto.
            """
            try:
                # La carpeta ya fue creada en catalogar_plan_ejecucion
                os.makedirs(carpeta_catalogaciones, exist_ok=True)
                
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                nombre_archivo = f"resultado_catalogacion_{timestamp}.txt"
                ruta_archivo = os.path.join(carpeta_catalogaciones, nombre_archivo)
                
                with open(ruta_archivo, 'w', encoding='utf-8') as f:
                    f.write(f"--- Resultado de Catalogación ---\n")
                    f.write(f"Fecha: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Usuario PC: {getpass.getuser()}\n")
                    f.write(f"Catalogador: {usuario_app or 'No definido'}\n")
                    # --- CAMBIO: Se elimina la línea "Ruta SD" del encabezado, ya que ahora está en la tabla de detalle ---
                    f.write(f"Descripción del Lote: {descripcion}\n")
                    f.write("-" * 40 + "\n\n")
                    
                    f.write(f"{'ESTADO':<10} | {'AMBIENTE':<15} | {'BASE DATOS':<15} | {'RUTA RELATIVA':<40} | {'DETALLE'}\n")
                    f.write(f"{'-'*10} | {'-'*15} | {'-'*15} | {'-'*40} | {'-'*50}\n")

                    for res in resultados:
                        bd_usada = res.get('base_datos', 'N/A')
                        f.write(f"{res['estado']:<10} | {res['ambiente']:<15} | {bd_usada:<15} | {res.get('ruta', 'N/A'):<40} | {res['detalle']}\n")
                
                log_func(f"Resultado de la catalogación guardado en: {ruta_archivo}")
            except Exception as e:
                log_func(f"ERROR: No se pudo guardar el archivo de resultado de catalogación: {e}")

        def lanzar_catalogacion(self):
            def aceptar(nombre, descripcion):
                messagebox.showinfo("Catalogado", f"Archivo '{nombre}' catalogado.\nDescripción: {descripcion}")
                self.logear_panel(f"Archivo '{nombre}' catalogado con descripción '{descripcion}'.")
            CatalogacionDialog(self.frame, aceptar_callback=aceptar)

    #--------------------------panel de ambientes-------------------------------------
    
    class AmbientesPanel:

        def __init__(self, parent, logtxt=None):
            self.frame = tb.LabelFrame(parent, text="Ambientes Configurados", bootstyle="primary", padding=(12, 8))
            
            # --- CORRECCIÓN: Inicializar el atributo al principio del constructor ---
            self.hijos_bloqueados_permanentemente = False
            
            # --- CORRECCIÓN: Carga segura de imágenes de estado ---
            try:
                self.imagen_check = tk.PhotoImage(file=recurso_path("imagenes_iconos", "check_green.png"))
                self.imagen_x = tk.PhotoImage(file=recurso_path("imagenes_iconos", "x_red.png"))
                self.imagen_neutral = tk.PhotoImage(file=recurso_path("imagenes_iconos", "neutral_grey.png"))
                icon_path = recurso_path("imagenes_iconos", "zeta99.png")
                self.zeta_icon = tb.PhotoImage(file=icon_path)
            except Exception as e:
                print(f"ADVERTENCIA: No se pudieron cargar los iconos de estado: {e}")
                self.imagen_check = self.imagen_x = self.imagen_neutral = self.zeta_icon = None
            
            self.ambientes = cargar_ambientes()
            self.estado_conex_ambs = [None] * len(self.ambientes)
            self.logtxt = logtxt

            self.ambientes_relacionados = {}
            try:
                with open(recurso_path('json', 'ambientesrelacionados.json'), 'r') as f:
                    self.ambientes_relacionados = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                self.logear_panel(f"ADVERTENCIA: No se pudo cargar 'ambientesrelacionados.json': {e}")

            self.checkbuttons = {} # Map name to {'var': ..., 'widget': ...}

            # Boton para probar conexión
            self.btn_testamb = tb.Button(
                self.frame,
                text="Probar Conexión",
                image=self.zeta_icon,
                compound="left" if self.zeta_icon else None,
                command=self.test_ambs,
                bootstyle="warning-outline",
                width=10
            )
            self.btn_testamb.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12), padx=(5, 5))

            # --- REQUERIMIENTO: Añadir Scrollbar al panel de ambientes ---
            # 1. Crear un frame contenedor para el canvas y el scrollbar
            canvas_container = tb.Frame(self.frame)
            canvas_container.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, 8))
            canvas_container.rowconfigure(0, weight=1)
            canvas_container.columnconfigure(0, weight=1)

            # 2. Crear el Canvas y el Scrollbar
            canvas = tb.Canvas(canvas_container, highlightthickness=0)
            scrollbar = tb.Scrollbar(canvas_container, orient="vertical", command=canvas.yview, bootstyle="info-round")
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.grid(row=0, column=0, sticky="nsew")
            scrollbar.grid(row=0, column=1, sticky="ns")

            # 3. El check_frame ahora va DENTRO del canvas
            self.ambientes_vars = []
            self.check_frame = tb.Frame(canvas)
            canvas.create_window((0, 0), window=self.check_frame, anchor="nw")

            self.check_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            # --- FIN DEL REQUERIMIENTO ---

            self.refresh_amb_list()

            self.frame.rowconfigure(1, weight=1)
            self.frame.columnconfigure(0, weight=1)

            # Botones de accion
            botones_amb = tb.Frame(self.frame, bootstyle="Panel2.TFrame")
            botones_amb.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
            tb.Button(botones_amb, text="➕Agregar", command=self.add_amb, bootstyle="success-outline").grid(row=2, column=0, padx=2, pady=2, sticky='ew')
            tb.Button(botones_amb, text="✏️Editar", command=self.edit_amb, bootstyle="info-outline").grid(row=2, column=3, padx=2, pady=2, sticky='ew')
            tb.Button(botones_amb, text="🗑️Eliminar", command=self.del_amb, bootstyle="danger-outline").grid(row=2, column=2, padx=2, pady=2, sticky='ew')
            tb.Button(botones_amb, text="relacionar", command=self.gestionar_relacionados, bootstyle="primary-outline", width=10).grid(row=2, column=1, pady=2, padx=2, sticky="ew")

            self.amb_estado = tb.Label(self.frame, text="", anchor="w", bootstyle="inverse-info", font=("sagoe UI", 10, "bold"))
            self.amb_estado.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))

            # Barra de progreso visual
            self.progressbar_amb = tb.Progressbar(
                self.frame,
                orient="horizontal",
                length=220,
                bootstyle="warning-striped",
                mode="determinate"
            )
            self.progressbar_amb.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 0))
            self.progressbar_amb.grid_remove()

            self.lbamb = None

        # --- SOLUCIÓN: Se reincorpora el método 'logear_panel' ---
        def logear_panel(self, msg):
            if self.logtxt is not None:
                self.logtxt.insert(tk.END, "[Ambientes] " + msg + "\n")
                self.logtxt.see(tk.END)

        def refresh_amb_list(self):
            for widget in self.check_frame.winfo_children():
                widget.destroy()
            self.ambientes_vars.clear()
            self.checkbuttons.clear()

            for idx, amb in enumerate(self.ambientes):
                var = tk.BooleanVar()
                self.ambientes_vars.append(var)
                label = f"{amb['nombre']} | {amb['ip']} | {amb['puerto']} "
                estado = self.estado_conex_ambs[idx]
                
                icono = self.imagen_neutral
                bootstyle = ""
                if estado is True:
                    bootstyle = "success"
                    icono = self.imagen_check
                elif estado is False:
                    bootstyle = "danger"
                    icono = self.imagen_x

                chk = tb.Checkbutton(self.check_frame, text=label, variable=var, bootstyle=bootstyle, command=self.actualizar_selecciones_relacionadas)
                chk.grid(row=idx, sticky='w', padx=2, pady=0)

                lbl_estado = tb.Label(self.check_frame, image=icono)
                lbl_estado.image = icono
                lbl_estado.grid(row=idx, column=1, padx=(8, 2), sticky='w')
                
                self.checkbuttons[amb['nombre']] = {'var': var, 'widget': chk}
            
            self.actualizar_selecciones_relacionadas()

            # --- CAMBIO: Re-aplicar el bloqueo permanente si está activo ---
            # Esto asegura que después de probar conexiones, los hijos sigan bloqueados.
            if self.hijos_bloqueados_permanentemente:
                ambientes_hijos = set()
                for hijos in self.ambientes_relacionados.values():
                    ambientes_hijos.update(hijos)

                for amb_name, chk_info in self.checkbuttons.items():
                    if amb_name in ambientes_hijos:
                        chk_info['var'].set(False)
                        chk_info['widget'].config(state='disabled')
            # --- FIN DEL CAMBIO ---

        def actualizar_selecciones_relacionadas(self):
            # --- CAMBIO: El bloqueo de hijos solo se aplica si el flujo automático está activo ---
            if self.hijos_bloqueados_permanentemente:
                # 1. Find all selected parents
                selected_parents = set()
                for parent_name in self.ambientes_relacionados:
                    if parent_name in self.checkbuttons and self.checkbuttons[parent_name]['var'].get():
                        selected_parents.add(parent_name)

                # 2. Create a set of all children that should be disabled
                children_to_disable = set()
                for parent in selected_parents:
                    children_to_disable.update(self.ambientes_relacionados.get(parent, []))

                # 3. Iterate through all checkbuttons to update their state
                for amb_name, chk_info in self.checkbuttons.items():
                    is_child_of_selected_parent = amb_name in children_to_disable

                    if is_child_of_selected_parent:
                        if chk_info['widget'].cget('state') != 'disabled':
                            chk_info['var'].set(False)
                            chk_info['widget'].config(state='disabled')
                    else:
                        # Solo desbloquear si no está bloqueado permanentemente (lo cual es el caso aquí)
                        if chk_info['widget'].cget('state') == 'disabled':
                            chk_info['widget'].config(state='normal')
            # Si el bloqueo permanente no está activo, no se hace nada y el usuario puede seleccionar libremente.


        def add_amb(self):
            self.editar_amb_dialog(nuevo=True)

        def edit_amb(self):
            # --- CORRECCIÓN: El nombre de la variable era 'sel' en la función de borrado ---
            sel_indices = [i for i, v in enumerate(self.ambientes_vars) if v.get()] # sel
            if len(sel_indices) != 1:
                messagebox.showerror("Editar ambiente", "Seleccione UN solo ambiente", parent=self.frame)
                return
            self.editar_amb_dialog(nuevo=False, editar_idx=sel_indices[0])

        def del_amb(self):
            sel = [i for i, v in enumerate(self.ambientes_vars) if v.get()]
            if not sel:
                messagebox.showwarning("Error", "debe seleccionar minimo un ambiente")
                return
            
            ok = messagebox.askyesno("Confirmar", "¿Eliminar los ambientes seleccionados?", parent=self.frame)
            if ok:
                # Eliminar de atrás hacia adelante para no alterar los índices
                for idx in sorted(sel, reverse=True):
                    self.logear_panel(f"Eliminado ambiente: {self.ambientes[idx]['nombre']}")
                    self.ambientes.pop(idx)
                    self.estado_conex_ambs.pop(idx)
                
                guardar_ambientes(self.ambientes)
                self.refresh_amb_list()

        def gestionar_relacionados(self):
            sel= [i for i, v in enumerate(self.ambientes_vars) if v.get()]
            if len(sel) != 1:
                messagebox.showwarning("seleccione un ambiente", "Seleccione UN solo ambiente", parent=self.frame)
                return
            idx = sel[0]
            nombre_ambiente=self.ambientes[idx]['nombre']
            gestionar_ambientes_relacionados(nombre_ambiente, master=self.frame)

        def set_bloqueo_ambientes_hijos(self, bloqueado: bool):
            """Bloquea o desbloquea la selección de ambientes hijos."""
            # --- LÓGICA DE BLOQUEO RESTAURADA ---
            self.hijos_bloqueados_permanentemente = bloqueado
            
            # Construir un set con todos los ambientes que son hijos de alguien
            ambientes_hijos = set()
            for hijos in self.ambientes_relacionados.values():
                ambientes_hijos.update(hijos)

            for amb_name, chk_info in self.checkbuttons.items():
                # Si el ambiente es un hijo, se bloquea/desbloquea
                if amb_name in ambientes_hijos:
                    if bloqueado:
                        chk_info['var'].set(False)  # Deseleccionar por seguridad
                        chk_info['widget'].config(state='disabled')
                    else:
                        chk_info['widget'].config(state='normal')
            
            if bloqueado:
                self.logear_panel("Bloqueando selección de ambientes hijos.")
            else:
                self.logear_panel("Desbloqueando todos los ambientes para selección.")
        
        def editar_amb_dialog(self, nuevo=True, editar_idx=None):
            window = tb.Toplevel(self.frame)
            window.title("Nuevo ambiente" if nuevo else "Editar ambiente")
            window.resizable(False, False)
            
            fields = [("Nombre","nombre"),("IP/HOST","ip"),("Puerto","puerto"),("Usuario","usuario"),("Clave","clave"),("Base de datos","base"),("Driver ODBC","driver")]
            default = {'driver':'Sybase ASE ODBC Driver', 'puerto':'7028'}
            vals = {}

            for i, (lbl, key) in enumerate(fields):
                lab = tb.Label(window, text=lbl + ":")
                lab.grid(row=i, column=0, padx=8, pady=4, sticky="e")
                show = "*" if key == "clave" else ""
                ent = tb.Entry(window, width=32, show=show, bootstyle="secondary")
                ent.grid(row=i, column=1, padx=8, pady=4, sticky="we")
                vals[key] = ent

            # --- CAMBIO: Posicionar el cursor en el primer campo de entrada ("Nombre") ---
            if "nombre" in vals:
                vals["nombre"].focus_set()

            window.columnconfigure(1, weight=1)

            if not nuevo and editar_idx is not None:
                amb = self.ambientes[editar_idx]
                for key in vals:
                    if key in amb:
                        vals[key].insert(0, amb[key])
            else:
                for key in vals:
                    if key in default:
                        vals[key].insert(0, default[key])

            def snd():
                data = {key: vals[key].get() for key in vals}
                if not all(data[x] for x in ['nombre', 'ip', 'puerto', 'usuario', 'clave', 'base', 'driver']):
                    messagebox.showwarning("Error", "Faltan datos obligatorios", parent=window)
                    return
                if nuevo:
                    self.ambientes.append(data)
                    self.estado_conex_ambs.append(None)
                    self.logear_panel(f"Agregado nuevo ambiente: {data['nombre']}")
                else:
                    self.logear_panel(f"Editado ambiente: {data['nombre']} (Anterior: {self.ambientes[editar_idx]['nombre']})")
                    self.ambientes[editar_idx] = data
                guardar_ambientes(self.ambientes)
                self.refresh_amb_list() # Actualiza la lista en la UI
                window.destroy()

            btn_save = tb.Button(window, text="Guardar", command=snd, bootstyle="success" )
            btn_save.grid(row=len(fields), column=0, pady=6, padx=8, sticky="we")
            btn_salir = tb.Button(window, text="Cancelar", command=window.destroy, bootstyle="secondary", width=10)
            btn_salir.grid(row=len(fields), column=1, pady=6, padx=8, sticky="we")
            
            window.grab_set() 
        
        # --- SOLUCIÓN: Se restaura el método original que sí funciona ---
        def test_ambs(self):
            sel = [i for i, v in enumerate(self.ambientes_vars) if v.get()]
            if not sel:
                messagebox.showinfo("Conexión", "Seleccione al menos un ambiente para probar.", parent=self.frame)
                return

            self.btn_testamb.config(bootstyle="warning-outline")
            self.frame.update()

            total = len(sel)
            self.progressbar_amb.config(bootstyle="warning-striped")
            self.progressbar_amb['maximum'] = total
            self.progressbar_amb['value'] = 0
            self.progressbar_amb.grid()
            hay_exito = False
            hay_fallo = False

            for idx in sel:
                self.estado_conex_ambs[idx] = None

            for i, idx in enumerate(sel):
                amb = self.ambientes[idx]
                self.progressbar_amb['value'] = i
                self.amb_estado.config(text=f"Probando ambiente {amb['nombre']}...")
                self.logear_panel(f"Intentando conexión al ambiente '{amb['nombre']}'")
                self.frame.update()
                ok, msg = probar_conexion_amb(amb, log_func=self.logear_panel)
                self.progressbar_amb['value'] = i + 1

                self.estado_conex_ambs[idx] = ok

                if ok:
                    self.progressbar_amb.config(bootstyle="success-striped")
                    self.amb_estado.config(text=f"Ambiente {amb['nombre']}: Conexión exitosa")
                    hay_exito = True
                    self.logear_panel(f"Conexión exitosa a '{amb['nombre']}': {msg}")
                else:
                    self.progressbar_amb.config(bootstyle="warning-striped")
                    self.amb_estado.config(text=f"Ambiente {amb['nombre']}: Conexión fallida")
                    hay_fallo = True
                    self.logear_panel(f"Conexión *fallida* a '{amb['nombre']}': {msg}")
                self.frame.update()

            self.progressbar_amb.grid_remove()
            self.refresh_amb_list()
            for var in self.ambientes_vars:
                var.set(False)

            if hay_exito and not hay_fallo:
                self.btn_testamb.config(bootstyle="success-outline")
                self.amb_estado.config(text="Todas las conexiones exitosas")
                self.logear_panel("Prueba de ambientes: ¡todas las conexiones exitosas!")
            elif hay_exito and hay_fallo:
                self.btn_testamb.config(bootstyle="warning-outline") # Cambiado para ser más visible
                self.amb_estado.config(text="Al menos un ambiente OK")
                self.logear_panel("Prueba de ambientes: al menos un ambiente OK, alguno fallido.")
            else:
                self.btn_testamb.config(bootstyle="danger-outline")
                self.amb_estado.config(text="Todas las conexiones fallidas")
                self.logear_panel("Prueba de ambientes: todas las conexiones fallidas.")

        def get_seleccionados(self):
            return [i for i, v in enumerate(self.ambientes_vars) if v.get()]
