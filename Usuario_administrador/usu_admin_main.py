#importaciones generales
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import os
import datetime
import threading # <-- SOLUCIÓN: Se añade el import que faltaba

# --- Import clave para que las rutas funcionen en el .exe ---
from util_rutas import recurso_path

#importaciones frame derecha (panel de archivos)
from .handlers.explorador import explorar_sd_folder
from .util_repetidos import quitar_repetidos

#Importacion de estilos
from styles import boton_principal, boton_accion, boton_exito, boton_rojo
from .widgets.tooltip import ToolTip

from .validacion_dialog import lanzar_validacion
from .catalogacion_dialog import CatalogacionDialog
from .Catalogacion_CTS import CatalogacionCTS

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
            style = tb.Style()
            print(style.element_names())


            #tamaño de la ventana
            ventana_ancho = 1300 # Reducido para portátiles
            ventana_alto = 680  # Reducido para portátiles
            pantalla_ancho = self.root.winfo_screenwidth()
            pantalla_alto = self.root.winfo_screenheight()
            x = int((pantalla_ancho / 2) - (ventana_ancho / 2 ))
            # --- CORRECCIÓN: Se ajusta la posición 'y' para compensar la barra de tareas de Windows ---
            # Se sube la ventana un poco para que la parte inferior no quede oculta.
            y = int((pantalla_alto / 2) - (ventana_alto / 2) - 40) # Restamos 40px extra
            self.root.geometry(f"{ventana_ancho}x{ventana_alto}+{x}+{y}")
            root.resizable(True, True) # Permitir minimizar/maximizar

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
            barra_sd.columnconfigure(0, weight=1, minsize=180)
            barra_sd.columnconfigure(1, weight=1, minsize=230)
            barra_sd.columnconfigure(2, weight=5)
            barra_sd.columnconfigure(3, weight=2, minsize=240)

            #botones de seleccion
            self.single_sd_btn = tb.Button(
                barra_sd, text="SD Único", command=self.single_sd, bootstyle="primary-outline", width=14
            )
            self.multi_sd_btn = tb.Button(
                barra_sd, text="Carpeta con varios SD", command=self.multi_sd, bootstyle="primary-outline", width=22
            )
            self.single_sd_btn.grid(row=0, column=0, padx=10, sticky="ew")
            self.multi_sd_btn.grid(row=0, column=1, padx=10, sticky="ew")

            self.sd_label = tb.Label(barra_sd, text="")
            self.sd_label.grid(row=0, column=2, sticky="w", padx=(16, 0))

            self.btn_repetidos = tb.Button(
                barra_sd, text="Programas Repetidos", command=self.ver_repetidos, width=31, bootstyle="dark-outline-button"
            )
            self.btn_repetidos.grid(row=0, column=3, padx=(6, 6), sticky="e")

            self.btn_cata_cts = tb.Button(barra_sd, text="catalogacion de CTS", command=self.abrir_Catalog_CTS, width=31, bootstyle="dark-outline-button")
            self.btn_cata_cts.grid(row=0, column=2, padx=(6, 6), sticky="e")

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
            self.tree.heading("Ruta", text="Ruta SD")
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
            tb.Button(barra_accion, text="Validar Seleccionados", command=self.validar_seleccionados, bootstyle="warning-outline").pack(side="left", padx=18) #amarillo borde
            tb.Button(barra_accion, text="Log de Operaciones 📝", command=self.toggle_log, bootstyle="TButton").pack(side="left", padx=18) #azul
            tb.Button(barra_accion, text="Salir", command=self.salir, bootstyle="danger", width=10).pack(side="right", padx=18) #Rojo
            tb.Button(barra_accion, text="volver", command=self.volver_creden, bootstyle="dark", width=10).pack(side="right", padx=18) #gris

            self.frame.columnconfigure(0, weight=1)
            self.frame.rowconfigure(1, weight=1)

            self.archivos_unicos = []
            self.selected_sd_folder = ""
            self.multi_sd_flag = False
            self.repetidos_log = []
         
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

        def deseleccionar_todos(self):
            for iid in self.tree.selection():
                self.tree.selection_remove(iid)
            self.logear_panel("Deseleccionados todos los archivos.")

        def salir(self):
            self.logear_panel("Aplicación finalizada a solicitud del usuario.")
            self.frame.quit()
            self.frame.winfo_toplevel().quit()

        def volver_creden(self):
            self.controlador.mostrar_pantalla_inicio()

        def single_sd(self):
            carpeta = filedialog.askdirectory(title="Seleccionar carpeta SD única")
            if carpeta:
                self.selected_sd_folder = carpeta
                self.multi_sd_flag = False
                self.sd_label.config(text="SD único: " + carpeta)
                self.logear_panel(f"Seleccionado SD único: {carpeta}")
                self.escanear_archivos_inner()

        def multi_sd(self):
            carpeta = filedialog.askdirectory(title="Seleccionar carpeta con varios SDs")
            if carpeta:
                self.selected_sd_folder = carpeta
                self.multi_sd_flag = True
                self.sd_label.config(text="Carpeta con varios SDs: " + carpeta)
                self.logear_panel(f"Seleccionada carpeta multi-SD: {carpeta}")
                self.escanear_archivos_inner()

        def escanear_archivos_inner(self):
            carpeta = self.selected_sd_folder
            multi = self.multi_sd_flag
            if not carpeta:
                messagebox.showwarning("Advertencia", "Seleccione una carpeta válida.", parent=self.frame)
                self.repetidos_log = []
                self.logear_panel("Intento de escaneo con carpeta inválida.")
                return
            archivos_candidatos = explorar_sd_folder(carpeta, multi_sd=multi)
            if not archivos_candidatos:
                self.tree.delete(*self.tree.get_children())
                self.archivos_unicos = []
                self.repetidos_log = []
                self.logear_panel("No se detectaron archivos candidatos en la carpeta.")
                return
            self.archivos_unicos, self.repetidos_log = quitar_repetidos(archivos_candidatos)
            self.tree.delete(*self.tree.get_children())
            for idx, a in enumerate(self.archivos_unicos):
                fecha = datetime.datetime.fromtimestamp(a['fecha_mod']).strftime('%Y-%m-%d %H:%M:%S')
                ruta_corta = a['rel_path']
                tag = "alt" if idx % 2 == 1 else ""
                self.tree.insert("", "end", iid=str(idx), values=(a['nombre_archivo'], ruta_corta, fecha), tags=(tag,))
            self.tree.tag_configure('alt', background="#f3f9fb")
            self.logear_panel(f"Escaneados {len(self.archivos_unicos)} archivos únicos. Repetidos: {len(self.repetidos_log)}.")

        def get_tooltip_for_row(self, iid):
            try:
                if iid and int(iid)<len(self.archivos_unicos):
                    return self.archivos_unicos[int(iid)]['rel_path']
            except (ValueError, IndexError):
                return ""
            return ""

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
                st.insert(tk.END, "-"*110+"\n")
            st.configure(state="disabled")
            self.logear_panel("Mostrada ventana de fuentes repetidos.")

        def abrir_Catalog_CTS(self):
            CatalogacionCTS(self.app_root)

        def validar_seleccionados(self):
            seleccionados_iids = self.tree.selection()
            if not seleccionados_iids:
                messagebox.showwarning("Validación", "Seleccione uno o más archivos de la lista.", parent=self.frame)
                self.logear_panel("Intento de validar sin selección de archivos.")
                return

            seleccionados_archivos = [int(iid) for iid in seleccionados_iids]
            ambientes_panel = self.ambientes_panel

            selamb_idx = ambientes_panel.get_seleccionados()          
            if not selamb_idx:
                messagebox.showwarning("Validación", "No ha seleccionado ambientes para validar.", parent=self.frame)
                self.logear_panel("Intento de validar sin selección de ambientes.")
                return

            no_conectados = [idx for idx in selamb_idx if ambientes_panel.estado_conex_ambs[idx] is not True]
            if no_conectados:
                nombres = [ambientes_panel.ambientes[i]['nombre'] for i in no_conectados]
                msg = "Debe seleccionar solo ambientes con CONEXIÓN exitosa (verde) antes de validar.\n" \
                    "Los siguientes ambientes no tienen conexión exitosa:\n" + \
                    "\n".join(f"- {n}" for n in nombres)
                messagebox.showwarning("Ambiente", msg, parent=self.frame)
                self.logear_panel("Intento de validar ambientes sin conexión OK.")
                return

            self.logear_panel("Validando seleccionados contra multiambiente (detalle en log).")
            lanzar_validacion(self.frame, self.archivos_unicos, seleccionados_archivos, ambientes_panel)

        def lanzar_catalogacion(self):
            def aceptar(nombre, descripcion):
                messagebox.showinfo("Catalogado", f"Archivo '{nombre}' catalogado.\nDescripción: {descripcion}")
                self.logear_panel(f"Archivo '{nombre}' catalogado con descripción '{descripcion}'.")
            CatalogacionDialog(self.frame, aceptar_callback=aceptar)

    #--------------------------panel de ambientes-------------------------------------
    #--------------------------panel de ambientes-------------------------------------
    class AmbientesPanel:

        def __init__(self, parent, logtxt=None):
            self.frame = tb.LabelFrame(parent, text="Ambientes Configurados", bootstyle="primary", padding=(12, 8))
            
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

            self.ambientes_vars = []
            self.check_frame = tb.Frame(self.frame)
            self.check_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, 8), padx=(0, 0))
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

                chk = tb.Checkbutton(self.check_frame, text=label, variable=var, bootstyle=bootstyle)
                chk.grid(row=idx, sticky='w', padx=2, pady=0)

                lbl_estado = tb.Label(self.check_frame, image=icono)
                lbl_estado.image = icono
                lbl_estado.grid(row=idx, column=1, padx=(8, 2), sticky='w')

        def add_amb(self):
            self.editar_amb_dialog(nuevo=True)

        def edit_amb(self):
            sel = [i for i, v in enumerate(self.ambientes_vars) if v.get()]
            if len(sel) != 1:
                messagebox.showerror("Editar ambiente", "Seleccione UN solo ambiente", parent=self.frame)
                return
            self.editar_amb_dialog(nuevo=False, editar_idx=sel[0])

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