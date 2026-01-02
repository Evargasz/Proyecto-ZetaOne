import tkinter as tk
from tkinter import Toplevel, ttk, messagebox, simpledialog
import datetime
import os
import threading # Already imported, no change needed here
import re
import json
from util_rutas import recurso_path
from util_ventanas import centrar_ventana
from Usuario_administrador.handlers.ambientes import cargar_relaciones_hijos # Correcto

# --- SUGERENCIA: Mover estas funciones a un módulo de utilidades de parsing o a `handlers/catalogacion.py`
# para evitar duplicación de código, ya que `catalogacion.py` también las necesita.
def _extraer_info_desde_encabezado(ruta_archivo):
    """
    Lee un archivo .sp y extrae el nombre de la base de datos y del SP
    desde los comentarios del encabezado.
    Ej: /* Base de datos: cob_atm */
        /* Stored procedure: sp_consulta_asigna_tc */
    """
    db_name = None
    sp_name = None
    try:
        with open(ruta_archivo, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                # Búsqueda flexible que ignora espacios y mayúsculas/minúsculas
                match_db = re.search(r'Base\s+de\s+datos\s*:\s*(\w+)', line, re.IGNORECASE)
                if match_db:
                    db_name = match_db.group(1).strip()

                match_sp = re.search(r'Stored\s+procedure\s*:\s*(\w+)', line, re.IGNORECASE)
                if match_sp:
                    sp_name = match_sp.group(1).strip()

                # Si ya encontramos ambos, no es necesario seguir leyendo
                if db_name and sp_name:
                    break
    except Exception:
        pass # Si hay un error de lectura, devolvemos None

    return db_name, sp_name

def _extraer_db_de_sp(ruta_archivo):
    """
    Lee un archivo .sp y extrae el nombre de la base de datos de la línea 'use <database>'.
    """
    try:
        with open(ruta_archivo, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                linea_limpia = line.strip().lower()
                if linea_limpia.startswith('use '):
                    # Extrae la palabra después de 'use'
                    partes = line.strip().split()
                    if len(partes) > 1:
                        return partes[1].strip()
    except Exception:
        return None
    return None

def _extraer_sp_name_de_sp(ruta_archivo):
    """
    Lee un archivo .sp y extrae el nombre del Stored Procedure de la línea 'create procedure <sp_name>'.
    """
    try:
        with open(ruta_archivo, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                # Busca 'create procedure' o 'create proc', ignorando mayúsculas/minúsculas y espacios extra
                match = re.search(r'create\s+(?:procedure|proc)\s+([\w\.]+)', line, re.IGNORECASE)
                if match:
                    # El nombre del SP puede tener formato db.owner.name, solo queremos el nombre.
                    nombre_completo = match.group(1)
                    nombre_simple = nombre_completo.split('.')[-1]
                    return nombre_simple.strip()
    except Exception:
        return None
    return None




class ValidacionAutomatizadaDialog(Toplevel):
    def __init__(self, parent, plan_ejecucion, macros_seleccionados=None, on_ejecutar_callback=None):
        print(">>> [dialog] A. __init__() INICIADO.")
        super().__init__(parent)
        self.title("Confirmar Plan de Ejecución")
        # --- CAMBIO: Ampliar ventana, centrar y permitir maximizar ---
        self.geometry("1100x650")
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.transient(parent)  # Vincular a la ventana padre para mantener jerarquía
        self.grab_set()

        centrar_ventana(self, offset_y=-60)
        # --- FIN DEL CAMBIO ---

        self.on_ejecutar_callback = on_ejecutar_callback
        self.plan_ejecucion = plan_ejecucion
        self.plan_plano = [] # --- CAMBIO: Lista plana para tareas individuales (archivo, ambiente)
        self.macros_seleccionados = macros_seleccionados or []
        
        # --- NUEVO: Variables para animación del botón validar ---
        self.animacion_validar_activa = False
        self.animacion_validar_estado = 0  # 0 o 1 para alternar colores
        self.animacion_validar_id = None  # ID del after() para poder cancelarlo
        
        # --- NUEVO: Flag para cancelar validación en curso ---
        self.validacion_cancelada = False
        
        # --- MEJORA: Estructura para manejar pestañas si hay múltiples macros ---
        self.es_multi_ambiente = len(self.macros_seleccionados) > 1
        self.notebook = None
        self.tabs_info = {} # {tab_id: {'tree': tree_widget, 'frame': frame_widget}}
        self.relaciones_hijos = cargar_relaciones_hijos()
        self.resultado = "cancelar"

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)

        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        # --- CORRECCIÓN DEFINITIVA: Lógica para crear pestañas o un solo Treeview ---
        if self.es_multi_ambiente:
            self.notebook = ttk.Notebook(main_frame)
            self.notebook.grid(row=0, column=0, sticky="nsew")
            # --- CAMBIO: Vincular el evento de cambio de pestaña ---
            self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

            for macro in self.macros_seleccionados:
                tab_frame = ttk.Frame(self.notebook, padding=5)
                self.notebook.add(tab_frame, text=macro['nombre'])
                tree = self._crear_treeview_en(tab_frame, es_pestaña=True)
                # --- CAMBIO: Inicializar el estado para cada pestaña ---
                self.tabs_info[macro['nombre']] = {
                    'tree': tree, 'frame': tab_frame,
                    'is_validated': False, 'validated_iids': set(), 'checked_states': {}
                }
        else:
            # Si no es multi-ambiente, crear un solo treeview como antes
            frame_preview = ttk.LabelFrame(main_frame, text="Vista Previa de Asignación")
            frame_preview.grid(row=0, column=0, sticky="nsew")
            self.tree_preview = self._crear_treeview_en(frame_preview, es_pestaña=False)
        # --- FIN DE LA CORRECCIÓN ---
        
        # --- CAMBIO: Si no es multi-ambiente, también necesita una estructura de estado ---
        if not self.es_multi_ambiente:
            self.estado_unico = {
                'is_validated': False, 'validated_iids': set(), 'checked_states': {}
            }

        # --- Botones de Acción Final ---
        self.frame_acciones = ttk.Frame(main_frame, padding=(10, 10, 0, 0))
        self.frame_acciones.grid(row=1, column=0, sticky="ew", pady=(10, 0))

        # --- CAMBIO: Añadir botones de selección ---
        self.btn_seleccionar_todos = ttk.Button(self.frame_acciones, text="Seleccionar Todos", command=self.seleccionar_todos, bootstyle="success-outline")
        self.btn_seleccionar_todos.pack(side="left", padx=(0, 5))
        self.btn_deseleccionar_todos = ttk.Button(self.frame_acciones, text="Deseleccionar", command=self.deseleccionar_todos, bootstyle="secondary-outline")
        self.btn_deseleccionar_todos.pack(side="left", padx=(0, 20))

        # --- CAMBIO: Añadir botón Regresar y modificar Cancelar ---
        self.btn_ejecutar = ttk.Button(self.frame_acciones, text="Ejecutar Validación", 
                                       command=self.iniciar_proceso_validacion, 
                                       bootstyle="secondary-outline")
        self.btn_ejecutar.pack(side="right")
        
        self.btn_cancelar = ttk.Button(self.frame_acciones, text="Cancelar", command=self.resetear_pantalla, bootstyle="warning-outline")
        self.btn_cancelar.pack(side="right", padx=(0, 10))

        self.btn_regresar = ttk.Button(self.frame_acciones, text="Regresar", command=self.on_close, bootstyle="secondary")
        self.btn_regresar.pack(side="right", padx=(0, 10))

        # --- CAMBIO: Añadir barra de progreso ---
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        progress_frame.columnconfigure(0, weight=1)

        self.progress_label = ttk.Label(progress_frame, text="Listo para validar.")
        self.progress_label.grid(row=0, column=0, sticky="w", padx=10)

        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=(2, 5))

        self.after(100, self.poblar_vista_previa)
        # --- FIN DEL CAMBIO ---
        
    def _crear_treeview_en(self, parent_frame, es_pestaña):
        """Función auxiliar para crear y configurar un Treeview."""
        if not es_pestaña:
            parent_frame.rowconfigure(0, weight=1)
            parent_frame.columnconfigure(0, weight=1)

        # --- CAMBIO: Añadir columna "Base de Datos" ---
        cols = ("Sel.", "Archivo", "Ruta", "Fecha Local", "Ambiente Asignado", "Base de Datos", "Resultado / Fecha DB")
        tree = ttk.Treeview(parent_frame, columns=cols, show="headings", selectmode="extended")

        for col in cols:
            tree.heading(col, text=col)
        
        tree.column("Sel.", width=40, anchor="c", stretch=False)
        tree.column("Archivo", width=160, anchor="w")
        tree.column("Ruta", width=250, anchor="w")
        tree.column("Fecha Local", width=130, anchor="c")
        tree.column("Ambiente Asignado", width=130, anchor="w")
        tree.column("Base de Datos", width=120, anchor="w")
        tree.column("Resultado / Fecha DB", width=300, anchor="w")

        tree.grid(row=0, column=0, sticky="nsew")

        v_scroll = ttk.Scrollbar(parent_frame, orient="vertical", command=tree.yview)
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll = ttk.Scrollbar(parent_frame, orient="horizontal", command=tree.xview)
        h_scroll.grid(row=1, column=0, sticky="ew")
        tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        # Configurar tags de colores
        tree.tag_configure("advertencia_rojo", background="#ff8a80")
        tree.tag_configure("advertencia_amarillo", background="#fff3bf")
        tree.tag_configure("deshabilitado", foreground="#9ca3af")
        tree.tag_configure("checkbox", foreground="#007bff")

        # Vincular eventos
        tree.bind("<Button-1>", self.on_tree_click)
        tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        # Detectar cambios de selección para animar botón validar
        tree.bind("<<TreeviewSelect>>", lambda e: self._verificar_seleccion_para_animacion(), add="+")

        parent_frame.rowconfigure(0, weight=1)
        parent_frame.columnconfigure(0, weight=1)
        
        return tree

    def on_close(self):
        self.resultado = "finalizar"
        # Detener animación antes de cerrar
        self._detener_animacion_validar()
        # --- CAMBIO: Devolver el foco a la ventana principal antes de cerrar ---
        if self.master.winfo_exists():
            self.master.focus_set()
        self.destroy()
    
    def _verificar_seleccion_para_animacion(self):
        """Verifica si hay archivos seleccionados y activa/desactiva la animación del botón."""
        active_tab_state = self._get_active_tab_state()
        if not active_tab_state:
            return
        
        # Contar cuántos archivos están seleccionados (checked)
        items_seleccionados = sum(1 for checked in active_tab_state.get('checked_states', {}).values() if checked)
        
        if items_seleccionados > 0:
            # Hay archivos seleccionados - activar animación
            if not self.animacion_validar_activa:
                self._iniciar_animacion_validar()
        else:
            # No hay archivos seleccionados - detener animación
            if self.animacion_validar_activa:
                self._detener_animacion_validar()
    
    def _iniciar_animacion_validar(self):
        """Inicia la animación de parpadeo del botón Ejecutar Validación."""
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
                self.after_cancel(self.animacion_validar_id)
            except:
                pass
            self.animacion_validar_id = None
        
        # Restaurar el botón a su estilo normal
        try:
            if hasattr(self, 'btn_ejecutar') and self.btn_ejecutar.winfo_exists():
                self.btn_ejecutar.configure(bootstyle="secondary-outline")
        except:
            pass
    
    def _animar_boton_validar(self):
        """Alterna el color del botón para crear efecto de parpadeo."""
        if not self.animacion_validar_activa:
            return
        
        try:
            if not hasattr(self, 'btn_ejecutar') or not self.btn_ejecutar.winfo_exists():
                self.animacion_validar_activa = False
                return
            
            # Alternar entre dos estilos llamativos
            if self.animacion_validar_estado == 0:
                self.btn_ejecutar.configure(bootstyle="success")  # Verde brillante
                self.animacion_validar_estado = 1
            else:
                self.btn_ejecutar.configure(bootstyle="success-outline")  # Verde outline
                self.animacion_validar_estado = 0
            
            # Programar siguiente cambio (500ms para parpadeo visible pero no molesto)
            self.animacion_validar_id = self.after(500, self._animar_boton_validar)
        except:
            self.animacion_validar_activa = False

    def _get_active_treeview(self):
        """Devuelve el Treeview de la pestaña activa o el único Treeview si no hay pestañas."""
        if not self.winfo_exists():
            return None
        if self.es_multi_ambiente:
            try:
                if self.notebook and self.notebook.winfo_exists():
                    active_tab_frame = self.notebook.nametowidget(self.notebook.select())
                    for info in self.tabs_info.values():
                        if info['frame'] == active_tab_frame:
                            return info['tree']
            except tk.TclError:
                return None # El widget fue destruido
        else:
            return self.tree_preview if hasattr(self, 'tree_preview') else None
        return None

    def _get_active_tab_state(self):
        """Devuelve el diccionario de estado de la pestaña activa o el estado único."""
        if not self.winfo_exists():
            return None
        if self.es_multi_ambiente:
            try:
                if self.notebook and self.notebook.winfo_exists():
                    active_tab_name = self.notebook.tab(self.notebook.select(), "text")
                    return self.tabs_info.get(active_tab_name)
            except tk.TclError:
                return None
        else:
            return self.estado_unico if hasattr(self, 'estado_unico') else None
        return None

    def _on_tab_changed(self, event):
        """Actualiza la UI cuando el usuario cambia de pestaña."""
        self.actualizar_estado_botones()

    def on_tree_click(self, event):
        """Maneja los clics en el Treeview activo para simular checkboxes."""
        active_tree = self._get_active_treeview()
        if not active_tree: return

        region = active_tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        column_id = active_tree.identify_column(event.x)
        # Solo actuar si se hace clic en la primera columna ("Sel.")
        if column_id == "#1":
            iid = active_tree.identify_row(event.y)
            active_tab_state = self._get_active_tab_state()
            if iid and active_tab_state and "deshabilitado" not in active_tree.item(iid, "tags"):
                # Alternar estado
                checked_states = active_tab_state['checked_states']
                checked_states[iid] = not checked_states.get(iid, False)
                
                # Actualizar visualmente
                if checked_states[iid]:
                    active_tree.set(iid, "Sel.", "☑") # Solo actualiza el checkbox
                else:
                    active_tree.set(iid, "Sel.", "☐") # Solo actualiza el checkbox
                
                # Verificar si debe activarse/desactivarse la animación del botón
                self._verificar_seleccion_para_animacion()

    def on_tree_select(self, event):
        """Evita que se seleccionen filas deshabilitadas."""
        active_tree = self._get_active_treeview()
        if not active_tree: return

        selection = active_tree.selection()
        for iid in selection:
            # Si un ítem seleccionado está deshabilitado, quitarlo de la selección
            if "deshabilitado" in active_tree.item(iid, "tags"):
                active_tree.selection_remove(iid)


    def poblar_vista_previa(self):
        print(">>> [dialog] B. poblar_vista_previa() INICIADO.")
        # Limpiar todos los treeviews
        if self.es_multi_ambiente:
            for info in self.tabs_info.values():
                info['tree'].delete(*info['tree'].get_children())
                # --- CAMBIO: Resetear el estado de cada pestaña ---
                info['is_validated'] = False
                info['validated_iids'] = set()
                info['checked_states'] = {}
        else:
            self.tree_preview.delete(*self.tree_preview.get_children())
            # --- CAMBIO: Resetear el estado único ---
            self.estado_unico['is_validated'] = False
            self.estado_unico['validated_iids'] = set()
            self.estado_unico['checked_states'] = {}

        self.plan_plano = []

        # --- CAMBIO: Crear una lista plana de tareas (una por cada archivo-ambiente) ---
        for tarea in self.plan_ejecucion:
            archivo = tarea['archivo']
            if not tarea['ambientes']:
                self.plan_plano.append({'archivo': archivo, 'ambiente': None})
            else:
                for ambiente in tarea['ambientes']:
                    self.plan_plano.append({'archivo': archivo, 'ambiente': ambiente})
        
        for i, tarea_plana in enumerate(self.plan_plano):
            iid = str(i)
            nombre_archivo = tarea_plana['archivo']['nombre_archivo']
            ruta_archivo = tarea_plana['archivo']['rel_path']
            fecha_local_ts = tarea_plana['archivo']['fecha_mod']
            fecha_local_str = datetime.datetime.fromtimestamp(fecha_local_ts).strftime('%Y-%m-%d %H:%M')
            nombre_ambiente = tarea_plana['ambiente']['nombre'] if tarea_plana['ambiente'] else "Sin Asignar"

            # --- CAMBIO: Determinar la base de datos a mostrar en la nueva columna ---
            archivo_obj = tarea_plana['archivo']
            ambiente_obj = tarea_plana['ambiente']
            db_desde_encabezado, _ = _extraer_info_desde_encabezado(archivo_obj['path'])
            db_desde_use = _extraer_db_de_sp(archivo_obj['path'])
            # La lógica de prioridad es la misma que en la validación
            base_datos_a_mostrar = archivo_obj.get("db_override") or db_desde_encabezado or db_desde_use or (ambiente_obj.get('base') if ambiente_obj else "N/A")

            # Añadir la base de datos a los valores de la fila
            values = ("☑", nombre_archivo, ruta_archivo, fecha_local_str, nombre_ambiente, base_datos_a_mostrar, "")

            target_tree = None
            if self.es_multi_ambiente:
                # Determinar a qué pestaña (macro) pertenece esta tarea
                macro_padre = self._get_macro_for_ambiente(nombre_ambiente)
                if macro_padre and macro_padre in self.tabs_info:
                    tab_info = self.tabs_info[macro_padre]
                    target_tree = tab_info['tree']
                    tab_info['checked_states'][iid] = True # Marcar como seleccionado por defecto
            else:
                target_tree = self.tree_preview
                self.estado_unico['checked_states'][iid] = True

            if target_tree:
                target_tree.insert("", "end", values=values, iid=iid, tags=("checkbox",))
                target_tree.selection_add(iid)
        
        # Verificar si hay archivos seleccionados para activar la animación del botón
        self.after(100, self._verificar_seleccion_para_animacion)

    def _get_macro_for_ambiente(self, nombre_ambiente):
        """Encuentra el macroambiente padre para un ambiente dado."""
        # Si el ambiente es un macro, es su propio padre
        if nombre_ambiente in self.relaciones_hijos:
            return nombre_ambiente
        # Buscar si es hijo de algún macro
        for macro, hijos in self.relaciones_hijos.items():
            if nombre_ambiente in hijos:
                return macro
        return None

    def resetear_pantalla(self):
        """Reinicia la pestaña activa a su estado inicial (pre-validación)."""
        # --- NUEVO: Cancelar validación en curso ---
        if hasattr(self, 'validacion_cancelada'):
            self.validacion_cancelada = True
            print(">>> [dialog] CANCELACIÓN SOLICITADA - Deteniendo worker...")
        
        active_tree = self._get_active_treeview()
        active_tab_state = self._get_active_tab_state()

        if not active_tree or not active_tab_state:
            return

        # 1. Resetear el estado de la pestaña
        active_tab_state['is_validated'] = False
        active_tab_state['validated_iids'].clear()

        # 2. Restaurar cada fila en el Treeview de la pestaña activa
        try:
            if active_tree.winfo_exists():
                for iid in active_tree.get_children():
                    # Restaurar checkbox y estado
                    active_tree.set(iid, "Sel.", "☑")
                    active_tab_state['checked_states'][iid] = True
                    # Limpiar resultado
                    active_tree.set(iid, "Resultado / Fecha DB", "")
                    # Quitar todos los tags y dejar solo el de checkbox
                    active_tree.item(iid, tags=("checkbox",))
        except tk.TclError:
            pass # El widget fue destruido

        # 3. Resetear la barra de progreso y el texto
        self.progress_label.config(text="Listo para validar.")
        self.progress_bar['value'] = 0

        # 4. Restaurar los botones y estados
        self.actualizar_estado_botones()
        self.bloquear_controles(False)

    def iniciar_proceso_validacion(self):
        print(">>> [dialog] C. iniciar_proceso_validacion() INICIADO.")
        
        # Resetear flag de cancelación
        self.validacion_cancelada = False
        
        # Detener la animación del botón al iniciar la validación
        self._detener_animacion_validar()
        
        active_tree = self._get_active_treeview()
        if not active_tree:
            messagebox.showerror("Error", "No se pudo encontrar la tabla de archivos activa.", parent=self)
            return

        active_tab_state = self._get_active_tab_state()
        items_seleccionados = [iid for iid, checked in active_tab_state['checked_states'].items() if checked]

        if not items_seleccionados:
            messagebox.showwarning("Sin Selección", "Debe seleccionar al menos un archivo para validar.", parent=self)
            return

        # --- REQUERIMIENTO: Guardar los IIDs que se van a validar ---
        active_tab_state['validated_iids'] = set(items_seleccionados)

        self.bloquear_controles(True)
        self.progress_bar['maximum'] = len(items_seleccionados)
        self.progress_bar['value'] = 0

        tareas_a_validar = []
        for iid in items_seleccionados:
            # Limpiar resultados anteriores
            active_tree.set(iid, "Resultado / Fecha DB", "")
            tareas_a_validar.append((iid, self.plan_plano[int(iid)]))

        print(f">>> [dialog] D. Lanzando hilo worker_validacion para {len(tareas_a_validar)} tareas...")
        threading.Thread(target=self.worker_validacion, args=(tareas_a_validar,), daemon=True).start()

    def worker_validacion(self, tareas):
        from Usuario_administrador.handlers.catalogacion import obtener_fecha_desde_sp_help, _validar_y_corregir_base_datos
        import pyodbc # Para capturar errores de conexión

        print(">>> [dialog-worker] E. Hilo worker_validacion INICIADO.")
        print(f">>> [FASE 1] Verificando BDs de {len(tareas)} archivos...")
        
        # ============================================================================
        # FASE 1: VERIFICAR TODAS LAS BDs PRIMERO
        # ============================================================================
        tareas_con_bd_valida = []
        tareas_sin_bd_valida = []
        
        for i, (iid, tarea) in enumerate(tareas):
            # Verificar si se solicitó cancelación
            if self.validacion_cancelada:
                print(f">>> [FASE 1] CANCELADA por usuario en iteración {i+1}/{len(tareas)}")
                self.after(0, self.progress_label.config, {'text': 'Validación cancelada por usuario'})
                return
            
            archivo = tarea['archivo']
            ambiente_a_validar = tarea['ambiente']
            nombre_archivo_completo = archivo['nombre_archivo']
            
            # Omitir si no hay ambiente
            if not ambiente_a_validar:
                self.after(0, self.actualizar_fila, iid, i + 1, "Sin Ambiente")
                continue

            # Omitir archivos .sql
            if nombre_archivo_completo.lower().endswith('.sql'):
                self.after(0, self.actualizar_fila, iid, i + 1, "Listo para catalogar")
                continue

            # Extraer información del archivo
            db_desde_encabezado, sp_desde_encabezado = _extraer_info_desde_encabezado(archivo['path'])
            db_desde_use = _extraer_db_de_sp(archivo['path'])
            base_datos_inicial = archivo.get("db_override") or db_desde_encabezado or db_desde_use or ambiente_a_validar.get('base')
            
            sp_desde_create = _extraer_sp_name_de_sp(archivo['path'])
            nombre_sp_a_buscar = archivo.get("sp_name_override") or sp_desde_encabezado or sp_desde_create or os.path.splitext(nombre_archivo_completo)[0]
            
            # Actualizar progreso
            self.after(0, self.actualizar_progreso, i, f"[Fase 1/3] Preparando: {base_datos_inicial}...")
            
            # NO verificar conexión aquí - causaba errores HY000 con Sybase
            # La verificación real se hace en Fase 2 al buscar el SP
            
            # Todas las tareas van a validación normal (Fase 2)
            tareas_con_bd_valida.append({
                'iid': iid,
                'archivo': archivo,
                'ambiente': ambiente_a_validar,
                'bd': base_datos_inicial,  # Usar BD inicial directamente
                'sp': nombre_sp_a_buscar,
                'fecha_local': archivo['fecha_mod']
            })
        
        print(f">>> [FASE 1] Completada: {len(tareas_con_bd_valida)} archivos preparados para validación")
        # Nota: tareas_sin_bd_valida estará vacía porque ya no clasificamos en Fase 1
        
        # ============================================================================
        # FASE 2: VALIDACIÓN NORMAL
        # ============================================================================
        print(f">>> [FASE 2] Validación de {len(tareas_con_bd_valida)} archivos...")
        
        for idx, tarea_info in enumerate(tareas_con_bd_valida):
            # Verificar si se solicitó cancelación
            if self.validacion_cancelada:
                print(f">>> [FASE 2] CANCELADA por usuario en iteración {idx+1}/{len(tareas_con_bd_valida)}")
                self.after(0, self.progress_label.config, {'text': 'Validación cancelada por usuario'})
                return
            
            iid = tarea_info['iid']
            # Actualizar barra de progreso (idx va de 0 a len-1, entonces idx+1 para mostrar de 1 a len)
            progreso_actual = idx + 1
            bd_inicial = tarea_info['bd']
            
            # Validar y corregir la BD antes de buscar
            from Usuario_administrador.handlers.catalogacion import _validar_y_corregir_base_datos
            bd_corregida = _validar_y_corregir_base_datos(bd_inicial, tarea_info['archivo']['path'], tarea_info['ambiente'])
            
            self.after(0, self.actualizar_progreso, progreso_actual, 
                      f"[Fase 2/2] Validando '{tarea_info['sp']}' ({progreso_actual}/{len(tareas_con_bd_valida)}) → Buscando en: {bd_corregida}")
            
            # Ya no hay flag 'error_conexion' porque no hay verificación previa
            
            try:
                # Definir callback para actualizar progreso con cada BD que se busca
                def callback_bd_actual(bd_nombre):
                    self.after(0, self.actualizar_progreso, progreso_actual, 
                              f"[Fase 2/2] '{tarea_info['sp']}' ({progreso_actual}/{len(tareas_con_bd_valida)}) → Buscando en: {bd_nombre}")
                
                # Búsqueda normal - obtener_fecha_desde_sp_help manejará BD incorrectas
                resultado_busqueda = obtener_fecha_desde_sp_help(tarea_info['sp'], bd_corregida, tarea_info['ambiente'], callback_bd_actual)
                
                if isinstance(resultado_busqueda, tuple) and len(resultado_busqueda) == 2:
                    fecha_db_str, bd_real = resultado_busqueda
                else:
                    fecha_db_str = str(resultado_busqueda)
                    bd_real = None
                
                # Actualizar mensaje de progreso con la BD donde se encontró realmente
                if bd_real:
                    self.after(0, self.actualizar_progreso, progreso_actual, 
                              f"[Fase 2/2] '{tarea_info['sp']}' ({progreso_actual}/{len(tareas_con_bd_valida)}) → Encontrado en: {bd_real}")
                else:
                    self.after(0, self.actualizar_progreso, progreso_actual, 
                              f"[Fase 2/2] '{tarea_info['sp']}' ({progreso_actual}/{len(tareas_con_bd_valida)}) → BD: {bd_corregida}")
                
                resultado_final = self._procesar_resultado_fecha(fecha_db_str, tarea_info['fecha_local'], iid)
                
                # Si se encontró en BD diferente, actualizar la columna BD y agregar nota
                if bd_real:
                    resultado_final = f"{resultado_final} [encontrado en: {bd_real}]"
                    # Actualizar la columna "Base de Datos" con la BD real
                    self.after(0, self.actualizar_columna_bd, iid, bd_real)
                
                self.after(0, self.actualizar_fila, iid, progreso_actual, resultado_final)
                
            except Exception as e:
                self.after(0, self.actualizar_fila, iid, progreso_actual, f"Error: {str(e)[:40]}")
        
        print(f">>> [FASE 2] Completada")
        print(">>> [dialog-worker] F. Hilo worker_validacion FINALIZADO.")
        self.after(0, self.finalizar_validacion)
    
    def _procesar_resultado_fecha(self, fecha_db_str, fecha_local_ts, iid):
        """Procesa el resultado de la fecha y retorna el texto formateado."""
        if fecha_db_str not in ["No encontrado en DB", "Error de conexión"]:
            try:
                # Intentar parsear fecha
                try:
                    fecha_db_obj = datetime.datetime.strptime(fecha_db_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    fecha_db_obj = datetime.datetime.strptime(fecha_db_str, '%b %d %Y %I:%M:%S:%f%p')

                fecha_local_obj = datetime.datetime.fromtimestamp(fecha_local_ts)
                
                # Lógica de resaltado
                tags_a_aplicar = []
                now = datetime.datetime.now()
                un_mes_atras = now - datetime.timedelta(days=30)

                if fecha_local_obj < fecha_db_obj:
                    resultado = f"⚠️ Fecha local menor a fecha BD | {fecha_db_obj.strftime('%Y-%m-%d %H:%M:%S')}"
                    tags_a_aplicar.append("advertencia_rojo")
                elif fecha_db_obj > un_mes_atras:
                    resultado = f"🟡 Reciente (<1 mes) | {fecha_db_obj.strftime('%Y-%m-%d %H:%M:%S')}"
                    tags_a_aplicar.append("advertencia_amarillo")
                else:
                    resultado = fecha_db_obj.strftime('%Y-%m-%d %H:%M:%S')
                
                self.after(0, self.actualizar_tags_fila, iid, tags_a_aplicar)
                return resultado
                
            except (ValueError, TypeError) as e:
                return f"Error parseo fecha: {str(e)[:30]}"
        else:
            return fecha_db_str

    def actualizar_progreso(self, valor, texto):
        # --- CORRECCIÓN: Verificar si el widget existe antes de actualizar para evitar crash ---
        if not self.progress_bar.winfo_exists():
            return
        self.progress_bar['value'] = valor
        self.progress_label.config(text=texto)

    def actualizar_fila(self, iid, valor_progreso, resultado_texto):
        """Actualiza una fila en el Treeview correspondiente, sea único o en una pestaña."""
        if not self.winfo_exists():
            return

        if self.progress_bar.winfo_exists():
            self.progress_bar['value'] = valor_progreso

        # Obtener la lista de todos los treeviews existentes
        treeviews = []
        if self.es_multi_ambiente:
            if hasattr(self, 'tabs_info'):
                treeviews = [info['tree'] for info in self.tabs_info.values()]
        else:
            if hasattr(self, 'tree_preview') and self.tree_preview.winfo_exists():
                treeviews = [self.tree_preview]

        # Buscar el iid en todos los treeviews y actualizar la fila correspondiente
        for tree in treeviews:
            try:
                if tree and tree.winfo_exists() and tree.exists(iid):
                    tree.set(iid, "Resultado / Fecha DB", resultado_texto)
                    break # El iid es único, no es necesario seguir buscando
            except tk.TclError:
                continue # El widget fue destruido, pasar al siguiente

    def actualizar_columna_bd(self, iid, nueva_bd):
        """Actualiza la columna 'Base de Datos' cuando se encuentra en una BD diferente."""
        if not self.winfo_exists():
            return

        # Obtener la lista de todos los treeviews existentes
        treeviews = []
        if self.es_multi_ambiente:
            if hasattr(self, 'tabs_info'):
                treeviews = [info['tree'] for info in self.tabs_info.values()]
        else:
            if hasattr(self, 'tree_preview') and self.tree_preview.winfo_exists():
                treeviews = [self.tree_preview]

        # Buscar el iid en todos los treeviews y actualizar la columna BD
        for tree in treeviews:
            try:
                if tree and tree.winfo_exists() and tree.exists(iid):
                    tree.set(iid, "Base de Datos", nueva_bd)
                    print(f"  ✏️ Columna BD actualizada a: '{nueva_bd}' para iid {iid}")
                    break # El iid es único, no es necesario seguir buscando
            except tk.TclError:
                continue # El widget fue destruido, pasar al siguiente

    def actualizar_tags_fila(self, iid, nuevos_tags):
        """Añade nuevos tags a una fila sin borrar los existentes."""
        if not self.winfo_exists():
            return

        treeviews = []
        if self.es_multi_ambiente:
            if hasattr(self, 'tabs_info'):
                treeviews = [info['tree'] for info in self.tabs_info.values()]
        else:
            if hasattr(self, 'tree_preview') and self.tree_preview.winfo_exists():
                treeviews = [self.tree_preview]

        for tree in treeviews:
            try:
                if tree and tree.winfo_exists() and tree.exists(iid):
                    tags_actuales = list(tree.item(iid, "tags"))
                    tags_finales = tuple(tags_actuales + nuevos_tags)
                    tree.item(iid, tags=tags_finales)
                    break
            except tk.TclError:
                continue

    def finalizar_validacion(self):
        if not self.winfo_exists():
            return

        # Actualizar la barra de progreso al 100%
        if hasattr(self, 'progress_bar') and self.progress_bar.winfo_exists():
            self.progress_bar['value'] = self.progress_bar['maximum']
            self.progress_label.config(text="Validación completada al 100%")

        active_tab_state = self._get_active_tab_state()
        if active_tab_state:
            active_tab_state['is_validated'] = True
            active_tree = self._get_active_treeview()

            if active_tree:
                try:
                    if not active_tree.winfo_exists(): return
                    all_iids_in_tree = active_tree.get_children()
                    for iid in all_iids_in_tree:
                        if iid not in active_tab_state['validated_iids']:
                            active_tree.set(iid, "Sel.", "")
                            active_tree.item(iid, tags=("deshabilitado",))
                            active_tab_state['checked_states'][iid] = False
                        else:
                            active_tree.set(iid, "Sel.", "☑")
                            active_tree.selection_remove(iid)
                except tk.TclError:
                    pass

        self.actualizar_estado_botones()
        self.bloquear_controles(False)

        if self.winfo_exists():
            messagebox.showinfo("Validación Finalizada", "El proceso de validación ha terminado. Revise los resultados antes de catalogar.", parent=self)

    def ejecutar_catalogacion(self):
        print(">>> [dialog] G. ejecutar_catalogacion() INICIADO.")
        active_tab_state = self._get_active_tab_state()
        if not active_tab_state:
            return

        validated_iids = active_tab_state.get('validated_iids', set())
        items_seleccionados = [iid for iid, checked in active_tab_state['checked_states'].items() if checked and iid in validated_iids]
        if not items_seleccionados:
            messagebox.showwarning("Sin Selección", "Debe seleccionar al menos un archivo para catalogar usando los checkboxes.", parent=self)
            return

       # Construir el plan final solo con los ítems seleccionados
        # IMPORTANTE: Actualizar la BD con la encontrada durante la validación
        active_tree = self._get_active_treeview()
        self.plan_ejecucion = []
        
        for iid in items_seleccionados:
            tarea_original = self.plan_plano[int(iid)]
            archivo = tarea_original['archivo'].copy()
            
            # Obtener la BD correcta del Treeview (actualizada durante validación)
            if active_tree and active_tree.exists(iid):
                bd_validada = active_tree.set(iid, "Base de Datos")
                if bd_validada and bd_validada != 'N/A':
                    # Actualizar db_override con la BD correcta encontrada en validación
                    archivo['db_override'] = bd_validada
                    print(f">>> [dialog] BD actualizada para {archivo['nombre_archivo']}: {bd_validada}")
            
            self.plan_ejecucion.append({
                'archivo': archivo,
                'ambiente': tarea_original['ambiente']
            })
        
        if self.plan_ejecucion:
            self.resultado = "ejecutar"
            print(f">>> [dialog] H. Plan final construido con {len(self.plan_ejecucion)} tareas.")
            print(">>> [dialog] I. Llamando callback para ejecutar catalogación...")
            # --- CAMBIO: Llamar al callback en lugar de cerrar la ventana ---
            if self.on_ejecutar_callback:
                self.on_ejecutar_callback(self.plan_ejecucion)
            # La ventana permanece abierta durante la catalogación

    def bloquear_controles(self, bloquear):
        estado = "disabled" if bloquear else "normal"
        self.btn_ejecutar.config(state=estado)
        self.btn_seleccionar_todos.config(state=estado)
        self.btn_deseleccionar_todos.config(state=estado)
        if bloquear:
            self.btn_regresar.config(text="Cerrar")
        else:
            self.btn_regresar.config(text="Regresar")

    def actualizar_estado_botones(self):
        """Actualiza el botón principal según el estado de la pestaña activa."""
        if not self.winfo_exists():
            return

        active_tab_state = self._get_active_tab_state()
        if not active_tab_state:
            return

        try:
            if active_tab_state['is_validated']:
                self.btn_ejecutar.config(text="Ejecutar Catalogación", command=self.ejecutar_catalogacion)
            else:
                self.btn_ejecutar.config(text="Ejecutar Validación", command=self.iniciar_proceso_validacion)
        except tk.TclError:
            pass # El widget fue destruido

    def seleccionar_todos(self):
        active_tree = self._get_active_treeview()
        active_tab_state = self._get_active_tab_state()
        if not active_tree or not active_tab_state: return

        for iid in active_tree.get_children():
            # --- MEJORA: Solo seleccionar los que no están deshabilitados ---
            if "deshabilitado" not in active_tree.item(iid, "tags"):
                active_tree.selection_add(iid)
                active_tree.set(iid, "Sel.", "☑")
                active_tab_state['checked_states'][iid] = True
        
        # Verificar si debe activarse la animación del botón
        self._verificar_seleccion_para_animacion()

    def deseleccionar_todos(self):
        active_tree = self._get_active_treeview()
        active_tab_state = self._get_active_tab_state()
        if not active_tree or not active_tab_state: return

        # --- MEJORA: Desmarcar todos los checkboxes y limpiar la selección ---
        for iid in active_tree.get_children():
            if "deshabilitado" not in active_tree.item(iid, "tags"):
                active_tree.set(iid, "Sel.", "☐")
                active_tab_state['checked_states'][iid] = False
        # Siempre eliminar la selección visual para que los colores sean visibles
        active_tree.selection_remove(active_tree.selection())
        
        # Verificar si debe desactivarse la animación del botón
        self._verificar_seleccion_para_animacion()
